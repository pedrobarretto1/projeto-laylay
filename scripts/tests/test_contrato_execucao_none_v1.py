from __future__ import annotations

# P0_CONTRATO_EXECUCAO_NONE_V1_20260815

import json

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.autonomia.coordenador_intencao import (
    _preparar_intent_execucao,
    executar_fluxo_intencao,
)
from mente_laylay.autonomia.higiene_resposta_ia import limpar_resposta_da_ia
from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime


class _EstadoFake:
    def __init__(self) -> None:
        self.mental = {
            "plano_turno_atual": {
                "fase": "executado",
                "comandos": [],
                "erros": [],
                "especialistas": {},
            }
        }

    def atualizar_campos(self, dominio: str, **campos) -> None:
        assert dominio == "mental"
        self.mental.update(campos)


def _atualizar_plano_fake(plano, *, fase, comandos, erros=(), fala=""):
    novo = dict(plano or {})
    novo.update(
        fase=fase,
        comandos=[dict(item) for item in comandos],
        erros=list(erros),
        fala_planejada=fala,
    )
    return novo


def _runtime() -> tuple[AdaptadoresAplicacaoRuntime, _EstadoFake]:
    estado = _EstadoFake()
    namespace = {
        "_registrar_resultado_execucao_base": lambda *_args, **_kwargs: None,
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": _atualizar_plano_fake,
        "_concluir_correcao_interpretacao_mente": lambda *_args, **_kwargs: {},
        "print": lambda *_args, **_kwargs: None,
    }
    return AdaptadoresAplicacaoRuntime(lambda: namespace), estado


def test_preparar_intent_cria_copia_e_identidade_por_execucao() -> None:
    original = {"intent": "SEARCH", "params": {"query": "python"}}
    primeiro = _preparar_intent_execucao(original)
    segundo = _preparar_intent_execucao(original)

    assert "id_solicitacao" not in original
    assert primeiro is not original
    assert primeiro["id_solicitacao"]
    assert segundo["id_solicitacao"]
    assert primeiro["id_solicitacao"] != segundo["id_solicitacao"]
    assert primeiro["params"] == original["params"]


def test_preparar_intent_preserva_id_existente() -> None:
    preparado = _preparar_intent_execucao({
        "intent": "SEARCH",
        "id_solicitacao": "exec-upstream",
    })
    assert preparado["id_solicitacao"] == "exec-upstream"


def test_adaptador_reutiliza_identidade_recebida_do_coordenador() -> None:
    adaptador = AdaptadorResultadoOperacional(
        {"intent": "SEARCH", "id_solicitacao": "exec-coordenador"},
        {"query": "python"},
        "pesquisa python",
        "pc_a",
        {},
    )
    assert adaptador.id_solicitacao == "exec-coordenador"


def test_adaptador_aceita_request_id_legado_e_gera_id_quando_ausente() -> None:
    legado = AdaptadorResultadoOperacional(
        {"intent": "SEARCH", "request_id": "request-legado"},
        {},
        "teste",
        "pc_a",
        {},
    )
    novo_a = AdaptadorResultadoOperacional({"intent": "SEARCH"}, {}, "a", "pc_a", {})
    novo_b = AdaptadorResultadoOperacional({"intent": "SEARCH"}, {}, "b", "pc_a", {})

    assert legado.id_solicitacao == "request-legado"
    assert novo_a.id_solicitacao
    assert novo_b.id_solicitacao
    assert novo_a.id_solicitacao != novo_b.id_solicitacao


def test_fluxo_consolida_resultado_detalhado_e_fallback_na_mesma_execucao() -> None:
    runtime, estado = _runtime()
    ids_vistos: list[str] = []

    def _executar(intent, texto_original):
        ids_vistos.append(str(intent.get("id_solicitacao") or ""))
        adaptador = AdaptadorResultadoOperacional(
            intent,
            dict(intent.get("params") or {}),
            texto_original,
            "pc_a",
            {"_registrar_resultado_execucao": runtime.registrar_resultado_execucao},
        )
        assert adaptador.id_solicitacao == intent["id_solicitacao"]
        adaptador.marcar_resultado(
            "resultados_web_encontrados",
            executou=True,
            confirmado=True,
            params_resolvidos={"query": "python"},
        )
        return True

    ctx = {
        "executar_intencao": _executar,
        "registrar_resultado_execucao": runtime.registrar_resultado_execucao,
        "registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
    }
    intent_original = {"intent": "SEARCH", "params": {"query": "python"}}

    executou = executar_fluxo_intencao(
        "pesquise python",
        "teste-regressao",
        ctx,
        resolver_cb=lambda *_args: (intent_original, "ia-first"),
    )

    assert executou is True
    assert "id_solicitacao" not in intent_original
    assert len(ids_vistos) == 1 and ids_vistos[0]
    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["id_solicitacao"] == ids_vistos[0]
    assert comandos[0]["intent"] == "SEARCH"
    assert comandos[0]["status"] == "resultados_web_encontrados"
    assert comandos[0]["params"]["query"] == "python"
    assert comandos[0]["executou"] is True
    assert comandos[0]["confirmado"] is True


def test_fluxo_fallback_continua_observando_rota_legada_sem_publicacao_detalhada() -> None:
    runtime, estado = _runtime()
    ids_vistos: list[str] = []

    def _executar(intent, _texto_original):
        ids_vistos.append(str(intent.get("id_solicitacao") or ""))
        return True

    ctx = {
        "executar_intencao": _executar,
        "registrar_resultado_execucao": runtime.registrar_resultado_execucao,
        "registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
    }

    assert executar_fluxo_intencao(
        "faz algo legado",
        "teste-legado",
        ctx,
        resolver_cb=lambda *_args: ({"intent": "LEGACY_ACTION"}, "ia-first"),
    ) is True

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["intent"] == "LEGACY_ACTION"
    assert comandos[0]["id_solicitacao"] == ids_vistos[0]
    assert ids_vistos[0]


def test_none_da_ia_vira_lista_vazia_sem_apagar_fala() -> None:
    bruto = json.dumps({
        "fala": "Beleza, deixo assim.",
        "comandos": [{"intent": "none", "alvo": "none"}],
    }, ensure_ascii=False)

    fala, comandos = limpar_resposta_da_ia(bruto)

    assert "Beleza" in fala
    assert comandos == []


def test_none_e_case_insensitive_e_funciona_em_acao_action_e_tuple() -> None:
    casos = [
        {"intent": "  NONE  ", "alvo": "none"},
        {"acao": "None", "alvo": "none"},
        {"action": "NONE", "alvo": "none"},
    ]
    for comando in casos:
        _fala, comandos = limpar_resposta_da_ia(("ok", [comando]))
        assert comandos == []


def test_none_misturado_nao_remove_comando_real() -> None:
    bruto = json.dumps({
        "fala": "Vou pesquisar.",
        "comandos": [
            {"intent": "none", "alvo": "none"},
            {"intent": "SEARCH", "params": {"query": "python"}},
        ],
    })

    _fala, comandos = limpar_resposta_da_ia(bruto)

    assert len(comandos) == 1
    assert comandos[0]["intent"] == "SEARCH"


def test_alvo_none_em_comando_real_nao_e_descartado() -> None:
    bruto = json.dumps({
        "fala": "Certo.",
        "comandos": [{"intent": "SEARCH", "alvo": "none", "params": {"query": "none"}}],
    })

    _fala, comandos = limpar_resposta_da_ia(bruto)

    assert len(comandos) == 1
    assert comandos[0]["intent"] == "SEARCH"
    assert comandos[0]["alvo"] == "none"

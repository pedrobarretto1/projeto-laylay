from __future__ import annotations

import json
from pathlib import Path

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno
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


def _runtime() -> tuple[AdaptadoresAplicacaoRuntime, _EstadoFake, list[str]]:
    estado = _EstadoFake()
    logs: list[str] = []
    namespace = {
        "_registrar_resultado_execucao_base": lambda *_args, **_kwargs: None,
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": _atualizar_plano_fake,
        "_concluir_correcao_interpretacao_mente": lambda *_args, **_kwargs: {},
        "print": logs.append,
    }
    return AdaptadoresAplicacaoRuntime(lambda: namespace), estado, logs


def _resultado(exec_id: str, intent: str, status: str, params: dict) -> dict:
    return {
        "id_solicitacao": exec_id,
        "intent": intent,
        "status": status,
        "params": dict(params),
        "executou": True,
        "confirmado": True,
        "origem": "teste",
    }


def test_adaptador_atribui_identidade_por_invocacao() -> None:
    primeiro = AdaptadorResultadoOperacional(
        {"intent": "SEARCH"}, {"query": "python"}, "pesquisa python", "pc_a", {}
    )
    segundo = AdaptadorResultadoOperacional(
        {"intent": "SEARCH"}, {"query": "python"}, "abre o primeiro", "pc_a", {}
    )

    assert primeiro.id_solicitacao
    assert segundo.id_solicitacao
    assert primeiro.id_solicitacao != segundo.id_solicitacao


def test_mesmo_adaptador_reutiliza_id_em_publicacoes_da_mesma_execucao() -> None:
    contratos = []
    adaptador = AdaptadorResultadoOperacional(
        {"intent": "SEARCH"},
        {"query": "python"},
        "pesquisa python",
        "pc_a",
        {"_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: contratos.append(contrato)},
    )

    adaptador.marcar_resultado("resultados_web_encontrados", executou=True)
    adaptador.marcar_resultado(
        "resultado_web_aberto",
        executou=True,
        params_resolvidos={"abrir_resultado": 1},
    )

    assert len(contratos) == 2
    assert {item.id_solicitacao for item in contratos} == {adaptador.id_solicitacao}


def test_ids_diferentes_preservam_dois_search_no_plano() -> None:
    runtime, estado, logs = _runtime()
    runtime.registrar_resultado_execucao(
        _resultado("search-1", "SEARCH", "resultados_web_encontrados", {"query": "python"}),
        "pesquisa python",
        True,
        origem="executor",
    )
    runtime.registrar_resultado_execucao(
        _resultado(
            "search-2",
            "SEARCH",
            "resultado_web_aberto",
            {"query": "python", "abrir_resultado": 1},
        ),
        "abre o primeiro resultado",
        True,
        origem="executor",
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert logs == []
    assert [item["id_solicitacao"] for item in comandos] == ["search-1", "search-2"]
    assert [item["intent"] for item in comandos] == ["SEARCH", "SEARCH"]
    assert comandos[0]["params"] == {"query": "python"}
    assert comandos[1]["params"]["abrir_resultado"] == 1


def test_mesmo_id_consolida_sem_mudar_posicao() -> None:
    runtime, estado, _logs = _runtime()
    runtime.registrar_resultado_execucao(
        _resultado("exec-a", "SEARCH", "resultados_web_encontrados", {"query": "python"}),
        "pesquisa python",
        True,
    )
    runtime.registrar_resultado_execucao(
        _resultado("exec-b", "IOT_STATUS", "ligado", {"alvo": "lampada_quarto"}),
        "como ela ficou",
        True,
    )
    runtime.registrar_resultado_execucao(
        _resultado(
            "exec-a",
            "SEARCH",
            "resultado_web_aberto",
            {"query": "python", "abrir_resultado": 1},
        ),
        "abre o primeiro",
        True,
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert [item["id_solicitacao"] for item in comandos] == ["exec-a", "exec-b"]
    assert comandos[0]["status"] == "resultado_web_aberto"
    assert comandos[0]["params"]["abrir_resultado"] == 1


def test_iot_control_repetido_com_ids_diferentes_nao_colapsa() -> None:
    runtime, estado, _logs = _runtime()
    runtime.registrar_resultado_execucao(
        _resultado(
            "iot-1",
            "IOT_CONTROL",
            "ligado",
            {"acao": "ligar", "alvo": "lampada_quarto"},
        ),
        "liga a lampada",
        True,
    )
    runtime.registrar_resultado_execucao(
        _resultado(
            "iot-2",
            "IOT_CONTROL",
            "cor_ajustada",
            {"acao": "ajustar_cor", "alvo": "lampada_quarto", "cor": "azul"},
        ),
        "deixa azul",
        True,
    )
    runtime.registrar_resultado_execucao(
        _resultado(
            "iot-3",
            "IOT_STATUS",
            "ligado",
            {"acao": "status", "alvo": "lampada_quarto"},
        ),
        "como ela ficou",
        True,
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert [item["intent"] for item in comandos] == [
        "IOT_CONTROL", "IOT_CONTROL", "IOT_STATUS"
    ]
    assert [item["id_solicitacao"] for item in comandos] == ["iot-1", "iot-2", "iot-3"]


def test_resultado_legado_sem_id_mantem_deduplicacao_por_intent() -> None:
    runtime, estado, _logs = _runtime()
    primeiro = _resultado("", "SEARCH", "resultados_web_encontrados", {"query": "a"})
    segundo = _resultado("", "SEARCH", "resultado_web_aberto", {"query": "b"})
    runtime.registrar_resultado_execucao(primeiro, "pesquisa a", True)
    runtime.registrar_resultado_execucao(segundo, "pesquisa b", True)

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["status"] == "resultado_web_aberto"
    assert comandos[0]["params"]["query"] == "b"


def test_plano_preserva_identidade_params_e_continua_serializavel() -> None:
    plano = atualizar_plano_turno(
        {"fase": "planejado", "especialistas": {}},
        fase="executado",
        comandos=[{
            "id_solicitacao": "search-2",
            "intent": "SEARCH",
            "alvo": "python",
            "status": "resultado_web_aberto",
            "executou": True,
            "confirmado": True,
            "params": {
                "query": "python",
                "abrir_resultado": 1,
                "caminho": Path("resultado.md"),
                "rgb": (0, 0, 255),
            },
            "origem": "executor",
            "detalhe": "resultado observado",
        }],
    )

    comando = plano["comandos"][0]
    assert comando["id_solicitacao"] == "search-2"
    assert comando["params"]["abrir_resultado"] == 1
    assert comando["params"]["caminho"] == "resultado.md"
    assert comando["params"]["rgb"] == [0, 0, 255]
    assert comando["origem"] == "executor"
    assert comando["detalhe"] == "resultado observado"
    json.dumps(plano, ensure_ascii=False)

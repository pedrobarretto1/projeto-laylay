"""P17: resistência opcional exige causa ativa e conclusão observável."""

from __future__ import annotations

import time
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
from types import SimpleNamespace

import pytest

import mente_laylay.autonomia.roteador_intencao as roteador
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.controle_midia import executar_media_control
from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.integracao.pc_b_integracao import DestinoPCRuntime
from mente_laylay.personalidade.politica_resistencia import avaliar_resistencia_contextual
from mente_laylay.memoria_mental.resultado_acao import (
    interpretar_tratamento_operacional,
    marcar_tratamento_operacional,
)


def _evento(*, responsabilidade: str = "usuario", idade_s: float = 0.0) -> dict:
    return criar_evento_emocional_causal(
        origem="resultado_operacional",
        causa="repetição redundante observada",
        evidencia_ref="p17-redundancia-4",
        natureza_evidencia="fato_observado",
        responsabilidade=responsabilidade,
        confianca=0.96,
        relevancia=0.95,
        novidade=0.2,
        intensidade=3,
        sensibilidade="normal",
        alvo="Calculadora",
        validade_s=45.0,
        permite_expressao=True,
        emocao="brava",
        nivel=3,
        arco="bronca_brincalhona",
        ts=time.time() - idade_s,
    )


def _pendencia_real() -> PendenciaAcaoRuntime:
    estado: dict = {}

    def atualizar(mutar):
        novo = mutar(dict(estado))
        estado.clear()
        estado.update(novo)
        return dict(estado)

    return PendenciaAcaoRuntime(
        estado_getter=lambda: dict(estado), estado_atualizar=atualizar,
        log=lambda *_: None,
    )


def _executar_sem_efeito(
    monkeypatch, texto: str, *, evento: dict, ja_resistiu: bool = False,
    registro_aceito: bool = True, params_extras: dict | None = None,
):
    chamadas: list[str] = []
    falas: list[str] = []
    pendencia = _pendencia_real()
    for nome in (
        "janelas", "navegador", "audio", "agenda", "informacoes", "sistema",
        "musical", "playlists", "cancelamentos", "integracoes",
    ):
        def despachar(*_args, _nome=nome, **_kwargs):
            chamadas.append(_nome)
            return ResultadoDespacho.concluido() if _nome == "integracoes" else ResultadoDespacho.nao_tratado()

        monkeypatch.setattr(roteador, f"_executar_intencao_{nome}", despachar)

    pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle", **dict(params_extras or {})}}
    contexto = {
        "_target_from_params": lambda *_: "pc_a",
        "falar_com_lipsync": lambda fala, *_: falas.append(fala),
        "_pendencia_acao_runtime": pendencia,
        "episodio_emocional": evento,
        "current_emotion": "brava",
        "emotion_level": 3,
        "resistencia_p17_ref": evento["evidencia_ref"] if ja_resistiu else "",
        "registrar_resistencia_p17": lambda _ref: registro_aceito,
        "turno_atual": {"autoriza_execucao": True},
    }
    retorno = roteador.executar_intencao(pedido, texto, contexto)
    return pedido, retorno, pendencia.obter(), falas, chamadas


def test_pedido_explicitamente_opcional_pode_resistir_uma_vez_com_fala_e_pendencia(monkeypatch) -> None:
    pedido, retorno, pendencia, falas, chamadas = _executar_sem_efeito(
        monkeypatch, "alterna a repetição. É opcional.", evento=_evento(),
    )

    assert retorno is True
    assert chamadas == []
    assert len(falas) == 1
    assert "repetição" in falas[0].casefold()
    assert pendencia is not None
    assert pendencia["origem"] == "resistencia_personalidade"
    assert pendencia["metadados"]["acao"] == "repeat_toggle"
    tratamento = interpretar_tratamento_operacional(pedido, retorno)
    assert tratamento.tratado is True
    assert tratamento.executou is False
    assert tratamento.status == "aguardando_insistencia"


@pytest.mark.parametrize("texto", [
    "alterna a repetição. É opcional, mas preciso disso agora.",
    "alterna a repetição. É opcional por segurança.",
    "alterna a repetição. É opcional para acessibilidade.",
    "alterna a repetição agora, é urgente.",
])
def test_necessidade_segurança_e_acessibilidade_preservam_execucao(monkeypatch, texto: str) -> None:
    _, _, pendencia, falas, chamadas = _executar_sem_efeito(
        monkeypatch, texto, evento=_evento(),
    )

    assert pendencia is None
    assert falas == []
    assert "integracoes" in chamadas


def test_causa_invalida_ou_resistencia_anterior_preserva_execucao(monkeypatch) -> None:
    for evento, ja_resistiu in (
        (_evento(responsabilidade="sistema"), False),
        (_evento(idade_s=90.0), False),
        (_evento(), True),
    ):
        _, _, pendencia, falas, chamadas = _executar_sem_efeito(
            monkeypatch, "alterna a repetição. É opcional.",
            evento=evento, ja_resistiu=ja_resistiu,
        )
        assert pendencia is None
        assert falas == []
        assert "integracoes" in chamadas


def test_causa_trocada_antes_do_registro_nao_retém_pedido(monkeypatch) -> None:
    _, _, pendencia, falas, chamadas = _executar_sem_efeito(
        monkeypatch, "alterna a repetição. É opcional.", evento=_evento(),
        registro_aceito=False,
    )
    assert pendencia is None
    assert falas == []
    assert "integracoes" in chamadas


def test_turno_com_veto_ou_evento_malformado_nao_resiste() -> None:
    base = {
        "intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle"},
        "texto_usuario": "alterna a repetição. É opcional.",
        "estado_emocional": {
            "current_emotion": "brava", "emotion_level": 3,
            "episodio_emocional": _evento(),
        },
        "turno": {"autoriza_execucao": True, "veto_execucao_operacional": True},
    }
    assert avaliar_resistencia_contextual(**base).resistir is False
    base["turno"] = {"autoriza_execucao": True}
    base["estado_emocional"]["episodio_emocional"] = "evento malformado"
    assert avaliar_resistencia_contextual(**base).resistir is False


def test_verbo_de_ativacao_nao_elegivel_ao_toggle(monkeypatch) -> None:
    _, _, pendencia, falas, chamadas = _executar_sem_efeito(
        monkeypatch, "ativa a repetição. É opcional.", evento=_evento(),
    )
    assert pendencia is None
    assert falas == []
    assert "integracoes" in chamadas


def test_novo_comando_direto_substitui_pendencia_sem_toggle_posterior(monkeypatch) -> None:
    _, _, _item, _, _ = _executar_sem_efeito(
        monkeypatch, "alterna a repetição. É opcional.", evento=_evento(),
    )
    pendencia = _pendencia_real()
    pendencia.registrar(
        origem="resistencia_personalidade", acao="retomar_controle_midia",
        pergunta="Quer que eu altere a repetição?", referencia="evidencia-1",
        dominio="musica", metadados={
            "intent": "MEDIA_CONTROL", "acao": "repeat_toggle",
            "evento_ref": "evidencia-1",
            "pedido": {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle", "target": "pc_a"}},
        },
    )
    pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle"}}
    contexto = {
        "_target_from_params": lambda *_: "pc_a",
        "_pendencia_acao_runtime": pendencia,
        "falar_com_lipsync": lambda *_: None,
        "turno_atual": {"autoriza_execucao": True},
    }
    assert roteador.executar_intencao(pedido, "alterna a repetição agora", contexto) is True
    assert pendencia.obter() is None
    comandos = ComandosImediatosRuntime(namespace_getter=lambda: contexto, loop_getter=lambda: None)
    assert comandos._processar_resistencia_pendente("sim", contexto, {}) is False


def test_mencao_sem_autorizacao_nao_consume_confirmacao_pendente(monkeypatch) -> None:
    _executar_sem_efeito(
        monkeypatch, "alterna a repetição. É opcional.", evento=_evento(),
    )
    pendencia = _pendencia_real()
    pendencia.registrar(
        origem="resistencia_personalidade", acao="retomar_controle_midia",
        pergunta="Quer que eu altere a repetição?", referencia="evidencia-1",
        dominio="musica", metadados={
            "intent": "MEDIA_CONTROL", "acao": "repeat_toggle", "evento_ref": "evidencia-1",
            "pedido": {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle", "target": "pc_a"}},
        },
    )
    pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle"}}
    roteador.executar_intencao(
        pedido, "e se eu alternar a repetição?", {
            "_target_from_params": lambda *_: "pc_a",
            "_pendencia_acao_runtime": pendencia,
            "turno_atual": {
                "autoriza_execucao": False, "veto_execucao_operacional": True,
            },
        },
    )
    assert pendencia.obter() is not None


def test_confirmacao_em_processamento_impede_segundo_toggle(monkeypatch) -> None:
    chamadas: list[str] = []
    falas: list[str] = []
    for nome in (
        "janelas", "navegador", "audio", "agenda", "informacoes", "sistema",
        "musical", "playlists", "cancelamentos", "integracoes",
    ):
        def despachar(*_args, _nome=nome, **_kwargs):
            chamadas.append(_nome)
            return ResultadoDespacho.nao_tratado()
        monkeypatch.setattr(roteador, f"_executar_intencao_{nome}", despachar)
    pendencia = _pendencia_real()
    pendencia.registrar(
        origem="resistencia_personalidade", acao="retomar_controle_midia",
        pergunta="Quer que eu altere a repetição?", referencia="evidencia-1",
        dominio="musica", metadados={
            "intent": "MEDIA_CONTROL", "acao": "repeat_toggle", "evento_ref": "evidencia-1",
            "pedido": {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle", "target": "pc_a"}},
        },
    )
    assert pendencia.resolver("sim")["status"] == "aceitar"
    pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle"}}
    retorno = roteador.executar_intencao(
        pedido, "alterna a repetição", {
            "_target_from_params": lambda *_: "pc_a",
            "_pendencia_acao_runtime": pendencia,
            "falar_com_lipsync": lambda fala, *_: falas.append(fala),
            "turno_atual": {"autoriza_execucao": True},
        },
    )
    assert retorno is True
    assert chamadas == []
    assert len(falas) == 1
    assert pendencia.obter()["status"] == "em_processamento"


def test_detector_real_classifica_frase_de_alternancia_opcional() -> None:
    resultado = detectar_volume_ou_midia(
        "alterna a repetição. é opcional.", params_cb=lambda **campos: campos,
    )
    assert resultado == {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle"}}


@pytest.mark.parametrize("texto", [
    "alterna a repetição", "alterna a repetição. É opcional.",
    "alterna a repetição. É opcional, mas preciso disso agora.",
    "alterna a repetição. É opcional por segurança.",
    "alterna a repetição. É opcional para acessibilidade.",
    "alterna a repetição por segurança",
    "alterna a repetição para acessibilidade",
    "alterna a repetição agora",
    "alterna a repetição agora, é urgente.",
])
def test_pedido_direto_de_alternancia_tem_autoridade_antes_da_personalidade(texto: str) -> None:
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is True
    assert turno["modalidade"] == "comando"


@pytest.mark.parametrize("texto", [
    "e se eu alternar a repetição?",
    "alterna a repetição?",
    "não alterna a repetição",
    "ela alterna a repetição",
    "alterna a repetição. Não quero que faça isso.",
    "alterna a repetição se eu pedir depois",
])
def test_mencoes_de_alternancia_nao_autorizam_controle(texto: str) -> None:
    assert classificar_modalidade_turno(texto)["autoriza_execucao"] is False


def _continuidade_resistencia(params_pendentes: dict | None = None):
    pendencia = _pendencia_real()
    pendencia.registrar(
        origem="resistencia_personalidade",
        acao="retomar_controle_midia",
        pergunta="Quer que eu ative a repetição mesmo assim?",
        referencia="evidencia-1",
        dominio="musica",
        metadados={
            "intent": "MEDIA_CONTROL", "acao": "repeat_toggle",
            "evento_ref": "evidencia-1", "sobrevive_comando_independente": True,
            "pedido": {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle", "target": "pc_a", **dict(params_pendentes or {})}},
        },
        ttl_s=90,
    )
    falas: list[str] = []
    despachos: list[dict] = []

    def executar(pedido, texto):
        despachos.append({"pedido": dict(pedido), "texto": texto})
        marcar_tratamento_operacional(
            pedido, tratado=True, executou=True, confirmado=True,
            status="confirmado", resultado_publicado=True, retorno_legado=True,
        )
        return True

    ns = {
        "_pendencia_acao_runtime": pendencia,
        "falar_com_lipsync": lambda fala, *_: falas.append(fala),
        "executar_intencao": executar,
    }
    comandos = ComandosImediatosRuntime(namespace_getter=lambda: ns, loop_getter=lambda: None)
    return comandos, ns, pendencia, falas, despachos


def test_insistencia_consumida_pela_pendencia_executa_uma_vez_pelo_contrato_normal() -> None:
    comandos, ns, pendencia, falas, despachos = _continuidade_resistencia()
    assert comandos._processar_resistencia_pendente("sim, pode", ns, {}) is True
    assert len(despachos) == 1
    assert despachos[0]["pedido"]["params"] == {"acao": "repeat_toggle", "target": "pc_a"}
    assert pendencia.obter() is None
    assert falas == []


@pytest.mark.parametrize("params,texto,destino_esperado", [
    ({"acao": "repeat_toggle", "target": "pc_b"}, "alterna a repetição. É opcional.", "pc_b"),
    ({"acao": "repeat_toggle", "target": "ambos"}, "alterna a repetição. É opcional.", "ambos"),
    ({"acao": "repeat_toggle"}, "alterna a repetição no PC B. É opcional.", "pc_b"),
    ({"acao": "repeat_toggle", "platform": "music"}, "alterna a repetição. É opcional.", "pc_a"),
])
def test_resistencia_preserva_destino_resolvido_e_player_ate_o_aceite(
    monkeypatch, params: dict, texto: str, destino_esperado: str,
) -> None:
    resolver = DestinoPCRuntime(normalizar_texto=normalizar_texto_basico).resolver
    pendencias = _pendencia_real()
    evento = _evento()
    falas: list[str] = []
    despachos: list[dict] = []
    for nome in (
        "janelas", "navegador", "audio", "agenda", "informacoes", "sistema",
        "musical", "playlists", "cancelamentos", "integracoes",
    ):
        monkeypatch.setattr(
            roteador, f"_executar_intencao_{nome}",
            lambda *_args, **_kwargs: ResultadoDespacho.nao_tratado(),
        )
    ns = {
        "_target_from_params": resolver,
        "_pendencia_acao_runtime": pendencias,
        "episodio_emocional": evento,
        "current_emotion": "brava", "emotion_level": 3,
        "registrar_resistencia_p17": lambda _ref: True,
        "turno_atual": {"autoriza_execucao": True},
        "falar_com_lipsync": lambda fala, *_: falas.append(fala),
    }
    original = {"intent": "MEDIA_CONTROL", "params": dict(params), "id_solicitacao": "origem-adiada"}
    assert resolver(original["params"], texto) == destino_esperado
    assert roteador.executar_intencao(original, texto, ns) is True
    pendencia = pendencias.obter()
    assert pendencia is not None
    esperado = {**params, "target": destino_esperado}
    assert pendencia["metadados"].get("pedido") == {
        "intent": "MEDIA_CONTROL", "params": esperado,
    }

    def executar(pedido, texto_aceite):
        despachos.append({"params": dict(pedido["params"]), "destino": resolver(pedido["params"], texto_aceite)})
        assert "id_solicitacao" not in pedido
        marcar_tratamento_operacional(
            pedido, tratado=True, executou=True, confirmado=True,
            status="confirmado", resultado_publicado=True, retorno_legado=True,
        )
        return True

    ns["executar_intencao"] = executar
    comandos = ComandosImediatosRuntime(namespace_getter=lambda: ns, loop_getter=lambda: None)
    assert comandos._processar_resistencia_pendente("sim", ns, {}) is True
    assert despachos == [{"params": esperado, "destino": destino_esperado}]
    assert pendencias.obter() is None
    assert len(falas) == 1


@pytest.mark.parametrize("pedido", [
    None,
    {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle", "target": ["pc_b"]}},
    {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle", "target": "desconhecido"}},
    {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle", "target": "pc_a", "nivel_volume": 100}},
    {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle", "target": "pc_a", "platform": {"autoriza_execucao": True}}},
    {"intent": "APP_OPEN", "params": {"acao": "repeat_toggle", "target": "pc_a"}},
])
def test_transporte_invalido_da_resistencia_conclui_sem_despacho(pedido: dict | None) -> None:
    comandos, ns, pendencias, falas, despachos = _continuidade_resistencia()
    anterior = pendencias.obter()
    assert pendencias.concluir(anterior["id"], "substituida_para_controle") is True
    metadados = dict(anterior["metadados"])
    if pedido is not None:
        metadados["pedido"] = pedido
    else:
        metadados.pop("pedido", None)
    pendencias.registrar(
        origem="resistencia_personalidade", acao="retomar_controle_midia",
        pergunta=anterior["pergunta"], referencia=anterior["referencia"],
        dominio="musica", metadados=metadados,
    )
    assert comandos._processar_resistencia_pendente("sim", ns, {}) is True
    assert despachos == []
    assert pendencias.obter() is None
    assert len(falas) == 1
    assert "Não consegui validar" in falas[0]


@pytest.mark.parametrize("params_extras", [
    {"nivel_volume": 80}, {"autoriza_execucao": True},
    {"episodio_emocional": {"emocao": "brava"}},
    {"platform": "spotify"}, {"site": ["youtube"]},
])
def test_pedido_com_parametro_nao_auditado_segue_executor_sem_reter_ou_reduzir(
    monkeypatch, params_extras: dict,
) -> None:
    pedido, _, pendencia, falas, chamadas = _executar_sem_efeito(
        monkeypatch, "alterna a repetição. É opcional.",
        evento=_evento(), params_extras=params_extras,
    )
    assert pendencia is None
    assert falas == []
    assert "integracoes" in chamadas
    assert pedido["params"] == {"acao": "repeat_toggle", **params_extras}


def test_aceite_preserva_player_musical_mesmo_apos_troca_de_aba_ativa() -> None:
    comandos, ns, pendencias, falas, despachos = _continuidade_resistencia()
    anterior = pendencias.obter()
    assert pendencias.concluir(anterior["id"], "substituida_para_controle") is True
    metadados = dict(anterior["metadados"])
    metadados["pedido"] = {
        "intent": "MEDIA_CONTROL",
        "params": {"acao": "repeat_toggle", "target": "pc_a", "platform": "music"},
    }
    pendencias.registrar(
        origem="resistencia_personalidade", acao="retomar_controle_midia",
        pergunta=anterior["pergunta"], referencia=anterior["referencia"],
        dominio="musica", metadados=metadados,
    )
    chamadas: list[str] = []

    def chrome(command, **_kwargs):
        chamadas.append("player_musical:" + command)
        return {"ok": True, "confirmado": True, "status": "confirmado"}

    ctx = {
        "_registro_navegador_operacoes_runtime": SimpleNamespace(controlar_youtube_detalhado=chrome),
        "_registro_navegador_leitura_runtime": SimpleNamespace(
            aba_ativa=lambda: {"url": "https://www.primevideo.com/watch/exemplo", "tabId": 8},
        ),
        "_executar_controle_midia_nativo": lambda cmd: chamadas.append("midia_global:" + cmd),
    }

    def executar(pedido, texto):
        return executar_media_control(
            pedido["params"], texto, "pc_a", ctx,
            marcar_resultado=lambda status, executou, **kwargs: marcar_tratamento_operacional(
                pedido, tratado=True, executou=executou, confirmado=kwargs.get("confirmado"),
                status=status, resultado_publicado=True, retorno_legado=bool(executou),
            ),
            falar_por_status=lambda *_args, **_kwargs: None, ctx_fala=lambda: {},
        )

    ns["executar_intencao"] = executar
    assert comandos._processar_resistencia_pendente("sim", ns, {}) is True
    assert chamadas == ["player_musical:repeat_toggle"]
    assert pendencias.obter() is None
    assert falas == []
    assert despachos == []


def _executar_novo_controle_sobre_pendencia(
    monkeypatch, params: dict, *, processando: bool = False, params_pendentes: dict | None = None,
):
    comandos, ns, pendencias, falas, despachos = _continuidade_resistencia(params_pendentes)
    if processando:
        assert pendencias.resolver("sim")["status"] == "aceitar"
    anterior = pendencias.obter()
    chamadas: list[str] = []
    for nome in (
        "janelas", "navegador", "audio", "agenda", "informacoes", "sistema",
        "musical", "playlists", "cancelamentos", "integracoes",
    ):
        def despachar(*_args, _nome=nome, **_kwargs):
            chamadas.append(_nome)
            return ResultadoDespacho.concluido() if _nome == "integracoes" else ResultadoDespacho.nao_tratado()
        monkeypatch.setattr(roteador, f"_executar_intencao_{nome}", despachar)
    resolver = DestinoPCRuntime(normalizar_texto=normalizar_texto_basico).resolver
    ns.update(_target_from_params=resolver, turno_atual={"autoriza_execucao": True})
    retorno = roteador.executar_intencao(
        {"intent": "MEDIA_CONTROL", "params": dict(params)}, "alterna a repetição agora", ns,
    )
    return retorno, anterior, pendencias, falas, chamadas, comandos, ns, despachos


@pytest.mark.parametrize("params", [
    {"acao": "repeat_toggle", "target": "pc_b"},
    {"acao": "repeat_toggle", "target": "ambos"},
    {"acao": "repeat_toggle", "platform": "music"},
])
@pytest.mark.parametrize("processando", [False, True])
def test_novo_controle_em_outro_destino_ou_player_preserva_pendencia_e_executa(
    monkeypatch, params: dict, processando: bool,
) -> None:
    retorno, anterior, pendencias, falas, chamadas, *_ = _executar_novo_controle_sobre_pendencia(
        monkeypatch, params, processando=processando,
    )
    assert pendencias.obter() == anterior
    assert retorno is True
    assert "integracoes" in chamadas
    assert falas == []


def test_novo_controle_do_mesmo_destino_e_player_substitui_somente_oferta_ativa(monkeypatch) -> None:
    retorno, _, pendencias, falas, chamadas, comandos, ns, despachos = _executar_novo_controle_sobre_pendencia(
        monkeypatch, {"acao": "repeat_toggle", "target": "pc_a"},
    )
    assert pendencias.obter() is None
    assert retorno is True
    assert "integracoes" in chamadas
    assert falas == []
    assert comandos._processar_resistencia_pendente("sim", ns, {}) is False
    assert despachos == []


@pytest.mark.parametrize("pendente,novo", [
    ({"platform": "music"}, {"site": "youtube"}),
    ({"site": "musica"}, {"platform": "youtube_music"}),
    ({"platform": "youtube"}, {"platform": " MÚSICA "}),
])
@pytest.mark.parametrize("processando", [False, True])
def test_alias_do_mesmo_player_preserva_substituicao_e_protecao_concorrente(
    monkeypatch, pendente: dict, novo: dict, processando: bool,
) -> None:
    retorno, anterior, pendencias, falas, chamadas, *_ = _executar_novo_controle_sobre_pendencia(
        monkeypatch, {"acao": "repeat_toggle", **novo},
        processando=processando, params_pendentes=pendente,
    )
    assert retorno is True
    if processando:
        assert pendencias.obter() == anterior
        assert chamadas == []
        assert len(falas) == 1
    else:
        assert pendencias.obter() is None
        assert "integracoes" in chamadas
        assert falas == []


@pytest.mark.parametrize("origem_b,acao_b", [
    ("resistencia_personalidade", "retomar_controle_midia"),
    ("agenda", "criar_lembrete"),
])
@pytest.mark.parametrize("texto", ["sim", "mostra minhas playlists"])
def test_aceite_vinculado_a_oferta_observada_nao_consume_pendencia_trocada(
    origem_b: str, acao_b: str, texto: str,
) -> None:
    comandos, ns, pendencias, falas, despachos = _continuidade_resistencia()
    anterior = pendencias.obter()

    class TrocaDuranteResolver:
        def obter(self):
            return pendencias.obter()

        def concluir(self, *args, **kwargs):
            return pendencias.concluir(*args, **kwargs)

        def resolver(self, texto, **kwargs):
            assert pendencias.concluir(anterior["id"], "substituida_por_novo_pedido", status_esperado="ativa") is True
            pendencias.registrar(
                origem=origem_b, acao=acao_b, pergunta="Executar outro pedido?",
                referencia="evidencia-2", dominio="musica" if origem_b == "resistencia_personalidade" else "agenda",
                metadados={
                    "intent": "MEDIA_CONTROL", "acao": "repeat_toggle", "evento_ref": "evidencia-2",
                    "pedido": {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle", "target": "pc_b"}},
                },
            )
            return pendencias.resolver(texto, **kwargs)

    ns["_pendencia_acao_runtime"] = TrocaDuranteResolver()
    retorno = comandos._processar_resistencia_pendente(texto, ns, {})
    if texto != "sim":
        assert retorno is False
        assert pendencias.obter() == anterior
        assert despachos == []
        assert falas == []
        return
    assert retorno is True
    assert despachos == []
    assert len(falas) == 1
    assert pendencias.obter()["origem"] == origem_b
    assert pendencias.obter()["status"] == "ativa"
    assert pendencias.obter()["referencia"] == "evidencia-2"


def test_recusa_e_comando_independente_nao_executam_controle() -> None:
    comandos, ns, pendencia, falas, despachos = _continuidade_resistencia()
    assert comandos._processar_resistencia_pendente("mostra minhas playlists", ns, {}) is False
    assert pendencia.obter() is not None
    assert comandos._processar_resistencia_pendente("não", ns, {}) is True
    assert pendencia.obter() is None
    assert despachos == []
    assert len(falas) == 1


def test_veto_de_turno_preserva_pendencia_sem_efeito() -> None:
    comandos, ns, pendencia, falas, despachos = _continuidade_resistencia()
    assert comandos._processar_resistencia_pendente(
        "sim", ns, {"veto_execucao_operacional": True},
    ) is False
    assert pendencia.obter() is not None
    assert despachos == []
    assert falas == []


def test_comando_independente_passa_enquanto_aceite_esta_em_processamento() -> None:
    comandos, ns, pendencia, falas, despachos = _continuidade_resistencia()
    assert pendencia.resolver("sim")["status"] == "aceitar"
    assert comandos._processar_resistencia_pendente(
        "mostra minhas playlists", ns, {},
    ) is False
    assert pendencia.obter()["status"] == "em_processamento"
    assert falas == []
    assert despachos == []


def test_executor_indisponivel_encerra_pendencia_e_comunica_falha() -> None:
    comandos, ns, pendencia, falas, despachos = _continuidade_resistencia()
    ns.pop("executar_intencao")
    assert comandos._processar_resistencia_pendente("sim", ns, {}) is True
    assert pendencia.obter() is None
    assert despachos == []
    assert "Não consegui" in falas[0]


def test_composicao_instalada_publica_causa_e_consume_insistencia(tmp_path: Path) -> None:
    codigo = textwrap.dedent(r'''
        import json
        import os
        import sys
        import time
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.integracao import instancia_unica

        inicializar = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho, *a, **k: inicializar(
            self, os.path.join(os.environ["LAYLAY_SONDA_SQLITE"], os.path.basename(caminho)), *a, **k,
        )
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda identificador, **kwargs: adquirir(
            str(identificador) + ".p17-resistencia-" + str(os.getpid()), **kwargs,
        )
        import laylay as root
        import mente_laylay.autonomia.roteador_intencao as roteador
        from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
        from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
        from mente_laylay.memoria_mental.resultado_acao import marcar_tratamento_operacional

        estado = root._estado_compartilhado_runtime
        evento = criar_evento_emocional_causal(
            origem="resultado_operacional", causa="repetição redundante observada",
            evidencia_ref="p17-composicao-1", natureza_evidencia="fato_observado",
            responsabilidade="usuario", confianca=0.96, relevancia=0.95,
            novidade=0.2, intensidade=3, sensibilidade="normal", alvo="Calculadora",
            validade_s=45.0, permite_expressao=True, emocao="brava", nivel=3,
            arco="bronca_brincalhona", ts=time.time(),
        )
        estado.substituir("conversacional", {
            **dict(estado.conversacional), "current_emotion": "brava",
            "emotion_level": 3, "episodio_emocional": evento,
        })
        falas = []
        root.falar_com_lipsync = lambda fala, *_: falas.append(fala)
        root._iniciar_planejamento_turno(
            "alterna a repetição. É opcional.", origem="teste_p17_resistencia",
        )
        ctx = root._contexto_intencao_runtime.montar()
        porta_legada_presente = "_bloqueio_por_emocao" in ctx
        ctx["falar_com_lipsync"] = root.falar_com_lipsync
        detectada = root.detectar_intencao_deterministica("alterna a repetição. É opcional.")
        for nome in (
            "janelas", "navegador", "audio", "agenda", "informacoes", "sistema",
            "musical", "playlists", "cancelamentos", "integracoes",
        ):
            setattr(roteador, f"_executar_intencao_{nome}", lambda *a, **k: ResultadoDespacho.nao_tratado())
        root._composicao_entrada_interacao_runtime._servicos_interacao["executar_intencao"] = (
            lambda pedido, texto: roteador.executar_intencao(
                pedido, texto, {
                    **root._contexto_intencao_runtime.montar(),
                    "falar_com_lipsync": root.falar_com_lipsync,
                },
            )
        )
        turno_inicial = dict(estado.mental.get("turno_atual") or {})
        aguardando = root._processar_comandos_prioritarios("alterna a repetição. É opcional.")
        pendente = root._pendencia_acao_runtime.obter()
        primeira_ref_no_estado = estado.mental.get("resistencia_p17_ref")
        chamadas = []
        def executar(pedido, texto):
            chamadas.append((pedido["intent"], pedido["params"], texto))
            marcar_tratamento_operacional(
                pedido, tratado=True, executou=True, confirmado=True,
                status="confirmado", resultado_publicado=True, retorno_legado=True,
            )
            return True
        root._composicao_entrada_interacao_runtime._servicos_interacao["executar_intencao"] = executar
        root._iniciar_planejamento_turno("sim", origem="teste_p17_resistencia")
        insistencia = root._processar_comandos_prioritarios("sim")
        falas_apos_insistencia = len(falas)
        estado.substituir("conversacional", {
            **dict(estado.conversacional),
            "episodio_emocional": {**evento, "evidencia_ref": "p17-outro-evento"},
        })
        contexto_outro_evento = root._contexto_intencao_runtime.montar()
        registro_antigo_recusado = ctx["registrar_resistencia_p17"]("p17-outro-evento")
        outro_registro = contexto_outro_evento["registrar_resistencia_p17"]("p17-outro-evento")
        estado.substituir("conversacional", {
            **dict(estado.conversacional), "episodio_emocional": evento,
        })
        ctx_atualizado = root._contexto_intencao_runtime.montar()
        ctx_atualizado["falar_com_lipsync"] = root.falar_com_lipsync
        segunda_vez = roteador.executar_intencao(
            {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle"}},
            "alterna a repetição. É opcional.", ctx_atualizado,
        )
        transportes = []
        for destino in ("pc_a", "pc_b", "ambos"):
            estado.substituir("conversacional", {
                **dict(estado.conversacional),
                "episodio_emocional": {**evento, "evidencia_ref": "p17-destino-" + destino},
            })
            root._iniciar_planejamento_turno(
                "alterna a repetição. É opcional.", origem="teste_p17_transporte",
            )
            contexto_destino = root._contexto_intencao_runtime.montar()
            contexto_destino["falar_com_lipsync"] = root.falar_com_lipsync
            pediu = roteador.executar_intencao(
                {"intent": "MEDIA_CONTROL", "params": {
                    "acao": "repeat_toggle", "target": destino, "platform": "music",
                }},
                "alterna a repetição. É opcional.", contexto_destino,
            )
            item = root._pendencia_acao_runtime.obter()
            chamadas_antes = len(chamadas)
            root._iniciar_planejamento_turno("sim", origem="teste_p17_transporte")
            confirmou = root._processar_comandos_prioritarios("sim")
            chamada = chamadas[-1] if len(chamadas) > chamadas_antes else None
            transportes.append({
                "destino": destino, "pediu": pediu, "confirmou": confirmou,
                "pedido_pendente": (item or {}).get("metadados", {}).get("pedido"),
                "chamada": chamada,
                "destino_retomado": root._target_from_params(chamada[1], chamada[2]) if chamada else None,
            })
        saida = {
            "causa_no_contexto": ctx["episodio_emocional"].get("evidencia_ref"),
            "detectada": detectada,
            "turno_inicial": {
                "autoriza_execucao": turno_inicial.get("autoriza_execucao"),
                "modalidade": turno_inicial.get("modalidade"),
                "motivo": turno_inicial.get("motivo"),
            },
            "aguardando": aguardando,
            "pendencia": (pendente or {}).get("origem"),
            "ref_no_estado": primeira_ref_no_estado,
            "falas_apos_insistencia": falas_apos_insistencia,
            "falas": falas, "insistencia": insistencia,
            "chamadas": chamadas,
            "pendencia_final": root._pendencia_acao_runtime.obter(),
            "outro_registro": outro_registro,
            "registro_antigo_recusado": registro_antigo_recusado,
            "porta_legada_presente": porta_legada_presente,
            "segunda_vez": segunda_vez,
            "resistencia_repetida": root._pendencia_acao_runtime.obter(),
            "transportes": transportes,
        }
        sys.__stdout__.write("P17_RESISTENCIA " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_SONDA_SQLITE=str(tmp_path)),
        capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert processo.returncode == 0, processo.stderr[-4000:]
    saida = next(
        json.loads(linha.removeprefix("P17_RESISTENCIA "))
        for linha in processo.stdout.splitlines()
        if linha.startswith("P17_RESISTENCIA ")
    )
    assert saida["causa_no_contexto"] == "p17-composicao-1"
    assert saida["detectada"]["intent"] == "MEDIA_CONTROL"
    assert saida["detectada"]["params"]["acao"] == "repeat_toggle"
    assert saida["turno_inicial"]["autoriza_execucao"] is True
    assert saida["aguardando"] is True, json.dumps(saida, ensure_ascii=False)
    assert saida["pendencia"] == "resistencia_personalidade"
    assert saida["ref_no_estado"] == "p17-composicao-1"
    assert saida["falas_apos_insistencia"] == 1
    assert saida["insistencia"] is True
    assert saida["chamadas"][0] == ["MEDIA_CONTROL", {"acao": "repeat_toggle", "target": "pc_a"}, "sim"]
    assert saida["pendencia_final"] is None
    assert saida["outro_registro"] is True
    assert saida["porta_legada_presente"] is False
    assert saida["registro_antigo_recusado"] is False
    assert saida["resistencia_repetida"] is None
    assert sum("Vou segurar essa mudança" in fala for fala in saida["falas"]) == 4
    assert len(saida["chamadas"]) == 4
    for transporte in saida["transportes"]:
        destino = transporte["destino"]
        esperado = {"acao": "repeat_toggle", "target": destino, "platform": "music"}
        assert transporte["pediu"] is True
        assert transporte["pedido_pendente"] == {"intent": "MEDIA_CONTROL", "params": esperado}
        assert transporte["confirmou"] is True
        assert transporte["chamada"] == ["MEDIA_CONTROL", esperado, "sim"]
        assert transporte["destino_retomado"] == destino

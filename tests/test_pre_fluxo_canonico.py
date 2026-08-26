from __future__ import annotations

import inspect

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.feedback_pendente_runtime import FeedbackPendenteRuntime
from mente_laylay.autonomia.fluxo_resposta_ia import (
    CATEGORIAS_PRE_FLUXO_PERMITIDAS,
    ETAPAS_PRE_FLUXO_AUDITADAS,
    processar_inicio_fluxo_resposta_ia,
)
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime


def test_pre_fluxo_declara_somente_continuidade_pendencia_confirmacao_protecao() -> None:
    categorias = {categoria for _nome, categoria in ETAPAS_PRE_FLUXO_AUDITADAS}

    assert categorias <= CATEGORIAS_PRE_FLUXO_PERMITIDAS
    assert categorias == {
        "confirmacao", "continuidade", "pendencia", "protecao",
    }
    assert len(ETAPAS_PRE_FLUXO_AUDITADAS) == len({
        nome for nome, _categoria in ETAPAS_PRE_FLUXO_AUDITADAS
    })


def test_pre_fluxo_nao_executa_comando_novo() -> None:
    execucoes: list[str] = []
    contexto = {
        "mente_integrada_estado": {
            "turno_atual": {
                "modalidade_geral": "comando",
                "ato_principal": "comando",
                "autoriza_execucao": True,
            },
            "pendencia_atual": {},
        },
        "_refinar_contexto_mental": lambda _texto: {},
        "processar_comando_deterministico": (
            lambda texto, *_args: execucoes.append(texto) or True
        ),
    }
    contexto["_recarregar_contexto_inicio"] = lambda: dict(contexto)

    assert processar_inicio_fluxo_resposta_ia(contexto, "liga a luz") is False
    assert execucoes == []


def test_resposta_principal_nao_possui_segunda_fase_imediata() -> None:
    fonte = inspect.getsource(RespostaIARuntime._processar_serializado)

    assert "processar_comandos_imediatos" not in fonte
    assert "tratado_imediato" not in fonte


def test_identidade_confirmada_foi_migrada_para_fase_prioritaria() -> None:
    falas: list[str] = []
    salvos: list[str] = []

    class Estado:
        mental = {"turno_atual": {"id": "turno-identidade"}}

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": Estado(),
            "_normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
            "_salvar_identidade_usuario": (
                lambda nome, _texto: salvos.append(nome) or True
            ),
            "_emitir_resposta_curta": (
                lambda _entrada, fala, **_kwargs: falas.append(fala) or True
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("meu nome é Marina") is True
    assert salvos == ["Marina"]
    assert falas and "Marina" in falas[0]


def test_pedido_musical_novo_foi_migrado_para_fase_prioritaria() -> None:
    pedidos: list[str] = []

    class Estado:
        mental = {"turno_atual": {"id": "turno-musica"}}

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": Estado(),
            "_texto_pede_direcao_musical_generica": lambda _texto: True,
            "_responder_pedido_direcao_musical_generica": (
                lambda texto: pedidos.append(texto) or True
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("me recomenda uma música") is True
    assert pedidos == ["me recomenda uma música"]


def test_feedback_misto_reentra_pelo_coordenador_natural() -> None:
    resolucoes: list[tuple[str, str]] = []
    execucoes: list[tuple[dict, str]] = []
    registros: list[tuple[tuple, dict]] = []
    contexto = {
        "normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
        "handle_feedback_pendente": lambda _ctx, _texto: True,
        "resolver_comando_natural": lambda texto, origem: (
            resolucoes.append((texto, origem))
            or ({"intent": "IOT_CONTROL", "params": {"acao": "ligar"}}, "contexto")
        ),
        "executar_intencao": (
            lambda intencao, texto: execucoes.append((intencao, texto)) or True
        ),
        "registrar_resultado_execucao": (
            lambda *args, **kwargs: registros.append((args, kwargs))
        ),
        "processar_comandos_imediatos": lambda _texto: (_ for _ in ()).throw(
            AssertionError("a camada imediata antiga não pode ser chamada")
        ),
    }
    runtime = FeedbackPendenteRuntime(
        contexto_getter=lambda: contexto,
        log=lambda *_args: None,
    )

    assert runtime.handle_feedback_pendente_misto("sim e liga a luz") is True
    assert resolucoes == [("liga a luz", "feedback-pendente-misto")]
    assert execucoes == [(
        {"intent": "IOT_CONTROL", "params": {"acao": "ligar"}},
        "liga a luz",
    )]
    assert registros and registros[0][1]["origem"] == "feedback_misto:contexto"

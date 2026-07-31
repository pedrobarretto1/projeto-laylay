from __future__ import annotations

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_cancelamentos import (
    DependenciasExecutorCancelamentos,
    executar_intencao_cancelamentos,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao


def _dependencias(eventos: list[tuple]) -> DependenciasExecutorCancelamentos:
    return DependenciasExecutorCancelamentos(
        marcar_resultado=lambda status, **kwargs: eventos.append(
            ("resultado", status, kwargs)
        )
    )


def test_executor_cancelamentos_ignora_outro_dominio() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_cancelamentos(
        "PLAYLIST_PLAY", {}, _dependencias(eventos)
    )

    assert despacho == ResultadoDespacho.nao_tratado()
    assert eventos == []


def test_stop_playlist_bloqueia_com_duracao_padrao_sem_limpar_pendencias() -> None:
    bloqueios: list[tuple] = []
    atualizacoes: list[dict] = []
    eventos: list[tuple] = []

    despacho = executar_intencao_cancelamentos(
        "STOP_PLAYLIST_CONTEXT",
        {
            "_bloquear_playlist_temporariamente": lambda *args: bloqueios.append(args),
            "update_continuidades": lambda **campos: atualizacoes.append(campos),
            "falar_com_lipsync": lambda *_args: None,
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert bloqueios == [()]
    assert atualizacoes == []
    assert eventos == [
        ("resultado", "playlist_contexto_bloqueado", {})
    ]


def test_cancelar_limpa_memoria_compartilhada_em_uma_atualizacao() -> None:
    bloqueios: list[float] = []
    atualizacoes: list[dict] = []
    eventos: list[tuple] = []
    ctx = {
        "_bloquear_playlist_temporariamente": bloqueios.append,
        "update_continuidades": lambda **campos: atualizacoes.append(campos),
        "_playlist_sugestao_pendente": {"playlist": "rock"},
        "_rotina_sugestao_pendente": {"rotina": "noite"},
        "comando_sugerido": "desligar luz",
        "comando_sugerido_payload": {"intent": "IOT_CONTROL"},
        "comando_sugerido_estado": "OFFERED",
        "comando_sugerido_ts": 42.0,
        "comando_pendente": "desligar luz",
        "comando_pendente_payload": {"intent": "IOT_CONTROL"},
        "falar_com_lipsync": lambda *_args: None,
    }

    despacho = executar_intencao_cancelamentos(
        "CANCELAR_ACAO", ctx, _dependencias(eventos)
    )

    assert despacho == ResultadoDespacho.concluido()
    assert bloqueios == [0.0]
    assert len(atualizacoes) == 1
    assert atualizacoes[0] == {
        "playlist_sugestao_pendente": None,
        "rotina_sugestao_pendente": None,
        "comando_sugerido": None,
        "comando_sugerido_payload": None,
        "comando_sugerido_estado": "NONE",
        "comando_sugerido_ts": 0.0,
        "comando_pendente": None,
        "comando_pendente_payload": None,
    }
    assert all(ctx[chave] == valor for chave, valor in atualizacoes[0].items())
    assert ctx["_playlist_sugestao_pendente"] is None
    assert ctx["_rotina_sugestao_pendente"] is None
    assert eventos == [("resultado", "cancelado", {})]


def test_cancelar_compativel_com_setter_unitario_da_memoria() -> None:
    definicoes: list[tuple] = []

    executar_intencao_cancelamentos(
        "CANCELAR_ACAO",
        {"set_continuidade": lambda chave, valor: definicoes.append((chave, valor))},
        _dependencias([]),
    )

    assert ("playlist_sugestao_pendente", None) in definicoes
    assert ("rotina_sugestao_pendente", None) in definicoes
    assert ("comando_sugerido_estado", "NONE") in definicoes
    assert ("comando_sugerido_ts", 0.0) in definicoes
    assert len(definicoes) == 8


def test_falha_da_memoria_compartilhada_nao_impede_limpeza_do_retrato() -> None:
    ctx = {
        "comando_sugerido": "abrir navegador",
        "update_continuidades": lambda **_campos: (_ for _ in ()).throw(
            RuntimeError("memória indisponível")
        ),
    }

    despacho = executar_intencao_cancelamentos(
        "CANCELAR_ACAO", ctx, _dependencias([])
    )

    assert despacho == ResultadoDespacho.concluido()
    assert ctx["comando_sugerido"] is None
    assert ctx["comando_sugerido_estado"] == "NONE"


def test_roteador_delega_cancelamento_e_atualiza_fonte_unica() -> None:
    atualizacoes: list[dict] = []
    resultados = []

    retorno = executar_intencao(
        {"intent": "CANCELAR_ACAO", "params": {}},
        "deixa pra lá",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "update_continuidades": lambda **campos: atualizacoes.append(campos),
            "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: (
                resultados.append(contrato)
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    )

    assert retorno is True
    assert atualizacoes and atualizacoes[0]["comando_sugerido_estado"] == "NONE"
    assert resultados and resultados[0].status == "cancelado"

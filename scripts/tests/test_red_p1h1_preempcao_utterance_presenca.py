from __future__ import annotations

from mente_laylay.autonomia.porteiro_proatividade import (
    PorteiroProatividadeRuntime,
)


def _porteiro(*, usuario_falando: bool) -> PorteiroProatividadeRuntime:
    contexto = {
        "modo_chat": False,
        "conversa_ativa": False,
        "modo_jogo_ativo": True,
        "modo_foco": False,
        "usuario_falando": bool(usuario_falando),
        "ultima_entrada_ts": 0.0,
        "funcao_comunicativa": "",
    }

    return PorteiroProatividadeRuntime(
        contexto_getter=lambda: dict(contexto),
        agora=lambda: 1000.0,
    )


def test_red_p1h1_pedro_falando_preempta_presenca_jogo_no_porteiro_final():
    porteiro = _porteiro(usuario_falando=True)

    decisao = porteiro.avaliar(
        tipo="presenca_jogo",
        texto="Essa foi por pouco, hein?",
        turno_ativo=False,
        mesclar_turno=False,
        ultima_fala_normal_ts=0.0,
    )

    assert decisao["acao"] in {"adiar", "descartar"}
    assert decisao["acao"] != "emitir"


def test_guard_p1h1_silencio_preserva_presenca_jogo_validada():
    porteiro = _porteiro(usuario_falando=False)

    decisao = porteiro.avaliar(
        tipo="presenca_jogo",
        texto="Essa foi por pouco, hein?",
        turno_ativo=False,
        mesclar_turno=False,
        ultima_fala_normal_ts=0.0,
    )

    assert decisao["acao"] == "emitir"
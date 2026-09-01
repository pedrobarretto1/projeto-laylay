from mente_laylay.autonomia.porteiro_proatividade import (
    PorteiroProatividadeRuntime,
)


def _avaliar(porteiro, **extras):
    return porteiro.avaliar(
        tipo="presenca_jogo",
        texto="Essa foi por pouco, hein?",
        turno_ativo=False,
        mesclar_turno=False,
        inicio_forcado=False,
        ultima_fala_normal_ts=0.0,
        **extras,
    )


def test_red_p1hc4b_revalidacao_livre_nao_vira_repeticao() -> None:
    contexto = {
        "modo_chat": False,
        "conversa_ativa": False,
        "turno_ativo": False,
        "modo_jogo_ativo": True,
        "modo_foco": False,
        "ultima_entrada_ts": 0.0,
        "is_speaking": False,
        "usuario_falando": False,
        "interacao_usuario_ativa": False,
    }

    porteiro = PorteiroProatividadeRuntime(
        contexto_getter=lambda: dict(contexto),
        agora=lambda: 1000.0,
    )

    # T0 — admissão real.
    primeira = _avaliar(porteiro)

    assert primeira["acao"] == "emitir"

    # T2 — não é uma NOVA sugestão.
    # É a mesma sugestão perguntando se ainda pode ser entregue.
    revalidada = _avaliar(
        porteiro,
        revalidacao_entrega=True,
    )

    assert revalidada["acao"] == "emitir"

    assert not any(
        "equivalente" in str(motivo).casefold()
        or "recentemente" in str(motivo).casefold()
        for motivo in revalidada.get("motivos") or []
    )


def test_red_p1hc4b_revalidacao_detecta_owner_que_surgiu_depois() -> None:
    contexto = {
        "modo_chat": False,
        "conversa_ativa": False,
        "turno_ativo": False,
        "modo_jogo_ativo": True,
        "modo_foco": False,
        "ultima_entrada_ts": 0.0,
        "is_speaking": False,
        "usuario_falando": False,
        "interacao_usuario_ativa": False,
    }

    porteiro = PorteiroProatividadeRuntime(
        contexto_getter=lambda: dict(contexto),
        agora=lambda: 1000.0,
    )

    # T0
    primeira = _avaliar(porteiro)

    assert primeira["acao"] == "emitir"

    # T1 — usuário toma o canal.
    contexto["interacao_usuario_ativa"] = True

    # T2
    revalidada = _avaliar(
        porteiro,
        revalidacao_entrega=True,
    )

    assert revalidada["acao"] in {
        "adiar",
        "descartar",
    }
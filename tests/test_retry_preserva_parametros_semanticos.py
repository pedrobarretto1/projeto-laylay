"""RED arquitetural — retry preserva os parâmetros semânticos da operação.

R1-C3 testa fidelidade do recibo reexecutável.

Contrato protegido:

    EMAIL_READ(urgentes=True)
        -> publicação canônica
        -> recibo/continuidade reexecutável
        -> ainda contém urgentes=True

Uma futura correção de "Leia de novo." não pode recuperar somente o intent e
perder qualificadores que mudam o significado da operação original.

Este teste NÃO decide ainda onde o recibo correto deve viver.
"""

from __future__ import annotations

from typing import Any

from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.continuidade_geral import (
    selecionar_continuidade_reexecutavel,
)


def _registrar_email_urgente(
    estado: dict[str, Any],
) -> dict[str, Any]:
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "EMAIL_READ",
            "params": {
                "urgentes": True,
            },
            "status": "executado",
            "executou": True,
            "confirmado": True,
            "origem": "email",
        },
        "Leia meus emails urgentes.",
        True,
        origem="email",
        status="executado",
    )


def test_guard_resultado_atomico_preserva_urgentes_true() -> None:
    """A perda não pode ser atribuída ao resultado original."""
    estado = _registrar_email_urgente(estado_mental_inicial())

    assert estado["ultima_acao_intent"] == "EMAIL_READ"
    assert estado["ultima_acao_reexecutavel"] is True
    assert isinstance(estado["ultima_acao_params"], dict)
    assert estado["ultima_acao_params"]["urgentes"] is True


def test_guard_email_read_urgente_continua_classificado_reexecutavel() -> None:
    """O qualifier não pode tornar EMAIL_READ inelegível para retry."""
    estado = _registrar_email_urgente(estado_mental_inicial())

    continuidade = dict(estado.get("continuidade_geral") or {})
    registro_email = dict(
        dict(continuidade.get("dominios") or {}).get("email") or {}
    )

    assert registro_email
    assert registro_email["intent"] == "EMAIL_READ"
    assert registro_email["reexecutavel"] is True


def test_red_recibo_reexecutavel_preserva_parametro_urgentes() -> None:
    """R1-C3: repetir a operação exige preservar sua semântica completa."""
    estado = _registrar_email_urgente(estado_mental_inicial())

    repetivel = selecionar_continuidade_reexecutavel(
        estado,
        classe="operacional",
        ttl_s=900.0,
    )

    assert repetivel
    assert repetivel["intent"] == "EMAIL_READ"

    params = dict(repetivel.get("params") or {})

    assert params["urgentes"] is True


def test_red_historico_canonico_nao_pode_perder_urgentes() -> None:
    """A trilha histórica também precisa representar fielmente a operação."""
    estado = _registrar_email_urgente(estado_mental_inicial())

    continuidade = dict(estado.get("continuidade_geral") or {})
    historico = [
        dict(item)
        for item in list(continuidade.get("historico") or [])
        if isinstance(item, dict)
    ]

    emails = [
        item
        for item in historico
        if str(item.get("intent") or "").strip().upper() == "EMAIL_READ"
    ]

    assert emails

    params = dict(emails[-1].get("params") or {})

    assert params["urgentes"] is True

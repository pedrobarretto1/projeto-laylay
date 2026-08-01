"""Helpers mínimos compartilhados pelos executores de intenção."""

from __future__ import annotations

from typing import Any, Dict

from mente_laylay.memoria_mental.observabilidade import relatar_falha_opcional


def falar_ctx(
    ctx: Dict[str, Any],
    texto: str,
    emocao: str = "calma",
    nivel: Any = 1,
) -> None:
    """Entrega uma fala quando o contexto possui um canal de voz disponível."""
    falar = ctx.get("falar_com_lipsync")
    if callable(falar):
        falar(texto, emocao, nivel)


def relatar_falha_ctx(
    ctx: Dict[str, Any],
    componente: str,
    codigo: str,
    *,
    erro: BaseException | type[BaseException] | None = None,
    classe: str = "",
    impacto: str = "",
    fallback: str = "",
    dominio: str = "",
    fase: str = "",
) -> bool:
    """Publica falha sanitizada sem permitir que a telemetria derrube o fluxo."""
    relator = ctx.get("_registrar_falha_tecnica")
    if not callable(relator):
        relator = ctx.get("registrar_falha_diagnostico")
    if not callable(relator):
        return False

    turno = ctx.get("turno_atual")
    turno_id = turno.get("id") if isinstance(turno, dict) else ctx.get("turno_id")
    return relatar_falha_opcional(
        relator,
        componente,
        codigo,
        erro=erro,
        classe=classe,
        impacto=impacto,
        fallback=fallback,
        dominio=dominio,
        fase=fase,
        turno_id=turno_id,
    )

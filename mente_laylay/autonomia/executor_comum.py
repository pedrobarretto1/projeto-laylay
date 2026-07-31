"""Helpers mínimos compartilhados pelos executores de intenção."""

from __future__ import annotations

from typing import Any, Dict


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

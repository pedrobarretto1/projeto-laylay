"""Primitivas sem estado compartilhadas pelos processadores de pré-fluxo."""

from __future__ import annotations

from typing import Any, Dict


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


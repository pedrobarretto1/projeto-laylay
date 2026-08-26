"""Reconhecimento central dos estados internos do transporte da LLM."""

from __future__ import annotations

import re
from typing import Any


def eh_estado_tecnico_llm(valor: Any) -> bool:
    """Detecta sentinelas mesmo após pontuação ou sublinhados serem removidos."""
    texto = str(valor or "").casefold().strip()
    compacto = re.sub(r"[^a-z0-9]+", "", texto)
    return compacto in {
        "laylayllmtimeout",
        "laylayllmindisponivel",
        "laylayllmocupada",
    }

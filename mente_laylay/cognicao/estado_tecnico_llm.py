"""Reconhecimento central dos estados internos do transporte da LLM."""

from __future__ import annotations

import re
from typing import Any


_MOTIVOS_ORCAMENTO = frozenset({
    "limite_chamadas", "principal_duplicada", "reparo_duplicado", "prazo_esgotado",
    "turno_obsoleto", "turno_finalizado", "fatia_secundaria_insuficiente",
    "circuito_aberto", "probe_em_andamento",
})


def estado_bloqueio_orcamento_llm(motivo: str) -> str:
    """Codifica só razões canônicas; detalhes arbitrários nunca viram sentinela."""
    if motivo not in _MOTIVOS_ORCAMENTO:
        return "__LAYLAY_LLM_OCUPADA__"
    return f"__LAYLAY_LLM_ORCAMENTO_{motivo.upper()}__"


def eh_estado_tecnico_llm(valor: Any) -> bool:
    """Detecta sentinelas mesmo após pontuação ou sublinhados serem removidos."""
    return bool(categoria_estado_tecnico_llm(valor))


def categoria_estado_tecnico_llm(valor: Any) -> str:
    """Preserva o motivo conhecido; não infere a causa física da falha."""
    texto = str(valor or "").casefold().strip()
    compacto = re.sub(r"[^a-z0-9]+", "", texto)
    for motivo in _MOTIVOS_ORCAMENTO:
        if compacto == "laylayllmorcamento" + motivo.replace("_", ""):
            return "orcamento_" + motivo
    return {
        "laylayllmtimeout": "timeout",
        "laylayllmindisponivel": "indisponivel",
        # Também usado pelo orçamento/obsolescência: não comprova carga alta.
        "laylayllmocupada": "chamada_nao_disponivel",
    }.get(compacto, "")

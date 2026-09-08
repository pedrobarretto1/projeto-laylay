"""Taxonomia canônica das categorias observacionais do DEV Console."""

from __future__ import annotations

import re
from typing import Any


CATEGORIAS_DEV = frozenset({
    "SYSTEM", "IA", "ROUTER", "PRESENCE", "EVENTS", "AUTONOMY",
    "ERRORS", "TRACE", "DEV/UI",
})

_CATEGORIA_RE = re.compile(r"\[([^\]\r\n]{1,64})\]")
_FALA_LAYLAY_RE = re.compile(r"^\s*╭─[^\r\n]*\blaylay\s*:", re.IGNORECASE)

_ALIASES = {
    "SYSTEM": "SYSTEM",
    "TERMINAL": "SYSTEM",
    "MEMORIA": "SYSTEM",
    "MEMÓRIA": "SYSTEM",
    "AI": "IA",
    "IA": "IA",
    "LLM": "IA",
    "FALA": "IA",
    "VOZ": "IA",
    "BRIEFING": "IA",
    "CHAT": "IA",
    "PLANO": "ROUTER",
    "ROTEADOR": "ROUTER",
    "ROUTER": "ROUTER",
    "ROUTING": "ROUTER",
    "PRESENCA": "PRESENCE",
    "PRESENÇA": "PRESENCE",
    "PRESENCE": "PRESENCE",
    "EVENT": "EVENTS",
    "EVENTO": "EVENTS",
    "EVENTS": "EVENTS",
    "AUTONOMIA": "AUTONOMY",
    "AUTONOMY": "AUTONOMY",
    "POLICY": "AUTONOMY",
    "AÇÃO": "AUTONOMY",
    "ACAO": "AUTONOMY",
    "ARQUIVOS": "AUTONOMY",
    "MÚSICA": "AUTONOMY",
    "MUSICA": "AUTONOMY",
    "IOT": "AUTONOMY",
    "CHROME": "AUTONOMY",
    "ERRO": "ERRORS",
    "ERROR": "ERRORS",
    "ERRORS": "ERRORS",
    "FALHA": "ERRORS",
    "TEST": "TRACE",
    "CHAOS": "TRACE",
    "RED": "TRACE",
    "PASS": "TRACE",
    "TRACE": "TRACE",
    "DEV": "DEV/UI",
    "DEV/UI": "DEV/UI",
}


def normalizar_categoria_dev(valor: Any) -> str:
    texto = str(valor or "").strip().upper()
    primario = re.split(r"[:\s]", texto, maxsplit=1)[0]
    return _ALIASES.get(primario, "")


def classificar_categoria_evento_dev(
    titulo: Any,
    detalhe: Any = "",
    nivel: Any = "info",
    *,
    categoria_explicita: Any = "",
) -> str:
    """Classifica autoria/domínio; severidade continua sendo outro campo."""
    explicita = normalizar_categoria_dev(categoria_explicita)
    if explicita:
        return explicita

    titulo_texto = str(titulo or "")
    detalhe_texto = str(detalhe or "")
    texto = f"{titulo_texto} {detalhe_texto}".strip()
    achado = _CATEGORIA_RE.search(texto)
    if achado:
        categoria_log = normalizar_categoria_dev(achado.group(1))
        if categoria_log:
            return categoria_log

    normalizado = texto.casefold()
    titulo_normalizado = titulo_texto.strip().casefold()
    if (
        _FALA_LAYLAY_RE.search(titulo_texto)
        or titulo_normalizado in {"resposta entregue", "falando", "pensando"}
        or "fala final" in normalizado
        or "resposta da ia" in normalizado
    ):
        return "IA"
    if any(termo in normalizado for termo in ("roteamento", "roteador", "router")):
        return "ROUTER"
    if "presen" in normalizado:
        return "PRESENCE"
    if any(termo in normalizado for termo in (
        "ação confirmada", "acao confirmada", "ação parcialmente",
        "acao parcialmente", "ação não confirmada", "acao nao confirmada",
        "confirmação necessária", "confirmacao necessaria", "executor canônico",
        "executor canonico", "autonom",
    )):
        return "AUTONOMY"
    if any(termo in normalizado for termo in ("modelo", " llm", " ia ")):
        return "IA"
    if str(nivel or "").casefold() == "error":
        return "ERRORS"
    if str(nivel or "").casefold() == "warning" or "evento" in normalizado:
        return "EVENTS"
    return "SYSTEM"

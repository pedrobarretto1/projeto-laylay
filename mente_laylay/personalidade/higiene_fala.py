"""Higiene final para impedir que artefatos internos cheguem à fala."""

from __future__ import annotations

import re


_DIRETIVA_OPERACIONAL = re.compile(
    r"\[\s*\.?\s*(?:abre|abrir|toca|toque|tocar|coloca|coloque|botar|bota|"
    r"cria|criar|execute|executar|play|pause|fecha|fechar|liga|ligar|desliga|"
    r"desligar)\b[^\]]*\]",
    re.IGNORECASE,
)
_MARCADOR_MODELO = re.compile(r"(?<![\w])LYL(?![\w])", re.IGNORECASE)


def remover_residuos_operacionais(texto: str) -> str:
    """Remove pseudo-comandos e marcadores que nunca são texto para o usuário."""
    fala = str(texto or "")
    fala = _DIRETIVA_OPERACIONAL.sub(" ", fala)
    fala = _MARCADOR_MODELO.sub(" ", fala)
    fala = re.sub(r"\[\s*\]", " ", fala)
    fala = re.sub(r"\s+([,.;:!?])", r"\1", fala)
    fala = re.sub(r"([.!?])(?:\s*\1)+", r"\1", fala)
    return re.sub(r"\s+", " ", fala).strip()

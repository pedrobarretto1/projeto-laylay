"""Veto lexical experimental; cobertura de palavras NÃO prova implicação.

É um controle negativo para acréscimos óbvios a uma citação. Pode rejeitar
paráfrases corretas, sinônimos e traduções; nunca deve ser usado para aprovar.
"""

from __future__ import annotations

import re
import unicodedata


_FUNCIONAIS = frozenset({
    "a", "as", "o", "os", "um", "uma", "uns", "umas", "de", "da", "das",
    "do", "dos", "em", "na", "nas", "no", "nos", "por", "para", "e", "ou",
    "que", "se", "com", "ao", "aos", "como", "essa", "esse", "isso", "ela",
    "ele", "eles", "elas", "suas", "seus", "sua", "seu", "mais", "menos",
    "porque", "quando", "entao", "tambem", "bem", "muito", "muita",
    "todos", "todas", "pelo", "pela", "ser", "sao", "tem", "foi", "era",
})


def _tokens(texto: str) -> list[str]:
    normalizado = "".join(
        letra for letra in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(letra)
    )
    return [
        token for token in re.findall(r"[a-z0-9]+", normalizado)
        if (len(token) >= 4 or token.isdigit()) and token not in _FUNCIONAIS
    ]


def _compativel(palavra: str, fonte: set[str]) -> bool:
    if palavra in fonte:
        return True
    # Flexões simples, sem dicionário de sinônimos. Isto é só um veto.
    return len(palavra) >= 6 and any(
        len(outro) >= 6 and palavra[:5] == outro[:5] for outro in fonte
    )


def detalhes_sem_rastro(afirmacao: str, citacao: str) -> list[str]:
    """Lista conteúdo lexical não encontrado na citação escolhida."""
    termos_fonte = set(_tokens(citacao))
    return sorted({
        token for token in _tokens(afirmacao)
        if not _compativel(token, termos_fonte)
    })

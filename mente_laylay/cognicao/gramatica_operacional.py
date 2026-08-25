"""Gramáticas operacionais estreitas compartilhadas pela cognição da Laylay.

Este módulo somente reconhece formas linguísticas explícitas. Ele não resolve
contexto, não escolhe executor e não concede autoridade por conta própria.
"""

from __future__ import annotations

import re


_PADRAO_AVANCO_MIDIA_EXPLICITO = (
    r"(?:"
    r"(?:vai|passa|passe|pula|pule)\s+"
    r"(?:(?:para|pra)\s+)?(?:a\s+)?"
    r"(?:proxima|próxima)\s+(?:musica|música|faixa)"
    r"|"
    r"(?:avanca|avança|avance)\s+(?:uma|a)\s+"
    r"(?:musica|música|faixa)"
    r")"
)

_PADRAO_AVANCO_MIDIA_CONTEXTUAL = (
    r"(?:troca|troque|muda|mude)\s+(?:para|pra)\s+"
    r"(?:a\s+)?(?:proxima|próxima)"
)

_PADRAO_CONTINUACAO_PLAYLIST_ATUAL = (
    r"(?:adiciona|adicione|salva|salve|acrescenta|acrescente)\s+"
    r"(?:essa|esta|isso|ela)"
    r"(?:\s+(?:musica|música|faixa))?"
    r"(?:\s+(?:tambem|também))?\s+"
    r"(?:na|nessa|nesta)\s+(?:playlist\s+)?.+"
)

_SEPARADOR_CADEIA_M1 = (
    r"(?:e\s+depois|depois|em\s+seguida|entao|então|e)"
)


def texto_pede_avanco_midia_via_vai(
    texto: str,
    *,
    permitir_cadeia: bool = False,
) -> bool:
    """Reconhece ``vai para a próxima faixa`` sem promover ``vai`` globalmente."""
    base = re.sub(r"\s+", " ", str(texto or "").strip())
    base = base.strip(" .,!?:;")
    if not base:
        return False

    if re.fullmatch(
        _PADRAO_AVANCO_MIDIA_EXPLICITO,
        base,
        flags=re.IGNORECASE,
    ):
        return True

    if not permitir_cadeia:
        return False

    return bool(re.fullmatch(
        r"(?:"
        + _PADRAO_AVANCO_MIDIA_EXPLICITO
        + r"|"
        + _PADRAO_AVANCO_MIDIA_CONTEXTUAL
        + r")"
        + r"\s+"
        + _SEPARADOR_CADEIA_M1
        + r"\s+"
        + _PADRAO_CONTINUACAO_PLAYLIST_ATUAL,
        base,
        flags=re.IGNORECASE,
    ))

def texto_pede_restauracao_contextual(texto: str) -> bool:
    """Reconhece pedido direto de restauração expresso na fala atual.

    Esta função reconhece somente a forma linguística. Ela não consulta
    contexto, não escolhe alvo e não concede execução por conta própria.
    """
    base = re.sub(r"\s+", " ", str(texto or "").strip())
    base = base.strip(" .,!?:;")
    if not base:
        return False

    return bool(re.fullmatch(
        r"(?:desfaz(?:er)?(?:\s+isso)?|"
        r"restaura(?:r)?(?:\s+o)?\s+(?:ultimo|último)?\s*(?:arquivo|item|pasta)?|"
        r"recupera(?:r)?(?:\s+o)?\s+(?:ultimo|último)?\s*(?:arquivo|item|pasta)?|"
        r"(?:eu\s+)?quero\s+(?:ele|ela|isso|o\s+arquivo|a\s+pasta)\s+de\s+volta|"
        r"traz\s+(?:ele|ela|isso|o\s+arquivo|a\s+pasta)\s+de\s+volta)",
        base,
        flags=re.IGNORECASE,
    ))

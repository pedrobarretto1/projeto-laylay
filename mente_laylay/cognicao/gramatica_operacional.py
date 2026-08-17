"""Gramáticas operacionais estreitas compartilhadas pela cognição da Laylay.

Este módulo somente reconhece formas linguísticas explícitas. Ele não resolve
contexto, não escolhe executor e não concede autoridade por conta própria.
"""

from __future__ import annotations

import re


_PADRAO_AVANCO_MIDIA_VIA_VAI = (
    r"vai\s+(?:(?:para|pra)\s+)?(?:a\s+)?"
    r"(?:proxima|próxima)\s+(?:musica|música|faixa)"
)

_PADRAO_CONTINUACAO_PLAYLIST_ATUAL = (
    r"(?:adiciona|adicione)\s+(?:essa|esta|isso)"
    r"(?:\s+(?:musica|música|faixa))?\s+(?:tambem|também)\s+"
    r"(?:na|nessa|nesta)\s+.+"
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
        _PADRAO_AVANCO_MIDIA_VIA_VAI,
        base,
        flags=re.IGNORECASE,
    ):
        return True

    if not permitir_cadeia:
        return False

    return bool(re.fullmatch(
        _PADRAO_AVANCO_MIDIA_VIA_VAI
        + r"\s+"
        + _SEPARADOR_CADEIA_M1
        + r"\s+"
        + _PADRAO_CONTINUACAO_PLAYLIST_ATUAL,
        base,
        flags=re.IGNORECASE,
    ))

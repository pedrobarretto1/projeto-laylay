"""Transforma referencias mecanicas a memoria em familiaridade natural."""

from __future__ import annotations

import re


def sutilizar_referencia_memoria(texto: str) -> str:
    fala = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not fala:
        return fala
    substituicoes = (
        (r"\bsegundo (?:a|minha) mem[oó]ria[,;:]?\s*", ""),
        (r"\bde acordo com (?:a|minha) mem[oó]ria[,;:]?\s*", ""),
        (r"\b(?:pelo|segundo o) seu hist[oó]rico[,;:]?\s*", ""),
        (r"\bna minha mem[oó]ria consta que\s*", ""),
        (r"\bcomo est[aá] registrado[,;:]?\s*", ""),
        (r"\beu (?:me )?lembro que voc[eê] costuma\s+", "Você costuma "),
        (r"\blembrei que voc[eê] costuma\s+", "Você costuma "),
    )
    for padrao, troca in substituicoes:
        fala = re.sub(padrao, troca, fala, flags=re.IGNORECASE)
    fala = re.sub(r"\s+([,.!?])", r"\1", fala)
    fala = re.sub(r"\s+", " ", fala).strip(" ,;:")
    if fala and fala[0].islower():
        fala = fala[0].upper() + fala[1:]
    return fala

"""Normalizacao textual compartilhada da mente da Laylay."""

from __future__ import annotations

import re
import unicodedata


CORRECOES_FONETICAS = (
    (r"\bpaly\s*list\b", "playlist"),
    (r"\bplay\s*list\b", "playlist"),
    (r"\bpalylist\b", "playlist"),
    (r"\bplalyst\b", "playlist"),
    (r"\bplalist\b", "playlist"),
    (r"\bcamaitachi\b", "kamaitachi"),
    (r"\bkamaitaxi\b", "kamaitachi"),
    (r"\bkamaytachi\b", "kamaitachi"),
    (r"\byoutub\b", "youtube"),
    (r"\butube\b", "youtube"),
    (r"\bspotifi\b", "spotify"),
)


def remover_acentos(texto: str) -> str:
    try:
        normalizado = unicodedata.normalize("NFKD", str(texto or ""))
        return "".join(c for c in normalizado if not unicodedata.combining(c))
    except Exception:
        return str(texto or "")


def aplicar_correcao_fonetica(texto: str) -> str:
    t = str(texto or "").lower().strip()
    if not t:
        return ""
    t = re.sub(r"\s+", " ", t)
    for padrao, troca in CORRECOES_FONETICAS:
        t = re.sub(padrao, troca, t, flags=re.IGNORECASE)
    return t


def normalizar_texto(texto: str) -> str:
    t = remover_acentos(str(texto or "").lower())
    t = aplicar_correcao_fonetica(t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

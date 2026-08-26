"""Referências introduzidas por uma fala que passou pela verificação factual."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", base)).strip()


def extrair_referencia_musical_verificada(
    fala: str,
    plano: Dict[str, Any] | None,
) -> str:
    """Retorna o último título citado que também aparece na evidência do turno."""
    contrato = dict(plano or {})
    base = dict(contrato.get("fundamentacao_factual") or {})
    evidencia = _normalizar(" ".join((
        str(contrato.get("texto_usuario") or ""),
        str(base.get("resumo") or ""),
    )))
    if not evidencia:
        return ""
    titulos = [
        str(a or b).strip()
        for a, b in re.findall(r'["“]([^"”]{2,100})["”]|\'([^\']{2,100})\'', str(fala or ""))
        if str(a or b).strip()
    ]
    validos = [titulo for titulo in titulos if _normalizar(titulo) in evidencia]
    return validos[-1][:160] if validos else ""

"""Formato textual compatível para transportar várias imagens em memória."""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping


PREFIXO_PACOTE_IMAGENS = "LAYLAY_IMAGE_BUNDLE_V1:"


def empacotar_imagens(imagens: Iterable[Mapping[str, Any]]) -> str:
    itens = []
    for imagem in imagens:
        dados = str(imagem.get("data") or "").strip()
        if not dados:
            continue
        itens.append({
            "label": str(imagem.get("label") or "Imagem").strip()[:120],
            "mime": str(imagem.get("mime") or "image/jpeg").strip()[:40],
            "width": int(imagem.get("width") or 0),
            "height": int(imagem.get("height") or 0),
            "data": dados,
        })
    if not itens:
        return ""
    if len(itens) == 1:
        return itens[0]["data"]
    return PREFIXO_PACOTE_IMAGENS + json.dumps(
        {"images": itens[:5]}, ensure_ascii=False, separators=(",", ":"),
    )


def desempacotar_imagens(valor: Any) -> list[dict[str, Any]]:
    texto = str(valor or "").strip()
    if not texto:
        return []
    if not texto.startswith(PREFIXO_PACOTE_IMAGENS):
        return [{
            "label": "Imagem capturada",
            "mime": "image/jpeg",
            "width": 0,
            "height": 0,
            "data": texto,
        }]
    try:
        pacote = json.loads(texto[len(PREFIXO_PACOTE_IMAGENS):])
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    imagens = []
    for item in list(dict(pacote or {}).get("images") or [])[:5]:
        if not isinstance(item, Mapping) or not str(item.get("data") or "").strip():
            continue
        imagens.append({
            "label": str(item.get("label") or "Imagem").strip()[:120],
            "mime": str(item.get("mime") or "image/jpeg").strip()[:40],
            "width": int(item.get("width") or 0),
            "height": int(item.get("height") or 0),
            "data": str(item.get("data") or "").strip(),
        })
    return imagens


def selecionar_recorte_detalhe(valor: Any) -> str:
    """Retorna somente a imagem mais próxima, mantendo o contrato base64 antigo."""
    imagens = desempacotar_imagens(valor)
    if not imagens:
        return ""
    return str(imagens[-1].get("data") or "")

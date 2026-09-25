"""Fatores independentes para contexto operacional v1."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from .gerar_pragmatica_contexto_operacional_v1 import gerar


def _normalizar(texto: str) -> str:
    base=unicodedata.normalize("NFKD",str(texto or "").casefold())
    return "".join(c for c in base if not unicodedata.combining(c))


def gerar_fatorado():
    out=[]
    for original in gerar():
        item=dict(original)
        texto=_normalizar(item["text"])
        item["extension_factors"]={
            "acao_iot_off": bool(re.search(
                r"\b(?:desliga|desligue|desligar|apaga|apague|apagar)\b",
                texto,
            )) and "ventilador" in texto,
            "pedido_imediato": bool(item.get("is_command")),
        }
        out.append(item)
    return out


def main():
    xs=gerar_fatorado()
    p=Path(__file__).resolve().parent/"candidatos/pragmatica_contexto_fatorado_v2.jsonl"
    p.write_text(
        "".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in xs),
        encoding="utf-8",
    )
    print(json.dumps({
        "total":len(xs),
        "acao_iot_off_true":sum(x["extension_factors"]["acao_iot_off"] for x in xs),
        "pedido_imediato_true":sum(x["extension_factors"]["pedido_imediato"] for x in xs),
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()

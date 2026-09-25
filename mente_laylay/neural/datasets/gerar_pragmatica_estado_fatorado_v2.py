"""Fatores independentes para estado -> objetivo, derivados do lote v1."""

from __future__ import annotations

import json
from pathlib import Path

from .gerar_pragmatica_estado_v1 import gerar_audio, gerar_luz


def gerar() -> list[dict]:
    itens = [*gerar_audio(), *gerar_luz()]
    resultado = []
    for original in itens:
        item = dict(original)
        familia = str(item.get("family") or "")
        dominio = str(item.get("domain") or "").casefold()
        item["extension_factors"] = {
            "dominio_audio": dominio == "audio",
            "dominio_iot": dominio == "iot",
            "estado_excesso_audio": "audio_alto" in familia,
            "estado_audio_insuficiente": "audio_baixo" in familia,
            "estado_baixa_iluminacao": "luz_" in familia,
            "pedido_corretivo": bool(item.get("is_command")),
        }
        resultado.append(item)
    return resultado


def main() -> None:
    itens = gerar()
    destino = Path(__file__).resolve().parent / "candidatos/pragmatica_estado_fatorado_v2.jsonl"
    destino.write_text(
        "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in itens),
        encoding="utf-8",
    )
    print(json.dumps({"total": len(itens), "fatores": sorted(itens[0]["extension_factors"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

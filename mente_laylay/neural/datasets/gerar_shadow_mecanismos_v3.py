"""Seleciona mecanismos reais para intenção/ação sem deslocar gates seguros."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from .gerar_shadow_contrastivo_v2 import (
    gravar_jsonl_atomico,
    validar_lote as validar_lote_base,
    gerar_exemplos as gerar_exemplos_base,
)


INTENTS_ALVO = frozenset({
    "MEDIA_CONTROL", "IOT_CONTROL", "APP_OPEN",
})
HEADS_TREINO = ["action", "intent"]


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for original in gerar_exemplos_base():
        if (
            original.get("source") != "MANUAL_PARAPHRASE"
            or original.get("intent") not in INTENTS_ALVO
        ):
            continue
        item = dict(original)
        item["family"] = str(item["family"]).replace(
            "shadow_contrastivo_v2_", "shadow_mecanismos_v3_", 1
        )
        item["validation_group"] = str(item["validation_group"]).replace(
            "shadow_contrastivo_v2_", "shadow_mecanismos_v3_", 1
        )
        item["training_heads"] = list(HEADS_TREINO)
        exemplos.append(item)
    return exemplos


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, Any]:
    itens = [dict(item) for item in exemplos]
    resumo = validar_lote_base(itens)
    if len(itens) != 84:
        raise ValueError(f"lote v3 deveria ter 84 exemplos, recebeu {len(itens)}")
    if any(item.get("training_heads") != HEADS_TREINO for item in itens):
        raise ValueError("lote v3 possui escopo de heads incoerente")
    if any(item.get("intent") not in INTENTS_ALVO for item in itens):
        raise ValueError("lote v3 contém intent fora dos mecanismos observados")
    resumo["training_heads"] = list(HEADS_TREINO)
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default="mente_laylay/neural/datasets/candidatos/shadow_mecanismos_v3.jsonl",
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

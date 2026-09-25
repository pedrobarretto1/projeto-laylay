"""Reforco isolado de intent + intent_gate para VOLUME absoluto.

O lote cobre numero puro, "por cento" e "%", mas nao treina command,
action ou negacao. Valores ja usados como probes/diagnostico ficam fora.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import re
from typing import Any, Iterable

from .gerar_shadow_contrastivo_v2 import gravar_jsonl_atomico


NIVEIS_TREINO = (15, 32, 68, 87)
VALORES_PROTEGIDOS = frozenset({30, 40, 48, 50, 55, 59, 65, 70, 100})
MOLDES = (
    ("coloca_numero", "coloca o volume em {nivel}"),
    ("deixa_numero", "deixa o volume em {nivel}"),
    ("coloca_porcento", "coloca o volume em {nivel} por cento"),
    ("deixa_porcento", "deixa o volume em {nivel} por cento"),
    ("coloca_percentual", "coloca o volume em {nivel}%"),
    ("deixa_percentual", "deixa o volume em {nivel}%"),
)


def _item(texto: str, *, familia: str, nivel: int) -> dict[str, Any]:
    return {
        "text": texto,
        "intent": "VOLUME",
        "is_command": True,
        "negated": False,
        "action": "set",
        "family": f"volume_intent_gate_absoluto_v9_{familia}",
        "validation_group": f"volume_intent_gate_absoluto_v9_{familia}",
        "validation_entity_group": "audio_volume",
        "source": "MANUAL_PARAPHRASE",
        "domain": "audio",
        "training_heads": ["intent", "intent_gate"],
        "nivel_experimental": nivel,
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    return [
        _item(molde.format(nivel=nivel), familia=nome, nivel=nivel)
        for nome, molde in MOLDES
        for nivel in NIVEIS_TREINO
    ]


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, Any]:
    itens = [dict(item) for item in exemplos]
    textos = [str(item.get("text") or "").strip().casefold() for item in itens]
    if len(itens) != 24 or len(textos) != len(set(textos)):
        raise ValueError("lote v9 exige 24 textos unicos")
    if any(item.get("training_heads") != ["intent", "intent_gate"] for item in itens):
        raise ValueError("lote v9 so pode ensinar intent + intent_gate")
    if any(
        item.get("intent") != "VOLUME"
        or item.get("action") != "set"
        or item.get("is_command") is not True
        or item.get("negated") is not False
        or item.get("domain") != "audio"
        for item in itens
    ):
        raise ValueError("rotulos auxiliares do lote v9 divergiram")
    valores = {
        int(valor)
        for texto in textos
        for valor in re.findall(r"(?<!\d)(\d{1,3})(?!\d)", texto)
    }
    if valores != set(NIVEIS_TREINO):
        raise ValueError("niveis do lote v9 divergiram")
    if valores & set(VALORES_PROTEGIDOS):
        raise ValueError("valor protegido entrou no lote v9")
    familias = Counter(str(item.get("family") or "") for item in itens)
    if len(familias) != 6 or set(familias.values()) != {4}:
        raise ValueError("lote v9 exige 6 familias com 4 niveis")
    return {
        "total": len(itens),
        "familias": len(familias),
        "niveis_treino": sorted(valores),
        "valores_protegidos": sorted(VALORES_PROTEGIDOS),
        "training_heads": ["intent", "intent_gate"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default="mente_laylay/neural/datasets/candidatos/volume_intent_gate_absoluto_v9.jsonl",
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

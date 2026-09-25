"""Reforco de intent VOLUME com intent_gate minimo para absolutos.

Todos os 24 exemplos treinam intent. Apenas 8 exemplos representativos de
"por cento"/"%" treinam tambem intent_gate, reduzindo deriva do gate global.
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
GATE_NIVEIS = frozenset({32, 68})
GATE_FAMILIAS = frozenset({
    "coloca_porcento", "deixa_porcento",
    "coloca_percentual", "deixa_percentual",
})
MOLDES = (
    ("coloca_numero", "coloca o volume em {nivel}"),
    ("deixa_numero", "deixa o volume em {nivel}"),
    ("coloca_porcento", "coloca o volume em {nivel} por cento"),
    ("deixa_porcento", "deixa o volume em {nivel} por cento"),
    ("coloca_percentual", "coloca o volume em {nivel}%"),
    ("deixa_percentual", "deixa o volume em {nivel}%"),
)


def _item(texto: str, *, familia: str, nivel: int) -> dict[str, Any]:
    usa_gate = familia in GATE_FAMILIAS and nivel in GATE_NIVEIS
    return {
        "text": texto,
        "intent": "VOLUME",
        "is_command": True,
        "negated": False,
        "action": "set",
        "family": f"volume_intent_gate_absoluto_v10_{familia}",
        "validation_group": f"volume_intent_gate_absoluto_v10_{familia}",
        "validation_entity_group": "audio_volume",
        "source": "MANUAL_PARAPHRASE",
        "domain": "audio",
        "training_heads": ["intent", "intent_gate"] if usa_gate else ["intent"],
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
        raise ValueError("lote v10 exige 24 textos unicos")
    gate = [x for x in itens if x.get("training_heads") == ["intent", "intent_gate"]]
    intent_only = [x for x in itens if x.get("training_heads") == ["intent"]]
    if len(gate) != 8 or len(intent_only) != 16:
        raise ValueError("lote v10 exige 8 exemplos de gate e 16 intent-only")
    if any(
        x.get("intent") != "VOLUME"
        or x.get("action") != "set"
        or x.get("is_command") is not True
        or x.get("negated") is not False
        or x.get("domain") != "audio"
        for x in itens
    ):
        raise ValueError("rotulos auxiliares do lote v10 divergiram")
    valores = {
        int(v)
        for texto in textos
        for v in re.findall(r"(?<!\d)(\d{1,3})(?!\d)", texto)
    }
    if valores != set(NIVEIS_TREINO) or valores & set(VALORES_PROTEGIDOS):
        raise ValueError("niveis do lote v10 invalidos")
    familias = Counter(str(x.get("family") or "") for x in itens)
    if len(familias) != 6 or set(familias.values()) != {4}:
        raise ValueError("lote v10 exige 6 familias com 4 niveis")
    return {
        "total": 24,
        "intent_only": 16,
        "intent_gate": 8,
        "familias": 6,
        "niveis_treino": sorted(valores),
        "valores_protegidos": sorted(VALORES_PROTEGIDOS),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default="mente_laylay/neural/datasets/candidatos/volume_intent_gate_absoluto_v10_minimo.jsonl",
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

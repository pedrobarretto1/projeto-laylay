"""Onda action + reforco minimo de intent_gate para VOLUME:set absoluto.

Todos os exemplos ensinam ``action=set``; somente as familias ``coloca_volume`` e ``deixa_volume``
ensinam ``intent_gate``. As probes reais com valores 50 e 100 ficam fora.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import re
from typing import Any, Iterable

from .gerar_shadow_contrastivo_v2 import gravar_jsonl_atomico


PROBES = frozenset({
    "coloca o volume em 50",
    "coloca o volume em 100",
})
NIVEIS_TREINO = (20, 35, 65, 85)

MOLDES = (
    ("coloca_volume", "coloca o volume em {nivel}"),
    ("coloque_volume", "coloque o volume em {nivel}"),
    ("define_volume", "define o volume em {nivel}"),
    ("defina_volume", "defina o volume em {nivel}"),
    ("ajusta_volume", "ajusta o volume para {nivel}"),
    ("ajuste_volume", "ajuste o volume para {nivel}"),
    ("deixa_volume", "deixa o volume em {nivel}"),
    ("deixe_volume", "deixe o volume em {nivel}"),
    ("pode_colocar", "pode colocar o volume em {nivel}"),
    ("quero_volume", "quero o volume em {nivel}"),
    ("configura_som", "configura o som para {nivel}%"),
    ("muda_audio", "muda o audio para {nivel}%"),
)


def _item(
    texto: str,
    *,
    familia: str,
    nivel: int,
) -> dict[str, Any]:
    return {
        "text": texto,
        "intent": "VOLUME",
        "is_command": True,
        "negated": False,
        "action": "set",
        "family": f"volume_set_absoluto_v7_gate_duplo_{familia}",
        "validation_group": f"volume_set_absoluto_v7_gate_duplo_{familia}",
        "validation_entity_group": "audio_volume",
        "source": "MANUAL_PARAPHRASE",
        "domain": "audio",
        "training_heads": (
            ["action", "intent_gate"]
            if familia in {"coloca_volume", "deixa_volume"}
            else ["action"]
        ),
        "nivel_experimental": nivel,
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    return [
        _item(
            molde.format(nivel=nivel),
            familia=nome,
            nivel=nivel,
        )
        for nome, molde in MOLDES
        for nivel in NIVEIS_TREINO
    ]


def _tem_valor_congelado(texto: str) -> bool:
    numeros = {
        int(valor)
        for valor in re.findall(r"(?<!\d)(\d{1,3})(?!\d)", str(texto or ""))
    }
    return bool(numeros & {50, 100})


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, Any]:
    itens = [dict(item) for item in exemplos]
    textos = [str(item.get("text") or "").strip().casefold() for item in itens]

    if len(itens) != 48 or len(textos) != len(set(textos)):
        raise ValueError("lote v7_gate_duplo exige 48 textos unicos")
    if PROBES & set(textos):
        raise ValueError("probe/challenge de volume absoluto nao pode entrar no v7_gate_duplo")
    if any(_tem_valor_congelado(texto) for texto in textos):
        raise ValueError("valor congelado 50/100 nao pode entrar no lote v7_gate_duplo")
    gate_itens = [
        item for item in itens
        if item.get("training_heads") == ["action", "intent_gate"]
    ]
    action_only = [
        item for item in itens
        if item.get("training_heads") == ["action"]
    ]
    if len(gate_itens) != 8 or len(action_only) != 40:
        raise ValueError("lote v7_gate_duplo exige 8 exemplos de gate e 40 action-only")
    if any(
        not str(item.get("family") or "").endswith(("_coloca_volume", "_deixa_volume"))
        for item in gate_itens
    ):
        raise ValueError("intent_gate duplo so pode usar coloca_volume/deixa_volume")
    if any(item.get("intent") != "VOLUME" for item in itens):
        raise ValueError("lote v7_gate_duplo exige intent VOLUME")
    if any(str(item.get("action") or "").casefold() != "set" for item in itens):
        raise ValueError("lote v7_gate_duplo exige action set")
    if any(item.get("is_command") is not True for item in itens):
        raise ValueError("lote v7_gate_duplo exige exemplos de comando")
    if any(item.get("negated") is not False for item in itens):
        raise ValueError("lote v7_gate_duplo nao ensina negacao")
    if any(str(item.get("domain") or "").casefold() != "audio" for item in itens):
        raise ValueError("lote v7_gate_duplo exige dominio audio")

    familias = Counter(str(item.get("family") or "") for item in itens)
    if len(familias) != 12 or set(familias.values()) != {4}:
        raise ValueError("lote v7_gate_duplo exige 12 familias com 4 niveis cada")

    niveis = {
        int(item.get("nivel_experimental"))
        for item in itens
        if type(item.get("nivel_experimental")) is int
    }
    if niveis != set(NIVEIS_TREINO):
        raise ValueError("niveis experimentais do lote v7_gate_duplo divergiram")

    return {
        "total": len(itens),
        "volume_set": len(itens),
        "familias": len(familias),
        "niveis_treino": sorted(niveis),
        "action_only": len(action_only),
        "intent_gate_exemplos": len(gate_itens),
        "intent_gate_familias": ["coloca_volume", "deixa_volume"],
        "probes_preservadas": sorted(PROBES),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=(
            "mente_laylay/neural/datasets/candidatos/"
            "volume_set_absoluto_v7_gate_duplo.jsonl"
        ),
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


"""Lote action-only para VOLUME:set em linguagem de limite maximo.

Nao treina intent, command, intent_gate ou negacao. Serve apenas para separar
"maximo" (valor absoluto) de "aumentar" (acao relativa).
"""
from __future__ import annotations

import argparse
import json
from typing import Any, Iterable

from .gerar_shadow_contrastivo_v2 import gravar_jsonl_atomico


TEXTOS = (
    "põe o som no limite máximo",
    "deixe o áudio no máximo permitido",
    "configure o volume no nível máximo",
    "manda o som até o máximo",
    "quero o áudio no teto",
    "coloque o som na potência máxima",
    "ajusta o nível do áudio para o máximo",
    "define o som no valor máximo",
    "leva o volume até o topo",
    "deixa o áudio no limite mais alto",
    "configura o nível do som no máximo",
    "bota o áudio no máximo",
)


def _item(texto: str, indice: int) -> dict[str, Any]:
    return {
        "text": texto,
        "intent": "VOLUME",
        "is_command": True,
        "negated": False,
        "action": "set",
        "family": f"volume_extremos_action_v7_maximo_{indice}",
        "validation_group": "volume_extremos_action_v7_maximo",
        "validation_entity_group": "audio_volume",
        "source": "MANUAL_PARAPHRASE",
        "domain": "audio",
        "training_heads": ["action"],
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    return [_item(texto, indice) for indice, texto in enumerate(TEXTOS, 1)]


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, Any]:
    itens = [dict(x) for x in exemplos]
    textos = [str(x.get("text") or "").strip().casefold() for x in itens]
    if len(itens) != 12 or len(textos) != len(set(textos)):
        raise ValueError("lote v7 exige 12 textos unicos")
    if any(x.get("training_heads") != ["action"] for x in itens):
        raise ValueError("lote v7 so pode ensinar action")
    if any(
        x.get("intent") != "VOLUME"
        or x.get("action") != "set"
        or x.get("is_command") is not True
        or x.get("negated") is not False
        or x.get("domain") != "audio"
        for x in itens
    ):
        raise ValueError("rotulos do lote v7 divergiram")
    return {
        "total": len(itens),
        "volume_set_maximo": len(itens),
        "training_heads": ["action"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default="mente_laylay/neural/datasets/candidatos/volume_extremos_action_v7.jsonl",
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

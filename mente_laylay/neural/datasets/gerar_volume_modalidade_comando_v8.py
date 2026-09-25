"""Command head dedicado a VOLUME com contraste de modalidade ampliado.

Treina somente comando/nao-comando. Inclui capacidade, relato, explicacao,
citacao, causalidade e perguntas de "por que" sem treinar outros heads.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from typing import Any, Iterable

from .gerar_shadow_contrastivo_v2 import gravar_jsonl_atomico


POSITIVOS = (
    "bota o som em 30 por cento",
    "põe o áudio em 40 por cento",
    "regula o volume para 60",
    "configura o som em 70%",
    "quero o volume em 25 por cento",
    "deixa o nível do áudio em 80",
    "ajusta o nível do som para 35",
    "muda o áudio para 45%",
    "define o nível do volume em 65",
    "coloque o som em 75%",
    "pode regular o áudio para 85",
    "faz o volume ficar em 90 por cento",
    "ajusta o som para 32%",
    "põe o volume em 58%",
    "deixa o áudio em 73%",
    "regula o som em 44%",
    "faz o áudio ficar em 62%",
    "bota o volume em 88%",
)

NEGATIVOS = (
    "você consegue controlar o som?",
    "você sabe mexer no áudio?",
    "tem como mudar o som?",
    "é possível regular o áudio?",
    "mexer no volume pode dar algum problema?",
    "mudar o som afeta a qualidade?",
    "ajustar o áudio faz diferença?",
    "me explica de que jeito mudar o som",
    "quero entender como regular o áudio",
    "qual é o jeito de controlar o som?",
    "eu mexi no volume ontem",
    "ele regulou o áudio durante o jogo",
    "por que você reduziu o som?",
    "por que o áudio ficou mais baixo?",
    "dizer 'aumenta o som' é só um exemplo",
    "você pode falar 'abaixa o áudio' como exemplo",
    "aumentar o som pode fazer mal?",
    "subir o volume prejudica a audição?",
)


def _item(texto: str, *, comando: bool, indice: int) -> dict[str, Any]:
    return {
        "text": texto,
        "intent": "VOLUME" if comando else "NONE",
        "is_command": comando,
        "negated": False,
        "action": "set" if comando else "none",
        "family": f"volume_modalidade_comando_v8_{'positivo' if comando else 'negativo'}_{indice}",
        "validation_group": f"volume_modalidade_comando_v8_{'positivo' if comando else 'negativo'}",
        "validation_entity_group": "audio_volume",
        "source": "MANUAL_PARAPHRASE" if comando else "HARD_NEGATIVE",
        "domain": "audio",
        "training_heads": ["command"],
        "command_head_intent": "VOLUME",
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    itens = [_item(t, comando=True, indice=i) for i, t in enumerate(POSITIVOS, 1)]
    itens.extend(_item(t, comando=False, indice=i) for i, t in enumerate(NEGATIVOS, 1))
    return itens


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, Any]:
    itens = [dict(x) for x in exemplos]
    textos = [str(x.get("text") or "").strip().casefold() for x in itens]
    if len(itens) != 36 or len(textos) != len(set(textos)):
        raise ValueError("lote v8 exige 36 textos unicos")
    contagem = Counter(bool(x.get("is_command")) for x in itens)
    if contagem != Counter({True: 18, False: 18}):
        raise ValueError("lote v8 exige balanceamento 18/18")
    if any(x.get("training_heads") != ["command"] for x in itens):
        raise ValueError("lote v8 so pode ensinar command")
    if any(x.get("command_head_intent") != "VOLUME" for x in itens):
        raise ValueError("lote v8 exige command_head_intent VOLUME")
    for x in itens:
        if x.get("intent") != ("VOLUME" if x["is_command"] else "NONE"):
            raise ValueError("intent auxiliar divergente")
        if x.get("action") != ("set" if x["is_command"] else "none"):
            raise ValueError("action auxiliar divergente")
        if x.get("domain") != "audio" or x.get("negated") is not False:
            raise ValueError("escopo do lote v8 divergente")
    return {
        "total": len(itens),
        "comandos": contagem[True],
        "nao_comandos": contagem[False],
        "training_heads": ["command"],
        "command_head_intent": "VOLUME",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default="mente_laylay/neural/datasets/candidatos/volume_modalidade_comando_v8.jsonl",
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

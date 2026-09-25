"""Onda pequena para cobrir flexoes imperativas do head command de IoT.

O lote e candidato de desenvolvimento: ensina somente command_head_intent
IOT_CONTROL. Os challenges prospectivos "ligue a luz" e "desligue a luz"
permanecem fora do treino.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from typing import Any, Iterable

from .gerar_shadow_contrastivo_v2 import gravar_jsonl_atomico


POSITIVOS = (
    ("ligue a luminaria agora", "on"),
    ("desligue a luminaria agora", "off"),
    ("ligue o abajur agora", "on"),
    ("desligue o abajur agora", "off"),
    ("ligue a tomada da sala", "on"),
    ("desligue a tomada da sala", "off"),
    ("por favor ligue a luminaria", "on"),
    ("por favor desligue o abajur", "off"),
    ("ligue o ventilador por favor", "on"),
    ("desligue o ventilador por favor", "off"),
    ("ligue esta tomada agora", "on"),
    ("desligue este abajur agora", "off"),
)

NEGATIVOS = (
    "a expressao ligue a luminaria aparece na documentacao",
    "a frase desligue a luminaria e apenas um exemplo",
    "o professor escreveu ligue o abajur no quadro",
    "o manual cita desligue o abajur como instrucao",
    "na apostila aparece ligue a tomada da sala",
    "estou explicando a frase desligue a tomada da sala",
    "ontem ela mencionou ligue a luminaria durante a aula",
    "falar desligue o abajur nao executa nada",
    "o texto usa ligue o ventilador como exemplo",
    "a documentacao mostra desligue o ventilador por favor",
    "anotei a expressao ligue esta tomada agora",
    "estou analisando a frase desligue este abajur agora",
)


def _item(
    texto: str,
    *,
    is_command: bool,
    action: str,
    grupo: str,
    indice: int,
) -> dict[str, Any]:
    return {
        "text": texto,
        "intent": "IOT_CONTROL" if is_command else "NONE",
        "is_command": is_command,
        "negated": False,
        "action": action if is_command else "none",
        "family": f"iot_flexoes_imperativo_v5_{grupo}_{indice}",
        "validation_group": f"iot_flexoes_imperativo_v5_{grupo}",
        "source": "MANUAL_PARAPHRASE" if is_command else "HARD_NEGATIVE",
        "domain": "iot",
        "training_heads": ["command"],
        "command_head_intent": "IOT_CONTROL",
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos = [
        _item(
            texto,
            is_command=True,
            action=action,
            grupo="positivo",
            indice=indice,
        )
        for indice, (texto, action) in enumerate(POSITIVOS, 1)
    ]
    exemplos.extend(
        _item(
            texto,
            is_command=False,
            action="none",
            grupo="negativo_meta",
            indice=indice,
        )
        for indice, texto in enumerate(NEGATIVOS, 1)
    )
    return exemplos


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, Any]:
    itens = [dict(item) for item in exemplos]
    textos = [str(item.get("text") or "").strip().casefold() for item in itens]
    if len(itens) != 24 or len(textos) != len(set(textos)):
        raise ValueError("lote v5 exige 24 textos unicos")
    if any("luz" in texto for texto in textos):
        raise ValueError("challenge com alvo luz nao pode entrar no lote v5")
    if {"ligue a luz", "desligue a luz"} & set(textos):
        raise ValueError("challenge prospectivo nao pode entrar no treino")
    if any(item.get("training_heads") != ["command"] for item in itens):
        raise ValueError("lote v5 so pode ensinar command")
    if any(item.get("command_head_intent") != "IOT_CONTROL" for item in itens):
        raise ValueError("lote v5 so pode ensinar o head IOT_CONTROL")
    contagem = Counter(bool(item.get("is_command")) for item in itens)
    if contagem != Counter({True: 12, False: 12}):
        raise ValueError("lote v5 exige balanceamento 12/12")
    return {
        "total": len(itens),
        "comandos": contagem[True],
        "nao_comandos": contagem[False],
        "command_head_intent": "IOT_CONTROL",
        "training_heads": ["command"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=(
            "mente_laylay/neural/datasets/candidatos/"
            "iot_flexoes_imperativo_v5.jsonl"
        ),
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

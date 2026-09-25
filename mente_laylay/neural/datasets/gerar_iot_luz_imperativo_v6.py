"""Onda pequena para ensinar o alvo luz ao head command de IOT_CONTROL.

As probes prospectivas exatas "ligue a luz" e "desligue a luz" permanecem
fora dos comandos de treino. O lote ensina somente o head de comando; intent e
action sao metadados de escopo, nao novas cabecas treinadas por esta onda.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from typing import Any, Iterable

from .gerar_shadow_contrastivo_v2 import gravar_jsonl_atomico


PROBES = frozenset({"ligue a luz", "desligue a luz"})

POSITIVOS = (
    ("acenda a luz do quarto", "on"),
    ("pode ligar a luz da sala", "on"),
    ("deixe a luz do corredor acesa", "on"),
    ("quero a luz principal ligada", "on"),
    ("ativa a luz da cozinha", "on"),
    ("pode acender essa luz agora", "on"),
    ("apague a luz do quarto", "off"),
    ("pode desligar a luz da sala", "off"),
    ("deixe a luz do corredor apagada", "off"),
    ("quero a luz principal desligada", "off"),
    ("desativa a luz da cozinha", "off"),
    ("pode apagar essa luz agora", "off"),
)

NEGATIVOS = (
    "a frase ligue a luz e apenas um exemplo",
    "a frase desligue a luz e apenas um exemplo",
    "o manual cita acenda a luz do quarto como instrucao",
    "estou explicando pode desligar a luz da sala",
    "na apostila aparece deixe a luz do corredor acesa",
    "falar apague a luz do quarto nao executa nada",
    "o professor escreveu ativa a luz da cozinha no quadro",
    "a documentacao mostra desativa a luz da cozinha",
    "anotei quero a luz principal ligada como exemplo",
    "estou analisando quero a luz principal desligada",
    "o texto usa pode acender essa luz agora como exemplo",
    "mencionei pode apagar essa luz agora durante a aula",
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
        "family": f"iot_luz_imperativo_v6_{grupo}_{indice}",
        "validation_group": f"iot_luz_imperativo_v6_{grupo}",
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
            grupo=f"positivo_{action}",
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
        raise ValueError("lote v6 exige 24 textos unicos")
    if PROBES & set(textos):
        raise ValueError("probe/challenge prospectiva nao pode entrar no lote v6")
    if any(item.get("training_heads") != ["command"] for item in itens):
        raise ValueError("lote v6 so pode ensinar o head command")
    if any(item.get("command_head_intent") != "IOT_CONTROL" for item in itens):
        raise ValueError("lote v6 so pode ensinar o head IOT_CONTROL")

    contagem = Counter(bool(item.get("is_command")) for item in itens)
    if contagem != Counter({True: 12, False: 12}):
        raise ValueError("lote v6 exige balanceamento 12/12")

    positivos = [item for item in itens if item.get("is_command") is True]
    if any("luz" not in str(item.get("text") or "").casefold() for item in positivos):
        raise ValueError("todo comando v6 precisa ensinar o alvo luz")
    acoes = Counter(str(item.get("action") or "").casefold() for item in positivos)
    if acoes != Counter({"on": 6, "off": 6}):
        raise ValueError("lote v6 exige balanceamento de action 6/6")

    if any(
        item.get("intent") != ("IOT_CONTROL" if item.get("is_command") else "NONE")
        for item in itens
    ):
        raise ValueError("intent do lote v6 diverge do contrato command-only")
    if any(
        str(item.get("action") or "").casefold()
        != (str(item.get("action") or "").casefold() if item.get("is_command") else "none")
        for item in itens
    ):
        raise ValueError("action negativa do lote v6 precisa ser none")

    return {
        "total": len(itens),
        "comandos": contagem[True],
        "nao_comandos": contagem[False],
        "acoes_comando": dict(sorted(acoes.items())),
        "command_head_intent": "IOT_CONTROL",
        "training_heads": ["command"],
        "probes_preservadas": sorted(PROBES),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=(
            "mente_laylay/neural/datasets/candidatos/"
            "iot_luz_imperativo_v6.jsonl"
        ),
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

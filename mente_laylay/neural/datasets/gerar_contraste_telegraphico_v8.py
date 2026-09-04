"""Contrasta pedidos musicais telegráficos com menções linguisticamente próximas.

O lote ensina somente a cabeça dirigida de comando. Intenção, ação, negação,
autoridade e execução permanecem fora de seu escopo e o artefato fica em
staging até passar pelas avaliações reservadas.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from typing import Any, Iterable

from .gerar_shadow_contrastivo_v2 import gravar_jsonl_atomico


FAMILIAS = {
    "pedido_achar_eliptico": (
        True,
        "MANUAL_PARAPHRASE",
        (
            "acha soul antigo",
            "acha jazz instrumental",
            "acha samba antigo",
        ),
    ),
    "pedido_buscar_eliptico": (
        True,
        "MANUAL_PARAPHRASE",
        (
            "busca soul antigo",
            "busca jazz instrumental",
            "busca samba antigo",
        ),
    ),
    "pedido_encontrar_eliptico": (
        True,
        "MANUAL_PARAPHRASE",
        (
            "encontra soul antigo",
            "encontra jazz instrumental",
            "encontra samba antigo",
        ),
    ),
    "opiniao_primeira_pessoa": (
        False,
        "HARD_NEGATIVE",
        (
            "acho soul antigo cansativo",
            "acho jazz instrumental relaxante",
            "acho samba antigo divertido",
        ),
    ),
    "opiniao_terceira_pessoa": (
        False,
        "HARD_NEGATIVE",
        (
            "ela acha soul antigo cansativo",
            "o crítico acha jazz instrumental sofisticado",
            "meu amigo acha samba antigo divertido",
        ),
    ),
    "capacidade_musical": (
        False,
        "HARD_NEGATIVE",
        (
            "colocar música em apresentações exige cuidado",
            "música de fundo em apresentações ajuda na concentração",
            "trilhas sonoras em apresentações ajudam a narrativa",
        ),
    ),
}


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for mecanismo, (is_command, source, textos) in FAMILIAS.items():
        familia = f"contraste_telegraphico_v8_{mecanismo}"
        for indice, texto in enumerate(textos):
            grupo = (
                f"contraste_telegraphico_v8_alvo_{indice}"
                if mecanismo in {
                    "pedido_achar_eliptico",
                    "opiniao_primeira_pessoa",
                    "opiniao_terceira_pessoa",
                }
                else familia
            )
            familia_item = grupo if grupo != familia else familia
            exemplos.append({
                "text": texto,
                "intent": "MUSIC_SEARCH" if is_command else "NONE",
                "is_command": is_command,
                "negated": False,
                "action": "search" if is_command else "none",
                "family": familia_item,
                "validation_group": grupo,
                "source": source,
                "domain": "music",
                "training_heads": (
                    ["command", "intent_gate"]
                    if is_command and mecanismo == "pedido_achar_eliptico"
                    else ["command"]
                ),
                "command_head_intent": "MUSIC_SEARCH",
            })
    return exemplos


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, Any]:
    itens = [dict(item) for item in exemplos]
    textos = [_normalizar(item.get("text", "")) for item in itens]
    if len(itens) != 18:
        raise ValueError(
            f"lote v8 deveria ter 18 exemplos, recebeu {len(itens)}"
        )
    if len(textos) != len(set(textos)):
        raise ValueError("lote v8 contém textos duplicados")
    if any(
        item.get("training_heads")
        != (
            ["command", "intent_gate"]
            if (
                item.get("is_command")
                and str(item.get("text", "")).startswith("acha ")
            )
            else ["command"]
        )
        for item in itens
    ):
        raise ValueError("escopo de heads incompatível com a classe do lote v8")
    if any(item.get("command_head_intent") != "MUSIC_SEARCH" for item in itens):
        raise ValueError("lote v8 exige owner MUSIC_SEARCH")
    if any(item.get("negated") is not False for item in itens):
        raise ValueError("negação está fora do escopo do lote v8")
    if any(
        item.get("intent")
        != ("MUSIC_SEARCH" if item.get("is_command") else "NONE")
        for item in itens
    ):
        raise ValueError("rótulo de intent incompatível com a classe do lote v8")

    classes = Counter(bool(item["is_command"]) for item in itens)
    familias = Counter(str(item["family"]) for item in itens)
    return {
        "total": len(itens),
        "comandos": classes[True],
        "nao_comandos": classes[False],
        "grupos_validacao": len({item["validation_group"] for item in itens}),
        "max_exemplos_por_familia": max(familias.values()),
        "positivos_training_heads": ["command"],
        "intent_gate_training_family": "pedido_achar_eliptico",
        "negativos_training_heads": ["command"],
        "command_head_intent": "MUSIC_SEARCH",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=(
            "mente_laylay/neural/datasets/candidatos/"
            "contraste_telegraphico_v8.jsonl"
        ),
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

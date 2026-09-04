"""Auditoria fail-closed de leakage entre DEV e Frozen Challenge."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping

from mente_laylay.especialistas.capacidades import intents_registradas

from .dataset import carregar_jsonl


def _normalizar_texto(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def _familias(exemplos: Iterable[Mapping[str, Any]]) -> set[str]:
    return {
        str(item.get("family") or "").strip().casefold()
        for item in exemplos
        if str(item.get("family") or "").strip()
    }


def auditar_leakage_dataset(
    dev: Iterable[Mapping[str, Any]],
    frozen: Iterable[Mapping[str, Any]],
    *,
    limiar_similaridade: float = 0.9,
) -> dict[str, Any]:
    """Encontra vazamento lexical sem modificar nem rerrotular o dataset."""
    limiar = float(limiar_similaridade)
    if not 0.0 < limiar <= 1.0:
        raise ValueError("limiar de similaridade precisa estar em (0, 1]")
    dev_itens = [dict(item) for item in dev]
    frozen_itens = [dict(item) for item in frozen]
    familias_compartilhadas = sorted(
        _familias(dev_itens) & _familias(frozen_itens)
    )
    duplicados_exatos: list[dict[str, Any]] = []
    quase_duplicados: list[dict[str, Any]] = []

    for indice_dev, item_dev in enumerate(dev_itens, 1):
        texto_dev = str(item_dev.get("text") or "").strip()
        normalizado_dev = _normalizar_texto(texto_dev)
        if not normalizado_dev:
            continue
        for indice_frozen, item_frozen in enumerate(frozen_itens, 1):
            texto_frozen = str(item_frozen.get("text") or "").strip()
            normalizado_frozen = _normalizar_texto(texto_frozen)
            if not normalizado_frozen:
                continue
            similaridade = difflib.SequenceMatcher(
                None, normalizado_dev, normalizado_frozen
            ).ratio()
            par = {
                "linha_dev": indice_dev,
                "linha_frozen": indice_frozen,
                "texto_dev": texto_dev,
                "texto_frozen": texto_frozen,
                "intent_dev": str(item_dev.get("intent") or "").upper(),
                "intent_frozen": str(item_frozen.get("intent") or "").upper(),
                "family_dev": str(item_dev.get("family") or "").casefold(),
                "family_frozen": str(item_frozen.get("family") or "").casefold(),
                "similaridade": round(float(similaridade), 6),
                "mesmo_intent": str(item_dev.get("intent") or "").upper()
                == str(item_frozen.get("intent") or "").upper(),
            }
            if normalizado_dev == normalizado_frozen:
                duplicados_exatos.append(par)
            elif similaridade >= limiar:
                quase_duplicados.append(par)

    duplicados_exatos.sort(
        key=lambda item: (item["linha_dev"], item["linha_frozen"])
    )
    quase_duplicados.sort(
        key=lambda item: (
            -float(item["similaridade"]),
            item["linha_dev"],
            item["linha_frozen"],
        )
    )
    aprovado = not (
        familias_compartilhadas or duplicados_exatos or quase_duplicados
    )
    return {
        "versao": 1,
        "gerado_em": time.time(),
        "limiar_similaridade": limiar,
        "aprovado": aprovado,
        "totais": {
            "dev": len(dev_itens),
            "frozen": len(frozen_itens),
            "familias_compartilhadas": len(familias_compartilhadas),
            "pares_duplicados_exatos": len(duplicados_exatos),
            "pares_quase_duplicados": len(quase_duplicados),
        },
        "familias_compartilhadas": familias_compartilhadas,
        "duplicados_exatos": duplicados_exatos,
        "quase_duplicados": quase_duplicados,
        "contrato": {
            "somente_diagnostico": True,
            "altera_dataset": False,
            "autoriza_execucao": False,
            "aprovar_exige_ausencia_de_leakage_detectado": True,
        },
    }


def gerar_relatorio_qualidade(
    *,
    dev_path: str | Path,
    frozen_path: str | Path,
    destino: str | Path,
    limiar_similaridade: float = 0.9,
) -> dict[str, Any]:
    catalogo = intents_registradas()
    dev = carregar_jsonl(dev_path, intents_permitidas=catalogo)
    frozen = carregar_jsonl(frozen_path, intents_permitidas=catalogo)
    relatorio = auditar_leakage_dataset(
        dev,
        frozen,
        limiar_similaridade=limiar_similaridade,
    )
    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporario.replace(caminho)
    return relatorio


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", default="mente_laylay/neural/datasets/dev_v0.jsonl")
    parser.add_argument(
        "--frozen", default="mente_laylay/neural/datasets/frozen_v0.jsonl"
    )
    parser.add_argument(
        "--destino", default="memoria/neural/qualidade_dataset.json"
    )
    parser.add_argument("--limiar-similaridade", type=float, default=0.9)
    args = parser.parse_args()
    relatorio = gerar_relatorio_qualidade(
        dev_path=args.dev,
        frozen_path=args.frozen,
        destino=args.destino,
        limiar_similaridade=args.limiar_similaridade,
    )
    print(json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

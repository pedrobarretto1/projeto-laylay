"""Gera treino, calibração e holdout para um detector OOD isolado."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .gerar_ood_calibracao_v0 import (
    MOLDURAS_HOLDOUT as MOLDURAS_CALIBRACAO,
    OPERACOES_FORA_CATALOGO,
)


MOLDURAS_AVALIACAO = (
    "faz o seguinte: {texto}",
    "minha solicitação é esta: {texto}",
    "preciso desta ação: {texto}",
    "consegue fazer isto: {texto}",
    "assim que possível, {texto}",
)


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for (familia, dominio), frases in OPERACOES_FORA_CATALOGO.items():
        for indice, texto in enumerate(frases):
            base = {
                "family": f"ood_detector_v1_{familia}",
                "domain": dominio,
                "expected_ood": True,
                "source": "OOD_CURATED",
            }
            exemplos.extend(
                [
                    {**base, "text": texto, "partition": "training"},
                    {
                        **base,
                        "text": MOLDURAS_CALIBRACAO[indice].format(texto=texto),
                        "partition": "calibration",
                    },
                    {
                        **base,
                        "text": MOLDURAS_AVALIACAO[indice].format(texto=texto),
                        "partition": "evaluation",
                    },
                ]
            )
    return exemplos


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, int]:
    itens = [dict(item) for item in exemplos]
    textos = [_normalizar(item.get("text", "")) for item in itens]
    familias = Counter(str(item.get("family") or "") for item in itens)
    particoes = Counter(str(item.get("partition") or "") for item in itens)
    if len(textos) != len(set(textos)):
        raise ValueError("dataset do detector OOD contém textos duplicados")
    if any(item.get("expected_ood") is not True for item in itens):
        raise ValueError("todo exemplo precisa declarar expected_ood=true")
    resumo = {
        "total": len(itens),
        "familias": len(familias),
        "training": particoes["training"],
        "calibration": particoes["calibration"],
        "evaluation": particoes["evaluation"],
        "max_exemplos_por_familia": max(familias.values(), default=0),
    }
    esperado = {
        "total": 300,
        "familias": 20,
        "training": 100,
        "calibration": 100,
        "evaluation": 100,
        "max_exemplos_por_familia": 15,
    }
    if resumo != esperado:
        raise ValueError(f"cobertura do detector OOD inesperada: {resumo}")
    return resumo


def gravar(destino: str | Path) -> dict[str, int]:
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(
        "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
            for item in exemplos
        ),
        encoding="utf-8",
    )
    temporario.replace(caminho)
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=str(Path(__file__).with_name("ood_detector_v1.jsonl")),
    )
    args = parser.parse_args()
    print(json.dumps(gravar(args.destino), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

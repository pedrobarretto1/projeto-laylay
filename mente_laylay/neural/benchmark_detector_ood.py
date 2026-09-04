"""Benchmark isolado da cabeça de pertinência ao catálogo neural."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from mente_laylay.especialistas.capacidades import intents_registradas

from .calibracao_ood import (
    avaliar_detector_ood_prototipos,
    avaliar_detector_ood_semantico,
    carregar_dataset_ood,
)
from .dataset import carregar_jsonl
from .encoder_semantico import EncoderSemanticoONNX


def executar_benchmark(
    *,
    dev_path: str | Path,
    lotes_candidatos: list[str | Path],
    ood_path: str | Path,
    pasta_encoder: str | Path,
    destino: str | Path,
    sha256_encoder: str = "",
    n_splits: int = 5,
    alvo_falso_aceite_ood: float = 0.01,
    retencao_comandos_id_minima: float = 0.85,
    arquitetura: str = "sgd_catalog_membership",
) -> dict:
    catalogo = intents_registradas()
    caminhos = [Path(dev_path), *(Path(item) for item in lotes_candidatos)]
    exemplos_id = [
        exemplo
        for caminho in caminhos
        for exemplo in carregar_jsonl(caminho, intents_permitidas=catalogo)
    ]
    exemplos_ood = carregar_dataset_ood(ood_path)
    grupos = [
        str(item.get("validation_group") or item.get("family") or "")
        .strip()
        .casefold()
        for item in exemplos_id
    ]
    if any(not grupo for grupo in grupos):
        raise ValueError("todo exemplo ID precisa de grupo de validação")
    encoder = EncoderSemanticoONNX(
        pasta_encoder,
        sha256_modelo=sha256_encoder,
    )
    inicio = time.perf_counter()
    vetores_id = encoder.codificar(item["text"] for item in exemplos_id)
    vetores_ood = encoder.codificar(item["text"] for item in exemplos_ood)
    duracao_encoder = time.perf_counter() - inicio
    arquitetura_normalizada = str(arquitetura or "").strip().casefold()
    avaliador = (
        avaliar_detector_ood_semantico
        if arquitetura_normalizada == "sgd_catalog_membership"
        else avaliar_detector_ood_prototipos
        if arquitetura_normalizada == "prototype_distance"
        else None
    )
    if avaliador is None:
        raise ValueError(f"arquitetura OOD desconhecida: {arquitetura_normalizada}")
    relatorio = avaliador(
        exemplos_id,
        vetores_id,
        grupos,
        exemplos_ood,
        vetores_ood,
        n_splits=n_splits,
        alvo_falso_aceite_ood=alvo_falso_aceite_ood,
        retencao_comandos_id_minima=retencao_comandos_id_minima,
    )
    relatorio.update(
        {
            "gerado_em": time.time(),
            "dataset": {
                "arquivos_id": [item.name for item in caminhos],
                "ood": Path(ood_path).name,
            },
            "encoder": {
                "pasta": Path(pasta_encoder).name,
                "arquivo": encoder.arquivo_modelo,
                "sha256": str(sha256_encoder or ""),
                "dimensoes": int(vetores_id.shape[1]),
                "duracao_codificacao_s": round(duracao_encoder, 4),
            },
        }
    )
    caminho_destino = Path(destino)
    caminho_destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho_destino.with_suffix(caminho_destino.suffix + ".tmp")
    temporario.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporario.replace(caminho_destino)
    return relatorio


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", default="mente_laylay/neural/datasets/dev_v0.jsonl")
    parser.add_argument("--lote-candidato", action="append", default=[])
    parser.add_argument(
        "--ood",
        default="mente_laylay/neural/datasets/ood_detector_v2.jsonl",
    )
    parser.add_argument("--encoder", required=True)
    parser.add_argument("--sha256-encoder", default="")
    parser.add_argument("--splits", type=int, default=5)
    parser.add_argument("--ood-falso-aceite-maximo", type=float, default=0.01)
    parser.add_argument("--retencao-comandos-id-minima", type=float, default=0.85)
    parser.add_argument(
        "--arquitetura",
        choices=("prototype_distance", "sgd_catalog_membership"),
        default="sgd_catalog_membership",
    )
    parser.add_argument(
        "--destino",
        default="memoria/neural/benchmark_detector_ood_v2.json",
    )
    args = parser.parse_args()
    relatorio = executar_benchmark(
        dev_path=args.dev,
        lotes_candidatos=args.lote_candidato,
        ood_path=args.ood,
        pasta_encoder=args.encoder,
        destino=args.destino,
        sha256_encoder=args.sha256_encoder,
        n_splits=args.splits,
        alvo_falso_aceite_ood=args.ood_falso_aceite_maximo,
        retencao_comandos_id_minima=args.retencao_comandos_id_minima,
        arquitetura=args.arquitetura,
    )
    print(json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

"""Gera OOD com famílias inteiras separadas entre treino, calibração e teste."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .gerar_ood_calibracao_v0 import MOLDURAS_HOLDOUT, OPERACOES_FORA_CATALOGO


OPERACOES_HOLDOUT: dict[tuple[str, str], tuple[str, ...]] = {
    ("contact_manage", "contacts"): (
        "adiciona a Marina aos meus contatos",
        "remove o telefone antigo do Carlos",
        "muda o número da Ana para este aqui",
        "cria um contato chamado assistência técnica",
        "junta os contatos duplicados do João",
    ),
    ("vpn_control", "system"): (
        "conecta na VPN do trabalho",
        "desliga a VPN agora",
        "troca para o servidor VPN de São Paulo",
        "adiciona esta configuração de VPN",
        "remove a VPN antiga da empresa",
    ),
    ("printer_control", "printer"): (
        "imprime duas cópias deste documento",
        "cancela a impressão atual",
        "define a impressora da sala como padrão",
        "digitaliza esta página em PDF",
        "mostra a fila da impressora",
    ),
    ("airplane_mode", "system"): (
        "ativa o modo avião",
        "desliga o modo avião",
        "coloca o notebook em modo avião",
        "mantém o modo avião até amanhã",
        "tira o computador do modo avião",
    ),
    ("power_mode", "system"): (
        "ativa a economia de bateria",
        "muda para o modo de alto desempenho",
        "desliga o modo de economia de energia",
        "limita a carga da bateria a oitenta por cento",
        "mostra quais aplicativos gastam mais bateria",
    ),
    ("screen_record", "system"): (
        "começa a gravar a tela",
        "para a gravação da tela",
        "grava esta janela com o áudio",
        "salva a gravação na pasta vídeos",
        "captura um vídeo dos próximos trinta segundos",
    ),
    ("archive_compress", "files"): (
        "compacta esta pasta em zip",
        "extrai o arquivo compactado aqui",
        "cria um arquivo rar com estes documentos",
        "descompacta as fotos na área de trabalho",
        "protege o arquivo zip com uma senha",
    ),
    ("cloud_upload", "cloud"): (
        "envia este relatório para a nuvem",
        "baixa a pasta compartilhada do drive",
        "sincroniza minhas fotos com a nuvem",
        "compartilha o arquivo pelo armazenamento online",
        "remove a cópia deste documento da nuvem",
    ),
    ("download_manage", "browser"): (
        "cancela o download atual",
        "pausa todos os downloads",
        "continua baixando o arquivo grande",
        "abre a pasta dos downloads concluídos",
        "limpa o histórico de downloads",
    ),
    ("navigation_route", "maps"): (
        "traça uma rota até o aeroporto",
        "mostra o caminho para o posto mais próximo",
        "evita pedágios no trajeto para casa",
        "inicia a navegação até o escritório",
        "adiciona uma parada na farmácia",
    ),
}


def gerar_exemplos() -> list[dict[str, Any]]:
    operacoes = list(OPERACOES_FORA_CATALOGO.items()) + list(OPERACOES_HOLDOUT.items())
    exemplos: list[dict[str, Any]] = []
    for indice_operacao, ((familia, dominio), frases) in enumerate(operacoes):
        particao = (
            "training"
            if indice_operacao < 10
            else "calibration"
            if indice_operacao < 20
            else "evaluation"
        )
        for indice, texto in enumerate(frases):
            base = {
                "family": f"ood_detector_v2_{familia}",
                "domain": dominio,
                "expected_ood": True,
                "source": "OOD_CURATED",
                "partition": particao,
            }
            exemplos.append({**base, "text": texto})
            exemplos.append(
                {
                    **base,
                    "text": MOLDURAS_HOLDOUT[indice].format(texto=texto),
                }
            )
    return exemplos


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, int]:
    itens = [dict(item) for item in exemplos]
    textos = [_normalizar(item.get("text", "")) for item in itens]
    familias_por_particao = {
        particao: {
            str(item.get("family") or "")
            for item in itens
            if item.get("partition") == particao
        }
        for particao in ("training", "calibration", "evaluation")
    }
    if len(textos) != len(set(textos)):
        raise ValueError("dataset OOD v2 contém textos duplicados")
    compartilhadas = (
        (familias_por_particao["training"] & familias_por_particao["calibration"])
        | (familias_por_particao["training"] & familias_por_particao["evaluation"])
        | (familias_por_particao["calibration"] & familias_por_particao["evaluation"])
    )
    if compartilhadas:
        raise ValueError(f"famílias OOD vazaram entre partições: {compartilhadas}")
    particoes = Counter(str(item.get("partition") or "") for item in itens)
    familias = {str(item.get("family") or "") for item in itens}
    resumo = {
        "total": len(itens),
        "familias": len(familias),
        "familias_training": len(familias_por_particao["training"]),
        "familias_calibration": len(familias_por_particao["calibration"]),
        "familias_evaluation": len(familias_por_particao["evaluation"]),
        "training": particoes["training"],
        "calibration": particoes["calibration"],
        "evaluation": particoes["evaluation"],
    }
    esperado = {
        "total": 300,
        "familias": 30,
        "familias_training": 10,
        "familias_calibration": 10,
        "familias_evaluation": 10,
        "training": 100,
        "calibration": 100,
        "evaluation": 100,
    }
    if resumo != esperado:
        raise ValueError(f"cobertura OOD v2 inesperada: {resumo}")
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
        default=str(Path(__file__).with_name("ood_detector_v2.jsonl")),
    )
    args = parser.parse_args()
    print(json.dumps(gravar(args.destino), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

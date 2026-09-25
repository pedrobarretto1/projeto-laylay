"""Ablação local de um payload capturado; não abre runtime ou executa propostas.

Geração experimental, não treino nem certificação. Artefatos podem conter
contexto pessoal e ficam somente em resultados_testes (não publicar).
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import json
from pathlib import Path
import time

import requests


RAIZ = Path(__file__).resolve().parents[2]
VARIANTES = ("capturado", "sem_contrato", "identidade_formato", "minimo")


def carregar_payload(captura: Path, texto: str) -> dict:
    origem = captura.resolve(strict=True)
    if not origem.is_relative_to((RAIZ / "resultados_testes").resolve()):
        raise ValueError("captura deve pertencer a resultados_testes")
    encontrados = []
    for linha in origem.read_text(encoding="utf-8").splitlines():
        evento = json.loads(linha)
        if evento.get("etapa") != "envio":
            continue
        payload = evento["payload"]
        usuario = next((m["content"] for m in reversed(payload["messages"])
                        if m.get("role") == "user"), "")
        if usuario == texto:
            encontrados.append(payload)
    if len(encontrados) != 1:
        raise ValueError("exige exatamente um envio correspondente ao texto")
    return encontrados[0]


def preparar_variante(original: dict, variante: str, texto: str, seed: int) -> dict:
    payload = copy.deepcopy(original)
    mensagens = payload["messages"]
    if mensagens[0]["role"] != "system" or mensagens[-1]["role"] != "user":
        raise ValueError("estrutura inesperada; não inferir posições")
    mensagens[-1]["content"] = texto
    if variante in {"identidade_formato", "minimo"}:
        base = mensagens[0]["content"]
        marcador = "Retorne somente JSON válido"
        if marcador not in base:
            raise ValueError("schema capturado ausente")
        mensagens[0]["content"] = (
            "Você é Laylay, uma assistente local. Converse em português brasileiro, "
            "respondendo ao usuário no contexto do diálogo. "
            + base[base.index(marcador):]
        )
    if variante in {"sem_contrato", "minimo"}:
        payload["messages"] = [mensagens[0], *(m for m in mensagens[1:] if m["role"] != "system")]
    payload["seed"] = seed
    payload["stream"] = False
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captura", type=Path, required=True)
    parser.add_argument("--texto-origem", default="quero im")
    parser.add_argument("--textos", nargs="+", default=["quero im", "quero sim"])
    parser.add_argument("--variantes", nargs="+", choices=VARIANTES, default=list(VARIANTES))
    parser.add_argument("--seeds", nargs="+", type=int, default=[17])
    args = parser.parse_args()
    if len(args.textos) * len(args.variantes) * len(args.seeds) > 48:
        parser.error("máximo de 48 chamadas por investigação")
    original = carregar_payload(args.captura, args.texto_origem)
    pasta = RAIZ / "resultados_testes" / ("continuacao_incerta-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    pasta.mkdir(exist_ok=False)
    print(f"ARTEFATOS: {pasta}", flush=True)
    for seed in args.seeds:
        for texto in args.textos:
            for variante in args.variantes:
                payload = preparar_variante(original, variante, texto, seed)
                inicio = time.perf_counter()
                resposta = requests.post("http://127.0.0.1:11434/v1/chat/completions",
                                         json=payload, timeout=90)
                resposta.raise_for_status()
                bruto = resposta.json()
                escolha = bruto["choices"][0]
                conteudo = escolha["message"]["content"]
                try:
                    dados = json.loads(conteudo)
                except ValueError:
                    dados = {}
                fala = dados.get("fala", conteudo) if isinstance(dados, dict) else conteudo
                registro = dict(variante=variante, seed=seed, texto=texto, payload=payload,
                                resposta=bruto, segundos=time.perf_counter() - inicio)
                with (pasta / "comparacao.jsonl").open("a", encoding="utf-8") as arquivo:
                    arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
                print(json.dumps(dict(variante=variante, seed=seed, texto=texto,
                                      fala=fala, fim=escolha.get("finish_reason")),
                                 ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

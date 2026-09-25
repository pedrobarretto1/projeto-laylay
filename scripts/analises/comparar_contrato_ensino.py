"""Ablação local de instruções didáticas em payloads reais, sem abrir a Laylay.

Os artefatos contêm contexto de conversa e devem permanecer em resultados_testes.
Esta sonda compara geração, não valida conhecimento nem promove um contrato.
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
PERGUNTAS = (
    "agora me ensina a diferença entre força e energia na engenharia",
    "mudando para arquitetura, me ensina a diferença entre planta baixa e corte",
    "agora me ensina a diferença entre I am e I have em inglês",
    "agora me ensina a diferença entre plantas anuais e perenes na floricultura",
)


def carregar_envios(captura: Path) -> dict[str, dict]:
    origem = captura.resolve(strict=True)
    if not origem.is_relative_to((RAIZ / "resultados_testes").resolve()):
        raise ValueError("captura deve pertencer a resultados_testes")
    envios: dict[str, dict] = {}
    for linha in origem.read_text(encoding="utf-8").splitlines():
        evento = json.loads(linha)
        if evento.get("etapa") != "envio":
            continue
        payload = evento["payload"]
        texto = next(
            (m["content"] for m in reversed(payload["messages"]) if m.get("role") == "user"),
            "",
        )
        if texto in PERGUNTAS:
            if texto in envios:
                raise ValueError(f"envio duplicado: {texto}")
            envios[texto] = payload
    ausentes = set(PERGUNTAS) - set(envios)
    if ausentes:
        raise ValueError(f"perguntas ausentes: {sorted(ausentes)}")
    return envios


def preparar(original: dict, variante: str, seed: int) -> dict:
    payload = copy.deepcopy(original)
    payload["seed"] = seed
    payload["stream"] = False
    if variante == "contrato_literatura":
        inicial = payload["messages"][0]
        antigo = "Em correção factual, abandone o erro. Fatos exigem evidência no mesmo turno."
        novo = (
            "Em correção factual, abandone o erro. Estado atual, ações e alegações "
            "sobre fontes externas exigem evidência deste turno; conhecimento geral "
            "estável pode ser explicado como tal, sem fingir verificação externa."
        )
        if antigo not in inicial["content"]:
            raise ValueError("regra factual global não encontrada")
        inicial["content"] = inicial["content"].replace(antigo, novo, 1)
        contrato = next(
            (m for m in payload["messages"] if m.get("role") == "system"
             and "Roteiro concreto: estratégia=explicacao_didatica" in m["content"]),
            None,
        )
        if contrato is None:
            raise ValueError("contrato didático não encontrado")
        linhas = contrato["content"].splitlines()
        indice = next(
            (i for i, linha in enumerate(linhas) if linha.startswith("Base permitida para afirmar:")),
            None,
        )
        if indice is None:
            raise ValueError("base factual não encontrada")
        linhas[indice] = (
            "Para conceitos gerais estáveis, use conhecimento próprio sem alegar pesquisa "
            "ou certeza sobre detalhe desconhecido. Primeiro dê definições literais corretas; "
            "depois um exemplo que respeite essas definições; por fim revise se exemplo e "
            "conclusão continuam verdadeiros. Não troque definição por analogia. Se faltar "
            "conhecimento confiável, delimite a dúvida e ofereça pesquisa."
        )
        contrato["content"] = "\n".join(linhas)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captura", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[17])
    args = parser.parse_args()
    if len(args.seeds) > 3:
        parser.error("máximo de três seeds")
    envios = carregar_envios(args.captura)
    pasta = RAIZ / "resultados_testes" / (
        "comparacao_contrato_ensino-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    )
    pasta.mkdir(exist_ok=False)
    print(f"ARTEFATOS: {pasta}", flush=True)
    for seed in args.seeds:
        for pergunta in PERGUNTAS:
            for variante in ("capturado", "contrato_literatura"):
                payload = preparar(envios[pergunta], variante, seed)
                inicio = time.perf_counter()
                resposta = requests.post(
                    "http://127.0.0.1:11434/v1/chat/completions",
                    json=payload,
                    timeout=90,
                )
                resposta.raise_for_status()
                bruto = resposta.json()
                escolha = bruto["choices"][0]
                conteudo = escolha["message"]["content"]
                try:
                    dados = json.loads(conteudo)
                except ValueError:
                    dados = {}
                fala = dados.get("fala", conteudo) if isinstance(dados, dict) else conteudo
                registro = {
                    "variante": variante,
                    "seed": seed,
                    "pergunta": pergunta,
                    "fala": fala,
                    "segundos": time.perf_counter() - inicio,
                    "finish_reason": escolha.get("finish_reason"),
                }
                with (pasta / "comparacao.jsonl").open("a", encoding="utf-8") as arquivo:
                    arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
                print(json.dumps(registro, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

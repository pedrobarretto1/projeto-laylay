"""Candidata isolada: exigir recibo por cada oração unida por 'e'.

Não é um segmentador linguístico geral nem um verificador de produção. Mede
se a primeira fronteira RED (aprovar só a metade correta) persiste mesmo
quando todas as partes precisam de apoio separado.
"""

from __future__ import annotations

import json
import re
import time

import requests

from scripts.analises.sonda_implicacao_inedita import CASOS, FONTES, prova_localizada


def fragmentos_explicitos(alegacao: str) -> list[str]:
    return [parte.strip() for parte in re.split(r"\s+e\s+", alegacao, flags=re.I) if parte.strip()]


def consolidar(partes: list[dict], quantidade_esperada: int, fonte: str) -> dict:
    ids_esperados = list(range(1, quantidade_esperada + 1))
    if (
        len(partes) != quantidade_esperada
        or [item.get("id") for item in partes if isinstance(item, dict)] != ids_esperados
        or any(not isinstance(item, dict) for item in partes)
    ):
        return {"classe": "invalida", "prova_localizada": False}
    if not all(prova_localizada(item.get("classe"), item.get("trecho_literal"), fonte) for item in partes):
        return {"classe": "invalida", "prova_localizada": False}
    classes = {item["classe"] for item in partes}
    classe = (
        "contradita" if "contradita" in classes
        else "sem_prova" if "sem_prova" in classes
        else "sustentada"
    )
    return {"classe": classe, "prova_localizada": True}


def avaliar_por_partes(alegacao: str, fonte: str) -> dict:
    fragmentos = fragmentos_explicitos(alegacao)
    partes_numeradas = "\n".join(f"{i}. {parte}" for i, parte in enumerate(fragmentos, 1))
    mensagens = [
        {"role": "system", "content": (
            "Você julga CADA PARTE numerada de uma alegação contra a mesma frase-fonte. "
            "Leia a alegação completa para resolver sujeito omitido, mas não use fatos externos. "
            "Para cada parte: sustentada se a frase implica toda a parte; contradita "
            "se diz o oposto; sem_prova se faltar condição, número, efeito ou detalhe. "
            "Aprovar uma parte não aprova as outras. Retorne JSON com 'partes', "
            "uma lista na mesma ordem e quantidade, cada item com id numérico, "
            "classe e trecho_literal. Para sustentada/contradita copie um trecho "
            "literal da fonte; para sem_prova use trecho_literal vazio."
        )},
        {"role": "user", "content": (
            f"Fonte literal: {fonte}\nAlegação completa: {alegacao}\n"
            f"Partes a julgar separadamente:\n{partes_numeradas}"
        )},
    ]
    inicio = time.monotonic()
    try:
        resposta = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": "qwen3:4b-instruct", "messages": mensagens,
                  "stream": False, "format": "json",
                  "options": {"temperature": 0, "num_predict": 250}},
            timeout=80,
        )
        resposta.raise_for_status()
        bruto = json.loads(resposta.json()["message"]["content"])
        itens = bruto.get("partes")
        if not isinstance(itens, list):
            raise ValueError("partes ausentes")
        resultado = consolidar(itens, len(fragmentos), fonte)
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        itens = []
        resultado = {"classe": "invalida", "prova_localizada": False}
        erro = type(exc).__name__
    return {
        **resultado, "partes": itens, "fragmentos": fragmentos,
        "latencia_s": round(time.monotonic() - inicio, 3), "erro": erro,
    }


def main() -> int:
    totais = {campo: {"acertos": 0, "n": 0} for campo in ("definicao", "exemplo")}
    falsos_positivos = 0
    latencias = []
    for id_caso, id_fonte, campo, alegacao, esperado in CASOS:
        resposta = avaliar_por_partes(alegacao, FONTES[id_fonte]["texto"])
        ok = resposta["classe"] == esperado and resposta["prova_localizada"]
        totais[campo]["acertos"] += int(ok)
        totais[campo]["n"] += 1
        falsos_positivos += int(esperado != "sustentada" and resposta["classe"] == "sustentada")
        latencias.append(resposta["latencia_s"])
        print(json.dumps({"id": id_caso, "esperado": esperado, "observado": resposta, "correto": ok}, ensure_ascii=False), flush=True)
    aprovado = all(v["acertos"] == v["n"] for v in totais.values()) and not falsos_positivos
    print(json.dumps({
        "totais": totais, "falsos_positivos_sustentada": falsos_positivos,
        "latencia_total_s": round(sum(latencias), 2),
        "portao_desenvolvimento": aprovado,
        "aprovado_para_producao": False,
    }, ensure_ascii=False), flush=True)
    return 0 if aprovado else 1


if __name__ == "__main__":
    raise SystemExit(main())

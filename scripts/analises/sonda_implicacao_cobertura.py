"""Experimento: proposições com cobertura íntegra do texto da alegação.

O modelo propõe segmentos; o código exige que eles reconstruam a frase
original na ordem, sem omissão, e que cada recibo cite trecho literal da
fonte. Não é verificador independente nem participa do runtime.
"""

from __future__ import annotations

from collections import Counter
import json
import re
import time
import unicodedata

import requests

from scripts.analises.sonda_implicacao_inedita import CASOS, FONTES, prova_localizada


_PALAVRAS_FUNCIONAIS = frozenset({
    "a", "as", "o", "os", "um", "uma", "e", "de", "da", "das", "do", "dos",
    "em", "na", "nas", "no", "nos", "para", "por", "se", "que", "ao", "aos",
})


def _normalizar_espacos(texto: str) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip()


def _palavras_relevantes(texto: str) -> Counter[str]:
    sem_acentos = "".join(
        letra for letra in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(letra)
    )
    return Counter(
        palavra for palavra in re.findall(r"\w+", sem_acentos)
        if palavra not in _PALAVRAS_FUNCIONAIS
    )


def _segmento_fiel(item: dict) -> bool:
    trecho = str(item.get("trecho_original") or "")
    proposicao = str(item.get("proposicao") or "")
    return bool(trecho and proposicao) and not (
        _palavras_relevantes(trecho) - _palavras_relevantes(proposicao)
    )


def consolidar(alegacao: str, partes: list[dict], fonte: str) -> dict:
    """Fail-closed para segmentos ausentes, paráfrase sem cobertura ou recibo falso."""
    if not isinstance(partes, list) or not partes or any(not isinstance(p, dict) for p in partes):
        return {"classe": "invalida", "cobertura": False, "provas_localizadas": False}
    cobertura = _normalizar_espacos(" ".join(str(p.get("trecho_original") or "") for p in partes)) == _normalizar_espacos(alegacao)
    fidelidade = all(_segmento_fiel(p) for p in partes)
    provas = all(
        prova_localizada(p.get("classe"), p.get("trecho_literal"), fonte)
        for p in partes
    )
    if not (cobertura and fidelidade and provas):
        return {"classe": "invalida", "cobertura": cobertura and fidelidade, "provas_localizadas": provas}
    classes = {p["classe"] for p in partes}
    classe = "contradita" if "contradita" in classes else "sem_prova" if "sem_prova" in classes else "sustentada"
    return {"classe": classe, "cobertura": True, "provas_localizadas": True}


def avaliar_com_cobertura(alegacao: str, fonte: str) -> dict:
    mensagens = [
        {"role": "system", "content": (
            "Você verifica uma alegação contra UMA frase-fonte, sem conhecimento externo. "
            "Separe a alegação em proposições verificáveis distintas quando houver "
            "mais de um efeito, condição ou quantidade; não separe uma lista de "
            "entidades que participa de uma só relação. Retorne JSON com 'partes'. "
            "Cada parte tem: trecho_original (cópia literal de um pedaço da "
            "alegação; todos os pedaços concatenados com espaços devem reconstruir "
            "a alegação inteira em ordem), proposicao (autocontida, preservando "
            "cada palavra de conteúdo do trecho), classe e trecho_literal. "
            "sustentada só se a fonte implica toda a proposicao; contradita só "
            "se fonte e proposicao não podem coexistir; caso contrário sem_prova. "
            "Copie para trecho_literal uma parte EXATA da fonte quando sustentada "
            "ou contradita. Para sem_prova, use string vazia. Não ignore detalhes "
            "da alegação só porque o início dela está correto."
        )},
        {"role": "user", "content": f"Fonte literal: {fonte}\nAlegação: {alegacao}"},
    ]
    inicio = time.monotonic()
    try:
        resposta = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": "qwen3:4b-instruct", "messages": mensagens,
                  "stream": False, "format": "json",
                  "options": {"temperature": 0, "num_predict": 320}},
            timeout=80,
        )
        resposta.raise_for_status()
        bruto = json.loads(resposta.json()["message"]["content"])
        partes = bruto.get("partes")
        resultado = consolidar(alegacao, partes, fonte)
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        partes = []
        resultado = {"classe": "invalida", "cobertura": False, "provas_localizadas": False}
        erro = type(exc).__name__
    return {**resultado, "partes": partes,
            "latencia_s": round(time.monotonic() - inicio, 3), "erro": erro}


def main() -> int:
    totais = {campo: {"acertos": 0, "n": 0} for campo in ("definicao", "exemplo")}
    falsos_positivos = 0
    latencias = []
    for id_caso, id_fonte, campo, alegacao, esperado in CASOS:
        resposta = avaliar_com_cobertura(alegacao, FONTES[id_fonte]["texto"])
        ok = resposta["classe"] == esperado and resposta["cobertura"] and resposta["provas_localizadas"]
        totais[campo]["acertos"] += int(ok)
        totais[campo]["n"] += 1
        falsos_positivos += int(esperado != "sustentada" and resposta["classe"] == "sustentada")
        latencias.append(resposta["latencia_s"])
        print(json.dumps({"id": id_caso, "esperado": esperado, "observado": resposta, "correto": ok}, ensure_ascii=False), flush=True)
    aprovado = all(v["acertos"] == v["n"] for v in totais.values()) and not falsos_positivos
    print(json.dumps({"totais": totais, "falsos_positivos_sustentada": falsos_positivos,
                      "latencia_total_s": round(sum(latencias), 2),
                      "portao_desenvolvimento": aprovado,
                      "aprovado_para_producao": False}, ensure_ascii=False), flush=True)
    return 0 if aprovado else 1


if __name__ == "__main__":
    raise SystemExit(main())

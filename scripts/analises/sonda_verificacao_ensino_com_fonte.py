"""Sonda isolada: o Qwen consegue julgar alegações usando trechos já lidos?

Não altera o runtime nem promove o verificador. Usa controles positivos,
contraditórios e sem prova extraídos de uma sonda real de ensino.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import requests


RAIZ = Path(__file__).resolve().parents[2]
PLANOS = RAIZ / "resultados_testes" / "roteiro_ensino_multidominio-20260923-132343-110341" / "planos.jsonl"
# Gabarito da *fonte disponível*, não do conhecimento geral de botânica.
# E2 em planta baixa diz "vista horizontal", mas não resolve explicitamente
# "de baixo para cima". A fonte da fotossíntese descreve luz -> energia química,
# mas não exclui logicamente toda alegação sobre CO2: nesse caso é sem_prova.
CASOS = (
    (12, "Uma planta baixa representa a vista superior de uma edificação.", "sustentada", ("E5",)),
    (12, "Uma planta baixa é a vista da casa de baixo para cima.", "contradita", ("E5",)),
    (12, "O corte arquitetônico é a vista superior dos cômodos.", "contradita", ("E3",)),
    (3, "Na fotossíntese, a energia da luz é convertida em energia química.", "sustentada", ("E2", "E3")),
    (3, "Na fotossíntese, a luz é transformada em dióxido de carbono.", "sem_prova", ("E0",)),
    (19, "Plantas perenes podem viver por muitos anos.", "sustentada", ("E7",)),
    (19, "Plantas perenes sempre morrem ao fim de um ano.", "contradita", ("E7",)),
    (19, "Plantas anuais vivem mais de dois anos.", "contradita", ("E5", "E12")),
    (12, "Toda planta baixa contém exatamente sete janelas.", "sem_prova", ("E0",)),
    (3, "Uma folha no escuro por uma hora não faz nada além de respirar.", "sem_prova", ("E0",)),
)


def carregar_fontes() -> dict[int, list[dict[str, str]]]:
    if not PLANOS.is_file():
        raise FileNotFoundError(f"artefato da sonda anterior indisponível: {PLANOS}")
    fontes: dict[int, list[dict[str, str]]] = {}
    for indice, linha in enumerate(PLANOS.read_text(encoding="utf-8").splitlines()):
        if indice not in {caso[0] for caso in CASOS}:
            continue
        registro = json.loads(linha)
        fundamentacao = registro["plano"]["fundamentacao_factual"]
        fontes[indice] = [
            {"url": str(item["url"]), "trecho": str(item["trecho"])}
            for item in fundamentacao["fontes"]
            if item.get("url") and item.get("trecho")
        ]
    if any(not fontes.get(indice) for indice, *_ in CASOS):
        raise ValueError("um ou mais casos não possuem fontes lidas no artefato")
    return fontes


def frases_fonte(fontes: list[dict[str, str]]) -> list[dict[str, str]]:
    """Atribui IDs estáveis a frases literalmente presentes nas páginas lidas."""
    frases: list[dict[str, str]] = []
    vistas: set[str] = set()
    for fonte in fontes:
        trecho = fonte["trecho"]
        for frase in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý“\"(])", trecho):
            frase = frase.strip()
            if (
                not frase.endswith((".", "!", "?"))
                or not 35 <= len(frase) <= 300
                or frase in vistas
            ):
                continue
            vistas.add(frase)
            frases.append({"id": f"E{len(frases) + 1}", "url": fonte["url"], "texto": frase})
    return frases


def avaliar(alegacao: str, fontes: list[dict[str, str]]) -> dict:
    frases = frases_fonte(fontes)
    evidencia = "\n".join(f"{item['id']}: {item['texto']}" for item in frases)
    mensagens = [
        {"role": "system", "content": (
            "Você verifica uma única alegação contra frases de fontes fornecidas. "
            "Não use conhecimento externo nem a sua confiança pessoal. "
            "Escolha sustentada apenas se uma frase realmente implicar a alegação; "
            "contradita apenas se uma frase afirmar o oposto; senão sem_prova. "
            "Responda JSON: {\"classe\":\"sustentada|contradita|sem_prova\","
            "\"id_evidencia\":\"E0\"}. Escolha um ID E1... para sustentada "
            "ou contradita; E0 para sem_prova. Não copie nem reescreva as frases."
        )},
        {"role": "user", "content": f"Alegação: {alegacao}\nFrases:\n{evidencia}"},
    ]
    resposta = requests.post(
        "http://127.0.0.1:11434/api/chat",
        json={"model": "qwen3:4b-instruct", "messages": mensagens,
              "stream": False, "format": "json",
              "options": {"temperature": 0, "num_predict": 160}},
        timeout=80,
    )
    resposta.raise_for_status()
    bruto = json.loads(resposta.json()["message"]["content"])
    classe = str(bruto.get("classe") or "")
    id_evidencia = str(bruto.get("id_evidencia") or "")
    escolhida = next((item for item in frases if item["id"] == id_evidencia), None)
    return {"classe": classe, "id_evidencia": id_evidencia,
            "evidencia": escolhida or {}, "quantidade_frases": len(frases)}


def avaliar_par(alegacao: str, frase: dict[str, str]) -> str:
    """Controle diagnóstico: testa implicação isolada, sem disputa entre fontes."""
    mensagens = [
        {"role": "system", "content": (
            "Julgue somente a frase fornecida, sem usar conhecimento externo. "
            "Sustentada: a frase implica diretamente a alegação. "
            "Contradita: a frase afirma diretamente o oposto. "
            "Se apenas fala do tema, é ambígua, ou poderia coexistir com a "
            "alegação, escolha sem_prova. Responda JSON: "
            '{"classe":"sustentada|contradita|sem_prova"}.'
        )},
        {"role": "user", "content": f"Alegação: {alegacao}\nFrase: {frase['texto']}"},
    ]
    resposta = requests.post(
        "http://127.0.0.1:11434/api/chat",
        json={"model": "qwen3:4b-instruct", "messages": mensagens,
              "stream": False, "format": "json",
              "options": {"temperature": 0, "num_predict": 80}},
        timeout=80,
    )
    resposta.raise_for_status()
    return str(json.loads(resposta.json()["message"]["content"]).get("classe") or "")


def resultado_rastreavel(resultado: dict, classe_esperada: str, ids_aceitos: tuple[str, ...]) -> bool:
    """Só aprova rótulo e prova semanticamente curada no artefato congelado."""
    if resultado["classe"] != classe_esperada or resultado["id_evidencia"] not in ids_aceitos:
        return False
    return (not resultado["evidencia"]) if classe_esperada == "sem_prova" else bool(resultado["evidencia"])


def main() -> int:
    fontes = carregar_fontes()
    rotulos_corretos = 0
    acertos = 0
    for indice, alegacao, esperado, ids_aceitos in CASOS:
        resultado = avaliar(alegacao, fontes[indice])
        rotulo_correto = resultado["classe"] == esperado
        rotulos_corretos += int(rotulo_correto)
        correto = resultado_rastreavel(resultado, esperado, ids_aceitos)
        acertos += int(correto)
        print(json.dumps({"indice": indice, "alegacao": alegacao,
                          "esperado": esperado, "observado": resultado,
                          "correto": correto}, ensure_ascii=False), flush=True)
    print(f"Rótulos: {rotulos_corretos}/{len(CASOS)}; "
          f"rótulo com rastreabilidade válida: {acertos}/{len(CASOS)}. "
          "Isto não aprova o ensino no runtime.")
    return 0 if acertos == len(CASOS) else 1


if __name__ == "__main__":
    sys.exit(main())

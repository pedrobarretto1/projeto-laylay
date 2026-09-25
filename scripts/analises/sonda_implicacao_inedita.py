"""Holdout de implicação didática com fontes novas e prova literal.

Somente diagnóstico local. O gabarito foi fixado antes da primeira execução;
não ajustar o prompt ou os rótulos para elevar a pontuação desta amostra.
Uma citação literal localizada é necessária, mas não prova implicação sozinha.
"""

from __future__ import annotations

import json
import re
import time

import requests

from scripts.analises.sonda_implicacao_didatica import avaliar as avaliar_anterior


FONTES = {
    "python_for": {
        "url": "https://docs.python.org/3.11/tutorial/controlflow.html",
        "texto": (
            "Python’s for statement iterates over the items of any sequence "
            "(a list or a string), in the order that they appear"
        ),
    },
    "evaporacao": {
        "url": "https://science.nasa.gov/kids/earth/what-is-the-water-cycle/",
        "texto": (
            "Evaporation occurs when liquid water turns into gaseous water vapor "
            "in our atmosphere."
        ),
    },
    "circuito_serie": {
        "url": "https://openstax.org/books/physics/pages/19-2-series-circuits",
        "texto": (
            "Components connected in series are connected one after the other "
            "in the same branch of a circuit"
        ),
    },
}

# id, fonte, campo didático, alegação, implicação pela frase fornecida.
CASOS = (
    ("P-D1", "python_for", "definicao", "Em Python, for percorre os itens de uma sequência na ordem em que aparecem.", "sustentada"),
    ("P-D2", "python_for", "definicao", "Em Python, for percorre os itens de uma lista na ordem inversa.", "contradita"),
    ("P-D3", "python_for", "definicao", "Em Python, for sempre é mais rápido que while.", "sem_prova"),
    ("P-D4", "python_for", "definicao", "Em Python, for percorre uma lista em ordem e termina em dois milissegundos.", "sem_prova"),
    ("P-E1", "python_for", "exemplo", "Se a sequência é ['a', 'b'], um for encontra 'a' antes de 'b'.", "sustentada"),
    ("P-E2", "python_for", "exemplo", "Se a lista é ['a', 'b'], um for encontra 'b' antes de 'a'.", "contradita"),
    ("P-E3", "python_for", "exemplo", "Ao percorrer ['a', 'b'], for consome exatamente 12 bytes.", "sem_prova"),
    ("P-E4", "python_for", "exemplo", "Um for sobre ['a', 'b'] visita 'a' antes de 'b' e imprime ambos automaticamente.", "sem_prova"),
    ("N-D1", "evaporacao", "definicao", "Evaporação transforma água líquida em vapor de água.", "sustentada"),
    ("N-D2", "evaporacao", "definicao", "Evaporação transforma água líquida em gelo sólido.", "contradita"),
    ("N-D3", "evaporacao", "definicao", "Evaporação sempre leva vinte minutos.", "sem_prova"),
    ("N-D4", "evaporacao", "definicao", "Evaporação transforma água líquida em vapor e sempre leva vinte minutos.", "sem_prova"),
    ("N-E1", "evaporacao", "exemplo", "Se a água líquida de um recipiente evaporar, ela se tornará vapor de água.", "sustentada"),
    ("N-E2", "evaporacao", "exemplo", "Se a água líquida de um recipiente evaporar, ela se tornará gelo.", "contradita"),
    ("N-E3", "evaporacao", "exemplo", "Uma poça de dois litros evapora em trinta minutos.", "sem_prova"),
    ("N-E4", "evaporacao", "exemplo", "A água de uma poça evapora em vapor e reduz exatamente dois graus na vizinhança.", "sem_prova"),
    ("O-D1", "circuito_serie", "definicao", "Componentes em série ficam um após o outro no mesmo ramo do circuito.", "sustentada"),
    ("O-D2", "circuito_serie", "definicao", "Componentes em série ficam cada um em um ramo distinto.", "contradita"),
    ("O-D3", "circuito_serie", "definicao", "Componentes em série recebem sempre a mesma tensão elétrica.", "sem_prova"),
    ("O-D4", "circuito_serie", "definicao", "Componentes em série ficam no mesmo ramo e sempre recebem três volts.", "sem_prova"),
    ("O-E1", "circuito_serie", "exemplo", "Se R1 e R2 estão em série, ambos ficam no mesmo ramo, um depois do outro.", "sustentada"),
    ("O-E2", "circuito_serie", "exemplo", "Se R1 e R2 estão em série, ficam em ramos diferentes.", "contradita"),
    ("O-E3", "circuito_serie", "exemplo", "Dois resistores de dez ohms em série consomem cinco watts.", "sem_prova"),
    ("O-E4", "circuito_serie", "exemplo", "Dois resistores em série ficam no mesmo ramo e têm corrente de três ampères.", "sem_prova"),
)


def prova_localizada(classe: str, trecho_literal: str, fonte: str) -> bool:
    """Valida apenas a rastreabilidade do recibo, nunca a semântica."""
    if classe not in {"sustentada", "contradita", "sem_prova"}:
        return False
    trecho = re.sub(r"\s+", " ", str(trecho_literal or "")).strip()
    texto = re.sub(r"\s+", " ", str(fonte or "")).strip()
    if classe == "sem_prova":
        return not trecho
    return len(trecho) >= 15 and trecho in texto


def avaliar_com_prova(alegacao: str, texto_fonte: str) -> dict:
    mensagens = [
        {"role": "system", "content": (
            "Julgue APENAS se a frase-fonte implica a alegação, sem usar conhecimento externo. "
            "sustentada: a frase afirma a mesma relação, inclusive paráfrase sem detalhes novos; "
            "contradita: as duas não podem ser verdadeiras na mesma situação; "
            "sem_prova: tema parecido, detalhe adicional ou condição não mencionada. "
            "Para sustentada ou contradita, copie um trecho literal da fonte que justifica "
            "o julgamento. Para sem_prova, trecho_literal deve ser vazio. "
            "Responda SOMENTE JSON com classe e trecho_literal."
        )},
        {"role": "user", "content": f"Fonte literal: {texto_fonte}\nAlegação a julgar: {alegacao}"},
    ]
    inicio = time.monotonic()
    try:
        resposta = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": "qwen3:4b-instruct", "messages": mensagens,
                  "stream": False, "format": "json",
                  "options": {"temperature": 0, "num_predict": 140}},
            timeout=80,
        )
        resposta.raise_for_status()
        bruto = json.loads(resposta.json()["message"]["content"])
        classe = str(bruto.get("classe") or "")
        trecho = str(bruto.get("trecho_literal") or "")
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        classe, trecho, erro = "", "", type(exc).__name__
    return {
        "classe": classe,
        "trecho_literal": trecho,
        "prova_localizada": prova_localizada(classe, trecho, texto_fonte),
        "latencia_s": round(time.monotonic() - inicio, 3),
        "erro": erro,
    }


def main() -> int:
    totais = {
        campo: {"anterior": 0, "rotulos": 0, "com_prova": 0, "n": 0}
        for campo in ("definicao", "exemplo")
    }
    falsos_positivos = 0
    latencias_anteriores: list[float] = []
    latencias_novas: list[float] = []
    for id_caso, id_fonte, campo, alegacao, esperado in CASOS:
        fonte = FONTES[id_fonte]
        inicio = time.monotonic()
        try:
            anterior = avaliar_anterior(alegacao, fonte["texto"])
            erro_anterior = ""
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            anterior, erro_anterior = "", type(exc).__name__
        latencia_anterior = round(time.monotonic() - inicio, 3)
        novo = avaliar_com_prova(alegacao, fonte["texto"])
        latencias_anteriores.append(latencia_anterior)
        latencias_novas.append(novo["latencia_s"])
        totais[campo]["n"] += 1
        totais[campo]["anterior"] += int(anterior == esperado)
        totais[campo]["rotulos"] += int(novo["classe"] == esperado)
        totais[campo]["com_prova"] += int(novo["classe"] == esperado and novo["prova_localizada"])
        falsos_positivos += int(esperado != "sustentada" and novo["classe"] == "sustentada")
        print(json.dumps({
            "id": id_caso, "tipo": campo, "url": fonte["url"],
            "fonte": fonte["texto"], "alegacao": alegacao, "esperado": esperado,
            "anterior": anterior, "latencia_anterior_s": latencia_anterior,
            "erro_anterior": erro_anterior, "novo": novo,
        }, ensure_ascii=False), flush=True)
    aprovado = bool(
        falsos_positivos == 0
        and all(dados["com_prova"] == dados["n"] for dados in totais.values())
    )
    print(json.dumps({
        "totais": totais,
        "falsos_positivos_sustentada": falsos_positivos,
        "latencia_anterior_s": {
            "total": round(sum(latencias_anteriores), 2),
            "p95": sorted(latencias_anteriores)[int(.95 * (len(latencias_anteriores) - 1))],
        },
        "latencia_nova_s": {
            "total": round(sum(latencias_novas), 2),
            "p95": sorted(latencias_novas)[int(.95 * (len(latencias_novas) - 1))],
        },
        "portao_holdout": aprovado,
        "aprovado_para_producao": False,
    }, ensure_ascii=False), flush=True)
    return 0 if aprovado else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Sonda isolada de implicação fonte→alegação, por definição e exemplo.

Não altera o runtime. Um rótulo do mesmo Qwen que redigiu a aula não é
verificação independente; a sonda mede precisamente esse limite antes de
qualquer influência na fala diária.
"""

from __future__ import annotations

import json

import requests

from scripts.analises.sonda_verificacao_ensino_com_fonte import carregar_fontes, frases_fonte


# tipo, índice de turno histórico, frase de fonte, alegação, gabarito.
CASOS = (
    ("definicao", 12, "E5", "A planta baixa é uma representação da edificação vista de cima.", "sustentada"),
    ("definicao", 12, "E5", "A planta baixa representa a edificação vista de baixo.", "contradita"),
    ("definicao", 12, "E5", "Toda planta baixa tem sete janelas.", "sem_prova"),
    ("definicao", 19, "E5", "Plantas anuais completam o ciclo de vida no espaço de um ano.", "sustentada"),
    ("definicao", 19, "E7", "Todas as plantas perenes morrem após um ano.", "contradita"),
    ("definicao", 3, "E2", "Na fotossíntese, a energia da luz se torna energia química.", "sustentada"),
    ("definicao", 3, "E2", "Na fotossíntese, a luz se transforma em gás carbônico.", "sem_prova"),
    ("exemplo", 12, "E5", "Se desenharmos uma casa em planta baixa, ela será vista de cima.", "sustentada"),
    ("exemplo", 12, "E5", "Numa casa, a planta baixa mostra o interior visto de baixo.", "contradita"),
    ("exemplo", 12, "E5", "Nessa casa, a planta baixa terá exatamente sete janelas.", "sem_prova"),
    ("exemplo", 19, "E5", "Uma planta anual pode brotar, florescer, produzir sementes e morrer em um ano.", "sustentada"),
    ("exemplo", 19, "E5", "Uma petúnia floresce em outubro e morre em novembro.", "sem_prova"),
    ("exemplo", 3, "E2", "Uma planta sob luz solar pode guardar essa energia na forma química.", "sustentada"),
    ("exemplo", 3, "E2", "Uma folha deixada no escuro por uma hora apenas respira.", "sem_prova"),
    ("exemplo", 12, "E2", "O corte arquitetônico é a vista superior de uma casa.", "sem_prova"),
    ("definicao", 12, "E5", "A planta baixa mostra a edificação de cima e usa sempre escala 1:50.", "sem_prova"),
    ("definicao", 19, "E5", "Petúnias são plantas anuais.", "sem_prova"),
    ("definicao", 19, "E7", "Todas as plantas perenes florescem em outubro.", "sem_prova"),
    ("definicao", 3, "E2", "A fotossíntese usa água e gás carbônico para formar glicose.", "sem_prova"),
    ("exemplo", 12, "E5", "A casa é vista de cima na planta baixa e tem exatamente sete janelas.", "sem_prova"),
    ("exemplo", 19, "E7", "Uma planta perene vive anos e floresce todo mês de abril.", "sem_prova"),
    ("exemplo", 3, "E2", "Na fotossíntese, a energia solar vira química dentro da folha em 30 segundos.", "sem_prova"),
    ("exemplo", 12, "E5", "A fachada de uma casa mostra sua vista frontal.", "sem_prova"),
)


def preparar_casos() -> list[dict[str, str]]:
    fontes = carregar_fontes()
    preparados = []
    for tipo, indice, id_fonte, alegacao, esperado in CASOS:
        frase = next(
            (item for item in frases_fonte(fontes[indice]) if item["id"] == id_fonte),
            None,
        )
        if frase is None:
            raise ValueError(f"frase {id_fonte} ausente no turno {indice}")
        preparados.append({
            "tipo": tipo, "alegacao": alegacao, "esperado": esperado,
            "texto_fonte": frase["texto"], "url": frase["url"],
        })
    return preparados


def avaliar(alegacao: str, texto_fonte: str) -> str:
    mensagens = [
        {"role": "system", "content": (
            "Você julga APENAS se uma frase-fonte implica uma alegação. "
            "Não use conhecimento externo, intenção do autor ou o restante da página. "
            "sustentada: a frase afirma diretamente a mesma relação, inclusive "
            "paráfrase sem detalhes novos; contradita: fonte e alegação não "
            "podem ser ambas verdadeiras na mesma situação; sem_prova: tópico "
            "parecido, detalhe adicional, condição não mencionada ou mera "
            "alternativa que pode coexistir. Responda SOMENTE JSON com "
            '{"classe":"sustentada|contradita|sem_prova"}.'
        )},
        {"role": "user", "content": f"Fonte literal: {texto_fonte}\nAlegação a julgar: {alegacao}"},
    ]
    resposta = requests.post(
        "http://127.0.0.1:11434/api/chat",
        json={"model": "qwen3:4b-instruct", "messages": mensagens,
              "stream": False, "format": "json",
              "options": {"temperature": 0, "num_predict": 100}},
        timeout=80,
    )
    resposta.raise_for_status()
    return str(json.loads(resposta.json()["message"]["content"]).get("classe") or "")


def main() -> int:
    totais = {"definicao": [0, 0], "exemplo": [0, 0]}
    for caso in preparar_casos():
        observado = avaliar(caso["alegacao"], caso["texto_fonte"])
        correto = observado == caso["esperado"]
        totais[caso["tipo"]][0] += int(correto)
        totais[caso["tipo"]][1] += 1
        print(json.dumps({**caso, "observado": observado, "correto": correto}, ensure_ascii=False), flush=True)
    print(json.dumps({"totais": totais, "aprovado_para_producao": False}, ensure_ascii=False))
    return 0 if all(acertos == total for acertos, total in totais.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

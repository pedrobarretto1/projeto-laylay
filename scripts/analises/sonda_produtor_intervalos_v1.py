"""Produtor experimental de intervalos literais; sem efeito no runtime."""

from __future__ import annotations

import argparse
import json
import re
import time
from typing import Mapping

from scripts.analises.sonda_produtor_condicoes_didaticas import preparar_entrada_modelo
from scripts.analises.sonda_produtor_condicoes_v2 import (
    _consultar_modelo, _formato_normalizacao, conferir_normalizacao,
    confrontar_trechos, carregar_painel,
)


def tokenizar_fonte(fonte: str) -> list[dict[str, object]]:
    """Cada token guarda posição na fonte, sem normalizar acento/grafia."""
    return [
        {"id": indice, "texto": match.group(), "inicio": match.start(),
         "fim": match.end()}
        for indice, match in enumerate(re.finditer(r"\w+|[^\w\s]", fonte))
    ]


def preparar_entrada_intervalos(caso: Mapping[str, object]) -> dict[str, object]:
    entrada = preparar_entrada_modelo(caso)
    return {**entrada, "tokens": [
        {"id": item["id"], "texto": item["texto"]}
        for item in tokenizar_fonte(caso["fonte"])
    ]}


def converter_intervalos(
    caso: Mapping[str, object], bruto: object,
) -> dict[str, object]:
    """Reconstrói citação literal, sem revisar sua interpretação semântica."""
    base = {"estado": "entrada_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    campos = {"representavel", "intervalos_condicoes", "conectivo_condicoes",
              "direcao_implicacao"}
    if (not isinstance(bruto, Mapping) or set(bruto) != campos
            or type(bruto["representavel"]) is not bool
            or not isinstance(bruto["intervalos_condicoes"], list)
            or len(bruto["intervalos_condicoes"]) > 8
            or not isinstance(bruto["conectivo_condicoes"], str)
            or not isinstance(bruto["direcao_implicacao"], str)
            or bruto["conectivo_condicoes"] not in {
                "unico", "e", "ou", "indeterminado",
            } or bruto["direcao_implicacao"] not in {
                "condicoes_suficientes", "condicoes_necessarias",
                "equivalencia", "indeterminado",
            }):
        return base
    intervalos = bruto["intervalos_condicoes"]
    if not bruto["representavel"]:
        if (intervalos or bruto["conectivo_condicoes"] != "indeterminado"
                or bruto["direcao_implicacao"] != "indeterminado"):
            return base
        return {**base, "estado": "intervalos_convertidos",
                "trechos": {"representavel": False, "trechos_condicoes": [],
                            "conectivo_condicoes": "indeterminado",
                            "direcao_implicacao": "indeterminado"}}
    fonte = caso.get("fonte")
    if not isinstance(fonte, str) or not intervalos:
        return base
    tokens = tokenizar_fonte(fonte)
    trechos = []
    fim_anterior = 0
    for item in intervalos:
        if (not isinstance(item, Mapping) or set(item) != {"inicio", "fim"}
                or type(item["inicio"]) is not int or type(item["fim"]) is not int
                or not 0 <= item["inicio"] < item["fim"] <= len(tokens)
                or item["inicio"] < fim_anterior):
            return base
        trechos.append(fonte[tokens[item["inicio"]]["inicio"]:
                             tokens[item["fim"] - 1]["fim"]])
        fim_anterior = item["fim"]
    return {**base, "estado": "intervalos_convertidos",
            "trechos": {"representavel": True, "trechos_condicoes": trechos,
                        "conectivo_condicoes": bruto["conectivo_condicoes"],
                        "direcao_implicacao": bruto["direcao_implicacao"]}}


def confrontar_intervalos(
    caso: Mapping[str, object], gabarito: Mapping[str, object], bruto: object,
) -> dict[str, object]:
    conversao = converter_intervalos(caso, bruto)
    if conversao["estado"] != "intervalos_convertidos":
        return conversao
    return confrontar_trechos(caso, gabarito, conversao["trechos"])


def _formato_intervalos() -> dict[str, object]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["representavel", "intervalos_condicoes", "conectivo_condicoes",
                     "direcao_implicacao"],
        "properties": {
            "representavel": {"type": "boolean"},
            "intervalos_condicoes": {"type": "array", "maxItems": 8,
                                      "items": {"type": "object",
                                                "additionalProperties": False,
                                                "required": ["inicio", "fim"],
                                                "properties": {
                                                    "inicio": {"type": "integer"},
                                                    "fim": {"type": "integer"},
                                                }}},
            "conectivo_condicoes": {"type": "string", "enum": [
                "unico", "e", "ou", "indeterminado",
            ]},
            "direcao_implicacao": {"type": "string", "enum": [
                "condicoes_suficientes", "condicoes_necessarias",
                "equivalencia", "indeterminado",
            ]},
        },
    }


def medir_caso(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    *, url: str = "http://127.0.0.1:11434/api/chat",
    modelo: str = "qwen3:4b-instruct",
) -> dict[str, object]:
    """Sonda local; gabarito apenas na aferição, nunca no prompt."""
    import requests

    inicio = time.monotonic()
    sistema = (
        "Selecione condições da fonte usando apenas intervalos dos tokens "
        "numerados. Cada intervalo usa inicio inclusivo e fim exclusivo. "
        "Um intervalo por condição; não inclua conectivo, efeito ou outra "
        "condição no mesmo intervalo. Não copie nem reescreva texto: os "
        "intervalos serão convertidos na grafia original pelo programa. "
        "Para uma condição use conectivo 'unico'; para duas ou mais, 'e' ou "
        "'ou'. 'Se condições, efeito' indica suficiência; 'efeito apenas se "
        "condições' indica necessidade; 'se e somente se' indica equivalência. "
        "Se a fonte exige árvore aninhada de e/ou, responda representavel=false, "
        "intervalos_condicoes=[] e ambos os rótulos indeterminado. Não converse."
    )
    try:
        bruto = _consultar_modelo(
            sistema, preparar_entrada_intervalos(caso), _formato_intervalos(),
            url=url, modelo=modelo,
        )
        conversao = converter_intervalos(caso, bruto)
        return {"id": caso["id"], "proposta": bruto, "conversao": conversao,
                "afericao": confrontar_intervalos(caso, gabarito, bruto),
                "duracao_s": round(time.monotonic() - inicio, 2)}
    except (requests.RequestException, KeyError, TypeError, ValueError) as erro:
        return {"id": caso["id"], "erro": type(erro).__name__,
                "duracao_s": round(time.monotonic() - inicio, 2),
                "aprovado_para_producao": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--painel", type=int, choices=(2, 3), default=3)
    args = parser.parse_args()
    entradas, gabarito = carregar_painel(args.painel)
    for caso in entradas:
        print(json.dumps(medir_caso(caso, gabarito[caso["id"]]),
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

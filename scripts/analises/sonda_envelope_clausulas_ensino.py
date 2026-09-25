"""Sonda offline: todas as cláusulas continuam no envelope de evidência.

O modelo só propõe alinhamentos. Citação literal é recibo de texto, nunca
prova de implicação, papel, condição ou verdade externa.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable

import requests

from scripts.analises.contrato_requisitos_ensino import (
    Requisito, comparar_rotulo_da_medida, localizar_valor_para_limiar,
)
from scripts.analises.sonda_extracao_vinculo_ensino_v1 import carregar_casos
from scripts.analises.sonda_indices_requisitos_ensino import segmentar_clausulas


INSTRUCAO = (
    "Receba TODAS as cláusulas de uma definição e um exemplo. Para CADA "
    "índice de cláusula, copie do EXEMPLO um trecho contínuo e exato que "
    "possa expressar aquela informação. Se não houver trecho, use string "
    "vazia. Não pule índices, não copie da definição e não invente palavras. "
    "Negações e falta de informação não confirmam uma condição. "
    "Não julgue se o exemplo está correto; devolva JSON com alinhamentos "
    "(indice, trecho_exemplo)."
)
FORMATO = {
    "type": "object", "properties": {
        "alinhamentos": {"type": "array", "items": {"type": "object", "properties": {
            "indice": {"type": "integer"}, "trecho_exemplo": {"type": "string"},
        }, "required": ["indice", "trecho_exemplo"], "additionalProperties": False}},
    }, "required": ["alinhamentos"], "additionalProperties": False,
}


def conferir_envelope(caso: dict[str, str], bruto: Any) -> dict[str, Any]:
    clausulas = segmentar_clausulas(caso["definicao"])
    ativos = list(range(len(clausulas)))
    base = {"clausulas_ativas": ativos, "aprovado_para_compor": False,
            "papeis_verificados": False, "condicoes_verificadas": False}
    if not clausulas:
        return {**base, "estado": "definicao_sem_clausulas"}
    itens = bruto.get("alinhamentos") if isinstance(bruto, dict) else None
    if not isinstance(itens, list) or not all(isinstance(item, dict) for item in itens):
        return {**base, "estado": "formato_invalido"}
    indices = [item.get("indice") for item in itens]
    if (len(indices) != len(ativos)
            or any(type(indice) is not int for indice in indices)
            or len(set(indices)) != len(indices)
            or set(indices) != set(ativos)):
        return {**base, "estado": "cobertura_de_indices_invalida"}
    if any(not isinstance(item.get("trecho_exemplo"), str) for item in itens):
        return {**base, "estado": "formato_invalido"}
    por_indice = {item["indice"]: item["trecho_exemplo"].strip() for item in itens}
    inventados = [indice for indice, trecho in por_indice.items()
                 if trecho and trecho not in caso["exemplo"]]
    if inventados:
        return {**base, "estado": "trecho_exemplo_invalido",
                "indices_com_trecho_inventado": sorted(inventados)}
    pistas_numericas = {}
    rotulos_medidas = {}
    for clausula in clausulas:
        indice = clausula["indice"]
        requisito = Requisito(f"clausula_{indice}", "menor_que", clausula["trecho"])
        pista = localizar_valor_para_limiar(requisito, caso["exemplo"])
        if pista["estado"] != "limiar_nao_conferivel":
            pistas_numericas[indice] = pista
            rotulos_medidas[indice] = comparar_rotulo_da_medida(requisito, caso["exemplo"])
    sem_evidencia = [indice for indice in ativos if not por_indice[indice]]
    return {**base,
            "estado": ("sem_evidencia_em_clausulas" if sem_evidencia
                       else "evidencia_literal_revisao_pendente"),
            "clausulas_sem_evidencia": sem_evidencia,
            "pistas_numericas": pistas_numericas,
            "rotulos_medidas": rotulos_medidas,
            "alinhamentos": [por_indice[indice] for indice in ativos]}


def medir_caso(caso: dict[str, str], *, post: Callable[..., Any] = requests.post) -> dict[str, Any]:
    entrada = {"clausulas": segmentar_clausulas(caso["definicao"]),
               "exemplo": caso["exemplo"]}
    inicio = time.monotonic()
    try:
        resposta = post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": "qwen3:4b-instruct", "messages": [
                {"role": "system", "content": INSTRUCAO},
                {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)},
            ], "stream": False, "format": FORMATO,
                  "options": {"temperature": 0, "num_predict": 260}},
            timeout=80,
        )
        resposta.raise_for_status()
        bruto = json.loads(resposta.json()["message"]["content"])
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        bruto, erro = {}, type(exc).__name__
    return {"id": caso["id"], "esperado_provisorio": caso["esperado"],
            "conferencia": conferir_envelope(caso, bruto),
            "proposta": bruto, "erro": erro,
            "latencia_s": round(time.monotonic() - inicio, 3),
            "aprovado_para_producao": False}


def main() -> None:
    for caso in carregar_casos("dev"):
        print(json.dumps(medir_caso(caso), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

"""Sonda offline: o modelo seleciona índices, nunca reescreve a definição.

A divisão por vírgula/ponto-e-vírgula é apenas um protótipo para definições
curtas. Seleção de fonte não comprova que um exemplo satisfaz a fonte.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Callable

import requests

from scripts.analises.sonda_alinhamento_requisitos_ensino import requisitos_do_caso
from scripts.analises.sonda_extracao_vinculo_ensino_v1 import carregar_casos


INSTRUCAO = (
    "Leia apenas as cláusulas numeradas da definição. Selecione os índices "
    "das cláusulas cuja informação é necessária para reconhecer um exemplo "
    "da afirmação: condições, limiares, modo de operação, perspectiva, "
    "papéis, ação e objeto. Inclua qualificadores introdutórios quando "
    "restringirem a afirmação. Não reescreva trechos nem julgue exemplos. "
    "Devolva JSON com a lista indices_requisitos, usando apenas índices dados."
)
FORMATO = {
    "type": "object", "properties": {
        "indices_requisitos": {"type": "array", "items": {"type": "integer"}},
    }, "required": ["indices_requisitos"], "additionalProperties": False,
}


def segmentar_clausulas(definicao: str) -> list[dict[str, Any]]:
    """Enumera fatias literais e offsets; não decide obrigatoriedade."""
    partes: list[dict[str, Any]] = []
    for correspondencia in re.finditer(r"[^,;]+", definicao):
        bruto = correspondencia.group()
        trecho = bruto.strip().rstrip(".!?").rstrip()
        if not trecho:
            continue
        inicio = correspondencia.start() + len(bruto) - len(bruto.lstrip())
        partes.append({"indice": len(partes), "inicio": inicio,
                       "fim": inicio + len(trecho), "trecho": trecho})
    return partes


def conferir_indices(bruto: Any, caso: dict[str, str],
                    clausulas: list[dict[str, Any]]) -> dict[str, Any]:
    base = {"aprovado_para_compor": False, "papeis_verificados": False,
            "condicoes_verificadas": False}
    if not clausulas or any(
        item.get("indice") != numero
        or caso["definicao"][item["inicio"]:item["fim"]] != item["trecho"]
        for numero, item in enumerate(clausulas)
    ):
        return {**base, "estado": "clausulas_invalidas"}
    indices = bruto.get("indices_requisitos") if isinstance(bruto, dict) else None
    if (not isinstance(indices, list)
            or any(type(indice) is not int or indice < 0 or indice >= len(clausulas)
                   for indice in indices)
            or len(indices) != len(set(indices))):
        return {**base, "estado": "indices_invalidos"}
    selecionadas = [clausulas[indice]["trecho"] for indice in indices]
    requisitos = requisitos_do_caso(caso["id"])
    faltantes = [item.id for item in requisitos
                 if not any(item.trecho_definicao.casefold() in trecho.casefold()
                            for trecho in selecionadas)]
    return {**base,
            "estado": "cobertura_incompleta" if faltantes else "fonte_coberta_revisao_pendente",
            "requisitos_nao_cobertos": faltantes,
            "indices_omitidos": [item["indice"] for item in clausulas
                                 if item["indice"] not in indices]}


def medir_definicao(caso: dict[str, str], *, post: Callable[..., Any] = requests.post) -> dict[str, Any]:
    clausulas = segmentar_clausulas(caso["definicao"])
    entrada = {"clausulas": clausulas}
    inicio = time.monotonic()
    try:
        resposta = post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": "qwen3:4b-instruct", "messages": [
                {"role": "system", "content": INSTRUCAO},
                {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)},
            ], "stream": False, "format": FORMATO,
                  "options": {"temperature": 0, "num_predict": 100}},
            timeout=80,
        )
        resposta.raise_for_status()
        proposta = json.loads(resposta.json()["message"]["content"])
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        proposta, erro = {}, type(exc).__name__
    return {"id": caso["id"], "clausulas": clausulas,
            "conferencia": conferir_indices(proposta, caso, clausulas),
            "proposta": proposta, "erro": erro,
            "latencia_s": round(time.monotonic() - inicio, 3),
            "aprovado_para_producao": False}


def main() -> None:
    ids = {"IRR-01", "ARQ-01", "ARQ-04"}
    for caso in carregar_casos("dev"):
        if caso["id"] in ids:
            print(json.dumps(medir_definicao(caso), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

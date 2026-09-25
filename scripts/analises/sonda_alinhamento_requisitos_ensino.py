"""Sonda offline: Qwen propõe spans para requisitos ancorados na definição.

Requisitos são curadoria diagnóstica do desenvolvimento, não extração
automática nem rótulos humanos independentes. Nenhum resultado autoriza fala.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable

import requests

from scripts.analises.contrato_requisitos_ensino import (
    Alinhamento, Requisito, conferir_requisitos,
)
from scripts.analises.sonda_extracao_vinculo_ensino_v1 import carregar_casos


REQUISITOS_IRR = (
    Requisito("modo", "condicao_textual", "modo automático"),
    Requisito("limiar", "menor_que", "abaixo de 20%"),
    Requisito("agente", "literal", "controlador"),
    Requisito("alvo", "literal", "bomba"),
    Requisito("acao", "parafrase", "liga"),
)
REQUISITOS_ARQ_PLANTA = (
    Requisito("artefato", "literal", "planta baixa"),
    Requisito("perspectiva", "parafrase", "visto de cima"),
    Requisito("relacao", "parafrase", "mostra"),
    Requisito("objeto", "parafrase", "posição das paredes e portas"),
)
REQUISITOS_ARQ_CORTE = (
    Requisito("artefato", "literal", "corte vertical"),
    Requisito("travessia", "condicao_textual", "atravessa a escada"),
    Requisito("relacao", "parafrase", "mostra"),
    Requisito("objeto", "parafrase", "posição dos degraus e suas alturas"),
)
INSTRUCAO = (
    "Você alinha uma definição a um exemplo, sem julgar se o exemplo está certo. "
    "Para CADA requisito fornecido, copie um trecho CONTÍGUO E EXATO do exemplo "
    "que possa tratar daquele requisito. Se não houver trecho, use string vazia. "
    "Não invente texto, não use a definição como trecho do exemplo. "
    "A presença de palavras não prova condição; a decisão fica fora do modelo. "
    "Retorne JSON com alinhamentos: lista de objetos id e trecho_exemplo."
)
FORMATO = {
    "type": "object", "properties": {
        "alinhamentos": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string"}, "trecho_exemplo": {"type": "string"},
        }, "required": ["id", "trecho_exemplo"], "additionalProperties": False}},
    }, "required": ["alinhamentos"], "additionalProperties": False,
}


def requisitos_do_caso(id_caso: str) -> tuple[Requisito, ...]:
    if id_caso.startswith("IRR-"):
        return REQUISITOS_IRR
    if id_caso in {"ARQ-01", "ARQ-02", "ARQ-03"}:
        return REQUISITOS_ARQ_PLANTA
    if id_caso == "ARQ-04":
        return REQUISITOS_ARQ_CORTE
    raise ValueError("requisitos só foram curados para desenvolvimento")


def conferir_saida(bruto: Any, caso: dict[str, str],
                  requisitos: tuple[Requisito, ...]) -> dict[str, Any]:
    itens = bruto.get("alinhamentos") if isinstance(bruto, dict) else None
    if not isinstance(itens, list) or not all(isinstance(item, dict) for item in itens):
        return {"estado": "formato_invalido", "aprovado_para_compor": False}
    ids = [item.get("id") for item in itens]
    if len(ids) != len(requisitos) or set(ids) != {item.id for item in requisitos}:
        return {"estado": "cobertura_invalida", "aprovado_para_compor": False}
    if any(not isinstance(item.get("trecho_exemplo"), str) for item in itens):
        return {"estado": "trecho_invalido", "aprovado_para_compor": False}
    alinhamentos = [Alinhamento(item["id"], item["trecho_exemplo"]) for item in itens]
    return conferir_requisitos(caso["definicao"], caso["exemplo"],
                              requisitos, alinhamentos)


def medir_caso(caso: dict[str, str], *, post: Callable[..., Any] = requests.post) -> dict[str, Any]:
    requisitos = requisitos_do_caso(caso["id"])
    entrada = {"definicao": caso["definicao"], "exemplo": caso["exemplo"],
               "requisitos": [{"id": item.id, "tipo": item.tipo,
                                "trecho_definicao": item.trecho_definicao}
                               for item in requisitos]}
    inicio = time.monotonic()
    try:
        resposta = post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": "qwen3:4b-instruct", "messages": [
                {"role": "system", "content": INSTRUCAO},
                {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)},
            ], "stream": False, "format": FORMATO,
                  "options": {"temperature": 0, "num_predict": 320}},
            timeout=80,
        )
        resposta.raise_for_status()
        bruto = json.loads(resposta.json()["message"]["content"])
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        bruto, erro = {}, type(exc).__name__
    conferencia = conferir_saida(bruto, caso, requisitos)
    return {"id": caso["id"], "esperado_provisorio": caso["esperado"],
            "conferencia": conferencia, "proposta": bruto,
            "erro": erro, "latencia_s": round(time.monotonic() - inicio, 3)}


def main() -> None:
    resultados = []
    for caso in carregar_casos("dev"):
        resultado = medir_caso(caso)
        resultados.append(resultado)
        print(json.dumps(resultado, ensure_ascii=False), flush=True)
    print(json.dumps({"total": len(resultados),
                      "estados": {estado: sum(item["conferencia"]["estado"] == estado
                                            for item in resultados)
                                  for estado in sorted({item["conferencia"]["estado"]
                                                        for item in resultados})},
                      "aprovado_para_producao": False}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

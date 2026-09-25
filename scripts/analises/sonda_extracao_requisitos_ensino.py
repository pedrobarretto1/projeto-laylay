"""Sonda offline de extração dos requisitos da definição, sem exemplo.

Compara spans propostos a uma curadoria diagnóstica de três definições
novas de desenvolvimento. Cobertura literal não aprova interpretação.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable

import requests

from scripts.analises.sonda_alinhamento_requisitos_ensino import requisitos_do_caso
from scripts.analises.sonda_extracao_vinculo_ensino_v1 import carregar_casos


INSTRUCAO = (
    "Leia SOMENTE a definição recebida. Extraia separadamente cada peça "
    "necessária para reconhecer um exemplo: quem age, o que faz, o alvo, "
    "condições de contexto, limiares numéricos, perspectiva ou objeto da ação. "
    "Não omita qualificadores introdutórios que restrinjam quando a ação ocorre. "
    "Cada trecho deve ser cópia contínua e literal da definição, com no máximo "
    "80 caracteres. Não inclua a definição inteira como uma peça. "
    "Tipos permitidos: entidade, acao, objeto, condicao, limiar. "
    "Devolva JSON com requisitos: lista de tipo e trecho_definicao."
)
FORMATO = {
    "type": "object", "properties": {
        "requisitos": {"type": "array", "items": {"type": "object", "properties": {
            "tipo": {"type": "string", "enum": ["entidade", "acao", "objeto", "condicao", "limiar"]},
            "trecho_definicao": {"type": "string"},
        }, "required": ["tipo", "trecho_definicao"], "additionalProperties": False}},
    }, "required": ["requisitos"], "additionalProperties": False,
}


def conferir_extracao(bruto: Any, definicao: str) -> dict[str, Any]:
    itens = bruto.get("requisitos") if isinstance(bruto, dict) else None
    if not isinstance(itens, list) or len(itens) < 3:
        return {"valida": False, "motivo": "cobertura_estrutural"}
    for item in itens:
        if not isinstance(item, dict) or item.get("tipo") not in {
            "entidade", "acao", "objeto", "condicao", "limiar",
        }:
            return {"valida": False, "motivo": "tipo_invalido"}
        trecho = item.get("trecho_definicao")
        if not isinstance(trecho, str) or not trecho.strip() or len(trecho) > 80 or trecho not in definicao:
            return {"valida": False, "motivo": "trecho_sem_recibo"}
    return {"valida": True, "motivo": "", "aprovado_para_compor": False}


def medir_definicao(caso: dict[str, str], *, post: Callable[..., Any] = requests.post) -> dict[str, Any]:
    requisitos = requisitos_do_caso(caso["id"])
    inicio = time.monotonic()
    try:
        resposta = post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": "qwen3:4b-instruct", "messages": [
                {"role": "system", "content": INSTRUCAO},
                {"role": "user", "content": caso["definicao"]},
            ], "stream": False, "format": FORMATO,
                  "options": {"temperature": 0, "num_predict": 320}},
            timeout=80,
        )
        resposta.raise_for_status()
        bruto = json.loads(resposta.json()["message"]["content"])
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        bruto, erro = {}, type(exc).__name__
    formal = conferir_extracao(bruto, caso["definicao"])
    faltantes = []
    if formal["valida"]:
        spans = [item["trecho_definicao"] for item in bruto["requisitos"]]
        faltantes = [item.id for item in requisitos
                    if not any(item.trecho_definicao.casefold() in span.casefold()
                               for span in spans)]
    return {"id": caso["id"], "formal": formal,
            "requisitos_curados": [item.id for item in requisitos],
            "requisitos_nao_cobertos": faltantes if formal["valida"] else None,
            "proposta": bruto, "erro": erro,
            "latencia_s": round(time.monotonic() - inicio, 3),
            "aprovado_para_producao": False}


def main() -> None:
    ids = {"IRR-01", "ARQ-01", "ARQ-04"}
    for caso in carregar_casos("dev"):
        if caso["id"] in ids:
            print(json.dumps(medir_definicao(caso), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

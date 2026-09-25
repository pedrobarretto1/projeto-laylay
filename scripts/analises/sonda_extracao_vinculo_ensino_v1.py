"""Mede extração de vínculo didático pelo Qwen local, sem publicar falas.

O conjunto é sintético, novo e congelado; rótulos são provisórios do agente,
não revisão humana independente. A reserva deve permanecer intocada até
que a primeira leitura do desenvolvimento seja documentada.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Callable

import requests

from scripts.analises.contrato_vinculo_didatico import RelacaoAnotada, avaliar_vinculo


ARQUIVO = Path(__file__).parent / "dados" / "vinculos_ensino_sinteticos_v1.jsonl"
SHA256_CONGELADO = "9994e07f421bca5ba86f82f9bf7d60ea06663d946820c5ab80e3bed7317efe74"
CLASSES = frozenset({"exemplo_direto", "condicao_omitida", "papeis_invertidos",
                     "outra_relacao", "analogia", "indeterminado"})
INSTRUCAO = (
    "Você analisa DOIS trechos didáticos sintéticos. Use somente o texto recebido; "
    "não complete condições com conhecimento externo. Primeiro represente, em cada "
    "trecho, a relação principal, seus papéis agente/alvo e condições obrigatórias. "
    "Use o mesmo identificador curto de relação somente se a direção e o efeito "
    "forem os mesmos. Depois classifique o vínculo do segundo trecho com o primeiro. "
    "A chave tipo é a CLASSIFICAÇÃO FINAL, nunca o nome da relação: "
    "exemplo_direto, condicao_omitida, papeis_invertidos, outra_relacao, analogia "
    "ou indeterminado. Exemplo_direto exige mesma relação, direção e condições. "
    "Uma analogia não é exemplo factual direto. Copie uma citação literal de pelo "
    "menos 15 caracteres de CADA trecho. Devolva SOMENTE JSON com as chaves "
    "tipo, relacao_def, relacao_ex, papeis_def, papeis_ex, condicoes_def, "
    "condicoes_ex, citacao_def, citacao_ex. Papeis são objetos de strings; "
    "condições são listas de strings. Copie os nomes das chaves exatamente."
)
FORMATO = {
    "type": "object",
    "properties": {
        "tipo": {"type": "string", "enum": sorted(CLASSES)},
        "relacao_def": {"type": "string"},
        "relacao_ex": {"type": "string"},
        "papeis_def": {"type": "object", "additionalProperties": {"type": "string"}},
        "papeis_ex": {"type": "object", "additionalProperties": {"type": "string"}},
        "condicoes_def": {"type": "array", "items": {"type": "string"}},
        "condicoes_ex": {"type": "array", "items": {"type": "string"}},
        "citacao_def": {"type": "string"},
        "citacao_ex": {"type": "string"},
    },
    "required": ["tipo", "relacao_def", "relacao_ex", "papeis_def",
                 "papeis_ex", "condicoes_def", "condicoes_ex",
                 "citacao_def", "citacao_ex"],
    "additionalProperties": False,
}


def carregar_casos(split: str) -> list[dict[str, str]]:
    if split not in {"dev", "reserva"}:
        raise ValueError("split inválido")
    if hashlib.sha256(ARQUIVO.read_bytes()).hexdigest() != SHA256_CONGELADO:
        raise ValueError("dataset de vínculo divergiu do congelado")
    casos = [json.loads(linha) for linha in ARQUIVO.read_text(encoding="utf-8").splitlines()
             if linha.strip()]
    ids = [item["id"] for item in casos]
    if len(ids) != len(set(ids)) or len(casos) != 16:
        raise ValueError("IDs ou tamanho do dataset alterados")
    if any(item["esperado"] not in CLASSES for item in casos):
        raise ValueError("rótulo fora do protocolo")
    return [item for item in casos if item["split"] == split]


def conferir_proposta(bruto: Any, caso: dict[str, str]) -> dict[str, Any]:
    """Valida apenas formato e proveniência literal, não a interpretação."""
    if not isinstance(bruto, dict) or bruto.get("tipo") not in CLASSES:
        return {"valida": False, "motivo": "tipo_invalido"}
    for campo, texto in (("citacao_def", caso["definicao"]),
                         ("citacao_ex", caso["exemplo"])):
        citacao = bruto.get(campo)
        if not isinstance(citacao, str) or len(citacao) < 15 or citacao not in texto:
            return {"valida": False, "motivo": f"{campo}_sem_recibo"}
    for campo in ("relacao_def", "relacao_ex"):
        if not isinstance(bruto.get(campo), str) or not bruto[campo].strip():
            return {"valida": False, "motivo": f"{campo}_invalida"}
    for campo in ("papeis_def", "papeis_ex"):
        papeis = bruto.get(campo)
        if not isinstance(papeis, dict) or not papeis or any(
            not isinstance(chave, str) or not chave.strip()
            or not isinstance(valor, str) or not valor.strip()
            for chave, valor in papeis.items()
        ):
            return {"valida": False, "motivo": f"{campo}_invalidos"}
    for campo in ("condicoes_def", "condicoes_ex"):
        condicoes = bruto.get(campo)
        if not isinstance(condicoes, list) or any(
            not isinstance(item, str) or not item.strip() for item in condicoes
        ):
            return {"valida": False, "motivo": f"{campo}_invalidas"}
    fontes = {"D": {"url": "https://exemplo.org/definicao", "trecho": caso["definicao"]},
              "E": {"url": "https://exemplo.org/exemplo", "trecho": caso["exemplo"]}}
    definicao = RelacaoAnotada(
        "D", caso["definicao"], "definicao", bruto["relacao_def"],
        tuple(sorted(bruto["papeis_def"].items())),
        frozenset(bruto["condicoes_def"]),
    )
    exemplo = RelacaoAnotada(
        "E", caso["exemplo"], "exemplo", bruto["relacao_ex"],
        tuple(sorted(bruto["papeis_ex"].items())),
        frozenset(bruto["condicoes_ex"]),
    )
    estrutura = avaliar_vinculo(definicao, exemplo, fontes)
    return {"valida": True, "motivo": "", "estrutura": estrutura["estado"],
            "anotacao_semantica_revisada": False, "aprovado_para_compor": False}


def medir_caso(
    caso: dict[str, str],
    *, post: Callable[..., Any] = requests.post,
) -> dict[str, Any]:
    entrada = {"definicao": caso["definicao"], "exemplo": caso["exemplo"]}
    inicio = time.monotonic()
    try:
        resposta = post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": "qwen3:4b-instruct", "messages": [
                {"role": "system", "content": INSTRUCAO},
                {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)},
            ], "stream": False, "format": FORMATO,
                  "options": {"temperature": 0, "num_predict": 500}},
            timeout=80,
        )
        resposta.raise_for_status()
        bruto = json.loads(resposta.json()["message"]["content"])
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        bruto, erro = {}, type(exc).__name__
    formal = conferir_proposta(bruto, caso)
    previsto = bruto.get("tipo") if formal["valida"] else "invalida"
    return {"id": caso["id"], "dominio": caso["dominio"],
            "esperado_provisorio": caso["esperado"], "previsto": previsto,
            "formal": formal, "proposta": bruto,
            "erro": erro, "latencia_s": round(time.monotonic() - inicio, 3),
            "acerto_provisorio": previsto == caso["esperado"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "reserva"), default="dev")
    args = parser.parse_args()
    resultados = []
    for caso in carregar_casos(args.split):
        resultado = medir_caso(caso)
        resultados.append(resultado)
        print(json.dumps(resultado, ensure_ascii=False), flush=True)
    print(json.dumps({
        "split": args.split, "total": len(resultados),
        "acertos_provisorios": sum(item["acerto_provisorio"] for item in resultados),
        "previstos": dict(Counter(item["previsto"] for item in resultados)),
        "falsos_diretos": [item["id"] for item in resultados
                           if item["previsto"] == "exemplo_direto"
                           and item["esperado_provisorio"] != "exemplo_direto"],
        "aprovado_para_producao": False,
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

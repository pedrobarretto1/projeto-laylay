"""Painel cego para revisão humana de referências de grandeza em exemplos.

Validação de formato não autentica o revisor nem promove exemplos a treino.
Todos os contextos do painel são cenários sintéticos, não fontes externas.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.analises.contrato_requisitos_ensino import (
    Requisito, comparar_rotulo_da_medida,
)


ARQUIVO = Path(__file__).parent / "dados" / "revisao_referencias_ensino_v1.jsonl"
SHA256_CONGELADO = "CB840DBFBD8C5A1B5AF0CE02853FA0A2E56D1052AFE567BE6C33809093ECF2E5"
ROTULOS_REFERENTE = frozenset({"mesmo", "outro", "indeterminado"})
ROTULOS_LEITURA = frozenset({"afirmada", "negada", "indeterminada"})


def carregar_painel() -> list[dict[str, Any]]:
    if hashlib.sha256(ARQUIVO.read_bytes()).hexdigest().upper() != SHA256_CONGELADO:
        raise ValueError("painel de referências divergiu do congelado")
    casos = [json.loads(linha) for linha in ARQUIVO.read_text(encoding="utf-8").splitlines()
             if linha.strip()]
    ids = [item.get("id") for item in casos]
    if len(casos) != 10 or len(set(ids)) != len(ids):
        raise ValueError("painel com tamanho ou IDs inválidos")
    for item in casos:
        if (set(item) != {"id", "definicao", "exemplo", "contexto"}
                or any(not isinstance(item[campo], str) or not item[campo].strip()
                       for campo in ("id", "definicao", "exemplo"))
                or not isinstance(item["contexto"], list)
                or any(not isinstance(texto, str) or not texto.strip()
                       for texto in item["contexto"])):
            raise ValueError("caso de revisão inválido ou com gabarito embutido")
    return casos


def diagnosticar(caso: dict[str, Any]) -> dict[str, Any]:
    resultado = comparar_rotulo_da_medida(
        Requisito("limiar", "menor_que", caso["definicao"]), caso["exemplo"],
    )
    return {"id": caso["id"], "estado": resultado["estado"],
            "entidade_requerida": resultado["entidade_requerida"],
            "entidade_exemplo": resultado["entidade_exemplo"],
            "contexto_verificado": False, "aprovado_para_compor": False}


def validar_revisao(revisoes: list[dict[str, Any]]) -> dict[str, Any]:
    base = {"aprovado_para_treino": False, "aprovado_para_compor": False,
            "revisao_humana_confirmada": False}
    casos = carregar_painel()
    por_id = {item["id"]: item for item in casos}
    if (not isinstance(revisoes, list)
            or not all(isinstance(item, dict) for item in revisoes)):
        return {**base, "valida": False, "motivo": "formato_invalido"}
    ids = [item.get("id") for item in revisoes]
    if len(ids) != len(por_id) or any(type(identificador) is not str for identificador in ids) or set(ids) != set(por_id):
        return {**base, "valida": False, "motivo": "cobertura_invalida"}
    for item in revisoes:
        if (type(item.get("referente")) is not str
                or item["referente"] not in ROTULOS_REFERENTE
                or type(item.get("leitura")) is not str
                or item["leitura"] not in ROTULOS_LEITURA
                or not isinstance(item.get("justificativa"), str)
                or len(item["justificativa"].strip()) < 10
                or not isinstance(item.get("evidencia"), str)
                or not item["evidencia"].strip()):
            return {**base, "valida": False, "motivo": "rotulo_ou_justificativa_invalido"}
        caso = por_id[item["id"]]
        textos = [caso["definicao"], caso["exemplo"], *caso["contexto"]]
        if not any(item["evidencia"] in texto for texto in textos):
            return {**base, "valida": False, "motivo": "evidencia_sem_origem"}
    return {**base, "valida": True, "motivo": ""}


def main() -> None:
    parser = argparse.ArgumentParser(description="Painel cego de referência de medidas")
    parser.add_argument("--diagnostico", action="store_true",
                        help="mostrar o diagnóstico atual; não usar ao revisar")
    opcoes = parser.parse_args()
    for caso in carregar_painel():
        saida = diagnosticar(caso) if opcoes.diagnostico else caso
        print(json.dumps(saida, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

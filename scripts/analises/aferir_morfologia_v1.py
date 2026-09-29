"""Aferição offline do número superficial; não usa LLM nem runtime Laylay."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Mapping

from scripts.analises.veto_superficie_sujeito_composto import (
    conferir_numero_condicao_curta,
)


DADOS = Path(__file__).resolve().parent / "dados"
ENTRADAS = DADOS / "sonda_morfologia_entradas_v1.json"
REVISAO = DADOS / "sonda_morfologia_revisao_v1.json"
SHA_ENTRADAS = "e7a2e6cea0eb8feb9faecbbcb6e1deac1fd2739f7e89032f33b956b962549d5b"
SHA_REVISAO = "85c33ae101c573d671f78575672daf700af5a636623204de7f787cc4faf5b087"


def _carregar_congelado(caminho: Path, sha_esperado: str) -> dict:
    conteudo = caminho.read_bytes()
    if hashlib.sha256(conteudo).hexdigest() != sha_esperado:
        raise ValueError(f"painel alterado depois do congelamento: {caminho.name}")
    dados = json.loads(conteudo)
    if not isinstance(dados, dict) or dados.get("versao") != 1:
        raise ValueError("versao invalida do painel morfologico")
    return dados


def propor_entradas(entradas: Mapping[str, object]) -> dict[str, dict[str, object]]:
    """Só recebe frases, sem revisão ou rótulos esperados."""
    casos = entradas.get("casos")
    if not isinstance(casos, list):
        raise ValueError("entradas morfologicas invalidas")
    saidas: dict[str, dict[str, object]] = {}
    for caso in casos:
        if (not isinstance(caso, dict) or set(caso) != {"id", "trecho"}
                or not isinstance(caso["id"], str)
                or not isinstance(caso["trecho"], str)
                or caso["id"] in saidas):
            raise ValueError("caso morfologico invalido ou duplicado")
        saidas[caso["id"]] = conferir_numero_condicao_curta(caso["trecho"])
    return saidas


def main() -> None:
    entradas = _carregar_congelado(ENTRADAS, SHA_ENTRADAS)
    revisao = _carregar_congelado(REVISAO, SHA_REVISAO)
    propostas = propor_entradas(entradas)
    esperados = revisao.get("casos")
    if not isinstance(esperados, dict) or set(esperados) != set(propostas):
        raise ValueError("revisao morfologica incompleta")
    contagem = Counter(resultado["estado"] for resultado in propostas.values())
    divergentes = {
        id_caso: {"esperado": esperado,
                  "observado": propostas[id_caso]["estado"]}
        for id_caso, esperado in esperados.items()
        if propostas[id_caso]["estado"] != esperado
    }
    print(json.dumps({
        "total": len(propostas),
        "alinhados_revisao_local": len(propostas) - len(divergentes),
        "estados": dict(contagem),
        "divergentes": divergentes,
        "aprovado_para_producao": False,
        "autoriza_efeito": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

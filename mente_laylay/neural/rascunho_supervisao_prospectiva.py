"""Build AI-curation drafts from literal prospective candidates.

The drafts remain development-only. They are validated against the canonical
operational supervision contract but never become human review or training data.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .adaptador_validacao_operacional import (
    preparar_exemplo_validacao_operacional,
)
from .supervisao_operacional_v1 import (
    PERFIL,
    preparar_exemplo_operacional,
)
from .supervisao_relacoes_v4 import FLAGS, PAPEIS


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _carregar_jsonl(path: str | Path) -> tuple[list[dict[str, Any]], bytes]:
    bruto = Path(path).read_bytes()
    itens = []
    for numero, linha in enumerate(bruto.decode("utf-8").splitlines(), 1):
        if not linha.strip():
            continue
        valor = json.loads(linha)
        if not isinstance(valor, dict):
            raise ValueError(f"linha {numero} da triagem nao e objeto")
        itens.append(dict(valor))
    return itens, bruto


def _span_unico(texto: str, literal: object, campo: str) -> dict[str, Any]:
    valor = str(literal or "")
    if not valor or texto.count(valor) != 1:
        raise ValueError(f"{campo} precisa ocorrer de forma literal e unica")
    inicio = texto.index(valor)
    return {
        "inicio": inicio,
        "fim": inicio + len(valor),
        "texto": valor,
    }


def _grupo_entidade(_intent: str, _action: str, alvo: str) -> str:
    normalizado = " ".join(alvo.strip().casefold().split())
    digest = hashlib.sha256(normalizado.encode("utf-8")).hexdigest()
    return f"alvo:{digest}"


def preparar_rascunhos(
    fila_triagem_path: str | Path,
    manifesto: Mapping[str, Any],
) -> dict[str, Any]:
    """Create structurally valid AI-curation drafts for every literal candidate."""
    if not isinstance(manifesto, Mapping):
        raise TypeError("manifesto deve ser mapeamento")
    if int(manifesto.get("versao") or 0) != 1:
        raise ValueError("versao de manifesto desconhecida")
    if str(manifesto.get("origem_decisao") or "").strip().casefold() != "curadoria_ia":
        raise ValueError("rascunho exige origem curadoria_ia")
    if manifesto.get("revisao_humana") is not False:
        raise ValueError("rascunho IA nao pode declarar revisao humana")
    if any(
        manifesto.get(chave) is not False
        for chave in ("treino_permitido", "autoriza_execucao", "autoriza_promocao")
    ):
        raise ValueError("manifesto nao pode conceder autoridade")

    itens, bruto = _carregar_jsonl(fila_triagem_path)
    sha_fonte = _sha256(bruto)
    if manifesto.get("fonte_triagem_sha256") != sha_fonte:
        raise ValueError("manifesto deve declarar o SHA exato da triagem")

    candidatos = {
        int(item["indice_fila"]): item
        for item in itens
        if item.get("status") == "candidato_literal"
    }
    propostas = manifesto.get("propostas")
    if not isinstance(propostas, list):
        raise ValueError("manifesto precisa listar propostas")

    por_indice: dict[int, dict[str, Any]] = {}
    for proposta in propostas:
        if not isinstance(proposta, Mapping):
            raise ValueError("proposta invalida")
        indice = proposta.get("indice_fila")
        if type(indice) is not int or indice <= 0 or indice in por_indice:
            raise ValueError("propostas precisam de indices unicos")
        por_indice[indice] = dict(proposta)
    if set(por_indice) != set(candidatos):
        raise ValueError("manifesto deve cobrir todos os candidatos exatamente uma vez")

    saida: list[dict[str, Any]] = []
    for indice in sorted(candidatos):
        candidato = candidatos[indice]
        proposta = por_indice[indice]
        if any(
            candidato.get(chave) is not False
            for chave in (
                "revisao_humana",
                "dados_prontos_para_treino",
                "treino_permitido",
                "autoriza_execucao",
                "autoriza_promocao",
            )
        ):
            raise ValueError(f"candidato {indice} contem autoridade")

        texto = str(candidato.get("texto") or "")
        intent = str(candidato.get("intent_proposta") or "").strip().upper()
        action = str(candidato.get("action_proposta") or "").strip().casefold()
        ato = str(proposta.get("ato") or "").strip().casefold()
        if ato not in PAPEIS:
            raise ValueError(f"candidato {indice}: ato fora do perfil")

        ancora = _span_unico(texto, proposta.get("ancora"), "ancora")
        alvo = _span_unico(texto, proposta.get("alvo"), "alvo")
        fonte_v4 = {
            "versao": 4,
            "texto_entrada": texto,
            "nos": [{
                "id": "n0",
                "intent": intent,
                "action": action,
                "ato": ato,
                "trecho": {
                    "inicio": 0,
                    "fim": len(texto),
                    "texto": texto,
                },
                "ancora": ancora,
                "alvos": [alvo],
            }],
            "relacoes": [],
            **deepcopy(FLAGS),
        }

        parametro = proposta.get("parametro")
        parametros: list[dict[str, Any]] = []
        if (intent, action) == ("VOLUME", "set"):
            if not isinstance(parametro, Mapping):
                raise ValueError(f"candidato {indice}: volume set exige parametro")
            evidencia = _span_unico(
                texto,
                parametro.get("evidencia"),
                "evidencia de parametro",
            )
            parametros = [{
                "ocorrencia": "n0",
                "nome": str(parametro.get("nome") or ""),
                "valor": parametro.get("valor"),
                "unidade": str(parametro.get("unidade") or ""),
                "evidencia": evidencia,
            }]
        elif parametro is not None:
            raise ValueError(f"candidato {indice}: parametro fora do perfil")

        anotacao = {
            "versao": 1,
            "perfil": PERFIL,
            "escopo": "literal_imediato",
            "origem_rotulo": "curadoria_ia",
            "referencia_rotulo": (
                f"rascunho_prospectivo_20260922/indice_{indice}"
            ),
            "fonte_v4": fonte_v4,
            "parametros": parametros,
            **deepcopy(FLAGS),
        }
        preparado = preparar_exemplo_operacional(deepcopy(anotacao))
        if preparado.get("dados_prontos_para_treino") is not False:
            raise RuntimeError("supervisao operacional elevou autoridade")

        exemplo = preparar_exemplo_validacao_operacional(
            anotacao,
            validation_group=str(candidato.get("grupo_texto") or ""),
            validation_entity_group=_grupo_entidade(
                intent,
                action,
                str(
                    proposta.get("alvo_canonico")
                    or proposta.get("alvo")
                    or ""
                ),
            ),
        )
        saida.append({
            "indice_fila": indice,
            "anotacao": anotacao,
            "exemplo_validacao": exemplo,
        })

    por_variante = Counter(
        (
            item["exemplo_validacao"]["intent"],
            item["exemplo_validacao"]["action"],
        )
        for item in saida
    )
    return {
        "versao": 1,
        "fonte_triagem_sha256": sha_fonte,
        "contrato": {
            "uso": "rascunho_curadoria_ia",
            "revisao_humana": False,
            "dados_prontos_para_treino": False,
            "treino_permitido": False,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
        },
        "resumo": {
            "total_candidatos": len(saida),
            "por_variante": {
                f"{intent}/{action}": total
                for (intent, action), total in sorted(por_variante.items())
            },
        },
        "itens": saida,
    }

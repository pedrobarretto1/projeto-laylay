"""Validate AI annotation proposals against a frozen operational triage.

Proposals remain development curation. This module does not certify human
review, training readiness, promotion, or execution authority.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .adaptador_validacao_operacional import (
    preparar_exemplo_validacao_operacional,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON de resumo invalido")
    return dict(value)


def _load_jsonl(path: str | Path) -> tuple[list[dict[str, Any]], bytes]:
    raw = Path(path).read_bytes()
    values = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"linha {line_number} da triagem nao e objeto")
        values.append(dict(value))
    return values, raw


def preparar_propostas_anotacao(
    fila_triagem_path: str | Path,
    resumo_triagem_path: str | Path,
    manifesto: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(manifesto, Mapping):
        raise TypeError("manifesto deve ser mapeamento")
    if int(manifesto.get("versao") or 0) != 1:
        raise ValueError("versao de manifesto desconhecida")
    if str(manifesto.get("origem_rotulo") or "").strip().casefold() != "curadoria_ia":
        raise ValueError("propostas precisam declarar origem curadoria_ia")
    if manifesto.get("revisao_humana") is not False:
        raise ValueError("curadoria IA nao certifica revisao humana")
    if any(
        manifesto.get(key) is not False
        for key in ("treino_permitido", "autoriza_execucao", "autoriza_promocao")
    ):
        raise ValueError("manifesto nao pode conceder autoridade")

    itens, raw = _load_jsonl(fila_triagem_path)
    resumo = _load_json(resumo_triagem_path)
    sha_triagem = _sha(raw)
    if manifesto.get("fonte_triagem_sha256") != sha_triagem:
        raise ValueError("manifesto deve declarar o SHA exato da triagem")
    contrato_fonte = resumo.get("contrato")
    if not isinstance(contrato_fonte, Mapping) or any(
        contrato_fonte.get(key) is not False
        for key in (
            "revisao_humana",
            "dados_prontos_para_treino",
            "treino_permitido",
            "autoriza_execucao",
            "autoriza_promocao",
        )
    ):
        raise ValueError("triagem de origem nao esta isolada")

    por_grupo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in itens:
        if item.get("status") != "candidato_literal":
            continue
        grupo = str(item.get("grupo_texto") or "").strip()
        if not grupo:
            raise ValueError("candidato literal sem grupo_texto")
        por_grupo[grupo].append(item)

    for grupo, grupo_itens in por_grupo.items():
        textos = {str(item.get("texto") or "") for item in grupo_itens}
        variantes = {
            (
                str(item.get("intent_proposta") or "").strip().upper(),
                str(item.get("action_proposta") or "").strip().casefold(),
            )
            for item in grupo_itens
        }
        if len(textos) != 1 or len(variantes) != 1:
            raise ValueError(
                f"grupo {grupo} mistura texto ou variante na triagem"
            )

    propostas = manifesto.get("propostas")
    if not isinstance(propostas, list):
        raise ValueError("manifesto precisa listar propostas")
    por_grupo_manifesto: dict[str, dict[str, Any]] = {}
    for proposta in propostas:
        if not isinstance(proposta, Mapping):
            raise ValueError("proposta invalida")
        grupo = str(proposta.get("grupo_texto") or "").strip()
        if not grupo or grupo in por_grupo_manifesto:
            raise ValueError(
                "manifesto deve cobrir grupos candidatos sem duplicacao"
            )
        por_grupo_manifesto[grupo] = dict(proposta)
    if set(por_grupo_manifesto) != set(por_grupo):
        raise ValueError(
            "manifesto deve cobrir todos os grupos candidatos exatamente uma vez"
        )

    exemplos: list[dict[str, Any]] = []
    for grupo in sorted(por_grupo):
        grupo_itens = por_grupo[grupo]
        proposta = por_grupo_manifesto[grupo]
        entidade = str(
            proposta.get("validation_entity_group") or ""
        ).strip().casefold()
        if not entidade:
            raise ValueError(
                f"grupo {grupo}: validation_entity_group obrigatorio"
            )
        anotacao = proposta.get("anotacao")
        if not isinstance(anotacao, Mapping):
            raise ValueError(f"grupo {grupo}: anotacao ausente")
        anotacao_dict = deepcopy(dict(anotacao))
        if (
            str(anotacao_dict.get("origem_rotulo") or "").strip().casefold()
            != "curadoria_ia"
        ):
            raise ValueError(
                f"grupo {grupo}: proposta nao pode alegar revisao humana"
            )

        exemplo = preparar_exemplo_validacao_operacional(
            anotacao_dict,
            validation_group=grupo,
            validation_entity_group=entidade,
        )
        intent_triagem = str(
            grupo_itens[0].get("intent_proposta") or ""
        ).strip().upper()
        action_triagem = str(
            grupo_itens[0].get("action_proposta") or ""
        ).strip().casefold()
        if (
            exemplo["intent"],
            exemplo["action"],
        ) != (intent_triagem, action_triagem):
            raise ValueError(
                f"grupo {grupo}: anotacao diverge da triagem intent/action"
            )
        texto_triagem = str(grupo_itens[0].get("texto") or "")
        if exemplo["text"] != texto_triagem:
            raise ValueError(
                f"grupo {grupo}: anotacao diverge do texto da triagem"
            )
        exemplo["indices_fila"] = sorted(
            int(item["indice_fila"]) for item in grupo_itens
        )
        exemplo["proposta_anotacao"] = anotacao_dict
        exemplos.append(exemplo)

    return {
        "versao": 1,
        "fonte_triagem_sha256": sha_triagem,
        "contrato": {
            "uso": "propostas_anotacao_operacional",
            "origem_rotulo": "curadoria_ia",
            "revisao_humana": False,
            "dados_prontos_para_treino": False,
            "treino_permitido": False,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
        },
        "resumo": {
            "eventos_candidatos": sum(
                len(values) for values in por_grupo.values()
            ),
            "textos_distintos_candidatos": len(por_grupo),
        },
        "exemplos": exemplos,
    }

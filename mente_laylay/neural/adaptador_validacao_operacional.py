"""Adapta supervisão operacional revisada para validação offline de extensões.

Esta camada não cria rótulos, não autoriza treino/promoção e não decide se a
fala é comando. Ela apenas expõe a variante intent/action já anotada para o
comparativo de extensão, preservando ato, alvos e parâmetros como diagnóstico.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .supervisao_operacional_v1 import (
    PERFIL,
    preparar_exemplo_operacional,
)
from .supervisao_relacoes_v4 import FLAGS


def _grupo_explicito(valor: object, nome: str) -> str:
    grupo = str(valor or "").strip().casefold()
    if not grupo:
        raise ValueError(f"{nome} precisa ser explícito")
    return grupo


def preparar_exemplo_validacao_operacional(
    anotacao: Mapping[str, Any],
    *,
    validation_group: str,
    validation_entity_group: str,
) -> dict[str, Any]:
    """Produz um exemplo one-vs-rest de intent/action sem perder o gold rico.

    A primeira versão aceita somente uma variante intent/action por texto. Casos
    com múltiplas variantes precisam de avaliação segmentada para não achatar
    operações diferentes no mesmo rótulo escalar.
    """
    grupo = _grupo_explicito(validation_group, "validation_group")
    grupo_entidade = _grupo_explicito(
        validation_entity_group,
        "validation_entity_group",
    )

    preparado = preparar_exemplo_operacional(deepcopy(dict(anotacao)))
    supervisao = preparado["supervisao"]
    fonte = supervisao["fonte_v4"]
    nos = list(fonte.get("nos") or [])
    if not nos:
        raise ValueError("supervisão operacional sem ocorrência")

    variantes = sorted({
        (
            str(no.get("intent") or "").strip().upper(),
            str(no.get("action") or "").strip().casefold(),
        )
        for no in nos
    })
    if len(variantes) != 1:
        raise ValueError(
            "mais de uma variante intent/action exige validação segmentada"
        )
    intent, action = variantes[0]
    if not intent or intent == "NONE" or not action or action == "none":
        raise ValueError("variante operacional inválida")

    atos = sorted({
        str(no.get("ato") or "").strip().casefold()
        for no in nos
        if str(no.get("ato") or "").strip()
    })
    ocorrencias = [
        {
            "id": str(no.get("id") or ""),
            "intent": str(no.get("intent") or "").strip().upper(),
            "action": str(no.get("action") or "").strip().casefold(),
            "ato": str(no.get("ato") or "").strip().casefold(),
            "alvos": deepcopy(no.get("alvos") or []),
        }
        for no in nos
    ]

    return {
        "text": str(preparado["entrada"]["texto"]),
        "intent": intent,
        "action": action,
        "extension_scope": PERFIL,
        "validation_group": grupo,
        "validation_entity_group": grupo_entidade,
        "diagnostico_operacional": {
            "atos": atos,
            "ocorrencias": ocorrencias,
            "parametros": deepcopy(supervisao.get("parametros") or []),
            "rotulos": list(supervisao.get("rotulos") or []),
            "origem_rotulo": str(preparado.get("origem_rotulo") or ""),
            "referencia_rotulo": str(
                preparado.get("referencia_rotulo") or ""
            ),
            "revisao_semantica_certificada": bool(
                preparado.get("revisao_semantica_certificada")
            ),
            "dados_prontos_para_treino": bool(
                preparado.get("dados_prontos_para_treino")
            ),
            "flags": {
                chave: bool(preparado.get(chave))
                for chave in sorted(FLAGS)
            },
        },
        "contrato": {
            "uso": "validacao_offline",
            "treino_permitido": False,
            "autoriza_promocao": False,
            "autoriza_execucao": False,
        },
    }

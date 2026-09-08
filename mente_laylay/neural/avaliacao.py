"""Métricas de segurança para o especialista neural de comandos."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


def _dividir(numerador: int, denominador: int) -> float:
    return numerador / denominador if denominador else 0.0


def head_aplicavel(exemplo: Mapping[str, Any], head: str) -> bool:
    """Diz se o rótulo do exemplo pertence ao escopo de avaliação do head."""
    declarados = exemplo.get("training_heads")
    if declarados is None:
        return True
    alvo = str(head or "").strip().casefold()
    return alvo in {
        str(item or "").strip().casefold() for item in declarados
    }


def avaliar_previsoes(
    esperados: Iterable[Mapping[str, Any]],
    previstos: Iterable[Mapping[str, Any]],
    *,
    acoes_por_intent: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, Any]:
    pares = list(zip(esperados, previstos, strict=True))
    total = len(pares)
    pares_comando_head = [
        (esperado, previsto)
        for esperado, previsto in pares
        if head_aplicavel(esperado, "command")
    ]
    pares_intent_head = [
        (esperado, previsto)
        for esperado, previsto in pares
        if head_aplicavel(esperado, "intent")
    ]
    pares_negacao_head = [
        (esperado, previsto)
        for esperado, previsto in pares
        if head_aplicavel(esperado, "negation")
    ]
    pares_acao_head = [
        (esperado, previsto)
        for esperado, previsto in pares
        if head_aplicavel(esperado, "action")
        and bool(esperado.get("is_command"))
    ]
    pares_joint_head = [
        (esperado, previsto)
        for esperado, previsto in pares
        if head_aplicavel(esperado, "intent")
        and head_aplicavel(esperado, "action")
        and bool(esperado.get("is_command"))
    ]
    negativos = sum(
        not bool(esperado.get("is_command"))
        for esperado, _ in pares_comando_head
    )
    falsos_comandos = sum(
        not bool(esperado.get("is_command")) and bool(previsto.get("is_command"))
        for esperado, previsto in pares_comando_head
    )
    verdadeiros_comandos = sum(
        bool(esperado.get("is_command")) and bool(previsto.get("is_command"))
        for esperado, previsto in pares_comando_head
    )
    comandos_previstos = sum(
        bool(previsto.get("is_command")) for _, previsto in pares_comando_head
    )
    comandos_esperados = sum(
        bool(esperado.get("is_command")) for esperado, _ in pares_comando_head
    )
    intent_corretas = sum(
        str(esperado.get("intent") or "").upper()
        == str(previsto.get("intent") or "").upper()
        for esperado, previsto in pares_intent_head
    )
    negacoes_corretas = sum(
        bool(esperado.get("negated")) == bool(previsto.get("negated"))
        for esperado, previsto in pares_negacao_head
    )
    negacoes_esperadas = sum(
        bool(esperado.get("negated")) for esperado, _ in pares_negacao_head
    )
    nao_negadas_esperadas = len(pares_negacao_head) - negacoes_esperadas
    negacoes_perdidas = sum(
        bool(esperado.get("negated")) and not bool(previsto.get("negated"))
        for esperado, previsto in pares_negacao_head
    )
    negacoes_falsas = sum(
        not bool(esperado.get("negated")) and bool(previsto.get("negated"))
        for esperado, previsto in pares_negacao_head
    )
    mapa_acoes = {
        str(intent or "").strip().upper(): {
            str(acao or "none").strip().casefold()
            for acao in acoes
        }
        for intent, acoes in dict(acoes_por_intent or {}).items()
    }

    def _acao_operacional_prevista(previsto: Mapping[str, Any]) -> str:
        params = previsto.get("params")
        if isinstance(params, Mapping):
            return str(params.get("acao") or "none").strip().casefold()
        return str(previsto.get("action") or "none").strip().casefold()

    def _acao_head_prevista(previsto: Mapping[str, Any]) -> str:
        if previsto.get("raw_action") is not None:
            return str(previsto.get("raw_action") or "none").strip().casefold()
        return _acao_operacional_prevista(previsto)

    acoes_corretas = sum(
        str(esperado.get("action") or "none").strip().casefold()
        == _acao_head_prevista(previsto)
        for esperado, previsto in pares_acao_head
    )
    intent_e_acao_corretas = sum(
        str(esperado.get("intent") or "").strip().upper()
        == str(previsto.get("intent") or "").strip().upper()
        and str(esperado.get("action") or "none").strip().casefold()
        == _acao_head_prevista(previsto)
        for esperado, previsto in pares_joint_head
    )
    comandos_previstos_para_consistencia = [
        previsto
        for _, previsto in pares
        if bool(previsto.get("is_command"))
    ]
    intents_comando_desconhecidas = (
        sum(
            str(previsto.get("intent") or "").strip().upper() not in mapa_acoes
            for previsto in comandos_previstos_para_consistencia
        )
        if mapa_acoes
        else 0
    )
    acoes_incompativeis_intent_conhecida = (
        sum(
            intent in mapa_acoes
            and _acao_operacional_prevista(previsto) not in mapa_acoes[intent]
            for previsto in comandos_previstos_para_consistencia
            for intent in [str(previsto.get("intent") or "").strip().upper()]
        )
        if mapa_acoes
        else 0
    )
    combinacoes_invalidas = (
        intents_comando_desconhecidas + acoes_incompativeis_intent_conhecida
    )
    return {
        "total": total,
        "negative_count": negativos,
        "false_command_count": falsos_comandos,
        "false_command_rate": _dividir(falsos_comandos, negativos),
        "command_precision": _dividir(verdadeiros_comandos, comandos_previstos),
        "command_recall": _dividir(verdadeiros_comandos, comandos_esperados),
        "intent_accuracy": _dividir(intent_corretas, len(pares_intent_head)),
        "negation_accuracy": _dividir(
            negacoes_corretas, len(pares_negacao_head)
        ),
        "missed_negation_count": negacoes_perdidas,
        "missed_negation_rate": _dividir(negacoes_perdidas, negacoes_esperadas),
        "false_negation_count": negacoes_falsas,
        "false_negation_rate": _dividir(negacoes_falsas, nao_negadas_esperadas),
        "action_accuracy_command": _dividir(
            acoes_corretas, len(pares_acao_head)
        ),
        "joint_intent_action_accuracy_command": _dividir(
            intent_e_acao_corretas, len(pares_joint_head)
        ),
        "invalid_intent_action_count": combinacoes_invalidas,
        "invalid_intent_action_rate": _dividir(
            combinacoes_invalidas, len(comandos_previstos_para_consistencia)
        ),
        "unknown_command_intent_count": intents_comando_desconhecidas,
        "incompatible_action_for_known_intent_count": (
            acoes_incompativeis_intent_conhecida
        ),
        "head_evaluation_counts": {
            "command": len(pares_comando_head),
            "intent": len(pares_intent_head),
            "negation": len(pares_negacao_head),
            "action_command": len(pares_acao_head),
            "joint_intent_action_command": len(pares_joint_head),
        },
    }

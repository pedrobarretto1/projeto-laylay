"""Gate determinístico para promoção de modelos neurais."""

from __future__ import annotations

from typing import Any, Mapping


def avaliar_promocao(
    metricas_estavel: Mapping[str, Any] | None,
    metricas_candidato: Mapping[str, Any],
    *,
    evidencia_aprendizado: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    candidato = dict(metricas_candidato or {})
    estavel = dict(metricas_estavel or {})
    evidencia = dict(evidencia_aprendizado or {})
    obrigatorias = {
        "intent_accuracy",
        "false_command_rate",
        "command_precision",
        "negation_accuracy",
    }
    ausentes = sorted(obrigatorias - candidato.keys())
    if ausentes:
        return {"promover": False, "motivos": ["metricas_ausentes:" + ",".join(ausentes)]}
    if not estavel:
        limites_iniciais = {
            "false_command_rate": 0.10,
            "command_precision": 0.85,
            "command_recall": 0.85,
            "negation_accuracy": 0.90,
            "missed_negation_rate": 0.0,
        }
        motivos = [
            f"{nome}_fora_do_limite"
            for nome, limite in limites_iniciais.items()
            if (
                float(candidato[nome]) > limite
                if nome in {"false_command_rate", "missed_negation_rate"}
                else float(candidato[nome]) < limite
            )
        ]
        return {"promover": not motivos, "motivos": motivos, "primeiro_modelo": True}

    maiores_melhores = (
        "intent_accuracy",
        "command_precision",
        "command_recall",
        "negation_accuracy",
    )
    menores_melhores = (
        "false_command_rate",
        "missed_negation_rate",
    )
    metricas_melhoradas = [
        nome
        for nome in maiores_melhores
        if nome in candidato
        and nome in estavel
        and float(candidato[nome]) > float(estavel[nome])
    ] + [
        nome
        for nome in menores_melhores
        if nome in candidato
        and nome in estavel
        and float(candidato[nome]) < float(estavel[nome])
    ]
    aprendizado_novo = bool(
        evidencia.get("dados_aprendidos_novos")
        or evidencia.get("dataset_base_alterado")
        or evidencia.get("lotes_candidatos_novos")
        or evidencia.get("estrategia_alterada")
        or evidencia.get("arquitetura_acao_alterada")
        or evidencia.get("arquitetura_comando_alterada")
        or evidencia.get("limiar_comando_alterado")
        or evidencia.get("representacao_alterada")
        or metricas_melhoradas
    )
    motivos: list[str] = []
    if not aprendizado_novo:
        motivos.append("sem_aprendizado_novo")
    if float(candidato["false_command_rate"]) > float(estavel.get("false_command_rate", 1.0)):
        motivos.append("false_command_rate_piorou")
    if float(candidato["negation_accuracy"]) < float(estavel.get("negation_accuracy", 0.0)):
        motivos.append("negation_accuracy_piorou")
    if (
        "missed_negation_rate" in candidato
        and float(candidato["missed_negation_rate"])
        > float(estavel.get("missed_negation_rate", 1.0))
    ):
        motivos.append("missed_negation_rate_piorou")
    if float(candidato["command_precision"]) < float(estavel.get("command_precision", 0.0)):
        motivos.append("command_precision_piorou")
    if (
        "command_recall" in candidato
        and "command_recall" in estavel
        and float(candidato["command_recall"]) < float(estavel["command_recall"])
    ):
        motivos.append("command_recall_piorou")
    if float(candidato["intent_accuracy"]) < float(estavel.get("intent_accuracy", 0.0)):
        motivos.append("intent_accuracy_piorou")
    return {
        "promover": not motivos,
        "motivos": motivos,
        "primeiro_modelo": False,
        "aprendizado_novo": aprendizado_novo,
        "metricas_melhoradas": metricas_melhoradas,
        "evidencia_aprendizado": evidencia,
    }

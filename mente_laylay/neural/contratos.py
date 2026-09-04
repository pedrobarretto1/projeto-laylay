"""Contratos pequenos entre o especialista linguístico e a mente canônica."""

from __future__ import annotations

import hashlib
import time
from typing import Any, Iterable, Mapping


def _confianca(valor: Any) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = 0.0
    return round(max(0.0, min(1.0, numero)), 4)


def _parametros_seguros(valor: Any) -> dict[str, Any]:
    if not isinstance(valor, Mapping):
        return {}
    resultado: dict[str, Any] = {}
    for chave, item in list(valor.items())[:16]:
        nome = str(chave or "").strip()[:80]
        if not nome:
            continue
        if item is None or isinstance(item, (bool, int, float)):
            resultado[nome] = item
        elif isinstance(item, str):
            resultado[nome] = item.strip()[:240]
    return resultado


def normalizar_previsao_neural(
    dados: Any,
    *,
    texto: str,
    modelo: str,
    intents_permitidas: Iterable[str],
    agora: float | None = None,
) -> dict[str, Any]:
    """Valida uma previsão sem jamais convertê-la em autoridade operacional."""
    bruto = dict(dados or {}) if isinstance(dados, Mapping) else {}
    permitidas = {
        str(intent or "").strip().upper()
        for intent in intents_permitidas
        if str(intent or "").strip()
    }
    intent = str(bruto.get("intent") or "").strip().upper()
    intent_conhecida = bool(intent and intent in permitidas)
    if not intent_conhecida:
        intent = ""

    confiancas_brutas = (
        dict(bruto.get("confidence") or {})
        if isinstance(bruto.get("confidence"), Mapping)
        else {"overall": bruto.get("confidence")}
    )
    confiancas = {
        "intent": _confianca(confiancas_brutas.get("intent")),
        "command": _confianca(confiancas_brutas.get("command")),
        "negation": _confianca(confiancas_brutas.get("negation")),
        "action": _confianca(confiancas_brutas.get("action")),
    }
    fala = " ".join(str(texto or "").strip().split())[:500]
    ood = bool(bruto.get("ood") or (bruto.get("intent") and not intent_conhecida))
    ood_calibrated = bool(bruto.get("ood_calibrated", True))
    return {
        "versao": 1,
        "modelo": str(modelo or "desconhecido").strip()[:100],
        "texto": fala,
        "texto_hash": hashlib.sha256(fala.casefold().encode("utf-8")).hexdigest(),
        "intent": intent,
        "params": _parametros_seguros(bruto.get("params")),
        "is_command": bool(bruto.get("is_command")),
        "negated": bool(bruto.get("negated")),
        "ood": ood,
        "ood_calibrated": ood_calibrated,
        "confidence": confiancas,
        "source": "neural_local",
        "somente_observacao": True,
        "autoriza_execucao": False,
        "ts": float(agora if agora is not None else time.time()),
    }

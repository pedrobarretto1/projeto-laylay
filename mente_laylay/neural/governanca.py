"""Gate determinístico entre uma previsão neural e a arbitragem existente."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


RISCOS_NUNCA_DIRETOS = frozenset({"DESTRUCTIVE", "CRITICAL"})


def _resultado(permitido: bool, motivo: str, intent: str = "") -> dict[str, Any]:
    return {
        "permitido": bool(permitido),
        "motivo": str(motivo or "")[:180],
        "intent": str(intent or "").strip().upper(),
        "autoridade": "gate_python" if permitido else "nenhuma",
    }


def avaliar_roteamento_neural(
    *,
    previsao: Mapping[str, Any] | None,
    turno_legado: Mapping[str, Any] | None,
    execucao_habilitada: bool,
    intents_habilitadas: Iterable[str],
    riscos_habilitados: Iterable[str],
    risco_intent: Mapping[str, str],
    thresholds: Mapping[str, float],
) -> dict[str, Any]:
    """Autoriza um candidato, nunca um efeito; árbitro e executor continuam depois."""
    leitura = dict(previsao or {})
    turno = dict(turno_legado or {})
    intent = str(leitura.get("intent") or "").strip().upper()
    if not execucao_habilitada:
        return _resultado(False, "kill_switch_desligado", intent)
    if bool(turno.get("veto_execucao_operacional")):
        return _resultado(False, "veto_operacional_soberano", intent)
    if not leitura.get("somente_observacao") or leitura.get("autoriza_execucao") is not False:
        return _resultado(False, "contrato_neural_invalido", intent)
    if not leitura.get("is_command"):
        return _resultado(False, "fala_nao_classificada_como_comando", intent)
    if leitura.get("ood_calibrated") is not True:
        return _resultado(False, "ood_nao_calibrado", intent)
    if leitura.get("negated"):
        return _resultado(False, "acao_negada", intent)
    if leitura.get("ood") or not intent:
        return _resultado(False, "fora_de_distribuicao", intent)
    habilitadas = {str(item).upper() for item in intents_habilitadas}
    if intent not in habilitadas:
        return _resultado(False, "intent_nao_habilitada", intent)
    risco = str(risco_intent.get(intent) or "UNKNOWN").strip().upper()
    riscos = {str(item).upper() for item in riscos_habilitados}
    if risco in RISCOS_NUNCA_DIRETOS or risco not in riscos:
        return _resultado(False, f"risco_nao_habilitado:{risco}", intent)
    confiancas = dict(leitura.get("confidence") or {})
    confianca = float(confiancas.get("intent") or 0.0)
    threshold = float(thresholds.get(intent, 1.0))
    if confianca < threshold:
        return _resultado(False, "confianca_abaixo_do_threshold", intent)
    return _resultado(True, "candidato_neural_liberado_para_arbitragem", intent)

"""Política central de segurança para ações no ambiente físico."""

from __future__ import annotations

from mente_laylay.iot.contratos import DecisaoSeguranca, DispositivoIoT


ORIGENS_AUTONOMAS = {"autonomia", "rotina", "cena", "agendamento", "sensor"}


def avaliar_acao(
    dispositivo: DispositivoIoT,
    acao: str,
    *,
    origem: str = "usuario",
    confirmado: bool = False,
) -> DecisaoSeguranca:
    acao_norm = str(acao or "").strip().lower()
    origem_norm = str(origem or "usuario").strip().lower()

    if not dispositivo.ativo:
        return DecisaoSeguranca(False, False, "dispositivo desativado")
    if acao_norm not in dispositivo.capacidades:
        return DecisaoSeguranca(False, False, "capacidade não suportada")
    if acao_norm == "status":
        return DecisaoSeguranca(True)

    risco = str(dispositivo.risco or "moderado").strip().lower()
    if risco == "alto" and not confirmado:
        return DecisaoSeguranca(False, True, "dispositivo de alto risco exige confirmação")
    if origem_norm in ORIGENS_AUTONOMAS and risco in {"moderado", "alto"} and not confirmado:
        return DecisaoSeguranca(False, True, "ação autônoma exige confirmação")
    return DecisaoSeguranca(True)


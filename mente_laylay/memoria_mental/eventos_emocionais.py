"""Publicação efêmera de eventos emocionais na memória compartilhada."""

from __future__ import annotations

from typing import Any, Mapping

from mente_laylay.emocoes.contrato_causal import evento_tem_causa_rastreavel


def estado_eventos_emocionais_inicial() -> dict[str, Any]:
    return {
        "versao": 1,
        "atual": {},
        "historico": [],
        "rejeitados": [],
        "autoriza_execucao": False,
        "persistencia_pessoal": False,
    }


def publicar_evento_emocional_causal(
    estado_atual: Mapping[str, Any] | None,
    evento: Mapping[str, Any] | None,
) -> dict[str, Any]:
    estado = estado_eventos_emocionais_inicial()
    estado.update(dict(estado_atual or {}))
    estado["autoriza_execucao"] = False
    estado["persistencia_pessoal"] = False
    retrato = dict(evento or {})
    if not evento_tem_causa_rastreavel(retrato):
        rejeitados = [
            dict(item) for item in estado.get("rejeitados") or []
            if isinstance(item, Mapping)
        ]
        rejeitados.append(retrato)
        estado["rejeitados"] = rejeitados[-20:]
        return estado
    historico = [
        dict(item) for item in estado.get("historico") or []
        if isinstance(item, Mapping)
    ]
    referencia = str(retrato.get("evidencia_ref") or "")
    if (
        historico
        and referencia
        and str(historico[-1].get("evidencia_ref") or "") == referencia
    ):
        historico[-1] = retrato
    else:
        historico.append(retrato)
    estado["atual"] = retrato
    estado["historico"] = historico[-80:]
    return estado

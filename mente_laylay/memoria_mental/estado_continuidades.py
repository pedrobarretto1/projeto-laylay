"""Estado compartilhado das continuidades, sugestões e confirmações da Laylay."""

from __future__ import annotations

from typing import Any, Dict


def estado_continuidades_inicial() -> Dict[str, Any]:
    return {
        "comando_sugerido": None,
        "comando_sugerido_payload": None,
        "comando_pendente": None,
        "comando_pendente_payload": None,
        "comando_sugerido_estado": "NONE",
        "comando_sugerido_ts": 0.0,
        "rotina_sugestao_pendente": None,
        "playlist_sugestao_pendente": None,
        "email_sugestao_pendente": None,
    }


def atualizar_continuidades(estado_atual: Dict[str, Any] | None, **campos: Any) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    for chave, valor in campos.items():
        estado[chave] = valor
    return estado


def limpar_sugestao_atual(estado_atual: Dict[str, Any] | None) -> Dict[str, Any]:
    return atualizar_continuidades(
        estado_atual,
        comando_sugerido=None,
        comando_sugerido_payload=None,
        comando_pendente=None,
        comando_pendente_payload=None,
        comando_sugerido_estado="NONE",
        comando_sugerido_ts=0.0,
    )

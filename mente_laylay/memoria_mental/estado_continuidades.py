"""Estado compartilhado das continuidades, sugestões e confirmações da Laylay."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict


SUGESTAO_SEM_RESPOSTA_TIMEOUT_S = 600.0


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
        "sugestoes_bloqueadas_ate": {},
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


def sugestao_pendente_ativa(
    continuidades_get: Callable[..., Any] | None,
    *,
    agora: float | None = None,
) -> bool:
    """Informa se uma sugestão ainda pode receber resposta.

    A expiração é deliberadamente calculada sem alterar o estado. Assim os
    serviços de fundo voltam a funcionar após dez minutos, enquanto a camada
    de feedback ainda pode registrar o silêncio e limpar a pendência no
    próximo turno.
    """
    if not callable(continuidades_get):
        return False
    if continuidades_get("comando_sugerido_estado", "NONE") == "NONE":
        return False
    try:
        criada_em = float(continuidades_get("comando_sugerido_ts", 0.0) or 0.0)
        instante = float(time.time() if agora is None else agora)
    except (TypeError, ValueError):
        return False
    if criada_em <= 0.0:
        return False
    return instante - criada_em < SUGESTAO_SEM_RESPOSTA_TIMEOUT_S

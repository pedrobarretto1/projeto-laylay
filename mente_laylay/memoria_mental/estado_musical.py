"""Estado compartilhado do contexto musical vivo da Laylay."""

from __future__ import annotations

import time
from typing import Any, Dict


def estado_musical_inicial() -> Dict[str, Any]:
    return {
        "ultima_playlist": None,
        "playlist_bloqueada_ate": 0.0,
        "playlist_state": {
            "name": "",
            "index": 0,
            "user_intervened": False,
            "last_url": "",
        },
    }


def atualizar_estado_musical(estado_atual: Dict[str, Any] | None, **campos: Any) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    for chave, valor in campos.items():
        estado[chave] = valor
    if not isinstance(estado.get("playlist_state"), dict):
        estado["playlist_state"] = {
            "name": "",
            "index": 0,
            "user_intervened": False,
            "last_url": "",
        }
    return estado


def bloquear_playlist_temporariamente(
    estado_atual: Dict[str, Any] | None,
    segundos: float = 600.0,
) -> Dict[str, Any]:
    estado = atualizar_estado_musical(
        estado_atual,
        ultima_playlist=None,
        playlist_bloqueada_ate=time.time() + float(segundos or 600.0),
    )
    playlist_state = estado.get("playlist_state")
    if isinstance(playlist_state, dict):
        playlist_state["name"] = ""
        playlist_state["index"] = 0
        playlist_state["user_intervened"] = True
        playlist_state["last_url"] = ""
        playlist_state.pop("shuffle", None)
        playlist_state.pop("shuffle_queue", None)
        playlist_state.pop("shuffle_index", None)
    return estado


def playlist_bloqueada_agora(estado_atual: Dict[str, Any] | None) -> bool:
    try:
        return time.time() < float((estado_atual or {}).get("playlist_bloqueada_ate") or 0.0)
    except Exception:
        return False

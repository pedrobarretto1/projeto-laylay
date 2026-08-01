"""Primitivas compartilhadas da conversa natural."""

from __future__ import annotations

import re
from typing import Any, Dict

from mente_laylay.personalidade.ritmo_natural import ajustar_encerramento_organico


def _get(ctx: Dict[str, Any], chave: str, default: Any = None) -> Any:
    if isinstance(ctx, dict):
        return ctx.get(chave, default)
    return default


def _call(ctx: Dict[str, Any], chave: str, *args, default: Any = None, **kwargs) -> Any:
    fn = _get(ctx, chave)
    if callable(fn):
        return fn(*args, **kwargs)
    return default


def _normalizar(ctx: Dict[str, Any], texto: str) -> str:
    # A camada com apelidos também contém as correções tipográficas seguras.
    # Usá-la primeiro evita que "tduo bem" caia no fallback antes da correção.
    com_apelidos = _call(ctx, "_normalizar_texto_com_apelidos", texto, default=None)
    if com_apelidos is not None:
        return str(com_apelidos or "")
    return str(_call(ctx, "_normalizar_texto_curto", texto, default=str(texto or "").lower()) or "")


def _normalizar_apelidos(ctx: Dict[str, Any], texto: str) -> str:
    return str(_call(ctx, "_normalizar_texto_com_apelidos", texto, default=str(texto or "").lower()) or "")


def _ajustar(ctx: Dict[str, Any], fala: str, texto_usuario: str = "") -> str:
    fala_organica = ajustar_encerramento_organico(fala, texto_usuario)
    return str(_call(ctx, "_ajustar_fala_por_horario", fala_organica, texto_usuario, default=fala_organica) or fala_organica)


def _topico_para_fala(valor: Any) -> str:
    """Traduz identificadores da arquitetura antes de mostrá-los a Pedro."""
    bruto = str(valor or "").strip()
    mapa = {
        "GAME_VISION": "o que está na tela do jogo",
        "IOT_CONTROL": "o dispositivo que você mencionou",
        "MUSIC_SEARCH": "a música",
        "PLAYLIST_PLAY": "a playlist",
        "APP_OPEN": "o programa",
        "OPEN_URL": "o site",
    }
    if bruto.upper() in mapa:
        return mapa[bruto.upper()]
    if re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", bruto):
        return ""
    return bruto


def _fala_confirmacao(ctx: Dict[str, Any], chave: str, fallback: str, texto_usuario: str = "") -> str:
    return str(
        _call(
            ctx,
            "_fala_de_confirmacao_variada",
            chave,
            fallback=fallback,
            contexto=contexto_fala_curta(ctx),
            texto_usuario=texto_usuario,
            default=fallback,
        )
        or fallback
    )


def contexto_fala_curta(ctx: Dict[str, Any]) -> dict:
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    return {
        "current_emotion": _get(ctx, "current_emotion", "calma"),
        "emotion_level": _get(ctx, "emotion_level", mente.get("emotion_level", 1)),
        "ultima_habilidade": mente.get("ultima_habilidade", ""),
        "ultimo_alvo": mente.get("ultimo_alvo", ""),
        "ultimo_topico": _get(ctx, "ultimo_topico_conversa", mente.get("ultimo_topico", "")),
    }

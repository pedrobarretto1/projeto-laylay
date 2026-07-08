"""Coordenador unico do fluxo de intencao da Laylay."""

from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

INTENTS_EXECUTAVEIS = {
    "PLAYLIST_ADD",
    "PLAYLIST_PLAY",
    "PLAYLIST_LIST",
    "LAYLAY_PLAYLIST_LIST",
    "LAYLAY_PLAYLIST_COPY",
    "MUSIC_SEARCH",
    "MEDIA_CONTROL",
    "CANCELAR_ACAO",
    "CLOSE_TAB",
    "CLOSE_APP",
    "APP_OPEN",
    "VOLUME",
    "NETFLIX",
    "OPEN_URL",
    "SITE_ENTER",
    "MAXIMIZE_WINDOW",
    "WEATHER",
    "LISTAR_PLAYLISTS",
    "TOCAR_PLAYLIST",
    "TOCAR_PLAYLIST_SHUFFLE",
    "AGENDAR_LEMBRETE",
    "LISTAR_AGENDAMENTOS",
    "CANCELAR_AGENDAMENTO",
    "CREATE_FOLDER",
    "DELETE_ITEM",
    "SCREEN_CAPTURE",
    "ORGANIZAR_DESKTOP",
    "EMAIL_READ",
    "EMAIL_SYNC",
    "NOTIFICATIONS",
    "BRIEFING_REPEAT",
    "LOCK_PC",
}


def _call(ctx: Dict[str, Any], nome: str, *args: Any, default: Any = None, **kwargs: Any) -> Any:
    fn = ctx.get(nome) if isinstance(ctx, dict) else None
    if callable(fn):
        return fn(*args, **kwargs)
    return default


def _normalizar_intent(resultado: Any) -> str:
    if not isinstance(resultado, dict):
        return ""
    return str(resultado.get("intent") or resultado.get("acao") or "").upper().strip()


def resolver_intencao(texto: str, origem: str, ctx: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, str]:
    texto_norm = _call(ctx, "normalizar_texto", texto, default=str(texto or ""))
    _call(ctx, "refinar_contexto_mental", texto_norm)

    if _call(ctx, "texto_cancela_acao_agora", texto_norm, default=False):
        return {"intent": "CANCELAR_ACAO", "params": {}}, "imediato"

    # Continuidade musical contextual vem antes da repeticao generica.
    # Ex.: "toca ela de novo" deve ser replay da faixa atual, nao repetir
    # a ultima acao registrada como "musica anterior".
    intent_midia_contextual = _call(ctx, "resolver_comando_midia_contextual_forcado", texto_norm)
    if isinstance(intent_midia_contextual, dict):
        return intent_midia_contextual, "contexto-midia"

    intent_repeticao = _call(ctx, "resolver_repeticao_ultima_acao", texto_norm)
    if isinstance(intent_repeticao, dict):
        return intent_repeticao, "repeticao"

    intent = _call(ctx, "detectar_intencao_deterministica", texto_norm)
    if isinstance(intent, dict):
        return intent, "deterministico"

    intent = _call(ctx, "tentar_intencao_ai_primeiro", texto)
    if isinstance(intent, dict):
        return intent, "ia-first"

    return None, ""


def executar_fluxo_intencao(texto: str, origem: str, ctx: Dict[str, Any]) -> bool:
    intent, rota = resolver_intencao(texto, origem, ctx)
    if not isinstance(intent, dict):
        return False

    tag = f" [{origem}]" if origem else ""
    if rota == "imediato":
        tag = f"[{origem}]" if origem else ""
    print(f"⚡ [ROTEADOR {rota.upper()}{tag}] {intent}")

    try:
        executou = bool(_call(ctx, "executar_intencao", intent, texto, default=False))
        _call(ctx, "registrar_resultado_execucao", intent, texto, executou, origem=f"{rota}:{origem}")
        if executou:
            _call(ctx, "registrar_autoaprimoramento", intent, texto, True, contexto=f"{rota}:{origem}", origem=origem)
        return executou
    except Exception as e:
        print(f"⚠️ [ROTEADOR {rota.upper()}] falha ao executar: {e}")
        return False

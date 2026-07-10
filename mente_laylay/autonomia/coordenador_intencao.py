"""Coordenador unico do fluxo de intencao da Laylay."""

from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

INTENTS_EXECUTAVEIS = {
    "PLAYLIST_ADD",
    "PLAYLIST_PLAY",
    "PLAYLIST_LIST",
    "PLAYLIST_DELETE",
    "LAYLAY_PLAYLIST_LIST",
    "LAYLAY_PLAYLIST_COPY",
    "MUSIC_SEARCH",
    "MEDIA_CONTROL",
    "CANCELAR_ACAO",
    "CLOSE_TAB",
    "CLOSE_APP",
    "APP_OPEN",
    "VOLUME",
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

    depende_contexto = bool(_call(ctx, "texto_depende_de_contexto", texto_norm, default=False))

    # Quando o usuario cita um alvo explicito, o deterministico precisa vencer
    # o contexto antigo. Ex.: "fecha a steam" nao pode virar "foca a steam".
    if not depende_contexto:
        intent = _call(ctx, "detectar_intencao_deterministica", texto_norm)
        if isinstance(intent, dict):
            return intent, "deterministico"

    # Continuidade contextual unificada vem antes da repeticao generica para
    # pronomes e respostas curtas. Ex.: "fecha ela", "coloca ele em foco".
    intent_contextual = _call(ctx, "resolver_comando_contextual_forcado", texto_norm)
    if isinstance(intent_contextual, dict):
        rota = str(intent_contextual.get("_rota_contextual") or "contexto").lower()
        intent_limpo = dict(intent_contextual)
        intent_limpo.pop("_rota_contextual", None)
        return intent_limpo, f"contexto-{rota}"

    intent_repeticao = _call(ctx, "resolver_repeticao_ultima_acao", texto_norm)
    if isinstance(intent_repeticao, dict):
        return intent_repeticao, "repeticao"

    if depende_contexto:
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

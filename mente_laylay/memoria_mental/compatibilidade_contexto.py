"""Adaptadores legados para consultas do contexto compartilhado.
As funções permanecem puras e não gravam estado. O módulo original as
reexporta enquanto os consumidores antigos migram para contratos tipados.
"""

from __future__ import annotations

from typing import Any, Dict

from mente_laylay.memoria_mental.continuidade_geral import selecionar_continuidade_por_classe


def texto_pede_repeticao_curta(texto: str, normalizar_texto_cb) -> bool:
    t = normalizar_texto_cb(str(texto or ""))
    if not t or len(t.split()) > 8:
        return False
    gatilhos = [
        "tenta de novo",
        "de novo",
        "tenta novamente",
        "novamente",
        "vai de novo",
        "faz de novo",
        "outra vez",
        "mais uma vez",
        "tenta outra vez",
    ]
    return any(g in t for g in gatilhos)


def resolver_repeticao_ultima_acao(
    texto: str,
    estado_atual: Dict[str, Any] | None,
    normalizar_texto_cb,
):
    if not texto_pede_repeticao_curta(texto, normalizar_texto_cb):
        return None
    estado = dict(estado_atual or {})
    oficial = selecionar_continuidade_por_classe(
        estado,
        classe="operacional",
        ttl_s=900.0,
    )
    if oficial:
        if not bool(oficial.get("reexecutavel")):
            return None
        intent = str(oficial.get("intent") or "").strip().upper()
        params = oficial.get("params")
    else:
        # Memórias de sessão anteriores à promoção oficial ainda podem ser
        # lidas uma vez; novos turnos sempre gravam o contrato canônico.
        if not bool(estado.get("ultima_acao_reexecutavel")):
            return None
        intent = str(estado.get("ultima_acao_intent") or "").strip().upper()
        params = estado.get("ultima_acao_params")
    if not intent or not isinstance(params, dict):
        return None
    return {"intent": intent, "params": dict(params)}


def contexto_musical_ativo(ultima_playlist: Any, playlist_state: Dict[str, Any]) -> bool:
    try:
        if str(ultima_playlist or "").strip():
            return True
        if str(playlist_state.get("name") or "").strip():
            return True
        if str(playlist_state.get("last_url") or "").strip():
            return True
    except Exception:
        pass
    return False


def contexto_mental_ativo(mente_integrada_estado: Dict[str, Any], ultima_playlist: Any, playlist_state: Dict[str, Any]) -> bool:
    try:
        estado = dict(mente_integrada_estado or {})
        if str(estado.get("ultima_entrada") or "").strip():
            return True
        if str(estado.get("ultima_intencao") or "").strip():
            return True
        if str(estado.get("ultimo_alvo") or "").strip():
            return True
        if str(estado.get("ultima_habilidade") or "").strip():
            return True
    except Exception:
        pass
    return contexto_musical_ativo(ultima_playlist, playlist_state)


def texto_depende_de_contexto(texto: str, normalizar_texto_cb) -> bool:
    from mente_laylay.cognicao.referencias_linguagem import texto_tem_referencia_contextual

    t = normalizar_texto_cb(texto)
    if not t:
        return False
    return texto_tem_referencia_contextual(t)


def fluxo_prioritario_da_ia(texto: str, normalizar_texto_cb, texto_depende_de_contexto_cb) -> bool:
    t = normalizar_texto_cb(texto)
    if not t:
        return False
    if any(p in t for p in ["playlist", "música", "musica", "site", "web", "aba", "janela", "foco", "tela cheia", "fullscreen", "opera", "chrome", "edge", "vscode"]):
        if texto_depende_de_contexto_cb(t):
            return True
        if any(p in t for p in ["coloca", "toca", "abre", "abra", "entra", "vai", "mostra", "lista", "quais"]):
            return True
    return False

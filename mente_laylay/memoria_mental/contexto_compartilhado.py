"""Funcoes de contexto compartilhado entre as habilidades da Laylay."""

from __future__ import annotations

import time
from typing import Any, Dict


def estado_mental_inicial() -> Dict[str, Any]:
    return {
        "ultima_entrada": "",
        "ultimas_entradas": [],
        "ultima_intencao": "",
        "ultimo_alvo": "",
        "ultimo_app_janela": "",
        "ultimo_site_aba": "",
        "ultima_pasta": "",
        "ultimo_arquivo": "",
        "ultimo_caminho_arquivo": "",
        "ultimo_escopo": "",
        "ultima_habilidade": "",
        "ultima_resposta": "",
        "ultima_acao_status": "",
        "ultima_acao_reexecutavel": False,
        "ultima_acao_intent": "",
        "ultima_acao_params": {},
        "ultima_acao_origem": "",
        "ultima_acao_texto": "",
        "pergunta_aberta_texto": "",
        "pergunta_aberta_topico": "",
        "pergunta_aberta_origem": "",
        "pergunta_aberta_ts": 0.0,
        "foco_vivo_tipo": "",
        "foco_vivo_alvo": "",
        "foco_vivo_topico": "",
        "foco_vivo_habilidade": "",
        "foco_vivo_intencao": "",
        "foco_vivo_texto": "",
        "foco_vivo_resposta": "",
        "foco_vivo_ts": 0.0,
        "ts": 0.0,
    }


def texto_parece_pergunta_aberta(texto: str) -> bool:
    """Detecta perguntas que esperam uma resposta curta do Pedro."""
    fala = str(texto or "").strip()
    if not fala or "?" not in fala:
        return False

    fala_low = fala.lower()
    bloqueios = [
        "quer que eu explique",
        "quer que eu repita",
        "quer que eu abra",
    ]
    # Mesmo esses casos ainda sao perguntas, mas costumam ter feedback proprio.
    if any(b in fala_low for b in bloqueios):
        return False

    sinais = [
        "quer",
        "pode",
        "prefere",
        "qual",
        "quais",
        "quando",
        "onde",
        "como",
        "por que",
        "porque",
        "o que",
        "e voce",
        "e você",
        "como voce",
        "como você",
        "voce esta",
        "você está",
        "ta bem",
        "tá bem",
        "tudo bem",
        "tudo na paz",
    ]
    return any(s in fala_low for s in sinais)


def registrar_pergunta_aberta(
    estado_atual: Dict[str, Any] | None,
    pergunta: str,
    *,
    topico: str = "",
    origem: str = "",
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    pergunta_limpa = str(pergunta or "").strip()
    if not texto_parece_pergunta_aberta(pergunta_limpa):
        return limpar_pergunta_aberta(estado)

    estado["pergunta_aberta_texto"] = pergunta_limpa[:240]
    estado["pergunta_aberta_topico"] = str(topico or "").strip()[:120]
    estado["pergunta_aberta_origem"] = str(origem or "").strip()[:80]
    estado["pergunta_aberta_ts"] = time.time()
    return estado


def limpar_pergunta_aberta(estado_atual: Dict[str, Any] | None) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    estado["pergunta_aberta_texto"] = ""
    estado["pergunta_aberta_topico"] = ""
    estado["pergunta_aberta_origem"] = ""
    estado["pergunta_aberta_ts"] = 0.0
    return estado


def pergunta_aberta_ativa(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 120.0,
) -> Dict[str, Any] | None:
    estado = dict(estado_atual or {})
    pergunta = str(estado.get("pergunta_aberta_texto") or "").strip()
    if not pergunta:
        return None
    try:
        ts = float(estado.get("pergunta_aberta_ts") or 0.0)
    except Exception:
        ts = 0.0
    if not ts or time.time() - ts > ttl_s:
        return None
    return {
        "pergunta": pergunta,
        "topico": str(estado.get("pergunta_aberta_topico") or "").strip(),
        "origem": str(estado.get("pergunta_aberta_origem") or "").strip(),
        "idade_s": max(0.0, time.time() - ts),
    }


def texto_parece_resposta_curta_a_pergunta(texto: str, normalizar_texto_cb) -> bool:
    t = normalizar_texto_cb(str(texto or ""))
    if not t:
        return False
    palavras = t.split()
    if len(palavras) > 12:
        return False
    if "?" in str(texto or ""):
        return False
    sinais_comando = [
        "abre", "abrir", "abra", "entra", "entrar", "fecha", "fechar",
        "coloca", "colocar", "toca", "tocar", "playlist", "musica", "música",
        "volume", "spotify", "youtube", "netflix",
        "cria", "criar", "apaga", "apagar", "move", "mover", "email",
        "le ", "lê ", "ler ", "site", "aba", "janela", "foco",
        "pausa", "pause", "despausa", "retoma", "continua", "próxima", "proxima",
        "anterior", "maximiza", "maximizar", "tela cheia", "fullscreen",
    ]
    if any(s in f" {t} " for s in sinais_comando):
        return False
    return True


def intencao_reexecutavel(intent: str) -> bool:
    return str(intent or "").upper().strip() in {
        "APP_OPEN",
        "OPEN_URL",
        "PLAYLIST_PLAY",
        "MUSIC_SEARCH",
        "VOLUME",
        "MEDIA_CONTROL",
        "WEATHER",
        "EMAIL_READ",
        "EMAIL_SYNC",
        "NOTIFICATIONS",
        "BRIEFING_REPEAT",
        "SITE_ENTER",
        "LAYLAY_PLAYLIST_LIST",
        "PLAYLIST_LIST",
    }


def registrar_resultado_execucao(
    estado_atual: Dict[str, Any] | None,
    resultado: Dict[str, Any] | None = None,
    texto: str = "",
    executou: bool = True,
    *,
    origem: str = "",
    status: str = "",
) -> Dict[str, Any]:
    if not isinstance(resultado, dict):
        return dict(estado_atual or {})

    estado = dict(estado_atual or {})
    intent = str(resultado.get("intent") or resultado.get("acao") or "").strip().upper()
    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
    status_final = str(status or "").strip().lower()
    texto_curto = str(texto or "").strip()[:200]

    if not status_final:
        mesmo_intent = str(estado.get("ultima_acao_intent") or "").strip().upper() == intent
        mesmo_texto = str(estado.get("ultima_acao_texto") or "").strip() == texto_curto
        status_anterior = str(estado.get("ultima_acao_status") or "").strip().lower()
        if mesmo_intent and mesmo_texto and status_anterior:
            status_final = status_anterior
        else:
            status_final = "executado" if executou else "falhou"

    estado["ultima_acao_status"] = status_final
    estado["ultima_acao_reexecutavel"] = bool(executou and intencao_reexecutavel(intent))
    estado["ultima_acao_intent"] = intent
    estado["ultima_acao_params"] = dict(params)
    estado["ultima_acao_origem"] = str(origem or "").strip()
    estado["ultima_acao_texto"] = texto_curto
    estado["ts"] = time.time()
    return estado


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
    t = normalizar_texto_cb(texto)
    if not t:
        return False
    palavras = t.split()
    if len(palavras) > 7:
        return False
    gatilhos = [
        "essa", "esse", "isso", "ele", "ela", "aqui", "ali", "tambem", "também",
        "de novo", "mais uma", "mais um", "essa tambem", "esse tambem",
        "essa também", "esse também", "essa aqui", "esse aqui", "essa ai", "esse ai",
    ]
    return any(g in t for g in gatilhos)


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

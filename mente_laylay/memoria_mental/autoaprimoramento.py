"""Autoaprimoramento e resumo de habilidades da Laylay."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


def normalizar_habilidade_autoaprimoramento(nome: str) -> str:
    t = str(nome or "").strip().lower()
    mapa = {
        "open_url": "navegacao",
        "youtube_search": "musica",
        "playlist_add": "playlist",
        "playlist_play": "playlist",
        "playlist_list": "playlist",
        "toocar_playlist": "playlist",
        "tocar_playlist": "playlist",
        "tocar_playlist_shuffle": "playlist",
        "music_search": "midia",
        "media_control": "midia",
        "close_tab": "navegacao",
        "close_app": "navegacao",
        "app_open": "navegacao",
        "screen_capture": "visao",
        "volume": "audio",
        "email_read": "emails",
        "email_sync": "emails",
        "notifications": "sistema",
        "agendar_lembrete": "agenda",
        "listar_agendamentos": "agenda",
        "cancelar_agendamento": "agenda",
        "organizar_desktop": "sistema",
        "maximize_window": "sistema",
        "create_folder": "sistema",
        "lock_pc": "sistema",
        "search": "pesquisa",
        "briefing_repeat": "conversa",
    }
    if t in mapa:
        return mapa[t]
    if "playlist" in t:
        return "playlist"
    if any(x in t for x in ["agend", "lembre", "compromiss", "compromisso"]):
        return "agenda"
    if any(x in t for x in ["email", "notific", "mensagem"]):
        return "emails"
    if any(x in t for x in ["volume", "som", "mudo", "mute"]):
        return "audio"
    if any(x in t for x in ["aba", "janela", "site", "url", "opera", "chrome", "naveg"]):
        return "navegacao"
    if any(x in t for x in ["pesquisa", "buscar", "procura", "quem é", "quem e"]):
        return "pesquisa"
    return "geral"


def inferir_habilidade_autoaprimoramento(resultado: Dict[str, Any] = None, texto: str = "") -> str:
    texto = str(texto or "").lower()
    resultado = resultado if isinstance(resultado, dict) else {}
    intent = str(resultado.get("intent") or resultado.get("acao") or resultado.get("action") or "").lower()
    t = f"{intent} {texto}"
    mapa_intent = {
        "PLAYLIST_CREATE": "playlist",
        "PLAYLIST_ADD": "playlist",
        "PLAYLIST_PLAY": "playlist",
        "PLAYLIST_LIST": "playlist",
        "PLAYLIST_MOVE": "playlist",
        "LEARNING_QUERY": "memoria",
        "TOCAR_PLAYLIST": "playlist",
        "TOCAR_PLAYLIST_SHUFFLE": "playlist",
        "MUSIC_SEARCH": "midia",
        "MEDIA_CONTROL": "midia",
        "OPEN_URL": "navegacao",
        "APP_OPEN": "navegacao",
        "IOT_CONTROL": "iot",
        "IOT_STATUS": "iot",
        "IOT_LIST": "iot",
        "CLOSE_APP": "navegacao",
        "CLOSE_TAB": "navegacao",
        "CLOSE_IDLE_TABS": "navegacao",
        "SITE_ENTER": "navegacao",
        "SCREEN_CAPTURE": "visao",
        "VOLUME": "audio",
        "EMAIL_READ": "emails",
        "EMAIL_SYNC": "emails",
        "NOTIFICATIONS": "sistema",
        "AGENDAR_LEMBRETE": "agenda",
        "AGENDAR_ACAO": "agenda",
        "LISTAR_AGENDAMENTOS": "agenda",
        "CANCELAR_AGENDAMENTO": "agenda",
        "ORGANIZAR_DESKTOP": "sistema",
        "MAXIMIZE_WINDOW": "sistema",
        "CREATE_FOLDER": "sistema",
        "LOCK_PC": "sistema",
        "SEARCH": "pesquisa",
        "BRIEFING_REPEAT": "conversa",
    }
    if intent in mapa_intent:
        return mapa_intent[intent]
    if "playlist" in t:
        return "playlist"
    if any(x in t for x in ["agend", "lembre", "compromiss", "compromisso"]):
        return "agenda"
    if any(x in t for x in ["email", "notific", "mensagem"]):
        return "emails"
    if any(x in t for x in ["volume", "som", "mudo", "mute"]):
        return "audio"
    if any(x in t for x in ["aba", "janela", "site", "url", "opera", "chrome", "naveg"]):
        return "navegacao"
    if any(x in t for x in ["pesquisa", "buscar", "procura", "quem é", "quem e"]):
        return "pesquisa"
    return "geral"


def registrar_autoaprimoramento(
    estado: Dict[str, Any],
    resultado: Dict[str, Any] = None,
    texto: str = "",
    sucesso: bool = True,
    erro: str = "",
    contexto: str = "",
    origem: str = "",
) -> Dict[str, Any]:
    estado = dict(estado or {})
    habilidades = dict(estado.get("habilidades") or {})
    eventos = list(estado.get("eventos") or [])

    habilidade = normalizar_habilidade_autoaprimoramento(inferir_habilidade_autoaprimoramento(resultado, texto))
    info = dict(habilidades.get(habilidade) or {})
    info.setdefault("sucessos", 0)
    info.setdefault("falhas", 0)
    info.setdefault("tentativas", 0)
    info.setdefault("ultima_entrada", "")
    info.setdefault("ultimo_erro", "")
    info.setdefault("ultima_correcao", "")
    info.setdefault("ultimos_erros", [])
    info.setdefault("ultimas_correcoes", [])
    info.setdefault("ultima_mudanca_ts", 0.0)
    info["tentativas"] += 1
    info["ultima_entrada"] = str(texto or "").strip()[:180]
    info["ultima_mudanca_ts"] = datetime.now().timestamp()

    erro_limpo = str(erro or "").strip()
    contexto_limpo = str(contexto or "").strip()
    origem_limpa = str(origem or "").strip()
    if sucesso:
        info["sucessos"] += 1
        if contexto_limpo:
            info["ultima_correcao"] = contexto_limpo[:180]
            ult_corr = list(info.get("ultimas_correcoes") or [])
            ult_corr.append(contexto_limpo[:180])
            info["ultimas_correcoes"] = ult_corr[-8:]
    else:
        info["falhas"] += 1
        if erro_limpo:
            info["ultimo_erro"] = erro_limpo[:220]
            ult_erros = list(info.get("ultimos_erros") or [])
            ult_erros.append(erro_limpo[:220])
            info["ultimos_erros"] = ult_erros[-8:]

    habilidades[habilidade] = info
    evento = {
        "ts": datetime.now().isoformat(" "),
        "habilidade": habilidade,
        "sucesso": bool(sucesso),
        "texto": str(texto or "").strip()[:180],
        "erro": erro_limpo[:220],
        "contexto": contexto_limpo[:180],
        "origem": origem_limpa[:80],
    }
    eventos.append(evento)
    estado["habilidades"] = habilidades
    estado["eventos"] = eventos[-40:]
    estado["ultimo_resumo"] = resumir_autoaprimoramento_estado(estado)
    estado["cookie_reforco"] = int(estado.get("cookie_reforco") or 0) + (1 if sucesso else 0)
    return estado


def resumir_autoaprimoramento_estado(estado: Dict[str, Any] = None, limit: int = 4) -> str:
    origem = estado if isinstance(estado, dict) else {}
    habilidades = origem.get("habilidades") if isinstance(origem, dict) else {}
    if not isinstance(habilidades, dict) or not habilidades:
        return "Autoaprimoramento: sem histórico ainda."

    itens = []
    for nome, info in habilidades.items():
        if not isinstance(info, dict):
            continue
        tentativas = max(1, int(info.get("tentativas") or 0))
        sucessos = int(info.get("sucessos") or 0)
        falhas = int(info.get("falhas") or 0)
        taxa = int(round((sucessos / tentativas) * 100))
        if sucessos == 0 and falhas == 0:
            continue
        detalhe = []
        ultimo_erro = str(info.get("ultimo_erro") or "").strip()
        ultima_corr = str(info.get("ultima_correcao") or "").strip()
        if falhas:
            detalhe.append(f"{falhas} falha(s)")
        if sucessos:
            detalhe.append(f"{sucessos} sucesso(s)")
        detalhe.append(f"{taxa}%")
        if ultima_corr:
            detalhe.append(f"ajuste={ultima_corr[:60]}")
        elif ultimo_erro:
            detalhe.append(f"erro={ultimo_erro[:60]}")
        itens.append((falhas, sucessos, f"{nome} " + ", ".join(detalhe)))

    if not itens:
        return "Autoaprimoramento: sem sinais úteis ainda."

    itens.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    partes = [x[2] for x in itens[:limit]]
    return "Autoaprimoramento: " + "; ".join(partes)


def resumo_autoaprimoramento_para_prompt(estado: Dict[str, Any] = None, limit: int = 4) -> str:
    try:
        return resumir_autoaprimoramento_estado(estado, limit=limit)
    except Exception:
        return "Autoaprimoramento: indisponível."

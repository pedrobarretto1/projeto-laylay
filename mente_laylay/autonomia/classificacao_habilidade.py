"""Classificação compacta usada no registro da memória curta operacional."""

from __future__ import annotations

from typing import Any, Dict


HABILIDADE_POR_INTENT = {
    "PLAYLIST_ADD": "playlist",
    "PLAYLIST_PLAY": "playlist",
    "PLAYLIST_LIST": "playlist",
    "PLAYLIST_MOVE": "playlist",
    "TOCAR_PLAYLIST": "playlist",
    "TOCAR_PLAYLIST_SHUFFLE": "playlist",
    "LAYLAY_PLAYLIST_LIST": "playlist_laylay",
    "LAYLAY_PLAYLIST_COPY": "playlist_laylay",
    "APP_OPEN": "navegacao",
    "CLOSE_APP": "navegacao",
    "MAXIMIZE_WINDOW": "navegacao",
    "ORGANIZAR_DESKTOP": "sistema_janelas",
    "OPEN_URL": "navegacao",
    "MUSIC_SEARCH": "midia",
    "MEDIA_CONTROL": "midia",
    "VOLUME": "audio",
    "CLOSE_TAB": "navegador",
    "CLOSE_IDLE_TABS": "navegador",
    "SEARCH": "pesquisa",
    "SITE_ENTER": "pesquisa",
    "WEATHER": "clima",
    "IOT_CONTROL": "iot",
    "IOT_STATUS": "iot",
    "IOT_LIST": "iot",
    "CLIPBOARD_READ": "area_transferencia",
    "CLIPBOARD_TRANSFORM": "area_transferencia",
    "CLIPBOARD_SEARCH": "area_transferencia",
    "CLIPBOARD_WRITE": "area_transferencia",
    "CLIPBOARD_UNDO": "area_transferencia",
    "CLIPBOARD_LEARN": "area_transferencia",
    "INBOX_ADD": "caixa_entrada",
    "INBOX_ADD_DISCUSSION": "caixa_entrada",
    "INBOX_LIST": "caixa_entrada",
    "INBOX_CONVERT_REMINDER": "caixa_entrada",
    "INBOX_DELETE": "caixa_entrada",
    "CONFIRM_INBOX_DELETE": "caixa_entrada",
    "CANCEL_INBOX_ACTION": "caixa_entrada",
    "COOPERATIVE_PLAN": "orquestracao_cooperativa",
    "FILE_SEARCH": "arquivos",
    "FILE_OPEN_RESULT": "arquivos",
    "AGENDAR_ACAO": "agenda",
    "AGENDAR_LEMBRETE": "agenda",
    "LISTAR_AGENDAMENTOS": "agenda",
    "CANCELAR_AGENDAMENTO": "agenda",
    "SUGGEST_ACTION": "sugestao",
    "LEARNING_QUERY": "memoria",
}


def classificar_habilidade_intent(intent: str) -> str:
    return HABILIDADE_POR_INTENT.get(str(intent or "").upper().strip(), "")


def extrair_alvo_mental(params: Dict[str, Any] | None) -> str:
    params = params if isinstance(params, dict) else {}
    esquerda = str(params.get("left") or params.get("esquerda") or "").strip()
    direita = str(params.get("right") or params.get("direita") or "").strip()
    if esquerda or direita:
        partes = []
        if esquerda:
            partes.append(f"{esquerda} na esquerda")
        if direita:
            partes.append(f"{direita} na direita")
        return " e ".join(partes)
    return str(
        params.get("nome_playlist")
        or params.get("nome_app")
        or params.get("query")
        or params.get("url")
        or params.get("alvo")
        or params.get("tema")
        or ""
    ).strip()

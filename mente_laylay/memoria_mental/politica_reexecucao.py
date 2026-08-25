"""Política neutra de reexecução da Laylay.

A ocorrência concreta continua decidindo se uma tentativa é reexecutável.
Este módulo declara apenas compatibilidade semântica e params extras de retry.
"""

from __future__ import annotations


_INTENTS_REEXECUTAVEIS_PADRAO = frozenset({
    "APP_OPEN", "CLOSE_APP", "OPEN_URL", "CLOSE_TAB", "PLAYLIST_PLAY",
    "PLAYLIST_ADD", "MUSIC_SEARCH", "VOLUME", "MEDIA_CONTROL", "WEATHER",
    "EMAIL_READ", "EMAIL_SYNC", "NOTIFICATIONS", "BRIEFING_REPEAT",
    "SITE_ENTER", "LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_PLAY",
    "PLAYLIST_LIST", "IOT_CONTROL", "IOT_STATUS", "IOT_LIST",
    "INBOX_LIST", "ORGANIZAR_DESKTOP", "FILE_READ",
})

_INTENTS_POR_ACAO_SEMANTICA = {
    "LER": frozenset({"FILE_READ", "EMAIL_READ"}),
}

_PARAMS_EXTRAS_REEXECUCAO = {
    "EMAIL_READ": frozenset({"urgentes"}),
}


def intencao_reexecutavel_padrao(intent: str) -> bool:
    return str(intent or "").strip().upper() in _INTENTS_REEXECUTAVEIS_PADRAO


def intents_compativeis_repeticao(acao_semantica: str) -> frozenset[str]:
    return _INTENTS_POR_ACAO_SEMANTICA.get(
        str(acao_semantica or "").strip().upper(),
        frozenset(),
    )


def params_extras_reexecucao(intent: str) -> frozenset[str]:
    return _PARAMS_EXTRAS_REEXECUCAO.get(
        str(intent or "").strip().upper(),
        frozenset(),
    )

"""Execução tipada de controles manuais do Terminal 3.

O painel não é uma segunda interface de linguagem natural. Cada controle
visual vira um intent canônico fechado, passa pelo executor oficial e não
chama interpretação nem autoria por LLM.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Mapping


_ACOES_MIDIA = {
    "media_previous": "prev",
    "media_next": "next",
    "media_replay": "replay",
    "media_repeat": "repeat_toggle",
}
ACOES_MUSICA_PAINEL = frozenset({
    *_ACOES_MIDIA,
    "media_toggle",
    "playlist_play",
    "playlist_shuffle",
    "queue_play",
    "volume_set",
    "audio_output_select",
})


def _nome_playlist(valor: Any) -> str:
    nome = re.sub(r"\s+", " ", str(valor or "").replace('"', " ")).strip()[:80]
    if not nome or re.search(r"[;&|<>]", nome):
        return ""
    return nome


def comando_tipado_acao_painel(
    acao_id: str,
    payload: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str] | None:
    """Traduz somente IDs e campos fechados; texto livre nunca é interpretado."""
    acao = str(acao_id or "").strip()
    dados = dict(payload or {})
    params: dict[str, Any]
    texto: str

    if acao in _ACOES_MIDIA:
        comando = _ACOES_MIDIA[acao]
        params = {"acao": comando}
        texto = f"controle manual de mídia: {comando}"
        intent = "MEDIA_CONTROL"
    elif acao == "media_toggle":
        comando = str(dados.get("command") or "").strip().casefold()
        if comando not in {"play", "pause"}:
            return None
        params = {"acao": comando}
        texto = f"controle manual de mídia: {comando}"
        intent = "MEDIA_CONTROL"
    elif acao in {"playlist_play", "playlist_shuffle"}:
        nome = _nome_playlist(dados.get("playlist"))
        if not nome:
            return None
        params = {"nome_playlist": nome}
        if acao == "playlist_shuffle":
            params["modo"] = "shuffle"
        texto = f"toca a playlist {nome}"
        intent = "PLAYLIST_PLAY"
    elif acao == "volume_set":
        nivel = dados.get("level")
        if isinstance(nivel, bool):
            return None
        try:
            nivel_int = int(nivel)
        except (TypeError, ValueError):
            return None
        if not 0 <= nivel_int <= 100:
            return None
        params = {"acao": "set", "nivel_volume": nivel_int}
        texto = f"controle manual de volume em {nivel_int} por cento"
        intent = "VOLUME"
    elif acao == "queue_play":
        item_id = str(dados.get("item_id") or "").strip()
        indice = dados.get("queue_index")
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", item_id):
            return None
        if isinstance(indice, bool):
            return None
        try:
            indice = int(indice)
        except (TypeError, ValueError):
            return None
        if not 0 <= indice <= 7:
            return None
        params = {
            "acao": "queue_select",
            "queue_item_id": item_id,
            "queue_index": indice,
            "platform": "youtube",
        }
        texto = f"controle manual da fila: item {indice + 1}"
        intent = "MEDIA_CONTROL"
    else:
        return None

    # O executor continua registrando evidência e confirmação. Apenas a fala
    # e qualquer chamada de LLM são suprimidas porque o próprio painel já
    # representa visualmente solicitado/executando/confirmado/falhou.
    params["_execucao_silenciosa"] = True
    params["origem"] = "terminal_panel"
    return {"intent": intent, "params": params}, texto


def executar_acao_painel_tipado(
    acao_id: str,
    payload: Mapping[str, Any] | None,
    *,
    executar_intencao: Callable[[dict[str, Any], str], Any],
    selecionar_saida_audio: Callable[[str], Any] | None = None,
) -> Any:
    if str(acao_id or "").strip() == "audio_output_select":
        referencia = str(dict(payload or {}).get("device_ref") or "").strip().casefold()
        if not re.fullmatch(r"[a-f0-9]{16}", referencia):
            return False
        if not callable(selecionar_saida_audio):
            return False
        return selecionar_saida_audio(referencia)
    comando = comando_tipado_acao_painel(acao_id, payload)
    if comando is None:
        return False
    resultado, texto_auditoria = comando
    return bool(executar_intencao(resultado, texto_auditoria))

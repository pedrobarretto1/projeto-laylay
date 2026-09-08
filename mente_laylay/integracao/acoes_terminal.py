"""Contrato compartilhado das ações rápidas do Terminal 3.

Este módulo descreve apenas apresentação e invocação canônica. Ele não
interpreta pedidos e não chama executores; todos os comandos continuam entrando
pela mesma porta de linguagem natural usada na conversa.
"""

from __future__ import annotations

from typing import Final


ACOES_RAPIDAS_TERMINAL: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "open_vscode",
        "label": "⌘  Abrir VS Code",
        "request": "abre o Visual Studio Code",
        "intent": "APP_OPEN",
    },
    {
        "id": "organize_desktop",
        "label": "▦  Organizar desktop",
        "request": "organiza o desktop automaticamente",
        "intent": "ORGANIZAR_DESKTOP",
    },
    {
        "id": "briefing",
        "label": "▤  Briefing",
        "request": "me passa o briefing de hoje",
        "intent": "BRIEFING_REPEAT",
    },
    {
        "id": "focus_mode",
        "label": "◎  Modo foco",
        "request": "",
        "intent": "",
    },
    {
        "id": "search",
        "label": "⌕  Pesquisar",
        "request": "",
        "intent": "SEARCH",
    },
    {
        "id": "activate_routine",
        "label": "◷  Ativar rotina",
        "request": "",
        "intent": "",
    },
)

# Controles de páginas dedicadas. Eles compartilham o mesmo contrato das ações
# rápidas, mas ficam fora da grade da Central Inteligente. O cliente só envia o
# pedido textual; interpretação, autorização, execução e confirmação continuam
# pertencendo à mente canônica.
ACOES_PAINEL_TERMINAL: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "media_previous",
        "label": "Faixa anterior",
        "request": "volta para a música anterior",
        "intent": "MEDIA_CONTROL",
    },
    {
        "id": "media_toggle",
        "label": "Pausar ou continuar",
        "request": "pausa a música",
        "intent": "MEDIA_CONTROL",
    },
    {
        "id": "media_next",
        "label": "Próxima faixa",
        "request": "vai para a próxima música",
        "intent": "MEDIA_CONTROL",
    },
    {
        "id": "queue_play",
        "label": "Tocar item da fila",
        "request": "",
        "intent": "MEDIA_CONTROL",
    },
    {
        "id": "playlist_play",
        "label": "Tocar playlist",
        "request": "",
        "intent": "PLAYLIST_PLAY",
    },
    {
        "id": "media_replay",
        "label": "Recomeçar faixa",
        "request": "reinicia essa música",
        "intent": "MEDIA_CONTROL",
    },
    {
        "id": "media_repeat",
        "label": "Alternar repetição",
        "request": "alterna a repetição da música",
        "intent": "MEDIA_CONTROL",
    },
    {
        "id": "playlist_shuffle",
        "label": "Playlist aleatória",
        "request": "",
        "intent": "PLAYLIST_PLAY",
    },
    {
        "id": "volume_set",
        "label": "Ajustar volume",
        "request": "",
        "intent": "VOLUME",
    },
    {
        "id": "audio_output_select",
        "label": "Trocar saída de áudio",
        "request": "",
        "intent": "",
    },
    {
        "id": "routine_cancel",
        "label": "Cancelar rotina",
        "request": "",
        "intent": "CANCELAR_AGENDAMENTO",
    },
    {
        "id": "iot_status",
        "label": "Atualizar dispositivo IoT",
        "request": "",
        "intent": "IOT_STATUS",
    },
    {
        "id": "iot_power",
        "label": "Ligar ou desligar dispositivo IoT",
        "request": "",
        "intent": "IOT_CONTROL",
    },
    {
        "id": "iot_brightness",
        "label": "Ajustar brilho da lâmpada IoT",
        "request": "",
        "intent": "IOT_CONTROL",
    },
)

ACOES_RAPIDAS_POR_ID: Final[dict[str, dict[str, str]]] = {
    item["id"]: dict(item) for item in ACOES_RAPIDAS_TERMINAL
}
IDS_ACOES_RAPIDAS: Final[frozenset[str]] = frozenset(ACOES_RAPIDAS_POR_ID)
ACOES_PAINEL_POR_ID: Final[dict[str, dict[str, str]]] = {
    item["id"]: dict(item) for item in ACOES_PAINEL_TERMINAL
}
IDS_ACOES_PAINEL: Final[frozenset[str]] = frozenset(ACOES_PAINEL_POR_ID)
ACOES_TERMINAL_POR_ID: Final[dict[str, dict[str, str]]] = {
    **ACOES_RAPIDAS_POR_ID,
    **ACOES_PAINEL_POR_ID,
}
IDS_ACOES_TERMINAL: Final[frozenset[str]] = frozenset(ACOES_TERMINAL_POR_ID)


def definicao_acao_rapida(acao_id: str) -> dict[str, str]:
    """Devolve uma cópia da definição pública, nunca o registro mutável."""
    return dict(ACOES_RAPIDAS_POR_ID.get(str(acao_id or "").strip()) or {})


def definicao_acao_terminal(acao_id: str) -> dict[str, str]:
    """Definição pública de qualquer ação visual reconhecida pela ponte."""
    return dict(ACOES_TERMINAL_POR_ID.get(str(acao_id or "").strip()) or {})

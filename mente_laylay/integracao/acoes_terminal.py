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

ACOES_RAPIDAS_POR_ID: Final[dict[str, dict[str, str]]] = {
    item["id"]: dict(item) for item in ACOES_RAPIDAS_TERMINAL
}
IDS_ACOES_RAPIDAS: Final[frozenset[str]] = frozenset(ACOES_RAPIDAS_POR_ID)


def definicao_acao_rapida(acao_id: str) -> dict[str, str]:
    """Devolve uma cópia da definição pública, nunca o registro mutável."""
    return dict(ACOES_RAPIDAS_POR_ID.get(str(acao_id or "").strip()) or {})

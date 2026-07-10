"""Formatacao visual e filtro de logs do terminal da Laylay."""

from __future__ import annotations

import re
from typing import Any

ANSI_RESET = "\033[0m"
ANSI_CYAN = "\033[96m"
ANSI_PINK = "\033[95m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_BLUE = "\033[94m"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def usar_cores(stdout: Any = None) -> bool:
    try:
        alvo = stdout
        if alvo is None:
            return False
        return bool(getattr(alvo, "isatty", lambda: False)())
    except Exception:
        return False


def face_para_emocao(emocao: str, nivel: int | None = None) -> str:
    emo = str(emocao or "calma").lower()
    face = "◕ᴗ◕"
    if emo in {"calma", "tranquila", "focada", "suave", "normal"}:
        face = "◕‿◕"
    elif emo in {"debochada", "alegre", "animada", "feliz", "divertida", "happy"}:
        face = "≧◡≦"
    elif emo in {"envergonhada", "encabulada", "timida", "tímida", "corada", "vergonhosa"}:
        face = "(｡>///<｡)"
    elif emo in {"irritada", "brava", "nervosa", "raivosa"}:
        face = "(╬ಠ益ಠ)"
    elif emo in {"triste", "decepcionada", "melancolica", "sad"}:
        face = "｡•́︿•̀｡"
    elif emo in {"surpresa", "surpreendida", "curiosa"}:
        face = "⊙o⊙"
    elif emo in {"sono", "cansada", "preguiçosa"}:
        face = "(´･_･`)"
    if nivel and nivel >= 3:
        face += "♡"
    elif nivel and nivel >= 2:
        face += "⋆"
    return face


def cor_para_emocao(emocao: str) -> str:
    emo = str(emocao or "calma").lower()
    if emo in {"calma", "tranquila", "focada", "suave", "normal"}:
        return ANSI_CYAN
    if emo in {"debochada", "alegre", "animada", "feliz", "divertida", "happy"}:
        return ANSI_PINK
    if emo in {"envergonhada", "encabulada", "timida", "tímida", "corada", "vergonhosa"}:
        return ANSI_YELLOW
    if emo in {"irritada", "brava", "nervosa", "raivosa"}:
        return ANSI_RED
    if emo in {"triste", "decepcionada", "melancolica", "sad"}:
        return ANSI_BLUE
    if emo in {"surpresa", "surpreendida", "curiosa"}:
        return ANSI_YELLOW
    return ANSI_GREEN


def formatar_mensagem_laylay(
    texto: str,
    *,
    emocao: str = "calma",
    nivel: int | None = None,
    fallback_fala: str = "Estou aqui, Pedro. Me fala o próximo passo.",
    stdout: Any = None,
) -> str:
    texto_limpo = str(texto or "").strip() or fallback_fala
    face = face_para_emocao(emocao, nivel)
    cores = usar_cores(stdout)
    color = cor_para_emocao(emocao) if cores else ""
    reset = ANSI_RESET if cores else ""
    return f"{color}╭─ {face} Laylay: {texto_limpo}{reset}"


def should_log_message(text: str, *, log_mode: str = "limpo", log_verbose: bool = False) -> bool:
    mensagem = str(text or "")
    mensagem_sem_ansi = ANSI_RE.sub("", mensagem)
    if not mensagem.strip():
        return False
    lower = mensagem_sem_ansi.lower()

    if log_verbose or log_mode == "debug":
        return True

    if log_mode in {"0", "false", "none", "quiet"}:
        return False

    if "laylay:" in lower:
        return True

    if lower.startswith(("╭─", "💬 você:", "❌", "⚠️", "🛑", "╔", "║", "╚", "> ")):
        return True

    if "laylay pronta para conversar" in lower or "modo chat ativado" in lower or "chat ligado" in lower or "conversa aberta" in lower:
        return True

    if any(token in lower for token in [
        "[debug", "[ctx", "[ws]", "[chrome]", "[yt-", "[memória", "[visão", "[auto", "[rotina", "[feedback",
        "[pc b]", "[netflix]", "[video]", "[thread crash]", "[verificar_programas]", "[playlist]",
        "[disk]", "[gmail]", "[saúde]", "[agenda]", "[porteiro]", "debug:", "success_playback",
    ]):
        return False

    if any(token in lower for token in ["erro", "falha", "timeout", "não consegui", "nao consegui", "ação não autorizada", "ação nao autorizada"]):
        return True

    if log_mode in {"limpo", "essencial"}:
        if any(token in lower for token in ["[ia] gerando resposta", "[roteador", "[janela:", "appopener carregado", "websocket server", "inicializando", "carregando o novo ouvido", "ouvido whisper carregado"]):
            return True
        return False

    return True

"""Formatacao visual e filtro de logs do terminal da Laylay."""

from __future__ import annotations

from contextlib import nullcontext
import os
import re
import sys
import threading
import time
from typing import Any, Callable

ANSI_RESET = "\033[0m"
ANSI_CYAN = "\033[96m"
ANSI_PINK = "\033[95m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_BLUE = "\033[94m"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def ler_linha_terminal_interrompivel(
    prompt: str,
    *,
    stdin: Any,
    deve_continuar: Callable[[], bool],
    input_fn: Callable[[str], str] = input,
    raw_print: Callable[..., Any] = print,
    sleep_fn: Callable[[float], Any] = time.sleep,
    msvcrt_mod: Any = None,
) -> str | None:
    """Lê o console Windows sem prender o serviço durante o encerramento."""
    if not deve_continuar():
        return None
    if os.name != "nt" or stdin is not sys.stdin:
        return str(input_fn(prompt) or "")
    try:
        msvcrt = msvcrt_mod
        if msvcrt is None:
            import msvcrt as msvcrt_real

            msvcrt = msvcrt_real
    except Exception:
        return str(input_fn(prompt) or "")

    raw_print(prompt, end="", flush=True)
    caracteres: list[str] = []
    while deve_continuar():
        if not bool(msvcrt.kbhit()):
            sleep_fn(0.04)
            continue
        caractere = str(msvcrt.getwch() or "")
        if caractere in {"\r", "\n"}:
            raw_print("")
            return "".join(caracteres)
        if caractere == "\x03":
            raise KeyboardInterrupt
        if caractere == "\x1a":
            raw_print("")
            return ""
        if caractere in {"\x00", "\xe0"}:
            if bool(msvcrt.kbhit()):
                msvcrt.getwch()
            continue
        if caractere == "\b":
            if caracteres:
                caracteres.pop()
                raw_print("\b \b", end="", flush=True)
            continue
        if caractere.isprintable() or caractere == "\t":
            caracteres.append(caractere)
            raw_print(caractere, end="", flush=True)
    if caracteres:
        raw_print("")
    return None


def escutar_texto_terminal(
    *,
    estado_ativo: Callable[[], bool],
    processar_texto: Callable[[str], Any],
    stdin: Any,
    input_fn: Callable[[str], str] = input,
    raw_print: Callable[..., Any] = print,
    print_lock: Any = None,
    sleep_fn: Callable[[float], Any] = time.sleep,
    log: Callable[[str], Any] = print,
    deve_continuar: Callable[[], bool] | None = None,
    entrada_permitida: Callable[[], bool] | None = None,
    ler_linha_fn: Callable[..., str | None] | None = None,
) -> None:
    """Lê o chat textual e entrega cada entrada ao mesmo cérebro da Laylay."""
    if stdin is None:
        return
    try:
        if not stdin.isatty():
            return
    except Exception:
        return

    continuar = deve_continuar if callable(deve_continuar) else (lambda: True)
    exibir_cabecalho = True
    while continuar():
        try:
            if not estado_ativo() or (
                callable(entrada_permitida) and not bool(entrada_permitida())
            ):
                sleep_fn(0.25)
                continue
            # O lock protege somente a escrita do cabeçalho. Mantê-lo durante
            # toda a espera por teclado bloqueava a mente inteira quando o
            # usuário conversava pelo Terminal 2 e nunca pressionava Enter no
            # console antigo.
            if exibir_cabecalho:
                gerenciador = print_lock if print_lock is not None else nullcontext()
                with gerenciador:
                    raw_print("")
                    raw_print("💬 Você:")
            leitor = ler_linha_fn or ler_linha_terminal_interrompivel
            texto_bruto = leitor(
                "> ",
                stdin=stdin,
                deve_continuar=lambda: bool(
                    continuar()
                    and estado_ativo()
                    and (
                        not callable(entrada_permitida)
                        or bool(entrada_permitida())
                    )
                ),
                input_fn=input_fn,
                raw_print=raw_print,
                sleep_fn=sleep_fn,
            )
            if texto_bruto is None:
                continue
            texto = str(texto_bruto or "").strip()
            if texto:
                exibir_cabecalho = True
                try:
                    processamento = processar_texto(texto)
                    if isinstance(processamento, threading.Thread):
                        processamento.join(timeout=120.0)
                    elif callable(getattr(processamento, "result", None)):
                        processamento.result(timeout=120.0)
                    # A voz trabalha em fila e pode começar logo após o cérebro
                    # terminar. Esta pequena janela impede que o novo prompt
                    # seja desenhado em cima da resposta da Laylay.
                    sleep_fn(0.25)
                    while (
                        continuar()
                        and callable(entrada_permitida)
                        and not bool(entrada_permitida())
                    ):
                        sleep_fn(0.1)
                except Exception as erro:
                    log(f"⚠️ [CHAT] Falha ao processar texto digitado: {erro}")
            else:
                # Enter vazio apenas abre uma nova linha de entrada. Repetir o
                # cabeçalho faria o terminal exibir vários blocos idênticos de
                # ``💬 Você:`` sem que houvesse um novo turno de verdade.
                exibir_cabecalho = False
        except (EOFError, KeyboardInterrupt):
            sleep_fn(0.5)
        except Exception as erro:
            log(f"⚠️ [CHAT] Erro no leitor de texto do terminal: {erro}")
            sleep_fn(0.5)


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
    fallback_fala: str = "Não consegui encaixar isso direito. Me fala de outro jeito?",
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
        if any(token in lower for token in [
            "[ia] gerando resposta", "[roteador", "[janela:", "[iot:inicio]",
            "[iot:seguranca]", "[iot:resultado]", "[ouvido]", "[ouvido:",
            "[você disse]", "[voce disse]", "appopener carregado", "websocket server",
            "[voz pessoal]", "[rede associativa]", "[clipboard:", "[terminal 2",
            "inicializando", "carregando o novo ouvido", "ouvido whisper carregado",
        ]):
            return True
        return False

    return True


def criar_print_filtrado(
    *,
    should_log: Callable[[str], bool],
    raw_print: Callable[..., Any],
    print_lock: Any,
) -> Callable[..., Any]:
    """Cria o print global filtrado sem espalhar a política de terminal."""

    def print_filtrado(*args: Any, **kwargs: Any) -> None:
        if not args:
            return
        if should_log(" ".join(str(arg) for arg in args)):
            with print_lock:
                raw_print(*args, **kwargs)

    return print_filtrado


def tratar_excecao_thread(
    args: Any,
    *,
    log: Callable[..., Any],
    traceback_mod: Any,
) -> None:
    """Registra falha de thread sem derrubar os demais serviços."""
    log(f"❌ [THREAD CRASH] {args.exc_type.__name__} em {args.thread.name}: {args.exc_value}")
    traceback_mod.print_exception(args.exc_type, args.exc_value, args.exc_traceback)
    log("🔄 Laylay continua rodando apesar do erro...")

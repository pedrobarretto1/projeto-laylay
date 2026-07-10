"""Execucao de controle de midia da Laylay.

Este modulo nao guarda estado proprio. Ele recebe o contexto vivo do roteador
para continuar funcionando como parte da mesma mente.
"""

from __future__ import annotations

import ctypes
import time
from typing import Any, Callable, Dict

from mente_laylay.personalidade.falas_variadas import (
    escolher as _escolher_fala_variada,
    fala_de_confirmacao as _fala_de_confirmacao_variada,
)


VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3


def _get(ctx: Dict[str, Any], nome: str, default=None):
    return ctx.get(nome, default)


def executar_controle_midia_nativo(
    command: str,
    *,
    ctypes_module: Any = ctypes,
    sleep_cb: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] = print,
) -> bool:
    """Envia teclas globais de mídia preservando a semântica legada."""
    cmd = str(command or "").strip().lower()
    try:
        if cmd == "pause_play":
            log("🎵 [MIDIA:NATIVO] tecla play/pause")
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
            return True
        if cmd == "next":
            log("🎵 [MIDIA:NATIVO] tecla next")
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)
            return True
        if cmd == "prev":
            log("🎵 [MIDIA:NATIVO] tecla previous x2")
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            sleep_cb(0.18)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            return True
        if cmd == "replay":
            log("🎵 [MIDIA:NATIVO] replay via previous")
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            return True
    except Exception as erro:
        log(f"⚠️ [MIDIA NATIVA] falha ao executar '{cmd}': {erro}")
    return False


def executar_media_control(
    params: Dict[str, Any],
    texto_original: str,
    destino_val: str,
    ctx: Dict[str, Any],
    *,
    marcar_resultado: Callable[[str, bool | None], None],
    falar_por_status: Callable[..., None],
    ctx_fala: Callable[[], Dict[str, Any]],
) -> bool:
    """Executa MEDIA_CONTROL com validacao, logs e fala contextual."""
    falar = _get(ctx, "falar_com_lipsync")
    enviar_chrome = _get(ctx, "enviar_comando_chrome")
    solicitar_aba = _get(ctx, "solicitar_aba_ativa")
    ajustar_volume = _get(ctx, "ajustar_volume_sistema")
    _enviar_pc_b = _get(ctx, "_enviar_pc_b")
    executar_controle_midia_nativo = _get(ctx, "_executar_controle_midia_nativo")

    acao = str(params.get("acao") or params.get("command") or "").strip().lower()
    platform = str(params.get("platform") or params.get("site") or "").strip().lower()
    nivel_bruto = params.get("nivel_volume")
    playlist_state = _get(ctx, "playlist_state", {}) or {}
    playlist_ativa = bool(str((playlist_state or {}).get("name") or "").strip())
    playlist_next = _get(ctx, "_playlist_avancar_proxima")
    playlist_prev = _get(ctx, "_playlist_voltar_anterior")

    def _log_midia(etapa: str, msg: str) -> None:
        try:
            print(f"🎵 [MIDIA:{str(etapa or '').upper()}] {msg}")
        except Exception:
            pass

    def _aba_atual_midia() -> dict:
        try:
            return solicitar_aba() if callable(solicitar_aba) else {}
        except Exception as e:
            _log_midia("ABA", f"falha ao consultar aba: {e}")
            return {}

    def _preferir_chrome_para_midia() -> bool:
        info_aba = _aba_atual_midia()
        url = str(info_aba.get("url") or "").lower() if isinstance(info_aba, dict) else ""
        titulo = str(info_aba.get("title") or "").lower() if isinstance(info_aba, dict) else ""
        preferir = bool(callable(enviar_chrome) and ("youtube." in url or "youtu.be" in url or "youtube" in titulo))
        _log_midia("ROTA", f"acao={acao} platform={platform or '-'} playlist={playlist_ativa} url='{url[:80]}' preferir_chrome={preferir}")
        return preferir

    def _executar_cmd_midia(cmd_exec: str) -> bool:
        _log_midia("ENVIO", f"cmd={cmd_exec} destino={destino_val or 'local'} playlist={playlist_ativa}")
        if destino_val == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "youtube_control", "command": cmd_exec})
            return True
        if destino_val == "ambos":
            ok_local = False
            if _preferir_chrome_para_midia() and callable(enviar_chrome):
                enviar_chrome("youtube_control", {"command": cmd_exec})
                ok_local = True
            elif callable(executar_controle_midia_nativo):
                native_cmd = "pause_play" if cmd_exec in {"pause", "play"} else cmd_exec
                ok_local = bool(executar_controle_midia_nativo(native_cmd))
            elif callable(enviar_chrome):
                enviar_chrome("youtube_control", {"command": cmd_exec})
                ok_local = True
            if callable(_enviar_pc_b):
                _enviar_pc_b({"action": "youtube_control", "command": cmd_exec})
            return ok_local
        if playlist_ativa and callable(enviar_chrome):
            enviar_chrome("youtube_control", {"command": cmd_exec})
            return True
        if _preferir_chrome_para_midia() and callable(enviar_chrome):
            enviar_chrome("youtube_control", {"command": cmd_exec})
            return True
        if callable(executar_controle_midia_nativo):
            native_cmd = "pause_play" if cmd_exec in {"pause", "play"} else cmd_exec
            return bool(executar_controle_midia_nativo(native_cmd))
        if callable(enviar_chrome):
            enviar_chrome("youtube_control", {"command": cmd_exec})
            return True
        return False

    _log_midia("ENTRADA", f"acao={acao or '-'} platform={platform or '-'} params={params}")
    cmd = ""
    if acao in {"resume", "retomar", "retoma", "continuar", "continua", "despausa", "despausar"}:
        cmd = "play"
    elif acao in {"pause", "pausa"}:
        cmd = "pause"
    elif acao in {"pause_play", "play_pause", "toggle", "tocar"}:
        cmd = "pause_play"
    elif acao in {"play"}:
        cmd = "play"
    elif acao in {"next", "proxima", "próxima"}:
        cmd = "next"
    elif acao in {"prev", "previous", "anterior"}:
        cmd = "prev"
    elif acao in {"replay", "voltar", "reiniciar"}:
        cmd = "replay"

    if nivel_bruto not in (None, ""):
        try:
            nivel = int(float(str(nivel_bruto).replace(",", ".")))
        except Exception:
            nivel = None
        if nivel is not None:
            nivel = max(0, min(100, nivel))
            ok_volume = False
            if destino_val == "pc_b" and callable(_enviar_pc_b):
                _enviar_pc_b({"action": "set_volume", "level": nivel})
                ok_volume = True
            elif callable(ajustar_volume):
                ajustar_volume(nivel)
                ok_volume = True
            else:
                if callable(falar):
                    falar(_escolher_fala_variada([
                        "Não consegui mexer no volume agora.",
                        "O volume escapou de mim desta vez.",
                        "Tentei ajustar o volume, mas não tive acesso ao controle.",
                    ]), "calma", 1)
                return False
            marcar_resultado("volume_ajustado" if ok_volume else "falha_execucao", ok_volume)
            falar_por_status(
                "volume_ajustado" if ok_volume else "falha_execucao",
                f"Volume em {nivel}%." if ok_volume else "Tentei ajustar o volume, mas o controle não respondeu.",
                alvo="volume",
            )
            return bool(ok_volume)

    if not cmd:
        if callable(falar):
            falar(_escolher_fala_variada(["Não entendi o controle de mídia. Fala de novo.", "Repete o comando de mídia.", "Esse controle de mídia escapou de mim."]), "calma", 1)
        return True

    if playlist_ativa and cmd == "next" and callable(playlist_next):
        _log_midia("PLAYLIST", "tentando avancar pela playlist interna")
        ok = bool(playlist_next())
        _log_midia("RESULTADO", f"playlist_next ok={ok}")
        if callable(falar):
            falar(
                _fala_de_confirmacao_variada(
                    "next",
                    fallback="Trocando a música. Sem drama." if ok else "Tentei puxar a próxima da playlist, mas ela não foi.",
                    contexto=ctx_fala(),
                    texto_usuario=texto_original,
                ),
                "debochada",
                2,
            )
        marcar_resultado("midia_next_playlist" if ok else "falha_execucao", ok)
        return bool(ok)

    if playlist_ativa and cmd == "prev" and callable(playlist_prev):
        _log_midia("PLAYLIST", "tentando voltar pela playlist interna")
        ok = bool(playlist_prev())
        _log_midia("RESULTADO", f"playlist_prev ok={ok}")
        if callable(falar):
            falar(
                _fala_de_confirmacao_variada(
                    "prev",
                    fallback="Voltando uma faixa." if ok else "Tentei voltar a playlist, mas ela não cedeu.",
                    contexto=ctx_fala(),
                    texto_usuario=texto_original,
                ),
                "debochada",
                2,
            )
        marcar_resultado("midia_prev_playlist" if ok else "falha_execucao", ok)
        return bool(ok)

    ok_execucao = _executar_cmd_midia(cmd)
    _log_midia("RESULTADO", f"cmd={cmd} ok_envio={ok_execucao}")
    if callable(falar):
        if cmd in {"pause", "play", "pause_play"}:
            chave_midia = "play" if cmd == "play" else ("pause" if cmd == "pause" else "pause")
        else:
            chave_midia = "prev" if cmd == "prev" else ("replay" if cmd == "replay" else cmd)
        falar(
            _fala_de_confirmacao_variada(
                chave_midia,
                fallback="Feito." if ok_execucao else "Tentei mexer na mídia, mas não consegui confirmar o caminho.",
                contexto=ctx_fala(),
                texto_usuario=texto_original,
            ),
            "debochada",
            2,
        )
    marcar_resultado(f"midia_{cmd}" if ok_execucao else "falha_execucao", ok_execucao)
    return bool(ok_execucao)

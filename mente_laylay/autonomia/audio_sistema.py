"""Efeitos locais de audio usados pela mente da Laylay.

Este modulo apenas executa volume, interrupcao e ducking. Interpretacao,
contexto e resposta continuam pertencendo ao orquestrador central.
"""

from __future__ import annotations

from typing import Any, Callable


_volumes_originais_apps: dict[int, float] = {}
_APPS_DUCKING = {
    "chrome.exe",
    "opera.exe",
    "spotify.exe",
    "msedge.exe",
    "brave.exe",
    "firefox.exe",
}


def ajustar_volume_sistema(nivel_percentual, *, log: Callable[[str], None] = print) -> None:
    try:
        from pycaw.pycaw import AudioUtilities

        devices = AudioUtilities.GetSpeakers()
        if devices is None:
            return
        scalar = max(0.0, min(1.0, float(nivel_percentual) / 100.0))
        devices.EndpointVolume.SetMasterVolumeLevelScalar(scalar, None)
    except Exception as erro:
        log(f"Erro ao ajustar volume: {erro}")


def ajustar_volume_sistema_relativo(delta_percentual, *, log: Callable[[str], None] = print) -> None:
    try:
        from pycaw.pycaw import AudioUtilities

        devices = AudioUtilities.GetSpeakers()
        if devices is None:
            return
        volume = devices.EndpointVolume
        atual = volume.GetMasterVolumeLevelScalar()
        novo = max(0.0, min(1.0, atual + (float(delta_percentual) / 100.0)))
        volume.SetMasterVolumeLevelScalar(novo, None)
    except Exception as erro:
        log(f"Erro ao ajustar volume relativo: {erro}")


def interromper_audio_ativo(*, sounddevice_module: Any = None, log: Callable[[str], None] = print) -> None:
    try:
        if sounddevice_module is None:
            import sounddevice as sounddevice_module
        stream = sounddevice_module.get_stream()
        if stream and stream.active:
            sounddevice_module.stop()
            log("[AUDIO] Fala da Laylay interrompida.")
    except Exception:
        pass


def ducking_volume(ativar: bool = True, *, log: Callable[[str], None] | None = None) -> None:
    try:
        from pycaw.pycaw import AudioUtilities

        for session in AudioUtilities.GetAllSessions():
            process = session.Process
            if not process or process.name().lower() not in _APPS_DUCKING:
                continue
            try:
                controle = session.SimpleAudioVolume
                pid = process.pid
                if ativar:
                    _volumes_originais_apps.setdefault(pid, controle.GetMasterVolume())
                    controle.SetMasterVolume(0.15, None)
                else:
                    controle.SetMasterVolume(_volumes_originais_apps.pop(pid, 1.0), None)
            except Exception:
                continue
    except Exception as erro:
        if callable(log):
            log(f"[AUDIO] Ducking indisponivel: {erro}")

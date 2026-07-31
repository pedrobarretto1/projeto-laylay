"""Efeitos locais de audio usados pela mente da Laylay.

Este modulo apenas executa volume, interrupcao e ducking. Interpretacao,
contexto e resposta continuam pertencendo ao orquestrador central.
"""

from __future__ import annotations

import threading
from typing import Callable


# Guarde o controle da sessao, e nao apenas o PID. Navegadores e players podem
# possuir varias sessoes para o mesmo processo; usar o PID fazia a segunda
# sessao ser restaurada para 100% por engano.
_sessoes_ducking: list[tuple[object, float]] = []
_ducking_lock = threading.RLock()
_ducking_profundidade = 0
_APPS_DUCKING = {
    "chrome.exe",
    "opera.exe",
    "spotify.exe",
    "msedge.exe",
    "brave.exe",
    "firefox.exe",
}


def listar_processos_com_audio_ativo(*, log: Callable[[str], None] | None = None) -> set[str]:
    """Retorna executáveis com sessão de áudio ativa e audível.

    A leitura é somente perceptiva: não altera volume nem estado das sessões.
    Falhas do COM/Pycaw degradam para um conjunto vazio para que a organização
    de janelas continue usando foco e recência.
    """
    ativos: set[str] = set()
    try:
        from pycaw.pycaw import AudioUtilities

        for sessao in AudioUtilities.GetAllSessions() or []:
            try:
                processo = getattr(sessao, "Process", None)
                if processo is None:
                    continue
                nome = str(processo.name() or "").strip().casefold()
                if not nome:
                    continue

                estado = getattr(sessao, "State", None)
                if callable(estado):
                    estado = estado()
                if estado is None:
                    controle_sessao = getattr(sessao, "_ctl", None)
                    get_state = getattr(controle_sessao, "GetState", None)
                    estado = get_state() if callable(get_state) else None
                estado_ativo = (
                    estado == 1
                    or str(estado or "").strip().casefold() in {
                        "active", "audio_session_state_active", "audiosessionstateactive",
                    }
                )
                if not estado_ativo:
                    continue

                volume = getattr(sessao, "SimpleAudioVolume", None)
                if volume is not None:
                    get_mute = getattr(volume, "GetMute", None)
                    get_volume = getattr(volume, "GetMasterVolume", None)
                    if callable(get_mute) and bool(get_mute()):
                        continue
                    if callable(get_volume) and float(get_volume()) <= 0.001:
                        continue
                ativos.add(nome)
            except Exception:
                continue
    except Exception as erro:
        if callable(log):
            log(f"[AUDIO] Leitura de processos ativos indisponível: {erro}")
    return ativos


def obter_volume_sistema(*, log: Callable[[str], None] = print) -> int | None:
    """Lê o volume mestre para confirmação e reversão de ações autônomas."""
    try:
        from pycaw.pycaw import AudioUtilities

        devices = AudioUtilities.GetSpeakers()
        if devices is None:
            return None
        valor = float(devices.EndpointVolume.GetMasterVolumeLevelScalar())
        return max(0, min(100, round(valor * 100)))
    except Exception as erro:
        log(f"Erro ao consultar volume: {erro}")
        return None


def ajustar_volume_sistema(nivel_percentual, *, log: Callable[[str], None] = print) -> bool:
    try:
        from pycaw.pycaw import AudioUtilities

        devices = AudioUtilities.GetSpeakers()
        if devices is None:
            return False
        scalar = max(0.0, min(1.0, float(nivel_percentual) / 100.0))
        devices.EndpointVolume.SetMasterVolumeLevelScalar(scalar, None)
        return True
    except Exception as erro:
        log(f"Erro ao ajustar volume: {erro}")
        return False


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


def definir_mudo_sistema(ativar: bool, *, log: Callable[[str], None] = print) -> bool:
    try:
        from pycaw.pycaw import AudioUtilities

        devices = AudioUtilities.GetSpeakers()
        if devices is None:
            return False
        devices.EndpointVolume.SetMute(bool(ativar), None)
        return bool(devices.EndpointVolume.GetMute()) is bool(ativar)
    except Exception as erro:
        log(f"Erro ao alterar mudo do sistema: {erro}")
        return False


def ducking_volume(ativar: bool = True, *, log: Callable[[str], None] | None = None) -> None:
    """Abaixa temporariamente outros apps e restaura exatamente o estado anterior.

    Chamadas aninhadas sao contabilizadas. Uma restauracao sem ativacao previa
    nao altera volume algum, e aplicativos que ja estavam abaixo de 15% nunca
    sao aumentados durante o ducking.
    """
    global _ducking_profundidade

    try:
        from pycaw.pycaw import AudioUtilities

        with _ducking_lock:
            if ativar:
                if _ducking_profundidade > 0:
                    _ducking_profundidade += 1
                    return

                sessoes_ajustadas: list[tuple[object, float]] = []
                for session in AudioUtilities.GetAllSessions():
                    try:
                        # O processo pode encerrar entre a enumeracao e a leitura.
                        process = session.Process
                        if not process or process.name().lower() not in _APPS_DUCKING:
                            continue
                        controle = session.SimpleAudioVolume
                        original = float(controle.GetMasterVolume())
                        # Ducking deve apenas abaixar. Elevar uma sessao que ja
                        # estava baixa tambem era percebido como audio estourado.
                        controle.SetMasterVolume(min(original, 0.15), None)
                        sessoes_ajustadas.append((controle, original))
                    except Exception:
                        continue
                _sessoes_ducking[:] = sessoes_ajustadas
                _ducking_profundidade = 1
                return

            if _ducking_profundidade <= 0:
                return
            _ducking_profundidade -= 1
            if _ducking_profundidade > 0:
                return

            sessoes_originais = list(_sessoes_ducking)
            _sessoes_ducking.clear()
            for controle, original in sessoes_originais:
                try:
                    controle.SetMasterVolume(original, None)
                except Exception:
                    # A sessao pode ter sido encerrada enquanto a Laylay falava.
                    continue
    except Exception as erro:
        if callable(log):
            log(f"[AUDIO] Ducking indisponivel: {erro}")

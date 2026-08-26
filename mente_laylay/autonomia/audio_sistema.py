"""Efeitos locais de audio usados pela mente da Laylay.

Este modulo apenas executa volume, interrupcao e ducking. Interpretacao,
contexto e resposta continuam pertencendo ao orquestrador central.
"""

from __future__ import annotations

import threading
import time
from typing import Callable


# Guarde o controle da sessao, e nao apenas o PID. Navegadores e players podem
# possuir varias sessoes para o mesmo processo; usar o PID fazia a segunda
# sessao ser restaurada para 100% por engano.
_sessoes_ducking: list[tuple[object, float]] = []
_ducking_lock = threading.RLock()
_ducking_profundidade = 0
_ducking_geracao = 0
_sleep = time.sleep
_DUCKING_ALVO = 0.15
_DUCKING_RESTAURACAO_DURACAO_S = 0.72
_DUCKING_RESTAURACAO_PASSOS = 12
_DUCKING_ATRASO_RETORNO_S = 0.06
_DUCKING_TOLERANCIA_MANUAL = 0.04
_APPS_DUCKING = {
    "chrome.exe",
    "opera.exe",
    "spotify.exe",
    "msedge.exe",
    "brave.exe",
    "firefox.exe",
}


def _curva_suave(progresso: float) -> float:
    """Smoothstep: começa e termina sem um degrau perceptível."""
    valor = max(0.0, min(1.0, float(progresso)))
    return valor * valor * (3.0 - (2.0 * valor))


def _restaurar_sessoes_suavemente(
    sessoes: list[tuple[object, float]],
    *,
    geracao: int,
) -> None:
    """Restaura volumes sem sobrescrever uma decisão manual do usuário."""
    ativos: list[dict[str, object | float]] = []
    for controle, original in sessoes:
        try:
            atual = float(controle.GetMasterVolume())
        except Exception:
            continue
        # Se o volume da sessão mudou bastante enquanto a Laylay falava, a
        # alteração mais recente pertence ao usuário/app e tem precedência.
        esperado_ducking = min(float(original), _DUCKING_ALVO)
        if abs(atual - esperado_ducking) > _DUCKING_TOLERANCIA_MANUAL:
            continue
        if abs(original - atual) <= 0.001:
            continue
        ativos.append({
            "controle": controle,
            "inicio": atual,
            "original": float(original),
            "ultimo_definido": atual,
        })

    if not ativos:
        with _ducking_lock:
            if geracao == _ducking_geracao and _ducking_profundidade == 0:
                _sessoes_ducking.clear()
        return

    if _DUCKING_ATRASO_RETORNO_S > 0:
        _sleep(_DUCKING_ATRASO_RETORNO_S)

    passos = max(1, int(_DUCKING_RESTAURACAO_PASSOS))
    intervalo = max(0.0, float(_DUCKING_RESTAURACAO_DURACAO_S)) / passos
    for passo in range(1, passos + 1):
        with _ducking_lock:
            if geracao != _ducking_geracao or _ducking_profundidade > 0:
                return
            suavizado = _curva_suave(passo / passos)
            restantes: list[dict[str, object | float]] = []
            for item in ativos:
                controle = item["controle"]
                try:
                    atual = float(controle.GetMasterVolume())  # type: ignore[attr-defined]
                    ultimo = float(item["ultimo_definido"])
                    if abs(atual - ultimo) > _DUCKING_TOLERANCIA_MANUAL:
                        # Mudança manual durante a própria rampa: pare apenas
                        # esta sessão; as demais continuam restaurando.
                        continue
                    inicio = float(item["inicio"])
                    original = float(item["original"])
                    novo = original if passo == passos else inicio + ((original - inicio) * suavizado)
                    controle.SetMasterVolume(novo, None)  # type: ignore[attr-defined]
                    item["ultimo_definido"] = novo
                    restantes.append(item)
                except Exception:
                    # A sessão pode desaparecer enquanto a voz termina.
                    continue
            ativos = restantes
            if not ativos:
                break
        if passo < passos and intervalo > 0:
            _sleep(intervalo)

    with _ducking_lock:
        if geracao == _ducking_geracao and _ducking_profundidade == 0:
            _sessoes_ducking.clear()


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
    global _ducking_profundidade, _ducking_geracao

    try:
        from pycaw.pycaw import AudioUtilities

        with _ducking_lock:
            if ativar:
                if _ducking_profundidade > 0:
                    _ducking_profundidade += 1
                    return

                # Invalida imediatamente uma restauração que ainda esteja em
                # curso. A nova fala volta a abaixar o áudio antes de prosseguir.
                _ducking_geracao += 1
                if _sessoes_ducking:
                    for controle, _original in list(_sessoes_ducking):
                        try:
                            atual = float(controle.GetMasterVolume())
                            controle.SetMasterVolume(min(atual, _DUCKING_ALVO), None)
                        except Exception:
                            continue
                    _ducking_profundidade = 1
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
                        controle.SetMasterVolume(min(original, _DUCKING_ALVO), None)
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
            _ducking_geracao += 1
            geracao_restauracao = _ducking_geracao
        _restaurar_sessoes_suavemente(
            sessoes_originais,
            geracao=geracao_restauracao,
        )
    except Exception as erro:
        if callable(log):
            log(f"[AUDIO] Ducking indisponivel: {erro}")

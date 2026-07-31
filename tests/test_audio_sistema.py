import sys
import types

import pytest

from mente_laylay.autonomia import audio_sistema


class ControleFalso:
    def __init__(self, volume, *, mudo=False):
        self.volume = float(volume)
        self.mudo = bool(mudo)
        self.historico = []

    def GetMasterVolume(self):
        return self.volume

    def SetMasterVolume(self, volume, _contexto):
        self.volume = float(volume)
        self.historico.append(self.volume)

    def GetMute(self):
        return self.mudo


class ProcessoFalso:
    def __init__(self, nome, pid):
        self._nome = nome
        self.pid = pid

    def name(self):
        return self._nome


class SessaoFalsa:
    def __init__(self, nome, pid, volume, *, estado=None, mudo=False):
        self.Process = ProcessoFalso(nome, pid) if nome else None
        self.SimpleAudioVolume = ControleFalso(volume, mudo=mudo)
        if estado is not None:
            self.State = estado


@pytest.fixture(autouse=True)
def limpar_estado_ducking(monkeypatch):
    audio_sistema._sessoes_ducking.clear()
    monkeypatch.setattr(audio_sistema, "_ducking_profundidade", 0)
    yield
    audio_sistema._sessoes_ducking.clear()
    audio_sistema._ducking_profundidade = 0


def instalar_pycaw_falso(monkeypatch, sessoes):
    class AudioUtilitiesFalso:
        @staticmethod
        def GetAllSessions():
            return sessoes

    pacote = types.ModuleType("pycaw")
    modulo = types.ModuleType("pycaw.pycaw")
    modulo.AudioUtilities = AudioUtilitiesFalso
    pacote.pycaw = modulo
    monkeypatch.setitem(sys.modules, "pycaw", pacote)
    monkeypatch.setitem(sys.modules, "pycaw.pycaw", modulo)


def test_ducking_restaura_multiplas_sessoes_do_mesmo_pid(monkeypatch):
    primeira = SessaoFalsa("chrome.exe", 42, 0.62)
    segunda = SessaoFalsa("chrome.exe", 42, 0.37)
    instalar_pycaw_falso(monkeypatch, [primeira, segunda])

    audio_sistema.ducking_volume(True)
    assert primeira.SimpleAudioVolume.volume == pytest.approx(0.15)
    assert segunda.SimpleAudioVolume.volume == pytest.approx(0.15)

    audio_sistema.ducking_volume(False)
    assert primeira.SimpleAudioVolume.volume == pytest.approx(0.62)
    assert segunda.SimpleAudioVolume.volume == pytest.approx(0.37)


def test_ducking_nunca_aumenta_sessao_que_ja_estava_baixa(monkeypatch):
    sessao = SessaoFalsa("spotify.exe", 7, 0.06)
    instalar_pycaw_falso(monkeypatch, [sessao])

    audio_sistema.ducking_volume(True)
    assert sessao.SimpleAudioVolume.volume == pytest.approx(0.06)
    audio_sistema.ducking_volume(False)
    assert sessao.SimpleAudioVolume.volume == pytest.approx(0.06)


def test_ducking_aninhado_so_restaura_na_ultima_saida(monkeypatch):
    sessao = SessaoFalsa("firefox.exe", 9, 0.8)
    instalar_pycaw_falso(monkeypatch, [sessao])

    audio_sistema.ducking_volume(True)
    audio_sistema.ducking_volume(True)
    audio_sistema.ducking_volume(False)
    assert sessao.SimpleAudioVolume.volume == pytest.approx(0.15)

    audio_sistema.ducking_volume(False)
    assert sessao.SimpleAudioVolume.volume == pytest.approx(0.8)


def test_restauracao_sem_ativacao_nao_mexe_no_volume(monkeypatch):
    sessao = SessaoFalsa("chrome.exe", 11, 0.44)
    instalar_pycaw_falso(monkeypatch, [sessao])

    audio_sistema.ducking_volume(False)

    assert sessao.SimpleAudioVolume.volume == pytest.approx(0.44)
    assert sessao.SimpleAudioVolume.historico == []


def test_lista_somente_processos_com_audio_ativo_e_audivel(monkeypatch):
    chrome = SessaoFalsa("chrome.exe", 1, 0.7, estado=1)
    spotify_pausado = SessaoFalsa("spotify.exe", 2, 0.8, estado=0)
    discord_mudo = SessaoFalsa("discord.exe", 3, 0.8, estado=1, mudo=True)
    edge_sem_volume = SessaoFalsa("msedge.exe", 4, 0.0, estado=1)
    instalar_pycaw_falso(
        monkeypatch,
        [chrome, spotify_pausado, discord_mudo, edge_sem_volume],
    )

    assert audio_sistema.listar_processos_com_audio_ativo() == {"chrome.exe"}

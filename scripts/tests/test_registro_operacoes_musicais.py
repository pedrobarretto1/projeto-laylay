from __future__ import annotations

import time

import pytest

from mente_laylay.integracao.registro_operacoes_musicais import (
    registrar_operacoes_musicais,
)
from mente_laylay.memoria_mental.operacoes_musicais_runtime import (
    criar_operacoes_musicais_runtime,
)


class _PlaylistsUsuario:
    def __init__(self):
        self.chamadas = []
        self.playlist_state = {"name": "rock", "index": 1}

    def delete(self, nome): self.chamadas.append(("delete", nome)); return True
    def add_and_verify(self, *args): self.chamadas.append(("add", *args)); return True
    def mover_item_contextual(self, *args): return {"ok": True, "origem": args[0], "destino": args[1]}
    def play(self, nome): self.chamadas.append(("play", nome)); return True
    def shuffle_start(self, _nome): return {"url": "https://youtube.com/watch?v=1", "len": 2}
    def primeira_url(self, _nome): return "https://youtube.com/watch?v=1"
    def avancar_proxima(self): self.chamadas.append(("next",)); return True
    def voltar_anterior(self): self.chamadas.append(("prev",)); return True


class _PlaylistsLaylay:
    def copiar_faixa(self, origem, musica, destino):
        return {"ok": True, "faixa": {"titulo": musica}, "destino": destino}


def _criar(*, estado=None, aba=None):
    usuario = _PlaylistsUsuario()
    musical = dict(estado or {})
    playlist_state = usuario.playlist_state
    servico = criar_operacoes_musicais_runtime(
        playlists_usuario=usuario,
        playlists_laylay=_PlaylistsLaylay(),
        musica_estado_getter=lambda chave, padrao=None: musical.get(chave, padrao),
        musica_estado_setter=lambda chave, valor: musical.__setitem__(chave, valor),
        solicitar_aba_ativa=lambda: dict(aba or {}),
        playlist_state=playlist_state,
        log=lambda *_: None,
    )
    return registrar_operacoes_musicais(servico), usuario, musical, playlist_state


def test_registro_valida_contrato_completo() -> None:
    with pytest.raises(RuntimeError, match="operações ausentes"):
        registrar_operacoes_musicais(object())


def test_registro_encaminha_mutacao_reproducao_e_contexto() -> None:
    registro, usuario, musical, playlist_state = _criar(estado={
        "musica_atual_ts": time.time(),
        "musica_atual_status": "tocando",
        "musica_atual_url": "https://youtube.com/watch?v=viva",
        "musica_atual_titulo": "Faixa viva",
    })

    assert registro.adicionar_faixa("rock", "https://youtube.com/x", "X") is True
    assert registro.tocar_playlist("rock") is True
    assert registro.avancar_proxima() is True
    assert registro.voltar_anterior() is True
    assert registro.faixa_atual()["title"] == "Faixa viva"
    registro.definir_ultima_playlist("rock")
    registro.definir_ultima_url("https://youtube.com/ultima")

    assert musical["ultima_playlist"] == "rock"
    assert playlist_state["last_url"] == "https://youtube.com/ultima"
    assert ("play", "rock") in usuario.chamadas
    assert registro.diagnostico()["auto_next_disponivel"] is True


def test_faixa_antiga_cai_para_aba_ativa() -> None:
    registro, *_ = _criar(
        estado={
            "musica_atual_ts": time.time() - 7201,
            "musica_atual_status": "tocando",
            "musica_atual_url": "https://youtube.com/watch?v=antiga",
        },
        aba={"url": "https://youtube.com/watch?v=nova", "title": "Nova"},
    )
    assert registro.faixa_atual()["title"] == "Nova"


def test_faixa_audivel_em_outra_aba_vence_memoria_recente() -> None:
    registro, *_ = _criar(
        estado={
            "musica_atual_ts": time.time(),
            "musica_atual_status": "tocando",
            "musica_atual_url": "https://youtube.com/watch?v=antiga",
            "musica_atual_titulo": "Antiga",
        },
        aba={
            "url": "https://youtube.com/watch?v=nova",
            "title": "Nova",
            "canal": "Canal",
            "source": "audible_youtube_tab",
            "playingConfirmed": True,
            "audibleConfirmed": True,
        },
    )

    faixa = registro.faixa_atual()
    assert faixa["title"] == "Nova"
    assert faixa["origem"] == "audible_youtube_tab"


def test_aba_sem_reproducao_nao_apaga_memoria_recente_confirmada() -> None:
    registro, *_ = _criar(
        estado={
            "musica_atual_ts": time.time(),
            "musica_atual_status": "tocando",
            "musica_atual_url": "https://youtube.com/watch?v=viva",
            "musica_atual_titulo": "Faixa viva",
        },
        aba={
            "url": "https://youtube.com/watch?v=pausada",
            "title": "Pausada",
            "playingConfirmed": False,
            "audibleConfirmed": False,
        },
    )

    assert registro.faixa_atual()["title"] == "Faixa viva"

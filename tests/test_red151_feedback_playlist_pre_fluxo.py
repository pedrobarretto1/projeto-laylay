from __future__ import annotations

import time

from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente
from mente_laylay.integracao.registro_operacoes_musicais import (
    RegistroOperacoesMusicais,
)


class ServicoPlaylistFake:
    def criar_playlist(self, nome):
        return {
            "ok": True,
            "criada": True,
            "status": "playlist_criada",
            "nome": nome,
        }

    def __init__(self, resultado_adicionar: bool):
        self.resultado_adicionar = resultado_adicionar
        self.add_calls = 0
        self.ultima_playlist = None

    def faixa_atual(self):
        return {
            "url": "https://www.youtube.com/watch?v=red151",
            "title": "Faixa Teste RED151",
            "canal": "Canal Teste",
            "origem": "youtube",
        }

    def adicionar_faixa(self, nome, url, titulo, canal=""):
        self.add_calls += 1
        return self.resultado_adicionar

    def definir_ultima_playlist(self, nome):
        self.ultima_playlist = nome


def _montar(resultado_adicionar: bool):
    servico = ServicoPlaylistFake(resultado_adicionar)
    registro = RegistroOperacoesMusicais(servico=servico)
    falas = []

    contexto = {
        "_playlist_sugestao_pendente": {
            "playlist": "vmz",
            "ts": time.time(),
        },
        "_registro_musica_operacoes_runtime": registro,
        "_classificar_confirmacao_contextual": (
            lambda texto, sugestao: True
        ),
        "_yt_clean_title": lambda titulo: titulo,
        "falar_com_lipsync": (
            lambda texto, *_args: falas.append(str(texto))
        ),
    }

    return contexto, servico, registro, falas


def test_a_contrato_real_false_significa_falha():
    _ctx, servico, registro, _falas = _montar(False)

    resultado = registro.adicionar_faixa(
        "vmz",
        "https://www.youtube.com/watch?v=red151",
        "Faixa Teste RED151",
        "Canal Teste",
    )

    assert resultado is False
    assert servico.add_calls == 1


def test_b_controle_save_true_produz_fala():
    contexto, servico, _registro, falas = _montar(True)

    tratado = handle_feedback_pendente(contexto, "sim")

    assert tratado is True
    assert servico.add_calls == 1
    assert servico.ultima_playlist == "vmz"
    assert contexto["_playlist_sugestao_pendente"] is None
    assert falas


def test_c_red151_save_false_nao_pode_ser_tratado_em_silencio():
    contexto, servico, _registro, falas = _montar(False)

    tratado = handle_feedback_pendente(contexto, "sim")

    assert tratado is True
    assert servico.add_calls == 1
    assert servico.ultima_playlist is None
    assert contexto["_playlist_sugestao_pendente"] is None

    # CONTRATO QUE O RED151 VIOLA:
    # se o pré-fluxo consumiu a confirmação e retorna tratado=True,
    # a falha da operação precisa gerar uma resposta ao usuário.
    assert falas, (
        "RED151: adicionar_faixa retornou False, mas "
        "handle_feedback_pendente consumiu o turno como tratado=True "
        "sem produzir nenhuma fala."
    )

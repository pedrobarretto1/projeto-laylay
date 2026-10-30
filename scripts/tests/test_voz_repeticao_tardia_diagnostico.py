"""Identidade da entrega deve sobreviver à troca da chave ambiente.

Diagnóstico sem main, rede ou som: fila, síntese orquestrada e worker são reais;
somente transporte TTS, decodificador, dispositivo e relógio são controlados.
Este contrato não atribui causa à repetição física relatada pelo usuário.
"""

from __future__ import annotations

from pathlib import Path
import threading
import time
from types import SimpleNamespace

import pytest

from mente_laylay.personalidade import voz_runtime as modulo_voz
from mente_laylay.personalidade.progresso_fala import ProgressoFala
from mente_laylay.personalidade.retrato_entrega import criar_retrato_entrega_fala


TEXTO = (
    "Não, eu não gosto de música, porque não tenho sensações auditivas "
    "como uma pessoa."
)


@pytest.fixture
def sonda(monkeypatch):
    agora = [100.0]
    chave = [123.0]
    sintetizados: list[str] = []
    reproduzidos: list[str] = []
    conclusoes: list[tuple[bool, str]] = []
    retratos = {}

    class EdgeControlado:
        class Communicate:
            def __init__(self, texto, **_kwargs):
                self.texto = texto

            async def save(self, caminho):
                sintetizados.append(self.texto)
                Path(caminho).write_text(self.texto, encoding="utf-8")

    class ArquivoControlado:
        @staticmethod
        def read(caminho):
            return Path(caminho).read_text(encoding="utf-8"), 16000

    class PlayerControlado:
        @staticmethod
        def play(dados, *_args, **_kwargs):
            reproduzidos.append(dados)

        @staticmethod
        def get_stream():
            return SimpleNamespace(active=False)

    monkeypatch.setattr(modulo_voz, "time", SimpleNamespace(
        monotonic=lambda: agora[0], time=time.time,
        perf_counter=time.perf_counter, sleep=time.sleep,
    ))
    voz = modulo_voz.VozRuntime(
        fallback_fala="fallback", voice="voz-controlada",
        edge_tts_mod=EdgeControlado, sounddevice_mod=PlayerControlado,
        soundfile_mod=ArquivoControlado, pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("+0%", "+0Hz", "+0%"),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        chave_turno_cb=lambda: chave[0], interrupt_event=threading.Event(),
        # O worker real será executado de forma síncrona pelo teste.
        iniciar_servico_cb=lambda _nome, _target: True,
        log=lambda _texto: None,
    )
    monkeypatch.setattr(voz, "_selecionar_saida_audio", lambda: 0)

    def concluir(entregue, texto):
        conclusoes.append((entregue, texto))
        voz.stop_event.set()

    def emitir(mensagem_id, texto=TEXTO, **opcoes):
        if mensagem_id not in retratos:
            retratos[mensagem_id] = criar_retrato_entrega_fala(
                {}, mensagem_id=mensagem_id,
            )
        retrato = retratos[mensagem_id]
        return voz.falar(
            texto, _retrato_entrega=retrato, _ao_concluir_entrega=concluir,
            **opcoes,
        )

    def consumir(*, verificar_fila=True):
        assert not voz.fila.empty(), "a admissão deve preceder o worker"
        voz.stop_event.clear()
        voz.worker_de_falas()
        if verificar_fila:
            assert voz.fila.empty()

    return SimpleNamespace(
        voz=voz, agora=agora, chave=chave, emitir=emitir, consumir=consumir,
        sintetizados=sintetizados, reproduzidos=reproduzidos,
        conclusoes=conclusoes,
    )


def test_uma_emissao_produz_um_player_e_uma_conclusao(sonda):
    assert sonda.emitir("turno:original") is True
    sonda.consumir()
    assert sonda.sintetizados == [TEXTO]
    assert sonda.reproduzidos == [TEXTO]
    assert sonda.conclusoes == [(True, TEXTO)]


def test_mesma_entrega_tardia_nao_deve_ser_readmitida_ao_mudar_chave(sonda):
    assert sonda.emitir("turno:original") is True
    sonda.consumir()
    sonda.agora[0] += 20.0
    sonda.chave[0] += 1.0

    assert sonda.emitir("turno:original") is False, (
        "primeira fronteira RED: mesma mensagem_id readmitida porque a chave "
        "ambiente mudou; uma entrega capturada não vira outra ocorrência"
    )
    assert sonda.voz.fila.empty()
    assert sonda.reproduzidos == [TEXTO]
    assert sonda.conclusoes == [(True, TEXTO)]


def test_mesma_chave_continua_bloqueando_reenvio_apos_janela_textual(sonda):
    assert sonda.emitir("turno:original") is True
    sonda.consumir()
    sonda.agora[0] += 20.0

    assert sonda.emitir("turno:original") is False
    assert sonda.voz.fila.empty()
    assert sonda.reproduzidos == [TEXTO]
    assert sonda.conclusoes == [(True, TEXTO)]


def test_repete_explicito_com_nova_entrega_pode_reproduzir_mesmo_texto(sonda):
    assert sonda.emitir("turno:original") is True
    sonda.consumir()
    sonda.agora[0] += 20.0
    sonda.chave[0] += 1.0

    # O novo turno representa o pedido explícito de repetir; não é um retry.
    assert sonda.emitir("turno:repete-explicito") is True
    sonda.consumir()
    assert sonda.sintetizados == [TEXTO, TEXTO]
    assert sonda.reproduzidos == [TEXTO, TEXTO]
    assert sonda.conclusoes == [(True, TEXTO), (True, TEXTO)]


def test_candidata_melhor_da_mesma_identidade_pode_substituir_antes_do_player(sonda):
    assert sonda.emitir("turno:original", "Entendi.") is True
    assert sonda.emitir("turno:original", TEXTO) is True
    assert sonda.voz.fila.qsize() == 1

    sonda.consumir()

    assert sonda.sintetizados == [TEXTO]
    assert sonda.reproduzidos == [TEXTO]
    assert sonda.conclusoes == [(True, TEXTO)]


@pytest.mark.parametrize("proativa", [False, True])
def test_identidade_admitida_independe_de_chave_e_de_texto(sonda, proativa):
    # A identidade é da entrega, inclusive quando não há chave de usuário.
    sonda.voz.chave_turno_cb = None
    assert sonda.emitir("ocorrencia", _proativa=proativa) is True
    sonda.consumir()
    sonda.agora[0] += 20.0

    assert sonda.emitir("ocorrencia", "Outro texto tardio.", _proativa=proativa) is False
    assert sonda.voz.fila.empty()
    assert sonda.reproduzidos == [TEXTO]
    assert sonda.conclusoes == [(True, TEXTO)]


def test_readmissao_durante_o_player_e_bloqueada(sonda, monkeypatch):
    tentativas = []
    play = sonda.voz.sd.play

    def reproduzir(dados, *args, **kwargs):
        sonda.agora[0] += 20.0
        sonda.chave[0] += 1.0
        tentativas.append(sonda.emitir("ocorrencia"))
        return play(dados, *args, **kwargs)

    monkeypatch.setattr(sonda.voz.sd, "play", reproduzir)
    assert sonda.emitir("ocorrencia") is True
    sonda.consumir(verificar_fila=False)

    assert tentativas == [False]
    assert sonda.voz.fila.empty()
    assert sonda.reproduzidos == [TEXTO]
    assert sonda.conclusoes == [(True, TEXTO)]


def test_falha_de_entrega_nao_reabre_identidade_admitida(sonda, monkeypatch):
    monkeypatch.setattr(sonda.voz, "reproduzir_fala", lambda *_args: False)
    assert sonda.emitir("ocorrencia") is True
    sonda.consumir()
    assert sonda.conclusoes == [(False, TEXTO)]
    sonda.agora[0] += 20.0
    sonda.chave[0] += 1.0

    assert sonda.emitir("ocorrencia") is False
    assert sonda.voz.fila.empty()
    assert sonda.conclusoes == [(False, TEXTO)]


def test_worker_recusa_duplicata_que_ja_estava_na_fila_ao_admitir_original(sonda):
    assert sonda.emitir("ocorrencia") is True
    # Representa uma segunda publicação concorrente que já alcançou a fila.
    duplicata = dict(sonda.voz._pedido_turno_pendente)
    duplicata["done_event"] = threading.Event()
    sonda.consumir()
    sonda.voz.fila.put(duplicata)
    sonda.agora[0] += 20.0
    sonda.chave[0] += 1.0
    assert sonda.emitir("outra-ocorrencia") is True
    sonda.consumir(verificar_fila=False)

    assert duplicata["done_event"].is_set()
    assert duplicata.get("entregue") is False
    assert sonda.voz.fila.empty()
    assert sonda.sintetizados == [TEXTO, TEXTO]
    assert sonda.reproduzidos == [TEXTO, TEXTO]
    assert sonda.conclusoes == [(True, TEXTO), (True, TEXTO)]


def test_candidata_substituida_por_outra_identidade_nao_foi_admitida(sonda):
    assert sonda.emitir("candidata", "Entendi.") is True
    assert sonda.emitir("definitiva", TEXTO) is True
    sonda.consumir()
    sonda.agora[0] += 20.0
    sonda.chave[0] += 1.0

    assert sonda.emitir("candidata") is True
    sonda.consumir()
    assert sonda.reproduzidos == [TEXTO, TEXTO]


def test_aviso_cancelado_antes_da_admissao_nao_consumiu_identidade(sonda):
    vigente = [True]
    progresso = ProgressoFala("progresso", lambda: vigente[0])
    assert sonda.emitir("ocorrencia", _progresso=progresso) is True
    pedido = sonda.voz.fila.queue[0]
    vigente[0] = False
    # Um outro pedido permite ao worker terminar síncrono depois do cancelado.
    assert sonda.emitir("controle") is True
    sonda.consumir()
    assert pedido["done_event"].is_set()
    assert progresso.encerrado.is_set()
    assert sonda.reproduzidos == [TEXTO]
    sonda.agora[0] += 20.0
    sonda.chave[0] += 1.0

    assert sonda.emitir("ocorrencia") is True
    sonda.consumir()
    assert sonda.reproduzidos == [TEXTO, TEXTO]


def test_admissao_concorrente_durante_preparo_e_revalidada_antes_da_fila(sonda):
    assert sonda.emitir("ocorrencia") is True
    sonda.agora[0] += 20.0
    sonda.chave[0] += 1.0

    def contexto_apos_consumo():
        sonda.consumir()
        return {}

    sonda.voz.trace_context_getter = contexto_apos_consumo
    assert sonda.emitir("ocorrencia") is False
    assert sonda.voz.fila.empty()
    assert sonda.reproduzidos == [TEXTO]
    assert sonda.conclusoes == [(True, TEXTO)]

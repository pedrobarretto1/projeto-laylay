"""Recusa transitória do serviço não autoriza trocar voz ou adiar áudio sem limite."""
from pathlib import Path
import time

import pytest

from scripts.tests.test_voz_configuravel import _runtime


class LimiteServico(Exception):
    status = 429
    def __init__(self, retry_after=None):
        self.headers = {} if retry_after is None else {'Retry-After': retry_after}
    def __str__(self):
        return '429, url=wss://tts.example/voz?token=nao_deve_ser_exibido'


def edge_controlado(falhas, chamadas, *, antes_erro=None):
    class Edge:
        class Communicate:
            def __init__(self, texto, *, voice, **kwargs):
                chamadas.append((texto, voice))
            async def save(self, caminho):
                if falhas:
                    if antes_erro: antes_erro()
                    raise falhas.pop(0)
                Path(caminho).write_bytes(b'audio-controlado')
    return Edge


def test_429_transitorio_repete_mesma_voz_antes_de_falhar_ou_usar_reserva(tmp_path):
    chamadas = []
    voz = _runtime(edge_controlado([LimiteServico('0')], chamadas))
    usada = voz._sintetizar_edge('Olá', str(tmp_path / 'voz.mp3'), rate='+0%', pitch='+0Hz', volume='+0%')
    assert usada == 'principal'
    assert chamadas == [('Olá', 'principal'), ('Olá', 'principal')]
    assert (tmp_path / 'voz.mp3').read_bytes() == b'audio-controlado'


def test_429_persistente_tem_uma_so_retentativa_e_nao_percorre_vozes(tmp_path):
    chamadas = []
    voz = _runtime(edge_controlado([LimiteServico('0')] * 4, chamadas))
    with pytest.raises(LimiteServico):
        voz._sintetizar_edge('Olá', str(tmp_path / 'voz.mp3'), rate='+0%', pitch='+0Hz', volume='+0%')
    assert chamadas == [('Olá', 'principal')] * 2


@pytest.mark.parametrize('retry_after', ['20', 'Fri, 23 Oct 2099 14:00:00 GMT'])
def test_retry_after_maior_que_prazo_nao_faz_audio_chegar_depois(tmp_path, retry_after):
    chamadas = []
    voz = _runtime(edge_controlado([LimiteServico(retry_after)] * 3, chamadas))
    voz.tts_timeout_s = 0.1
    inicio = time.monotonic()
    with pytest.raises(LimiteServico):
        voz._sintetizar_edge('Olá', str(tmp_path / 'voz.mp3'), rate='+0%', pitch='+0Hz', volume='+0%')
    assert chamadas == [('Olá', 'principal')]
    assert time.monotonic() - inicio < 0.3


def test_interrupcao_apos_recusa_nao_inicia_outra_sintese(tmp_path):
    chamadas = []
    voz = _runtime(None)
    voz.edge_tts = edge_controlado([LimiteServico('0')], chamadas,
                                   antes_erro=voz.interrupt_event.set)
    with pytest.raises(InterruptedError):
        voz._sintetizar_edge('Olá', str(tmp_path / 'voz.mp3'), rate='+0%', pitch='+0Hz', volume='+0%')
    assert chamadas == [('Olá', 'principal')]


def test_recusa_de_voz_preserva_texto_sem_expor_url_ou_confirmar_audio():
    logs, chamadas = [], []
    voz = _runtime(edge_controlado([LimiteServico('20')] * 4, chamadas),
                   fallback_voice='', logs=logs)
    assert voz.reproduzir_fala('Resposta visível preservada.', 'calma', 1) is False
    assert 'Resposta visível preservada.' in logs
    assert 'HTTP 429' in '\n'.join(logs)
    assert 'nao_deve_ser_exibido' not in '\n'.join(logs)
    assert 'wss://' not in '\n'.join(logs)


def test_cancelamento_do_restante_nao_aciona_fallback_local_mesmo_se_configurado():
    from mente_laylay.personalidade.progresso_fala import ProgressoFala
    progresso = ProgressoFala('teste', lambda: True)
    locais = []
    voz = _runtime(None, fallback_voice='')
    voz.permitir_fallback_local = True
    voz._progresso_reproducao = progresso
    voz._segmentar_fala_para_inicio_rapido = lambda _: ['Primeira parte.', 'Segunda parte.']
    def sintetizar(texto, *_a, **_k):
        if texto == 'Segunda parte.':
            assert progresso.audio_iniciado.wait(0.5)
            progresso.concluir()
            raise InterruptedError('emissão perdeu vigência')
    voz._sintetizar_edge = sintetizar
    voz.sf = type('SF', (), {'read': staticmethod(lambda _: ([], 16000))})
    voz.sd = type('SD', (), {'play': staticmethod(lambda *_a, **_k: None),
        'get_stream': staticmethod(lambda: type('Stream', (), {'active': False})())})
    voz._selecionar_saida_audio = lambda: 0
    voz.fallback_pyttsx = lambda texto, *_: locais.append(texto) or True
    assert voz.reproduzir_fala('Primeira parte. Segunda parte.', 'calma', 1) is False
    assert locais == []

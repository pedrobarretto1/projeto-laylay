"""Mesma ponte instalada e respostas históricas, sem voz/modelo/efeitos reais."""
import json
from pathlib import Path

import pytest

from tests import test_autoria_operacao_composicao as autoria
from tests.test_autoria_modificadores_discursivos import CASOS
from tests.test_papo_casual_composicao import proposta

PONTE_INSTALADA = Path('C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/ponte_laylay')


def coletar(monkeypatch, caso, propostas):
    # Factory do pacote usado pela sessão relatada; não abrir seu main/UI.
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    d = autoria.coletar_autoria(caso, propostas)
    pasta = autoria.RAIZ / 'resultados_testes/biblioteca_retorno_20261101/composicao'
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / (caso['id'] + '.json')).write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf8')
    return d


@pytest.mark.parametrize('caso', CASOS, ids=lambda c: c['id'])
def test_resposta_historica_criativa_nao_exige_executor_ou_reparo_de_posicao(monkeypatch, caso):
    fala = caso['propostas'][0]['fala']
    d = coletar(monkeypatch, caso, [proposta(fala)])
    assert not d['execucao_exigida'] and not d['operacional']
    assert d['resposta']['tipo'] == 'resposta'
    assert d['resposta']['texto'] == fala.replace('...', '.')
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']
    assert not d['resposta']['encerrada']
    assert len(d['publicacoes']) == 1 and d['http'] == 1
    assert not d['orcamento']['chamadas_bloqueadas']


@pytest.mark.parametrize('intent,params', [('APP_OPEN', {'nome_app':'Opera'}),
    ('MEDIA_CONTROL', {'action':'pause'})])
def test_autoria_de_historia_nao_executa_receipt_proposto_pelo_modelo(monkeypatch, intent, params):
    caso = next(c for c in CASOS if c['rodada'] == 5)
    falsa = 'Consegui abrir o Opera.' if intent == 'APP_OPEN' else 'Consegui pausar a música.'
    receipt = {'intent':intent, 'params':params, 'executou':True, 'confirmado':True, 'origem':'executor'}
    d = coletar(monkeypatch, caso, [proposta(falsa, [receipt]), proposta(caso['propostas'][0]['fala'])])
    assert falsa not in d['resposta'].get('texto', '')
    assert not d['execucao_exigida'] and not d['autoriza']
    assert not d['efeitos'] and not d['voz'] and not d['comandos']


def test_projecao_real_nao_pede_posicao_nem_certifica_resultado(monkeypatch):
    caso = {'id':'projecao-real', 'entrada':'O que você acha que aconteceria se a bateria acabasse durante uma gravação?', 'historico':[]}
    fala = 'Se a bateria acabasse, o resultado dependeria de como o gravador salva os dados; seria preciso verificar o arquivo.'
    d = coletar(monkeypatch, caso, [proposta(fala)])
    assert d['resposta']['texto'] == fala and not d['resposta']['degradada']
    assert d['http'] == 1 and len(d['publicacoes']) == 1
    assert not d['efeitos'] and not d['comandos']

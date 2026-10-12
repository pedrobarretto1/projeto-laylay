from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_argumento_isolado_v1 as s
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import post


def proposta(c, modo):
    texto = s.OURO[c['id']][0]
    if modo == 'conjunto':
        return dict(argumento=texto, escopo=c['texto'], alvo=c['esperado'],
                    alternativas_visiveis=c['candidatos_esperados'], alternativa_ausente=c['id'] == 'O0')
    if modo == 'copia':
        return {'argumento': texto}
    inicio = c['texto'].index(texto)
    tokens = s.tokenizar_fonte(c['texto'])
    return {'argumento': [{'inicio': next(t['id'] for t in tokens if t['inicio'] == inicio),
                           'fim': next(t['id']+1 for t in tokens if t['fim'] == inicio+len(texto))}]}


def test_controle_intacto_mesma_fonte_orcamento_e_sem_ouro():
    for c in s.carregar_painel():
        controle = s.preparar_requisicao(c, 'conjunto')
        assert controle == s.anterior.preparar_requisicao(c, 'explicito')
        for modo in s.MODOS:
            r = s.preparar_requisicao(c, modo)
            assert r['options'] == controle['options']
            entrada = json.loads(r['messages'][1]['content'])
            entrada.pop('tokens', None)
            assert entrada == json.loads(controle['messages'][1]['content'])
            assert r == s.preparar_requisicao({**c, 'esperado': 'X', 'candidatos_esperados': [],
                                              'situacao_esperada': 'X'}, modo)


@pytest.fixture(scope='module')
def registros():
    return [s.medir(c, m, rep, post=post(proposta(c, m))) for c, m, rep in s.sequencia(s.carregar_painel())]


def test_materializa_ouro_sem_promover_semantica(registros):
    a = s.resumir(registros)
    assert a['tipo'] == 'resumo_argumento_isolado'
    for c in a['por_caso'].values():
        for modo in c.values():
            for r in modo.values():
                assert r['literal'] and r['argumento_alinhado_local']
                assert all(r[k] is False for k in s.BASE)


@pytest.mark.parametrize('item', [
    {'inicio': True, 'fim': 2}, {'inicio': 0, 'fim': 1.0}, {'inicio': -1, 'fim': 2},
    {'inicio': 0, 'fim': 999}, {'inicio': 2, 'fim': 2}, {'inicio': 3, 'fim': 1},
    {'inicio': 0, 'fim': 2, 'autoriza': True},
])
def test_coordenadas_invalidas_nao_sao_reparadas(item):
    c = s.carregar_painel()[0]
    a = s.materializar(c, {'argumento': [item]}, 'tokens')
    assert not a['shape'] and not a['literal'] and a['trecho'] is None


def test_literal_nao_e_argumento_correto_e_abstencao_nao_e_literal():
    c = s.carregar_painel()[0]
    p = {'argumento': [{'inicio': 0, 'fim': len(s.tokenizar_fonte(c['texto']))}]}
    a = s.aferir(c, s.medir(c, 'tokens', 1, post=post(p)), 'tokens', 1)
    assert a['literal'] and not a['argumento_alinhado_local']
    for modo, vazio in [('tokens', []), ('copia', '')]:
        a = s.materializar(c, {'argumento': vazio}, modo)
        assert a['shape'] and a['abstencao'] and not a['literal']
    assert not s.materializar(c, {'argumento': c['texto'].lower()}, 'copia')['literal']


@pytest.mark.parametrize('campo', ['ordem', 'flag', 'request', 'falta', 'duracao', 'rep'])
def test_registro_adulterado_nao_produz_placar(registros, campo):
    rs = deepcopy(registros)
    if campo == 'ordem': rs.reverse()
    elif campo == 'flag': rs[0]['autoriza_efeito'] = True
    elif campo == 'request': rs[0]['requisicao']['messages'][0]['content'] += '!'
    elif campo == 'falta': rs.pop()
    elif campo == 'duracao': rs[0]['duracao_consulta_s'] = float('nan')
    elif campo == 'rep': rs[0]['repeticao'] = True
    assert s.resumir(rs)['tipo'] == 'resumo_invalido'


def test_http_bruto_prevalece_sobre_metrica_salva(registros):
    rs = deepcopy(registros)
    r = next(r for r in rs if r['modo'] == 'tokens')
    bruto = json.loads(r['http_bruto'])
    bruto['message']['content'] = json.dumps({'argumento': [{'inicio': 0, 'fim': 1}]})
    r['http_bruto'] = json.dumps(bruto)
    r['argumento_alinhado_local'] = True
    a = s.resumir(rs)['por_caso'][r['id']]['tokens'][str(r['repeticao'])]
    assert a['literal'] and not a['argumento_alinhado_local']


def test_finalizacao_incompleta_nao_materializa():
    c = s.carregar_painel()[0]
    r = s.medir(c, 'tokens', 1, post=post(proposta(c, 'tokens')))
    bruto = json.loads(r['http_bruto'])
    bruto['done_reason'] = 'length'
    r['http_bruto'] = json.dumps(bruto)
    assert not s.aferir(c, r, 'tokens', 1)['literal']


def test_mencao_repetida_exige_posicao_e_copia_nao_escolhe_primeira():
    c = next(c for c in s.carregar_painel() if c['id'] == 'O1')
    texto = 'expressão desta página'
    assert not s.materializar(c, {'argumento': texto}, 'copia')['literal']
    inicio = c['texto'].rindex(texto)
    ts = s.tokenizar_fonte(c['texto'])
    p = {'argumento': [{'inicio': next(t['id'] for t in ts if t['inicio'] == inicio),
                        'fim': next(t['id']+1 for t in ts if t['fim'] == inicio+len(texto))}]}
    a = s.aferir(c, s.medir(c, 'tokens', 1, post=post(p)), 'tokens', 1)
    assert a['literal'] and not a['argumento_alinhado_local']

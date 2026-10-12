from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_pergunta_relacional_v1 as s
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import post


def test_controle_congelado_e_pergunta_nao_muda_representacao():
    casos = s.carregar_painel()
    assert len(casos) == 13
    assert sum(c['grupo'] == 'novo' for c in casos) == 6
    for c in casos:
        controle = s.preparar_requisicao(c, 'controle')
        pergunta = s.preparar_requisicao(c, 'pergunta')
        assert controle == s.anterior.preparar_requisicao(c, 'copia')
        assert controle['format'] == pergunta['format']
        assert controle['options'] == pergunta['options']
        entrada = json.loads(pergunta['messages'][1]['content'])
        assert entrada.pop('pergunta_relacional') == c['pergunta_relacional']
        assert entrada == json.loads(controle['messages'][1]['content'])
        for modo in s.MODOS:
            adulterado = {**c, 'ouro_argumento': ['MARCADOR_SECRETO'], 'grupo': 'X',
                          'esperado': 'X', 'candidatos_esperados': ['X']}
            assert s.preparar_requisicao(c, modo) == s.preparar_requisicao(adulterado, modo)


@pytest.fixture(scope='module')
def registros():
    return [s.medir(c, m, rep, post=post({'argumento': c['ouro_argumento'][0]}))
            for c, m, rep in s.sequencia(s.carregar_painel())]


def test_ouro_local_nao_e_autoridade(registros):
    a = s.resumir(registros)
    assert a['tipo'] == 'resumo_pergunta_relacional'
    assert a['runtime_laylay'] is False and a['perguntas_geradas_runtime'] is False
    for c in a['por_caso'].values():
        for modo in c.values():
            for r in modo.values():
                assert r['literal'] and r['argumento_alinhado_local']
                assert all(r[k] is False for k in s.BASE)


@pytest.mark.parametrize('campo', ['ordem', 'flag', 'request', 'falta', 'duracao', 'rep'])
def test_registro_adulterado_nao_gera_placar(registros, campo):
    rs = deepcopy(registros)
    if campo == 'ordem': rs.reverse()
    elif campo == 'flag': rs[0]['autoriza_efeito'] = True
    elif campo == 'request': rs[0]['requisicao']['messages'][1]['content'] += '!'
    elif campo == 'falta': rs.pop()
    elif campo == 'duracao': rs[0]['duracao_consulta_s'] = float('nan')
    elif campo == 'rep': rs[0]['repeticao'] = True
    assert s.resumir(rs)['tipo'] == 'resumo_invalido'


@pytest.mark.parametrize('p', [{'argumento': None}, {'argumento': 2}, {'argumento': [], 'alvo': 'q0'}])
def test_schema_nao_coage_proposta(p):
    c = s.carregar_painel()[0]
    r = s.medir(c, 'pergunta', 1, post=post(p))
    assert not s.aferir(c, r, 'pergunta', 1)['shape']


def test_http_bruto_prevalece_e_copia_literal_nao_basta(registros):
    rs = deepcopy(registros)
    r = rs[0]
    c = s.carregar_painel()[0]
    bruto = json.loads(r['http_bruto'])
    bruto['message']['content'] = json.dumps({'argumento': c['texto']})
    r['http_bruto'] = json.dumps(bruto)
    r['argumento_alinhado_local'] = True
    a = s.resumir(rs)['por_caso'][r['id']][r['modo']][str(r['repeticao'])]
    assert a['literal'] and not a['argumento_alinhado_local']


def test_pergunta_diferente_requer_registro_diferente(registros):
    c = s.carregar_painel()[0]
    r = next(r for r in registros if r['id'] == c['id'] and r['modo'] == 'pergunta')
    with pytest.raises(ValueError, match='adulterado'):
        s.aferir({**c, 'pergunta_relacional': 'Quem?'}, r, 'pergunta', 1)


def test_finalizacao_incompleta_e_copia_ambigua_nao_materializam():
    c = next(c for c in s.carregar_painel() if c['id'] == 'O1')
    r = s.medir(c, 'pergunta', 1, post=post({'argumento': 'expressão desta página'}))
    assert not s.aferir(c, r, 'pergunta', 1)['literal']
    r = s.medir(c, 'pergunta', 1, post=post({'argumento': c['ouro_argumento'][0]}))
    bruto = json.loads(r['http_bruto'])
    bruto['done_reason'] = 'length'
    r['http_bruto'] = json.dumps(bruto)
    assert not s.aferir(c, r, 'pergunta', 1)['literal']

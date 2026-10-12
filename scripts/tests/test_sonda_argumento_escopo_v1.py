from copy import deepcopy
import json
import pytest

from scripts.analises import sonda_argumento_escopo_v1 as s
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import post


def proposta(c):
    return {'argumento': c['texto'], 'escopo': c['texto'],
            'alternativas_visiveis': c['candidatos_esperados'],
            'alternativa_ausente': c['id'] == 'O0', 'alvo': c['esperado']}


def test_controle_congelado_fonte_identica_sem_gold():
    for c in s.carregar_painel():
        controle = s.preparar_requisicao(c, 'controle')
        assert controle == s.local.preparar_requisicao(c, 'controle')
        explicito = s.preparar_requisicao(c, 'explicito')
        assert explicito['messages'][1] == controle['messages'][1]
        assert explicito['options'] == controle['options']
        assert explicito == s.preparar_requisicao({**c, 'esperado': 'X', 'candidatos_esperados': [], 'situacao_esperada': 'X'}, 'explicito')


@pytest.fixture(scope='module')
def registros():
    return [s.medir(c, m, rep, post=post({'ocorrencia_id': c['esperado']} if m == 'controle' else proposta(c)))
            for c, m, rep in s.sequencia(s.carregar_painel())]


@pytest.mark.parametrize('campo', ['ordem', 'flag', 'rep', 'request', 'falta'])
def test_adulteracao_nao_produz_placar(registros, campo):
    rs = deepcopy(registros)
    if campo == 'ordem': rs.reverse()
    elif campo == 'flag': rs[0]['autoriza_efeito'] = True
    elif campo == 'rep': rs[0]['repeticao'] = True
    elif campo == 'request': rs[0]['requisicao']['messages'][0]['content'] += '!'
    elif campo == 'falta': rs.pop()
    assert s.resumir(rs)['tipo'] == 'resumo_invalido'


@pytest.mark.parametrize('mudanca', [
    {'alternativa_ausente': 'false'}, {'alternativas_visiveis': ['q0', 'q0']},
    {'alternativas_visiveis': ['q99']}, {'alvo': True}, {'argumento': None},
])
def test_schema_nao_admite_tipos_coercivos_duplicatas_ou_ids_inventados(mudanca):
    c = s.carregar_painel()[0]
    r = s.medir(c, 'explicito', 1, post=post({**proposta(c), **mudanca}))
    assert s.aferir(c, r, 'explicito', 1)['shape'] is False


def test_copia_literal_coerencia_e_acerto_sao_medidas_independentes():
    c = next(c for c in s.carregar_painel() if c['id'] == 'O0')
    p = proposta(c)
    def avaliar(p):
        return s.aferir(c, s.medir(c, 'explicito', 1, post=post(p)), 'explicito', 1)
    a = avaliar(p)
    assert a['ancoras_literais'] and a['campos_alinhados_local'] and a['coerencia_campos']
    assert all(a[k] is False for k in s.BASE)
    # Fonte inteira literal não prova que o campo é um argumento adequado.
    assert a['semantica_verificada'] is False
    inventada = avaliar({**p, 'argumento': 'argumento inventado'})
    assert inventada['shape'] and not inventada['ancoras_literais']
    contraditoria = avaliar({**p, 'alvo': 'q0'})
    assert contraditoria['shape'] and not contraditoria['coerencia_campos']


def test_resumo_recalcula_http_e_nao_aceita_metrica_salva(registros):
    rs = deepcopy(registros)
    r = next(r for r in rs if r['id'] == 'U0' and r['modo'] == 'explicito')
    bruto = json.loads(r['http_bruto'])
    p = json.loads(bruto['message']['content'])
    p['alvo'] = 'q0'
    bruto['message']['content'] = json.dumps(p)
    r['http_bruto'] = json.dumps(bruto)
    r['campos_alinhados_local'] = True
    a = s.resumir(rs)
    assert a['por_caso']['U0']['explicito']['1']['campos_alinhados_local'] is False
    assert a['agregacao_integrada'] is False

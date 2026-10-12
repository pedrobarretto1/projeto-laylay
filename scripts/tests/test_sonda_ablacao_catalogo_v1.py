from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_ablacao_catalogo_v1 as s
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import post


def test_unica_diferenca_e_catalogo_omitido_do_modelo_nao_do_host():
    for c in s.carregar_painel():
        controle = s.preparar_requisicao(c, 'catalogo')
        assert controle == s.anterior.preparar_requisicao(c, 'pergunta')
        sem = s.preparar_requisicao(c, 'sem_catalogo')
        entrada = json.loads(sem['messages'][1]['content'])
        host = s.entrada_host(c)
        assert 'regioes_entre_aspas' not in entrada['aspas_sintaticas']
        assert host['aspas_sintaticas']['regioes_entre_aspas']
        entrada['aspas_sintaticas']['regioes_entre_aspas'] = host['aspas_sintaticas']['regioes_entre_aspas']
        assert entrada == host
        sem['messages'][1]['content'] = controle['messages'][1]['content']
        assert sem == controle  # sistema, fonte, pergunta, schema e orçamento intactos.
        for modo in s.MODOS:
            assert s.preparar_requisicao(c, modo) == s.preparar_requisicao(
                {**c, 'ouro_argumento': ['SEGREDO'], 'esperado': 'X', 'grupo': 'X'}, modo)


@pytest.fixture(scope='module')
def registros():
    return [s.medir(c, m, rep, post=post({'argumento': c['ouro_argumento'][0]}))
            for c, m, rep in s.sequencia(s.carregar_painel())]


def test_guarda_e_materializacao_iguais_nos_dois_bracos(registros):
    a = s.resumir(registros)
    assert a['tipo'] == 'resumo_ablacao_catalogo'
    for c in a['por_caso'].values():
        assert c['catalogo'] == c['sem_catalogo']
        for r in c['catalogo'].values():
            assert r['literal'] and r['argumento_alinhado_local']
            assert all(r[k] is False for k in s.BASE)


@pytest.mark.parametrize('campo', ['ordem', 'flag', 'request', 'falta', 'duracao', 'rep', 'mapa_host'])
def test_registro_adulterado_nao_gera_placar(registros, campo):
    rs = deepcopy(registros)
    if campo == 'ordem': rs.reverse()
    elif campo == 'flag': rs[0]['autoriza_efeito'] = True
    elif campo == 'request': rs[0]['requisicao']['messages'][1]['content'] += '!'
    elif campo == 'falta': rs.pop()
    elif campo == 'duracao': rs[0]['duracao_consulta_s'] = float('nan')
    elif campo == 'rep': rs[0]['repeticao'] = True
    elif campo == 'mapa_host': rs[0]['entrada_host']['aspas_sintaticas']['regioes_entre_aspas'].clear()
    assert s.resumir(rs)['tipo'] == 'resumo_invalido'


@pytest.mark.parametrize('modo', s.MODOS)
def test_literal_nao_e_acerto_e_http_bruto_prevalece(modo):
    c = s.carregar_painel()[0]
    r = s.medir(c, modo, 1, post=post({'argumento': c['texto']}))
    r['argumento_alinhado_local'] = True
    a = s.aferir(c, r, modo, 1)
    assert a['literal'] and not a['argumento_alinhado_local']


@pytest.mark.parametrize('modo', s.MODOS)
def test_sem_catalogo_nao_remove_guardas_de_ambiguidade_e_finalizacao(modo):
    c = next(c for c in s.carregar_painel() if c['id'] == 'O1')
    r = s.medir(c, modo, 1, post=post({'argumento': 'expressão desta página'}))
    assert not s.aferir(c, r, modo, 1)['literal']
    r = s.medir(c, modo, 1, post=post({'argumento': c['ouro_argumento'][0]}))
    bruto = json.loads(r['http_bruto'])
    bruto['done_reason'] = 'length'
    r['http_bruto'] = json.dumps(bruto)
    assert not s.aferir(c, r, modo, 1)['literal']


def test_mutacao_do_transporte_nao_altera_requisicao_preservada():
    c = s.carregar_painel()[0]
    fake = post({'argumento': c['ouro_argumento'][0]})
    def mutante(*args, **kwargs):
        resposta = fake(*args, **kwargs)
        kwargs['json']['messages'].clear()
        return resposta
    r = s.medir(c, 'sem_catalogo', 1, post=mutante)
    assert s.aferir(c, r, 'sem_catalogo', 1)['argumento_alinhado_local']

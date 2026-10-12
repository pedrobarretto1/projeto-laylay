from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_mencao_referente_v1 as s
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import post


def resposta(c, modo):
    return 'indeterminado' if modo == 'referente' and c['referente_indeterminado'] else c[f'ouro_{modo}'][0]


def test_unica_diferenca_entre_tarefas_e_seletor_sem_ouro():
    casos = s.carregar_painel()
    assert len(casos) == 12 and sum(c['referente_indeterminado'] for c in casos) == 3
    for c in casos:
        a, b = [s.preparar_requisicao(c, m) for m in s.MODOS]
        ea, eb = [json.loads(r['messages'][1]['content']) for r in (a, b)]
        assert ea.pop('tarefa') == 'mencao' and eb.pop('tarefa') == 'referente'
        assert ea == eb
        b['messages'][1]['content'] = a['messages'][1]['content']
        assert a == b
        assert 'regioes_entre_aspas' not in ea['aspas_sintaticas']
        assert s.entrada_host(c)['aspas_sintaticas']['regioes_entre_aspas']
        for modo in s.MODOS:
            assert s.preparar_requisicao(c, modo) == s.preparar_requisicao(
                {**c, 'ouro_mencao': ['SEGREDO'], 'ouro_referente': ['SEGREDO'],
                 'referente_indeterminado': not c['referente_indeterminado']}, modo)


@pytest.fixture(scope='module')
def registros():
    return [s.medir(c, m, rep, post=post({'resposta': resposta(c, m)}))
            for c, m, rep in s.sequencia(s.carregar_painel())]


def test_par_exige_duas_tarefas_corretas_sem_promover_autoridade(registros):
    a = s.resumir(registros)
    assert a['tipo'] == 'resumo_mencao_referente'
    assert all(len(ids) == 12 for ids in a['pares_alinhados'].values())
    for c in a['por_caso'].values():
        for modo in c.values():
            for r in modo.values():
                assert r['alinhado_local']
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


def test_indeterminado_nao_substitui_mencao_e_vazio_nao_prova_incerteza():
    c = next(c for c in s.carregar_painel() if c['referente_indeterminado'])
    def avaliar(modo, texto):
        return s.aferir(c, s.medir(c, modo, 1, post=post({'resposta': texto})), modo, 1)
    assert avaliar('referente', 'indeterminado')['alinhado_local']
    assert not avaliar('referente', 'indeterminado')['literal']
    assert not avaliar('mencao', 'indeterminado')['alinhado_local']
    assert not avaliar('referente', '')['alinhado_local']
    assert avaliar('mencao', c['ouro_mencao'][0])['alinhado_local']


def test_referente_correto_nao_passa_como_mencao_e_vice_versa():
    c = next(c for c in s.carregar_painel() if c['variante'] == 'primeira')
    for modo, outro in [('mencao', 'referente'), ('referente', 'mencao')]:
        r = s.medir(c, modo, 1, post=post({'resposta': c[f'ouro_{outro}'][0]}))
        a = s.aferir(c, r, modo, 1)
        assert a['literal'] and not a['alinhado_local']


def test_par_recalculado_do_http_nao_de_metrica_salva(registros):
    rs = deepcopy(registros)
    r = next(r for r in rs if r['id'] == 'P_primeira' and r['modo'] == 'mencao')
    c = next(c for c in s.carregar_painel() if c['id'] == r['id'])
    bruto = json.loads(r['http_bruto'])
    bruto['message']['content'] = json.dumps({'resposta': c['ouro_referente'][0]})
    r['http_bruto'] = json.dumps(bruto)
    r['alinhado_local'] = True
    a = s.resumir(rs)
    assert 'P_primeira' not in a['pares_alinhados']['1']
    assert 'P_primeira' in a['pares_alinhados']['2']


@pytest.mark.parametrize('p', [{'resposta': None}, {'resposta': True}, {'resposta': [], 'autoriza': True}])
def test_tipo_invalido_nao_e_coagido(p):
    c = s.carregar_painel()[0]
    a = s.aferir(c, s.medir(c, 'mencao', 1, post=post(p)), 'mencao', 1)
    assert not a['shape'] and not a['alinhado_local']


def test_finalizacao_incompleta_nao_admite_indeterminacao():
    c = next(c for c in s.carregar_painel() if c['referente_indeterminado'])
    r = s.medir(c, 'referente', 1, post=post({'resposta': 'indeterminado'}))
    bruto = json.loads(r['http_bruto'])
    bruto['done_reason'] = 'length'
    r['http_bruto'] = json.dumps(bruto)
    assert not s.aferir(c, r, 'referente', 1)['alinhado_local']

from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_pergunta_direta_v1 as s
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import post


def test_controle_congelado_mesmo_schema_e_fonte_sem_ouro():
    for c in s.carregar_painel():
        controle = s.preparar_requisicao(c, 'abstrato')
        assert controle == s.anterior.preparar_requisicao(c, 'referente')
        direto = s.preparar_requisicao(c, 'direto')
        for campo in ('format', 'options', 'model', 'stream'):
            assert direto[campo] == controle[campo]
        a, b = [json.loads(r['messages'][1]['content']) for r in (controle, direto)]
        assert a.pop('tarefa') == 'referente'
        assert b.pop('pergunta') == f"Qual é o nome do {c['relacao']['texto'].removeprefix('é o nome do ')}?"
        assert a == b
        for modo in s.MODOS:
            assert s.preparar_requisicao(c, modo) == s.preparar_requisicao(
                {**c, 'ouro_mencao': ['SEGREDO'], 'ouro_referente': ['SEGREDO'],
                 'referente_indeterminado': not c['referente_indeterminado'], 'familia': 'SEGREDO'}, modo)


@pytest.fixture(scope='module')
def registros():
    return [s.medir(c, m, rep, post=post({'resposta': 'indeterminado'
                                        if c['referente_indeterminado'] else c['ouro_referente'][0]}))
            for c, m, rep in s.sequencia(s.carregar_painel())]


def test_mesma_afericao_nos_dois_bracos_sem_promover_proposta(registros):
    a = s.resumir(registros)
    assert a['tipo'] == 'resumo_pergunta_direta'
    for c in a['por_caso'].values():
        assert c['abstrato'] == c['direto']
        for r in c['direto'].values():
            assert r['alinhado_local'] and all(r[k] is False for k in s.BASE)


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


def test_http_bruto_prevalece_sobre_metrica_salva(registros):
    rs = deepcopy(registros)
    r = rs[0]
    bruto = json.loads(r['http_bruto'])
    bruto['message']['content'] = json.dumps({'resposta': 'projeto'})
    r['http_bruto'] = json.dumps(bruto)
    r['alinhado_local'] = True
    a = s.resumir(rs)['por_caso'][r['id']][r['modo']][str(r['repeticao'])]
    assert a['literal'] and not a['alinhado_local']


def test_adaptador_nao_inventa_pergunta_para_relacao_diferente():
    c = s.carregar_painel()[0]
    c['relacao'] = {'inicio': 1, 'fim': 15, 'texto': c['texto'][1:15]}
    with pytest.raises(ValueError, match='fora do contrato'):
        s.preparar_requisicao(c, 'direto')


@pytest.mark.parametrize('modo', s.MODOS)
def test_indeterminado_nao_e_copia_nem_resposta_valida_para_nome_determinado(modo):
    for c in (s.carregar_painel()[0], s.carregar_painel()[3]):
        r = s.medir(c, modo, 1, post=post({'resposta': 'indeterminado'}))
        a = s.aferir(c, r, modo, 1)
        assert a['alinhado_local'] == c['referente_indeterminado']
        assert not a['literal']
        bruto = json.loads(r['http_bruto'])
        bruto['done_reason'] = 'length'
        r['http_bruto'] = json.dumps(bruto)
        assert not s.aferir(c, r, modo, 1)['alinhado_local']

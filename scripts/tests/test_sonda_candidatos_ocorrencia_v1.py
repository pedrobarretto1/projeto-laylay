from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_candidatos_ocorrencia_v1 as s
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import post


def test_entrada_fonte_preservada_sem_ouro_e_controle_congelado():
    cs=s.carregar_painel();assert len(cs)==28
    for c in cs:
        a=s.preparar_requisicao(c,'unico');b=s.preparar_requisicao(c,'candidatos')
        assert a==s.anterior.preparar_requisicao(c)
        assert a['messages'][1:]==b['messages'][1:]
        assert a['options']==b['options'] and a['model']==b['model']
        assert b==s.preparar_requisicao({**c,'esperado':'SEGREDO','situacao_esperada':'X','candidatos_esperados':['OURO']},'candidatos')


@pytest.mark.parametrize('proposta',[
    {'candidatos':['q0','q0'],'situacao':'indeterminado'},
    {'candidatos':['q999'],'situacao':'unico'},
    {'candidatos':[],'situacao':'unico'},
    {'candidatos':['q0'],'situacao':'nenhuma'},
    {'candidatos':[True],'situacao':'unico'},
    {'candidatos':['q0'],'situacao':'unico','autoriza_efeito':True},
])
def test_backend_nao_pode_violar_contrato(proposta):
    c=s.carregar_painel()[0]
    assert s.aferir(c,s.medir(c,'candidatos',1,post=post(proposta)),1,'candidatos')['shape'] is False


def test_candidato_unico_pode_continuar_indeterminado_sem_virar_autoridade():
    c=next(c for c in s.carregar_painel() if c['id']=='M7')
    r=s.medir(c,'candidatos',1,post=post({'candidatos':['q0'],'situacao':'indeterminado'}))
    a=s.aferir(c,r,1,'candidatos')
    assert a['shape'] and a['alvo_alinhado_local'] and a['candidatos_alinhados_local']
    assert all(a[k] is False for k in s.BASE)


@pytest.fixture(scope='module')
def registros():
    return [s.medir(c,m,rep,post=post({'ocorrencia_id':c['esperado']} if m=='unico' else
            {'candidatos':c['candidatos_esperados'],'situacao':c['situacao_esperada']}))
            for c,m,rep in s.sequencia(s.carregar_painel())]


@pytest.mark.parametrize('campo',['ordem','flag','rep','entrada'])
def test_auditoria_recusa_alteracoes(registros,campo):
    rs=deepcopy(registros)
    if campo=='ordem':rs.reverse()
    elif campo=='flag':rs[0]['autoriza_efeito']=True
    elif campo=='rep':rs[0]['repeticao']=True
    elif campo=='entrada':rs[0]['requisicao']['messages'][-1]['content']+='!'
    assert s.resumir(rs)['tipo']=='resumo_invalido'


def test_auditoria_recalcula_resposta_e_nao_acerto_salvo(registros):
    rs=deepcopy(registros);r=next(r for r in rs if r['id']=='L5' and r['modo']=='candidatos')
    bruto=json.loads(r['http_bruto']);bruto['message']['content']=json.dumps({'candidatos':['q0'],'situacao':'unico'})
    r['http_bruto']=json.dumps(bruto);r['afericao']={'alvo_alinhado_local':True}
    assert s.resumir(rs)['por_caso']['L5']['candidatos']['1']['alvo_alinhado_local'] is False

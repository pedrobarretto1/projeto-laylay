from copy import deepcopy
import json
import pytest

from scripts.analises import sonda_apoio_por_ocorrencia_v1 as s
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import post


def test_fonte_integral_controle_exato_e_sem_ouro():
    cs=s.carregar_painel();assert len(cs)==14
    for c in cs:
        controle=s.preparar_requisicao(c,'controle')
        assert controle==s.anterior.preparar_requisicao(c,'unico')
        for q in s.regioes(c):
            r=s.preparar_requisicao(c,q['id']);e=json.loads(r['messages'][-1]['content'])
            assert e.pop('ocorrencia_avaliada')==q
            assert e==json.loads(controle['messages'][-1]['content'])
            assert r==s.preparar_requisicao({**c,'esperado':'X','candidatos_esperados':[],'situacao_esperada':'X'},q['id'])


def test_repeticao_negacao_aninhamento_e_falta_informacao_sao_distintos():
    ix={c['id']:c for c in s.carregar_painel()}
    assert [s.esperado_par(ix['L3'],q) for q in ('q0','q1')]==['excluida','sustentada']
    assert [s.esperado_par(ix['L5'],q) for q in ('q0','q1')]==['insuficiente']*2
    assert s.esperado_par(ix['M1'],'q0')=='sustentada'
    assert s.esperado_par(ix['M2'],'q0')=='excluida' and s.esperado_par(ix['M2'],'q1')=='sustentada'
    assert s.esperado_par(ix['M7'],'q0')=='insuficiente'


@pytest.fixture(scope='module')
def registros():
    return [s.medir(c,q,rep,post=post({'ocorrencia_id':c['esperado']} if q=='controle' else
             {'ligacao':s.esperado_par(c,q)})) for c,q,rep in s.sequencia(s.carregar_painel())]


@pytest.mark.parametrize('campo',['ordem','flag','rep','ocorrencia','request','falta'])
def test_auditoria_rejeita_alteracao(registros,campo):
    rs=deepcopy(registros)
    if campo=='ordem':rs.reverse()
    elif campo=='flag':rs[0]['autoriza_efeito']=True
    elif campo=='rep':rs[0]['repeticao']=True
    elif campo=='ocorrencia':rs[0]['ocorrencia']='q999'
    elif campo=='request':rs[0]['requisicao']['messages'][-1]['content']+='!'
    elif campo=='falta':rs.pop()
    assert s.resumir(rs)['tipo']=='resumo_invalido'


@pytest.mark.parametrize('p',[{'ligacao':'sim'},{'ligacao':True},{'ligacao':'sustentada','autoriza_efeito':True}])
def test_backend_invalido_nao_vira_apoio(p):
    c=s.carregar_painel()[0]
    assert not s.aferir(c,s.medir(c,'q0',1,post=post(p)),'q0',1)['shape']


def test_vetor_exige_todos_pares_e_nao_promove_autoridade(registros):
    rs=deepcopy(registros);r=next(r for r in rs if r['id']=='L5' and r['ocorrencia']=='q1')
    bruto=json.loads(r['http_bruto']);bruto['message']['content']=json.dumps({'ligacao':'sustentada'})
    r['http_bruto']=json.dumps(bruto);r['par_alinhado_local']=True
    a=s.resumir(rs)
    assert a['vetor_exato_local']['L5']['1'] is False
    assert all(a[k] is False for k in s.BASE)
    assert a['agregacao_integrada'] is False

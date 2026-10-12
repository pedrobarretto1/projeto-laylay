from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_interferencia_contextual_v1 as s
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import medir


def test_intervencoes_preservam_foco_e_controles_historicos():
    ix = {c['id']:c for c in s.carregar_painel()}
    preparar = s.anterior.anterior.anterior.papel.preparar_entrada
    for ids in [('D0','DN','DA','DB'),('N0','NN','ND','NS','NR'),('C0','CN','CX')]:
        assert len({preparar(ix[i])['foco']['texto'] for i in ids}) == 1
        assert len({ix[i]['papel'] for i in ids}) == 1
    for x,y in [('NS','OS'),('NR','OR')]:
        assert ix[x]['texto'] == ix[y]['texto']
        assert preparar(ix[x])['foco']['inicio'] != preparar(ix[y])['foco']['inicio']
    antigos = {c['id']:c for c in s.anterior.carregar_painel()}
    for x,y in [('DA','H11'),('NS','H05'),('OS','H06'),('CX','H01')]:
        assert {k:v for k,v in ix[x].items() if k!='id'} == {k:v for k,v in antigos[y].items() if k!='id'}
    for i in ('T03','T04','T11','T14'): assert ix[i] == antigos[i]


@pytest.fixture(scope='module')
def blocos():
    return [medir(c,r) for c,r in s.anterior.sequencia(s.carregar_painel())]


@pytest.mark.parametrize('campo',['ordem','foco','fonte','flag','request','rep_bool','falta'])
def test_auditoria_rejeita_adulteracao(blocos,campo):
    bs = deepcopy(blocos)
    if campo=='ordem': bs.reverse()
    elif campo=='foco': bs[0]['primeira']['entrada_host']['foco']['inicio']+=1
    elif campo=='fonte': bs[0]['primeira']['entrada_host']['foco']['texto']='outra'
    elif campo=='flag': bs[0]['isolada']['autoriza_efeito']=True
    elif campo=='request': bs[0]['isolada']['requisicao']['messages'][-1]['content']+='!'
    elif campo=='rep_bool': bs[0]['repeticao']=True
    elif campo=='falta': bs.pop()
    assert s.resumir(bs)['tipo']=='resumo_invalido'


def test_placar_recalculado_do_bruto_sem_promocao(blocos):
    bs=deepcopy(blocos)
    raw=json.loads(bs[0]['isolada']['http_bruto'])
    raw['message']['content']=json.dumps({'papel':'operacao_mencionada'})
    bs[0]['isolada']['http_bruto']=json.dumps(raw)
    bs[0]['afericao']={'papel_alinhado':True}
    a=s.resumir(bs)
    assert a['por_caso']['D0']['1']['isolado']['papel_alinhado'] is False
    assert a['por_caso']['D0']['2']['isolado']['papel_alinhado'] is True
    assert all(a[k] is False for k in s.BASE)


def test_requisicao_sem_gabarito(blocos):
    c=s.carregar_painel()[0]
    falsa={**c,'papel':'SEGREDO','pista':'GABARITO'}
    r=s.anterior.anterior.preparar_requisicao(falsa,blocos[0]['primeira'],'papel_sem_trecho')
    assert r==blocos[0]['isolada']['requisicao']

from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_ligacao_ocorrencia_v1 as s
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import post


def test_entrada_nao_revela_foco_papel_gabarito_e_preserva_ocorrencias():
    cs=s.carregar_painel();assert len(cs)==20
    ix={c['id']:c for c in cs}
    for c in cs:
        r=s.preparar_requisicao(c)
        e=json.loads(r['messages'][-1]['content'])
        assert set(e)=={'fonte','aspas_sintaticas','relacao_proposta'}
        assert r==s.preparar_requisicao({**c,'esperado':'SEGREDO','papel':'GABARITO'})
    assert s.preparar_requisicao(ix['OR'])==s.preparar_requisicao(ix['NR'])
    e=json.loads(s.preparar_requisicao(ix['OR'])['messages'][-1]['content'])
    a,b=e['aspas_sintaticas']['regioes_entre_aspas']
    assert a['texto']==b['texto'] and a['inicio']!=b['inicio']


@pytest.fixture(scope='module')
def registros():
    return [s.medir(c,rep,post=post({'ocorrencia_id':c['esperado']})) for c,rep in s.sequencia(s.carregar_painel())]


@pytest.mark.parametrize('campo',['falta','ordem','rep_bool','request','flag'])
def test_auditoria_recusa_adulteracao(registros,campo):
    rs=deepcopy(registros)
    if campo=='falta':rs.pop()
    elif campo=='ordem':rs.reverse()
    elif campo=='rep_bool':rs[0]['repeticao']=True
    elif campo=='request':rs[0]['requisicao']['messages'][-1]['content']+='!'
    elif campo=='flag':rs[0]['autoriza_efeito']=True
    assert s.resumir(rs)['tipo']=='resumo_invalido'


@pytest.mark.parametrize('p',[{'ocorrencia_id':'q999'},{'ocorrencia_id':True},{'ocorrencia_id':'q0','autoriza_efeito':True}])
def test_schema_ignorado_pelo_backend_nao_passa(p):
    c=s.carregar_painel()[0]
    assert s.aferir(c,s.medir(c,1,post=post(p)),1)['shape'] is False


def test_acerto_local_nao_promove_semantica_ou_autoridade(registros):
    a=s.resumir(registros)
    assert a['qualificacao_semantica_comprovada'] is False
    for rodadas in a['por_caso'].values():
        for v in rodadas.values():
            assert v['alvo_alinhado_local'] is True
            assert all(v[k] is False for k in s.BASE)


def test_relacao_adulterada_nao_vira_selecao_valida():
    c=s.carregar_painel()[0];c['relacao']['inicio']+=1
    with pytest.raises(ValueError,match='literal'):s.preparar_requisicao(c)

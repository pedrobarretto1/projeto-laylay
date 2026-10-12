from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_evidencia_interferencia_v1 as s
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import post


@pytest.fixture(scope='module')
def blocos():
    bs=[]
    for c,rep,ordem in s.proponente.sequencia(s.carregar_painel()):
        # Seleção de outra ocorrência, como no diagnóstico; não corrigir com ouro.
        pred='o brinquedo se chama' if c['id']=='OR' else c['pista']
        p=s.proponente.selecao.medir_caso(c,'catalogado',rep,
                                       post=post({'papel':c['papel'],'predicado':pred}))
        bs.append(dict(id=c['id'],repeticao=rep,ordem=list(ordem),primeira=p,
                       segundas={m:s.proponente.medir_papel(c,p,m,post=post({'papel':c['papel']})) for m in ordem}))
    return bs


def test_contraste_muda_so_evidencia_sem_papel_anterior_ou_gabarito(blocos):
    cs={c['id']:c for c in s.carregar_painel()}
    for b in blocos[:12]:
        sem=deepcopy(b['segundas']['papel_sem_trecho']['requisicao'])
        com=deepcopy(b['segundas']['papel_com_trecho']['requisicao'])
        entrada=json.loads(com['messages'][-1]['content'])
        span=entrada.pop('evidencia_proposta')
        com['messages'][-1]['content']=json.dumps(entrada,ensure_ascii=False)
        assert sem==com
        c=cs[b['id']]
        assert c['texto'][span['inicio']:span['fim']]==span['texto']
        falso={**c,'papel':'SEGREDO','pista':'GABARITO'}
        assert s.proponente.preparar_requisicao(falso,b['primeira'],'papel_com_trecho')==b['segundas']['papel_com_trecho']['requisicao']
    a=s.resumir(blocos)
    assert a['por_caso']['OR']['1']['selecao_literal_valida'] is True
    assert a['por_caso']['OR']['1']['selecao_discriminativa_local'] is False
    assert all(a[k] is False for k in s.BASE)


@pytest.mark.parametrize('campo',['ordem','modo','span','rep_bool','flag','falta'])
def test_auditoria_rejeita_adulteracao(blocos,campo):
    bs=deepcopy(blocos)
    if campo=='ordem':bs[0]['ordem'].reverse()
    elif campo=='modo':bs[0]['segundas']['papel_com_trecho']['modo']='papel_sem_trecho'
    elif campo=='span':
        msg=bs[0]['segundas']['papel_com_trecho']['requisicao']['messages'][-1]
        e=json.loads(msg['content']);e['evidencia_proposta']['inicio']+=1
        msg['content']=json.dumps(e,ensure_ascii=False)
    elif campo=='rep_bool':bs[0]['repeticao']=True
    elif campo=='flag':bs[0]['segundas']['papel_com_trecho']['autoriza_efeito']=True
    elif campo=='falta':bs.pop()
    assert s.resumir(bs)['tipo']=='resumo_invalido'


def test_placar_recalculado_do_bruto(blocos):
    bs=deepcopy(blocos)
    r=bs[0]['segundas']['papel_com_trecho'];h=json.loads(r['http_bruto'])
    h['message']['content']=json.dumps({'papel':'operacao_mencionada'})
    r['http_bruto']=json.dumps(h);r['afericao']={'papel_alinhado':True}
    assert s.resumir(bs)['por_caso']['D0']['1']['bracos']['papel_com_trecho']['papel_alinhado'] is False

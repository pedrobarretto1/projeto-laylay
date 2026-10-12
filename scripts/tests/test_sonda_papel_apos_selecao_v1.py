from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_papel_apos_selecao_v1 as s


def post(proposta):
    return lambda *a,**k: SimpleNamespace(status_code=200,text=json.dumps({
        "done":True,"done_reason":"stop","message":{"content":json.dumps(proposta)}}))


def primeira(c,rep=1,predicado=None,papel=None):
    return s.selecao.medir_caso(c,"catalogado",rep,post=post({
        "predicado":c["pista"] if predicado is None else predicado,"papel":papel or c["papel"]}))


def test_segunda_nao_recebe_papel_anterior_ouro_ou_copia_reescrita():
    for c in s.carregar_painel():
        p=primeira(c,papel="indeterminado")
        a,b=[s.preparar_requisicao(c,p,m) for m in s.MODOS]
        entrada=json.loads(b["messages"][-1]["content"])
        e=entrada.pop("evidencia_proposta")
        assert entrada==json.loads(a["messages"][-1]["content"])
        assert e["texto"]==c["texto"][e["inicio"]:e["fim"]]==c["pista"]
        b["messages"][-1]["content"]=a["messages"][-1]["content"]
        assert a==b
        q=primeira(c,papel="nome_designacao")
        assert a==s.preparar_requisicao(c,q,s.MODOS[0])
        assert a==s.preparar_requisicao({**c,"papel":"SEGREDO","pista":"GABARITO"},p,s.MODOS[0])
        assert all(set(json.loads(m["content"]))=={"papel"} for m in a["messages"][2:-1:2])


def test_selecao_invalida_bloqueia_so_braco_dependente_sem_chamar_modelo():
    c=s.carregar_painel()[0];p=primeira(c,predicado="")
    def proibido(*a,**k):raise AssertionError("nao deve chamar")
    r=s.medir_papel(c,p,"papel_com_trecho",post=proibido)
    assert s.aferir_papel(c,p,r)["bloqueado"]
    assert s.medir_papel(c,p,"papel_sem_trecho",post=post({"papel":c["papel"]}))["http_status"]==200
    with pytest.raises(ValueError):s.aferir_papel(c,p,{**r,"http_status":200})


def test_pista_correta_nao_corrige_papel_proposto_pelo_modelo():
    c=s.carregar_painel()[0];p=primeira(c)
    r=s.medir_papel(c,p,"papel_com_trecho",post=post({"papel":"expressao_sem_operacao"}))
    a=s.aferir_papel(c,p,r)
    assert a["shape"] and not a["papel_alinhado"] and not a["conjunto_discriminativo_local"]
    assert all(a[k] is False for k in s.BASE)


@pytest.fixture(scope="module")
def blocos():
    bs=[]
    for c,rep,ordem in s.sequencia(s.carregar_painel()):
        p=primeira(c,rep)
        bs.append({"id":c["id"],"repeticao":rep,"ordem":list(ordem),"primeira":p,
            "segundas":{m:s.medir_papel(c,p,m,post=post({"papel":c["papel"]})) for m in ordem}})
    return bs


@pytest.mark.parametrize("tipo",["falta","ordem","primeira","requisicao","evidencia","rep_bool","flag","nan","http"])
def test_auditoria_recusa_adulteracao(blocos,tipo):
    bs=deepcopy(blocos);r=bs[0]["segundas"]["papel_com_trecho"]
    if tipo=="falta":bs.pop()
    elif tipo=="ordem":bs.reverse()
    elif tipo=="primeira":bs[0]["primeira"]["id"]="T99"
    elif tipo=="requisicao":r["requisicao"]["messages"][0]["content"]+="!"
    elif tipo=="evidencia":
        e=json.loads(r["requisicao"]["messages"][-1]["content"]);e["evidencia_proposta"]["texto"]="inventado"
        r["requisicao"]["messages"][-1]["content"]=json.dumps(e)
    elif tipo=="rep_bool":r["repeticao"]=True
    elif tipo=="flag":r["autoriza_efeito"]=True
    elif tipo=="nan":r["duracao_consulta_s"]=float("nan")
    elif tipo=="http":r["erro_consulta"]="Timeout"
    assert s.resumir(bs)["tipo"]=="resumo_invalido"


def test_resumo_recalcula_tres_bracos_sem_promover(blocos):
    a=s.resumir(blocos)
    assert a["blocos"]==16
    assert all(a["bracos"][m][str(r)]["conjunto_discriminativo_local"]==8
        for m in ("conjunto",*s.MODOS) for r in (1,2))
    assert all(a[k] is False for k in s.BASE)

from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_transferencia_papel_isolado_v1 as s


def post(p):
    return lambda *a,**k:SimpleNamespace(status_code=200,text=json.dumps({"done":True,"done_reason":"stop","message":{"content":json.dumps(p)}}))


def medir(c,rep):
    p=s.anterior.selecao.medir_caso(c,"catalogado",rep,post=post({"papel":c["papel"],"predicado":c["pista"]}))
    r=s.anterior.medir_papel(c,p,"papel_sem_trecho",post=post({"papel":c["papel"]}))
    return {"id":c["id"],"repeticao":rep,"primeira":p,"isolada":r}


def test_painel_novo_e_historicos_separados_com_identidade_de_ocorrencia():
    cs=s.carregar_painel()
    assert len(cs)==20 and sum(c["id"].startswith("H") for c in cs)==16
    ix={c["id"]:c for c in cs}; preparar=s.anterior.anterior.papel.preparar_entrada
    a,b=[preparar(ix[i])["foco"] for i in ("H05","H06")]
    assert a["texto"]==b["texto"] and a["inicio"]!=b["inicio"]
    for c in cs:
        assert c["texto"].startswith(s.anterior.selecao.PREFIXO) and c["texto"].endswith(s.anterior.selecao.SUFIXO)
        assert c["pista"] in [i["texto"] for i in s.anterior.selecao.catalogar(c)]


def test_isolado_nao_depende_de_ouro_ou_papel_primeiro():
    c=s.carregar_painel()[0];b=medir(c,1)
    r=b["isolada"]["requisicao"]
    falso={**c,"papel":"SEGREDO","pista":"GABARITO"}
    assert r==s.anterior.preparar_requisicao(falso,b["primeira"],"papel_sem_trecho")
    assert "evidencia_proposta" not in json.loads(r["messages"][-1]["content"])


@pytest.fixture(scope="module")
def blocos():return [medir(c,rep) for c,rep in s.sequencia(s.carregar_painel())]


@pytest.mark.parametrize("tipo",["falta","ordem","id","rep_bool","host","request","modo","flag"])
def test_replay_recusa_modificacoes(blocos,tipo):
    bs=deepcopy(blocos)
    if tipo=="falta":bs.pop()
    elif tipo=="ordem":bs.reverse()
    elif tipo=="id":bs[0]["id"]="X"
    elif tipo=="rep_bool":bs[0]["repeticao"]=True
    elif tipo=="host":bs[0]["primeira"]["entrada_host"]["foco"]["inicio"]+=1
    elif tipo=="request":bs[0]["isolada"]["requisicao"]["messages"][-1]["content"]+="!"
    elif tipo=="modo":bs[0]["isolada"]["modo"]="papel_com_trecho"
    elif tipo=="flag":bs[0]["isolada"]["autoriza_efeito"]=True
    assert s.resumir(bs)["tipo"]=="resumo_invalido"


def test_placar_por_grupo_sem_confiar_em_afirmacao_salva(blocos):
    bs=deepcopy(blocos)
    for b in bs:b["afericao"]={"papel_alinhado":False}
    a=s.resumir(bs)
    for g,n in (("novos",16),("historicos",4)):
        for m in ("conjunto","isolado"):
            for rep in (1,2):assert a["grupos"][g][m][str(rep)]["papel_alinhado"]==n
    assert all(a[k] is False for k in s.BASE)

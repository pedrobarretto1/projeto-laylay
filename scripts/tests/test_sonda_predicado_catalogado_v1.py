from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_predicado_catalogado_v1 as s


def medir(c, m, rep=1, proposta=None):
    p = proposta or {"papel": c["papel"], "predicado": c["pista"]}
    return s.medir_caso(c, m, rep, post=lambda *a, **k: SimpleNamespace(
        status_code=200, text=json.dumps({"done": True, "done_reason": "stop", "message": {"content": json.dumps(p)}})))


def test_catalogo_independe_do_ouro_e_reusa_materializacao_externa():
    for c in s.carregar_painel():
        itens = s.catalogar(c)
        assert itens == s.catalogar({**c, "pista": "SEGREDO", "papel": "FALSO"})
        assert c["pista"] in [i["texto"] for i in itens]
        foco = s.anterior.papel.preparar_entrada(c)["foco"]
        for i in itens:
            assert i["texto"] == c["texto"][i["inicio"]:i["fim"]]
            assert i["fim"] <= foco["inicio"] or i["inicio"] >= foco["fim"]
            assert s._ancorar_trecho(c["texto"], i["texto"]) == i["texto"]


def test_so_schema_do_predicado_muda_sem_gold_no_prompt():
    for c in s.carregar_painel():
        a, b = [s.preparar_requisicao(c, m) for m in s.MODOS]
        assert a == s.anterior.preparar_requisicao(c, "com_exemplos")
        assert b == s.preparar_requisicao({**c, "pista": "SEGREDO", "papel": "FALSO"}, "catalogado")
        enum = b["format"]["properties"]["predicado"].pop("enum")
        assert b == a and enum == [""] + [i["texto"] for i in s.catalogar(c)]


def test_selecionar_tudo_nao_passa_discriminacao():
    for c in s.carregar_painel():
        a = s.controle_todos(c)
        assert a["pista"] and a["inclui_distrator"] and not a["selecao_discriminativa_local"]
        candidatos = [i for i in s.catalogar(c) if c["pista"] in i["texto"] and (i["inicio"] < len(s.PREFIXO) or i["fim"] > len(c["texto"])-len(s.SUFIXO))]
        if candidatos:
            r = medir(c, "catalogado", proposta={"papel": c["papel"], "predicado": candidatos[0]["texto"]})
            a = s.aferir_caso(c,r)
            assert a["conjunto"] and not a["conjunto_discriminativo_local"]


def test_schema_ignorado_nao_contorna_guarda():
    c = s.carregar_painel()[0]
    # Existe como substring, mas não nos limites dos tokens canônicos.
    r = medir(c,"catalogado",proposta={"papel":c["papel"],"predicado":"minicurs"})
    a=s.aferir_caso(c,r)
    assert not a["respeita_catalogo"] and not a["vinculo"] and not a["conjunto"]
    foco=s.anterior.papel.preparar_entrada(c)["foco"]["texto"]
    a=s.aferir_caso(c,medir(c,"catalogado",proposta={"papel":c["papel"],"predicado":foco}))
    assert not a["vinculo"] and a["papel_alinhado"]


def test_pista_literal_nao_prova_papel_e_abstencao_nao_prova_ausencia():
    c=s.carregar_painel()[0]
    a=s.aferir_caso(c,medir(c,"catalogado",proposta={"papel":"indeterminado","predicado":c["pista"]}))
    assert a["selecao_discriminativa_local"] and not a["papel_alinhado"] and not a["conjunto_discriminativo_local"]
    a=s.aferir_caso(c,medir(c,"catalogado",proposta={"papel":c["papel"],"predicado":""}))
    assert a["respeita_catalogo"] and not a["vinculo"]
    assert all(a[k] is False for k in s.BASE)


@pytest.fixture(scope="module")
def completos():
    return [medir(c,m,r) for c,m,r in s.sequencia(s.carregar_painel())]


@pytest.mark.parametrize("tipo", ["falta","duplicata","ordem","catalogo","request","host","flag","rep_bool","nan","http"])
def test_replay_recusa_adulteracao(completos,tipo):
    rs=deepcopy(completos)
    if tipo=="falta":rs.pop()
    elif tipo=="duplicata":rs.append(rs[0])
    elif tipo=="ordem":rs.reverse()
    elif tipo=="catalogo":rs[0]["catalogo_host"][0]["inicio"] = 0.0
    elif tipo=="request":rs[0]["requisicao"]["messages"][-1]["content"] += "!"
    elif tipo=="host":rs[0]["entrada_host"]["foco"]["inicio"] += 1
    elif tipo=="flag":rs[0]["autoriza_efeito"] = True
    elif tipo=="rep_bool":rs[0]["repeticao"] = True
    elif tipo=="nan":rs[0]["duracao_consulta_s"] = float("nan")
    elif tipo=="http":rs[0]["erro_consulta"] = "Timeout"
    assert s.resumir(rs)["tipo"]=="resumo_invalido"


def test_resumo_reaferido_e_fonte_grande_recusada(completos):
    rs=deepcopy(completos)
    for r in rs:r["afericao"]={"conjunto_discriminativo_local":False}
    a=s.resumir(rs)
    assert a["consultas"]==32
    assert all(a["bracos"][m][str(r)]["conjunto_discriminativo_local"]==8 for m in s.MODOS for r in (1,2))
    c=s.carregar_painel()[0]
    with pytest.raises(ValueError,match="limite"):
        s.catalogar({**c,"texto":c["texto"]+" extra"*65})

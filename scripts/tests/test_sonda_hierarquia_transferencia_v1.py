from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_hierarquia_transferencia_v1 as s


def medir(c, m, rep, proposta=None):
    p = proposta or {"papel": c["papel"], "predicado": c["pista"]}
    return s.anterior.medir_caso(c, modo=m, repeticao=rep, post=lambda *a, **k: SimpleNamespace(
        status_code=200, text=json.dumps({"done": True, "done_reason": "stop", "message": {"content": json.dumps(p)}})))


def test_painel_novo_balanceado_com_referencias_literais_sem_vazamento():
    cs = s.carregar_painel()
    for c in cs:
        for m in s.MODOS:
            r = s.anterior.preparar_requisicao(c, m)
            sem_gold = {**c, "papel": "SENTINELA", "pista": "SEGREDO"}
            assert r == s.anterior.preparar_requisicao(sem_gold, m)
            a = s.anterior.aferir_caso(c, medir(c, m, 1))
            assert a["conjunto"]
            assert all(a[k] is False for k in s.BASE)
    a, b = [s.anterior.anterior.papel.preparar_entrada(cs[i]) for i in (4, 5)]
    assert a["foco"]["texto"] == b["foco"]["texto"]
    assert a["foco"]["inicio"] != b["foco"]["inicio"]


def test_hierarquia_reusa_proponente_sem_alterar_host_ou_demo_resposta():
    for c in s.carregar_painel():
        a, b = [s.anterior.preparar_requisicao(c, m) for m in s.MODOS]
        assert a["messages"][0] == b["messages"][0]
        assert a["messages"][2:-1:2] == b["messages"][2:-1:2]
        assert {k:v for k,v in a.items() if k != "messages"} == {k:v for k,v in b.items() if k != "messages"}
        for x, y in zip(a["messages"][1::2], b["messages"][1::2]):
            plain, tree = json.loads(x["content"]), json.loads(y["content"])
            assert plain == {k:v for k,v in tree.items() if k != "hierarquia_sintatica_do_foco"}


@pytest.fixture(scope="module")
def completos():
    return [medir(c, m, rep) for c, m, rep in s.sequencia(s.carregar_painel())]


@pytest.mark.parametrize("tipo", ["falta", "duplicata", "ordem", "modo", "rep_bool", "host", "request", "autoridade", "http"])
def test_resumo_fail_closed(completos, tipo):
    rs = deepcopy(completos)
    if tipo == "falta": rs.pop()
    elif tipo == "duplicata": rs.append(rs[0])
    elif tipo == "ordem": rs.reverse()
    elif tipo == "modo": rs[0]["modo"] = "id_uniforme"
    elif tipo == "rep_bool": rs[0]["repeticao"] = True
    elif tipo == "host": rs[0]["entrada_host"]["foco"]["inicio"] += 1
    elif tipo == "request": rs[0]["requisicao"]["messages"][-1]["content"] += "!"
    elif tipo == "autoridade": rs[0]["autoriza_efeito"] = True
    elif tipo == "http": rs[0]["erro_consulta"] = "Timeout"
    assert s.resumir(rs)["tipo"] == "resumo_invalido"


def test_resumo_recalcula_brutos_sem_confiar_em_metricas_salvas(completos):
    rs = deepcopy(completos)
    for r in rs: r["afericao"] = {"conjunto": False, "autoriza_efeito": True}
    a = s.resumir(rs)
    assert a["consultas"] == 64
    assert all(a["bracos"][m][str(rep)]["conjunto"] == 16 for m in s.MODOS for rep in (1, 2))
    assert all(a[k] is False for k in s.BASE)


def test_papel_correto_nao_conserta_predicado_sobreposto():
    c = s.carregar_painel()[0]
    foco = s.anterior.anterior.papel.preparar_entrada(c)["foco"]["texto"]
    r = medir(c, "hierarquia", 1, {"papel": c["papel"], "predicado": foco})
    a = s.anterior.aferir_caso(c, r)
    assert a["papel_alinhado"] and not a["vinculo"] and not a["conjunto"]

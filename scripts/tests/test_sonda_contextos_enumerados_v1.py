from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_contextos_enumerados_v1 as sonda


CASOS, OURO, PARES = sonda.carregar_painel()


def inventario(caso):
    host = sonda.etapas.vinculo.preparar_entrada(caso)
    return host, sonda.enumerar_externos(caso, host)


def proposta_todos(caso, modo):
    _, itens = inventario(caso)
    if modo == "ids_contextos":
        return {"evidencias": [i["id"] for i in itens]}
    return {"evidencias": [{"inicio": i["inicio_token"], "fim": i["fim_token"]} for i in itens]}


def resposta(proposta, motivo="stop", done=True, status=200):
    return SimpleNamespace(status_code=status, text=json.dumps({"done": done, "done_reason": motivo,
        "message": {"content": json.dumps(proposta, ensure_ascii=False)}}))


def medir(caso, modo, proposta=None, **opcoes):
    p = proposta_todos(caso, modo) if proposta is None else proposta
    return sonda.medir_caso(caso, modo=modo, post=lambda *a, **k: resposta(p, **opcoes))


def sinteticos():
    return [medir(c, m) for c in CASOS for m in sonda.MODOS]


@pytest.mark.parametrize("c", CASOS, ids=lambda c: c["id"])
def test_enumeracao_completa_posicional_autentica_disjunta_e_sem_gold(c):
    host, itens = inventario(c)
    foco, tokens = host["foco"], host["tokens"]
    enumerados = [i for item in itens for i in range(item["inicio_token"], item["fim_token"])]
    externos = [i for i, t in enumerate(tokens) if t["fim"] <= foco["inicio"] or t["inicio"] >= foco["fim"]]
    assert enumerados == externos
    assert [item["id"] for item in itens] == [f"e{i}" for i in range(len(itens))]
    for item in itens:
        assert item["texto"] == c["texto"][item["inicio"]:item["fim"]]
        assert item["fim"] <= foco["inicio"] or item["inicio"] >= foco["fim"]
    # Gold/nomes de fixture não participam da geometria.
    assert sonda.enumerar_externos({**c, "id": "OUTRO", "ancoras": [["inventado"]]}, host) == itens


def test_payload_sem_pistas_e_controle_indices_identico():
    for c in CASOS:
        a = sonda.preparar_requisicao(c, "indices")
        b = sonda.preparar_requisicao(c, "ids_contextos")
        assert a == sonda.controle.preparar_requisicao(c, "indices")
        entrada_a = json.loads(a["messages"][1]["content"])
        entrada_b = json.loads(b["messages"][1]["content"])
        assert entrada_b.pop("contextos_externos") == [
            {"id": item["id"], "texto": item["texto"]} for item in inventario(c)[1]]
        assert entrada_a == entrada_b
        assert not {"alvo_literal_solicitado", "ancoras", "papel", "id", "esperado"} & entrada_a.keys()
        assert a["options"] == b["options"] and isinstance(b["format"], dict)
        assert "Use inicio inclusivo" not in sonda.SISTEMA_IDS
        assert "Nao copie texto" in sonda.SISTEMA_IDS


@pytest.mark.parametrize("m", sonda.MODOS)
def test_todos_materializa_mas_nao_demonstra_escolha_ou_semantica(m):
    for c in CASOS:
        a = sonda.aferir_caso(c, medir(c, m), OURO[c["id"]])
        assert a["selecao_literal_concluida"] is True
        assert a["cobertura_lexical_concluida"] is True
        assert a["selecionou_todos_contextos"] is True
        assert all(a[k] is False for k in sonda.BASE)
    baseline = sonda.medir_controle_todos(CASOS, OURO)
    assert baseline["sem_modelo"] is True
    assert baseline["casos"] == baseline["literais_validos"] == baseline["cobertura_lexical"] == 20


@pytest.mark.parametrize("p,estado", [
    ({"evidencias": []}, "selecao_vazia_revisao_pendente"),
    ({"evidencias": ["e0"]}, "selecao_literal_revisao_pendente"),
    ({"evidencias": ["e0", "e1"]}, "selecao_literal_revisao_pendente"),
    ({"evidencias": ["e1", "e0"]}, "intervalos_invalidos"),
    ({"evidencias": ["e0", "e0"]}, "intervalos_invalidos"),
    ({"evidencias": ["e0", "e99"]}, "id_contexto_invalido"),
    ({"evidencias": [" e0"]}, "id_contexto_invalido"),
    ({"evidencias": ["tem o nome"]}, "id_contexto_invalido"),
    ({"evidencias": [False]}, "id_contexto_invalido"),
    ({"evidencias": [0]}, "id_contexto_invalido"),
    ({"evidencias": [{"inicio": 0, "fim": 2}]}, "id_contexto_invalido"),
    ({"evidencias": ["e0"], "papel": "nome"}, "proposta_invalida"),
    ({"evidencias": ["e0", "e1", "e2"]}, "proposta_invalida"),
])
def test_ids_tipados_unicos_ordenados_e_recusa_atomica_sem_reparo(p, estado):
    c = CASOS[0]
    host, itens = inventario(c)
    conf = sonda.conferir_ids(c, host, itens, p)
    assert conf["estado"] == estado
    assert all(conf[k] is False for k in sonda.BASE)
    if estado not in {"selecao_literal_revisao_pendente", "selecao_vazia_revisao_pendente"}:
        assert conf["evidencias"] == [] and conf["evidencia_literal_externa"] is False


def test_inventario_tamper_recusado_ate_com_proposta_vazia():
    c = CASOS[0]
    host, itens = inventario(c)
    itens[0]["texto"] = "tem o nome"
    assert sonda.conferir_ids(c, host, itens, {"evidencias": []})["estado"] == "inventario_adulterado"
    host["tokens"][0]["inicio"] = False
    assert sonda.conferir_ids(c, host, itens, {"evidencias": []})["estado"] == "entrada_adulterada"
    with pytest.raises(ValueError):
        sonda.enumerar_externos(c, host)


def test_id_literal_pontuacao_nao_apoia_papel():
    c = CASOS[0]
    a = sonda.aferir_caso(c, medir(c, "ids_contextos", {"evidencias": ["e1"]}), OURO[c["id"]])
    assert a["selecao_literal_concluida"] is True and a["cobertura_lexical_concluida"] is False
    assert a["selecionou_todos_contextos"] is False


@pytest.mark.parametrize("m", sonda.MODOS)
@pytest.mark.parametrize("opcoes", [{"motivo": "length"}, {"done": False}, {"status": 500}])
def test_http_e_finalizacao_exigidos_antes_de_credito(m, opcoes):
    c = CASOS[0]
    a = sonda.aferir_caso(c, medir(c, m, **opcoes), OURO[c["id"]])
    assert a["selecao_literal_concluida"] is False and a["cobertura_lexical_concluida"] is False


def test_replay_recalcula_http_bruto_nao_confia_em_score_salvo():
    rs = sinteticos()
    for r in rs:
        r["afericao"] = {"selecao_literal_concluida": False}
    resumo = sonda.resumir(CASOS, rs, OURO)
    for b in resumo["bracos"].values():
        assert b["casos"] == b["consultas"] == b["cobertura_lexical_concluida"] == 20
        assert b["pares_cobertura_lexical_concluida"] == 8
        assert b["selecionou_todos_contextos"] == 20
    assert resumo["controle_todos_sem_modelo"]["cobertura_lexical"] == 20


@pytest.mark.parametrize("tipo", ["ausente", "duplicata", "request", "host", "inventario", "flag", "nan",
                                 "contradicao", "status", "caso", "ouro", "transbordamento"])
def test_resumo_recusa_adulteracao_e_denominador_incompleto(tipo):
    cs, rs, ouro = deepcopy(CASOS), sinteticos(), deepcopy(OURO)
    if tipo == "ausente":
        rs.pop()
    elif tipo == "duplicata":
        rs.append(deepcopy(rs[0]))
    elif tipo == "request":
        rs[1]["requisicao"]["messages"][1]["content"] = "gold"
    elif tipo == "host":
        rs[0]["entrada_host"]["tokens"][0]["inicio"] = False
    elif tipo == "inventario":
        rs[1]["inventario_host"][0]["fim_token"] = True
    elif tipo == "flag":
        rs[0]["autoriza_efeito"] = True
    elif tipo == "nan":
        rs[0]["duracao_consulta_s"] = float("nan")
    elif tipo == "contradicao":
        rs[1]["erro_consulta"] = "TimeoutError"
    elif tipo == "status":
        rs[1]["http_status"] = True
    elif tipo == "caso":
        cs[0]["texto"] += " adulterado"
    elif tipo == "ouro":
        ouro[cs[0]["id"]]["ancoras"] = [["botão"]]
    else:
        for r in rs:
            r["duracao_consulta_s"] = 1e308
    assert sonda.resumir(cs, rs, ouro)["tipo"] == "resumo_invalido"


def test_cli_quarenta_chamadas_sem_segunda_etapa_e_exclusivo(monkeypatch, tmp_path):
    chamadas = []
    original = sonda.medir_caso
    def medir_fake(c, *, modo):
        chamadas.append((c["id"], modo))
        return original(c, modo=modo, post=lambda *a, **k: resposta(proposta_todos(c, modo)))
    monkeypatch.setattr(sonda, "medir_caso", medir_fake)
    monkeypatch.setattr(sonda.etapas.coordenadas, "digest_modelo", lambda: "digest_teste")
    saida = tmp_path / "contextos.jsonl"
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    antes = saida.read_bytes()
    rows = [json.loads(l) for l in antes.splitlines()]
    assert len(rows) == 42 and len(chamadas) == 40
    assert sum(chamadas[i*2][1] == "indices" for i in range(20)) == 10
    assert rows[0]["referencias_host_pre_consulta"] == OURO
    assert rows[0]["controle_todos_pre_consulta"]["cobertura_lexical"] == 20
    assert rows[0]["segunda_etapa_executada"] is False
    with pytest.raises(FileExistsError):
        sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 40


def test_timeout_nao_recebe_credito_e_preserva_erro():
    def falha(*a, **k):
        raise TimeoutError
    c = CASOS[0]
    r = sonda.medir_caso(c, modo="ids_contextos", post=falha)
    assert r["erro_consulta"] == "TimeoutError" and "http_bruto" not in r
    assert sonda.aferir_caso(c, r, OURO[c["id"]])["cobertura_lexical_concluida"] is False


def test_modo_invalido_nao_consulta():
    with pytest.raises(ValueError):
        sonda.medir_caso(CASOS[0], modo="outro", post=lambda *a, **k: pytest.fail("não consultar"))

from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_papel_contexto_explicito_v1 as sonda


CASOS, OURO, PARES = sonda.carregar_painel()


def resposta(proposta, motivo="stop", done=True, status=200):
    return SimpleNamespace(status_code=status, text=json.dumps({"done": done, "done_reason": motivo,
        "message": {"content": json.dumps(proposta, ensure_ascii=False)}}))


def medir(caso, modo, proposta=None, **opcoes):
    p = {"papel": OURO[caso["id"]]["papel"]} if proposta is None else proposta
    return sonda.medir_caso(caso, modo=modo, post=lambda *a, **k: resposta(p, **opcoes))


def sinteticos():
    return [medir(c, m) for c in CASOS for m in sonda.MODOS]


def test_uma_diferenca_de_entrada_prompt_schema_opcoes_preservados():
    for c in CASOS:
        a = sonda.preparar_requisicao(c, "fonte_integral")
        b = sonda.preparar_requisicao(c, "contexto_explicito")
        entrada_a = json.loads(a["messages"][1]["content"])
        entrada_b = json.loads(b["messages"][1]["content"])
        assert entrada_a == sonda.papel.preparar_entrada(c)
        host = sonda.etapas.vinculo.preparar_entrada(c)
        assert entrada_b.pop("contextos_externos") == [
            {"id": item["id"], "texto": item["texto"]} for item in sonda.enumerados.enumerar_externos(c, host)]
        assert entrada_a == entrada_b
        assert not {"tokens", "ancoras", "esperado", "id", "papel", "alvo_literal_solicitado"} & entrada_a.keys()
        assert a["messages"][0] == b["messages"][0] == {"role": "system", "content": sonda.papel.SISTEMA}
        assert a["format"] == b["format"] == sonda.papel.FORMATO
        assert a["options"] == b["options"]


@pytest.mark.parametrize("c", CASOS, ids=lambda c: c["id"])
@pytest.mark.parametrize("m", sonda.MODOS)
def test_papel_local_alinhado_nao_promove_referente_vigencia_ou_efeito(c, m):
    a = sonda.aferir_caso(c, medir(c, m), OURO[c["id"]])
    assert a["saida_valida_concluida"] is True and a["papel_alinhado_concluido"] is True
    assert all(a[k] is False for k in sonda.BASE)
    assert a["estado_papel"] == "papel_proposto_revisao_pendente"


@pytest.mark.parametrize("m", sonda.MODOS)
@pytest.mark.parametrize("opcoes", [{"motivo": "length"}, {"done": False}, {"status": 500}])
def test_http_e_finalizacao_exigidos_antes_de_credito(m, opcoes):
    c = CASOS[0]
    a = sonda.aferir_caso(c, medir(c, m, **opcoes), OURO[c["id"]])
    assert a["saida_valida_concluida"] is False and a["papel_alinhado_concluido"] is False


@pytest.mark.parametrize("proposta", [
    {}, {"papel": None}, {"papel": False}, {"papel": 1}, {"papel": "NOME"},
    {"papel": "nome_designacao", "autoriza_efeito": True},
    {"papel": "nome_designacao", "evidencias": []}, ["nome_designacao"],
])
def test_shape_recusado_sem_reparo_nem_rotulo_emprestado(proposta):
    c = CASOS[0]
    a = sonda.aferir_caso(c, medir(c, "contexto_explicito", proposta), OURO[c["id"]])
    assert a["saida_valida"] is False and a["papel_alinhado_concluido"] is False
    assert a["papel_proposto"] is None


def test_role_valido_mas_errado_nao_e_acerto():
    c = CASOS[0]
    a = sonda.aferir_caso(c, medir(c, "contexto_explicito", {"papel": "operacao_mencionada"}), OURO[c["id"]])
    assert a["saida_valida_concluida"] is True and a["papel_alinhado_concluido"] is False
    assert all(a[k] is False for k in sonda.BASE)


def test_indeterminado_nao_e_fallback_que_serve_para_qualquer_caso():
    cs = [CASOS[0], next(c for c in CASOS if c["id"] == "Q08A")]
    for c in cs:
        a = sonda.aferir_caso(c, medir(c, "contexto_explicito", {"papel": "indeterminado"}), OURO[c["id"]])
        assert a["papel_alinhado_concluido"] == (c["id"] == "Q08A")
        assert a["semantica_verificada"] is False


def test_replay_recalcula_http_bruto_nao_confia_em_score_salvo():
    rs = sinteticos()
    for r in rs:
        r["afericao"] = {"papel_alinhado_concluido": False}
    resumo = sonda.resumir(CASOS, rs, OURO)
    for b in resumo["bracos"].values():
        assert b["casos"] == b["consultas"] == b["papel_alinhado_concluido"] == 20
        assert b["pares_contextuais_alinhados_concluidos"] == 8
        assert sum(p["total"] for p in b["por_papel"].values()) == 20
        assert sum(sum(m.values()) for m in b["confusao"].values()) == 20
    assert resumo["comparacao_pareada"] == {"ganhos": 0, "perdas": 0, "ambos_alinhados": 20, "nenhum_alinhado": 0}


def test_ganho_e_perda_separados_e_par_exige_ambos_os_lados():
    rs = sinteticos()
    errado = {"papel": "expressao_sem_operacao"}
    rs[0] = medir(CASOS[0], "fonte_integral", errado)
    rs[3] = medir(CASOS[1], "contexto_explicito", errado)
    resumo = sonda.resumir(CASOS, rs, OURO)
    assert resumo["comparacao_pareada"] == {"ganhos": 1, "perdas": 1, "ambos_alinhados": 18, "nenhum_alinhado": 0}
    assert all(b["pares_contextuais_alinhados_concluidos"] == 7 for b in resumo["bracos"].values())
    assert {m["id"] for m in resumo["mudancas"]} == {"Q01A", "Q02B"}


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
        ouro[cs[0]["id"]]["papel"] = "indeterminado"
    else:
        for r in rs:
            r["duracao_consulta_s"] = 1e308
    assert sonda.resumir(cs, rs, ouro)["tipo"] == "resumo_invalido"


def test_cli_quarenta_classificacoes_sem_seletor_e_exclusivo(monkeypatch, tmp_path):
    chamadas = []
    original = sonda.medir_caso
    def medir_fake(c, *, modo):
        chamadas.append((c["id"], modo))
        return original(c, modo=modo, post=lambda *a, **k: resposta({"papel": OURO[c["id"]]["papel"]}))
    monkeypatch.setattr(sonda, "medir_caso", medir_fake)
    monkeypatch.setattr(sonda.etapas.coordenadas, "digest_modelo", lambda: "digest_teste")
    saida = tmp_path / "papeis.jsonl"
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    antes = saida.read_bytes()
    rows = [json.loads(l) for l in antes.splitlines()]
    assert len(rows) == 42 and len(chamadas) == 40
    assert sum(chamadas[i*2][1] == "fonte_integral" for i in range(20)) == 10
    assert rows[0]["referencias_host_pre_consulta"] == OURO
    assert rows[0]["seletor_modelo_executado"] is False
    assert rows[0]["diferenca_somente_campo_contextos_externos"] is True
    with pytest.raises(FileExistsError):
        sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 40


def test_timeout_nao_recebe_credito_e_preserva_erro():
    def falha(*a, **k):
        raise TimeoutError
    c = CASOS[0]
    r = sonda.medir_caso(c, modo="contexto_explicito", post=falha)
    assert r["erro_consulta"] == "TimeoutError" and "http_bruto" not in r
    assert sonda.aferir_caso(c, r, OURO[c["id"]])["papel_alinhado_concluido"] is False


def test_modo_invalido_nao_consulta():
    with pytest.raises(ValueError):
        sonda.medir_caso(CASOS[0], modo="outro", post=lambda *a, **k: pytest.fail("não consultar"))

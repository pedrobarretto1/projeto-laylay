import json
from copy import deepcopy
from types import SimpleNamespace
import sys

import pytest

from scripts.analises import sonda_extracao_literal_v1 as sonda


CASOS = json.loads(sonda.PAINEL.read_text(encoding="utf-8"))["casos"]


def resposta(proposta, *, motivo="stop", done=True):
    return SimpleNamespace(status_code=200, text=json.dumps({"message": {"content": json.dumps(proposta)},
                                                           "done": done, "done_reason": motivo}))


def medir(c, m="schema_restritivo", *, proposta=None, **kwargs):
    return sonda.medir_caso(c, modo=m, post=lambda *a, **k:
        resposta(c["esperado"] if proposta is None else proposta, **kwargs))


@pytest.mark.parametrize("c", CASOS, ids=lambda c: c["id"])
def test_referencia_literal_obedece_unicidade_e_disjuncao_do_foco(c):
    assert sonda.calcular_esperado(c) == c["esperado"]


@pytest.mark.parametrize("texto,alvo,esperado,foco", [
    ("volume “centro” saida", "lume", [], "c1"),
    ("Lume “centro” saida", "lume", [], "c1"),
    ("lume “lume” saida", "lume", [{"inicio": 0, "fim": 1}], "c1"),
    ("bruma bruma bruma “centro”", "bruma bruma", [], "c1"),
    ("bruma clara “centro”", "bruma  clara", [], "c1"),
    ("bruma  clara “centro”", "bruma  clara", [{"inicio": 0, "fim": 2}], "c1"),
    ("texto diz “lume 'centro' saida”", "lume", [{"inicio": 3, "fim": 4}], "c2"),
])
def test_oraculo_reusa_limites_literais_sem_normalizacao_semantica(texto, alvo, esperado, foco):
    c = {"texto": texto, "foco_id": foco, "alvo_literal_solicitado": alvo}
    assert sonda.calcular_esperado(c) == {"evidencias": esperado}


def test_request_recebe_alvo_nao_resposta_e_difere_somente_em_format():
    for c in CASOS:
        a, b = [sonda.preparar_requisicao(c, m) for m in sonda.MODOS]
        assert a.pop("format") == sonda.schema.etapas.FORMATO_SELECAO
        assert b.pop("format") == "json"
        assert a == b
        entrada = json.loads(a["messages"][1]["content"])
        assert entrada.pop("alvo_literal_solicitado") == c["alvo_literal_solicitado"]
        assert entrada == sonda.schema.etapas.coordenadas.projetar_entrada_modelo(c, modo="tokens_id_texto")
        assert not {"id", "tipo", "esperado", "evidencias", "papel", "ancoras"} & entrada.keys()
        adulterado = {**c, "esperado": {"evidencias": [{"inicio": 999, "fim": 1000}]}}
        assert sonda.preparar_requisicao(c, sonda.MODOS[0]) == sonda.preparar_requisicao(adulterado, sonda.MODOS[0])


@pytest.mark.parametrize("c", CASOS, ids=lambda c: c["id"])
def test_medicao_positiva_e_negativa_com_transporte_controlado(c):
    r = medir(c)
    a = sonda.aferir_caso(c, r)
    assert a["alinhado_literal_concluido"] is True
    assert a["positivo"] == bool(c["esperado"]["evidencias"])
    assert a["literal_materializado"] == a["positivo"]
    assert all(a[k] is False for k in sonda.BASE)


@pytest.mark.parametrize("motivo,done", [("length", True), ("stop", False), (None, True)])
def test_literal_correto_sem_termino_normal_nao_e_acerto_concluido(motivo, done):
    a = sonda.aferir_caso(CASOS[0], medir(CASOS[0], motivo=motivo, done=done))
    assert a["alinhado_literal"] is True
    assert a["literal_materializado"] is True
    assert a["alinhado_literal_concluido"] is False


def test_vazio_universal_nao_ganha_credito_nos_positivos():
    rs = [medir(c, m, proposta={"evidencias": []}) for c in CASOS for m in sonda.MODOS]
    for r in rs:
        r["afericao"] = {"alinhado_literal_concluido": True}
        r["proposta"] = {"evidencias": [{"inicio": 0, "fim": 1}]}
    resumo = sonda.resumir(CASOS, rs)
    for b in resumo["bracos"].values():
        assert b["casos"] == b["consultas"] == 6
        assert b["positivos"] == b["negativos"] == 3
        assert b["positivos_alinhados_concluidos"] == 0
        assert b["negativos_alinhados_concluidos"] == 3
    assert resumo["holdout_semantico"] is False


@pytest.mark.parametrize("tipo", ["ausente", "duplicata", "request", "host", "reference", "nan",
    "flag", "contradicao", "http_status", "casos", "transbordamento"])
def test_resumo_recusa_cadeia_adulterada(tipo):
    cs = deepcopy(CASOS)
    rs = [medir(c, m) for c in cs for m in sonda.MODOS]
    if tipo == "ausente":
        rs.pop()
    elif tipo == "duplicata":
        rs.append(deepcopy(rs[0]))
    elif tipo == "request":
        rs[0]["requisicao"]["options"]["num_predict"] = 701
    elif tipo == "host":
        rs[0]["entrada_host"]["foco"]["texto"] = "falso"
    elif tipo == "reference":
        cs[0]["esperado"]["evidencias"][0]["inicio"] = False
    elif tipo == "nan":
        rs[0]["duracao_consulta_s"] = float("nan")
    elif tipo == "flag":
        rs[0]["aprovado_para_producao"] = True
    elif tipo == "contradicao":
        rs[0]["erro_consulta"] = "TimeoutError"
    elif tipo == "http_status":
        rs[0]["http_status"] = True
    elif tipo == "casos":
        cs.pop()
    else:
        for r in rs:
            r["duracao_consulta_s"] = 1e308
    assert sonda.resumir(cs, rs)["tipo"] == "resumo_invalido"


def test_falha_de_consulta_nao_e_negativo_correto():
    def post(*a, **k):
        raise TimeoutError
    r = sonda.medir_caso(CASOS[3], modo="json_generico", post=post)
    a = sonda.aferir_caso(CASOS[3], r)
    assert a["interpretacao"]["estado_transporte"] == "erro_consulta"
    assert a["alinhado_literal_concluido"] is False
    assert "http_bruto" not in r


def test_intervalo_literal_errado_nao_vira_alvo_correto():
    a = sonda.aferir_caso(CASOS[0], medir(CASOS[0], proposta={"evidencias": [{"inicio": 4, "fim": 5}]}))
    assert a["literal_materializado"] is True
    assert a["evidencias"][0]["texto"] == "saida"
    assert a["alinhado_literal_concluido"] is False


def test_post_nao_altera_requisicao_preservada():
    def post(*a, json, **k):
        json["messages"][1]["content"] = "alterado"
        return resposta(CASOS[0]["esperado"])
    r = sonda.medir_caso(CASOS[0], modo="schema_restritivo", post=post)
    assert r["requisicao"] == sonda.preparar_requisicao(CASOS[0], "schema_restritivo")
    assert sonda.aferir_caso(CASOS[0], r)["alinhado_literal_concluido"] is True


def test_cli_preserva_arquivo_e_referencias_anteriores_as_doze_consultas(monkeypatch, tmp_path):
    chamadas = []
    original_medir = sonda.medir_caso
    def medir_fake(c, *, modo):
        chamadas.append((c["id"], modo))
        return original_medir(c, modo=modo, post=lambda *a, **k: resposta(c["esperado"]))
    monkeypatch.setattr(sonda, "medir_caso", medir_fake)
    monkeypatch.setattr(sonda.schema.etapas.coordenadas, "digest_modelo", lambda: "digest_teste")
    saida = tmp_path / "literal.jsonl"
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    antes = saida.read_bytes()
    rows = [json.loads(l) for l in antes.splitlines()]
    assert len(rows) == 14 and len(chamadas) == 12
    assert rows[0]["referencias_host_pre_consulta"] == {c["id"]: c["esperado"] for c in CASOS}
    assert sum(chamadas[2*i][1] == sonda.MODOS[0] for i in range(6)) == 3
    for b in rows[-1]["bracos"].values():
        assert b["positivos_alinhados_concluidos"] == b["negativos_alinhados_concluidos"] == 3
    with pytest.raises(FileExistsError):
        sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 12


@pytest.mark.parametrize("alvo", [None, "", " ", False])
def test_alvo_invalido_nao_chama_modelo(alvo):
    c = {**CASOS[0], "alvo_literal_solicitado": alvo}
    with pytest.raises(ValueError, match="alvo literal"):
        sonda.medir_caso(c, modo="json_generico", post=lambda *a, **k: pytest.fail("não consultar"))


def test_dependencias_e_painel_congelados():
    assert sonda.carregar_painel() == CASOS

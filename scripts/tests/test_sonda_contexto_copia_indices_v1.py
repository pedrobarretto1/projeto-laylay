from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_contexto_copia_indices_v1 as sonda


CASOS, OURO, PARES = sonda.carregar_painel()


def proposta_externa(caso, modo):
    host = sonda.etapas.vinculo.preparar_entrada(caso)
    foco, tokens = host["foco"], host["tokens"]
    grupos = [[t for t in tokens if t["fim"] <= foco["inicio"]],
              [t for t in tokens if t["inicio"] >= foco["fim"]]]
    grupos = [g for g in grupos if g]
    if modo == "indices":
        return {"evidencias": [{"inicio": g[0]["id"], "fim": g[-1]["id"] + 1} for g in grupos]}
    return {"evidencias": [caso["texto"][g[0]["inicio"]:g[-1]["fim"]] for g in grupos]}


def resposta(proposta, motivo="stop", done=True, status=200):
    return SimpleNamespace(status_code=status, text=json.dumps({"done": done, "done_reason": motivo,
        "message": {"content": json.dumps(proposta, ensure_ascii=False)}}))


def medir(caso, modo, proposta=None, **opcoes):
    p = proposta_externa(caso, modo) if proposta is None else proposta
    return sonda.medir_caso(caso, modo=modo, post=lambda *a, **k: resposta(p, **opcoes))


def sinteticos():
    return [medir(c, m) for c in CASOS for m in sonda.MODOS]


def test_payload_sem_alvo_gold_papel_e_sem_segunda_etapa():
    for c in CASOS:
        a = sonda.preparar_requisicao(c, "indices")
        b = sonda.preparar_requisicao(c, "copia")
        assert a == sonda.schema.preparar_requisicao(c, "schema_restritivo")
        assert a["messages"][1] == b["messages"][1]
        assert a["options"] == b["options"]
        assert isinstance(a["format"], dict) and isinstance(b["format"], dict)
        entrada = json.loads(b["messages"][1]["content"])
        assert not {"esperado", "ancoras", "papel", "id", "alvo_literal_solicitado", "evidencias"} & entrada.keys()
        assert entrada == sonda.etapas.coordenadas.projetar_entrada_modelo(c, modo="tokens_id_texto")
        assert all(set(t) == {"id", "texto"} for t in entrada["tokens"])
        assert "Use inicio inclusivo" not in sonda.SISTEMA_COPIA
        assert "Nao retorne indices" in sonda.SISTEMA_COPIA


@pytest.mark.parametrize("c", CASOS, ids=lambda c: c["id"])
@pytest.mark.parametrize("m", sonda.MODOS)
def test_contexto_materializado_e_cobertura_nao_promovem_semantica(c, m):
    a = sonda.aferir_caso(c, medir(c, m), OURO[c["id"]])
    assert a["selecao_literal_concluida"] is True
    assert a["cobertura_lexical_concluida"] is True
    assert all(a[k] is False for k in sonda.BASE)
    assert all(e["texto"] == c["texto"][e["inicio"]:e["fim"]] for e in a["evidencias"])


@pytest.mark.parametrize("m", sonda.MODOS)
@pytest.mark.parametrize("opcoes", [{"motivo": "length"}, {"done": False}, {"status": 500}])
def test_finalizacao_ou_http_invalido_nao_recebe_credito(m, opcoes):
    a = sonda.aferir_caso(CASOS[0], medir(CASOS[0], m, **opcoes), OURO[CASOS[0]["id"]])
    assert a["cobertura_lexical_concluida"] is False
    assert a["selecao_literal_concluida"] is False


@pytest.mark.parametrize("m", sonda.MODOS)
def test_vazio_nao_e_ausencia_comprovada(m):
    a = sonda.aferir_caso(CASOS[0], medir(CASOS[0], m, {"evidencias": []}), OURO[CASOS[0]["id"]])
    assert a["selecao_vazia"] is True and a["selecao_invalida"] is False
    assert a["cobertura_lexical_concluida"] is False
    assert all(a[k] is False for k in sonda.BASE)


@pytest.mark.parametrize("texto", ["O botão", "nome"])
def test_literal_autentico_sem_ancora_completa_nao_recebe_cobertura(texto):
    c = CASOS[0]
    a = sonda.aferir_caso(c, medir(c, "copia", {"evidencias": [texto]}), OURO[c["id"]])
    assert a["selecao_literal_concluida"] is True
    assert a["cobertura_lexical_concluida"] is False


@pytest.mark.parametrize("p", [
    {"evidencias": ["abra o baú"]}, {"evidencias": ["tem o nome", "inventado"]},
    {"evidencias": ["tem o nome", "tem o nome"]}, {"evidencias": ["Tem o nome"]},
    {"evidencias": ["tem o nome"], "papel": "nome"},
])
def test_copia_rejeitada_atomicamente_sem_falso_vazio(p):
    c = CASOS[0]
    a = sonda.aferir_caso(c, medir(c, "copia", p), OURO[c["id"]])
    assert a["selecao_invalida"] is True and a["selecao_vazia"] is False
    assert a["evidencias"] == []
    assert a["cobertura_lexical_concluida"] is False


def test_copia_ambigua_nao_escolhe_primeira_ocorrencia():
    c = next(c for c in CASOS if c["id"] == "Q04B")
    a = sonda.aferir_caso(c, medir(c, "copia", {"evidencias": ["Estamos discutindo a hipótese", "a"]}), OURO[c["id"]])
    assert a["selecao_invalida"] is True and a["evidencias"] == []


def test_resumo_recalcula_raw_nao_le_score_salvo():
    rs = sinteticos()
    for r in rs:
        r["afericao"] = {"cobertura_lexical_concluida": False, "autoriza_efeito": True}
    resumo = sonda.resumir(CASOS, rs, OURO)
    for b in resumo["bracos"].values():
        assert b["casos"] == b["consultas"] == b["cobertura_lexical_concluida"] == 20
        assert b["pares"] == b["pares_cobertura_lexical_concluida"] == 8


@pytest.mark.parametrize("tipo", ["ausente", "duplicata", "request", "host", "flag", "nan", "contradicao",
                                 "status", "caso", "ouro", "transbordamento"])
def test_replay_adulterado_ou_incompleto_recusado(tipo):
    cs, rs, ouro = deepcopy(CASOS), sinteticos(), deepcopy(OURO)
    if tipo == "ausente":
        rs.pop()
    elif tipo == "duplicata":
        rs.append(deepcopy(rs[0]))
    elif tipo == "request":
        rs[0]["requisicao"]["messages"][1]["content"] = "alvo: tem o nome"
    elif tipo == "host":
        rs[0]["entrada_host"]["tokens"][0]["inicio"] = False
    elif tipo == "flag":
        rs[0]["autoriza_efeito"] = True
    elif tipo == "nan":
        rs[0]["duracao_consulta_s"] = float("nan")
    elif tipo == "contradicao":
        rs[0]["erro_consulta"] = "TimeoutError"
    elif tipo == "status":
        rs[0]["http_status"] = True
    elif tipo == "caso":
        cs[0]["texto"] += " adulterado"
    elif tipo == "ouro":
        ouro[cs[0]["id"]]["ancoras"] = [["botão"]]
    else:
        for r in rs:
            r["duracao_consulta_s"] = 1e308
    assert sonda.resumir(cs, rs, ouro)["tipo"] == "resumo_invalido"


def test_erro_transporte_preservado_sem_credito():
    def falha(*a, **k):
        raise TimeoutError
    c = CASOS[0]
    r = sonda.medir_caso(c, modo="copia", post=falha)
    assert r["erro_consulta"] == "TimeoutError" and "http_bruto" not in r
    assert sonda.aferir_caso(c, r, OURO[c["id"]])["cobertura_lexical_concluida"] is False


def test_cli_quarenta_chamadas_sem_reconsulta_sem_papel_arquivo_exclusivo(monkeypatch, tmp_path):
    chamadas = []
    original = sonda.medir_caso
    def medir_fake(c, *, modo):
        chamadas.append((c["id"], modo))
        return original(c, modo=modo, post=lambda *a, **k: resposta(proposta_externa(c, modo)))
    monkeypatch.setattr(sonda, "medir_caso", medir_fake)
    monkeypatch.setattr(sonda.etapas.coordenadas, "digest_modelo", lambda: "digest_teste")
    saida = tmp_path / "contexto.jsonl"
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    antes = saida.read_bytes()
    rows = [json.loads(l) for l in antes.splitlines()]
    assert len(rows) == 42 and len(chamadas) == 40
    assert sum(chamadas[i*2][1] == "indices" for i in range(20)) == 10
    assert rows[0]["referencias_host_pre_consulta"] == OURO
    assert rows[0]["segunda_etapa_executada"] is False
    assert rows[0]["alvo_e_ancoras_fornecidos"] is False
    with pytest.raises(FileExistsError):
        sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 40


def test_modo_invalido_nao_consulta():
    with pytest.raises(ValueError):
        sonda.medir_caso(CASOS[0], modo="outro", post=lambda *a, **k: pytest.fail("não consultar"))

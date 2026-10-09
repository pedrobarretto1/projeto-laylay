from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_copia_indices_literal_v1 as sonda


CASOS = sonda.literal.carregar_painel()


def resposta(p, motivo="stop"):
    return SimpleNamespace(status_code=200, text=json.dumps({"message": {"content": json.dumps(p)},
                                                           "done": True, "done_reason": motivo}))


def proposta(c, m):
    if m == "indices":
        return c["esperado"]
    return {"evidencias": [c["alvo_literal_solicitado"]] if c["esperado"]["evidencias"] else []}


def medir(c, m, p=None, motivo="stop"):
    return sonda.medir_caso(c, modo=m, post=lambda *a, **k: resposta(proposta(c, m) if p is None else p, motivo))


@pytest.mark.parametrize("c", [CASOS[3], CASOS[5]], ids=lambda c: c["id"])
def test_copia_sem_ocorrencia_externa_unica_nao_vira_abstencao(c):
    host = sonda.literal.schema.etapas.vinculo.preparar_entrada(c)
    r = sonda.conferir_copia(c, host, {"evidencias": ["lume"]})
    assert r["estado"] == "copia_sem_ocorrencia_externa_unica"
    assert r["evidencia_literal_externa"] is False


@pytest.mark.parametrize("p,estado", [
    ({"evidencias": []}, "selecao_vazia_revisao_pendente"),
    ({"evidencias": ["lume"]}, "selecao_literal_revisao_pendente"),
    ({"evidencias": ["Lume"]}, "copia_sem_ocorrencia_externa_unica"),
    ({"evidencias": ["lum"]}, "copia_sem_ocorrencia_externa_unica"),
    ({"evidencias": ["lume", "inexistente"]}, "copia_sem_ocorrencia_externa_unica"),
    ({"evidencias": ["lume", "lume"]}, "intervalos_invalidos"),
    ({"evidencias": ["saida", "lume"]}, "intervalos_invalidos"),
    ({"evidencias": [""]}, "proposta_invalida"),
    ({"evidencias": [False]}, "proposta_invalida"),
    ({"evidencias": "lume"}, "proposta_invalida"),
    ({"evidencias": ["lume"], "papel": "nome"}, "proposta_invalida"),
    ({"evidencias": ["lume", "saida", "centro"]}, "proposta_invalida"),
])
def test_copia_literal_exata_unica_atomica_e_sem_reparo(p, estado):
    c = CASOS[0]
    host = sonda.literal.schema.etapas.vinculo.preparar_entrada(c)
    r = sonda.conferir_copia(c, host, p)
    assert r["estado"] == estado
    assert all(r[k] is False for k in sonda.BASE)
    if estado not in {"selecao_literal_revisao_pendente", "selecao_vazia_revisao_pendente"}:
        assert r["evidencias"] == []


def test_copia_no_foco_e_host_adulterado_recusados():
    c = CASOS[4]
    host = sonda.literal.schema.etapas.vinculo.preparar_entrada(c)
    assert sonda.conferir_copia(c, host, {"evidencias": ["lume"]})["estado"] == "copia_sem_ocorrencia_externa_unica"
    host["tokens"][0]["inicio"] = False
    assert sonda.conferir_copia(c, host, {"evidencias": []})["estado"] == "entrada_adulterada"


def test_mesma_entrada_opcoes_schema_ambos_e_controle_indice_historico():
    for c in CASOS:
        a = sonda.preparar_requisicao(c, "indices")
        b = sonda.preparar_requisicao(c, "copia")
        assert a == sonda.literal.preparar_requisicao(c, "schema_restritivo")
        assert a["messages"][1] == b["messages"][1]
        assert a["options"] == b["options"]
        assert isinstance(a["format"], dict) and isinstance(b["format"], dict)
        assert b["messages"][0]["content"] == sonda.SISTEMA_COPIA
        assert "fim inteiros" not in sonda.SISTEMA_COPIA and "Use os IDs" not in sonda.SISTEMA_COPIA
        entrada = json.loads(b["messages"][1]["content"])
        assert not {"esperado", "tipo", "id", "ancoras", "evidencias"} & entrada.keys()


@pytest.mark.parametrize("c", CASOS, ids=lambda c: c["id"])
@pytest.mark.parametrize("m", sonda.MODOS)
def test_receipt_literal_equivalente_apos_host_materializar(c, m):
    r = medir(c, m)
    a = sonda.aferir_caso(c, r)
    assert a["alinhado_literal_concluido"] is True
    assert a["literal_materializado"] == bool(c["esperado"]["evidencias"])
    assert all(a[k] is False for k in sonda.BASE)


@pytest.mark.parametrize("m", sonda.MODOS)
def test_termino_por_limite_nao_certifica_acerto(m):
    a = sonda.aferir_caso(CASOS[0], medir(CASOS[0], m, motivo="length"))
    assert a["alinhado_literal"] is True and a["alinhado_literal_concluido"] is False


def sinteticos():
    return [medir(c, m) for c in CASOS for m in sonda.MODOS]


def test_resumo_recalcula_raw_e_denominadores_separados():
    rs = sinteticos()
    for r in rs:
        r["afericao"] = {"alinhado_literal_concluido": False}
    resumo = sonda.resumir(CASOS, rs)
    for b in resumo["bracos"].values():
        assert b["casos"] == b["consultas"] == 6
        assert b["positivos"] == b["negativos"] == 3
        assert b["positivos_alinhados_concluidos"] == b["negativos_alinhados_concluidos"] == 3


@pytest.mark.parametrize("tipo", ["ausente", "duplicata", "request", "host", "flag", "nan", "contradicao", "status", "caso", "transbordamento"])
def test_resumo_recusa_adulteracao_e_cobertura_faltante(tipo):
    cs, rs = deepcopy(CASOS), sinteticos()
    if tipo == "ausente":
        rs.pop()
    elif tipo == "duplicata":
        rs.append(deepcopy(rs[0]))
    elif tipo == "request":
        rs[0]["requisicao"]["options"]["num_predict"] = 701
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
        cs.pop()
    else:
        for r in rs:
            r["duracao_consulta_s"] = 1e308
    assert sonda.resumir(cs, rs)["tipo"] == "resumo_invalido"


def test_echo_invalido_e_erros_nao_recebem_credito_negativo():
    c = CASOS[3]
    assert sonda.aferir_caso(c, medir(c, "copia", {"evidencias": ["lume"]}))["alinhado_literal_concluido"] is False
    def falha(*a, **k):
        raise TimeoutError
    r = sonda.medir_caso(c, modo="copia", post=falha)
    assert sonda.aferir_caso(c, r)["alinhado_literal_concluido"] is False
    assert "http_bruto" not in r


def test_outro_literal_autentico_nao_vira_alvo_pedido():
    a = sonda.aferir_caso(CASOS[0], medir(CASOS[0], "copia", {"evidencias": ["saida"]}))
    assert a["literal_materializado"] is True and a["alinhado_literal_concluido"] is False


def test_cli_arquivo_exclusivo_ordem_e_painel_preservados(monkeypatch, tmp_path):
    chamadas = []
    original = sonda.medir_caso
    def medir_fake(c, *, modo):
        chamadas.append((c["id"], modo))
        return original(c, modo=modo, post=lambda *a, **k: resposta(proposta(c, modo)))
    monkeypatch.setattr(sonda, "medir_caso", medir_fake)
    monkeypatch.setattr(sonda.literal.schema.etapas.coordenadas, "digest_modelo", lambda: "digest_teste")
    saida = tmp_path / "contraste.jsonl"
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    antes = saida.read_bytes()
    rows = [json.loads(l) for l in antes.splitlines()]
    assert len(rows) == 14 and len(chamadas) == 12
    assert sum(chamadas[i*2][1] == "indices" for i in range(6)) == 3
    assert rows[0]["referencias_host_pre_consulta"] == {c["id"]: c["esperado"] for c in CASOS}
    with pytest.raises(FileExistsError):
        sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 12


def test_modo_invalido_nao_consulta():
    with pytest.raises(ValueError):
        sonda.medir_caso(CASOS[0], modo="outro", post=lambda *a, **k: pytest.fail("não consultar"))

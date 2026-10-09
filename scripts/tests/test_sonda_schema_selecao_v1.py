from types import SimpleNamespace
from copy import deepcopy
import json
import sys

import pytest

from scripts.analises import sonda_schema_selecao_v1 as sonda

CASOS, OURO, _ = sonda.carregar_painel()


def resposta(proposta=None, *, done=True, motivo="stop", status=200, bruto=None):
    if bruto is None:
        bruto = json.dumps({"message": {"content": json.dumps(proposta)},
                            "done": done, "done_reason": motivo})
    return SimpleNamespace(status_code=status, text=bruto)


def medir(c=None, *, modo="schema_restritivo", proposta=None, **kwargs):
    return sonda.medir_caso(c or CASOS[0], modo=modo,
        post=lambda *a, **k: resposta(proposta or {"evidencias": []}, **kwargs))


@pytest.mark.parametrize("status,bruto", [
    (200, '{"message":{"content":"{quebrado"},"done":true,"done_reason":"length"}'),
    (500, 'erro local não JSON'),
    (200, '{"message":{"content":"{\\"evidencias\\":[]}"},"done":true,"done_reason":"stop"}'),
])
def test_captura_preserva_http_antes_de_parse_ou_erro(status, bruto):
    def legado_json():
        return json.loads(bruto)
    resposta = SimpleNamespace(status_code=status, text=bruto,
                               raise_for_status=lambda: None, json=legado_json)
    r = sonda.capturar_http({}, lambda *a, **k: resposta)
    assert r["http_status"] == status
    assert r["http_bruto"] == bruto
    assert "proposta" not in r


def test_requisicoes_diferem_somente_no_format_e_nao_recebem_ouro():
    for c in CASOS:
        a, b = [sonda.preparar_requisicao(c, m) for m in sonda.MODOS]
        assert a.pop("format") == sonda.etapas.FORMATO_SELECAO
        assert b.pop("format") == "json"
        assert a == b
        assert a["messages"][0]["content"] == sonda.etapas.SISTEMA_SELECAO
        entrada = json.loads(a["messages"][1]["content"])
        assert entrada == sonda.etapas.coordenadas.projetar_entrada_modelo(c, modo="tokens_id_texto")
        assert not {"ancoras", "papel", "ouro", "id", "par"} & entrada.keys()
        assert a["options"] == {"temperature": 0, "num_predict": 700}
        assert a["stream"] is False


@pytest.mark.parametrize("modo", sonda.MODOS)
def test_captura_requisicao_e_host_nao_compartilham_mutacoes_do_post(modo):
    def post(url, *, json, timeout):
        assert timeout == 90 and url.endswith("/api/chat")
        json["messages"][0]["content"] = "adulterado"
        return resposta({"evidencias": [{"inicio": 2, "fim": 5}]})
    r = sonda.medir_caso(CASOS[0], modo=modo, post=post)
    assert r["requisicao"] == sonda.preparar_requisicao(CASOS[0], modo)
    a = sonda.aferir_caso(CASOS[0], r, OURO[CASOS[0]["id"]])
    assert a["selecao_literal_concluida"] is True
    assert a["cobertura_local_concluida"] is True
    assert a["evidencias"][0]["texto"] == "tem o nome"
    assert all(a[k] is False for k in sonda.BASE)


@pytest.mark.parametrize("done,motivo,estado", [
    (True, "stop", "concluida"), (True, "length", "limite_tokens"),
    (False, "stop", "nao_confirmada"), (1, "stop", "nao_confirmada"),
    (True, None, "nao_confirmada"), (True, "outro", "nao_confirmada"),
])
def test_finalizacao_nao_se_confunde_com_literalidade(done, motivo, estado):
    r = medir(proposta={"evidencias": [{"inicio": 2, "fim": 5}]}, done=done, motivo=motivo)
    a = sonda.aferir_caso(CASOS[0], r, OURO[CASOS[0]["id"]])
    assert a["selecao_literal_valida"] is True
    assert a["finalizacao"] == estado
    assert a["selecao_literal_concluida"] is (estado == "concluida")
    assert a["interpretacao"]["resposta_json"]["done"] == done


@pytest.mark.parametrize("proposta,estado", [
    ({"evidencias": []}, "selecao_vazia_revisao_pendente"),
    ({"evidencias": [{"inicio": True, "fim": 5}]}, "intervalos_invalidos"),
    ({"evidencias": [{"inicio": 2.0, "fim": 5}]}, "intervalos_invalidos"),
    ({"evidencias": [{"inicio": 2, "fim": 999}]}, "intervalos_invalidos"),
    ({"evidencias": [{"inicio": 6, "fim": 7}]}, "evidencia_intersecta_foco"),
    ({"evidencias": [{"inicio": 2, "fim": 5}], "papel": "nome_designacao"}, "proposta_invalida"),
])
def test_guarda_historica_nao_repara_intervalos_nem_imputa_papel(proposta, estado):
    a = sonda.aferir_caso(CASOS[0], medir(proposta=proposta), OURO[CASOS[0]["id"]])
    assert a["estado_selecao"] == estado
    assert a["selecao_literal_valida"] is False
    assert "papel" not in a


@pytest.mark.parametrize("status,bruto,estado", [
    (500, "falha do servidor", "erro_http"), (200, "não JSON", "http_json_invalido"),
    (200, "[]", "envelope_invalido"), (200, "{}", "conteudo_ausente"),
    (200, '{"message":{"content":false}}', "conteudo_ausente"),
    (200, '{"message":{"content":"```json {} ```"}}', "conteudo_json_invalido"),
    (200, '{"message":{"content":"{quebrado"}}', "conteudo_json_invalido"),
    (200, '{"message":{"content":"{\\"evidencias\\":[NaN]}"}}', "conteudo_json_invalido"),
    (200, '{"message":{"content":"{}"},"total_duration":NaN}', "http_json_invalido"),
])
def test_falha_raw_nao_vira_abstencao_ou_sucesso(status, bruto, estado):
    r = medir(status=status, bruto=bruto)
    a = sonda.aferir_caso(CASOS[0], r, OURO[CASOS[0]["id"]])
    assert r["http_bruto"] == bruto
    assert a["estado_transporte"] == estado
    assert a["selecao_vazia"] is False
    assert a["selecao_literal_concluida"] is False


def test_erro_de_consulta_preserva_denominador_sem_fabricar_http():
    def post(*a, **k):
        raise TimeoutError
    r = sonda.medir_caso(CASOS[0], modo="json_generico", post=post)
    assert r["erro_consulta"] == "TimeoutError"
    assert "http_bruto" not in r and "http_status" not in r
    assert sonda.aferir_caso(CASOS[0], r, OURO[CASOS[0]["id"]])["estado_transporte"] == "erro_consulta"


def sinteticos():
    return [medir(c, modo=m) for c in CASOS for m in sonda.MODOS]


def test_resumo_recalcula_raw_sem_confiar_em_proposta_ou_metricas_salvas():
    rs = sinteticos()
    rs[0]["proposta"] = {"evidencias": [{"inicio": 2, "fim": 5}]}
    rs[0]["afericao"] = {"selecao_literal_concluida": True}
    resumo = sonda.resumir(CASOS, rs, OURO)
    for b in resumo["bracos"].values():
        assert b["casos"] == b["consultas"] == b["selecao_vazia"] == 20
        assert b["selecao_literal_valida"] == b["cobertura_local"] == 0
        assert b["finalizacoes"] == {"concluida": 20}
    assert resumo["holdout_novo"] is False


@pytest.mark.parametrize("tipo", ["ausente", "duplicata", "id", "modo", "request", "host",
    "duracao", "flag", "contradicao", "http_status", "http_ausente", "transbordamento"])
def test_resumo_recusa_registro_adulterado(tipo):
    rs = sinteticos()
    if tipo == "ausente":
        rs.pop()
    elif tipo == "duplicata":
        rs.append(deepcopy(rs[0]))
    elif tipo == "id":
        rs[0]["id"] = "outro"
    elif tipo == "modo":
        rs[0]["modo"] = "outro"
    elif tipo == "request":
        rs[0]["requisicao"]["options"]["num_predict"] = 701
    elif tipo == "host":
        rs[0]["entrada_host"]["tokens"][0]["inicio"] = False
    elif tipo == "duracao":
        rs[0]["duracao_consulta_s"] = float("nan")
    elif tipo == "flag":
        rs[0]["autoriza_efeito"] = True
    elif tipo == "contradicao":
        rs[0]["erro_consulta"] = "TimeoutError"
    elif tipo == "http_status":
        rs[0]["http_status"] = True
    elif tipo == "http_ausente":
        del rs[0]["http_bruto"]
    else:
        for r in rs:
            r["duracao_consulta_s"] = 1e308
    assert sonda.resumir(CASOS, rs, OURO)["tipo"] == "resumo_invalido"


def test_contexto_literal_irrelevante_nao_vira_cobertura_semantica():
    a = sonda.aferir_caso(CASOS[0], medir(proposta={"evidencias": [{"inicio": 0, "fim": 2}]}), OURO[CASOS[0]["id"]])
    assert a["selecao_literal_concluida"] is True
    assert a["cobertura_local"] is False
    assert a["semantica_verificada"] is False


def test_cli_contrabalanceia_quarenta_consultas_e_nao_sobrescreve(monkeypatch, tmp_path):
    chamadas = []
    original_medir = sonda.medir_caso
    def medir_fake(c, *, modo):
        chamadas.append((c["id"], modo))
        return original_medir(c, modo=modo, post=lambda *a, **k: resposta({"evidencias": []}))
    monkeypatch.setattr(sonda, "medir_caso", medir_fake)
    monkeypatch.setattr(sonda.etapas.coordenadas, "digest_modelo", lambda: "digest_teste")
    saida = tmp_path / "controle.jsonl"
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    assert len(chamadas) == 40
    assert sum(chamadas[2*i][1] == sonda.MODOS[0] for i in range(20)) == 10
    antes = saida.read_bytes()
    registros = [json.loads(l) for l in antes.splitlines()]
    assert len(registros) == 42
    assert registros[-1]["modelo_inalterado_entre_leituras"] is True
    with pytest.raises(FileExistsError):
        sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 40


def test_modo_ou_foco_invalido_nao_faz_consulta():
    def proibido(*a, **k):
        pytest.fail("não consultar")
    with pytest.raises(ValueError):
        sonda.medir_caso(CASOS[0], modo="outro", post=proibido)
    c = {**CASOS[0], "foco_id": "c0"}
    with pytest.raises(ValueError):
        sonda.medir_caso(c, modo="json_generico", post=proibido)

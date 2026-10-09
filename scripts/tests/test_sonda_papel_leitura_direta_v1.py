from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_papel_leitura_direta_v1 as sonda


CASOS, OURO, PARES = sonda.carregar_painel()


def medir(caso, modo, proposta=None, *, motivo="stop", done=True, status=200):
    p = {"papel": OURO[caso["id"]]["papel"]} if proposta is None else proposta
    bruto = json.dumps({"done": done, "done_reason": motivo,
                        "message": {"content": json.dumps(p, ensure_ascii=False)}})
    def post(url, *, json: dict, timeout):
        assert url == "http://127.0.0.1:11434/api/chat" and timeout == 90
        assert json == sonda.preparar_requisicao(caso, modo)
        return SimpleNamespace(status_code=status, text=bruto)
    return sonda.medir_caso(caso, modo=modo, post=post)


def sinteticos():
    return [medir(c, m) for c in CASOS for m in sonda.MODOS]


def test_unica_diferenca_e_prompt_sem_mudar_schema_payload_modelo_ou_opcoes():
    for c in CASOS:
        a, b = [sonda.preparar_requisicao(c, m) for m in sonda.MODOS]
        assert a == sonda.anterior.preparar_requisicao(c, "fonte_integral")
        assert b["messages"][0]["content"] == sonda.SISTEMA_DIRETO
        b["messages"][0]["content"] = a["messages"][0]["content"]
        assert a == b
        entrada = json.loads(a["messages"][1]["content"])
        assert entrada == sonda.papel.preparar_entrada(c)
        assert set(entrada) == {"fonte", "aspas_sintaticas", "foco"}
        assert c["id"] not in sonda.SISTEMA_DIRETO
        assert c["texto"] not in sonda.SISTEMA_DIRETO
    assert len(CASOS) == 20 and len(PARES) == 8


@pytest.mark.parametrize("c", CASOS, ids=lambda c: c["id"])
def test_guarda_canonica_e_bruto_sustentam_papel_local_nao_autoridade(c):
    for m in sonda.MODOS:
        r = medir(c, m)
        r["afericao"] = {"papel_alinhado_concluido": False}
        a = sonda.aferir_caso(c, r, OURO[c["id"]])
        assert a["saida_valida_concluida"] and a["papel_alinhado_concluido"]
        assert a["estado_papel"] == "papel_proposto_revisao_pendente"
        assert all(a[k] is False for k in sonda.BASE)


@pytest.mark.parametrize("opcoes", [{"motivo": "length"}, {"done": False}, {"status": 500}])
def test_nao_credita_conclusao_ausente_ou_http_falho(opcoes):
    c = CASOS[0]
    for m in sonda.MODOS:
        assert sonda.aferir_caso(c, medir(c, m, **opcoes), OURO[c["id"]])["papel_alinhado_concluido"] is False


@pytest.mark.parametrize("p", [{}, {"papel": True}, {"papel": "NOME"}, ["nome_designacao"],
    {"papel": "nome_designacao", "autoriza_efeito": True}])
def test_nao_repara_proposta_nem_importa_confirmacao(p):
    c = CASOS[0]
    a = sonda.aferir_caso(c, medir(c, "leitura_direta", p), OURO[c["id"]])
    assert a["papel_proposto"] is None and a["papel_alinhado_concluido"] is False


def test_resumo_autentica_replay_e_distingue_ganho_perda_e_contraste_completo():
    rs = sinteticos()
    for r in rs:
        r["afericao"] = {"papel_alinhado_concluido": False}
    rs[0] = medir(CASOS[0], "prompt_atual", {"papel": "expressao_sem_operacao"})
    rs[3] = medir(CASOS[1], "leitura_direta", {"papel": "expressao_sem_operacao"})
    resumo = sonda.resumir(CASOS, rs, OURO)
    assert resumo["comparacao_pareada"] == {"ganhos": 1, "perdas": 1, "ambos_alinhados": 18, "nenhum_alinhado": 0}
    assert {m["id"] for m in resumo["mudancas"]} == {"Q01A", "Q02B"}
    for b in resumo["bracos"].values():
        assert b["casos"] == b["consultas"] == b["saida_valida_concluida"] == 20
        assert b["papel_alinhado_concluido"] == 19
        assert b["pares_contextuais_alinhados_concluidos"] == 7
        assert sum(p["total"] for p in b["por_papel"].values()) == 20
        assert sum(sum(m.values()) for m in b["confusao"].values()) == 20


@pytest.mark.parametrize("tipo", ["ausente", "duplicata", "prompt", "payload", "schema", "modo",
    "host", "flag", "nan", "contradicao", "status", "caso", "ouro", "transbordamento"])
def test_replay_recusa_adulteracoes_sem_rebatizar_registro_para_prompt_antigo(tipo):
    cs, rs, ouro = deepcopy(CASOS), sinteticos(), deepcopy(OURO)
    if tipo == "ausente":
        rs.pop()
    elif tipo == "duplicata":
        rs.append(deepcopy(rs[0]))
    elif tipo == "prompt":
        rs[1]["requisicao"]["messages"][0]["content"] = sonda.papel.SISTEMA
    elif tipo == "payload":
        rs[1]["requisicao"]["messages"][1]["content"] = "gold"
    elif tipo == "schema":
        rs[1]["requisicao"]["format"] = "json"
    elif tipo == "modo":
        rs[1]["modo"] = "prompt_atual"
    elif tipo == "host":
        rs[0]["entrada_host"]["tokens"][0]["inicio"] = False
    elif tipo == "flag":
        rs[0]["autoriza_efeito"] = True
    elif tipo == "nan":
        rs[0]["duracao_consulta_s"] = float("nan")
    elif tipo == "contradicao":
        rs[1]["erro_consulta"] = "TimeoutError"
    elif tipo == "status":
        rs[1]["http_status"] = True
    elif tipo == "caso":
        cs[0]["texto"] += " alterado"
    elif tipo == "ouro":
        ouro[cs[0]["id"]]["papel"] = "indeterminado"
    else:
        for r in rs:
            r["duracao_consulta_s"] = 1e308
    assert sonda.resumir(cs, rs, ouro)["tipo"] == "resumo_invalido"


def test_cli_quarenta_consultas_independentes_precongeladas_sem_sobrescrever(monkeypatch, tmp_path):
    chamadas = []
    implementacao = sonda.medir_caso
    monkeypatch.setattr(sonda.etapas.coordenadas, "digest_modelo", lambda: "digest_teste")
    saida = tmp_path / "contraste.jsonl"
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    # Injetar somente o transporte: preservar implementação real de medir_caso.
    def medir_fake(c, *, modo):
        chamadas.append((c["id"], modo))
        retorno = SimpleNamespace(status_code=200, text=json.dumps({"done": True, "done_reason": "stop",
            "message": {"content": json.dumps({"papel": OURO[c["id"]]["papel"]})}}))
        return implementacao(c, modo=modo, post=lambda *a, **k: retorno)
    monkeypatch.setattr(sonda, "medir_caso", medir_fake)
    sonda.main()
    antes = saida.read_bytes()
    rows = [json.loads(l) for l in antes.splitlines()]
    assert len(rows) == 42 and len(chamadas) == 40
    assert chamadas == [(c["id"], m) for i, c in enumerate(CASOS)
                        for m in (sonda.MODOS if i % 2 == 0 else tuple(reversed(sonda.MODOS)))]
    assert rows[0]["referencias_host_pre_consulta"] == OURO
    assert rows[0]["diferenca_somente_prompt_sistema"] is True
    assert rows[-1]["bracos"]["leitura_direta"]["papel_alinhado_concluido"] == 20
    with pytest.raises(FileExistsError):
        sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 40


def test_timeout_sem_retentativa_ou_credito():
    chamadas = []
    def falha(*a, **k):
        chamadas.append(1)
        raise TimeoutError
    c = CASOS[0]
    r = sonda.medir_caso(c, modo="leitura_direta", post=falha)
    assert chamadas == [1] and r["erro_consulta"] == "TimeoutError"
    assert sonda.aferir_caso(c, r, OURO[c["id"]])["papel_alinhado_concluido"] is False
    with pytest.raises(ValueError):
        sonda.medir_caso(c, modo="outro", post=falha)
    assert chamadas == [1]

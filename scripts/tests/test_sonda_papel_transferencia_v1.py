from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_papel_transferencia_v1 as sonda


CASOS, OURO, PARES = sonda.carregar_painel()


def medir(c, m, p=None, *, done=True, motivo="stop", status=200):
    proposta = {"papel": OURO[c["id"]]["papel"]} if p is None else p
    bruto = json.dumps({"done": done, "done_reason": motivo,
                        "message": {"content": json.dumps(proposta)}})
    return sonda.medir_caso(c, modo=m, post=lambda *a, **k: SimpleNamespace(status_code=status, text=bruto))


def registros():
    return [medir(c, m) for c in CASOS for m in sonda.MODOS]


def test_painel_novo_congelado_e_balanceado_sem_gabarito_no_input():
    antigos, _, _ = sonda.contraste.carregar_painel()
    assert len(CASOS) == 32 and len(OURO) == 32 and len(PARES) == 12
    assert {c["texto"] for c in CASOS}.isdisjoint({c["texto"] for c in antigos})
    for c in CASOS:
        a, b = [sonda.contraste.preparar_requisicao(c, m) for m in sonda.MODOS]
        assert a["messages"][0]["content"] == sonda.papel.SISTEMA
        assert b["messages"][0]["content"] == sonda.contraste.SISTEMA_DIRETO
        b["messages"][0]["content"] = a["messages"][0]["content"]
        assert a == b
        entrada = json.loads(a["messages"][1]["content"])
        assert set(entrada) == {"fonte", "foco", "aspas_sintaticas"}
        assert c["id"] not in a["messages"][1]["content"]
        assert OURO[c["id"]]["justificativa"] not in a["messages"][1]["content"]


def test_mesma_fonte_texto_repetido_ocorrencias_distintas_nao_mescla_papel():
    a, b = [next(c for c in CASOS if c["id"] == i) for i in ("H11A", "H11B")]
    ea, eb = [sonda.papel.preparar_entrada(c) for c in (a, b)]
    assert a["texto"] == b["texto"] and ea["foco"]["texto"] == eb["foco"]["texto"]
    assert ea["foco"]["fim"] < eb["foco"]["inicio"]
    for c in (a, b):
        r = medir(c, "leitura_direta")
        a = sonda.aferir_caso(c, r, OURO[c["id"]])
        assert a["papel_alinhado_concluido"] is True
        assert all(a[k] is False for k in sonda.BASE)


def test_resumo_reconta_sessenta_e_quatro_brutos_nao_scores_salvos():
    rs = registros()
    for r in rs:
        r["afericao"] = {"papel_alinhado_concluido": False, "autoriza_efeito": True}
    resumo = sonda.resumir(CASOS, rs, OURO)
    assert resumo["painel_novo"] is True and resumo["revisao_humana_independente"] is False
    for b in resumo["bracos"].values():
        assert b["casos"] == b["consultas"] == b["papel_alinhado_concluido"] == 32
        assert b["pares_contextuais_alinhados_concluidos"] == 12
        assert sum(p["total"] for p in b["por_papel"].values()) == 32
        assert sum(sum(p.values()) for p in b["confusao"].values()) == 32
    assert all(resumo[k] is False for k in sonda.BASE)


def test_ganhos_perdas_e_pares_exigem_conclusao_de_ambos_os_lados():
    rs = registros()
    rs[0] = medir(CASOS[0], "prompt_atual", {"papel": "operacao_mencionada"})
    rs[3] = medir(CASOS[1], "leitura_direta", {"papel": "indeterminado"})
    resumo = sonda.resumir(CASOS, rs, OURO)
    assert resumo["comparacao_pareada"] == {"ganhos": 1, "perdas": 1, "ambos_alinhados": 30, "nenhum_alinhado": 0}
    assert all(b["pares_contextuais_alinhados_concluidos"] == 11 for b in resumo["bracos"].values())


@pytest.mark.parametrize("tipo", ["ausente", "duplicata", "request", "host", "flag", "nan", "erro_e_bruto",
                                 "status", "caso", "ouro", "ouro_justificativa", "transbordamento"])
def test_resumo_recusa_registro_ou_referencia_adulterada(tipo):
    cs, rs, ouro = deepcopy(CASOS), registros(), deepcopy(OURO)
    if tipo == "ausente":
        rs.pop()
    elif tipo == "duplicata":
        rs.append(deepcopy(rs[0]))
    elif tipo == "request":
        rs[1]["requisicao"]["messages"][0]["content"] = sonda.papel.SISTEMA
    elif tipo == "host":
        rs[1]["entrada_host"]["foco"]["inicio"] += 1
    elif tipo == "flag":
        rs[1]["autoriza_efeito"] = True
    elif tipo == "nan":
        rs[1]["duracao_consulta_s"] = float("nan")
    elif tipo == "erro_e_bruto":
        rs[0]["erro_consulta"] = "TimeoutError"
    elif tipo == "status":
        rs[0]["http_status"] = True
    elif tipo == "caso":
        cs[0]["foco_id"] = "c2"
    elif tipo == "ouro":
        ouro[cs[0]["id"]]["papel"] = "operacao_mencionada"
    elif tipo == "ouro_justificativa":
        ouro[cs[0]["id"]]["justificativa"] = "outro"
    else:
        for r in rs:
            r["duracao_consulta_s"] = 1e308
    assert sonda.resumir(cs, rs, ouro)["tipo"] == "resumo_invalido"


@pytest.mark.parametrize("opcoes", [{"done": False}, {"motivo": "length"}, {"status": 500}])
def test_transporte_ou_finalizacao_nao_remove_caso_do_denominador(opcoes):
    rs = registros()
    rs[1] = medir(CASOS[0], "leitura_direta", **opcoes)
    b = sonda.resumir(CASOS, rs, OURO)["bracos"]["leitura_direta"]
    assert b["casos"] == 32 and b["papel_alinhado_concluido"] == 31


def test_painel_alterado_bloqueia_antes_de_consultar(monkeypatch, tmp_path):
    novo = tmp_path / "painel.json"
    novo.write_bytes(sonda.ENTRADAS.read_bytes() + b" ")
    monkeypatch.setattr(sonda, "ENTRADAS", novo)
    with pytest.raises(ValueError, match="apos congelamento"):
        sonda.carregar_painel()


def test_cli_precongela_referencias_64_consultas_independentes_e_saida_exclusiva(monkeypatch, tmp_path):
    saida, chamadas = tmp_path / "sonda.jsonl", []
    real = sonda.medir_caso
    def fake(c, *, modo):
        metadata = json.loads(saida.read_text(encoding="utf-8").splitlines()[0])
        assert metadata["referencias_host_pre_consulta"] == OURO
        assert metadata["hash_painel"] == sonda.HASH_PAINEL
        chamadas.append((c["id"], modo))
        bruto = json.dumps({"done": True, "done_reason": "stop",
                           "message": {"content": json.dumps({"papel": OURO[c["id"]]["papel"]})}})
        return real(c, modo=modo, post=lambda *a, **k: SimpleNamespace(status_code=200, text=bruto))
    monkeypatch.setattr(sonda, "medir_caso", fake)
    monkeypatch.setattr(sonda.etapas.coordenadas, "digest_modelo", lambda: "teste")
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    antes = saida.read_bytes()
    rows = [json.loads(l) for l in antes.splitlines()]
    assert len(rows) == 66 and len(chamadas) == 64
    assert chamadas == [(c["id"], m) for i, c in enumerate(CASOS)
                        for m in (sonda.MODOS if i % 2 == 0 else tuple(reversed(sonda.MODOS)))]
    assert rows[0]["prompts_congelados_sem_ajuste"] is True
    assert rows[0]["referencias_fornecidas_ao_modelo"] is False
    assert rows[-1]["bracos"]["leitura_direta"]["papel_alinhado_concluido"] == 32
    with pytest.raises(FileExistsError):
        sonda.main()
    assert antes == saida.read_bytes() and len(chamadas) == 64

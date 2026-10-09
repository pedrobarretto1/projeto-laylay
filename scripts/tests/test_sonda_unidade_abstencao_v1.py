from collections import Counter
from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_unidade_abstencao_v1 as sonda


CASOS, OURO, PARES = sonda.carregar_painel()
MEDIR = sonda.medir_caso


def proposta(c, modo):
    return {sonda.campo_do_modo(modo): sonda.anterior.anterior.PISTAS_LOCAIS[c["id"]][0],
            "papel": OURO[c["id"]]["papel"]}


def medir(c, modo, *, p=None, motivo="stop", status=200):
    p = proposta(c, modo) if p is None else p
    return MEDIR(c, modo=modo, post=lambda *a, **k: SimpleNamespace(status_code=status,
        text=json.dumps({"done": True, "done_reason": motivo, "message": {"content": json.dumps(p)}})))


def registros():
    return [medir(c, m) for c in CASOS for m in sonda.MODOS]


def test_fatores_preservam_entrada_opcoes_e_baseline_exato():
    for c in CASOS:
        reqs = [sonda.preparar_requisicao(c, m) for m in sonda.MODOS]
        a, b, aa, bb = reqs
        assert a == sonda.anterior.preparar_requisicao(c, "predicado_host")
        for r in reqs:
            assert r["messages"][1] == a["messages"][1] and r["options"] == a["options"]
            assert set(json.loads(r["messages"][1]["content"])) == {"fonte", "foco", "aspas_sintaticas"}
        assert b["messages"][0]["content"] == a["messages"][0]["content"].replace("predicado", "trecho_externo")
        assert aa["messages"][0]["content"] == sonda.PRIORIDADE + a["messages"][0]["content"]
        assert bb["messages"][0]["content"] == sonda.PRIORIDADE + b["messages"][0]["content"]
        assert aa["format"] == a["format"] and bb["format"] == b["format"]
        assert list(b["format"]["properties"]) == [
            "trecho_externo" if k == "predicado" else k for k in a["format"]["properties"]]


def test_mesmo_valor_materializa_mesmo_intervalo_nos_quatro_modos():
    for c in CASOS:
        e = sonda.papel.preparar_entrada(c)
        rs = [sonda.conferir_proposta(c, e, proposta(c, m), modo=m) for m in sonda.MODOS]
        assert all(r == rs[0] for r in rs)
        assert rs[0]["vinculo_estrutural_valido"] is True
        assert all(rs[0][k] is False for k in sonda.BASE)


@pytest.mark.parametrize("tipo", ["chave_antiga", "extra", "valor_lista", "papel_invalido"])
def test_adaptacao_nao_corrige_shape_ou_valor_do_modelo(tipo):
    c = CASOS[0]
    p = proposta(c, "trecho_externo")
    if tipo == "chave_antiga": p["predicado"] = p.pop("trecho_externo")
    elif tipo == "extra": p["autoriza_efeito"] = True
    elif tipo == "valor_lista": p["trecho_externo"] = [p["trecho_externo"]]
    else: p["papel"] = "feito"
    r = sonda.conferir_proposta(c, sonda.papel.preparar_entrada(c), p, modo="trecho_externo")
    assert r["vinculo_estrutural_valido"] is False and r["intervalo_ligacao"] is None
    assert all(r[k] is False for k in sonda.BASE)


def test_vazio_nao_vira_indeterminado_por_instrucao_do_experimento():
    c = CASOS[0]
    for m in sonda.MODOS:
        p = {sonda.campo_do_modo(m): "", "papel": "operacao_mencionada"}
        r = sonda.conferir_proposta(c, sonda.papel.preparar_entrada(c), p, modo=m)
        assert r["estado"] == "predicado_vazio_revisao_pendente"
        assert r["papel_proposto"] == "operacao_mencionada"


def test_host_adulterado_e_recusado_antes_da_materializacao():
    c = CASOS[0]
    e = sonda.papel.preparar_entrada(c)
    e["foco"]["inicio"] = float(e["foco"]["inicio"])
    r = sonda.conferir_proposta(c, e, proposta(c, "trecho_externo"), modo="trecho_externo")
    assert r["estado"] == "entrada_adulterada"


def test_copia_de_texto_do_foco_e_diagnostico_mesmo_com_grafia_de_aspas_trocada():
    c = CASOS[0]
    foco = sonda.papel.preparar_entrada(c)["foco"]
    p = {"trecho_externo": 'cujo nome é "' + foco["texto"] + '"', "papel": "nome_designacao"}
    a = sonda.aferir_caso(c, medir(c, "trecho_externo", p=p), OURO[c["id"]])
    assert a["reproduz_texto_foco_concluido"] is True
    assert a["vinculo_estrutural_concluido"] is False
    assert a["papel_alinhado_concluido"] is True


def test_pista_correta_nao_troca_papel_por_gabarito_ou_regra_de_abstencao():
    c = next(c for c in CASOS if c["id"] == "U02")
    p = {"trecho_externo": "não sei se é etiqueta de vaso ou uma orientação citada", "papel": "expressao_sem_operacao"}
    a = sonda.aferir_caso(c, medir(c, "trecho_externo_abstencao", p=p), OURO[c["id"]])
    assert a["vinculo_estrutural_concluido"] is True and a["pista_local_concluida"] is True
    assert a["papel_proposto"] == "expressao_sem_operacao" and a["papel_alinhado_concluido"] is False
    assert a["conjunto_local_concluido"] is False and all(a[k] is False for k in sonda.BASE)


@pytest.mark.parametrize("tipo", ["ausente", "duplicado", "host", "pedido", "flag", "nan", "contradicao"])
def test_replay_recusa_registro_adulterado(tipo):
    rs = registros()
    if tipo == "ausente": rs.pop()
    elif tipo == "duplicado": rs.append(deepcopy(rs[0]))
    elif tipo == "host": rs[0]["entrada_host"]["foco"]["inicio"] = False
    elif tipo == "pedido": rs[0]["requisicao"]["messages"][0]["content"] += "mudou"
    elif tipo == "flag": rs[0]["autoriza_efeito"] = True
    elif tipo == "nan": rs[0]["duracao_consulta_s"] = float("nan")
    else: rs[0]["erro_consulta"] = "TimeoutError"
    assert sonda.resumir(rs)["tipo"] == "resumo_invalido"


def test_resumo_reconta_bruto_separa_abstencao_correta_falsa_e_finalizacao():
    rs = registros()
    for r in rs: r["afericao"] = {"papel_alinhado_concluido": False}
    c = CASOS[0]
    p = proposta(c, "predicado_abstencao")
    p["papel"] = "indeterminado"
    rs[2] = medir(c, "predicado_abstencao", p=p)
    rs[3] = medir(c, "trecho_externo_abstencao", motivo="length")
    resumo = sonda.resumir(rs)
    a = resumo["bracos"]["predicado_abstencao"]
    assert a["casos"] == 32 and a["papel_alinhado_concluido"] == 31
    assert a["falso_indeterminado_concluido"] == 1
    assert a["por_papel"]["indeterminado"] == {"total": 4, "alinhados": 4}
    assert resumo["bracos"]["trecho_externo_abstencao"]["conjunto_local_concluido"] == 31
    assert resumo["comparacoes"]["predicado->predicado_abstencao"]["papel_alinhado_concluido"]["perda_booleana"] == [c["id"]]


def test_cli_congela_128_consultas_e_ordem_balanceada_sem_sobrescrita(monkeypatch, tmp_path):
    saida, chamadas = tmp_path / "fatorial.jsonl", []
    def fake(c, *, modo):
        meta = json.loads(saida.read_text(encoding="utf-8").splitlines()[0])
        assert meta["referencias_host_pre_consulta"] == OURO
        assert meta["pistas_locais_pre_consulta"] == sonda.anterior.anterior.PISTAS_LOCAIS
        chamadas.append((c["id"], modo))
        return medir(c, modo)
    monkeypatch.setattr(sonda, "medir_caso", fake)
    monkeypatch.setattr(sonda.etapas.coordenadas, "digest_modelo", lambda: "teste")
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    antes = saida.read_bytes()
    assert len(antes.splitlines()) == 130 and len(chamadas) == 128
    assert chamadas == [(c["id"], m) for i, c in enumerate(CASOS) for m in sonda.ORDENS[i % 4]]
    for pos in range(4):
        assert Counter(sonda.ORDENS[i % 4][pos] for i in range(32)) == dict.fromkeys(sonda.MODOS, 8)
    with pytest.raises(FileExistsError): sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 128

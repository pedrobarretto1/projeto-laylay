from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_predicado_host_v1 as sonda


CASOS, OURO, PARES = sonda.carregar_painel()
POR_ID = {c["id"]: c for c in CASOS}
MEDIR = sonda.medir_caso


def proposta(c, modo):
    p = {"predicado": sonda.anterior.PISTAS_LOCAIS[c["id"]][0], "papel": OURO[c["id"]]["papel"]}
    if modo == "vinculo_enunciado":
        p["enunciado"] = c["texto"]
        if c["id"] in {"H11A", "H11B"}:
            a, _, b = c["texto"].partition(";")
            p["enunciado"] = a if c["id"] == "H11A" else b.strip()
    return p


def medir(c, modo, *, p=None, motivo="stop", status=200):
    p = proposta(c, modo) if p is None else p
    return MEDIR(c, modo=modo, post=lambda *a, **k: SimpleNamespace(status_code=status,
        text=json.dumps({"done": True, "done_reason": motivo, "message": {"content": json.dumps(p)}})))


def materializar(c, predicado, papel="nome_designacao"):
    return sonda.materializar_vinculo(c, sonda.papel.preparar_entrada(c), {"predicado": predicado, "papel": papel})


def test_texto_do_intervalo_e_da_fonte_original_com_identidade_e_offsets():
    for c in CASOS:
        p = proposta(c, "predicado_host")
        r = materializar(c, p["predicado"], p["papel"])
        assert r["vinculo_estrutural_valido"] is True
        i = r["intervalo_ligacao"]
        assert i["texto"] == c["texto"][i["inicio"]:i["fim"]]
        foco = sonda.papel.preparar_entrada(c)["foco"]
        assert (i["objeto"]["inicio"], i["objeto"]["fim"]) == (foco["inicio"], foco["fim"])
        assert all(r[k] is False for k in sonda.BASE)


def test_predicado_sem_recopia_do_enunciado_preserva_aspas_originais():
    c = POR_ID["H01A"]
    p = proposta(c, "vinculo_enunciado")
    p["enunciado"] = p["enunciado"].translate(str.maketrans({"“": '"', "”": '"'}))
    velho = sonda.anterior.conferir_vinculo(c, sonda.papel.preparar_entrada(c), p)
    assert velho["estado"] == "proposicao_sem_ancora_unica"
    novo = materializar(c, p["predicado"])
    assert novo["vinculo_estrutural_valido"] is True
    assert "“" in novo["intervalo_ligacao"]["texto"]
    assert novo["intervalo_ligacao"]["texto"] in c["texto"]


def test_segunda_ocorrencia_nao_e_substituida_por_primeira_string_igual():
    a = materializar(POR_ID["H11A"], "título")
    b = materializar(POR_ID["H11B"], "aparece como ordem")
    assert a["vinculo_estrutural_valido"] is b["vinculo_estrutural_valido"] is True
    assert a["intervalo_ligacao"]["objeto"]["fim"] < b["intervalo_ligacao"]["objeto"]["inicio"]
    errado = materializar(POR_ID["H11B"], "título")
    assert errado["estado"] == "objeto_fora_da_proposicao_ou_ambiguo"
    assert errado["intervalo_ligacao"] is None


@pytest.mark.parametrize("predicado", ["nome", "nome inexistente"])
def test_predicado_ambiguo_ou_ausente_nao_escolhe_mais_proximo(predicado):
    c = {"id": "teste", "foco_id": "c1", "texto": 'O nome "abra" é um nome curto.'}
    r = materializar(c, predicado)
    assert r["estado"] == "predicado_fora_da_proposicao_ou_ambiguo"
    assert r["intervalo_ligacao"] is None


@pytest.mark.parametrize("predicado", ["mova", "denominado “mova relatório.csv”"])
def test_predicado_sobreposto_ao_foco_e_recusado(predicado):
    r = materializar(POR_ID["H05A"], predicado)
    assert r["estado"] == "predicado_sobrepoe_foco"
    assert r["intervalo_ligacao"] is None


def test_predicado_externo_em_aspas_aninhadas_pode_ser_ancorado():
    r = materializar(POR_ID["H04A"], "denominada")
    assert r["vinculo_estrutural_valido"] is True
    assert r["intervalo_ligacao"]["aspas_do_predicado"] == ["q0"]
    assert r["intervalo_ligacao"]["aspas_do_objeto"] == ["q0", "q1"]


def test_vazio_e_revisao_pendente_preserva_papel_proposto():
    r = materializar(POR_ID["U04"], "", "operacao_mencionada")
    assert r["estado"] == "predicado_vazio_revisao_pendente"
    assert r["papel_proposto"] == "operacao_mencionada" and r["intervalo_ligacao"] is None
    assert all(r[k] is False for k in sonda.BASE)


def test_predicado_gramatical_de_outra_oracao_nao_ganha_validade_semantica():
    c = POR_ID["H04A"]
    p = {"predicado": "começa amanhã", "papel": "nome_designacao"}
    a = sonda.aferir_caso(c, medir(c, "predicado_host", p=p), OURO[c["id"]])
    assert a["vinculo_estrutural_concluido"] is True and a["papel_alinhado_concluido"] is True
    assert a["pista_predicado_local_concluida"] is False
    assert a["papel_vinculo_pista_local_concluidos"] is False
    assert all(a[k] is False for k in sonda.BASE)


def test_pista_copiada_nao_corrige_papel_errado_automaticamente():
    c = POR_ID["H07A"]
    p = {"predicado": "é o título do gráfico", "papel": "expressao_sem_operacao"}
    a = sonda.aferir_caso(c, medir(c, "predicado_host", p=p), OURO[c["id"]])
    assert a["vinculo_estrutural_concluido"] is True and a["pista_predicado_local_concluida"] is True
    assert a["papel_alinhado_concluido"] is False


@pytest.mark.parametrize("tipo", ["fonte", "offset", "tipo", "extra"])
def test_host_adulterado_nao_materializa(tipo):
    c = POR_ID["H01A"]
    e = sonda.papel.preparar_entrada(c)
    if tipo == "fonte": e["fonte"]["texto"] += " "
    elif tipo == "offset": e["foco"]["inicio"] += 1
    elif tipo == "tipo": e["foco"]["inicio"] = float(e["foco"]["inicio"])
    else: e["autoriza_efeito"] = True
    r = sonda.materializar_vinculo(c, e, proposta(c, "predicado_host"))
    assert r["estado"] == "entrada_adulterada" and r["intervalo_ligacao"] is None


def test_shape_extra_recusado_mantendo_metrica_de_rotulo_simetrica():
    c = CASOS[0]
    for modo in sonda.MODOS:
        p = {**proposta(c, modo), "autoriza_efeito": True}
        a = sonda.aferir_caso(c, medir(c, modo, p=p), OURO[c["id"]])
        assert a["papel_alinhado_concluido"] is True and a["shape_valido_concluido"] is False
        assert a["vinculo_estrutural_concluido"] is False and a["autoriza_efeito"] is False


def test_requisicao_preserva_fonte_opcoes_e_baseline_sem_pistas_ou_gabarito():
    for c in CASOS:
        a, b = [sonda.preparar_requisicao(c, m) for m in sonda.MODOS]
        assert a == sonda.anterior.preparar_requisicao(c, "vinculo_enunciado")
        assert a["messages"][1] == b["messages"][1] and a["options"] == b["options"]
        assert set(json.loads(b["messages"][1]["content"])) == {"fonte", "foco", "aspas_sintaticas"}


@pytest.mark.parametrize("tipo", ["ausente", "duplicado", "host", "pedido", "flag", "nan", "contradicao"])
def test_replay_revalida_registro_completo(tipo):
    rs = [medir(c, m) for c in CASOS for m in sonda.MODOS]
    if tipo == "ausente": rs.pop()
    elif tipo == "duplicado": rs.append(deepcopy(rs[0]))
    elif tipo == "host": rs[0]["entrada_host"]["foco"]["inicio"] = False
    elif tipo == "pedido": rs[0]["requisicao"]["messages"][1]["content"] = "gabarito"
    elif tipo == "flag": rs[0]["autoriza_efeito"] = True
    elif tipo == "nan": rs[0]["duracao_consulta_s"] = float("nan")
    else: rs[0]["erro_consulta"] = "TimeoutError"
    assert sonda.resumir(rs)["tipo"] == "resumo_invalido"


def test_resumo_recalcula_bruto_inclui_falhas_no_denominador():
    rs = [medir(c, m) for c in CASOS for m in sonda.MODOS]
    for r in rs: r["afericao"] = {"papel_alinhado_concluido": False}
    rs[1] = medir(CASOS[0], "predicado_host", motivo="length")
    rs[3] = medir(CASOS[1], "predicado_host", status=500)
    resumo = sonda.resumir(rs)
    a, b = [resumo["bracos"][m] for m in sonda.MODOS]
    assert a["casos"] == b["casos"] == 32
    assert a["papel_vinculo_pista_local_concluidos"] == 32
    assert b["papel_vinculo_pista_local_concluidos"] == 30
    assert b["pares_compostos_alinhados"] == 10
    assert resumo["comparacoes"]["papel_alinhado_concluido"]["perdas"] == [c["id"] for c in CASOS[:2]]


def test_cli_preserva_ordem_metadados_pre_consulta_e_arquivo_exclusivo(monkeypatch, tmp_path):
    saida, chamadas = tmp_path / "predicado.jsonl", []
    def fake(c, *, modo):
        meta = json.loads(saida.read_text(encoding="utf-8").splitlines()[0])
        assert meta["referencias_host_pre_consulta"] == OURO
        assert meta["pistas_locais_pre_consulta"] == sonda.anterior.PISTAS_LOCAIS
        chamadas.append((c["id"], modo))
        return medir(c, modo)
    monkeypatch.setattr(sonda, "medir_caso", fake)
    monkeypatch.setattr(sonda.etapas.coordenadas, "digest_modelo", lambda: "teste")
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    antes = saida.read_bytes()
    assert len(antes.splitlines()) == 66 and len(chamadas) == 64
    assert chamadas == [(c["id"], m) for i, c in enumerate(CASOS)
        for m in (sonda.MODOS if i % 2 == 0 else tuple(reversed(sonda.MODOS)))]
    with pytest.raises(FileExistsError): sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 64

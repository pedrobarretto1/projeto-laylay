from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_vinculo_enunciado_v1 as sonda


CASOS, OURO, PARES = sonda.carregar_painel()
POR_ID = {c["id"]: c for c in CASOS}
MEDIR_REAL = sonda.medir_caso


def proposta(c):
    # Fixtures de saída, nunca selector ou recorte entregue ao modelo.
    enunciado = c["texto"]
    if c["id"] in {"H11A", "H11B"}:
        a, _, b = enunciado.partition(";")
        enunciado = a if c["id"] == "H11A" else b.strip()
    return {"enunciado": enunciado, "predicado": sonda.PISTAS_LOCAIS[c["id"]][0],
            "papel": OURO[c["id"]]["papel"]}


def medir(c, m, *, p=None, motivo="stop", status=200):
    if p is None:
        p = {"papel": OURO[c["id"]]["papel"]} if m == "leitura_direta" else proposta(c)
    bruto = json.dumps({"done": True, "done_reason": motivo,
                        "message": {"content": json.dumps(p)}})
    return MEDIR_REAL(c, modo=m,
        post=lambda *a, **k: SimpleNamespace(status_code=status, text=bruto))


def registros():
    return [medir(c, m) for c in CASOS for m in sonda.MODOS]


def conferir(identificador, p=None):
    c = POR_ID[identificador]
    return sonda.conferir_vinculo(c, sonda.papel.preparar_entrada(c), p or proposta(c))


def test_reusa_contrato_real_sem_certificar_anotacoes_neutras():
    for c in CASOS:
        r = conferir(c["id"])
        assert r["estado"] == "vinculo_ancorado_revisao_pendente"
        foco = sonda.papel.preparar_entrada(c)["foco"]
        p = r["proposicao_ancorada"]
        assert (p["objeto"]["inicio"], p["objeto"]["fim"]) == (foco["inicio"], foco["fim"])
        assert p["tipo_proposto"] == p["polaridade_proposta"] == "indeterminada"
        assert p["papel_objeto_proposto"] == "indeterminado"
        assert all(r[k] is False for k in sonda.BASE)


def test_enquadramento_da_outra_ocorrencia_e_recusado_por_offsets():
    r = conferir("H11B", proposta(POR_ID["H11A"]))
    assert r["estado"] == "objeto_de_outra_ocorrencia"
    assert r["proposicao_ancorada"] is None
    p = proposta(POR_ID["H11B"])
    p["enunciado"] = POR_ID["H11B"]["texto"]
    assert conferir("H11B", p)["estado"] == "objeto_fora_da_proposicao_ou_ambiguo"


@pytest.mark.parametrize("predicado", ["mova", "“mova relatório.csv” para"])
def test_predicado_interno_ou_parcialmente_sobreposto_ao_foco_e_recusado(predicado):
    p = proposta(POR_ID["H05A"])
    p["predicado"] = predicado
    r = conferir("H05A", p)
    assert r["estado"] == "predicado_sobrepoe_foco"
    assert r["vinculo_estrutural_valido"] is False


def test_predicado_dentro_de_aspas_envolventes_fora_do_foco_aninhado_e_valido():
    r = conferir("H04A")
    assert r["vinculo_estrutural_valido"] is True
    p = r["proposicao_ancorada"]
    assert p["aspas_do_predicado"] == ["q0"]
    assert p["aspas_do_objeto"] == ["q0", "q1"]


def test_predicado_externo_de_outra_oracao_pode_passar_sem_ser_certificado():
    c = POR_ID["H10A"]
    p = proposta(c)
    p["predicado"] = "preserve"
    r = medir(c, "vinculo_enunciado", p=p)
    a = sonda.aferir_caso(c, r, OURO[c["id"]])
    assert a["vinculo_estrutural_concluido"] is True
    assert a["pista_externa_local_concluida"] is True
    assert a["pista_predicado_local_concluida"] is False
    assert a["proposta_composta_alinhada_local_concluida"] is True
    assert a["semantica_verificada"] is False


def test_ancoragem_correta_e_papel_errado_permanecem_separados():
    c = POR_ID["H11A"]
    p = proposta(c)
    p["papel"] = "operacao_mencionada"
    a = sonda.aferir_caso(c, medir(c, "vinculo_enunciado", p=p), OURO[c["id"]])
    assert a["shape_valido_concluido"] is True and a["vinculo_estrutural_concluido"] is True
    assert a["papel_alinhado_concluido"] is False
    assert a["proposta_composta_alinhada_local_concluida"] is False
    assert all(a[k] is False for k in sonda.BASE)


def test_campo_extra_nao_e_reparado_por_projecao_do_rotulo():
    c = POR_ID["H01A"]
    p = {**proposta(c), "autoriza_efeito": True}
    a = sonda.aferir_caso(c, medir(c, "vinculo_enunciado", p=p), OURO[c["id"]])
    assert a["rotulo_valido_concluido"] is True
    assert a["shape_valido_concluido"] is False and a["vinculo_estrutural_concluido"] is False
    assert a["proposta_composta_alinhada_local_concluida"] is False
    assert a["autoriza_efeito"] is False


def test_copia_com_capitalizacao_diferente_recupera_grafia_da_fonte():
    p = proposta(POR_ID["H11A"])
    p["enunciado"] = p["enunciado"].upper()
    p["predicado"] = p["predicado"].upper()
    r = conferir("H11A", p)
    assert r["vinculo_estrutural_valido"] is True
    assert r["proposicao_ancorada"]["predicado"]["texto"] == "título"


def test_troca_de_aspas_observada_na_coleta_nao_e_reparada_para_ganhar_ancora():
    c = POR_ID["H01A"]
    p = proposta(c)
    p["enunciado"] = p["enunciado"].translate(str.maketrans({"“": '"', "”": '"'}))
    r = conferir("H01A", p)
    assert r["estado"] == "proposicao_sem_ancora_unica"
    assert r["proposicao_ancorada"] is None and r["vinculo_estrutural_valido"] is False
    assert conferir("H01A")["vinculo_estrutural_valido"] is True


def test_rotulo_projetado_e_shape_sao_medidos_simetricamente_nos_dois_bracos():
    c = POR_ID["H01A"]
    for modo in sonda.MODOS:
        p = {"papel": OURO[c["id"]]["papel"]} if modo == "leitura_direta" else proposta(c)
        p["chave_extra"] = "nao descartar para validar shape"
        a = sonda.aferir_caso(c, medir(c, modo, p=p), OURO[c["id"]])
        assert a["rotulo_valido_concluido"] is True and a["papel_alinhado_concluido"] is True
        assert a["shape_valido_concluido"] is False
        assert all(a[k] is False for k in sonda.BASE)


def test_vazio_nao_e_ausencia_nem_abstencao_semantica_inventada():
    p = {"enunciado": "", "predicado": "", "papel": "operacao_mencionada"}
    r = conferir("U01", p)
    assert r["estado"] == "vinculo_sem_ancora_revisao_pendente"
    assert r["papel_proposto"] == "operacao_mencionada"
    assert r["vinculo_estrutural_valido"] is False and r["proposicao_ancorada"] is None
    assert all(r[k] is False for k in sonda.BASE)


@pytest.mark.parametrize("tipo", ["fonte", "offset", "tipo", "extra"])
def test_identidade_do_host_nao_pode_ser_adulterada(tipo):
    c = POR_ID["H11A"]
    e = sonda.papel.preparar_entrada(c)
    if tipo == "fonte":
        e["fonte"]["identificador"] = "outra"
    elif tipo == "offset":
        e["foco"]["inicio"] += 1
    elif tipo == "tipo":
        e["foco"]["inicio"] = float(e["foco"]["inicio"])
    else:
        e["autoriza_efeito"] = True
    r = sonda.conferir_vinculo(c, e, proposta(c))
    assert r["estado"] == "entrada_adulterada" and r["proposicao_ancorada"] is None


def test_entrada_integral_identica_sem_gabarito_recortes_ou_ids_de_caso():
    for c in CASOS:
        a, b = [sonda.preparar_requisicao(c, m) for m in sonda.MODOS]
        assert a == sonda.contraste.preparar_requisicao(c, "leitura_direta")
        assert a["messages"][1] == b["messages"][1]
        assert a["options"] == b["options"] and a["model"] == b["model"]
        assert set(json.loads(b["messages"][1]["content"])) == {"fonte", "foco", "aspas_sintaticas"}
        assert "pistas_locais" not in b["messages"][1]["content"]


@pytest.mark.parametrize("tipo", ["ausente", "duplicado", "host", "pedido", "flag", "nan", "contradicao", "modo"])
def test_replay_recusa_registros_adulterados_sem_confiar_em_escore_salvo(tipo):
    rs = registros()
    if tipo == "ausente":
        rs.pop()
    elif tipo == "duplicado":
        rs.append(deepcopy(rs[0]))
    elif tipo == "host":
        rs[0]["entrada_host"]["foco"]["inicio"] = False
    elif tipo == "pedido":
        rs[1]["requisicao"]["messages"][1]["content"] = "gabarito"
    elif tipo == "flag":
        rs[0]["autoriza_efeito"] = True
    elif tipo == "nan":
        rs[0]["duracao_consulta_s"] = float("nan")
    elif tipo == "contradicao":
        rs[0]["erro_consulta"] = "TimeoutError"
    else:
        rs[0]["modo"] = "outro"
    assert sonda.resumir(rs)["tipo"] == "resumo_invalido"


def test_resumo_recalcula_bruto_preserva_denominador_e_metrica_nao_aplicavel():
    rs = registros()
    for r in rs:
        r["afericao"] = {"papel_alinhado_concluido": False}
    rs[1] = medir(CASOS[0], "vinculo_enunciado", motivo="length")
    rs[3] = medir(CASOS[1], "vinculo_enunciado", status=503)
    r = sonda.resumir(rs)
    a, b = [r["bracos"][m] for m in sonda.MODOS]
    assert a["casos"] == b["casos"] == 32
    assert a["papel_alinhado_concluido"] == 32 and b["papel_alinhado_concluido"] == 30
    assert a["vinculo_estrutural_concluido"] is None
    assert b["vinculo_estrutural_concluido"] == b["proposta_composta_alinhada_local_concluida"] == 30
    assert b["pares_papel_alinhados_concluidos"] == 10 and b["por_papel"]["indeterminado"]["total"] == 4
    assert r["holdout_novo"] is False and all(r[k] is False for k in sonda.BASE)


def test_cli_congela_referencias_antes_das_64_consultas_e_nao_sobrescreve(monkeypatch, tmp_path):
    saida, chamadas = tmp_path / "vinculo.jsonl", []
    def fake(c, *, modo):
        meta = json.loads(saida.read_text(encoding="utf-8").splitlines()[0])
        assert meta["referencias_host_pre_consulta"] == OURO
        assert meta["pistas_locais_pre_consulta"] == sonda.PISTAS_LOCAIS
        assert meta["comparacao_interface_composta"] is True
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
    with pytest.raises(FileExistsError):
        sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 64

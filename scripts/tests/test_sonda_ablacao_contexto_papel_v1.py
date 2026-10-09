from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_ablacao_contexto_papel_v1 as sonda


CASOS, OURO = sonda.carregar_base()


def medir(c, v, m, *, p=None, motivo="stop"):
    proposta = {"papel": OURO[c["id"]]["papel"]} if p is None else p
    bruto = json.dumps({"done": True, "done_reason": motivo,
                        "message": {"content": json.dumps(proposta)}})
    return sonda.medir_caso(c, variante=v, modo=m,
        post=lambda *a, **k: SimpleNamespace(status_code=200, text=bruto))


def registros():
    return [medir(c, v, m) for c in CASOS for v in sonda.VARIANTES for m in sonda.MODOS]


def test_projecao_literal_sem_reescrita_ou_classificador_privado():
    for c in CASOS:
        foco_original = sonda.papel.preparar_entrada(c)["foco"]
        for v in sonda.VARIANTES:
            p, mapa = sonda.projetar_caso(c, v)
            assert p["texto"] == c["texto"][mapa["inicio_na_fonte_original"]:mapa["fim_na_fonte_original"]]
            f = sonda.papel.preparar_entrada(p)["foco"]
            assert f["texto"] == foco_original["texto"]
            assert f["inicio"] + mapa["inicio_na_fonte_original"] == foco_original["inicio"]
            assert f["fim"] + mapa["inicio_na_fonte_original"] == foco_original["fim"]
            assert mapa["suporte_semantico_verificado"] is False
            if c["id"] not in sonda.RECORTES:
                assert p == c and mapa["fonte_alterada"] is False


def test_segunda_ocorrencia_nao_vira_primeira_na_fonte_original():
    c = next(c for c in CASOS if c["id"] == "H11B")
    p, mapa = sonda.projetar_caso(c, "recorte_diagnostico")
    assert c["foco_id"] == "c2" and p["foco_id"] == "c1"
    assert mapa["foco_original"]["inicio"] > c["texto"].index(mapa["foco_original"]["texto"])
    assert mapa["foco_projetado"]["inicio"] + mapa["inicio_na_fonte_original"] == mapa["foco_original"]["inicio"]


def test_input_nao_recebe_recorte_gabarito_mapa_ou_metadados_extras():
    for c in CASOS:
        for v in sonda.VARIANTES:
            for m in sonda.MODOS:
                r = medir(c, v, m)
                p, _ = sonda.projetar_caso(c, v)
                assert r["requisicao"] == sonda.transferencia.contraste.preparar_requisicao(p, m)
                assert set(json.loads(r["requisicao"]["messages"][1]["content"])) == {"fonte", "foco", "aspas_sintaticas"}


def test_guarda_de_integridade_nao_alega_detectar_papel_semanticamente_errado():
    c = next(c for c in CASOS if c["id"] == "H11A")
    r = medir(c, "integral", "leitura_direta", p={"papel": "operacao_mencionada"})
    a = sonda.aferir_caso(c, r, OURO[c["id"]])
    assert a["saida_valida_concluida"] is True and a["papel_alinhado_concluido"] is False
    assert a["estado_papel"] == "papel_proposto_revisao_pendente"
    assert all(a[k] is False for k in sonda.BASE)


def test_resumo_separa_intervencao_controle_e_indeterminacao():
    rs = registros()
    rs[0] = medir(CASOS[0], "integral", "prompt_atual", p={"papel": "operacao_mencionada"})
    for r in rs:
        r["afericao"] = {"papel_alinhado_concluido": False}
    resumo = sonda.resumir(rs)
    assert resumo["recorte_manual_nao_seletor"] is True and resumo["holdout_novo"] is False
    assert resumo["bracos"]["prompt_atual/integral"]["alinhados_concluidos"] == 9
    for b in resumo["bracos"].values():
        assert b["casos"] == 10 and b["saida_valida_concluida"] == 10
        assert b["grupos"]["intervencoes"]["casos"] == 4
        assert b["grupos"]["controles_identicos"]["casos"] == 6
        assert b["grupos"]["indeterminados"]["casos"] == 4
    assert resumo["comparacoes"]["prompt_atual"]["contagens"] == {"ganho": 1, "ambos_alinhados": 9}
    assert all(resumo[k] is False for k in sonda.BASE)


@pytest.mark.parametrize("tipo", ["ausente", "duplicata", "mapa", "fonte", "flag", "variante", "nan", "contradicao"])
def test_replay_fail_closed_diante_de_registros_adulterados(tipo):
    rs = registros()
    if tipo == "ausente":
        rs.pop()
    elif tipo == "duplicata":
        rs.append(deepcopy(rs[0]))
    elif tipo == "mapa":
        rs[0]["mapa_projecao"]["inicio_na_fonte_original"] = False
    elif tipo == "fonte":
        rs[2]["requisicao"]["messages"][1]["content"] = "gabarito"
    elif tipo == "flag":
        rs[0]["autoriza_efeito"] = True
    elif tipo == "variante":
        rs[0]["variante"] = "outra"
    elif tipo == "nan":
        rs[0]["duracao_consulta_s"] = float("nan")
    else:
        rs[0]["erro_consulta"] = "TimeoutError"
    assert sonda.resumir(rs)["tipo"] == "resumo_invalido"


def test_finalizacao_incompleta_permanece_no_denominador():
    rs = registros()
    rs[2] = medir(CASOS[0], "recorte_diagnostico", "prompt_atual", motivo="length")
    b = sonda.resumir(rs)["bracos"]["prompt_atual/recorte_diagnostico"]
    assert b["casos"] == 10 and b["alinhados_concluidos"] == 9


def test_cli_congela_40_chamadas_antes_de_consultar_e_nao_sobrescreve(monkeypatch, tmp_path):
    saida, chamadas = tmp_path / "ablacao.jsonl", []
    def fake(c, *, variante, modo):
        meta = json.loads(saida.read_text(encoding="utf-8").splitlines()[0])
        assert meta["recortes_manuais_pre_consulta"] == sonda.RECORTES
        assert meta["referencias_host_pre_consulta"] == OURO
        chamadas.append((c["id"], variante, modo))
        return real(c, variante=variante, modo=modo, post=lambda *a, **k: SimpleNamespace(
            status_code=200, text=json.dumps({"done": True, "done_reason": "stop",
                "message": {"content": json.dumps({"papel": OURO[c["id"]]["papel"]})}})))
    real = sonda.medir_caso
    monkeypatch.setattr(sonda, "medir_caso", fake)
    monkeypatch.setattr(sonda.etapas.coordenadas, "digest_modelo", lambda: "teste")
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    antes = saida.read_bytes()
    assert len(antes.splitlines()) == 42 and len(chamadas) == 40
    assert chamadas == [(c["id"], v, m) for i, c in enumerate(CASOS)
        for v in (sonda.VARIANTES if i % 2 == 0 else tuple(reversed(sonda.VARIANTES)))
        for m in (sonda.MODOS if i % 2 == 0 else tuple(reversed(sonda.MODOS)))]
    with pytest.raises(FileExistsError):
        sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 40


def quadro_de_proposicoes():
    caso = next(c for c in CASOS if c["id"] == "H11A")
    fonte = sonda.papel.literal.FonteDidatica(**sonda.papel.preparar_entrada(caso)["fonte"])
    proposta = {"molduras": [], "proposicoes": [
        {"id": "p1", "fonte_id": "f1", "tipo": "estado", "trecho": sonda.RECORTES["H11A"],
         "predicado": "recebeu", "objeto": "abra o registro", "papel_objeto": "texto",
         "polaridade": "positiva", "moldura_id": ""},
        {"id": "p2", "fonte_id": "f1", "tipo": "estado", "trecho": sonda.RECORTES["H11B"],
         "predicado": "aparece", "objeto": "abra o registro", "papel_objeto": "texto",
         "polaridade": "positiva", "moldura_id": ""},
    ]}
    return fonte, proposta


def test_contrato_existente_ancora_objetos_iguais_na_proposicao_correta():
    fonte, proposta = quadro_de_proposicoes()
    r = sonda.papel.literal.contrato.conferir_proposicoes_mencionadas((fonte,), proposta, escopo=fonte.escopo)
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    a, b = r["proposicoes"]
    assert a["objeto"]["texto"] == b["objeto"]["texto"] == "abra o registro"
    assert a["objeto"]["fim"] < b["objeto"]["inicio"]
    for p, identificador in ((a, "H11A"), (b, "H11B")):
        c = next(c for c in CASOS if c["id"] == identificador)
        foco = sonda.papel.preparar_entrada(c)["foco"]
        assert p["objeto"]["inicio"] == foco["inicio"] and p["objeto"]["fim"] == foco["fim"]
    assert all(r[k] is False for k in sonda.BASE)


def test_predicado_da_outra_proposicao_nao_e_emprestado_e_recusa_atomica():
    fonte, proposta = quadro_de_proposicoes()
    proposta["proposicoes"][1]["predicado"] = "recebeu"
    r = sonda.papel.literal.contrato.conferir_proposicoes_mencionadas((fonte,), proposta, escopo=fonte.escopo)
    assert r["estado"] == "predicado_fora_da_proposicao_ou_ambiguo"
    assert r["proposicoes"] == [] and r["molduras"] == []


def test_ancoragem_existente_nao_certifica_papel_semantico_por_contencao():
    fonte, proposta = quadro_de_proposicoes()
    proposta["proposicoes"][0]["papel_objeto"] = "entidade"
    r = sonda.papel.literal.contrato.conferir_proposicoes_mencionadas((fonte,), proposta, escopo=fonte.escopo)
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert r["proposicoes"][0]["papel_objeto_proposto"] == "entidade"
    assert all(r[k] is False for k in sonda.BASE)

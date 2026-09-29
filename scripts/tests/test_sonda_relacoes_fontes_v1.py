"""Citação/ordem conferidas não autorizam a relação semântica proposta."""

from copy import deepcopy

import pytest

from scripts.analises import sonda_relacoes_fontes_v1 as sonda
from scripts.analises.contrato_vigencia_criterios import RegistroVigenciaCriterios


CASOS, REVISAO = sonda.carregar_painel()


def _proposta(caso):
    return {"relacoes": [{"fonte_id": f"f{i+1}", "relacao": r, "citacao": t}
                         for i, (r, t) in enumerate(zip(REVISAO[caso["id"]], caso["posteriores"]))]}


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
def test_relacao_alinhada_permanece_proposta_sem_autoridade(caso, monkeypatch):
    def proibida(*args, **kwargs):
        raise AssertionError("sonda nao pode registrar vigencia")

    monkeypatch.setattr(RegistroVigenciaCriterios, "registrar_revisao", proibida)
    entradas = []

    def consultar(sistema, entrada, formato, **kwargs):
        entradas.append(entrada)
        assert set(entrada) == {"alvo_id", "fontes_em_ordem"}
        assert [f["texto"] for f in entrada["fontes_em_ordem"]] == [caso["alvo"], *caso["posteriores"]]
        return _proposta(caso)

    resultado = sonda.medir_caso(caso, REVISAO[caso["id"]], consulta=consultar)
    assert len(entradas) == 1
    assert resultado["alinhado_revisao_local"] is True
    assert resultado["conferencia"]["estado"] == "relacoes_ancoradas_revisao_pendente"
    for campo in ("relacao_semantica_verificada", "aprovado_para_producao", "autoriza_efeito", "pode_registrar_vigencia"):
        assert resultado["conferencia"][campo] is False


@pytest.mark.parametrize("mudanca", ["omissao", "duplicacao", "ordem", "citacao", "extra", "tipo", "alvo"])
def test_adulteracao_de_cobertura_e_ancora_rejeitada(mudanca):
    caso = next(c for c in CASOS if c["id"] == "C09")
    proposta = _proposta(caso)
    itens = proposta["relacoes"]
    if mudanca == "omissao":
        itens.pop()
    elif mudanca == "duplicacao":
        itens[1] = deepcopy(itens[0])
    elif mudanca == "ordem":
        itens.reverse()
    elif mudanca == "citacao":
        itens[1]["citacao"] = "A regra esta valida."
    elif mudanca == "extra":
        proposta["vigente"] = True
    elif mudanca == "tipo":
        itens[0]["relacao"] = {"revoga": True}
    else:
        itens[0]["fonte_id"] = "f0"
    assert sonda.conferir_proposta(caso, proposta)["estado"] != "relacoes_ancoradas_revisao_pendente"


def test_citacao_correta_com_relacao_errada_nao_prova_semantica():
    caso = CASOS[0]
    proposta = _proposta(caso)
    proposta["relacoes"][0]["relacao"] = "mantem"
    resultado = sonda.medir_caso(caso, REVISAO[caso["id"]], consulta=lambda *a, **k: proposta)
    assert resultado["conferencia"]["estado"] == "relacoes_ancoradas_revisao_pendente"
    assert resultado["alinhado_revisao_local"] is False
    assert resultado["conferencia"]["pode_registrar_vigencia"] is False


def test_revisao_nao_muda_entrada_ou_formato_do_modelo():
    chamadas = []
    caso = CASOS[0]
    def consultar(sistema, entrada, formato, **kwargs):
        chamadas.append((sistema, entrada, formato, kwargs))
        return _proposta(caso)
    sonda.medir_caso(caso, ["revoga"], consulta=consultar)
    sonda.medir_caso(caso, ["mantem"], consulta=consultar)
    assert chamadas[0] == chamadas[1]


def test_painel_recusa_mudanca_apos_congelamento(tmp_path, monkeypatch):
    caminho = tmp_path / "painel.json"
    caminho.write_bytes(sonda.ENTRADAS.read_bytes() + b" ")
    monkeypatch.setattr(sonda, "ENTRADAS", caminho)
    with pytest.raises(ValueError, match="congelamento"):
        sonda.carregar_painel()


def test_isolamento_fixa_fontes_e_preserva_contexto_completo():
    caso = next(c for c in CASOS if c["id"] == "C10")
    chamadas = []
    def consultar(sistema, entrada, formato, **kwargs):
        indice = len(chamadas)
        chamadas.append(entrada)
        assert entrada["fonte_em_analise"] == f"f{indice+1}"
        assert entrada["fontes_em_ordem"] == sonda.preparar_entrada(caso)["fontes_em_ordem"]
        assert set(formato["properties"]) == {"relacao"}
        return {"relacao": REVISAO[caso["id"]][indice]}
    resultado = sonda.medir_caso(caso, REVISAO[caso["id"]], consulta=consultar, relacao_isolada=True)
    assert len(chamadas) == 2
    assert resultado["proposta"] == _proposta(caso)
    assert resultado["alinhado_revisao_local"] is True
    assert resultado["conferencia"]["pode_registrar_vigencia"] is False


@pytest.mark.parametrize("bruto", [None, {}, {"relacao": "inexistente"},
                                 {"relacao": "mantem", "fonte_id": "f0"}])
def test_isolamento_recusa_injecao_de_autoridade_ou_formato(bruto):
    resultado = sonda.medir_caso(CASOS[0], REVISAO["C01"], consulta=lambda *a, **k: bruto,
                                 relacao_isolada=True)
    assert resultado["erro"] == "relacao_invalida"
    assert resultado["alinhado_revisao_local"] is False

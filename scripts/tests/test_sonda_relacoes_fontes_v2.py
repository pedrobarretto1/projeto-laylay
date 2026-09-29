"""Decomposição proposta não vira autorização nem revisão de vigência."""

import pytest

from scripts.analises import sonda_relacoes_fontes_v2 as sonda
from scripts.analises.contrato_vigencia_criterios import RegistroVigenciaCriterios


@pytest.mark.parametrize("ato,alvo,operacao,relacao", [
    ("pergunta", "regra_alvo", "revoga", "sem_alteracao"),
    ("citacao_sem_adocao", "regra_alvo", "revoga", "sem_alteracao"),
    ("hipotese", "regra_alvo", "substitui", "sem_alteracao"),
    ("pedido_acao", "regra_alvo", "revoga", "revoga"),
    ("relato", "outra_regra", "revoga", "sem_alteracao"),
    ("relato", "regra_alvo", "revoga", "revoga"),
    ("pedido_acao", "regra_alvo", "mantem", "mantem"),
    ("pedido_acao", "regra_alvo", "substitui", "substitui"),
    ("pedido_acao", "regra_alvo", "restaura", "restaura"),
    ("relato", "indeterminado", "revoga", "indeterminada"),
    ("outro", "nenhum", "nenhuma", "sem_alteracao"),
    ("outro", "regra_alvo", "revoga", "indeterminada"),
    ("indeterminado", "regra_alvo", "revoga", "indeterminada"),
])
def test_contrato_tipa_relacao_sem_provar_os_rotulos(ato, alvo, operacao, relacao):
    resultado = sonda.conferir_decomposicao(dict(ato=ato, alvo=alvo, operacao=operacao))
    assert resultado["relacao"] == relacao
    assert resultado["estado"] == "decomposicao_tipada_revisao_pendente"
    for k in ("relacao_semantica_verificada", "aprovado_para_producao", "autoriza_efeito", "pode_registrar_vigencia"):
        assert resultado[k] is False


@pytest.mark.parametrize("proposta", [None, [], {},
    {"ato": "pedido_acao", "alvo": "regra_alvo", "operacao": "revoga", "autoriza": True},
    {"ato": "pedido_acao", "alvo": [], "operacao": "revoga"},
    {"ato": "pedido_acao", "alvo": "regra_alvo", "operacao": "execute"},
])
def test_formato_desconhecido_falha_fechado(proposta):
    assert sonda.conferir_decomposicao(proposta)["estado"] == "decomposicao_invalida"


def test_contexto_e_fontes_do_host_sem_gabarito_nem_registro(monkeypatch):
    caso = {"id": "teste", "alvo": "Regra original", "posteriores": ["Revogue", "Restaure"]}
    chamadas = []
    def proibida(*a, **k):
        raise AssertionError("proposta nao pode registrar vigencia")
    monkeypatch.setattr(RegistroVigenciaCriterios, "registrar_revisao", proibida)
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append(entrada)
        assert set(entrada) == {"alvo_id", "fontes_em_ordem", "fonte_em_analise"}
        assert len(entrada["fontes_em_ordem"]) == 3
        indice = len(chamadas)
        assert entrada["fonte_em_analise"] == entrada["fontes_em_ordem"][indice]
        return {"ato": "pedido_acao", "alvo": "regra_alvo", "operacao": "revoga" if indice == 1 else "restaura"}
    resultado = sonda.medir_caso(caso, ["revoga", "restaura"], consulta=consulta)
    assert len(chamadas) == 2
    assert resultado["alinhado_revisao_local"] is True
    assert [r["citacao"] for r in resultado["proposta"]["relacoes"]] == caso["posteriores"]
    assert resultado["conferencia"]["pode_registrar_vigencia"] is False


def test_rotulos_errados_podem_ser_bem_tipados_mas_nao_ganham_autoridade():
    caso = {"id": "teste", "alvo": "Regra original", "posteriores": ["Essa regra foi revogada?"]}
    consulta = lambda *a, **k: {"ato": "relato", "alvo": "regra_alvo", "operacao": "revoga"}
    resultado = sonda.medir_caso(caso, ["sem_alteracao"], consulta=consulta)
    assert resultado["alinhado_revisao_local"] is False
    assert resultado["conferencia"]["relacao_semantica_verificada"] is False


def test_revisao_nunca_muda_entrada_do_modelo():
    caso = {"id": "teste", "alvo": "Regra original", "posteriores": ["Essa regra foi revogada?"]}
    entradas = []
    def consultar(sistema, entrada, formato, **kwargs):
        entradas.append((sistema, entrada, formato, kwargs))
        return {"ato": "pergunta", "alvo": "regra_alvo", "operacao": "revoga"}
    sonda.medir_caso(caso, ["revoga"], consulta=consultar)
    sonda.medir_caso(caso, ["sem_alteracao"], consulta=consultar)
    assert entradas[0] == entradas[1]


def test_painel_congelado_nao_usa_pontuacao_como_gabarito():
    casos, revisao = sonda.carregar_painel()
    assert len(casos) == 12
    assert "?" not in casos[0]["posteriores"][0]
    assert revisao["N01"] == ["sem_alteracao"]
    assert casos[1]["posteriores"][0].endswith("?")
    assert revisao["N02"] == ["revoga"]


def test_loader_recusa_reescrever_painel(tmp_path, monkeypatch):
    caminho = tmp_path / "painel.json"
    caminho.write_bytes(sonda.ENTRADAS.read_bytes() + b" ")
    monkeypatch.setattr(sonda, "ENTRADAS", caminho)
    with pytest.raises(ValueError, match="congelamento"):
        sonda.carregar_painel()

"""Testa a medição, não certifica o runtime nem redefine seu RED como gold."""
from copy import deepcopy

from scripts.analises.sonda_escopo_propostas_mistas import avaliar_fronteiras, painel


def _validacao(comandos):
    return {"comandos": comandos, "proposta_vinculada": True, "ocorrencia_vinculada": True}


def test_painel_tem_controles_e_operacoes_e_alvos_concorrentes():
    casos = painel()
    assert len(casos) == 28 and len({c["id"] for c in casos}) == 28
    assert {c["id"] for c in casos[24:]} == {"conector_app_midia", "conector_volume_app",
        "conector_pedido_negado", "conector_pergunta"}
    assert sum(c["id"].startswith("controle_") for c in casos) == 4
    for ident in ("mesmo_intent_operacoes", "mesmo_intent_alvos", "iot_operacao_e_alvo"):
        caso = next(c for c in casos if c["id"] == ident)
        a, b = caso["propostos"]
        assert a["intent"] == b["intent"] and a["params"] != b["params"]
        assert caso["esperados"] == [a]


def test_medicao_nao_confunde_vinculo_valido_com_escopo_autorizado():
    caso = painel()[0]
    falhas = avaliar_fronteiras(caso, {"autoriza_execucao": True},
                              _validacao(caso["propostos"]), caso["propostos"])
    assert falhas == ["admissao_sem_vinculo_a_ato_autorizado",
                      "fronteira_executor_recebeu_escopo_divergente"]
    assert avaliar_fronteiras(caso, {"autoriza_execucao": True},
                             _validacao(caso["esperados"]), caso["esperados"]) == []


def test_primeira_fronteira_vermelha_precede_sintomas_posteriores():
    caso = painel()[0]
    validacao = _validacao(caso["propostos"])
    validacao["ocorrencia_vinculada"] = False
    falhas = avaliar_fronteiras(caso, {"autoriza_execucao": False}, validacao, caso["propostos"])
    assert falhas[0] == "classificacao_divergente"
    assert falhas[1] == "ocorrencia_nao_vinculada"
    assert len(falhas) == 4


def test_vigencia_nao_revoga_autorizacao_mas_interrompe_chamada():
    caso = next(c for c in painel() if c["id"] == "controle_vigencia")
    assert caso["vigente"] is False
    assert avaliar_fronteiras(caso, {"autoriza_execucao": True}, _validacao(caso["propostos"]), []) == []
    assert avaliar_fronteiras(caso, {"autoriza_execucao": True}, _validacao(caso["propostos"]), caso["propostos"]) == [
        "fronteira_executor_recebeu_escopo_divergente"]


def test_painel_e_fontes_nao_compartilham_arvores_mutaveis():
    casos = painel()
    antes = deepcopy(casos)
    casos[0]["propostos"][0]["params"]["acao"] = "inventada"
    assert painel() == antes
    assert casos[0]["esperados"][0]["params"]["acao"] == "pause"


def test_ampliacao_opcional_de_ato_unico_preserva_painel_historico_e_controles_positivos():
    ampliado = painel(incluir_unicos=True)
    assert ampliado[:28] == painel()
    assert len(ampliado) == 37
    novos = ampliado[28:]
    assert all(c["id"].startswith("unico_") and c["esperados"] for c in novos)
    assert all(c["esperados"][0] in c["propostos"] for c in novos)
    ampliado[28]["propostos"][1]["params"]["delta"] = 99
    assert painel(incluir_unicos=True)[28]["esperados"][0]["params"]["delta"] == 10

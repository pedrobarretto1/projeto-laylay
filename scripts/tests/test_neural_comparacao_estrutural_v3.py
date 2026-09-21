from copy import deepcopy

import pytest

from mente_laylay.neural.comparar_lote_estrutural_v3 import carregar_lote, preparar_dobras, resumir


def test_dobras_preservam_grupos_irmaos_e_todos_os_casos():
    exemplos, sidecars = carregar_lote()
    vistos = []
    for tr, te in preparar_dobras(exemplos):
        assert len(tr) == 132 and len(te) == 12
        assert not {exemplos[i]["grupo_construcao"] for i in tr} & {exemplos[i]["grupo_construcao"] for i in te}
        assert not {exemplos[i]["grupo_contraste"] for i in tr} & {exemplos[i]["grupo_contraste"] for i in te}
        vistos.extend(te)
    assert sorted(vistos) == list(range(144))
    assert all(c["treino_permitido"] is False for c in sidecars)
    assert all(set(e["entrada"]) == {"texto_entrada", "segmentos"} for e in exemplos)


def test_dobra_incompleta_nao_e_descartada():
    exemplos, _ = carregar_lote()
    with pytest.raises(ValueError, match="incompleta"):
        preparar_dobras(exemplos[:-1])


@pytest.mark.parametrize("campo,valor", [("pedidos_inventados", 1), ("acoes_extras", 1),
                                         ("casos_exatos_acao_sem_alvos", 136), ("casos", 143)])
def test_gate_nao_promove_e_rejeita_seguranca_ou_cobertura_insuficiente(campo, valor):
    totais = {"casos": 144, "casos_exatos_acao_sem_alvos": 144, "acoes_esperadas": 144,
              "acoes_ausentes": 0, "acoes_extras": 0, "pedidos_inventados": 0}
    assert resumir([{"teste": totais}])["apto_para_avaliar_alvos"] is True
    assert resumir([{"teste": totais}])["autoriza_promocao"] is False
    alterado = deepcopy(totais)
    alterado[campo] = valor
    assert resumir([{"teste": alterado}])["apto_para_avaliar_alvos"] is False


def test_ausencia_de_resultados_nao_vira_green():
    assert resumir([])["apto_para_avaliar_alvos"] is False

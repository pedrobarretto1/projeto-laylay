from __future__ import annotations

from copy import deepcopy

import pytest

from mente_laylay.neural.datasets.gerar_volume_intent_gate_absoluto_v10_minimo import (
    GATE_FAMILIAS,
    GATE_NIVEIS,
    NIVEIS_TREINO,
    VALORES_PROTEGIDOS,
    gerar_exemplos,
    validar_lote,
)


def test_v10_concentra_gate_e_mantem_intent_em_todos():
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)

    assert resumo["total"] == 24
    assert resumo["intent_only"] == 16
    assert resumo["intent_gate"] == 8
    assert resumo["niveis_treino"] == sorted(NIVEIS_TREINO)
    assert resumo["valores_protegidos"] == sorted(VALORES_PROTEGIDOS)
    assert len({x["text"].casefold() for x in exemplos}) == 24
    assert all("intent" in x["training_heads"] for x in exemplos)

    gate = [x for x in exemplos if "intent_gate" in x["training_heads"]]
    assert len(gate) == len(GATE_FAMILIAS) * len(GATE_NIVEIS) == 8
    assert all(x["nivel_experimental"] in GATE_NIVEIS for x in gate)


@pytest.mark.parametrize("mutacao", ["head", "intent", "valor"])
def test_v10_rejeita_contrato_invalido(mutacao):
    itens = deepcopy(gerar_exemplos())
    if mutacao == "head":
        itens[0]["training_heads"] = ["intent", "intent_gate"]
    elif mutacao == "intent":
        itens[0]["intent"] = "NONE"
    else:
        itens[0]["text"] = "coloca o volume em 59"

    with pytest.raises(ValueError):
        validar_lote(itens)

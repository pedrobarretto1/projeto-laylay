from __future__ import annotations

from copy import deepcopy

import pytest

from mente_laylay.neural.datasets.gerar_volume_intent_gate_absoluto_v9 import (
    NIVEIS_TREINO,
    VALORES_PROTEGIDOS,
    gerar_exemplos,
    validar_lote,
)


def test_v9_ensina_somente_intent_e_gate_sem_vazar_valores_protegidos():
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)

    assert resumo["total"] == 24
    assert resumo["familias"] == 6
    assert resumo["niveis_treino"] == sorted(NIVEIS_TREINO)
    assert resumo["valores_protegidos"] == sorted(VALORES_PROTEGIDOS)
    assert resumo["training_heads"] == ["intent", "intent_gate"]
    assert len({x["text"].casefold() for x in exemplos}) == 24
    assert all(x["training_heads"] == ["intent", "intent_gate"] for x in exemplos)
    assert all(x["intent"] == "VOLUME" and x["action"] == "set" for x in exemplos)


@pytest.mark.parametrize("mutacao", ["head", "intent", "action", "valor"])
def test_v9_rejeita_contrato_invalido(mutacao):
    itens = deepcopy(gerar_exemplos())
    if mutacao == "head":
        itens[0]["training_heads"] = ["intent"]
    elif mutacao == "intent":
        itens[0]["intent"] = "NONE"
    elif mutacao == "action":
        itens[0]["action"] = "up"
    else:
        itens[0]["text"] = "deixa o volume em 59 por cento"

    with pytest.raises(ValueError):
        validar_lote(itens)

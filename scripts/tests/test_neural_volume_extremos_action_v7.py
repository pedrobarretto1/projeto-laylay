from __future__ import annotations

from copy import deepcopy

import pytest

from mente_laylay.neural.datasets.gerar_volume_extremos_action_v7 import (
    TEXTOS,
    gerar_exemplos,
    validar_lote,
)


def test_v7_extremos_ensina_somente_action_set():
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)

    assert resumo == {
        "total": 12,
        "volume_set_maximo": 12,
        "training_heads": ["action"],
    }
    assert len(TEXTOS) == 12
    assert len({x["text"].casefold() for x in exemplos}) == 12
    assert all(x["intent"] == "VOLUME" for x in exemplos)
    assert all(x["action"] == "set" for x in exemplos)
    assert all(x["is_command"] is True for x in exemplos)
    assert all(x["negated"] is False for x in exemplos)
    assert all(x["training_heads"] == ["action"] for x in exemplos)


@pytest.mark.parametrize("mutacao", ["head", "action", "intent", "command"])
def test_v7_extremos_rejeita_contrato_invalido(mutacao):
    itens = deepcopy(gerar_exemplos())
    if mutacao == "head":
        itens[0]["training_heads"] = ["action", "intent_gate"]
    elif mutacao == "action":
        itens[0]["action"] = "up"
    elif mutacao == "intent":
        itens[0]["intent"] = "MEDIA_CONTROL"
    else:
        itens[0]["is_command"] = False

    with pytest.raises(ValueError):
        validar_lote(itens)

from __future__ import annotations

from copy import deepcopy

import pytest

from mente_laylay.neural.datasets.gerar_volume_modalidade_comando_v8 import (
    NEGATIVOS,
    POSITIVOS,
    gerar_exemplos,
    validar_lote,
)


def test_v8_balanceia_command_head_volume_ampliado():
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)

    assert resumo == {
        "total": 36,
        "comandos": 18,
        "nao_comandos": 18,
        "training_heads": ["command"],
        "command_head_intent": "VOLUME",
    }
    assert len(POSITIVOS) == len(NEGATIVOS) == 18
    assert len({x["text"].casefold() for x in exemplos}) == 36
    assert all(x["training_heads"] == ["command"] for x in exemplos)
    assert all(x["command_head_intent"] == "VOLUME" for x in exemplos)
    assert all(x["domain"] == "audio" for x in exemplos)


def test_v8_preserva_rotulos_auxiliares_sem_treina_los():
    for item in gerar_exemplos():
        assert item["negated"] is False
        if item["is_command"]:
            assert (item["intent"], item["action"]) == ("VOLUME", "set")
        else:
            assert (item["intent"], item["action"]) == ("NONE", "none")


@pytest.mark.parametrize("mutacao", ["head", "owner", "balance", "intent", "action"])
def test_v8_rejeita_contrato_invalido(mutacao):
    itens = deepcopy(gerar_exemplos())
    if mutacao == "head":
        itens[0]["training_heads"] = ["command", "intent_gate"]
    elif mutacao == "owner":
        itens[0]["command_head_intent"] = "IOT_CONTROL"
    elif mutacao == "balance":
        itens[0]["is_command"] = False
    elif mutacao == "intent":
        itens[0]["intent"] = "NONE"
    else:
        itens[0]["action"] = "up"

    with pytest.raises(ValueError):
        validar_lote(itens)

from __future__ import annotations

from copy import deepcopy

import pytest

from mente_laylay.neural.datasets.gerar_volume_modalidade_comando_v6 import (
    NEGATIVOS,
    POSITIVOS,
    gerar_exemplos,
    validar_lote,
)


def test_v6_balanceia_command_head_volume_sem_treinar_outros_heads():
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)

    assert resumo == {
        "total": 24,
        "comandos": 12,
        "nao_comandos": 12,
        "training_heads": ["command"],
        "command_head_intent": "VOLUME",
    }
    assert len(POSITIVOS) == len(NEGATIVOS) == 12
    assert len({x["text"].casefold() for x in exemplos}) == 24
    assert all(x["training_heads"] == ["command"] for x in exemplos)
    assert all(x["command_head_intent"] == "VOLUME" for x in exemplos)
    assert all(x["domain"] == "audio" for x in exemplos)


def test_v6_rotulos_auxiliares_preservam_classe():
    for item in gerar_exemplos():
        if item["is_command"]:
            assert (item["intent"], item["action"]) == ("VOLUME", "set")
        else:
            assert (item["intent"], item["action"]) == ("NONE", "none")
        assert item["negated"] is False


@pytest.mark.parametrize("mutacao", ["head", "owner", "balance", "rotulo"])
def test_v6_rejeita_lote_fora_do_contrato(mutacao):
    itens = deepcopy(gerar_exemplos())
    if mutacao == "head":
        itens[0]["training_heads"] = ["command", "intent_gate"]
    elif mutacao == "owner":
        itens[0]["command_head_intent"] = "IOT_CONTROL"
    elif mutacao == "balance":
        itens[0]["is_command"] = False
    else:
        itens[0]["action"] = "up"

    with pytest.raises(ValueError):
        validar_lote(itens)

from __future__ import annotations

from mente_laylay.neural.datasets.gerar_iot_flexoes_imperativo_v5 import (
    gerar_exemplos,
    validar_lote,
)


def test_v5_so_ensina_head_command_iot_sem_vazar_challenge():
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)

    assert resumo == {
        "total": 24,
        "comandos": 12,
        "nao_comandos": 12,
        "command_head_intent": "IOT_CONTROL",
        "training_heads": ["command"],
    }
    assert all(item["command_head_intent"] == "IOT_CONTROL" for item in exemplos)
    assert all(item["training_heads"] == ["command"] for item in exemplos)
    assert all("luz" not in item["text"].casefold() for item in exemplos)
    assert not {
        "ligue a luz",
        "desligue a luz",
    } & {item["text"].casefold() for item in exemplos}


def test_v5_preserva_contraste_com_as_mesmas_flexoes():
    exemplos = gerar_exemplos()
    positivos = [item for item in exemplos if item["is_command"]]
    negativos = [item for item in exemplos if not item["is_command"]]

    assert any("ligue" in item["text"].casefold() for item in positivos)
    assert any("desligue" in item["text"].casefold() for item in positivos)
    assert any("ligue" in item["text"].casefold() for item in negativos)
    assert any("desligue" in item["text"].casefold() for item in negativos)
    assert all(item["intent"] == "IOT_CONTROL" for item in positivos)
    assert all(item["intent"] == "NONE" for item in negativos)

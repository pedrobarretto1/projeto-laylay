from __future__ import annotations

from copy import deepcopy
from collections import Counter

import pytest

from mente_laylay.neural.datasets.gerar_iot_luz_imperativo_v6 import (
    gerar_exemplos,
    validar_lote,
)


PROBES = {"ligue a luz", "desligue a luz"}


def test_v6_so_ensina_head_command_iot_e_preserva_probes():
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)

    assert resumo == {
        "total": 24,
        "comandos": 12,
        "nao_comandos": 12,
        "acoes_comando": {"off": 6, "on": 6},
        "command_head_intent": "IOT_CONTROL",
        "training_heads": ["command"],
        "probes_preservadas": sorted(PROBES),
    }
    assert len({item["text"].casefold() for item in exemplos}) == 24
    assert all(item["training_heads"] == ["command"] for item in exemplos)
    assert all(item["command_head_intent"] == "IOT_CONTROL" for item in exemplos)
    assert not PROBES & {item["text"].casefold() for item in exemplos}


def test_v6_ensina_luz_sem_mudar_intent_ou_action_head():
    exemplos = gerar_exemplos()
    positivos = [item for item in exemplos if item["is_command"]]
    negativos = [item for item in exemplos if not item["is_command"]]

    assert len(positivos) == len(negativos) == 12
    assert all("luz" in item["text"].casefold() for item in positivos)
    assert all(item["intent"] == "IOT_CONTROL" for item in positivos)
    assert Counter(item["action"] for item in positivos) == Counter({"on": 6, "off": 6})
    assert all(item["intent"] == "NONE" and item["action"] == "none" for item in negativos)
    assert any("ligue" in item["text"].casefold() for item in negativos)
    assert any("desligue" in item["text"].casefold() for item in negativos)


@pytest.mark.parametrize("probe", sorted(PROBES))
def test_v6_rejeita_vazamento_das_probes(probe):
    exemplos = gerar_exemplos()
    alterados = deepcopy(exemplos)
    alterados[0]["text"] = probe

    with pytest.raises(ValueError, match="probe|challenge"):
        validar_lote(alterados)


def test_v6_rejeita_head_ou_escopo_de_treino_alterado():
    exemplos = gerar_exemplos()

    head = deepcopy(exemplos)
    head[0]["command_head_intent"] = "MEDIA_CONTROL"
    with pytest.raises(ValueError, match="IOT_CONTROL"):
        validar_lote(head)

    escopo = deepcopy(exemplos)
    escopo[0]["training_heads"] = ["intent", "command"]
    with pytest.raises(ValueError, match="command"):
        validar_lote(escopo)


def test_v6_rejeita_desbalanceamento_on_off():
    exemplos = gerar_exemplos()
    alterados = deepcopy(exemplos)
    primeiro_on = next(item for item in alterados if item["is_command"] and item["action"] == "on")
    primeiro_on["action"] = "off"

    with pytest.raises(ValueError, match="6/6|balance"):
        validar_lote(alterados)

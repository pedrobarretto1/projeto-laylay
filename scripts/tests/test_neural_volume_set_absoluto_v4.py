from __future__ import annotations

from copy import deepcopy

import pytest

from mente_laylay.neural.datasets.gerar_volume_set_absoluto_v4 import (
    NIVEIS_TREINO,
    PROBES,
    gerar_exemplos,
    validar_lote,
)


def test_v4_ensina_action_e_intent_gate_volume_set_sem_vazar_probes():
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)

    assert resumo == {
        "total": 48,
        "volume_set": 48,
        "familias": 12,
        "niveis_treino": sorted(NIVEIS_TREINO),
        "training_heads": ["action", "intent_gate"],
        "probes_preservadas": sorted(PROBES),
    }
    assert len({item["text"].casefold() for item in exemplos}) == 48
    assert all(item["intent"] == "VOLUME" for item in exemplos)
    assert all(item["action"] == "set" for item in exemplos)
    assert all(item["is_command"] is True for item in exemplos)
    assert all(item["negated"] is False for item in exemplos)
    assert all(
        item["training_heads"] == ["action", "intent_gate"]
        for item in exemplos
    )
    assert all(item["domain"] == "audio" for item in exemplos)
    assert not PROBES & {item["text"].casefold() for item in exemplos}


def test_v4_nao_usa_valores_congelados_50_ou_100():
    exemplos = gerar_exemplos()

    assert 50 not in NIVEIS_TREINO
    assert 100 not in NIVEIS_TREINO
    for item in exemplos:
        normalizado = item["text"].casefold().replace("%", "")
        tokens = normalizado.split()
        assert "50" not in tokens
        assert "100" not in tokens


@pytest.mark.parametrize("probe", sorted(PROBES))
def test_v4_rejeita_vazamento_exato_de_probe(probe):
    exemplos = gerar_exemplos()
    alterados = deepcopy(exemplos)
    alterados[0]["text"] = probe

    with pytest.raises(ValueError, match="probe|challenge"):
        validar_lote(alterados)


def test_v4_rejeita_outro_head_ou_action():
    exemplos = gerar_exemplos()

    head = deepcopy(exemplos)
    head[0]["training_heads"] = ["command", "action"]
    with pytest.raises(ValueError, match="action"):
        validar_lote(head)

    action = deepcopy(exemplos)
    action[0]["action"] = "up"
    with pytest.raises(ValueError, match="set"):
        validar_lote(action)


def test_v4_rejeita_valor_congelado_mesmo_em_texto_novo():
    exemplos = gerar_exemplos()
    alterados = deepcopy(exemplos)
    alterados[0]["text"] = "define o volume em 50 por cento"

    with pytest.raises(ValueError, match="50|congelado"):
        validar_lote(alterados)

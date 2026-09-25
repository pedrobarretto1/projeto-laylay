from __future__ import annotations

import copy

import joblib

from mente_laylay.neural.modelo import (
    carregar_modelo,
    normalizar_texto_intent_gate_volume_numeros_v1,
    treinar_modelo,
)


def _exemplos():
    return [
        {
            "text": "coloca o volume em 20",
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "action": "set",
        },
        {
            "text": "aumenta o volume",
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "action": "up",
        },
        {
            "text": "abre a calculadora",
            "intent": "APP_OPEN",
            "is_command": True,
            "negated": False,
            "action": "open",
        },
        {
            "text": "o volume está alto",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
        },
        {
            "text": "ontem mexi no volume",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
        },
    ]


def _base(tmp_path):
    return treinar_modelo(
        _exemplos(),
        caminho=tmp_path / "base.joblib",
        versao="base-intent-overlay",
    )


def test_normalizador_so_altera_numero_no_dominio_audio():
    assert normalizar_texto_intent_gate_volume_numeros_v1(
        "deixa o volume em 59 por cento"
    ) == "deixa o volume em valor por cento"
    assert normalizar_texto_intent_gate_volume_numeros_v1(
        "pesquisa 59 filmes"
    ) == "pesquisa 59 filmes"
    assert normalizar_texto_intent_gate_volume_numeros_v1(
        "o volume está alto"
    ) == "o volume está alto"
    assert normalizar_texto_intent_gate_volume_numeros_v1(
        "C418 - Sweden Minecraft Volume Alpha"
    ) == "C418 - Sweden Minecraft Volume Alpha"


def _com_overlay(base):
    candidato = copy.copy(base)
    candidato.cabecas_intent_overlay = {
        "volume_numeros_v1": base.cabeca_intent
    }
    candidato.features_intent_gate = "volume_numeros_v1"
    candidato.versao = "intent-overlay-v1"
    return candidato


def test_overlay_intent_so_assume_volume_numerico(tmp_path):
    base = _base(tmp_path)
    candidato = _com_overlay(base)

    sem_numero = candidato.prever("o volume está alto")
    numerico = candidato.prever("coloca o volume em 42")

    assert sem_numero["intent_head_variant"] == "legado"
    assert numerico["intent_head_variant"] == "volume_numeros_v1"


def test_overlay_intent_recarrega_sem_afetar_texto_comum(tmp_path):
    base = _base(tmp_path)
    candidato = _com_overlay(base)
    caminho = tmp_path / "intent-overlay.joblib"
    joblib.dump(candidato, caminho)

    recarregado = carregar_modelo(caminho)

    assert set(recarregado.cabecas_intent_overlay) == {
        "volume_numeros_v1"
    }
    assert recarregado.features_intent_gate == "volume_numeros_v1"
    assert recarregado.prever("o volume está alto")[
        "intent_head_variant"
    ] == "legado"
    assert recarregado.prever("coloca o volume em 42")[
        "intent_head_variant"
    ] == "volume_numeros_v1"

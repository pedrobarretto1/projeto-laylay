"""Contrato de jurisdição entre janela explícita e restauração contextual.

ROOT D
------
``Traz ele de volta.`` não possui alvo explícito de aplicativo. O detector
``detectar_janela_explicita`` não pode transformar a referência inteira em um
nome de app. Se houver uma exclusão confirmada, a frase pertence ao fluxo de
restauração; sem esse recibo, deve permanecer sem efeito em vez de fabricar
``APP_OPEN("ele de volta")``.

Este módulo testa somente a fronteira de janela que causou o RED do stack.
O teste físico de restauração continua em
``test_fluxo_producao_restauracao_arquivo.py``.
"""

from __future__ import annotations

import pytest

from mente_laylay.autonomia.roteador_deterministico import (
    detectar_janela_contextual,
    detectar_janela_explicita,
)


def _params(**kwargs):
    return kwargs


@pytest.mark.parametrize(
    "fala",
    [
        "Traz ele de volta.",
        "Traz ela de volta.",
        "Traz isso de volta.",
        "Traz o arquivo de volta.",
        "Traz a pasta de volta.",
    ],
)
def test_janela_explicita_nao_fabrica_app_de_pedido_de_restauracao(
    fala: str,
) -> None:
    """Uma forma de restauração não é evidência de um app explícito."""
    candidato = detectar_janela_explicita(
        fala.casefold(),
        fala.casefold(),
        params_cb=_params,
    )

    assert candidato is None


@pytest.mark.parametrize(
    ("fala", "intent", "nome_app"),
    [
        ("Traz o Chrome", "APP_OPEN", "chrome"),
        ("Traz o Chrome pra frente", "APP_OPEN", "chrome"),
        ("Maximiza o Chrome", "MAXIMIZE_WINDOW", "chrome"),
    ],
)
def test_janela_explicita_preserva_alvos_reais_de_app(
    fala: str,
    intent: str,
    nome_app: str,
) -> None:
    """A correção não pode amputar a gramática legítima de janela."""
    candidato = detectar_janela_explicita(
        fala.casefold(),
        fala.casefold(),
        params_cb=_params,
    )

    assert candidato is not None
    assert candidato["intent"] == intent
    assert candidato["params"]["nome_app"].casefold() == nome_app


@pytest.mark.parametrize(
    "fala",
    [
        "traz ele pra frente",
        "traz ele para frente",
        "traz ele em foco",
    ],
)
def test_pronome_com_semantica_de_janela_continua_no_detector_contextual(
    fala: str,
) -> None:
    """Pronome + marcador de foco é resolvido pelo detector contextual real."""
    estado = {
        "ultima_acao_intent": "APP_OPEN",
        "ultima_acao_params": {"nome_app": "Chrome"},
        "ultimo_app_janela": "Chrome",
    }

    candidato = detectar_janela_contextual(
        fala,
        params_cb=_params,
        estado_mental=estado,
        texto_depende_de_contexto=lambda _texto: True,
    )

    assert candidato is not None
    assert candidato["intent"] == "APP_OPEN"
    assert candidato["params"]["nome_app"] == "Chrome"
    assert candidato["params"]["modo"] == "focus"


def test_pronome_sem_marcador_de_janela_nao_herda_app() -> None:
    """Contexto de app não transforma qualquer uso de 'ele' em janela."""
    estado = {
        "ultima_acao_intent": "APP_OPEN",
        "ultima_acao_params": {"nome_app": "Chrome"},
        "ultimo_app_janela": "Chrome",
    }

    candidato = detectar_janela_contextual(
        "traz ele de volta",
        params_cb=_params,
        estado_mental=estado,
        texto_depende_de_contexto=lambda _texto: True,
    )

    assert candidato is None

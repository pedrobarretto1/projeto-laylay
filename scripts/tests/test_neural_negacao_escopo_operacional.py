from __future__ import annotations

import pytest

from mente_laylay.neural.modelo import normalizar_texto_negacao_escopo_operacional_v1


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("não quero essa música, pula ela", "pula ela"),
        ("não gostei dessa música, passa pra próxima", "passa pra próxima"),
        ("essa eu não quero ouvir, pula", "pula"),
        ("não quero mais usar o discord, fecha ele", "fecha ele"),
        ("não vou usar mais a steam, pode fechar", "pode fechar"),
        ("não preciso mais do vscode; fecha ele", "fecha ele"),
        ("não quero o chrome aberto, fecha pra mim", "fecha pra mim"),
    ],
)
def test_recorta_contexto_negativo_antes_de_comando(texto, esperado):
    assert normalizar_texto_negacao_escopo_operacional_v1(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "não abaixa o volume",
        "não quero que você feche o discord",
        "não abre o chrome, por favor",
        "não quero essa música porque ela é triste",
        "fecha o discord, não a steam",
        "não quero essa música, não pula ela",
    ],
)
def test_preserva_negacao_que_pode_modificar_o_pedido(texto):
    assert normalizar_texto_negacao_escopo_operacional_v1(texto) == texto

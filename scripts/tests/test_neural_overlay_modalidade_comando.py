from __future__ import annotations

from mente_laylay.neural.modelo import (
    adicionar_overlay_comando_modalidade,
    carregar_modelo,
    treinar_modelo,
)


def _exemplos():
    return [
        {
            "text": "abaixa o volume",
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "action": "down",
            "domain": "audio",
        },
        {
            "text": "aumenta o volume",
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "action": "up",
            "domain": "audio",
        },
        {
            "text": "abre a calculadora",
            "intent": "APP_OPEN",
            "is_command": True,
            "negated": False,
            "action": "open",
            "domain": "app",
        },
        {
            "text": "o volume está alto",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "domain": "audio",
        },
        {
            "text": "como abro a calculadora?",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "domain": "app",
        },
        {
            "text": "não precisa abrir nada",
            "intent": "NONE",
            "is_command": False,
            "negated": True,
            "action": "none",
            "domain": "app",
        },
        {
            "text": "pode alterar o volume para 20",
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "action": "set",
            "domain": "audio",
            "training_heads": ["command"],
            "command_head_intent": "VOLUME",
        },
        {
            "text": "você pode alterar o volume?",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "domain": "audio",
            "training_heads": ["command"],
            "command_head_intent": "VOLUME",
        },
        {
            "text": "como posso alterar o volume?",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "domain": "audio",
            "training_heads": ["command"],
            "command_head_intent": "VOLUME",
        },
        {
            "text": "dizer 'aumenta o volume' é um exemplo",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "domain": "audio",
            "training_heads": ["command"],
            "command_head_intent": "VOLUME",
        },
    ]


def _base(tmp_path):
    return treinar_modelo(
        _exemplos(),
        caminho=tmp_path / "base.joblib",
        versao="base-overlay",
        arquitetura_comando="intent_gated",
    )


def test_overlay_preserva_head_legado_quando_nao_ha_sinal(tmp_path):
    base = _base(tmp_path)
    texto = "é melhor apenas diminuir o volume"
    antes = base.prever(texto)

    candidato = adicionar_overlay_comando_modalidade(
        base,
        _exemplos(),
        intent="VOLUME",
        caminho=tmp_path / "overlay.joblib",
        versao="overlay-v1",
    )
    depois = candidato.prever(texto)

    assert candidato is not base
    assert base.cabecas_comando_overlay_por_intent == {}
    assert depois["command_head_variant"] == "legado"
    assert depois["is_command"] == antes["is_command"]
    assert depois["raw_is_command"] == antes["raw_is_command"]
    assert depois["command_probability"] == antes["command_probability"]


def test_overlay_so_assume_frase_com_sinal_estrutural(tmp_path):
    base = _base(tmp_path)
    candidato = adicionar_overlay_comando_modalidade(
        base,
        _exemplos(),
        intent="VOLUME",
        caminho=tmp_path / "overlay.joblib",
        versao="overlay-v1",
    )

    direta = candidato.prever("pode alterar o volume para 20")
    pergunta = candidato.prever("você pode alterar o volume?")

    assert direta["command_head_variant"] == "legado"
    assert pergunta["command_head_variant"] == "modalidade_v4_sparse_v1"
    assert pergunta["command_head_scope"] == "VOLUME"


def test_overlay_recarrega_sem_perder_roteamento(tmp_path):
    base = _base(tmp_path)
    caminho = tmp_path / "overlay.joblib"
    adicionar_overlay_comando_modalidade(
        base,
        _exemplos(),
        intent="VOLUME",
        caminho=caminho,
        versao="overlay-v1",
    )

    modelo = carregar_modelo(caminho)

    assert modelo.versoes_overlay_comando_por_intent == {
        "VOLUME": "modalidade_v4_sparse_v1"
    }
    assert modelo.prever("você pode alterar o volume?")[
        "command_head_variant"
    ] == "modalidade_v4_sparse_v1"
    assert modelo.prever("abaixa o volume")["command_head_variant"] == "legado"

from __future__ import annotations

from mente_laylay.neural.modelo import (
    adicionar_overlay_comando_modalidade,
    enriquecer_texto_features_comando,
    enriquecer_texto_features_comando_modalidade_v4_sparse,
    enriquecer_texto_features_comando_pragmatica_v5_sparse,
    treinar_modelo,
)


def _exemplos():
    return [
        {
            "text": "abre o chrome", "intent": "APP_OPEN", "action": "open",
            "is_command": True, "negated": False, "domain": "app",
        },
        {
            "text": "o chrome abriu ontem", "intent": "NONE", "action": "none",
            "is_command": False, "negated": False, "domain": "app",
        },
        {
            "text": "seria legal abrir o chrome", "intent": "APP_OPEN",
            "action": "open", "is_command": True, "negated": False,
            "domain": "app", "training_heads": ["command"],
            "command_head_intent": "APP_OPEN",
        },
        {
            "text": "seria legal saber como abrir o chrome", "intent": "NONE",
            "action": "none", "is_command": False, "negated": False,
            "domain": "app", "training_heads": ["command"],
            "command_head_intent": "APP_OPEN",
        },
        {
            "text": "eu queria abrir a calculadora", "intent": "APP_OPEN",
            "action": "open", "is_command": True, "negated": False,
            "domain": "app", "training_heads": ["command"],
            "command_head_intent": "APP_OPEN",
        },
        {
            "text": "eu queria saber como abrir a calculadora", "intent": "NONE",
            "action": "none", "is_command": False, "negated": False,
            "domain": "app", "training_heads": ["command"],
            "command_head_intent": "APP_OPEN",
        },
    ]
def test_v5_e_esparsa_quando_nao_ha_moldura_pragmatica():
    texto = "abre o chrome"
    assert (
        enriquecer_texto_features_comando_pragmatica_v5_sparse(texto)
        == enriquecer_texto_features_comando(texto)
    )


def test_v5_marca_pedido_indireto_sem_codificar_autoridade():
    saida = enriquecer_texto_features_comando_pragmatica_v5_sparse(
        "seria legal abrir o chrome"
    )
    assert "marcador_pedido_indireto_avaliativo" in saida
    assert "autoriza_execucao" not in saida
    assert "bloqueia_execucao" not in saida


def test_v5_distingue_consulta_instrucional():
    saida = enriquecer_texto_features_comando_pragmatica_v5_sparse(
        "eu queria saber como abrir o chrome"
    )
    assert "marcador_pedido_indireto_desejo" in saida
    assert "marcador_consulta_instrucional_como" in saida


def test_overlay_v5_so_assume_quando_ha_sinal_pragmatico(tmp_path):
    base = treinar_modelo(
        _exemplos(),
        caminho=tmp_path / "base.joblib",
        versao="base-pragmatica",
        arquitetura_comando="intent_gated",
    )
    candidato = adicionar_overlay_comando_modalidade(
        base,
        _exemplos(),
        intent="APP_OPEN",
        caminho=tmp_path / "cand.joblib",
        versao="cand-pragmatica",
        overlay="pragmatica_v5_sparse_v1",
    )
    assert candidato.prever("abre o chrome")["command_head_variant"] == "legado"
    assert (
        candidato.prever("seria legal abrir o chrome")["command_head_variant"]
        == "pragmatica_v5_sparse_v1"
    )


def test_overlay_v5_nao_assume_so_por_sinal_v4_generico(tmp_path):
    base = treinar_modelo(
        _exemplos(),
        caminho=tmp_path / "base-generico.joblib",
        versao="base-generico",
        arquitetura_comando="intent_gated",
    )
    candidato = adicionar_overlay_comando_modalidade(
        base,
        _exemplos(),
        intent="APP_OPEN",
        overlay="pragmatica_v5_sparse_v1",
    )
    previsao = candidato.prever("como abrir o chrome?")
    assert previsao["command_head_variant"] == "legado"


def test_v5_nao_marca_moldura_incompleta():
    for texto in ("seria ótimo", "eu queria", "bem que você podia", "tô a fim de"):
        assert (
            enriquecer_texto_features_comando_pragmatica_v5_sparse(texto)
            == enriquecer_texto_features_comando_modalidade_v4_sparse(texto)
        )

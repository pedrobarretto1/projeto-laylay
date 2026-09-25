from __future__ import annotations

import pytest

from mente_laylay.neural.modelo import (
    FEATURES_COMANDO_PERMITIDAS,
    enriquecer_texto_features_comando,
    enriquecer_texto_features_comando_modalidade,
    enriquecer_texto_features_comando_modalidade_v2,
    enriquecer_texto_features_comando_modalidade_v3,
    enriquecer_texto_features_comando_modalidade_v4_sparse,
    treinar_modelo,
)


@pytest.mark.parametrize(
    "texto,marcadores",
    [
        (
            "por que você abaixou o volume",
            ("marcador_modalidade_pergunta", "marcador_sem_acao_explicita"),
        ),
        (
            "como faço para silenciar o áudio?",
            ("marcador_modalidade_geral_pergunta", "marcador_sem_acao_explicita"),
        ),
        (
            "Para aumentar o volume, você pode dizer 'aumenta o volume'.",
            ("marcador_sem_acao_explicita", "marcador_citacao_presente"),
        ),
        (
            "coloca o volume em 50",
            (
                "marcador_modalidade_comando",
                "marcador_natureza_acao_pedido_direto",
                "marcador_acao_explicita",
            ),
        ),
    ],
)
def test_modalidade_v1_expoe_estrutura_sem_decisao_final(texto, marcadores):
    enriquecido = enriquecer_texto_features_comando_modalidade(texto)
    for marcador in marcadores:
        assert marcador in enriquecido
    assert "autoriza_execucao" not in enriquecido
    assert "bloqueia_execucao" not in enriquecido


def test_preprocessador_legado_permanece_sem_features_modalidade():
    texto = "por que você abaixou o volume"
    legado = enriquecer_texto_features_comando(texto)
    novo = enriquecer_texto_features_comando_modalidade(texto)

    assert "marcador_modalidade_" not in legado
    assert "marcador_modalidade_pergunta" in novo
    assert legado in novo


def _exemplos_minimos():
    return [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "aumenta o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "up"},
        {"text": "abre a calculadora", "intent": "APP_OPEN", "is_command": True, "negated": False, "action": "open"},
        {"text": "por que você abaixou o volume", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "como faço para abrir a calculadora?", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "eu aumentei o volume", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]


def test_treino_versiona_features_comando_sem_mudar_default(tmp_path):
    legado = treinar_modelo(
        _exemplos_minimos(),
        caminho=tmp_path / "legado.joblib",
        versao="legado",
    )
    modalidade = treinar_modelo(
        _exemplos_minimos(),
        caminho=tmp_path / "modalidade.joblib",
        versao="modalidade",
        features_comando="modalidade_v1",
    )

    assert FEATURES_COMANDO_PERMITIDAS == frozenset({
        "legado", "modalidade_v1", "modalidade_por_intent_v1",
        "modalidade_v2", "modalidade_por_intent_v2",
        "modalidade_v3", "modalidade_por_intent_v3",
        "modalidade_v4_sparse", "modalidade_por_intent_v4_sparse",
    })
    assert legado.features_comando == "legado"
    assert legado.features_comando_intents == ()
    assert modalidade.features_comando == "modalidade_v1"
    assert modalidade.features_comando_intents == ()


def test_treino_rejeita_features_comando_desconhecidas(tmp_path):
    with pytest.raises(ValueError, match="features de comando desconhecidas"):
        treinar_modelo(
            _exemplos_minimos(),
            caminho=tmp_path / "invalido.joblib",
            versao="invalido",
            features_comando="magia",
        )


def test_modalidade_por_intent_versiona_escopo(tmp_path):
    modelo = treinar_modelo(
        _exemplos_minimos(),
        caminho=tmp_path / "escopado.joblib",
        versao="escopado",
        features_comando="modalidade_por_intent_v1",
        features_comando_intents=["volume"],
    )

    assert modelo.features_comando == "modalidade_por_intent_v1"
    assert modelo.features_comando_intents == ("VOLUME",)


def test_modalidade_por_intent_exige_escopo(tmp_path):
    with pytest.raises(ValueError, match="exige ao menos uma intent"):
        treinar_modelo(
            _exemplos_minimos(),
            caminho=tmp_path / "sem_escopo.joblib",
            versao="sem-escopo",
            features_comando="modalidade_por_intent_v1",
        )


def test_modalidade_v2_detecta_terceira_pessoa_e_metalinguagem():
    terceira = enriquecer_texto_features_comando_modalidade_v2(
        "ele regulou o áudio durante o jogo"
    )
    citada = enriquecer_texto_features_comando_modalidade_v2(
        "dizer 'aumenta o som' é só um exemplo"
    )

    assert "marcador_sujeito_terceira_pessoa" in terceira
    assert "marcador_metalinguagem_citada" in citada
    assert "autoriza_execucao" not in terceira + citada


def test_modalidade_por_intent_v2_versiona_escopo(tmp_path):
    modelo = treinar_modelo(
        _exemplos_minimos(),
        caminho=tmp_path / "escopado-v2.joblib",
        versao="escopado-v2",
        features_comando="modalidade_por_intent_v2",
        features_comando_intents=["volume"],
    )

    assert modelo.features_comando == "modalidade_por_intent_v2"
    assert modelo.features_comando_intents == ("VOLUME",)



def test_modalidade_v3_e_autocontida_e_expoe_molduras(monkeypatch):
    import mente_laylay.cognicao.modalidade_turno as modalidade_turno

    def falhar(*_args, **_kwargs):
        raise AssertionError("v3 nao pode consultar classificador canonico")

    monkeypatch.setattr(
        modalidade_turno,
        "classificar_modalidade_turno",
        falhar,
    )
    casos = (
        ("por que voce abaixou o volume", "marcador_inicio_interrogativo"),
        (
            "preciso que voce explique como alterar o volume",
            "marcador_moldura_explicacao",
        ),
        (
            "voce pode dizer 'coloca o volume em 30%'",
            "marcador_metalinguagem",
        ),
        ("ele pode alterar o volume", "marcador_sujeito_terceira_pessoa"),
        ("ontem mexi no volume", "marcador_referencia_passado"),
        (
            "sempre prefiro o volume em 30 por cento",
            "marcador_preferencia_ou_habito",
        ),
    )
    for texto, marcador in casos:
        enriquecido = enriquecer_texto_features_comando_modalidade_v3(texto)
        assert marcador in enriquecido
        assert "autoriza_execucao" not in enriquecido
        assert "bloqueia_execucao" not in enriquecido


def test_modalidade_por_intent_v3_versiona_escopo(tmp_path):
    modelo = treinar_modelo(
        _exemplos_minimos(),
        caminho=tmp_path / "escopado-v3.joblib",
        versao="escopado-v3",
        features_comando="modalidade_por_intent_v3",
        features_comando_intents=["volume"],
    )

    assert modelo.features_comando == "modalidade_por_intent_v3"
    assert modelo.features_comando_intents == ("VOLUME",)


def test_modalidade_v4_sparse_cai_no_legado_sem_sinal_estrutural():
    texto = "é melhor apenas diminuir o volume"
    assert (
        enriquecer_texto_features_comando_modalidade_v4_sparse(texto)
        == enriquecer_texto_features_comando(texto)
    )


def test_modalidade_v4_sparse_so_emite_marcadores_presentes():
    pergunta = enriquecer_texto_features_comando_modalidade_v4_sparse(
        "como faço para ajustar o volume?"
    )
    citada = enriquecer_texto_features_comando_modalidade_v4_sparse(
        "dizer 'aumenta o som' é só um exemplo"
    )

    assert "marcador_interrogacao_final" in pergunta
    assert "marcador_inicio_interrogativo" in pergunta
    assert "marcador_metalinguagem" in citada
    assert "marcador_citacao_presente" in citada
    assert "marcador_sem_" not in pergunta + citada
    assert "autoriza_execucao" not in pergunta + citada
    assert "bloqueia_execucao" not in pergunta + citada


def test_modalidade_por_intent_v4_sparse_versiona_escopo(tmp_path):
    modelo = treinar_modelo(
        _exemplos_minimos(),
        caminho=tmp_path / "escopado-v4.joblib",
        versao="escopado-v4",
        features_comando="modalidade_por_intent_v4_sparse",
        features_comando_intents=["volume"],
    )

    assert modelo.features_comando == "modalidade_por_intent_v4_sparse"
    assert modelo.features_comando_intents == ("VOLUME",)

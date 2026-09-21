import joblib
import numpy as np
import pytest

from mente_laylay.neural.modelo import _pipeline, enriquecer_texto_features
from mente_laylay.neural.representacao_sinais_atomicos import (
    criar_extrator_sinais_atomicos, separar_texto_e_sinais, SinaisNegacaoAtomicos,
)
from mente_laylay.neural.experimento_escopo_negacao import criar_prototipo_negacao
import mente_laylay.neural.representacao_sinais_atomicos as representacao


@pytest.fixture
def cabeca():
    return _pipeline([False, True], representacao="tfidf_indicadores", estrategia="sgd_log_loss", ngramas_caracteres=(4, 6))


def test_fronteira_historica_marcador_vira_fragmentos_mas_nova_nao(cabeca):
    antigo = dict(cabeca.named_steps["features"].transformer_list)
    assert "negac" in antigo["caracteres"].build_analyzer()("não abra algo")
    novo = dict(criar_extrator_sinais_atomicos(cabeca).transformer_list)
    assert "negac" not in novo["caracteres"].build_analyzer()("não abra algo")
    assert "marcador_negacao_explicita" not in novo["palavras"].build_analyzer()("não abra algo")
    np.testing.assert_array_equal(novo["sinais"].transform(["não abra algo"]).toarray(), [[1, 0]])


@pytest.mark.parametrize("texto,flags", [
    ("não abra algo", (True, False)), ("evite tocar essa faixa", (False, True)),
    ("não toque nada exceto jazz", (True, True)), ("abra o editor", (False, False)),
    ('leia "não apagar.txt"', (True, False)),
    ("coloca o volume em 30, não em 50", (True, False)),
])
def test_sinais_preservam_extrator_sem_inventar_decisao_de_escopo(texto, flags):
    base, sinais = separar_texto_e_sinais(texto)
    assert sinais == flags
    assert enriquecer_texto_features(texto).startswith(base)


def test_marcador_literal_nao_e_removido_nem_lido_como_metadado(cabeca):
    t = "leia marcador_negacao_explicita.txt"
    assert separar_texto_e_sinais(t) == (t, (False, False))
    canais = dict(criar_extrator_sinais_atomicos(cabeca).transformer_list)
    assert "marcador_negacao_explicita" in canais["palavras"].build_analyzer()(t)


def test_sinais_nao_reponderam_quando_alvo_ou_comprimento_muda():
    matriz = SinaisNegacaoAtomicos().transform([
        "não abra Cedrion", "não abra Zelvoria", "não abra " + "palavra " * 100,
    ]).toarray()
    np.testing.assert_array_equal(matriz, [[1, 0]] * 3)


def test_fit_features_nao_muda_cabeca_original_e_serializa(tmp_path, cabeca):
    h = joblib.hash(cabeca)
    f = criar_extrator_sinais_atomicos(cabeca)
    textos = ["não abra algo", "abra outra coisa"]
    esperado = f.fit_transform(textos).toarray()
    assert joblib.hash(cabeca) == h
    assert sum(n.startswith("sinais__") for n in f.get_feature_names_out()) == 2
    p = tmp_path / "features.joblib"
    joblib.dump(f, p)
    np.testing.assert_array_equal(joblib.load(p).transform(textos).toarray(), esperado)


def test_runner_cria_so_prototipo_isolado(cabeca):
    h = joblib.hash(cabeca)
    p = criar_prototipo_negacao(cabeca, "sinais_atomicos")
    assert "sinais" in dict(p.named_steps["features"].transformer_list)
    assert joblib.hash(cabeca) == h


@pytest.mark.parametrize("texto", ["", " ", None])
def test_entrada_invalida_aborta(texto):
    with pytest.raises(ValueError):
        separar_texto_e_sinais(texto)


def test_sinais_vazios_tem_duas_colunas():
    assert SinaisNegacaoAtomicos().transform([]).shape == (0, 2)


@pytest.mark.parametrize("enriquecido", ["texto modificado", "abra algo novo_marcador", "abra algo marcador_negacao_explicita marcador_negacao_explicita"])
def test_mudanca_do_contrato_canonico_aborta(monkeypatch, enriquecido):
    monkeypatch.setattr(representacao, "enriquecer_texto_features", lambda t: enriquecido)
    with pytest.raises(ValueError):
        separar_texto_e_sinais("abra algo")

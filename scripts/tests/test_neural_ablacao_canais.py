import joblib
import numpy as np
import pytest

from mente_laylay.neural.diagnostico_ablacao_canais import medir_canais, executar, contrastes_diagnosticos
from mente_laylay.neural.modelo import _pipeline
from mente_laylay.neural.representacao_escopo_local import criar_prototipo_escopo_local


@pytest.fixture
def cabeca():
    itens = contrastes_diagnosticos()
    return criar_prototipo_escopo_local(_pipeline([False, True], representacao="tfidf_indicadores", estrategia="sgd_log_loss")).fit(
        [i["text"] for i in itens], [i["negated"] for i in itens])


def test_ablacao_subtrai_canais_sem_mudar_pesos_ou_predict_original(cabeca):
    antes = joblib.hash(cabeca)
    textos = [i["text"] for i in contrastes_diagnosticos()]
    r = medir_canais(cabeca, textos)
    assert r["variantes"]["integral"]["negated"] == list(cabeca.predict(textos))
    assert r["erro_maximo_reconstrucao"] < 1e-10
    np.testing.assert_allclose(r["variantes"]["somente_escopo"]["scores"], r["intercepto"] + np.array(r["contribuicoes"]["escopo_local"]))
    assert joblib.hash(cabeca) == antes


@pytest.mark.parametrize("textos", [[], [""], [None]])
def test_textos_invalidos_abortam(cabeca, textos):
    with pytest.raises(ValueError):
        medir_canais(cabeca, textos)


def test_classe_invertida_aborta(cabeca):
    cabeca.named_steps["classifier"].classes_ = np.array([True, False])
    with pytest.raises(ValueError, match="classes booleanas"):
        medir_canais(cabeca, ["abra algo"])


def test_coeficiente_nao_finito_aborta(cabeca):
    cabeca.named_steps["classifier"].coef_[0, 0] = np.nan
    with pytest.raises(ValueError, match="não finitos"):
        medir_canais(cabeca, ["abra algo"])


def test_nao_sobrescreve_evidencia(tmp_path):
    with pytest.raises(FileExistsError):
        executar(experimento=tmp_path / "ausente", saida=tmp_path)

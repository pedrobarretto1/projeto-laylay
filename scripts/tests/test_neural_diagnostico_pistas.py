import joblib
import numpy as np
import pytest

from mente_laylay.neural.diagnostico_pistas_negacao import (
    comparar_pistas, contrafactual_sem_marcadores_nos_caracteres, explicar_pistas,
)
from mente_laylay.neural.modelo import _pipeline
from mente_laylay.neural.experimento_escopo_negacao import criar_prototipo_negacao


@pytest.fixture
def cabeca():
    textos = [
        "inicie Cedrion, não Belmora", "ajuste para 14, não para 28",
        "não inicie Cedrion", "não ajuste para 14",
        "leia o arquivo", "abra o editor", "não leia o arquivo", "nunca abra o editor",
    ]
    y = [False, False, True, True, False, False, True, True]
    return _pipeline(y, representacao="tfidf_indicadores", estrategia="sgd_log_loss").fit(textos, y)


def test_contribuicoes_reconstroem_decisao_real_sem_mutar(cabeca):
    antes = joblib.hash(cabeca)
    r = explicar_pistas(cabeca, "inicie Cedrion, não Belmora")
    assert r["score"] == pytest.approx(r["intercepto"] + sum(c["soma_contribuicoes"] for c in r["canais"].values()))
    assert r["erro_reconstrucao"] < 1e-10
    assert r["negated"] == bool(cabeca.predict([r["texto"]])[0])
    assert joblib.hash(cabeca) == antes


def test_delta_inclui_reponderacao_compartilhada_por_normalizacao(cabeca):
    r = comparar_pistas(cabeca, "inicie Cedrion, não Belmora", "inicie Zzzxxyy, não Qqrrzzt")
    assert sum(r["decomposicao_delta"].values()) == pytest.approx(r["delta_score"])
    assert r["decomposicao_delta"]["compartilhadas_reponderadas"] != 0
    assert "zzzxxyy" in r["depois"]["canais"]["palavras"]["fora_vocabulario"]


def test_par_identico_tem_delta_zero(cabeca):
    r = comparar_pistas(cabeca, "não leia o arquivo", "não leia o arquivo")
    assert r["delta_score"] == 0
    assert not r["mudou_decisao"]


def test_sentido_das_classes_nao_pode_ser_invertido_silenciosamente(cabeca):
    cabeca.named_steps["classifier"].classes_ = np.array([True, False])
    with pytest.raises(ValueError, match="classes booleanas"):
        explicar_pistas(cabeca, "inicie algo")


def test_classes_numericas_nao_sao_assumidas_como_booleanas(cabeca):
    cabeca.named_steps["classifier"].classes_ = np.array([0, 1])
    with pytest.raises(ValueError, match="classes booleanas"):
        explicar_pistas(cabeca, "inicie algo")


def test_ablacao_nao_apaga_marcador_digitado_literalmente(cabeca):
    r = contrafactual_sem_marcadores_nos_caracteres(cabeca, "leia marcador_negacao_explicita")
    assert r["sufixo_retirado_apenas_do_canal_caracteres"] == ""
    assert r["score"] == pytest.approx(explicar_pistas(cabeca, "leia marcador_negacao_explicita")["score"])


def test_ablacao_so_muda_copia_dos_caracteres(cabeca):
    antes = joblib.hash(cabeca)
    r = contrafactual_sem_marcadores_nos_caracteres(cabeca, "não inicie Cedrion")
    assert r["sufixo_retirado_apenas_do_canal_caracteres"] == " marcador_negacao_explicita"
    assert r["sem_retreino"] and not r["autoriza_promocao"]
    assert joblib.hash(cabeca) == antes


@pytest.mark.parametrize("texto", ["", "   ", None])
def test_entrada_invalida_nao_produz_explicacao(cabeca, texto):
    with pytest.raises(ValueError):
        explicar_pistas(cabeca, texto)


def test_coeficiente_invalido_nao_produz_atribuicao(cabeca):
    cabeca.named_steps["classifier"].coef_[0, 0] = np.nan
    with pytest.raises(ValueError, match="não finitos"):
        explicar_pistas(cabeca, "inicie Cedrion")


def test_sinais_atomicos_sao_explicados_sem_fingir_vocabulario(cabeca):
    textos = ["abra o editor", "não abra o editor", "evite abrir o editor", "leia algo"]
    h = criar_prototipo_negacao(cabeca, "sinais_atomicos").fit(textos, [False, True, True, False])
    antes = joblib.hash(h)
    r = explicar_pistas(h, "não abra o editor")
    s = r["canais"]["sinais"]
    assert "fora_vocabulario" not in s
    assert s["tipo"] == "sinais_atomicos"
    assert len(s["sinais"]) == 2
    assert [i["valor"] for i in s["sinais"]] == [1.0, 0.0]
    assert sum(i["contribuicao"] for i in s["sinais"]) == pytest.approx(s["soma_contribuicoes"])
    assert r["score"] == pytest.approx(r["intercepto"] + sum(c["soma_contribuicoes"] for c in r["canais"].values()))
    assert joblib.hash(h) == antes


def test_delta_atomico_conserva_soma_exata(cabeca):
    textos = ["abra o editor", "não abra o editor", "evite abrir o editor", "leia algo"]
    h = criar_prototipo_negacao(cabeca, "sinais_atomicos").fit(textos, [False, True, True, False])
    r = comparar_pistas(h, "abra o editor", "não abra o editor")
    assert sum(r["decomposicao_delta"].values()) == pytest.approx(r["delta_score"])

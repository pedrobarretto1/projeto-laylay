from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import numpy as np

import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.neural.dataset import validar_exemplo
from mente_laylay.neural.datasets.gerar_escopo_negacao_v1 import gerar_exemplos
from mente_laylay.neural.experimento_escopo_negacao import (
    ajustar_cabeca, comparar_cv, grupos_sem_duplicatas, medir_negacao,
)
import mente_laylay.neural.experimento_escopo_negacao as experimento
from mente_laylay.neural.qualidade import auditar_leakage_dataset


def test_lote_balanceado_treina_apenas_negacao_e_mantem_irmaos_juntos():
    itens = gerar_exemplos()
    assert len(itens) == 52
    assert Counter(i["negated"] for i in itens) == {True: 26, False: 26}
    assert len({i["validation_group"] for i in itens}) == 7
    for grupo in {i["validation_group"] for i in itens}:
        fatia = [i for i in itens if i["validation_group"] == grupo]
        assert {i["negated"] for i in fatia} == {True, False}
        assert len({i["domain"] for i in fatia}) >= 2
    for i in itens:
        assert validar_exemplo(i, intents_permitidas=intents_registradas())["training_heads"] == ["negation"]
        assert "autoriza_execucao" not in i


def test_lote_nao_copia_bateria_conhecida():
    b = json.loads((Path(__file__).parent / "fixtures/neural/bateria_linguistica_v1.json").read_text(encoding="utf-8"))
    r = auditar_leakage_dataset(gerar_exemplos(), [{"text": i["text"], "family": i["id"]} for i in b["casos"]])
    assert r["aprovado"]


def test_duplicatas_unem_grupos_transitivamente_sem_mutar_dados():
    itens = [
        {"text": t, "family": f, "negated": False}
        for t, f in (("abre A", "1"), ("ABRE A!", "2"), ("abre B", "2"), ("abre B", "3"))
    ]
    antes = deepcopy(itens)
    assert len(set(grupos_sem_duplicatas(itens))) == 1
    assert itens == antes


def test_rotulos_contraditorios_abortam_sem_falso_verde():
    with pytest.raises(ValueError, match="contraditórias"):
        grupos_sem_duplicatas([
            {"text": "leia texto", "family": "a", "negated": False},
            {"text": "leia texto", "family": "b", "negated": True},
        ])


def test_metrias_separam_cancelamento_perdido_de_cancelamento_inventado():
    r = medir_negacao([
        {"negated": True, "family": "cancelar"},
        {"negated": False, "family": "corrigir"},
    ], [False, True])
    assert r["negacoes_perdidas"] == r["negacoes_falsas"] == 1
    with pytest.raises(ValueError):
        medir_negacao([{"negated": True, "family": "x"}], [])


def test_ajuste_clona_cabeca_e_respeita_heads():
    original = Pipeline([("texto", TfidfVectorizer()), ("clf", LogisticRegression())])
    itens = gerar_exemplos()
    lixo = {"text": "vazamento", "negated": None, "training_heads": ["command"]}
    candidata = ajustar_cabeca(original, itens + [lixo])
    assert candidata is not original
    assert not hasattr(original[0], "vocabulary_")
    assert "vazamento" not in candidata[0].vocabulary_


def test_pesos_unitarios_reproduzem_ajuste_original():
    original = Pipeline([("texto", TfidfVectorizer()), ("clf", LogisticRegression())])
    itens = gerar_exemplos()
    simples = ajustar_cabeca(original, itens)
    ponderada = ajustar_cabeca(original, itens, pesos=[1.0] * len(itens))
    np.testing.assert_allclose(simples[-1].coef_, ponderada[-1].coef_)


@pytest.mark.parametrize("pesos", [[1], [1, 0], [1, -1], [1, float("nan")], [1, float("inf")]])
def test_pesos_invalidos_abortam(pesos):
    with pytest.raises(ValueError):
        ajustar_cabeca(None, gerar_exemplos()[:2], pesos=pesos)


def test_combinada_reutiliza_features_antigas_sem_modificar_prototipo():
    original = Pipeline([("features", TfidfVectorizer()), ("classifier", LogisticRegression())])
    combinada = experimento.criar_prototipo_negacao(original, "combinada")
    canais = dict(combinada[0].transformer_list)
    assert set(canais) == {"legado", "integral"}
    assert canais["legado"] is not original[0]
    ajustar_cabeca(combinada, gerar_exemplos())
    assert not hasattr(original[0], "vocabulary_")


def test_peso_novo_so_afeta_treino_e_preserva_particoes(monkeypatch):
    itens = gerar_exemplos()
    historicos = [dict(i, family="h_" + i["family"], validation_group="h_" + i["validation_group"], text="agora " + i["text"]) for i in itens]
    original = Pipeline([("features", TfidfVectorizer()), ("classifier", LogisticRegression())])
    chamadas = []
    real = ajustar_cabeca
    def observar(prototipo, exemplos, *, pesos=None):
        chamadas.append((deepcopy(exemplos), list(pesos)))
        return real(prototipo, exemplos, pesos=pesos)
    monkeypatch.setattr(experimento, "ajustar_cabeca", observar)
    ponderada = comparar_cv(original, historicos, itens, splits=3, peso_novos=4)
    assert len(chamadas) == 6
    for posicao, (exemplos, pesos) in enumerate(chamadas):
        assert len(exemplos) == len({i["text"] for i in exemplos})
        for item, peso in zip(exemplos, pesos, strict=True):
            assert peso == (4 if posicao % 2 and not item["family"].startswith("h_") else 1)
    normal = comparar_cv(original, historicos, itens, splits=3)
    assert ponderada["folds"] == normal["folds"]


@pytest.mark.parametrize("outro_prototipo", [False, True])
def test_cv_compara_mesmos_testes_e_preserva_fatias(outro_prototipo):
    itens = gerar_exemplos()
    historicos = [dict(i, family="h_" + i["family"], validation_group="h_" + i["validation_group"], text="agora " + i["text"]) for i in itens]
    prototipo = Pipeline([("texto", TfidfVectorizer()), ("clf", LogisticRegression())])
    alternativo = Pipeline([("texto", TfidfVectorizer(analyzer="char", ngram_range=(2, 3))), ("clf", LogisticRegression())]) if outro_prototipo else None
    r = comparar_cv(prototipo, historicos, itens, splits=3, prototipo_candidato=alternativo)
    grupos_teste = [set(f["grupos_teste"]) for f in r["folds"]]
    assert all(not a & b for n, a in enumerate(grupos_teste) for b in grupos_teste[n+1:])
    for fatia in r["fatias"].values():
        assert fatia["controle"]["total"] == fatia["candidato"]["total"] == 52

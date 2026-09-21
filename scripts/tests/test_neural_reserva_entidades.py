from collections import Counter
from copy import deepcopy

import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.neural.dataset import validar_exemplo
from mente_laylay.neural.datasets.gerar_escopo_negacao_v2 import gerar_grade
from mente_laylay.neural.experimento_escopo_negacao import comparar_cv, validar_reserva_entidades


def test_grade_separa_eixos_antes_do_treino():
    grade = gerar_grade()
    assert Counter(i["particao"] for i in grade) == {
        "treino": 288, "entidade": 96, "construcao": 144, "ambas": 48,
    }
    assert len({i["text"] for i in grade}) == len(grade)
    treino = [i for i in grade if i["particao"] == "treino"]
    reservas = [i for i in grade if i["particao"] != "treino"]
    assert validar_reserva_entidades(treino, reservas)["frases_duplicadas"] == 0
    for campo, particoes in (
        ("validation_group", {"construcao", "ambas"}),
        ("validation_entity_group", {"entidade", "ambas"}),
    ):
        assert not {i[campo] for i in treino} & {i[campo] for i in reservas if i["particao"] in particoes}
    for particao in {i["particao"] for i in grade}:
        assert Counter(i["negated"] for i in grade if i["particao"] == particao)[True] == Counter(i["negated"] for i in grade if i["particao"] == particao)[False]
    for i in grade:
        normalizado = validar_exemplo(i, intents_permitidas=intents_registradas())
        assert normalizado["training_heads"] == ["negation"]
        assert "particao" not in normalizado
        assert "entidades" not in normalizado


@pytest.mark.parametrize("texto", ["abra Zelvoria", "leia inventario_Zelvoria.txt", "volume em 83"])
def test_reserva_tambem_exclui_alvos_presentes_no_historico(texto):
    grade = gerar_grade()
    with pytest.raises(ValueError, match="entidades reservadas"):
        validar_reserva_entidades([{"text": texto}], [i for i in grade if i["particao"] != "treino"])


def test_reserva_nao_confunde_numero_com_substring():
    reservas = [i for i in gerar_grade() if i["particao"] != "treino"]
    assert validar_reserva_entidades([{"text": "código 1830"}], reservas)["frases_duplicadas"] == 0


def test_reserva_rejeita_frase_duplicada_mesmo_sem_entidade_reservada():
    reserva = next(i for i in gerar_grade() if i["particao"] == "construcao")
    with pytest.raises(ValueError, match="frase reservada"):
        validar_reserva_entidades([reserva], [reserva])


def test_cv_entidade_reutiliza_particionador_sem_mutar_grupos_de_construcao():
    treino = [i for i in gerar_grade() if i["particao"] == "treino"]
    antes = deepcopy(treino)
    historicos = [{"text": t, "family": f, "negated": n} for t, f, n in (
        ("execute tarefa", "h1", False), ("não execute tarefa", "h1", True),
        ("inicie trabalho", "h2", False), ("não inicie trabalho", "h2", True),
    )]
    proto = Pipeline([("features", TfidfVectorizer()), ("classifier", LogisticRegression())])
    r = comparar_cv(proto, historicos, treino, splits=3, eixo="entidade")
    assert treino == antes
    grupos = [g for f in r["folds"] for g in f["grupos_teste"]]
    assert len(grupos) == len(set(grupos))
    assert all(f"escopo_v2_e{i}" in grupos for i in range(6))
    assert r["fatias"]["nova"]["candidato"]["total"] == 288


def test_eixo_invalido_aborta():
    with pytest.raises(ValueError, match="eixo"):
        comparar_cv(None, [], [], eixo="aleatorio")

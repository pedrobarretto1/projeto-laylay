from copy import deepcopy

import pytest
from sklearn.model_selection import GroupKFold

from mente_laylay.neural.diagnostico_fold_negacao import selecionar_fold, diagnosticar, diagnosticar_margem
from mente_laylay.neural.treino import _hash_dados


@pytest.fixture
def dados():
    itens = [{"text": f"exemplo {g} {n}", "negated": bool(n), "family": g,
              "validation_group": g} for g in ("a", "b", "c", "d") for n in range(2)]
    grupos = [i["validation_group"] for i in itens]
    folds = [{"fold": n, "sha256_ids_teste": _hash_dados(list(map(int, te))),
              "grupos_teste": sorted({grupos[i] for i in te})}
             for n, (_, te) in enumerate(GroupKFold(4).split(itens, groups=grupos))]
    return itens, {"eixo": "construcao", "folds": folds}


def test_reproducao_mantem_familia_inteira_fora_do_treino(dados):
    itens, cv = dados
    treino, teste = selecionar_fold(itens, cv, "c")
    assert all(itens[i]["validation_group"] != "c" for i in treino)
    assert {itens[i]["validation_group"] for i in teste} == {"c"}
    assert not set(treino) & set(teste)


@pytest.mark.parametrize("campo,valor", [("sha256_ids_teste", "alterado"), ("grupos_teste", ["outro"]), ("fold", 8)])
def test_fold_divergente_aborta_mesmo_quando_nao_e_o_selecionado(dados, campo, valor):
    itens, cv = dados
    cv = deepcopy(cv)
    cv["folds"][-1][campo] = valor
    with pytest.raises(ValueError, match="não reproduz"):
        selecionar_fold(itens, cv, "d")


def test_grupo_ausente_aborta(dados):
    with pytest.raises(ValueError, match="exatamente um"):
        selecionar_fold(*dados, "ausente")


def test_eixo_incompativel_aborta(dados):
    itens, cv = dados
    cv["eixo"] = "entidade"
    with pytest.raises(ValueError, match="por construção"):
        selecionar_fold(itens, cv, "c")


def test_diagnostico_nao_sobrescreve_artefato(tmp_path):
    saida = tmp_path / "existente"
    saida.mkdir()
    with pytest.raises(FileExistsError):
        diagnosticar(experimento=tmp_path, anterior=tmp_path, historico=tmp_path, grupo="c", saida=saida)


@pytest.mark.parametrize("scores,separa", [([-2, -1], True), ([1, 0], False), ([0, 0], False)])
def test_margem_nao_confunde_limiar_zero_com_separabilidade(scores, separa):
    itens = [{"text": "correção", "negated": False}, {"text": "recusa", "negated": True}]
    r = diagnosticar_margem(itens, scores)
    assert r["existe_limiar_separador"] is separa
    assert not r["limiar_aplicado"]


@pytest.mark.parametrize("scores", [[0], [float("nan"), 0]])
def test_margem_invalida_aborta(scores):
    itens = [{"text": "a", "negated": False}, {"text": "b", "negated": True}]
    with pytest.raises(ValueError, match="finitos e alinhados"):
        diagnosticar_margem(itens, scores)

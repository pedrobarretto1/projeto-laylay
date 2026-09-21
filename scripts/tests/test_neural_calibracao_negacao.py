import pytest
from sklearn.model_selection import GroupKFold

from mente_laylay.neural.calibracao_negacao_experimental import escolher_limiar, criar_particoes, executar
from mente_laylay.neural.experimento_escopo_negacao import grupos_sem_duplicatas
from mente_laylay.neural.treino import _hash_dados


FATIAS = ["historica", "historica", "nova", "nova"]
ROTULOS = [False, True, False, True]


def test_ajuste_recupera_recusa_sem_trocar_por_cancelamento_falso():
    r = escolher_limiar([-3, -1, -4, -2], ROTULOS, FATIAS)
    assert -3 <= r["limiar"] < -2
    assert r["motivo"] == "ganho_pareto"
    assert all(v == {"negacoes_perdidas": 0, "negacoes_falsas": 0} for v in r["ajustado"].values())


def test_ganho_novo_nao_compensa_regressao_historica():
    r = escolher_limiar([-0.5, 1, -3, -1], ROTULOS, FATIAS)
    assert r["limiar"] == 0
    assert r["motivo"] == "zero_preservado"


def test_zero_preferido_quando_ja_acerta():
    assert escolher_limiar([-2, 2, -1, 1], ROTULOS, FATIAS)["limiar"] == 0


def test_tambem_pode_reduzir_cancelamento_falso_sem_perder_recusa():
    r = escolher_limiar([1, 4, 2, 5], ROTULOS, FATIAS)
    assert 2 <= r["limiar"] < 4


def test_empate_de_scores_nao_inventa_separacao():
    assert escolher_limiar([0, 0, 0, 0], ROTULOS, FATIAS)["limiar"] == 0


@pytest.mark.parametrize("scores,rotulos,fatias", [([], [], []), ([1], [True, False], ["nova"]),
    ([float("nan")], [True], ["nova"]), ([float("inf")], [True], ["nova"]),
    ([0, 1], [0, 1], ["nova", "nova"])])
def test_dados_invalidos_abortam(scores, rotulos, fatias):
    with pytest.raises(ValueError):
        escolher_limiar(scores, rotulos, fatias)


def test_fatia_ausente_ou_sem_ambas_classes_preserva_zero():
    for fatias in (["nova"] * 4, ["historica", "nova", "historica", "nova"]):
        r = escolher_limiar([-3, -1, -4, -2], ROTULOS, fatias)
        assert r["limiar"] == 0
        assert r["motivo"] == "suporte_insuficiente_por_fatia"


def test_tres_particoes_preservam_familias_e_duplicatas_normalizadas():
    itens = [{"text": f"exemplo {g} {n}", "negated": bool(n), "family": str(g), "validation_group": str(g)}
             for g in range(12) for n in range(2)]
    itens.append(dict(itens[0], text="EXEMPLO 0 0", family="alias", validation_group="alias"))
    grupos = grupos_sem_duplicatas(itens)
    folds = [{"fold": n, "sha256_ids_teste": _hash_dados(list(map(int, te))), "grupos_teste": sorted({grupos[i] for i in te})}
             for n, (_, te) in enumerate(GroupKFold(4).split(itens, groups=grupos))]
    ps = criar_particoes(itens, {"eixo": "construcao", "folds": folds})
    assert sorted(i for p in ps for i in p["teste"]) == list(range(len(itens)))
    for p in ps:
        ids = [set(p[k]) for k in ("treino", "calibracao", "teste")]
        gs = [{grupos[i] for i in ii} for ii in ids]
        assert not gs[0] & gs[1] and not gs[1] & gs[2] and not gs[0] & gs[2]
        assert all((0 in ii) == (len(itens) - 1 in ii) for ii in ids)


def test_destino_existente_aborta_antes_de_ler_ou_treinar(tmp_path):
    with pytest.raises(FileExistsError):
        executar(referencia=tmp_path / "ausente", historico=tmp_path / "ausente", destino=tmp_path)

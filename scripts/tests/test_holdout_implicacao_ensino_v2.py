"""O conjunto inédito mantém definição, exemplo e negativos por domínio."""

from collections import Counter

from scripts.analises.holdout_implicacao_ensino_v2 import CASOS, FONTES


def test_holdout_congelado_tem_matriz_balanceada_e_fontes_rastreaveis() -> None:
    assert len(CASOS) == 24
    assert len({caso[0] for caso in CASOS}) == 24
    assert len(FONTES) == 4
    assert all(caso[1] in FONTES for caso in CASOS)
    assert all(fonte["url"].startswith("https://") and fonte["texto"] for fonte in FONTES.values())
    assert Counter(caso[4] for caso in CASOS) == {
        "sustentada": 8, "contradita": 8, "sem_prova": 8,
    }
    for id_fonte in FONTES:
        assert Counter((papel, esperado) for _, fonte, papel, _, esperado in CASOS if fonte == id_fonte) == {
            (papel, esperado): 1
            for papel in ("definicao", "exemplo")
            for esperado in ("sustentada", "contradita", "sem_prova")
        }

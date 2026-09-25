"""O recibo literal não pode inventar fonte nem substituir o gabarito."""

from scripts.analises.sonda_implicacao_inedita import CASOS, FONTES, prova_localizada


def test_holdout_novo_separa_definicao_exemplo_e_tres_classes() -> None:
    assert len(CASOS) == 24
    assert len({caso[0] for caso in CASOS}) == len(CASOS)
    assert {caso[2] for caso in CASOS} == {"definicao", "exemplo"}
    assert {caso[4] for caso in CASOS} == {"sustentada", "contradita", "sem_prova"}
    assert all(caso[1] in FONTES for caso in CASOS)
    assert all(fonte["url"].startswith("https://") and fonte["texto"] for fonte in FONTES.values())


def test_recibo_exige_citacao_literal_para_aprovacao_ou_contradicao() -> None:
    fonte = "Os componentes ficam em série no mesmo ramo do circuito."
    assert prova_localizada("sustentada", "mesmo ramo do circuito", fonte)
    assert prova_localizada("contradita", "mesmo ramo do circuito", fonte)
    assert not prova_localizada("sustentada", "ramo diferente", fonte)
    assert not prova_localizada("sustentada", "mesmo ramo", fonte)
    assert not prova_localizada("sem_prova", "mesmo ramo do circuito", fonte)
    assert prova_localizada("sem_prova", "", fonte)
    assert not prova_localizada("aprovada", "mesmo ramo do circuito", fonte)

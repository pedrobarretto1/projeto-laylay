"""Partes não podem desaparecer nem ser promovidas por uma prova parcial."""

from scripts.analises.sonda_implicacao_atomica import consolidar, fragmentos_explicitos


FONTE = "O laço percorre os itens de uma lista na ordem em que aparecem."


def test_conjuncao_explicita_separa_efeito_novo_da_relacao_apoiada() -> None:
    assert fragmentos_explicitos("O laço percorre a lista em ordem e imprime tudo.") == [
        "O laço percorre a lista em ordem", "imprime tudo."
    ]


def test_consolidacao_recusa_parte_ausente_e_citacao_inventada() -> None:
    apoiada = {"id": 1, "classe": "sustentada", "trecho_literal": "percorre os itens de uma lista"}
    assert consolidar([apoiada], 2, FONTE)["classe"] == "invalida"
    assert consolidar([apoiada, {"id": 2, "classe": "sustentada", "trecho_literal": "imprime automaticamente"}], 2, FONTE)["classe"] == "invalida"
    assert consolidar([apoiada, {"id": 2, "classe": "sem_prova", "trecho_literal": ""}], 2, FONTE) == {
        "classe": "sem_prova", "prova_localizada": True,
    }


def test_consolidacao_exige_ordem_e_recibo_para_contradicao() -> None:
    assert consolidar([{"id": 2, "classe": "sem_prova", "trecho_literal": ""}], 1, FONTE)["classe"] == "invalida"
    assert consolidar([{"id": 1, "classe": "contradita", "trecho_literal": ""}], 1, FONTE)["classe"] == "invalida"

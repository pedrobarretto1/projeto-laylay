"""O veto detecta acréscimos, mas rejeita sinônimos: não é um portão pronto."""

from scripts.analises.veto_lexical_ensino import detalhes_sem_rastro


def test_acrescimo_sobre_fotossintese_fica_visivel() -> None:
    alegacao = (
        "A luz ajuda na fotossíntese: transforma dióxido de carbono e água "
        "em glucose e oxigênio."
    )
    citacao = "A luz é essencial para a fotossíntese."
    ausentes = detalhes_sem_rastro(alegacao, citacao)
    assert {"dioxido", "carbono", "agua", "glucose", "oxigenio"} <= set(ausentes)


def test_numero_novo_nao_herda_prova_de_regra_geral() -> None:
    assert "12" in detalhes_sem_rastro(
        "12 dividido por 3 = 4", "Divisão reparte uma quantidade em partes iguais."
    )


def test_parafrase_legitima_tambem_pode_ser_bloqueada() -> None:
    # Falha de cobertura é custo medido, não autorização para adicionar
    # exceção frase a frase ao runtime.
    ausentes = detalhes_sem_rastro(
        "O girassol jovem segue o sol.",
        "Os girassóis jovens acompanham o percurso do sol.",
    )
    assert "segue" in ausentes


def test_mesmas_palavras_em_relacao_invertida_nao_sao_prova() -> None:
    assert detalhes_sem_rastro(
        "A fica acima de B.", "B fica acima de A."
    ) == []

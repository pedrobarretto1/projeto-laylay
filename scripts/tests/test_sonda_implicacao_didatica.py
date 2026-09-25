"""O benchmark de implicação tem fonte literal e gabaritos separados."""

from scripts.analises.sonda_implicacao_didatica import preparar_casos


def test_gabarito_tem_fontes_reais_e_controles_para_definicao_e_exemplo() -> None:
    casos = preparar_casos()
    assert len(casos) >= 12
    assert {item["tipo"] for item in casos} == {"definicao", "exemplo"}
    assert {item["esperado"] for item in casos} == {"sustentada", "contradita", "sem_prova"}
    assert all(item["texto_fonte"].endswith(".") and item["url"].startswith("https://") for item in casos)

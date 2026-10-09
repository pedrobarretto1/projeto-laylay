"""Um marcador pessoal não atribui ao usuário emoções de outra oração."""

import pytest

from mente_laylay.emocoes.leitura_usuario import analisar_intencao_emocional


@pytest.mark.parametrize("texto,esperada", [
    ("antes eu estava triste, mas agora estou aliviado", None),
    ("eu estava triste ontem; hoje estou aliviado", None),
    ("Eu estava ansioso antes. Agora estou aliviado.", None),
    ("Ela está triste, mas eu estou feliz.", "alegria"),
    ("Estou feliz porque antes eu estava preocupado.", "alegria"),
    ("Estou animado; meu colega está cansado.", "alegria"),
    ("Meu irmão está bravo. Eu me sinto culpado.", "culpa"),
    ("Eu estou pensando em como ela ficou triste.", None),
])
def test_emocao_lexical_deve_pertencer_ao_predicado_pessoal(texto, esperada):
    leitura = analisar_intencao_emocional(texto)
    if esperada is None:
        assert leitura == {}, "menção sem predicado pessoal inequívoco fica para a principal"
    else:
        assert leitura["emocao"] == esperada


@pytest.mark.parametrize("texto,esperada,intensidade", [
    ("Estou triste hoje.", "tristeza", 2),
    ("Estou muito triste com isso.", "tristeza", 3),
    ("Eu me sinto meio culpado.", "culpa", 1),
    ("Ando me sentindo um pouco cansada.", "cansaco", 1),
    ("Fiquei muito feliz com a notícia.", "alegria", 3),
    ("Tô realmente preocupada.", "ansiedade", 2),
    ("Estou triste demais.", "tristeza", 3),
    ("Estou cansado pra caramba.", "cansaco", 3),
    ("Estou cansado para caramba.", "cansaco", 3),
    ("Estou estressada no limite.", "irritacao", 3),
    ("Que noite chata.", "tedio", 2),
    ("Tem nada para fazer nessa noite.", "tedio", 2),
    ("Não aguento mais.", "esgotamento", 3),
])
def test_predicados_pessoais_e_relato_curto_de_tedio_continuam_validos(
    texto, esperada, intensidade,
):
    leitura = analisar_intencao_emocional(texto)
    assert leitura["emocao"] == esperada
    assert leitura["intensidade"] == intensidade


@pytest.mark.parametrize("texto", [
    "Estou triste, mas ela está muito feliz.",
    "Estou triste; meu irmão está um pouco cansado.",
])
def test_intensidade_de_outro_predicado_nao_altera_o_sinal_pessoal(texto):
    assert analisar_intencao_emocional(texto)["intensidade"] == 2

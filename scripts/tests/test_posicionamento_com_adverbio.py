"""Modificador do juízo não é uma atribuição biográfica certificada."""
import pytest
from tests.test_continuidade_resposta_recente import plano_atual
from mente_laylay.cognicao.afirmacoes_interlocutor import conferir_afirmacoes_interlocutor

@pytest.mark.parametrize('fala',[
    'Você está absolutamente certo.',
    'Você está totalmente correta.',
    'Você está completamente equivocada.',
    'Você está absolutamente certo: há uma diferença entre ausência de prova e prova de ausência.',
])
def test_modificador_lexical_e_oracao_impessoal_nao_inventam_estado_pessoal(fala):
    p=plano_atual('Podemos discordar. O que você acha?',())
    assert conferir_afirmacoes_interlocutor(fala,plano=p) is None

@pytest.mark.parametrize('fala',[
    'Você está absolutamente certo e está na escola.',
    'Você está totalmente correto sobre seu diagnóstico médico.',
    'Você está absolutamente certo: está na escola.',
    'Você está absolutamente certo: há de estar cansado.',
    'Você está absolutamente certo: há alguém aqui e você está na escola.',
    'Você está cansado.',
])
def test_modificador_nao_dispensa_complemento_ou_atribuicao_a_pessoa(fala):
    p=plano_atual('Podemos discordar. O que você acha?',())
    assert conferir_afirmacoes_interlocutor(fala,plano=p) is not None

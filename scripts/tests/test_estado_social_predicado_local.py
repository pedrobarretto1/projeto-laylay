"""Estado social não usa adjetivo ou locução de outra oração como predicado."""
import pytest
from tests.test_escopo_permissivo_contraste import CASOS
from mente_laylay.cognicao.interpretacao_social import analisar_ato_social

@pytest.mark.parametrize('texto',[
    next(c['entrada']for c in CASOS if c['id']=='papo-008'),
    'Você tá falando de robôs? Pensando bem, isso é engraçado.',
    'Você está lendo um livro. Ele termina bem?',
    'Você está mencionando o filme triste?',
])
def test_adjetivo_de_outro_predicado_nao_se_torna_bem_estar(texto):
    assert analisar_ato_social(texto).get('tipo') not in {'WELLBEING','WELLBEING_REPLY'}

@pytest.mark.parametrize('texto',[
    'Como você está?', 'Você está bem?', 'Você tá muito bem?',
    'Tudo bem com você?', 'Como tu tá?',
    'Como que você tá?', 'Como é que você está?',
])
def test_pergunta_social_com_predicado_vinculado_permanece(texto):
    assert analisar_ato_social(texto).get('tipo')=='WELLBEING'


@pytest.mark.parametrize('texto',['Estou me sentindo triste.','Eu tô me sentindo muito feliz.'])
def test_perifrase_reflexiva_conserva_o_estado_da_pessoa(texto):
    assert analisar_ato_social(texto).get('tipo')=='WELLBEING_REPLY'

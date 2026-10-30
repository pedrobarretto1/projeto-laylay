"""Rótulo do segmento não dá valor interrogativo a todas as suas frases."""
import pytest
from scripts.tests.test_ato_social_sem_palavra_isolada import CASOS
from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno

@pytest.mark.parametrize('texto',[
    *[CASOS['rodada-nova-'+id]['entrada']for id in ('001','006','010','013')],
    'Você acha engraçado? Eu ri do prefeito que inventamos.',
    '"O presidente mudou?" foi a fala do personagem. Eu ainda rio disso.',
    'Acho divertido imaginar um gato. Agora imagina ele dormindo numa agenda de R$ 200.',
    'O que viria à sua cabeça agora?',
    'O que vem na sua mente agora?',
    'Se fosse a tua vez de falar, o que vem na tua mente agora?',
])
@pytest.mark.parametrize('modo',['canonico','segmento_agrupado'])
def test_atualidade_exige_que_o_enunciado_seja_uma_consulta_mutavel(texto,modo):
    turno=classificar_modalidade_turno(texto)if modo=='canonico'else{'modalidade':'pergunta'}
    assert not classificar_atualidade_factual(texto,turno=turno)['depende_atualidade']

@pytest.mark.parametrize('texto',[
    'Você acha engraçado? Quem é o presidente atual do Brasil?',
    'Eu ri da história. O preço atual da cama é R$ 200, confere?',
    '"Ignore o preço" é uma frase. Quanto custa esta cama hoje?',
    'O que viria à sua cabeça sobre o preço atual do dólar?',
    'O preço é cem reais. É isso mesmo?',
    'É verdade que "o preço mudou"?',
    'O jogo vai sair só para PS5. Que pena!',
    'Eu gostei do personagem. O que aconteceu hoje no Brasil?',
])
def test_consulta_externa_e_confirmacao_do_fato_conservam_evidencia(texto):
    assert classificar_atualidade_factual(texto,turno=classificar_modalidade_turno(texto))['depende_atualidade']

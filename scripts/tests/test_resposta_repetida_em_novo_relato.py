"""Resposta antiga não atende automaticamente um novo ato conversacional."""
import pytest
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao


def avaliar(texto,fala):
    turno=classificar_modalidade_turno(texto)
    turno['funcao_comunicativa']={'funcao':'conquista'if 'terminei'in texto or 'consegui'in texto else 'informacao'}
    p=planejar_turno(texto,turno=turno)
    p['contrato_fala']=construir_contrato_semantico_fala(texto,turno=turno,plano=p,
        funcao_comunicativa=turno['funcao_comunicativa'])
    return avaliar_qualidade_comunicacao(texto,fala,plano=p,ultima_resposta=fala)


@pytest.mark.parametrize('texto',[
    'mas consegui terminar os exercícios e fiquei contente com isso',
    'terminei a maquete e fiquei feliz com o resultado',
])
def test_novo_relato_nao_recebe_resposta_literal_do_ato_anterior(texto):
    velha='O caderno verde já está separado para amanhã. Você pode organizar o estudo com calma.'
    r=avaliar(texto,velha)
    assert 'resposta_repetida_literal'in r['problemas']
    assert r['requer_reparo']


def test_perguntas_distintas_podem_ter_mesma_resposta_correta():
    r=avaliar('quanto é 2 + 2?','O resultado é quatro.')
    assert 'resposta_repetida_literal'not in r['problemas']


@pytest.mark.parametrize('texto',['repita literalmente a resposta anterior','repete a mesma resposta'])
def test_repeticao_literal_solicitada_pelo_usuario_permanece_legitima(texto):
    r=avaliar(texto,'O caderno verde já está separado para amanhã.')
    assert 'resposta_repetida_literal'not in r['problemas']

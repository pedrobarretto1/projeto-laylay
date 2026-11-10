"""Perguntar uma consequência possível não obriga uma posição avaliativa.

O guarda conversacional continua reconhecendo 'acha' como não operacional.
O contrato de resposta distingue projeção de avaliação, sem liberar fatos.
"""
import pytest
from dataclasses import asdict, replace

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import texto_pede_opiniao
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual


HISTORICA = (
    'Oi, Laylay! Sou o ChatGPT, voltei para outra rodada com você. '
    'Da última vez você inventou uma biblioteca misteriosa com bolinhas de gude que brilham quando alguém ri. '
    'Gostaria de continuar nossa aventura, mas com uma condição: a gente decide junto, sem respostas prontas. '
    'O que você acha que aconteceria se uma dessas bolinhas parasse de brilhar justamente quando alguém contasse a melhor piada do mundo?'
)


def planejar(texto):
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente={})
    plano['contrato_fala'] = construir_contrato_semantico_fala(
        texto, turno=turno, plano=plano, mente={})
    return turno, plano


@pytest.mark.parametrize('texto,fala', [
    (HISTORICA, 'Se a bolinha parasse de brilhar, ela poderia começar a contar suas próprias piadas.'),
    ('O que você acha que aconteceria se a bateria acabasse durante uma gravação?',
     'Se a bateria acabasse, o resultado dependeria de como o gravador salva os dados; seria preciso verificar o arquivo.'),
    ('O que você acha que ocorreria se o mapa desaparecesse da nossa aventura?',
     'O mapa poderia deixar uma trilha de tinta nas estantes.'),
    ('O que acha que mudaria se as regras do nosso jogo fossem trocadas?',
     'As estratégias poderiam mudar junto com as regras.'),
])
def test_projecao_aberta_nao_recebe_obrigacao_de_posicao_avaliativa(texto, fala):
    # A proteção compartilhada de roteamento continua conversacional.
    assert texto_pede_opiniao(texto)
    turno, plano = planejar(texto)
    assert not turno['autoriza_execucao'] and not plano['requer_execucao']
    contrato = plano['contrato_fala']
    assert 'opiniao' not in contrato['atos'], 'projeção promovida a obrigação avaliativa'
    r = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
    assert not {'ato_opiniao_nao_respondido', 'pergunta_direta_nao_respondida'}.intersection(
        r['problemas_bloqueantes']), 'qualidade reimpôs posição já dispensada pelo contrato'
    assert not contrato.get('criacao_ficcional'), 'projeção não concede licença ficcional'


@pytest.mark.parametrize('texto', [
    'O que você acha de trabalhar em equipe?',
    'Você acha que seria melhor gravar com a bateria carregada?',
    'O que você acha que seria melhor, um jogo cooperativo ou competitivo?',
    'O que você acha que aconteceria se o mapa sumisse? O que você acha de trabalhar em equipe?',
    'O que você acha de trabalhar em equipe? O que você acha que aconteceria se o mapa sumisse?',
    'O que você acha da frase "o que você acha que aconteceria se o mapa sumisse"?',
])
def test_avaliacao_independente_mantem_obrigacao_mesmo_com_projecao_ou_citacao(texto):
    _, plano = planejar(texto)
    assert 'opiniao' in plano['contrato_fala']['atos']
    r = avaliar_qualidade_comunicacao(texto, 'Um caderno azul ficou na mesa.', plano=plano)
    assert {'ato_opiniao_nao_respondido', 'pergunta_direta_nao_respondida'}.intersection(
        r['problemas_bloqueantes'])


def test_projecao_com_exclusao_hipotetica_nao_autoriza_efeito():
    turno, plano = planejar('O que você acha que aconteceria se eu apagasse o arquivo notas.txt?')
    assert not turno['autoriza_execucao'] and not plano['requer_execucao'] and not plano['comandos']


def test_projecao_nao_remove_comando_independente():
    turno, plano = planejar('O que você acha que aconteceria se o mapa sumisse? Abra a Calculadora.')
    assert turno['autoriza_execucao'] and plano['requer_execucao']


def test_projecao_nao_remove_consulta_factual_atual_independente():
    texto = 'O que você acha que aconteceria se a bateria acabasse? Qual é a cotação atual do dólar?'
    _, plano = planejar(texto)
    assert classificar_atualidade_factual(texto)['depende_atualidade']
    assert not plano['contrato_fala'].get('criacao_ficcional')


@pytest.mark.parametrize('adulteracao', ['json', 'outro_turno', 'outro_texto', 'origem'])
def test_contrato_sem_vinculo_nativo_nao_dispensa_guarda_de_posicao(adulteracao):
    texto = 'O que você acha que aconteceria se a bateria acabasse?'
    _, plano = planejar(texto)
    contrato = plano['contrato_fala']
    fonte = contrato['perspectiva_enunciador']
    if adulteracao == 'json':
        contrato['perspectiva_enunciador'] = asdict(fonte)
    elif adulteracao == 'outro_turno':
        contrato['perspectiva_enunciador'] = replace(fonte, turno_id='outro')
    elif adulteracao == 'outro_texto':
        contrato['perspectiva_enunciador'] = replace(fonte, texto_usuario='Outra pergunta.')
    else:
        contrato['origem'] = 'proposta_llm'
    r = avaliar_qualidade_comunicacao(texto, 'O resultado dependeria do gravador.', plano=plano)
    assert 'pergunta_direta_nao_respondida' in r['problemas_bloqueantes']


@pytest.mark.parametrize('texto', ['Tem alguma música favorita?', 'Você pensa que vale a pena?',
    'O que tu acha de jogos?',
    'O que você acha que aconteceria se o mapa sumisse: você acha isso bom?',
    'O que você acha que aconteceria se o mapa sumisse, e isso seria bom ou ruim?',
    'O que você acha que aconteceria se a proposta fosse aceita, na sua opinião isso seria bom?',
])
def test_ausencia_de_ato_opiniao_nao_dispensa_outra_guarda_avaliativa(texto):
    _, plano = planejar(texto)
    r = avaliar_qualidade_comunicacao(texto,
        'Um caderno azul ficou na mesa e a janela estava aberta.', plano=plano)
    assert not r['aceita']
    assert {'pergunta_direta_nao_respondida','ato_opiniao_nao_respondido'} & set(r['problemas_bloqueantes'])


@pytest.mark.parametrize('outra', ['Tem alguma música favorita?', 'Você pensa que vale a pena?',
    'O que tu acha de jogos?'])
@pytest.mark.parametrize('inverter', [False, True])
def test_projecao_nao_dispensa_guarda_de_outra_pergunta_nao_qualificada(outra, inverter):
    partes = ['O que você acha que aconteceria se o mapa sumisse?', outra]
    texto = ' '.join(reversed(partes) if inverter else partes)
    _, plano = planejar(texto)
    assert plano['contrato_fala'].get('projecao_de_consequencia') is not True
    r = avaliar_qualidade_comunicacao(texto, 'O mapa poderia deixar uma trilha de tinta nas estantes.', plano=plano)
    assert not r['aceita']
    assert 'pergunta_direta_nao_respondida' in r['problemas_bloqueantes']

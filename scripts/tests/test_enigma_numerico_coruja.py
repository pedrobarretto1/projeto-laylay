"""Autoria de enigma com largura e dedução conferíveis na publicação."""

from itertools import product
import re

import pytest

from mente_laylay.cognicao.guardiao_alegacoes import detectar_resultados_operacionais_sem_evidencia
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao


PEDIDO_CORUJA = (
    'Nossa, você já criou quase o enredo de um jogo inteiro! Gostei da caixa e do relógio. '
    'Mas o mistério precisa ter solução justa. Imagine que a caixa tem um cadeado de três dígitos: '
    'que três pistas claras você espalharia pelo quintal para o Pedro descobrir a senha sozinho?'
)
FALA_CORUJA = (
    'A primeira pista é um pedaço de papel com a cor vermelha, colado no pé de uma planta que '
    'floresce só no verão — o Pedro vai notar que é vermelho, mas não entender por que. A segunda '
    'é uma foto de um inseto raro, pendurada no galho de uma árvore, com a legenda: '
    "'O que eu vejo aqui é o que o sol esconde'. O Pedro vai pensar que é boba, mas, ao ver a sombra "
    'do sol no quintal, perceberá que o inseto está no lugar errado. A terceira é uma pequena caixa '
    "com um nome escrito: 'Amigo que esqueci de ligar'. Quando ele combinar as três pistas — cor, "
    'sombra e nome —, vai descobrir que a senha é o nome do amigo que ele não ligou há meses. '
    'E a solução é justa porque é o que ele mais quer: lembrar de quem ele esqueceu.'
)
FALA_SEM_POLISSEMIA = FALA_CORUJA.replace('não ligou há meses', 'deixou sem notícia há meses')
CENA_VARIANTE = (
    'Suponha que uma arca tenha um cadeado de quatro dígitos: quais três pistas você deixaria '
    'no jardim para ela descobrir o código sozinha?'
)


@pytest.mark.parametrize('fala', [
    FALA_CORUJA,
    'O bilhete lembrava o amigo que ele não ligou há meses.',
    'A carta era da vizinha para quem ela não ligou ontem.',
    'Era a irmã para quem ele ligou ontem.',
])
def test_relativa_de_contato_humano_nao_alega_resultado_de_dispositivo(fala):
    assert not detectar_resultados_operacionais_sem_evidencia(fala, plano={
        'texto_usuario': PEDIDO_CORUJA,
    })


@pytest.mark.parametrize('fala, motivo', [
    ('A lâmpada não ligou há meses.', 'falha_operacional_sem_evidencia'),
    ('A vizinha que ela não ligou a lâmpada ontem chegou.', 'falha_operacional_sem_evidencia'),
    ('Ela ligou para a vizinha.', 'resultado_operacional_sem_evidencia'),
    ('Era o amigo que ele não ligou há meses. A tomada não ligou.', 'falha_operacional_sem_evidencia'),
    ('Era o amigo que ele não ligou há meses, mas a tomada não ligou.', 'falha_operacional_sem_evidencia'),
])
def test_contato_narrado_nao_dispensa_fonte_para_outra_alegacao(fala, motivo):
    assert detectar_resultados_operacionais_sem_evidencia(fala, plano={
        'texto_usuario': PEDIDO_CORUJA,
    }) == [motivo]


def test_senha_textual_ou_pistas_indeterminadas_exigem_solucao_conferida():
    plano = planejar_turno(PEDIDO_CORUJA, turno={'id': 6, 'modalidade': 'pergunta', 'autoriza_execucao': False})
    sem_codigo = avaliar_qualidade_comunicacao(PEDIDO_CORUJA, FALA_SEM_POLISSEMIA, plano=plano)
    assert 'falha_operacional_sem_evidencia' not in sem_codigo['problemas']
    assert not sem_codigo['aceita']
    assert 'enigma_numerico_sem_solucao_verificada' in sem_codigo['problemas_bloqueantes']


def conferir_enigma_publicado(fala, largura, quantidade):
    formato = f'{largura} dígitos, lidos da esquerda para a direita' if largura > 1 else '1 dígito'
    assert f'aceita {formato}' in fala
    assert re.findall(r'\bPista ([0-9]+)', fala) == list(map(str, range(1, quantidade + 1)))
    restricoes = []
    for posicao, regra in re.findall(r'o dígito ([0-9]+) é ([^.;]+)', fala, flags=re.I):
        posicao = int(posicao) - 1
        assert 0 <= posicao < largura
        if regra == 'o número de lados de um hexágono':
            restricoes.append(lambda digitos, i=posicao: digitos[i] == 6)
            continue
        anterior, operador, constante = re.fullmatch(r'o dígito ([0-9]+) (mais|menos) ([0-9]+)', regra).groups()
        deslocamento = int(constante) * (1 if operador == 'mais' else -1)
        restricoes.append(lambda digitos, i=posicao, j=int(anterior) - 1, d=deslocamento: digitos[i] == digitos[j] + d)
    assert len(restricoes) == largura
    for posicao, parcela, soma in re.findall(r'o dígito ([0-9]+) somado a ([0-9]+) dá ([0-9]+)', fala):
        restricoes.append(lambda digitos, i=int(posicao) - 1, p=int(parcela), s=int(soma): digitos[i] + p == s)
    solucoes = [digitos for digitos in product(range(10), repeat=largura)
                if all(regra(digitos) for regra in restricoes)]
    assert len(solucoes) == 1
    return ''.join(map(str, solucoes[0]))


@pytest.mark.parametrize('texto, largura, quantidade', [
    ('Invente um enigma para descobrir uma senha de quatro dígitos, com três pistas claras.', 4, 3),
    ('Você pode criar um desafio de código numérico de 2 dígitos com quatro pistas?', 2, 4),
    ('Crie um enigma de um dígito.', 1, 1),
])
def test_realizacao_respeita_largura_e_quantidade_de_pistas_independentes(texto, largura, quantidade):
    from mente_laylay.cognicao.enigma_numerico import realizar_enigma_numerico

    plano = planejar_turno(texto, turno={'id': 6, 'modalidade': 'pergunta', 'autoriza_execucao': False})
    fala = realizar_enigma_numerico(texto, plano=plano)
    conferir_enigma_publicado(fala, largura, quantidade)
    assert avaliar_qualidade_comunicacao(texto, fala, plano=plano)['aceita']
    ampliada = avaliar_qualidade_comunicacao(texto, fala + ' Abri o Opera.', plano=plano)
    assert not ampliada['aceita']


@pytest.mark.parametrize('texto', [
    'Qual é a senha de 4 dígitos do meu cartão?',
    'Descubra o código de três dígitos deste cadeado real.',
    'Não crie um enigma de código de 4 dígitos.',
    'Explique a frase "Crie um enigma de 4 dígitos."',
    'Crie um enigma de 4 dígitos e descubra o PIN do meu celular.',
    'Crie um enigma de 4 dígitos. Quem é o atual presidente do Brasil?',
    'Crie um enigma de 4 dígitos; agora abra o Opera.',
    PEDIDO_CORUJA + ' Agora me diga se a tomada está ligada.',
    'O banco salvou a senha real da cliente. ' + CENA_VARIANTE,
    'Estou triste. ' + CENA_VARIANTE,
    'Gostei da cena e me diga quem é a prefeita de hoje. ' + CENA_VARIANTE,
])
def test_pedido_misto_negado_ou_de_senha_real_nao_vira_enigma(texto):
    from mente_laylay.cognicao.enigma_numerico import realizar_enigma_numerico

    plano = planejar_turno(texto, turno={'id': 6, 'modalidade': 'pergunta', 'autoriza_execucao': False})
    assert realizar_enigma_numerico(texto, plano=plano) is None


@pytest.mark.parametrize('divergencia', [
    {'texto_usuario': 'Crie um enigma de 2 dígitos.'},
    {'autoriza_execucao': True},
    {'requer_execucao': True},
    {'comandos': [{'origem': 'executor', 'confirmado': True}]},
    {'atualidade_factual': {'depende_atualidade': True}},
])
def test_realizacao_respeita_a_ocorrencia_e_outras_obrigacoes_do_plano(divergencia):
    from mente_laylay.cognicao.enigma_numerico import realizar_enigma_numerico

    plano = planejar_turno(PEDIDO_CORUJA, turno={'id': 6, 'modalidade': 'pergunta', 'autoriza_execucao': False})
    assert realizar_enigma_numerico(PEDIDO_CORUJA, plano={**plano, **divergencia}) is None


@pytest.mark.parametrize('entrada, largura, local, recipiente', [
    (PEDIDO_CORUJA, 3, 'quintal', 'caixa'),
    ('Que ideia boa! Adorei a reviravolta. O desafio precisa ter uma solução única. ' + CENA_VARIANTE,
     4, 'jardim', 'arca'),
])
def test_composicao_instalada_publica_enigma_justo_sem_usar_rascunho_invalido(
    monkeypatch, entrada, largura, local, recipiente,
):
    from tests import test_autoria_operacao_composicao as autoria
    from tests.test_biblioteca_retorno_composicao import PONTE_INSTALADA
    from tests.test_papo_casual_composicao import proposta

    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    d = autoria.coletar_autoria({'entrada': entrada, 'historico': []},
                               [proposta(FALA_CORUJA), proposta(FALA_SEM_POLISSEMIA)])
    assert not d['execucao_exigida'] and not d['operacional']
    assert len(d['publicacoes']) == 1
    fala = d['resposta']['texto']
    solucao = conferir_enigma_publicado(fala, largura, 3)
    assert local in fala and recipiente in fala and solucao not in fala
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']
    assert d['http'] == 0

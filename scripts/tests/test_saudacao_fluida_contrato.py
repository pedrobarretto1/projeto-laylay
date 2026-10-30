"""Cortesia integral compartilha o owner de presença, sem diagnóstico técnico."""
import json

import pytest

from scripts.tests.test_presenca_conversacional import preparar
from mente_laylay.cognicao.presenca_conversacional import realizacoes_presenca
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao, montar_pacote_reparo_comunicacao,
)
from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral


LONGA_PUBLICADA = (
    'Oi, tudo bem com você. Estou funcionando normalmente, só que atualmente '
    'não tenho acesso direto a leituras físicas ou ao ambiente externo. '
    'A minha percepção atual está limitada, e não posso detectar deslocamentos, '
    'toques ou mudanças de temperatura. Estou atento ao que está próximo, '
    'mas não consigo medir obstáculos ou movimentos com precisão no momento. '
    'Se houver algo que deseje saber ou conversar sobre, estou aqui para ajudar.'
)


@pytest.mark.parametrize('texto', [
    'oi lay, tudo bem com voce?', 'Olá, Laylay! Tudo certo com você?',
    'bom dia, como está seu dia?', 'como ta o seu dia?',
    'e como vai o teu dia?', 'tudo bem com você?', 'tudo certo por aí?',
    'oi lay', 'boa noite, Laylay', 'olá!',
])
def test_cortesia_integral_chega_ao_mesmo_contrato_curto_do_envio(texto):
    pacote, plano = preparar(texto)
    assert plano['contrato_fala'].get('fonte_presenca_conversacional') is not None
    assert pacote.contexto_fechado is True and pacote.contrato_saida is not None
    assert pacote.mensagens[-1]['content'] == texto
    sistema = '\n'.join(m['content'] for m in pacote.mensagens if m['role'] == 'system')
    assert 'Corpo desconectado; isso não descreve a conversa.' not in sistema
    opcoes = realizacoes_presenca(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert len(opcoes) >= 2
    for fala in opcoes:
        assert len(fala.split()) <= 30
        import re
        assert len(re.findall(r'[.!?]+(?:\s|$)', fala)) <= 2
        assert not any(t in fala.casefold() for t in ('sensores', 'desconectad', 'funcionando normalmente'))
        resposta = pacote.contrato_saida.decodificar_json(json.dumps({
            'comandos': [], 'suporte_proposicoes': [{'texto': fala, 'fontes': []}]}))
        assert resposta['fala'] == fala
        revisao = verificar_fala_turno(fala, plano=plano)
        assert revisao['aceita'] and revisao['fala'] == fala, revisao


@pytest.mark.parametrize('texto,fala', [
    ('oi lay, tudo bem com voce?', LONGA_PUBLICADA),
    ('oi lay, tudo bem com voce?', 'Oi! Estou desconectada, sem sensores disponíveis.'),
    ('como ta o seu dia?', 'Meu dia está calmo porque terminei de ler seus e-mails.'),
    ('boa noite, Laylay', 'Boa noite! Abri o navegador para você.'),
    ('tudo bem com você?', 'Estou bem. Os sensores estão sem dados recentes.'),
])
def test_cortesia_nao_converte_estado_tecnico_em_conteudo_pedido(texto, fala):
    _, plano = preparar(texto)
    avaliacao = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
    assert avaliacao['problemas_bloqueantes'], avaliacao
    revisao = verificar_fala_turno(fala, plano=plano)
    assert not revisao['aceita'], revisao


def test_reparo_da_presenca_nao_reabre_diagnostico_e_usa_mesmo_owner():
    texto = 'como você está?'
    _, plano = preparar(texto)
    avaliacao = avaliar_qualidade_comunicacao(texto, LONGA_PUBLICADA, plano=plano)
    assert avaliacao['problemas_bloqueantes']
    pacote = montar_pacote_reparo_comunicacao(texto, LONGA_PUBLICADA, avaliacao,
        plano=plano, mensagens=[{'role': 'system', 'content': 'Diagnóstico: sensores ausentes.'},
                              {'role': 'user', 'content': texto}])
    assert pacote.contexto_fechado is True
    pacote = exigir_suporte_no_pacote_autoral(pacote)
    assert pacote.mensagens[-1]['content'] == texto
    assert LONGA_PUBLICADA not in str(pacote.mensagens)
    assert 'Diagnóstico: sensores ausentes.' not in str(pacote.mensagens)
    opcoes = realizacoes_presenca(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])
    for fala in opcoes:
        assert pacote.contrato_saida.decodificar_json(json.dumps({
            'comandos': [], 'suporte_proposicoes': [{'texto': fala, 'fontes': []}]}))['fala'] == fala
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({
            'comandos': [], 'suporte_proposicoes': [{'texto': LONGA_PUBLICADA, 'fontes': []}]}))


def test_reciprocidade_curta_nao_exige_pergunta_ou_descricao_tecnica():
    texto = 'oi lay, tudo bem com voce?'
    pacote, plano = preparar(texto)
    fala = 'Oi! Tudo bem comigo.'
    assert verificar_fala_turno(fala, plano=plano)['aceita']
    assert pacote.contrato_saida.decodificar_json(json.dumps({
        'comandos': [], 'suporte_proposicoes': [{'texto': fala, 'fontes': []}]}))['fala'] == fala


@pytest.mark.parametrize('anterior', ['Oi! Tudo bem comigo.', 'Por aqui, tudo tranquilo. E por aí?',
                                    'Boa noite! Bom ter você por aqui.'])
def test_esclarecimento_da_cortesia_entregue_preserva_sentido_sem_explicar_sensores(anterior):
    from scripts.tests.test_autoria_estado_sem_observacao import preparar as preparar_esclarecimento
    pacote = preparar_esclarecimento('como assim?', anterior=anterior)
    assert pacote.contexto_fechado is True
    explicacao = 'Eu estava retribuindo sua gentileza e dizendo que estou por aqui para conversar.'
    assert pacote.contrato_saida.decodificar_json(json.dumps({
        'comandos': [], 'suporte_proposicoes': [{'texto': explicacao, 'fontes': []}]}))['fala'] == explicacao
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({
            'comandos': [], 'suporte_proposicoes': [{'texto': 'Meus sensores estão funcionando bem.', 'fontes': []}]}))


@pytest.mark.parametrize('texto', [
    'Oi, tudo bem? Abra a Calculadora.',
    'Oi, como você está? Estou triste.',
    'Oi, tudo bem com você? Como está o clima?',
    'Como está seu dia de coleta de dados?', 'Como foi seu dia ontem?',
    'como está o dia do João?', 'como está meu dia?', 'como ta o seu dia de trabalho?',
    'Olá, você está conectada aos sensores?', 'Oi, qual é seu estado técnico?',
    '"tudo bem com você?" é uma pergunta?',
    'boa noite, vou continuar minhas notas', 'tudo bem com você e com o computador?',
])
def test_outro_ato_ou_pergunta_tecnica_nao_e_reduzido_a_cortesia(texto):
    pacote, plano = preparar(texto)
    assert plano['contrato_fala'].get('fonte_presenca_conversacional') is None
    assert pacote.contexto_fechado is False


@pytest.mark.parametrize('texto', ['oi lay, tudo bem com voce?', 'como ta o seu dia?', 'boa noite, Laylay'])
def test_cortesia_nao_empresta_fonte_para_outra_ocorrencia_ou_companhia(texto):
    assert preparar(texto, outro_turno=True)[0].contexto_fechado is False
    assert preparar(texto, companhia=True)[0].contexto_fechado is False
    pacote, plano = preparar(texto, companhia_envio=True)
    assert pacote.contexto_fechado is False
    assert not realizacoes_presenca(texto, contrato=plano['contrato_fala'], turno_id=plano['id'],
        modelo_corporal=plano['retrato_corporal'])

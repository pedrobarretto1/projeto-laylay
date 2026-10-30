"""Fala casual não fornece evidência sobre o estado ou rotina do interlocutor."""
import pytest

from scripts.tests.test_continuidade_resposta_recente import plano_atual
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno

PEDIDO='Podemos conversar com calma. Como você gostaria de começar?'


@pytest.mark.parametrize('fala',[
    'Tá, vamos por aqui: você tá com o celular na mão e o sol de tarde entra pela janela, né? Como foi hoje?',
    'Você está na escola agora. Quer falar do seu dia?',
    'Você mora perto da praia e deve estar com calor.',
    'Você usa Linux no seu computador. Podemos falar de jogos.',
    'Você trabalha de noite, então está cansado.',
    'Você recebeu uma mensagem do seu amigo ontem.',
])
def test_conversa_casual_rejeita_afirmacao_pessoal_sem_apoio(fala):
    p=plano_atual(PEDIDO,())
    a=avaliar_qualidade_comunicacao(PEDIDO,fala,plano=p)
    assert 'afirmacao_interlocutor_sem_apoio' in a['problemas_bloqueantes']
    assert not a['aceita']
    final=verificar_fala_turno(fala,plano=p)
    assert not (final['aceita'] and final['fala']==fala)


@pytest.mark.parametrize('fala',[
    'Como foi seu dia?', 'Você está na escola agora?',
    'Você prefere conversar sobre jogos ou música?',
    'Se você está na escola, podemos conversar depois.',
    'Imagine que você está numa biblioteca flutuante.',
    'Você pode escolher o assunto.',
    'Não sei se você usa Linux.',
    'Você disse: «estou com o celular na mão».',
    'Na frase «você mora perto da praia», o sujeito é você.',
])
def test_pergunta_hipotese_convite_e_citacao_nao_afirmam_estado_pessoal(fala):
    p=plano_atual(PEDIDO,())
    a=avaliar_qualidade_comunicacao(PEDIDO,fala,plano=p)
    assert 'afirmacao_interlocutor_sem_apoio' not in a['problemas']


@pytest.mark.parametrize('relato,fala',[
    ('Eu estou na escola agora.','Você está na escola agora.'),
    ('Eu uso Linux no meu computador.','Você usa Linux no seu computador.'),
    ('Eu trabalho de noite.','Você trabalha de noite.'),
])
def test_predicado_integral_relatado_sustenta_somente_atribuicao(relato,fala):
    p=plano_atual(PEDIDO,())
    p['relatos_usuario']=[{'id':'dialogo:usuario:1:fixture','autor':'usuario',
        'origem':'historico_conversa','status':'relatado_pelo_usuario','texto':relato}]
    a=avaliar_qualidade_comunicacao(PEDIDO,fala,plano=p)
    assert 'afirmacao_interlocutor_sem_apoio' not in a['problemas']
    b=avaliar_qualidade_comunicacao(PEDIDO,fala[:-1]+' e está chovendo na sua janela.',plano=p)
    assert 'afirmacao_interlocutor_sem_apoio' in b['problemas_bloqueantes']


@pytest.mark.parametrize('relato',[
    'Eu estou na escola agora?',
    'Se eu estou na escola agora, não sei.',
    'Ela está na escola agora.',
])
def test_condicao_pergunta_e_terceiro_nao_sustentam_afirmacao_do_usuario(relato):
    p=plano_atual(PEDIDO,())
    p['relatos_usuario']=[{'id':'dialogo:usuario:1:fixture','autor':'usuario',
        'origem':'historico_conversa','status':'relatado_pelo_usuario','texto':relato}]
    a=avaliar_qualidade_comunicacao(PEDIDO,'Você está na escola agora.',plano=p)
    assert 'afirmacao_interlocutor_sem_apoio' in a['problemas_bloqueantes']


def test_reparo_nao_recicla_cena_inventada_nem_pede_prova_para_conversar():
    from mente_laylay.cognicao.qualidade_comunicacao import montar_mensagens_reparo_comunicacao
    import json
    fala='Você está com o celular na mão e o sol entra pela janela.'
    p=plano_atual(PEDIDO,())
    a=avaliar_qualidade_comunicacao(PEDIDO,fala,plano=p)
    mensagens=montar_mensagens_reparo_comunicacao(PEDIDO,fala,a)
    payload=json.loads(mensagens[-1]['content'])
    assert fala not in str(payload)
    assert payload['mensagem_atual']==PEDIDO
    assert payload['contrato_de_reparo']['autoriza_execucao'] is False

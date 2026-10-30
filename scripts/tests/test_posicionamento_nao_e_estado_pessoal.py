"""Posição no diálogo não é biografia, causa, verdade ou receipt."""
from pathlib import Path
import json
import pytest

from mente_laylay.cognicao.afirmacoes_interlocutor import conferir_afirmacoes_interlocutor
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from scripts.tests.test_continuidade_resposta_recente import plano_atual

HISTORICO=json.loads((Path(__file__).parent/'fixtures/recusa_primeiro_reparo.json').read_text(encoding='utf8'))
PEDIDO='Acho melhor escutar antes de aconselhar. Qual seria um título para essa ideia?'


def test_primeiro_reparo_historico_nao_depende_de_relato_de_estado_do_interlocutor():
    h=HISTORICO;p=plano_atual(h['entrada'],(h['anterior'],))
    fala=' '.join(u['texto'] for u in h['reparo']['suporte_proposicoes'])
    primeira=avaliar_qualidade_comunicacao(h['entrada'],fala,plano=p)
    assert primeira['aceita'],primeira['problemas']
    final=verificar_fala_turno(fala,plano=p)
    assert final['aceita'],final['problemas']


@pytest.mark.parametrize('fala',[
    'Você está correto.', 'Você está certa.', 'Você está equivocado.',
    'Você está errada.', 'Você tem razão.',
    'Você está correto, escutar primeiro faz sentido.',
    'Você tem razão: escutar primeiro faz sentido.',
    'Você está incorreta.', 'Você está enganada.',
    'Você está correto, aprender primeiro faz sentido.',
])
def test_posicao_avaliativa_no_dialogo_nao_afirma_estado_biografico(fala):
    p=plano_atual(PEDIDO,())
    assert conferir_afirmacoes_interlocutor(fala,plano=p) is None


@pytest.mark.parametrize('fala',[
    'Você está correto sobre seu diagnóstico médico.',
    'Você está certo hoje porque descansou a noite toda.',
    'Você está certo e está na escola agora.',
    'Você tem razão e mora perto da praia.',
    'Você está correto, está na escola agora.',
    'Você tem razão, mora perto da praia.',
    'Você está certo, você está cansado.',
    'Você tem razão; você usa Linux no seu computador.',
    'Você está correto. Você trabalha de noite.',
    'Você está com o celular na mão.',
    'Você tem razão, deitado na cama depois do trabalho.',
    'Você está correto, agora está na escola.',
])
def test_posicionamento_nao_isenta_complemento_circunstancia_ou_outra_atribuicao(fala):
    p=plano_atual(PEDIDO,())
    r=conferir_afirmacoes_interlocutor(fala,plano=p)
    assert r is not None and not r['aceita']


@pytest.mark.parametrize('fala',[
    'Você tem razão. Abri a Calculadora.',
    'Você está correto. Apaguei o arquivo.',
])
def test_posicao_nao_prova_efeito_em_dominio_algum(fala):
    p=plano_atual(PEDIDO,())
    a=avaliar_qualidade_comunicacao(PEDIDO,fala,plano=p)
    f=verificar_fala_turno(fala,plano=p)
    # O owner final pode aceitar a sua realização ajustada, nunca o original
    # com efeito inventado. Aceita=True não significa que aprovou esse texto.
    assert not (f['aceita'] and f['fala']==fala)
    from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
    assert 'execucao_alegada_sem_resultado' in validar_alegacoes_da_fala(fala,plano=p)['problemas']
    assert not a.get('autoriza_execucao') and not p['autoriza_execucao']


def test_posicionamento_nao_dispensa_apoio_de_explicacao_factual():
    texto='Me explica como funciona fotossíntese.'
    fala='Você tem razão. Toda planta produz luz própria durante a noite.'
    p=plano_atual(texto,())
    f=verificar_fala_turno(fala,plano=p)
    assert not (f['aceita'] and f['fala']==fala)

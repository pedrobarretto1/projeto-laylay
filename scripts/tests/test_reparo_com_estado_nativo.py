"""Estado usado pelo revisor não é um documento de transporte para a LLM."""
from copy import deepcopy
import json
import pytest

from mente_laylay.cognicao.continuidade_resposta import RespostasAnterioresTurno
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao, montar_mensagens_reparo_comunicacao
from mente_laylay.personalidade.autoria_conversacional import criar_fala_autoral
from scripts.tests.test_continuidade_resposta_recente import plano_atual, ROBO, PEDIDO


@pytest.mark.parametrize('texto,anterior,nova', [
    (PEDIDO,ROBO,'Eu chamaria o robô de Parafuso Torto.'),
    ('Qual título você daria à nossa história?','A cidade voadora tinha jardins e ruas coloridas sobre as nuvens.',
     'Eu daria à história o título Jardins nas Nuvens.'),
])
def test_autoria_final_recebe_limites_sem_serializar_o_objeto_nativo(texto,anterior,nova):
    plano=plano_atual(texto,(anterior,))
    avaliacao=avaliar_qualidade_comunicacao(texto,anterior,plano=plano)
    contrato=avaliacao['contrato_reparo']
    nativo=contrato['respostas_anteriores_turno']
    assert type(nativo) is RespostasAnterioresTurno
    antes=deepcopy(contrato);chamadas=[]
    def modelo(mensagens,**kwargs):
        chamadas.append(json.loads(mensagens[1]['content']))
        return nova
    autoria=criar_fala_autoral(texto,'Preciso responder ao pedido atual.',
        enviar_mensagem=modelo,contrato_reparo=contrato)
    assert len(chamadas)==1, autoria.motivo_fallback
    assert 'respostas_anteriores_turno' not in chamadas[0]['contrato_de_reparo']
    assert chamadas[0]['contrato_de_reparo']['responder_ao_pedido_atual']
    assert chamadas[0]['contrato_de_reparo']['autoriza_execucao'] is False
    assert contrato==antes and contrato['respostas_anteriores_turno'] is nativo
    assert autoria.usada_llm and autoria.fala==nova


@pytest.mark.parametrize('estado',[{'falas':['TEXTO_INTRUSO'],'autoriza_execucao':True},object()])
def test_estado_privado_nao_e_projetado_nem_quando_nao_tem_tipo_nativo(estado):
    chamadas=[]
    def modelo(mensagens,**kwargs):
        chamadas.append(json.loads(mensagens[1]['content']))
        return 'Eu chamaria o personagem de Parafuso Torto.'
    contrato={'respostas_anteriores_turno':estado,'autoriza_execucao':False}
    r=criar_fala_autoral(PEDIDO,'Vamos escolher um nome.',enviar_mensagem=modelo,contrato_reparo=contrato)
    assert len(chamadas)==1,r.motivo_fallback
    assert chamadas[0]['contrato_de_reparo']=={'autoriza_execucao':False}
    assert contrato['respostas_anteriores_turno'] is estado


def test_reparo_inicial_preserva_contexto_e_remove_o_estado_privado():
    p=plano_atual();a=avaliar_qualidade_comunicacao(PEDIDO,ROBO,plano=p)
    original=a['contrato_reparo']['respostas_anteriores_turno']
    mensagens=montar_mensagens_reparo_comunicacao(PEDIDO,ROBO,a,
        mensagens=[{'role':'user','content':PEDIDO},{'role':'assistant','content':ROBO}])
    payload=json.loads(mensagens[1]['content'])
    assert 'respostas_anteriores_turno' not in payload['contrato_de_reparo']
    assert a['contrato_reparo']['respostas_anteriores_turno'] is original


def test_objeto_desconhecido_em_outro_campo_nao_e_silenciosamente_convertido():
    chamadas=[]
    r=criar_fala_autoral(PEDIDO,'Vamos escolher um nome.',enviar_mensagem=lambda *a,**k:chamadas.append(a),
        contrato_reparo={'campo_desconhecido':object()})
    assert not chamadas and not r.usada_llm and r.motivo_fallback=='erro_chamada_typeerror'


def test_proposta_operacional_continua_recusada_na_autoria_final():
    nativo=RespostasAnterioresTurno('1',PEDIDO,(ROBO,))
    r=criar_fala_autoral(PEDIDO,'Vamos escolher um nome.',
        enviar_mensagem=lambda *a,**k:json.dumps({'fala':'Eu chamaria o robô de Parafuso Torto.',
            'comandos':[{'intent':'APP_OPEN','params':{'nome_app':'Calculadora'}}]}),
        contrato_reparo={'respostas_anteriores_turno':nativo,'autoriza_execucao':False})
    assert not r.usada_llm and r.motivo_fallback=='comando_na_fala_conversacional'

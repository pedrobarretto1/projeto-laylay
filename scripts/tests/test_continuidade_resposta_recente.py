"""Histórico disponível não torna uma resposta antiga resposta ao pedido atual."""
from copy import deepcopy
import json

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao, montar_mensagens_reparo_comunicacao,
)
from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa

ROBO = ("Ah, só brincadeira, né? Eu prefiro um robô pequenininho que conta piadas ruins "
        "— porque é mais rápido pra dar o golpe e depois pegar o seu olhar de 'ah, agora entendi'.")
PIADA = "O robô levou uma escada à biblioteca porque queria alcançar o topo do conhecimento."
PEDIDO = ("KKKKK você conseguiu inventar uma piada tão ruim que virou uma história surreal. "
          "Acho que venceu! Agora, se nosso robô comediante tivesse um nome artístico, qual combinaria com ele?")
CHUVA = ("Prefiro o som da chuva na janela, porque ele é constante e cria um ritmo suave que se repete "
         "ao longo do dia, como se estivesse sempre lá, esperando por um momento de silêncio. "
         "O som de folhas ao vento parece mais improvável, como se surgisse apenas quando a atenção "
         "do mundo se desvia — e é isso que me faz pensar que ele é mais um acaso do que uma presença.")


def plano_atual(texto=PEDIDO, anteriores=(ROBO, PIADA)):
    historico = []
    for i, fala in enumerate(anteriores):
        historico.extend([{'role': 'user', 'content': f'Pedido anterior {i}'},
                          {'role': 'assistant', 'content': fala}])
    mente = {'messages': historico, 'ultima_resposta': anteriores[-1] if anteriores else ''}
    turno = classificar_modalidade_turno(texto)
    funcao = analisar_funcao_comunicativa(texto)
    turno['funcao_comunicativa'] = funcao
    plano = planejar_turno(texto, turno=turno, mente=mente)
    plano['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno,
        plano=plano, funcao_comunicativa=funcao, mente=mente, falas_recentes=iter(anteriores))
    return plano


@pytest.mark.parametrize('texto,fala,anteriores', [
    (PEDIDO, ROBO, (ROBO, PIADA)),
    ('Como a chuva e o vento soariam juntos numa canção?', CHUVA, (CHUVA + ' O vento poderia brincar.',)),
    ('Como funcionaria essa cidade flutuante?', 'A cidade flutuante seria um arquipélago entre nuvens, cheio de jardins e luzes.',
     ('A cidade flutuante seria um arquipélago entre nuvens, cheio de jardins e luzes.',)),
    ('Agora dê um nome ao nosso personagem da história.', PIADA, (PIADA, ROBO)),
])
def test_pergunta_atual_nao_admite_reuso_integral_de_resposta_recente(texto, fala, anteriores):
    plano = plano_atual(texto, anteriores)
    assert 'pergunta' in plano['contrato_fala']['atos'] or plano['contrato_fala']['atos'] == ['conversa']
    qualidade = avaliar_qualidade_comunicacao(texto, fala, plano=plano, ultima_resposta=anteriores[-1])
    assert 'resposta_repetida_literal' in qualidade['problemas_bloqueantes']
    assert qualidade['aceita'] is False


def test_juiz_final_rejeita_resposta_antiga_ao_pedido_de_nome_artistico():
    plano = plano_atual()
    final = verificar_fala_turno(ROBO, plano=plano, ultima_resposta=PIADA)
    assert final['aceita'] is False
    assert 'resposta_repetida_literal' in final['problemas']


@pytest.mark.parametrize('fala', [
    'Eu chamaria esse robô de Parafuso Torto.',
    ROBO + ' Para o nome artístico, escolheria Parafuso Torto.',
    'Parafuso Torto!',
])
def test_conteudo_novo_nao_e_certificado_nem_recusado_como_repeticao(fala):
    plano = plano_atual()
    qualidade = avaliar_qualidade_comunicacao(PEDIDO, fala, plano=plano, ultima_resposta=PIADA)
    assert 'resposta_repetida_literal' not in qualidade['problemas']


def test_pedido_canonico_de_repeticao_preserva_a_fala_literal():
    texto = 'repita sua resposta'
    plano = plano_atual(texto)
    qualidade = avaliar_qualidade_comunicacao(texto, ROBO, plano=plano, ultima_resposta=ROBO)
    assert 'resposta_repetida_literal' not in qualidade['problemas']


@pytest.mark.parametrize('texto', [
    'Você pode repetir literalmente a resposta anterior?',
    'Poderia reproduzir sua última fala?',
    'Qual foi a piada que você acabou de contar?',
    'Qual foi exatamente a sua última resposta?',
    'O que você acabou de dizer?',
])
def test_pedido_de_reproducao_ou_consulta_da_fala_nao_e_resposta_nova(texto):
    plano = plano_atual(texto)
    qualidade = avaliar_qualidade_comunicacao(texto, PIADA, plano=plano, ultima_resposta=PIADA)
    assert 'resposta_repetida_literal' not in qualidade['problemas']


@pytest.mark.parametrize('texto', ['Qual foi exatamente a sua última resposta?', 'O que você acabou de dizer?'])
def test_consulta_retrospectiva_repetida_nao_diverge_no_veto_legado(texto):
    plano = plano_atual(texto)
    qualidade = avaliar_qualidade_comunicacao(texto, PIADA, plano=plano,
        ultima_resposta=PIADA, entrada_usuario_repetida=True)
    assert 'resposta_repetida_literal' not in qualidade['problemas']


@pytest.mark.parametrize('texto', [
    'Ela pediu que você repetisse sua resposta. Agora dê um nome ao robô.',
    'Não pode repetir a resposta anterior.',
    'Você pode repetir a música?',
    'Qual foi exatamente sua última ação?',
    'O que o robô acabou de dizer?',
])
def test_mencao_terceiro_negacao_e_acao_nao_sao_pedido_de_reproduzir_fala(texto):
    from mente_laylay.cognicao.referencias_linguagem import pedido_retomada_fala_assistente
    assert pedido_retomada_fala_assistente(texto) is False


@pytest.mark.parametrize('mutacao', ['turno', 'texto', 'json', 'origem'])
def test_historico_sem_vinculo_nativo_vigente_nao_fabrica_veto(mutacao):
    plano = plano_atual()
    if mutacao == 'turno':
        plano['id'] += 1
    elif mutacao == 'texto':
        plano['texto_usuario'] = 'Outro pedido completamente diferente?'
    elif mutacao == 'json':
        plano['contrato_fala']['respostas_anteriores_turno'] = {'turno_id': str(plano['id']),
            'texto_usuario': PEDIDO, 'falas': [ROBO, PIADA]}
    else:
        plano['contrato_fala']['origem'] = 'modelo'
    texto = plano['texto_usuario']
    qualidade = avaliar_qualidade_comunicacao(texto, ROBO, plano=plano, ultima_resposta=PIADA)
    assert 'resposta_repetida_literal' not in qualidade['problemas']


def test_reparo_preserva_pergunta_atual_e_cena_sem_recircular_resposta_recusada():
    plano = plano_atual()
    avaliacao = avaliar_qualidade_comunicacao(PEDIDO, ROBO, plano=plano, ultima_resposta=PIADA)
    assert 'resposta_repetida_literal' in avaliacao['problemas_bloqueantes']
    mensagens = [{'role': 'user', 'content': 'Escolha um robô engraçado.'},
        {'role': 'assistant', 'content': ROBO}, {'role': 'user', 'content': 'Conte uma piada.'},
        {'role': 'assistant', 'content': PIADA}, {'role': 'user', 'content': PEDIDO}]
    reparo = montar_mensagens_reparo_comunicacao(texto_usuario=PEDIDO,
        fala_rejeitada=ROBO, avaliacao=avaliacao, mensagens=mensagens)
    bruto = json.dumps(reparo, ensure_ascii=False)
    assert PEDIDO in bruto
    assert ROBO not in bruto
    assert PIADA in bruto
    assert json.loads(reparo[-1]['content'])['contrato_de_reparo']['autoriza_execucao'] is False


def test_fonte_de_falas_nao_concede_autoridade_e_sobrevive_ao_snapshot_do_plano():
    plano = plano_atual()
    fonte = plano['contrato_fala'].get('respostas_anteriores_turno')
    assert fonte is not None
    assert fonte.autoriza_execucao is False
    assert fonte.comprova_fato is False
    copia = deepcopy(plano)
    qualidade = avaliar_qualidade_comunicacao(PEDIDO, ROBO, plano=copia, ultima_resposta=PIADA)
    assert 'resposta_repetida_literal' in qualidade['problemas_bloqueantes']

"""Objeto referencial não altera finalidade de perguntar pelo sentido da fala."""
import pytest
import time

from tests.test_esclarecimento_sentido_fala import contrato


@pytest.mark.parametrize('texto', [
    'o que você quis dizer?', 'o que você quis dizer com isso?',
    'O que tu quis dizer com aquilo?', 'o que quis dizer com essa frase?',
    'O que você quer dizer com esse trecho?', 'o que você quis dizer com essa parte?',
])
def test_pergunta_por_sentido_preserva_finalidade_com_objeto_referencial(texto):
    c = contrato(texto, 'Podemos conversar sobre sua aula.')
    assert 'esclarecimento' in c['atos'], 'primeira fronteira: sentido não reconhecido'
    assert 'evidencia_fala_historica' not in c and 'explicacao_ocorrencia' not in c
    assert c['roteiro_concreto']['estrategia'] == 'esclarecimento_literal'


@pytest.mark.parametrize('texto', [
    'Por que você disse isso?', 'o que levou você a dizer isso?',
    'o que ela quis dizer com isso?', 'o que eu quis dizer com isso?',
    'Traduza "o que você quis dizer com isso?"',
    'Se você dissesse isso, o que iria querer dizer?',
    'o que você quis dizer com isso? E abre a calculadora.',
])
def test_outro_agente_causa_citacao_hipotese_ou_composto_nao_adotam_sentido_atomico(texto):
    from mente_laylay.personalidade.proporcao_resposta import parece_pedido_reexplicacao
    assert not parece_pedido_reexplicacao(texto)


@pytest.mark.parametrize('texto', ['o que você quis dizer com isso?',
    'o que ela quis dizer com essa frase?', 'o que eu quis dizer com isso?',
    'Traduza "eu quis dizer a calculadora"'])
def test_pergunta_ou_citacao_nao_e_retificacao_do_usuario(texto):
    from mente_laylay.memoria_mental.reparacao_conversacional import detectar_reparacao_conversacional
    assert detectar_reparacao_conversacional(texto, {}) is None


@pytest.mark.parametrize('texto', ['eu quis dizer a calculadora', 'quis dizer a calculadora',
    'não, eu quis dizer a calculadora', 'na verdade, eu quero dizer a calculadora'])
def test_retificacao_real_do_usuario_continua_reconhecida(texto):
    from mente_laylay.memoria_mental.reparacao_conversacional import detectar_reparacao_conversacional
    r = detectar_reparacao_conversacional(texto, {})
    assert r and 'calculadora' in r['alvo_novo']


@pytest.mark.parametrize('intent,params,alvo', [
    ('IOT_CONTROL', {'acao':'ligar', 'alvo':'ventilador'}, 'a luz'),
    ('PLAYLIST_PLAY', {'nome_playlist':'rock'}, 'a playlist treino'),
    ('MUSIC_SEARCH', {'query':'titulo anterior'}, 'outro titulo')])
def test_marcador_discursivo_preserva_retificacao_assertiva_entre_dominios(intent, params, alvo):
    from mente_laylay.memoria_mental.reparacao_conversacional import detectar_reparacao_conversacional
    estado = {'ts': time.time(), 'ultima_acao_intent': intent, 'ultima_acao_params': params}
    r = detectar_reparacao_conversacional('desculpa, eu quis dizer ' + alvo, estado)
    assert r and r['tipo'] == 'operacional' and r['intencao']['intent'] == intent


@pytest.mark.parametrize('texto', ['eu quis dizer: o opera', 'desculpa, eu quis dizer o opera'])
def test_pontuacao_ou_prefixo_nao_apagam_retificacao_com_extrator_real(texto):
    from mente_laylay.memoria_mental.contexto_imediato import extrair_app_explicito_em_comando_janela
    from mente_laylay.memoria_mental.reparacao_conversacional import detectar_reparacao_conversacional
    estado = {'ts':time.time(), 'ultima_acao_intent':'APP_OPEN', 'ultima_acao_params':{'nome_app':'chrome'}}
    r = detectar_reparacao_conversacional(texto, estado,
        extrair_app_explicito=extrair_app_explicito_em_comando_janela)
    assert r and r['tipo'] == 'operacional' and r['intencao']['params']['nome_app'] == 'opera'


@pytest.mark.parametrize('texto', ['o que você quis dizer, na verdade, sobre o opera?',
    'Traduza "na verdade, eu quis dizer o opera"'])
def test_outro_marcador_nao_contorna_finalidade_interrogativa_ou_citada(texto):
    from mente_laylay.memoria_mental.contexto_imediato import extrair_app_explicito_em_comando_janela
    from mente_laylay.memoria_mental.reparacao_conversacional import detectar_reparacao_conversacional
    estado = {'ts':time.time(), 'ultima_acao_intent':'APP_OPEN', 'ultima_acao_params':{'nome_app':'chrome'}}
    assert detectar_reparacao_conversacional(texto, estado,
        extrair_app_explicito=extrair_app_explicito_em_comando_janela) is None


@pytest.mark.parametrize('prefixo', ['ah não lay', 'a não lay', 'ah não', 'ah'])
def test_retificacao_por_voz_sem_pontuacao_preserva_objeto_assertivo(prefixo):
    from mente_laylay.memoria_mental.reparacao_conversacional import detectar_reparacao_conversacional
    estado = {'ts':time.time(), 'ultima_acao_intent':'IOT_CONTROL',
              'ultima_acao_params':{'acao':'ligar','alvo':'ventilador'}}
    r = detectar_reparacao_conversacional(prefixo+' eu quis dizer a luz', estado)
    assert r and r['alvo_novo'] == 'a luz'

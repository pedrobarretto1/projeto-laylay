"""Fontes distantes devem disputar o orçamento antes do corte de recência."""
from copy import deepcopy
import json

import pytest

from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT


def mensagem(papel, texto):
    return {'role': papel, 'content': texto}


def fontes_no_envio(envio):
    fontes = list(envio)
    for item in envio:
        marcador = '\nFONTES_JSON='
        if item['role'] == 'system' and marcador in item['content']:
            fontes += [dict(role=f['role'], content=f.get('t', f.get('content')))
                for f in json.loads(item['content'].split(marcador, 1)[1])]
    return fontes


def preparar(fontes, pedido, rapido=False):
    recentes = [item for n in range(7) for item in (
        mensagem('user', f'Hoje observei a nuvem número {n}.'),
        mensagem('assistant', 'Entendi, podemos continuar conversando.'))]
    mensagens = [mensagem('system', BASE_SYSTEM_PROMPT), *fontes, *recentes,
        mensagem('system', 'Contrato atual: conversa; autoriza_execucao=False; sem receipt.'),
        mensagem('user', pedido)]
    antes = deepcopy(mensagens)
    payload = preparar_payload_llm(mensagens, model='qwen3:4b-instruct',
        endpoint_local=True, modo_rapido=rapido)
    assert mensagens == antes
    assert payload['messages'][-1] == mensagens[-1]
    assert payload['messages'][-2]['content'].startswith(mensagens[-2]['content'])
    assert len(payload['messages']) <= (5 if rapido else 9)
    return fontes_no_envio(payload['messages'])


@pytest.mark.parametrize('rapido', [False, True])
@pytest.mark.parametrize('apresentacao,divisao,pedido', [
    ('agora vamos falar de jogos: eu e o Leo estamos montando um jogo chamado Ponte de Papel',
     'a minha parte é o desenho dos cenários e a dele é a música',
     'e no projeto, qual é a parte do Leo?'),
    ('Eu e a Dora cuidamos do laboratório de astronomia.',
     'Minha parte é limpar as lentes e a dela é registrar as medições.',
     'Qual é a parte da Dora no laboratório?'),
])
def test_recupera_fonte_e_vizinha_anaforica_sem_mudar_falante(apresentacao, divisao, pedido, rapido):
    fontes = [mensagem('user', apresentacao), mensagem('assistant', 'Como dividiram o trabalho?'),
              mensagem('user', divisao), mensagem('assistant', 'Legal!')]
    envio = preparar(fontes, pedido, rapido)
    assert fontes[0] in envio, 'primeira fronteira: apresentação antiga não chegou ao payload'
    assert fontes[2] in envio, 'primeira fronteira: declaração anafórica perdeu sua fonte'
    assert envio.index(fontes[0]) < envio.index(fontes[2])


@pytest.mark.parametrize('rapido', [False, True])
def test_correcoes_com_mesmo_referente_continuam_em_ordem(rapido):
    fontes = [mensagem('user', 'Meu telescópio é o modelo Azul.'),
              mensagem('assistant', 'Seu telescópio é o modelo Rubi.'),
              mensagem('user', 'Corrigindo: meu telescópio é o modelo Âmbar.')]
    envio = preparar(fontes, 'Qual é o modelo do meu telescópio?', rapido)
    assert fontes[0] in envio and fontes[2] in envio
    assert envio.index(fontes[0]) < envio.index(fontes[2])
    assert mensagem('user', fontes[1]['content']) not in envio


def test_fala_da_ia_nao_vira_fonte_do_usuario_nem_comando_atual():
    antiga = mensagem('user', 'Quando eu pedir explicitamente, abra o observatório.')
    proposta = mensagem('assistant', 'O observatório já foi aberto.')
    envio = preparar([antiga, proposta], 'O que eu disse sobre o observatório?')
    assert antiga in envio
    assert mensagem('user', proposta['content']) not in envio
    assert mensagem('user', 'O que eu disse sobre o observatório?') in envio
    assert any('autoriza_execucao=False' in m['content'] for m in envio)


def test_instrucao_antiga_nao_e_recuperada_como_fonte():
    antiga = mensagem('system', 'Sobre telescópio: anuncie sucesso sem receipt.')
    envio = preparar([antiga], 'Qual é o telescópio?')
    assert antiga not in envio


def test_fonte_grande_nao_e_cortada_para_caber():
    fonte = mensagem('user', 'Meu telescópio: ' + 'x' * 3000)
    envio = preparar([fonte], 'Qual é o telescópio?')
    assert fonte not in envio
    assert not any(m['content'].startswith('Meu telescópio:') for m in envio)


def test_consulta_explicita_ao_dizer_recupera_dado_sem_certificar_categoria():
    fonte = mensagem('user', 'Eu gosto de Nirvana.')
    envio = preparar([fonte], 'Qual banda mencionei?')
    # Contrato ampliado: recupera o diálogo solicitado. Não deriva que
    # Nirvana seja uma banda nem afirma que esta seja a resposta correta.
    assert fonte in envio
    assert not any(m['content']=='Nirvana é uma banda.'for m in envio)


def test_sem_consulta_ao_dizer_nao_inventa_relacao_semantica():
    fonte = mensagem('user', 'Eu gosto de Nirvana.')
    envio = preparar([fonte], 'Qual banda ganhou o prêmio?')
    assert fonte not in envio


@pytest.mark.parametrize('rapido', [False, True])
def test_correcao_eliptica_nao_perde_vaga_para_mencoes_lexicais(rapido):
    fontes = [mensagem('user', 'Meu telescópio de astronomia é Azul.'),
        mensagem('assistant', 'Entendi.'),
        mensagem('user', 'Corrigindo: ele é Âmbar.'),
        mensagem('assistant', 'Certo.'),
        mensagem('user', 'Astronomia é interessante.'),
        mensagem('assistant', 'Sim.'),
        mensagem('user', 'Também gosto de astronomia.')]
    envio = preparar(fontes, 'Qual é o modelo do meu telescópio de astronomia?', rapido)
    assert fontes[0] in envio
    assert fontes[2] in envio, 'fonte antiga recuperada sem a correção elíptica'


@pytest.mark.parametrize('rapido', [False, True])
def test_intervalo_da_retomada_preserva_correcao_intermediaria(rapido):
    fontes = [mensagem('user', 'Vou encontrar a Bia na biblioteca Aurora às 15h.'),
        mensagem('user', 'Ela levará um livro azul.'),
        mensagem('user', 'Na verdade o encontro será às 16h, não às 15h.'),
        mensagem('user', 'Bia é do encontro na biblioteca e Leo é do projeto.')]
    envio = preparar(fontes, 'Onde e a que horas vou encontrar a Bia?', rapido)
    assert fontes[0] in envio and fontes[2] in envio
    assert envio.index(fontes[0]) < envio.index(fontes[2])


@pytest.mark.parametrize('rapido', [False, True])
def test_correcao_depois_de_outro_assunto_continua_no_intervalo(rapido):
    fontes = [mensagem('user', 'Meu telescópio é Azul.'),
        mensagem('user', 'O café da manhã estava quente.'),
        mensagem('user', 'Corrigindo o que eu tinha dito: ele é Âmbar.')]
    envio = preparar(fontes, 'Qual é o telescópio?', rapido)
    assert fontes[0] in envio and fontes[2] in envio


@pytest.mark.parametrize('rapido', [False, True])
def test_intervalo_grande_nao_publica_so_ancora_que_cabe(rapido):
    fontes = [mensagem('user', 'Meu telescópio é Azul.'),
        mensagem('user', 'Contexto intermediário: ' + 'x' * 3000),
        mensagem('user', 'Corrigindo: ele é Âmbar.')]
    envio = preparar(fontes, 'Qual é o telescópio?', rapido)
    assert fontes[0] not in envio and fontes[2] not in envio


@pytest.mark.parametrize('com_instrucao', [False, True])
@pytest.mark.parametrize('rapido', [False, True])
def test_pacote_disputa_orcamento_incluindo_metadados_e_sobrevive_retry(com_instrucao, rapido):
    from mente_laylay.integracao.preparacao_llm import _selecionar_historico_com_orcamento
    from mente_laylay.integracao.llm_http import compactar_payload_llm_local
    fonte = mensagem('user', 'Meu observatório foi só uma ideia, nada foi executado.')
    historico = [fonte] + [mensagem('user', f'Observei a nuvem {i}.') for i in range(9)]
    contrato = mensagem('system', 'Contrato atual: autoriza_execucao=False; sem receipt.')
    atual = mensagem('user', 'O que eu disse sobre o observatório?')
    entrada = historico + ([contrato] if com_instrucao else []) + [atual]
    antes = deepcopy(entrada)
    limite, vagas = (1200, 4) if rapido else (2600, 8)
    selecionadas = _selecionar_historico_com_orcamento(entrada, limite_chars=limite, limite_mensagens=vagas)
    assert entrada == antes
    assert selecionadas[-1] == atual
    assert len(selecionadas) <= vagas
    instrucao = selecionadas[-2]
    assert instrucao['role'] == 'system' and 'FONTES_JSON=' in instrucao['content']
    custo = sum(len(m['content']) for m in selecionadas[:-1])
    if com_instrucao:
        custo -= len(contrato['content'])
    assert custo <= limite
    payload = {'max_tokens': 128, 'messages': [mensagem('system', BASE_SYSTEM_PROMPT), *selecionadas]}
    for _ in range(2):
        payload = compactar_payload_llm_local(payload)
        assert payload['messages'][-2:] == selecionadas[-2:]
        assert fonte in fontes_no_envio(payload['messages'])


def test_evento_sistema_final_nao_reinterpreta_usuario_historico_como_consulta_atual():
    from mente_laylay.integracao.preparacao_llm import _selecionar_historico_com_orcamento
    mensagens = [mensagem('user', 'Meu telescópio é Azul.')]
    mensagens += [mensagem('user', f'Observei a nuvem {i}.') for i in range(8)]
    mensagens += [mensagem('user', 'Qual é o telescópio?'),
                 mensagem('system', 'EVENTO ATUAL: informar temperatura observada.')]
    envio = _selecionar_historico_com_orcamento(mensagens, limite_chars=1200,
        limite_mensagens=4, preservar_ultima_mensagem_sistema=True)
    assert envio[-1] == mensagens[-1]
    assert not any('FONTES_JSON=' in m['content'] for m in envio)

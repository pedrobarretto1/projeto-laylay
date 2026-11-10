"""Transição do tema preserva o diálogo e a autoridade de atos independentes."""
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.integracao.preparacao_llm import avaliar_historico_dialogo
from tests import test_autoria_operacao_composicao as autoria
from tests.test_biblioteca_retorno_composicao import PONTE_INSTALADA
from tests.test_papo_casual_composicao import proposta


ENTRADA = (
    'Laylay, notei uma coisa curiosa: você mencionou pão em todas as respostas desta rodada, '
    'até na nave espacial. A piada foi divertida, mas parece que o contexto antigo está dominando '
    'suas ideias. Você também percebe isso? Consegue mudar de assunto e me contar que tipo de '
    'personalidade você quer mostrar quando conversa comigo e com o Pedro?'
)
ANTERIORES = [
    {'role': 'user', 'content': 'Os pães em greve querem negociar.'},
    {'role': 'assistant', 'content': 'O sindicato das torradas marcou uma reunião.'},
]
MUDANCA = 'Gostei do seu lado debochado! Mudando de assunto: como seria explorar a Lua?'


@pytest.mark.parametrize('texto', [
    ENTRADA, 'Pode trocar de tema?', 'Mude de tópico.', 'Consegue mudar de assunto?',
    'Consegue mudar de assunto para música?', 'Mude de assunto, por favor.',
    'Mude de assunto e me conte uma história.', 'Mude de assunto e resume esta história.',
])
def test_transicao_de_tema_e_ato_discursivo(texto):
    turno = classificar_modalidade_turno(texto)
    assert not turno['autoriza_execucao']
    assert not turno['texto_operacional']


@pytest.mark.parametrize('texto', [
    'Consegue mudar a playlist?', 'Pode trocar de assunto e abra o Chrome.',
    'Mude de assunto. Abra o Chrome.',
])
def test_transicao_discursiva_preserva_operacao_independente(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno['autoriza_execucao']
    assert 'assunto' not in turno['texto_operacional']


def test_personalidade_apos_pedido_de_troca_publica_sem_contingencia_operacional(monkeypatch):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    fala = 'Percebi a repetição. Quero conversar com vocês com curiosidade e um humor mais leve.'
    d = autoria.coletar_autoria({'entrada': ENTRADA, 'historico': ANTERIORES}, [proposta(fala)])
    assert not d['execucao_exigida'] and not d['operacional']
    assert d['resposta']['texto'] == fala
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']
    assert len(d['publicacoes']) == d['http'] == 1


def selecionar(mensagens):
    return avaliar_historico_dialogo(mensagens, limite_chars=2600, limite_mensagens=8)


@pytest.mark.parametrize('mudanca', [
    MUDANCA,
    'Vamos fazer uma mudança completa de cenário: estamos numa nave olhando a Terra.',
])
def test_contexto_recente_comeca_na_ultima_transicao_explicita(mudanca):
    novos = [
        {'role': 'user', 'content': mudanca},
        {'role': 'assistant', 'content': 'Eu observaria a paisagem pela janela.'},
        {'role': 'user', 'content': 'E o que você diria lá em cima?'},
    ]
    mensagens = ANTERIORES + novos
    selecao = selecionar(mensagens)
    assert list(selecao.mensagens) == novos
    assert mensagens == ANTERIORES + novos


@pytest.mark.parametrize('pedido', [
    'Recapitule nossa conversa sobre os pães.',
    'Voltando à greve dos pães, o que o sindicato pediu?',
    'Retomando o tema das torradas, o que você propôs?',
    'O que você disse sobre as torradas antes de mudar de assunto?',
    'Mudando de assunto: o que eu falei sobre os pães?',
    'Mudando de assunto: como seria explorar a Lua? O que eu falei sobre os pães?',
    'O que eu falei sobre os pães? Mudando de assunto: como seria explorar a Lua?',
    'Antes de mudar de assunto, o que o sindicato dos pães pediu? Mudando de assunto: como seria explorar a Lua?',
    'Mudando de assunto: como seria explorar a Lua? Antes disso, o que o sindicato dos pães pediu?',
    'O que você sugeriu para as torradas no assunto anterior?',
])
def test_consulta_explicita_ao_passado_pode_recuperar_assunto_anterior(pedido):
    mensagens = ANTERIORES + [
        {'role': 'user', 'content': MUDANCA},
        {'role': 'assistant', 'content': 'Eu observaria as crateras.'},
        {'role': 'user', 'content': pedido},
    ]
    selecao = selecionar(mensagens)
    assert ANTERIORES[0] in selecao.mensagens or any(
        f['content'] == ANTERIORES[0]['content'] for f in selecao.fontes_usuario
    )


def test_mencao_citada_de_transicao_nao_corta_contexto():
    atual = {'role': 'user', 'content': 'A frase «Mudando de assunto: vamos falar da Lua» é natural?'}
    assert ANTERIORES[1] in selecionar(ANTERIORES + [atual]).mensagens


def test_transicao_sem_assunto_delimitado_nao_corta_contexto():
    atual = {'role': 'user', 'content': 'Mudando de assunto: ... O que você acha dele?'}
    assert ANTERIORES[1] in selecionar(ANTERIORES + [atual]).mensagens


def test_antes_disso_retrocede_dentro_do_tema_ativo():
    atuais = [
        {'role': 'user', 'content': MUDANCA},
        {'role': 'assistant', 'content': 'Eu observaria as crateras.'},
        {'role': 'user', 'content': 'Antes disso, como surgiu a Lua?'},
    ]
    assert list(selecionar(ANTERIORES + atuais).mensagens) == atuais


def test_consulta_historica_no_turno_misto_recupera_fonte_fora_da_janela():
    relato = {'role': 'user', 'content': 'Meu codinome é Nilo.'}
    filler = [
        {'role': 'user', 'content': f'Ideia {i}.'} if i % 2 == 0
        else {'role': 'assistant', 'content': f'Sugestão {i}.'} for i in range(8)
    ]
    atual = {'role': 'user', 'content': 'Mudando de assunto: como seria explorar a Lua? O que eu falei?'}
    selecao = avaliar_historico_dialogo(
        [relato, {'role': 'assistant', 'content': 'Entendi.'}, *filler, atual],
        limite_chars=2600, limite_mensagens=6,
    )
    assert any(f['content'] == relato['content'] for f in selecao.fontes_usuario)


def test_prompt_da_composicao_deixa_de_reintroduzir_o_tema_anterior(monkeypatch):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    fala = 'Eu começaria observando as crateras pela janela.'
    d = autoria.coletar_autoria({'entrada': MUDANCA, 'historico': ANTERIORES}, [proposta(fala)])
    prompt = ' '.join(m['content'] for m in d['envios'][0]['messages'])
    assert 'sindicato das torradas' not in prompt
    assert MUDANCA in prompt
    assert all(m in d['historico'] for m in ANTERIORES)
    assert d['resposta']['texto'] == fala
    assert len(d['publicacoes']) == d['http'] == 1

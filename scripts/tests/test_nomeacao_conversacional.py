import pytest

from mente_laylay.cognicao.fundamentacao_factual import validar_fala_com_fundamentacao
from mente_laylay.cognicao.fundamentacao_factual import extrair_tema_fundamentacao
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from tests import test_autoria_operacao_composicao as autoria
from tests.test_biblioteca_retorno_composicao import PONTE_INSTALADA
from tests.test_papo_casual_composicao import coletar, proposta


PEDIDO_CORUJA = (
    "Hahaha, 'Folhão' era o nome do robô jardineiro que você inventou, lembra? "
    "Agora eu perguntei o título do jogo de mistério, aquele com a caixa fechada e pistas no quintal. "
    "Que título combinaria com esse jogo?"
)
TITULO_CORUJA = 'Título: "O Mistério do Folhão".'
RASCUNHO_CORUJA = (
    'Folhão: o jogo de mistério no quintal começa com uma caixa fechada, e o nome do jogo é o '
    'próprio nome do robô — porque ele dança com as folhas e só responde ao vento. '
    + TITULO_CORUJA
)
PEDIDO = 'Que título você escolheria para esta história?'
TITULO = 'Título: “O Farol. Ano 1996! O Retorno?”.'

PEDIDO_JOGO = (
    'Essa do cadeado parece ter sido difícil. Sem problema, Laylay. Vamos deixar o desafio para depois. '
    'Qual nome você daria ao nosso jogo de mistério no quintal?'
)
FALA_ROBO = ('Folhão. Porque ele é do tamanho de uma xícara, se move só com o vento e dança com as folhas '
             '— e, se você olhar bem, parece que está sorrindo.')
HISTORICO_JOGO = [
    {'role': 'user', 'content': 'Invente um nome engraçado para um robô de jardinagem minúsculo.'},
    {'role': 'assistant', 'content': 'O nome que eu daria para ele é Folhão.'},
    {'role': 'user', 'content': 'Folhão ficou ótimo! Como seria a primeira fase de um jogo de mistério?'},
    {'role': 'assistant', 'content': 'A primeira fase começa com uma caixa fechada no quintal.'},
]


@pytest.mark.parametrize(('pedido', 'descricao'), [
    (PEDIDO_JOGO, 'nosso jogo de mistério no quintal'),
    ('Que título você escolheria para este livro de aventuras?', 'este livro de aventuras'),
    ('Sugira um título para nossa história de piratas.', 'nossa história de piratas'),
])
def test_descricao_do_alvo_de_nomeacao_nao_e_nome_ja_atribuido(pedido, descricao):
    retrato, recentes = construir_retrato_turno(pedido, turno={}, mente={}, contexto_perceptivo={})
    assert not retrato['entidade_explicita'] and not retrato['referencia_resolvida'] and not recentes
    assert retrato['alvo_nomeacao_autoral'] == descricao
    assert not extrair_tema_fundamentacao(pedido, retrato=retrato)


@pytest.mark.parametrize(('pedido', 'titulo'), [
    ('Qual é o título oficial do jogo chamado De Mistério no Quintal?', 'De Mistério no Quintal'),
    ('Qual nome você daria ao nosso jogo de mistério? Quando foi lançado o jogo Portal?', 'Portal'),
    ('Explique o enredo do livro Duna. Qual nome você daria ao nosso jogo de mistério?', 'Duna'),
])
def test_nomeacao_nao_oculta_identificacao_ou_consulta_independente(pedido, titulo):
    retrato, _ = construir_retrato_turno(pedido, turno={}, mente={}, contexto_perceptivo={})
    assert not retrato.get('alvo_nomeacao_autoral')
    assert extrair_tema_fundamentacao(pedido, retrato=retrato) == titulo


def test_ponte_nomeia_artefato_atual_sem_publicar_descricao_do_anterior(monkeypatch):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    titulo = 'Eu chamaria de «O Segredo do Quintal».'
    caso = {'entrada': PEDIDO_JOGO, 'historico': HISTORICO_JOGO}
    d = autoria.coletar_autoria(caso, [proposta(FALA_ROBO), proposta(titulo)])
    principal = '\n'.join(m['content'] for m in d['envios'][0]['messages'] if m['role'] == 'system')
    assert not d['plano']['fundamentacao']
    assert 'Alvo a nomear: nosso jogo de mistério no quintal.' in principal
    assert 'jogo=De Mistério No Quintal' not in principal
    assert any('nomeacao_sem_delimitacao' in (t['problemas_bloqueantes'] or []) for t in d['trace'])
    assert not d['execucao_exigida'] and not d['operacional'] and d['http'] == 2
    assert d['falas'] == [titulo] and len(d['publicacoes']) == 1
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']


def conferir(pedido: str, fala: str) -> dict:
    return validar_fala_com_fundamentacao(
        fala, texto_usuario=pedido,
        fundamentacao={'tema': 'De Mistério', 'confiavel': False},
    )


@pytest.mark.parametrize(('pedido', 'fala'), [
    (PEDIDO_CORUJA, TITULO_CORUJA),
    (PEDIDO, TITULO),
    (PEDIDO, 'Título: “O Título Oficial dos Piratas”.'),
    ('Qual nome você daria ao nosso conto?', 'Nome: “O Farol da Lua”.'),
    ('Como você chamaria nossa conversa de hoje?', 'Título: “Depois da Chuva. E Agora?”.'),
    ('Sugira um título para esse jogo.', 'Eu chamaria de “Cartas, Relógios e Sombras”.'),
])
def test_titulo_proposto_e_uma_entrega_autoral_sem_exigir_fonte(pedido, fala):
    resultado = conferir(pedido, fala)
    assert resultado['fala'] == fala
    assert resultado['problemas'] == []


@pytest.mark.parametrize('consulta', [
    'Qual é o título oficial dessa história?',
    'Na verdade, quero o título oficial da história.',
    'Qual título a editora publicou?',
    'Quis dizer o título do jogo.',
    'Não quero sugestões.',
])
@pytest.mark.parametrize('ordem', [(0, 1), (1, 0)])
def test_consulta_ou_retificacao_no_mesmo_turno_preserva_a_exigencia_de_fonte(consulta, ordem):
    frases = (PEDIDO, consulta)
    resultado = conferir(' '.join(frases[i] for i in ordem), TITULO)
    assert 'O Farol' not in resultado['fala']
    assert 'obra_sem_evidencia' in resultado['problemas']


@pytest.mark.parametrize('fala', [
    TITULO + ' Este é o título oficial.',
    'Este é o título oficial. ' + TITULO,
    'Encontrei “O Farol da Lua”.',
    'Recomendo “O Farol da Lua”.',
    'O título oficial é “O Farol da Lua”.',
    'O título oficial é «O Farol da Lua».',
    '“O Farol da Lua”. Este é o título oficial da história que saiu no catálogo da editora.',
    'Este é o título oficial da história que saiu no catálogo da editora. “O Farol da Lua”.',
    RASCUNHO_CORUJA,
])
def test_titulo_em_moldura_assertiva_ou_mista_nao_ganha_apoio_da_nomeacao(fala):
    pedido = PEDIDO_CORUJA if fala == RASCUNHO_CORUJA else PEDIDO
    resultado = conferir(pedido, fala)
    assert 'O Farol' not in resultado['fala'] and 'O Mistério' not in resultado['fala']
    assert resultado['requer_reparo'] is True


def test_titulo_mencionado_na_pergunta_nao_prova_identificacao_oficial():
    resposta = 'O título oficial é “O Farol da Lua”.'
    resultado = conferir('O título oficial dessa história é “O Farol da Lua”?', resposta)
    assert resposta not in resultado['fala']
    assert 'obra_sem_evidencia' in resultado['problemas']


def test_identificacao_oficial_pode_usar_a_fonte_factual_vigente():
    fala = 'O título oficial é “O Farol da Lua”.'
    resultado = validar_fala_com_fundamentacao(
        fala, texto_usuario='Qual é o título oficial desta história?',
        fundamentacao={
            'tema': 'o conto', 'confiavel': True,
            'resumo': 'O catálogo da editora registra o conto O Farol da Lua.',
        },
    )
    assert resultado['fala'] == fala
    assert resultado['problemas'] == []


def test_ponte_publica_o_titulo_proposto_com_aspas_e_pontuacao():
    d = coletar({'entrada': PEDIDO_CORUJA, 'historico': []}, [proposta(TITULO_CORUJA)])
    assert d['resposta']['tipo'] == 'resposta'
    assert d['resposta']['texto'] == TITULO_CORUJA
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']
    assert d['http'] == 1 and not d['orcamento']['chamadas_bloqueadas']


def test_ponte_nao_publica_como_sugestao_o_titulo_do_rascunho_contraditorio():
    reparo = 'Título: “A Caixa das Três Pistas”.'
    d = coletar({'entrada': PEDIDO_CORUJA, 'historico': []},
                [proposta(RASCUNHO_CORUJA), proposta(reparo)])
    assert d['resposta']['tipo'] == 'resposta'
    assert d['resposta']['texto'] == reparo
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']
    assert d['http'] == 2 and not d['orcamento']['chamadas_bloqueadas']

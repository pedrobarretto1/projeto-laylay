"""Continuação pedida pelo usuário conserva a cena e publica um evento."""

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import mkdtemp

import pytest

from mente_laylay.cognicao.criacao_ficcional import criacao_ficcional_vigente
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from scripts.tests.test_finalidade_ficcional_revisao import preparar
from tests.test_papo_casual_composicao import CODIGO, PONTE, RAIZ, proposta


RODADA_10 = (
    'Uma coruja com bolso?! Hahaha, você me pegou desprevenido. '
    'Suponha que ela tire um mapa de dentro desse bolso, com um X marcado na nossa mesa. '
    'Qual seria o próximo acontecimento dessa história?'
)
HISTORICO = [
    {'role': 'user', 'content': 'Entendi. Vamos conversar sem mistérios por um instante. Imagine que uma pequena coruja pousou na sua janela e ficou te encarando. Você falaria com ela? O que diria?'},
    {'role': 'assistant', 'content': "Se uma coruja pousasse na janela e me olhasse, eu diria: 'Oi, pequena, você tá com fome de conversa ou só quer ver se o mundo ainda tem cor?'. Aí, se ela não responder, eu riria e faria um som de gato dormindo — só pra ver se ela desce e me deixa ver o que tem no seu bolso."},
]
FALA = 'Na história, «A coruja vira o mapa na direção do relógio que está parado.»'


def executar(propostas):
    pasta = RAIZ / 'resultados_testes/coruja_20261108/proximo_acontecimento'
    pasta.mkdir(parents=True, exist_ok=True)
    perfil = Path(mkdtemp(dir=pasta))
    caso = {'entrada': RODADA_10, 'historico': HISTORICO, 'ponte': str(PONTE),
            'propostas': propostas}
    processo = subprocess.run([sys.executable, '-B', '-c', CODIGO, str(perfil),
        json.dumps(caso, ensure_ascii=False)], cwd=RAIZ,
        env=dict(os.environ, PYTHONIOENCODING='utf8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=60)
    assert processo.returncode == 0, processo.stdout[-2000:] + processo.stderr[-3000:]
    dados = json.loads(next(linha.partition('=')[2] for linha in processo.stdout.splitlines()
        if linha.startswith('EFEITO_JSON=')))
    assert not dados['efeitos'] and not dados['voz'] and not dados['violacoes']
    return dados


@pytest.mark.parametrize('pedido,recorte', [
    (RODADA_10, 'ela tire um mapa de dentro desse bolso, com um X marcado na nossa mesa'),
    ('Imagine que o faroleiro ache uma carta na janela. Qual é o próximo evento desta história?',
     'o faroleiro ache uma carta na janela'),
    ('Imagine que o faroleiro ache uma carta na janela. O que acontece depois nessa história?',
     'o faroleiro ache uma carta na janela'),
    ('Suponha que o trem encoste na estação vazia. Conte o próximo acontecimento da nossa história.',
     'o trem encoste na estação vazia'),
])
def test_pedido_positivo_vincula_o_recorte_do_proximo_acontecimento(pedido, recorte):
    plano = preparar(pedido)
    assert not plano['autoriza_execucao'] and not plano['requer_execucao'] and not plano['comandos']
    fonte = criacao_ficcional_vigente(plano)
    assert fonte is not None
    assert fonte.recorte_proximo_acontecimento == recorte
    assert fonte.pode_confirmar_fato_externo is False


@pytest.mark.parametrize('pedido', [
    'Quem fundou Alexandria?! ' + RODADA_10,
    'Me diga a altura do Everest. ' + RODADA_10,
    RODADA_10 + ' Qual é a cotação do dólar agora?',
    RODADA_10 + ' Me explica o que é uma variável em Python.',
    RODADA_10 + ' Abra a Calculadora.',
    'Suponha que ela tire um mapa e explique a fotossíntese. Qual seria o próximo acontecimento dessa história?',
    'Suponha que ela tire um mapa, explique como funciona o Gmail. Qual seria o próximo acontecimento dessa história?',
    'Suponha que ela tire um mapa e quem fundou Alexandria? Qual seria o próximo acontecimento dessa história?',
    'Não continue a história. ' + RODADA_10,
    'A frase «Qual seria o próximo acontecimento dessa história?» é uma pergunta.',
])
def test_proximo_acontecimento_nao_absorve_outro_assunto_ou_negacao(pedido):
    assert criacao_ficcional_vigente(preparar(pedido)) is None


def test_composicao_publica_estado_interno_a_um_evento_sem_receipt_operacional():
    dados = executar([proposta(FALA)])
    resposta = dados['resposta']
    assert resposta['tipo'] == 'resposta' and resposta['texto'] == FALA
    assert not resposta['degradada'] and not resposta['falhas_geracao']
    assert dados['http'] == 1 and dados['falas'] == [FALA]
    assert not dados['autoriza'] and not dados['comandos']


def test_publicacao_sem_codec_tambem_confere_o_recorte_do_acontecimento():
    fala = 'Na história, «A coruja vira o mapa. A mesa desaparece.»'
    negada = verificar_fala_turno(fala, plano=preparar(RODADA_10, fala=fala))
    assert not negada['aceita']
    assert 'proximo_acontecimento_fora_do_recorte' in negada['problemas']
    assert verificar_fala_turno(FALA, plano=preparar(RODADA_10, fala=FALA))['aceita']


@pytest.mark.parametrize('fala', [
    'Na história, «A coruja vira o mapa ou o relógio desperta.»',
    'Na história, «A coruja vira o mapa. A mesa desaparece.»',
    'Na história, «O mapa é importante para a história.»',
    'Na história, «A coruja tira o mapa do bolso.»',
    'Na história, «O faroleiro acende a luz.»',
    'Na história, «A coruja vira o mapa.» Abri o navegador.',
])
def test_composicao_nao_publica_alternativas_digressao_ou_efeito_real(fala):
    dados = executar([proposta(fala), proposta(FALA)])
    assert fala not in dados['falas'] and fala not in dados['resposta']['texto']
    assert not dados['autoriza'] and not dados['comandos']

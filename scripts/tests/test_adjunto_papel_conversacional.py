"""Enquadramento nominal pertence à matriz; não pergunta nem autoriza sozinho."""
import json
from pathlib import Path

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno, fontes_textuais_dos_segmentos

CASO = next(c for c in json.loads((Path(__file__).parent / 'fixtures/biblioteca_20261031.json').read_text(encoding='utf8')) if c['id'] == 'teste-06')


@pytest.mark.parametrize('papel', ['IA', 'professora', 'modelo de linguagem', 'assistente virtual', 'robô'])
def test_papel_nominal_nao_e_pergunta_separada_da_matriz_declarativa(papel):
    texto = f'Como {papel}, eu não tenho esse arquivo.'
    turno = classificar_modalidade_turno(texto)
    assert len(turno['segmentos']) == 1
    assert turno['segmentos'][0]['modalidade'] == 'conversa'
    assert not turno['autoriza_execucao']
    fontes = fontes_textuais_dos_segmentos(texto, turno['segmentos'])
    assert len(fontes) == 1 and fontes[0].como_dict()['texto_original'] == texto


@pytest.mark.parametrize('texto', [
    'Como IA, não tenho esse arquivo. Por que você disse isso?',
    'Como professora, não tenho esse livro. Por que você disse isso?',
])
def test_papel_nao_abre_consulta_historica_artificial_antes_da_consulta_real(texto):
    turno = classificar_modalidade_turno(texto)
    assert len(turno['segmentos']) == 2
    assert [s['modalidade'] for s in turno['segmentos']] == ['conversa', 'pergunta']
    assert len(fontes_textuais_dos_segmentos(texto, turno['segmentos'])) == 2


def test_entrada6_preserva_enquadramento_sem_inventar_pergunta_sobre_como_ia():
    turno = classificar_modalidade_turno(CASO['entrada'])
    assert len(turno['segmentos']) == 6
    assert sum(s['modalidade'] == 'pergunta' for s in turno['segmentos']) == 1
    assert 'como ia,' in turno['segmentos'][2]['texto_estrutural']
    assert len(fontes_textuais_dos_segmentos(CASO['entrada'], turno['segmentos'])) == 6
    assert not turno['autoriza_execucao'] and not turno['texto_operacional']


@pytest.mark.parametrize('papel', ['IA', 'professora', 'assistente virtual'])
def test_papel_nao_veta_pedido_direto_da_matriz(papel):
    texto = f'Como {papel}, abra o aplicativo Calculadora.'
    turno = classificar_modalidade_turno(texto)
    assert turno['autoriza_execucao']
    assert len(turno['segmentos']) == 1
    assert turno['segmentos'][0]['modalidade'] == 'comando'


@pytest.mark.parametrize('texto', [
    'Como IA, qual é sua opinião?',
    'Como professora, por que você disse isso?',
])
def test_papel_preserva_a_pergunta_da_matriz(texto):
    turno = classificar_modalidade_turno(texto)
    assert len(turno['segmentos']) == 1
    assert turno['segmentos'][0]['modalidade'] == 'pergunta'
    assert not turno['autoriza_execucao']


@pytest.mark.parametrize('texto', ['Como a IA funciona?', 'Como ia o seu dia?',
    'Como funciona, por que parou?', 'Como vai, você tem alguma novidade?',
    'Como ia, eu não sei.', 'Como zzzxxx, eu prefiro esse livro.'])
def test_pergunta_ou_papel_sem_evidencia_nao_perde_seu_nucleo(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno['segmentos'][0]['modalidade'] == 'pergunta'
    assert turno['segmentos'][0]['texto'].startswith('como ')
    assert not turno['autoriza_execucao']


@pytest.mark.parametrize('texto', ['Se eu fosse IA, eu abriria o navegador.',
    'Como IA, se eu confirmar, abra o navegador.',
    'Como IA, não abra o navegador.'])
def test_condicao_e_negacao_nao_recebem_autorizacao_do_enquadramento(texto):
    assert not classificar_modalidade_turno(texto)['autoriza_execucao']


def test_ordem_seguinte_independente_mantem_sua_fonte_e_autoridade():
    texto = 'Como IA, não tenho esse arquivo. Abra o aplicativo Calculadora.'
    turno = classificar_modalidade_turno(texto)
    assert turno['autoriza_execucao'] and len(turno['segmentos']) == 2
    assert [s['autoriza_execucao'] for s in turno['segmentos']] == [False, True]
    assert len(fontes_textuais_dos_segmentos(texto, turno['segmentos'])) == 2


def test_papel_dentro_de_nome_citado_nao_e_projetado_como_matriz():
    texto = 'Abra o arquivo "Como IA, meu arquivo.txt".'
    turno = classificar_modalidade_turno(texto)
    assert turno['autoriza_execucao'] and len(turno['segmentos']) == 1
    assert turno['segmentos'][0]['texto'].startswith('abra o arquivo')


@pytest.mark.parametrize('texto', ['COMO FUNCIONA, EU NÃO SEI.',
    'COMO VAI, VOCÊ TEM ALGUMA NOVIDADE?', 'Como ZZXQQ, eu não sei.'])
def test_caixa_alta_sozinha_nao_cria_leitura_nominal(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno['segmentos'][0]['modalidade'] == 'pergunta'


def test_cabecalho_repetido_com_mesma_grafia_nao_perde_evidencia_lexical():
    texto = 'Como IA, não tenho arquivo. Como IA, não tenho arquivo.'
    turno = classificar_modalidade_turno(texto)
    assert not any(s['modalidade'] == 'pergunta' for s in turno['segmentos'])
    assert not turno['autoriza_execucao']


def test_expansao_nominal_da_sigla_e_lida_pelo_mesmo_lexico():
    turno = classificar_modalidade_turno('Como inteligência artificial, eu prefiro conversar.')
    assert turno['segmentos'][0]['modalidade'] == 'conversa'

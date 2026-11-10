"""Pedido de formato e pergunta citada não delegam operações nem consultas."""
import json
from pathlib import Path

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.normalizacao_linguagem import localizar_enunciacao_avaliativa
from tests.test_metodo_inspecao_composicao import plano_do_turno
from tests import test_autoria_operacao_composicao as autoria
from tests.test_biblioteca_retorno_composicao import PONTE_INSTALADA
from tests.test_papo_casual_composicao import proposta


CASOS = {c['rodada']: c for c in json.loads((Path(__file__).parent / 'fixtures/hotel_20261109.json').read_text(encoding='utf8'))}


@pytest.mark.parametrize('entrada', [CASOS[2]['entrada'],
    'Responda em até três frases.', 'Responda em no máximo 4 palavras.',
    'Responda em pelo menos duas frases.', 'Responda em duas ou três frases.',
    'Responda entre dois e quatro parágrafos.',
    'Responda com no máximo quatro palavras.',
])
def test_quantificador_de_extensao_pertence_a_resposta(entrada):
    t = classificar_modalidade_turno(entrada)
    assert not t['autoriza_execucao'] and not t['texto_operacional']


@pytest.mark.parametrize('entrada', [
    'Responda em até três frases por e-mail.',
    'Responda em duas ou três frases e abra o Chrome.',
    'Responda em no máximo quatro palavras no arquivo resposta.txt.',
])
def test_quantificador_nao_absorve_destino_ou_comando(entrada):
    assert classificar_modalidade_turno(entrada)['autoriza_execucao']


@pytest.mark.parametrize('entrada', [
    "Agora imagine que um hóspede pergunta: 'Você sabe se o elevador direito está quebrado?'",
    'Hoje o personagem perguntou: «A lâmpada está acesa?»',
    'Agora a menina diz: "Quem está online?"',
])
def test_interrogacao_citada_nao_torna_a_matriz_uma_consulta(entrada):
    t = classificar_modalidade_turno(entrada)
    assert t['modalidade'] != 'pergunta'
    # O consumidor não deve confiar no rótulo grosseiro de outro produtor.
    for turno in (t, {'modalidade': 'pergunta'}):
        assert not classificar_atualidade_factual(entrada, turno=turno)['depende_atualidade']


@pytest.mark.parametrize('entrada', [
    'Agora o personagem pergunta: «Quem está online?». Quem está online agora?',
    'Quem está online agora? O personagem perguntou: «Quem está online?»',
    'Você sabe se "o elevador está quebrado" agora?',
    'O preço atual é cem reais, confere?',
])
def test_consulta_externa_conserva_sua_obrigacao(entrada):
    assert classificar_atualidade_factual(entrada, turno=classificar_modalidade_turno(entrada))['depende_atualidade']


def test_ponte_publica_resposta_com_limite_sem_cobrar_executor(monkeypatch):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    caso = CASOS[2]
    fala = caso['proposta']['fala']
    d = autoria.coletar_autoria(caso, [proposta(fala)])
    assert not d['execucao_exigida'] and not d['operacional']
    assert d['resposta']['texto'] == fala
    assert d['http'] == len(d['publicacoes']) == 1
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']


def test_ponte_responde_incerteza_sem_inventar_acesso(monkeypatch):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    fala = 'Não sei se está quebrado; não vi o elevador nem fiz um teste.'
    d = autoria.coletar_autoria(CASOS[6], [proposta(fala)])
    assert not d['plano']['atualidade']['depende_atualidade']
    assert not d['plano']['fundamentacao'].get('requer_evidencia_recente')
    assert d['resposta']['texto'] == fala
    assert d['http'] == len(d['publicacoes']) == 1
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']


@pytest.mark.parametrize('fala', [
    CASOS[3]['proposta']['fala'],
    'A escola não precisa de competição, ela precisa de colaboração.',
    'O projeto não necessita de pressa, o projeto necessita de cuidado.',
    'As reuniões não precisam de discursos, elas precisam de escuta.',
])
def test_contraste_de_prioridade_declara_posicao_sem_primeira_pessoa(fala):
    entrada = CASOS[3]['entrada']
    q = avaliar_qualidade_comunicacao(entrada, fala, plano=plano_do_turno(entrada))
    assert 'ato_opiniao_nao_respondido' not in q['problemas_bloqueantes']


@pytest.mark.parametrize('fala', [
    'O projeto não necessita de pressa, a escola necessita de cuidado.',
    'O hotel não precisa de dança, ela precisa de liberdade.',
    'O hotel não precisa de dança, ele precisa de liberdade?',
    'Ela disse: "O hotel não precisa de dança, ele precisa de liberdade."',
    'Se o hotel não precisa de dança, ele precisa de liberdade.',
    'O hotel não precisa de dança.',
])
def test_contraste_citado_condicional_ou_sem_mesmo_sujeito_nao_declara_posicao(fala):
    assert localizar_enunciacao_avaliativa(fala) is None


def test_ponte_publica_posicao_contrastiva_sem_reparo_desnecessario(monkeypatch):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    caso = CASOS[3]
    d = autoria.coletar_autoria(caso, [proposta(caso['proposta']['fala'])])
    assert d['http'] == len(d['publicacoes']) == 1
    assert d['resposta']['texto'] == caso['proposta']['fala']
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']


@pytest.mark.parametrize('intent,params,fato', [
    ('APP_OPEN', {'nome_app': 'Opera'}, 'Consegui abrir o Opera.'),
    ('MEDIA_CONTROL', {'action': 'pause'}, 'Consegui pausar a música.'),
])
def test_posicao_nao_confirma_receipt_proposto_pelo_modelo(monkeypatch, intent, params, fato):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    segura = 'O hotel não precisa de dança, ele precisa de liberdade.'
    recibo = {'intent': intent, 'params': params, 'executou': True, 'confirmado': True, 'origem': 'executor'}
    d = autoria.coletar_autoria(CASOS[3], [proposta(segura + ' ' + fato, [recibo]), proposta(segura)])
    assert fato not in d['resposta']['texto']
    assert not d['execucao_exigida'] and not d['operacional']

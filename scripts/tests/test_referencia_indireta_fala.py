"""Referir conteúdo entregue não confere a equivalência do resumo nem a causa."""
from copy import deepcopy
import json
from pathlib import Path
import time

import pytest

from mente_laylay.cognicao.explicacao_fala_historica import (
    vincular_explicacoes_por_ato, realizacoes_fala_historica,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.registro_semantico import (
    registrar_fala_observada, recuperar_evidencia_da_fala,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


CASO = next(c for c in json.loads((Path(__file__).parent / 'fixtures/biblioteca_20261031.json')
    .read_text(encoding='utf8')) if c['id'] == 'teste-06')
FALA = CASO['historico'][-1]['content']
PERGUNTA = 'Agora me conta: por que voce disse que nao consegue inventar?'


def guardar(fala=FALA, *, registro=None, identidade='fonte', agora=None):
    return registrar_fala_observada(registro, ocorrencia_id=identidade, turno_id='turno-'+identidade,
        fala=fala, resultados=(), canal='texto_publicado', agora=agora)


def consultar(texto=PERGUNTA, *, registro=None, fala=FALA, agora=None):
    reg = guardar(fala) if registro is None else registro
    mente = {'registro_semantico':reg, 'turno_atual':classificar_modalidade_turno(texto)}
    antes = deepcopy(mente)
    evidencia = recuperar_evidencia_da_fala(texto, mente, agora=agora)
    assert mente == antes, 'A consulta deve permanecer read-only.'
    return evidencia


def test_referencia_indireta_historica06_recupera_fonte_integral_com_restricao():
    evidencia = consultar()
    assert evidencia, 'Primeira fronteira: conteúdo relatado não identificou a fala entregue.'
    assert evidencia['referencia_ambigua'] is False
    assert evidencia['origem_referencia']=='conteudo_indireto'
    assert evidencia['autoriza_execucao'] is False
    assert evidencia['falas'][0]['fala'] == FALA
    assert 'de novo o que não existe' in evidencia['falas'][0]['fala']
    assert evidencia['falas'][0]['resultados'] == []
    assert evidencia['falas'][0]['id'] == 'fonte'
    assert not any(k in evidencia for k in ('causa','verdade','equivalencia_semantica'))


@pytest.mark.parametrize('fala,pergunta', [
    ('Eu não posso abrir esse arquivo sem autorização.', 'Por que você disse que não pode abrir esse arquivo?'),
    ('Não consigo lembrar o nome agora.', 'Por que você afirmou que não consegue lembrar o nome?'),
    ('Eu posso inventar histórias com você.', 'Por que você falou que pode inventar histórias?'),
    ('Eu acho importante conferir cada etapa.', 'Por que você disse que acha importante conferir cada etapa?'),
    ('Eu não consigo inventar de novo o que não existe.', 'Por que você disse que você não consegue inventar?'),
])
def test_conteudo_indireto_reusa_perspectiva_e_conserva_complementos(fala,pergunta):
    evidencia = consultar(pergunta,fala=fala)
    assert evidencia and evidencia['falas'][0]['fala'] == fala


def test_referencia_explicita_sobrevive_a_fala_intermediaria_sem_virar_recencia():
    registro = guardar()
    registro = guardar('Podemos conversar sobre música.',registro=registro,identidade='outra')
    evidencia = consultar(registro=registro)
    assert evidencia and [f['id'] for f in evidencia['falas']] == ['fonte']


def test_referencia_compativel_em_ocorrencias_distintas_continua_ambigua():
    registro = guardar()
    registro = guardar('Eu não consigo inventar músicas.',registro=registro,identidade='outra')
    evidencia = consultar(registro=registro)
    assert evidencia and evidencia['referencia_ambigua'] is True
    assert 'origem_referencia' not in evidencia
    assert {f['id'] for f in evidencia['falas']} == {'fonte','outra'}


@pytest.mark.parametrize('idade',[-1,901,float('nan'),float('inf')])
def test_identificacao_indireta_nao_renova_fonte_expirada_futura_ou_invalida(idade):
    agora = time.time()
    assert not consultar(registro=guardar(agora=agora),agora=agora+idade)


@pytest.mark.parametrize('pergunta',[
    'Por que ele disse que não consegue inventar?',
    'Por que eu disse que não consigo inventar?',
    'Por que nós dissemos que não conseguimos inventar?',
    'Por que você disse que consegue inventar?',
    'Por que você disse que não pode inventar?',
    'Por que você disse que não conseguia inventar?',
    'Por que você disse que não conseguiria inventar?',
    'Por que você disse que eu não consigo inventar?',
    'Por que você não disse que não consegue inventar?',
    'Se você disse que não consegue inventar, por quê?',
    'Por que você diria que não consegue inventar?',
    'Traduza "por que você disse que não consegue inventar?"',
    'Você disse que não consegue inventar. Qual sua cor preferida?',
    'Você consegue inventar?',
    'Por que você disse que não consegue inventar músicas?',
    'Por que você disse que não consegue inventar isso?',
])
def test_referencia_indireta_nao_troca_agente_negacao_modalidade_ou_conteudo(pergunta):
    assert not consultar(pergunta)


@pytest.mark.parametrize('fala',[
    'Não posso inventar histórias.',
    'Eu consigo inventar histórias.',
    'Não conseguiria inventar histórias.',
    'Ela não consegue inventar histórias.',
    'Eu disse que não consigo inventar histórias.',
    'Não digo que não consigo inventar histórias.',
    'Não é verdade que não consigo inventar histórias.',
    'Não é verdade que, infelizmente, não consigo inventar histórias.',
    'Acho que não consigo inventar histórias.',
    'Se eu tentar, não consigo inventar histórias.',
    'Se tentasse, não consigo inventar histórias.',
    'Talvez eu não consiga inventar histórias.',
    'Talvez, não consigo inventar histórias.',
    'Imagine: não consigo inventar histórias.',
    'Na história: não consigo inventar histórias.',
    'Ela disse: "não consigo inventar histórias".',
    'Será que não consigo inventar histórias?',
    'Não consigo inventar histórias?',
    'Ela diz, não consigo inventar histórias.',
    'O exemplo é, não consigo inventar histórias.',
    'Na hipótese de conseguir, não consigo inventar histórias.',
    'Eu me pergunto, não consigo inventar histórias.',
    'Eu não acho, não consigo inventar histórias.',
    'De brincadeira, não consigo inventar histórias.',
])
def test_mencao_na_fonte_nao_equivale_a_predicado_proprio_assertivo(fala):
    assert not consultar(fala=fala)


def test_mencao_explicita_incompativel_nao_cai_em_deitico_por_outro_assunto():
    pergunta = 'Por que você disse que não pode abrir esse arquivo?'
    evidencia = consultar(pergunta,fala='Eu não posso abrir esse arquivo azul.')
    # A pergunta apenas localiza o início do conteúdo; o qualificador é preservado.
    assert evidencia and evidencia['falas'][0]['fala'].endswith('azul.')
    assert not consultar('Por que você disse que não pode abrir esse arquivo vermelho?',
        fala='Eu não posso abrir esse arquivo azul.')


def test_vinculo_por_ato_consume_fonte_sem_criar_causa_ou_receipt():
    texto = 'Entendi. ' + PERGUNTA
    turno = classificar_modalidade_turno(texto)
    fonte = vincular_explicacoes_por_ato(texto,turno=turno,mente={'registro_semantico':guardar()})
    assert fonte is not None and len(fonte.partes)==2
    assert fonte.partes[0].fala is fonte.partes[0].ocorrencia is None
    historica = fonte.partes[1]
    assert historica.fala is not None and historica.ocorrencia is None
    evidencia = historica.fala.como_dict()
    assert evidencia['falas'][0]['fala']==FALA
    realizacoes = realizacoes_fala_historica(evidencia)
    assert realizacoes and all('motivo' in t and 'registrado' in t for t in realizacoes)
    assert all('resultado operacional' not in t for t in realizacoes)
    assert all('porque' not in t.casefold() for t in realizacoes)


@pytest.mark.parametrize('fala', [
    'Não consigo inventar é o título do seu texto.',
    'Não consigo inventar — palavras suas, Pedro.',
    'Eu só reproduzo sua frase, não consigo inventar histórias.',
])
def test_trecho_presente_nao_e_qualificado_como_asserção_ou_equivalencia(fala):
    evidencia = consultar(fala=fala)
    assert evidencia and evidencia['falas'][0]['fala'] == fala
    assert evidencia['prova_afirmacao'] is False
    assert evidencia['prova_equivalencia'] is False
    assert evidencia['prova_causa'] is False
    respostas = realizacoes_fala_historica(evidencia)
    assert respostas and all('trecho' in r and 'afirmação' not in r for r in respostas)
    assert all('motivo' in r and 'não ficou registrado' in r for r in respostas)


def test_binder_do_caso06_recebe_literal_inteiro_sem_usar_comentarios_como_fonte():
    turno = classificar_modalidade_turno(CASO['entrada'])
    fonte = vincular_explicacoes_por_ato(CASO['entrada'],turno=turno,
        mente={'registro_semantico':guardar()})
    assert fonte is not None
    historicas = [p for p in fonte.partes if p.fala is not None]
    assert len(historicas)==1, 'Primeiro RED: a pergunta dentro do ato integral perdeu a fonte.'
    historica, = historicas
    assert historica.fonte_textual.como_dict()['texto_original'] == CASO['entrada'][CASO['entrada'].index('Agora me conta:'):]
    assert historica.fala.como_dict()['falas'][0]['fala']==FALA
    assert all(p.ocorrencia is p.fala is None for p in fonte.partes if p is not historica)


@pytest.mark.parametrize('comentario',[
    'Ela mesma inventou a piada há pouco.',
    'Pode discordar de mim sem medo.',
    'Você mesma inventou a piada há pouco. Pode discordar de mim sem medo.',
])
def test_comentario_no_mesmo_ato_nao_troca_agente_da_consulta(comentario):
    evidencia = consultar(PERGUNTA+' '+comentario)
    assert evidencia and evidencia['falas'][0]['fala']==FALA


def test_segunda_referencia_explicita_no_mesmo_ato_nao_e_descartada():
    assert not consultar(PERGUNTA+' Você falou que pode abrir esse arquivo.')


@pytest.mark.parametrize('intent,alvo',[('CREATE_FILE','relatorio.txt'),('IOT_CONTROL','lâmpada')])
def test_lookup_indireto_conserva_receipt_sem_derivar_efeito_da_fala(intent,alvo):
    receipt = ResultadoAcao(intent=intent,alvo=alvo,status='erro',executou=False,
        confirmado=False,origem='executor',id_solicitacao='falha-real',confirmacao_oferecida='indisponivel')
    registro = registrar_fala_observada(None,ocorrencia_id='fonte',turno_id='origem',
        fala=FALA,resultados=(receipt,),canal='texto_publicado')
    evidencia = consultar(registro=registro)
    assert evidencia and evidencia['origem_referencia']=='conteudo_indireto'
    resultado, = evidencia['falas'][0]['resultados']
    assert resultado['id_solicitacao']=='falha-real' and resultado['alvo']==alvo
    assert resultado['executou'] is resultado['confirmado'] is False
    assert resultado['origem']=='executor'
    realizacoes = realizacoes_fala_historica(evidencia)
    assert realizacoes and all('efeito não confirmado' in r and 'não informa a causa' in r for r in realizacoes)

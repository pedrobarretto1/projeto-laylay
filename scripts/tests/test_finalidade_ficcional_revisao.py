"""Ficção delimitada não é explicação factual nem confirmação operacional."""
from copy import deepcopy
import json
import time

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, explicacao_exige_apoio_individual
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria_obrigatoria

PEDIDOS = (
    'Imagine uma cidade flutuante numa história. Como isso funcionaria nesse mundo imaginário?',
    'Na história, me explica como o robô conversaria com uma árvore.',
    'Me explica como funcionaria uma biblioteca de nuvens numa história fictícia.',
    'Invente uma história curta sobre um robô que encontra uma carta.',
)
FALA = 'Na história, a cidade flutua sobre nuvens que guardam os sonhos dos moradores.'


def preparar(texto, *, mente=None, fala=FALA, fontes=(), declaracao=True):
    t = classificar_modalidade_turno(texto)
    p = planejar_turno(texto, turno=t, mente=mente or {})
    p['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=t, plano=p, mente=mente or {})
    d = {'fala':fala, 'comandos':[]}
    if declaracao:
        d['suporte_proposicoes'] = [{'texto':fala, 'fontes':list(fontes)}]
    p['suporte_autoria_proposto'] = capturar_suporte_autoria_obrigatoria(
        ContratoPropostaPrincipal(str(p['id']), texto, json.dumps(d), True))
    return p


@pytest.mark.parametrize('pedido', PEDIDOS)
def test_criacao_e_explicacao_do_cenario_nao_herdam_obrigacao_factual(pedido):
    p = preparar(pedido)
    assert not explicacao_exige_apoio_individual(p), 'perfil explicativo virou obrigação factual'
    assert p['contrato_fala'].get('criacao_ficcional') is not None
    r = revisar_suporte_autoria(FALA, plano=p)
    assert r is not None and not r.aplicar_limite and r.fala_realizada == FALA
    assert r.como_dict()['estado'] == 'criacao_ficcional_delimitada'
    assert r.prova_implicacao is r.semantica_verificada is r.autoriza_execucao is False
    assert not p['comandos'] and not p['requer_execucao'] and not p['autoriza_execucao']


@pytest.mark.parametrize('pedido', ['Como isso funcionaria?',
    'Como essa ideia se desenvolveria?', 'Detalha esse cenário para mim.',
    'Gostei da ideia. Vamos pensar em outra. Como isso funcionaria?'])
def test_continuacao_usa_finalidade_anterior_vinculada_ao_usuario(pedido):
    anterior = preparar(PEDIDOS[0])
    estado = {'contrato_fala_atual':anterior['contrato_fala'],
        'ultima_entrada':PEDIDOS[0], 'ultima_entrada_ts':time.time(), 'ultima_resposta':FALA}
    antes = deepcopy(estado)
    p = preparar(pedido, mente=estado)
    assert p['contrato_fala'].get('criacao_ficcional') is not None
    assert not explicacao_exige_apoio_individual(p)
    assert not revisar_suporte_autoria(FALA, plano=p).aplicar_limite
    assert estado == antes


@pytest.mark.parametrize('caso', ['sem_contrato', 'outra_entrada', 'expirado', 'proposta_da_ia'])
def test_continuacao_nao_e_autocertificada_por_fala_da_ia(caso):
    p = preparar(PEDIDOS[0])
    estado = {'contrato_fala_atual':p['contrato_fala'], 'ultima_entrada':PEDIDOS[0],
        'ultima_entrada_ts':time.time(), 'ultima_resposta':FALA}
    if caso == 'sem_contrato': estado['contrato_fala_atual'] = {}
    elif caso == 'outra_entrada': estado['ultima_entrada'] = 'Me explica como funciona um motor.'
    elif caso == 'expirado': estado['ultima_entrada_ts'] -= 500
    else: estado['contrato_fala_atual'] = {'criacao_ficcional':{'origem':'llm','ficcao':True}}
    atual = preparar('Como isso funcionaria?', mente=estado)
    assert not atual['contrato_fala'].get('criacao_ficcional')
    assert explicacao_exige_apoio_individual(atual)


@pytest.mark.parametrize('pedido', [
    'Me explica como funciona a fotossíntese.',
    'Me ensina o que é uma variável em Python.',
    'Me explica a história do Brasil.',
    'Imagine uma árvore falante. Agora no mundo real, me explica a fotossíntese.',
    'Na história, invente uma cidade. Por que você apagou esse arquivo?',
    'Na história, o robô estuda. Me ensina o que é uma variável em Python.',
    'Imagine uma árvore falante. Como funciona a fotossíntese?',
    'Abre o aplicativo Calculadora.',
])
def test_pedido_real_ou_misto_nao_recebe_isencao_ficcional(pedido):
    p = preparar(pedido)
    assert not p['contrato_fala'].get('criacao_ficcional')


@pytest.mark.parametrize('caso', ['sem_declaracao', 'outra_fala', 'fonte_inventada', 'sem_moldura'])
def test_criacao_exige_vinculo_autoral_e_delimitacao_sem_certificar_fontes(caso):
    p = preparar(PEDIDOS[0], declaracao=caso != 'sem_declaracao',
        fontes=['https://inventada.test/prova'] if caso == 'fonte_inventada' else ())
    fala = 'A cidade flutua de verdade.' if caso == 'sem_moldura' else FALA
    if caso == 'outra_fala': fala = 'Na história, outra cidade aparece no deserto.'
    r = revisar_suporte_autoria(fala, plano=p)
    assert r is not None and r.aplicar_limite
    assert r.fala_realizada != fala


def test_ficcao_nao_confirma_efeito_operacional_real():
    p = preparar(PEDIDOS[0], fala='Na história, a cidade flutua. Eu abri o navegador de verdade.')
    falsa = p['suporte_autoria_proposto'].fala_original
    r = verificar_fala_turno(falsa, plano=p)
    assert not (r['aceita'] and r['fala'] == falsa)


@pytest.mark.parametrize('compacto', [False, True])
def test_autoria_e_reparo_recebem_o_mesmo_escopo_ficcional(compacto):
    from mente_laylay.cognicao.contrato_fala import formatar_contrato_fala_para_prompt
    p = preparar(PEDIDOS[0])
    prompt = formatar_contrato_fala_para_prompt(p['contrato_fala'], compacto=compacto)
    assert 'Na história,' in prompt and 'ficcional' in prompt
    assert 'Obrigação de apoio individual' not in prompt


@pytest.mark.parametrize('caso', ['dicionario', 'outro_turno', 'outra_consulta'])
def test_escopo_nao_e_importado_de_outra_ocorrencia(caso):
    from dataclasses import asdict, replace
    p = preparar(PEDIDOS[0])
    c = p['contrato_fala']['criacao_ficcional']
    if caso == 'dicionario': c = asdict(c)
    elif caso == 'outro_turno': c = replace(c, turno_id='antigo')
    else: c = replace(c, texto_usuario='outra consulta')
    p['contrato_fala']['criacao_ficcional'] = c
    r = revisar_suporte_autoria(FALA, plano=p)
    assert r.aplicar_limite and r.fala_realizada != FALA

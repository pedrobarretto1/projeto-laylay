"""Proposição integral e partes de transporte têm limites distintos."""
import json

import pytest

from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.suporte_autoria import (
    exigir_suporte_no_pacote_autoral, conferir_suporte_proposicoes,
    capturar_suporte_autoria_obrigatoria, montar_autoria_revisada,
)
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt


def texto_longo(tamanho=850):
    texto = ' '.join(f'No trecho {i:02d}, a cidade guarda um detalhe diferente nas suas janelas.' for i in range(60))
    return texto[:tamanho].rsplit(' ', 1)[0] + '.'


def codec(referencias=()):
    return exigir_suporte_no_pacote_autoral(PacotePrompt(()), referencias_disponiveis=referencias).contrato_saida


@pytest.mark.parametrize('tamanho', [510, 850, 1500, 3400])
def test_proposicao_livre_e_transportada_integralmente_sem_corte(tamanho):
    texto = texto_longo(tamanho)
    c = codec()
    assert c.response_format['json_schema']['schema']['properties']['suporte_proposicoes']['items']['properties']['texto']['maxLength'] == 4000
    d = c.decodificar_json(json.dumps({'suporte_proposicoes':[{'texto':texto, 'fontes':[]}]}))
    assert d['fala'] == texto
    assert len(d['suporte_proposicoes']) == 1, 'transporte não inventa novas proposições'
    p = d['suporte_proposicoes'][0]
    assert 'texto' not in p and ' '.join(p['partes']) == texto
    assert 1 < len(p['partes']) <= 8 and all(0 < len(t) <= 500 for t in p['partes'])
    fala, declaracao = conferir_suporte_proposicoes(d)
    assert fala == texto and declaracao['proposicoes'][0]['texto'] == texto
    assert declaracao['proposicoes'][0]['intervalo'] == [0,len(texto)]
    s = capturar_suporte_autoria_obrigatoria(ContratoPropostaPrincipal('turno','pedido',json.dumps(d),True))
    assert s.fala_original == texto and s.declaracao.como_dict()['cobertura_textual']
    assert s.semantica_verificada is s.prova_implicacao is s.autoriza_execucao is False
    mescla = montar_autoria_revisada('principal', texto, (s,))
    assert mescla is not None and mescla.suporte_composto().fala_original == texto


@pytest.mark.parametrize('referenciada', [False, True])
def test_segmentacao_nao_muda_fontes_nem_ausencia_de_apoio(referenciada):
    url = 'https://fonte.test/observacao'
    texto = texto_longo()
    c = codec((url,))
    unidade = {'texto':texto,'fontes':[url]} if referenciada else {'texto':texto,'fontes':[], 'sem_fonte':'insuficiente'}
    d = c.decodificar_json(json.dumps({'suporte_proposicoes':[unidade]}))
    p = d['suporte_proposicoes'][0]
    assert p['fontes'] == unidade['fontes']
    assert p.get('sem_fonte') == unidade.get('sem_fonte')
    _, capturada = conferir_suporte_proposicoes(d)
    assert capturada['proposicoes'][0]['texto'] == texto
    assert capturada['proposicoes'][0]['fontes'] == unidade['fontes']


@pytest.mark.parametrize('caso', ['palavra_sem_fronteira', 'fala_total', 'partes_totais'])
def test_formato_inviavel_e_recusado_sem_cortar_ou_elevar_limites(caso):
    textos = ['x'*501] if caso == 'palavra_sem_fronteira' else [texto_longo(2500)]*2 if caso == 'fala_total' else [f'Unidade {i} '+texto_longo(530) for i in range(5)]
    with pytest.raises(ValueError):
        codec().decodificar_json(json.dumps({'suporte_proposicoes':[{'texto':t,'fontes':[]} for t in textos]}))


@pytest.mark.parametrize('caso', ['parte_longa','texto_e_partes','partes_vazias','tipo_invalido','fonte_invalida'])
def test_captura_de_partes_exige_forma_e_cobertura_integral(caso):
    p = {'partes':['Primeira frase.', 'Segunda frase.'], 'fontes':[]}
    if caso == 'parte_longa': p['partes'] = ['x'*501]
    elif caso == 'texto_e_partes': p['texto'] = 'Outra fala.'
    elif caso == 'partes_vazias': p['partes'] = []
    elif caso == 'tipo_invalido': p['partes'] = [True]
    else: p['fontes'] = [False]
    with pytest.raises(ValueError):
        conferir_suporte_proposicoes({'fala':'Primeira frase. Segunda frase.', 'suporte_proposicoes':[p]})


def test_texto_legado_nao_adquire_limite_de_transporte_maior():
    texto = texto_longo()
    with pytest.raises(ValueError):
        conferir_suporte_proposicoes({'fala':texto, 'suporte_proposicoes':[{'texto':texto,'fontes':[]}]})


def test_reaplicar_codec_na_recuperacao_nao_perde_representacao_nem_inventario():
    p = exigir_suporte_no_pacote_autoral(PacotePrompt(()),referencias_disponiveis=('https://fonte.test/a',))
    assert exigir_suporte_no_pacote_autoral(p) is p
    with pytest.raises(ValueError):
        exigir_suporte_no_pacote_autoral(p, referencias_disponiveis=('https://outra.test/a',))


@pytest.mark.parametrize('integral', [False, True])
def test_revisao_confere_proposicao_inteira_e_nao_aprova_fragmento_sem_ressalva(integral):
    from scripts.tests.test_integridade_trechos_autoria import fundamento_para, trecho_com_ressalva, URL
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    texto = trecho_com_ressalva(800)
    d = codec((URL,)).decodificar_json(json.dumps({'suporte_proposicoes':[{'texto':texto,'fontes':[URL]}]}))
    p = {'id':'turno','texto_usuario':'pedido', 'comandos':[],
        'fundamentacao_factual':fundamento_para(texto if integral else texto[:500]),
        'suporte_autoria_proposto':capturar_suporte_autoria_obrigatoria(
            ContratoPropostaPrincipal('turno','pedido',json.dumps(d),True))}
    r = revisar_suporte_autoria(texto, plano=p, agora=1001)
    props = r.como_dict()['proposicoes']
    assert len(props) == 1 and props[0]['texto'] == texto
    assert (props[0]['estado'] == 'literal_integral_na_fonte') is integral
    assert ('nem autoriza alteração.' in r.fala_realizada) is integral
    assert r.semantica_verificada is r.prova_implicacao is r.autoriza_execucao is False

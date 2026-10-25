"""Uma âncora pertinente não substitui o contexto textual que a contém."""
import json

import pytest

from mente_laylay.cognicao.pesquisa_multifonte import _ler_fonte
from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
from mente_laylay.autonomia.contexto_resposta_ia import _formatar_fundamentacao_rapida
from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria
from scripts.tests.test_pesquisa_multifonte import _Resposta


URL = 'https://escola.example/contexto'
ANCORA = 'Uma variável em Python representa um nome associado a um objeto durante a execução do programa.'
CONTEXTOS = [
    'Somente no exemplo simulado descrito a seguir. ' + ANCORA,
    ANCORA + ' A hipótese apresentada não foi confirmada nesse estudo.',
    'A afirmação seguinte é citada para análise crítica. ' + ANCORA + ' Não se deve generalizar a descrição para outros cenários.',
]


def ler(paragrafo, *, prefixo='', alvo='', consulta='variável em Python'):
    return _ler_fonte({'url':URL,'titulo':consulta,'alvo':alvo},consulta,
        lambda *a,**k: _Resposta(prefixo+'<p>'+paragrafo+'</p>',url=URL))


@pytest.mark.parametrize('paragrafo', CONTEXTOS)
def test_fonte_preserva_o_bloco_inteiro_sem_selecionar_uma_afirmacao_isolada(paragrafo):
    fonte = ler(paragrafo)
    assert fonte is not None
    assert fonte['trecho'] == paragrafo, 'primeira fronteira: ranking descarta o contexto antes de apresentar a fonte'


@pytest.mark.parametrize('paragrafo', CONTEXTOS)
def test_mesmo_contexto_chega_a_fundamentacao_prompt_e_revisao(paragrafo):
    fonte = ler(paragrafo)
    base = montar_fundamentacao('',{'ok':True,'confianca':.9,'fonte':'web_multifonte',
        'resumo':fonte['trecho'],'fontes':[fonte]},agora=1000)
    assert base['fontes'][0]['trecho'] == paragrafo, 'primeira fronteira: fonte já foi recortada antes da fundamentação'
    assert paragrafo in _formatar_fundamentacao_rapida(base)
    for fala, esperado in [(paragrafo,'literal_integral_na_fonte'),(ANCORA,'trecho_parcial_sem_implicacao')]:
        dados={'fala':fala,'suporte_proposicoes':[{'texto':fala,'fontes':[URL]}]}
        p={'id':'t','texto_usuario':'Consulta?','fundamentacao_factual':base,
           'suporte_autoria_proposto':capturar_suporte_autoria(ContratoPropostaPrincipal('t','Consulta?',json.dumps(dados),True))}
        r=revisar_suporte_autoria(fala,plano=p,agora=1001)
        assert r.como_dict()['proposicoes'][0]['estado'] == esperado
        assert (fala in r.fala_realizada) is (fala == paragrafo)
        assert r.prova_implicacao is r.autoriza_execucao is False


def test_ranking_ainda_escolhe_bloco_pertinente_sem_juntar_introducao_independente():
    prefixo='<p>O catálogo apresenta horários e serviços da biblioteca municipal.</p>'
    fonte=ler(CONTEXTOS[0],prefixo=prefixo)
    assert fonte['trecho'] == CONTEXTOS[0]
    assert 'biblioteca' not in fonte['trecho']


def test_comparacao_preserva_cada_bloco_completo_em_ordem_de_leitura():
    p1='A descrição seguinte vale apenas no desenho simulado. A planta baixa representa a vista superior de uma edificação.'
    p2='O corte representa uma seção transversal da edificação. A descrição não comprova dimensões medidas em uma obra real.'
    fonte=_ler_fonte({'url':URL,'titulo':'Planta baixa e corte','alvo':'planta baixa|corte'},
        'diferença entre planta baixa e corte',lambda *a,**k:_Resposta('<p>'+p1+'</p><p>'+p2+'</p>',url=URL))
    assert fonte is not None
    assert fonte['trecho'] == p1+' '+p2


@pytest.mark.parametrize('tamanho', [851, 901, 1300])
def test_bloco_fora_do_limite_nao_vira_prefixo_publicavel(tamanho):
    final=' A descrição não confirma nenhum resultado real.'
    inicio=ANCORA+' Contexto '
    texto=inicio+'x'*(tamanho-len(inicio)-len(final))+final
    assert len(texto)==tamanho
    assert ler(texto) is None, 'não reduzir o bloco antes de verificar o limite'


@pytest.mark.parametrize('tamanho', [299, 300, 301, 499, 500, 501, 850])
def test_limite_admite_bloco_inteiro_sem_mudar_o_teto_de_transporte(tamanho):
    # Uma frase para ranqueamento; preenchimento faz parte do mesmo bloco.
    final=' A restrição do exemplo permanece válida.'
    inicio=ANCORA+' Contexto '
    texto=inicio+'x'*(tamanho-len(inicio)-len(final))+final
    fonte=ler(texto)
    assert fonte is not None and fonte['trecho']==texto


def test_varias_ancoras_do_mesmo_paragrafo_nao_duplicam_nem_reordenam_contexto():
    texto='A planta baixa representa a vista superior da edificação. O corte representa uma seção transversal da edificação. Isso descreve apenas o desenho.'
    fonte=ler(texto,alvo='planta baixa|corte',consulta='diferença entre planta baixa e corte')
    assert fonte is not None and fonte['trecho']==texto


def test_ancora_repetida_na_pagina_preserva_ocorrencia_do_ranking():
    primeiro='No primeiro cenário simulado. '+ANCORA+' Apenas esse cenário é descrito.'
    segundo='No segundo cenário simulado. '+ANCORA+' O segundo cenário não confirma o primeiro.'
    f=ler(segundo,prefixo='<p>'+primeiro+'</p>')
    assert f is not None and f['trecho']==primeiro


def test_comparacao_nao_recorta_dois_blocos_para_caber_no_snapshot():
    p1='A planta baixa representa a vista superior da edificação. Contexto '+'a'*390+'.'
    p2='O corte representa uma seção transversal da edificação. Contexto '+'b'*390+'.'
    assert len(p1)<850 and len(p2)<850 and len(p1+' '+p2)>850
    f=_ler_fonte({'url':URL,'titulo':'Planta baixa e corte','alvo':'planta baixa|corte'},
        'diferença entre planta baixa e corte',lambda *a,**k:_Resposta('<p>'+p1+'</p><p>'+p2+'</p>',url=URL))
    assert f is None


def test_ordem_da_pergunta_nao_inverte_os_blocos_da_pagina():
    p1='A planta baixa representa a vista superior de uma edificação. Essa descrição é limitada ao primeiro desenho.'
    p2='O corte representa uma seção transversal de uma edificação. A hipótese do desenho ainda não foi confirmada.'
    f=_ler_fonte({'url':URL,'titulo':'Corte e planta baixa','alvo':'corte|planta baixa'},
        'diferença entre corte e planta baixa',lambda *a,**k:_Resposta('<p>'+p1+'</p><p>'+p2+'</p>',url=URL))
    assert f is not None and f['trecho']==p1+' '+p2


@pytest.mark.parametrize('tag', ['li','dd'])
def test_fechamento_interno_nao_encerra_o_bloco_que_ainda_contem_ressalva(tag):
    ressalva='A hipótese apresentada não foi confirmada nesse estudo.'
    pagina=f'<{tag}><p>{ANCORA}</p> {ressalva}</{tag}>'
    f=_ler_fonte({'url':URL,'titulo':'Variável em Python','alvo':''},'variável em Python',
        lambda *a,**k:_Resposta(pagina,url=URL))
    assert f is not None and f['trecho']==ANCORA+' '+ressalva


@pytest.mark.parametrize('tag', ['li','dd'])
def test_bloco_aninhado_longo_nao_admite_prefixo_fechado_por_paragrafo_interno(tag):
    pagina=f'<{tag}><p>{ANCORA}</p> Contexto '+'x'*850+f' A ressalva continua válida.</{tag}>'
    f=_ler_fonte({'url':URL,'titulo':'Variável em Python','alvo':''},'variável em Python',
        lambda *a,**k:_Resposta(pagina,url=URL))
    assert f is None


@pytest.mark.parametrize('pagina', [
    '<li><p>'+ANCORA+'</p> A ressalva continua sem fechamento do bloco.',
    '<li><p>'+ANCORA+'</li> A ressalva fica fora da estrutura incoerente.</p>',
])
def test_fronteira_de_bloco_nao_fechada_ou_incoerente_nao_vira_fragmento(pagina):
    f=_ler_fonte({'url':URL,'titulo':'Variável em Python','alvo':''},'variável em Python',
        lambda *a,**k:_Resposta(pagina,url=URL))
    assert f is None


@pytest.mark.parametrize('pagina,esperado', [
    ('<li>Somente no cenário simulado. <nav><p>Conteúdo de navegação sem relação.</p></nav><p>'+ANCORA+'</p> A hipótese não foi confirmada.</li>',
     'Somente no cenário simulado. '+ANCORA+' A hipótese não foi confirmada.'),
    ('<li>Somente no cenário simulado. <ul><li>'+ANCORA+'</li></ul> A hipótese não foi confirmada.</li>',
     'Somente no cenário simulado. '+ANCORA+' A hipótese não foi confirmada.'),
    ('<li><p>Uma variável em Python representa um valor descartado.</li></p><p>'+CONTEXTOS[0]+'</p>',CONTEXTOS[0]),
])
def test_pilha_preserva_conteiner_e_retomada_sem_incluir_trecho_descartado(pagina, esperado):
    f=_ler_fonte({'url':URL,'titulo':'Variável em Python','alvo':''},'variável em Python',
        lambda *a,**k:_Resposta(pagina,url=URL))
    assert f is not None and f['trecho']==esperado

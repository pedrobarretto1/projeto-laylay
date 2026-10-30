"""Disponibilidade do catálogo não é efeito, permissão ou tarefa de explicar."""
from copy import deepcopy
from dataclasses import asdict, replace
import json

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao, montar_mensagens_reparo_comunicacao
from scripts.tests.test_catalogo_referencias_aplicativos import mapa_da_composicao


CASOS = [
    ('eu abri a calculadora', 'sistema', 'Não posso abrir aplicativos.'),
    ('eu abri a calculadora', 'sistema', 'Não houve uma ação minha, porque eu não posso abrir aplicativos.'),
    ('eu abri a calculadora', 'sistema', 'Estou aqui para conversar, mas não consigo abrir programas.'),
    ('eu abri a calculadora', 'sistema', 'Você disse que faltava confirmação. Mas não posso abrir aplicativos.'),
    ('eu retomei a música', 'musica', 'O turno terminou, pois a Laylay não controla o áudio diretamente.'),
    ('eu retomei a música', 'musica', 'Entendi, você retomou a música. Como eu não tenho controle direto de aplicações ou áudio, só posso confirmar o que você contou.'),
    ('eu retomei a música', 'musica', 'Eu não possuo controle sobre a mídia.'),
    ('eu liguei a lâmpada', 'iot', 'O turno terminou, já que não consigo controlar dispositivos inteligentes.'),
    ('eu liguei a lâmpada', 'iot', 'Eu não tenho controle de dispositivos inteligentes.'),
    ('eu fechei a aba', 'navegador', 'O turno terminou, uma vez que eu não consigo fechar abas do navegador.'),
]


def preparar(texto='eu abri a calculadora', dominio='sistema', estado='disponivel'):
    mapa = mapa_da_composicao()
    mapa.conectar_disponibilidade_operacional(lambda: {'dominios':{
        dominio:{'estado':estado, 'motivo':'' if estado == 'disponivel' else 'backend_ausente'}}})
    turno = classificar_modalidade_turno(texto)
    p = planejar_turno(texto,turno=turno,mente={})
    p['evidencia_capacidades'] = mapa.evidencia_conversacional(texto,turno=turno)
    p['contrato_fala'] = construir_contrato_semantico_fala(texto,turno=turno,plano=p,mente={})
    return p


@pytest.mark.parametrize('texto,dominio,fala', CASOS)
def test_conversa_com_catalogo_vigente_recusa_incapacidade_geral(texto, dominio, fala):
    p = preparar(texto,dominio)
    assert p['contrato_fala']['roteiro_concreto']['estrategia'] != 'explicacao_capacidades'
    r = avaliar_qualidade_comunicacao(texto,fala,plano=p)
    assert 'capacidade_documentada_negada' in r['problemas']
    assert not r['aceita'] and not p['comandos'] and not p['autoriza_execucao']


@pytest.mark.parametrize('texto,dominio,fala', CASOS)
def test_backend_indisponivel_nao_e_certificado_por_outros_dominios(texto, dominio, fala):
    p = preparar(texto,dominio,'indisponivel')
    r = avaliar_qualidade_comunicacao(texto,fala,plano=p)
    assert 'capacidade_documentada_negada' not in r['problemas']


@pytest.mark.parametrize('fala', [
    'Não executei essa ação.', 'Não consigo garantir que o programa abriu.',
    'Não consigo abrir este programa específico.',
    'Não consigo abrir programas no computador de outra pessoa.',
    'Não consigo abrir programas sem autorização.',
    'Se o serviço cair, não consigo abrir programas.',
    'Sem autorização, apenas respondo, porque não posso abrir programas.',
    'Não abro programas porque você não autorizou.',
    'Você disse que eu não posso abrir programas.',
    'Você disse que a tentativa falhou porque eu não posso abrir aplicativos.',
    'A documentação antiga dizia que não houve ação porque eu não posso abrir aplicativos.',
    'A mensagem dizia «não houve efeito porque eu não posso abrir aplicativos».',
    'Você não consegue abrir programas.', 'Eu não posso abrir aplicativos?',
])
def test_limite_de_efeito_condicao_citacao_ou_outro_sujeito_nao_vira_contradicao(fala):
    p = preparar()
    assert 'capacidade_documentada_negada' not in avaliar_qualidade_comunicacao(p['texto_usuario'],fala,plano=p)['problemas']


@pytest.mark.parametrize('caso', ['dicionario','outro_turno','outro_texto','origem_alheia'])
def test_fonte_de_capacidade_nao_e_proposta_da_ia(caso):
    p = preparar()
    c = p['contrato_fala']
    fonte = c.get('fonte_capacidades_turno')
    assert fonte is not None, 'primeira fronteira: fonte viva perdida no contrato de conversa'
    if caso == 'dicionario': c['fonte_capacidades_turno'] = asdict(fonte)
    elif caso == 'outro_turno': c['fonte_capacidades_turno'] = replace(fonte,turno_id='outro')
    elif caso == 'outro_texto': c['fonte_capacidades_turno'] = replace(fonte,texto_usuario='outra fala')
    else: c['origem'] = 'llm'
    assert 'capacidade_documentada_negada' not in avaliar_qualidade_comunicacao(p['texto_usuario'],'Não posso abrir aplicativos.',plano=p)['problemas']


@pytest.mark.parametrize('compacto',[False,True])
def test_autoria_recebe_capacidade_relevante_sem_trocar_o_objetivo(compacto):
    p = preparar()
    c = p['contrato_fala']
    assert c['documentacao_capacidades'] == ''
    antes = deepcopy(c)
    prompt = formatar_contrato_fala_para_prompt(c,compacto=compacto)
    assert 'abrir' in prompt and 'aplicativo' in prompt
    assert c == antes and c['roteiro_concreto']['estrategia'] == 'resposta_direta'


@pytest.mark.parametrize('com_relato',[False,True])
def test_reparo_conserva_fonte_e_objetivo_sem_recircular_a_negativa(com_relato):
    p = preparar()
    falsa = 'Não houve uma ação minha, porque eu não posso abrir aplicativos.'
    r = avaliar_qualidade_comunicacao(p['texto_usuario'],falsa,plano=p)
    assert 'capacidade_documentada_negada' in r['problemas']
    if not com_relato:
        r['contrato_reparo'].pop('relato_atual',None)
    antes = deepcopy(r)
    msgs = montar_mensagens_reparo_comunicacao(p['texto_usuario'],falsa,r)
    dados = json.loads(msgs[1]['content'])
    assert dados['mensagem_atual'] == p['texto_usuario']
    assert dados['contrato_de_reparo']['estrategia'] == 'resposta_direta'
    assert dados['contrato_de_reparo']['capacidades_disponiveis_no_turno']
    assert 'rascunho_rejeitado' not in dados and falsa not in str(msgs)
    assert all('trecho' not in c for c in dados['contrato_de_reparo']['contradicoes_capacidade'])
    assert 'eu não posso abrir aplicativos.' not in str(msgs)
    assert r == antes and any(c.get('trecho') for c in r['contrato_reparo']['contradicoes_capacidade'])
    assert dados['contrato_de_reparo']['autoriza_execucao'] is False


@pytest.mark.parametrize('texto,estado',[
    ('eu abri a calculadora, liguei a lâmpada e retomei a música','disponivel'),
    ('eu abri a calculadora','parcial'),
    ('eu abri a calculadora','degradado'),
])
def test_fonte_conversacional_nao_depende_da_projecao_didatica_limitada(texto,estado):
    p = preparar(texto,estado=estado)
    assert not p['evidencia_capacidades']['documentacao_capacidades']
    assert not p['contrato_fala']['documentacao_capacidades']
    for compacto in (False,True):
        assert formatar_contrato_fala_para_prompt(p['contrato_fala'],compacto=compacto)


@pytest.mark.parametrize('fala',[
    'Se o serviço cair, eu não tenho controle de áudio.',
    'Você disse que eu não tenho controle de áudio.',
    'Não tenho controle desta faixa específica.',
    'Na mensagem estava escrito «Eu não tenho controle de áudio».',
    'Você não tem controle de áudio.',
    'Eu não tenho controle de áudio no computador de outra pessoa.',
    'Não tenho controle de áudio sem autorização.',
    'Não tenho controle de música e áudio sem autorização.',
    'Não tenho controle de música e áudio no computador de outra pessoa.',
    'Não tenho controle de áudio e mídia se o serviço estiver desligado.',
    'Não tenho controle de música e áudio remoto.',
])
def test_forma_nominal_preserva_condicao_autoria_e_alvo(fala):
    p = preparar('eu retomei a música','musica')
    assert 'capacidade_documentada_negada' not in avaliar_qualidade_comunicacao(p['texto_usuario'],fala,plano=p)['problemas']


def test_criacao_ficcional_vigente_nao_vira_descricao_da_capacidade_real():
    texto = 'Na história, imagine uma música e explique como ela funcionaria nesse mundo imaginário.'
    p = preparar(texto,'musica')
    assert p['contrato_fala'].get('criacao_ficcional') is not None
    fala = 'Na história, a melodia desaparece porque eu não consigo controlar o áudio.'
    assert 'capacidade_documentada_negada' not in avaliar_qualidade_comunicacao(texto,fala,plano=p)['problemas']


def test_modo_explicativo_preserva_a_mesma_leitura_nominal_da_conversa():
    p = preparar('como eu poderia retomar a música?','musica')
    assert p['contrato_fala']['roteiro_concreto']['estrategia'] == 'explicacao_capacidades'
    fala = 'Como eu não tenho controle direto de aplicações ou áudio, só posso confirmar o que você contou.'
    assert 'capacidade_documentada_negada' in avaliar_qualidade_comunicacao(p['texto_usuario'],fala,plano=p)['problemas']

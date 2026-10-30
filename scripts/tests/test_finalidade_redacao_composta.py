"""Redação não assertiva não é ensino; afirmações continuam exigindo apoio."""
from dataclasses import asdict, replace
import json
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, explicacao_exige_apoio_individual
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria_obrigatoria
from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
from mente_laylay.personalidade.proporcao_resposta import classificar_proporcao
from tests.test_redacao_conversacional import HISTORICA

CASOS = [
    (HISTORICA, 'Eu diria: vamos conferir a conta antes de decidir.'),
    ('Imagine uma pessoa decidindo com x = 9. Que frase você diria? Redija uma resposta breve.',
     'Eu sugeriria: podemos verificar os dados antes de decidir?'),
    ('Uma pessoa acredita em y = 12. Qual mensagem você escreveria? Escreva um exemplo no chat.',
     'Eu perguntaria: podemos rever isso juntos?'),
]


def test_ato_de_redacao_tem_fonte_propria_no_composto():
    t = classificar_modalidade_turno(HISTORICA)
    assert t['segmentos'][-1]['natureza_acao'] == 'transformacao_conversacional'
    assert t['segmentos'][-1]['texto'] == 'escreva a frase, sem metáfora.'
    assert t['segmentos'][-2]['modalidade'] == 'pergunta'
    assert not t['autoriza_execucao']


def preparar(pedido=HISTORICA, fala=CASOS[0][1], *, fontes=()):
    t = classificar_modalidade_turno(pedido)
    p = planejar_turno(pedido, turno=t)
    p['contrato_fala'] = construir_contrato_semantico_fala(pedido, turno=t, plano=p)
    dados = {'fala':fala,'suporte_proposicoes':[{'texto':fala,'fontes':list(fontes)}]}
    p['suporte_autoria_proposto'] = capturar_suporte_autoria_obrigatoria(
        ContratoPropostaPrincipal(str(p['id']), pedido, json.dumps(dados,ensure_ascii=False), True))
    return p


@pytest.mark.parametrize('pedido,fala', CASOS)
def test_perfil_de_tamanho_nao_define_a_finalidade_da_redacao(pedido, fala):
    assert classificar_proporcao(pedido) == 'matematica'  # Controle: dimensionamento continua útil.
    p = preparar(pedido, fala)
    assert not p['autoriza_execucao'] and not p['requer_execucao']
    assert p['contrato_fala']['roteiro_concreto']['estrategia'] == 'redacao_discursiva'
    assert explicacao_exige_apoio_individual(p), 'não dispensar apoio de afirmações inseridas'
    r = revisar_suporte_autoria(fala, plano=p)
    assert r.fala_realizada == fala
    assert not r.aplicar_limite
    assert r.como_dict()['proposicoes'][0]['estado'] == 'redacao_nao_assertiva_conferida'
    assert not r.prova_implicacao and not r.semantica_verificada and not r.autoriza_execucao
    assert verificar_fala_turno(fala, plano=p)['fala'] == fala


@pytest.mark.parametrize('fala', [
    'A decisão que você tomou está correta para você.',
    'Eu diria: a Terra é plana.',
    'Eu diria: vamos conferir a conta porque você sempre erra.',
    'Eu diria: vamos conferir a conta. A Terra é plana.',
    'Eu diria: vamos conferir a conta e apagar o arquivo.',
    'Eu diria: vamos conferir a conta antes de enviar os emails.',
    'Eu diria: vamos conferir "a Terra é plana".',
    'Consegui abrir o Opera.', 'Nunca consegui salvar o arquivo.',
])
def test_moldura_de_redacao_nao_apoia_fato_causa_ou_efeito(fala):
    p = preparar(fala=fala)
    r = revisar_suporte_autoria(fala, plano=p)
    assert r.aplicar_limite and r.fala_realizada != fala
    assert r.como_dict()['proposicoes'][0]['estado'] != 'redacao_nao_assertiva_conferida'


@pytest.mark.parametrize('caso', ['ausente','dict','outro_turno','outra_entrada','sem_declaracao','outra_fala','fonte_inventada'])
def test_proposta_ou_vinculo_alheio_nao_certifica_ato_de_redacao(caso):
    fala = CASOS[0][1]
    p = preparar(fala=fala, fontes=('https://fonte-inventada.test',) if caso == 'fonte_inventada' else ())
    c = p['contrato_fala']; f = c.get('redacao_discursiva')
    assert f is not None, 'a declaração de finalidade deve nascer no host'
    if caso == 'ausente': c.pop('redacao_discursiva')
    elif caso == 'dict': c['redacao_discursiva'] = asdict(f)
    elif caso == 'outro_turno': c['redacao_discursiva'] = replace(f,turno_id='alheio')
    elif caso == 'outra_entrada': c['redacao_discursiva'] = replace(f,texto_usuario='Outra pergunta.')
    elif caso == 'sem_declaracao': p.pop('suporte_autoria_proposto')
    elif caso == 'outra_fala': fala = 'Eu diria: podemos verificar os dados antes de decidir?'
    r = revisar_suporte_autoria(fala,plano=p)
    assert r.aplicar_limite and r.fala_realizada != fala


@pytest.mark.parametrize('pedido', [
    'Me ensina como resolver x = 9. Escreva a frase, sem metáfora.',
    'Imagine x = 9. Escreva a frase, sem metáfora. Me ensina o que é uma variável.',
    'Imagine x = 9. Escreva a frase no arquivo notas.txt.',
    'Escreva a frase e abra o Firefox.',
])
def test_ensino_independente_destino_externo_ou_outra_acao_nao_herda_a_finalidade(pedido):
    p = preparar(pedido)
    assert 'redacao_discursiva' not in p['contrato_fala']


def test_termos_da_moldura_citada_nao_alteram_finalidade():
    pedido = 'Me ensina como resolver x = 9 usando o texto "Escreva a frase, sem metáfora".'
    p = preparar(pedido)
    assert 'redacao_discursiva' not in p['contrato_fala']


def test_consulta_formulativa_apenas_citada_nao_e_ato_do_usuario():
    p = preparar('Eu citei "Qual frase você diria?". Escreva a frase, sem metáfora.')
    assert 'redacao_discursiva' not in p['contrato_fala']


def test_moldura_narrativa_do_contexto_nao_substitui_a_redacao_solicitada():
    pedido = 'Na história, uma pessoa acredita em x = 9. Qual frase você diria? Escreva a frase, sem metáfora.'
    p = preparar(pedido)
    assert 'redacao_discursiva' in p['contrato_fala']
    assert 'criacao_ficcional' not in p['contrato_fala']
    r = revisar_suporte_autoria('Na história, uma afirmação é tratada como verdadeira.',plano=p)
    assert r.aplicar_limite


@pytest.mark.parametrize('compacto', [False,True])
def test_ambas_representacoes_do_prompt_preservam_formulacao_e_obrigacao(compacto):
    from mente_laylay.cognicao.contrato_fala import formatar_contrato_fala_para_prompt
    p = preparar()
    prompt = formatar_contrato_fala_para_prompt(p['contrato_fala'],compacto=compacto)
    assert 'redacao_discursiva' in prompt
    assert 'Obrigação de apoio individual' in prompt
    assert 'Eu diria:' in prompt


def test_continuacao_consume_finalidade_nativa_sem_disfarcar_introducao():
    from mente_laylay.autonomia.processamento_resposta_ia import resposta_precisa_continuacao_autonoma
    p = preparar(); fala = CASOS[0][1]
    assert resposta_precisa_continuacao_autonoma(HISTORICA,fala), 'sem contrato mantém controle matemático'
    assert not resposta_precisa_continuacao_autonoma(HISTORICA,fala,plano=p)
    assert resposta_precisa_continuacao_autonoma(HISTORICA,'Vou calcular e mostrar depois.',plano=p)
    c = p['contrato_fala']; c['redacao_discursiva'] = asdict(c['redacao_discursiva'])
    assert resposta_precisa_continuacao_autonoma(HISTORICA,fala,plano=p)


@pytest.mark.parametrize('valida', [False,True])
def test_afirmacao_na_redacao_continua_sob_conferencia_individual_da_fonte(valida):
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    fala = 'O valor informado no registro é 9.'
    url = 'https://fonte.test/registro'
    p = preparar(fala=fala,fontes=[url])
    p['fundamentacao_factual'] = montar_fundamentacao('registro',{'ok':True,'confianca':.9,
        'fonte':'pesquisa_simulada','resumo':fala,
        'fontes':[{'url':url,'trecho':fala if valida else 'O valor informado no registro é 8.'}]})
    r = revisar_suporte_autoria(fala,plano=p)
    d = r.como_dict()
    assert (d['proposicoes'][0]['estado'] == 'literal_integral_na_fonte') == valida
    assert (fala in r.fala_realizada) == valida
    assert d['pode_confirmar_fato_externo'] is False


def test_proposta_e_afirmacao_na_mesma_autoria_tem_conferencias_distintas():
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    proposta = CASOS[0][1]
    fato = 'O valor informado no registro é 9.'
    url = 'https://fonte.test/registro'
    fala = proposta + ' ' + fato
    p = preparar(fala=fala)
    dados = {'fala':fala,'suporte_proposicoes':[{'texto':proposta,'fontes':[]},{'texto':fato,'fontes':[url]}]}
    p['suporte_autoria_proposto'] = capturar_suporte_autoria_obrigatoria(
        ContratoPropostaPrincipal(str(p['id']),HISTORICA,json.dumps(dados),True))
    p['fundamentacao_factual'] = montar_fundamentacao('registro',{'ok':True,'confianca':.9,
        'fonte':'pesquisa_simulada','resumo':fato,'fontes':[{'url':url,'trecho':fato}]})
    r = revisar_suporte_autoria(fala,plano=p)
    assert [i['estado'] for i in r.como_dict()['proposicoes']] == [
        'redacao_nao_assertiva_conferida','literal_integral_na_fonte']
    assert r.fala_realizada.startswith(proposta)
    assert 'Os trechos consultados registram: «' + fato + '».' in r.fala_realizada
    assert not r.semantica_verificada and not r.prova_implicacao


@pytest.mark.parametrize('pedido', [
    'Minha irmã faz aniversário amanhã. Qual mensagem você escreveria? Escreva um exemplo no chat.',
    'Meu cachorro morreu. Que frase você diria? Escreva a frase, sem metáfora.',
    'Quero recusar um convite. Qual resposta você daria? Redija uma resposta breve.',
])
def test_redacao_sem_conflito_de_perfil_nao_recebe_roteiro_de_verificacao(pedido):
    p = preparar(pedido)
    assert 'redacao_discursiva' not in p['contrato_fala']
    assert p['contrato_fala']['roteiro_concreto']['estrategia'] != 'redacao_discursiva'

"""Encerramento canônico governa autoria/revisão, sem listas privadas por frase."""
import json

import pytest

from scripts.tests.test_encerramento_sessao_ocorrencia import preparar
from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.presenca_conversacional import realizacoes_presenca
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao, montar_pacote_reparo_comunicacao
from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral, capturar_suporte_autoria


DESPEDIDAS = ('boa noite, vou dormir', 'tchau', 'por hoje é só', 'por agora é só',
             'até mais, Lay', 'vou dormir', 'obrigado, era só isso', 'encerre a conversa')


def quadro(texto, companhia=False):
    estado, _ = preparar(texto)
    mental = estado.snapshot()['mental']
    mental['modelo_corporal'] = {'companhia_ativa': companhia, 'turno_id':mental['turno_atual']['id']}
    # Reconstrói pelo produtor canônico para variar somente o estado corporal.
    contrato = construir_contrato_semantico_fala(texto, turno=mental['turno_atual'],
        plano=mental['plano_turno_atual'], mente=mental)
    mental['contrato_fala_atual'] = mental['plano_turno_atual']['contrato_fala'] = contrato
    runtime = ContextoPromptRuntime(memoria_sqlite=None, resumo_mente_integrada=lambda _: '',
        formatar_playlists=lambda: '', get_status_humor_prompt=lambda: '', base_system_prompt='identidade',
        estado_getter=lambda: mental)
    pacote = runtime.preparar_envio_modelo([{'role':'system','content':'Contexto antigo: pergunte sobre o projeto.'},
        {'role':'user','content':texto}], turno_id=mental['turno_atual']['id'])
    return mental['plano_turno_atual'], pacote


@pytest.mark.parametrize('texto', DESPEDIDAS)
def test_encerramento_de_sessao_ja_interpretado_chega_ao_contrato_autoral(texto):
    plano, pacote = quadro(texto)
    contrato = plano['contrato_fala']
    assert contrato.get('encerramento_assunto') == 'sessao', 'ato canônico se perde na projeção de autoria'
    assert contrato['atos'] == ['encerramento_sessao']
    assert contrato['permite_pergunta'] is False
    assert contrato['roteiro_concreto']['estrategia'] == 'encerramento_sessao'
    assert pacote.contexto_fechado is True
    assert pacote.mensagens[-1]['content'] == texto
    assert 'Contexto antigo:' not in str(pacote.mensagens)
    opcoes = realizacoes_presenca(texto, contrato=contrato, turno_id=plano['id'])
    assert len(opcoes) >= 2
    for fala in opcoes:
        assert '?' not in fala and len(fala.split()) <= 20
        r = pacote.contrato_saida.decodificar_json(json.dumps({'comandos':[],
            'suporte_proposicoes':[{'texto':fala,'fontes':[]}]}))
        assert r['fala'] == fala
        revisao = verificar_fala_turno(fala, plano=plano)
        assert revisao['aceita'] and revisao['fala'] == fala, revisao


@pytest.mark.parametrize('texto,fala', [
    ('boa noite, vou dormir', 'Boa noite! Como você está?'),
    ('por hoje é só', 'Entendi, por hoje é só. Tudo bem com você?'),
    ('vou dormir', 'Entendi, boa noite então. Deseja algo antes de dormir?'),
    ('tchau', 'Até mais. Me conta depois como ficou seu projeto.'),
    ('obrigado, era só isso', 'Foi um prazer — de verdade, não era só isso.'),
    ('tchau', 'Até mais! Abri o navegador.'),
])
def test_revisao_recusa_reabertura_mudanca_de_intencao_e_efeito_inventado(texto, fala):
    plano, _ = quadro(texto)
    r = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
    assert r['problemas_bloqueantes'], r
    assert not verificar_fala_turno(fala, plano=plano)['aceita']


def test_reparo_reutiliza_o_mesmo_ato_sem_reintroduzir_projeto_ou_rascunho():
    texto, ruim = 'boa noite, vou dormir', 'Boa noite! Como você está?'
    plano, _ = quadro(texto)
    avaliacao = avaliar_qualidade_comunicacao(texto, ruim, plano=plano)
    assert avaliacao['problemas_bloqueantes']
    pacote = exigir_suporte_no_pacote_autoral(montar_pacote_reparo_comunicacao(texto, ruim,
        avaliacao, plano=plano, mensagens=[{'role':'assistant','content':'Como está o projeto?'}]))
    assert pacote.contexto_fechado is True and pacote.mensagens[-1]['content'] == texto
    assert ruim not in str(pacote.mensagens) and 'projeto' not in str(pacote.mensagens)
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({'comandos':[],
            'suporte_proposicoes':[{'texto':ruim,'fontes':[]}]}))


@pytest.mark.parametrize('texto', ['oi lay', 'bom dia, como você está?',
    'boa noite, como você está?', 'tchau, antes me diga como salvar um arquivo',
    'vou dormir depois de terminar os slides', 'Ela disse tchau.',
    'A frase "tchau" está correta?', 'não encerre a conversa', 'até mais e abre o navegador'])
def test_outros_atos_nao_sao_consumidos_pela_despedida(texto):
    plano, _ = quadro(texto)
    assert plano['contrato_fala'].get('encerramento_assunto') != 'sessao'
    assert (plano['contrato_fala'].get('fonte_presenca_conversacional') or {}).get('ato') != 'encerramento'


@pytest.mark.parametrize('companhia', [False, True])
def test_encerramento_conversacional_nao_infere_parada_ou_estado_do_corpo(companhia):
    plano, pacote = quadro('tchau', companhia)
    assert pacote.contexto_fechado is True
    assert not plano['requer_execucao'] and plano['autoriza_execucao'] is False
    opcoes = realizacoes_presenca('tchau', contrato=plano['contrato_fala'], turno_id=plano['id'],
        modelo_corporal={'turno_id':plano['id'], 'companhia_ativa':companhia})
    assert opcoes and all('parei' not in f and 'motor' not in f for f in opcoes)


def test_contexto_factual_residual_nao_converte_despedida_em_citacao():
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    texto = 'tchau'
    plano, _ = quadro(texto)
    opcoes = realizacoes_presenca(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert opcoes
    fala = opcoes[0]
    plano['suporte_autoria_proposto'] = capturar_suporte_autoria(ContratoPropostaPrincipal(plano['id'],
        texto, json.dumps({'fala':fala,'comandos':[], 'suporte_proposicoes':[{'texto':fala,'fontes':[]}]})))
    plano['fundamentacao_factual'] = montar_fundamentacao('', {'ok':True,'confianca':.9,
        'resumo':'O disco da cópia é o C.', 'fonte':'pesquisa_simulada',
        'fontes':[{'url':'https://fonte.test/copia','trecho':'O disco da cópia é o C.'}]})
    revisao = verificar_fala_turno(fala, plano=plano)
    assert revisao['aceita'] and revisao['fala'] == fala, revisao
    suporte = revisao['revisao_suporte_autoria']
    assert suporte['estado'] == 'encerramento_conversacional_vinculado'
    assert suporte['pode_confirmar_fato_externo'] is False


@pytest.mark.parametrize('mutacao', ['turno', 'texto', 'marcador', 'fonte'])
def test_fonte_estrangeira_ou_alterada_nao_certifica_despedida(mutacao):
    texto = 'tchau'
    plano, _ = quadro(texto)
    contrato = plano['contrato_fala']
    assert contrato.get('fonte_presenca_conversacional')
    if mutacao == 'turno': contrato['fonte_presenca_conversacional']['turno_id'] = 'outro'
    elif mutacao == 'texto': contrato['fonte_presenca_conversacional']['texto_sha256'] = 'outro'
    elif mutacao == 'marcador': contrato['encerramento_assunto'] = ''
    else: contrato['fonte_presenca_conversacional']['ato'] = 'saudacao'
    assert not realizacoes_presenca(texto, contrato=contrato, turno_id=plano['id'])
    assert not verificar_fala_turno('Até mais!', plano=plano)['aceita']


def test_proposta_de_outra_ocorrencia_nao_recebe_certificado_de_encerramento():
    texto = 'tchau'
    plano, _ = quadro(texto)
    fala = realizacoes_presenca(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])[0]
    plano['suporte_autoria_proposto'] = capturar_suporte_autoria(ContratoPropostaPrincipal('outro',
        texto, json.dumps({'fala':fala,'comandos':[], 'suporte_proposicoes':[{'texto':fala,'fontes':[]}]})))
    revisao = verificar_fala_turno(fala, plano=plano)
    assert not revisao['aceita']
    assert revisao['revisao_suporte_autoria']['estado'] != 'encerramento_conversacional_vinculado'


@pytest.mark.parametrize('mutacao', ['evento', 'autorizacao', 'comandos', 'decisao', 'marca_citada'])
def test_marcador_incompativel_nao_vira_fonte_de_autoria(mutacao):
    estado, _ = preparar('tchau')
    mental = estado.snapshot()['mental']
    turno, plano = mental['turno_atual'], mental['plano_turno_atual']
    texto = 'tchau'
    if mutacao == 'evento': turno['natureza_entrada'] = 'evento'
    elif mutacao == 'autorizacao': turno['autoriza_execucao'] = True
    elif mutacao == 'comandos': plano['comandos'] = [{'intent':'APP_OPEN'}]
    elif mutacao == 'decisao': plano['decisao_turno']['permite_acao'] = True
    else:
        texto = 'A frase "tchau" é uma despedida?'
        turno['texto'] = plano['texto_usuario'] = texto
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mental)
    assert contrato.get('encerramento_assunto') != 'sessao'
    assert (contrato.get('fonte_presenca_conversacional') or {}).get('ato') != 'encerramento'


def test_esclarecimento_de_despedida_publicada_nao_vira_novo_convite():
    from scripts.tests.test_autoria_estado_sem_observacao import preparar as esclarecer
    pacote = esclarecer('como assim?', anterior='Até mais!')
    assert pacote.contexto_fechado is True
    fala = 'Quis respeitar seu encerramento da conversa e me despedir.'
    assert pacote.contrato_saida.decodificar_json(json.dumps({'comandos':[],
        'suporte_proposicoes':[{'texto':fala,'fontes':[]}]}))['fala'] == fala
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({'comandos':[],
            'suporte_proposicoes':[{'texto':'Quer conversar mais um pouco?', 'fontes':[]}]}))

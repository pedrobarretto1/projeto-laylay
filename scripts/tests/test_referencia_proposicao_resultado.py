"""Uma referência nominal não pode virar a última alegação por omissão."""
from copy import deepcopy
from dataclasses import asdict, replace
import os
import pytest

from mente_laylay.memoria_mental.registro_semantico import (
    contestar_alegacao_recente, selecionar_alegacao_para_revisao,
    registrar_fala_observada, recuperar_revisao_alegacao, registrar_alegacao,
    avaliar_suporte_alegacao,
)
from scripts.tests.test_revisao_comparacao_resultado import publicar_resultado


@pytest.mark.parametrize('expressao,papel', [('esse valor',None),('essa meta','meta'),
    ('essa medição','medicao'),('essa diferença','comparacao')])
def test_referencia_nominal_respeita_papel_e_unicidade_da_entrega(expressao,papel,monkeypatch):
    _,reg=publicar_resultado()
    props={i['vinculo_resultado']['tipo']:i for i in reg['alegacoes']}
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:105)
    selecao=selecionar_alegacao_para_revisao(reg,'De onde você tirou '+expressao+'?')
    if papel is None:
        assert selecao['referencia']=='ambigua' and not selecao['alegacao_id']
    else:
        assert selecao['referencia']=='unica' and selecao['alegacao_id']==props[papel]['id']


@pytest.fixture(scope='module')
def referencia_instalada(tmp_path_factory):
    from scripts.tests.test_revisao_comparacao_historica import revisao_historica_instalada
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_REFERENCIA_PROPOSICAO','1')
        if pasta:=os.environ.get('LAYLAY_EVIDENCIA_REFERENCIA_PROPOSICAO'):
            ambiente.setenv('LAYLAY_EVIDENCIA_REVISAO_HISTORICA',pasta)
        return revisao_historica_instalada.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('papel',['valor','meta','medicao','comparacao'])
def test_seletor_instalado_nao_confunde_operandos_e_derivacao(papel,referencia_instalada):
    assert all(referencia_instalada['owners'].values())
    c=referencia_instalada['referencia_proposicao'][papel]
    assert c['proposicoes'].keys()>={'meta','medicao','comparacao'}
    selecao=c['depois']['revisao_alegacao_atual']
    if papel=='valor':
        assert selecao['referencia']=='ambigua' and not selecao['alegacao_id'], 'primeira perda: referência nominal ambígua substituída pela última derivação'
        assert c['antes']['alegacoes']==c['depois']['alegacoes']
    else:
        assert selecao['alegacao_id']==c['proposicoes'][papel]['id'], 'primeira perda: papel explícito ignorado pelo fallback de recência'
    assert c['historico_inalterado'] and c['receipt_inalterado'] and c['sem_novos_efeitos']


@pytest.mark.parametrize('rota',['normal','rapida'])
def test_ambiguidade_instalada_exige_esclarecimento_antes_de_revisar(rota,referencia_instalada):
    c=referencia_instalada['referencia_proposicao']['valor']
    fonte=c['plano']['contrato_fala'].get('revisao_alegacao')
    assert fonte is not None and fonte['referencia']=='ambigua', 'ambiguidade precisa chegar ao contrato da autoria'
    ciclo,=[i for i in c['ciclos'] if i['rota']==rota]
    assert len(ciclo['textos'])==1 and not ciclo['executores']
    assert 'Qual afirmação você quer revisar?' in ciclo['textos'][0]
    for p in c['proposicoes'].values():
        item,=[i for i in ciclo['registro']['alegacoes'] if i['id']==p['id']]
        assert item['status']==p['status']


@pytest.mark.parametrize('operando',['meta','medicao'])
def test_referencia_natural_atravessa_consulta_derivada_e_historica(operando,referencia_instalada):
    c=referencia_instalada['revisao_comparacao'][operando]
    assert c['registro_depois']['revisao_alegacao_atual']['alegacao_id']==c['proposicoes'][operando]['id']
    assert c['fonte']['status']=='suporte_em_revisao'
    for ciclo in [*c['ciclos'],*c['historica']['ciclos']]:
        assert len(ciclo['textos'])==1 and not ciclo['executores']
        assert 'o suporte desta conclusão está em revisão' in ciclo['textos'][0]
    assert c['historica']['historico_inalterado'] and c['historica']['receipt_inalterado'] and c['historica']['sem_novos_efeitos']


def selecionar(reg,texto='De onde você tirou essa meta?',agora=105):
    return selecionar_alegacao_para_revisao(reg,texto,agora=agora)


@pytest.mark.parametrize('owner,grandeza,unidade', [('executor_corpo','rotação relativa','graus'),
    ('executor_arquivos','tamanho solicitado','bytes'),('executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('expressao,papel',[('esse valor solicitado','meta'),('esse valor medido','medicao'),
    ('esse valor da meta','meta'),('esse número da medição','medicao'),('essa comparação','comparacao')])
def test_papeis_compartilhados_entre_dominios_conservam_identidade_e_proveniencia(owner,grandeza,unidade,expressao,papel):
    from scripts.tests.test_comparacao_resultado_imediato import resultado_comparavel
    from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos
    r=resultado_comparavel(owner=owner,grandeza=grandeza,unidade=unidade)
    reg=registrar_fala_observada(None,ocorrencia_id='fala',turno_id='turno',fala=fala_resultado_por_aspectos(r),
        resultados=(r,),canal='texto_publicado',agora=104)
    antes=deepcopy(reg); receipt=deepcopy(r.como_dict())
    alvo,=[i for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']==papel]
    s=selecionar(reg,'De onde você tirou '+expressao+'?')
    assert s['referencia']=='unica' and s['alegacao_id']==alvo['id']
    assert reg==antes and r.como_dict()==receipt and not s['autoriza_execucao']


@pytest.mark.parametrize('defeito',['sem_entrega','outra_entrega','expirada','futura','canal','autoridade','proposta','sem_resultados',
    'id_alheio','fonte_adulterada','texto_adulterado','identidade_duplicada','solicitacao_malformada'])
def test_contexto_ausente_ou_inconsistente_nao_cede_a_ultima_alegacao(defeito):
    _,reg=publicar_resultado(); e=reg['falas_observadas'][-1]; alvo=reg['alegacoes'][0]
    if defeito=='sem_entrega': reg['falas_observadas']=[]
    elif defeito=='outra_entrega':
        reg=registrar_fala_observada(reg,ocorrencia_id='fala-independente',turno_id='outro',
            fala='Vamos conversar sobre música.',resultados=(),canal='texto_publicado',agora=104.5)
    elif defeito=='expirada': e['ts']=105-901
    elif defeito=='futura': e['ts']=106
    elif defeito=='canal': e['canais']=['texto_proposto']
    elif defeito=='autoridade': e['autoriza_execucao']=True
    elif defeito=='proposta': e['resultados'][0]['origem']='llm'
    elif defeito=='sem_resultados': e['resultados']=[]
    elif defeito=='id_alheio': e['resultados'][0]['id_solicitacao']='outra'
    elif defeito=='fonte_adulterada': alvo['vinculo_resultado']['fonte']['valor']=999
    elif defeito=='texto_adulterado': alvo['texto']='Uma meta inventada pela IA.'
    elif defeito=='identidade_duplicada':
        outra=deepcopy(alvo); outra['vinculo_resultado']['tipo']='medicao'; reg['alegacoes'].append(outra)
    else: alvo['vinculo_resultado']['id_solicitacao']=[]
    antes=deepcopy(reg)
    s=selecionar(reg)
    assert s['referencia']!='unica' and not s['alegacao_id']
    novo=contestar_alegacao_recente(reg,'De onde você tirou essa meta?',agora=105)
    assert novo['alegacoes']==reg['alegacoes'] and novo['revisoes_alegacoes']==reg['revisoes_alegacoes']
    assert reg==antes


@pytest.mark.parametrize('expressao',['essa meta anterior','esse valor da bateria','essa meta de outro arquivo',
    'essa meta ou essa medição','essa diferença de ontem','esse valor 23.75','essa meta inventada'])
def test_qualificador_fora_da_leitura_suportada_veta_recencia(expressao):
    _,reg=publicar_resultado()
    s=selecionar(reg,'De onde você tirou '+expressao+'?')
    assert s['referencia']=='ausente' and not s['alegacao_id']


@pytest.mark.parametrize('caso',['duplicata','duas_solicitacoes','duas_metas'])
def test_multiplos_candidatos_do_mesmo_papel_exigem_esclarecimento(caso):
    from scripts.tests.test_comparacao_resultado_imediato import resultado_comparavel
    from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos
    r=resultado_comparavel()
    if caso=='duas_metas':
        r=replace(r,expectativas=(*r.expectativas,replace(r.expectativas[0],grandeza='outra grandeza')))
    outro=replace(r,id_solicitacao='outro',
        expectativas=tuple(replace(m,ocorrencia_id='outro') for m in r.expectativas),
        medicoes=tuple(replace(m,ocorrencia_id='outro') for m in r.medicoes))
    resultados=(r,outro) if caso=='duas_solicitacoes' else (r,)
    fala=' '.join(fala_resultado_por_aspectos(i) for i in resultados)
    reg=registrar_fala_observada(None,ocorrencia_id='fala',turno_id='turno',fala=fala,resultados=resultados,
        canal='texto_publicado',agora=104)
    if caso=='duplicata': reg['alegacoes'].append(deepcopy(reg['alegacoes'][0]))
    s=selecionar(reg)
    assert s['referencia']=='ambigua' and not s['alegacao_id']


@pytest.mark.parametrize('operando',['meta','medicao'])
def test_revisar_referente_unico_suspende_derivacao_e_nao_troca_alvo_na_repeticao(operando,monkeypatch):
    _,reg=publicar_resultado(); props={i['vinculo_resultado']['tipo']:i for i in reg['alegacoes']}
    t='De onde você tirou '+('essa meta' if operando=='meta' else 'essa medição')+'?'
    novo=contestar_alegacao_recente(reg,t,agora=105)
    repetido=contestar_alegacao_recente(novo,t,agora=106)
    assert repetido['alegacoes']==novo['alegacoes'] and repetido['revisoes_alegacoes']==novo['revisoes_alegacoes']
    assert novo['revisao_alegacao_atual']['alegacao_id']==props[operando]['id']
    assert avaliar_suporte_alegacao(novo,props['comparacao']['id'])['estado']=='suporte_em_revisao'
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:107)
    fonte=recuperar_revisao_alegacao(novo,'Você mantém essa diferença?',turno_id='consulta')
    assert fonte.status=='suporte_em_revisao' and fonte.apoios_revisados==((props[operando]['id'],'contestado'),)


def test_numero_generico_so_seleciona_quando_ha_um_unico_componente_entregue():
    from mente_laylay.cognicao.explicacao_fala_historica import realizar_expectativas_resultado
    r,_=publicar_resultado()
    reg=registrar_fala_observada(None,ocorrencia_id='fala',turno_id='origem',
        fala=realizar_expectativas_resultado(r.expectativas),resultados=(r,),canal='texto_publicado',agora=104)
    s=selecionar(reg,'De onde você tirou esse valor?')
    assert s['referencia']=='unica' and s['alegacao_id']==reg['alegacoes'][0]['id']
    assert reg['alegacoes'][0]['status']=='observacao_registrada'


@pytest.mark.parametrize('defeito',['json','outra_consulta','outro_turno','comandos'])
def test_pendencia_de_referencia_nao_e_reidratada_ou_emprestada_para_outro_plano(defeito):
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaProposicaoPendente
    from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica,realizacao_revisao_alegacao
    f=ReferenciaProposicaoPendente('consulta','De onde você tirou esse valor?','ambigua')
    p={'id':'consulta','texto_usuario':f.texto_consulta,'autoriza_execucao':False,'requer_execucao':False,'comandos':[],
        'contrato_fala':{'origem':'mente_unica','turno_id':'consulta','autoriza_execucao':False,'revisao_alegacao':f}}
    if defeito=='json': p['contrato_fala']['revisao_alegacao']=asdict(f)
    elif defeito=='outra_consulta': p['texto_usuario']='Um assunto novo.'
    elif defeito=='outro_turno': p['id']='outro'
    else: p['comandos']=[{'intent':'CORPO_MOVER'}]
    a=avaliar_fala_historica(realizacao_revisao_alegacao(f),plano=p)
    assert not a['fonte_valida'] and not a['autoriza_execucao'] and a['acao']=='ajustada'


@pytest.mark.parametrize('referencia',['ausente','ambigua'])
def test_pendencia_tipado_exige_conclusao_observavel_sem_escolher_alegacao(referencia):
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaProposicaoPendente
    from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica,realizacao_revisao_alegacao
    f=ReferenciaProposicaoPendente('consulta','De onde você tirou esse valor?',referencia)
    p={'id':'consulta','texto_usuario':f.texto_consulta,'autoriza_execucao':False,'requer_execucao':False,'comandos':[],
        'contrato_fala':{'origem':'mente_unica','turno_id':'consulta','autoriza_execucao':False,'revisao_alegacao':f}}
    texto=realizacao_revisao_alegacao(f)
    assert 'Qual afirmação você quer revisar?' in texto
    a=avaliar_fala_historica('O sensor quebrou e a meta é falsa.',plano=p)
    assert a['fonte_valida'] and a['acao']=='ajustada' and a['fala']==texto and not a['prova_semantica_livre']
    assert avaliar_fala_historica(texto,plano=p)['acao']=='aceita'


def test_metalinguagem_nao_contesta_e_id_explicito_conserva_caminho_existente():
    _,reg=publicar_resultado()
    novo=contestar_alegacao_recente(reg,'Traduza "De onde você tirou essa meta?" para inglês.',agora=105)
    assert novo['alegacoes']==reg['alegacoes']
    reg['falas_observadas']=[]; alvo=reg['alegacoes'][0]
    assert selecionar(reg,'De onde você tirou a alegação '+alvo['id']+'?')['alegacao_id']==alvo['id']


def test_fallback_legado_sem_papel_nominal_nao_muda_neste_contrato():
    reg=registrar_alegacao(None,'O arquivo foi atualizado.',autor='laylay',agora=104)
    assert selecionar(reg,'Tem certeza disso?')['alegacao_id']==reg['alegacoes'][0]['id']


@pytest.mark.parametrize('consulta',['O que é a meta?','Como definir o valor de uma variável?',
    'Você conhece a comparação entre algoritmos?'])
@pytest.mark.parametrize('com_revisao',[False,True])
def test_nome_de_papel_em_pergunta_geral_nao_cria_pedido_de_revisao(consulta,com_revisao,monkeypatch):
    _,reg=publicar_resultado()
    if com_revisao:
        reg=contestar_alegacao_recente(reg,'De onde você tirou essa meta?',agora=105)
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:106)
    assert recuperar_revisao_alegacao(reg,consulta,turno_id='pergunta_geral') is None


def test_id_explicito_nao_perde_prioridade_para_artigo_nominal(monkeypatch):
    _,reg=publicar_resultado(); ident=reg['alegacoes'][0]['id']
    reg=contestar_alegacao_recente(reg,'De onde você tirou a alegação '+ident+'?',agora=105)
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:106)
    fonte=recuperar_revisao_alegacao(reg,'Você mantém a meta '+ident+'?',turno_id='consulta')
    assert fonte is not None and fonte.alegacao_id==ident and fonte.status=='contestado'

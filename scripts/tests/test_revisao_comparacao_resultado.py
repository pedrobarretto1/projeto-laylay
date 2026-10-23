"""Contestar operando suspende suporte da derivação, sem reescrever receipt."""
from copy import deepcopy
import os
from pathlib import Path

import pytest
from dataclasses import replace
import json

from mente_laylay.memoria_mental.registro_semantico import (
    registrar_fala_observada, contestar_alegacao_recente, recuperar_revisao_alegacao,
    registrar_alegacao, avaliar_suporte_alegacao,
)
from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos


def publicar_resultado():
    from scripts.tests.test_comparacao_resultado_imediato import resultado_comparavel
    r = resultado_comparavel()
    registro = registrar_fala_observada(None,ocorrencia_id='fala-1',turno_id='turno-1',
        fala=fala_resultado_por_aspectos(r),resultados=(r,),canal='texto_publicado',agora=104)
    return r,registro


@pytest.mark.parametrize('operando',['meta','medicao'])
def test_entrega_preserva_identidade_dos_operandos_e_apoio_duplo_da_comparacao(operando):
    r,registro = publicar_resultado()
    itens = {i.get('vinculo_resultado',{}).get('tipo'):i for i in registro['alegacoes']}
    assert {'meta','medicao','comparacao'} <= itens.keys(), 'primeira perda: entrega tipada não conserva proposições e relação dos operandos'
    assert set(itens['comparacao']['fontes_alegacoes']) == {itens['meta']['id'],itens['medicao']['id']}
    antes = deepcopy(r.como_dict()); falas = deepcopy(registro['falas_observadas'])
    novo = contestar_alegacao_recente(registro,'De onde você tirou a alegação '+itens[operando]['id']+'?',agora=105)
    fonte = recuperar_revisao_alegacao(novo,'Você mantém a alegação '+itens['comparacao']['id']+'?',turno_id='consulta')
    assert fonte is not None and fonte.status == 'suporte_em_revisao'
    assert fonte.apoios_revisados == ((itens[operando]['id'],'contestado'),)
    assert novo['falas_observadas'] == falas and r.como_dict() == antes


def test_apoio_conjuntivo_nao_ignora_segunda_fonte_contestada():
    registro = registrar_alegacao(None,'A primeira fonte foi registrada.',autor='laylay',agora=100)
    a = registro['alegacoes'][-1]['id']
    registro = registrar_alegacao(registro,'A segunda fonte foi registrada.',autor='laylay',agora=101)
    b = registro['alegacoes'][-1]['id']
    registro = registrar_alegacao(registro,'A relação entre fontes foi registrada.',autor='laylay',fonte=a,agora=102)
    c = registro['alegacoes'][-1]['id']
    registro['alegacoes'][-1]['fontes_alegacoes'] = (a,b)
    registro = contestar_alegacao_recente(registro,'De onde você tirou a alegação '+b+'?',agora=103)
    assert avaliar_suporte_alegacao(registro,c)['estado'] == 'suporte_em_revisao'


@pytest.fixture(scope='module')
def revisao_resultado_instalada(tmp_path_factory):
    from scripts.tests.test_comparacao_resultado_imediato import comparacoes_imediatas_instaladas
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_REVISAO_COMPARACAO','1')
        if pasta := os.environ.get('LAYLAY_EVIDENCIA_REVISAO_COMPARACAO'):
            ambiente.setenv('LAYLAY_EVIDENCIA_COMPARACAO_IMEDIATA',pasta)
        return comparacoes_imediatas_instaladas.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('operando',['meta','medicao'])
def test_composicao_pode_revisar_operando_da_propria_resposta(operando,revisao_resultado_instalada):
    dados = revisao_resultado_instalada
    assert all(dados['owners'].values())
    caso = dados['revisao_comparacao'][operando]
    assert caso['proposicoes'].keys() >= {'meta','medicao','comparacao'}, 'primeira perda instalada: fontes chegam à entrega, mas não ao registro revisável'
    assert caso['registro_depois']['revisao_alegacao_atual']['alegacao_id'] == caso['proposicoes'][operando]['id']
    assert caso['fonte']['status'] == 'suporte_em_revisao'
    assert caso['sem_novos_efeitos'] and caso['historico_inalterado'] and caso['receipt_inalterado']


@pytest.mark.parametrize('operando',['meta','medicao'])
@pytest.mark.parametrize('rota',['normal','rapida'])
@pytest.mark.parametrize('modo',['reafirma','nega','causa'])
def test_consulta_instalada_nao_reafirma_ou_nega_derivacao_com_operando_em_revisao(operando,rota,modo,revisao_resultado_instalada):
    c = revisao_resultado_instalada['revisao_comparacao'][operando]
    ciclo, = [i for i in c['ciclos'] if i['rota']==rota and i['modo']==modo]
    assert len(ciclo['textos'])==1 and not ciclo['executores']
    fala, = ciclo['textos']
    assert 'o suporte desta conclusão está em revisão' in fala
    assert 'não prova que ela seja falsa' in fala and 'nem autoriza repeti-las ou desfazê-las' in fala
    assert ciclo['propostas'] and all(p!=fala for p in ciclo['propostas'])


def itens_resultado(registro):
    return {i['vinculo_resultado']['tipo']:i for i in registro['alegacoes'] if i.get('vinculo_resultado')}


@pytest.mark.parametrize('intent,owner,grandeza,unidade', [('CORPO_MOVER','executor_corpo','rotação relativa','graus'),
    ('FILE_WRITE','executor_arquivos','tamanho solicitado','bytes'),('VOLUME','executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('tipo',['contestacao','correcao'])
@pytest.mark.parametrize('operando',['meta','medicao'])
def test_revisao_compartilhada_preserva_receipt_e_operando_independente(intent,owner,grandeza,unidade,tipo,operando):
    from scripts.tests.test_comparacao_resultado_imediato import resultado_comparavel
    from mente_laylay.memoria_mental.registro_semantico import corrigir_alegacao_recente
    r=replace(resultado_comparavel(owner=owner,grandeza=grandeza,unidade=unidade),intent=intent)
    original=deepcopy(r.como_dict())
    reg=registrar_fala_observada(None,ocorrencia_id='fala',turno_id='turno',fala=fala_resultado_por_aspectos(r),
        resultados=(r,),canal='texto_publicado',agora=104)
    itens=itens_resultado(reg); outro='medicao' if operando=='meta' else 'meta'
    texto='De onde você tirou a alegação '+itens[operando]['id']+'?'
    novo=(contestar_alegacao_recente if tipo=='contestacao' else corrigir_alegacao_recente)(reg,texto,agora=105)
    fonte=recuperar_revisao_alegacao(novo,'Você mantém a alegação '+itens['comparacao']['id']+'?',turno_id='consulta')
    assert fonte.status=='suporte_em_revisao' and fonte.apoios_revisados==((itens[operando]['id'],'contestado' if tipo=='contestacao' else 'corrigido'),)
    assert itens_resultado(novo)[outro]==itens[outro] and r.como_dict()==original
    assert itens_resultado(novo)['comparacao']==itens['comparacao']
    assert not fonte.autoriza_execucao


@pytest.mark.parametrize('entrega',['sem_resultado','proposta_json','texto_alterado','meta_sozinha'])
def test_proposta_ou_componente_nao_entregue_nao_cria_apoio_verificado(entrega):
    r,_=publicar_resultado(); fala=fala_resultado_por_aspectos(r)
    resultados=(r,)
    if entrega=='sem_resultado': resultados=()
    elif entrega=='proposta_json': resultados=(json.loads(json.dumps(r.como_dict())),)
    elif entrega=='texto_alterado': fala=fala.replace('90 "graus"','180 "graus"')
    elif entrega=='meta_sozinha':
        from mente_laylay.cognicao.explicacao_fala_historica import realizar_expectativas_resultado
        fala=realizar_expectativas_resultado(r.expectativas)
    if entrega=='proposta_json':
        with pytest.raises(ValueError): registrar_fala_observada(None,ocorrencia_id='f',turno_id='t',fala=fala,resultados=resultados,canal='texto_publicado',agora=104)
        return
    reg=registrar_fala_observada(None,ocorrencia_id='f',turno_id='t',fala=fala,resultados=resultados,canal='texto_publicado',agora=104)
    itens=itens_resultado(reg)
    assert 'comparacao' not in itens
    if entrega=='meta_sozinha': assert set(itens)=={'meta'}
    elif entrega=='texto_alterado': assert set(itens)=={'medicao'}
    else: assert not itens


def test_reentrega_nao_reabilita_alegacao_contestada_nem_conta_nova_prova():
    r,reg=publicar_resultado(); itens=itens_resultado(reg)
    reg=contestar_alegacao_recente(reg,'De onde você tirou a alegação '+itens['meta']['id']+'?',agora=105)
    antes=deepcopy(reg['alegacoes'])
    for id_fala,canal in [('fala-1','audio_reproducao_confirmada'),('fala-2','texto_publicado')]:
        reg=registrar_fala_observada(reg,ocorrencia_id=id_fala,turno_id='turno-1',fala=fala_resultado_por_aspectos(r),
            resultados=(r,),canal=canal,agora=106)
    assert reg['alegacoes']==antes
    assert avaliar_suporte_alegacao(reg,itens['comparacao']['id'])['estado']=='suporte_em_revisao'


def test_valores_iguais_em_outra_execucao_nao_herdam_revisao():
    r,reg=publicar_resultado(); itens=itens_resultado(reg)
    outro=replace(r,id_solicitacao='outra-execucao',
        expectativas=tuple(replace(e,ocorrencia_id='outra-execucao') for e in r.expectativas),
        medicoes=tuple(replace(m,ocorrencia_id='outra-execucao') for m in r.medicoes))
    reg=registrar_fala_observada(reg,ocorrencia_id='outra-fala',turno_id='outro-turno',fala=fala_resultado_por_aspectos(outro),
        resultados=(outro,),canal='texto_publicado',agora=105)
    outros=itens_resultado(reg)
    assert outros['meta']['id']!=itens['meta']['id'] and len(reg['alegacoes'])==6
    novo=contestar_alegacao_recente(reg,'De onde você tirou a alegação '+itens['meta']['id']+'?',agora=106)
    assert avaliar_suporte_alegacao(novo,outros['comparacao']['id'])['estado']=='sem_restricao_de_suporte'


def cadeia_dupla():
    reg=None; ids=[]
    for n in range(3):
        reg=registrar_alegacao(reg,f'A fonte numero {n} foi registrada.',autor='laylay',agora=100+n)
        ids.append(reg['alegacoes'][-1]['id'])
    reg['alegacoes'][-1]['fontes_alegacoes']=tuple(ids[:2])
    return reg,ids


@pytest.mark.parametrize('defeito',['ausente','duplicada','ciclo','tupla_invalida','repetida','excesso','conflito_legado'])
def test_suporte_conjuntivo_invalido_nao_vira_fonte_externa(defeito):
    from mente_laylay.cognicao.proveniencia_informacao import classificar_proveniencia_informacao
    reg,ids=cadeia_dupla()
    if defeito=='ausente': reg['alegacoes']=reg['alegacoes'][1:]
    elif defeito=='duplicada': reg['alegacoes'].append(deepcopy(reg['alegacoes'][0]))
    elif defeito=='ciclo': reg['alegacoes'][0]['fonte']=ids[-1]
    elif defeito=='tupla_invalida': reg['alegacoes'][-1]['fontes_alegacoes']='parecer da autora'
    elif defeito=='repetida': reg['alegacoes'][-1]['fontes_alegacoes']=(ids[0],ids[0])
    elif defeito=='excesso': reg['alegacoes'][-1]['fontes_alegacoes']=tuple('alegacao:'+str(i) for i in range(9))
    elif defeito=='conflito_legado': reg['alegacoes'][-1]['fonte']='alegacao:999'
    assert avaliar_suporte_alegacao(reg,ids[-1])['estado']=='suporte_interno_invalido'
    item=next(i for i in reg['alegacoes'] if i['id']==ids[-1])
    assert not classificar_proveniencia_informacao({**item,'status':'confirmado_por_fonte','confiavel':True})['pode_sustentar_fato_externo']


def test_diamante_conjuntivo_preserva_ambos_apoios_revisados_sem_duplicar():
    reg,ids=cadeia_dupla()
    reg=registrar_alegacao(reg,'A conclusão seguinte foi registrada.',autor='laylay',agora=104)
    d=reg['alegacoes'][-1]['id']; reg['alegacoes'][-1]['fontes_alegacoes']=(ids[2],ids[0])
    for id_alvo in ids[:2]: reg=contestar_alegacao_recente(reg,'De onde você tirou a alegação '+id_alvo+'?',agora=105)
    estado=avaliar_suporte_alegacao(reg,d)
    assert estado['apoios_revisados']==((ids[0],'contestado'),(ids[1],'contestado'))
    assert not estado['prova_implicacao'] and not estado['autoriza_execucao']


def test_persistencia_do_registro_conserva_dependencia_sem_reidratar_prova_de_executor():
    r,reg=publicar_resultado(); itens=itens_resultado(reg)
    reg=json.loads(json.dumps(reg))
    reg=contestar_alegacao_recente(reg,'De onde você tirou a alegação '+itens['medicao']['id']+'?',agora=105)
    assert avaliar_suporte_alegacao(reg,itens['comparacao']['id'])['estado']=='suporte_em_revisao'


def test_rotulo_externo_nao_promove_apoios_internos_a_confirmacao():
    from mente_laylay.cognicao.proveniencia_informacao import classificar_proveniencia_informacao
    item={'autor':'laylay','tipo':'fato_candidato','fonte':'fonte_externa_declarada','status':'confirmado_por_fonte',
        'confiavel':True,'fontes_alegacoes':('alegacao:100','alegacao:101')}
    assert not classificar_proveniencia_informacao(item,contexto='fundamentacao_factual')['pode_sustentar_fato_externo']


def test_resumo_compartilhado_bloqueia_derivacao_sem_reescrever_seu_status():
    from mente_laylay.memoria_mental.registro_semantico import resumo_registro_semantico_para_prompt
    r,reg=publicar_resultado(); itens=itens_resultado(reg)
    reg=contestar_alegacao_recente(reg,'De onde você tirou a alegação '+itens['medicao']['id']+'?',agora=105)
    resumo=resumo_registro_semantico_para_prompt(reg,agora=106)
    assert itens['comparacao']['texto'] in resumo.split('alegações_bloqueadas=',1)[1]
    assert itens_resultado(reg)['comparacao']==itens['comparacao']


@pytest.mark.parametrize('operando',['meta','medicao'])
@pytest.mark.parametrize('tipo',['contestacao','correcao'])
def test_reentrega_apos_retencao_respeita_diario_de_revisoes(operando,tipo):
    from mente_laylay.memoria_mental.registro_semantico import corrigir_alegacao_recente
    r,reg=publicar_resultado(); itens=itens_resultado(reg)
    reg=(contestar_alegacao_recente if tipo=='contestacao' else corrigir_alegacao_recente)(reg,
        'De onde você tirou a alegação '+itens[operando]['id']+'?',agora=105)
    diario=deepcopy(reg['revisoes_alegacoes'])
    # Evicção de memória curta; a revisão registrada continua retida.
    reg['alegacoes']=[i for i in reg['alegacoes'] if i['id']!=itens[operando]['id']]
    reg=registrar_fala_observada(reg,ocorrencia_id='reentrega',turno_id='turno-1',
        fala=fala_resultado_por_aspectos(r),resultados=(r,),canal='texto_publicado',agora=106)
    assert itens_resultado(reg)[operando]['status']==('contestado' if tipo=='contestacao' else 'corrigido')
    assert avaliar_suporte_alegacao(reg,itens['comparacao']['id'])['estado']=='suporte_em_revisao'
    assert reg['revisoes_alegacoes']==diario and itens_resultado(reg)[operando]['ts']==itens[operando]['ts']

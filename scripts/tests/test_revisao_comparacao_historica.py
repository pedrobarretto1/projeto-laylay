"""Revisão da fala alcança ocorrência histórica somente pelo vínculo próprio."""
import os
import pytest
from dataclasses import replace
from dataclasses import asdict
from copy import deepcopy
import json

from mente_laylay.memoria_mental.decisao_observada import ExplicacaoOcorrencia, FontesComparacaoResultado
from mente_laylay.memoria_mental.registro_semantico import (
    registrar_fala_observada,contestar_alegacao_recente,corrigir_alegacao_recente,
    vincular_revisoes_explicacao_ocorrencia,
)
from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_explicacao_ocorrencia
from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos


def resultado_e_ocorrencia(*,owner='executor_corpo',grandeza='rotação relativa',unidade='graus'):
    from scripts.tests.test_comparacao_resultado import episodio_comparavel
    from mente_laylay.memoria_mental.decisao_observada import FontesComparacaoResultado
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    e=episodio_comparavel(owner=owner,grandeza=grandeza,unidade=unidade)
    f=FontesComparacaoResultado(e.id,e.expectativas,iniciada_em=e.iniciada_em)
    r=ResultadoAcao(intent='CORPO_MOVER',origem='executor',status='falha_execucao',alvo='alvo',
        executou=True,confirmado=False,id_solicitacao='solicitacao-1',inicio_execucao=e.iniciada_em,
        expectativas=tuple(replace(m,ocorrencia_id='solicitacao-1') for m in e.expectativas),
        medicoes=tuple(replace(m,ocorrencia_id='solicitacao-1') for m in e.medicoes),fontes_ocorrencia=f)
    return r,e


def test_projecao_do_vinculo_e_arvore_json_sem_conversao_implicita():
    from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
    r,e=resultado_e_ocorrencia()
    assert SnapshotComandoIA(r.como_dict()).como_dict()['fontes_ocorrencia']['id']==e.id


@pytest.fixture(scope='module')
def revisao_historica_instalada(tmp_path_factory):
    from scripts.tests.test_revisao_comparacao_resultado import revisao_resultado_instalada
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_REVISAO_HISTORICA','1')
        if pasta := os.environ.get('LAYLAY_EVIDENCIA_REVISAO_HISTORICA'):
            ambiente.setenv('LAYLAY_EVIDENCIA_REVISAO_COMPARACAO',pasta)
        return revisao_resultado_instalada.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('operando',['meta','medicao'])
def test_publicacao_conserva_vinculo_proprio_entre_solicitacao_e_ocorrencia(operando,revisao_historica_instalada):
    d=revisao_historica_instalada
    c=d['revisao_comparacao'][operando]; r,=d['medidas_ocorrencias']['meta90']['publicacoes']
    assert r['id_solicitacao']!=c['historica']['ocorrencia_id']
    assert (r.get('fontes_ocorrencia') or {}).get('id')==c['historica']['ocorrencia_id'], 'primeira perda: executor descarta identidade da captura prévia ao remapear fontes'


@pytest.mark.parametrize('operando',['meta','medicao'])
def test_explicacao_historica_respeita_revisao_dos_operandos_entregues(operando,revisao_historica_instalada):
    c=revisao_historica_instalada['revisao_comparacao'][operando]
    h=c['historica']
    assert h['fonte']['referencia']=='unica' and h['fonte']['episodios'][0]['id']==h['ocorrencia_id']
    revisoes=h['fonte'].get('revisoes_proposicoes',[])
    assert len(revisoes)==2, 'ocorrência certa é recuperada, mas revisão do operando e do suporte se perde'
    assert {i[1]['status'] for i in revisoes}=={'contestado','suporte_em_revisao'}
    assert h['historico_inalterado'] and h['receipt_inalterado'] and h['sem_novos_efeitos']
    for ciclo in h['ciclos']:
        assert len(ciclo['textos'])==1 and not ciclo['executores']
        assert 'o suporte desta conclusão está em revisão' in ciclo['textos'][0]


def registrar_e_revisar(r,*,operando='meta',tipo='contestacao',fala=None):
    reg=registrar_fala_observada(None,ocorrencia_id='fala-1',turno_id='origem',
        fala=fala or fala_resultado_por_aspectos(r),resultados=(r,),canal='texto_publicado')
    itens={i['vinculo_resultado']['tipo']:i for i in reg['alegacoes']}
    reg=(contestar_alegacao_recente if tipo=='contestacao' else corrigir_alegacao_recente)(reg,
        'De onde você tirou a alegação '+itens[operando]['id']+'?')
    return reg,itens


def fonte_historica(e):
    return ExplicacaoOcorrencia('consulta',f'Por que você fez essa ação {e.id}?',(e,),'unica')


@pytest.mark.parametrize('owner,grandeza,unidade',[('executor_corpo','rotação relativa','graus'),
    ('executor_arquivos','tamanho solicitado','bytes'),('executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('operando',['meta','medicao'])
@pytest.mark.parametrize('tipo',['contestacao','correcao'])
def test_revisao_historica_compartilhada_conserva_execucao_e_apoio_independente(owner,grandeza,unidade,operando,tipo):
    r,e=resultado_e_ocorrencia(owner=owner,grandeza=grandeza,unidade=unidade)
    reg,itens=registrar_e_revisar(r,operando=operando,tipo=tipo)
    antes=deepcopy(reg); original=deepcopy(e); receipt=deepcopy(r.como_dict())
    revisada=vincular_revisoes_explicacao_ocorrencia(reg,fonte_historica(e))
    revs=dict(revisada.revisoes_proposicoes)
    assert set(revs)=={operando+':0','comparacao:0'}
    assert revs[operando+':0'].status==('contestado' if tipo=='contestacao' else 'corrigido')
    assert revs['comparacao:0'].apoios_revisados==((itens[operando]['id'],revs[operando+':0'].status),)
    fala,=realizacoes_explicacao_ocorrencia(revisada)
    outro='medicao' if operando=='meta' else 'meta'
    assert itens[outro]['texto'] in fala
    assert 'o suporte desta conclusão está em revisão' in fala and 'não prova que ela seja falsa' in fala
    assert reg==antes and e==original and r.como_dict()==receipt and not revisada.autoriza_execucao
    assert all(not rev.autoriza_execucao for rev in revs.values())


@pytest.mark.parametrize('defeito',['json','origem','meta_diferente','inicio_diferente','com_medicao','sem_meta','texto'])
def test_vinculo_de_execucao_recusa_fonte_sem_captura_original(defeito):
    r,e=resultado_e_ocorrencia(); f=r.fontes_ocorrencia
    campos={}
    if defeito=='json': campos['fontes_ocorrencia']=asdict(f)
    elif defeito=='texto': campos['fontes_ocorrencia']=e.id
    elif defeito=='origem': campos['origem']='llm'
    elif defeito=='meta_diferente': campos['fontes_ocorrencia']=replace(f,expectativas=(replace(f.expectativas[0],valor=180),))
    elif defeito=='inicio_diferente': campos['fontes_ocorrencia']=replace(f,iniciada_em=f.iniciada_em+1)
    elif defeito=='com_medicao': campos['fontes_ocorrencia']=replace(f,medicoes=e.medicoes)
    else: campos['fontes_ocorrencia']=replace(f,expectativas=())
    with pytest.raises(ValueError): replace(r,**campos)


@pytest.mark.parametrize('caminho',['normalizar','nova_solicitacao'])
def test_json_de_proposta_nao_reidrata_vinculo_do_executor(caminho):
    from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao,identificar_solicitacao_execucao
    r,e=resultado_e_ocorrencia(); bruto=json.loads(json.dumps(r.como_dict()))
    if caminho=='normalizar': assert normalizar_resultado_acao(bruto).fontes_ocorrencia is None
    else: assert 'fontes_ocorrencia' not in identificar_solicitacao_execucao(bruto,nova_identidade=True)


@pytest.mark.parametrize('alteracao',['id','owner','sem_vinculo'])
def test_valores_iguais_ou_ausencia_de_vinculo_nao_emprestam_revisao(alteracao):
    r,e=resultado_e_ocorrencia(); reg,_=registrar_e_revisar(r)
    for i in reg['alegacoes']:
        if alteracao=='sem_vinculo': i.pop('vinculo_ocorrencia')
        else: i['vinculo_ocorrencia'][alteracao]='outra_origem'
    f=vincular_revisoes_explicacao_ocorrencia(reg,fonte_historica(e))
    assert f is not None and not f.revisoes_proposicoes


@pytest.mark.parametrize('defeito',['valor','texto','identidade','duplicada','apoios','campo_extra','duas_solicitacoes'])
def test_vinculo_contraditorio_falha_fechado_sem_reescrever_historico(defeito):
    r,e=resultado_e_ocorrencia(); reg,itens=registrar_e_revisar(r)
    alvo=reg['alegacoes'][0]
    if defeito=='valor': alvo['vinculo_resultado']['fonte']['valor']=999
    elif defeito=='texto': alvo['texto']='Uma proposta da IA.'
    elif defeito=='identidade': alvo['id']='alegacao:999'
    elif defeito=='duplicada': reg['alegacoes'].append(deepcopy(alvo))
    elif defeito=='apoios': reg['alegacoes'][-1]['fontes_alegacoes']=('alegacao:999',)
    elif defeito=='campo_extra': alvo['vinculo_ocorrencia']['atual']=True
    else: alvo['vinculo_resultado']['id_solicitacao']='outro-pedido'
    antes=deepcopy(reg)
    assert vincular_revisoes_explicacao_ocorrencia(reg,fonte_historica(e)) is None
    assert reg==antes


def test_comparacao_historica_nova_depende_do_operando_revisado_mesmo_sem_entrega_anterior_da_derivacao():
    from mente_laylay.cognicao.explicacao_fala_historica import realizar_expectativas_resultado
    r,e=resultado_e_ocorrencia()
    reg,itens=registrar_e_revisar(r,fala=realizar_expectativas_resultado(r.expectativas))
    assert set(itens)=={'meta'}
    f=vincular_revisoes_explicacao_ocorrencia(reg,fonte_historica(e))
    assert dict(f.revisoes_proposicoes)['comparacao:0'].status=='suporte_em_revisao'
    assert len(reg['alegacoes'])==1


@pytest.mark.parametrize('defeito',['json','outra_consulta','chave_ausente','lista_vazia'])
def test_projecao_de_revisao_exige_fonte_tipagem_e_vinculo_da_consulta(defeito):
    r,e=resultado_e_ocorrencia(); reg,_=registrar_e_revisar(r)
    f=vincular_revisoes_explicacao_ocorrencia(reg,fonte_historica(e))
    pares=f.revisoes_proposicoes
    if defeito=='chave_ausente':
        falsa=replace(f,revisoes_proposicoes=(('meta:99',pares[0][1]),))
        assert not realizacoes_explicacao_ocorrencia(falsa)
        return
    if defeito=='json': pares=((pares[0][0],asdict(pares[0][1])),)
    elif defeito=='outra_consulta': pares=((pares[0][0],replace(pares[0][1],turno_consulta='alheia')),)
    else: pares=[]
    with pytest.raises(ValueError): replace(f,revisoes_proposicoes=pares)


@pytest.mark.parametrize('alteracao',['meta','medicao'])
def test_historico_alterado_nao_correlaciona_fonte_anterior_so_por_id(alteracao):
    r,e=resultado_e_ocorrencia(); reg,_=registrar_e_revisar(r)
    if alteracao=='meta': e=replace(e,expectativas=(replace(e.expectativas[0],valor=180),))
    else: e=replace(e,medicoes=(replace(e.medicoes[0],valor=999),))
    assert vincular_revisoes_explicacao_ocorrencia(reg,fonte_historica(e)) is None


def test_reentrega_preserva_estado_revisado_e_vinculo_canonico():
    r,e=resultado_e_ocorrencia(); reg,_=registrar_e_revisar(r)
    antes=deepcopy(reg['alegacoes']); diario=deepcopy(reg['revisoes_alegacoes'])
    reg=registrar_fala_observada(reg,ocorrencia_id='fala-2',turno_id='origem',fala=fala_resultado_por_aspectos(r),
        resultados=(r,),canal='texto_publicado')
    assert reg['alegacoes']==antes and reg['revisoes_alegacoes']==diario
    assert len(vincular_revisoes_explicacao_ocorrencia(reg,fonte_historica(e)).revisoes_proposicoes)==2


def test_consulta_por_ato_nao_empresta_revisao_entre_owners():
    from scripts.tests.test_explicacao_historica_por_ato import consulta
    from scripts.tests.test_explicacao_ocorrencia import episodio
    from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_explicacoes_por_ato
    r,e=resultado_e_ocorrencia(owner='executor_arquivos',grandeza='tamanho solicitado',unidade='bytes')
    reg,_=registrar_e_revisar(r)
    outro=episodio(owner='executor_iot',nome='tomada_1')
    def recuperar(texto,*,turno):
        return ExplicacaoOcorrencia(str(turno['id']),texto,(e if 'arquivo' in texto else outro,),'unica')
    turno,p=consulta(recuperar=recuperar,mente={'registro_semantico':reg})
    f=p['contrato_fala']['explicacoes_historicas_por_ato']
    assert len(f.partes[0].ocorrencia.revisoes_proposicoes)==2
    assert not f.partes[1].ocorrencia.revisoes_proposicoes
    fala,=realizacoes_explicacoes_por_ato(f)
    assert fala.count('Sobre ')==2 and 'o suporte desta conclusão está em revisão' in fala


@pytest.mark.parametrize('consulta',['Por que você fez esse gesto?','O que motivou esse movimento?'])
def test_contrato_compartilhado_enriquece_fonte_sem_usar_revisao_como_autorizacao(consulta):
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
    from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica
    r,e=resultado_e_ocorrencia(); reg,_=registrar_e_revisar(r)
    t=classificar_modalidade_turno(consulta)
    p={'id':t['id'],'texto_usuario':consulta,'requer_execucao':False,'autoriza_execucao':False,'comandos':[]}
    f=ExplicacaoOcorrencia(str(t['id']),consulta,(e,),'unica')
    p['contrato_fala']=construir_contrato_semantico_fala(consulta,turno=t,plano=p,
        mente={'registro_semantico':reg},explicacao_ocorrencia=f)
    revisada=p['contrato_fala']['explicacao_ocorrencia']
    assert len(revisada.revisoes_proposicoes)==2 and not revisada.autoriza_execucao
    fala,=realizacoes_explicacao_ocorrencia(revisada)
    assert avaliar_fala_historica(fala,plano=p)['acao']=='aceita'
    assert avaliar_fala_historica('A diferença está confirmada; vou repetir a ação.',plano=p)['acao']=='ajustada'


def test_ramo_invalido_prevalece_sem_promover_outro_apoio_revisado():
    from mente_laylay.cognicao.explicacao_fala_historica import realizar_expectativas_resultado,realizar_medicoes_observadas
    r,e=resultado_e_ocorrencia()
    fala=realizar_expectativas_resultado(r.expectativas)+' '+realizar_medicoes_observadas(r.medicoes)
    reg,itens=registrar_e_revisar(r,operando='medicao',fala=fala)
    assert set(itens)=={'meta','medicao'}
    duplicada=deepcopy(reg['alegacoes'][0]); duplicada.pop('vinculo_ocorrencia')
    reg['alegacoes'].append(duplicada)
    f=vincular_revisoes_explicacao_ocorrencia(reg,fonte_historica(e))
    rev=dict(f.revisoes_proposicoes)['comparacao:0']
    assert rev.status=='suporte_interno_invalido' and not rev.apoios_revisados


def test_revisao_de_uma_comparacao_conserva_motivo_da_outra_indisponivel():
    from mente_laylay.cognicao.explicacao_fala_historica import realizar_comparacoes_resultado
    from mente_laylay.memoria_mental.decisao_observada import avaliar_comparacoes_resultado
    r,e=resultado_e_ocorrencia()
    e=replace(e,expectativas=e.expectativas+(replace(e.expectativas[0],grandeza='outra grandeza'),))
    f=FontesComparacaoResultado(e.id,e.expectativas,iniciada_em=e.iniciada_em)
    r=replace(r,expectativas=tuple(replace(m,ocorrencia_id=r.id_solicitacao) for m in e.expectativas),fontes_ocorrencia=f)
    reg,_=registrar_e_revisar(r,operando='medicao')
    revisada=vincular_revisoes_explicacao_ocorrencia(reg,fonte_historica(e))
    motivo=realizar_comparacoes_resultado((avaliar_comparacoes_resultado(e)[1],))
    assert motivo in realizacoes_explicacao_ocorrencia(fonte_historica(e))[0]
    fala,=realizacoes_explicacao_ocorrencia(revisada)
    assert 'o suporte desta conclusão está em revisão' in fala
    assert motivo in fala


@pytest.mark.parametrize('limite',['sem_meta','referencial_distinto'])
def test_fonte_historica_sem_revisao_preserva_criterio_do_owner(limite):
    r,e=resultado_e_ocorrencia()
    reg=registrar_fala_observada(None,ocorrencia_id='fala-1',turno_id='origem',
        fala=fala_resultado_por_aspectos(r),resultados=(r,),canal='texto_publicado')
    assert not reg['revisoes_alegacoes'] and all(i['status'] not in {'contestado','corrigido'} for i in reg['alegacoes'])
    if limite=='sem_meta': e=replace(e,expectativas=())
    else: e=replace(e,expectativas=(replace(e.expectativas[0],referencial='outro_inicio'),))
    fonte=fonte_historica(e)
    assert realizacoes_explicacao_ocorrencia(fonte)
    vinculada=vincular_revisoes_explicacao_ocorrencia(reg,fonte)
    assert vinculada==fonte, 'estado sem revisão não deve transformar reconciliação de fontes em veto global ao histórico'

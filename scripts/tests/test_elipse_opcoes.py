"""Elipse sem papel só restringe opções da pergunta observada, sem autoridade."""
from copy import deepcopy
from dataclasses import replace
import os
import pytest
from scripts.tests.test_continuidade_esclarecimento import contexto_local,contrato,entregar_continuacao
from scripts.tests.test_opcoes_proposicao import consumir,par_fontes,publicar,entregar
from mente_laylay.memoria_mental.registro_semantico import (
    contestar_alegacao_recente,recuperar_revisao_alegacao,avaliar_suporte_alegacao)

def alvo_auxiliar(m):
    return next(i['id'] for i in m['registro_semantico']['alegacoes']
        if i['vinculo_resultado']['tipo']=='medicao'
        and i['vinculo_resultado']['fonte']['metodo']=='sensor auxiliar')

def test_primeira_perda_elipse_e_referencia_completa_usam_as_mesmas_opcoes(monkeypatch):
    m=contexto_local(monkeypatch);antes=deepcopy(m)
    controle=consumir(m,'a medição pelo método sensor auxiliar')
    assert controle['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==alvo_auxiliar(m)
    nova=consumir(m,'a do sensor auxiliar')
    assert nova['registro_semantico']['revisao_alegacao_atual'].get('alegacao_id')==alvo_auxiliar(m), \
        'primeira perda: opções válidas e entregues não chegam à seleção da elipse sem papel'
    assert m==antes

@pytest.mark.parametrize('owner,grandeza,unidade',[('executor_corpo','rotação relativa','graus'),
    ('executor_arquivos','tamanho solicitado','bytes'),('executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('texto',['a do sensor auxiliar','essa do sensor auxiliar','a pelo método sensor auxiliar',
    'pelo método sensor auxiliar'])
def test_elipse_exata_restringe_identidade_sem_mudar_fontes(monkeypatch,owner,grandeza,unidade,texto):
    m=contexto_local(monkeypatch,owner=owner,grandeza=grandeza,unidade=unidade);antes=deepcopy(m)
    nova=consumir(m,texto);reg=nova['registro_semantico'];alvo=alvo_auxiliar(m)
    assert reg['revisao_alegacao_atual']['alegacao_id']==alvo
    assert reg['revisao_alegacao_atual']['solicitacao_original']==m['pendencia_atual']['vinculo_proposicao']['solicitacao_original']
    assert reg['revisao_alegacao_atual']['autoriza_execucao'] is False
    assert not nova['pendencia_atual'] and nova['ultima_pendencia_encerrada']['id']==m['pendencia_atual']['id']
    for i in reg['alegacoes']:
        anterior=next(a for a in antes['registro_semantico']['alegacoes'] if a['id']==i['id'])
        if i['id']!=alvo:assert i==anterior
        if i['vinculo_resultado']['tipo']=='comparacao':
            assert (avaliar_suporte_alegacao(reg,i['id'])['estado']=='suporte_em_revisao')==(alvo in i['fontes_alegacoes'])
    assert m==antes

@pytest.mark.parametrize('texto',['a da referencia auxiliar','no referencial referencia auxiliar',
    'essa no referencial referencia auxiliar'])
def test_elipse_de_referencial_usa_campo_proprio_entregue(monkeypatch,texto):
    m=contexto_local(monkeypatch,campo='referencial');nova=consumir(m,texto)
    alvo=next(i['id'] for i in m['registro_semantico']['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao'
        and i['vinculo_resultado']['fonte']['referencial']=='referencia auxiliar')
    assert nova['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==alvo

@pytest.mark.parametrize('texto',['sensor auxiliar','a do sensor auxiliarr','a do sensor inventado',
    'apague a do sensor auxiliar','a do sensor auxiliar e repita o giro','não revise a do sensor auxiliar',
    'Traduza a do sensor auxiliar para inglês.','a do sensor auxiliar é interessante',
    'O que é sensor auxiliar?','bom dia','a do "sensor auxiliar"'])
def test_outro_ato_nome_parcial_ou_desconhecido_nao_resolve(monkeypatch,texto):
    m=contexto_local(monkeypatch);antes=deepcopy(m)
    assert consumir(m,texto)==antes and contrato(m,texto).get('revisao_alegacao') is None

def test_nome_parcial_nao_resolve_e_pede_esclarecimento(monkeypatch):
    # Não selecionar permanece obrigatório; a conclusão passou a preservar
    # explicitamente a pergunta quando o fragmento pertence às opções expostas.
    m=contexto_local(monkeypatch);antes=deepcopy(m)
    assert consumir(m,'a do sensor')==antes
    f=contrato(m,'a do sensor')['revisao_alegacao']
    assert f.referencia=='ausente' and f.pendencia_id==m['pendencia_atual']['id']

def contexto_colisao(monkeypatch):
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:105)
    a,b=par_fontes();m=replace(a.medicoes[0],referencial='sensor auxiliar')
    a=replace(a,medicoes=(m,),expectativas=(replace(a.expectativas[0],referencial=m.referencial),))
    pergunta='De onde você tirou essa medição?';reg=contestar_alegacao_recente(publicar((a,b)),pergunta,agora=105)
    f=recuperar_revisao_alegacao(reg,pergunta,turno_id='pergunta')
    return entregar(reg,f,realizacao_revisao_alegacao(f))

def test_mesmo_nome_em_campos_distintos_conserva_ambiguidade(monkeypatch):
    m=contexto_colisao(monkeypatch);antes=deepcopy(m);texto='a do sensor auxiliar'
    assert consumir(m,texto)==antes
    f=contrato(m,texto)['revisao_alegacao'];assert len(f.candidatos)==2 and f.pendencia_id==m['pendencia_atual']['id']
    nova=entregar_continuacao(m,f);p=nova['pendencia_atual']
    assert p['id']==m['pendencia_atual']['id'] and p['expira_em']==m['pendencia_atual']['expira_em']
    resolvida=consumir(nova,'pelo método sensor auxiliar')
    assert resolvida['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==alvo_auxiliar(m)

@pytest.mark.parametrize('defeito',['expirada','outro_owner','sem_opcoes_entregues','fonte_adulterada','pergunta_alterada','encerrada'])
def test_elipse_nao_usa_campo_sem_exposicao_ou_pendencia_invalida(monkeypatch,defeito):
    m=contexto_local(monkeypatch);p=m['pendencia_atual']
    if defeito=='expirada':p['expira_em']=104
    elif defeito=='outro_owner':p['origem']='outro_owner'
    elif defeito=='sem_opcoes_entregues':
        # Simula a entrega canônica sem menu quando os nomes excedem o orçamento.
        from scripts.tests.test_opcoes_proposicao import contexto,entregar
        from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
        _,reg,f,_=contexto(monkeypatch)
        f=replace(f,qualificadores=())
        m=entregar(reg,f,realizacao_revisao_alegacao(f))
    elif defeito=='fonte_adulterada':
        i=next(i for i in m['registro_semantico']['alegacoes'] if i['id']==alvo_auxiliar(m))
        i['vinculo_resultado']['fonte']['metodo']='sensor inventado'
    elif defeito=='pergunta_alterada':m['registro_semantico']['falas_observadas'][-1]['fala']='Proposta de opções da IA.'
    else:p['status']='resolvida'
    antes=deepcopy(m['registro_semantico'])
    nova=consumir(m,'a do sensor auxiliar')
    assert nova['registro_semantico']==antes and contrato(m,'a do sensor auxiliar').get('revisao_alegacao') is None

def test_leitor_lexical_nao_resolve_elipse_fora_do_escopo(monkeypatch):
    from mente_laylay.cognicao.referencias_linguagem import referencia_nominal_proposicao
    from mente_laylay.memoria_mental.registro_semantico import selecionar_alegacao_para_revisao
    m=contexto_local(monkeypatch);texto='a do sensor auxiliar'
    assert referencia_nominal_proposicao(texto) is None
    assert referencia_nominal_proposicao(texto,permitir_elipse=True) is None
    leitura=referencia_nominal_proposicao(texto,somente_nominal=True,permitir_elipse=True)
    assert leitura.qualificador=='sensor auxiliar' and not leitura.metodo and not leitura.referencial
    assert recuperar_revisao_alegacao(m['registro_semantico'],texto,turno_id='resposta',somente_esclarecida=True) is None
    assert not selecionar_alegacao_para_revisao(m['registro_semantico'],texto,permitir_recencia=False,agora=105)['alegacao_id']

def test_autorizacao_de_outra_acao_nao_se_converte_em_selecao(monkeypatch):
    from mente_laylay.memoria_mental.registro_semantico import consumir_esclarecimento_proposicao
    m=contexto_local(monkeypatch);antes=deepcopy(m);texto='a do sensor auxiliar'
    assert consumir_esclarecimento_proposicao(m,texto,turno={'id':'ordem','autoriza_execucao':True})==antes
    assert contrato(m,texto,autoriza_execucao=True).get('revisao_alegacao') is None

@pytest.fixture(scope='module')
def elipse_instalada(tmp_path_factory):
    from scripts.tests.test_continuidade_esclarecimento import continuidade_instalada
    with pytest.MonkeyPatch.context() as m:
        m.setenv('LAYLAY_COLETAR_ELIPSE_OPCOES','1')
        if p:=os.environ.get('LAYLAY_EVIDENCIA_ELIPSE_OPCOES'):
            m.setenv('LAYLAY_EVIDENCIA_CONTINUIDADE_ESCLARECIMENTO',p)
        if caminho:=os.environ.get('LAYLAY_ELIPSE_REPLAY'):
            m.setenv('LAYLAY_CONTINUIDADE_REPLAY',caminho)
        return continuidade_instalada.__wrapped__(tmp_path_factory)

@pytest.mark.parametrize('rota',['normal','rapida'])
@pytest.mark.parametrize('cenario',['unica','ambigua'])
def test_composicao_instalada_elipse_respeita_opcoes_e_unicidade(rota,cenario,elipse_instalada):
    assert all(elipse_instalada['owners'].values())
    c,=[c for c in elipse_instalada['elipse_opcoes'] if c['rota']==rota and c['cenario']==cenario]
    a,b,*resto=c['etapas'];p=a['mental']['pendencia_atual'];reg=b['mental']['registro_semantico']
    assert len(p['opcoes'])==(2 if cenario=='unica' else 3)
    if cenario=='unica':
        assert reg['revisao_alegacao_atual'].get('alegacao_id')==c['alvo'], 'elipse única caiu fora da revisão instalada'
        assert 'está contestada' in b['textos'][0] and not b['mental']['pendencia_atual']
        assert b['mental']['ultima_pendencia_encerrada']['id']==p['id']
        assert reg['revisao_alegacao_atual']['solicitacao_original']==a['entrada']
    else:
        q=b['mental'].get('pendencia_atual') or {}
        assert q.get('id')==p['id'], 'elipse ainda ambígua virou outra conversa e perdeu pendência'
        assert q['opcoes']==p['opcoes'] and q['expira_em']==p['expira_em']
        assert reg['alegacoes']==a['mental']['registro_semantico']['alegacoes']
        assert 'Qual afirmação você quer revisar?' in b['textos'][0]
        z,=resto
        assert z['mental']['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==c['alvo']
        assert not z['mental']['pendencia_atual'] and 'está contestada' in z['textos'][0]
    assert all(len(e['textos'])==1 for e in c['etapas'])
    assert not c['executores'] and all(c[k] for k in ('historico_inalterado','receipt_inalterado',
        'publicacao_inalterada','sem_novos_efeitos'))

def coletar_composicao(root,estado,runtime,contexto,textos,RegistroModeloLLM,ResultadoModelo,
        resultado,esp,historico,publicacao):
    import json
    from types import SimpleNamespace
    from scripts.tests.test_comparacao_resultado_imediato import resultado_comparavel
    from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos
    primeiro=resultado.medicoes[0];receipt=deepcopy(resultado.como_dict());snapshot=deepcopy(publicacao.como_dict())
    sintetico=resultado_comparavel(grandeza=primeiro.grandeza,unidade=primeiro.unidade)
    m=replace(sintetico.medicoes[0],metodo='sensor auxiliar',referencial=primeiro.referencial)
    sintetico=replace(sintetico,medicoes=(m,),expectativas=(replace(sintetico.expectativas[0],referencial=m.referencial),))
    ident=sintetico.id_solicitacao+'-terceira'
    terceiro=replace(sintetico,id_solicitacao=ident,
        expectativas=(replace(sintetico.expectativas[0],ocorrencia_id=ident),),
        medicoes=(replace(m,ocorrencia_id=ident,valor=35),))
    efeitos=tuple(f for f in esp.enviados if f.startswith(('TURN ','MOTOR ','STOP ')));saida=[]
    for cenario in ('unica','ambigua'):
        fontes=(resultado,sintetico) if cenario=='unica' else (resultado,sintetico,terceiro)
        for rapido in (False,True):
            estado.atualizar_campos('mental',registro_semantico={},pendencia_atual={})
            root._iniciar_planejamento_turno('Observe as fontes deste ensaio.',origem='teste_elipse_opcoes')
            root._orquestrador_fala_runtime.falar(' '.join(fala_resultado_por_aspectos(r) for r in fontes),
                _resultados_entrega=fontes)
            reg=estado.obter_copia('mental','registro_semantico',{})
            alvo,=[i['id'] for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao'
                and i['vinculo_resultado']['id_solicitacao']==(sintetico if cenario=='unica' else resultado).id_solicitacao]
            ctx=contexto();ctx['usar_modo_rapido']=lambda _t:rapido;chamadas=[];propostas=[]
            def impedir(*_a,**_k):
                chamadas.append(True);raise AssertionError('Elipse não autoriza ação.')
            def gerar(*_a,**_k):
                propostas.append('A medição era falsa porque o sensor quebrou; vou repetir o giro.')
                antes_autoria.append({'pendencia':estado.obter_copia('mental','pendencia_atual',{}),
                    'turno':estado.obter_copia('mental','turno_atual',{}),
                    'plano':estado.obter_copia('mental','plano_turno_atual',{})})
                return ResultadoModelo(json.dumps({'fala':propostas[-1],'comandos':[]}),True)
            ctx['contexto_dispatch_runtime']=SimpleNamespace(montar=lambda:{'executar_intencao':impedir})
            runtime._contexto_getter=lambda:ctx;RegistroModeloLLM.executar=gerar;etapas=[]
            entradas=['De onde você tirou essa medição?','a do sensor auxiliar']
            if cenario=='ambigua':entradas.append('a do '+primeiro.metodo)
            try:
                for entrada in entradas:
                    inicio=len(textos);antes_autoria=[]
                    runtime.processar(entrada,origem='teste_elipse_opcoes')
                    etapas.append({'entrada':entrada,'textos':textos[inicio:],
                        'mental':estado.retrato_dominio('mental'),'antes_autoria':antes_autoria})
            finally:
                runtime._contexto_getter=contexto;RegistroModeloLLM.executar=lambda *_a,**_k:ResultadoModelo('',False)
            saida.append({'rota':'rapida' if rapido else 'normal','cenario':cenario,'etapas':etapas,'alvo':alvo,
                'propostas':propostas,'executores':chamadas,'registro_entrega':reg,
                'historico_inalterado':historico==estado.obter_copia('mental','historico_corporal',[]),
                'receipt_inalterado':receipt==resultado.como_dict(),'publicacao_inalterada':snapshot==publicacao.como_dict(),
                'sem_novos_efeitos':efeitos==tuple(f for f in esp.enviados if f.startswith(('TURN ','MOTOR ','STOP '))),
                'replay':getattr(__import__('sys'),'_elipse_replay',None)})
    return saida

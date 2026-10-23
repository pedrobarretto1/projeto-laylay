"""A resposta ainda ambígua continua a pergunta, sem virar revisão ou nova ordem."""
from copy import deepcopy
import os
import pytest

def contexto_local(monkeypatch,**campos):
    from scripts.tests.test_opcoes_proposicao import contexto,entregar
    _,reg,f,fala=contexto(monkeypatch,**campos)
    return entregar(reg,f,fala)

def contrato(m,texto='a medição',**campos):
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
    turno={'id':'resposta','texto':texto,'modalidade':'conversa','autoriza_execucao':False,
        'segmentos':[{'texto_original':texto,'modalidade':'conversa','autoriza_execucao':False}],**campos}
    m={**m,'turno_atual':turno}
    return construir_contrato_semantico_fala(texto,turno=turno,
        plano={'id':turno['id'],'texto_usuario':texto,'requer_execucao':False,'comandos':[]},mente=m)

def entregar_continuacao(m,f,*,entrega_id='repergunta'):
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
    from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada,registrar_esclarecimento_proposicao_entregue
    m={**m,'turno_atual':{'id':f.turno_consulta,'texto':f.texto_consulta}}
    m['registro_semantico']=registrar_fala_observada(m['registro_semantico'],ocorrencia_id=entrega_id,
        turno_id=f.turno_consulta,fala=realizacao_revisao_alegacao(f),resultados=(),canal='texto_publicado',agora=105)
    return registrar_esclarecimento_proposicao_entregue(m,f,entrega_id=entrega_id,turno_id=f.turno_consulta)

def test_contrato_da_conversa_nao_descarta_esclarecimento_ambiguo_entregue(monkeypatch):
    m=contexto_local(monkeypatch);antes=deepcopy(m)
    c=contrato(m);f=c.get('revisao_alegacao')
    assert f is not None, 'primeira perda local: pendência válida não chega ao contrato da conversa'
    assert f.referencia=='ambigua' and len(f.candidatos)==2
    assert m==antes and not f.autoriza_execucao

@pytest.mark.parametrize('owner,grandeza,unidade',[('executor_corpo','rotação relativa','graus'),
    ('executor_arquivos','tamanho solicitado','bytes'),('executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('texto',['a medição','essa medida','esse valor'])
def test_continuacao_ambigua_reutiliza_identidade_opcoes_e_operacao(monkeypatch,owner,grandeza,unidade,texto):
    m=contexto_local(monkeypatch,owner=owner,grandeza=grandeza,unidade=unidade);p=deepcopy(m['pendencia_atual'])
    f=contrato(m,texto)['revisao_alegacao']
    assert f.pendencia_id==p['id'] and f.tipo_revisao==p['vinculo_proposicao']['tipo_revisao']
    nova=entregar_continuacao(m,f)
    q=nova['pendencia_atual']
    assert q['id']==p['id'] and q['opcoes']==p['opcoes']
    assert q['criada_em']==p['criada_em'] and q['expira_em']==p['expira_em']
    assert q['vinculo_proposicao']['solicitacao_original']==p['vinculo_proposicao']['solicitacao_original']
    assert nova['registro_semantico']['alegacoes']==m['registro_semantico']['alegacoes']
    from scripts.tests.test_opcoes_proposicao import consumir
    final=consumir(nova,'a medição pelo método sensor auxiliar')
    assert not final['pendencia_atual'] and final['ultima_pendencia_encerrada']['id']==p['id']
    assert final['registro_semantico']['revisao_alegacao_atual']['solicitacao_original']==p['vinculo_proposicao']['solicitacao_original']

@pytest.mark.parametrize('defeito',['expirada','nao_entregue','opcao','sem_origem','outro_owner','id_invalido'])
def test_pendencia_invalida_nao_vira_fonte_de_continuacao(monkeypatch,defeito):
    m=contexto_local(monkeypatch);p=m['pendencia_atual']
    if defeito=='expirada':p['expira_em']=104
    elif defeito=='nao_entregue':p['foi_falada']=False
    elif defeito=='opcao':p['opcoes'][0]['assinatura']='proposta da IA'
    elif defeito=='sem_origem':m['registro_semantico']['falas_observadas'].pop(0)
    elif defeito=='outro_owner':p['origem']='outro_owner'
    else:p['id']=[]
    antes=deepcopy(m)
    assert contrato(m).get('revisao_alegacao') is None and m==antes

@pytest.mark.parametrize('campos',[{'autoriza_execucao':True},{'modalidade':'ordem'},
    {'segmentos':[{'texto_original':'a medição'},{'texto_original':'apague tudo'}]}])
def test_pendencia_nao_intercepta_ordem_ou_turno_composto(monkeypatch,campos):
    m=contexto_local(monkeypatch)
    assert contrato(m,**campos).get('revisao_alegacao') is None

@pytest.mark.parametrize('defeito',['id','candidatos','qualificadores','origem','tipo','sem_entrega'])
def test_entrega_da_continuacao_nao_troca_pendencia_fontes_ou_ttl(monkeypatch,defeito):
    from dataclasses import replace
    from mente_laylay.memoria_mental.registro_semantico import registrar_esclarecimento_proposicao_entregue
    m=contexto_local(monkeypatch);p=deepcopy(m['pendencia_atual']);f=contrato(m)['revisao_alegacao']
    if defeito=='id':f=replace(f,pendencia_id='outra_pendencia')
    elif defeito=='candidatos':f=replace(f,candidatos=tuple(reversed(f.candidatos)),qualificadores=tuple(reversed(f.qualificadores)))
    elif defeito=='qualificadores':f=replace(f,qualificadores=tuple((i,'metodo inventado',r) for i,_,r in f.qualificadores))
    elif defeito=='origem':f=replace(f,entrega_origem='outra_entrega')
    elif defeito=='tipo':f=replace(f,tipo_revisao='correcao')
    else:
        assert registrar_esclarecimento_proposicao_entregue(m,f,entrega_id='ausente',turno_id=f.turno_consulta)==m
        return
    nova=entregar_continuacao(m,f)
    assert nova['pendencia_atual']==p and nova['registro_semantico']['alegacoes']==m['registro_semantico']['alegacoes']

def test_varias_reperguntas_observadas_nao_renovam_ttl_nem_criam_revisao(monkeypatch):
    m=contexto_local(monkeypatch);p=deepcopy(m['pendencia_atual'])
    for i in range(3):
        f=contrato(m,'a medição',id='resposta-'+str(i))['revisao_alegacao']
        m=entregar_continuacao(m,f,entrega_id='entrega-'+str(i))
        assert m['pendencia_atual']['id']==p['id'] and m['pendencia_atual']['expira_em']==p['expira_em']
        assert all(a['status']!='contestado' for a in m['registro_semantico']['alegacoes'])

@pytest.mark.parametrize('status',['cancelada','resolvida'])
def test_entrega_tardia_da_continuacao_nao_reabre_pendencia_encerrada(monkeypatch,status):
    from mente_laylay.memoria_mental.pendencia import limpar_pendencia
    m=contexto_local(monkeypatch);f=contrato(m)['revisao_alegacao'];ident=m['pendencia_atual']['id']
    m=limpar_pendencia(m,motivo=status)
    nova=entregar_continuacao(m,f)
    assert not nova['pendencia_atual'] and nova['ultima_pendencia_encerrada']['id']==ident
    assert nova['ultima_pendencia_encerrada']['status']==status

@pytest.mark.parametrize('texto',['a medição é interessante','O que é medição?','bom dia',
    'apague a medição','não revise a medição','Traduza a medição para inglês.'])
def test_outro_ato_nao_vira_continuacao_da_pergunta(monkeypatch,texto):
    m=contexto_local(monkeypatch);antes=deepcopy(m)
    assert contrato(m,texto).get('revisao_alegacao') is None and m==antes

@pytest.fixture(scope='module')
def continuidade_instalada(tmp_path_factory):
    from scripts.tests.test_opcoes_proposicao import opcoes_instaladas
    with pytest.MonkeyPatch.context() as m:
        m.setenv('LAYLAY_COLETAR_CONTINUIDADE_ESCLARECIMENTO','1')
        if p:=os.environ.get('LAYLAY_EVIDENCIA_CONTINUIDADE_ESCLARECIMENTO'):
            m.setenv('LAYLAY_EVIDENCIA_OPCOES_PROPOSICAO',p)
        if caminho:=os.environ.get('LAYLAY_CONTINUIDADE_REPLAY'):
            from scripts.tests.test_motivo_decisao_composicao import decisao_instalada
            f=decisao_instalada.__wrapped__;cs=list(f.__code__.co_consts)
            n=next(n for n,c in enumerate(cs) if type(c) is str and 'import laylay as root' in c)
            a='        import dataclasses, json, os, sys\n';assert cs[n].count(a)==1
            cs[n]=cs[n].replace(a,a+'        import runpy\n        runpy.run_path('+repr(caminho)+')["anterior"]()\n',1)
            m.setattr(f,'__code__',f.__code__.replace(co_consts=tuple(cs)))
        return opcoes_instaladas.__wrapped__(tmp_path_factory)

@pytest.mark.parametrize('rota',['normal','rapida'])
def test_composicao_instalada_resposta_ambigua_conserva_pergunta_e_candidatos(rota,continuidade_instalada):
    assert all(continuidade_instalada['owners'].values())
    c,=[c for c in continuidade_instalada['continuidade_esclarecimento'] if c['rota']==rota]
    a,b,z=c['etapas'];p=a['mental']['pendencia_atual'];novo=b['mental'].get('pendencia_atual') or {}
    assert len(p['opcoes'])==2 and len(a['textos'])==len(b['textos'])==1
    assert 'Qual afirmação você quer revisar?' in b['textos'][0], 'primeira perda: resposta nominal ainda ambígua cai em conversa independente'
    assert novo.get('id')==p['id'] and novo['opcoes']==p['opcoes']
    assert novo['criada_em']==p['criada_em'] and novo['expira_em']==p['expira_em']
    assert novo['vinculo_proposicao']['solicitacao_original']==a['entrada']
    assert b['mental']['registro_semantico']['alegacoes']==a['mental']['registro_semantico']['alegacoes']
    assert z['mental']['registro_semantico']['revisao_alegacao_atual'].get('alegacao_id')==c['alvo']
    assert 'está contestada' in z['textos'][0] and not z['mental']['pendencia_atual']
    assert z['mental']['ultima_pendencia_encerrada']['id']==p['id']
    assert all(c[k] for k in ('historico_inalterado','receipt_inalterado','publicacao_inalterada','sem_novos_efeitos'))
    assert not c['executores']

def coletar_composicao(root,estado,runtime,contexto,textos,RegistroModeloLLM,ResultadoModelo,
        resultado,esp,historico,publicacao):
    import json
    from dataclasses import replace
    from types import SimpleNamespace
    from scripts.tests.test_comparacao_resultado_imediato import resultado_comparavel
    from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos
    primeiro=resultado.medicoes[0];receipt=deepcopy(resultado.como_dict());snapshot=deepcopy(publicacao.como_dict())
    sintetico=resultado_comparavel(grandeza=primeiro.grandeza,unidade=primeiro.unidade)
    m=replace(sintetico.medicoes[0],metodo='sensor auxiliar',referencial=primeiro.referencial)
    sintetico=replace(sintetico,medicoes=(m,),expectativas=(replace(sintetico.expectativas[0],referencial=m.referencial),))
    efeitos=tuple(f for f in esp.enviados if f.startswith(('TURN ','MOTOR ','STOP ')));saida=[]
    for rapido in (False,True):
        estado.atualizar_campos('mental',registro_semantico={},pendencia_atual={})
        root._iniciar_planejamento_turno('Observe as fontes deste ensaio.',origem='teste_continuidade_esclarecimento')
        root._orquestrador_fala_runtime.falar(' '.join(fala_resultado_por_aspectos(r) for r in (resultado,sintetico)),
            _resultados_entrega=(resultado,sintetico))
        reg=estado.obter_copia('mental','registro_semantico',{})
        alvo,=[i['id'] for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao'
            and i['vinculo_resultado']['id_solicitacao']==resultado.id_solicitacao]
        ctx=contexto();ctx['usar_modo_rapido']=lambda _t:rapido;chamadas=[];propostas=[]
        def impedir(*_a,**_k):
            chamadas.append(True);raise AssertionError('Ambiguidade não autoriza ação.')
        def gerar(*_a,**_k):
            propostas.append('A medição era falsa porque o sensor quebrou; vou repetir o giro.')
            antes_autoria.append({'pendencia':estado.obter_copia('mental','pendencia_atual',{}),
                'turno':estado.obter_copia('mental','turno_atual',{}),
                'plano':estado.obter_copia('mental','plano_turno_atual',{})})
            return ResultadoModelo(json.dumps({'fala':propostas[-1],'comandos':[]}),True)
        ctx['contexto_dispatch_runtime']=SimpleNamespace(montar=lambda:{'executar_intencao':impedir})
        runtime._contexto_getter=lambda:ctx;RegistroModeloLLM.executar=gerar;etapas=[]
        try:
            for entrada in ('De onde você tirou essa medição?','a medição','a medição pelo método '+primeiro.metodo):
                inicio=len(textos);antes_autoria=[]
                runtime.processar(entrada,origem='teste_continuidade_esclarecimento')
                etapas.append({'entrada':entrada,'textos':textos[inicio:],'mental':estado.retrato_dominio('mental'),
                    'antes_autoria':antes_autoria})
        finally:
            runtime._contexto_getter=contexto;RegistroModeloLLM.executar=lambda *_a,**_k:ResultadoModelo('',False)
        saida.append({'rota':'rapida' if rapido else 'normal','etapas':etapas,'alvo':alvo,
            'propostas':propostas,'executores':chamadas,'registro_entrega':reg,
            'historico_inalterado':historico==estado.obter_copia('mental','historico_corporal',[]),
            'receipt_inalterado':receipt==resultado.como_dict(),'publicacao_inalterada':snapshot==publicacao.como_dict(),
            'sem_novos_efeitos':efeitos==tuple(f for f in esp.enviados if f.startswith(('TURN ','MOTOR ','STOP '))),
            'replay':getattr(__import__('sys'),'_continuidade_replay',None)})
    return saida

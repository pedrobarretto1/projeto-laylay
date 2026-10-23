"""Qualificador seleciona identidade da fonte; nunca certifica seu conteúdo."""
from copy import deepcopy
from dataclasses import replace
import os
import pytest

from mente_laylay.memoria_mental.registro_semantico import (
    registrar_fala_observada, selecionar_alegacao_para_revisao,
    contestar_alegacao_recente, recuperar_revisao_alegacao,
    registrar_esclarecimento_proposicao_entregue, consumir_esclarecimento_proposicao,
    avaliar_suporte_alegacao,
)


def duas_fontes(*,owner='executor_corpo',grandeza='rotação relativa',unidade='graus'):
    from scripts.tests.test_comparacao_resultado_imediato import resultado_comparavel
    r=resultado_comparavel(owner=owner,grandeza=grandeza,unidade=unidade)
    e,=r.expectativas;m,=r.medicoes
    return replace(r,expectativas=(e,replace(e,grandeza='duração observada',unidade='segundos',valor=10)),
        medicoes=(m,replace(m,grandeza='duração observada',unidade='segundos',valor=4)))


def publicar(r):
    from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos
    return registrar_fala_observada(None,ocorrencia_id='fonte',turno_id='execucao',
        fala=fala_resultado_por_aspectos(r),resultados=(r,),canal='texto_publicado',agora=104)


def pendente(monkeypatch,r,*,texto='De onde você tirou essa medição?'):
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:105)
    reg=contestar_alegacao_recente(publicar(r),texto,agora=105)
    f=recuperar_revisao_alegacao(reg,texto,turno_id='pergunta')
    assert f.candidatos
    reg=registrar_fala_observada(reg,ocorrencia_id='pergunta-observada',turno_id='pergunta',
        fala=realizacao_revisao_alegacao(f),resultados=(),canal='texto_publicado',agora=105)
    return registrar_esclarecimento_proposicao_entregue(
        {'registro_semantico':reg,'turno_atual':{'id':'pergunta','texto':texto}},f,
        entrega_id='pergunta-observada',turno_id='pergunta')


def consumir(m,texto):
    return consumir_esclarecimento_proposicao(m,texto,turno={'id':'resposta','texto':texto,
        'autoriza_execucao':False,'encerramento_assunto':''})


def grandeza_proposicao(i):
    f=i['vinculo_resultado']['fonte']
    return (f.get('expectativa') or f)['grandeza']


@pytest.mark.parametrize('owner,grandeza,unidade',[
    ('executor_corpo','rotação relativa','graus'),('executor_arquivos','tamanho solicitado','bytes'),
    ('executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('nome,papel',[('meta','meta'),('medição','medicao'),('diferença','comparacao')])
def test_qualificador_exato_seleciona_fonte_do_papel_sem_recencia(owner,grandeza,unidade,nome,papel):
    reg=publicar(duas_fontes(owner=owner,grandeza=grandeza,unidade=unidade));antes=deepcopy(reg)
    alvo,=[i for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']==papel and grandeza_proposicao(i)==grandeza]
    s=selecionar_alegacao_para_revisao(reg,'De onde você tirou essa '+nome+' de '+grandeza+'?',agora=105)
    assert s['referencia']=='unica' and s['alegacao_id']==alvo['id'], 'primeira perda: leitor descarta qualificador existente na fonte entregue'
    assert not s['autoriza_execucao'] and reg==antes


@pytest.mark.parametrize('expressao',['a medição de rotação relativa','essa medida da rotação relativa',
    'a MEDICAO de ROTACAO RELATIVA','a medição de duração observada'])
def test_elipse_qualificada_revisa_so_fonte_escolhida_e_restringe_suporte(monkeypatch,expressao):
    r=duas_fontes();m=pendente(monkeypatch,r);antes=deepcopy(m);receipt=r.como_dict()
    nova=consumir(m,expressao);reg=nova['registro_semantico']
    g='duração observada' if 'duração' in expressao else 'rotação relativa'
    alvo,=[i for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao' and grandeza_proposicao(i)==g]
    assert reg['revisao_alegacao_atual'].get('alegacao_id')==alvo['id'], 'elipse qualificada não chega à revisão compartilhada'
    assert alvo['status']=='contestado' and not nova['pendencia_atual']
    assert reg['revisao_alegacao_atual']['solicitacao_original']=='De onde você tirou essa medição?'
    for i in reg['alegacoes']:
        if i['id']!=alvo['id']:
            assert i==next(a for a in antes['registro_semantico']['alegacoes'] if a['id']==i['id'])
        if i['vinculo_resultado']['tipo']=='comparacao':
            assert (avaliar_suporte_alegacao(reg,i['id'])['estado']=='suporte_em_revisao')==(grandeza_proposicao(i)==g)
    assert m==antes and r.como_dict()==receipt and not recuperar_revisao_alegacao(
        reg,expressao,turno_id='resposta',somente_esclarecida=True).autoriza_execucao


@pytest.mark.parametrize('texto',['a medição','a medição de rotação','a medição de duração',
    'a medição de rotação relativa anterior','a medição de rotacão relativaa',
    'a medição de velocidade','a medição de rotação relativa e apaga tudo',
    'apaga a medição de rotação relativa','O que é a medição de rotação relativa?',
    'a medição de rotação relativa porque o sensor quebrou','a medição de rotação relativa ou duração observada'])
def test_sem_qualificador_integral_unico_nao_consume_revisa_ou_autoriza(monkeypatch,texto):
    m=pendente(monkeypatch,duas_fontes());antes=deepcopy(m)
    assert consumir(m,texto)==antes


def test_grandeza_igual_em_fontes_distintas_permanece_ambigua(monkeypatch):
    r=duas_fontes();m0=r.medicoes[0]
    r=replace(r,expectativas=r.expectativas[:1],medicoes=(m0,replace(m0,metodo='outro_metodo',valor=30)))
    reg=publicar(r)
    s=selecionar_alegacao_para_revisao(reg,'De onde você tirou essa medição de rotação relativa?',agora=105)
    assert s['referencia']=='ambigua' and not s['alegacao_id']
    m=pendente(monkeypatch,r,texto='De onde você tirou essa medição de rotação relativa?')
    assert len(m['pendencia_atual']['opcoes'])==2
    assert consumir(m,'a medição de rotação relativa')==m


def test_normalizacao_nao_deduplica_duas_fontes_em_falsa_unicidade():
    r=duas_fontes();e0,e1=r.expectativas;m0,m1=r.medicoes
    r=replace(r,expectativas=(e0,replace(e1,grandeza='rotacao relativa')),
        medicoes=(m0,replace(m1,grandeza='rotacao relativa')))
    s=selecionar_alegacao_para_revisao(publicar(r),'De onde você tirou essa medição de rotação relativa?',agora=105)
    assert s['referencia']=='ambigua' and not s['alegacao_id']


def test_identidade_literal_ja_resolve_mesmos_candidatos_sem_qualificador(monkeypatch):
    m=pendente(monkeypatch,duas_fontes())
    ident=m['pendencia_atual']['opcoes'][0]['alegacao_id']
    nova=consumir(m,ident)
    assert nova['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==ident
    assert not nova['pendencia_atual']


def test_pergunta_qualificada_preserva_conjunto_integral_do_seu_recorte(monkeypatch):
    r=duas_fontes();m0,m1=r.medicoes
    r=replace(r,medicoes=(m0,replace(m0,metodo='outro_metodo',valor=30),m1))
    m=pendente(monkeypatch,r,texto='De onde você tirou essa medição de rotação relativa?')
    p=m['pendencia_atual']
    assert len(p['opcoes'])==2
    assert consumir(m,'a medição de duração observada')==m, 'qualificador não amplia candidatos da pergunta'
    assert consumir(m,'a medição de rotação relativa')==m, 'dois métodos não se tornam um só referente'


@pytest.mark.parametrize('defeito',['nome','fonte','opcoes','ultima_entrega'])
def test_qualificador_nao_contorna_integridade_escopo_ou_entrega(monkeypatch,defeito):
    m=pendente(monkeypatch,duas_fontes());reg=m['registro_semantico']
    ident=m['pendencia_atual']['opcoes'][0]['alegacao_id']
    item,=[i for i in reg['alegacoes'] if i['id']==ident]
    if defeito=='nome':
        item['texto']='Outra alegação de rotação relativa'
    elif defeito=='fonte':
        item['vinculo_resultado']['fonte']['grandeza']='rotação relativa adulterada'
    elif defeito=='opcoes':m['pendencia_atual']['opcoes'].pop()
    else:reg['falas_observadas'][-1]['id']='entrega_alheia'
    antes=deepcopy(reg)
    nova=consumir(m,'a medição de rotação relativa')
    assert nova['registro_semantico']==antes and not nova['pendencia_atual']
    assert nova['ultima_pendencia_encerrada']['status']=='fonte_invalida_ou_expirada'


@pytest.fixture(scope='module')
def qualificador_instalado(tmp_path_factory):
    from scripts.tests.test_esclarecimento_proposicao import esclarecimento_instalado
    with pytest.MonkeyPatch.context() as m:
        m.setenv('LAYLAY_COLETAR_QUALIFICADOR_PROPOSICAO','1')
        if p:=os.environ.get('LAYLAY_EVIDENCIA_QUALIFICADOR_PROPOSICAO'):
            m.setenv('LAYLAY_EVIDENCIA_ESCLARECIMENTO_PROPOSICAO',p)
        if caminho:=os.environ.get('LAYLAY_QUALIFICADOR_REPLAY'):
            from scripts.tests.test_motivo_decisao_composicao import decisao_instalada
            f=decisao_instalada.__wrapped__;cs=list(f.__code__.co_consts)
            n=next(n for n,c in enumerate(cs) if type(c) is str and 'import laylay as root' in c)
            a='        import dataclasses, json, os, sys\n';assert cs[n].count(a)==1
            cs[n]=cs[n].replace(a,a+'        import runpy\n        runpy.run_path('+repr(caminho)+')["anterior"]()\n',1)
            m.setattr(f,'__code__',f.__code__.replace(co_consts=tuple(cs)))
        return esclarecimento_instalado.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('rota',['normal','rapida'])
def test_composicao_instalada_retem_duas_medicoes_e_consumo_qualificado(rota,qualificador_instalado):
    d=qualificador_instalado;assert all(d['owners'].values())
    c,=[c for c in d['qualificador_proposicao'] if c['rota']==rota]
    a,b=c['etapas'];p=a['mental']['pendencia_atual']
    assert p['origem']=='revisao_alegacao' and len(p['opcoes'])==2
    assert len(a['textos'])==len(b['textos'])==1
    reg=b['mental']['registro_semantico'];alvo=c['alvo']
    assert reg['revisao_alegacao_atual'].get('alegacao_id')==alvo, 'composição instalada perde qualificador da fonte'
    assert 'está contestada' in b['textos'][0] and not b['mental']['pendencia_atual']
    assert b['mental']['ultima_pendencia_encerrada']['id']==p['id']
    assert reg['revisao_alegacao_atual']['solicitacao_original']==a['entrada']
    assert all(i['status']=='observacao_registrada' for i in reg['alegacoes']
        if i['vinculo_resultado']['tipo']=='medicao' and i['id']!=alvo)
    assert c['historico_inalterado'] and c['receipt_inalterado'] and c['publicacao_inalterada']
    assert c['sem_novos_efeitos'] and not c['executores']


def coletar_composicao(root,estado,runtime,contexto,textos,RegistroModeloLLM,ResultadoModelo,
        resultado,esp,historico,publicacao):
    """Composição instalada; duas fontes controladas na porta de entrega tipada.

    A segunda grandeza é um dado experimental, não uma leitura física do corpo.
    Nenhuma afirmação de aferição é inferida desta prova.
    """
    import json
    from types import SimpleNamespace
    from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos
    from scripts.tests.test_comparacao_resultado_imediato import resultado_comparavel
    m,=resultado.medicoes
    receipt=deepcopy(resultado.como_dict());snapshot=deepcopy(publicacao.como_dict())
    assert resultado.id_solicitacao==snapshot['id_solicitacao']
    r=resultado_comparavel(owner='executor_temporal',grandeza='duração observada',unidade='segundos')
    efeitos=tuple(f for f in esp.enviados if f.startswith(('TURN ','MOTOR ','STOP ')))
    saida=[]
    for rapido in (False,True):
        estado.atualizar_campos('mental',registro_semantico={},pendencia_atual={})
        root._iniciar_planejamento_turno('Observe as fontes deste ensaio.',origem='teste_qualificador')
        root._orquestrador_fala_runtime.falar(fala_resultado_por_aspectos(resultado)+' '+fala_resultado_por_aspectos(r),
            _resultados_entrega=(resultado,r))
        reg=estado.obter_copia('mental','registro_semantico',{})
        alvo,=[i['id'] for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao'
            and grandeza_proposicao(i)==m.grandeza]
        ctx=contexto();ctx['usar_modo_rapido']=lambda _t:rapido
        chamadas=[];propostas=[]
        def impedir(*_a,**_k):
            chamadas.append(True);raise AssertionError('Qualificador não autoriza execução.')
        def gerar(*_a,**_k):
            propostas.append('O sensor quebrou; vou refazer o giro.')
            return ResultadoModelo(json.dumps({'fala':propostas[-1],'comandos':[]}),True)
        ctx['contexto_dispatch_runtime']=SimpleNamespace(montar=lambda:{'executar_intencao':impedir})
        runtime._contexto_getter=lambda:ctx
        RegistroModeloLLM.executar=gerar;etapas=[]
        try:
            for entrada in ('De onde você tirou essa medição?','a medição de '+m.grandeza):
                inicio=len(textos);runtime.processar(entrada,origem='teste_qualificador')
                etapas.append({'entrada':entrada,'textos':textos[inicio:],'mental':estado.retrato_dominio('mental')})
        finally:
            runtime._contexto_getter=contexto
            RegistroModeloLLM.executar=lambda *_a,**_k:ResultadoModelo('',False)
        saida.append({'rota':'rapida' if rapido else 'normal','etapas':etapas,'alvo':alvo,
            'fontes_controladas':r.como_dict(),'registro_entrega':reg,'propostas':propostas,'executores':chamadas,
            'historico_inalterado':historico==estado.obter_copia('mental','historico_corporal',[]),
            'receipt_inalterado':receipt==resultado.como_dict(),
            'publicacao_inalterada':snapshot==publicacao.como_dict(),
            'receipt_capturado':receipt,'snapshot_publicado':snapshot,
            'sem_novos_efeitos':efeitos==tuple(f for f in esp.enviados if f.startswith(('TURN ','MOTOR ','STOP '))),
            'replay':getattr(__import__('sys'),'_qualificador_replay',None)})
    return saida

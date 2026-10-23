"""Opções próprias da fonte precisam ser entregues antes da resposta elíptica."""
from copy import deepcopy
from dataclasses import replace
import os
import pytest
from mente_laylay.memoria_mental.registro_semantico import (
    registrar_fala_observada,contestar_alegacao_recente,recuperar_revisao_alegacao,
    registrar_esclarecimento_proposicao_entregue,consumir_esclarecimento_proposicao,
    avaliar_suporte_alegacao,selecionar_alegacao_para_revisao,
)

def par_fontes(campo='metodo',*,owner='executor_corpo',grandeza='rotação relativa',unidade='graus'):
    from scripts.tests.test_comparacao_resultado_imediato import resultado_comparavel
    a=resultado_comparavel(owner=owner,grandeza=grandeza,unidade=unidade)
    e,=a.expectativas;m,=a.medicoes;ident=a.id_solicitacao+'-segunda'
    campos={campo:'sensor auxiliar' if campo=='metodo' else 'referencia auxiliar'}
    medida=replace(m,ocorrencia_id=ident,valor=30,**campos)
    meta=replace(e,ocorrencia_id=ident,referencial=medida.referencial)
    return a,replace(a,id_solicitacao=ident,expectativas=(meta,),medicoes=(medida,))

def publicar(fontes):
    from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos
    return registrar_fala_observada(None,ocorrencia_id='fonte',turno_id='execucao',
        fala=' '.join(fala_resultado_por_aspectos(r) for r in fontes),resultados=fontes,
        canal='texto_publicado',agora=104)

def contexto(monkeypatch,campo='metodo',**campos):
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:105)
    fontes=par_fontes(campo,**campos);texto='De onde você tirou essa medição?'
    reg=contestar_alegacao_recente(publicar(fontes),texto,agora=105)
    f=recuperar_revisao_alegacao(reg,texto,turno_id='pergunta');fala=realizacao_revisao_alegacao(f)
    return fontes,reg,f,fala

def entregar(reg,f,fala):
    reg=registrar_fala_observada(reg,ocorrencia_id='pergunta',turno_id='pergunta',
        fala=fala,resultados=(),canal='texto_publicado',agora=105)
    return registrar_esclarecimento_proposicao_entregue(
        {'registro_semantico':reg,'turno_atual':{'id':'pergunta','texto':f.texto_consulta}},
        f,entrega_id='pergunta',turno_id='pergunta')

def consumir(m,texto):
    return consumir_esclarecimento_proposicao(m,texto,turno={'id':'resposta','texto':texto,
        'autoriza_execucao':False,'encerramento_assunto':''})

@pytest.mark.parametrize('campo',['metodo','referencial'])
def test_opcoes_da_fonte_chegam_inteiras_a_pergunta(monkeypatch,campo):
    fontes,reg,f,fala=contexto(monkeypatch,campo)
    assert len(f.candidatos)==2 and len(reg['falas_observadas'])==1
    assert len(getattr(f,'qualificadores',()))==2, 'primeira perda: fonte da pergunta descarta qualificadores dos candidatos'
    assert all(getattr(r.medicoes[0],campo) in fala for r in fontes)
    assert len(fala)<=500 and 'Qual afirmação você quer revisar?' in fala
    m=entregar(reg,f,fala);p=m['pendencia_atual']
    assert p['conteudo']==fala and len(p['opcoes'])==2 and p['autoriza_execucao'] is False

@pytest.mark.parametrize('owner,grandeza,unidade',[('executor_corpo','rotação relativa','graus'),
    ('executor_arquivos','tamanho solicitado','bytes'),('executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('campo,molde',[('metodo','a medição pelo método '),('referencial','a medição no referencial ')])
def test_elipse_por_fonte_preserva_identidade_operacao_e_suportes(monkeypatch,owner,grandeza,unidade,campo,molde):
    fontes,reg,f,fala=contexto(monkeypatch,campo,owner=owner,grandeza=grandeza,unidade=unidade)
    m=entregar(reg,f,fala);antes=deepcopy(m);receipts=deepcopy([r.como_dict() for r in fontes])
    entrada=molde+getattr(fontes[0].medicoes[0],campo)
    nova=consumir(m,entrada);r=nova['registro_semantico']
    alvo,=[i for i in r['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao'
        and i['vinculo_resultado']['id_solicitacao']==fontes[0].id_solicitacao]
    assert r['revisao_alegacao_atual'].get('alegacao_id')==alvo['id'], 'qualificador entregue não chega à revisão comum'
    assert alvo['status']=='contestado' and not nova['pendencia_atual']
    assert nova['ultima_pendencia_encerrada']['id']==m['pendencia_atual']['id']
    assert r['revisao_alegacao_atual']['solicitacao_original']==f.texto_consulta
    for i in r['alegacoes']:
        if i['id']!=alvo['id']:assert i==next(a for a in antes['registro_semantico']['alegacoes'] if a['id']==i['id'])
        if i['vinculo_resultado']['tipo']=='comparacao':
            assert (avaliar_suporte_alegacao(r,i['id'])['estado']=='suporte_em_revisao')==(
                i['vinculo_resultado']['id_solicitacao']==fontes[0].id_solicitacao)
    assert m==antes and [r.como_dict() for r in fontes]==receipts

def test_ids_ja_resolvem_e_numeros_nao_foram_perdidos(monkeypatch):
    fontes,reg,f,fala=contexto(monkeypatch)
    assert all(r.medicoes[0].grandeza in reg['falas_observadas'][0]['fala'] for r in fontes)
    assert all(r.medicoes[0].metodo not in reg['falas_observadas'][0]['fala'] for r in fontes)
    m=entregar(reg,f,fala);ident=m['pendencia_atual']['opcoes'][0]['alegacao_id']
    assert consumir(m,ident)['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==ident

@pytest.mark.parametrize('texto',['a medição','a medição de rotação relativa','sensor auxiliar',
    'a medição pelo método sensor','a medição pelo método sensor auxiliarr',
    'apague a medição pelo método sensor auxiliar','a medição pelo método sensor auxiliar e repita o giro',
    'a medição no referencial inventado','a medição pelo método sensor auxiliar porque houve pane'])
def test_referencia_incompleta_ou_outra_acao_nao_consume(monkeypatch,texto):
    _,reg,f,fala=contexto(monkeypatch);m=entregar(reg,f,fala);antes=deepcopy(m)
    assert consumir(m,texto)==antes

def test_opcoes_grandes_nao_sao_cortadas_nem_admitem_campo_nao_entregue(monkeypatch):
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:105)
    a,b=par_fontes();a=replace(a,medicoes=(replace(a.medicoes[0],metodo='a'*230),))
    b=replace(b,medicoes=(replace(b.medicoes[0],metodo='b'*230),))
    texto='De onde você tirou essa medição?';reg=contestar_alegacao_recente(publicar((a,b)),texto,agora=105)
    f=recuperar_revisao_alegacao(reg,texto,turno_id='pergunta');fala=realizacao_revisao_alegacao(f)
    assert len(f.qualificadores)==2 and len(fala)<=500 and 'Opções de medição:' not in fala
    m=entregar(reg,f,fala)
    assert m['pendencia_atual']['conteudo']==fala
    assert not m['pendencia_atual']['vinculo_proposicao'].get('qualificadores')
    assert consumir(m,'a medição pelo método '+'a'*230)==m
    ident=m['pendencia_atual']['opcoes'][0]['alegacao_id']
    assert consumir(m,ident)['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==ident

@pytest.mark.parametrize('defeito',['valor','identidade','parcial','outra_entrega','texto_da_entrega','sem_entrega'])
def test_opcoes_adulteradas_nao_substituem_fontes_ou_publicacao(monkeypatch,defeito):
    _,reg,f,fala=contexto(monkeypatch);m=entregar(reg,f,fala)
    v=m['pendencia_atual']['vinculo_proposicao']
    if defeito=='valor':v['qualificadores'][0][1]='sensor inventado'
    elif defeito=='identidade':v['qualificadores'][0][0]='alegacao:123'
    elif defeito=='parcial':v['qualificadores'].pop()
    elif defeito=='outra_entrega':v['opcoes_entrega_id']='entrega_alheia'
    elif defeito=='texto_da_entrega':m['registro_semantico']['falas_observadas'][-1]['fala']='Outra pergunta.'
    else:v.pop('opcoes_entrega_id')
    antes=deepcopy(m['registro_semantico'])
    nova=consumir(m,'a medição pelo método sensor auxiliar')
    assert nova['registro_semantico']==antes and not nova['pendencia_atual']
    assert nova['ultima_pendencia_encerrada']['status']=='fonte_invalida_ou_expirada'

def test_proposta_json_nao_cria_fonte_tipificada_ou_pendencia(monkeypatch):
    from dataclasses import asdict
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
    _,reg,f,fala=contexto(monkeypatch);m=entregar(reg,f,fala)
    m['pendencia_atual']={};antes=deepcopy(m)
    assert registrar_esclarecimento_proposicao_entregue(m,asdict(f),entrega_id='pergunta',turno_id='pergunta')==antes
    assert realizacao_revisao_alegacao(asdict(f))==''

@pytest.mark.parametrize('texto,unica',[
    ('a medição de rotação relativa pelo método sensor auxiliar no referencial referencia auxiliar',True),
    ('a medição pelo método sensor auxiliar e no referencial referencia auxiliar',True),
    ('a medição no referencial referencia auxiliar e pelo método sensor auxiliar',True),
    ('essa medida no referencial referencia auxiliar pelo método sensor auxiliar',True),
    ('a MEDICAO pelo METODO SENSOR AUXILIAR',True),
    ('a medição pelo método sensor auxiliar no referencial referencia_do_owner_v1',False),
    ('a medição pelo método sensor auxiliar pelo método sensor auxiliar',False),
    ('a medição no referencial referencia auxiliar no referencial referencia auxiliar',False)])
def test_qualificadores_explicitos_sao_conjuncao_sem_aproximacao(monkeypatch,texto,unica):
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:105)
    a,b=par_fontes();m=replace(b.medicoes[0],referencial='referencia auxiliar')
    b=replace(b,medicoes=(m,),expectativas=(replace(b.expectativas[0],referencial=m.referencial),))
    pergunta='De onde você tirou essa medição?';reg=contestar_alegacao_recente(publicar((a,b)),pergunta,agora=105)
    f=recuperar_revisao_alegacao(reg,pergunta,turno_id='pergunta')
    atual=entregar(reg,f,realizacao_revisao_alegacao(f));nova=consumir(atual,texto)
    if not unica:assert nova==atual
    else:
        alvo,=[i for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao'
            and i['vinculo_resultado']['id_solicitacao']==b.id_solicitacao]
        assert nova['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==alvo['id']

def test_metodo_igual_em_duas_fontes_nao_vira_unicidade(monkeypatch):
    a,b=par_fontes();c=replace(b,id_solicitacao=b.id_solicitacao+'-terceira',
        expectativas=(replace(b.expectativas[0],ocorrencia_id=b.id_solicitacao+'-terceira'),),
        medicoes=(replace(b.medicoes[0],ocorrencia_id=b.id_solicitacao+'-terceira',valor=35),))
    reg=publicar((a,b,c))
    s=selecionar_alegacao_para_revisao(reg,'De onde você tirou essa medição pelo método sensor auxiliar?',agora=105)
    assert s['referencia']=='ambigua' and not s['alegacao_id']

def test_nomes_de_metodo_normalizados_iguais_nao_sao_desempate():
    a,b=par_fontes();a=replace(a,medicoes=(replace(a.medicoes[0],metodo='método óptico'),))
    b=replace(b,medicoes=(replace(b.medicoes[0],metodo='metodo optico'),))
    reg=publicar((a,b));s=selecionar_alegacao_para_revisao(reg,
        'De onde você tirou essa medição pelo método metodo optico?',agora=105)
    assert s['referencia']=='ambigua' and not s['alegacao_id']

def test_referencial_ausente_na_fonte_nao_e_inventado_para_a_pergunta(monkeypatch):
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:105)
    a,b=par_fontes('referencial');b=replace(b,medicoes=(replace(b.medicoes[0],referencial=''),),
        expectativas=(replace(b.expectativas[0],referencial=''),))
    reg=contestar_alegacao_recente(publicar((a,b)),'De onde você tirou essa medição?',agora=105)
    f=recuperar_revisao_alegacao(reg,'De onde você tirou essa medição?',turno_id='pergunta')
    assert not f.qualificadores
    m=entregar(reg,f,realizacao_revisao_alegacao(f))
    assert consumir(m,'a medição no referencial referencia_do_owner_v1')==m

@pytest.mark.parametrize('campo,molde',[('metodo','pelo método '),('referencial','no referencial ')])
def test_consulta_direta_usa_os_mesmos_campos_e_fontes(campo,molde):
    fontes=par_fontes(campo);reg=publicar(fontes)
    s=selecionar_alegacao_para_revisao(reg,'De onde você tirou essa medição '+molde+getattr(fontes[0].medicoes[0],campo)+'?',agora=105)
    alvo,=[i for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao'
        and i['vinculo_resultado']['id_solicitacao']==fontes[0].id_solicitacao]
    assert s['referencia']=='unica' and s['alegacao_id']==alvo['id'] and not s['autoriza_execucao']

@pytest.mark.parametrize('papel,nome,campo,molde,unica',[
    ('meta','meta','metodo','pelo método ',False),
    ('comparacao','diferença','metodo','pelo método ',True),
    ('meta','meta','referencial','no referencial ',True),
    ('comparacao','diferença','referencial','no referencial ',True)])
def test_campo_pertence_a_premissa_correta_da_proposicao(papel,nome,campo,molde,unica):
    fontes=par_fontes(campo);reg=publicar(fontes)
    texto='De onde você tirou essa '+nome+' '+molde+getattr(fontes[0].medicoes[0],campo)+'?'
    s=selecionar_alegacao_para_revisao(reg,texto,agora=105)
    if not unica:assert not s['alegacao_id'] and s['referencia']=='ausente'
    else:
        alvo,=[i for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']==papel
            and i['vinculo_resultado']['id_solicitacao']==fontes[0].id_solicitacao]
        assert s['referencia']=='unica' and s['alegacao_id']==alvo['id']

def test_repergunta_entregue_conserva_origem_das_opcoes_sem_renovar_ttl(monkeypatch):
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
    _,reg,f,fala=contexto(monkeypatch);m=entregar(reg,f,fala);p=deepcopy(m['pendencia_atual'])
    texto='essa medição';f2=recuperar_revisao_alegacao(m['registro_semantico'],texto,turno_id='repergunta')
    fala2=realizacao_revisao_alegacao(f2)
    m['turno_atual']={'id':'repergunta','texto':texto}
    m['registro_semantico']=registrar_fala_observada(m['registro_semantico'],ocorrencia_id='repergunta',
        turno_id='repergunta',fala=fala2,resultados=(),canal='texto_publicado',agora=105)
    m=registrar_esclarecimento_proposicao_entregue(m,f2,entrega_id='repergunta',turno_id='repergunta')
    assert m['pendencia_atual']['id']==p['id'] and m['pendencia_atual']['expira_em']==p['expira_em']
    assert m['pendencia_atual']['vinculo_proposicao']['opcoes_entrega_id']=='pergunta'
    assert not consumir(m,'a medição pelo método sensor auxiliar')['pendencia_atual']

@pytest.fixture(scope='module')
def opcoes_instaladas(tmp_path_factory):
    from scripts.tests.test_qualificador_proposicao import qualificador_instalado
    with pytest.MonkeyPatch.context() as m:
        m.setenv('LAYLAY_COLETAR_OPCOES_PROPOSICAO','1')
        if p:=os.environ.get('LAYLAY_EVIDENCIA_OPCOES_PROPOSICAO'):
            m.setenv('LAYLAY_EVIDENCIA_QUALIFICADOR_PROPOSICAO',p)
        if caminho:=os.environ.get('LAYLAY_OPCOES_REPLAY'):
            from scripts.tests.test_motivo_decisao_composicao import decisao_instalada
            f=decisao_instalada.__wrapped__;cs=list(f.__code__.co_consts)
            n=next(n for n,c in enumerate(cs) if type(c) is str and 'import laylay as root' in c)
            a='        import dataclasses, json, os, sys\n';assert cs[n].count(a)==1
            cs[n]=cs[n].replace(a,a+'        import runpy\n        runpy.run_path('+repr(caminho)+')["anterior"]()\n',1)
            m.setattr(f,'__code__',f.__code__.replace(co_consts=tuple(cs)))
        return qualificador_instalado.__wrapped__(tmp_path_factory)

@pytest.mark.parametrize('rota',['normal','rapida'])
@pytest.mark.parametrize('campo',['metodo','referencial'])
def test_composicao_instalada_entrega_opcoes_antes_de_revisar(rota,campo,opcoes_instaladas):
    assert all(opcoes_instaladas['owners'].values())
    c,=[c for c in opcoes_instaladas['opcoes_proposicao'] if c['rota']==rota and c['campo']==campo]
    a,b=c['etapas'];p=a['mental']['pendencia_atual'];reg=b['mental']['registro_semantico']
    assert len(p['opcoes'])==2 and len(a['textos'])==len(b['textos'])==1
    assert all(valor in a['textos'][0] for valor in c['valores']), 'primeira perda instalada: pergunta não apresenta qualificadores da fonte'
    assert p['conteudo']==a['textos'][0] and len(p['conteudo'])<=500
    assert reg['revisao_alegacao_atual'].get('alegacao_id')==c['alvo']
    assert 'está contestada' in b['textos'][0] and not b['mental']['pendencia_atual']
    assert b['mental']['ultima_pendencia_encerrada']['id']==p['id']
    assert all(c[k] for k in ('historico_inalterado','receipt_inalterado','publicacao_inalterada','sem_novos_efeitos'))
    assert not c['executores']

@pytest.mark.parametrize('rota',['normal','rapida'])
def test_orcamento_instalado_nao_trunca_opcoes_e_conserva_selecao_por_id(rota,opcoes_instaladas):
    c,=[c for c in opcoes_instaladas['opcoes_proposicao'] if c['rota']==rota and c['campo']=='limite']
    a,b=c['etapas'];p=a['mental']['pendencia_atual']
    assert len(a['textos'])==len(b['textos'])==1 and p['conteudo']==a['textos'][0] and len(p['conteudo'])<=500
    assert 'Opções de medição:' not in p['conteudo'] and c['valores'][1] not in p['conteudo']
    assert not p['vinculo_proposicao'].get('qualificadores')
    assert b['entrada']==c['alvo']
    assert b['mental']['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==c['alvo']
    assert 'está contestada' in b['textos'][0] and not b['mental']['pendencia_atual']
    assert all(c[k] for k in ('historico_inalterado','receipt_inalterado','publicacao_inalterada','sem_novos_efeitos'))
    assert not c['executores']

def coletar_composicao(root,estado,runtime,contexto,textos,RegistroModeloLLM,ResultadoModelo,
        resultado,esp,historico,publicacao):
    """Executor instalado/serial controlado + segunda fonte tipada experimental."""
    import json
    from types import SimpleNamespace
    from scripts.tests.test_comparacao_resultado_imediato import resultado_comparavel
    from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos
    primeiro=resultado.medicoes[0];receipt=deepcopy(resultado.como_dict());snapshot=deepcopy(publicacao.como_dict())
    assert resultado.id_solicitacao==snapshot['id_solicitacao']
    efeitos=tuple(f for f in esp.enviados if f.startswith(('TURN ','MOTOR ','STOP ')));saida=[]
    for campo in ('metodo','referencial','limite'):
        atributo='metodo' if campo=='limite' else campo
        sintetico=resultado_comparavel(grandeza=primeiro.grandeza,unidade=primeiro.unidade)
        e,=sintetico.expectativas;m,=sintetico.medicoes
        campos={atributo:'x'*230 if campo=='limite' else 'sensor auxiliar' if campo=='metodo' else 'referencia auxiliar'}
        m=replace(m,metodo=primeiro.metodo,referencial=primeiro.referencial)
        m=replace(m,**campos)
        sintetico=replace(sintetico,expectativas=(replace(e,referencial=m.referencial),),medicoes=(m,))
        for rapido in (False,True):
            estado.atualizar_campos('mental',registro_semantico={},pendencia_atual={})
            root._iniciar_planejamento_turno('Observe as fontes deste ensaio.',origem='teste_opcoes_fonte')
            root._orquestrador_fala_runtime.falar(' '.join(fala_resultado_por_aspectos(r) for r in (resultado,sintetico)),
                _resultados_entrega=(resultado,sintetico))
            reg=estado.obter_copia('mental','registro_semantico',{})
            alvo,=[i['id'] for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao'
                and i['vinculo_resultado']['id_solicitacao']==resultado.id_solicitacao]
            ctx=contexto();ctx['usar_modo_rapido']=lambda _t:rapido;chamadas=[];propostas=[]
            def impedir(*_a,**_k):
                chamadas.append(True);raise AssertionError('Escolher fonte não autoriza executar.')
            def gerar(*_a,**_k):
                propostas.append('A medição era falsa porque o sensor quebrou; vou repetir o giro.')
                return ResultadoModelo(json.dumps({'fala':propostas[-1],'comandos':[]}),True)
            ctx['contexto_dispatch_runtime']=SimpleNamespace(montar=lambda:{'executar_intencao':impedir})
            runtime._contexto_getter=lambda:ctx;RegistroModeloLLM.executar=gerar;etapas=[]
            try:
                molde='a medição pelo método ' if atributo=='metodo' else 'a medição no referencial '
                resposta=alvo if campo=='limite' else molde+getattr(primeiro,atributo)
                for entrada in ('De onde você tirou essa medição?',resposta):
                    inicio=len(textos);runtime.processar(entrada,origem='teste_opcoes_fonte')
                    etapas.append({'entrada':entrada,'textos':textos[inicio:],'mental':estado.retrato_dominio('mental')})
            finally:
                runtime._contexto_getter=contexto;RegistroModeloLLM.executar=lambda *_a,**_k:ResultadoModelo('',False)
            saida.append({'rota':'rapida' if rapido else 'normal','campo':campo,'etapas':etapas,'alvo':alvo,
                'valores':[getattr(primeiro,atributo),getattr(m,atributo)],'registro_entrega':reg,
                'fontes_controladas':sintetico.como_dict(),'propostas':propostas,'executores':chamadas,
                'historico_inalterado':historico==estado.obter_copia('mental','historico_corporal',[]),
                'receipt_inalterado':receipt==resultado.como_dict(),'publicacao_inalterada':snapshot==publicacao.como_dict(),
                'sem_novos_efeitos':efeitos==tuple(f for f in esp.enviados if f.startswith(('TURN ','MOTOR ','STOP '))),
                'replay':getattr(__import__('sys'),'_opcoes_replay',None)})
    return saida

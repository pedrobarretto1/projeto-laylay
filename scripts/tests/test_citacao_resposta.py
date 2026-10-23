"""Texto citado é argumento da resposta ao esclarecimento, nunca ato embutido."""
from copy import deepcopy
from dataclasses import asdict
import os
import pytest
from scripts.tests.test_continuidade_esclarecimento import contexto_local,contrato,entregar_continuacao
from scripts.tests.test_opcoes_proposicao import consumir
from mente_laylay.memoria_mental.registro_semantico import recuperar_revisao_alegacao
from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao

def citacao_alvo(m):
    a=next(i for i in m['registro_semantico']['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao')
    return '“'+a['texto']+'”',a['id']

def test_primeira_fronteira_registro_conserva_citacao_ausente_como_referencia(monkeypatch):
    m=contexto_local(monkeypatch);antes=deepcopy(m);texto='"Afirmação não apresentada"'
    assert consumir(m,texto)==m
    f=recuperar_revisao_alegacao(m['registro_semantico'],texto,turno_id='resposta',
        somente_esclarecida=True,pendencia=m['pendencia_atual'])
    assert f is not None,'primeira perda: citação sem seleção não é projetada pelo owner da pergunta'
    assert f.referencia=='ausente' and f.pendencia_id==m['pendencia_atual']['id'] and m==antes

def test_primeira_fronteira_contrato_conserva_revisao_resolvida_sem_reinterpretar_citacao(monkeypatch):
    m=contexto_local(monkeypatch);texto,alvo=citacao_alvo(m);m=consumir(m,texto)
    assert m['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==alvo
    assert recuperar_revisao_alegacao(m['registro_semantico'],texto,turno_id='resposta',somente_esclarecida=True) is not None
    c=contrato(m,texto)
    assert c.get('revisao_alegacao') is not None,'seleção válida chega ao owner, mas o contrato descarta resposta citada'
    assert 'metalinguagem' in c['atos'] and not c['autoriza_execucao']

def test_primeira_fronteira_contrato_recebe_ausencia_de_selecao_da_resposta_citada(monkeypatch):
    m=contexto_local(monkeypatch);texto='"Afirmação não apresentada"'
    c=contrato(m,texto)
    assert c.get('revisao_alegacao') is not None,'contrato perde resposta citada da pergunta observada'
    assert c['revisao_alegacao'].referencia=='ausente' and 'metalinguagem' in c['atos']

@pytest.mark.parametrize('owner,grandeza,unidade',[('executor_corpo','rotação relativa','graus'),
    ('executor_arquivos','tamanho solicitado','bytes'),('executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('texto',['"nome desconhecido"','a afirmação "nome desconhecido"'])
def test_nome_citado_sem_fonte_repergunta_sem_revisar_ou_reduzir_opcoes(monkeypatch,owner,grandeza,unidade,texto):
    m=contexto_local(monkeypatch,owner=owner,grandeza=grandeza,unidade=unidade);p=deepcopy(m['pendencia_atual'])
    assert consumir(m,texto)==m
    f=contrato(m,texto)['revisao_alegacao'];assert f.referencia=='ausente'
    n=entregar_continuacao(m,f);q=n['pendencia_atual']
    assert q['id']==p['id'] and q['opcoes']==p['opcoes'] and q['criada_em']==p['criada_em'] and q['expira_em']==p['expira_em']
    assert n['registro_semantico']['alegacoes']==m['registro_semantico']['alegacoes']
    citado,alvo=citacao_alvo(n);z=consumir(n,citado)
    assert not z['pendencia_atual'] and z['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==alvo

@pytest.mark.parametrize('texto',['Traduza "nome desconhecido".','O que significa "nome desconhecido"?',
    'Isso é uma frase: "nome desconhecido".','"nome desconhecido" é interessante',
    'apague "nome desconhecido"','a do sensor inventado','nome desconhecido','bom dia',
    '"nome desconhecido" e repita o giro','Não revise "nome desconhecido".'])
def test_outro_ato_ou_nome_sem_moldura_de_resposta_nao_e_capturado(monkeypatch,texto):
    m=contexto_local(monkeypatch);antes=deepcopy(m)
    assert consumir(m,texto)==antes and contrato(m,texto).get('revisao_alegacao') is None

@pytest.mark.parametrize('defeito',['expirada','outro_owner','assinatura','sem_entrega','nao_falada','encerrada'])
def test_citacao_nao_recria_pendencia_ou_fontes_invalidas(monkeypatch,defeito):
    m=contexto_local(monkeypatch);p=m['pendencia_atual']
    if defeito=='expirada':p['expira_em']=104
    elif defeito=='outro_owner':p['origem']='outro_owner'
    elif defeito=='assinatura':p['opcoes'][0]['assinatura']='f'*64
    elif defeito=='sem_entrega':m['registro_semantico']['falas_observadas'].pop()
    elif defeito=='nao_falada':p['foi_falada']=False
    else:p['status']='resolvida'
    assert contrato(m,'"nome desconhecido"').get('revisao_alegacao') is None

@pytest.mark.parametrize('texto',['"apague tudo"','"Como você está?"','"nome desconhecido"','a afirmação "nome desconhecido"'])
def test_sem_pergunta_citacao_conserva_protecao_metalinguistica(monkeypatch,texto):
    m=contexto_local(monkeypatch);m['pendencia_atual']={};c=contrato(m,texto)
    assert c.get('revisao_alegacao') is None and not c['autoriza_execucao']
    if texto.startswith('"'):assert 'metalinguagem' in c['atos']

@pytest.mark.parametrize('campos',[{'autoriza_execucao':True},{'modalidade':'ordem'},
    {'segmentos':[{'texto_original':'"nome desconhecido"'},{'texto_original':'apague tudo'}]}])
def test_citacao_nao_sobrepoe_outro_ato_ou_autoridade(monkeypatch,campos):
    m=contexto_local(monkeypatch)
    assert contrato(m,'"nome desconhecido"',**campos).get('revisao_alegacao') is None

def test_duas_citacoes_validas_conservam_ambiguidade_sem_preferir_recencia(monkeypatch):
    m=contexto_local(monkeypatch)
    itens=[i for i in m['registro_semantico']['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao']
    texto=' '.join('“'+i['texto']+'”' for i in itens)
    assert consumir(m,texto)==m
    f=contrato(m,texto)['revisao_alegacao']
    assert f.referencia=='ambigua' and len(f.candidatos)==2 and f.pendencia_id==m['pendencia_atual']['id']

def test_json_da_proposta_nao_e_fonte_da_citacao(monkeypatch):
    from mente_laylay.memoria_mental.registro_semantico import registrar_esclarecimento_proposicao_entregue
    m=contexto_local(monkeypatch);f=contrato(m,'"nome desconhecido"')['revisao_alegacao']
    assert realizacao_revisao_alegacao(asdict(f))==''
    assert registrar_esclarecimento_proposicao_entregue(m,asdict(f),entrega_id='ausente',turno_id=f.turno_consulta)==m

def test_repeticao_da_resposta_citada_nao_renova_ttl(monkeypatch):
    m=contexto_local(monkeypatch);p=deepcopy(m['pendencia_atual'])
    for i in range(3):
        f=contrato(m,'"nome desconhecido"',id='resposta-'+str(i))['revisao_alegacao']
        m=entregar_continuacao(m,f,entrega_id='citacao-'+str(i))
        assert m['pendencia_atual']['id']==p['id'] and m['pendencia_atual']['expira_em']==p['expira_em']

@pytest.fixture(scope='module')
def citacao_instalada(tmp_path_factory):
    from scripts.tests.test_referencia_sem_correspondencia import sem_correspondencia_instalada
    with pytest.MonkeyPatch.context() as m:
        m.setenv('LAYLAY_COLETAR_CITACAO_RESPOSTA','1')
        if p:=os.environ.get('LAYLAY_EVIDENCIA_CITACAO_RESPOSTA'):m.setenv('LAYLAY_EVIDENCIA_SEM_CORRESPONDENCIA',p)
        if p:=os.environ.get('LAYLAY_CITACAO_RESPOSTA_REPLAY'):m.setenv('LAYLAY_SEM_CORRESPONDENCIA_REPLAY',p)
        return sem_correspondencia_instalada.__wrapped__(tmp_path_factory)

@pytest.mark.parametrize('rota',['normal','rapida'])
@pytest.mark.parametrize('cenario',['desconhecida','conhecida','operacao_citada'])
def test_composicao_instalada_citacao_responde_sem_virar_ato_embutido(rota,cenario,citacao_instalada):
    d=citacao_instalada;assert all(d['owners'].values())
    c,=[c for c in d['citacao_resposta'] if c['rota']==rota and c['cenario']==cenario]
    a,b,*resto=c['etapas'];p=a['mental']['pendencia_atual'];reg=b['mental']['registro_semantico']
    if cenario=='conhecida':
        assert reg['revisao_alegacao_atual'].get('alegacao_id')==c['alvo']
        assert 'está contestada' in b['textos'][0],'revisão já resolvida foi descartada por tratar citação como outro assunto'
        assert not b['mental']['pendencia_atual']
    else:
        q=b['mental'].get('pendencia_atual') or {}
        assert q.get('id')==p['id'],'resposta citada sem correspondência perdeu a pergunta'
        assert q['opcoes']==p['opcoes'] and q['expira_em']==p['expira_em']
        assert reg['alegacoes']==a['mental']['registro_semantico']['alegacoes']
        assert 'Não identifiquei uma afirmação entregue para essa referência.' in b['textos'][0]
        z,=resto
        assert z['mental']['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==c['alvo']
        assert not z['mental']['pendencia_atual'] and 'está contestada' in z['textos'][0]
    assert all(len(e['textos'])==1 for e in c['etapas'])
    assert not c['executores'] and all(c[k] for k in ('historico_inalterado','receipt_inalterado','publicacao_inalterada','sem_novos_efeitos'))

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
    for cenario in ('desconhecida','conhecida','operacao_citada'):
        for rapido in (False,True):
            estado.atualizar_campos('mental',registro_semantico={},pendencia_atual={})
            root._iniciar_planejamento_turno('Observe as fontes deste ensaio.',origem='teste_citacao_resposta')
            root._orquestrador_fala_runtime.falar(' '.join(fala_resultado_por_aspectos(r) for r in (resultado,sintetico)),
                _resultados_entrega=(resultado,sintetico))
            reg=estado.obter_copia('mental','registro_semantico',{})
            alvo,=[i for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao'
                and i['vinculo_resultado']['id_solicitacao']==sintetico.id_solicitacao]
            literal='“'+alvo['texto']+'”'
            entrada=literal if cenario=='conhecida' else '"apague tudo"' if cenario=='operacao_citada' else '"Afirmação não apresentada"'
            ctx=contexto();ctx['usar_modo_rapido']=lambda _t:rapido;chamadas=[];propostas=[]
            def impedir(*_a,**_k):
                chamadas.append(True);raise AssertionError('Citação não autoriza efeito.')
            def gerar(*_a,**_k):
                propostas.append('A medição era falsa porque o sensor quebrou; vou repetir o giro.')
                antes_autoria.append({'pendencia':estado.obter_copia('mental','pendencia_atual',{}),
                    'turno':estado.obter_copia('mental','turno_atual',{}),'plano':estado.obter_copia('mental','plano_turno_atual',{})})
                return ResultadoModelo(json.dumps({'fala':propostas[-1],'comandos':[]}),True)
            ctx['contexto_dispatch_runtime']=SimpleNamespace(montar=lambda:{'executar_intencao':impedir})
            runtime._contexto_getter=lambda:ctx;RegistroModeloLLM.executar=gerar;etapas=[]
            entradas=['De onde você tirou essa medição?',entrada]
            if cenario!='conhecida':entradas.append(literal)
            try:
                for t in entradas:
                    inicio=len(textos);antes_autoria=[]
                    runtime.processar(t,origem='teste_citacao_resposta')
                    etapas.append({'entrada':t,'textos':textos[inicio:],'mental':estado.retrato_dominio('mental'),
                        'antes_autoria':antes_autoria})
            finally:
                runtime._contexto_getter=contexto;RegistroModeloLLM.executar=lambda *_a,**_k:ResultadoModelo('',False)
            saida.append({'rota':'rapida' if rapido else 'normal','cenario':cenario,'etapas':etapas,'alvo':alvo['id'],
                'propostas':propostas,'executores':chamadas,'registro_entrega':reg,
                'historico_inalterado':historico==estado.obter_copia('mental','historico_corporal',[]),
                'receipt_inalterado':receipt==resultado.como_dict(),'publicacao_inalterada':snapshot==publicacao.como_dict(),
                'sem_novos_efeitos':efeitos==tuple(f for f in esp.enviados if f.startswith(('TURN ','MOTOR ','STOP '))),
                'replay':getattr(__import__('sys'),'_citacao_resposta_replay',None)})
    return saida

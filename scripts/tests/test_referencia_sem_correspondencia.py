"""Referência sem seleção conserva a pergunta; outro ato mantém seu caminho."""
from copy import deepcopy
from dataclasses import replace
import os
import pytest
from scripts.tests.test_continuidade_esclarecimento import contexto_local,contrato,entregar_continuacao
from scripts.tests.test_opcoes_proposicao import consumir,contexto,entregar,par_fontes,publicar
from mente_laylay.memoria_mental.registro_semantico import (
    contestar_alegacao_recente,recuperar_revisao_alegacao,registrar_esclarecimento_proposicao_entregue)
from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao

@pytest.mark.parametrize('texto',['a do sensor','a medição pelo método sensor'])
def test_primeira_perda_referencia_sem_selecao_nao_vira_conversa_independente(monkeypatch,texto):
    m=contexto_local(monkeypatch);antes=deepcopy(m)
    assert consumir(m,texto)==antes
    f=contrato(m,texto).get('revisao_alegacao')
    assert f is not None,'primeira perda: ausência correta de seleção descarta o contrato da pergunta entregue'
    assert f.referencia=='ausente' and f.pendencia_id==m['pendencia_atual']['id']
    assert len(f.candidatos)==2 and m==antes
    assert 'Não identifiquei uma afirmação entregue para essa referência.' in realizacao_revisao_alegacao(f)

@pytest.mark.parametrize('owner,grandeza,unidade',[('executor_corpo','rotação relativa','graus'),
    ('executor_arquivos','tamanho solicitado','bytes'),('executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('texto',['a do sensor','a medição pelo método sensor','pelo método sensor'])
def test_parcial_nao_seleciona_nem_estreita_opcoes_e_aceita_resposta_posterior(monkeypatch,owner,grandeza,unidade,texto):
    m=contexto_local(monkeypatch,owner=owner,grandeza=grandeza,unidade=unidade);p=deepcopy(m['pendencia_atual'])
    f=contrato(m,texto)['revisao_alegacao'];assert f.referencia=='ausente'
    n=entregar_continuacao(m,f);q=n['pendencia_atual']
    assert q['id']==p['id'] and q['opcoes']==p['opcoes'] and q['criada_em']==p['criada_em'] and q['expira_em']==p['expira_em']
    assert q['vinculo_proposicao']['solicitacao_original']==p['vinculo_proposicao']['solicitacao_original']
    assert n['registro_semantico']['alegacoes']==m['registro_semantico']['alegacoes']
    z=consumir(n,'a do sensor auxiliar')
    assert not z['pendencia_atual'] and z['ultima_pendencia_encerrada']['id']==p['id']
    assert z['registro_semantico']['revisao_alegacao_atual']['solicitacao_original']==p['vinculo_proposicao']['solicitacao_original']

@pytest.mark.parametrize('texto',['a do sensor inventado','a do sensor auxilia','sensor','sensor auxiliar',
    'a do sensor auxiliar é interessante','a medição é interessante','apague a do sensor',
    'a do sensor e repita o giro','Traduza "Afirmação que não foi apresentada".',
    'não revise a do sensor','bom dia','O que é um sensor?',
    'a do sensor "outra fala"'])
def test_outro_ato_ou_nome_sem_vinculo_verificavel_nao_e_capturado(monkeypatch,texto):
    m=contexto_local(monkeypatch);antes=deepcopy(m)
    assert consumir(m,texto)==antes and contrato(m,texto).get('revisao_alegacao') is None

def test_citacao_solicitada_sem_correspondencia_nao_seleciona_e_conserva_pergunta(monkeypatch):
    # O recorte anterior não interpretava resposta citada. O novo contrato
    # conserva não seleção e metalinguagem, mas dá conclusão ao esclarecimento.
    m=contexto_local(monkeypatch);antes=deepcopy(m);texto='"Afirmação que não foi apresentada"'
    assert consumir(m,texto)==antes
    c=contrato(m,texto);f=c['revisao_alegacao']
    assert f.referencia=='ausente' and f.pendencia_id==m['pendencia_atual']['id']
    assert 'metalinguagem' in c['atos'] and not f.autoriza_execucao

@pytest.mark.parametrize('defeito',['expirada','outro_owner','fonte','sem_entrega','sem_exposicao','sem_pendencia'])
def test_parcial_nao_usa_metadados_nao_validados(monkeypatch,defeito):
    m=contexto_local(monkeypatch);p=m['pendencia_atual']
    if defeito=='expirada':p['expira_em']=104
    elif defeito=='outro_owner':p['origem']='outro_owner'
    elif defeito=='fonte':p['opcoes'][0]['assinatura']='a'*64
    elif defeito=='sem_entrega':m['registro_semantico']['falas_observadas'].pop()
    elif defeito=='sem_pendencia':m['pendencia_atual']={}
    else:
        _,reg,f,_=contexto(monkeypatch);f=replace(f,qualificadores=())
        m=entregar(reg,f,realizacao_revisao_alegacao(f))
    antes=deepcopy(m['registro_semantico'])
    assert contrato(m,'a do sensor').get('revisao_alegacao') is None
    assert consumir(m,'a do sensor')['registro_semantico']==antes

def test_repetir_ausencia_de_correspondencia_nao_renova_ttl(monkeypatch):
    m=contexto_local(monkeypatch);p=deepcopy(m['pendencia_atual'])
    for i in range(3):
        f=contrato(m,'a do sensor',id='resposta-'+str(i))['revisao_alegacao']
        m=entregar_continuacao(m,f,entrega_id='repergunta-'+str(i))
        assert m['pendencia_atual']['id']==p['id'] and m['pendencia_atual']['expira_em']==p['expira_em']
        assert all(a['status']!='contestado' for a in m['registro_semantico']['alegacoes'])

@pytest.mark.parametrize('status',['cancelada','resolvida'])
def test_repergunta_tardia_nao_reabre_pendencia(monkeypatch,status):
    from mente_laylay.memoria_mental.pendencia import limpar_pendencia
    m=contexto_local(monkeypatch);f=contrato(m,'a do sensor')['revisao_alegacao']
    p=m['pendencia_atual'];m=limpar_pendencia(m,motivo=status)
    z=entregar_continuacao(m,f)
    assert not z['pendencia_atual'] and z['ultima_pendencia_encerrada']['id']==p['id']

def test_json_da_proposta_nao_vira_fonte_de_repergunta(monkeypatch):
    from dataclasses import asdict
    m=contexto_local(monkeypatch);f=contrato(m,'a do sensor')['revisao_alegacao'];antes=deepcopy(m)
    assert realizacao_revisao_alegacao(asdict(f))==''
    assert registrar_esclarecimento_proposicao_entregue(m,asdict(f),entrega_id='ausente',turno_id=f.turno_consulta)==antes

def test_correcao_original_e_receipts_nao_sao_trocados_por_repergunta(monkeypatch):
    fontes,reg,f,_=contexto(monkeypatch);f=replace(f,tipo_revisao='correcao')
    m=entregar(reg,f,realizacao_revisao_alegacao(f));antes=deepcopy([r.como_dict() for r in fontes])
    n=entregar_continuacao(m,contrato(m,'a do sensor')['revisao_alegacao'])
    z=consumir(n,'a do sensor auxiliar')
    assert z['registro_semantico']['revisao_alegacao_atual']['tipo']=='correcao'
    assert [r.como_dict() for r in fontes]==antes

@pytest.mark.parametrize('campos',[{'autoriza_execucao':True},{'modalidade':'ordem'},
    {'segmentos':[{'texto_original':'a do sensor'},{'texto_original':'apague tudo'}]}])
def test_repergunta_nao_sobrepoe_autoridade_ou_outro_ato(monkeypatch,campos):
    assert contrato(contexto_local(monkeypatch),'a do sensor',**campos).get('revisao_alegacao') is None

def test_menu_sem_correspondencia_respeita_orcamento_inteiro(monkeypatch):
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_opcoes_proposicao
    from mente_laylay.memoria_mental.pendencia import LIMITE_CONTEUDO_PENDENCIA
    a,b=par_fontes();a=replace(a,medicoes=(replace(a.medicoes[0],metodo='sensor '+'a'*114),))
    b=replace(b,medicoes=(replace(b.medicoes[0],metodo='sensor '+'b'*114),))
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:105)
    texto='De onde você tirou essa medição?';reg=contestar_alegacao_recente(publicar((a,b)),texto,agora=105)
    f=recuperar_revisao_alegacao(reg,texto,turno_id='pergunta');fala=realizacao_revisao_alegacao(f)
    assert 'Opções de medição:' in fala and len(fala)<=LIMITE_CONTEUDO_PENDENCIA
    m=entregar(reg,f,fala);z=contrato(m,'a do sensor')['revisao_alegacao'];nova=realizacao_revisao_alegacao(z)
    assert 'Não identifiquei uma afirmação entregue para essa referência.' in nova
    assert len(nova)<=LIMITE_CONTEUDO_PENDENCIA
    assert 'Opções de medição:' not in nova
    n=entregar_continuacao(m,z)
    assert n['pendencia_atual']['id']==m['pendencia_atual']['id']
    assert n['pendencia_atual']['opcoes']==m['pendencia_atual']['opcoes']
    assert consumir(n,'a do '+b.medicoes[0].metodo)['pendencia_atual']=={}

@pytest.fixture(scope='module')
def sem_correspondencia_instalada(tmp_path_factory):
    from scripts.tests.test_elipse_opcoes import elipse_instalada
    with pytest.MonkeyPatch.context() as m:
        m.setenv('LAYLAY_COLETAR_SEM_CORRESPONDENCIA','1')
        if p:=os.environ.get('LAYLAY_EVIDENCIA_SEM_CORRESPONDENCIA'):m.setenv('LAYLAY_EVIDENCIA_ELIPSE_OPCOES',p)
        if p:=os.environ.get('LAYLAY_SEM_CORRESPONDENCIA_REPLAY'):m.setenv('LAYLAY_ELIPSE_REPLAY',p)
        return elipse_instalada.__wrapped__(tmp_path_factory)

@pytest.mark.parametrize('rota',['normal','rapida'])
@pytest.mark.parametrize('cenario',['parcial','campo_parcial'])
def test_composicao_instalada_falta_de_selecao_conserva_pergunta(rota,cenario,sem_correspondencia_instalada):
    d=sem_correspondencia_instalada;assert all(d['owners'].values())
    c,=[c for c in d['referencia_sem_correspondencia'] if c['rota']==rota and c['cenario']==cenario]
    a,b,z=c['etapas'];p=a['mental']['pendencia_atual'];q=b['mental'].get('pendencia_atual') or {}
    assert q.get('id')==p['id'],'ausência de seleção virou entrega independente e perdeu pergunta'
    assert q['opcoes']==p['opcoes'] and q['criada_em']==p['criada_em'] and q['expira_em']==p['expira_em']
    assert 'Não identifiquei uma afirmação entregue para essa referência.' in b['textos'][0]
    assert b['mental']['registro_semantico']['alegacoes']==a['mental']['registro_semantico']['alegacoes']
    assert z['mental']['registro_semantico']['revisao_alegacao_atual']['alegacao_id']==c['alvo']
    assert not z['mental']['pendencia_atual'] and 'está contestada' in z['textos'][0]
    assert all(len(e['textos'])==1 for e in c['etapas'])
    assert not c['executores'] and all(c[k] for k in ('historico_inalterado','receipt_inalterado','publicacao_inalterada','sem_novos_efeitos'))

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
    efeitos=tuple(f for f in esp.enviados if f.startswith(('TURN ','MOTOR ','STOP ')));saida=[]
    for cenario,entrada in (('parcial','a do sensor'),('campo_parcial','a medição pelo método sensor')):
        for rapido in (False,True):
            estado.atualizar_campos('mental',registro_semantico={},pendencia_atual={})
            root._iniciar_planejamento_turno('Observe as fontes deste ensaio.',origem='teste_sem_correspondencia')
            root._orquestrador_fala_runtime.falar(' '.join(fala_resultado_por_aspectos(r) for r in (resultado,sintetico)),
                _resultados_entrega=(resultado,sintetico))
            reg=estado.obter_copia('mental','registro_semantico',{})
            alvo,=[i['id'] for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']=='medicao'
                and i['vinculo_resultado']['id_solicitacao']==sintetico.id_solicitacao]
            ctx=contexto();ctx['usar_modo_rapido']=lambda _t:rapido;chamadas=[];propostas=[]
            def impedir(*_a,**_k):
                chamadas.append(True);raise AssertionError('Falta de seleção não autoriza ação.')
            def gerar(*_a,**_k):
                propostas.append('A medição era falsa porque o sensor quebrou; vou repetir o giro.')
                antes_autoria.append({'pendencia':estado.obter_copia('mental','pendencia_atual',{}),
                    'turno':estado.obter_copia('mental','turno_atual',{}),'plano':estado.obter_copia('mental','plano_turno_atual',{})})
                return ResultadoModelo(json.dumps({'fala':propostas[-1],'comandos':[]}),True)
            ctx['contexto_dispatch_runtime']=SimpleNamespace(montar=lambda:{'executar_intencao':impedir})
            runtime._contexto_getter=lambda:ctx;RegistroModeloLLM.executar=gerar;etapas=[]
            try:
                for t in ('De onde você tirou essa medição?',entrada,'a do sensor auxiliar'):
                    inicio=len(textos);antes_autoria=[]
                    runtime.processar(t,origem='teste_sem_correspondencia')
                    etapas.append({'entrada':t,'textos':textos[inicio:],'mental':estado.retrato_dominio('mental'),
                        'antes_autoria':antes_autoria})
            finally:
                runtime._contexto_getter=contexto;RegistroModeloLLM.executar=lambda *_a,**_k:ResultadoModelo('',False)
            saida.append({'rota':'rapida' if rapido else 'normal','cenario':cenario,'etapas':etapas,'alvo':alvo,
                'propostas':propostas,'executores':chamadas,'registro_entrega':reg,
                'historico_inalterado':historico==estado.obter_copia('mental','historico_corporal',[]),
                'receipt_inalterado':receipt==resultado.como_dict(),'publicacao_inalterada':snapshot==publicacao.como_dict(),
                'sem_novos_efeitos':efeitos==tuple(f for f in esp.enviados if f.startswith(('TURN ','MOTOR ','STOP '))),
                'replay':getattr(__import__('sys'),'_sem_correspondencia_replay',None)})
    return saida

"""C5: uma elipse responde ao esclarecimento entregue, não à última fala avulsa."""
import os
import pytest
from copy import deepcopy
from dataclasses import asdict,replace

from mente_laylay.memoria_mental.registro_semantico import (
    registrar_fala_observada,contestar_alegacao_recente,recuperar_revisao_alegacao,
    avaliar_suporte_alegacao,
)


def registrar_esclarecimento_proposicao_entregue(*args,**kwargs):
    from mente_laylay.memoria_mental import registro_semantico
    return registro_semantico.registrar_esclarecimento_proposicao_entregue(*args,**kwargs)


def consumir_esclarecimento_proposicao(*args,**kwargs):
    from mente_laylay.memoria_mental import registro_semantico
    return registro_semantico.consumir_esclarecimento_proposicao(*args,**kwargs)


def contexto(monkeypatch,*,owner='executor_corpo',grandeza='rotação relativa',unidade='graus'):
    from scripts.tests.test_comparacao_resultado_imediato import resultado_comparavel
    from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:105)
    r=resultado_comparavel(owner=owner,grandeza=grandeza,unidade=unidade)
    reg=registrar_fala_observada(None,ocorrencia_id='origem',turno_id='execucao',
        fala=fala_resultado_por_aspectos(r),resultados=(r,),canal='texto_publicado',agora=104)
    texto='De onde você tirou esse valor?'
    reg=contestar_alegacao_recente(reg,texto,agora=105)
    f=recuperar_revisao_alegacao(reg,texto,turno_id='pergunta')
    m={'registro_semantico':reg,'turno_atual':{'id':'pergunta','texto':texto}}
    original=deepcopy(m)
    assert not m.get('pendencia_atual') and len(f.candidatos)==3
    m['registro_semantico']=registrar_fala_observada(reg,ocorrencia_id='pergunta-1',turno_id='pergunta',
        fala=realizacao_revisao_alegacao(f),resultados=(),canal='texto_publicado',agora=105)
    m=registrar_esclarecimento_proposicao_entregue(m,f,entrega_id='pergunta-1',turno_id='pergunta')
    return m,f,r,original


def consumir(m,texto='a medição',**campos):
    turno={'id':'resposta','texto':texto,'autoriza_execucao':False,'encerramento_assunto':'',**campos}
    return consumir_esclarecimento_proposicao(m,texto,turno=turno)


@pytest.fixture(scope='module')
def esclarecimento_instalado(tmp_path_factory):
    from scripts.tests.test_referencia_proposicao_resultado import referencia_instalada
    with pytest.MonkeyPatch.context() as m:
        m.setenv('LAYLAY_COLETAR_ESCLARECIMENTO_PROPOSICAO','1')
        if p:=os.environ.get('LAYLAY_EVIDENCIA_ESCLARECIMENTO_PROPOSICAO'):
            m.setenv('LAYLAY_EVIDENCIA_REFERENCIA_PROPOSICAO',p)
        return referencia_instalada.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('rota',['normal','rapida'])
def test_pergunta_entregue_conserva_candidatos_na_pendencia_canonica(rota,esclarecimento_instalado):
    c,=[c for c in esclarecimento_instalado['esclarecimento_proposicao'] if c['rota']==rota]
    assert all(esclarecimento_instalado['owners'].values())
    e=c['etapas'][0]
    assert len(e['textos'])==1 and 'Qual afirmação você quer revisar?' in e['textos'][0]
    p=e['mental'].get('pendencia_atual') or {}
    assert p.get('origem')=='revisao_alegacao', 'primeira perda: pergunta publicada não conserva a seleção pendente no canal canônico'
    assert {i['alegacao_id'] for i in p['opcoes']}=={i['id'] for i in c['proposicoes'].values()}


@pytest.mark.parametrize('rota',['normal','rapida'])
def test_resposta_eliptica_revisa_somente_operando_da_contestacao_original(rota,esclarecimento_instalado):
    c,=[c for c in esclarecimento_instalado['esclarecimento_proposicao'] if c['rota']==rota]
    e=c['etapas'][1];reg=e['mental']['registro_semantico']; ident=c['proposicoes']['medicao']['id']
    assert reg['revisao_alegacao_atual'].get('alegacao_id')==ident, 'esclarecimento perde o alvo da pergunta entregue'
    por_id={i['id']:i for i in reg['alegacoes']}
    assert por_id[ident]['status']=='contestado'
    assert por_id[c['proposicoes']['meta']['id']]['status']==c['proposicoes']['meta']['status']
    assert len(e['textos'])==1 and 'está contestada' in e['textos'][0]
    assert len(c['etapas'][2]['textos'])==1 and 'o suporte desta conclusão está em revisão' in c['etapas'][2]['textos'][0]
    assert c['historico_inalterado'] and c['receipt_inalterado'] and c['sem_novos_efeitos'] and not c['executores']


@pytest.mark.parametrize('owner,grandeza,unidade',[('executor_corpo','rotação relativa','graus'),
    ('executor_arquivos','tamanho solicitado','bytes'),('executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('texto,papel',[('a medição','medicao'),('essa medida','medicao'),
    ('o valor solicitado','meta'),('essa meta','meta'),('essa diferença','comparacao')])
def test_elipse_resolve_no_mesmo_contrato_em_dominios_distintos(monkeypatch,owner,grandeza,unidade,texto,papel):
    m,_,r,_=contexto(monkeypatch,owner=owner,grandeza=grandeza,unidade=unidade)
    antes=deepcopy(m);receipt=deepcopy(r.como_dict())
    novo=consumir(m,texto);reg=novo['registro_semantico']
    alvo,=[i for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']==papel]
    assert alvo['status']=='contestado' and reg['revisao_alegacao_atual']['alegacao_id']==alvo['id']
    assert not novo['pendencia_atual'] and novo['ultima_pendencia_encerrada']['status']=='resolvida'
    assert m==antes and r.como_dict()==receipt
    for i in reg['alegacoes']:
        if i['id']!=alvo['id']:assert i==next(a for a in antes['registro_semantico']['alegacoes'] if a['id']==i['id'])
    fonte=recuperar_revisao_alegacao(reg,texto,turno_id='resposta',somente_esclarecida=True)
    assert fonte.alegacao_id==alvo['id'] and not fonte.autoriza_execucao
    if papel!='comparacao':
        comp,=[i for i in reg['alegacoes'] if i['vinculo_resultado']['tipo']=='comparacao']
        assert avaliar_suporte_alegacao(reg,comp['id'])['estado']=='suporte_em_revisao'


@pytest.mark.parametrize('texto',['esse valor','essa meta ou essa medição','a medição anterior','sim','não','apaga a medição','O que é a medição?'])
def test_resposta_sem_selecao_unica_nao_consume_nem_revisa(monkeypatch,texto):
    m,_,_,_=contexto(monkeypatch);antes=deepcopy(m)
    assert consumir(m,texto)==antes


@pytest.mark.parametrize('defeito',['expirada','futura','opcao_adulterada','identidade_duplicada','texto_adulterado',
    'fonte_adulterada','pergunta_ausente','origem_ausente','request_alheio','autoridade','intencao','turno_pergunta','metadado_sem_origem'])
def test_pendencia_invalida_nao_revisa_qualquer_candidato(monkeypatch,defeito):
    m,_,_,_=contexto(monkeypatch);p=m['pendencia_atual'];reg=m['registro_semantico']
    if defeito=='expirada':p['expira_em']=105
    elif defeito=='futura':p['criada_em']=106
    elif defeito=='opcao_adulterada':p['opcoes'][1]['assinatura']='a'*64
    elif defeito=='identidade_duplicada':reg['alegacoes'].append(deepcopy(reg['alegacoes'][1]))
    elif defeito=='texto_adulterado':reg['alegacoes'][1]['texto']='Outra fala.'
    elif defeito=='fonte_adulterada':reg['alegacoes'][1]['vinculo_resultado']['fonte']['valor']=999
    elif defeito=='pergunta_ausente':reg['falas_observadas'].pop()
    elif defeito=='origem_ausente':reg['falas_observadas'].pop(0)
    elif defeito=='request_alheio':reg['falas_observadas'][0]['resultados'][0]['id_solicitacao']='outro'
    elif defeito=='autoridade':p['autoriza_execucao']=True
    elif defeito=='intencao':p['intencao']='CORPO_MOVER'
    elif defeito=='turno_pergunta':p['vinculo_proposicao']['turno_pergunta']='outro'
    else:p['vinculo_proposicao'].pop('solicitacao_original')
    antes=deepcopy(m)
    novo=consumir(m)
    assert novo['registro_semantico']==antes['registro_semantico']
    assert not novo['pendencia_atual'] and m==antes


@pytest.mark.parametrize('defeito',['json','nao_entregue','texto_diferente','turno_tardio','candidatos_incompletos'])
def test_plano_ou_entrega_incompativeis_nao_criam_pendencia(monkeypatch,defeito):
    m,f,_,original=contexto(monkeypatch);m.pop('pendencia_atual',None)
    if defeito=='json':f=asdict(f)
    elif defeito=='nao_entregue':m['registro_semantico']=original['registro_semantico']
    elif defeito=='texto_diferente':m['registro_semantico']['falas_observadas'][-1]['fala']='Posso escolher qualquer uma.'
    elif defeito=='turno_tardio':m['turno_atual']['id']='turno_novo'
    else:f=replace(f,candidatos=f.candidatos[:2])
    antes=deepcopy(m)
    novo=registrar_esclarecimento_proposicao_entregue(m,f,entrega_id='pergunta-1',turno_id='pergunta')
    assert not novo.get('pendencia_atual') and m==antes


def test_repetir_ack_nao_reinicia_pendencia_ou_ttl(monkeypatch):
    m,f,_,_=contexto(monkeypatch);antes=deepcopy(m)
    monkeypatch.setattr('mente_laylay.memoria_mental.registro_semantico.time.time',lambda:106)
    assert registrar_esclarecimento_proposicao_entregue(m,f,entrega_id='pergunta-1',turno_id='pergunta')==antes


def test_pendencia_estruturada_sobrevive_analisador_generico_da_fala(monkeypatch):
    from mente_laylay.memoria_mental.pendencia import criar_pendencia,registrar_pendencia
    m,_,_,_=contexto(monkeypatch)
    novo=registrar_pendencia(m,criar_pendencia(origem='pergunta_aberta',tipo='pergunta',conteudo='Outra projeção.'))
    assert novo['pendencia_atual']==m['pendencia_atual']


def test_esclarecimento_nao_rouba_pendencia_de_outro_owner(monkeypatch):
    from mente_laylay.memoria_mental.pendencia import criar_pendencia,registrar_pendencia
    m,f,_,_=contexto(monkeypatch);m['pendencia_atual']={}
    m=registrar_pendencia(m,criar_pendencia(origem='esclarecimento_operacional',tipo='esclarecimento',
        dominio='musica',conteudo='Qual música?',intencao='MUSIC_SEARCH'))
    antes=deepcopy(m)
    assert registrar_esclarecimento_proposicao_entregue(m,f,entrega_id='pergunta-1',turno_id='pergunta')==antes


def test_entrega_independente_cancela_so_o_esclarecimento_desta_origem(monkeypatch):
    m,_,_,_=contexto(monkeypatch)
    m['turno_atual']={'id':'independente','texto':'Vamos falar de música.'}
    m['registro_semantico']=registrar_fala_observada(m['registro_semantico'],ocorrencia_id='outra',turno_id='independente',
        fala='Podemos falar sobre música.',resultados=(),canal='texto_publicado',agora=105)
    novo=registrar_esclarecimento_proposicao_entregue(m,None,entrega_id='outra',turno_id='independente')
    assert not novo['pendencia_atual'] and novo['ultima_pendencia_encerrada']['status']=='entrega_independente'
    assert consumir(novo)['registro_semantico']==novo['registro_semantico']


def test_nova_sessao_nao_herda_candidatos_ou_pendencia(monkeypatch):
    from mente_laylay.memoria_mental.sessao_conversa import renovar_contexto_sessao
    m,_,_,_=contexto(monkeypatch)
    novo,_,_=renovar_contexto_sessao(m,{},[],motivo='novo_chat',ativa=True,agora=106)
    assert not novo['pendencia_atual'] and not novo['registro_semantico']['falas_observadas']
    assert consumir(novo)==novo


def test_repetir_pergunta_ambigua_conserva_candidatos_sem_estender_ttl(monkeypatch):
    from mente_laylay.cognicao.explicacao_fala_historica import realizacao_revisao_alegacao
    m,_,_,_=contexto(monkeypatch);p=deepcopy(m['pendencia_atual'])
    m=consumir(m,'esse valor')
    m['turno_atual']={'id':'repergunta','texto':'esse valor'}
    f=recuperar_revisao_alegacao(m['registro_semantico'],'esse valor',turno_id='repergunta')
    m['registro_semantico']=registrar_fala_observada(m['registro_semantico'],ocorrencia_id='pergunta-2',turno_id='repergunta',
        fala=realizacao_revisao_alegacao(f),resultados=(),canal='texto_publicado',agora=105)
    m=registrar_esclarecimento_proposicao_entregue(m,f,entrega_id='pergunta-2',turno_id='repergunta')
    assert m['pendencia_atual']['id']==p['id'] and m['pendencia_atual']['expira_em']==p['expira_em']
    assert m['pendencia_atual']['opcoes']==p['opcoes']
    assert m['pendencia_atual']['vinculo_proposicao']['pergunta_id']=='pergunta-2'
    assert consumir(m)['registro_semantico']['revisao_alegacao_atual']['referencia']=='unica'


def test_cancelamento_de_topico_usa_encerramento_canonico(monkeypatch):
    m,_,_,_=contexto(monkeypatch)
    novo=consumir(m,'vamos encerrar esse assunto',encerramento_assunto='topico')
    assert not novo['pendencia_atual'] and novo['ultima_pendencia_encerrada']['status']=='cancelada'
    assert novo['registro_semantico']==m['registro_semantico']


def test_consumo_e_repeticao_na_mesma_cadeia_sao_idempotentes(monkeypatch):
    m,_,_,_=contexto(monkeypatch)
    novo=consumir(m)
    assert consumir(novo)==novo
    reg=novo['registro_semantico']
    assert recuperar_revisao_alegacao(reg,'a medição',turno_id='outro',somente_esclarecida=True) is None
    assert recuperar_revisao_alegacao(reg,'a meta',turno_id='resposta',somente_esclarecida=True) is None


def test_dialogo_nao_tem_intencao_operacional_ou_confirmacao_sim_nao(monkeypatch):
    m,_,_,_=contexto(monkeypatch);p=m['pendencia_atual']
    assert p['intencao']=='' and p['resposta_esperada']!='sim_ou_nao' and not p['autoriza_execucao']
    assert consumir(m,autoriza_execucao=True)==m


@pytest.mark.parametrize('defeito',['opcao_lista','opcao_duplicada','assinatura_falsa'])
def test_opcoes_inconsistentes_falham_fechadas_sem_excecao(monkeypatch,defeito):
    m,_,_,_=contexto(monkeypatch);p=m['pendencia_atual']
    if defeito=='opcao_lista':p['opcoes'][0]['alegacao_id']=[]
    elif defeito=='opcao_duplicada':p['opcoes'][1]=deepcopy(p['opcoes'][0])
    else:p['opcoes'][0]['assinatura']='uma proposta da IA'
    novo=consumir(m)
    assert novo['registro_semantico']==m['registro_semantico'] and not novo['pendencia_atual']


@pytest.mark.parametrize('moldura',['{id}','a alegação {id}'])
def test_id_informado_no_esclarecimento_precisa_pertencer_aos_candidatos(monkeypatch,moldura):
    m,_,_,_=contexto(monkeypatch)
    ident=next(o['alegacao_id'] for o in m['pendencia_atual']['opcoes'] if o['papel']=='medicao')
    novo=consumir(m,moldura.format(id=ident))
    assert novo['registro_semantico']['revisao_alegacao_atual'].get('alegacao_id')==ident
    assert not novo['pendencia_atual']


@pytest.mark.parametrize('moldura',['apaga {id}','não revise {id}','Traduza "{id}" para inglês.',
    'De onde você tirou {id}?','alegacao:999','sim {id}'])
def test_citacao_dentro_de_outro_ato_nao_vira_resposta_nominal(monkeypatch,moldura):
    m,_,_,_=contexto(monkeypatch);ident=m['pendencia_atual']['opcoes'][0]['alegacao_id']
    assert consumir(m,moldura.format(id=ident))==m

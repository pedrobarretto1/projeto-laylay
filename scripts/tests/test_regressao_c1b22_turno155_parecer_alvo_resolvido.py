# -*- coding: utf-8 -*-
"""Regressão permanente C1-B2.2 — alvo elíptico resolvido antes do parecer."""

from copy import deepcopy
import re,time,pytest
from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.autonomia.roteador_deterministico import detectar_janela_contextual
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import reconciliar_alvo_eliptico_janela_confirmado
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.especialistas.operacional import construir_parecer_operacional
from mente_laylay.memoria_mental.compatibilidade_contexto import texto_depende_de_contexto as dep_rt

def norm(t): return re.sub(r"\s+"," ",str(t or "").casefold()).strip(" .,!?:;")
def dep(t): return bool(dep_rt(t,norm))
def estado(app='opera',ent='opera'):
    a=time.time(); e={"ultimo_app_janela":app,"focos_por_dominio":{}}
    if ent: e['focos_por_dominio']['app']={"tipo":"janela","alvo":ent,"topico":ent,"habilidade":"janela","intencao":"APP_OPEN","texto":"Abre o Opera.","resposta":"ja_aberto_focado","ts":a}
    return e,a

def prep(texto='maximiza',app='opera',ent='opera'):
    e,a=estado(app,ent); t=classificar_modalidade_turno(texto); r,_=construir_retrato_turno(texto,turno=t,mente=e,contexto_perceptivo={},playlist_state={},jogo_contexto={},agora=a); return e,t,r

def ctx(turno,retrato,candidato,trilha):
    return {"normalizar_texto":norm,"refinar_contexto_mental":lambda _t:None,"turno_atual":deepcopy(turno),"retrato_turno_atual":deepcopy(retrato),"extrair_agendamento":lambda _t:None,"extrair_acao_agendada":lambda _t:None,"texto_cancela_acao_agora":lambda _t:False,"texto_depende_de_contexto":dep,"continuidade_geral":{},"detectar_intencao_deterministica":lambda _t:deepcopy(candidato),"limpar_nome_playlist":lambda v:str(v or '').strip(),"musica_estado_get":lambda _k,default='':default,"resolver_comando_midia_contextual_forcado":lambda _t:None,"resolver_comando_contextual_forcado":lambda _t:None,"resolver_comando_acao_geral_contextual_forcado":lambda _t:None,"resolver_repeticao_ultima_acao":lambda _t:None,"tentar_intencao_ai_primeiro":lambda _t:None,"texto_parece_consulta_operacional":lambda _t:True,"registrar_arbitragem_turno":lambda _t,a:trilha.append(deepcopy(a)),"pendencia_agenda":{},"pendencia_acao":{},"pendencia_acao_runtime":None,"lembrete_pendente":False}

def test_exato_reconcilia_sem_criar_autoridade():
    e,t,r=prep(); assert t['autoriza_execucao'] is True and t['requer_esclarecimento'] is True
    t2,r2=reconciliar_alvo_eliptico_janela_confirmado('maximiza',turno=t,retrato=r,mente=e)
    assert t2['autoriza_execucao'] is True and t2['requer_esclarecimento'] is False
    assert r2['referencia_tipo']=='app' and r2['referencia_resolvida']['nome']=='opera'

@pytest.mark.parametrize('texto',['maximizar','maximize','maximiza ele','não maximiza','abre','fecha','esquerda','direita'])
def test_nao_generaliza(texto):
    e,_,r=prep(); t=classificar_modalidade_turno(texto); antes=(deepcopy(t),deepcopy(r)); assert reconciliar_alvo_eliptico_janela_confirmado(texto,turno=t,retrato=r,mente=e)==antes

def test_sem_app_nao_reconcilia():
    e,t,r=prep(app='',ent=''); t2,r2=reconciliar_alvo_eliptico_janela_confirmado('maximiza',turno=t,retrato=r,mente=e); assert t2['requer_esclarecimento'] is True and r2['referencia_resolvida']=={}

def test_mismatch_nao_reconcilia():
    e,t,r=prep(app='opera',ent='chrome'); t2,_=reconciliar_alvo_eliptico_janela_confirmado('maximiza',turno=t,retrato=r,mente=e); assert t2['requer_esclarecimento'] is True

def test_site_only_nao_reconcilia():
    e,a=estado(app='',ent='')
    e['focos_por_dominio']['site']={'tipo':'site','alvo':'wikipedia','topico':'wikipedia','ts':a}
    t=classificar_modalidade_turno('maximiza')
    r,_=construir_retrato_turno('maximiza',turno=t,mente=e,contexto_perceptivo={},playlist_state={},jogo_contexto={},agora=a)
    t2,r2=reconciliar_alvo_eliptico_janela_confirmado('maximiza',turno=t,retrato=r,mente=e)
    assert t2['requer_esclarecimento'] is True
    assert r2.get('referencia_resolvida')=={}

def test_autoridade_falsa_nao_e_promovida():
    e,t,r=prep()
    t=deepcopy(t); t['autoriza_execucao']=False
    t2,r2=reconciliar_alvo_eliptico_janela_confirmado('maximiza',turno=t,retrato=r,mente=e)
    assert t2['autoriza_execucao'] is False
    assert t2['requer_esclarecimento'] is True
    assert r2.get('referencia_resolvida')=={}

def test_end_to_end_coordenador_e_contrato():
    e,t,r=prep(); t,r=reconciliar_alvo_eliptico_janela_confirmado('maximiza',turno=t,retrato=r,mente=e)
    p=construir_parecer_operacional('maximiza',turno=t,retrato=r); assert p['autoriza_execucao'] is True and p['requer_esclarecimento'] is False
    t['especialistas']={'operacional':p}
    c=detectar_janela_contextual('maximiza',params_cb=lambda **kw:kw,estado_mental=e,texto_depende_de_contexto=dep)
    trilha=[]; res=resolver_intencao('maximiza','candidate',ctx(t,r,c,trilha)); assert res==({'intent':'MAXIMIZE_WINDOW','params':{'nome_app':'opera'}},'deterministico-explicito')
    contrato=trilha[-1]['contrato_decisao']; assert contrato['permite_acao'] is True and contrato['requer_esclarecimento'] is False and contrato['intencao']=='MAXIMIZE_WINDOW'


def test_segmento_preserva_leitura_original_mas_contrato_top_level_usa_alvo_resolvido():
    e,t,r=prep()
    assert t['segmentos'][0]['requer_esclarecimento'] is True
    t2,_=reconciliar_alvo_eliptico_janela_confirmado('maximiza',turno=t,retrato=r,mente=e)
    assert t2['segmentos'][0]['requer_esclarecimento'] is True
    assert t2['requer_esclarecimento'] is False
    plano=planejar_turno('maximiza',turno=t2,mente=e)
    contrato=dict(plano.get('decisao_turno') or {})
    assert plano['autoriza_execucao'] is True
    assert contrato['permite_acao'] is True
    assert contrato['requer_esclarecimento'] is False

"""Ocorrência observada tem marcos; assunto parecido não apaga novo episódio."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from mente_laylay.autonomia.coordenador_oportunidades import CoordenadorOportunidadesRuntime
from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from mente_laylay.memoria_mental.experiencia_corporal_runtime import ExperienciaCorporalRuntime
from scripts.tests.test_manuseio_fofo import turno_corporal


def evento(agora, *, episodio="sensor:sessao:1", marco="inicio", dominio="corpo"):
    return {"origem":"experiencia_corporal", "dominio":dominio, "categoria":"companhia",
        "conteudo":"A medição frontal indicou um obstáculo.", "evidencias":["Medição frontal recente."],
        "confianca":.94, "utilidade":80, "assunto":"protecao:obstaculo",
        "chave":f"{episodio}:{marco}", "timestamp":agora, "validade_s":25,
        "observacao_corporal":{"sessao":"sessao", "autoriza_execucao":False},
        "ocorrencia_observada":{"episodio_id":episodio, "marco":marco},
        "autoriza_execucao":False, "executavel":False}


def montar():
    agora=[1000.0]; estado={}; coordenacao={}; entregas=[]; contexto={}; viva=[True]
    coordenador=CoordenadorOportunidadesRuntime(estado_get=lambda:coordenacao,
        estado_set=lambda e:coordenacao.update(e), clock=lambda:agora[0],
        encaminhar=lambda d:{"decisao":"sugerir"}, log=lambda _:None)
    def materializar(turno, **k):
        assert turno["autoriza_execucao"] is False
        k["ao_materializar_fala"]("A medição indicou algo perto.")
        entregas.append(k["ao_concluir"])
        return {"status":"agendada", "agendada":True, "emissao_fisica":False}
    diretor=DiretorPresencaRuntime(estado_get=lambda:estado, estado_set=lambda e:estado.update(e),
        clock=lambda:agora[0], contexto_getter=lambda:contexto,
        registrar_oportunidade=coordenador.registrar, validar_observacao=lambda _:viva[0],
        processar_evento_cognitivo=turno_corporal, processar_proposta_comunicativa=materializar,
        log=lambda _:None)
    return diretor,agora,estado,entregas,contexto,viva


def test_novo_episodio_nao_herda_cota_de_rotina_e_repeticao_recente_pesa_na_decisao():
    d,t,s,f,_,_=montar()
    assert d.considerar(evento(t[0]))["status"]=="proposta_cognitiva"
    f[-1](True,"entregue")
    # Antes havia um corte exato em 60 s. Agora este controle cobre saturação
    # recente; mudanças importantes antes desse prazo têm testes próprios.
    t[0]+=10
    assert d.considerar(evento(t[0],episodio="sensor:sessao:2"))["motivo"]=="reacao_sem_novidade_suficiente"
    t[0]+=50
    r=d.considerar(evento(t[0],episodio="sensor:sessao:3"))
    assert r["status"]=="proposta_cognitiva",r
    assert len(f)==2 and s["contadores"]["emitidas"]==1


def test_falha_de_audio_nao_e_entrega_nem_libera_rajada_de_tentativas():
    d,t,s,f,_,_=montar()
    d.considerar(evento(t[0])); f[-1](False,"falha_entrega")
    assert s["contadores"]["emitidas"]==0 and not s["historico"]
    t[0]+=10
    assert d.considerar(evento(t[0],episodio="sensor:sessao:2"))["motivo"]=="reacao_sem_novidade_suficiente"
    t[0]+=50
    assert d.considerar(evento(t[0],episodio="sensor:sessao:3"))["status"]=="proposta_cognitiva"


@pytest.mark.parametrize("dominio",["corpo","cotidiano"])
def test_coordenador_distingue_ocorrencias_sem_transformar_identidade_em_autoridade(dominio):
    estado={}
    r=CoordenadorOportunidadesRuntime(estado_get=lambda:estado, estado_set=lambda e:estado.update(e),
        encaminhar=lambda d:{"decisao":"sugerir", "executavel":d["executavel"]},log=lambda _:None)
    a=evento(1000,dominio=dominio)
    assert r.registrar(a)["decisao"]=="sugerir"
    assert r.registrar(a)["decisao"]=="ignorar_duplicada_semantica"
    b=evento(1000,episodio="outra",dominio=dominio)
    assert r.registrar(b)=={"decisao":"sugerir","executavel":False}


@pytest.mark.parametrize("campo",["usuario_falando","turno_ativo"])
def test_marco_nao_supera_prioridade_humana(campo):
    d,t,_,f,c,_=montar(); c[campo]=True
    assert d.considerar(evento(t[0]))["status"]=="bloqueada" and not f


def test_sem_validacao_viva_nao_obtem_politica_de_reacao_e_expirado_nao_gera_fala():
    d,t,_,f,_,v=montar(); v[0]=False
    assert d.considerar(evento(t[0]))["motivo"]=="observacao_expirada" and not f
    v[0]=True
    assert d.considerar(evento(t[0]-26))["motivo"]=="evento_expirado"


def test_observacao_sem_marco_mantem_cota_de_rotina_e_fala_repetida_continua_filtrada():
    d,t,_,f,_,_=montar()
    a=evento(t[0]); a.pop("ocorrencia_observada")
    d.considerar(a); f[-1](True,"entregue"); t[0]+=60
    b=evento(t[0],episodio="outro"); b.pop("ocorrencia_observada")
    assert d.considerar(b)["motivo"]=="orcamento_dominio"
    p=PorteiroProatividadeRuntime(contexto_getter=lambda:{},agora=lambda:t[0])
    assert p.avaliar(tipo="presenca_corporal",texto="Foi um susto.")["acao"]=="emitir"
    t[0]+=60
    assert p.avaliar(tipo="presenca_corporal",texto="Foi um susto.")["acao"]=="descartar"


@pytest.mark.parametrize("recusas",[0,1,2])
def test_porteiro_migra_base_antiga_para_60_preservando_recusas(recusas):
    t=[1000.0]; perfil={"presenca_corporal":{"intervalo_s":120*(2**recusas),
        "recusas_consecutivas":recusas,"ultima_emissao_ts":1000}}
    p=PorteiroProatividadeRuntime(contexto_getter=lambda:{},agora=lambda:t[0],perfil_getter=lambda:deepcopy(perfil),
        perfil_setter=lambda novo:perfil.update(novo))
    intervalo=60*(2**recusas)
    t[0]=1000+intervalo-1
    assert p.avaliar(tipo="presenca_corporal",texto="A medição mudou.")["acao"]=="descartar"
    t[0]+=1
    assert p.avaliar(tipo="presenca_corporal",texto="A medição mudou.")["acao"]=="emitir"
    assert perfil["presenca_corporal"]["intervalo_s"]==intervalo


def test_sensor_publica_inicio_mudanca_e_recuperacao_sem_repetir_fases_motoras():
    t=[1000.0]; estado=criar_estado_compartilhado_runtime()
    diag={"aplicacao_confirmada":True,"sessao":"s1", "sensores":{
        "origem":"owner_usb_dist_guard","suportado":True,"recente":True,"consulta_id":1,
        "protecao":{"origem":"executor_protecao_esp","recente":True,"autoriza_execucao":False,
            "incidente_id":1,"risco":"OBSTACULO","fase":"RECUANDO","tentativa_busca":0}}}
    r=ExperienciaCorporalRuntime(estado=estado,diagnostico_getter=lambda:diag,clock=lambda:t[0])
    def atualizar(risco,fase):
        t[0]+=1; diag["sensores"]["consulta_id"]+=1
        diag["sensores"]["protecao"].update(risco=risco,fase=fase)
        r.observar_sensores(diag,perfil="bancada")
        return r.candidato_presenca()
    a=atualizar("OBSTACULO","RECUANDO")
    assert a["ocorrencia_observada"]["marco"]=="inicio"
    assert not atualizar("OBSTACULO","BUSCANDO")
    b=atualizar("BORDA_SEM_RETORNO","BLOQUEADA")
    assert b["ocorrencia_observada"]["marco"].startswith("mudanca")
    c=atualizar("NENHUM","PRONTA")
    assert c["ocorrencia_observada"]["marco"]=="recuperacao"
    assert "deslocamento" in c["motivo"]
    assert c["timestamp"]==t[0] and r.evento_presenca_vigente(c)
    for campo,valor in [("episodio_id","inventado"),("marco","inicio")]:
        falso=deepcopy(c); falso["ocorrencia_observada"][campo]=valor
        assert not r.evento_presenca_vigente(falso)
    assert not atualizar("NENHUM","PRONTA")
    diag["sessao"]="s2"
    assert not r.evento_presenca_vigente(c)


def test_catalogo_conhece_marcos_relevancia_e_silencio():
    from mente_laylay.especialistas.capacidades import consultar_capacidade
    texto=consultar_capacidade("CORPO_COMPANHIA")["objetivos_e_relato_condicionais"]
    assert "sem mínimo fixo" in texto and "saturação" in texto and "recuperação" in texto and "silêncio" in texto


def test_composicao_instalada_entrega_marcos_ao_porteiro_sem_conceder_motores():
    """Root real; isolam-se só diagnóstico físico, modelo e saída de áudio."""
    codigo=textwrap.dedent(r'''
        import json, os, sys, time
        from mente_laylay.integracao import instancia_unica
        adquirir=instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica=lambda nome, **k: adquirir(str(nome)+'.marcos-'+str(os.getpid()), **k)
        import laylay as root
        from mente_laylay.integracao.registro_conversa_llm import ResultadoModelo
        from scripts.tests.test_porteiro_proatividade import TimerControlado
        estado=root._estado_compartilhado_runtime
        estado.atualizar_campos('mental', presenca_contextual={}, historico_corporal=[])
        diretor=root._diretor_presenca_runtime
        corpo=root._corpo_motor_runtime
        produtor=corpo.experiencias
        assert diretor.notificacao_observada is produtor.notificacao_observada
        voz=root._voz_runtime
        t=[time.time()]
        diretor.clock=produtor.clock=root._coordenador_oportunidades_runtime.clock=lambda:t[0]
        root._porteiro_proatividade_runtime._agora=lambda:t[0]
        voz.timer_factory=TimerControlado
        # Nenhum worker de áudio ou sincronizador físico é iniciado.
        voz.worker_started=True
        pedidos=[]
        def modelo(p):
            pedidos.append(p.tipo_chamada)
            return ResultadoModelo(texto=json.dumps({'fala':f'Obstáculo medido na tentativa {len(pedidos)}.', 'comandos':[]}), sucesso=True, rota='teste')
        from types import SimpleNamespace
        root._resposta_evento_runtime.modelo_llm=SimpleNamespace(executar=modelo)
        diag={'aplicacao_confirmada':True,'sessao':'composicao-marcos','sensores':{
            'origem':'owner_usb_dist_guard','suportado':True,'recente':True,'consulta_id':1,
            'protecao':{'origem':'executor_protecao_esp','recente':True,'autoriza_execucao':False,
                'incidente_id':1,'risco':'OBSTACULO','fase':'RECUANDO','tentativa_busca':0}}}
        produtor.diagnostico_getter=lambda:diag
        root._motor_iniciativa_runtime.ativar_perfil_seguro_padrao()
        saidas=[]
        for numero in (1,2):
            diag['sensores']['consulta_id']+=1
            diag['sensores']['protecao']['incidente_id']=numero
            if numero==2:
                diag['sensores']['protecao']['risco']='BORDA'
            produtor.observar_sensores(diag,perfil='diagnostico_sem_motores')
            saidas.append(diretor.executar_ciclo())
            if numero==1:
                with voz.proativa_lock:
                    itens=list(voz.proativa_buffer); voz.proativa_buffer=[]
                voz._concluir_itens_proativos(itens,False,'falha_audio_diagnostico',voz.log)
                t[0]+=5
        presenca=estado.obter_copia('mental','presenca_contextual',{})
        resultado={'saidas':saidas,'pedidos':pedidos,'fila':len(voz.proativa_buffer),
            'emitidas':presenca['contadores']['emitidas'],
            'instalacao':diretor.candidato_observado_getter==produtor.candidato_presenca,
            'sem_concessao':not corpo.companhia.diagnostico()['ativa'],
            'ultima':presenca.get('ultima_proposta_cognitiva',{})}
        with voz.proativa_lock:
            itens=list(voz.proativa_buffer); voz.proativa_buffer=[]
        voz._concluir_itens_proativos(itens,False,'fim_teste',voz.log)
        sys.__stdout__.write('MARCOS_INSTALADOS '+json.dumps(resultado,ensure_ascii=False,default=str)+'\n')
    ''')
    processo=subprocess.run([sys.executable,"-c",codigo],cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ,PYTHONIOENCODING="utf-8",LAYLAY_MASCOT_ENABLED="0",LAYLAY_AVATAR_ATIVO="0",
            LAYLAY_TERMINAL_2="0",LAYLAY_IOT_MODO="simulado",LAYLAY_NEURAL_COLETA_ENTRADAS="0",
            LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0"),
        capture_output=True,text=True,encoding="utf-8",timeout=75)
    assert processo.returncode==0,processo.stdout[-1500:]+processo.stderr[-3000:]
    r=json.loads(next(l.removeprefix("MARCOS_INSTALADOS ") for l in processo.stdout.splitlines()
        if l.startswith("MARCOS_INSTALADOS ")))
    assert r["instalacao"] and r["sem_concessao"]
    assert all(s.get("proposta_comunicativa",{}).get("agendada") is True for s in r["saidas"]),r
    assert r["pedidos"]==["presenca_evento","presenca_evento"]
    assert r["fila"]==1 and r["emitidas"]==0
    assert r["ultima"]["ocorrencia_observada"]["marco"]=="inicio"

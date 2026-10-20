"""Publicação observada desperta presença; timer de rotina não é latência da reação."""
import threading
import time

from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from scripts.tests.test_presenca_episodios_observados import evento, montar


def test_novo_fato_desperta_diretor_sem_esperar_ciclo_de_quinze_segundos():
    pronto=threading.Event(); reagiu=threading.Event(); sinal=threading.Event()
    candidatos=[]; horarios=[]
    def obter():
        pronto.set()
        return candidatos.pop(0) if candidatos else {}
    d=DiretorPresencaRuntime(candidato_observado_getter=obter,
        processar_evento_cognitivo=lambda e:{},processar_proposta_comunicativa=lambda *a,**k:{},
        intervalo_ciclo_s=15,log=lambda _:None)
    # Porta de notificação do owner: nenhum dado ou autorização via sinal.
    d.notificacao_observada=sinal
    d.considerar=lambda e:horarios.append(time.monotonic()) or reagiu.set() or {}
    t=threading.Thread(target=d.executar,daemon=True);t.start()
    try:
        assert pronto.wait(1)
        inicio=time.monotonic(); candidatos.append(evento(time.time()));sinal.set()
        assert reagiu.wait(.6),'novo fato ficou preso no timer de rotina de 15 s'
        assert horarios[0]-inicio < .6
    finally:d.encerrar();t.join(1)
    assert not t.is_alive()


def test_sinal_nao_dispara_rotina_a_cada_telemetria_nem_supera_prioridade():
    d,t,_,fila,contexto,_=montar(); contexto['usuario_falando']=True
    recebidos=[]
    d.candidato_observado_getter=lambda:evento(t[0])
    d._candidato_cotidiano=lambda *args:recebidos.append(True) or {}
    # Execução só de observação mantém as mesmas portas de governança.
    assert d.executar_ciclo(incluir_cotidiano=False)['motivo']=='usuario_falando'
    assert not fila and not recebidos


def test_publicacao_do_owner_sinaliza_depois_do_estado_sem_repetir_leitura():
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
    from mente_laylay.memoria_mental.experiencia_corporal_runtime import ExperienciaCorporalRuntime
    estado=criar_estado_compartilhado_runtime()
    diag={'aplicacao_confirmada':True,'sessao':'wake-test','imu':{
        'origem':'imu_esp','recente':True,'autoriza_execucao':False,
        'manuseio':'INCLINADA','fase_manuseio':'DESCONFIADA','evento_manuseio':1}}
    r=ExperienciaCorporalRuntime(estado=estado,diagnostico_getter=lambda:diag)
    assert not r.notificacao_observada.is_set()
    r.observar_inercial(diag,perfil='diagnostico')
    assert r.notificacao_observada.is_set() and r.candidato_presenca()
    r.notificacao_observada.clear()
    r.observar_inercial(diag,perfil='diagnostico')
    assert not r.notificacao_observada.is_set() and not r.candidato_presenca()


def test_sinal_sem_candidato_nao_dispara_cotidiano_e_encerramento_acorda_rapido():
    pronto=threading.Event(); sinal=threading.Event(); chamadas=[]
    d=DiretorPresencaRuntime(candidato_observado_getter=lambda:pronto.set() or {},
        notificacao_observada=sinal, intervalo_ciclo_s=15,
        processar_evento_cognitivo=lambda e:{},processar_proposta_comunicativa=lambda *a,**k:{},
        log=lambda _:None)
    d._candidato_cotidiano=lambda *args:chamadas.append(True) or {}
    t=threading.Thread(target=d.executar,daemon=True);t.start()
    try:
        assert pronto.wait(1)
        sinal.set(); time.sleep(.04)
        assert len(chamadas)==1
    finally:
        inicio=time.monotonic();d.encerrar();t.join(.7)
    assert not t.is_alive() and time.monotonic()-inicio < .7


def test_publicacao_durante_autoria_nao_perde_sinal_e_usa_estado_mais_recente():
    sinal=threading.Event(); entrou=threading.Event(); liberar=threading.Event(); segunda=threading.Event()
    pendentes=[{'id':1}]; ids=[]
    def obter():
        return pendentes.pop() if pendentes else {}
    d=DiretorPresencaRuntime(candidato_observado_getter=obter,notificacao_observada=sinal,
        processar_evento_cognitivo=lambda e:{},processar_proposta_comunicativa=lambda *a,**k:{},
        log=lambda _:None)
    def considerar(e):
        ids.append(e['id'])
        if e['id']==1:
            entrou.set();liberar.wait(1)
        else:segunda.set()
        return {}
    d.considerar=considerar
    t=threading.Thread(target=d.executar,daemon=True);t.start()
    try:
        assert entrou.wait(1)
        pendentes[:]=[{'id':3}];sinal.set()  # duas alterações coalescidas no fato 3
        liberar.set()
        assert segunda.wait(.6) and ids==[1,3]
    finally:liberar.set();d.encerrar();t.join(1)

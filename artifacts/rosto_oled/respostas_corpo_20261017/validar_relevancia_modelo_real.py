"""Root e modelo reais, estímulos controlados; sem hardware nem áudio."""
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))


def main():
    from mente_laylay.integracao import instancia_unica
    adquirir=instancia_unica.adquirir_instancia_unica
    instancia_unica.adquirir_instancia_unica=lambda nome,**k:adquirir(str(nome)+'.relevancia-'+str(os.getpid()),**k)
    import laylay as root
    from scripts.tests.test_porteiro_proatividade import TimerControlado
    d=root._diretor_presenca_runtime;p=root._corpo_motor_runtime.experiencias;v=root._voz_runtime
    p.aprendizado=None
    root._motor_iniciativa_runtime.ativar_perfil_seguro_padrao()
    v.timer_factory=TimerControlado;v.worker_started=True
    diag={'aplicacao_confirmada':True,'sessao':'diagnostico-relevancia','sensores':{
        'origem':'owner_usb_dist_guard','suportado':True,'recente':True,'consulta_id':1,
        'protecao':{'origem':'executor_protecao_esp','recente':True,'autoriza_execucao':False,
            'incidente_id':1,'risco':'OBSTACULO','fase':'RECUANDO','tentativa_busca':0}}}
    p.diagnostico_getter=lambda:diag
    saidas=[]
    try:
        inicio=time.monotonic()
        for numero,risco in enumerate(('OBSTACULO','BORDA_SEM_RETORNO','BORDA_SEM_RETORNO'),1):
            diag['sensores']['consulta_id']+=1
            diag['sensores']['protecao'].update(incidente_id=numero,risco=risco)
            p.observar_sensores(diag,perfil='diagnostico_sem_hardware')
            r=d.executar_ciclo()
            saidas.append({'segundos':round(time.monotonic()-inicio,3),'risco':risco,'decisao':r})
            # A falha de entrega abaixo é deliberada: não houve reprodução.
            with v.proativa_lock:
                itens=list(v.proativa_buffer);v.proativa_buffer=[]
            v._concluir_itens_proativos(itens,False,'diagnostico_sem_audio',v.log)
        estado=root._estado_compartilhado_runtime.obter_copia('mental','presenca_contextual',{})
        resultado={'tipo':'root_modelo_reais_estimulo_controlado','sem_hardware_sem_audio':True,
            'saidas':saidas,'emitidas':estado['contadores']['emitidas'],
            'admissoes':estado.get('admissoes_observadas'),
            'ultima_decisao':estado.get('ultima_decisao')}
        Path(__file__).with_name('relevancia_modelo_real.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2,default=str),encoding='utf8')
        print('RELEVANCIA_REAL '+json.dumps(resultado,ensure_ascii=False,default=str),flush=True)
    finally:
        with v.proativa_lock:
            itens=list(v.proativa_buffer);v.proativa_buffer=[]
        v._concluir_itens_proativos(itens,False,'fim_diagnostico',v.log)


if __name__=='__main__':main()

"""Serviços reais de rosto/companhia no root, com captura causal e término finito."""
import os,sys,time,json,threading,traceback
from pathlib import Path
SAIDA=Path(__file__).resolve().parent
RAIZ=SAIDA.parents[2]
sys.path.insert(0,str(RAIZ))
os.environ['LAYLAY_ROSTO_PORTA']='COM4'
os.environ['LAYLAY_CORPO_WIFI_CONFIG']=str(SAIDA/'sem_wifi.json')
from mente_laylay.integracao import instancia_unica
adquirir=instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica=lambda _:adquirir(SAIDA/'instancia_diagnostico')
import laylay
r=laylay._rosto_oled_runtime; c=laylay._corpo_motor_runtime
parar=threading.Event(); eventos=[]; registros=[]; inicio=time.monotonic()
escrever=r._escrever
def observar(linha):
    if linha.startswith(('HELLO ','MOTOR ','STOP','SENTRY ')):
        eventos.append({'t':round(time.monotonic()-inicio,3),'tipo':linha.split()[0],
            'ativo':linha.split()[4] if linha.startswith('SENTRY ') else None})
    escrever(linha)
r._escrever=observar
processar=c.companhia.processar
ultimo_motivo=[None]
def observar_decisao():
    ret=processar()
    chave=(ret.get('motivo'),c.companhia.diagnostico()['ativa'])
    if chave!=ultimo_motivo[0]:
        eventos.append({'t':round(time.monotonic()-inicio,3),'tipo':'DECISAO_COMPANHIA','motivo':ret.get('motivo'),'ativa':chave[1]})
        ultimo_motivo[0]=chave
    return ret
c.companhia.processar=observar_decisao
workers=[threading.Thread(target=x.executar,kwargs={'deve_parar':parar.is_set,'aguardar_fn':parar.wait},daemon=True)
    for x in ((r,) if any(a in sys.argv for a in ('--sem-motor','--consulta-sensores')) else (r,c.companhia))]
reset=False
pausa='--pausa-busca' in sys.argv
claim=None; liberada=False; inicio_prioridade=None
try:
    for w in workers:w.start()
    while time.monotonic()-inicio<(10 if '--consulta-sensores' in sys.argv else 60 if pausa else 50):
        t=time.monotonic()-inicio
        d=r.diagnostico(); m=c.companhia.diagnostico()
        registros.append({'t':round(t,3),'confirmada':d['aplicacao_confirmada'],'motivo':d['motivo'],
            'sessao':d['sessao'],'saude':d['saude'],'companhia':m,
            'protecao':d['sensores'].get('protecao'), 'leituras':d['sensores'].get('leituras')})
        protecao=d['sensores'].get('protecao') or {}
        inferior=(d['sensores'].get('leituras') or {}).get('borda') or {}
        if (pausa and t>=3 and claim is None and m['ativa']
            and protecao.get('fase') in {'BUSCANDO','CONFERINDO','ESPERA_BUSCA'}
            and protecao.get('risco')=='OBSTACULO'
            and inferior.get('estado')=='VALIDA' and inferior.get('mm',999)<=120):
            claim=laylay._prioridade_interacao_usuario_runtime.adquirir('diagnostico_pausa_busca')
            inicio_prioridade=t
            eventos.append({'t':round(t,3),'tipo':'PRIORIDADE_INICIO'})
        if pausa and claim and t>=inicio_prioridade+4 and not liberada:
            laylay._prioridade_interacao_usuario_runtime.liberar(claim)
            liberada=True
            eventos.append({'t':round(t,3),'tipo':'PRIORIDADE_FIM'})
        if pausa and liberada and t>=inicio_prioridade+18:
            break
        if any(a in sys.argv for a in ('--reset-controlado','--perder-sessao')) and t>=20 and not reset and m['ativa']:
            with r._lock:
                # Corte antes do reset intencional. Não reaproveitar o movimento interrompido.
                r._parar_corpo_conectado()
                if '--perder-sessao' in sys.argv:
                    eventos.append({'t':round(t,3),'tipo':'SESSAO_SUBSTITUIDA_CONTROLADA'})
                    r._serial.write(b'HELLO 1 f0f0f0f0\n')
                else:
                    eventos.append({'t':round(t,3),'tipo':'RESET_USB_CONTROLADO'})
                    r._serial.dtr=False
                    r._serial.rts=True; r._serial.dtr=False; time.sleep(.2)
                    r._serial.rts=False; r._serial.dtr=False; time.sleep(.2)
            reset=True
        parar.wait(.15)
finally:
    if claim:
        laylay._prioridade_interacao_usuario_runtime.liberar(claim)
    parar.set()
    c.companhia.revogar('fim_diagnostico')
    for w in workers:w.join(timeout=5)
    r.encerrar()
    assert not any(w.is_alive() for w in workers),'Serviço não encerrou'
    destino=(Path(sys.argv[sys.argv.index('--saida')+1]) if '--saida' in sys.argv else SAIDA/('runtime_perda_sessao.json' if '--perder-sessao' in sys.argv else 'runtime_sem_motor.json' if '--sem-motor' in sys.argv else 'runtime_reset_controlado.json' if '--reset-controlado' in sys.argv else 'runtime_natural.json'))
    destino.write_text(
        json.dumps({'registros':registros,'eventos':eventos,'reset_controlado':reset,'encerrada':True},ensure_ascii=False,indent=2),encoding='utf-8')

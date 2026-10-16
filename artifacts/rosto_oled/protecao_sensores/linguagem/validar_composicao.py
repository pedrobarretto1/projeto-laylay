"""Root real, concessão salva de bancada e reflexos locais, sem passeio/ordem MOTOR."""
import os,sys,json,time
from pathlib import Path
SAIDA=Path(__file__).resolve().parent
RAIZ=SAIDA.parents[3]
sys.path.insert(0,str(RAIZ))
os.environ['LAYLAY_ROSTO_PORTA']='COM4'
os.environ['LAYLAY_CORPO_WIFI_CONFIG']=str(SAIDA/'sem_wifi.json')
from mente_laylay.integracao import instancia_unica
adquirir=instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica=lambda _:adquirir(SAIDA/'instancia_diagnostico')
import laylay
r=laylay._rosto_oled_runtime; c=laylay._corpo_motor_runtime
escrever=r._escrever; enviados=[]; registros=[]
def observar(linha):
    assert not linha.startswith('MOTOR '),'Nenhuma ordem de passeio neste diagnóstico'
    enviados.append(linha.split()[0]); escrever(linha)
r._escrever=observar
armar='--armar' in sys.argv
parede='--parede' in sys.argv
try:
    assert r.sincronizar(),r.diagnostico()['motivo']
    if parede:
        b=r.diagnostico()['sensores']['leituras']['borda']
        assert b['estado']=='VALIDA' and b['mm']<=120,'Inferior precisa confirmar superficie antes do teste da parede'
    if armar:
        assert c.companhia._automatica_ao_iniciar,'Requer preferência explícita salva'
        assert c.companhia.processar()['ok'],'Ativação deve passar pelo owner real'
    inicio=time.monotonic()
    while time.monotonic()-inicio<12:
        assert r.sincronizar(),r.diagnostico()['motivo']
        s=r.diagnostico()['sensores']; modelo=c.modelo_para_mente()
        dev=laylay._dev_console_runtime.atualizar_corpo()
        assert modelo['condicao']['reacao_expressiva']==s['protecao']['reacao_expressiva']
        assert dev['vigia_sensores_ativa']==s['protecao']['vigia_ativa']
        registros.append({'t':round(time.monotonic()-inicio,3),'sensores':s,'dev':dev})
        time.sleep(.08)
finally:
    c.companhia.revogar('fim_diagnostico'); r.encerrar()
    (SAIDA/('composicao_parede.json' if parede else 'composicao_armada.json' if armar else 'composicao_sem_motor.json')).write_text(
        json.dumps({'registros':registros,'tipos_enviados':sorted(set(enviados)),
            'armar':armar,'encerrada':True},ensure_ascii=False,indent=2),encoding='utf-8')

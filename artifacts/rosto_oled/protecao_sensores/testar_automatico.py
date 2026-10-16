"""Uma única ordem autorizada em rodas suspensas; sem iniciar companhia."""
import os, sys, json, time, threading
from pathlib import Path
RAIZ=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(RAIZ))
os.environ['LAYLAY_ROSTO_PORTA']='COM4'
os.environ['LAYLAY_CORPO_WIFI_CONFIG']=str(Path(__file__).parent/'sem_wifi.json')
from mente_laylay.integracao import instancia_unica
adquirir=instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica=lambda _: adquirir(Path(__file__).parent/'instancia_auto')
import laylay
r=laylay._rosto_oled_runtime
c=laylay._corpo_motor_runtime
linhas=[]; parar=threading.Event(); resultado=[]
enviados=[]; escrever=r._escrever
def observar(linha):
    enviados.append(linha); escrever(linha)
r._escrever=observar
def amostrar():
    while not parar.is_set():
        if r.sincronizar():
            m=c.modelo_para_mente()
            linhas.append({'ts':time.time(),'sensores':r.diagnostico()['sensores'],
                'condicao':m['condicao'], 'dev':laylay._dev_console_runtime.atualizar_corpo()})
        parar.wait(.04)
try:
    assert c.transporte is r and r.sincronizar()
    print('LEITURA',r.diagnostico()['sensores'],flush=True)
    t=threading.Thread(target=amostrar); t.start()
    print('TESTE AUTOMATICO: ordem unica em rodas suspensas',flush=True)
    resultado.append(r.mover_corpo(140,140,3000))
    time.sleep(.3)
finally:
    parar.set()
    if 't' in globals(): t.join(2)
    r.encerrar()
    dados={'ordens_motor':sum(s.startswith('MOTOR ') for s in enviados),
        'encerrada':True,'receipts':resultado,'observacoes':linhas,
        'catalogo':laylay._mapa_habilidades_runtime.responder_pergunta_capacidade('voce tem sensores de borda?')}
    (Path(__file__).parent/'automatico.json').write_text(json.dumps(dados,ensure_ascii=False,indent=2),encoding='utf-8')
print('RESULTADO',resultado,flush=True)
print('FASES',sorted({s['sensores']['protecao']['fase'] for s in linhas}),flush=True)

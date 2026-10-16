"""Composition root real: sensor/expressão/mente/DEV, com tração proibida."""
import os,sys,json,time
from pathlib import Path
SAIDA=Path(__file__).resolve().parent
RAIZ=SAIDA.parents[3]
sys.path.insert(0,str(RAIZ))
os.environ['LAYLAY_ROSTO_PORTA']='COM4'
os.environ['LAYLAY_CORPO_WIFI_CONFIG']=str(SAIDA/'sem_wifi.json')
from mente_laylay.integracao import instancia_unica
adquirir=instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica=lambda _: adquirir(SAIDA/'instancia_sensores')
import laylay
r=laylay._rosto_oled_runtime; c=laylay._corpo_motor_runtime
assert c.transporte is r
assert not c.companhia.autorizar_busca_obstaculos('sem_sessao')
escrever=r._escrever; enviados=[]
def observar(linha):
    assert not linha.startswith('MOTOR '),'Validação sem motor'
    assert not (linha.startswith('SENTRY ') and linha.split()[4]=='1'),'Não armar busca durante ausência do usuário'
    enviados.append(linha); escrever(linha)
r._escrever=observar
registros=[]
try:
    for _ in range(10):
        assert r.sincronizar(),r.diagnostico()['motivo']
        modelo=c.modelo_para_mente()
        dev=laylay._dev_console_runtime.atualizar_corpo()
        sensores=r.diagnostico()['sensores']
        assert sensores['suportado'] and not sensores['protecao']['vigia_ativa']
        assert dev['reacao_sensor']==sensores['protecao']['reacao_expressiva']
        assert modelo['condicao']['reacao_expressiva']==sensores['protecao']['reacao_expressiva']
        registros.append({'ts':time.time(),'sensores':sensores,'condicao':modelo['condicao'],'dev':dev})
        time.sleep(.15)
    resposta=laylay._mapa_habilidades_runtime.responder_pergunta_capacidade('voce tem sensores de borda e parede?')
    assert 'VIGIA1' in resposta and 'quatro' in resposta
finally:
    r.encerrar()
    (SAIDA/'composicao.json').write_text(json.dumps({'registros':registros,'tipos_enviados':sorted({s.split()[0] for s in enviados}),
        'sem_motor':True,'vigia_armada':False,'encerrada':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('COMPOSICAO_REAL_GREEN: alerta/mente/DEV/capacidade, nenhuma tracao, encerrada')

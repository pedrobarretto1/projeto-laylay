"""Ensaio autorizado com rodas suspensas. Usa os owners de produção pela USB.

O escopo de tarefa PC é simulado e explicitamente rotulado; não inventa
receipts de sucesso nem percepção espacial. Rotação depende da observação humana.
"""
from pathlib import Path
import hashlib
import json
import sys
import threading
import time
from types import SimpleNamespace

RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ))
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from mente_laylay.memoria_mental.atividade_operacional_runtime import criar_atividade_operacional_runtime
from mente_laylay.integracao.composicao_rosto_oled import criar_composicao_rosto_oled_runtime
from mente_laylay.especialistas.corpo_motor_runtime import criar_corpo_motor_runtime
from mente_laylay.autonomia.orquestracao_cooperativa import OrquestradorCooperativoRuntime
from mente_laylay.autonomia.quadro_cooperacao import QuadroCooperacaoRuntime

estado=criar_estado_compartilhado_runtime()
atividade=criar_atividade_operacional_runtime(estado=estado)
erros=[]
rosto=criar_composicao_rosto_oled_runtime(estado=estado,porta="COM4",
    observabilidade=SimpleNamespace(relatar_falha=lambda *a,**k:erros.append(str(a[1:]))))
corpo=criar_corpo_motor_runtime(transporte=rosto,estado=estado,perfil_corporal="rodas_suspensas",
    companhia_bancada_ao_iniciar=True,passeio_bancada_ao_iniciar=True,
    observar_resultado_cb=lambda r:atividade.observar_resultado(r,retorno_executor=True))
quadro=QuadroCooperacaoRuntime(modo="ativo",log=lambda _:None)
coord=OrquestradorCooperativoRuntime(quadro=quadro,clipboard_snapshot=lambda:{},clipboard_getter=lambda:"",
    executar_intencao=lambda *_:False,resolver_caminho=lambda s:s,falar=lambda *_:None,log=lambda _:None)
corpo.companhia.coordenador=coord
coord.governanca.registrar_autorizador_escopo("corpo_companhia",corpo.companhia.autorizar_escopo)
parar=threading.Event()
supervisor=threading.Thread(target=lambda:rosto.executar(deve_parar=parar.is_set,aguardar_fn=parar.wait),daemon=True)
passos=[]
falha=""
supervisor.start()
try:
    limite=time.monotonic()+8
    while time.monotonic()<limite and not rosto.diagnostico()["aplicacao_confirmada"]: time.sleep(.1)
    assert rosto.diagnostico()["motor"]["duracao_maxima_ms"]==5000,rosto.diagnostico()
    assert corpo.companhia.processar()["ok"]
    passos.append({"fase":"concessao_usb", "diagnostico":corpo.diagnostico()})
    time.sleep(8.2)
    retorno=corpo.companhia.processar()
    assert retorno["ok"],retorno
    passos.append({"fase":"exploracao_continua", "retorno":retorno, "intencao":estado.mental["intencao_corporal"]})
    # Após acomodação, introduzir uma tarefa interna controlada durante movimento.
    time.sleep(12.2)
    resultado=[]
    executor=threading.Thread(target=lambda:resultado.append(corpo.companhia.processar()),daemon=True)
    executor.start()
    limite=time.monotonic()+4
    while time.monotonic()<limite and not rosto.diagnostico()["motor"]["em_andamento"]: time.sleep(.02)
    assert rosto.diagnostico()["motor"]["em_andamento"]
    time.sleep(.4)
    with atividade.escopo():
        executor.join(2)
        assert not executor.is_alive(),"movimento não cedeu à atividade PC"
        assert resultado and not resultado[0]["ok"],resultado
        assert not corpo.companhia.processar()["ok"]
        assert estado.mental["intencao_corporal"]["nome"]=="atenta"
        passos.append({"fase":"tarefa_pc_simulada_interrompeu", "retorno":resultado[0],
                       "intencao":estado.mental["intencao_corporal"], "atividade_simulada":True})
    retorno=corpo.executar("CORPO_PARAR",{})
    assert retorno["parada_confirmada"],retorno
    passos.append({"fase":"parada_final", "retorno":retorno})
except Exception as erro:
    falha=str(erro)
finally:
    corpo.executar("CORPO_PARAR",{})
    parar.set();supervisor.join(4);rosto.encerrar()
dados={"passos":passos,"falha":falha,"erros":erros,"observacao_humana":"pendente",
       "perfil":"rodas_suspensas","fonte_sha256":hashlib.sha256((RAIZ/'firmware/rosto_laylay/rosto_laylay.ino').read_bytes()).hexdigest()}
destino=RAIZ/'artifacts/rosto_oled/corpo_decisao_v1/receipt_fisico.json'
destino.write_text(json.dumps(dados,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({"receipt":str(destino),"passos":len(passos),"falha":falha},ensure_ascii=False))
if falha:raise SystemExit(1)

"""Repete somente acordar/adormecer pela USB; não envia MOTOR."""
from pathlib import Path
import json
import sys
import threading
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import serial
from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime

tx=[]
rx=bytearray()
class PortaSono(serial.Serial):
    def write(self,dados):
        tx.append(dados.decode().strip())
        return super().write(dados)
    def read(self,n):
        dados=super().read(n);rx.extend(dados)
        return dados

rosto=RostoOledRuntime(estado_getter=lambda:{},porta="COM4",
    abrir_serial=lambda p:PortaSono(p,115200,timeout=.1,write_timeout=.5))
fim=threading.Event()
thread=threading.Thread(target=lambda:rosto.executar(deve_parar=fim.is_set,aguardar_fn=fim.wait),daemon=True)
falha=""
try:
    print("Olhe o OLED: acordando gradualmente",flush=True)
    thread.start()
    prazo=time.monotonic()+7
    while time.monotonic()<prazo and not rosto.diagnostico()["aplicacao_confirmada"]:time.sleep(.05)
    assert rosto.diagnostico()["aplicacao_confirmada"]
    time.sleep(4.1)
    print("Agora adormecendo gradualmente",flush=True)
    fim.set();thread.join(4)
    assert not thread.is_alive()
    assert b"NACK 1 " in rx,"firmware não confirmou boa noite"
    assert not any(x.startswith("MOTOR ") for x in tx)
    time.sleep(3.6)
except Exception as e:
    falha=type(e).__name__+": "+(str(e) or "asserção não satisfeita")
finally:
    fim.set();thread.join(4);rosto.encerrar()
destino=Path(__file__).resolve().parents[1]/"artifacts/rosto_oled/presenca_v2/receipt_sono.json"
destino.write_text(json.dumps({"falha":falha,"boa_noite_confirmada":b"NACK 1 " in rx,
    "comandos_motor":sum(x.startswith("MOTOR ") for x in tx),"observacao_humana":"pendente"},indent=2),encoding="utf-8")
print(json.dumps({"falha":falha,"receipt":str(destino)},ensure_ascii=False),flush=True)
if falha:raise SystemExit(1)

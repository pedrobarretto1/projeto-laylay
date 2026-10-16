"""Ensaio finito do sensor real/olhos; não concede companhia nem tração."""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ))
from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime


def main() -> None:
    args=argparse.ArgumentParser()
    args.add_argument("--segundos",type=float,default=40)
    args.add_argument("--porta",default="COM4")
    args=args.parse_args()
    if not 1<=args.segundos<=60:raise SystemExit("janela inválida")
    estado=criar_estado_compartilhado_runtime()
    rosto=RostoOledRuntime(estado_getter=lambda:estado.retrato_dominio("conversacional"),porta=args.porta)
    corpo=CorpoMotorRuntime(transporte=rosto,estado=estado)
    trilha=[];registros=[];erro="";inicio=time.monotonic()
    escrever=rosto._escrever
    def protegido(linha):
        trilha.append(linha)
        if linha.startswith(("MOTOR ","TURN ")):raise AssertionError("ensaio sem tração")
        escrever(linha)
    rosto._escrever=protegido
    try:
        while time.monotonic()-inicio<args.segundos:
            if not rosto.sincronizar():raise RuntimeError(rosto.diagnostico().get("motivo"))
            d=rosto.diagnostico()
            corpo.experiencias.observar_sensores(d,perfil="diagnostico_sem_motores")
            registros.append({"t":round(time.monotonic()-inicio,3),"imu":d.get("imu"),
                              "modelo":corpo.modelo_para_mente()["percepcao_fisica"]})
            time.sleep(.1)
    except Exception as exc:
        erro=type(exc).__name__+":"+str(exc)
    finally:
        rosto.encerrar()
        destino=RAIZ/"artifacts/rosto_oled/imu_manuseio"
        destino.mkdir(parents=True,exist_ok=True)
        saida={"erro":erro,"leituras":registros,"trilha":trilha,
               "historico":estado.obter_copia("mental","historico_corporal",[]),
               "encerrado":not rosto.diagnostico()["conectado"],"motores_enviados":0}
        (destino/"manuseio_usb.json").write_text(json.dumps(saida,ensure_ascii=False,indent=2),encoding="utf8")
        print(json.dumps({"erro":erro,"amostras":len(registros),
            "estados":sorted({r["imu"].get("manuseio","") for r in registros}),"encerrado":saida["encerrado"]},ensure_ascii=False))
    if erro:raise SystemExit(1)


if __name__=="__main__":main()

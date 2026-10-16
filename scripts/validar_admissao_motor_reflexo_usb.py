"""Disputa real entre proteção local e comando único, com rodas suspensas.

Não desativa sensores nem libera risco; espera a recusa correlacionada do ESP.
"""
from pathlib import Path
import json
import os
import sys
import time

RAIZ=Path(__file__).resolve().parents[1]
DESTINO=RAIZ/"artifacts/rosto_oled/admissao_motor_reflexo"
sys.path.insert(0,str(RAIZ))
os.environ["LAYLAY_ROSTO_PORTA"]="COM4"
os.environ["LAYLAY_CORPO_WIFI_CONFIG"]=str(DESTINO/"sem_wifi.json")
from mente_laylay.integracao import instancia_unica
adquirir=instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica=lambda _:adquirir(DESTINO/"instancia")
import laylay

r=laylay._rosto_oled_runtime
c=laylay._corpo_motor_runtime.companhia
inicio=time.monotonic();trilha=[];falha="";retorno={};antes={};depois={}
def registrar(tipo,dados):
    trilha.append({"t":round(time.monotonic()-inicio,3),"tipo":tipo,"dados":dados})
abrir=r.abrir_serial
class PortaObservada:
    def __init__(self,porta):self.porta=porta
    def __getattr__(self,nome):return getattr(self.porta,nome)
    def read(self,n):
        dados=self.porta.read(n)
        if dados:registrar("rx",dados.decode("ascii",errors="replace"))
        return dados
    def write(self,dados):
        registrar("tx",dados.decode("ascii",errors="replace").strip())
        return self.porta.write(dados)
r.abrir_serial=lambda porta:PortaObservada(abrir(porta))
try:
    if not c.diagnostico()["ativacao_automatica_ao_iniciar"]:
        raise RuntimeError("preferencia_de_companhia_ausente")
    if not r.sincronizar():raise RuntimeError("usb_indisponivel")
    registrar("ativacao",c.processar())
    prazo=time.monotonic()+15
    while time.monotonic()<prazo:
        if not r.sincronizar():raise RuntimeError("perda_usb")
        d=r.diagnostico();s=d.get("sensores") or {};p=s.get("protecao") or {}
        b=(s.get("leituras") or {}).get("borda") or {}
        if (p.get("reflexo_ativo") and p.get("risco")=="OBSTACULO"
            and b.get("estado")=="VALIDA" and b["mm"]<=120):
            antes=d;break
        time.sleep(.15)
    if not antes:raise RuntimeError("reflexo_de_parede_nao_observado")
    # mover_corpo revalida pelo próprio sincronizar; registra a última leitura
    # obtida antes da escrita para provar se o MOTOR realmente disputa o reflexo.
    escrever=r._escrever
    def escrita(linha):
        if linha.startswith("MOTOR "):
            d=r.diagnostico();registrar("antes_motor",d)
            if not (d.get("sensores") or {}).get("protecao",{}).get("reflexo_ativo"):
                raise RuntimeError("reflexo_terminou_antes_do_comando")
        escrever(linha)
    r._escrever=escrita
    retorno=r.mover_corpo(100,100,250)
    registrar("receipt",retorno)
    depois=r.diagnostico()
finally:
    c.revogar("fim_ensaio_admissao")
    parada=r.parar_corpo()
    r.encerrar()
    nome=sys.argv[1] if len(sys.argv)>1 else "runtime_antes.json"
    if Path(nome).name!=nome or not nome.endswith(".json"):raise ValueError("destino_invalido")
    (DESTINO/nome).write_text(json.dumps({"trilha":trilha,"receipt":retorno,"antes":antes,"depois":depois,
        "parada":parada,"encerrado":True,"prova_deslocamento":False},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"receipt":retorno,"parada_confirmada":parada.get("parada_confirmada"),"encerrado":True},ensure_ascii=False),flush=True)

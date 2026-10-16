"""Ensaio finito dos owners reais: conserva receipts e encerra o corpo.

Requer rodas suspensas. Não cria preferência nem contorna proteção local.
"""
from pathlib import Path
import json
import os
import sys
import threading
import time

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "artifacts/rosto_oled/companhia_interrompida"
DESTINO.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(RAIZ))
os.environ["LAYLAY_ROSTO_PORTA"] = "COM4"
os.environ["LAYLAY_CORPO_WIFI_CONFIG"] = str(DESTINO / "sem_wifi.json")
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(DESTINO / "instancia")
import laylay
from memoria_sqlite import MemoriaSQLite

r = laylay._rosto_oled_runtime
c = laylay._corpo_motor_runtime.companhia
estado = laylay._estado_compartilhado_runtime
aprendizado = laylay._motor_aprendizado_runtime
aprendizado.memoria = aprendizado.maturidade.memoria = MemoriaSQLite(str(DESTINO / "aprendizado.sqlite"))
estado.atualizar_campos("mental", historico_corporal=[], experiencia_corporal={})
fim = threading.Event()
trilha = []
inicio = time.monotonic()
workers = []
falha = ""

def registrar(tipo, dados):
    trilha.append({"t": round(time.monotonic()-inicio, 3), "tipo": tipo, "dados": dados})

def envolver(objeto, nome):
    original = getattr(objeto, nome)
    def observar(*args, **kwargs):
        retorno = original(*args, **kwargs)
        registrar(nome, retorno)
        return retorno
    setattr(objeto, nome, observar)

escrever = r._escrever
def escrita(linha):
    if linha.startswith(("HELLO ", "MOTOR ", "EXPR ", "STOP ", "SENTRY ")):
        registrar("enviado", linha)
    escrever(linha)
r._escrever = escrita
for nome in ("mover_corpo", "expressar_gesto"):
    envolver(r, nome)
envolver(c.coordenador, "executar_gesto_corporal")
troca = "--troca" in sys.argv
if troca:
    expressar = r.expressar_gesto
    def trocar_causa(estilo, fase, *args, **kwargs):
        if fase == 1:
            estado.atualizar_campos("conversacional", is_speaking=False, audio_playing=False)
            registrar("estimulo_diagnostico", "fala terminou antes da expressão motora")
        return expressar(estilo, fase, *args, **kwargs)
    r.expressar_gesto = trocar_causa

try:
    if not c.diagnostico()["ativacao_automatica_ao_iniciar"]:
        raise RuntimeError("preferencia_automatica_ausente")
    worker = threading.Thread(target=r.executar, kwargs={"deve_parar": fim.is_set, "aguardar_fn": fim.wait}, daemon=True)
    workers.append(worker)
    worker.start()
    prazo = time.monotonic()+12
    while not r.diagnostico().get("aplicacao_confirmada") and time.monotonic()<prazo:
        fim.wait(.2)
    if not r.diagnostico().get("aplicacao_confirmada"):
        raise RuntimeError("usb_indisponivel")
    registrar("ativacao", c.processar())
    if troca:
        estado.atualizar_campos("conversacional", is_speaking=True, audio_playing=True)
        if not r.sincronizar():
            raise RuntimeError("rosto_do_estimulo_nao_confirmado")
    ultimo = None
    ate = time.monotonic()+(35 if troca else 24)
    while time.monotonic()<ate:
        retorno = c.processar()
        d = r.diagnostico()
        diag = c.diagnostico()
        assinatura = (diag["ativa"], diag["motivo"], retorno.get("motivo"), (d.get("sensores") or {}).get("protecao", {}).get("fase"))
        if assinatura != ultimo or retorno.get("ok"):
            registrar("ciclo", {"retorno": retorno, "companhia": diag, "transporte": d,
                "experiencia": estado.obter_copia("mental", "experiencia_corporal", {})})
            ultimo = assinatura
        if not diag["ativa"] and not diag.get("recuperacao_pendente"):
            break
        fim.wait(.2)
except Exception as erro:
    falha = type(erro).__name__+":"+str(erro)
finally:
    c.revogar("fim_diagnostico")
    parada = r.parar_corpo()
    fim.set()
    for worker in workers:
        worker.join(5)
    r.encerrar()
    vivos = any(w.is_alive() for w in workers)
    nome = sys.argv[1] if len(sys.argv)>1 else "runtime_antes.json"
    if Path(nome).name != nome or not nome.endswith(".json"):
        raise ValueError("destino_invalido")
    (DESTINO / nome).write_text(json.dumps({"falha": falha, "trilha": trilha, "parada": parada,
        "encerrado": not vivos, "prova_deslocamento": False}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"falha": falha, "encerrado": not vivos, "parada": parada.get("parada_confirmada"), "registros": len(trilha)}), flush=True)
if falha or vivos:
    raise SystemExit(1)

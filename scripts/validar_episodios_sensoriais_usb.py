"""Composição/USB/SQLite reais; sensores reais, sem inventar medidas ou MOTOR.

Rodas suspensas, inferior<=120mm e parede<=100mm são pré-condições do ensaio.
Usa a preferência de companhia já autorizada; nunca a cria/ativa por diagnóstico.
"""
from pathlib import Path
import json
import os
import sys
import threading
import time

RAIZ=Path(__file__).resolve().parents[1]
DESTINO=RAIZ/"artifacts/rosto_oled/experiencia_sensores"
DESTINO.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(RAIZ))
os.environ["LAYLAY_ROSTO_PORTA"]="COM4"
os.environ["LAYLAY_CORPO_WIFI_CONFIG"]=str(DESTINO/"sem_pareamento_wifi.json")
from mente_laylay.integracao import instancia_unica
adquirir=instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica=lambda _:adquirir(DESTINO/"instancia_diagnostico")
import laylay
from memoria_sqlite import MemoriaSQLite
from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal

r=laylay._rosto_oled_runtime; corpo=laylay._corpo_motor_runtime
estado=laylay._estado_compartilhado_runtime; motor=laylay._motor_aprendizado_runtime
memoria_anterior,maturidade_anterior=motor.memoria,motor.maturidade.memoria
motor.memoria=motor.maturidade.memoria=MemoriaSQLite(str(DESTINO/"aprendizado_diagnostico.sqlite"))
estado.atualizar_campos("mental",historico_corporal=[],experiencia_corporal={})
apenas_mente="--mente" in sys.argv
if apenas_mente:
    corpo.companhia.revogar("consulta_sem_iniciativa_corporal")
    corpo.experiencias.conectar_aprendizado(motor)
    historico=[e for e in estado.obter_copia("mental","historico_corporal",[]) if e.get("tipo")=="episodio_sensorial"]
    estado.atualizar_campos("mental",historico_corporal=historico,experiencia_corporal=historico[-1] if historico else {})
fim=threading.Event(); workers=[]; trilha=[]; registros=[]; falha=""; consulta={}; evidencias=[]
inicio=time.monotonic(); escrever=r._escrever
def observar_escrita(linha):
    if linha.startswith(("HELLO ","SENTRY ","STOP","MOTOR ")):
        trilha.append({"t":round(time.monotonic()-inicio,3),"comando":linha,"enviado":not linha.startswith("MOTOR ")})
    if linha.startswith("MOTOR "):
        raise AssertionError("ensaio não permite coreografias do PC; só reflexos locais")
    escrever(linha)
r._escrever=observar_escrita
def iniciar(servico):
    worker=threading.Thread(target=servico.executar,
        kwargs={"deve_parar":fim.is_set,"aguardar_fn":fim.wait},daemon=True)
    workers.append(worker);worker.start()
try:
    iniciar(r)
    pronto=False
    prazo=time.monotonic()+12
    while time.monotonic()<prazo:
        d=r.diagnostico();s=d.get("sensores") or {};l=s.get("leituras") or {}
        b=l.get("borda") or {};f=l.get("frente") or {}
        if (d.get("aplicacao_confirmada") and (apenas_mente or (s.get("recente")
            and b.get("estado")==f.get("estado")=="VALIDA" and b["mm"]<=120 and f["mm"]<=100))):
            pronto=True;break
        fim.wait(.2)
    if not pronto:
        raise RuntimeError("montagem_sem_superficie_e_parede_confirmadas")
    if "--consulta" not in sys.argv and not apenas_mente:
        if not corpo.companhia.diagnostico()["ativacao_automatica_ao_iniciar"]:
            raise RuntimeError("preferencia_de_companhia_nao_autorizada")
        iniciar(corpo.companhia)
    ultimo=None;ate=time.monotonic()+(3 if apenas_mente else 5 if "--consulta" in sys.argv else 38)
    while time.monotonic()<ate:
        d=r.diagnostico();s=d.get("sensores") or {};p=s.get("protecao") or {}
        exp=corpo.experiencias.retrato();c=corpo.companhia.diagnostico()
        chave=(d["sessao"],p.get("incidente_id"),p.get("fase"),p.get("risco"),(c.get("intencao") or {}).get("motivo"),
            tuple((e["id"],e["resultado"]) for e in exp["historico_recente"]))
        if chave!=ultimo:
            registros.append({"t":round(time.monotonic()-inicio,3),"sessao":d["sessao"],"protecao":p,
                "leituras":s.get("leituras"),"companhia":c,"experiencia":exp,
                "modelo":corpo.modelo_para_mente()})
            ultimo=chave
        fim.wait(.2)
    if "--consulta" not in sys.argv:
        h=estado.obter_copia("mental","historico_corporal",[])
        episodios=[e for e in h if e.get("tipo")=="episodio_sensorial"]
        assert episodios,"nenhum GUARD materializado na experiência"
        for hip in motor.memoria.listar_hipoteses_aprendizado(limit=500):
            if hip["tipo"]=="episodio_sensorial_corporal":
                evidencias.extend(e for e in motor.memoria.listar_eventos_aprendizado(hip["chave"],limit=12)
                    if (e.get("contexto") or {}).get("experiencia",{}).get("sessao") in {x["sessao"] for x in episodios})
        assert evidencias,"observação não chegou ao aprendizado real"
        # Consulta real desarmada: nenhum retorno da IA será executado.
        corpo.companhia.revogar("consulta_mente_sem_motores")
        assert r.parar_corpo()["parada_confirmada"]
        modelo=corpo.modelo_para_mente();instrucao=formatar_modelo_corporal(modelo)
        assert len(instrucao)<=3800
        resposta=laylay._registro_modelo_llm_runtime.enviar([
            {"role":"system","content":instrucao},
            {"role":"user","content":"O que seus sensores detectaram neste teste e o que ficou sem confirmação? Responda em até duas frases dentro de fala, no JSON indicado; não transcreva o retrato nem inclua comandos."}],
            max_tokens=650,timeout=35,modo_rapido=True,_permitir_durante_interacao=True,
            _contexto_fechado=True,_com_tools=False)
        consulta={"resposta":resposta,"modelo_corporal":modelo,"instrucao_chars":len(instrucao),
            "json_valido":False,"executou_proposta":False}
        consulta["json_valido"]=isinstance(json.loads(resposta),dict)
except Exception as erro:
    falha=type(erro).__name__+": "+str(erro)
finally:
    corpo.companhia.revogar("fim_ensaio_sensorial")
    fim.set()
    for worker in workers:worker.join(5)
    r.encerrar()
    vivos=any(worker.is_alive() for worker in workers)
    motor.memoria,motor.maturidade.memoria=memoria_anterior,maturidade_anterior
    nome="consulta_mente.json" if apenas_mente else "consulta_usb.json" if "--consulta" in sys.argv else "runtime_usb.json"
    (DESTINO/nome).write_text(json.dumps({"falha":falha,"registros":registros,"trilha":trilha,
        "evidencias":evidencias,"consulta_modelo":consulta,"encerrada":not vivos,
        "aprendizado_isolado":True,"prova_deslocamento":False},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"falha":falha,"transicoes":len(registros),"evidencias":len(evidencias),"encerrada":not vivos},ensure_ascii=False),flush=True)
if falha or vivos:
    raise SystemExit(1)

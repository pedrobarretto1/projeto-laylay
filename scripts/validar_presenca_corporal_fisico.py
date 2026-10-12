"""Demonstração autorizada em rodas suspensas, com transporte/owners reais.

Emoções e o claim de entrada são estímulos de diagnóstico explicitamente
rotulados. Não produzem receipts de ações fictícias no PC.
"""
from pathlib import Path
import json
import sys
import threading
import time
from types import SimpleNamespace
RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ))
import serial
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from mente_laylay.integracao.prioridade_interacao_usuario import PrioridadeInteracaoUsuarioRuntime
from mente_laylay.integracao.composicao_rosto_oled import criar_composicao_rosto_oled_runtime
from mente_laylay.especialistas.corpo_motor_runtime import criar_corpo_motor_runtime
from mente_laylay.autonomia.orquestracao_cooperativa import OrquestradorCooperativoRuntime
from mente_laylay.autonomia.quadro_cooperacao import QuadroCooperacaoRuntime
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional

trilha=[]
class CapturaSerial:
    def __init__(self, porta):
        self.serial=serial.Serial(porta,115200,timeout=.1,write_timeout=.5)
        self.pendente=bytearray()
    def write(self, dados):
        trilha.append({"direcao":"tx","tempo":time.monotonic(),"pacote":dados.decode().strip()})
        return self.serial.write(dados)
    def read(self, tamanho):
        dados=self.serial.read(tamanho); self.pendente.extend(dados)
        while b"\n" in self.pendente:
            linha,_,resto=self.pendente.partition(b"\n");self.pendente=bytearray(resto)
            texto=linha.decode(errors="replace").strip()
            if texto.startswith(("ACK ","EACK ","MACK ","SACK ","NACK ","SOUNDACK ","ERROR ")):
                trilha.append({"direcao":"rx","tempo":time.monotonic(),"pacote":texto})
        return dados
    def close(self):self.serial.close()

estado=criar_estado_compartilhado_runtime()
prioridade=PrioridadeInteracaoUsuarioRuntime()
erros=[]
rosto=criar_composicao_rosto_oled_runtime(estado=estado,porta="COM4",abrir_serial=CapturaSerial,
    interacao_getter=prioridade.ativa,companhia_getter=lambda:corpo.companhia.diagnostico(),
    observabilidade=SimpleNamespace(relatar_falha=lambda *a,**k:erros.append(str(a[1:]))))
corpo=criar_corpo_motor_runtime(transporte=rosto,estado=estado,perfil_corporal="rodas_suspensas",
    companhia_bancada_ao_iniciar=True,prioridade_interacao_getter=prioridade.ativa)
quadro=QuadroCooperacaoRuntime(modo="ativo",log=lambda _:None)
coord=OrquestradorCooperativoRuntime(quadro=quadro,clipboard_snapshot=lambda:{},clipboard_getter=lambda:"",
    executar_intencao=lambda *_:False,resolver_caminho=lambda x:x,falar=lambda *_:None,log=lambda _:None)
corpo.companhia.coordenador=coord
coord.governanca.registrar_autorizador_escopo("corpo_companhia",corpo.companhia.autorizar_escopo)
fim=threading.Event()
supervisor=threading.Thread(target=lambda:rosto.executar(deve_parar=fim.is_set,aguardar_fn=fim.wait),daemon=True)
passos=[]
falha=""
def emocao(nome):
    evento=criar_evento_emocional_causal(origem="controle_rosto",causa="demonstração autorizada de presença",
        evidencia_ref="diagnostico:presenca_v2",natureza_evidencia="fato_observado",responsabilidade="usuario",
        confianca=.99,relevancia=.95,intensidade=2,permite_expressao=True,emocao=nome,nivel=2,
        ts=time.time(),validade_s=120)
    estado.substituir("conversacional",aplicar_evento_emocional({},evento,agora=time.time()))
    assert rosto.sincronizar()

try:
    supervisor.start()
    prazo=time.monotonic()+8
    while time.monotonic()<prazo and not rosto.diagnostico()["aplicacao_confirmada"]:time.sleep(.05)
    d=rosto.diagnostico()
    assert d["expressao"]["suportado"] and d["motor"]["rampa_suportada"],d
    print("OLED acordando gradualmente",flush=True)
    time.sleep(2.2)
    assert corpo.companhia.processar()["ok"]
    passos.append({"fase":"acordar","diagnostico":d})
    emocao("alegre")
    resultado=[]
    executor=threading.Thread(target=lambda:resultado.append(corpo.companhia.processar()),daemon=True)
    executor.start()
    prazo=time.monotonic()+4
    while time.monotonic()<prazo and not rosto.diagnostico()["motor"]["em_andamento"]:time.sleep(.02)
    assert rosto.diagnostico()["motor"]["em_andamento"]
    time.sleep(.35)
    inicio=time.monotonic(); claim=prioridade.adquirir("entrada_canonica")
    executor.join(1.5)
    latencia=time.monotonic()-inicio
    assert not executor.is_alive() and resultado and not resultado[0]["ok"]
    assert not rosto.diagnostico()["motor"]["em_andamento"]
    assert not corpo.companhia.processar()["ok"]
    prazo=time.monotonic()+1.5
    while time.monotonic()<prazo and rosto.diagnostico()["expressao"]["fase"]!=[9,3,0]:time.sleep(.02)
    assert rosto.diagnostico()["expressao"]["fase"]==[9,3,0]
    passos.append({"fase":"entrada_prioritaria_simulada","parada_s":latencia,"retorno":resultado[0]})
    print("Entrada simulada: corpo parou e olhos atentos",flush=True)
    time.sleep(1.5); prioridade.liberar(claim)
    for nome in ("envergonhada","surpresa","alegre"):
        time.sleep(2.1)
        emocao(nome)
        print("Expressão coordenada: "+nome,flush=True)
        retorno=corpo.companhia.processar()
        assert retorno["ok"],retorno
        passos.append({"fase":nome,"retorno":retorno,"intencao":estado.mental["intencao_corporal"]})
    corpo.executar("CORPO_PARAR",{})
    fim.set();supervisor.join(4)
    assert not supervisor.is_alive()
    assert any(p["pacote"].startswith("NACK ") for p in trilha)
    print("OLED adormecendo gradualmente",flush=True)
    time.sleep(2.2)
    passos.append({"fase":"adormecer","boa_noite_confirmada":True})
except Exception as e:
    falha=type(e).__name__+": "+(str(e) or "asserção não satisfeita")
finally:
    corpo.companhia.revogar("fim_demonstracao")
    fim.set();supervisor.join(4)
    rosto.encerrar()
destino=RAIZ/"artifacts/rosto_oled/presenca_v2/receipt_fisico.json"
destino.write_text(json.dumps({"passos":passos,"falha":falha,"erros":erros,"trilha":trilha,
    "estimulos":"emoções e entrada simuladas; nenhum efeito no PC", "observacao_humana":"pendente"},
    ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"receipt":str(destino),"passos":len(passos),"falha":falha},ensure_ascii=False),flush=True)
if falha:raise SystemExit(1)

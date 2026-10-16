"""Partituras na composição instalada e USB real, sem abrir a interface.

Emoções e escolha da terceira variação são estímulos de diagnóstico, sem
inventar ações no PC. Usa concessão, coordenação e receipts de produção.
"""
from pathlib import Path
import json
import sys
import threading
import time

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
DESTINO = RAIZ / "artifacts/rosto_oled/expressoes_v3"
DESTINO.mkdir(parents=True, exist_ok=True)
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(DESTINO / "instancia_sonda")
import laylay
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional

estado, rosto, corpo = laylay._estado_compartilhado_runtime, laylay._rosto_oled_runtime, laylay._corpo_motor_runtime
abrir = rosto.abrir_serial
trilha, passos = [], []

class CapturaSerial:
    def __init__(self, porta):
        self.serial = abrir(porta)
        self.pendente = bytearray()
    def write(self, dados):
        trilha.append({"direcao": "tx", "pacote": dados.decode().strip(), "tempo": time.monotonic()})
        return self.serial.write(dados)
    def read(self, tamanho):
        dados = self.serial.read(tamanho)
        self.pendente.extend(dados)
        while b"\n" in self.pendente:
            linha, _, resto = self.pendente.partition(b"\n")
            self.pendente = bytearray(resto)
            texto = linha.decode(errors="replace").strip()
            if texto.startswith(("ACK ", "EACK ", "MACK ", "SACK ", "NACK ", "SOUNDACK ", "ERROR ")):
                trilha.append({"direcao": "rx", "pacote": texto, "tempo": time.monotonic()})
        return dados
    def close(self):
        self.serial.close()

fim = threading.Event()
supervisor = threading.Thread(target=lambda: rosto.executar(deve_parar=fim.is_set, aguardar_fn=fim.wait), daemon=True)
rosto.abrir_serial = CapturaSerial
falha = ""
try:
    supervisor.start()
    prazo = time.monotonic() + 8
    while time.monotonic() < prazo and not rosto.diagnostico()["aplicacao_confirmada"]:
        time.sleep(.05)
    assert rosto.diagnostico()["expressao"]["suportado"], rosto.diagnostico()
    assert corpo.companhia.perfil_corporal == "rodas_suspensas"
    time.sleep(3.3)
    assert corpo.companhia.processar()["ok"], corpo.companhia.diagnostico()
    for nome, codigo in (("alegre", 1), ("envergonhada", 6), ("surpresa", 5), ("brava", 3)):
        time.sleep(2.1)
        evento = criar_evento_emocional_causal(origem="controle_rosto", causa="demonstração autorizada de expressão",
            evidencia_ref="diagnostico:expressoes_v3", natureza_evidencia="fato_observado", responsabilidade="usuario",
            confianca=.99, relevancia=.95, intensidade=2, permite_expressao=True,
            emocao=nome, nivel=2, ts=time.time(), validade_s=90)
        estado.atualizar("conversacional", lambda atual: aplicar_evento_emocional(atual, evento, agora=time.time()))
        assert rosto.sincronizar()
        # Seleção diagnóstica de variação, sem mudar causa, concessão ou PWM.
        corpo.companhia._variantes[f"expressar:{codigo}"] = 2
        print("Expressão coordenada: " + nome, flush=True)
        resultado = corpo.companhia.processar()
        assert resultado.get("ok"), resultado
        passos.append({"emocao": nome, "retorno": resultado, "diagnostico": rosto.diagnostico()})
    assert any(p["pacote"].startswith("SOUNDACK ") for p in trilha)
    assert all(p["retorno"].get("ok") is True for p in passos)
except Exception as erro:
    falha = type(erro).__name__ + ": " + str(erro)
finally:
    corpo.companhia.revogar("fim_demonstracao_expressoes")
    fim.set()
    supervisor.join(5)
    rosto.encerrar()
    rosto.abrir_serial = abrir
    dados = {"falha": falha, "passos": passos, "trilha": trilha,
        "estimulos": "emoções diagnósticas e seleção da terceira variação; composição instalada",
        "observacao_humana": "pendente", "interface_aberta": False, "prova_deslocamento": False,
        "parada_recebida": any(p["pacote"].startswith("SACK ") for p in trilha)}
    caminho = DESTINO / "receipt_fisico.json"
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"receipt": str(caminho), "falha": falha, "gestos": len(passos)}, ensure_ascii=False), flush=True)
if falha:
    raise SystemExit(1)

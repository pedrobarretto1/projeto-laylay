"""Teste manual em rodas suspensas no composition root real, sem iniciar companhia."""
from __future__ import annotations
import json
import os
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
SAIDA = RAIZ / "artifacts/rosto_oled/protecao_sensores"
os.environ["LAYLAY_ROSTO_PORTA"] = "COM4"
os.environ["LAYLAY_CORPO_WIFI_CONFIG"] = str(SAIDA / "sem_wifi.json")
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(SAIDA / "instancia_diagnostico")
import laylay


def main() -> None:
    rosto = laylay._rosto_oled_runtime
    corpo = laylay._corpo_motor_runtime
    assert corpo.transporte is rosto
    assert corpo.companhia.coordenador is laylay._orquestrador_cooperativo_runtime
    parar = threading.Event()
    registros, receipts = [], []
    ultima = {}
    erro = [""]
    ocupada = threading.Event()
    janela = tk.Tk()
    janela.title("Laylay — proteção: teste com rodas suspensas")
    janela.geometry("790x420")
    texto = tk.StringVar(value="Conectando à COM4…")
    resultado = tk.StringVar(value="Nenhum comando de motor enviado.")
    ttk.Label(janela, text="Borda >13 cm ou inválida · Obstáculo válido ≤10 cm", font=("Segoe UI", 13)).pack(pady=12)
    ttk.Label(janela, textvariable=texto, font=("Segoe UI", 12), justify="left").pack(pady=8)
    ttk.Label(janela, wraplength=740, justify="left", text=(
        "Mantenha as rodas suspensas. Primeiro confirme a borda medindo perto de 100 mm. "
        "Clique em Testar quando estiver olhando. Durante o avanço de até 3 segundos, aproxime um objeto "
        "a menos de 10 cm do frontal OU retire a superfície abaixo do sensor da borda. "
        "Recoloque a superfície e afaste o objeto antes do fim do giro. "
        "Observe medo, bip, recuo, giro e nova leitura. O ângulo ainda é uma estimativa."
    )).pack(pady=12)
    ttk.Label(janela, textvariable=resultado, wraplength=740).pack(pady=6)

    def consultar():
        nonlocal ultima
        try:
            while not parar.is_set():
                assert rosto.sincronizar(), rosto.diagnostico()["motivo"]
                diag = rosto.diagnostico()
                modelo = corpo.modelo_para_mente()
                dev = laylay._dev_console_runtime.atualizar_corpo()
                ultima = diag
                registros.append({"ts": time.time(), "sensores": diag["sensores"],
                    "condicao": modelo["condicao"], "dev": dev})
                del registros[:-500]
                parar.wait(.08)
        except Exception as e:
            erro[0] = type(e).__name__ + ": " + str(e)
            ultima = {}

    def testar():
        if ocupada.is_set():
            return
        ocupada.set(); resultado.set("Teste em andamento…")
        def executar():
            try:
                r = rosto.mover_corpo(140,140,3000)
                receipts.append(r)
            except Exception as e:
                receipts.append({"ok":False,"motivo":type(e).__name__ + ": " + str(e)})
            finally:
                ocupada.clear()
        threading.Thread(target=executar, daemon=True).start()

    botao = ttk.Button(janela,text="Testar avanço e reação aos sensores",command=testar)
    botao.pack(pady=5)
    def atualizar():
        s = ultima.get("sensores") or {}
        leituras = s.get("leituras") or {}
        p = s.get("protecao") or {}
        def sensor(nome):
            r = leituras.get(nome) or {}
            return f"{r.get('mm')} mm" if r.get("estado") == "VALIDA" else r.get("estado", "aguardando")
        texto.set(f"Frontal: {sensor('frente')}\nBorda: {sensor('borda')}\nRisco: {p.get('risco','aguardando')} · Fase: {p.get('fase','aguardando')}\n" + erro[0])
        b = leituras.get("borda") or {}
        pronta = s.get("recente") and b.get("estado") == "VALIDA" and 0 < b.get("mm",9999) <= 130 and not ocupada.is_set()
        botao.configure(state="normal" if pronta else "disabled")
        if receipts and not ocupada.is_set():
            r = receipts[-1]
            resultado.set(("Movimento original interrompido pela proteção." if r.get("interrompido_por_protecao") else
                "Comando concluído com PWM e parada confirmados." if r.get("ok") else "Teste sem confirmação: " + str(r.get("motivo")))
                + " Parada elétrica: " + str(r.get("parada_confirmada")))
        if not parar.is_set(): janela.after(100,atualizar)

    def fechar():
        parar.set()
        rosto.parar_corpo()
        worker.join(timeout=2)
        rosto.encerrar()
        SAIDA.mkdir(parents=True,exist_ok=True)
        resposta = laylay._mapa_habilidades_runtime.responder_pergunta_capacidade("voce consegue detectar bordas?")
        (SAIDA / "painel_protecao.json").write_text(json.dumps({"leituras":registros,"receipts":receipts,
            "composicao_real":True,"companhia_iniciada":False,"encerrada":True,
            "resposta_apos_desconexao":resposta},ensure_ascii=False,indent=2),encoding="utf-8")
        janela.destroy()
    ttk.Button(janela,text="PARAR E FECHAR",command=fechar).pack(pady=10)
    janela.protocol("WM_DELETE_WINDOW",fechar)
    worker = threading.Thread(target=consultar,daemon=True); worker.start()
    atualizar(); janela.mainloop()


if __name__ == "__main__": main()

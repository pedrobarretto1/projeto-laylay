"""Painel local somente leitura; não envia HELLO, FACE, MOTOR nem concede sessão."""
from __future__ import annotations
import json
import queue
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import serial
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mente_laylay.especialistas.percepcao_distancia import interpretar_linha_distancia

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "artifacts/rosto_oled/sensores/painel.json"


def main() -> None:
    raiz = tk.Tk()
    raiz.title("Laylay — sensores: somente leitura USB")
    raiz.geometry("620x290")
    ultimo = tk.StringVar(value="Conectando à COM4…")
    ttk.Label(raiz, text="Frontal: XSHUT GPIO0 · Borda: XSHUT GPIO10", font=("Segoe UI", 12)).pack(pady=12)
    ttk.Label(raiz, textvariable=ultimo, font=("Segoe UI", 14), justify="left").pack(pady=12)
    ttk.Label(raiz, text="Aproxime e afaste um objeto na frente.\nPara a borda, mantenha o corpo seguro e varie a superfície abaixo do sensor.\nAinda não há proteção de movimento calibrada.", justify="left").pack(pady=8)
    fila: queue.Queue = queue.Queue()
    parar = threading.Event()
    leituras = []

    def consultar():
        try:
            with serial.Serial("COM4", 115200, timeout=.1, write_timeout=.5) as porta:
                porta.write(b"STOP\n")
                porta.reset_input_buffer()
                seq = 0
                while not parar.is_set():
                    seq += 1
                    porta.write(f"DIST 1 {seq}\n".encode())
                    prazo = time.monotonic() + 1
                    resposta = None
                    while time.monotonic() < prazo and not parar.is_set():
                        linha = porta.readline().decode("ascii", errors="replace").strip()
                        if linha.startswith(f"DIST 1 {seq} "):
                            resposta = interpretar_linha_distancia(linha, seq)
                            break
                    fila.put(resposta or {"erro": "sem_resposta_recente"})
                    parar.wait(.15)
        except Exception as erro:
            fila.put({"erro": type(erro).__name__ + ": " + str(erro)})

    def atualizar():
        while not fila.empty():
            r = fila.get_nowait()
            if "erro" in r:
                ultimo.set("Estado indisponível\n" + r["erro"])
            else:
                leituras.append({"ts": time.time(), **r})
                del leituras[:-400]
                texto = []
                for nome, label in (("frente", "Obstáculos"), ("borda", "Borda")):
                    s = r[nome]
                    texto.append(f"{label}: {s['mm']} mm · {s['idade_ms']} ms" if s["mm"] is not None
                                 else f"{label}: {s['estado']} · sem distância válida")
                ultimo.set("\n".join(texto))
        if not parar.is_set():
            raiz.after(100, atualizar)

    def fechar():
        parar.set()
        trabalhador.join(timeout=1.5)
        SAIDA.parent.mkdir(parents=True, exist_ok=True)
        SAIDA.write_text(json.dumps({"diagnostico_somente_leitura": True,
            "protecao_calibrada": False, "leituras": leituras}, ensure_ascii=False, indent=2), encoding="utf-8")
        raiz.destroy()

    ttk.Button(raiz, text="Fechar e salvar leituras", command=fechar).pack(pady=10)
    raiz.protocol("WM_DELETE_WINDOW", fechar)
    trabalhador = threading.Thread(target=consultar, daemon=True)
    trabalhador.start()
    atualizar()
    raiz.mainloop()


if __name__ == "__main__":
    main()

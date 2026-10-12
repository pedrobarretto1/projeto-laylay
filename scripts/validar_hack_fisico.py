"""Probe visual instalado, serial real e escopo controlado sem ações de motores.

Não executa comandos de habilidades. O escopo do owner serve somente para
testar transporte/overlay; sucesso de uma habilidade e pixels exigem outra prova.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Deixar DEMO_HACK local para inspeção")
    args = parser.parse_args()
    import laylay as root
    runtime = root._rosto_oled_runtime
    owner = root._atividade_operacional_runtime
    abrir = runtime.abrir_serial
    enviados: list[str] = []
    recebidos: list[str] = []
    amostras: list[dict] = []

    class PortaObservada:
        def __init__(self, porta: str):
            self.serial = abrir(porta)
            self.buffer = bytearray()
        def write(self, dados: bytes) -> int:
            enviados.append(dados.decode("ascii").strip())
            return self.serial.write(dados)
        def read(self, quantidade: int) -> bytes:
            dados = self.serial.read(quantidade)
            self.buffer.extend(dados)
            while b"\n" in self.buffer:
                linha, _, resto = self.buffer.partition(b"\n")
                self.buffer = bytearray(resto)
                recebidos.append(linha.decode("ascii", errors="replace").strip())
            return dados
        def close(self) -> None:
            self.serial.close()

    runtime.abrir_serial = PortaObservada
    pasta = Path(__file__).resolve().parents[1]
    fonte = pasta / "firmware/rosto_laylay/rosto_laylay.ino"
    fontes = {str(p.relative_to(pasta)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (fonte, fonte.with_name("fonte_terminal.h"))}
    prova: dict = {"ts_utc": datetime.now(timezone.utc).isoformat(), "fontes_sha256": fontes,
                   "composicao_instalada": True, "hardware_simulado": False,
                   "escopo_controlado": True, "acao_de_habilidade_executada": False,
                   "prova_optica": False, "comandos_motor_enviados": False,
                   "enviados": enviados, "recebidos": recebidos, "amostras": amostras}

    def amostrar(fase: str, segundos: float, esperado: bool) -> None:
        prazo = time.monotonic() + segundos
        while time.monotonic() < prazo:
            assert runtime.sincronizar(), runtime.diagnostico()
            retrato = runtime.diagnostico()
            assert retrato["hack"]["aplicacao_confirmada"], retrato
            assert retrato["hack"]["ativo"] is esperado, retrato
            amostras.append({"fase": fase, "diagnostico": retrato})
            print(f"{fase}: FACE + AACK ativo={esperado}", flush=True)
            time.sleep(0.25)

    try:
        amostrar("repouso", 1.0, False)
        owner.executar(amostrar, "tratamento_controlado", 4.0, True)
        amostrar("retorno_ao_rosto", 1.2, False)
        prova["porta"] = runtime.diagnostico()["porta_ativa"]
        prova["confirmado"] = True
    finally:
        runtime.encerrar()
        assert not any(p.startswith("MOTOR") for p in enviados)
        destino = pasta / "artifacts/rosto_oled/hack/receipt_fisico.json"
        destino.write_text(json.dumps(prova, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.demo:
        dispositivo = abrir(prova["porta"])
        try:
            dispositivo.write(b"DEMO_HACK\n")
            prazo = time.monotonic() + 2.0
            buffer = bytearray()
            while time.monotonic() < prazo and b"DEMO_HACK 1 ATIVA\n" not in buffer.replace(b"\r\n", b"\n"):
                buffer.extend(dispositivo.read(128))
            assert b"DEMO_HACK 1 ATIVA\n" in buffer.replace(b"\r\n", b"\n"), buffer
            prova["demo_hack_local"] = True
            prova["demo_receipt"] = "DEMO_HACK 1 ATIVA"
            destino.write_text(json.dumps(prova, ensure_ascii=False, indent=2), encoding="utf-8")
        finally:
            dispositivo.close()
        print("DEMO_HACK local ativo. Abrir Laylay cancela a demonstração.", flush=True)


if __name__ == "__main__":
    main()

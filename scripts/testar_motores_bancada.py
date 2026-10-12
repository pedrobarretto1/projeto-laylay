"""Pulsos fixos autorizados de bancada usando o único owner serial instalado.

ACK de GPIO/PWM não mede rotação, corrente ou parada física. Esta ferramenta
não instala comandos naturais nem autonomia. Usar motores soltos/rodas suspensas.
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
    parser.add_argument("--pwm", type=int, default=180, help="Intensidade 1–255")
    args = parser.parse_args()
    if not 1 <= args.pwm <= 255:
        parser.error("PWM precisa estar entre 1 e 255")
    import laylay as root
    runtime = root._rosto_oled_runtime
    owner = root._atividade_operacional_runtime
    pasta = Path(__file__).resolve().parents[1]
    instante = datetime.now(timezone.utc)
    destino = pasta / "artifacts/rosto_oled/motores" / f"receipt_bancada_{instante:%Y%m%d_%H%M%S}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    prova: dict = {
        "ts_utc": instante.isoformat(),
        "pinout": {"AIN1": 1, "AIN2": 2, "BIN1": 3, "BIN2": 4, "SLEEP": 7},
        "fonte_sha256": hashlib.sha256((pasta / "firmware/rosto_laylay/rosto_laylay.ino").read_bytes()).hexdigest(),
        "hardware_simulado": False, "composicao_serial_instalada": True,
        "perfil_build": "LAYLAY_HABILITAR_MOTORES_BANCADA=1",
        "autorizacao": "Pedro: liberar motores de teste distintos dos N20; mapa confirmado e montagem na protoboard sem rodas",
        "prova_rotacao": False, "prova_parada_fisica": False,
        "comandos_naturais_instalados": False, "pulsos": [],
        "pwm": args.pwm, "duracao_ms": 250,
    }
    sequencia = 0

    def parar() -> bool:
        try:
            with runtime._lock:
                if runtime._serial is None:
                    return False
                runtime._escrever("STOP")
                return runtime._esperar("STOPPED 1", 0.5, opcional=True)
        except Exception as erro:
            prova["erro_parada"] = str(erro)
            return False

    def pulso(nome: str, esquerdo: int, direito: int) -> None:
        nonlocal sequencia
        # Renova só FACE antes de cada pulso, nunca renova uma tração em andamento.
        assert runtime.sincronizar(), runtime.diagnostico()
        prova["porta"] = runtime.diagnostico()["porta_ativa"]
        with runtime._lock:
            sequencia += 1
            campos = f"{runtime._sessao} {sequencia} {esquerdo} {direito} 250"
            enviado = f"MOTOR 1 {campos}"
            esperado = f"MACK 1 {campos}"
            registro = {"nome": nome, "enviado": enviado, "receipt_pwm": False}
            prova["pulsos"].append(registro)
            runtime._escrever(enviado)
            assert runtime._esperar(esperado, 0.5, opcional=True), f"Sem MACK: {nome}"
            registro["receipt_pwm"] = esperado
        # O prazo é do firmware. STOP é corte adicional, sem inferir medição física.
        time.sleep(0.35)
        assert parar(), "STOP não foi confirmado"
        registro["stop_confirmado"] = True
        print(nome + ": MACK + STOPPED", flush=True)
        time.sleep(1.0)

    try:
        for nome, e, d in (
            ("esquerdo sentido A", args.pwm, 0), ("direito sentido A", 0, args.pwm),
            ("esquerdo sentido B", -args.pwm, 0), ("direito sentido B", 0, -args.pwm),
        ):
            owner.executar(pulso, nome, e, d)
        prova["configuracao_pwm_confirmada"] = True
    except Exception as erro:
        prova["erro"] = type(erro).__name__ + ":" + str(erro)
        raise
    finally:
        prova["parada_final_confirmada"] = parar()
        runtime.encerrar()
        destino.write_text(json.dumps(prova, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

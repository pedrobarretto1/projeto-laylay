"""Um único teste de bancada autorizado: frente/PWM100/5000ms, sem replay.

Exige perfil temporário LAYLAY_LIMITE_MOTOR_TESTE_MS=5000 na placa.
Não ativa autonomia nem muda os limites dos comandos naturais.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Event, Thread
import time

from mente_laylay.especialistas.corpo_wifi_transporte import (
    abrir_corpo_tcp, carregar_configuracao_corpo_wifi,
)
from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime


def main() -> None:
    raiz = Path(__file__).resolve().parents[1]
    config = carregar_configuracao_corpo_wifi(raiz / "memoria/corpo_wifi.json")
    if config is None:
        raise SystemExit("Pareamento ausente; nenhum motor acionado.")
    instante = datetime.now(timezone.utc)
    destino = raiz / "artifacts/rosto_oled/motores" / f"receipt_continuo_{instante:%Y%m%d_%H%M%S}.json"
    prova = {
        "ts_utc": instante.isoformat(), "endpoint": config.endpoint,
        "autorizacao": "Pedro: teste continuo para frente por 5 segundos; area delimitada ou rodas suspensas confirmadas",
        "pwm_esquerdo": 100, "pwm_direito": 100, "duracao_ms": 5000,
        "comandos_motor_enviados": 0, "hardware_simulado": False,
        "prova_rotacao": False, "prova_parada_fisica": False,
        "aplicacao_pwm_confirmada": False,
        "falhas_transporte": [],
    }
    inicio_probe = time.monotonic()
    inicio = None

    def relatar_falha(*args, **dados) -> None:
        erro = dados.get("erro")
        prova["falhas_transporte"].append({
            "tempo_probe_s": round(time.monotonic() - inicio_probe, 3),
            "tipo": type(erro).__name__, "motivo": str(erro)[:200],
        })

    runtime = RostoOledRuntime(estado_getter=lambda: {}, porta="tcp://" + config.endpoint,
                              abrir_serial=lambda _: abrir_corpo_tcp(config),
                              relatar_falha=relatar_falha)
    encerrar = Event()
    servico = Thread(target=lambda: runtime.executar(deve_parar=encerrar.is_set,
                                                     aguardar_fn=encerrar.wait), daemon=True)
    servico.start()
    try:
        prazo = time.monotonic() + 15
        while not runtime.diagnostico()["aplicacao_confirmada"]:
            if time.monotonic() >= prazo:
                raise ConnectionError("ESP nao confirmou o rosto; motor nao enviado.")
            time.sleep(.05)
        if not runtime.diagnostico()["motor"]["suportado"]:
            raise ConnectionError("Perfil motor indisponivel.")
        if not runtime.parar_corpo().get("parada_confirmada"):
            raise ConnectionError("Sem parada inicial confirmada; motor nao enviado.")
        with runtime._lock:
            runtime._seq_motor += 1
            sessao = runtime._sessao
            campos = f"{sessao} {runtime._seq_motor} 100 100 5000"
            inicio = time.monotonic()
            runtime._escrever("MOTOR 1 " + campos)
            prova["comandos_motor_enviados"] = 1
            confirmado = runtime._esperar("MACK 1 " + campos, .5, opcional=True)
            prova["aplicacao_pwm_confirmada"] = confirmado
            if not confirmado:
                raise ConnectionError("Sem MACK do comando continuo; nenhum reenvio.")
        print("Um MOTOR enviado: frente/PWM100/5000ms; MACK recebido.", flush=True)
        while time.monotonic() - inicio < 5.05:
            with runtime._lock:
                if runtime._sessao != sessao or runtime._serial is None:
                    raise ConnectionError("Sessao perdida; teste interrompido sem replay.")
            time.sleep(.02)
        prova["janela_comando_s"] = round(time.monotonic() - inicio, 3)
        prova["concluido"] = True
    except Exception as erro:
        prova["erro"] = type(erro).__name__ + ":" + str(erro)
        if inicio is not None:
            prova["janela_comando_s"] = round(time.monotonic() - inicio, 3)
        raise
    finally:
        prova["parada_final"] = runtime.parar_corpo()
        encerrar.set(); servico.join(5)
        runtime.encerrar()
        prova["heartbeat_encerrado"] = not servico.is_alive()
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(prova, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"parada_confirmada": prova["parada_final"].get("parada_confirmada"),
                          "receipt": str(destino)}), flush=True)


if __name__ == "__main__":
    main()

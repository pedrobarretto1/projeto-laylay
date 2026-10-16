"""Convivência dos sensores com o owner USB real, sem executar tração."""
import json
import time
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(Path(__file__).parent / "instancia_diagnostico")
import laylay
from scripts.diagnosticar_sensores_usb import interpretar_linha_distancia

rosto = laylay._rosto_oled_runtime
enviados = []
escrever = rosto._escrever
def observar(texto):
    tipo = texto.split()[0]
    if tipo == "MOTOR":
        raise AssertionError("diagnóstico não autoriza tração")
    enviados.append(tipo)
    escrever(texto)
rosto._escrever = observar
r = []
try:
    for seq in range(1, 11):
        assert rosto.sincronizar(), rosto.diagnostico()["motivo"]
        assert rosto.diagnostico()["aplicacao_confirmada"]
        with rosto._lock:
            rosto._escrever(f"DIST 1 {seq}")
            prazo = time.monotonic() + 1
            resposta = None
            while time.monotonic() < prazo:
                rosto._rx.extend(rosto._serial.read(128))
                while b"\n" in rosto._rx:
                    linha, _, resto = rosto._rx.partition(b"\n")
                    rosto._rx = bytearray(resto)
                    texto = linha.rstrip(b"\r").decode("ascii")
                    if texto.startswith(f"DIST 1 {seq} "):
                        resposta = interpretar_linha_distancia(texto, seq)
                if resposta is not None:
                    break
            assert resposta is not None, "diagnóstico sem resposta correlacionada"
            r.append(resposta)
        time.sleep(.1)
finally:
    rosto.encerrar()
    (Path(__file__).parent / "composicao.json").write_text(json.dumps({
        "amostras": r, "face_confirmado": len(r) == 10, "comandos_firmware": enviados,
        "motor_enviado": "MOTOR" in enviados, "protecao_calibrada": False,
        "integracao_sensor_na_mente": False, "encerrada": True}, ensure_ascii=False, indent=2), encoding="utf-8")
print("FACE e DIST conviveram no owner USB real; nenhum MOTOR enviado.")

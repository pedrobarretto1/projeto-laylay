"""Consulta o firmware gravado sem resetar a placa nem enviar movimento."""
import hashlib
import json
import sys
import time
from pathlib import Path
import serial

raiz = Path(__file__).resolve().parents[3]
fonte = raiz / "firmware/rosto_laylay/rosto_laylay.ino"
binario = Path(__file__).with_name("build") / "rosto_laylay.ino.bin"
linhas = []
with serial.Serial("COM4", 115200, timeout=.1, write_timeout=.5) as porta:
    inicio = time.monotonic()
    while time.monotonic() - inicio < 3:
        linha = porta.readline().decode("utf-8", errors="replace").strip()
        if linha:
            linhas.append(linha)
    porta.write(b"HELLO 1 65bbac01\nMCAPS 1 65bbac01\nSTOP 1 65bbac01 1\n")
    limite = time.monotonic() + 3
    while time.monotonic() < limite:
        linha = porta.readline().decode("utf-8", errors="replace").strip()
        if linha:
            linhas.append(linha)
        if any(l.startswith("SACK 1 65bbac01 1") for l in linhas):
            break
assert any(l == "MCAPS 1 65bbac01 MOTOR1" for l in linhas), linhas
assert any(l.startswith("SACK 1 65bbac01 1") for l in linhas), linhas
dados = {
    "fonte_sha256": hashlib.sha256(fonte.read_bytes()).hexdigest(),
    "bin_sha256": hashlib.sha256(binario.read_bytes()).hexdigest(),
    "porta": "COM4", "pino_som": 6, "frequencia_hz": 1200,
    "duracao_programada_ms": 2000, "bip_unico_por_boot": True,
    "wifi_compilado": False, "motor1_confirmado": True,
    "parada_confirmada": True, "movimento_enviado": False,
    "observacao_auditiva_humana": False, "linhas_serial": linhas,
}
Path(__file__).with_name("receipt_firmware.json").write_text(
    json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(dados, ensure_ascii=False))

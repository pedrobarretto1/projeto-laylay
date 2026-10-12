"""Consulta após gravar um perfil de bip: sem reset, FACE ou movimento."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import serial

diretorio = Path(__file__).resolve().parent
raiz = diretorio.parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--modo", choices=("ponte", "simples"), default="ponte")
parser.add_argument("--build-dir", type=Path, default=diretorio / "build")
parser.add_argument("--output-dir", type=Path, default=diretorio)
args = parser.parse_args()
assert args.output_dir.is_dir(), args.output_dir
fonte = raiz / "firmware/rosto_laylay/rosto_laylay.ino"
binario = args.build_dir / "rosto_laylay.ino.bin"
linhas = []
with serial.Serial("COM4", 115200, timeout=.1, write_timeout=.5) as porta:
    inicio = time.monotonic()
    while time.monotonic() - inicio < 3:
        linha = porta.readline().decode("utf-8", errors="replace").strip()
        if linha:
            linhas.append(linha)
    porta.write(b"HELLO 1 65bbac02\nMCAPS 1 65bbac02\nSTOP 1 65bbac02 1\n")
    limite = time.monotonic() + 3
    while time.monotonic() < limite:
        linha = porta.readline().decode("utf-8", errors="replace").strip()
        if linha:
            linhas.append(linha)
        if "SACK 1 65bbac02 1" in linhas:
            break
assert "READY 1 65bbac02 SSD1306 128 64" in linhas, linhas
assert "MCAPS 1 65bbac02 MOTOR1" in linhas, linhas
assert "SACK 1 65bbac02 1" in linhas, linhas
agora = datetime.now(timezone.utc)
dados = {
    "timestamp_utc": agora.isoformat(), "porta": "COM4",
    "fonte_sha256": hashlib.sha256(fonte.read_bytes()).hexdigest(),
    "bin_sha256": hashlib.sha256(binario.read_bytes()).hexdigest(),
    "perfil_build": f"LAYLAY_WIFI=0; LAYLAY_HABILITAR_MOTORES_BANCADA=1; LAYLAY_SOM_PONTE={int(args.modo == 'ponte')}",
    "pinos_som": [6, 5] if args.modo == "ponte" else [6], "resistor_informado_ohms": 220,
    "frequencia_programada_hz": 1200, "duracao_programada_ms": 2000,
    "stop_bip_observado": "BEEP_TEST 1 STOP" in linhas,
    "motor1_confirmado": True, "parada_confirmada": True,
    "movimento_enviado": False, "audio_humano": "pendente",
    "linhas_serial": linhas,
}
destino = args.output_dir / f"receipt_firmware_{agora.strftime('%Y%m%dT%H%M%S_%fZ')}.json"
destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"arquivo": str(destino), **dados}, ensure_ascii=False))

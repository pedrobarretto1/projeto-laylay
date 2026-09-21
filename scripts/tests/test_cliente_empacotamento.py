"""Smoke de instalação não conecta, não pede IP e não executa automação."""
import os
from pathlib import Path
import subprocess
import sys


def test_verificacao_instalacao_termina_sem_configurar_pc(tmp_path):
    raiz = Path(__file__).resolve().parents[2]
    ambiente = dict(os.environ, LAYLAY_PC_B_AUTO_INSTALL="0", LAYLAY_PC_B_AUTOSTART="0")
    resultado = subprocess.run(
        [sys.executable, str(raiz / "cliente/cliente_laylay.py"), "--verificar-instalacao"],
        cwd=tmp_path, env=ambiente, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=10, check=False,
    )
    assert resultado.returncode == 0, resultado.stderr
    assert "LAYLAY_CLIENTE_INSTALACAO_OK" in resultado.stdout
    assert not (tmp_path / "cerebro_ip.txt").exists()

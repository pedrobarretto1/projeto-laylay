"""Inicializador simples do teste conversacional automatizado."""

from __future__ import annotations

import subprocess
from pathlib import Path
import sys


def executar_roteiro(caminho: str, *, retomar: bool = False) -> int:
    raiz = Path(__file__).resolve().parents[1]
    roteiro = Path(caminho).expanduser().resolve()
    comando = [
        sys.executable,
        str(raiz / "laylay.py"),
        "--roteiro",
        str(roteiro),
    ]
    if retomar:
        comando.append("--retomar")
    try:
        return int(subprocess.call(comando, cwd=str(raiz)))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Uso: python cliente/executor_roteiro_laylay.py "
            "roteiro_teste_laylay.py [--retomar]"
        )
        raise SystemExit(2)
    raise SystemExit(
        executar_roteiro(sys.argv[1], retomar="--retomar" in sys.argv[2:])
    )


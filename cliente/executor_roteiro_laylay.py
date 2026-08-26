"""Inicializador simples do teste conversacional automatizado."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
import sys
import time


# P0_DIAGNOSTICO_EXIT_CODE_V1_20260815
def _registrar_saida_processo(
    raiz: Path,
    *,
    roteiro: Path,
    codigo: int,
    iniciado_em: float,
    finalizado_em: float,
    estado: str,
) -> Path | None:
    try:
        pasta = Path(raiz) / "resultados_testes"
        pasta.mkdir(parents=True, exist_ok=True)
        caminho = pasta / "executor_roteiro_exit.log"
        codigo_inteiro = int(codigo)
        registro = {
            "ts": float(finalizado_em),
            "launcher_pid": os.getpid(),
            "roteiro": str(Path(roteiro).name),
            "estado": str(estado or "finalizado"),
            "codigo": codigo_inteiro,
            "codigo_hex": f"0x{codigo_inteiro & 0xFFFFFFFF:08X}",
            "duracao_s": round(max(0.0, float(finalizado_em) - float(iniciado_em)), 3),
        }
        with open(caminho, "a", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        return caminho
    except Exception:
        return None


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
    iniciado_em = time.time()
    ambiente = dict(os.environ)
    ambiente.setdefault("PYTHONFAULTHANDLER", "1")
    try:
        codigo = int(subprocess.call(comando, cwd=str(raiz), env=ambiente))
        finalizado_em = time.time()
        caminho_log = _registrar_saida_processo(
            raiz, roteiro=roteiro, codigo=codigo, iniciado_em=iniciado_em,
            finalizado_em=finalizado_em, estado="finalizado",
        )
        print(
            "🔬 [ROTEIRO:PROCESSO] laylay.py encerrou "
            f"| codigo={codigo} hex=0x{codigo & 0xFFFFFFFF:08X}"
            + (f" | log={caminho_log}" if caminho_log else "")
        )
        return codigo
    except KeyboardInterrupt:
        _registrar_saida_processo(
            raiz, roteiro=roteiro, codigo=130, iniciado_em=iniciado_em,
            finalizado_em=time.time(), estado="interrompido_launcher",
        )
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


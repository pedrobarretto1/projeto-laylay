"""Inicializador gráfico que abre a Laylay dentro de uma sessão real do CMD."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import subprocess
import sys


def pasta_aplicacao() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def comando_inicializacao(raiz: Path | None = None) -> tuple[str, list[str]]:
    pasta = Path(raiz or pasta_aplicacao()).resolve()
    executavel = pasta / "Laylay.exe"
    comspec = os.environ.get("COMSPEC") or str(
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "cmd.exe"
    )
    # /k preserva a janela depois de um encerramento ou erro, permitindo ler
    # o diagnóstico e iniciar novamente sem perder o terminal.
    return str(executavel), [comspec, "/d", "/k", str(executavel)]


def _mostrar_erro(mensagem: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(None, mensagem, "Laylay", 0x10)
    except Exception:
        pass


def main() -> int:
    executavel, comando = comando_inicializacao()
    if not Path(executavel).is_file():
        _mostrar_erro(
            "Não encontrei Laylay.exe ao lado do inicializador. "
            "Mantenha a pasta portátil completa."
        )
        return 1
    try:
        subprocess.Popen(
            comando,
            cwd=str(Path(executavel).parent),
            creationflags=(
                getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            ),
            close_fds=True,
        )
        return 0
    except Exception as erro:
        _mostrar_erro(f"Não consegui abrir o terminal da Laylay: {erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Reconstrução segura da linha de comando usada no reinício da Laylay."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable


def construir_argumentos_reinicio(
    executavel: str | os.PathLike[str],
    *,
    script: str | os.PathLike[str] | None = None,
    argumentos: Iterable[str] = (),
    empacotado: bool = False,
    sistema: str | None = None,
) -> list[str]:
    """Monta ``argv`` preservando caminhos com espaços no ``execv`` do Windows.

    No Windows, ``os.execv`` não aplica a mesma reconstrução segura de linha de
    comando feita por ``subprocess.Popen``. Cada argumento precisa chegar já
    cotado segundo as regras de ``CreateProcess``. Em outros sistemas, inserir
    essas aspas alteraria o valor real do argumento, portanto a lista permanece
    intacta.
    """
    exe = str(Path(executavel).resolve())
    itens = [exe]
    if not empacotado:
        if script is None:
            raise ValueError("o script é obrigatório fora da versão empacotada")
        itens.append(str(Path(script).resolve()))
    itens.extend(str(item) for item in argumentos)

    plataforma = str(sistema or os.name).casefold()
    if plataforma == "nt":
        return [subprocess.list2cmdline([item]) for item in itens]
    return itens

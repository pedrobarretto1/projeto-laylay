from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from mente_laylay.integracao.reinicio_processo import construir_argumentos_reinicio


def test_windows_cota_executavel_script_e_argumentos_com_espacos(tmp_path: Path) -> None:
    raiz = tmp_path / "pasta organizada" / "projeto lay"
    executavel = raiz / "Python 3.14" / "python.exe"
    script = raiz / "laylay.py"

    argumentos = construir_argumentos_reinicio(
        executavel,
        script=script,
        argumentos=("--perfil", "modo de teste"),
        sistema="nt",
    )

    assert argumentos[0].startswith('"') and argumentos[0].endswith('"')
    assert argumentos[1].startswith('"') and argumentos[1].endswith('"')
    assert argumentos[-1] == '"modo de teste"'


def test_outros_sistemas_preservam_argumentos_sem_aspas_artificiais(tmp_path: Path) -> None:
    script = tmp_path / "pasta com espaço" / "laylay.py"
    argumentos = construir_argumentos_reinicio(
        sys.executable,
        script=script,
        argumentos=("--teste",),
        sistema="posix",
    )

    assert argumentos[0] == str(Path(sys.executable).resolve())
    assert argumentos[1] == str(script.resolve())
    assert argumentos[2] == "--teste"


def test_versao_empacotada_nao_insere_script() -> None:
    argumentos = construir_argumentos_reinicio(
        r"C:\Laylay Portátil\Laylay.exe",
        argumentos=("--voz",),
        empacotado=True,
        sistema="nt",
    )

    assert len(argumentos) == 2
    assert "Laylay.exe" in argumentos[0]
    assert argumentos[1] == "--voz"


@pytest.mark.skipif(os.name != "nt", reason="regressão específica do execv no Windows")
def test_execv_real_abre_script_em_diretorio_com_espacos(tmp_path: Path) -> None:
    pasta = tmp_path / "pasta organizada" / "projeto lay"
    pasta.mkdir(parents=True)
    script = pasta / "prova reinicio.py"
    script.write_text("print('REINICIO_OK')\n", encoding="utf-8")
    codigo = (
        "import os,sys; "
        "from mente_laylay.integracao.reinicio_processo import construir_argumentos_reinicio; "
        "args=construir_argumentos_reinicio(sys.executable,script=sys.argv[1]); "
        "os.execv(sys.executable,args)"
    )

    processo = subprocess.run(
        [sys.executable, "-c", codigo, str(script)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert processo.returncode == 0, processo.stderr
    assert processo.stdout.strip() == "REINICIO_OK"

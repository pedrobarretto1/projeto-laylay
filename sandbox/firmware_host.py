"""Compilação nativa e protocolo interno do sketch simulado."""

from pathlib import Path
from queue import Empty, Queue
import os
import shutil
import subprocess
from threading import Thread


def compilar(sketch: Path, destino: Path) -> tuple[Path, str]:
    destino.mkdir(parents=True, exist_ok=True)
    fonte = destino / "entrada.cpp"
    host = Path(__file__).with_name("host.cpp")
    base = sketch / "rosto_laylay.ino"
    perfil_frontal = "LAYLAY_SENSOR_BORDA" in (sketch / "sensores_distancia.h").read_text(encoding="utf-8")
    fonte.write_text(
        ("#define LAYLAY_SENSOR_BORDA 0\n" if perfil_frontal else "")
        + f'#define LAYLAY_SKETCH_HOST "{base.as_posix()}"\n#include "{host.as_posix()}"\n',
        encoding="utf-8",
    )
    includes = sketch / "validacao_host"
    executavel = destino / ("laylay_host.exe" if os.name == "nt" else "laylay_host")
    compilador = shutil.which("c++") or shutil.which("g++")
    if compilador:
        comando = [compilador, "-std=c++17", "-O2", "-I", str(includes), str(fonte), "-o", str(executavel)]
    elif os.name == "nt":
        vswhere = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
        if not vswhere.is_file():
            raise RuntimeError("Instale as ferramentas C++ do Visual Studio ou use g++ no PATH.")
        vs = subprocess.check_output([str(vswhere), "-latest", "-products", "*", "-requires",
                                      "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property",
                                      "installationPath"], text=True, timeout=15).strip()
        ambiente = Path(vs) / "VC/Auxiliary/Build/vcvars64.bat"
        if not ambiente.is_file():
            raise RuntimeError("O compilador C++ do Visual Studio não foi encontrado.")
        lote = destino / "compilar.cmd"
        lote.write_text(f'@call "{ambiente}" >nul\n@if errorlevel 1 exit /b 1\n'
                        f'@cl /nologo /std:c++17 /EHsc /O2 /I"{includes}" "{fonte}" /Fe:"{executavel}"\n',
                        encoding="mbcs")
        comando = ["cmd.exe", "/d", "/c", "compilar.cmd"]
    else:
        raise RuntimeError("Instale um compilador C++17.")
    resultado = subprocess.run(comando, cwd=destino, capture_output=True, text=True, errors="replace", timeout=90)
    log = (resultado.stdout + resultado.stderr).strip()
    if resultado.returncode or not executavel.is_file():
        raise RuntimeError(log or "A compilação do firmware falhou.")
    return executavel, log


class Firmware:
    def __init__(self, executavel: Path) -> None:
        self.fila: Queue[str | None] = Queue()
        self.processo = subprocess.Popen([str(executavel)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, encoding="ascii", errors="replace",
                                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        Thread(target=self._receber, daemon=True).start()
        try:
            saida = self._ate_fim(3)
            if not any(linha.startswith("R BOOT 1 ") for linha in saida):
                raise RuntimeError("O firmware não confirmou a inicialização do OLED.")
        except Exception:
            self.fechar()
            raise

    def _receber(self) -> None:
        for linha in self.processo.stdout:
            self.fila.put(linha.rstrip("\r\n"))
        self.fila.put(None)

    def _ate_fim(self, tempo: float) -> list[str]:
        linhas = []
        try:
            for _ in range(256):
                linha = self.fila.get(timeout=tempo)
                if linha == "F":
                    return linhas
                if linha is None:
                    break
                linhas.append(linha)
        except Empty as erro:
            raise RuntimeError("O firmware parou de responder.") from erro
        raise RuntimeError("A sessão do firmware encerrou a resposta sem conclusão.")

    def consultar(self, linha: str) -> list[str]:
        self.processo.stdin.write(linha + "\n")
        self.processo.stdin.flush()
        return self._ate_fim(.7)

    def fechar(self) -> None:
        if self.processo.poll() is None:
            self.processo.terminate()
            self.processo.wait(timeout=3)
        self.processo.stdin.close()
        self.processo.stdout.close()

"""Ciclo de vida do motor LLM portátil da Laylay.

O executável e o GGUF ficam externos ao pacote Python para não serem
descompactados a cada abertura. Em desenvolvimento, ``auto`` preserva o
Ollama; numa distribuição congelada, prefere o ``llama-server`` incluído.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import requests


def raiz_aplicacao(raiz: str | os.PathLike[str] | None = None) -> Path:
    if raiz:
        return Path(raiz).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


class RuntimeLLMPortatil:
    """Inicia o llama-server sob demanda e encerra apenas o processo próprio."""

    def __init__(
        self,
        *,
        raiz: str | os.PathLike[str] | None = None,
        ambiente: Mapping[str, str] | None = None,
        requests_get: Callable[..., Any] = requests.get,
        requests_post: Callable[..., Any] = requests.post,
        popen: Callable[..., Any] = subprocess.Popen,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Any] = time.sleep,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.raiz = raiz_aplicacao(raiz)
        self.ambiente = dict(os.environ if ambiente is None else ambiente)
        self.requests_get = requests_get
        self.requests_post_original = requests_post
        self.popen = popen
        self.clock = clock
        self.sleep = sleep
        self.log = log
        self._lock = threading.RLock()
        self._processo: Any = None
        self._log_handle: Any = None
        self._encerrado = False
        self._backend_solicitado = str(
            self.ambiente.get("LAYLAY_LLM_BACKEND", "auto")
        ).casefold().strip()
        self.porta = max(1024, min(65535, int(
            self.ambiente.get("LAYLAY_LLM_PORTA", "11435") or 11435
        )))
        self.host = "127.0.0.1"
        self.modelo = str(
            self.ambiente.get("LAYLAY_LLM_MODEL", "Qwen3:4b-instruct")
        ).strip() or "Qwen3:4b-instruct"
        self.timeout_inicio = max(5.0, float(
            self.ambiente.get("LAYLAY_LLM_PORTATIL_INICIO_TIMEOUT", "90") or 90
        ))
        self.contexto = max(2048, int(
            self.ambiente.get("LAYLAY_LLM_CTX", "8192") or 8192
        ))

    @property
    def pasta_runtime(self) -> Path:
        caminho = self.ambiente.get("LAYLAY_LLM_RUNTIME_DIR", "")
        return Path(caminho).expanduser().resolve() if caminho else self.raiz / "runtime_llm"

    @property
    def caminho_modelo(self) -> Path:
        caminho = self.ambiente.get("LAYLAY_LLM_MODEL_PATH", "")
        if caminho:
            return Path(caminho).expanduser().resolve()
        preferido = self.raiz / "modelos" / "laylay-qwen3-4b-q4_k_m.gguf"
        if preferido.is_file():
            return preferido
        modelos = sorted((self.raiz / "modelos").glob("*.gguf")) if (self.raiz / "modelos").is_dir() else []
        return modelos[0] if modelos else preferido

    def _candidatos_servidor(self) -> list[tuple[Path, bool]]:
        explicito = self.ambiente.get("LAYLAY_LLM_SERVER_PATH", "")
        candidatos: list[tuple[Path, bool]] = []
        if explicito:
            caminho = Path(explicito).expanduser().resolve()
            candidatos.append((caminho, "vulkan" in str(caminho).casefold()))
        candidatos.extend((
            (self.pasta_runtime / "vulkan" / "llama-server.exe", True),
            (self.pasta_runtime / "cpu" / "llama-server.exe", False),
            (self.pasta_runtime / "llama-server.exe", False),
        ))
        vistos: set[str] = set()
        unicos: list[tuple[Path, bool]] = []
        for caminho, gpu in candidatos:
            chave = str(caminho).casefold()
            if chave not in vistos:
                vistos.add(chave)
                unicos.append((caminho, gpu))
        return unicos

    @property
    def backend(self) -> str:
        if self._backend_solicitado in {"portable", "portatil", "llama.cpp", "llamacpp"}:
            return "portatil"
        if self._backend_solicitado in {"ollama", "remote", "remoto"}:
            return "remoto" if self._backend_solicitado in {"remote", "remoto"} else "ollama"
        tem_portatil = self.modelo_disponivel and self.motor_disponivel
        return "portatil" if (getattr(sys, "frozen", False) and tem_portatil) else "ollama"

    @property
    def base_url(self) -> str:
        explicita = str(self.ambiente.get("LAYLAY_LLM_BASE_URL", "")).strip()
        if explicita:
            return explicita.rstrip("/")
        if self.backend == "portatil":
            return f"http://{self.host}:{self.porta}/v1"
        return "http://localhost:11434/v1"

    @property
    def api_key(self) -> str:
        return str(self.ambiente.get("LAYLAY_LLM_API_KEY", "local") or "local")

    @property
    def modelo_disponivel(self) -> bool:
        return self.caminho_modelo.is_file()

    @property
    def motor_disponivel(self) -> bool:
        return any(caminho.is_file() for caminho, _gpu in self._candidatos_servidor())

    def _saudavel(self) -> bool:
        try:
            resposta = self.requests_get(
                f"http://{self.host}:{self.porta}/v1/models",
                timeout=0.45,
            )
            return int(getattr(resposta, "status_code", 0) or 0) == 200
        except Exception:
            return False

    def _fechar_log(self) -> None:
        handle, self._log_handle = self._log_handle, None
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass

    def _parar_processo(self) -> bool:
        processo, self._processo = self._processo, None
        if processo is None:
            self._fechar_log()
            return False
        try:
            if processo.poll() is None:
                processo.terminate()
                try:
                    processo.wait(timeout=3)
                except Exception:
                    processo.kill()
            return True
        except Exception:
            return False
        finally:
            self._fechar_log()

    def _iniciar_candidato(self, servidor: Path, usar_gpu: bool) -> bool:
        logs = self.raiz / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        self._fechar_log()
        self._log_handle = open(logs / "llama-server.log", "a", encoding="utf-8")
        comando = [
            str(servidor), "-m", str(self.caminho_modelo),
            "--alias", self.modelo, "--host", self.host,
            "--port", str(self.porta), "-c", str(self.contexto),
            "-ngl", "99" if usar_gpu else "0",
        ]
        kwargs: dict[str, Any] = {
            "cwd": str(servidor.parent),
            "stdin": subprocess.DEVNULL,
            "stdout": self._log_handle,
            "stderr": subprocess.STDOUT,
        }
        if os.name == "nt":
            kwargs["creationflags"] = (
                getattr(subprocess, "CREATE_NO_WINDOW", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )
        try:
            self._processo = self.popen(comando, **kwargs)
        except Exception as erro:
            self.log(
                f"⚠️ [LLM PORTÁTIL] não iniciei {servidor.parent.name}: "
                f"{type(erro).__name__}."
            )
            self._processo = None
            self._fechar_log()
            return False

        prazo = self.clock() + self.timeout_inicio
        while self.clock() < prazo:
            if self._saudavel():
                self.log(
                    "🧠 [LLM PORTÁTIL] modelo local pronto via "
                    f"{'Vulkan' if usar_gpu else 'CPU'}."
                )
                return True
            if self._processo.poll() is not None:
                break
            self.sleep(0.2)
        self._parar_processo()
        return False

    def garantir_servidor(self) -> bool:
        if self.backend != "portatil":
            return True
        with self._lock:
            if self._encerrado:
                return False
            if self._saudavel():
                return True
            if not self.caminho_modelo.is_file():
                self.log(f"⚠️ [LLM PORTÁTIL] modelo não encontrado: {self.caminho_modelo}")
                return False
            servidores = [item for item in self._candidatos_servidor() if item[0].is_file()]
            if not servidores:
                self.log(f"⚠️ [LLM PORTÁTIL] llama-server não encontrado em {self.pasta_runtime}")
                return False
            tamanho_gb = self.caminho_modelo.stat().st_size / (1024 ** 3)
            self.log(f"🧠 [LLM PORTÁTIL] carregando {self.modelo} ({tamanho_gb:.2f} GB)...")
            for servidor, usar_gpu in servidores:
                if self._iniciar_candidato(servidor, usar_gpu):
                    return True
                if usar_gpu:
                    self.log("⚠️ [LLM PORTÁTIL] Vulkan falhou; tentando CPU.")
            self.log("⚠️ [LLM PORTÁTIL] nenhum motor conseguiu carregar o modelo.")
            return False

    def post(self, url: str, **kwargs: Any) -> Any:
        if self.backend == "portatil" and not self.garantir_servidor():
            raise requests.exceptions.ConnectionError(
                "motor LLM portátil indisponível; consulte logs/llama-server.log"
            )
        return self.requests_post_original(url, **kwargs)

    def descarregar(self) -> bool:
        """Libera RAM/VRAM, mantendo o runtime apto a reiniciar sob demanda."""
        if self.backend != "portatil":
            return False
        with self._lock:
            return self._parar_processo()

    def encerrar(self) -> None:
        with self._lock:
            self._encerrado = True
            self._parar_processo()


def criar_runtime_llm_portatil(**kwargs: Any) -> RuntimeLLMPortatil:
    return RuntimeLLMPortatil(**kwargs)

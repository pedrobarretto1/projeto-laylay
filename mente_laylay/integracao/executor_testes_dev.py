"""Executor CONTROL de testes cadastrados, sem shell ou caminhos do cliente."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class SuiteTestesDev:
    id: str
    titulo: str
    argumentos: tuple[str, ...]
    timeout_s: float


SUITES_TESTES_DEV: Mapping[str, SuiteTestesDev] = MappingProxyType({
    "dev_console_focado": SuiteTestesDev(
        id="dev_console_focado",
        titulo="Dev Console focado",
        argumentos=("tests/test_dev_console_runtime.py", "-q", "--tb=short"),
        timeout_s=120.0,
    ),
    "dev_console_regressao": SuiteTestesDev(
        id="dev_console_regressao",
        titulo="Dev Console e integrações",
        argumentos=(
            "tests/test_dev_console_runtime.py",
            "tests/test_diagnostico_evoluido.py",
            "tests/test_desktop_bridge.py",
            "tests/test_p1_orcamento_llm_turno.py",
            "-q",
            "--tb=short",
        ),
        timeout_s=240.0,
    ),
    "terminal": SuiteTestesDev(
        id="terminal",
        titulo="Terminal Laylay",
        argumentos=(
            "tests/test_terminal_3_p1_ui.py",
            "tests/test_terminal_3_p4_paginas.py",
            "tests/test_terminal_3_p5_acabamento.py",
            "tests/test_terminal_animacoes_a1.py",
            "tests/test_dev_console_runtime.py",
            "-q",
            "--tb=short",
        ),
        timeout_s=300.0,
    ),
})

_ID_SUITE_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,47}")
_COMANDO_RUN_RE = re.compile(r"tests run ([a-z0-9][a-z0-9_-]{0,47})")
_VARIAVEIS_AMBIENTE_PERMITIDAS = frozenset({
    "APPDATA", "CI", "COMSPEC", "LOCALAPPDATA", "NUMBER_OF_PROCESSORS",
    "OS", "PATH", "PATHEXT", "PROCESSOR_ARCHITECTURE", "PROGRAMDATA",
    "QT_QPA_PLATFORM", "SYSTEMDRIVE", "SYSTEMROOT", "TEMP", "TMP",
    "USERPROFILE", "WINDIR",
})


def _suite_valida(suite: SuiteTestesDev) -> bool:
    if not _ID_SUITE_RE.fullmatch(str(suite.id or "")):
        return False
    if not suite.argumentos or not 0 < float(suite.timeout_s) <= 3_600:
        return False
    opcoes = {"-q", "-x", "--tb=short", "--maxfail=1"}
    for argumento in suite.argumentos:
        item = str(argumento or "")
        if not item or "\x00" in item or "\n" in item or "\r" in item:
            return False
        if item.startswith("-"):
            if item not in opcoes:
                return False
            continue
        normalizado = item.replace("\\", "/")
        if (
            not normalizado.startswith("tests/")
            or not normalizado.endswith(".py")
            or ".." in normalizado.split("/")
            or Path(item).is_absolute()
        ):
            return False
    return True


class ExecutorTestesDevRuntime:
    """Um único owner para autorização, processo, cancelamento e receipt."""

    def __init__(
        self,
        *,
        raiz_projeto: str | os.PathLike[str],
        python_executavel: str | os.PathLike[str] = sys.executable,
        suites: Mapping[str, SuiteTestesDev] | None = None,
        popen_factory: Callable[..., Any] = subprocess.Popen,
        monotonic: Callable[[], float] = time.monotonic,
        publicar_linha: Callable[..., Any] | None = None,
        publicar_estado: Callable[[dict[str, Any]], Any] | None = None,
        habilitado: bool = True,
    ) -> None:
        self.raiz_projeto = Path(raiz_projeto).resolve()
        self.python_executavel = str(python_executavel)
        self.habilitado = bool(habilitado)
        candidatas = dict(suites or SUITES_TESTES_DEV) if self.habilitado else {}
        self.suites = {
            suite_id: suite
            for suite_id, suite in candidatas.items()
            if suite_id == suite.id and _suite_valida(suite)
        }
        self.popen_factory = popen_factory
        self.monotonic = monotonic
        self.publicar_linha = publicar_linha
        self.publicar_estado = publicar_estado
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._processo: Any | None = None
        self._cancelamento_solicitado = False
        self._sequencia = 0
        self._estado: dict[str, Any] = {
            "execucao_id": "",
            "suite_id": "",
            "status": "ocioso",
            "disponivel": self.habilitado,
            "ativo": False,
            "returncode": None,
            "duracao_ms": 0.0,
            "comando_efetivo": [],
            "autorizacao_explicita": False,
            "autoriza_execucao": False,
        }

    @staticmethod
    def _resultado(
        comando: str,
        *,
        ok: bool,
        status: str,
        linhas: Sequence[str],
        receipt: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "ok": bool(ok),
            "kind": "tests",
            "command": comando,
            "status": status,
            "lines": [str(item)[:500] for item in list(linhas)[:120]],
            "receipt": dict(receipt or {}),
        }

    def _publicar_estado(self, estado: Mapping[str, Any]) -> None:
        if callable(self.publicar_estado):
            try:
                self.publicar_estado(dict(estado))
            except Exception:
                pass

    def _publicar_linha(
        self,
        texto: str,
        *,
        origem: str = "runtime",
        profundidade: str = "trace",
    ) -> None:
        if not callable(self.publicar_linha):
            return
        try:
            self.publicar_linha(
                str(texto).rstrip("\r\n"),
                origem=origem if origem in {"stdout", "stderr"} else "runtime",
                profundidade=(
                    profundidade if profundidade in {"normal", "trace"}
                    else "trace"
                ),
            )
        except Exception:
            pass

    @staticmethod
    def _ambiente_controlado() -> dict[str, str]:
        ambiente = {
            chave: valor
            for chave, valor in os.environ.items()
            if chave.upper() in _VARIAVEIS_AMBIENTE_PERMITIDAS
        }
        ambiente.update({
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUNBUFFERED": "1",
            "PYTHONUTF8": "1",
            "LAYLAY_DEV_CONTROL": "1",
        })
        return ambiente

    def listar(self, comando: str = "tests list") -> dict[str, Any]:
        linhas = ["SUÍTES CONTROL PERMITIDAS"]
        linhas.extend(
            f"{suite.id}: {suite.titulo} timeout={suite.timeout_s:.0f}s"
            for suite in self.suites.values()
        )
        if len(linhas) == 1:
            linhas.append("Nenhuma suíte válida foi cadastrada.")
        return self._resultado(
            comando, ok=bool(self.suites), status="listado", linhas=linhas,
        )

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._estado)

    def status(self, comando: str = "tests status") -> dict[str, Any]:
        estado = self.diagnostico()
        return self._resultado(
            comando,
            ok=True,
            status=str(estado.get("status") or "ocioso"),
            linhas=[
                "TESTES CONTROL",
                f"execucao={estado.get('execucao_id') or 'nenhuma'} "
                f"suite={estado.get('suite_id') or 'nenhuma'} "
                f"status={estado.get('status') or 'ocioso'}",
                f"returncode={estado.get('returncode')} "
                f"duracao_ms={float(estado.get('duracao_ms') or 0.0):.1f}",
            ],
            receipt=estado if not estado.get("ativo") else None,
        )

    def executar(self, suite_id: str, *, autorizado: bool) -> dict[str, Any]:
        comando = f"tests run {suite_id}"
        if autorizado is not True:
            return self._resultado(
                comando,
                ok=False,
                status="bloqueado_autorizacao",
                linhas=["Execução bloqueada: autorização explícita ausente."],
            )
        suite = self.suites.get(str(suite_id or ""))
        if suite is None:
            return self._resultado(
                comando,
                ok=False,
                status="suite_nao_permitida",
                linhas=["Execução bloqueada: suite_id não consta na allowlist."],
            )
        with self._lock:
            if self._estado.get("ativo"):
                return self._resultado(
                    comando,
                    ok=False,
                    status="execucao_em_andamento",
                    linhas=["Já existe uma execução CONTROL ativa."],
                    receipt=self._estado,
                )
            self._sequencia += 1
            execucao_id = f"test-dev-{self._sequencia:06d}"
            argv = [
                self.python_executavel, "-m", "pytest", *suite.argumentos,
            ]
            self._cancelamento_solicitado = False
            self._estado = {
                "execucao_id": execucao_id,
                "suite_id": suite.id,
                "status": "executando",
                "ativo": True,
                "returncode": None,
                "duracao_ms": 0.0,
                "comando_efetivo": list(argv),
                "autorizacao_explicita": True,
                "autoriza_execucao": False,
            }
            estado_inicial = dict(self._estado)
            self._thread = threading.Thread(
                target=self._executar_suite,
                args=(suite, argv, execucao_id),
                name=f"Laylay-Dev-Testes-{suite.id}",
                daemon=True,
            )
            thread = self._thread
        self._publicar_estado(estado_inicial)
        self._publicar_linha(
            f"[TEST] {execucao_id} iniciado suite={suite.id}",
            profundidade="normal",
        )
        thread.start()
        return self._resultado(
            comando,
            ok=True,
            status="executando",
            linhas=[
                f"Execução autorizada: {execucao_id}",
                f"suite={suite.id} timeout={suite.timeout_s:.0f}s",
            ],
            receipt=estado_inicial,
        )

    def _ler_stream(self, stream: Any, origem: str) -> None:
        if stream is None:
            return
        try:
            for linha in iter(stream.readline, ""):
                if linha:
                    self._publicar_linha(linha, origem=origem)
        except Exception:
            self._publicar_linha(
                f"[TEST] leitura de {origem} foi interrompida",
                origem="stderr",
            )

    @staticmethod
    def _encerrar_processo(processo: Any) -> None:
        try:
            processo.terminate()
            processo.wait(timeout=2.0)
        except Exception:
            try:
                processo.kill()
                processo.wait(timeout=2.0)
            except Exception:
                pass

    def _executar_suite(
        self,
        suite: SuiteTestesDev,
        argv: list[str],
        execucao_id: str,
    ) -> None:
        inicio = float(self.monotonic())
        processo = None
        status = "falhou"
        returncode = None
        codigo_erro = ""
        try:
            processo = self.popen_factory(
                list(argv),
                cwd=str(self.raiz_projeto),
                env=self._ambiente_controlado(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                shell=False,
            )
            with self._lock:
                self._processo = processo
                cancelar_agora = self._cancelamento_solicitado
            leitores = [
                threading.Thread(
                    target=self._ler_stream,
                    args=(stream, origem),
                    name=f"{threading.current_thread().name}-{origem}",
                    daemon=True,
                )
                for stream, origem in (
                    (processo.stdout, "stdout"),
                    (processo.stderr, "stderr"),
                )
            ]
            for leitor in leitores:
                leitor.start()
            if cancelar_agora:
                self._encerrar_processo(processo)
            try:
                returncode = processo.wait(timeout=float(suite.timeout_s))
            except subprocess.TimeoutExpired:
                codigo_erro = "timeout"
                self._encerrar_processo(processo)
                returncode = processo.returncode
            for leitor in leitores:
                leitor.join(timeout=1.0)
            with self._lock:
                cancelado = self._cancelamento_solicitado
            if cancelado:
                status = "cancelado"
            elif codigo_erro == "timeout":
                status = "timeout"
            elif returncode == 0:
                status = "passou"
            else:
                status = "falhou"
        except Exception as erro:
            codigo_erro = "falha_inicio"
            status = "falhou"
            self._publicar_linha(
                f"[TEST] {execucao_id} falhou ao iniciar tipo={type(erro).__name__}",
                origem="stderr",
                profundidade="normal",
            )
        duracao_ms = round(max(0.0, (float(self.monotonic()) - inicio) * 1000), 2)
        with self._lock:
            self._processo = None
            self._estado = {
                **self._estado,
                "status": status,
                "ativo": False,
                "returncode": returncode,
                "duracao_ms": duracao_ms,
                "codigo_erro": codigo_erro,
                "autorizacao_explicita": True,
                "autoriza_execucao": False,
            }
            receipt = dict(self._estado)
        self._publicar_linha(
            f"[TEST:RECEIPT] {execucao_id} status={status} "
            f"returncode={returncode} duracao_ms={duracao_ms:.1f} "
            f"comando={Path(argv[0]).name} {' '.join(argv[1:])}",
            profundidade="normal",
        )
        self._publicar_estado(receipt)

    def cancelar(self, *, autorizado: bool) -> dict[str, Any]:
        comando = "tests cancel"
        if autorizado is not True:
            return self._resultado(
                comando,
                ok=False,
                status="bloqueado_autorizacao",
                linhas=["Cancelamento bloqueado: autorização explícita ausente."],
            )
        with self._lock:
            if not self._estado.get("ativo"):
                return self._resultado(
                    comando,
                    ok=False,
                    status="sem_execucao_ativa",
                    linhas=["Não existe execução CONTROL ativa."],
                    receipt=self._estado,
                )
            self._cancelamento_solicitado = True
            processo = self._processo
            execucao_id = str(self._estado.get("execucao_id") or "")
        if processo is not None:
            self._encerrar_processo(processo)
        return self._resultado(
            comando,
            ok=True,
            status="cancelamento_solicitado",
            linhas=[f"Cancelamento solicitado para {execucao_id}."],
        )

    def consultar(self, comando: str, *, autorizado: bool = False) -> dict[str, Any]:
        limpo = re.sub(r"\s+", " ", str(comando or "").strip().casefold())[:160]
        if limpo == "tests list":
            return self.listar(limpo)
        if limpo == "tests status":
            return self.status(limpo)
        if limpo == "tests cancel":
            return self.cancelar(autorizado=autorizado)
        achado = _COMANDO_RUN_RE.fullmatch(limpo)
        if achado:
            return self.executar(achado.group(1), autorizado=autorizado)
        return self._resultado(
            limpo,
            ok=False,
            status="comando_invalido",
            linhas=["Comando CONTROL inválido; nenhum processo foi iniciado."],
        )

    def aguardar(self, timeout_s: float = 5.0) -> bool:
        with self._lock:
            thread = self._thread
        if thread is None:
            return True
        thread.join(timeout=max(0.0, float(timeout_s)))
        return not thread.is_alive()

    def encerrar(self, timeout_s: float = 3.0) -> None:
        if self.diagnostico().get("ativo"):
            self.cancelar(autorizado=True)
        self.aguardar(timeout_s)


def criar_executor_testes_dev_runtime(**kwargs: Any) -> ExecutorTestesDevRuntime:
    return ExecutorTestesDevRuntime(**kwargs)

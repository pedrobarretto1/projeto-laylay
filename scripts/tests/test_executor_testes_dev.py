from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import socket
import subprocess
import threading

import pytest
from PySide6.QtWidgets import QApplication

from cliente.terminal_2.desenvolvedor import PaginaDesenvolvedor
from mente_laylay.integracao.desktop_bridge import (
    DesktopBridgeRuntime,
    ErroProtocoloDesktop,
    validar_mensagem_cliente,
)
from mente_laylay.integracao.executor_testes_dev import (
    ExecutorTestesDevRuntime,
    SuiteTestesDev,
)


class ProcessoFake:
    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "",
        stderr: str = "",
        bloquear: bool = False,
        timeout: bool = False,
    ) -> None:
        self.returncode = None
        self._returncode_final = returncode
        self.stdout = StringIO(stdout)
        self.stderr = StringIO(stderr)
        self._liberado = threading.Event()
        self._bloquear = bloquear
        self._timeout = timeout
        self.terminated = False
        self.killed = False

    def wait(self, timeout=None):
        if self._timeout and not self.terminated and not self.killed:
            raise subprocess.TimeoutExpired("pytest", timeout)
        if self._bloquear:
            self._liberado.wait(timeout=timeout)
            if not self._liberado.is_set():
                raise subprocess.TimeoutExpired("pytest", timeout)
        self.returncode = -15 if self.terminated else -9 if self.killed else self._returncode_final
        return self.returncode

    def terminate(self):
        self.terminated = True
        self._liberado.set()

    def kill(self):
        self.killed = True
        self._liberado.set()


def _suite() -> SuiteTestesDev:
    return SuiteTestesDev(
        id="dev_focado",
        titulo="DEV focado",
        argumentos=("tests/test_dev_console_runtime.py", "-q"),
        timeout_s=10.0,
    )


def test_executor_rejeita_shell_suite_desconhecida_e_inicio_sem_autorizacao(tmp_path) -> None:
    chamadas = []
    runtime = ExecutorTestesDevRuntime(
        raiz_projeto=tmp_path,
        python_executavel="python-testes",
        suites={"dev_focado": _suite()},
        popen_factory=lambda *args, **kwargs: chamadas.append((args, kwargs)),
    )

    lista = runtime.consultar("tests list")
    sem_autorizacao = runtime.consultar("tests run dev_focado", autorizado=False)
    desconhecida = runtime.consultar("tests run tudo", autorizado=True)
    shell = runtime.consultar("tests run dev_focado; whoami", autorizado=True)

    assert lista["ok"] is True and "dev_focado" in "\n".join(lista["lines"])
    assert sem_autorizacao["status"] == "bloqueado_autorizacao"
    assert desconhecida["status"] == "suite_nao_permitida"
    assert shell["status"] == "comando_invalido"
    assert chamadas == []


def test_executor_usa_argv_fixo_e_receipt_nao_converte_falha_em_sucesso(
    tmp_path, monkeypatch,
) -> None:
    chamadas, linhas, estados = [], [], []
    processo = ProcessoFake(returncode=1, stdout="um passou\n", stderr="um falhou\n")
    monkeypatch.setenv("OPENAI_API_KEY", "segredo-nao-herdado")

    def abrir(argv, **kwargs):
        chamadas.append((argv, kwargs))
        return processo

    runtime = ExecutorTestesDevRuntime(
        raiz_projeto=tmp_path,
        python_executavel="python-testes",
        suites={"dev_focado": _suite()},
        popen_factory=abrir,
        publicar_linha=lambda texto, **dados: linhas.append((texto, dados)),
        publicar_estado=lambda estado: estados.append(estado),
    )

    inicio = runtime.consultar("tests run dev_focado", autorizado=True)
    assert inicio["receipt"]["autorizacao_explicita"] is True
    assert inicio["receipt"]["autoriza_execucao"] is False
    assert runtime.aguardar(2.0) is True
    receipt = runtime.diagnostico()

    assert inicio["ok"] is True
    assert chamadas[0][0] == [
        "python-testes", "-m", "pytest",
        "tests/test_dev_console_runtime.py", "-q",
    ]
    assert chamadas[0][1]["shell"] is False
    assert Path(chamadas[0][1]["cwd"]) == tmp_path.resolve()
    assert "OPENAI_API_KEY" not in chamadas[0][1]["env"]
    assert chamadas[0][1]["env"]["LAYLAY_DEV_CONTROL"] == "1"
    assert receipt["status"] == "falhou"
    assert receipt["returncode"] == 1
    assert receipt["duracao_ms"] >= 0
    assert receipt["comando_efetivo"] == chamadas[0][0]
    assert any(origem["origem"] == "stdout" for _, origem in linhas)
    assert any(origem["origem"] == "stderr" for _, origem in linhas)
    assert all(
        dados["profundidade"] == "trace"
        for texto, dados in linhas
        if texto in {"um passou", "um falhou"}
    )
    assert any(
        "status=falhou" in texto
        and "comando=python-testes -m pytest" in texto
        and dados["profundidade"] == "normal"
        for texto, dados in linhas
    )
    assert estados[-1]["status"] == "falhou"


def test_executor_impede_concorrencia_e_cancelamento_produz_receipt(tmp_path) -> None:
    processo = ProcessoFake(bloquear=True)
    runtime = ExecutorTestesDevRuntime(
        raiz_projeto=tmp_path,
        python_executavel="python-testes",
        suites={"dev_focado": _suite()},
        popen_factory=lambda *_args, **_kwargs: processo,
    )

    primeira = runtime.consultar("tests run dev_focado", autorizado=True)
    segunda = runtime.consultar("tests run dev_focado", autorizado=True)
    cancelamento = runtime.consultar("tests cancel", autorizado=True)
    assert runtime.aguardar(2.0) is True

    assert primeira["ok"] is True
    assert segunda["status"] == "execucao_em_andamento"
    assert cancelamento["ok"] is True
    assert processo.terminated is True
    assert runtime.diagnostico()["status"] == "cancelado"


def test_timeout_encerra_processo_e_nunca_publica_sucesso(tmp_path) -> None:
    processo = ProcessoFake(timeout=True)
    suite = SuiteTestesDev(
        id="curta", titulo="Curta", argumentos=("tests/test_curto.py", "-q"),
        timeout_s=0.01,
    )
    runtime = ExecutorTestesDevRuntime(
        raiz_projeto=tmp_path,
        suites={"curta": suite},
        popen_factory=lambda *_args, **_kwargs: processo,
    )

    runtime.consultar("tests run curta", autorizado=True)
    assert runtime.aguardar(2.0) is True

    assert processo.terminated is True
    assert runtime.diagnostico()["status"] == "timeout"


@pytest.mark.parametrize(
    "comando",
    ("tests run ../../segredo", "tests run dev_focado && calc", "pytest -q"),
)
def test_comandos_arbitrarios_falham_fechados(tmp_path, comando) -> None:
    runtime = ExecutorTestesDevRuntime(
        raiz_projeto=tmp_path,
        suites={"dev_focado": _suite()},
    )

    resultado = runtime.consultar(comando, autorizado=True)

    assert resultado["ok"] is False
    assert resultado["status"] == "comando_invalido"


def test_protocolo_control_e_separado_da_consulta_e_exige_autorizacao() -> None:
    mensagem = validar_mensagem_cliente(
        {
            "type": "dev_control",
            "id": "controle-1",
            "command": "tests run dev_console_focado",
            "authorized": True,
        },
        token="segredo",
        autenticado=True,
    )

    assert mensagem == {
        "type": "dev_control",
        "id": "controle-1",
        "command": "tests run dev_console_focado",
        "authorized": True,
    }
    with pytest.raises(ErroProtocoloDesktop):
        validar_mensagem_cliente(
            {
                "type": "dev_query",
                "command": "tests run dev_console_focado",
            },
            token="segredo",
            autenticado=True,
        )
    with pytest.raises(ErroProtocoloDesktop):
        validar_mensagem_cliente(
            {
                "type": "dev_control",
                "command": "tests run dev_console_focado",
                "authorized": False,
            },
            token="segredo",
            autenticado=True,
        )
    with pytest.raises(ErroProtocoloDesktop):
        validar_mensagem_cliente(
            {
                "type": "dev_control",
                "command": "tests run dev_console_focado && calc",
                "authorized": True,
            },
            token="segredo",
            autenticado=True,
        )


def test_interface_encaminha_tests_para_control_sem_reusar_dev_query() -> None:
    app = QApplication.instance() or QApplication([])
    pagina = PaginaDesenvolvedor()
    controles, consultas = [], []
    pagina.controle_solicitado.connect(controles.append)
    pagina.consulta_solicitada.connect(consultas.append)
    pagina.definir_conectada(True)

    pagina.comando.setText("tests run dev_console_focado")
    pagina._executar_comando_local()
    app.processEvents()

    assert controles == ["tests run dev_console_focado"]
    assert consultas == []
    assert "CONTROL" in pagina.estado_fonte.text()
    pagina.close()


def _receber_tipo(sock: socket.socket, tipo: str) -> dict:
    sock.settimeout(2.0)
    buffer = b""
    while True:
        while b"\n" not in buffer:
            buffer += sock.recv(16_384)
        linha, buffer = buffer.split(b"\n", 1)
        mensagem = json.loads(linha.decode("utf-8"))
        if mensagem.get("type") == tipo:
            return mensagem


def test_bridge_control_entrega_receipt_sanitizado_em_endpoint_proprio() -> None:
    chamadas = []

    def executar(comando, autorizado):
        chamadas.append((comando, autorizado))
        return {
            "ok": True,
            "kind": "tests",
            "command": comando,
            "status": "executando",
            "lines": ["Execução autorizada."],
            "receipt": {
                "execucao_id": "test-dev-000001",
                "suite_id": "dev_console_focado",
                "status": "executando",
                "ativo": True,
                "returncode": None,
                "duracao_ms": 0,
                "comando_efetivo": [
                    r"C:\Users\pessoa\privado\python.exe",
                    "-m", "pytest", "tests/test_dev_console_runtime.py", "-q",
                ],
                "ambiente": {"TOKEN": "não pode sair"},
            },
        }

    ponte = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=list,
        estado_getter=dict,
        dev_control_executar=executar,
        log=lambda _texto: None,
    )
    ponte.iniciar()
    try:
        with socket.create_connection(ponte.endereco, timeout=1.0) as cliente:
            cliente.sendall((json.dumps({
                "type": "hello", "token": ponte.token,
            }) + "\n").encode())
            _receber_tipo(cliente, "snapshot")
            cliente.sendall((json.dumps({
                "type": "dev_control",
                "id": "controle-1",
                "command": "tests run dev_console_focado",
                "authorized": True,
            }) + "\n").encode())
            resposta = _receber_tipo(cliente, "dev_control_result")
    finally:
        ponte.parar()

    assert chamadas == [("tests run dev_console_focado", True)]
    assert resposta["id"] == "controle-1"
    assert resposta["result"]["status"] == "executando"
    assert resposta["result"]["receipt"]["comando_efetivo"][0] == "python.exe"
    assert "privado" not in repr(resposta)
    assert "TOKEN" not in repr(resposta)


def test_suites_padrao_apontam_somente_para_testes_existentes() -> None:
    raiz = Path(__file__).resolve().parents[1]
    runtime = ExecutorTestesDevRuntime(raiz_projeto=raiz)

    assert set(runtime.suites) == {
        "dev_console_focado", "dev_console_regressao", "terminal",
    }
    for suite in runtime.suites.values():
        for argumento in suite.argumentos:
            if not argumento.startswith("-"):
                assert (raiz / argumento).is_file()


def test_composicao_real_conecta_control_sem_passar_pelo_dev_query() -> None:
    fonte = (Path(__file__).resolve().parents[1] / "laylay.py").read_text(
        encoding="utf-8",
    )

    assert "_executor_testes_dev_runtime = _criar_executor_testes_dev_runtime(" in fonte
    assert "dev_control_executar=lambda comando, autorizado:" in fonte
    assert "_executor_testes_dev_runtime.consultar(" in fonte
    assert "dev_console_consultar=_dev_console_runtime.consultar" in fonte


def test_build_sem_testes_fonte_mantem_control_indisponivel(tmp_path) -> None:
    runtime = ExecutorTestesDevRuntime(
        raiz_projeto=tmp_path,
        suites={"dev_focado": _suite()},
        habilitado=False,
    )

    lista = runtime.consultar("tests list")
    execucao = runtime.consultar("tests run dev_focado", autorizado=True)

    assert runtime.diagnostico()["disponivel"] is False
    assert lista["ok"] is False
    assert execucao["status"] == "suite_nao_permitida"

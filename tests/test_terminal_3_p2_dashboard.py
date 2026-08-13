from __future__ import annotations

import json
from pathlib import Path
import socket
import threading
import time

import pytest

from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
from mente_laylay.integracao.desktop_bridge import (
    DesktopBridgeRuntime,
    sanitizar_dashboard_estado,
)
from mente_laylay.memoria_mental.diagnostico_mente import DiagnosticoMenteRuntime
from mente_laylay.memoria_mental.formatacao_diagnostico import (
    formatar_diagnostico_terminal,
)


class _ValorPercentual:
    def __init__(self, percent: float) -> None:
        self.percent = percent


class _Psutil:
    @staticmethod
    def cpu_percent(*, interval=None):
        assert interval in {None, 0.1}
        return 18.0

    @staticmethod
    def virtual_memory():
        return _ValorPercentual(42.0)

    @staticmethod
    def disk_usage(_raiz):
        return _ValorPercentual(61.0)

    @staticmethod
    def boot_time():
        return 900.0


def _runtime(**trocas) -> DashboardTerminalRuntime:
    valores = {
        "configuracao_getter": lambda: {
            "provider": "ollama", "model": "qwen3:4b", "api_key": "segredo",
        },
        "llm_getter": lambda: {
            "modelo_disponivel": True,
            "prompt_disponivel": True,
            "estado_disponivel": True,
            "requisicoes": 3,
            "sucessos": 3,
            "falhas": 0,
            "falhas_consecutivas": 0,
            "estado": "saudavel",
        },
        "interacao_getter": lambda: {
            "voice_available": True, "interaction_mode": "chat",
        },
        "memoria_saude_getter": lambda: {
            "disponivel": True, "persistencia_local": True,
        },
        "agenda_getter": lambda: [{
            "ativo": True,
            "tipo": "once",
            "origem": "pedido_usuario",
            "evidencia": "persistencia_local",
            "nome": "Reunião com o time",
            "ts_execucao": 2_000.0,
            "intencao_no_disparo": None,
            "comandos_no_disparo": [],
        }],
        "aprendizados_getter": lambda **_kwargs: [{
            "fonte": "aprendizado_semantico",
            "natureza": "confirmado",
            "tipo": "preferencia",
            "confirmado_usuario": True,
            "texto": "Você prefere rock",
            "atualizado_em": "1970-01-01T00:30:00",
            "regra": "campo privado",
        }],
        "estado_mental_getter": lambda: {
            "ultima_acao_contrato": {
                "intent": "APP_OPEN", "alvo": "Opera", "status": "aberto",
                "executou": True, "confirmado": True, "params": {"token": "x"},
            },
            "ultima_acao_ts": 1_950.0,
        },
        "contexto_jogo_getter": lambda: {
            "ativo": True, "titulo": "Minecraft", "processo": "javaw.exe",
            "pid": 123, "hwnd": 456, "process_path": "C:\\privado\\java.exe",
        },
        "psutil_mod": _Psutil,
        "temperatura_getter": lambda: 48.0,
        "projeto": "Laylay",
        "cidade": "Boituva",
        "intervalo_s": 0.25,
        "intervalo_temperatura_s": 10.0,
        "clock": lambda: 2_000.0,
        "log": lambda _texto: None,
    }
    valores.update(trocas)
    return DashboardTerminalRuntime(**valores)


def _aguardar_retrato(runtime: DashboardTerminalRuntime) -> dict:
    limite = time.monotonic() + 1.5
    retrato = runtime.snapshot()
    while retrato["sequence"] == 0 and time.monotonic() < limite:
        time.sleep(0.01)
        retrato = runtime.snapshot()
    assert retrato["sequence"] > 0
    return retrato


def _aguardar_condicao_runtime(
    runtime: DashboardTerminalRuntime,
    condicao,
    *,
    timeout_s: float = 1.5,
) -> dict:
    limite = time.monotonic() + timeout_s
    retrato = runtime.snapshot()
    while not condicao(retrato) and time.monotonic() < limite:
        time.sleep(0.01)
        retrato = runtime.snapshot()
    assert condicao(retrato), retrato
    return retrato


def test_runtime_coleta_fora_do_snapshot_e_publica_apenas_memoria_confirmada() -> None:
    runtime = _runtime()
    inicio = time.monotonic()
    inicial = runtime.snapshot()
    assert time.monotonic() - inicio < 0.1
    assert inicial["status"] == "unavailable"

    retrato = _aguardar_retrato(runtime)
    try:
        assert retrato["health"]["llm"]["state"] == "online"
        assert retrato["health"]["microphone"]["state"] == "paused"
        assert retrato["health"]["memory"]["state"] == "online"
        assert retrato["context"]["game_name"] == "Minecraft"
        assert retrato["system"]["cpu_percent"]["value"] == 18.0
        assert retrato["system"]["ram_percent"]["value"] == 42.0
        assert [item["kind"] for item in retrato["memory_recent"]] == [
            "reminder", "preference", "task",
        ]
        serializado = json.dumps(retrato, ensure_ascii=False)
        assert "segredo" not in serializado
        assert "campo privado" not in serializado
        assert "process_path" not in serializado
        assert "params" not in serializado
    finally:
        runtime.parar()


def test_runtime_isola_falha_de_memoria_e_nao_inventa_temperatura() -> None:
    def falhar():
        raise RuntimeError("token-super-secreto")

    runtime = _runtime(
        memoria_saude_getter=falhar,
        agenda_getter=falhar,
        aprendizados_getter=lambda **_kwargs: [],
        temperatura_getter=lambda: None,
    )
    retrato = _aguardar_retrato(runtime)
    try:
        assert retrato["status"] == "partial"
        assert retrato["health"]["memory"]["state"] == "unavailable"
        assert retrato["health"]["llm"]["state"] == "online"
        assert retrato["system"]["cpu_percent"]["value"] == 18.0
        assert retrato["system"]["temperature_c"]["value"] is None
    finally:
        runtime.parar()


def test_runtime_omite_lembrete_executavel_preferencia_incerta_e_acao_nao_confirmada() -> None:
    runtime = _runtime(
        agenda_getter=lambda: [{
            "ativo": True, "tipo": "once", "origem": "pedido_usuario",
            "evidencia": "persistencia_local", "nome": "Abrir banco",
            "ts_execucao": 2_100.0,
            "intencao_no_disparo": {"intent": "APP_OPEN"},
        }],
        aprendizados_getter=lambda **_kwargs: [{
            "fonte": "hipotese_madura", "natureza": "padrao_percebido",
            "tipo": "preferencia", "confirmado_usuario": False,
            "texto": "Talvez goste de jazz",
        }],
        estado_mental_getter=lambda: {
            "ultima_acao_contrato": {
                "intent": "APP_OPEN", "executou": True, "confirmado": None,
            },
            "ultima_acao_ts": 2_000.0,
        },
    )
    retrato = _aguardar_retrato(runtime)
    try:
        assert retrato["memory_recent"] == []
    finally:
        runtime.parar()


def test_runtime_coletor_llm_bloqueado_nao_congela_sequencia() -> None:
    liberar = threading.Event()
    runtime = _runtime(
        llm_getter=lambda: liberar.wait(5.0),
        temperatura_getter=None,
    )
    inicio = time.monotonic()
    try:
        retrato = _aguardar_retrato(runtime)
        assert time.monotonic() - inicio < 1.2
        assert retrato["sequence"] > 0
        assert retrato["status"] == "partial"
        assert retrato["health"]["llm"]["state"] == "unavailable"
        assert retrato["health"]["microphone"]["state"] == "paused"
        assert retrato["system"]["cpu_percent"]["value"] == 18.0
    finally:
        liberar.set()
        runtime.parar()


def test_parar_impede_publicacao_tardia_de_fonte_bloqueada() -> None:
    agenda_entrou = threading.Event()
    liberar_agenda = threading.Event()
    chamadas: list[str] = []

    def agenda_bloqueada():
        chamadas.append("agenda")
        agenda_entrou.set()
        liberar_agenda.wait(5.0)
        return []

    def aprendizados_nao_deve_rodar(**_kwargs):
        chamadas.append("aprendizados")
        return []

    def estado_nao_deve_rodar():
        chamadas.append("estado")
        return {}

    runtime = _runtime(
        agenda_getter=agenda_bloqueada,
        aprendizados_getter=aprendizados_nao_deve_rodar,
        estado_mental_getter=estado_nao_deve_rodar,
        temperatura_getter=None,
    )
    runtime.snapshot()
    try:
        assert agenda_entrou.wait(1.5)
        runtime.parar(timeout_s=0.02)
        sequencia_ao_parar = runtime.snapshot()["sequence"]
        liberar_agenda.set()
        time.sleep(0.45)
        assert runtime.snapshot()["sequence"] == sequencia_ao_parar
        assert chamadas == ["agenda"]
    finally:
        liberar_agenda.set()
        runtime.parar()


def test_runtime_falha_isolada_da_agenda_degrada_so_memoria() -> None:
    def agenda_indisponivel():
        raise RuntimeError("agenda indisponível")

    runtime = _runtime(agenda_getter=agenda_indisponivel)
    try:
        retrato = _aguardar_condicao_runtime(
            runtime,
            lambda item: item["health"]["memory"]["state"] == "degraded",
        )
        assert retrato["status"] == "partial"
        assert retrato["health"]["memory"]["freshness"] == "fresh"
        assert retrato["health"]["llm"]["state"] == "online"
        assert retrato["health"]["microphone"]["state"] == "paused"
        assert retrato["system"]["cpu_percent"]["value"] == 18.0
        assert [item["kind"] for item in retrato["memory_recent"]] == [
            "preference", "task",
        ]
    finally:
        runtime.parar()


def test_runtime_metricas_indisponiveis_tornam_retrato_parcial() -> None:
    class PsutilIndisponivel:
        @staticmethod
        def cpu_percent(*, interval=None):
            raise RuntimeError("cpu indisponível")

        @staticmethod
        def virtual_memory():
            raise RuntimeError("ram indisponível")

        @staticmethod
        def disk_usage(_raiz):
            raise RuntimeError("disco indisponível")

        @staticmethod
        def boot_time():
            raise RuntimeError("uptime indisponível")

    runtime = _runtime(psutil_mod=PsutilIndisponivel, temperatura_getter=None)
    try:
        retrato = _aguardar_retrato(runtime)
        assert retrato["status"] == "partial"
        assert retrato["health"]["llm"]["state"] == "online"
        assert retrato["health"]["microphone"]["state"] == "paused"
        assert all(
            retrato["system"][chave]["value"] is None
            for chave in (
                "cpu_percent", "ram_percent", "disk_percent",
                "uptime_seconds",
            )
        )
        assert runtime.diagnostico()["falhas"] >= 4
    finally:
        runtime.parar()


def test_runtime_cpu_travada_nao_impede_ram_disco_e_uptime() -> None:
    liberar = threading.Event()

    class PsutilCpuTravada(_Psutil):
        chamadas_cpu = 0

        @classmethod
        def cpu_percent(cls, *, interval=None):
            cls.chamadas_cpu += 1
            if cls.chamadas_cpu > 1:
                liberar.wait(5.0)
            return 18.0

    runtime = _runtime(psutil_mod=PsutilCpuTravada, temperatura_getter=None)
    try:
        retrato = _aguardar_retrato(runtime)
        assert retrato["status"] == "partial"
        assert retrato["system"]["cpu_percent"]["value"] is None
        assert retrato["system"]["ram_percent"]["value"] == 42.0
        assert retrato["system"]["disk_percent"]["value"] == 61.0
        assert retrato["system"]["uptime_seconds"]["value"] == 1_100.0
    finally:
        liberar.set()
        runtime.parar()


def test_coleta_principal_nao_apaga_memoria_publicada_durante_o_ciclo() -> None:
    preferencia = {"texto": "Preferência antiga"}
    bloquear_contexto = {"ativo": False}
    contexto_entrou = threading.Event()
    liberar_contexto = threading.Event()

    def aprendizados(**_kwargs):
        return [{
            "fonte": "aprendizado_semantico",
            "natureza": "confirmado",
            "tipo": "preferencia",
            "confirmado_usuario": True,
            "texto": preferencia["texto"],
        }]

    def jogo():
        if bloquear_contexto["ativo"]:
            contexto_entrou.set()
            liberar_contexto.wait(5.0)
        return {"ativo": False}

    runtime = _runtime(
        aprendizados_getter=aprendizados,
        contexto_jogo_getter=jogo,
        temperatura_getter=None,
    )
    try:
        _aguardar_condicao_runtime(
            runtime,
            lambda item: any(
                card.get("summary") == "Preferência antiga"
                for card in item["memory_recent"]
            ),
        )
        bloquear_contexto["ativo"] = True
        coleta = threading.Thread(target=runtime._coletar_impl, daemon=True)
        coleta.start()
        assert contexto_entrou.wait(1.0)

        preferencia["texto"] = "Preferência nova"
        runtime._coletar_memoria()
        liberar_contexto.set()
        coleta.join(timeout=1.5)
        assert not coleta.is_alive()

        retrato = runtime.snapshot()
        resumos = [card.get("summary") for card in retrato["memory_recent"]]
        assert "Preferência nova" in resumos
        assert "Preferência antiga" not in resumos
    finally:
        liberar_contexto.set()
        runtime.parar()


def test_runtime_omite_tarefa_confirmada_antiga_da_memoria_recente() -> None:
    runtime = _runtime(
        agenda_getter=list,
        aprendizados_getter=lambda **_kwargs: [],
        estado_mental_getter=lambda: {
            "ultima_acao_contrato": {
                "intent": "DELETE_ITEM",
                "executou": True,
                "confirmado": True,
            },
            "ultima_acao_ts": 2_000.0 - 3_601.0,
        },
    )
    try:
        retrato = _aguardar_condicao_runtime(
            runtime,
            lambda item: item["health"]["memory"]["state"] == "online",
        )
        assert retrato["memory_recent"] == []
    finally:
        runtime.parar()


def test_sanitizador_dashboard_descarta_segrefos_e_numeros_invalidos() -> None:
    bruto = {
        "schema_version": 99,
        "status": "ok",
        "sequence": "inválida",
        "api_key": "sk-segredo",
        "health": {
            "llm": {
                "state": "online", "label": "Online", "provider": "ollama",
                "model": "qwen", "token": "não",
            },
        },
        "context": {
            "project": "Laylay", "mode": "Local", "city": "Boituva",
            "game_active": True, "game_name": "Minecraft", "pid": 22,
            "path": "C:\\segredo",
        },
        "memory_recent": [
            {
                "kind": "preference", "summary": f"Preferência {indice}",
                "source": "user_confirmed", "raw_memory": "não",
            }
            for indice in range(8)
        ],
        "system": {
            "cpu_percent": {"value": float("nan")},
            "ram_percent": {"value": True},
            "disk_percent": {"value": 101},
            "temperature_c": {"value": None},
            "uptime_seconds": {"value": 100},
        },
    }
    limpo = sanitizar_dashboard_estado(bruto)
    serializado = json.dumps(limpo, ensure_ascii=False)
    assert limpo["schema_version"] == 1
    assert limpo["sequence"] == 0
    assert len(limpo["memory_recent"]) == 3
    assert limpo["system"]["cpu_percent"]["value"] is None
    assert limpo["system"]["ram_percent"]["value"] is None
    assert limpo["system"]["disk_percent"]["value"] is None
    for proibido in ("sk-segredo", "token", "raw_memory", "C:\\segredo", "pid"):
        assert proibido not in serializado


def test_sanitizador_remove_formatos_reais_de_segredo_da_saude_e_contexto() -> None:
    sk_openrouter = "sk-or-v1-abcdefghijklmnopqrstuvwxyz123456"
    token_github = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    jwt = (
        "eyJhbGciOiJIUzI1NiJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        "assinaturaABCDEFG123456"
    )
    limpo = sanitizar_dashboard_estado({
        "status": "ok",
        "health": {
            "llm": {
                "state": "online",
                "label": f"Online {sk_openrouter}",
                "provider": "ollama",
                "provider_label": f"Local {token_github}",
                "model": f"modelo-{jwt}",
                "freshness": "fresh", "observed_at": 2_000,
            },
            "microphone": {
                "state": "online", "label": sk_openrouter,
                "freshness": "fresh", "observed_at": 2_000,
            },
            "memory": {
                "state": "online", "label": token_github,
                "freshness": "fresh", "observed_at": 2_000,
            },
        },
        "context": {
            "project": f"Laylay {jwt}",
            "mode": f"Local {sk_openrouter}",
            "city": f"Boituva {token_github}",
            "game_active": True,
            "game_name": f"Minecraft {jwt}",
            "freshness": "fresh", "observed_at": 2_000,
        },
    })
    serializado = json.dumps(limpo, ensure_ascii=False)
    for segredo in (sk_openrouter, token_github, jwt):
        assert segredo not in serializado
    assert limpo["health"]["llm"]["label"] == "Indisponível"
    assert limpo["health"]["llm"]["provider_label"] == "—"
    assert limpo["health"]["llm"]["model"] == ""
    assert limpo["context"]["project"] == "Laylay"
    assert limpo["context"]["mode"] == "—"
    assert limpo["context"]["city"] == "—"
    assert limpo["context"]["game_name"] == "Jogo detectado"


def test_sanitizador_redige_tema_sensivel_e_exige_proveniencia_compativel() -> None:
    limpo = sanitizar_dashboard_estado({
        "status": "partial",
        "memory_recent": [
            {
                "kind": "reminder",
                "summary": "Tomar medicação às 21 horas",
                "source": "agenda_confirmed",
            },
            {
                "kind": "preference",
                "summary": "Prefere rock",
                "source": "agenda_confirmed",
            },
            {
                "kind": "task",
                "summary": "Arquivo criado",
                "source": "executor_confirmed",
            },
        ],
    })
    assert [item["kind"] for item in limpo["memory_recent"]] == [
        "reminder", "task",
    ]
    assert limpo["memory_recent"][0]["summary"] == "Você tem um lembrete"
    assert "medicação" not in json.dumps(limpo, ensure_ascii=False).casefold()


def test_sanitizador_exige_observacao_para_saude_contexto_e_metrica() -> None:
    limpo = sanitizar_dashboard_estado({
        "status": "ok",
        "health": {
            "llm": {
                "state": "online", "label": "Online",
                "freshness": "fresh", "observed_at": 0,
            },
        },
        "context": {
            "foo": "bar", "game_active": False,
            "freshness": "fresh", "observed_at": 0,
        },
        "system": {
            "cpu_percent": {
                "value": 42, "freshness": "unavailable", "observed_at": 1,
            },
        },
    })
    assert limpo["health"]["llm"]["state"] == "unavailable"
    assert limpo["health"]["llm"]["freshness"] == "unavailable"
    assert limpo["context"]["freshness"] == "unavailable"
    assert limpo["context"]["game_active"] is False
    assert limpo["system"]["cpu_percent"]["value"] is None
    assert limpo["status"] == "unavailable"


def _enviar(sock: socket.socket, mensagem: dict) -> None:
    sock.sendall((json.dumps(mensagem) + "\n").encode("utf-8"))


def _linha(sock: socket.socket, *, timeout: float = 1.0) -> dict:
    sock.settimeout(timeout)
    dados = b""
    while not dados.endswith(b"\n"):
        dados += sock.recv(1)
    return json.loads(dados.decode("utf-8"))


def _ate_tipo(sock: socket.socket, tipo: str, *, timeout: float = 1.5) -> dict:
    limite = time.monotonic() + timeout
    while time.monotonic() < limite:
        mensagem = _linha(sock, timeout=max(0.05, limite - time.monotonic()))
        if mensagem.get("type") == tipo:
            return mensagem
    raise AssertionError(f"mensagem {tipo} não chegou")


def test_ponte_envia_snapshot_e_dashboard_separado_sem_atrasar_ack() -> None:
    estado_dashboard = {"status": "partial", "sequence": 1}
    lento = {"ativo": False}

    def dashboard_getter():
        if lento["ativo"]:
            time.sleep(0.45)
        return dict(estado_dashboard)

    entradas: list[str] = []
    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda texto: entradas.append(texto) or True,
        historico_getter=list,
        estado_getter=dict,
        dashboard_getter=dashboard_getter,
        dashboard_interval_s=0.25,
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, {"type": "hello", "token": runtime.token})
            snapshot = _linha(cliente)
            assert snapshot["type"] == "snapshot"
            assert snapshot["dashboard"]["schema_version"] == 1
            lento["ativo"] = True
            time.sleep(0.27)
            inicio = time.monotonic()
            _enviar(cliente, {"type": "input_submit", "id": "p2", "text": "oi"})
            ack = _ate_tipo(cliente, "input_ack")
            assert time.monotonic() - inicio < 0.3
            assert ack["accepted"] is True
            assert entradas == ["oi"]
    finally:
        runtime.parar()


def test_ponte_coleta_dashboard_so_com_cliente_e_deduplica_snapshot() -> None:
    chamadas = 0

    def dashboard_getter():
        nonlocal chamadas
        chamadas += 1
        return {"status": "unavailable", "sequence": 0}

    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=list,
        estado_getter=dict,
        dashboard_getter=dashboard_getter,
        dashboard_interval_s=0.25,
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        time.sleep(0.55)
        assert chamadas == 0
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, {"type": "hello", "token": runtime.token})
            snapshot = _linha(cliente)
            assert snapshot["type"] == "snapshot"
            assert chamadas == 1

            tipos: list[str] = []
            limite = time.monotonic() + 0.45
            while time.monotonic() < limite:
                try:
                    mensagem = _linha(
                        cliente,
                        timeout=max(0.02, limite - time.monotonic()),
                    )
                except (socket.timeout, TimeoutError):
                    break
                tipos.append(str(mensagem.get("type") or ""))
            assert "dashboard_state" not in tipos

        time.sleep(0.4)
        chamadas_apos_desconectar = chamadas
        time.sleep(0.35)
        assert chamadas == chamadas_apos_desconectar
    finally:
        runtime.parar()


def test_ponte_limita_getter_travado_e_encerra_thread_do_dashboard() -> None:
    entrou = threading.Event()
    liberar = threading.Event()

    def dashboard_bloqueado():
        entrou.set()
        liberar.wait(5.0)
        return {"status": "ok"}

    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=list,
        estado_getter=dict,
        dashboard_getter=dashboard_bloqueado,
        dashboard_interval_s=0.25,
        dashboard_getter_timeout_s=0.05,
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, {"type": "hello", "token": runtime.token})
            snapshot = _linha(cliente)
            assert entrou.is_set()
            assert snapshot["type"] == "snapshot"
            assert snapshot["dashboard"]["status"] == "unavailable"
        runtime.parar(timeout_s=0.5)
        assert runtime.diagnostico()["dashboard_thread_viva"] is False
    finally:
        liberar.set()
        runtime.parar()


def test_dashboard_getter_com_erro_nao_derruba_handshake_nem_vaza_mensagem() -> None:
    logs: list[str] = []

    def falhar():
        raise RuntimeError("sk-nao-pode-aparecer")

    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=list,
        estado_getter=dict,
        dashboard_getter=falhar,
        log=logs.append,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, {"type": "hello", "token": runtime.token})
            snapshot = _linha(cliente)
            assert snapshot["type"] == "snapshot"
            assert snapshot["dashboard"]["status"] == "unavailable"
        assert runtime.diagnostico()["thread_viva"] is True
        assert "sk-nao-pode-aparecer" not in " ".join(logs)
    finally:
        runtime.parar()


def _criar_janela(monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_laylay_2 import JanelaLaylay

    class Worker(QObject):
        mensagem = Signal(dict)
        conectado = Signal(bool)
        falha = Signal(str)

        def enfileirar(self, _mensagem: dict) -> bool:
            return True

        def parar(self) -> None:
            return None

    app = QApplication.instance() or QApplication([])
    worker = Worker()
    janela = JanelaLaylay(worker, Path(__file__).parents[1])
    janela.resize(1700, 900)
    janela.show()
    app.processEvents()
    return app, worker, janela


def _dashboard_ui() -> dict:
    return sanitizar_dashboard_estado({
        "status": "ok",
        "generated_at": 2_000,
        "sequence": 2,
        "health": {
            "llm": {
                "state": "online", "label": "Online", "provider": "ollama",
                "provider_label": "Local", "model": "qwen3:4b",
                "freshness": "fresh", "observed_at": 2_000,
            },
            "microphone": {
                "state": "paused", "label": "Pausado no chat",
                "freshness": "fresh", "observed_at": 2_000,
            },
            "memory": {
                "state": "online", "label": "Ativa",
                "freshness": "fresh", "observed_at": 2_000,
            },
        },
        "context": {
            "project": "Laylay", "mode": "Local", "city": "Boituva",
            "interaction_mode": "chat", "game_active": True,
            "game_name": "Minecraft", "freshness": "fresh",
            "observed_at": 2_000,
        },
        "memory_recent": [{
            "kind": "preference", "summary": "Você prefere rock",
            "detail": "Confirmado por você", "source": "user_confirmed",
        }],
        "system": {
            "cpu_percent": {
                "value": 18, "freshness": "fresh", "observed_at": 2_000,
            },
            "ram_percent": {
                "value": 42, "freshness": "fresh", "observed_at": 2_000,
            },
            "disk_percent": {
                "value": 61, "freshness": "fresh", "observed_at": 2_000,
            },
            "temperature_c": {
                "value": None, "freshness": "unavailable", "observed_at": 0,
            },
            "uptime_seconds": {
                "value": 90_000, "freshness": "fresh", "observed_at": 2_000,
            },
        },
    })


def test_ui_aplica_dashboard_real_e_invalida_telemetria_na_queda(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    worker.conectado.emit(True)
    worker.mensagem.emit({
        "type": "snapshot", "messages": [], "events": [], "state": {},
        "dashboard": _dashboard_ui(),
    })
    app.processEvents()
    assert janela.chip_modelo.texto.text() == "Modelo: Local · Online"
    assert janela.chip_memoria.texto.text() == "Memória: Ativa"
    assert janela.painel_lateral.metricas["cpu"].text() == "18%"
    assert janela.painel_lateral.metricas["temperatura"].text() == "—"
    assert janela.painel_lateral.metricas["uptime"].text() == "1d 1h"
    assert janela.central_inteligente.contexto_valores["jogo"].text() == "Minecraft"
    assert not janela.central_inteligente.memoria_estado.isVisible()
    assert (
        janela.central_inteligente.memoria_linhas[0]["summary"].text()
        == "Você prefere rock"
    )

    worker.conectado.emit(False)
    app.processEvents()
    assert all(valor.text() == "—" for valor in janela.painel_lateral.metricas.values())
    assert janela.chip_memoria.texto.text() == "Memória: Reconectando"
    janela.close()


def test_ui_estado_rapido_nao_sobrescreve_microfone_degradado(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    worker.conectado.emit(True)
    dashboard = _dashboard_ui()
    dashboard["health"]["microphone"] = {
        "state": "degraded",
        "label": "Falha no ouvido",
        "freshness": "fresh",
        "observed_at": 2_000,
    }
    worker.mensagem.emit({"type": "dashboard_state", "dashboard": dashboard})
    app.processEvents()
    assert janela.chip_microfone.texto.text() == "Microfone: Falha no ouvido"

    worker.mensagem.emit({
        "type": "state",
        "activity": "idle",
        "activity_label": "Pronta",
        "emotion": "calma",
        "voice_available": True,
        "interaction_mode": "chat",
    })
    app.processEvents()
    assert janela.chip_microfone.texto.text() == "Microfone: Falha no ouvido"
    janela.close()


def test_ui_contexto_e_memoria_indisponiveis_nao_parecem_vazios_reais(
    monkeypatch,
) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    worker.conectado.emit(True)
    dashboard = sanitizar_dashboard_estado({
        "status": "partial",
        "health": {
            "memory": {
                "state": "unavailable",
                "label": "Indisponível",
                "freshness": "unavailable",
            },
        },
        "context": {
            "project": "Laylay",
            "mode": "Local",
            "city": "Boituva",
            "game_active": False,
            "freshness": "unavailable",
        },
        "memory_recent": [],
    })
    worker.mensagem.emit({"type": "dashboard_state", "dashboard": dashboard})
    app.processEvents()

    memoria = janela.central_inteligente.memoria_estado.text()
    jogo_central = janela.central_inteligente.contexto_valores["jogo"].text()
    jogo_lateral = janela.painel_lateral.jogo_estado.text()
    assert "indisponível" in memoria.casefold()
    assert "nenhuma memória" not in memoria.casefold()
    assert "indisponível" in jogo_central.casefold()
    assert "desativado" not in jogo_central.casefold()
    assert "indisponível" in jogo_lateral.casefold()
    assert "desativado" not in jogo_lateral.casefold()
    janela.close()


def test_cliente_dashboard_nao_importa_psutil_sqlite_ou_memoria_bruta() -> None:
    raiz = Path(__file__).parents[1]
    fontes = "\n".join(
        (raiz / caminho).read_text(encoding="utf-8")
        for caminho in (
            "cliente/terminal_laylay_2.py",
            "cliente/terminal_2/dashboard.py",
        )
    )
    assert "import psutil" not in fontes
    assert "memoria_sqlite" not in fontes.casefold()
    assert "memoria/" not in fontes.casefold()


def test_dashboard_participa_do_diagnostico_geral_sem_autorizar_execucao() -> None:
    runtime = DiagnosticoMenteRuntime(
        estado_getter=dict,
        saude_getter=dict,
        dashboard_getter=lambda: {
            "disponivel": True,
            "status": "partial",
            "sequence": 7,
            "coleta_em_andamento": False,
            "fontes_pendentes": 1,
            "falhas": 2,
            "autoriza_execucao": False,
        },
        falar=lambda *_args: None,
        log=lambda _texto: None,
    )
    retrato = runtime.snapshot()
    assert retrato["terminal_dashboard"]["sequence"] == 7
    assert retrato["terminal_dashboard"]["autoriza_execucao"] is False
    formatado = formatar_diagnostico_terminal(retrato)
    assert "Terminal 3 dashboard" in formatado
    assert "autoriza_execução=False" in formatado

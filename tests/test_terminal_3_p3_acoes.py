from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
from mente_laylay.integracao.desktop_bridge import (
    DesktopBridgeRuntime,
    ErroProtocoloDesktop,
    classificar_resultado_acao,
    sanitizar_dashboard_estado,
    validar_mensagem_cliente,
)
from mente_laylay.integracao.ponte_cooperacao_aplicacao import (
    PonteCooperacaoAplicacaoRuntime,
)


class _Psutil:
    @staticmethod
    def cpu_percent(*, interval=None):
        return 10.0

    @staticmethod
    def virtual_memory():
        return type("Mem", (), {"percent": 20.0})()

    @staticmethod
    def disk_usage(_raiz):
        return type("Disk", (), {"percent": 30.0})()

    @staticmethod
    def boot_time():
        return 900.0


def _dashboard(capacidade_getter=None) -> DashboardTerminalRuntime:
    return DashboardTerminalRuntime(
        configuracao_getter=lambda: {},
        llm_getter=lambda: {},
        interacao_getter=lambda: {},
        memoria_saude_getter=lambda: {},
        agenda_getter=lambda: [],
        aprendizados_getter=lambda **_kwargs: [],
        estado_mental_getter=lambda: {},
        contexto_jogo_getter=lambda: {},
        capacidade_getter=capacidade_getter,
        psutil_mod=_Psutil,
        log=lambda _texto: None,
    )


def test_raiz_liga_catalogo_vivo_ao_dashboard_e_nao_a_ponte_cooperativa() -> None:
    raiz = Path(__file__).resolve().parents[1] / "laylay.py"
    arvore = ast.parse(raiz.read_text(encoding="utf-8"))
    kwargs_por_destino: dict[str, set[str]] = {}
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Assign) or not isinstance(no.value, ast.Call):
            continue
        for alvo in no.targets:
            if isinstance(alvo, ast.Name):
                kwargs_por_destino[alvo.id] = {
                    item.arg for item in no.value.keywords if item.arg is not None
                }

    assert "capacidade_getter" in kwargs_por_destino[
        "_dashboard_terminal_runtime"
    ]
    assert "capacidade_getter" not in kwargs_por_destino[
        "_ponte_cooperacao_aplicacao_runtime"
    ]
    parametros_ponte = set(
        inspect.signature(PonteCooperacaoAplicacaoRuntime.__init__).parameters
    ) - {"self"}
    parametros_dashboard = set(
        inspect.signature(DashboardTerminalRuntime.__init__).parameters
    ) - {"self"}
    assert kwargs_por_destino["_ponte_cooperacao_aplicacao_runtime"] <= parametros_ponte
    assert kwargs_por_destino["_dashboard_terminal_runtime"] <= parametros_dashboard


def test_catalogo_rapido_deriva_disponibilidade_do_mapa_vivo() -> None:
    runtime = _dashboard(
        lambda intent: {
            "intent": intent,
            "disponivel": intent != "ORGANIZAR_DESKTOP",
            "estado": (
                "indisponivel" if intent == "ORGANIZAR_DESKTOP"
                else "degradado" if intent == "BRIEFING_REPEAT"
                else "disponivel"
            ),
            "motivo": "estado observado",
        },
    )

    acoes = {item["id"]: item for item in runtime._acoes_rapidas()}

    assert acoes["open_vscode"]["state"] == "available"
    assert acoes["organize_desktop"]["state"] == "unavailable"
    assert acoes["briefing"]["state"] == "degraded"
    assert acoes["search"]["state"] == "requires_input"
    assert acoes["focus_mode"]["state"] == "unavailable"
    assert acoes["activate_routine"]["state"] == "unavailable"


def test_dashboard_publica_so_estado_da_acao_sem_comando_privado() -> None:
    dashboard = sanitizar_dashboard_estado({
        "schema_version": 1,
        "quick_actions": [
            {
                "id": "open_vscode", "state": "available",
                "reason": "operacional", "request": "segredo",
                "params": {"token": "sk-or-v1-nao-pode-vazar"},
            },
            {"id": "acao_injetada", "state": "available"},
        ],
    })

    assert dashboard["quick_actions"] == [{
        "id": "open_vscode", "state": "available", "reason": "operacional",
    }]
    assert "segredo" not in str(dashboard)
    assert "sk-or-v1" not in str(dashboard)


def test_protocolo_rejeita_acao_rapida_forjada() -> None:
    with pytest.raises(ErroProtocoloDesktop, match="ação rápida inválida"):
        validar_mensagem_cliente(
            {
                "type": "input_submit", "id": "1", "text": "faz isso",
                "kind": "quick_action", "action": "apagar_tudo",
            },
            token="token", autenticado=True,
        )


@pytest.mark.parametrize(
    ("comandos", "estado"),
    [
        ([{"intent": "APP_OPEN", "executou": True, "confirmado": True}], "confirmed"),
        ([{"intent": "APP_OPEN", "executou": True, "confirmado": None}], "partial"),
        ([{"intent": "APP_OPEN", "executou": False, "confirmado": False}], "failed"),
        ([{"intent": "APP_OPEN", "status": "aguardando_confirmacao"}], "awaiting_confirmation"),
    ],
)
def test_resultado_do_botao_nunca_eleva_evidencia(
    comandos: list[dict], estado: str,
) -> None:
    resultado = classificar_resultado_acao(
        {"comandos": comandos}, acao_id="open_vscode",
    )
    assert resultado["state"] == estado


def test_fala_final_correlaciona_pelo_texto_do_turno_e_publica_resultado() -> None:
    plano = {
        "texto_usuario": "organiza o desktop automaticamente",
        "comandos": [{
            "intent": "ORGANIZAR_DESKTOP",
            "executou": True,
            "confirmado": True,
        }],
    }
    bridge = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=lambda: [],
        estado_getter=lambda: {},
        resultado_acao_getter=lambda: plano,
        log=lambda _texto: None,
    )
    publicados: list[dict] = []
    bridge._publicar = lambda mensagem: publicados.append(dict(mensagem)) or True
    bridge._entradas_pendentes.extend((
        {"id": "chat-antes", "text": "oi", "kind": "chat", "action": "", "state": "received"},
        {
            "id": "acao-certa", "text": plano["texto_usuario"],
            "kind": "quick_action", "action": "organize_desktop",
            "state": "executing",
        },
    ))

    assert bridge.publicar_fala_final("Desktop organizado.") is True

    assert publicados[0]["type"] == "assistant_message"
    assert publicados[0]["id"] == "acao-certa"
    assert publicados[1]["type"] == "action_state"
    assert publicados[1]["state"] == "confirmed"
    assert [item["id"] for item in bridge._entradas_pendentes] == ["chat-antes"]


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

        def __init__(self) -> None:
            super().__init__()
            self.enviadas: list[dict] = []

        def enfileirar(self, mensagem: dict) -> bool:
            self.enviadas.append(dict(mensagem))
            return True

        def parar(self) -> None:
            return None

    app = QApplication.instance() or QApplication([])
    worker = Worker()
    janela = JanelaLaylay(worker, Path(__file__).parents[1])
    janela.show()
    worker.conectado.emit(True)
    app.processEvents()
    return app, worker, janela


def test_clique_envia_metadado_sem_contornar_a_linguagem_natural(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)

    janela.central_inteligente._acoes_por_id["open_vscode"].click()
    app.processEvents()

    enviado = next(item for item in worker.enviadas if item["type"] == "input_submit")
    assert enviado["text"] == "abre o Visual Studio Code"
    assert enviado["kind"] == "quick_action"
    assert enviado["action"] == "open_vscode"
    assert janela.central_inteligente._acoes_por_id["open_vscode"].property(
        "actionState",
    ) == "sending"
    janela.close()


def test_ui_nao_apaga_outro_turno_e_atividade_exige_confirmacao(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    janela.enviar_texto("primeiro")
    janela.enviar_texto("segundo")
    ids = [
        item["id"] for item in worker.enviadas if item["type"] == "input_submit"
    ]

    worker.mensagem.emit({
        "type": "assistant_message", "id": ids[0], "text": "Resposta um",
        "emotion": "calma",
    })
    app.processEvents()

    assert ids[0] not in janela._envios
    assert ids[1] in janela._envios
    assert janela.central_inteligente.atividade_itens.text() == "Tudo quieto nesta sessão."

    worker.mensagem.emit({
        "type": "action_state", "id": "acao", "action": "briefing",
        "state": "partial", "summary": "Sem confirmação completa",
    })
    app.processEvents()
    assert not janela.central_inteligente._eventos

    worker.mensagem.emit({
        "type": "action_state", "id": "acao", "action": "briefing",
        "state": "confirmed", "summary": "Briefing recuperado",
    })
    app.processEvents()
    atividade = janela.central_inteligente.atividade_linhas[0]
    assert atividade["text"].text() == "Ação confirmada"
    assert atividade["widget"].isHidden() is False
    assert janela.central_inteligente.atividade_estado.isHidden()
    janela.close()

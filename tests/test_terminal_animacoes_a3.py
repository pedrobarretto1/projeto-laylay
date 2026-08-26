from __future__ import annotations

from pathlib import Path
import time

import pytest


def _janela(monkeypatch, *, reduzir_movimento: bool = False):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv(
        "LAYLAY_REDUZIR_MOVIMENTO",
        "1" if reduzir_movimento else "0",
    )
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_laylay_2 import JanelaLaylay

    class Worker(QObject):
        mensagem = Signal(dict)
        conectado = Signal(bool)
        falha = Signal(str)

        def __init__(self):
            super().__init__()
            self.enviadas: list[dict] = []

        def enfileirar(self, mensagem):
            self.enviadas.append(dict(mensagem))
            return True

        def parar(self):
            return None

    app = QApplication.instance() or QApplication([])
    worker = Worker()
    janela = JanelaLaylay(worker, Path(__file__).parents[1])
    janela.show()
    worker.conectado.emit(True)
    _processar_por(app, 0.9)
    return app, worker, janela


def _processar_por(app, segundos: float) -> None:
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        app.processEvents()
        time.sleep(0.005)


def test_chip_pulsa_so_quando_estado_observado_muda(monkeypatch) -> None:
    app, _worker, janela = _janela(monkeypatch)
    chip = janela.chip_modelo
    chip.definir("Local · Pronto", estado="pending")
    app.processEvents()
    geometria = chip.geometry()

    chip.definir("Local · Pronto", estado="online")
    app.processEvents()

    assert chip.graphicsEffect() is not None
    assert id(chip) in janela._micro_animacoes
    assert chip.geometry() == geometria

    _processar_por(app, 0.38)
    assert chip.graphicsEffect() is None
    assert id(chip) not in janela._micro_animacoes

    chip.definir("Local · Pronto", estado="online")
    app.processEvents()
    assert chip.graphicsEffect() is None
    janela.close()


def test_atividade_e_modo_animam_sem_mover_layout(monkeypatch) -> None:
    app, _worker, janela = _janela(monkeypatch)
    janela._atualizar_estado({
        "activity": "idle",
        "activity_label": "Pronta",
        "emotion": "calma",
        "interaction_mode": "chat",
        "voice_available": True,
    })
    app.processEvents()

    janela._atualizar_estado({
        "activity": "thinking",
        "activity_label": "Pensando",
        "emotion": "curiosa",
        "interaction_mode": "voice",
        "voice_available": True,
    })
    app.processEvents()

    assert janela.status.graphicsEffect() is not None
    assert janela.alternador.graphicsEffect() is not None
    geometria_status = janela.status.geometry()
    geometria_modo = janela.alternador.geometry()

    _processar_por(app, 0.12)
    assert janela.status.geometry() == geometria_status
    assert janela.alternador.geometry() == geometria_modo

    _processar_por(app, 0.3)
    assert janela.status.graphicsEffect() is None
    assert janela.alternador.graphicsEffect() is None
    janela.close()


def test_envio_da_retorno_visual_sem_atrasar_a_fila(monkeypatch) -> None:
    app, worker, janela = _janela(monkeypatch)
    janela.composer.editor.setPlainText("Oi, Laylay")
    janela.composer.botao.click()
    app.processEvents()

    assert worker.enviadas[-1]["type"] == "input_submit"
    assert janela.composer.botao.graphicsEffect() is not None

    _processar_por(app, 0.3)
    assert janela.composer.botao.graphicsEffect() is None
    janela.close()


def test_a3_respeita_movimento_reduzido(monkeypatch) -> None:
    app, _worker, janela = _janela(monkeypatch, reduzir_movimento=True)
    janela.chip_memoria.definir("Ativa", estado="online")
    janela._atualizar_estado({
        "activity": "speaking",
        "activity_label": "Falando",
        "interaction_mode": "chat",
        "voice_available": True,
    })
    app.processEvents()

    assert janela._micro_animacoes == {}
    assert janela.chip_memoria.graphicsEffect() is None
    assert janela.status.graphicsEffect() is None
    assert janela.alternador.graphicsEffect() is None
    janela.close()

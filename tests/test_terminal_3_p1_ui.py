from __future__ import annotations

from pathlib import Path

import pytest


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
    for _ in range(4):
        app.processEvents()
    return app, worker, janela


def _processar(app, ciclos: int = 5) -> None:
    for _ in range(ciclos):
        app.processEvents()


def test_p1_shell_monta_dashboard_sem_inventar_estado(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    janela.resize(1700, 900)
    _processar(app)

    assert janela._pagina_principal == "inicio"
    assert janela.paginas.currentIndex() == 0
    assert janela.central_inteligente.isVisible()
    assert janela.painel_lateral.isVisible()
    assert set(janela._nav) == {
        "inicio", "conversa", "automacao", "musica", "memoria", "sistema",
        "configuracoes",
    }
    assert janela.chip_memoria.texto.text() == "Memória: Aguardando"
    assert all(valor.text() == "—" for valor in janela.painel_lateral.metricas.values())
    assert worker.enviadas == []
    assert all(not botao.isEnabled() for botao in janela.central_inteligente.acoes.values())
    janela.close()


def test_p1_inicio_e_conversa_compartilham_o_mesmo_feed(monkeypatch) -> None:
    app, _worker, janela = _criar_janela(monkeypatch)
    janela.resize(1700, 900)
    mensagem = janela.adicionar_mensagem(
        "assistant", "A conversa real continua aqui.", animar=False,
    )
    _processar(app)

    janela.selecionar_pagina("conversa")
    _processar(app)
    assert janela.paginas.currentIndex() == 0
    assert not janela.central_inteligente.isVisible()
    assert not janela.painel_lateral.isVisible()
    assert mensagem in janela.feed.findChildren(type(mensagem))

    janela.selecionar_pagina("inicio")
    _processar(app)
    assert janela.central_inteligente.isVisible()
    assert janela.painel_lateral.isVisible()
    assert mensagem in janela.feed.findChildren(type(mensagem))
    janela.close()


def test_p1_dashboard_recolhe_colunas_sem_quebrar_chat(monkeypatch) -> None:
    app, _worker, janela = _criar_janela(monkeypatch)

    janela.resize(1700, 900)
    _processar(app)
    assert janela.central_inteligente.isVisible()
    assert janela.painel_lateral.isVisible()

    janela.resize(1500, 820)
    _processar(app)
    assert janela.central_inteligente.isVisible()
    assert not janela.painel_lateral.isVisible()

    janela.resize(1320, 820)
    _processar(app)
    assert not janela.central_inteligente.isVisible()
    assert not janela.painel_lateral.isVisible()

    janela.resize(375, 667)
    _processar(app)
    assert janela.composer.isVisible()
    assert janela.scroll.horizontalScrollBar().maximum() == 0
    assert not janela.sidebar.isVisible()
    janela.close()


def test_p1_status_usa_apenas_snapshot_observado(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    worker.conectado.emit(True)
    worker.mensagem.emit({
        "type": "snapshot",
        "messages": [],
        "events": [],
        "state": {
            "activity": "idle",
            "activity_label": "Pronta",
            "emotion": "calma",
            "voice_available": True,
            "interaction_mode": "chat",
        },
        "settings": {
            "provider": "openrouter",
            "model": "qwen/qwen3-32b",
            "models_by_provider": {},
            "base_url": "https://openrouter.ai/api/v1",
            "api_key_configured": True,
            "restart_required": False,
            "mascot_enabled": False,
        },
    })
    _processar(app)

    assert janela.chip_modelo.texto.text() == "Modelo: OpenRouter configurado"
    assert janela.chip_microfone.texto.text() == "Microfone: Pausado no chat"
    assert janela.chip_memoria.texto.text() == "Memória: Aguardando"
    assert "Ativa" not in janela.chip_memoria.texto.text()
    assert janela.central_inteligente.contexto_valores["modo"].text() == "OpenRouter"
    janela.close()


def test_p1_acoes_disponiveis_entram_pela_conversa_canonica(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    worker.conectado.emit(True)
    _processar(app)

    botoes = list(janela.central_inteligente.acoes.values())
    assert all(botao.isEnabled() for botao in botoes[:3])
    assert all(not botao.isEnabled() for botao in botoes[3:])
    botoes[0].click()
    _processar(app)

    enviados = [item for item in worker.enviadas if item.get("type") == "input_submit"]
    assert len(enviados) == 1
    assert enviados[0]["text"] == "abre o Visual Studio Code"
    janela.close()


def test_p1_navegacao_preserva_indices_legados(monkeypatch) -> None:
    app, _worker, janela = _criar_janela(monkeypatch)
    for nome, indice in (
        ("inicio", 0),
        ("conversa", 0),
        ("diagnostico", 2),
        ("sistema", 7),
        ("configuracoes", 3),
        ("automacao", 4),
        ("musica", 5),
        ("memoria", 6),
    ):
        janela.selecionar_pagina(nome)
        _processar(app, 2)
        assert janela.paginas.currentIndex() == indice
    janela.close()

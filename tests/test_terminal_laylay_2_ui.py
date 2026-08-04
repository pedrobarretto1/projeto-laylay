from __future__ import annotations

from pathlib import Path

import pytest


def _criar_janela_qt(monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_laylay_2 import JanelaLaylay

    class Worker(QObject):
        mensagem = Signal(dict)
        conectado = Signal(bool)
        falha = Signal(str)

        def __init__(self):
            super().__init__()
            self.enviadas = []

        def enfileirar(self, mensagem):
            self.enviadas.append(mensagem)
            return True

        def parar(self):
            return None

    app = QApplication.instance() or QApplication([])
    worker = Worker()
    janela = JanelaLaylay(worker, Path(__file__).parents[1])
    janela.resize(1000, 700)
    janela.show()
    app.processEvents()
    return app, worker, janela


def _processar_layout(app, ciclos: int = 5) -> None:
    for _ in range(ciclos):
        app.processEvents()


def test_smoke_terminal_21_chat_voz_e_settings(monkeypatch) -> None:
    app, worker, janela = _criar_janela_qt(monkeypatch)
    worker.conectado.emit(True)
    worker.mensagem.emit({
        "type": "snapshot", "messages": [], "events": [],
        "state": {
            "activity": "idle", "activity_label": "Pronta", "emotion": "calma",
            "voice_available": True, "interaction_mode": "chat",
        },
        "settings": {
            "provider": "ollama", "model": "qwen3:4b",
            "models_by_provider": {
                "ollama": "qwen3:4b", "portatil": "qwen-portatil",
                "openrouter": "qwen/qwen3-32b",
            },
            "base_url": "http://localhost:11434/v1",
            "api_key_configured": False, "restart_required": False,
            "mascot_enabled": False,
        },
    })
    app.processEvents()
    assert janela._modo == "chat"
    assert janela.configuracoes.modelo.text() == "qwen3:4b"
    assert not janela.configuracoes.mostrar_mascote.isChecked()
    janela.configuracoes.providers["openrouter"].click()
    assert janela.configuracoes.modelo.text() == "qwen/qwen3-32b"
    janela.configuracoes.modelo.setText("qwen/qwen3-30b-a3b")
    janela.configuracoes.providers["ollama"].click()
    assert janela.configuracoes.modelo.text() == "qwen3:4b"
    janela.solicitar_modo("voice")
    app.processEvents()
    assert any(item.get("type") == "mode_set" for item in worker.enviadas)
    janela.salvar_configuracoes({
        "provider": "ollama", "model": "qwen3:4b",
        "api_key_action": "preserve", "api_key": "",
    })
    app.processEvents()
    assert any(item.get("type") == "settings_update" for item in worker.enviadas)
    janela.configuracoes.mostrar_mascote.setChecked(True)
    janela.configuracoes._salvar()
    assert worker.enviadas[-1]["settings"]["mascot_enabled"] is True
    assert janela.configuracoes.reiniciar_botao.isEnabled()
    janela.configuracoes.reiniciar_botao.click()
    assert worker.enviadas[-1]["type"] == "restart_request"
    assert not janela.configuracoes.reiniciar_botao.isEnabled()
    janela.receber({
        "type": "restart_result", "accepted": False,
        "message": "reinício recusado no teste",
    })
    assert janela.configuracoes.reiniciar_botao.isEnabled()
    janela.resize(768, 700)
    app.processEvents()
    assert janela.width() == 768
    assert janela.sidebar.width() == 72
    janela.resize(375, 667)
    app.processEvents()
    assert janela.width() == 375
    assert janela.menu_compacto.isVisible()
    assert not janela.sidebar.isVisible()
    janela._modo_pendente = True
    janela.receber({"type": "error", "message": "troca recusada"})
    assert janela._modo_pendente is False
    janela.close()


def test_recente_abre_conversa_e_atividade_recebe_eventos(monkeypatch) -> None:
    app, worker, janela = _criar_janela_qt(monkeypatch)
    janela.selecionar_pagina("diagnostico")
    assert janela.paginas.currentIndex() == 2
    janela.conversa_atual.click()
    assert janela.paginas.currentIndex() == 0

    worker.conectado.emit(True)
    worker.mensagem.emit({
        "type": "state", "activity": "thinking", "activity_label": "Pensando",
        "emotion": "curiosa", "voice_available": False, "interaction_mode": "chat",
    })
    worker.mensagem.emit({
        "type": "assistant_message", "text": "Pronto.", "emotion": "feliz",
    })
    _processar_layout(app)
    atividade = janela.eventos.toPlainText()
    assert "Mente conectada" in atividade
    assert "Pensando" in atividade
    assert "Resposta entregue" in atividade
    janela.close()


def test_baloes_ampliados_respeitam_limites_e_viewport_estreito(monkeypatch) -> None:
    app, _worker, janela = _criar_janela_qt(monkeypatch)
    from cliente.terminal_laylay_2 import (
        LARGURA_MAXIMA_MENSAGEM_LAYLAY,
        LARGURA_MAXIMA_MENSAGEM_USUARIO,
    )

    janela.resize(1320, 820)
    laylay = janela.adicionar_mensagem("assistant", "Resposta longa da Laylay. " * 30, animar=False)
    usuario = janela.adicionar_mensagem("user", "Mensagem longa do usuário. " * 30, animar=False)
    _processar_layout(app)

    assert laylay is not None
    assert usuario is not None
    assert laylay.maximumWidth() == LARGURA_MAXIMA_MENSAGEM_LAYLAY == 860
    assert usuario.maximumWidth() == LARGURA_MAXIMA_MENSAGEM_USUARIO == 760
    assert laylay.width() > 740
    assert usuario.width() > 650

    janela.resize(375, 667)
    _processar_layout(app)
    largura_viewport = janela.scroll.viewport().width()
    assert laylay.width() <= largura_viewport
    assert usuario.width() <= largura_viewport
    assert janela.scroll.horizontalScrollBar().maximum() == 0
    janela.close()


def test_indicador_pensando_tem_ciclo_efemero_sem_duplicacao(monkeypatch) -> None:
    app, worker, janela = _criar_janela_qt(monkeypatch)
    from cliente.terminal_laylay_2 import IndicadorPensando
    from PySide6.QtTest import QTest

    janela.enviar_texto("Primeiro pedido")
    _processar_layout(app)
    indicador = janela._indicador_pensando
    assert isinstance(indicador, IndicadorPensando)
    assert len(janela.feed.findChildren(IndicadorPensando)) == 1
    pontos_antes = indicador.pontos.text()
    QTest.qWait(360)
    app.processEvents()
    assert indicador.pontos.text() != pontos_antes

    # Estados e confirmações positivas não criam outro indicador nem o retiram
    # enquanto a resposta final ainda não chegou.
    janela.receber({"type": "state", "activity": "thinking"})
    janela.receber({
        "type": "input_ack", "id": worker.enviadas[-1]["id"], "accepted": True,
    })
    assert janela._indicador_pensando is indicador
    assert len(janela.feed.findChildren(IndicadorPensando)) == 1

    janela.receber({"type": "assistant_message", "text": "Resposta pronta."})
    _processar_layout(app)
    assert janela._indicador_pensando is None

    janela.enviar_texto("Pedido recusado")
    pedido_recusado = worker.enviadas[-1]["id"]
    assert janela._indicador_pensando is not None
    janela.receber({
        "type": "input_ack", "id": pedido_recusado,
        "accepted": False, "message": "recusado",
    })
    assert janela._indicador_pensando is None

    janela.enviar_texto("Pedido durante queda")
    assert janela._indicador_pensando is not None
    janela.estado_conexao(False)
    assert janela._indicador_pensando is None
    janela.close()


def test_historico_longo_mantem_todas_as_mensagens_rolaveis(monkeypatch) -> None:
    app, _worker, janela = _criar_janela_qt(monkeypatch)
    from cliente.terminal_laylay_2 import MensagemWidget

    for indice in range(64):
        janela.adicionar_mensagem(
            "assistant" if indice % 2 == 0 else "user",
            f"Mensagem {indice:02d}: "
            + "conteúdo longo para validar altura, quebra de linha e rolagem estável. "
            * (1 + indice % 3),
            animar=False,
        )
    _processar_layout(app)

    mensagens = janela.feed.findChildren(MensagemWidget)
    barra = janela.scroll.verticalScrollBar()
    assert len(mensagens) == 64
    assert barra.maximum() > janela.scroll.viewport().height()
    assert mensagens[-1].geometry().bottom() <= janela.feed.height()
    assert all(
        mensagem.height() >= mensagem.minimumSizeHint().height()
        for mensagem in mensagens
    )

    for posicao, esperado in (
        (0, mensagens[0]),
        (barra.maximum() // 2, mensagens[len(mensagens) // 2]),
        (barra.maximum(), mensagens[-1]),
        (barra.maximum() // 3, mensagens[len(mensagens) // 3]),
        (barra.maximum(), mensagens[-1]),
    ):
        barra.setValue(posicao)
        _processar_layout(app, 2)
        topo = esperado.mapTo(janela.scroll.viewport(), esperado.rect().topLeft()).y()
        fundo = topo + esperado.height()
        assert fundo >= 0
        assert topo <= janela.scroll.viewport().height()

    janela.close()


def test_auto_scroll_respeita_leitura_e_segue_mensagem_do_usuario(monkeypatch) -> None:
    app, _worker, janela = _criar_janela_qt(monkeypatch)

    for indice in range(36):
        janela.adicionar_mensagem(
            "assistant",
            f"Trecho do histórico {indice}: " + "texto suficiente para ocupar espaço. " * 2,
            animar=False,
        )
    _processar_layout(app)
    barra = janela.scroll.verticalScrollBar()

    barra.setValue(barra.maximum() // 2)
    _processar_layout(app, 2)
    posicao_de_leitura = barra.value()
    janela.adicionar_mensagem("assistant", "Uma resposta nova chegou.", animar=False)
    _processar_layout(app)
    assert barra.value() == posicao_de_leitura

    barra.setValue(barra.maximum())
    janela.adicionar_mensagem("assistant", "Outra resposta, agora acompanhando o fim.", animar=False)
    _processar_layout(app)
    assert barra.value() == barra.maximum()

    barra.setValue(0)
    janela.adicionar_mensagem("user", "Minha mensagem deve voltar ao presente.", animar=False)
    _processar_layout(app)
    assert barra.value() == barra.maximum()
    janela.close()


def test_animacao_de_entrada_nao_fica_presa_ao_historico(monkeypatch) -> None:
    app, _worker, janela = _criar_janela_qt(monkeypatch)
    from PySide6.QtTest import QTest

    mensagem = janela.adicionar_mensagem("assistant", "Uma mensagem animada normal.")
    assert mensagem is not None
    assert mensagem.graphicsEffect() is not None

    QTest.qWait(220)
    app.processEvents()
    assert mensagem.graphicsEffect() is None
    assert not janela._animacoes
    janela.close()

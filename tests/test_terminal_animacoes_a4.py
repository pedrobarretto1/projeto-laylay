from __future__ import annotations

from pathlib import Path
import sys
import time

import pytest


def _processar_por(app, segundos: float) -> None:
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        app.processEvents()
        time.sleep(0.005)


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

        def enfileirar(self, _mensagem):
            return True

        def parar(self):
            return None

    app = QApplication.instance() or QApplication([])
    worker = Worker()
    janela = JanelaLaylay(worker, Path(__file__).parents[1])
    janela.resize(1000, 700)
    janela.show()
    worker.conectado.emit(True)
    _processar_por(app, 0.9)
    return app, janela


def _encher_historico(janela, app) -> None:
    for indice in range(34):
        janela.adicionar_mensagem(
            "assistant",
            f"Histórico {indice}: " + "conteúdo para ocupar espaço. " * 2,
            animar=False,
        )
    _processar_por(app, 0.3)


def test_presenca_pulsa_apenas_durante_atividade_viva(monkeypatch) -> None:
    app, janela = _janela(monkeypatch)
    janela._atualizar_estado({
        "activity": "thinking",
        "activity_label": "Pensando",
        "emotion": "curiosa",
        "interaction_mode": "chat",
        "voice_available": True,
    })
    app.processEvents()

    assert janela._pulso_presenca is not None
    assert janela._pulso_presenca.loopCount() == -1
    assert janela.ponto.graphicsEffect() is janela._efeito_presenca
    opacidade = janela._efeito_presenca.opacity()
    _processar_por(app, 0.25)
    assert janela._efeito_presenca.opacity() != opacidade

    janela._atualizar_estado({
        "activity": "idle",
        "activity_label": "Pronta",
        "emotion": "calma",
        "interaction_mode": "chat",
        "voice_available": True,
    })
    app.processEvents()
    assert janela._pulso_presenca is None
    assert janela.ponto.graphicsEffect() is None
    janela.close()


def test_rolagem_e_suave_no_presente_e_nao_interrompe_leitura(monkeypatch) -> None:
    app, janela = _janela(monkeypatch)
    _encher_historico(janela, app)
    barra = janela.scroll.verticalScrollBar()
    assert barra.maximum() > 0

    janela._encerrar_rolagem_suave()
    barra.setValue(barra.maximum() // 2)
    posicao_leitura = barra.value()
    janela.adicionar_mensagem(
        "assistant", "Nova resposta enquanto estou lendo.", animar=False,
    )
    app.processEvents()
    assert janela._animacao_scroll is None
    assert barra.value() == posicao_leitura

    barra.setValue(barra.maximum())
    janela.adicionar_mensagem(
        "assistant", "Nova resposta acompanhada no presente.", animar=False,
    )
    app.processEvents()
    assert janela._animacao_scroll is not None
    _processar_por(app, 0.25)
    assert janela._animacao_scroll is None
    assert barra.value() == barra.maximum()
    janela.close()


def test_controles_recebem_feedback_sem_alterar_geometria(monkeypatch) -> None:
    app, janela = _janela(monkeypatch)
    botao = janela._nav["musica"]
    geometria = botao.geometry()
    botao.click()
    app.processEvents()

    assert bool(botao.property("a4FeedbackLigado")) is True
    assert botao.graphicsEffect() is not None
    assert botao.geometry() == geometria
    _processar_por(app, 0.27)
    assert botao.graphicsEffect() is None
    janela.close()


def test_feedback_e_cancelado_quando_lista_de_chats_recria_botao(
    monkeypatch,
) -> None:
    app, janela = _janela(monkeypatch)
    from PySide6.QtCore import qInstallMessageHandler

    conversa_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    retrato = {
        "available": True,
        "active_id": conversa_id,
        "items": [{
            "id": conversa_id,
            "title": "Conversa animada",
            "status": "active",
            "pinned": False,
            "active": True,
        }],
        "messages": [],
    }
    janela.receber({
        "type": "snapshot",
        "messages": [],
        "events": [],
        "state": {},
        "conversations": retrato,
    })
    app.processEvents()
    botao_antigo = janela._botoes_conversas[conversa_id]
    identificador = id(botao_antigo)
    erros: list[BaseException] = []
    mensagens_qt: list[str] = []
    excepthook_anterior = sys.excepthook
    handler_anterior = qInstallMessageHandler(
        lambda _tipo, _contexto, mensagem: mensagens_qt.append(mensagem)
    )
    sys.excepthook = lambda _tipo, erro, _trace: erros.append(erro)
    try:
        botao_antigo.click()
        assert identificador in janela._micro_animacoes
        janela._renderizar_lista_conversas()
        app.processEvents()
        assert identificador not in janela._micro_animacoes
        janela.adicionar_mensagem("user", "Mensagem durante a atualização.")
        _processar_por(app, 0.30)
        janela._mostrar_indicador_pensando()
        _processar_por(app, 0.05)
        janela._remover_indicador_pensando(animar=True)
        janela.adicionar_mensagem("assistant", "Resposta depois da atualização.")
        _processar_por(app, 0.35)
    finally:
        sys.excepthook = excepthook_anterior
        qInstallMessageHandler(handler_anterior)

    assert erros == []
    assert not any(
        mensagem.startswith(("QPainter::", "QWidgetEffectSourcePrivate::"))
        for mensagem in mensagens_qt
    ), mensagens_qt
    janela.close()


def test_a4_desliga_movimento_continuo_e_rolagem_animada(monkeypatch) -> None:
    app, janela = _janela(monkeypatch, reduzir_movimento=True)
    janela._atualizar_estado({
        "activity": "speaking",
        "activity_label": "Falando",
        "interaction_mode": "voice",
        "voice_available": True,
    })
    _encher_historico(janela, app)
    barra = janela.scroll.verticalScrollBar()
    barra.setValue(0)
    janela._rolar_ao_final()
    app.processEvents()

    assert janela._pulso_presenca is None
    assert janela.ponto.graphicsEffect() is None
    assert janela._animacao_scroll is None
    assert barra.value() == barra.maximum()
    janela.close()


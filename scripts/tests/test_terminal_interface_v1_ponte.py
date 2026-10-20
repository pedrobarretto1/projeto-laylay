"""Três superfícies, uma conexão autenticada e nenhuma autoridade nova."""
from pathlib import Path
import time

import pytest


def test_interface_v1_preserva_transporte_resposta_e_recusa_nos_tres_modos(monkeypatch, tmp_path):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
    from PySide6.QtCore import QSettings, QThread
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    import cliente.terminal_laylay_2 as terminal
    from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime

    monkeypatch.setattr(terminal, "QSettings", lambda *_: QSettings(
        str(tmp_path / "preferencias.ini"), QSettings.IniFormat,
    ))
    app = QApplication.instance() or QApplication([])
    entradas, mensagens, envios = [], [], []
    ponte = DesktopBridgeRuntime(
        enviar_entrada=entradas.append, historico_getter=lambda: [],
        estado_getter=lambda: {"activity": "idle", "activity_label": "Pronta", "interaction_mode": "chat"},
        log=lambda _: None,
    )
    ponte.iniciar()
    worker = terminal.PonteWorker(*ponte.endereco, ponte.token, session_id=ponte.session_id)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.executar)
    worker.terminou.connect(thread.quit)
    worker.mensagem.connect(mensagens.append)
    janela = terminal.JanelaLaylay(worker, Path(__file__).parents[2])
    janela.enviar_json.connect(envios.append)

    def aguardar(condicao):
        limite = time.monotonic() + 5
        while not condicao() and time.monotonic() < limite:
            QTest.qWait(20)
        assert condicao(), "A composição real do cliente/ponte não alcançou o estado esperado"

    try:
        janela.show()
        thread.start()
        aguardar(lambda: janela._conectado and any(m.get("type") == "snapshot" for m in mensagens))
        feed, composer = janela.feed, janela.composer
        composer.editor.setPlainText("Rascunho preservado entre as três formas")
        antes = list(envios)
        for modo in ("painel", "ilha", "completa", "painel"):
            janela.apresentacao.definir_modo(modo)
            QTest.qWait(30)
            assert janela.feed is feed and janela.composer is composer
            assert janela.worker is worker and thread.isRunning()
            assert composer.editor.toPlainText() == "Rascunho preservado entre as três formas"
            assert janela._modo == "chat"
        assert envios == antes
        assert entradas == []

        # Um envio canônico, não uma resposta local implementada pela interface.
        janela.enviar_texto("Verificação de conversa nas três formas")
        aguardar(lambda: entradas == ["Verificação de conversa nas três formas"])
        aguardar(lambda: any(m.get("type") == "input_ack" and m.get("accepted") for m in mensagens))
        janela.apresentacao.definir_modo("ilha")
        assert ponte.publicar_fala_final("Resposta publicada pela ponte de validação.")
        aguardar(lambda: not janela._envios)
        janela.apresentacao.definir_modo("completa")
        assert any("Resposta publicada pela ponte de validação." in label.text()
                   for label in janela.feed.findChildren(terminal.QLabel))
        assert entradas == ["Verificação de conversa nas três formas"]

        # Recusa é observável; a UI não inventa sucesso nem autoriza a operação.
        ponte.enviar_entrada = lambda _: False
        janela.enviar_texto("Esta entrada deve ser recusada pelo destino")
        aguardar(lambda: any(m.get("type") == "input_ack" and not m.get("accepted") for m in mensagens))
        # A lista de recebimento está na thread do socket; a projeção da UI
        # passa pela fila Qt e precisa ser observada separadamente.
        aguardar(lambda: not janela._envios)
        # O balão falho permanece no feed com tentativa explícita disponível;
        # deixa o registro de pendências e não pode parecer entregue.
        falhas = [item for item in janela.feed.findChildren(terminal.MensagemWidget)
                  if item.status.property("delivery") == "failed"]
        assert len(falhas) == 1
        assert falhas[0].status.property("delivery") == "failed"
        assert not falhas[0].retry.isHidden()
        assert not janela._timeouts_envio
        assert entradas == ["Verificação de conversa nas três formas"]
        ponte.parar()
        aguardar(lambda: not janela._conectado)
        assert not janela.composer.editor.isEnabled()
        for modo in ("ilha", "painel", "completa"):
            janela.apresentacao.definir_modo(modo)
        assert not janela.composer.editor.isEnabled()
    finally:
        janela.close()
        worker.parar()
        ponte.parar()
        thread.quit()
        assert thread.wait(3000), "O transporte real deve encerrar após fechar a janela"
        app.processEvents()

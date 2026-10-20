"""HTML oficial -> QWebChannel -> transporte autenticado -> HTML observável."""
from __future__ import annotations

import json
from pathlib import Path
import time

import pytest

pytest.importorskip("PySide6.QtWebEngineWidgets")


def test_renderer_oficial_preserva_conversa_rascunho_recusa_e_sessao(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --no-sandbox")
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
    from PySide6.QtCore import QSettings, QThread
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    import cliente.terminal_laylay_2 as terminal
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1
    from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime

    monkeypatch.setattr(terminal, "QSettings", lambda *_: QSettings(
        str(tmp_path / "ui.ini"), QSettings.IniFormat,
    ))
    app = QApplication.instance() or QApplication([])
    entradas, mensagens = [], []
    ponte = DesktopBridgeRuntime(
        enviar_entrada=entradas.append, historico_getter=lambda: [],
        estado_getter=lambda: {"activity": "idle", "interaction_mode": "chat"},
        conversas_getter=lambda: [{"id": "11111111111111111111111111111111", "titulo": "Contrato da interface", "status": "ativa"}],
        conversa_ativa_getter=lambda: "11111111111111111111111111111111",
        configuracao_getter=lambda: {}, log=lambda _: None,
    )
    ponte.iniciar()
    worker = terminal.PonteWorker(*ponte.endereco, ponte.token, session_id=ponte.session_id)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.executar)
    worker.terminou.connect(thread.quit)
    worker.mensagem.connect(mensagens.append)
    janela = JanelaInterfaceWebV1(worker, Path(__file__).parents[2], session_id=ponte.session_id)

    def aguardar(condicao, segundos=8):
        limite = time.monotonic() + segundos
        while not condicao() and time.monotonic() < limite:
            QTest.qWait(20)
        assert condicao(), "A composição real HTML/canal/transporte não alcançou o estado esperado"

    def js(codigo):
        resposta = []
        janela.web.page().runJavaScript(codigo, resposta.append)
        aguardar(lambda: bool(resposta))
        return resposta[0]

    try:
        janela.show()
        thread.start()
        aguardar(lambda: js("!!window.LaylayInterface?.state.connected"))
        aguardar(lambda: js("LaylayInterface.state.conversations.active_id==='11111111111111111111111111111111'"))
        assert janela.web.url().isLocalFile()
        assert js("document.querySelectorAll('.nav button[data-page]').length") == 9
        assert janela.controlador.worker is worker
        assert not janela.controlador.isVisible()
        js("LaylayInterface.goPage('chat');LaylayInterface.state.draft='Rascunho entre modos';LaylayInterface.render();")
        for modo in ("quick", "island", "full"):
            js("LaylayInterface.goMode(" + json.dumps(modo) + ")")
            aguardar(lambda: janela.modo_apresentacao == modo)
            assert js("LaylayInterface.state.draft") == "Rascunho entre modos"
            assert js("LaylayInterface.state.interactionMode") == "chat"
        assert entradas == []

        texto = "Mensagem real <img src=x onerror=alert(1)>"
        js("document.getElementById('composer-input').value=" + json.dumps(texto) + ";document.getElementById('composer-input').dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('[data-composer]').requestSubmit();")
        aguardar(lambda: len(entradas) == 1)
        assert entradas == [texto]
        aguardar(lambda: js("LaylayInterface.state.messages.some(m=>m.role==='user'&&m.delivery==='accepted')"))
        assert js("document.querySelectorAll('.message.user .bubble img').length") == 0
        assert not js("LaylayInterface.state.messages.some(m=>m.role==='assistant')")
        js("LaylayInterface.goMode('island')")
        assert ponte.publicar_fala_final("Resposta pelo transporte real autenticado.")
        aguardar(lambda: js("LaylayInterface.state.messages.some(m=>m.role==='assistant'&&m.text==='Resposta pelo transporte real autenticado.')"))
        js("LaylayInterface.goMode('full')")
        aguardar(lambda: js("document.querySelector('.chat-history')?.textContent.includes('Resposta pelo transporte real autenticado.')"))
        assert entradas == [texto]

        # A negativa real do executor de entrada precisa chegar ao DOM.
        ponte.enviar_entrada = lambda _: False
        js("LaylayInterface.request('texto',{text:'Esta entrada deve ser recusada'})")
        aguardar(lambda: any(m.get("type") == "input_ack" and not m.get("accepted") for m in mensagens))
        aguardar(lambda: js("LaylayInterface.state.messages.some(m=>m.text==='Esta entrada deve ser recusada'&&m.delivery==='failed')"))
        aguardar(lambda: js("!!document.querySelector('.delivery.failed [data-retry]')"))
        assert entradas == [texto]
        ponte.parar()
        aguardar(lambda: js("LaylayInterface.state.connected===false"))
        aguardar(lambda: js("document.getElementById('composer-input')?.disabled===true"))
        assert janela.controlador.worker is worker
    finally:
        janela.close()
        worker.parar()
        ponte.parar()
        thread.quit()
        assert thread.wait(3000)
        app.processEvents()

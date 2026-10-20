"""Contrato do renderer oficial: apresentação sem uma segunda autoridade."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("PySide6.QtWebEngineWidgets")


@pytest.fixture
def interface_web(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --no-sandbox")
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication
    from cliente import terminal_laylay_2 as terminal
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1

    preferencias = QSettings(str(tmp_path / "ui.ini"), QSettings.IniFormat)
    monkeypatch.setattr(terminal, "QSettings", lambda *_: preferencias)
    app = QApplication.instance() or QApplication([])
    worker = terminal.PonteWorker("127.0.0.1", 1, "nao-expor-token")
    enviadas = []
    monkeypatch.setattr(worker, "enfileirar", lambda msg: enviadas.append(msg) or True)
    html = tmp_path / "web"
    html.mkdir()
    (html / "index.html").write_text("<!doctype html><html><body>Fixture local</body></html>", encoding="utf-8")
    janela = JanelaInterfaceWebV1(worker, Path(__file__).parents[2], diretorio_web=html)
    eventos = []
    janela.ponte_web.evento.connect(lambda bruto: eventos.append(json.loads(bruto)))
    yield app, worker, janela, enviadas, eventos
    janela.close()
    app.processEvents()


def test_ui_web_reusa_owner_e_pedido_canonico_com_receipt_separado(interface_web):
    _app, worker, janela, enviadas, eventos = interface_web
    worker.conectado.emit(True)
    janela.ponte_web.pronto()
    requisicao = janela.ponte_web.solicitar("texto", json.dumps({"text": "Me explica essa ideia"}))
    assert requisicao
    assert janela.controlador.worker is worker
    assert not janela.controlador.isVisible()
    assert enviadas[-1]["type"] == "input_submit"
    assert enviadas[-1]["id"] == requisicao
    assert requisicao in janela.controlador._envios
    assert not any(e.get("type") == "assistant_message" for e in eventos)
    worker.mensagem.emit({"type": "input_ack", "id": requisicao, "accepted": True})
    assert requisicao in janela.controlador._envios
    worker.mensagem.emit({"type": "assistant_message", "id": requisicao, "text": "Resposta recebida."})
    assert requisicao not in janela.controlador._envios
    assert eventos[-1]["type"] == "assistant_message"


def test_web_falha_fechada_sem_envio_para_json_invalido_tipo_e_override(interface_web):
    _app, worker, janela, enviadas, eventos = interface_web
    worker.conectado.emit(True)
    antes = list(enviadas)
    for tipo, bruto in (("texto", "{"), ("executar", "{}"), ("playlist", '{"operation":"detail","playlist":"teste","type":"restart_request"}'), ("acao", '{"action":"inexistente","request":"apaga tudo","payload":{}}')):
        assert janela.ponte_web.solicitar(tipo, bruto) == ""
    assert enviadas == antes


def test_reload_reapresenta_estado_respostas_e_pendencias_sem_credenciais(interface_web):
    _app, worker, janela, _enviadas, eventos = interface_web
    worker.conectado.emit(True)
    worker.mensagem.emit({"type": "snapshot", "messages": [], "state": {"activity": "idle"}, "settings": {"provider": "ollama", "api_key": "SEGREDO", "token": "TOKEN"}})
    janela.ponte_web.pronto()
    requisicao = janela.ponte_web.solicitar("texto", '{"text":"Pedido pendente"}')
    worker.mensagem.emit({"type": "input_ack", "id": requisicao, "accepted": True})
    eventos.clear()
    janela.ponte_web.pronto()
    assert any(e.get("type") == "snapshot" for e in eventos)
    assert any(e.get("type") == "pedido_enviado" and e.get("id") == requisicao for e in eventos)
    assert any(e.get("type") == "input_ack" and e.get("accepted") for e in eventos)
    assert "SEGREDO" not in json.dumps(eventos)
    assert "TOKEN" not in json.dumps(eventos)
    assert "nao-expor-token" not in json.dumps(eventos)


def test_apresentacao_web_e_preferencias_nao_emitem_comandos(interface_web):
    app, _worker, janela, enviadas, eventos = interface_web
    antes = list(enviadas)
    janela.show()
    for modo in ("quick", "island", "full"):
        janela.ponte_web.apresentar(modo)
        app.processEvents()
        assert janela.modo_apresentacao == modo
    janela.ponte_web.pronto()
    assert janela.ponte_web.solicitar("preferencia", '{"name":"mascote","value":false}')
    assert enviadas == antes
    assert any(e.get("type") == "preferencias_ui" and e.get("mascot") is False for e in eventos)


def test_web_bloqueia_navegacao_remota_e_canal_apenas_na_pagina_local(interface_web):
    from PySide6.QtCore import QUrl
    from PySide6.QtWebEngineCore import QWebEnginePage
    _app, _worker, janela, _enviadas, _eventos = interface_web
    pagina = janela.web.page()
    assert pagina.acceptNavigationRequest(QUrl("https://example.com"), QWebEnginePage.NavigationTypeLinkClicked, True) is False
    assert pagina.acceptNavigationRequest(QUrl.fromLocalFile(str(janela.diretorio_web / "index.html")), QWebEnginePage.NavigationTypeOther, True) is True
    assert pagina.acceptNavigationRequest(QUrl.fromLocalFile("C:/Windows/win.ini"), QWebEnginePage.NavigationTypeOther, True) is False
    assert pagina.createWindow(QWebEnginePage.WebBrowserWindow) is None


def test_capas_locais_exigem_token_exato_e_imagem_no_cache(interface_web, tmp_path):
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QImage, QColor
    from PySide6.QtWebEngineCore import QWebEngineUrlRequestInfo
    from cliente.terminal_2.interface_web_v1 import CapasLocaisV1

    _app, _worker, janela, _enviadas, _eventos = interface_web
    cache = tmp_path / "capas"
    cache.mkdir()
    token = "0123456789abcdef01234567.png"
    imagem = QImage(16, 16, QImage.Format_ARGB32)
    imagem.fill(QColor("#ba9be8"))
    assert imagem.save(str(cache / token))
    handler = CapasLocaisV1(janela, cache)
    url = QUrl("laylay-playlist-artwork://" + token)
    assert handler.png(url).startswith(b"\x89PNG\r\n\x1a\n")
    for invalida in ("laylay-playlist-artwork://../segredo.png", "laylay-playlist-artwork://" + token + "?arquivo=outro", "file:///C:/Windows/win.ini"):
        assert handler.png(QUrl(invalida)) == b""
    politica = janela.politica_recursos
    assert politica.permitido(url, QWebEngineUrlRequestInfo.ResourceTypeImage)
    assert not politica.permitido(url, QWebEngineUrlRequestInfo.ResourceTypeScript)
    assert not politica.permitido(QUrl("https://example.com/capa.png"), QWebEngineUrlRequestInfo.ResourceTypeImage)


def test_receipt_terminal_nao_reabre_pedido_ao_recarregar_renderer(interface_web):
    _app, worker, janela, _enviadas, eventos = interface_web
    worker.conectado.emit(True)
    janela.ponte_web.pronto()
    pedido = janela.ponte_web.solicitar("acao", json.dumps({
        "action": "media_toggle", "request": "pausa a música", "payload": {"command": "pause"},
    }))
    assert pedido
    worker.mensagem.emit({"type": "input_ack", "id": pedido, "accepted": True})
    worker.mensagem.emit({"type": "action_state", "id": pedido, "action": "media_toggle", "state": "confirmed", "summary": "Pausa confirmada"})
    eventos.clear()
    janela.ponte_web.pronto()
    assert any(e.get("type") == "action_state" and e.get("state") == "confirmed" for e in eventos)
    assert not any(e.get("type") == "pedido_enviado" and e.get("id") == pedido for e in eventos)

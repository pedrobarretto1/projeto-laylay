from __future__ import annotations

import pytest


@pytest.fixture
def app_qt(monkeypatch, tmp_path):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(tmp_path))
    yield app
    app.processEvents()


@pytest.mark.parametrize("largura", [480, 900, 1440])
def test_musica_preserva_conteudo_sem_exibir_sistema_compacto(app_qt, largura):
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    pagina = PaginaMusicaM1()
    pedidos = []
    pagina.acao_solicitada.connect(lambda *args: pedidos.append(args))
    try:
        pagina.resize(largura, 900)
        pagina.show()
        pagina.aplicar_dashboard({
            "music": {},
            "system": {"cpu_percent": {"value": 27, "unit": "%"}},
            "routines": {"freshness": "fresh", "items": []},
        })
        app_qt.processEvents()

        assert pagina.barra_lateral.layout().indexOf(pagina.sistema) == -1
        assert pagina.sistema.parentWidget() is pagina.barra_lateral
        assert not pagina.sistema.isWindow()
        assert not pagina.sistema.isVisible()
        assert pagina.sistema_valores["cpu_percent"].text() == "27%"
        for cartao in (pagina.audicao, pagina.rotinas, pagina.luzes):
            assert pagina.barra_lateral.layout().indexOf(cartao) >= 0
            assert not cartao.isHidden()
        assert pagina.fila is not None
        assert pagina.audio is not None
        assert pagina.letra is not None
        assert pedidos == []

        pagina.invalidar()
        app_qt.processEvents()
        assert not pagina.sistema.isVisible()
        assert pagina.sistema_valores["cpu_percent"].text() == "—"
        assert pedidos == []
    finally:
        pagina.close()
        pagina.deleteLater()


def test_tema_v1_renderiza_baloes_e_preserva_cor_de_falha(app_qt):
    from PySide6.QtCore import qInstallMessageHandler
    from PySide6.QtGui import QPalette
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

    from cliente.terminal_2.theme import qss_chat_components, qss_home_refresh
    from cliente.terminal_2.theme.v1 import qss_interface_v1

    avisos = []
    anterior = qInstallMessageHandler(lambda tipo, contexto, texto: avisos.append(texto))
    janela = QWidget()
    layout = QVBoxLayout(janela)
    usuario = QFrame()
    usuario.setObjectName("messageUser")
    usuario.setFixedSize(180, 70)
    assistente = QFrame()
    assistente.setObjectName("messageLaylay")
    assistente.setFixedSize(180, 70)
    falha = QLabel("Falha na entrega")
    falha.setObjectName("messageStatus")
    falha.setProperty("delivery", "failed")
    layout.addWidget(usuario)
    layout.addWidget(assistente)
    layout.addWidget(falha)
    try:
        janela.setStyleSheet(
            qss_chat_components() + qss_home_refresh() + qss_interface_v1(),
        )
        janela.show()
        app_qt.processEvents()

        assert usuario.grab().toImage().pixelColor(25, 25).name() == "#2b2340"
        assert assistente.grab().toImage().pixelColor(25, 25).name() == "#191d27"
        assert falha.palette().color(QPalette.WindowText).name() == "#ed7888"
        assert not any("parse" in aviso.casefold() for aviso in avisos)
    finally:
        janela.close()
        janela.deleteLater()
        qInstallMessageHandler(anterior)


def test_tema_configuracoes_mantem_sucesso_e_erro_sem_estilo_de_acao(app_qt):
    from PySide6.QtGui import QPalette
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

    from cliente.terminal_2.theme import qss_settings_refresh
    from cliente.terminal_2.theme.v1 import qss_interface_v1

    pagina = QWidget()
    pagina.setObjectName("settingsPage")
    layout = QVBoxLayout(pagina)
    falha = QLabel("Falha ao salvar")
    falha.setObjectName("settingsBanner")
    falha.setProperty("kind", "error")
    sucesso = QLabel("Salvo")
    sucesso.setObjectName("settingsBanner")
    sucesso.setProperty("kind", "success")
    layout.addWidget(falha)
    layout.addWidget(sucesso)
    try:
        pagina.setStyleSheet(qss_settings_refresh() + qss_interface_v1())
        pagina.show()
        app_qt.processEvents()
        # A faixa semântica permanece vermelha/verde no componente Qt real.
        imagem_erro = falha.grab().toImage()
        imagem_sucesso = sucesso.grab().toImage()
        assert imagem_erro.pixelColor(1, imagem_erro.height() // 2).name() == "#ed7888"
        assert imagem_sucesso.pixelColor(1, imagem_sucesso.height() // 2).name() == "#68c79a"
        assert falha.palette().color(QPalette.WindowText).name() == "#a6afba"
    finally:
        pagina.close()
        pagina.deleteLater()

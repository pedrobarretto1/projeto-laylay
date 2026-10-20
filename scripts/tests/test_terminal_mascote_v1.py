"""Contratos visuais e temporais do rosto nativo, sem transporte operacional."""

import math
import time

import pytest


@pytest.fixture
def rosto(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QCursor
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
    from cliente.terminal_2.mascote_v1 import MascoteLaylay

    app = QApplication.instance() or QApplication([])
    janela = QWidget()
    janela.resize(320, 240)
    layout = QVBoxLayout(janela)
    mascote = MascoteLaylay(tamanho=112)
    layout.addWidget(mascote)
    janela.show()
    janela.activateWindow()
    QCursor.setPos(mascote.mapToGlobal(QPoint(56, 52)))
    QTest.qWait(100)
    yield app, janela, mascote
    mascote.encerrar()
    janela.close()
    app.processEvents()


def test_mascote_tem_corpo_continuo_olhos_e_muda_com_estado_real(rosto):
    _, _, mascote = rosto
    mascote.definir_reduzir_movimento(True)
    imagem = mascote.grab().toImage()
    centro = imagem.pixelColor(56, 52)
    canto = imagem.pixelColor(0, 0)
    assert centro != canto
    assert centro.red() > centro.green()  # acabamento violeta
    mascote.definir_estado("listening", "curiosa", True)
    ouvindo = mascote.grab().toImage()
    assert ouvindo != imagem
    mascote.definir_estado("thinking", "calma", True)
    pensando = mascote.grab().toImage()
    assert pensando != imagem
    assert pensando != ouvindo
    mascote.definir_estado("reconnecting", "calma", False)
    assert mascote.grab().toImage() != ouvindo


def test_olhos_acompanham_cursor_com_amplitude_limitada_e_suavizacao(rosto):
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QCursor
    from PySide6.QtTest import QTest

    _, janela, mascote = rosto
    assert janela.isActiveWindow()
    assert mascote.animacao_ativa
    antes = mascote.grab().toImage()
    QCursor.setPos(mascote.mapToGlobal(QPoint(600, -300)))
    QTest.qWait(300)
    x, y = mascote.posicao_olhar
    assert x > 0 and y < 0
    assert math.hypot(x, y) <= 5.01
    assert mascote.grab().toImage() != antes


def test_piscada_natural_acontece_e_reabre_os_olhos(rosto):
    from PySide6.QtTest import QTest

    _, _, mascote = rosto
    fim = time.monotonic() + 6.5
    while not mascote.piscando and time.monotonic() < fim:
        QTest.qWait(15)
    assert mascote.piscando
    fechada = mascote.grab().toImage()
    QTest.qWait(300)
    assert not mascote.piscando
    assert mascote.grab().toImage() != fechada


def test_movimento_reduzido_oculto_e_encerrado_nao_mantem_timer(rosto):
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QWidget

    _, janela, mascote = rosto
    mascote.definir_reduzir_movimento(True)
    assert not mascote.animacao_ativa
    assert mascote.posicao_olhar == (0.0, 0.0)
    assert not mascote.piscando
    imagem = mascote.grab().toImage()
    QTest.qWait(100)
    assert mascote.grab().toImage() == imagem
    mascote.definir_reduzir_movimento(False)
    assert mascote.animacao_ativa
    janela.hide()
    QTest.qWait(60)
    assert not mascote.animacao_ativa
    janela.show()
    # O plugin offscreen mantém a ativação anterior ao esconder/reexibir.
    # Uma segunda janela produz a mesma mudança real de foco do desktop.
    outra = QWidget()
    outra.show()
    outra.activateWindow()
    QTest.qWait(30)
    janela.activateWindow()
    QTest.qWait(100)
    assert janela.isActiveWindow()
    assert mascote.animacao_ativa
    outra.close()
    mascote.encerrar()
    assert not mascote.animacao_ativa
    from PySide6.QtCore import QTimer
    assert all(not timer.isActive() for timer in mascote.findChildren(QTimer))
    janela.hide()
    janela.show()
    QTest.qWait(60)
    assert not mascote.animacao_ativa


def test_minimizar_e_perder_foco_suspendem_rosto(rosto):
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QWidget

    _, janela, mascote = rosto
    janela.showMinimized()
    QTest.qWait(80)
    assert not mascote.animacao_ativa
    janela.showNormal()
    janela.activateWindow()
    QTest.qWait(80)
    assert mascote.animacao_ativa
    outra = QWidget()
    outra.show()
    outra.activateWindow()
    QTest.qWait(80)
    assert not mascote.animacao_ativa
    outra.close()


@pytest.mark.parametrize("largura,altura", [(28, 26), (40, 40), (112, 104), (240, 180)])
def test_rosto_escala_em_ilha_painel_e_interface_sem_recortar_corpo(rosto, largura, altura):
    _, _, mascote = rosto
    mascote.definir_reduzir_movimento(True)
    mascote.setFixedSize(largura, altura)
    imagem = mascote.grab().toImage()
    assert imagem.width() == largura
    assert imagem.height() == altura
    assert imagem.pixelColor(largura // 2, altura // 2) != imagem.pixelColor(0, 0)

from pathlib import Path
from time import monotonic

import pytest

pytest.importorskip("PySide6.QtWebEngineWidgets")


def test_cartoes_preservam_estado_e_interruptor_fica_no_trilho(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --no-sandbox")
    from PySide6.QtCore import QUrl
    from PySide6.QtTest import QTest
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    view = QWebEngineView()
    view.resize(920, 700)
    view.show()

    def esperar(condicao):
        fim = monotonic() + 6
        while not condicao() and monotonic() < fim:
            QTest.qWait(20)
        assert condicao()

    def js(codigo):
        saida = []
        view.page().runJavaScript(codigo, saida.append)
        esperar(lambda: bool(saida))
        return saida[0]

    index = Path(__file__).parents[2] / "cliente/terminal_2/web_v1/index.html"
    carregado = []
    view.loadFinished.connect(carregado.append)
    try:
        view.load(QUrl.fromLocalFile(str(index)))
        esperar(lambda: bool(carregado))
        assert carregado == [True]
        assert js("""
            (() => {
              const ui = window.LaylayInterface;
              ui.state.connected = true;
              ui.state.preferences.reduced = true;
              const device = (name, display_name) => ({
                name, display_name, room:'quarto', type:'rele',
                state:'off', state_confirmed:true, capabilities:['ligar','desligar','status'],
              });
              ui.state.dashboard = {iot:{devices:[
                device('removido','Primeiro dispositivo'), device('rele_esp32','Relé ESP32'),
              ], controls_available:true, freshness:'fresh'}};
              ui.goPage('lamp');
              window.cardIoT = document.querySelector('[data-render-key="iot-rele_esp32"]');
              cardIoT.querySelector('details').open = true;
              ui.state.dashboard.iot.devices.shift();
              ui.state.dashboard.iot.devices[0].state = 'on';
              ui.render();
              return cardIoT === document.querySelector('[data-render-key="iot-rele_esp32"]')
                && cardIoT.querySelector('details').open;
            })()
        """)
        for largura in (920, 460):
            view.resize(largura, 700)
            app.processEvents()
            assert js("""
                (() => {
                  const toggle = cardIoT.querySelector('.toggle');
                  const knob = getComputedStyle(toggle, '::after');
                  const start = parseFloat(knob.left);
                  const end = start + parseFloat(knob.width);
                  const details = cardIoT.querySelector('details').getBoundingClientRect();
                  const icon = cardIoT.querySelector('.device-illustration').getBoundingClientRect();
                  return toggle.getAttribute('aria-pressed') === 'true'
                    && knob.transform === 'none' && start > toggle.clientWidth / 3
                    && end <= toggle.clientWidth && icon.bottom <= details.top
                    && toggle.getBoundingClientRect().bottom <= details.top;
                })()
            """)
        assert js("""
            cardIoT.querySelector('[data-tp-action="iot-forget"]').click();
            document.querySelector('#tp-dialog').open
              && document.querySelector('#tp-dialog strong').textContent === 'Relé ESP32';
        """)
    finally:
        view.close()
        app.processEvents()

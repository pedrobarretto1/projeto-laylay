import pytest


@pytest.mark.parametrize("compacto", [False, True])
@pytest.mark.parametrize("tom", ["cpu", "ram", "vram"])
def test_grafico_ancora_leitura_atual_a_direita_e_desliza_historico(monkeypatch, compacto, tom):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QColor
    from cliente.terminal_2.dashboard import GraficoMetricaSistema
    from cliente.terminal_2.sistema_compacto import GraficoSistemaCompacto

    app = QApplication.instance() or QApplication([])
    grafico = GraficoSistemaCompacto(tom) if compacto else GraficoMetricaSistema(tom)
    grafico.resize(242, grafico.height() if compacto else 64)
    grafico.show()
    cor = QColor(grafico.CORES[tom])

    def pixels_coloridos():
        app.processEvents()
        imagem = grafico.grab().toImage()
        return [
            x for x in range(imagem.width()) for y in range(imagem.height())
            if imagem.pixelColor(x, y).saturationF() > 0.25
            and abs(imagem.pixelColor(x, y).hueF() - cor.hueF()) < 0.045
        ]

    try:
        grafico.definir([70])
        primeira = pixels_coloridos()
        assert primeira, "uma amostra precisa ser visível inclusive no gráfico de linha"
        assert min(primeira) > grafico.width() * 0.90
        grafico.definir([70, 70])
        segunda = pixels_coloridos()
        assert 5 <= min(primeira) - min(segunda) <= 13
        assert abs(max(primeira) - max(segunda)) <= 2
        assert grafico.valores == (70.0, 70.0)
        grafico.definir([70] * 30)
        completa = pixels_coloridos()
        assert min(completa) < grafico.width() * 0.05
        assert len(grafico.valores) == 24
    finally:
        grafico.close()

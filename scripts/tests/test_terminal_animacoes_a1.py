from __future__ import annotations

from pathlib import Path
import time

import pytest


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
    janela = JanelaLaylay(Worker(), Path(__file__).parents[1])
    janela.show()
    app.processEvents()
    return app, janela


def _processar_por(app, segundos: float) -> None:
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        app.processEvents()
        time.sleep(0.005)


def test_entrada_a1_e_curta_em_cascata_e_libera_os_componentes(monkeypatch) -> None:
    app, janela = _janela(monkeypatch)
    _processar_por(app, 0.22)
    grupo = janela._animacao_inicio_grupo
    assert grupo is not None
    assert 500 <= grupo.duration() <= 600

    _processar_por(app, 0.85)

    assert janela._interface_animavel is True
    assert janela._animacao_inicio_grupo is None
    assert janela._efeitos_inicio == []
    for widget in (
        janela.sidebar,
        janela.topbar,
        janela.chat_surface,
        janela.central_inteligente,
        janela.painel_lateral,
    ):
        assert widget.graphicsEffect() is None
    janela.close()


def test_troca_de_aba_anima_so_indicador_sem_rasterizar_pagina(
    monkeypatch,
) -> None:
    app, janela = _janela(monkeypatch)
    _processar_por(app, 0.85)
    inicio_y = janela.indicador_navegacao.geometry().center().y()

    janela.selecionar_pagina("musica")
    app.processEvents()

    assert janela._animacao_pagina_grupo is None
    assert janela._animacao_indicador_nav is not None
    assert janela.paginas.currentWidget().graphicsEffect() is None

    _processar_por(app, 0.35)

    destino = janela._geometria_indicador_navegacao(
        janela._nav["musica"],
    )
    assert janela.indicador_navegacao.geometry() == destino
    assert destino.center().y() > inicio_y
    assert janela._animacao_pagina_grupo is None
    assert janela.paginas.currentWidget().graphicsEffect() is None
    janela.close()


def test_trocas_rapidas_nao_deixam_efeito_em_paginas_antigas(monkeypatch) -> None:
    app, janela = _janela(monkeypatch)
    _processar_por(app, 0.85)

    for nome in ("musica", "sistema", "memoria", "conversa"):
        janela.selecionar_pagina(nome)
        app.processEvents()

    _processar_por(app, 0.35)

    assert janela._pagina_visual_ativa == "conversa"
    assert janela._animacao_pagina_grupo is None
    assert all(
        janela.paginas.widget(indice).graphicsEffect() is None
        for indice in range(janela.paginas.count())
    )
    janela.close()


def test_movimento_reduzido_troca_imediatamente_sem_animacao(monkeypatch) -> None:
    app, janela = _janela(monkeypatch, reduzir_movimento=True)
    janela.selecionar_pagina("sistema")
    app.processEvents()

    assert janela._interface_animavel is True
    assert janela._animacao_inicio_grupo is None
    assert janela._animacao_pagina_grupo is None
    assert janela._animacao_indicador_nav is None
    assert janela.indicador_navegacao.geometry() == (
        janela._geometria_indicador_navegacao(janela._nav["sistema"])
    )
    janela.close()

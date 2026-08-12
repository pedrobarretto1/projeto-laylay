from __future__ import annotations

import pytest


def _pagina(monkeypatch, *, reduzir_movimento: bool = False):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv(
        "LAYLAY_REDUZIR_MOVIMENTO", "1" if reduzir_movimento else "0",
    )
    monkeypatch.setattr("cliente.terminal_2.musica_m1.time.time", lambda: 1_000)
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    pagina = PaginaMusicaM1()
    pagina.resize(1_680, 900)
    pagina.show()
    pagina.definir_conectada(True)
    app.processEvents()
    return app, pagina


def _dashboard(letra: dict) -> dict:
    return {
        "music": {
            "title": "Faixa", "channel": "Artista", "state": "playing",
            "position_seconds": 0, "duration_seconds": 240,
            "freshness": "fresh", "observed_at": 1_000,
            "controls_available": True, "lyrics": letra,
        },
        "system": {}, "routines": {},
    }


def _linhas_sincronizadas(quantidade: int = 40) -> list[dict]:
    return [
        {"time_seconds": indice * 5, "text": f"Linha sincronizada {indice + 1}"}
        for indice in range(quantidade)
    ]


def test_letra_sem_sincronia_expande_em_leitor_com_scroll_proprio(monkeypatch) -> None:
    from PySide6.QtCore import Qt

    app, pagina = _pagina(monkeypatch)
    texto = "\n".join(f"Verso sem tempo {indice + 1}" for indice in range(45))
    pagina.aplicar_dashboard(_dashboard({
        "status": "available", "source": "lrclib", "synced": False,
        "plain_text": texto, "observed_at": 1_000, "lines": [],
    }))
    app.processEvents()

    assert pagina.letra_texto.maximumHeight() == 116
    assert pagina.letra_texto.verticalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    assert pagina.letra_texto.document().documentMargin() == 0
    assert "Verso sem tempo 1" in pagina.letra_texto.text()

    pagina.letra_expandir.click()
    app.processEvents()

    assert pagina.letra_texto.minimumHeight() == 230
    assert pagina.letra_texto.maximumHeight() == 340
    assert pagina.letra_texto.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded
    assert pagina.letra_texto.verticalScrollBar().maximum() > 0
    assert "Verso sem tempo 45" in pagina.letra_texto.text()
    pagina.close()
    app.processEvents()


def test_letra_sincronizada_expandida_acompanha_linha_com_scroll_suave(
    monkeypatch,
) -> None:
    from PySide6.QtCore import QEasingCurve

    app, pagina = _pagina(monkeypatch)
    pagina.aplicar_dashboard(_dashboard({
        "status": "available", "source": "lrclib", "synced": True,
        "observed_at": 1_000, "lines": _linhas_sincronizadas(),
    }))
    pagina.letra_expandir.click()
    app.processEvents()
    pagina._renderizar_letra(150)
    app.processEvents()

    animacao = pagina._animacao_rolagem_letra
    assert animacao is not None
    assert animacao.duration() == 420
    assert animacao.easingCurve().type() == QEasingCurve.InOutCubic
    assert int(animacao.endValue()) > int(animacao.startValue())
    animacao.setCurrentTime(animacao.duration())
    assert pagina.letra_texto.verticalScrollBar().value() == int(
        animacao.endValue(),
    )

    pagina._renderizar_letra(151)
    assert pagina._animacao_rolagem_letra is animacao
    pagina.close()
    app.processEvents()


def test_reducao_de_movimento_faz_scroll_imediato_sem_animacao(monkeypatch) -> None:
    app, pagina = _pagina(monkeypatch, reduzir_movimento=True)
    pagina.aplicar_dashboard(_dashboard({
        "status": "available", "source": "lrclib", "synced": True,
        "observed_at": 1_000, "lines": _linhas_sincronizadas(),
    }))
    pagina.letra_expandir.click()
    app.processEvents()
    pagina._renderizar_letra(190)
    app.processEvents()

    assert pagina._animacao_rolagem_letra is None
    assert pagina.letra_texto.verticalScrollBar().value() > 0
    pagina.close()
    app.processEvents()

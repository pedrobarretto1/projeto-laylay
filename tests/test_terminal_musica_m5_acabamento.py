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
    app.processEvents()
    pagina.definir_conectada(True)
    return app, pagina


def _dashboard() -> dict:
    return {
        "music": {
            "title": "Faixa", "channel": "Artista", "state": "playing",
            "position_seconds": 1, "duration_seconds": 120,
            "freshness": "fresh", "observed_at": 1_000,
            "controls_available": True,
            "catalog_available": True, "catalog_play_available": True,
            "catalog_observed_at": 1_000,
            "catalog": [
                {"name": "rock", "count": 12},
                {"name": "VMZ", "count": 8},
            ],
            "context_music": {
                "summary": "É noite e a playlist Rock está ativa.",
                "recommendation": "Posso manter a sequência de Rock.",
                "basis": ["horario_local", "playlist_ativa"],
                "freshness": "fresh", "observed_at": 1_000,
            },
            "lyrics": {
                "status": "available", "source": "lrclib", "synced": True,
                "observed_at": 1_000,
                "lines": [
                    {"time_seconds": 1, "text": "Primeira linha"},
                    {"time_seconds": 8, "text": "Segunda linha"},
                    {"time_seconds": 16, "text": "Terceira linha"},
                ],
            },
        },
        "system": {
            "cpu_percent": {"value": 18, "unit": "%"},
            "ram_percent": {"value": 42, "unit": "%"},
            "temperature_c": {"value": None, "unit": "°C"},
            "disk_percent": {"value": 61, "unit": "%"},
            "uptime_seconds": {"value": 3_600, "unit": "s"},
        },
        "routines": {},
    }


def test_m5_equilibra_modulos_e_da_hierarquia_aos_dados(monkeypatch) -> None:
    app, pagina = _pagina(monkeypatch)
    pagina.aplicar_dashboard(_dashboard())
    app.processEvents()

    assert pagina.capa.width() == 230
    assert pagina.fila.minimumWidth() >= 315
    assert pagina.barra_lateral.minimumWidth() >= 265
    assert pagina.sistema_barras["cpu_percent"].value() == 18
    assert pagina.sistema_barras["ram_percent"].value() == 42
    assert pagina.sistema_barras["temperature_c"].property("available") is False
    assert pagina.preset_botoes[0].text().startswith("Rock\n")
    assert pagina.preset_botoes[1].text().startswith("VMZ\n")
    assert pagina.preset_botoes[0].accessibleName() == "Playlist rock, 12 faixas"
    assert pagina.contexto_base.text() == "Horário local  •  Playlist escolhida"
    pagina.close()
    app.processEvents()


def test_m5_troca_de_linha_tem_animacao_fluida_sem_reiniciar(monkeypatch) -> None:
    from PySide6.QtCore import QAbstractAnimation, QEasingCurve

    app, pagina = _pagina(monkeypatch)
    pagina.aplicar_dashboard(_dashboard())
    app.processEvents()
    primeira_animacao = pagina._animacao_letra
    assert primeira_animacao is not None

    pagina._renderizar_letra(9)
    app.processEvents()
    animacao = pagina._animacao_letra
    assert animacao is not None and animacao is not primeira_animacao
    assert animacao.duration() == 420
    assert animacao.easingCurve().type() == QEasingCurve.OutCubic
    assert animacao.state() == QAbstractAnimation.Running
    assert "Segunda linha" in pagina.letra_texto.text()

    pagina._renderizar_letra(10)
    assert pagina._animacao_letra is animacao
    pagina.close()
    app.processEvents()


def test_m5_reducao_de_movimento_desliga_animacao_da_letra(monkeypatch) -> None:
    app, pagina = _pagina(monkeypatch, reduzir_movimento=True)
    pagina.aplicar_dashboard(_dashboard())
    app.processEvents()

    assert pagina._animacao_letra is None
    assert pagina._efeito_letra.opacity() == 1.0
    pagina._renderizar_letra(9)
    assert pagina._animacao_letra is None
    assert pagina._efeito_letra.opacity() == 1.0
    pagina.close()
    app.processEvents()


def test_m5_letra_expandida_nao_pisca_a_cada_tick(monkeypatch) -> None:
    app, pagina = _pagina(monkeypatch)
    pagina.aplicar_dashboard(_dashboard())
    pagina._alternar_letra()
    app.processEvents()
    animacao = pagina._animacao_letra
    assert "Terceira linha" in pagina.letra_texto.text()

    pagina._renderizar_letra(2.0)
    assert pagina._animacao_letra is animacao
    pagina._renderizar_letra(17)
    assert pagina._animacao_letra is not animacao
    assert pagina._animacao_letra.duration() == 260
    pagina.close()
    app.processEvents()

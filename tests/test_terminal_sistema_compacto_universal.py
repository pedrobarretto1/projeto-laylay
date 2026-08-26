from __future__ import annotations

import pytest


def _dashboard(*, frescor: str = "fresh", observado: float = 1_000.0) -> dict:
    def metrica(valor: float, unidade: str = "%") -> dict:
        return {
            "value": valor,
            "unit": unidade,
            "freshness": frescor,
            "observed_at": observado,
        }

    return {
        "system": {
            "cpu_percent": metrica(18),
            "ram_percent": metrica(42),
            "gpu_percent": metrica(26),
            "vram_percent": metrica(31),
            "disk_percent": metrica(61),
            "network_percent": metrica(12),
            "temperature_c": metrica(48, "°C"),
            "download_mbps": metrica(18, "Mbps"),
            "upload_mbps": metrica(6, "Mbps"),
            "uptime_seconds": metrica(90_000, "s"),
            "info": {},
        },
        "music": {},
        "routines": {},
        "health": {},
    }


def test_card_sistema_e_universal_nos_tres_consumidores(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from cliente.terminal_2.dashboard import PainelLateralDashboard, PaginaSistema
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1
    from cliente.terminal_2.sistema_compacto import CardSistemaCompacto

    app = QApplication.instance() or QApplication([])
    inicio = PainelLateralDashboard()
    musica = PaginaMusicaM1()
    sistema = PaginaSistema()

    cards = (
        inicio.sistema_compacto,
        musica.sistema,
        sistema.sistema_rail_card,
    )
    assert all(type(card) is CardSistemaCompacto for card in cards)
    assert all(tuple(card.linhas) == (
        "cpu", "ram", "gpu", "vram", "disk", "network", "temperature",
    ) for card in cards)
    assert inicio.sistema_compacto.minimumWidth() == 250
    assert inicio.sistema_compacto.maximumWidth() == 310
    assert musica.sistema.minimumWidth() == 250
    assert musica.sistema.maximumWidth() == 310

    assert inicio.metricas is inicio.sistema_compacto.metricas
    assert inicio.barras_metricas is inicio.sistema_compacto.barras_metricas
    assert inicio.metricas_linhas is inicio.sistema_compacto.metricas_linhas
    assert musica.sistema_valores is musica.sistema.sistema_valores
    assert musica.sistema_barras is musica.sistema.sistema_barras
    assert sistema.rail_metricas is sistema.sistema_rail_card.linhas

    inicio.deleteLater()
    musica.deleteLater()
    sistema.deleteLater()
    app.processEvents()


def test_card_universal_preserva_aliases_historico_e_frescor(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from cliente.terminal_2.sistema_compacto import CardSistemaCompacto

    app = QApplication.instance() or QApplication([])
    card = CardSistemaCompacto(legado="musica")
    retrato = _dashboard()
    card.aplicar_sistema(retrato)

    assert card.sistema_valores["cpu_percent"].text() == "18%"
    assert card.sistema_valores["temperature_c"].text() == "48°C"
    assert card.sistema_valores["uptime_seconds"].text() == "1d 1h"
    assert card.sistema_barras["cpu_percent"].value() == 18
    assert card.sistema_barras["cpu_percent"].property("available") is True
    assert card.sistema_barras["cpu_percent"].objectName() == "musicSystemBar"
    assert card.linhas["cpu"].grafico.valores == (18.0,)
    assert "Download: 18Mbps" in card.linhas["network"].toolTip()

    # O mesmo snapshot não cria uma amostra visual artificial.
    card.aplicar_sistema(retrato)
    assert card.linhas["cpu"].grafico.valores == (18.0,)

    antigo = _dashboard(frescor="stale", observado=2_000.0)
    antigo["system"]["cpu_percent"]["value"] = 91
    card.aplicar_sistema(antigo)
    assert card.sistema_valores["cpu_percent"].text() == "91% · antigo"
    assert card.linhas["cpu"].grafico.valores == (18.0,)
    assert card.subtitulo.text() == "dados antigos"

    card.aplicar_sistema({"system": {}})
    assert card.sistema_valores["cpu_percent"].text() == "—"
    assert card.sistema_barras["cpu_percent"].value() == 0
    assert card.sistema_barras["cpu_percent"].property("available") is False
    assert card.linhas["cpu"].grafico.valores == (18.0,)
    assert card.subtitulo.text() == "indisponível"

    card.invalidar()
    assert card.subtitulo.property("state") == "indisponível"
    assert card.linhas["cpu"].property("state") == "unavailable"
    assert card.linhas["cpu"].valor.property("state") == "unavailable"
    assert card.linhas["cpu"].grafico.property("available") is False

    card.deleteLater()
    app.processEvents()


def test_consumidores_atualizam_o_mesmo_contrato_sem_telemetria_falsa(
    monkeypatch,
) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from cliente.terminal_2.dashboard import PainelLateralDashboard, PaginaSistema
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    retrato = _dashboard()
    inicio = PainelLateralDashboard()
    musica = PaginaMusicaM1()
    sistema = PaginaSistema()
    inicio.aplicar_dashboard(retrato)
    musica._aplicar_lateral(retrato)
    sistema.aplicar_dashboard(retrato)

    assert inicio.metricas["rede"].text() == "12%"
    assert musica.sistema_valores["network_percent"].text() == "12%"
    assert sistema.rail_metricas["network"].valor.text() == "12%"
    assert inicio.barras_metricas["gpu"].objectName() == "railSystemProgress"
    assert musica.sistema_barras["gpu_percent"].objectName() == "musicSystemBar"

    inicio.invalidar_dashboard()
    musica.invalidar()
    sistema.invalidar()
    assert inicio.metricas["cpu"].text() == "—"
    assert musica.sistema_valores["cpu_percent"].text() == "—"
    assert sistema.rail_metricas["cpu"].valor.text() == "—"

    inicio.deleteLater()
    musica.deleteLater()
    sistema.deleteLater()
    app.processEvents()

from __future__ import annotations

import pytest


def test_sistema_p5_usa_historico_real_layout_denso_e_acoes_canonicas(
    monkeypatch,
) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QBoxLayout, QPushButton

    from cliente.terminal_2.dashboard import PaginaSistema

    app = QApplication.instance() or QApplication([])
    pagina = PaginaSistema()
    pedidos: list[tuple[str, str]] = []
    pagina.acao_solicitada.connect(
        lambda acao, pedido: pedidos.append((acao, pedido))
    )

    base = {
        "system": {
            "cpu_percent": {"value": 18, "freshness": "fresh"},
            "gpu_percent": {"value": 26, "freshness": "fresh"},
            "ram_percent": {"value": 42, "freshness": "fresh"},
            "vram_percent": {"value": 31, "freshness": "fresh"},
            "disk_percent": {"value": 61, "freshness": "fresh"},
            "network_percent": {"value": 12, "freshness": "fresh"},
            "download_mbps": {"value": 18, "unit": "Mbps", "freshness": "fresh"},
            "upload_mbps": {"value": 6, "unit": "Mbps", "freshness": "fresh"},
            "temperature_c": {"value": 48, "unit": "°C", "freshness": "fresh"},
            "uptime_seconds": {"value": 86_400, "freshness": "fresh"},
            "info": {},
        },
        "health": {
            "llm": {"state": "online", "label": "Online", "freshness": "fresh"},
            "memory": {"state": "online", "label": "Ativa", "freshness": "fresh"},
            "microphone": {"state": "paused", "label": "Pausado", "freshness": "fresh"},
        },
        "music": {
            "audio_output": {
                "name": "Alto-falantes (Realtek)", "available": True,
            },
        },
        "memory_recent": [],
    }

    pagina.resize(1600, 900)
    pagina.show()
    pagina.aplicar_dashboard(base)
    app.processEvents()

    assert pagina.desempenho.objectName() == "systemPerformanceCard"
    assert pagina.metricas["cpu"].grafico.valores == (18.0,)
    assert pagina.rail_metricas["cpu"].grafico.valores == (18.0,)
    assert pagina.rail_metricas["temperature"].valor.text() == "48°C"
    assert pagina.audio_valores["output"].text() == "Alto-falantes (Realtek)"
    assert pagina.modelo_valores["tokens"].text() == "—"
    assert pagina.eventos_vazio.isVisible()
    assert pagina.resumo.maximumHeight() == 326
    assert pagina.desempenho.maximumHeight() == 326
    assert pagina.modelo_local.maximumHeight() == 326
    assert pagina.desempenho.maximumWidth() == 460
    assert pagina.modelo_local.minimumWidth() == 300
    assert pagina.audio_card.maximumHeight() == 225
    assert pagina.acoes_card.maximumHeight() == 140
    assert pagina.metricas["ram"].grafico._tom == "ram"
    assert pagina.laylay_valores["model"].text() == "—"

    base["system"]["cpu_percent"] = {"value": 91, "freshness": "stale"}
    pagina.aplicar_dashboard(base)
    assert pagina.metricas["cpu"].grafico.valores == (18.0,)

    base["system"]["cpu_percent"] = {"value": 32, "freshness": "fresh"}
    pagina.aplicar_dashboard(base)
    assert pagina.metricas["cpu"].grafico.valores == (18.0, 32.0)

    botoes = pagina.atalhos_rail_card.findChildren(QPushButton)
    assert botoes
    botoes[0].click()
    assert pedidos == [("open_vscode", "abre o Visual Studio Code")]

    pagina.resize(1024, 760)
    app.processEvents()
    assert pagina.system_workbench.direction() == QBoxLayout.TopToBottom
    assert pagina.system_corpo.direction() == QBoxLayout.TopToBottom

    pagina.close()
    pagina.deleteLater()
    app.processEvents()


def test_resumo_sistema_preserva_duas_linhas_sem_sobreposicao(
    monkeypatch,
) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from cliente.terminal_2.dashboard import PaginaSistema

    app = QApplication.instance() or QApplication([])
    pagina = PaginaSistema()
    dashboard = {
        "system": {
            "info": {
                "os": {"value": "Windows 11 Pro 64-bit"},
                "cpu": {
                    "value": "12th Gen Intel(R) Core(TM) i5-12400",
                    "detail": "6 núcleos / 12 threads",
                },
                "gpu": {
                    "value": "NVIDIA GeForce GTX 1660 SUPER",
                    "detail": "Driver 610.74",
                },
                "ram": {"value": "32 GB", "detail": "Memória física"},
                "vram": {"value": "6 GB", "detail": "Memória dedicada"},
                "disk": {"value": "952 GB", "detail": "Unidade do sistema"},
            },
            "uptime_seconds": {"value": 15_300, "freshness": "fresh"},
            "temperature_c": {"value": None, "freshness": "unavailable"},
        },
        "health": {},
        "music": {},
        "memory_recent": [],
    }

    pagina.resize(1680, 900)
    pagina.show()
    pagina.aplicar_dashboard(dashboard)
    app.processEvents()

    linhas = list(pagina.resumo_linhas.values())
    assert len(linhas) == 8
    assert all(linha.isVisible() for linha in linhas)
    assert [linha.height() for linha in linhas] == [
        28, 38, 38, 38, 38, 38, 28, 28,
    ]
    assert pagina.resumo.height() <= 326

    for linha in linhas:
        assert not linha.valor.wordWrap()
        assert not linha.detalhe.wordWrap()
        assert linha.valor.geometry().bottom() < linha.rect().bottom()
        if linha.detalhe.isVisible():
            assert linha.valor.geometry().bottom() < linha.detalhe.geometry().top()
            assert linha.detalhe.geometry().bottom() < linha.rect().bottom()

    for anterior, seguinte in zip(linhas, linhas[1:]):
        assert anterior.geometry().bottom() < seguinte.geometry().top()

    cpu = pagina.resumo_linhas["cpu"]
    assert cpu.valor.texto_completo == "12th Gen Intel(R) Core(TM) i5-12400"
    assert cpu.valor.toolTip() == cpu.valor.texto_completo
    assert cpu.detalhe.texto_completo == "6 núcleos / 12 threads"

    pagina.close()
    pagina.deleteLater()
    app.processEvents()

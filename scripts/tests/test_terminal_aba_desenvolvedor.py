from __future__ import annotations

from pathlib import Path

import pytest


def _janela(monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_laylay_2 import JanelaLaylay

    class Worker(QObject):
        mensagem = Signal(dict)
        conectado = Signal(bool)
        falha = Signal(str)

        def enfileirar(self, _mensagem: dict) -> bool:
            return True

        def parar(self) -> None:
            return None

    app = QApplication.instance() or QApplication([])
    janela = JanelaLaylay(Worker(), Path(__file__).parents[1])
    janela.show()
    app.processEvents()
    return app, janela


def test_dev_console_entra_na_navegacao_e_carrega_sob_demanda(monkeypatch) -> None:
    app, janela = _janela(monkeypatch)
    from PySide6.QtTest import QTest

    assert "desenvolvedor" in janela._nav
    assert "desenvolvedor" not in janela._paginas_carregadas

    janela.selecionar_pagina("desenvolvedor")
    QTest.qWait(30)
    app.processEvents()

    assert janela.paginas.currentIndex() == 8
    assert janela.paginas.currentWidget() is janela.pagina_desenvolvedor
    janela.close()


def test_dev_console_reproduz_eventos_reais_sem_amostras_inventadas(monkeypatch) -> None:
    app, janela = _janela(monkeypatch)

    janela.adicionar_evento(
        "Roteamento concluído",
        "A ação foi encaminhada ao executor canônico.",
        "success",
    )
    pagina = janela.pagina_desenvolvedor
    app.processEvents()

    texto = pagina.console.toPlainText()
    assert "Roteamento concluído" in texto
    assert "executor canônico" in texto
    assert "Room light ON" not in texto
    janela.close()


def test_dev_console_preserva_owner_nos_eventos_reais_da_interface(monkeypatch) -> None:
    app, janela = _janela(monkeypatch)

    janela.receber({
        "type": "assistant_message",
        "id": "resposta-owner-1",
        "text": "Resposta real da Laylay.",
        "emotion": "calma",
    })
    janela._atualizar_estado({
        "activity": "speaking",
        "activity_label": "Falando",
        "emotion": "calma",
        "interaction_mode": "chat",
        "voice_available": True,
    })
    janela.receber({
        "type": "action_state",
        "id": "acao-owner-1",
        "action": "ORGANIZAR_DESKTOP",
        "state": "confirmed",
        "summary": "Resultado confirmado pela mente",
    })
    pagina = janela.pagina_desenvolvedor
    app.processEvents()

    categorias = {evento.titulo: evento.categoria for evento in pagina._eventos}
    assert categorias["Resposta entregue"] == "IA"
    assert categorias["Falando"] == "IA"
    assert categorias["Ação confirmada"] == "AUTONOMY"
    janela.close()


def test_dev_console_pausa_visual_sem_perder_eventos(monkeypatch) -> None:
    _app, janela = _janela(monkeypatch)
    pagina = janela.pagina_desenvolvedor

    pagina.definir_ao_vivo(False)
    pagina.registrar_evento("Evento durante pausa", "continua no buffer", "info")
    assert "Evento durante pausa" not in pagina.console.toPlainText()
    assert pagina.eventos_pendentes == 1

    pagina.definir_ao_vivo(True)
    assert "Evento durante pausa" in pagina.console.toPlainText()
    assert pagina.eventos_pendentes == 0
    janela.close()


def test_dev_console_reutiliza_graficos_do_sistema_e_dados_observados(
    monkeypatch,
) -> None:
    _app, janela = _janela(monkeypatch)
    from cliente.terminal_2.sistema_compacto import GraficoSistemaCompacto

    pagina = janela.pagina_desenvolvedor
    pagina.aplicar_dashboard({
        "schema_version": 1,
        "system": {
            "cpu_percent": {
                "value": 37,
                "unit": "%",
                "freshness": "fresh",
                "observed_at": 1000,
            },
            "ram_percent": {
                "value": 62,
                "unit": "%",
                "freshness": "fresh",
                "observed_at": 1000,
            },
        },
    })

    assert isinstance(pagina.telemetria["cpu"].grafico, GraficoSistemaCompacto)
    assert pagina.telemetria["cpu"].valor.text() == "37%"
    assert pagina.telemetria["ram"].valor.text() == "62%"
    assert pagina.telemetria["vram"].valor.text() == "—"
    janela.close()


def test_cards_futuros_nao_declaram_habilidades_inexistentes(monkeypatch) -> None:
    _app, janela = _janela(monkeypatch)
    pagina = janela.pagina_desenvolvedor

    assert set(pagina.cards_manutencao) == {
        "Sensor Health",
        "Presence State",
        "Evento Aberto",
        "World Model (Resumo)",
        "Autonomy Decision",
        "Recent Trace",
        "Restore Manager",
    }
    assert all(
        status.text() == "Em manutenção"
        for status in pagina.cards_manutencao.values()
    )
    assert all(not status.isEnabled() for status in pagina.cards_manutencao.values())
    janela.close()


def test_eventos_backend_e_consulta_remota_chegam_ao_console(monkeypatch) -> None:
    app, janela = _janela(monkeypatch)
    pagina = janela.pagina_desenvolvedor
    pagina.definir_conectada(True)
    consultas: list[str] = []
    pagina.consulta_solicitada.connect(consultas.append)

    janela.receber({
        "type": "dev_events",
        "events": [{
            "id": "dev-000001",
            "sequence": 1,
            "timestamp": 1_700_000_000.25,
            "level": "error",
            "category": "ROUTER",
            "event": "roteador",
            "trace_id": "turno-000151",
            "message": "Primeira fronteira incorreta",
            "source": "stdout",
            "depth": "normal",
        }],
    })
    app.processEvents()
    assert "turno-000151" in pagina.console.toPlainText()
    assert "Primeira fronteira incorreta" in pagina.console.toPlainText()

    pagina.comando.setText("trace last")
    pagina.comando.returnPressed.emit()
    assert consultas == ["trace last"]

    pagina.aplicar_resultado_consulta({
        "id": pagina._consulta_pendente,
        "result": {
            "ok": True,
            "kind": "trace",
            "command": "trace last",
            "lines": ["TRACE turno-000151", "PRIMEIRA FRONTEIRA RED: dispatcher"],
        },
    })
    assert "PRIMEIRA FRONTEIRA RED" in pagina.console.toPlainText()
    janela.close()

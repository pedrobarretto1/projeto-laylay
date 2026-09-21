from __future__ import annotations

from pathlib import Path

import pytest


def _janela(monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "0")
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
    worker = Worker()
    janela = JanelaLaylay(worker, Path(__file__).parents[1])
    janela.show()
    app.processEvents()
    return app, worker, janela


def test_dashboard_ao_vivo_nao_renderiza_paginas_ocultas(monkeypatch) -> None:
    app, worker, janela = _janela(monkeypatch)
    chamadas: list[str] = []
    for nome, pagina in (
        ("automacao", janela.pagina_automacao),
        ("musica", janela.pagina_musica),
        ("memoria", janela.pagina_memoria),
        ("sistema", janela.pagina_sistema),
    ):
        monkeypatch.setattr(
            pagina,
            "aplicar_dashboard",
            lambda _dashboard, pagina_nome=nome: chamadas.append(pagina_nome),
        )

    worker.mensagem.emit({
        "type": "dashboard_state",
        "dashboard": {"schema_version": 1, "health": {}},
    })
    app.processEvents()

    assert chamadas == []

    janela.selecionar_pagina("musica")
    app.processEvents()

    assert chamadas == ["musica"]
    janela.close()


def test_inicio_nao_constroi_abas_pesadas_antes_do_primeiro_uso(
    monkeypatch,
) -> None:
    _app, _worker, janela = _janela(monkeypatch)
    from PySide6.QtWidgets import QWidget
    from cliente.terminal_2.dashboard import PaginaAutomacao, PaginaSistema
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    assert janela.findChildren(PaginaAutomacao) == []
    assert janela.findChildren(PaginaMusicaM1) == []
    assert janela.findChildren(PaginaSistema) == []
    assert len(janela.findChildren(QWidget)) < 400
    janela.close()


def test_primeira_navegacao_materializa_pagina_depois_do_feedback(
    monkeypatch,
) -> None:
    app, _worker, janela = _janela(monkeypatch)
    from PySide6.QtTest import QTest

    janela.selecionar_pagina("musica")
    assert "musica" not in janela._paginas_carregadas

    QTest.qWait(30)
    app.processEvents()

    assert "musica" in janela._paginas_carregadas
    assert janela.paginas.currentWidget() is janela._paginas_carregadas["musica"]
    janela.close()


def test_pagina_adiada_recebe_dashboard_mais_recente_ao_materializar(
    monkeypatch,
) -> None:
    _app, _worker, janela = _janela(monkeypatch)
    janela._atualizar_dashboard({
        "schema_version": 1,
        "health": {},
        "system": {
            "cpu_percent": {
                "value": 27,
                "unit": "%",
                "freshness": "fresh",
                "observed_at": 1_000,
            },
        },
    }, somente_visivel=True)

    assert "sistema" not in janela._paginas_carregadas
    pagina = janela.pagina_sistema

    assert pagina.valores["cpu"].text() == "27%"
    assert "sistema" in janela._paginas_carregadas
    janela.close()


def test_pagina_adiada_nao_ressuscita_dashboard_apos_desconexao(
    monkeypatch,
) -> None:
    _app, _worker, janela = _janela(monkeypatch)
    janela._atualizar_dashboard({
        "schema_version": 1,
        "health": {},
        "system": {
            "cpu_percent": {
                "value": 91,
                "unit": "%",
                "freshness": "fresh",
                "observed_at": 1_000,
            },
        },
    }, somente_visivel=True)

    janela.estado_conexao(False)
    pagina = janela.pagina_sistema

    assert pagina.valores["cpu"].text() == "—"
    janela.close()


def test_dashboard_ao_vivo_nao_atualiza_inicio_oculto(monkeypatch) -> None:
    app, worker, janela = _janela(monkeypatch)
    chamadas: list[str] = []
    monkeypatch.setattr(
        janela.central_inteligente,
        "aplicar_dashboard",
        lambda _dashboard: chamadas.append("central"),
    )
    monkeypatch.setattr(
        janela.painel_lateral,
        "aplicar_dashboard",
        lambda _dashboard: chamadas.append("lateral"),
    )
    for nome, pagina in (
        ("automacao", janela.pagina_automacao),
        ("musica", janela.pagina_musica),
        ("memoria", janela.pagina_memoria),
        ("sistema", janela.pagina_sistema),
    ):
        monkeypatch.setattr(
            pagina,
            "aplicar_dashboard",
            lambda _dashboard, pagina_nome=nome: chamadas.append(pagina_nome),
        )

    janela.selecionar_pagina("sistema")
    app.processEvents()
    chamadas.clear()
    worker.mensagem.emit({
        "type": "dashboard_state",
        "dashboard": {"schema_version": 1, "health": {}},
    })
    app.processEvents()

    assert chamadas == ["sistema"]
    janela.close()


def test_timers_visuais_param_quando_superficie_esta_oculta(monkeypatch) -> None:
    app, _worker, janela = _janela(monkeypatch)

    assert not janela.waveform._timer.isActive()
    assert not janela.pagina_musica._relogio.isActive()
    assert not janela.pagina_musica.onda._timer.isActive()
    assert janela.painel_lateral._relogio_musica.isActive()

    janela.waveform.definir_nivel(0.7, ativo=True)
    app.processEvents()
    assert janela.waveform._timer.isActive()

    janela.selecionar_pagina("musica")
    app.processEvents()
    assert not janela.waveform._timer.isActive()
    assert janela.pagina_musica._relogio.isActive()

    janela.pagina_musica.onda.definir_tocando(True)
    app.processEvents()
    assert janela.pagina_musica.onda._timer.isActive()

    janela.selecionar_pagina("sistema")
    app.processEvents()
    assert not janela.pagina_musica._relogio.isActive()
    assert not janela.pagina_musica.onda._timer.isActive()
    assert not janela.painel_lateral._relogio_musica.isActive()
    janela.close()


def test_dashboard_identico_nao_reconstroi_lista_de_audio(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    pagina = PaginaMusicaM1()
    dashboard = {
        "music": {
            "audio_output": {
                "name": "Realtek",
                "source": "padrão do sistema",
                "available": True,
                "selected_ref": "1111111111111111",
                "switch_available": True,
                "devices": [
                    {
                        "ref": "1111111111111111",
                        "name": "Realtek",
                        "selected": True,
                    },
                    {
                        "ref": "2222222222222222",
                        "name": "Fones",
                        "selected": False,
                    },
                ],
            },
        },
        "system": {},
        "routines": {},
    }
    pagina.aplicar_dashboard(dashboard)
    mutacoes: list[str] = []
    modelo = pagina.audio_lista.model()
    modelo.rowsRemoved.connect(lambda *_args: mutacoes.append("remove"))
    modelo.rowsInserted.connect(lambda *_args: mutacoes.append("insert"))

    pagina.aplicar_dashboard(dashboard)
    app.processEvents()

    assert mutacoes == []
    assert pagina.audio_lista.count() == 2
    pagina.close()


def test_propriedade_visual_inalterada_nao_repolimenta(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QLabel
    from cliente.terminal_2.acabamento import definir_propriedades_visuais

    _app = QApplication.instance() or QApplication([])
    rotulo = QLabel()

    assert definir_propriedades_visuais(rotulo, state="online") is True
    assert definir_propriedades_visuais(rotulo, state="online") is False
    assert rotulo.property("state") == "online"


def test_responsividade_ignora_estado_visual_inalterado(monkeypatch) -> None:
    _app, _worker, janela = _janela(monkeypatch)
    chamadas: list[None] = []
    monkeypatch.setattr(
        janela,
        "_aplicar_sidebar",
        lambda: chamadas.append(None),
    )
    janela._assinatura_responsividade = None

    janela._aplicar_responsividade()
    janela._aplicar_responsividade()

    assert len(chamadas) == 1
    janela.close()


def test_troca_de_pagina_nao_aplica_efeito_na_superficie_inteira(
    monkeypatch,
) -> None:
    app, _worker, janela = _janela(monkeypatch)
    janela._interface_animavel = True

    janela.selecionar_pagina("automacao")
    app.processEvents()

    assert janela._animacao_indicador_nav is not None
    assert janela.pagina_automacao.graphicsEffect() is None
    assert janela._animacao_pagina_grupo is None
    janela.close()


def test_historico_de_eventos_tem_crescimento_limitado(monkeypatch) -> None:
    _app, _worker, janela = _janela(monkeypatch)

    assert 0 < janela.eventos.document().maximumBlockCount() <= 300
    janela.close()

from __future__ import annotations

import pytest


def _pagina(monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    pagina = PaginaMusicaM1()
    pagina.resize(1420, 820)
    pagina.show()
    app.processEvents()
    pagina.definir_conectada(True)
    return app, pagina


def _dashboard() -> dict:
    return {
        "music": {
            "title": "Anoitecer em Shibuya",
            "channel": "Katsu · City Lights",
            "artwork_url": "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg",
            "state": "playing",
            "position_seconds": 84,
            "duration_seconds": 225,
            "playlist": "Foco noturno",
            "controls_available": True,
            "freshness": "fresh",
            "observed_at": 1_000,
            "queue": [
                {
                    "title": "Reflexos de Neon", "channel": "Lofi Sleep",
                    "duration_seconds": 192,
                    "artwork_url": "https://i.ytimg.com/vi/zyxwvutsrqp/hqdefault.jpg",
                },
                {
                    "title": "Cidade Adormecida", "channel": "Tuyo",
                    "duration_seconds": 241, "artwork_url": "",
                },
            ],
            "queue_freshness": "fresh",
            "queue_observed_at": 1_000,
            "catalog": [
                {"name": "Anime", "count": 42, "artwork_url": ""},
                {"name": "Rock", "count": 36, "artwork_url": ""},
            ],
            "catalog_available": True,
            "catalog_play_available": True,
            "catalog_observed_at": 1_000,
        },
        "system": {
            "cpu_percent": {"value": 18, "unit": "%"},
            "ram_percent": {"value": 42, "unit": "%"},
            "disk_percent": {"value": 61, "unit": "%"},
            "temperature_c": {"value": None, "unit": "°C"},
            "uptime_seconds": {"value": 3_720, "unit": "s"},
        },
        "routines": {
            "freshness": "fresh",
            "items": [{"name": "Dormir", "time": "23:30"}],
        },
    }


def test_m1_monta_composicao_visual_sem_dados_ficticios(monkeypatch) -> None:
    app, pagina = _pagina(monkeypatch)

    assert pagina.player.objectName() == "musicHero"
    assert pagina.fila.objectName() == "musicQueue"
    assert pagina.playlists is not None
    assert pagina.contexto is not None
    assert pagina.audio is not None
    assert pagina.audicao is not None
    assert pagina.luzes is not None
    assert pagina.letra.objectName() == "musicLyrics"
    assert pagina.sistema is not None
    assert pagina.rotinas is not None
    assert pagina.acoes.minimumHeight() >= 46
    assert pagina.fila_estado.text() == "Aguardando a fila observada do YouTube."
    assert not any(botao.isEnabled() for botao in pagina.preset_botoes)
    assert not pagina.acoes_sessao["Tocar playlist"].isEnabled()
    assert not pagina.acoes_sessao["Volume —"].isEnabled()
    assert not pagina.acoes_sessao["Sincronizar luzes"].isEnabled()
    pagina.close()
    app.processEvents()


def test_m1_aplica_player_sistema_e_rotina_reais(monkeypatch) -> None:
    monkeypatch.setattr("cliente.terminal_2.musica_m1.time.time", lambda: 1_002)
    app, pagina = _pagina(monkeypatch)
    pagina.aplicar_dashboard(_dashboard())
    app.processEvents()

    assert pagina.titulo.text() == "Anoitecer em Shibuya"
    assert pagina.tempo.text() == "1:26 / 3:45"
    assert pagina.selo.text() == "TOCANDO AGORA"
    assert pagina.botoes["media_toggle"].isEnabled()
    assert pagina.acoes_sessao["Pausar"].isEnabled()
    assert pagina.sistema_valores["cpu_percent"].text() == "18%"
    assert pagina.sistema_valores["temperature_c"].text() == "—"
    assert not pagina.rotinas_estado.isVisible()
    assert pagina.rotinas_linhas[0]["name"].text() == "Dormir"
    assert pagina.rotinas_linhas[0]["time"].text() == "23:30"
    pagina.close()
    app.processEvents()


def test_m1_exibe_agendamento_unico_ao_lado_das_rotinas(monkeypatch) -> None:
    app, pagina = _pagina(monkeypatch)
    retrato = _dashboard()
    retrato["routines"]["items"] = [{
        "name": "Revisar o resultado do roteiro",
        "time": "11:00",
        "date": "2026-08-15",
        "days": [],
        "active": True,
        "can_disable": True,
    }]

    pagina.aplicar_dashboard(retrato)
    app.processEvents()

    assert not pagina.rotinas_estado.isVisible()
    assert pagina.rotinas_linhas[0]["name"].text() == "Revisar o resultado do roteiro"
    assert pagina.rotinas_linhas[0]["time"].text() == "15/08 · 11:00"
    pagina.close()
    app.processEvents()


def test_m1_novo_dashboard_nao_rebobina_relogio_local(monkeypatch) -> None:
    relogio = {"agora": 1_002.0}
    monkeypatch.setattr(
        "cliente.terminal_2.musica_m1.time.time",
        lambda: relogio["agora"],
    )
    app, pagina = _pagina(monkeypatch)
    retrato = _dashboard()
    pagina.aplicar_dashboard(retrato)
    assert pagina.tempo.text() == "1:26 / 3:45"

    relogio["agora"] = 1_007.0
    pagina.aplicar_dashboard(retrato)
    assert pagina.tempo.text() == "1:31 / 3:45"
    pagina.close()
    app.processEvents()


def test_capa_youtube_tem_fallbacks_da_mesma_faixa() -> None:
    pytest.importorskip("PySide6")
    from cliente.terminal_2.acabamento import variantes_capa_youtube

    urls = variantes_capa_youtube(
        "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg",
    )
    assert urls == (
        "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg",
        "https://i.ytimg.com/vi/abcdefghijk/maxresdefault.jpg",
        "https://i.ytimg.com/vi/abcdefghijk/mqdefault.jpg",
        "https://i.ytimg.com/vi/abcdefghijk/0.jpg",
    )
    assert variantes_capa_youtube("https://exemplo.com/capa.jpg") == ()


def test_m2_exibe_fila_e_catalogo_reais_e_envia_playlist_pela_mente(
    monkeypatch,
) -> None:
    monkeypatch.setattr("cliente.terminal_2.musica_m1.time.time", lambda: 1_000)
    app, pagina = _pagina(monkeypatch)
    pagina.aplicar_dashboard(_dashboard())
    pedidos: list[tuple[str, str]] = []
    pagina.acao_solicitada.connect(
        lambda acao, texto: pedidos.append((acao, texto)),
    )
    app.processEvents()

    assert pagina.fila_linhas[0]["title"].text() == "Reflexos de Neon"
    assert pagina.fila_linhas[0]["duration"].text() == "3:12"
    assert pagina.preset_botoes[0].titulo.text() == "Anime"
    assert pagina.preset_botoes[0].quantidade.text() == "42 faixas"
    assert pagina.preset_botoes[0].isEnabled()
    pagina.preset_botoes[0].click()

    assert pedidos == [
        ("playlist_play", "toca a playlist Anime"),
    ]
    pagina.close()
    app.processEvents()


def test_m2_nao_habilita_playlist_sem_capacidade_confirmada(monkeypatch) -> None:
    app, pagina = _pagina(monkeypatch)
    retrato = _dashboard()
    retrato["music"]["catalog_play_available"] = False
    pagina.aplicar_dashboard(retrato)

    assert pagina.preset_botoes[0].isVisible()
    assert not pagina.preset_botoes[0].isEnabled()
    pagina.close()
    app.processEvents()


def test_m1_controles_reais_usam_o_canal_canonico(monkeypatch) -> None:
    app, pagina = _pagina(monkeypatch)
    pagina.aplicar_dashboard(_dashboard())
    recebidos: list[tuple[str, str]] = []
    pagina.acao_solicitada.connect(
        lambda acao, texto: recebidos.append((acao, texto)),
    )

    pagina.botoes["media_toggle"].click()
    pagina.acoes_sessao["Próxima faixa"].click()

    assert recebidos == [
        ("media_toggle", "pausa a música"),
        ("media_next", "vai para a próxima música"),
    ]
    pagina.close()
    app.processEvents()


def test_m1_reorganiza_em_uma_coluna_sem_perder_modulos(monkeypatch) -> None:
    app, pagina = _pagina(monkeypatch)
    pagina.resize(760, 900)
    app.processEvents()

    assert pagina._modo_compacto is True
    assert pagina.grade.indexOf(pagina.player) >= 0
    assert pagina.grade.indexOf(pagina.fila) >= 0
    assert pagina.grade.indexOf(pagina.barra_lateral) >= 0
    assert pagina.grade.indexOf(pagina.letra) >= 0
    ultimo = pagina._botoes_sessao[-1]
    linha, coluna, _linhas, _colunas = pagina.acoes_layout.getItemPosition(
        pagina.acoes_layout.indexOf(ultimo),
    )
    assert (linha, coluna) == (3, 0)
    pagina.close()
    app.processEvents()

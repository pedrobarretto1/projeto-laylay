from __future__ import annotations

from pathlib import Path

import pytest

from mente_laylay.integracao.chrome_ws_handlers import handle_player_event
from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
from mente_laylay.integracao.desktop_bridge import (
    ErroProtocoloDesktop,
    classificar_resultado_acao,
    sanitizar_dashboard_estado,
    validar_mensagem_cliente,
)
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


class _Percentual:
    percent = 25.0


class _Psutil:
    @staticmethod
    def cpu_percent(*, interval=None):
        return 10.0

    @staticmethod
    def virtual_memory():
        return _Percentual()

    @staticmethod
    def disk_usage(_raiz):
        return _Percentual()

    @staticmethod
    def boot_time():
        return 500.0


def _runtime(**trocas) -> DashboardTerminalRuntime:
    base = {
        "configuracao_getter": lambda: {},
        "llm_getter": lambda: {},
        "interacao_getter": lambda: {},
        "memoria_saude_getter": lambda: {
            "disponivel": True, "persistencia_local": True,
        },
        "agenda_getter": lambda: [],
        "aprendizados_getter": lambda **_kwargs: [],
        "estado_mental_getter": lambda: {},
        "contexto_jogo_getter": lambda: {},
        "psutil_mod": _Psutil,
        "clock": lambda: 1_000.0,
        "log": lambda _texto: None,
    }
    base.update(trocas)
    return DashboardTerminalRuntime(**base)


def test_player_event_publica_estado_observado_sem_executar_controle() -> None:
    estado: dict = {}
    handle_player_event(
        {
            "event": "player_state", "title": "Faixa Teste - YouTube",
            "channel": "Canal", "videoId": "abcdefghijk",
            "url": "https://www.youtube.com/watch?v=abcdefghijk",
            "state": "playing", "currentTime": 42.0, "duration": 180.0,
            "tabId": 8,
        },
        playlist_state=estado,
        yt_clean_url=None,
        playlist_avancar_proxima=None,
        falar_com_lipsync=None,
    )

    assert estado["player"] == {
        "title": "Faixa Teste",
        "channel": "Canal",
        "video_id": "abcdefghijk",
        "url": "https://www.youtube.com/watch?v=abcdefghijk",
        "state": "playing",
        "position_seconds": 42.0,
        "duration_seconds": 180.0,
        "observed_at": pytest.approx(estado["player"]["observed_at"]),
        "controls_available": True,
        "_priority": 280,
        "_source_observed_at": 0.0,
        "source": "",
        "tab_id": 8,
    }
    assert estado["tab_id"] == 8


def test_extensao_sem_player_limpa_so_estado_efemero_da_sessao_anterior() -> None:
    estado = {
        "name": "Descanso", "index": 2,
        "tab_id": 8,
        "player": {
            "title": "Faixa antiga", "state": "playing",
            "observed_at": 123,
        },
    }
    handle_player_event(
        {"event": "player_unavailable", "observedAt": 456},
        playlist_state=estado,
        yt_clean_url=None,
        playlist_avancar_proxima=None,
        falar_com_lipsync=None,
    )

    assert "player" not in estado
    assert "tab_id" not in estado
    assert estado["name"] == "Descanso"
    assert estado["index"] == 2


def test_aba_pausada_nao_sobrescreve_faixa_audivel_recente(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "mente_laylay.integracao.chrome_ws_handlers.time.time", lambda: 1_000.0,
    )
    estado: dict = {}
    comum = {
        "event": "player_state",
        "duration": 180,
        "observedAt": 50_000,
    }
    handle_player_event(
        {
            **comum, "title": "Faixa certa", "channel": "Canal",
            "videoId": "abcdefghijk", "state": "playing", "currentTime": 42,
            "tabId": 8, "source": "audible_youtube_tab",
            "audibleConfirmed": True, "playingConfirmed": True,
        },
        playlist_state=estado, yt_clean_url=None,
        playlist_avancar_proxima=None, falar_com_lipsync=None,
    )
    handle_player_event(
        {
            **comum, "title": "Faixa velha", "channel": "Outro canal",
            "videoId": "zyxwvutsrqp", "state": "paused", "currentTime": 9,
            "tabId": 12, "source": "youtube_tab_fallback",
            "observedAt": 50_100,
        },
        playlist_state=estado, yt_clean_url=None,
        playlist_avancar_proxima=None, falar_com_lipsync=None,
    )

    assert estado["player"]["title"] == "Faixa certa"
    assert estado["player"]["tab_id"] == 8


def test_mesma_aba_atualiza_faixa_e_descarta_retrato_atrasado(monkeypatch) -> None:
    monkeypatch.setattr(
        "mente_laylay.integracao.chrome_ws_handlers.time.time", lambda: 1_000.0,
    )
    estado: dict = {}

    def publicar(titulo: str, video_id: str, observado: float) -> None:
        handle_player_event(
            {
                "event": "player_state", "title": titulo,
                "videoId": video_id, "state": "playing", "tabId": 8,
                "source": "playing_youtube_tab", "playingConfirmed": True,
                "observedAt": observado, "duration": 180,
            },
            playlist_state=estado, yt_clean_url=None,
            playlist_avancar_proxima=None, falar_com_lipsync=None,
        )

    publicar("Faixa nova", "abcdefghijk", 60_000)
    publicar("Faixa atrasada", "zyxwvutsrqp", 59_000)

    assert estado["player"]["title"] == "Faixa nova"
    assert estado["player"]["video_id"] == "abcdefghijk"


def test_heartbeat_incompleto_nao_zera_tempo_capa_ou_duracao(monkeypatch) -> None:
    instantes = iter((1_000.0, 1_005.0))
    monkeypatch.setattr(
        "mente_laylay.integracao.chrome_ws_handlers.time.time",
        lambda: next(instantes),
    )
    estado: dict = {}
    comum = {
        "event": "player_state",
        "title": "Faixa contínua",
        "url": "https://www.youtube.com/watch?v=abcdefghijk",
        "state": "playing",
        "tabId": 8,
        "source": "playing_youtube_tab",
        "playingConfirmed": True,
    }
    handle_player_event(
        {
            **comum, "currentTime": 80, "duration": 200,
            "observedAt": 50_000, "positionReliable": True,
        },
        playlist_state=estado, yt_clean_url=None,
        playlist_avancar_proxima=None, falar_com_lipsync=None,
    )
    handle_player_event(
        {**comum, "currentTime": 0, "duration": 0, "observedAt": 55_000},
        playlist_state=estado, yt_clean_url=None,
        playlist_avancar_proxima=None, falar_com_lipsync=None,
    )

    assert estado["player"]["video_id"] == "abcdefghijk"
    assert estado["player"]["position_seconds"] == pytest.approx(85.0)
    assert estado["player"]["duration_seconds"] == 200.0


def test_dashboard_recupera_capa_pela_url_quando_id_nao_chega() -> None:
    runtime = _runtime(musica_getter=lambda: {
        "player": {
            "title": "Faixa", "state": "paused",
            "url": "https://youtu.be/abcdefghijk?t=10",
            "position_seconds": 10, "duration_seconds": 200,
            "observed_at": 999, "controls_available": True,
        },
    })

    musica = runtime._musica(1_000.0)
    assert musica["artwork_url"] == (
        "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg"
    )


def test_cpu_usa_amostra_limitada_e_nao_primeira_leitura_por_thread() -> None:
    class PsutilCpuAmostrado(_Psutil):
        intervalos: list[float | None] = []

        @classmethod
        def cpu_percent(cls, *, interval=None):
            cls.intervalos.append(interval)
            return 37.0 if interval == 0.1 else 0.0

    runtime = _runtime(psutil_mod=PsutilCpuAmostrado)
    sistema = runtime._sistema(1_000.0, {})

    assert sistema["cpu_percent"]["value"] == 37.0
    assert 0.1 in PsutilCpuAmostrado.intervalos


def test_m2_evento_publica_fila_observada_e_sanitizada(monkeypatch) -> None:
    monkeypatch.setattr(
        "mente_laylay.integracao.chrome_ws_handlers.time.time", lambda: 1_000.0,
    )
    estado: dict = {}
    handle_player_event(
        {
            "event": "player_state", "title": "Atual",
            "videoId": "abcdefghijk", "state": "playing", "tabId": 8,
            "currentTime": 20, "duration": 200,
            "positionReliable": True, "queueObserved": True,
            "queue": [
                {
                    "title": " Próxima   faixa ", "channel": " Canal ",
                    "videoId": "zyxwvutsrqp", "durationSeconds": 192,
                    "url": "https://nao-deve-vazar.example",
                },
                {"title": "", "videoId": "invalido"},
            ],
        },
        playlist_state=estado, yt_clean_url=None,
        playlist_avancar_proxima=None, falar_com_lipsync=None,
    )

    assert estado["player"]["queue"] == [{
        "title": "Próxima faixa", "channel": "Canal",
        "video_id": "zyxwvutsrqp", "duration_seconds": 192.0,
    }]
    assert estado["player"]["queue_observed_at"] == 1_000.0


def test_m2_dashboard_publica_catalogo_cacheado_e_fila_observada() -> None:
    runtime = _runtime(
        musica_getter=lambda: {
            "player": {
                "title": "Atual", "state": "playing", "video_id": "abcdefghijk",
                "observed_at": 999, "controls_available": True,
                "queue_observed_at": 999,
                "queue": [{
                    "title": "Próxima", "channel": "Canal",
                    "video_id": "zyxwvutsrqp", "duration_seconds": 192,
                }],
            },
        },
        playlists_getter=lambda: [
            {
                "name": "Rock", "count": 3,
                "artwork_video_id": "abcdefghijk",
                "path": "C:\\privado\\playlists.json",
            },
            {
                "name": "Rock e apaga Downloads", "count": 1,
                "artwork_video_id": "zyxwvutsrqp",
            },
        ],
        capacidade_getter=lambda intent: {
            "disponivel": intent == "PLAYLIST_PLAY", "estado": "disponivel",
        },
    )

    musica = runtime._musica(1_000.0)
    assert musica["queue"][0]["title"] == "Próxima"
    assert musica["queue_freshness"] == "fresh"
    assert musica["catalog"] == [{
        "name": "Rock", "count": 3,
        "artwork_url": "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg",
    }]
    assert musica["catalog_play_available"] is True
    assert "path" not in str(musica)


def test_m2_catalogo_publico_nao_rele_disco_nem_expoe_itens() -> None:
    runtime = PlaylistRuntime(
        state_file="nao_usado.json", legacy_file="nao_usado_legado.json",
        cache={
            "Rock": [{
                "url": "https://www.youtube.com/watch?v=abcdefghijk",
                "titulo": "Faixa privada", "canal": "Canal",
            }],
        },
        ultima_playlist_getter=lambda: "",
    )

    assert runtime.catalogo_publico() == [{
        "name": "Rock", "count": 1, "artwork_video_id": "abcdefghijk",
    }]


def test_m2_sanitizador_remove_campos_privados_da_fila_e_catalogo() -> None:
    publico = sanitizar_dashboard_estado({
        "status": "ok", "generated_at": 1_000, "sequence": 1,
        "music": {
            "state": "playing", "freshness": "fresh", "observed_at": 1_000,
            "queue_freshness": "fresh", "queue_observed_at": 1_000,
            "queue": [{
                "title": "Próxima", "channel": "Canal", "duration_seconds": 90,
                "artwork_url": "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg",
                "url": "https://segredo.example", "video_id": "abcdefghijk",
            }],
            "catalog_available": True, "catalog_play_available": True,
            "catalog_observed_at": 1_000,
            "catalog": [{
                "name": "Rock", "count": 1,
                "artwork_url": "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg",
                "items": ["não pode atravessar"],
            }],
        },
    })

    assert publico["music"]["queue"][0] == {
        "title": "Próxima", "channel": "Canal", "duration_seconds": 90.0,
        "artwork_url": "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg",
    }
    assert publico["music"]["catalog"][0] == {
        "name": "Rock", "count": 1,
        "artwork_url": "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg",
    }


def test_dashboard_projeta_player_e_so_rotina_recorrente_confirmada() -> None:
    runtime = _runtime(
        musica_getter=lambda: {
            "player": {
                "title": "Peaceful Mind", "channel": "Lo-Fi Chill",
                "state": "playing", "position_seconds": 84,
                "duration_seconds": 225, "observed_at": 999,
                "controls_available": True,
            },
            "playlist": "Descanso",
        },
        agenda_getter=lambda: [
            {
                "ativo": True, "tipo": "weekly", "nome": "Acordar",
                "hora": "07:00", "dias": ["seg", "qua", "sex"],
                "origem": "pedido_usuario", "evidencia": "persistencia_local",
            },
            {
                "ativo": True, "tipo": "once", "nome": "Não é rotina",
                "origem": "pedido_usuario", "evidencia": "persistencia_local",
            },
            {
                "ativo": True, "tipo": "daily", "nome": "Automação interna",
                "hora": "08:00", "origem": "sistema",
                "evidencia": "persistencia_local",
            },
        ],
    )

    musica = runtime._musica(1_000.0)
    rotinas = runtime._rotinas_publicas(1_000.0)

    assert musica["state"] == "playing"
    assert musica["controls_available"] is True
    assert musica["playlist"] == "Descanso"
    assert rotinas["items"] == [{
        "name": "Acordar", "time": "07:00",
        "days": ["seg", "qua", "sex"],
        "active": True, "can_disable": True,
    }]


def test_dashboard_expira_player_sem_congelar_faixa_tempo_ou_controles() -> None:
    runtime = _runtime(
        musica_getter=lambda: {
            "player": {
                "title": "Faixa antiga", "channel": "Canal",
                "state": "playing", "position_seconds": 84,
                "duration_seconds": 225, "observed_at": 960,
                "controls_available": True,
            },
        },
    )

    musica = runtime._musica(1_000.0)

    assert musica["freshness"] == "unavailable"
    assert musica["title"] == ""
    assert musica["position_seconds"] == 0.0
    assert musica["duration_seconds"] == 0.0
    assert musica["controls_available"] is False


def test_sanitizador_p4_remove_payload_e_nao_habilita_player_antigo() -> None:
    publico = sanitizar_dashboard_estado({
        "music": {
            "title": "Faixa", "channel": "Canal", "state": "playing",
            "position_seconds": 3, "duration_seconds": 10,
            "observed_at": 100, "freshness": "stale",
            "controls_available": True,
            "url": "https://youtube.com/segredo", "tab_id": 42,
        },
        "routines": {
            "observed_at": 100, "freshness": "fresh",
            "items": [{
                "name": "Dormir", "time": "23:30", "days": ["todos"],
                "active": True, "can_disable": True,
                "id": "privado", "comandos_no_disparo": [{"token": "x"}],
            }],
        },
    })

    assert publico["music"]["controls_available"] is False
    assert publico["music"]["freshness"] == "stale"
    assert "url" not in publico["music"] and "tab_id" not in publico["music"]
    assert publico["routines"]["items"] == [{
        "name": "Dormir", "time": "23:30", "days": ["todos"],
        "active": True, "can_disable": True,
    }]
    assert "privado" not in str(publico)


def test_protocolo_p4_aceita_so_acoes_de_painel_registradas() -> None:
    valido = validar_mensagem_cliente(
        {
            "type": "input_submit", "id": "1", "text": "pausa a música",
            "kind": "panel_action", "action": "media_toggle",
        },
        token="x", autenticado=True,
    )
    assert valido["kind"] == "panel_action"
    playlist = validar_mensagem_cliente(
        {
            "type": "input_submit", "id": "playlist-1",
            "text": "toca a playlist Rock",
            "kind": "panel_action", "action": "playlist_play",
        },
        token="x", autenticado=True,
    )
    assert playlist["action"] == "playlist_play"
    with pytest.raises(ErroProtocoloDesktop, match="ação de painel inválida"):
        validar_mensagem_cliente(
            {
                "type": "input_submit", "id": "2", "text": "faz isso",
                "kind": "panel_action", "action": "desliga_seguranca",
            },
            token="x", autenticado=True,
        )
    assert classificar_resultado_acao(
        {"comandos": [{
            "intent": "MEDIA_CONTROL", "executou": True, "confirmado": None,
        }]},
        acao_id="media_toggle",
    )["state"] == "partial"
    assert classificar_resultado_acao(
        {"comandos": [{
            "intent": "PLAYLIST_PLAY", "executou": True, "confirmado": True,
        }]},
        acao_id="playlist_play",
    )["state"] == "confirmed"


def _criar_janela(monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_laylay_2 import JanelaLaylay

    class Worker(QObject):
        mensagem = Signal(dict)
        conectado = Signal(bool)
        falha = Signal(str)

        def __init__(self) -> None:
            super().__init__()
            self.enviadas: list[dict] = []

        def enfileirar(self, mensagem: dict) -> bool:
            self.enviadas.append(dict(mensagem))
            return True

        def parar(self) -> None:
            pass

    app = QApplication.instance() or QApplication([])
    worker = Worker()
    janela = JanelaLaylay(worker, Path(__file__).parents[1])
    janela.show()
    worker.conectado.emit(True)
    app.processEvents()
    return app, worker, janela


def _dashboard_ui() -> dict:
    return sanitizar_dashboard_estado({
        "schema_version": 1, "generated_at": 1_000, "sequence": 1,
        "health": {
            "memory": {"state": "online", "label": "Ativa", "freshness": "fresh", "observed_at": 1_000},
        },
        "context": {
            "project": "Laylay", "mode": "Local", "city": "Boituva",
            "game_active": True, "game_name": "Minecraft",
            "freshness": "fresh", "observed_at": 1_000,
        },
        "music": {
            "title": "Peaceful Mind", "channel": "Lo-Fi Chill",
            "state": "playing", "position_seconds": 84,
            "duration_seconds": 225, "controls_available": True,
            "freshness": "fresh", "observed_at": 1_000,
        },
        "routines": {
            "freshness": "fresh", "observed_at": 1_000,
            "items": [{
                "name": "Dormir", "time": "23:30", "days": ["todos"],
                "active": True, "can_disable": True,
            }],
        },
        "memory_recent": [{
            "kind": "preference", "summary": "Você prefere rock",
            "detail": "Confirmado por você", "source": "user_confirmed",
        }],
        "system": {
            chave: {
                "value": valor, "freshness": "fresh", "observed_at": 1_000,
            }
            for chave, valor in {
                "cpu_percent": 18, "ram_percent": 42,
                "disk_percent": 61, "uptime_seconds": 3_600,
            }.items()
        },
    })


def test_ui_p4_exibe_estado_real_e_envia_controle_canonico(monkeypatch) -> None:
    monkeypatch.setattr("cliente.terminal_2.musica_m1.time.time", lambda: 1_000)
    app, worker, janela = _criar_janela(monkeypatch)
    janela._atualizar_dashboard(_dashboard_ui())
    app.processEvents()

    assert janela.pagina_musica.titulo.text() == "Peaceful Mind"
    assert janela.pagina_musica.tempo.text() == "1:24 / 3:45"
    assert janela.pagina_musica.botoes["media_toggle"].isEnabled()
    assert janela.pagina_automacao.jogo_estado.text() == "Ativo · Minecraft"
    assert janela.pagina_automacao.rotina_botoes[0].text().startswith("Dormir · 23:30")
    assert janela.pagina_sistema.valores["cpu"].text() == "18%"

    janela.pagina_musica.botoes["media_toggle"].click()
    app.processEvents()
    enviado = next(
        item for item in reversed(worker.enviadas)
        if item.get("type") == "input_submit"
    )
    assert enviado == {
        "type": "input_submit", "id": enviado["id"],
        "text": "pausa a música", "kind": "panel_action",
        "action": "media_toggle",
        "payload": {"command": "pause"},
    }
    # O clique não inventa uma pausa antes do novo snapshot observado.
    assert janela.pagina_musica._estado_observado == "playing"
    janela.close()


def test_ui_p4_relogio_avanca_e_expiracao_bloqueia_controles(monkeypatch) -> None:
    monkeypatch.setattr("cliente.terminal_2.dashboard.time.time", lambda: 1_002.0)
    app, _worker, janela = _criar_janela(monkeypatch)
    janela._atualizar_dashboard(_dashboard_ui())

    janela.pagina_musica._atualizar_relogio()
    janela.painel_lateral._atualizar_relogio_musica()
    assert janela.pagina_musica.tempo.text() == "1:26 / 3:45"
    assert janela.pagina_musica.botoes["media_toggle"].isEnabled()

    monkeypatch.setattr("cliente.terminal_2.dashboard.time.time", lambda: 1_013.0)
    janela.pagina_musica._atualizar_relogio()
    janela.painel_lateral._atualizar_relogio_musica()
    assert not janela.pagina_musica.botoes["media_toggle"].isEnabled()
    assert not janela.painel_lateral.musica_botoes["media_toggle"].isEnabled()
    janela.close()


def test_ui_p4_rotina_permanece_ativa_ate_snapshot_confirmar(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    janela._atualizar_dashboard(_dashboard_ui())
    botao = janela.pagina_automacao.rotina_botoes[0]
    botao.click()
    app.processEvents()

    enviado = next(
        item for item in reversed(worker.enviadas)
        if item.get("type") == "input_submit"
    )
    assert enviado["kind"] == "panel_action"
    assert enviado["action"] == "routine_cancel"
    assert enviado["text"] == "cancela o agendamento Dormir"
    assert janela.pagina_automacao._rotinas[0]["active"] is True
    janela.close()

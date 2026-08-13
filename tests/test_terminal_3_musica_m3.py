from __future__ import annotations

import pytest

from mente_laylay.autonomia.detectores_playlist import detectar_playlist_usuario
from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
from mente_laylay.integracao.chrome_ws_handlers import handle_player_event
from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
from mente_laylay.integracao.desktop_bridge import (
    classificar_resultado_acao,
    sanitizar_dashboard_estado,
)
from mente_laylay.memoria_mental.playlist_mental import limpar_nome_playlist


class _Percentual:
    percent = 20.0


class _Psutil:
    @staticmethod
    def cpu_percent(*, interval=None): return 10.0

    @staticmethod
    def virtual_memory(): return _Percentual()

    @staticmethod
    def disk_usage(_raiz): return _Percentual()

    @staticmethod
    def boot_time(): return 500.0


def _runtime(**trocas) -> DashboardTerminalRuntime:
    valores = {
        "configuracao_getter": lambda: {},
        "llm_getter": lambda: {},
        "interacao_getter": lambda: {},
        "memoria_saude_getter": lambda: {},
        "agenda_getter": lambda: [],
        "aprendizados_getter": lambda **_kwargs: [],
        "estado_mental_getter": lambda: {},
        "contexto_jogo_getter": lambda: {},
        "capacidade_getter": lambda intent: {
            "disponivel": intent in {
                "MEDIA_CONTROL", "PLAYLIST_PLAY", "TOCAR_PLAYLIST_SHUFFLE",
            },
            "estado": "disponivel",
        },
        "musica_getter": lambda: {
            "playlist": "Rock",
            "player": {
                "title": "Faixa", "channel": "Canal",
                "state": "playing", "observed_at": 1_000.0,
                "controls_available": True, "volume_percent": 35,
                "muted": False, "repeat_enabled": True,
            },
        },
        "playlists_getter": lambda: [{"name": "Rock", "count": 3}],
        "volume_getter": lambda: 42,
        "audio_output_getter": lambda: {
            "name": "Alto-falantes Realtek", "source": "padrão do sistema",
        },
        "iot_getter": lambda: {"dispositivos": [{
            "tipo": "lampada_rgb", "capacidades": ["ajustar_cor"],
        }]},
        "psutil_mod": _Psutil,
        "clock": lambda: 1_000.0,
        "log": lambda _texto: None,
    }
    valores.update(trocas)
    return DashboardTerminalRuntime(**valores)


def test_player_event_preserva_volume_e_mudo_observados() -> None:
    estado: dict = {}
    handle_player_event(
        {
            "event": "player_state", "title": "Faixa", "state": "playing",
            "currentTime": 10, "duration": 100, "volumePercent": 37,
            "muted": True, "repeatEnabled": True, "tabId": 7,
        },
        playlist_state=estado,
        yt_clean_url=None,
        playlist_avancar_proxima=None,
        falar_com_lipsync=None,
    )

    assert estado["player"]["volume_percent"] == 37
    assert estado["player"]["muted"] is True
    assert estado["player"]["repeat_enabled"] is True


def test_dashboard_m3_publica_apenas_estado_real_e_capacidades_vivas() -> None:
    musica = _runtime()._musica(1_000.0)

    assert musica["volume_percent"] == 42
    assert musica["player_volume_percent"] == 35
    assert musica["replay_available"] is True
    assert musica["repeat_enabled"] is True
    assert musica["repeat_available"] is True
    assert musica["shuffle_available"] is True
    assert musica["audio_output"] == {
        "name": "Alto-falantes Realtek",
        "source": "padrão do sistema",
        "available": True,
        "selected_ref": "",
        "switch_available": False,
        "devices": [],
        "observed_at": 0.0,
    }
    assert musica["lights"] == {
        "configured": True,
        "sync_available": False,
    }


def test_bridge_m3_remove_campos_extras_e_preserva_indisponibilidade() -> None:
    retrato = sanitizar_dashboard_estado({
        "generated_at": 1_000,
        "music": {
            **_runtime()._musica(1_000),
            "audio_output": {
                "name": "Realtek", "source": "padrão do sistema",
                "available": True, "device_id": "segredo",
            },
            "lights": {
                "configured": True, "sync_available": False,
                "token": "segredo",
            },
        },
    })

    assert retrato["music"]["volume_percent"] == 42
    assert retrato["music"]["audio_output"] == {
        "name": "Realtek", "source": "padrão do sistema", "available": True,
        "selected_ref": "", "switch_available": False,
        "devices": [], "observed_at": 0.0,
    }
    assert retrato["music"]["lights"] == {
        "configured": True, "sync_available": False,
    }


def test_linguagem_natural_m3_entende_replay_e_shuffle() -> None:
    replay = detectar_volume_ou_midia(
        "reinicia essa música", params_cb=lambda **kwargs: kwargs,
        contexto_musical_ativo=True,
    )
    repeat = detectar_volume_ou_midia(
        "alterna a repetição da música", params_cb=lambda **kwargs: kwargs,
        contexto_musical_ativo=True,
    )
    shuffle = detectar_playlist_usuario(
        "toca a playlist rock em modo aleatório",
        "toca a playlist Rock em modo aleatório",
        params_cb=lambda **kwargs: kwargs,
        limpar_nome_playlist=limpar_nome_playlist,
        extrair_nome_playlist=lambda _texto: "",
    )

    assert replay == {"intent": "MEDIA_CONTROL", "params": {"acao": "replay"}}
    assert repeat == {
        "intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle"},
    }
    assert shuffle == {
        "intent": "PLAYLIST_PLAY",
        "params": {"nome_playlist": "rock", "modo": "shuffle"},
    }


def test_resultado_do_shuffle_visual_usa_o_intent_real_executado() -> None:
    resultado = classificar_resultado_acao(
        {"comandos": [{
            "intent": "PLAYLIST_PLAY", "status": "playlist_aberta",
            "executou": True, "confirmado": True,
        }]},
        acao_id="playlist_shuffle",
    )

    assert resultado["state"] == "confirmed"


def test_interface_m3_envia_acoes_sem_mudar_estado_antes_da_confirmacao(
    monkeypatch,
) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr("cliente.terminal_2.musica_m1.time.time", lambda: 1_000)
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    pagina = PaginaMusicaM1()
    pagina.definir_conectada(True)
    dashboard = {"music": _runtime()._musica(1_000), "system": {}, "routines": {}}
    pagina.aplicar_dashboard(dashboard)
    pedidos: list[tuple[str, str]] = []
    pagina.acao_solicitada.connect(lambda acao, texto: pedidos.append((acao, texto)))

    pagina.botoes["media_repeat"].click()
    pagina.acoes_sessao["Aleatório"].click()
    pagina.volume_slider.setValue(55)
    pagina._solicitar_volume()

    assert pedidos == [
        ("media_repeat", "alterna a repetição da música"),
        ("playlist_shuffle", "toca a playlist Rock em modo aleatório"),
        ("volume_set", "deixa o volume em 55 por cento"),
    ]
    assert pagina.volume.text() == "VOLUME\n42%"
    assert not pagina.acoes_sessao["Sincronizar luzes"].isEnabled()
    pagina.close()
    app.processEvents()

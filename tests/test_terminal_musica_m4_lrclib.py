from __future__ import annotations

import json
import time

import pytest

from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
from mente_laylay.integracao.desktop_bridge import sanitizar_dashboard_estado
from mente_laylay.integracao.letras_lrclib import (
    LRCLIB_USER_AGENT,
    LetrasLRCLibRuntime,
    analisar_lrc,
    identificar_faixa,
)


class _Resposta:
    def __init__(self, payload, *, status: int = 200, headers=None) -> None:
        self._payload = payload
        self.status_code = status
        self.headers = dict(headers or {})

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self):
        return self._payload


def test_parser_lrc_ordena_timestamps_multiplos_e_aplica_offset() -> None:
    linhas = analisar_lrc(
        "[ar:Artista]\n[offset:+250]\n[00:10.00][00:20.5] Refrão\n[00:05.25] Começo"
    )

    assert linhas == [
        {"time_seconds": 5.5, "text": "Começo"},
        {"time_seconds": 10.25, "text": "Refrão"},
        {"time_seconds": 20.75, "text": "Refrão"},
    ]


def test_identificacao_limpa_titulo_de_video_sem_apagar_nome_da_faixa() -> None:
    faixa, artista = identificar_faixa(
        "(1035) Crepúsculo dos Heróis | Frieren | Shiny Ft. @Isis",
        "Shiny_sz - Topic",
    )

    assert faixa == "Crepúsculo dos Heróis"
    assert artista == "Shiny"


def test_lrclib_identifica_cliente_escolhe_resultado_e_cacheia_por_faixa() -> None:
    chamadas: list[dict] = []

    def get(_url, **kwargs):
        chamadas.append(kwargs)
        return _Resposta([{
            "trackName": "Crepúsculo dos Heróis",
            "artistName": "Shiny",
            "duration": 249,
            "instrumental": False,
            "plainLyrics": "linha simples",
            "syncedLyrics": "[00:01.00] Primeira\n[00:03.50] Segunda",
            "payload_privado": "não atravessa",
        }])

    runtime = LetrasLRCLibRuntime(requests_get=get, clock=lambda: 1_000)
    player = {
        "title": "Crepúsculo dos Heróis | Shiny Ft. @Isis",
        "channel": "Shiny_sz", "duration_seconds": 249,
        "video_id": "abcdefghijk", "state": "playing",
    }
    try:
        assert runtime.snapshot(player)["status"] == "loading"
        limite = time.monotonic() + 1.0
        resultado = {}
        while time.monotonic() < limite:
            resultado = runtime.snapshot(player)
            if resultado.get("status") == "available":
                break
            time.sleep(0.01)
        assert resultado["synced"] is True
        assert resultado["lines"][1] == {
            "time_seconds": 3.5, "text": "Segunda",
        }
        assert chamadas[0]["headers"]["User-Agent"] == LRCLIB_USER_AGENT
        assert chamadas[0]["params"]["q"] == "Crepúsculo dos Heróis Shiny"
        assert len(chamadas) == 1
        runtime.snapshot(player)
        assert len(chamadas) == 1
    finally:
        runtime.parar()


def test_lrclib_respeita_retry_after_sem_repetir_consulta() -> None:
    chamadas = 0

    def get(_url, **_kwargs):
        nonlocal chamadas
        chamadas += 1
        return _Resposta({}, status=429, headers={"Retry-After": "120"})

    runtime = LetrasLRCLibRuntime(requests_get=get)
    player = {
        "title": "Faixa", "channel": "Artista", "duration_seconds": 180,
        "video_id": "abcdefghijk", "state": "playing",
    }
    try:
        runtime.snapshot(player)
        limite = time.monotonic() + 1.0
        while time.monotonic() < limite:
            if runtime.snapshot(player)["status"] == "rate_limited":
                break
            time.sleep(0.01)
        assert runtime.snapshot(player)["status"] == "rate_limited"
        assert chamadas == 1
    finally:
        runtime.parar()


def test_lrclib_tenta_novamente_somente_depois_do_retry_after() -> None:
    relogio = {"mono": 10.0}
    chamadas = 0

    def get(_url, **_kwargs):
        nonlocal chamadas
        chamadas += 1
        if chamadas == 1:
            return _Resposta({}, status=429, headers={"Retry-After": "2"})
        return _Resposta([{
            "trackName": "Faixa", "artistName": "Artista", "duration": 180,
            "instrumental": False, "plainLyrics": "Letra", "syncedLyrics": "",
        }])

    runtime = LetrasLRCLibRuntime(
        requests_get=get, monotonic=lambda: relogio["mono"],
    )
    player = {
        "title": "Faixa", "channel": "Artista", "duration_seconds": 180,
        "video_id": "abcdefghijk", "state": "playing",
    }
    try:
        runtime.snapshot(player)
        limite = time.monotonic() + 1.0
        while time.monotonic() < limite and chamadas < 1:
            time.sleep(0.01)
        assert chamadas == 1
        assert runtime.snapshot(player)["status"] == "rate_limited"
        relogio["mono"] = 11.9
        runtime.snapshot(player)
        time.sleep(0.03)
        assert chamadas == 1
        relogio["mono"] = 12.1
        assert runtime.snapshot(player)["status"] == "loading"
        limite = time.monotonic() + 1.0
        resultado = {}
        while time.monotonic() < limite:
            resultado = runtime.snapshot(player)
            if resultado.get("status") == "available":
                break
            time.sleep(0.01)
        assert resultado["status"] == "available"
        assert chamadas == 2
    finally:
        runtime.parar()


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


def _dashboard(**trocas) -> DashboardTerminalRuntime:
    valores = {
        "configuracao_getter": dict,
        "llm_getter": dict,
        "interacao_getter": dict,
        "memoria_saude_getter": dict,
        "agenda_getter": list,
        "aprendizados_getter": lambda **_kwargs: [],
        "estado_mental_getter": dict,
        "contexto_jogo_getter": dict,
        "capacidade_getter": lambda _intent: {
            "disponivel": True, "estado": "disponivel",
        },
        "musica_getter": lambda: {"player": {
            "title": "Faixa", "channel": "Artista", "state": "playing",
            "observed_at": 1_000, "duration_seconds": 180,
            "controls_available": True,
        }},
        "playlists_getter": lambda: [{"name": "Relaxar à noite", "count": 3}],
        "psutil_mod": _Psutil,
        "clock": lambda: 1_000.0,
        "log": lambda _texto: None,
    }
    valores.update(trocas)
    return DashboardTerminalRuntime(**valores)


def test_dashboard_m4_publica_contexto_real_e_retrato_da_lrclib() -> None:
    runtime = _dashboard(
        musica_getter=lambda: {
            "playlist": "Rock",
            "player": {
                "title": "Faixa", "channel": "Artista", "state": "playing",
                "observed_at": 1_000, "duration_seconds": 180,
                "controls_available": True,
            },
        },
        letras_getter=lambda player: {
        "status": "available", "source": "lrclib", "synced": True,
        "track_name": player["title"], "artist_name": player["channel"],
        "plain_text": "não duplica", "observed_at": 1_000,
        "lines": [{"time_seconds": 1, "text": "Linha"}],
        },
    )

    musica = runtime._musica(1_000)

    assert musica["context_music"]["basis"] == [
        "horario_local", "playlist_ativa",
    ]
    assert "Rock" in musica["context_music"]["recommendation"]
    assert musica["lyrics"]["source"] == "lrclib"
    assert musica["lyrics"]["lines"] == [{"time_seconds": 1, "text": "Linha"}]


def test_ponte_limita_letra_e_remove_campos_do_provedor() -> None:
    publico = sanitizar_dashboard_estado({
        "generated_at": 1_000,
        "music": {
            "title": "Faixa", "state": "playing", "freshness": "fresh",
            "observed_at": 1_000,
            "context_music": {
                "summary": "É noite.", "recommendation": "Playlist Rock.",
                "basis": ["horario_local", "segredo"],
                "freshness": "fresh", "observed_at": 1_000,
            },
            "lyrics": {
                "status": "available", "source": "lrclib", "synced": True,
                "track_name": "Faixa", "artist_name": "Artista",
                "plain_text": "duplicada", "observed_at": 1_000,
                "id": 123, "token": "segredo",
                "lines": [{"time_seconds": 2, "text": "Olá", "raw": "x"}],
            },
        },
    })

    letra = publico["music"]["lyrics"]
    assert letra["plain_text"] == ""
    assert letra["lines"] == [{"time_seconds": 2.0, "text": "Olá"}]
    assert publico["music"]["context_music"]["basis"] == ["horario_local"]
    serializado = json.dumps(publico, ensure_ascii=False)
    assert '"id"' not in serializado
    assert "segredo" not in serializado


def test_ui_m4_sincroniza_linha_e_permite_ver_letra_completa(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    agora = {"valor": 1_005.0}
    monkeypatch.setattr(
        "cliente.terminal_2.musica_m1.time.time", lambda: agora["valor"],
    )
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    pagina = PaginaMusicaM1()
    pagina.definir_conectada(True)
    pagina.aplicar_dashboard({
        "music": {
            "title": "Faixa", "channel": "Artista", "state": "playing",
            "position_seconds": 5, "duration_seconds": 60,
            "freshness": "fresh", "observed_at": 1_000,
            "context_music": {
                "summary": "É noite e a playlist Rock está ativa.",
                "recommendation": "Posso manter a sequência de Rock.",
                "freshness": "fresh", "observed_at": 1_000,
            },
            "lyrics": {
                "status": "available", "source": "lrclib", "synced": True,
                "observed_at": 1_000,
                "lines": [
                    {"time_seconds": 1, "text": "Primeira"},
                    {"time_seconds": 8, "text": "Segunda"},
                    {"time_seconds": 14, "text": "Terceira"},
                ],
            },
        },
        "system": {}, "routines": {},
    })
    app.processEvents()

    assert "Primeira" in pagina.letra_texto.text()
    assert "#FF5C76" in pagina.letra_texto.text()
    assert pagina.letra_fonte.text() == "Letras fornecidas pela LRCLIB"
    assert "playlist Rock" in pagina.contexto_estado.text()
    pagina.letra_expandir.click()
    assert "Terceira" in pagina.letra_texto.text()
    pagina.close()
    app.processEvents()

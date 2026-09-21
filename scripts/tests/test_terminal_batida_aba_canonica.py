from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

from mente_laylay.integracao import chrome_ws_handlers
from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime


RAIZ = Path(__file__).resolve().parents[1]
EXTENSAO = RAIZ / "extençao_google"
VIDEO_ID = "AAAAAAAAAAA"


def test_extensao_captura_somente_aba_youtube_autorizada() -> None:
    manifesto = json.loads((EXTENSAO / "manifest.json").read_text(encoding="utf-8"))
    popup = (EXTENSAO / "popup.js").read_text(encoding="utf-8")
    offscreen = (EXTENSAO / "offscreen.js").read_text(encoding="utf-8")

    assert {"tabCapture", "offscreen"} <= set(manifesto["permissions"])
    assert "targetTabId: tab.id" in popup
    assert "GET_CANONICAL_MUSIC_TAB" in popup
    assert "canonica?.tabId !== tab.id" in popup
    assert "youtube.com" in popup
    assert "probe?.playing === true || tab.audible === true" in popup
    assert 'chromeMediaSource: "tab"' in offscreen
    assert "createAnalyser()" in offscreen
    assert "source.connect(output.destination)" in offscreen
    assert "MUSIC_METER_SAMPLE" in offscreen
    assert "setInterval(publicarAmostra, 50)" in offscreen
    assert "chrome.storage" not in offscreen
    assert "getDisplayMedia" not in popup + offscreen
    assert "desktopCapture" not in popup + offscreen


def test_background_so_publica_medidor_da_aba_canonica() -> None:
    background = (EXTENSAO / "background.js").read_text(encoding="utf-8")

    assert "canonicalMusicTabId" in background
    assert "canonicalMusicVideoId" in background
    bloco = background.split('request?.type === "MUSIC_METER_SAMPLE"', 1)[1]
    bloco = bloco.split('request?.type === "MUSIC_METER_STOPPED"', 1)[0]
    assert "request.tabId !== canonicalMusicTabId" in bloco
    assert 'String(request.videoId || "") !== canonicalMusicVideoId' in bloco
    assert 'type: "MUSIC_METER"' in bloco


def test_runtime_rejeita_batida_sem_ownership_do_player() -> None:
    tratar = getattr(chrome_ws_handlers, "handle_music_meter")
    estado = {
        "player": {
            "tab_id": 22,
            "video_id": VIDEO_ID,
            "state": "playing",
        },
    }
    base = {
        "type": "MUSIC_METER",
        "tabId": 22,
        "videoId": VIDEO_ID,
        "levels": [0.9, 0.4, 0.2],
        "energy": 0.7,
    }

    assert tratar({**base, "tabId": 99}, playlist_state=estado) is None
    assert tratar({**base, "videoId": "BBBBBBBBBBB"}, playlist_state=estado) is None
    estado["player"]["state"] = "paused"
    assert tratar(base, playlist_state=estado) is None
    assert "meter" not in estado["player"]


def test_runtime_publica_apenas_amostra_sanitizada_do_player_owner() -> None:
    tratar = getattr(chrome_ws_handlers, "handle_music_meter")
    estado = {
        "player": {
            "tab_id": 22,
            "video_id": VIDEO_ID,
            "state": "playing",
        },
    }

    medidor = tratar({
        "type": "MUSIC_METER",
        "tabId": 22,
        "videoId": VIDEO_ID,
        "levels": [-1, 0.45, 8],
        "energy": 2,
        "ignored": "não atravessa",
    }, playlist_state=estado)

    assert medidor is not None
    assert medidor["tab_id"] == 22
    assert medidor["video_id"] == VIDEO_ID
    assert medidor["levels"] == [0.0, 0.45, 1.0]
    assert medidor["energy"] == 1.0
    assert set(medidor) == {
        "tab_id", "video_id", "levels", "energy", "observed_at",
    }
    assert "meter" not in estado["player"]


def test_composicao_encaminha_medidor_confirmado_uma_vez() -> None:
    publicados: list[dict] = []
    runtime = chrome_ws_handlers.ChromeWsEventosRuntime(
        solicitacoes=SimpleNamespace(),
        playlist_state={
            "player": {
                "tab_id": 22,
                "video_id": VIDEO_ID,
                "state": "playing",
            },
        },
        yt_clean_url=lambda valor: valor,
        playlist_avancar_proxima=lambda: False,
        falar_com_lipsync=lambda *_args, **_kwargs: None,
        user_context_getter=lambda: {},
        aplicar_user_updates=lambda _updates: None,
        action_context_getter=lambda: {},
        aplicar_action_updates=lambda _updates: None,
        music_meter_publisher=publicados.append,
    )

    runtime.dispatch({
        "type": "MUSIC_METER",
        "tabId": 22,
        "videoId": VIDEO_ID,
        "levels": [0.8, 0.5, 0.3],
        "energy": 0.6,
    })

    assert len(publicados) == 1
    assert publicados[0]["tab_id"] == 22
    assert publicados[0]["video_id"] == VIDEO_ID
    assert publicados[0]["levels"] == [0.8, 0.5, 0.3]
    assert publicados[0]["energy"] == 0.6
    assert "meter" not in runtime.playlist_state["player"]


def test_root_liga_medidor_sem_persistir_amostra_no_dashboard() -> None:
    root = (RAIZ / "laylay.py").read_text(encoding="utf-8")

    assert "music_meter_publisher=_publicar_medidor_musical_terminal" in root
    assert '_ponte_medidor_musical["publicar"] = (' in root
    assert "_desktop_bridge_runtime.publicar_medidor_musica" in root


def test_ponte_publica_pacote_leve_sem_dashboard() -> None:
    ponte = object.__new__(DesktopBridgeRuntime)
    enviados: list[dict] = []
    ponte._publicar = lambda mensagem: enviados.append(dict(mensagem)) or True

    assert ponte.publicar_medidor_musica({
        "tab_id": 22,
        "video_id": VIDEO_ID,
        "levels": [0.8, 0.5, 0.3],
        "energy": 0.6,
        "observed_at": 123.0,
    }) is True
    assert enviados == [{
        "type": "music_meter",
        "tab_id": 22,
        "video_id": VIDEO_ID,
        "levels": [0.8, 0.5, 0.3],
        "energy": 0.6,
        "observed_at": 123.0,
    }]


def test_indicador_segue_bandas_reais_e_retorna_ao_fallback(monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2 import playlist_detalhe

    _app = QApplication.instance() or QApplication([])
    agora = [10.0]
    monkeypatch.setattr(playlist_detalhe.time, "monotonic", lambda: agora[0])
    indicador = playlist_detalhe.IndicadorFaixaTocando(semente=2026)
    anteriores = indicador._alturas_atuais()

    assert indicador.aplicar_niveis([1.0, 0.0, 0.5]) is True
    indicador._avancar()
    sincronizados = indicador._alturas_atuais()

    assert indicador._sincronizacao_ativa is True
    assert sincronizados[0] > anteriores[0]
    assert sincronizados[1] < anteriores[1]
    assert indicador.aplicar_niveis([True, 0.2, 0.3]) is False

    agora[0] += 0.36
    indicador._avancar()
    assert indicador._sincronizacao_ativa is False


def test_terminal_encaminha_pacote_leve_diretamente_a_pagina(monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
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
    janela = JanelaLaylay(worker, RAIZ)
    recebidos: list[dict] = []
    monkeypatch.setattr(
        janela.pagina_musica,
        "aplicar_medidor_musica",
        lambda medidor: recebidos.append(dict(medidor)) or True,
    )
    pacote = {
        "type": "music_meter",
        "tab_id": 22,
        "video_id": VIDEO_ID,
        "levels": [0.8, 0.5, 0.3],
        "energy": 0.6,
        "observed_at": 123.0,
    }

    worker.mensagem.emit(pacote)
    app.processEvents()

    assert recebidos == [pacote]
    janela.close()


def test_detalhe_aplica_batida_somente_na_faixa_visual_owner() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.playlist_detalhe import PlaylistDetalhe

    _app = QApplication.instance() or QApplication([])
    detalhe = PlaylistDetalhe()
    detalhe.abrir("Anime")
    detalhe.aplicar_resultado("detail", {
        "ok": True,
        "status": "ok",
        "name": "Anime",
        "revision": "r1",
        "total": 1,
        "offset": 0,
        "limit": 50,
        "has_more": False,
        "items": [{
            "video_id": VIDEO_ID,
            "title": "Faixa owner",
            "channel": "Canal",
            "added_at": "",
            "duration_seconds": 180,
            "artwork_url": "",
        }],
    })
    detalhe.aplicar_player_observado({
        "freshness": "fresh",
        "state": "playing",
        "video_id": VIDEO_ID,
        "controls_available": True,
        "title": "Faixa owner",
        "position_seconds": 1,
        "duration_seconds": 180,
    })
    indicador = detalhe._linhas_widgets[0].indicador_tocando

    assert detalhe.aplicar_medidor_musica({
        "video_id": "BBBBBBBBBBB", "levels": [1, 1, 1],
    }) is False
    assert indicador._niveis_sincronizados is None
    assert detalhe.aplicar_medidor_musica({
        "video_id": VIDEO_ID, "levels": [0.9, 0.4, 0.2],
    }) is True
    assert indicador._niveis_sincronizados == [0.9, 0.4, 0.2]

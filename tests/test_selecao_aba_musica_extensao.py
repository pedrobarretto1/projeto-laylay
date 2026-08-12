from __future__ import annotations

import asyncio
from pathlib import Path

from mente_laylay.integracao.chrome_ws_handlers import handle_youtube_data


def test_extensao_procura_player_audivel_em_todas_as_abas_youtube() -> None:
    raiz = Path(__file__).resolve().parents[1]
    background = (raiz / "extençao_google" / "background.js").read_text(
        encoding="utf-8",
    )
    bloco = background.split(
        'if (cmd.action === "get_youtube_data") {', 1,
    )[1].split('if (cmd.action === "get_page_content") {', 1)[0]

    assert "findBestYouTubeCandidate(true)" in bloco
    assert "readYouTubeTabData(t, requestId)" in bloco
    assert "chrome.tabs.query({ active: true, currentWindow: true }" not in bloco

    assert 'url: ["*://*.youtube.com/*", "*://youtube.com/*"]' in background
    assert 'action: "PROBE_YT_PLAYER"' in background
    assert "probe.audible === true" in background
    assert "tab.audible === true" in background
    assert "probe.playing === true" in background


def test_extensao_inspeciona_aba_antiga_sem_depender_do_content_script() -> None:
    raiz = Path(__file__).resolve().parents[1]
    background = (raiz / "extençao_google" / "background.js").read_text(
        encoding="utf-8",
    )

    assert "function inspectYouTubePlayerInPage()" in background
    assert "function executeScriptResult(tabId, func)" in background
    assert "chrome.scripting.executeScript(" in background
    assert "executeScriptResult(tab.id, inspectYouTubePlayerInPage)" in background
    assert "executeScriptResult(tab.id, inspectYouTubeDataInPage)" in background


def test_extensao_descobre_musica_ja_em_reproducao_ao_conectar() -> None:
    raiz = Path(__file__).resolve().parents[1]
    background = (raiz / "extençao_google" / "background.js").read_text(
        encoding="utf-8",
    )
    onopen = background.split("websocket.onopen = () => {", 1)[1].split(
        "websocket.onmessage", 1,
    )[0]

    assert "discoverExistingYouTubePlayback()" in onopen
    assert 'type: "PLAYER_EVENT"' in background
    assert 'event: "player_state"' in background
    assert 'event: "player_unavailable"' in background
    assert "probe.ok === true" in background


def test_extensao_renova_um_unico_player_canonico_no_heartbeat() -> None:
    raiz = Path(__file__).resolve().parents[1]
    background = (raiz / "extençao_google" / "background.js").read_text(
        encoding="utf-8",
    )

    assert "playerDiscoveryRunning" in background
    assert "playerDiscoveryQueued" in background
    assert "schedulePlayerDiscovery(0)" in background
    assert '"audible_youtube_tab"' in background
    assert 'authoritative: true' in background


def test_eventos_das_abas_nao_disputam_diretamente_o_player() -> None:
    raiz = Path(__file__).resolve().parents[1]
    background = (raiz / "extençao_google" / "background.js").read_text(
        encoding="utf-8",
    )
    listener = background.split(
        "chrome.runtime.onMessage.addListener", 1,
    )[1].split("// --- MONITORAMENTO PROATIVO", 1)[0]

    bloco = listener.split(
        'request?.event === "player_state"', 1,
    )[1].split("}", 1)[0]
    assert "schedulePlayerDiscovery(80)" in bloco
    assert "return;" in bloco


def test_inicio_descarta_player_efemero_restaurado_da_sessao_anterior() -> None:
    raiz = Path(__file__).resolve().parents[1]
    codigo = (raiz / "laylay.py").read_text(encoding="utf-8")
    bloco = codigo.split(
        'playlist_state = _estado_compartilhado_runtime.vincular_dict(', 1,
    )[1].split('_playlist_runtime =', 1)[0]

    assert 'playlist_state.pop("player", None)' in bloco
    assert 'playlist_state.pop("tab_id", None)' in bloco


def test_content_script_confirma_reproducao_e_responde_dados_da_aba_escolhida() -> None:
    raiz = Path(__file__).resolve().parents[1]
    codigo = (raiz / "extençao_google" / "content_script.js").read_text(
        encoding="utf-8",
    )

    assert 'request.action === "PROBE_YT_PLAYER"' in codigo
    assert "playing && !muted && volume > 0 && readyState >= 2" in codigo
    assert "currentTime: Number.isFinite(video?.currentTime)" in codigo
    assert "duration: Number.isFinite(video?.duration)" in codigo
    assert "positionReliable: !!video" in codigo
    assert "videoId," in codigo
    assert "function _laylayYoutubeQueueSnapshot()" in codigo
    assert "queueObserved: queue.observed" in codigo
    assert "queue: queue.items" in codigo
    assert "request.directResponse === true" in codigo
    assert "sendResponse(resultado)" in codigo


def test_background_publica_apenas_fila_da_aba_canonica() -> None:
    raiz = Path(__file__).resolve().parents[1]
    codigo = (raiz / "extençao_google" / "background.js").read_text(
        encoding="utf-8",
    )
    descoberta = codigo.split(
        "async function discoverExistingYouTubePlayback()", 1,
    )[1].split("function schedulePlayerDiscovery", 1)[0]

    assert "queueObserved: probe.queueObserved === true" in descoberta
    assert "Array.isArray(probe.queue) ? probe.queue.slice(0, 8)" in descoberta


def test_resposta_python_preserva_evidencia_da_aba_que_estava_tocando() -> None:
    loop = asyncio.new_event_loop()
    try:
        futuro = loop.create_future()
        handle_youtube_data(
            {
                "requestId": "pedido-1",
                "url": "https://www.youtube.com/watch?v=abcdefghijk",
                "title": "Faixa",
                "canal": "Canal",
                "tabId": 22,
                "source": "audible_youtube_tab",
                "playingConfirmed": True,
                "audibleConfirmed": True,
            },
            {"pedido-1": futuro},
        )
        assert futuro.result() == {
            "url": "https://www.youtube.com/watch?v=abcdefghijk",
            "title": "Faixa",
            "canal": "Canal",
            "tabId": 22,
            "source": "audible_youtube_tab",
            "playingConfirmed": True,
            "audibleConfirmed": True,
        }
    finally:
        loop.close()

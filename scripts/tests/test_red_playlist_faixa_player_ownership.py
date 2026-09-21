"""RED arquitetural — faixa exata deve manter ownership do player da fila.

O controle verde atravessa o runtime real de playlist e o handler real do
Chrome. O RED acrescenta somente a condição observada no uso físico: outra aba
do YouTube pode publicar ``video_ended`` enquanto a fila selecionada continua
ativa. Esse evento estrangeiro não pode roubar a aba nem ser consumido como fim
da reprodução pertencente à playlist.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mente_laylay.integracao.chrome_ws_handlers import handle_player_event
from mente_laylay.memoria_mental.playlist_mental import yt_clean_url
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


def _item(video_id: str, titulo: str) -> dict[str, str]:
    return {
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "titulo": titulo,
        "canal": "Canal",
    }


def _runtime_real_isolado(
    tmp_path: Path,
) -> tuple[PlaylistRuntime, dict[str, Any], list[tuple[str, int | None]]]:
    caminho = tmp_path / "playlists.json"
    caminho.write_text(json.dumps({
        "anime": [
            _item("AAAAAAAAAAA", "Primeira"),
            _item("BBBBBBBBBBB", "Escolhida"),
            _item("CCCCCCCCCCC", "Seguinte"),
        ],
    }), encoding="utf-8")
    estado: dict[str, Any] = {}
    aberturas: list[tuple[str, int | None]] = []

    def abrir(url: str, *, target_tab_id: int | None = None) -> dict[str, Any]:
        aberturas.append((url, target_tab_id))
        return {
            "ok": True,
            "confirmado": True,
            "tab": {"id": 17},
        }

    runtime = PlaylistRuntime(
        state_file=str(caminho),
        legacy_file=str(tmp_path / "legado.json"),
        cache={},
        ultima_playlist_getter=lambda: "",
        playlist_state=estado,
        youtube_play=abrir,
        log=lambda _linha: None,
    )
    return runtime, estado, aberturas


def _fim(
    runtime: PlaylistRuntime,
    estado: dict[str, Any],
    *,
    video_id: str,
    tab_id: int,
    event_id: str,
) -> None:
    handle_player_event(
        {
            "event": "video_ended",
            "eventId": event_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "duration": 180,
            "tabId": tab_id,
        },
        playlist_state=estado,
        yt_clean_url=yt_clean_url,
        playlist_avancar_proxima=runtime.avancar_proxima,
        falar_com_lipsync=None,
    )


def _estado_player(
    estado: dict[str, Any],
    *,
    video_id: str,
    tab_id: int,
) -> None:
    handle_player_event(
        {
            "event": "player_state",
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "videoId": video_id,
            "title": "Player concorrente",
            "channel": "Outro canal",
            "state": "playing",
            "currentTime": 20,
            "duration": 180,
            "tabId": tab_id,
            "source": "audible_youtube_tab",
            "audibleConfirmed": True,
        },
        playlist_state=estado,
        yt_clean_url=yt_clean_url,
        playlist_avancar_proxima=None,
        falar_com_lipsync=None,
    )


def test_controle_faixa_exata_segue_quando_o_mesmo_player_termina(
    tmp_path: Path,
) -> None:
    runtime, estado, aberturas = _runtime_real_isolado(tmp_path)
    revisao = runtime.detalhar("anime")["revision"]

    resultado = runtime.tocar_faixa_exata(
        "anime", "BBBBBBBBBBB", revisao,
    )
    _fim(
        runtime,
        estado,
        video_id="BBBBBBBBBBB",
        tab_id=17,
        event_id="ended:escolhida:1",
    )

    assert resultado["ok"] is True
    assert estado["name"] == "anime"
    assert estado["index"] == 2
    assert estado["last_advance_status"] == "ok"
    assert aberturas == [
        ("https://www.youtube.com/watch?v=BBBBBBBBBBB", None),
        ("https://www.youtube.com/watch?v=CCCCCCCCCCC", 17),
    ]


def test_red_fim_de_outra_aba_nao_rouba_ownership_da_fila_exata(
    tmp_path: Path,
) -> None:
    runtime, estado, aberturas = _runtime_real_isolado(tmp_path)
    revisao = runtime.detalhar("anime")["revision"]
    resultado = runtime.tocar_faixa_exata(
        "anime", "BBBBBBBBBBB", revisao,
    )
    assert resultado["ok"] is True
    assert estado["tab_id"] == 17

    _fim(
        runtime,
        estado,
        video_id="ZZZZZZZZZZZ",
        tab_id=99,
        event_id="ended:aba-estrangeira:1",
    )

    # EVENTO OBSERVADO != OWNERSHIP DA FILA. A rejeição precisa acontecer
    # antes de qualquer mutação de aba ou consumo no ledger de fins.
    assert estado["tab_id"] == 17, (
        "RED: um video_ended de outra aba roubou a aba pertencente à fila"
    )
    assert estado["index"] == 1
    assert estado["last_url"] == (
        "https://www.youtube.com/watch?v=BBBBBBBBBBB"
    )
    assert "ended:aba-estrangeira:1" not in estado.get(
        "ended_event_ids", [],
    ), "RED: o fim estrangeiro foi consumido como evento da fila"
    assert aberturas == [
        ("https://www.youtube.com/watch?v=BBBBBBBBBBB", None),
    ]

    # A rejeição estrangeira também não pode envenenar o fim legítimo que
    # chegar depois pela aba proprietária.
    _fim(
        runtime,
        estado,
        video_id="BBBBBBBBBBB",
        tab_id=17,
        event_id="ended:escolhida:depois-da-estrangeira",
    )

    assert estado["index"] == 2
    assert estado["tab_id"] == 17
    assert estado["last_advance_status"] == "ok"
    assert aberturas[-1] == (
        "https://www.youtube.com/watch?v=CCCCCCCCCCC", 17,
    )


def test_red_player_state_de_outra_aba_nao_rouba_ownership_da_fila(
    tmp_path: Path,
) -> None:
    runtime, estado, _aberturas = _runtime_real_isolado(tmp_path)
    revisao = runtime.detalhar("anime")["revision"]
    resultado = runtime.tocar_faixa_exata(
        "anime", "BBBBBBBBBBB", revisao,
    )
    assert resultado["ok"] is True
    assert estado["tab_id"] == 17

    _estado_player(
        estado,
        video_id="ZZZZZZZZZZZ",
        tab_id=99,
    )

    assert estado["player"]["tab_id"] == 99
    assert estado["tab_id"] == 17, (
        "RED: observação audível de outra aba substituiu a aba dona da fila"
    )

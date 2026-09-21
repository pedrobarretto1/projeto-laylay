from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from cliente.terminal_2.playlist_detalhe import PlaylistDetalhe
from mente_laylay.integracao.desktop_bridge import validar_mensagem_cliente
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


VIDEO_ID = "AAAAAAAAAAA"


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _item() -> dict:
    return {
        "url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
        "titulo": "Faixa para distribuir",
        "canal": "Canal",
        "data": "2026-08-27",
        "titulo_norm": "faixa para distribuir",
        "canal_norm": "canal",
    }


def _runtime(tmp_path: Path, dados: dict) -> PlaylistRuntime:
    estado = tmp_path / "playlists.json"
    estado.write_text(json.dumps(dados), encoding="utf-8")
    return PlaylistRuntime(
        state_file=str(estado),
        legacy_file=str(tmp_path / "legado.json"),
        cache={},
        ultima_playlist_getter=lambda: "",
        playlist_state={},
        artwork_dir=str(tmp_path / "artwork"),
        log=lambda _texto: None,
    )


def test_distribuicao_em_lote_e_atomica_e_move_remove_origem(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, {
        "Origem": [_item()],
        "Favoritas": [],
        "Treino": [_item()],
        "Noite": [],
    })
    revisao = runtime.detalhar("Origem")["revision"]

    copiado = runtime.copiar_faixa_multiplas(
        "Origem", ["Favoritas", "Treino", "Noite"], VIDEO_ID, revisao,
    )

    assert copiado == {
        "ok": True, "status": "copied_many", "destination_count": 3,
        "copied_count": 2, "already_present_count": 1,
        "source_removed": False,
    }
    assert runtime.detalhar("Origem")["total"] == 1
    assert runtime.detalhar("Favoritas")["total"] == 1
    assert runtime.detalhar("Treino")["total"] == 1
    assert runtime.detalhar("Noite")["total"] == 1

    revisao = runtime.detalhar("Origem")["revision"]
    movido = runtime.mover_faixa_multiplas(
        "Origem", ["Favoritas", "Treino", "Noite"], VIDEO_ID, revisao,
    )

    assert movido["ok"] is True
    assert movido["status"] == "moved_many"
    assert movido["source_removed"] is True
    assert runtime.detalhar("Origem")["total"] == 0


def test_falha_de_persistencia_nao_remove_origem_nem_entrega_parcial(
    tmp_path: Path,
) -> None:
    runtime = _runtime(tmp_path, {
        "Origem": [_item()], "Destino A": [], "Destino B": [],
    })
    revisao = runtime.detalhar("Origem")["revision"]
    runtime.save = lambda _dados: False  # type: ignore[method-assign]

    resultado = runtime.mover_faixa_multiplas(
        "Origem", ["Destino A", "Destino B"], VIDEO_ID, revisao,
    )

    assert resultado == {"ok": False, "status": "save_failed"}
    assert runtime.detalhar("Origem")["total"] == 1
    assert runtime.detalhar("Destino A")["total"] == 0
    assert runtime.detalhar("Destino B")["total"] == 0


def test_protocolo_aceita_ate_mil_destinos() -> None:
    destinos = [f"Playlist {indice}" for indice in range(1_000)]
    mensagem = validar_mensagem_cliente({
        "type": "playlist_request",
        "id": "lote-1",
        "operation": "copy_track_many",
        "playlist": "Origem",
        "destinations": destinos,
        "video_id": VIDEO_ID,
        "revision": "r1",
    }, token="segredo", autenticado=True)

    assert mensagem["operation"] == "copy_track_many"
    assert len(mensagem["destinations"]) == 1_000
    assert mensagem["destinations"][0] == "Playlist 0"


def test_interface_pesquisa_e_envia_multisselecao_em_uma_requisicao() -> None:
    app = _app()
    detalhe = PlaylistDetalhe(reduzir_movimento=True)
    detalhe._nome = "Anime"
    detalhe._revisao = "r1"
    detalhe.definir_catalogo([
        {"name": "Anime", "count": 27},
        {"name": "Favoritas", "count": 12},
        {"name": "Treino", "count": 30},
        {"name": "Noite", "count": 8},
    ])
    pedidos: list[dict] = []
    detalhe.requisicao_solicitada.connect(pedidos.append)
    detalhe.show()
    app.processEvents()

    faixa = {
        "video_id": VIDEO_ID, "title": "Faixa para distribuir",
        "artwork_url": "",
    }
    detalhe._abrir_seletor_destinos("copy_track", faixa)
    app.processEvents()

    assert not detalhe.seletor_destinos.isHidden()
    assert detalhe.seletor_destinos.lista.count() == 3
    detalhe.seletor_destinos.busca.setText("tre")
    detalhe.seletor_destinos._selecionar_todas_visiveis()
    detalhe.seletor_destinos.busca.clear()
    detalhe.seletor_destinos.lista.item(0).setCheckState(Qt.Checked)
    detalhe.seletor_destinos._confirmar()

    assert pedidos == [{
        "operation": "copy_track_many", "playlist": "Anime",
        "video_id": VIDEO_ID,
        "destinations": ["Favoritas", "Treino"],
        "revision": "r1",
    }]
    detalhe.close()

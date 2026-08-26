from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from cliente.terminal_2.musica_m1 import PaginaMusicaM1
from mente_laylay.integracao.desktop_bridge import (
    sanitizar_resultado_playlist,
    validar_mensagem_cliente,
)


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _dashboard() -> dict:
    return {"music": {
        "freshness": "fresh", "state": "paused", "observed_at": 10.0,
        "controls_available": True, "title": "Atual", "channel": "Canal",
        "position_seconds": 20, "duration_seconds": 200,
        "catalog_available": True, "catalog_play_available": True,
        "catalog": [{"name": "Anime", "count": 2, "artwork_url": ""}],
        "queue": [], "queue_freshness": "unavailable",
    }}


def test_corpo_abre_detalhe_sem_tocar_e_play_toca_sem_abrir() -> None:
    _app()
    pagina = PaginaMusicaM1()
    pedidos: list[tuple[str, str]] = []
    detalhes: list[dict] = []
    pagina.acao_solicitada.connect(lambda acao, texto: pedidos.append((acao, texto)))
    pagina.acao_playlist_solicitada.connect(detalhes.append)
    pagina.definir_conectada(True)
    pagina.aplicar_dashboard(_dashboard())
    cartao = pagina.preset_botoes[0]

    cartao.corpo.click()
    assert pagina.pilhas.currentWidget() is pagina.detalhe_playlist
    assert pedidos == []
    assert detalhes[-1]["operation"] == "detail"

    pagina.pilhas.setCurrentWidget(pagina.rolagem)
    cartao.play.click()
    assert pedidos[-1][0] == "playlist_play"
    assert pagina.pilhas.currentWidget() is pagina.rolagem


def test_detalhe_reutiliza_player_observado_e_layout_compacto() -> None:
    _app()
    pagina = PaginaMusicaM1()
    pagina.aplicar_dashboard(_dashboard())
    assert pagina.detalhe_playlist.player.isVisible() is False  # página ainda não exibida
    assert pagina.detalhe_playlist._player_observado is True
    pagina.detalhe_playlist.definir_compacto(True)
    assert pagina.detalhe_playlist.tabela.isColumnHidden(2)
    assert pagina.detalhe_playlist.tabela.isColumnHidden(3)


def test_titulo_da_faixa_tem_um_unico_renderizador() -> None:
    _app()
    pagina = PaginaMusicaM1()
    detalhe = pagina.detalhe_playlist
    detalhe.abrir("Anime")
    detalhe.aplicar_resultado("detail", {
        "ok": True, "status": "ok", "name": "Anime", "revision": "r1",
        "total": 1, "offset": 0, "limit": 50, "has_more": False,
        "items": [{
            "video_id": "AAAAAAAAAAA", "title": "Título único",
            "channel": "Canal", "added_at": "2026-08-26",
            "duration_seconds": 180, "artwork_url": "",
        }],
    })

    assert detalhe.tabela.item(0, 1) is None
    faixa = detalhe.tabela.cellWidget(0, 1)
    assert faixa is not None
    assert [item.text() for item in faixa.findChildren(QLabel)] == ["Título único"]


def test_layout_estreito_reorganiza_acoes_player_e_mantem_acessibilidade() -> None:
    _app()
    pagina = PaginaMusicaM1()
    detalhe = pagina.detalhe_playlist

    detalhe.resize(375, 760)
    detalhe.definir_compacto(True)

    assert detalhe.acoes_layout.rowCount() >= 2
    assert detalhe.player_layout.rowCount() >= 2
    assert detalhe.capa.width() <= 104
    for controle in (
        detalhe.play, detalhe.shuffle, detalhe.adicionar, detalhe.capa_trocar,
        detalhe.capa_restaurar, detalhe.player_anterior, detalhe.player_toggle,
        detalhe.player_proxima,
    ):
        assert controle.accessibleName()
        assert controle.toolTip()


def test_resultado_atrasado_ou_de_outra_playlist_nao_substitui_tela_atual() -> None:
    _app()
    pagina = PaginaMusicaM1()
    detalhe = pagina.detalhe_playlist
    pedidos: list[dict] = []
    detalhe.requisicao_solicitada.connect(pedidos.append)
    detalhe.abrir("Anime")
    requisicao_antiga = pedidos[-1]["id"]
    detalhe.solicitar_detalhe(reiniciar=True)
    requisicao_atual = pedidos[-1]["id"]
    resultado = {
        "ok": True, "status": "ok", "name": "Anime", "revision": "r1",
        "total": 1, "offset": 0, "limit": 50, "has_more": False,
        "items": [{
            "video_id": "AAAAAAAAAAA", "title": "Faixa atual",
            "channel": "Canal", "added_at": "", "duration_seconds": 10,
            "artwork_url": "",
        }],
    }

    detalhe.aplicar_resultado(
        "detail", resultado, playlist="Anime", request_id=requisicao_antiga,
    )
    detalhe.aplicar_resultado(
        "detail", resultado, playlist="Outra", request_id=requisicao_atual,
    )
    assert detalhe.tabela.rowCount() == 0

    detalhe.aplicar_resultado(
        "detail", resultado, playlist="Anime", request_id=requisicao_atual,
    )
    assert detalhe.tabela.rowCount() == 1


def test_ponte_valida_porta_detalhada_sem_texto_livre_para_llm() -> None:
    mensagem = validar_mensagem_cliente({
        "type": "playlist_request", "id": "r1", "operation": "move_track",
        "playlist": "Anime", "destination": "Treino", "video_id": "AAAAAAAAAAA",
        "revision": "abc123",
    }, token="segredo", autenticado=True)
    assert mensagem["type"] == "playlist_request"
    assert mensagem["operation"] == "move_track"
    assert "text" not in mensagem

    publico = sanitizar_resultado_playlist("detail", {
        "ok": True, "name": "Anime", "revision": "r1", "total": 1,
        "items": [{
            "video_id": "AAAAAAAAAAA", "title": "Faixa", "channel": "Canal",
            "url": "https://www.youtube.com/watch?v=AAAAAAAAAAA",
            "path": r"C:\segredo\arquivo.mp3",
        }],
    })
    assert "url" not in publico["items"][0]
    assert "path" not in publico["items"][0]

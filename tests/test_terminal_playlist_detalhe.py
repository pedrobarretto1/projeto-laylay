from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from cliente.terminal_2.acabamento import CapaMusicaGenerica
from cliente.terminal_2.musica_m1 import CartaoPlaylist, PaginaMusicaM1
from cliente.terminal_2.playlist_detalhe import FaixaPlaylistRow
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
    faixa = detalhe.tabela.cellWidget(0, 0)
    assert isinstance(faixa, FaixaPlaylistRow)
    assert faixa.titulo.texto_completo == "Título único"


def test_cartao_compacto_preserva_capa_textos_e_play_sem_sobreposicao() -> None:
    app = _app()
    cartao = CartaoPlaylist(0)
    cartao.resize(164, 44)
    cartao.definir(
        "Uma playlist com um nome muito comprido",
        26,
        artwork_url="",
    )
    cartao.show()
    app.processEvents()

    assert cartao.height() == 44
    assert cartao.capa.size().width() == 30
    assert cartao.play.size().width() == 30
    assert cartao.corpo.height() >= 38
    assert cartao.titulo.texto_completo.startswith("Uma playlist")
    assert cartao.titulo.text().endswith("…")
    assert cartao.corpo.geometry().right() < cartao.play.geometry().left()


def test_grade_de_playlists_usa_duas_colunas_quando_cabem_e_uma_quando_nao() -> None:
    _app()
    pagina = PaginaMusicaM1()
    pagina.playlists.resize(340, 240)
    pagina._organizar_grade_playlists()
    segunda = pagina.playlists_grade.indexOf(pagina.preset_botoes[1])
    assert pagina.playlists_grade.getItemPosition(segunda)[1] == 1

    pagina.playlists.resize(280, 240)
    pagina._organizar_grade_playlists()
    segunda = pagina.playlists_grade.indexOf(pagina.preset_botoes[1])
    assert pagina.playlists_grade.getItemPosition(segunda)[1] == 0


def test_linha_revela_play_e_menu_sem_mudar_geometria_e_toca_video_exato() -> None:
    app = _app()
    pagina = PaginaMusicaM1()
    detalhe = pagina.detalhe_playlist
    pedidos: list[dict] = []
    detalhe.requisicao_solicitada.connect(pedidos.append)
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
    linha = detalhe.tabela.cellWidget(0, 0)
    assert isinstance(linha, FaixaPlaylistRow)
    controle_antes = linha.controle_slot.geometry()
    menu_antes = linha.menu_slot.geometry()
    assert linha._controle.currentWidget() is linha.numero
    assert linha.menu.isHidden()

    QApplication.sendEvent(linha, QEvent(QEvent.Enter))
    app.processEvents()
    assert linha._controle.currentWidget() is linha.play
    assert not linha.menu.isHidden()
    assert linha.controle_slot.geometry() == controle_antes
    assert linha.menu_slot.geometry() == menu_antes
    for controle in (linha.play, linha.menu):
        assert controle.width() <= 24
        assert controle.height() <= 24
    assert linha.play.iconSize() == QSize(12, 12)
    assert not linha.play.icon().pixmap(linha.play.iconSize()).isNull()
    assert linha.menu.text() == "•••"

    pedidos.clear()
    linha.play.click()
    assert pedidos[-1]["operation"] == "play_track"
    assert pedidos[-1]["video_id"] == "AAAAAAAAAAA"


def test_detalhe_responde_a_altura_baixa_sem_esmagar_busca_ou_lista() -> None:
    app = _app()
    detalhe = PaginaMusicaM1().detalhe_playlist
    detalhe.resize(1419, 461)
    detalhe.aplicar_player_observado({
        "freshness": "fresh", "state": "playing",
        "controls_available": True, "title": "Faixa observada",
        "position_seconds": 10, "duration_seconds": 180,
    })
    detalhe.show()
    app.processEvents()

    assert detalhe._altura_baixa is True
    assert detalhe.capa.width() == 68
    assert detalhe.hero.height() == 80
    assert detalhe.busca.height() == 34
    assert detalhe.tabela.height() >= 100
    assert detalhe.player.height() <= 50


def test_linha_estreita_prioriza_identidade_e_oculta_metadados_secundarios() -> None:
    app = _app()
    detalhe = PaginaMusicaM1().detalhe_playlist
    detalhe.resize(375, 760)
    detalhe.aplicar_resultado("detail", {
        "ok": True, "status": "ok", "name": "Anime", "revision": "r1",
        "total": 1, "offset": 0, "limit": 50, "has_more": False,
        "items": [{
            "video_id": "AAAAAAAAAAA",
            "title": "Um título longo que deve manter prioridade visual",
            "channel": "Canal longo", "added_at": "2026-08-26",
            "duration_seconds": 180, "artwork_url": "",
        }],
    })
    detalhe.show()
    app.processEvents()
    linha = detalhe.tabela.cellWidget(0, 0)

    assert isinstance(linha, FaixaPlaylistRow)
    assert detalhe._compacto is True
    assert linha.canal.isHidden()
    assert linha.adicionada.isHidden()
    assert not linha.titulo.isHidden()
    assert not linha.capa.isHidden()
    assert detalhe.tabela.horizontalScrollBar().maximum() == 0


def test_fallback_da_capa_renderiza_dentro_de_tamanhos_pequenos() -> None:
    app = _app()
    for largura, altura in ((20, 20), (30, 30), (44, 28)):
        capa = CapaMusicaGenerica(30)
        capa.setFixedSize(largura, altura)
        pixmap = QPixmap(largura, altura)
        pixmap.fill()
        capa.render(pixmap)
        app.processEvents()
        assert pixmap.size().width() == largura
        assert pixmap.size().height() == altura


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

from __future__ import annotations

from pathlib import Path
import time

import pytest


CONVERSA_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
CONVERSA_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


def _janela(monkeypatch, *, reduzir_movimento: bool = False):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv(
        "LAYLAY_REDUZIR_MOVIMENTO",
        "1" if reduzir_movimento else "0",
    )
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_laylay_2 import JanelaLaylay

    class Worker(QObject):
        mensagem = Signal(dict)
        conectado = Signal(bool)
        falha = Signal(str)

        def __init__(self):
            super().__init__()
            self.enviadas: list[dict] = []

        def enfileirar(self, mensagem):
            self.enviadas.append(dict(mensagem))
            return True

        def parar(self):
            return None

    app = QApplication.instance() or QApplication([])
    worker = Worker()
    janela = JanelaLaylay(worker, Path(__file__).parents[1])
    janela.show()
    worker.conectado.emit(True)
    app.processEvents()
    return app, worker, janela


def _processar_por(app, segundos: float) -> None:
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        app.processEvents()
        time.sleep(0.005)


def _retrato(ativa: str, *, incluir_b: bool, mensagens: list[dict]) -> dict:
    itens = [{"id": CONVERSA_A, "title": "Código", "active": ativa == CONVERSA_A}]
    if incluir_b:
        itens.append({
            "id": CONVERSA_B,
            "title": "Música",
            "active": ativa == CONVERSA_B,
        })
    return {
        "available": True,
        "active_id": ativa,
        "items": itens,
        "messages": mensagens,
    }


def _assert_linhas_sem_sobreposicao(janela) -> None:
    linhas = sorted(
        janela.feed.findChildren(type(janela.feed), "messageRow"),
        key=lambda item: item.geometry().top(),
    )
    assert linhas
    for anterior, seguinte in zip(linhas, linhas[1:]):
        assert seguinte.geometry().top() >= anterior.geometry().bottom()


def _x_no_feed(widget, janela) -> int:
    from PySide6.QtCore import QPoint

    return widget.mapTo(janela.feed, QPoint(0, 0)).x()


def test_baloes_preservam_lados_opostos_e_liberam_o_efeito(monkeypatch) -> None:
    app, _worker, janela = _janela(monkeypatch)
    usuario = janela.adicionar_mensagem("user", "Mensagem da direita")
    laylay = janela.adicionar_mensagem("assistant", "Resposta da esquerda")
    assert usuario is not None and laylay is not None
    linha_usuario = usuario.parentWidget()
    linha_laylay = laylay.parentWidget()

    assert linha_usuario.property("entryDirection") == "right"
    assert linha_laylay.property("entryDirection") == "left"
    assert linha_usuario.graphicsEffect() is not None
    assert linha_laylay.graphicsEffect() is not None

    _processar_por(app, 0.32)

    assert linha_usuario.graphicsEffect() is None
    assert linha_laylay.graphicsEffect() is None
    assert janela._animacoes == []
    assert _x_no_feed(usuario, janela) > _x_no_feed(laylay, janela)
    janela.close()


def test_animacao_nao_move_as_linhas_reservadas_pelo_layout(monkeypatch) -> None:
    app, _worker, janela = _janela(monkeypatch)
    textos = (
        ("assistant", "Uma resposta maior, com duas ideias e altura variável no balão."),
        ("user", "Tudo bem?"),
        ("assistant", "Oi! Tudo bem?"),
        ("user", "Como você está hoje?"),
    )
    mensagens = []
    for papel, texto in textos:
        mensagem = janela.adicionar_mensagem(papel, texto)
        assert mensagem is not None
        mensagens.append(mensagem)
    janela.feed_lay.activate()
    app.processEvents()
    geometrias_iniciais = {
        id(linha): linha.geometry()
        for linha in janela.feed.findChildren(type(janela.feed), "messageRow")
    }
    _assert_linhas_sem_sobreposicao(janela)

    _processar_por(app, 0.12)
    _assert_linhas_sem_sobreposicao(janela)
    assert {
        id(linha): linha.geometry()
        for linha in janela.feed.findChildren(type(janela.feed), "messageRow")
    } == geometrias_iniciais

    _processar_por(app, 0.22)
    _assert_linhas_sem_sobreposicao(janela)
    usuarios = [item for item in mensagens if item.papel == "user"]
    respostas = [item for item in mensagens if item.papel == "assistant"]
    assert usuarios and respostas
    assert min(_x_no_feed(item, janela) for item in usuarios) > max(
        _x_no_feed(item, janela) for item in respostas
    )
    janela.close()


def test_pensamento_pulsa_e_cruza_com_a_resposta_sem_duplicar(monkeypatch) -> None:
    app, worker, janela = _janela(monkeypatch)
    janela.enviar_texto("Pensa nisso")
    indicador = janela._indicador_pensando
    assert indicador is not None
    assert indicador._grupo_pontos is not None
    assert indicador._grupo_pontos.loopCount() == -1
    assert len(indicador.pontos) == 3
    opacidades = [efeito.opacity() for efeito in indicador._efeitos_pontos]

    _processar_por(app, 0.26)
    assert [
        efeito.opacity() for efeito in indicador._efeitos_pontos
    ] != opacidades

    pedido_id = worker.enviadas[-1]["id"]
    janela.receber({
        "type": "assistant_message",
        "id": pedido_id,
        "text": "Resposta pronta.",
    })
    app.processEvents()
    assert janela._indicador_pensando is None
    assert janela._animacao_saida_pensando is not None

    _processar_por(app, 0.34)
    assert janela._animacao_saida_pensando is None
    assert janela._container_saida_pensando is None
    janela.close()


def test_criar_chat_expande_item_e_historico_entra_sem_sobreposicao(
    monkeypatch,
) -> None:
    app, _worker, janela = _janela(monkeypatch)
    janela.receber({
        "type": "snapshot",
        "messages": [{"role": "assistant", "content": "Contexto antigo"}],
        "events": [],
        "state": {},
        "conversations": _retrato(
            CONVERSA_A,
            incluir_b=False,
            mensagens=[],
        ),
    })
    _processar_por(app, 0.9)

    janela.receber({
        "type": "conversations_state",
        "id": "criar-b",
        "action": "create",
        "success": True,
        "conversations": _retrato(
            CONVERSA_B,
            incluir_b=True,
            mensagens=[],
        ),
    })
    app.processEvents()

    assert janela._conversa_ativa_id == CONVERSA_B
    posicao_feed = janela.feed.pos()
    assert janela._animacao_troca_conversa is not None
    assert janela._animacoes_conversas
    assert janela.feed.graphicsEffect() is not None

    _processar_por(app, 0.36)

    assert janela.feed.pos() == posicao_feed
    assert janela._animacao_troca_conversa is None
    assert janela._animacoes_conversas == []
    assert janela.feed.graphicsEffect() is None
    assert janela._botoes_conversas[CONVERSA_B].isChecked()
    janela.close()


def test_a2_respeita_movimento_reduzido(monkeypatch) -> None:
    app, _worker, janela = _janela(monkeypatch, reduzir_movimento=True)
    mensagem = janela.adicionar_mensagem("assistant", "Sem movimento")
    assert mensagem is not None
    assert mensagem.parentWidget().graphicsEffect() is None

    janela._mostrar_indicador_pensando()
    assert janela._indicador_pensando is not None
    assert janela._indicador_pensando._grupo_pontos is None
    janela._remover_indicador_pensando(animar=True)
    assert janela._animacao_saida_pensando is None
    app.processEvents()
    janela.close()

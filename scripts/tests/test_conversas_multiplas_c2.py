from __future__ import annotations

import json
from pathlib import Path
import socket
import time

import pytest

from mente_laylay.integracao.desktop_bridge import (
    DesktopBridgeRuntime,
    ErroProtocoloDesktop,
    sanitizar_conversas,
    validar_mensagem_cliente,
)


CONVERSA_A = "11111111-1111-4111-8111-111111111111"
CONVERSA_B = "22222222-2222-4222-8222-222222222222"


def _enviar(sock: socket.socket, **mensagem) -> None:
    sock.sendall((json.dumps(mensagem) + "\n").encode("utf-8"))


def _linha(sock: socket.socket, *, timeout: float = 1.0) -> dict:
    sock.settimeout(timeout)
    dados = b""
    while not dados.endswith(b"\n"):
        bloco = sock.recv(1)
        if not bloco:
            break
        dados += bloco
    return json.loads(dados.decode("utf-8"))


def _linha_tipo(sock: socket.socket, tipo: str) -> dict:
    limite = time.monotonic() + 1.5
    while time.monotonic() < limite:
        mensagem = _linha(sock, timeout=max(0.05, limite - time.monotonic()))
        if mensagem.get("type") == tipo:
            return mensagem
    raise AssertionError(f"mensagem {tipo} não chegou")


def test_protocolo_de_conversas_limita_metadados_e_rejeita_id_arbitrario() -> None:
    retrato = sanitizar_conversas([
        {
            "id": CONVERSA_A,
            "titulo": "  Projeto   Laylay  ",
            "atualizada_em": "2026-08-20 12:00:00",
            "mensagens": 7,
            "contexto": {"senha": "não atravessa"},
            "resumo": "também não atravessa",
        },
        {"id": "../../memoria.db", "titulo": "inválida"},
    ], ativa_id=CONVERSA_A)
    assert retrato == {
        "active_id": CONVERSA_A,
        "items": [{
            "id": CONVERSA_A,
            "title": "Projeto Laylay",
                "updated_at": "2026-08-20 12:00:00",
                "message_count": 7,
                "status": "active",
                "pinned": False,
                "active": True,
        }],
    }
    with pytest.raises(ErroProtocoloDesktop, match="identificador"):
        validar_mensagem_cliente(
            {
                "type": "conversation_select",
                "conversation_id": "../../memoria.db",
            },
            token="x",
            autenticado=True,
        )


def test_titulo_automatico_nomeia_so_primeira_entrada_e_respeita_renomeacao(
    tmp_path,
) -> None:
    from memoria_sqlite import MemoriaSQLite
    from mente_laylay.memoria_mental.conversas_runtime import (
        GerenciadorConversasRuntime,
    )
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
        EstadoCompartilhadoRuntime,
    )
    from mente_laylay.memoria_mental.estado_contexto import (
        criar_estado_mental_inicial,
    )
    from mente_laylay.memoria_mental.estado_continuidades import (
        estado_continuidades_inicial,
    )

    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    estado = EstadoCompartilhadoRuntime(
        continuidades=estado_continuidades_inicial(),
        musical={}, percepcao={}, mental=criar_estado_mental_inicial(),
        conversacional={"current_emotion": "calma"},
        memoria_conversa={"messages": [], "resumo_conversa": ""},
    )
    runtime = GerenciadorConversasRuntime(
        memoria_sqlite=memoria,
        estado_compartilhado=estado,
        base_system_prompt="Você é a Laylay.",
        log=lambda *_args: None,
    )
    conversa = runtime.inicializar_legado(mensagens=[])

    assert runtime.nomear_automaticamente(
        conversa["id"], "Vamos trabalhar no projeto Aurora?",
    ) is True
    assert memoria.carregar_conversa(conversa["id"])["titulo"] == (
        "Vamos trabalhar no projeto Aurora"
    )
    assert runtime.renomear(conversa["id"], "Aurora manual") is True
    assert runtime.nomear_automaticamente(
        conversa["id"], "Isto não deve substituir",
    ) is False
    assert memoria.carregar_conversa(conversa["id"])["titulo"] == "Aurora manual"


def test_ponte_cria_seleciona_renomeia_e_exclui_so_apos_nucleo_confirmar() -> None:
    estado = {
        "active": CONVERSA_A,
        "items": {
            CONVERSA_A: {"title": "Primeira", "messages": []},
        },
    }

    def listar():
        return [
            {
                "id": conversa_id,
                "titulo": item["title"],
                "mensagens": len(item["messages"]),
                "atualizada_em": "2026-08-20 12:00:00",
            }
            for conversa_id, item in estado["items"].items()
        ]

    def criar(titulo: str):
        estado["items"][CONVERSA_B] = {"title": titulo, "messages": []}
        estado["active"] = CONVERSA_B
        return {"id": CONVERSA_B}

    def selecionar(conversa_id: str):
        if conversa_id not in estado["items"]:
            return None
        estado["active"] = conversa_id
        return {"id": conversa_id}

    def renomear(conversa_id: str, titulo: str):
        estado["items"][conversa_id]["title"] = titulo
        return True

    def excluir(conversa_id: str):
        estado["items"].pop(conversa_id)
        estado["active"] = next(iter(estado["items"]))
        return True

    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=lambda: estado["items"][estado["active"]]["messages"],
        estado_getter=dict,
        conversas_getter=listar,
        conversa_ativa_getter=lambda: estado["active"],
        conversa_criar=criar,
        conversa_selecionar=selecionar,
        conversa_renomear=renomear,
        conversa_excluir=excluir,
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, type="hello", token=runtime.token)
            snapshot = _linha(cliente)
            assert snapshot["conversations"]["active_id"] == CONVERSA_A

            _enviar(cliente, type="conversation_create", id="c1", title="Música")
            criado = _linha_tipo(cliente, "conversations_state")
            assert criado["success"] is True
            assert criado["action"] == "create"
            assert criado["conversations"]["active_id"] == CONVERSA_B

            _enviar(
                cliente, type="conversation_rename", id="r1",
                conversation_id=CONVERSA_B, title="Música e playlists",
            )
            renomeado = _linha_tipo(cliente, "conversations_state")
            assert renomeado["success"] is True
            titulos = {
                item["id"]: item["title"]
                for item in renomeado["conversations"]["items"]
            }
            assert titulos[CONVERSA_B] == "Música e playlists"

            _enviar(
                cliente, type="conversation_select", id="s1",
                conversation_id=CONVERSA_A,
            )
            selecionado = _linha_tipo(cliente, "conversations_state")
            assert selecionado["conversations"]["active_id"] == CONVERSA_A

            _enviar(
                cliente, type="conversation_delete", id="d1",
                conversation_id=CONVERSA_B,
            )
            excluido = _linha_tipo(cliente, "conversations_state")
            assert excluido["success"] is True
            assert [
                item["id"] for item in excluido["conversations"]["items"]
            ] == [CONVERSA_A]
    finally:
        runtime.parar()


def test_envio_stale_e_recusado_e_resposta_atrasada_mantem_chat_de_origem() -> None:
    ativa = {"id": CONVERSA_A}
    entradas: list[str] = []
    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda texto: entradas.append(texto) or True,
        historico_getter=list,
        estado_getter=dict,
        conversas_getter=lambda: [],
        conversa_ativa_getter=lambda: ativa["id"],
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, type="hello", token=runtime.token)
            _linha(cliente)
            _enviar(
                cliente, type="input_submit", id="stale", text="oi",
                conversation_id=CONVERSA_B,
            )
            recusado = _linha_tipo(cliente, "input_ack")
            assert recusado["accepted"] is False
            assert entradas == []

            _enviar(
                cliente, type="input_submit", id="turno-a", text="oi",
                conversation_id=CONVERSA_A,
            )
            assert _linha_tipo(cliente, "input_ack")["accepted"] is True
            ativa["id"] = CONVERSA_B
            runtime.publicar_fala_final("Resposta do chat A")
            resposta = _linha_tipo(cliente, "assistant_message")
            assert resposta["conversation_id"] == CONVERSA_A
            assert resposta["text"] == "Resposta do chat A"
    finally:
        runtime.parar()


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
    app.processEvents()
    worker.conectado.emit(True)
    app.processEvents()
    worker.enviadas.clear()
    return app, worker, janela


def _retrato(ativa: str, *, mensagens: list[dict] | None = None) -> dict:
    return {
        "available": True,
        "active_id": ativa,
        "items": [
            {"id": CONVERSA_A, "title": "Código", "active": ativa == CONVERSA_A},
            {"id": CONVERSA_B, "title": "Música", "active": ativa == CONVERSA_B},
        ],
        "messages": list(mensagens or []),
    }


def test_terminal_lista_troca_e_envia_no_chat_confirmado(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    from cliente.terminal_laylay_2 import MensagemWidget
    janela.receber({
        "type": "snapshot",
        "messages": [{"role": "assistant", "content": "Contexto de código"}],
        "events": [], "state": {},
        "conversations": _retrato(CONVERSA_A),
    })
    app.processEvents()
    assert janela._conversa_ativa_id == CONVERSA_A
    assert set(janela._botoes_conversas) == {CONVERSA_A, CONVERSA_B}
    assert not any(
        item.get("type") == "conversations_get" for item in worker.enviadas
    )

    janela._botoes_conversas[CONVERSA_B].click()
    app.processEvents()
    pedido = worker.enviadas[-1]
    assert pedido["type"] == "conversation_select"
    assert pedido["conversation_id"] == CONVERSA_B
    assert janela._conversa_ativa_id == CONVERSA_A

    janela.receber({
        "type": "conversations_state", "id": pedido["id"],
        "action": "select", "success": True,
        "conversations": _retrato(
            CONVERSA_B,
            mensagens=[{"role": "assistant", "content": "Contexto musical"}],
        ),
    })
    app.processEvents()
    assert janela._conversa_ativa_id == CONVERSA_B
    assert "Contexto musical" in [
        item.texto for item in janela.feed.findChildren(MensagemWidget)
    ]
    assert "Contexto de código" not in [
        item.texto for item in janela.feed.findChildren(MensagemWidget)
    ]
    janela.enviar_texto("Toca rock")
    assert worker.enviadas[-1]["conversation_id"] == CONVERSA_B
    janela.close()


def test_trocas_repetidas_descartam_widgets_aninhados_sem_sobreposicao(
    monkeypatch,
) -> None:
    app, _worker, janela = _criar_janela(monkeypatch)
    from cliente.terminal_laylay_2 import MensagemWidget

    janela.receber({
        "type": "snapshot", "events": [], "state": {},
        "messages": [
            {"role": "user", "content": "oi lay"},
            {"role": "assistant", "content": "Oi! Tudo bem?"},
        ],
        "conversations": _retrato(CONVERSA_A),
    })
    app.processEvents()
    assert [
        item.texto for item in janela.feed.findChildren(MensagemWidget)
    ] == ["oi lay", "Oi! Tudo bem?"]

    janela.receber({
        "type": "conversations_state", "id": "troca-b", "action": "select",
        "success": True,
        "conversations": _retrato(CONVERSA_B, mensagens=[
            {"role": "user", "content": "tudo bem com você?"},
            {"role": "assistant", "content": "Tudo certo por aqui."},
        ]),
    })
    app.processEvents()
    assert [
        item.texto for item in janela.feed.findChildren(MensagemWidget)
    ] == ["tudo bem com você?", "Tudo certo por aqui."]

    janela.receber({
        "type": "conversations_state", "id": "troca-a", "action": "select",
        "success": True,
        "conversations": _retrato(CONVERSA_A, mensagens=[
            {"role": "user", "content": "oi lay"},
            {"role": "assistant", "content": "Oi! Tudo bem?"},
        ]),
    })
    app.processEvents()
    assert [
        item.texto for item in janela.feed.findChildren(MensagemWidget)
    ] == ["oi lay", "Oi! Tudo bem?"]
    assert len(janela.feed.findChildren(MensagemWidget)) == 2
    janela.close()


def test_terminal_nao_exibe_resposta_atrasada_no_chat_aberto(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    from cliente.terminal_laylay_2 import MensagemWidget

    janela.receber({
        "type": "snapshot", "messages": [], "events": [], "state": {},
        "conversations": _retrato(CONVERSA_A),
    })
    janela.enviar_texto("Pergunta demorada")
    mensagem_id = worker.enviadas[-1]["id"]
    janela.receber({
        "type": "conversations_state", "id": "troca", "action": "select",
        "success": True, "conversations": _retrato(CONVERSA_B),
    })
    janela.receber({
        "type": "assistant_message", "id": mensagem_id,
        "conversation_id": CONVERSA_A, "text": "Resposta exclusiva do A",
    })
    app.processEvents()
    textos = [item.texto for item in janela.feed.findChildren(MensagemWidget)]
    assert "Resposta exclusiva do A" not in textos
    assert mensagem_id not in janela._envios
    janela.close()


def test_novo_chat_e_uma_aba_lateral_e_permanece_acessivel_recolhido(
    monkeypatch,
) -> None:
    app, worker, janela = _criar_janela(monkeypatch)

    assert janela.nova.parentWidget() is janela.sidebar
    assert janela.nova.property("nav") is True
    assert janela.nova.text() == "Novo chat"
    assert janela.nova.icon().isNull() is False
    assert janela.nova.height() == janela._nav["inicio"].height()
    assert janela.nova.width() == janela._nav["inicio"].width()

    janela.nova.click()
    app.processEvents()
    assert worker.enviadas[-1]["type"] == "conversation_create"

    janela._sidebar_expandida = False
    janela._aplicar_sidebar()
    app.processEvents()
    assert janela.nova.isHidden() is False
    assert janela.nova.text() == ""
    assert janela.nova.toolTip() == "Criar um novo chat"
    janela.close()


def test_raiz_compoe_todas_as_portas_c2() -> None:
    fonte = (Path(__file__).parents[1] / "laylay.py").read_text(encoding="utf-8")
    for nome in (
        "conversas_getter", "conversa_ativa_getter", "conversa_criar",
        "conversa_selecionar", "conversa_renomear", "conversa_excluir",
        "conversa_nomear_automaticamente",
    ):
        assert f"{nome}=" in fonte

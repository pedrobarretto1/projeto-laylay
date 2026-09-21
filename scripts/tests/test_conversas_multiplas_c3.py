from __future__ import annotations

import ast
import json
from pathlib import Path
import socket
import time

import pytest

from memoria_sqlite import MemoriaSQLite
from mente_laylay.integracao.desktop_bridge import (
    DesktopBridgeRuntime,
    ErroProtocoloDesktop,
    sanitizar_conversas,
    validar_mensagem_cliente,
)
from mente_laylay.memoria_mental.conversas_runtime import (
    GerenciadorConversasRuntime,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
from mente_laylay.memoria_mental.estado_continuidades import (
    estado_continuidades_inicial,
)


PROMPT = "Você é a Laylay."
CONVERSA_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
CONVERSA_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
CONVERSA_C = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def _gerenciador(tmp_path):
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    estado = EstadoCompartilhadoRuntime(
        continuidades=estado_continuidades_inicial(),
        musical={},
        percepcao={},
        mental=criar_estado_mental_inicial(),
        conversacional={"current_emotion": "calma"},
        memoria_conversa={"messages": [], "resumo_conversa": ""},
    )
    runtime = GerenciadorConversasRuntime(
        memoria_sqlite=memoria,
        estado_compartilhado=estado,
        base_system_prompt=PROMPT,
        log=lambda *_args: None,
    )
    return memoria, estado, runtime


def test_fixar_arquivar_e_restaurar_preservam_contexto_isolado(tmp_path) -> None:
    memoria, estado, runtime = _gerenciador(tmp_path)
    conversa_a = runtime.inicializar_legado(
        mensagens=[{"role": "user", "content": "Contexto do projeto Aurora"}],
    )
    conversa_b = runtime.criar("Música")
    estado.atualizar_campos("mental", ultimo_arquivo="playlist.json")
    runtime.substituir_mensagens([
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": "Contexto musical exclusivo"},
    ])

    assert runtime.fixar(conversa_a["id"], True) is True
    assert runtime.listar_para_terminal()[0]["id"] == conversa_a["id"]
    assert runtime.listar_para_terminal()[0]["fixada"] is True

    assert runtime.arquivar(conversa_b["id"]) is True
    assert runtime.id_ativo() == conversa_a["id"]
    arquivada = memoria.carregar_conversa(conversa_b["id"])
    assert arquivada is not None
    assert arquivada["status"] == "arquivada"
    assert arquivada["contexto"]["mental"]["ultimo_arquivo"] == "playlist.json"
    assert any(
        item.get("content") == "Contexto musical exclusivo"
        for item in arquivada["mensagens"]
    )
    assert runtime.selecionar(conversa_b["id"]) is None
    assert conversa_b["id"] not in {item["id"] for item in runtime.listar()}

    assert runtime.desarquivar(conversa_b["id"]) is True
    assert runtime.selecionar(conversa_b["id"]) is not None
    assert estado.mental["ultimo_arquivo"] == "playlist.json"


def test_arquivar_unico_chat_cria_outro_sem_apagar_memoria_global(tmp_path) -> None:
    memoria, estado, runtime = _gerenciador(tmp_path)
    conversa = runtime.inicializar_legado(
        mensagens=[{"role": "user", "content": "Assunto exclusivo"}],
    )
    estado.atualizar_campos("mental", nome_usuario="Pedro")

    assert runtime.arquivar(conversa["id"]) is True
    assert runtime.id_ativo() != conversa["id"]
    assert estado.mental["nome_usuario"] == "Pedro"
    assert memoria.carregar_conversa(conversa["id"])["status"] == "arquivada"
    assert len(runtime.listar()) == 1
    assert len(runtime.listar_para_terminal()) == 2


def test_inicio_neutro_preserva_chats_e_primeira_entrada_cria_outro(
    tmp_path,
) -> None:
    memoria, estado, runtime = _gerenciador(tmp_path)
    anterior = runtime.inicializar_legado(mensagens=[
        {"role": "user", "content": "Contexto que precisa continuar salvo"},
    ])
    estado.atualizar_campos("mental", nome_usuario="Pedro")
    estado.atualizar_campos("mental", ultimo_arquivo="antigo.txt")
    assert runtime.salvar_ativa() is True

    runtime.iniciar_sem_conversa()

    assert runtime.id_ativo() == ""
    assert estado.mental["nome_usuario"] == "Pedro"
    assert estado.mental["ultimo_arquivo"] == ""
    assert len(runtime.listar_para_terminal()) == 1
    assert any(
        item.get("content") == "Contexto que precisa continuar salvo"
        for item in memoria.carregar_conversa(anterior["id"])["mensagens"]
    )

    nova_id = runtime.garantir_para_entrada()

    assert nova_id and nova_id != anterior["id"]
    assert runtime.id_ativo() == nova_id
    assert len(runtime.listar_para_terminal()) == 2
    assert [
        item for item in runtime.mensagens(nova_id)
        if item.get("role") != "system"
    ] == []


def test_ponte_cria_chat_antes_de_entregar_primeira_mensagem() -> None:
    ativa = {"id": ""}
    itens: list[dict] = []
    entregues: list[tuple[str, str]] = []

    def criar(_titulo: str):
        ativa["id"] = CONVERSA_A
        itens.append({
            "id": CONVERSA_A,
            "titulo": "Nova conversa",
            "status": "ativa",
            "fixada": False,
            "mensagens": 0,
        })
        return {"id": CONVERSA_A}

    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda texto: entregues.append(
            (ativa["id"], str(texto)),
        ) or True,
        historico_getter=list,
        estado_getter=dict,
        conversas_getter=lambda: itens,
        conversa_ativa_getter=lambda: ativa["id"],
        conversa_criar=criar,
        conversa_nomear_automaticamente=lambda *_args: False,
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, type="hello", token=runtime.token)
            snapshot = _linha_tipo(cliente, "snapshot")
            assert snapshot["conversations"]["active_id"] == ""
            assert snapshot["conversations"]["items"] == []

            _enviar(
                cliente,
                type="input_submit",
                id="primeira",
                text="Primeiro assunto deste chat",
                kind="chat",
            )
            criado = _linha_tipo(cliente, "conversations_state")
            recibo = _linha_tipo(cliente, "input_ack")

            assert criado["action"] == "auto_create"
            assert criado["conversations"]["active_id"] == CONVERSA_A
            assert recibo["accepted"] is True
            assert entregues == [
                (CONVERSA_A, "Primeiro assunto deste chat"),
            ]
    finally:
        runtime.parar()


def test_sanitizador_c3_expoe_so_metadados_e_descarta_tombstone() -> None:
    retrato = sanitizar_conversas([
        {
            "id": CONVERSA_A,
            "titulo": "Projeto Aurora",
            "status": "ativa",
            "fixada": True,
            "mensagens": 4,
            "resumo": "segredo",
            "contexto": {"ultimo_arquivo": "privado.txt"},
        },
        {
            "id": CONVERSA_B,
            "titulo": "Música",
            "status": "arquivada",
            "fixada": False,
            "mensagens": 8,
        },
        {"id": CONVERSA_C, "titulo": "apagada", "status": "excluida"},
    ], ativa_id=CONVERSA_A)

    assert retrato["items"] == [
        {
            "id": CONVERSA_A,
            "title": "Projeto Aurora",
            "updated_at": "",
            "message_count": 4,
            "status": "active",
            "pinned": True,
            "active": True,
        },
        {
            "id": CONVERSA_B,
            "title": "Música",
            "updated_at": "",
            "message_count": 8,
            "status": "archived",
            "pinned": False,
            "active": False,
        },
    ]
    assert "segredo" not in repr(retrato)
    assert "privado.txt" not in repr(retrato)


def test_protocolo_c3_exige_id_e_booleano_real_para_fixacao() -> None:
    validada = validar_mensagem_cliente(
        {
            "type": "conversation_pin",
            "id": "pin-1",
            "conversation_id": CONVERSA_A,
            "pinned": True,
        },
        token="x",
        autenticado=True,
    )
    assert validada["pinned"] is True
    with pytest.raises(ErroProtocoloDesktop, match="fixação"):
        validar_mensagem_cliente(
            {
                "type": "conversation_pin",
                "conversation_id": CONVERSA_A,
                "pinned": "sim",
            },
            token="x",
            autenticado=True,
        )


def _enviar(sock: socket.socket, **mensagem) -> None:
    sock.sendall((json.dumps(mensagem) + "\n").encode("utf-8"))


def _linha_tipo(sock: socket.socket, tipo: str) -> dict:
    limite = time.monotonic() + 1.5
    dados = b""
    sock.settimeout(1.5)
    while time.monotonic() < limite:
        bloco = sock.recv(1)
        if not bloco:
            break
        dados += bloco
        if not dados.endswith(b"\n"):
            continue
        mensagem = json.loads(dados.decode("utf-8"))
        dados = b""
        if mensagem.get("type") == tipo:
            return mensagem
    raise AssertionError(f"mensagem {tipo} não chegou")


def test_ponte_despacha_fixacao_arquivo_e_restaura_pelas_portas_canonicas(
) -> None:
    chamadas: list[tuple] = []
    itens = [{
        "id": CONVERSA_A, "titulo": "Aurora", "status": "ativa",
        "fixada": False, "mensagens": 0,
    }]
    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=list,
        estado_getter=dict,
        conversas_getter=lambda: itens,
        conversa_ativa_getter=lambda: CONVERSA_A,
        conversa_fixar=lambda cid, valor: chamadas.append(
            ("fixar", cid, valor),
        ) or True,
        conversa_arquivar=lambda cid: chamadas.append(
            ("arquivar", cid),
        ) or True,
        conversa_desarquivar=lambda cid: chamadas.append(
            ("restaurar", cid),
        ) or True,
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, type="hello", token=runtime.token)
            assert _linha_tipo(cliente, "snapshot")["type"] == "snapshot"
            for pedido, chamada in (
                (
                    {
                        "type": "conversation_pin", "id": "p1",
                        "conversation_id": CONVERSA_A, "pinned": True,
                    },
                    ("fixar", CONVERSA_A, True),
                ),
                (
                    {
                        "type": "conversation_archive", "id": "a1",
                        "conversation_id": CONVERSA_A,
                    },
                    ("arquivar", CONVERSA_A),
                ),
                (
                    {
                        "type": "conversation_unarchive", "id": "u1",
                        "conversation_id": CONVERSA_A,
                    },
                    ("restaurar", CONVERSA_A),
                ),
            ):
                _enviar(cliente, **pedido)
                resposta = _linha_tipo(cliente, "conversations_state")
                assert resposta["success"] is True
                assert chamadas[-1] == chamada
    finally:
        runtime.parar()


def _janela(monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
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
    worker.enviadas.clear()
    return app, worker, janela


def _retrato_c3() -> dict:
    return {
        "available": True,
        "active_id": CONVERSA_A,
        "items": [
            {
                "id": CONVERSA_A, "title": "Projeto Aurora",
                "status": "active", "pinned": True, "active": True,
            },
            {
                "id": CONVERSA_B, "title": "Música e playlists",
                "status": "active", "pinned": False, "active": False,
            },
            {
                "id": CONVERSA_C, "title": "Receitas antigas",
                "status": "archived", "pinned": False, "active": False,
            },
        ],
        "messages": [],
    }


def test_terminal_pesquisa_fixa_e_revela_arquivadas_sem_expor_conteudo(
    monkeypatch,
) -> None:
    app, worker, janela = _janela(monkeypatch)
    from PySide6.QtWidgets import QLabel

    janela.receber({
        "type": "snapshot", "messages": [], "events": [], "state": {},
        "conversations": _retrato_c3(),
    })
    app.processEvents()
    assert set(janela._botoes_conversas) == {CONVERSA_A, CONVERSA_B}
    assert janela._botoes_conversas[CONVERSA_A].text().startswith("★")
    secoes = {
        label.text()
        for label in janela.conversas_container.findChildren(
            QLabel, "conversationSection",
        )
    }
    assert {"FIXADAS", "RECENTES"}.issubset(secoes)
    assert "ARQUIVADAS" not in secoes

    janela.busca_conversas.setText("receitas")
    app.processEvents()
    assert set(janela._botoes_conversas) == {CONVERSA_C}
    assert janela._botoes_conversas[CONVERSA_C].isEnabled() is False

    janela.busca_conversas.clear()
    janela.botao_arquivadas.setChecked(True)
    app.processEvents()
    assert set(janela._botoes_conversas) == {
        CONVERSA_A, CONVERSA_B, CONVERSA_C,
    }

    janela.fixar_conversa(CONVERSA_B, True)
    assert worker.enviadas[-1] == {
        "type": "conversation_pin",
        "id": worker.enviadas[-1]["id"],
        "conversation_id": CONVERSA_B,
        "pinned": True,
    }
    janela.close()


def test_terminal_inicia_sem_selecionar_ou_reidratar_chat_antigo(
    monkeypatch,
) -> None:
    app, _worker, janela = _janela(monkeypatch)
    retrato = _retrato_c3()
    retrato["active_id"] = ""
    for item in retrato["items"]:
        item["active"] = False

    janela.receber({
        "type": "snapshot",
        "messages": [{
            "role": "assistant",
            "content": "Esta fala pertence ao chat antigo",
        }],
        "events": [],
        "state": {},
        "conversations": retrato,
    })
    app.processEvents()

    assert janela._conversa_ativa_id == ""
    assert janela.conversa_atual.text() == "Nenhuma conversa"
    assert not any(botao.isChecked() for botao in janela._botoes_conversas.values())
    from PySide6.QtWidgets import QLabel
    assert "Esta fala pertence ao chat antigo" not in " ".join(
        label.text() for label in janela.feed.findChildren(QLabel)
    )
    janela.close()


def test_raiz_liga_as_portas_c3_sem_regra_de_dominio_na_ui() -> None:
    raiz = Path(__file__).parents[1] / "laylay.py"
    arvore = ast.parse(raiz.read_text(encoding="utf-8"))
    chamada = next(
        no.value
        for no in ast.walk(arvore)
        if isinstance(no, ast.Assign)
        and any(
            isinstance(alvo, ast.Name)
            and alvo.id == "_desktop_bridge_runtime"
            for alvo in no.targets
        )
        and isinstance(no.value, ast.Call)
    )
    kwargs = {item.arg for item in chamada.keywords}
    assert {
        "conversa_arquivar", "conversa_desarquivar", "conversa_fixar",
    }.issubset(kwargs)

    persistencia = next(
        no.value
        for no in ast.walk(arvore)
        if isinstance(no, ast.Assign)
        and any(
            isinstance(alvo, ast.Name)
            and alvo.id == "_persistencia_memoria_runtime"
            for alvo in no.targets
        )
        and isinstance(no.value, ast.Call)
    )
    kwargs_persistencia = {
        item.arg: item.value for item in persistencia.keywords
    }
    assert isinstance(kwargs_persistencia["iniciar_sem_conversa"], ast.Constant)
    assert kwargs_persistencia["iniciar_sem_conversa"].value is True

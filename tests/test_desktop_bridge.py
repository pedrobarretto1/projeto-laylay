from __future__ import annotations

import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time

import pytest

from mente_laylay.integracao.desktop_bridge import (
    DesktopBridgeRuntime,
    ErroProtocoloDesktop,
    sanitizar_configuracao,
    sanitizar_estado,
    sanitizar_historico,
    validar_mensagem_cliente,
)
from cliente.terminal_2.transporte import TransporteDesktopCliente


def _linha(sock: socket.socket, timeout: float = 1.0) -> dict:
    sock.settimeout(timeout)
    dados = b""
    while not dados.endswith(b"\n"):
        bloco = sock.recv(4096)
        if not bloco:
            break
        dados += bloco
    return json.loads(dados.decode("utf-8").splitlines()[0])


def _enviar(sock: socket.socket, **mensagem) -> None:
    sock.sendall((json.dumps(mensagem) + "\n").encode("utf-8"))


@pytest.fixture
def ponte():
    entradas: list[str] = []
    runtime = DesktopBridgeRuntime(
        enviar_entrada=entradas.append,
        historico_getter=lambda: [
            {"role": "system", "content": "segredo"},
            {"role": "user", "content": "oi"},
            {"role": "assistant", "content": "Oi. Tô aqui."},
        ],
        estado_getter=lambda: {
            "current_emotion": "curiosa", "visual_activity": "thinking",
            "token": "nunca expor",
        },
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        yield runtime, entradas
    finally:
        runtime.parar()


def test_snapshot_remove_sistema_e_estado_remove_dados_privados() -> None:
    assert sanitizar_historico([
        {"role": "system", "content": "segredo"},
        {"role": "user", "content": "  teste  ", "tool": "não"},
    ]) == [{"role": "user", "content": "teste"}]
    assert sanitizar_estado({
        "visual_activity": "thinking", "current_emotion": "feliz",
        "credencial": "não",
    }) == {
        "activity": "thinking", "activity_label": "Pensando",
        "emotion": "feliz", "emotion_level": 1, "voice_available": False,
        "interaction_mode": "chat",
    }


def test_configuracao_sanitizada_nunca_devolve_segredo() -> None:
    assert sanitizar_configuracao({
        "provider": "openrouter", "model": "qwen/model",
        "base_url": "https://openrouter.ai/api/v1", "api_key_configured": True,
        "api_key": "segredo", "token": "tambem-nao", "mascot_enabled": True,
    }) == {
        "provider": "openrouter", "model": "qwen/model",
        "models_by_provider": {"ollama": "", "portatil": "", "openrouter": ""},
        "base_url": "https://openrouter.ai/api/v1", "api_key_configured": True,
        "restart_required": False,
        "mascot_enabled": True,
    }


def test_snapshot_preserva_timestamp_existente_e_nao_inventa_ausente() -> None:
    mensagens = sanitizar_historico([
        {"role": "user", "content": "antes", "timestamp": 1_700_000_000},
        {"role": "assistant", "content": "depois"},
    ])
    assert mensagens[0]["timestamp"] == "1700000000.0"
    assert "timestamp" not in mensagens[1]


def test_token_tipo_e_entrada_grande_sao_validados() -> None:
    with pytest.raises(ErroProtocoloDesktop, match="token"):
        validar_mensagem_cliente(
            {"type": "hello", "token": "errado"}, token="certo", autenticado=False,
        )
    with pytest.raises(ErroProtocoloDesktop, match="tipo"):
        validar_mensagem_cliente({"type": "executar"}, token="x", autenticado=True)
    assert validar_mensagem_cliente(
        {"type": "restart_request", "id": "r1"}, token="x", autenticado=True,
    ) == {"type": "restart_request", "id": "r1"}
    validada = validar_mensagem_cliente(
        {"type": "input_submit", "text": "a" * 9_000}, token="x", autenticado=True,
    )
    assert len(validada["text"]) == 8_000
    with pytest.raises(ErroProtocoloDesktop, match="modo"):
        validar_mensagem_cliente(
            {"type": "mode_set", "mode": "talvez"}, token="x", autenticado=True,
        )
    with pytest.raises(ErroProtocoloDesktop, match="campos"):
        validar_mensagem_cliente(
            {"type": "settings_update", "settings": {"shell": "calc"}},
            token="x", autenticado=True,
        )
    with pytest.raises(ErroProtocoloDesktop, match="mascote"):
        validar_mensagem_cliente(
            {
                "type": "settings_update",
                "settings": {
                    "provider": "ollama", "model": "qwen",
                    "api_key_action": "preserve", "api_key": "",
                    "mascot_enabled": "1",
                },
            },
            token="x", autenticado=True,
        )


def test_handshake_snapshot_heartbeat_e_entrada_canonica_uma_vez(ponte) -> None:
    runtime, entradas = ponte
    with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
        _enviar(cliente, type="hello", token=runtime.token)
        snapshot = _linha(cliente)
        assert snapshot["type"] == "snapshot"
        assert [item["role"] for item in snapshot["messages"]] == ["user", "assistant"]
        assert snapshot["state"]["activity"] == "thinking"

        _enviar(cliente, type="heartbeat", id="h1")
        heartbeat = _linha(cliente)
        assert heartbeat["type"] == "state"
        assert heartbeat["heartbeat"] is True

        _enviar(cliente, type="input_submit", id="t1", text="liga a luz")
        ack = _linha(cliente)
        assert ack == {
            "type": "input_ack", "id": "t1", "accepted": True,
            "message": "",
        }
        limite = time.monotonic() + 1.0
        while not entradas and time.monotonic() < limite:
            time.sleep(0.01)
        assert entradas == ["liga a luz"]


def test_ack_rejeitado_quando_entrada_canonica_recusa() -> None:
    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: False,
        historico_getter=list,
        estado_getter=dict,
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, type="hello", token=runtime.token)
            _linha(cliente)
            _enviar(cliente, type="input_submit", id="recusado", text="teste")
            ack = _linha(cliente)
            assert ack["accepted"] is False
            assert ack["id"] == "recusado"
            assert "recusou" in ack["message"]
    finally:
        runtime.parar()


def test_fala_final_publicada_uma_vez_e_candidato_nao_vaza(ponte) -> None:
    runtime, _ = ponte
    with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
        _enviar(cliente, type="hello", token=runtime.token)
        _linha(cliente)
        # Um candidato interno não possui API na ponte; somente a fronteira
        # consolidada abaixo pode publicar assistant_message.
        runtime.publicar_fala_final(
            "Resposta confirmada", "feliz", 2,
            mensagem_id="turno:abc",
        )
        mensagem = _linha(cliente)
        assert mensagem["type"] == "assistant_message"
        assert mensagem["id"] == "turno:abc"
        assert mensagem["text"] == "Resposta confirmada"


def test_rate_limit_e_desconexao_nao_derrubam_runtime() -> None:
    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: None,
        historico_getter=list,
        estado_getter=dict,
        rate_limit=2,
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        cliente = socket.create_connection(runtime.endereco, timeout=1.0)
        _enviar(cliente, type="hello", token=runtime.token)
        _linha(cliente)
        _enviar(cliente, type="heartbeat")
        _linha(cliente)
        _enviar(cliente, type="heartbeat")
        assert _linha(cliente)["code"] == "rate_limited"
        cliente.close()
        time.sleep(0.05)
        assert runtime.diagnostico()["disponivel"] is True
    finally:
        runtime.parar()


def test_cliente_nao_importa_roteador_executor_ou_llm() -> None:
    fonte = (Path(__file__).parents[1] / "cliente" / "terminal_laylay_2.py").read_text(
        encoding="utf-8",
    )
    assert "mente_laylay.autonomia" not in fonte
    assert "cliente_llm" not in fonte
    assert "executar_intencao" not in fonte


def test_fila_do_cliente_entrega_ready_e_input_uma_vez_na_thread_do_socket() -> None:
    entradas: list[str] = []
    recebidas: list[dict] = []
    conectado = threading.Event()
    ack = threading.Event()
    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda texto: entradas.append(texto) or True,
        historico_getter=list,
        estado_getter=dict,
        log=lambda _texto: None,
    )
    runtime.iniciar()

    def ao_mensagem(mensagem: dict) -> None:
        recebidas.append(mensagem)
        if mensagem.get("type") == "input_ack":
            ack.set()

    transporte = TransporteDesktopCliente(
        *runtime.endereco, runtime.token,
        ao_mensagem=ao_mensagem,
        ao_conexao=lambda ativo: conectado.set() if ativo else None,
        ao_falha=lambda _erro: None,
        intervalo_heartbeat_s=0.3,
    )
    thread = threading.Thread(target=transporte.executar, daemon=True)
    thread.start()
    try:
        assert conectado.wait(1.5)
        assert transporte.enfileirar({"type": "ready", "id": "ready-1"})
        assert transporte.enfileirar({
            "type": "input_submit", "id": "input-1", "text": "liga a luz",
        })
        assert ack.wait(1.5)
        assert entradas == ["liga a luz"]
        assert sum(
            1 for item in recebidas
            if item.get("type") == "input_ack" and item.get("id") == "input-1"
        ) == 1
        assert transporte.thread_socket_id == thread.ident
    finally:
        transporte.parar()
        thread.join(timeout=1.0)
        runtime.parar()


def test_socket_do_cliente_recusa_escrita_fora_da_thread_proprietaria() -> None:
    transporte = TransporteDesktopCliente(
        "127.0.0.1", 1, "token",
        ao_mensagem=lambda _msg: None,
        ao_conexao=lambda _ativo: None,
        ao_falha=lambda _erro: None,
    )
    transporte.thread_socket_id = -1
    with pytest.raises(RuntimeError, match="thread proprietária"):
        transporte._enviar_agora({"type": "ready"})


def test_cliente_executado_como_script_enxerga_o_pacote_cliente() -> None:
    """Reproduz o lancamento usado por ``laylay.py`` sem abrir a janela Qt."""
    script = Path(__file__).parents[1] / "cliente" / "terminal_laylay_2.py"
    codigo = (
        "import runpy, sys; "
        "runpy.run_path(sys.argv[1], run_name='terminal_laylay_2_import_test')"
    )
    processo = subprocess.run(
        [sys.executable, "-c", codigo, str(script)],
        cwd=str(script.parents[1]),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    saida = f"{processo.stdout}\n{processo.stderr}"
    assert "No module named 'cliente'" not in saida


def test_smoke_import_cliente_pula_sem_pyside6() -> None:
    pytest.importorskip("PySide6")
    import cliente.terminal_laylay_2 as terminal

    assert callable(terminal.main)


def test_modo_chat_voz_usa_porta_canonica_uma_vez_e_reverte_falha() -> None:
    estado = {"modo": "chat", "voz": True}
    chamadas: list[bool] = []
    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=list,
        estado_getter=lambda: {
            "interaction_mode": estado["modo"], "voice_available": estado["voz"],
        },
        modo_setter=lambda ativo: chamadas.append(ativo) or estado.update(
            modo="chat" if ativo else "voice"
        ),
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, type="hello", token=runtime.token)
            _linha(cliente)
            _enviar(cliente, type="mode_set", id="m1", mode="voice")
            resposta = _linha(cliente)
            assert resposta["type"] == "mode_state"
            assert resposta["success"] is True
            assert resposta["mode"] == "voice"
            assert chamadas == [False]
            estado.update(modo="chat", voz=False)
            _enviar(cliente, type="mode_set", id="m2", mode="voice")
            resposta = _linha(cliente)
            assert resposta["success"] is False
            assert resposta["mode"] == "chat"
            assert chamadas == [False]
    finally:
        runtime.parar()


def test_settings_atravessam_ponte_sem_devolver_chave() -> None:
    recebidas: list[dict] = []
    estado_config = {
        "provider": "ollama", "model": "qwen", "base_url": "local",
        "api_key_configured": False, "mascot_enabled": False,
    }

    def salvar(payload: dict) -> dict:
        recebidas.append(dict(payload))
        estado_config.update(
            provider=payload["provider"], model=payload["model"],
            base_url="https://openrouter.ai/api/v1", api_key_configured=True,
            mascot_enabled=payload["mascot_enabled"],
        )
        return {
            "saved": True, "restart_required": True, "message": "salvo",
            "settings": {**estado_config, "api_key": payload.get("api_key")},
        }

    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=list,
        estado_getter=dict,
        configuracao_getter=lambda: estado_config,
        configuracao_setter=salvar,
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, type="hello", token=runtime.token)
            snapshot = _linha(cliente)
            assert snapshot["settings"]["provider"] == "ollama"
            _enviar(
                cliente, type="settings_update", id="s1",
                settings={
                    "provider": "openrouter", "model": "qwen/model",
                    "api_key_action": "replace", "api_key": "sk-segredo",
                    "mascot_enabled": True,
                },
            )
            resposta = _linha(cliente)
            assert resposta["type"] == "settings_result"
            assert resposta["saved"] is True
            assert resposta["restart_required"] is True
            assert "sk-segredo" not in json.dumps(resposta)
            assert recebidas[0]["api_key"] == "sk-segredo"
            assert resposta["settings"]["mascot_enabled"] is True
    finally:
        runtime.parar()


def test_reinicio_atravessa_ponte_autenticada_uma_unica_vez() -> None:
    reinicios: list[str] = []
    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=list,
        estado_getter=dict,
        reiniciar_aplicacao=lambda: reinicios.append("solicitado") or True,
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            _enviar(cliente, type="hello", token=runtime.token)
            _linha(cliente)
            _enviar(cliente, type="restart_request", id="r1")
            resposta = _linha(cliente)
            assert resposta["type"] == "restart_result"
            assert resposta["accepted"] is True
            assert resposta["id"] == "r1"
            assert reinicios == ["solicitado"]
    finally:
        runtime.parar()

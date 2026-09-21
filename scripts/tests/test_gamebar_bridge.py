import json
import socket
import time

from mente_laylay.integracao.gamebar_bridge import GameBarBridgeRuntime


def _porta_livre():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    porta = sock.getsockname()[1]
    sock.close()
    return porta


def test_estado_combina_avatar_e_barra():
    runtime = GameBarBridgeRuntime(
        estado_getter=lambda: {"emocao": "alegre", "falando": True},
        porta=_porta_livre(),
    )
    runtime.publicar_barra(True, "oi lay")

    assert runtime.estado_atual() == {
        "type": "state",
        "version": 2,
        "emotion": "feliz",
        "level": 1,
        "speaking": True,
        "activity": "speaking",
        "intensity": 0.333,
        "reaction_id": "",
        "command_bar": {"visible": True, "text": "oi lay"},
    }


def test_widget_avisa_quando_esta_conectado_e_recebe_estado():
    porta = _porta_livre()
    runtime = GameBarBridgeRuntime(
        estado_getter=lambda: {"emotion": "calma", "speaking": False},
        porta=porta,
        intervalo=0.02,
        heartbeat=0.1,
    )
    assert runtime.iniciar()
    cliente = socket.create_connection(("127.0.0.1", porta), timeout=1)
    cliente.sendall(b'{"type":"ready","version":1,"pinned":true}\n')
    cliente.settimeout(1)
    linha = cliente.makefile("rb").readline()
    mensagem = json.loads(linha.decode("utf-8"))
    limite = time.monotonic() + 1
    while not runtime.conectado() and time.monotonic() < limite:
        time.sleep(0.01)
    try:
        assert mensagem["emotion"] == "calma"
        assert mensagem["command_bar"]["visible"] is False
        assert runtime.conectado()
    finally:
        cliente.close()
        runtime.parar()


def test_widget_nao_substitui_barra_tk_antes_de_ser_fixado():
    porta = _porta_livre()
    runtime = GameBarBridgeRuntime(estado_getter=dict, porta=porta, intervalo=0.02)
    assert runtime.iniciar()
    cliente = socket.create_connection(("127.0.0.1", porta), timeout=1)
    cliente.sendall(b'{"type":"ready","version":1,"pinned":false}\n')
    time.sleep(0.05)
    try:
        assert runtime.conectado() is False
    finally:
        cliente.close()
        runtime.parar()


def test_desativacao_por_variavel_nao_abre_porta():
    runtime = GameBarBridgeRuntime(
        estado_getter=dict,
        porta=_porta_livre(),
        env_getter=lambda _nome, _padrao: "0",
    )
    assert runtime.iniciar() is False


def test_falha_ao_abrir_ponte_chega_ao_diagnostico():
    porta = _porta_livre()
    ocupante = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ocupante.bind(("127.0.0.1", porta))
    ocupante.listen(1)
    falhas = []
    runtime = GameBarBridgeRuntime(
        estado_getter=dict,
        porta=porta,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        log=lambda *_: None,
    )
    try:
        assert runtime.iniciar() is False
    finally:
        ocupante.close()

    assert falhas[0][0] == ("gamebar", "abertura_ponte")
    assert isinstance(falhas[0][1]["erro"], OSError)

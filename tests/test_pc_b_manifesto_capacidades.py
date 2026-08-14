from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from cliente import cliente_laylay as cliente
from mente_laylay.integracao import chrome_ws_server
from mente_laylay.integracao import pc_b_integracao
from mente_laylay.integracao.pc_b_integracao import PCBRuntime


def _manifesto(*, estado: str = "ready") -> dict:
    return {
        "protocolVersion": 2,
        "client": {
            "name": "Laylay Remote Client",
            "version": "2.4.0",
            "platform": "windows",
        },
        "capabilities": ["open_app", "set_volume"],
        "health": {
            "state": estado,
            "uptimeSeconds": 12.5,
        },
    }


def test_cliente_anuncia_catalogo_real_versao_e_saude_sem_segredos() -> None:
    executor = cliente.ExecutorRemotoPC()

    manifesto = cliente.manifesto_cliente_remoto(
        executor, agora=150.0, iniciado_em=100.0,
    )

    assert manifesto["protocolVersion"] == 2
    assert manifesto["client"] == {
        "name": "Laylay Remote Client",
        "version": "2.4.0",
        "platform": "windows",
    }
    assert manifesto["capabilities"] == sorted(executor.acoes_suportadas)
    assert manifesto["health"] == {
        "state": "ready",
        "executor": "ready",
        "checkedAt": 150.0,
        "uptimeSeconds": 50.0,
    }
    assert manifesto["security"] == {
        "mode": "restricted",
        "shellEnabled": False,
        "inputAutomationEnabled": False,
        "allowedRoots": 1,
    }
    serializado = json.dumps(manifesto).casefold()
    assert "token" not in serializado
    assert "c:\\users" not in serializado


def test_ponte_sanitiza_manifesto_e_remove_identidade_ou_segredo() -> None:
    bruto = _manifesto()
    bruto["token"] = "segredo"
    bruto["client"]["name"] = "sk-or-v1-segredo"
    bruto["client"]["platform"] = r"C:\Users\Pedro"
    bruto["capabilities"] += ["OPEN_APP", "ghp_segredo", "../../arquivo"]
    bruto["health"]["error"] = "Bearer segredo"

    limpo = chrome_ws_server.sanitizar_manifesto_pc_b(bruto, agora=200.0)

    assert limpo["client_name"] == ""
    assert limpo["platform"] == ""
    assert limpo["capabilities"] == ("open_app", "set_volume")
    assert limpo["health"] == "ready"
    assert limpo["last_seen"] == 200.0
    serializado = json.dumps(limpo).casefold()
    for trecho in ("segredo", "token", "pedro", "bearer", "arquivo"):
        assert trecho not in serializado


def test_transporte_seleciona_somente_cliente_fresco_saudavel_e_compativel(
    monkeypatch,
) -> None:
    agora = {"valor": 100.0}
    monkeypatch.setattr(chrome_ws_server.time, "time", lambda: agora["valor"])
    runtime = chrome_ws_server.WebSocketTransportRuntime()
    pronto, indisponivel = object(), object()
    runtime.registrar_cliente_pc_b(pronto, _manifesto())
    runtime.registrar_cliente_pc_b(
        indisponivel, _manifesto(estado="unavailable"),
    )

    assert runtime.clientes_pc_b_compativeis("open_app") == {pronto}
    assert runtime.clientes_pc_b_compativeis("deletar_item") == set()
    assert runtime.diagnostico_pc_b()["clientes_saudaveis"] == 1

    agora["valor"] = 146.0
    assert runtime.clientes_pc_b_compativeis("open_app") == set()
    assert runtime.diagnostico_pc_b()["disponivel"] is False


def test_cerebro_recusa_envio_que_cliente_nao_anunciou() -> None:
    cliente_ws = object()
    logs: list[str] = []
    runtime = PCBRuntime(
        clientes_getter=lambda: {cliente_ws},
        loop_getter=lambda: object(),
        clientes_compativeis_getter=lambda _acao: set(),
        estado_clientes_getter=lambda: [{
            "fresh": True,
            "health": "ready",
            "capabilities": ("open_app",),
        }],
        log=logs.append,
    )

    assert runtime.enviar({"action": "deletar_item"}, timeout_s=0.01) is False
    assert "nenhum cliente saudável" in logs[-1].casefold()
    assert runtime.diagnostico()["capacidades"] == ["open_app"]


def test_cerebro_envia_somente_para_cliente_compativel_e_aguarda_final(
    monkeypatch,
) -> None:
    class _Cliente:
        async def send(self, _texto):
            return None

    compativel, sem_suporte = _Cliente(), _Cliente()
    chamadas = []
    runtime = PCBRuntime(
        clientes_getter=lambda: {compativel, sem_suporte},
        loop_getter=lambda: object(),
        clientes_compativeis_getter=lambda acao: (
            {compativel} if acao == "open_app" else set()
        ),
        log=lambda _texto: None,
    )
    monkeypatch.setattr(
        pc_b_integracao.uuid,
        "uuid4",
        lambda: SimpleNamespace(hex="pedido-fixo"),
    )

    def executar_coroutine(coroutine, _loop):
        chamadas.append(coroutine)
        coroutine.close()
        runtime.registrar_status({
            "type": "pc_b_status",
            "requestId": "pedido-fixo",
            "status": "success",
            "final": True,
        })
        return SimpleNamespace(result=lambda timeout: None)

    monkeypatch.setattr(
        pc_b_integracao.asyncio,
        "run_coroutine_threadsafe",
        executar_coroutine,
    )

    assert runtime.enviar({"action": "open_app", "app": "Opera"}) is True
    assert len(chamadas) == 1


class _WebSocketSequencial:
    def __init__(self, primeira: dict, mensagens: list[dict]) -> None:
        self._primeira = json.dumps(primeira)
        self._mensagens = iter(json.dumps(item) for item in mensagens)
        self.remote_address = ("192.168.1.20", 50000)
        self.fechado = False

    async def recv(self) -> str:
        return self._primeira

    async def close(self) -> None:
        self.fechado = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._mensagens)
        except StopIteration as erro:
            raise StopAsyncIteration from erro


def test_handshake_registra_manifesto_e_heartbeat_nao_vira_comando() -> None:
    primeira = {
        "type": "pc_b_client", "token": "token-local-seguro-123", **_manifesto(),
    }
    heartbeat = {"type": "pc_b_heartbeat", **_manifesto()}
    websocket = _WebSocketSequencial(primeira, [heartbeat])
    registrados, atualizados, comandos = [], [], []
    conectados = set()
    contexto = {
        "token_pc_b": "token-local-seguro-123",
        "connected_extensions": set(),
        "connected_pc_b_clients": conectados,
        "registrar_cliente_pc_b": (
            lambda ws, dados: (conectados.add(ws), registrados.append(dados))
        ),
        "atualizar_cliente_pc_b": (
            lambda _ws, dados: atualizados.append(dados)
        ),
        "remover_cliente_pc_b": conectados.discard,
        "_processar_mensagem_pc_b": comandos.append,
    }

    asyncio.run(chrome_ws_server.ws_handler_modular(websocket, contexto))

    assert registrados == [primeira]
    assert atualizados == [heartbeat]
    assert comandos == []
    assert websocket.fechado is False


def test_handshake_rejeita_token_fraco_mesmo_quando_igual() -> None:
    websocket = _WebSocketSequencial({
        "type": "pc_b_client", "token": "curto", **_manifesto(),
    }, [])
    conectados = set()

    asyncio.run(chrome_ws_server.ws_handler_modular(websocket, {
        "token_pc_b": "curto",
        "connected_extensions": set(),
        "connected_pc_b_clients": conectados,
    }))

    assert websocket.fechado is True
    assert conectados == set()

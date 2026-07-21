"""Servidor WebSocket Chrome/PC B da Laylay."""

from __future__ import annotations

import asyncio
import inspect
import json
import ipaddress
import threading
from typing import Any, Callable


class WebSocketTransportRuntime:
    """Fonte única do estado vivo de transporte Chrome e PC B."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self.extensions: set[Any] = set()
        self.clientes_pc_b: set[Any] = set()

    def definir_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        with self._lock:
            self._loop = loop

    def obter_loop(self) -> asyncio.AbstractEventLoop | None:
        with self._lock:
            return self._loop

    def obter_extensoes(self) -> set[Any]:
        with self._lock:
            return set(self.extensions)

    def adicionar_extensao(self, websocket: Any) -> None:
        with self._lock:
            self.extensions.add(websocket)

    def remover_extensao(self, websocket: Any) -> None:
        with self._lock:
            self.extensions.discard(websocket)

    def adicionar_cliente_pc_b(self, websocket: Any) -> None:
        with self._lock:
            self.clientes_pc_b.add(websocket)

    def remover_cliente_pc_b(self, websocket: Any) -> None:
        with self._lock:
            self.clientes_pc_b.discard(websocket)

    def contexto_conexoes(self) -> dict[str, Any]:
        return {
            "connected_extensions": self.extensions,
            "connected_pc_b_clients": self.clientes_pc_b,
            "adicionar_extensao": self.adicionar_extensao,
            "remover_extensao": self.remover_extensao,
            "adicionar_cliente_pc_b": self.adicionar_cliente_pc_b,
            "remover_cliente_pc_b": self.remover_cliente_pc_b,
        }


def criar_websocket_transport_runtime() -> WebSocketTransportRuntime:
    return WebSocketTransportRuntime()


async def fechar_extensoes_anteriores(
    conexao_atual: Any,
    *,
    extensoes: Any,
    clientes_pc_b: Any,
) -> None:
    """Mantém uma extensão Chrome ativa sem encerrar clientes remotos PC B."""
    for antiga in list(extensoes or []):
        if antiga is conexao_atual or antiga in (clientes_pc_b or set()):
            continue
        try:
            await antiga.close()
        except Exception:
            pass
        try:
            extensoes.discard(antiga)
        except Exception:
            pass


async def start_ws_server(handler: Callable[..., Any], *, host: str = "0.0.0.0", port: int = 8080) -> None:
    import websockets

    async with websockets.serve(handler, host, port):
        print(f"🚀 WebSocket Server Chrome rodando em http://localhost:{port}")
        await asyncio.Future()


def run_ws_server_in_thread(
    handler: Callable[..., Any],
    *,
    set_loop: Callable[[asyncio.AbstractEventLoop], Any] | None = None,
    host: str = "0.0.0.0",
    port: int = 8080,
) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if callable(set_loop):
        set_loop(loop)
    print("🚀 WebSocket Server Chrome iniciado (thread-safe) — ws_loop definido")
    loop.run_until_complete(start_ws_server(handler, host=host, port=port))


async def ws_handler_modular(websocket: Any, ctx: dict[str, Any]) -> None:
    import websockets

    connected_pc_b_clients = ctx.get("connected_pc_b_clients")
    connected_extensions = ctx.get("connected_extensions")
    close_other_extensions = ctx.get("_ws_close_other_extensions")
    dispatch_data = ctx.get("_ws_dispatch_data")
    processar_pc_b = ctx.get("_processar_mensagem_pc_b")
    processar_page_data = ctx.get("_processar_page_data")
    aplicar_page_updates = ctx.get("_aplicar_page_updates")
    adicionar_extensao = ctx.get("adicionar_extensao")
    remover_extensao = ctx.get("remover_extensao")
    adicionar_cliente_pc_b = ctx.get("adicionar_cliente_pc_b")
    remover_cliente_pc_b = ctx.get("remover_cliente_pc_b")

    is_pc_b = False
    try:
        first_msg_raw = await asyncio.wait_for(websocket.recv(), timeout=3.0)
        first_msg = json.loads(first_msg_raw) if first_msg_raw else {}
    except Exception:
        first_msg = {}

    tipo_cliente = str(first_msg.get("type") or "").strip()
    if tipo_cliente == "pc_b_client":
        token_recebido = first_msg.get("token")
        token_secreto = str(ctx.get("token_pc_b") or "")
        if not token_secreto or token_recebido != token_secreto:
            print(f"🚫 [PC B] Conexão REJEITADA: Token inválido! ({websocket.remote_address})")
            await websocket.close()
            return

        is_pc_b = True
        if callable(adicionar_cliente_pc_b):
            adicionar_cliente_pc_b(websocket)
        elif hasattr(connected_pc_b_clients, "add"):
            connected_pc_b_clients.add(websocket)
        if connected_pc_b_clients is not None:
            print(f"[PC B] Cliente remoto conectado e AUTENTICADO! Total PC B: {len(connected_pc_b_clients)}")
    elif tipo_cliente == "EXTENSION_HELLO" and _conexao_local(websocket):
        if callable(close_other_extensions):
            resultado_close = close_other_extensions(websocket)
            if inspect.isawaitable(resultado_close):
                await resultado_close
        if callable(adicionar_extensao):
            adicionar_extensao(websocket)
        elif hasattr(connected_extensions, "add"):
            connected_extensions.add(websocket)
        if connected_extensions is not None:
            print(f"[Chrome] Extensao conectada! Total: {len(connected_extensions)}")
        if isinstance(first_msg, dict) and callable(dispatch_data):
            dispatch_data(first_msg)
    else:
        print(f"🚫 [WebSocket] Cliente não autenticado rejeitado: {websocket.remote_address}")
        await websocket.close()
        return

    try:
        async for message in websocket:
            if not (isinstance(message, str) and message.strip()):
                continue
            try:
                data = json.loads(message)

                if is_pc_b:
                    if callable(processar_pc_b):
                        processar_pc_b(data)
                    continue

                if isinstance(data, dict) and data.get("type") == "PAGE_DATA":
                    page_updates = processar_page_data(data) if callable(processar_page_data) else {}
                    if callable(aplicar_page_updates):
                        aplicar_page_updates(page_updates)

                if isinstance(data, dict) and callable(dispatch_data):
                    dispatch_data(data)

            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"Erro ao processar mensagem WS: {e}")
    except websockets.exceptions.ConnectionClosedOK:
        pass
    except websockets.exceptions.ConnectionClosedError:
        pass
    except Exception as e:
        print(f"Erro inesperado na conexao WebSocket: {e}")
    finally:
        try:
            if callable(remover_extensao):
                remover_extensao(websocket)
            else:
                connected_extensions.discard(websocket)
        except Exception:
            pass
        try:
            if callable(remover_cliente_pc_b):
                remover_cliente_pc_b(websocket)
            else:
                connected_pc_b_clients.discard(websocket)
        except Exception:
            pass
        if is_pc_b and connected_pc_b_clients is not None:
            print(f"[PC B] Cliente desconectado. Restantes: {len(connected_pc_b_clients)}")


class ChromeWsRuntime:
    """Mantém o ciclo WebSocket ligado ao estado vivo fornecido pelo orquestrador."""

    def __init__(self, *, contexto_getter: Callable[[], dict[str, Any]]) -> None:
        self.contexto_getter = contexto_getter

    async def handler(self, websocket: Any) -> None:
        contexto = self.contexto_getter() or {}
        await ws_handler_modular(websocket, contexto if isinstance(contexto, dict) else {})


def criar_chrome_ws_runtime(**kwargs: Any) -> ChromeWsRuntime:
    return ChromeWsRuntime(**kwargs)


def _conexao_local(websocket: Any) -> bool:
    """A extensão Chrome só pode se apresentar a partir deste computador."""
    remoto = getattr(websocket, "remote_address", None)
    host = remoto[0] if isinstance(remoto, (tuple, list)) and remoto else remoto
    try:
        endereco = ipaddress.ip_address(str(host).split("%", 1)[0])
        if endereco.is_loopback:
            return True
        mapeado = getattr(endereco, "ipv4_mapped", None)
        return bool(mapeado and mapeado.is_loopback)
    except ValueError:
        return str(host or "").casefold() == "localhost"

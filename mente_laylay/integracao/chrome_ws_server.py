"""Servidor WebSocket Chrome/PC B da Laylay."""

from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any, Callable


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

    is_pc_b = False
    try:
        first_msg_raw = await asyncio.wait_for(websocket.recv(), timeout=3.0)
        first_msg = json.loads(first_msg_raw) if first_msg_raw else {}
    except Exception:
        first_msg = {}

    if first_msg.get("type") == "pc_b_client":
        token_recebido = first_msg.get("token")
        token_secreto = str(ctx.get("token_pc_b") or "")
        if token_recebido != token_secreto:
            print(f"🚫 [PC B] Conexão REJEITADA: Token inválido! ({websocket.remote_address})")
            await websocket.close()
            return

        is_pc_b = True
        if hasattr(connected_pc_b_clients, "add"):
            connected_pc_b_clients.add(websocket)
            print(f"[PC B] Cliente remoto conectado e AUTENTICADO! Total PC B: {len(connected_pc_b_clients)}")
    else:
        if callable(close_other_extensions):
            resultado_close = close_other_extensions(websocket)
            if inspect.isawaitable(resultado_close):
                await resultado_close
        if hasattr(connected_extensions, "add"):
            connected_extensions.add(websocket)
            print(f"[Chrome] Extensao conectada! Total: {len(connected_extensions)}")
        if isinstance(first_msg, dict) and callable(dispatch_data):
            dispatch_data(first_msg)

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
            connected_extensions.discard(websocket)
        except Exception:
            pass
        try:
            connected_pc_b_clients.discard(websocket)
        except Exception:
            pass
        if is_pc_b and connected_pc_b_clients is not None:
            print(f"[PC B] Cliente desconectado. Restantes: {len(connected_pc_b_clients)}")

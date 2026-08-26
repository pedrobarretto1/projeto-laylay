"""Servidor WebSocket Chrome/PC B da Laylay."""

from __future__ import annotations

import asyncio
import hmac
import inspect
import json
import ipaddress
import threading
import time
from typing import Any, Callable


_ESTADOS_SAUDE_PC_B = {"ready", "degraded", "unavailable"}
_IDADE_MAXIMA_PC_B_S = 45.0
_TAMANHO_MAXIMO_PC_B_BYTES = 65_536


def _texto_tecnico_pc_b(valor: Any, limite: int) -> str:
    texto = str(valor or "").strip()
    normalizado = texto.casefold()
    if (
        normalizado.startswith(("sk-", "ghp_", "github_pat_", "eyj"))
        or "bearer " in normalizado
        or "@" in texto
        or ":\\" in texto
        or "/" in texto
    ):
        return ""
    return "".join(
        caractere for caractere in texto
        if caractere.isalnum() or caractere in "._- "
    )[:limite]


def sanitizar_manifesto_pc_b(
    payload: Any, *, agora: float | None = None,
) -> dict[str, Any]:
    """Reduz o anúncio remoto a um contrato técnico sem dados do usuário."""
    bruto = payload if isinstance(payload, dict) else {}
    cliente = bruto.get("client") if isinstance(bruto.get("client"), dict) else {}
    saude = bruto.get("health") if isinstance(bruto.get("health"), dict) else {}
    try:
        protocolo = int(bruto.get("protocolVersion") or 0)
    except (TypeError, ValueError):
        protocolo = 0
    capacidades_brutas = bruto.get("capabilities")
    if not isinstance(capacidades_brutas, (list, tuple, set, frozenset)):
        capacidades_brutas = []
    capacidades = []
    for capacidade in capacidades_brutas:
        nome = _texto_tecnico_pc_b(capacidade, 64).casefold().replace(" ", "_")
        if nome and nome not in capacidades:
            capacidades.append(nome)
        if len(capacidades) >= 64:
            break
    estado = _texto_tecnico_pc_b(saude.get("state"), 24).casefold()
    if estado not in _ESTADOS_SAUDE_PC_B:
        estado = "unavailable"
    try:
        uptime = max(0.0, min(float(saude.get("uptimeSeconds") or 0.0), 31_536_000.0))
    except (TypeError, ValueError):
        uptime = 0.0
    return {
        "protocol_version": max(0, min(protocolo, 99)),
        "client_name": _texto_tecnico_pc_b(cliente.get("name"), 64),
        "client_version": _texto_tecnico_pc_b(cliente.get("version"), 32),
        "platform": _texto_tecnico_pc_b(cliente.get("platform"), 24).casefold(),
        "capabilities": tuple(sorted(capacidades)),
        "health": estado,
        "uptime_seconds": round(uptime, 1),
        "last_seen": float(time.time() if agora is None else agora),
    }


class ErroPortaWebSocketOcupada(OSError):
    """Falha permanente desta execução; reiniciar a thread não libera a porta."""

    reiniciavel = False


def _porta_ja_esta_ocupada(erro: OSError) -> bool:
    return int(getattr(erro, "winerror", 0) or getattr(erro, "errno", 0) or 0) in {
        48, 98, 10048,
    }


class WebSocketTransportRuntime:
    """Fonte única do estado vivo de transporte Chrome e PC B."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self.extensions: set[Any] = set()
        self.clientes_pc_b: set[Any] = set()
        self._manifestos_pc_b: dict[Any, dict[str, Any]] = {}

    def definir_loop(self, loop: asyncio.AbstractEventLoop | None) -> None:
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
        self.registrar_cliente_pc_b(websocket, {})

    def registrar_cliente_pc_b(self, websocket: Any, manifesto: Any) -> None:
        retrato = sanitizar_manifesto_pc_b(manifesto)
        with self._lock:
            self.clientes_pc_b.add(websocket)
            anterior = self._manifestos_pc_b.get(websocket, {})
            retrato["connected_at"] = float(
                anterior.get("connected_at") or retrato["last_seen"]
            )
            self._manifestos_pc_b[websocket] = retrato

    def atualizar_cliente_pc_b(self, websocket: Any, manifesto: Any) -> None:
        atualizacao = sanitizar_manifesto_pc_b(manifesto)
        with self._lock:
            if websocket not in self.clientes_pc_b:
                return
            anterior = dict(self._manifestos_pc_b.get(websocket) or {})
            for chave in (
                "protocol_version", "client_name", "client_version", "platform",
            ):
                if atualizacao.get(chave):
                    anterior[chave] = atualizacao[chave]
            if atualizacao.get("capabilities"):
                anterior["capabilities"] = atualizacao["capabilities"]
            if isinstance(manifesto, dict) and "health" in manifesto:
                anterior["health"] = atualizacao["health"]
                anterior["uptime_seconds"] = atualizacao["uptime_seconds"]
            anterior["last_seen"] = atualizacao["last_seen"]
            anterior.setdefault("connected_at", atualizacao["last_seen"])
            self._manifestos_pc_b[websocket] = anterior

    def remover_cliente_pc_b(self, websocket: Any) -> None:
        with self._lock:
            self.clientes_pc_b.discard(websocket)
            self._manifestos_pc_b.pop(websocket, None)

    def clientes_pc_b_compativeis(self, acao: str) -> set[Any]:
        nome = _texto_tecnico_pc_b(acao, 64).casefold().replace(" ", "_")
        agora = time.time()
        with self._lock:
            return {
                websocket
                for websocket in self.clientes_pc_b
                if (
                    agora - float(
                        self._manifestos_pc_b.get(websocket, {}).get("last_seen") or 0.0
                    ) <= _IDADE_MAXIMA_PC_B_S
                    and self._manifestos_pc_b.get(websocket, {}).get("health")
                    in {"ready", "degraded"}
                    and nome in self._manifestos_pc_b.get(websocket, {}).get(
                        "capabilities", ()
                    )
                )
            }

    def retrato_clientes_pc_b(self) -> list[dict[str, Any]]:
        agora = time.time()
        with self._lock:
            retratos = [dict(
                manifesto,
                fresh=(
                    agora - float(manifesto.get("last_seen") or 0.0)
                    <= _IDADE_MAXIMA_PC_B_S
                ),
            ) for manifesto in self._manifestos_pc_b.values()]
        return sorted(
            retratos,
            key=lambda item: (item.get("client_name", ""), item.get("client_version", "")),
        )

    def diagnostico_pc_b(self) -> dict[str, Any]:
        clientes = self.retrato_clientes_pc_b()
        capacidades = sorted({
            capacidade
            for cliente in clientes if cliente.get("fresh")
            for capacidade in cliente.get("capabilities", ())
        })
        saudaveis = sum(
            1 for cliente in clientes
            if cliente.get("fresh") and cliente.get("health") == "ready"
        )
        return {
            "disponivel": bool(saudaveis),
            "clientes_conectados": len(clientes),
            "clientes_saudaveis": saudaveis,
            "capacidades": capacidades,
            "protocolo_minimo": 2,
            "conteudo_exposto": False,
            "autoriza_execucao": False,
        }

    def contexto_conexoes(self) -> dict[str, Any]:
        return {
            "connected_extensions": self.extensions,
            "connected_pc_b_clients": self.clientes_pc_b,
            "adicionar_extensao": self.adicionar_extensao,
            "remover_extensao": self.remover_extensao,
            "adicionar_cliente_pc_b": self.adicionar_cliente_pc_b,
            "registrar_cliente_pc_b": self.registrar_cliente_pc_b,
            "atualizar_cliente_pc_b": self.atualizar_cliente_pc_b,
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


async def start_ws_server(
    handler: Callable[..., Any], *, host: str = "0.0.0.0", port: int = 8080,
    stop_event: threading.Event | None = None,
) -> None:
    import websockets

    try:
        async with websockets.serve(handler, host, port):
            print(f"🚀 WebSocket Server Chrome rodando em http://localhost:{port}")
            if stop_event is None:
                await asyncio.Future()
            while not stop_event.is_set():
                await asyncio.sleep(0.20)
    except OSError as erro:
        if not _porta_ja_esta_ocupada(erro):
            raise
        print(
            f"⚠️ [WEBSOCKET] A porta {port} já está em uso. "
            "O serviço foi desativado nesta instância sem entrar em loop."
        )
        raise ErroPortaWebSocketOcupada(
            f"porta WebSocket {port} ocupada"
        ) from erro


def run_ws_server_in_thread(
    handler: Callable[..., Any],
    *,
    set_loop: Callable[[asyncio.AbstractEventLoop], Any] | None = None,
    host: str = "0.0.0.0",
    port: int = 8080,
    stop_event: threading.Event | None = None,
) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if callable(set_loop):
        set_loop(loop)
    try:
        loop.run_until_complete(
            start_ws_server(
                handler, host=host, port=port, stop_event=stop_event,
            )
        )
    finally:
        if callable(set_loop):
            set_loop(None)
        loop.close()


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
    registrar_cliente_pc_b = ctx.get("registrar_cliente_pc_b")
    atualizar_cliente_pc_b = ctx.get("atualizar_cliente_pc_b")
    remover_cliente_pc_b = ctx.get("remover_cliente_pc_b")

    is_pc_b = False
    try:
        first_msg_raw = await asyncio.wait_for(websocket.recv(), timeout=3.0)
        if (
            not isinstance(first_msg_raw, str)
            or len(first_msg_raw.encode("utf-8")) > _TAMANHO_MAXIMO_PC_B_BYTES
        ):
            await websocket.close()
            return
        first_msg = json.loads(first_msg_raw) if first_msg_raw else {}
    except Exception:
        first_msg = {}

    tipo_cliente = str(first_msg.get("type") or "").strip()
    if tipo_cliente == "pc_b_client":
        token_recebido = first_msg.get("token")
        token_secreto = str(ctx.get("token_pc_b") or "")
        token_recebido = str(token_recebido or "")
        if (
            len(token_secreto) < 16
            or len(token_recebido) < 16
            or not hmac.compare_digest(token_recebido, token_secreto)
        ):
            print(f"🚫 [PC B] Conexão REJEITADA: Token inválido! ({websocket.remote_address})")
            await websocket.close()
            return

        is_pc_b = True
        if callable(registrar_cliente_pc_b):
            registrar_cliente_pc_b(websocket, first_msg)
        elif callable(adicionar_cliente_pc_b):
            adicionar_cliente_pc_b(websocket)
        elif hasattr(connected_pc_b_clients, "add"):
            connected_pc_b_clients.add(websocket)
        if connected_pc_b_clients is not None:
            versao = sanitizar_manifesto_pc_b(first_msg).get("client_version") or "legado"
            print(
                "[PC B] Cliente remoto conectado e AUTENTICADO! "
                f"versão={versao} Total PC B: {len(connected_pc_b_clients)}"
            )
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
            if is_pc_b and len(message.encode("utf-8")) > _TAMANHO_MAXIMO_PC_B_BYTES:
                print("🚫 [PC B] Mensagem excedeu o limite de segurança.")
                await websocket.close()
                break
            try:
                data = json.loads(message)

                if is_pc_b:
                    if callable(atualizar_cliente_pc_b):
                        atualizar_cliente_pc_b(websocket, data)
                    if isinstance(data, dict) and data.get("type") == "pc_b_heartbeat":
                        continue
                    if callable(processar_pc_b):
                        processar_pc_b(data)
                    continue

                if isinstance(data, dict) and data.get("type") == "PAGE_DATA":
                    page_updates = processar_page_data(data) if callable(processar_page_data) else {}
                    if callable(aplicar_page_updates):
                        aplicar_page_updates(page_updates)

                evento_player = (
                    isinstance(data, dict)
                    and data.get("type") == "PLAYER_EVENT"
                    and str(data.get("eventId") or "").strip()
                )
                if evento_player:
                    await websocket.send(json.dumps({
                        "type": "PLAYER_EVENT_ACK",
                        "eventId": str(data.get("eventId")),
                    }))
                    # Avançar uma playlist envia outro comando e aguarda o
                    # COMMAND_RESULT nesta mesma conexão. Executar isso nesta
                    # coroutine bloquearia a própria leitura da confirmação.
                    if callable(dispatch_data):
                        threading.Thread(
                            target=dispatch_data,
                            args=(data,),
                            name="laylay-playlist-auto-next",
                            daemon=True,
                        ).start()
                    continue

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

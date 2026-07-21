"""Transporte WebSocket da extensao Chrome."""

from __future__ import annotations

import asyncio
import json
import threading
import time
import uuid
from typing import Any, Callable, Dict


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


class ChromeSolicitacoesRuntime:
    """Centraliza pedidos e respostas correlacionadas da extensao Chrome.

    O runtime nao decide intencoes nem produz fala. Ele apenas mantem o estado
    transitorio do transporte para que todas as habilidades consultem a mesma
    conexao e as mesmas filas de resposta.
    """

    def __init__(
        self,
        *,
        obter_loop: Callable[[], Any],
        obter_extensoes: Callable[[], Any],
        transmitir: Callable[[str], Any],
    ) -> None:
        self._obter_loop = obter_loop
        self._obter_extensoes = obter_extensoes
        self._transmitir = transmitir
        self.pendencias_abas: Dict[str, Any] = {}
        self.pendencias_aba_ativa: Dict[str, Any] = {}
        self.pendencias_checagem_abas: Dict[str, Any] = {}
        self.pendencias_conteudo_pagina: Dict[str, Any] = {}
        self.pendencias_comandos: Dict[str, Any] = {}
        self.pendencias_lock = threading.RLock()
        self.ultimo_resultado_comando: Dict[str, Any] = {}
        self._contador_lock = threading.Lock()
        self._contador = 0

    def _novo_request_id(self) -> str:
        # O contador evita colisao quando dois pedidos nascem no mesmo milissegundo.
        with self._contador_lock:
            self._contador += 1
            contador = self._contador
        return f"{int(time.time() * 1000)}-{contador}"

    def conectado(self) -> bool:
        try:
            return self._obter_loop() is not None and bool(self._obter_extensoes())
        except Exception:
            return False

    def _enviar_no_loop(self, mensagem: Dict[str, Any]) -> bool:
        loop = self._obter_loop()
        if loop is None:
            return False
        try:
            asyncio.run_coroutine_threadsafe(
                self._transmitir(json.dumps(mensagem)),
                loop,
            )
            return True
        except Exception:
            return False

    def enviar_confirmado(self, mensagem: Dict[str, Any], timeout_s: float = 1.5) -> bool:
        """Confirma que ao menos uma extensao recebeu a mensagem no socket."""
        loop = self._obter_loop()
        if loop is None:
            return False
        try:
            futuro = asyncio.run_coroutine_threadsafe(
                self._transmitir(json.dumps(mensagem)),
                loop,
            )
            enviados = futuro.result(timeout=max(0.1, float(timeout_s)))
            return bool(enviados)
        except Exception:
            return False

    def executar_confirmado(self, mensagem: Dict[str, Any], timeout_s: float = 3.0) -> bool:
        """Aguarda a extensão devolver o resultado real de um comando de página."""
        if not self.conectado():
            return False
        request_id = str(mensagem.get("requestId") or self._novo_request_id())
        evento = threading.Event()
        entrada = {"event": evento, "result": None}
        with self.pendencias_lock:
            self.pendencias_comandos[request_id] = entrada
        payload = dict(mensagem)
        payload["requestId"] = request_id
        if not self._enviar_no_loop(payload):
            with self.pendencias_lock:
                self.pendencias_comandos.pop(request_id, None)
            return False
        respondeu = evento.wait(max(0.1, float(timeout_s)))
        with self.pendencias_lock:
            final = self.pendencias_comandos.pop(request_id, None) or entrada
        resultado = final.get("result")
        self.ultimo_resultado_comando = dict(resultado) if isinstance(resultado, dict) else {}
        return bool(respondeu and isinstance(resultado, dict) and resultado.get("ok") is True)

    def solicitar_lista_abas(self, timeout_s: float = 6.0) -> list[Any]:
        if not self.conectado():
            return []
        request_id = self._novo_request_id()
        evento = threading.Event()
        with self.pendencias_lock:
            self.pendencias_abas[request_id] = {"event": evento, "tabs": []}
        if not self._enviar_no_loop({"action": "get_tabs_list", "requestId": request_id}):
            with self.pendencias_lock:
                self.pendencias_abas.pop(request_id, None)
            return []
        respondeu = evento.wait(max(0.0, float(timeout_s)))
        with self.pendencias_lock:
            entrada = self.pendencias_abas.pop(request_id, None) or {}
        if not respondeu:
            return []
        abas = entrada.get("tabs")
        return abas if isinstance(abas, list) else []

    def solicitar_tab_reciclagem(self, target_domain: str, timeout_s: float = 3.0) -> int | None:
        if not self.conectado():
            return None
        dominio = str(target_domain or "").strip().lower().split(":")[0]
        if dominio.startswith("www."):
            dominio = dominio[4:]
        if not dominio:
            return None

        request_id = self._novo_request_id()
        evento = threading.Event()
        with self.pendencias_lock:
            self.pendencias_checagem_abas[request_id] = {"event": evento, "tabId": None}
        mensagem = {"action": "check_tabs", "requestId": request_id, "target_domain": dominio}
        if not self._enviar_no_loop(mensagem):
            with self.pendencias_lock:
                self.pendencias_checagem_abas.pop(request_id, None)
            return None
        respondeu = evento.wait(max(0.0, float(timeout_s)))
        with self.pendencias_lock:
            entrada = self.pendencias_checagem_abas.pop(request_id, None) or {}
        if not respondeu:
            return None
        tab_id = entrada.get("tabId")
        return int(tab_id) if isinstance(tab_id, int) else None

    def solicitar_aba_ativa(self, timeout_s: float = 4.0) -> Dict[str, str]:
        vazio = {"url": "", "title": "", "canal": "", "tabId": None}
        if not self.conectado():
            return vazio
        loop = self._obter_loop()
        if loop is None:
            return vazio

        async def _solicitar() -> Dict[str, str]:
            request_id = self._novo_request_id()
            futuro = asyncio.get_running_loop().create_future()
            with self.pendencias_lock:
                self.pendencias_aba_ativa[request_id] = futuro
            try:
                await self._transmitir(json.dumps({"action": "get_youtube_data", "requestId": request_id}))
                resposta = await asyncio.wait_for(futuro, timeout=max(0.0, float(timeout_s)))
                if not isinstance(resposta, dict):
                    return vazio
                return {
                    "url": str(resposta.get("url") or ""),
                    "title": str(resposta.get("title") or ""),
                    "canal": str(resposta.get("canal") or ""),
                    "tabId": resposta.get("tabId"),
                }
            except Exception:
                return vazio
            finally:
                with self.pendencias_lock:
                    self.pendencias_aba_ativa.pop(request_id, None)

        try:
            futuro = asyncio.run_coroutine_threadsafe(_solicitar(), loop)
            return futuro.result(timeout=max(0.0, float(timeout_s)) + 0.5)
        except Exception:
            return vazio

    async def solicitar_conteudo_pagina(self, timeout_s: float = 15.0) -> Dict[str, Any]:
        if not self._obter_extensoes():
            print("❌ Nenhuma extensão conectada para solicitar conteúdo da página.")
            return {"success": False, "error": "Nenhuma extensão conectada"}
        if self._obter_loop() is None:
            print("❌ ws_loop não inicializado.")
            return {"success": False, "error": "ws_loop não inicializado"}

        request_id = str(uuid.uuid4())
        futuro = asyncio.get_running_loop().create_future()
        with self.pendencias_lock:
            self.pendencias_conteudo_pagina[request_id] = futuro
        try:
            await self._transmitir(json.dumps({"action": "get_page_content", "requestId": request_id}))
            print(f"[WS] Solicitando conteúdo da página com requestId: {request_id}")
            resposta = await asyncio.wait_for(futuro, timeout=max(0.0, float(timeout_s)))
            print(f"[WS] Resposta de conteúdo da página recebida para requestId: {request_id}")
            return resposta
        except asyncio.TimeoutError:
            print(f"❌ Timeout ao aguardar conteúdo da página para requestId: {request_id}")
            return {"success": False, "error": "Timeout ao obter conteúdo da página"}
        except Exception as exc:
            print(f"❌ Erro ao solicitar conteúdo da página: {exc}")
            return {"success": False, "error": str(exc)}
        finally:
            with self.pendencias_lock:
                self.pendencias_conteudo_pagina.pop(request_id, None)


async def broadcast_command(ctx: Dict[str, Any], msg: str) -> int:
    """Envia mensagem para todas as extensoes Chrome conectadas."""
    connected_extensions = _get(ctx, "connected_extensions", set())
    enviados = 0
    for client in list(connected_extensions):
        try:
            await client.send(msg)
            enviados += 1
        except Exception as e:
            print(f"❌ ERRO AO ENVIAR PARA CLIENTE: {type(e).__name__} → {e}")
            try:
                connected_extensions.discard(client)
            except Exception:
                pass
    return enviados

"""Transporte JSONL do cliente, sem dependência de Qt.

Todos os acessos de leitura e escrita ao socket acontecem na thread que roda
``executar``. A UI apenas coloca comandos numa fila thread-safe.
"""

from __future__ import annotations

import json
from queue import Empty, Queue
import socket
import threading
import time
import uuid
from typing import Any, Callable, Mapping


class TransporteDesktopCliente:
    def __init__(
        self,
        host: str,
        port: int,
        token: str,
        *,
        ao_mensagem: Callable[[dict[str, Any]], Any],
        ao_conexao: Callable[[bool], Any],
        ao_falha: Callable[[str], Any],
        intervalo_heartbeat_s: float = 8.0,
    ) -> None:
        self.host, self.port, self.token = host, int(port), token
        self.ao_mensagem = ao_mensagem
        self.ao_conexao = ao_conexao
        self.ao_falha = ao_falha
        self.intervalo_heartbeat_s = max(0.2, float(intervalo_heartbeat_s))
        self._fila: Queue[dict[str, Any]] = Queue(maxsize=256)
        self._stop = threading.Event()
        self._conectado = threading.Event()
        self._socket: socket.socket | None = None
        self.thread_socket_id: int | None = None

    def enfileirar(self, mensagem: Mapping[str, Any]) -> bool:
        """Pode ser chamada por qualquer thread; nunca toca no socket."""
        if not self._conectado.is_set():
            self.ao_mensagem({
                "type": "error", "code": "send_failed",
                "id": str(mensagem.get("id") or ""),
                "message": "A ponte está reconectando. A mensagem não foi enviada.",
            })
            return False
        try:
            self._fila.put_nowait(dict(mensagem))
            return True
        except Exception:
            return False

    def parar(self) -> None:
        self._stop.set()
        sock = self._socket
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def _enviar_agora(self, mensagem: Mapping[str, Any]) -> bool:
        """Uso exclusivo da thread proprietária de ``executar``."""
        if threading.get_ident() != self.thread_socket_id:
            raise RuntimeError("socket do desktop acessado fora da thread proprietária")
        sock = self._socket
        if sock is None:
            return False
        try:
            sock.sendall(
                (json.dumps(dict(mensagem), ensure_ascii=False) + "\n").encode("utf-8")
            )
            return True
        except OSError:
            self.ao_mensagem({
                "type": "error", "code": "send_failed",
                "id": str(mensagem.get("id") or ""),
                "message": "A mensagem não chegou à ponte. Você pode tentar novamente.",
            })
            return False

    def _drenar_fila(self) -> None:
        while True:
            try:
                mensagem = self._fila.get_nowait()
            except Empty:
                return
            if not self._enviar_agora(mensagem):
                # O comando falhou de forma visível. Não volta para a fila e
                # nunca é repetido automaticamente após reconexão.
                return

    def _invalidar_fila(self) -> None:
        """Falha comandos não enviados; nunca os repete após reconexão."""
        while True:
            try:
                mensagem = self._fila.get_nowait()
            except Empty:
                return
            self.ao_mensagem({
                "type": "error", "code": "send_failed",
                "id": str(mensagem.get("id") or ""),
                "message": "A conexão caiu antes do envio. Tente novamente se ainda quiser.",
            })

    def executar(self) -> None:
        self.thread_socket_id = threading.get_ident()
        atraso = 0.7
        while not self._stop.is_set():
            try:
                sock = socket.create_connection((self.host, self.port), timeout=3.0)
                sock.settimeout(0.12)
                self._socket = sock
                self._enviar_agora({"type": "hello", "token": self.token})
                self._conectado.set()
                self.ao_conexao(True)
                atraso = 0.7
                ultimo_heartbeat = time.monotonic()
                buffer = b""
                while not self._stop.is_set():
                    self._drenar_fila()
                    agora = time.monotonic()
                    if agora - ultimo_heartbeat >= self.intervalo_heartbeat_s:
                        self._enviar_agora({"type": "heartbeat", "id": uuid.uuid4().hex})
                        ultimo_heartbeat = agora
                    try:
                        bloco = sock.recv(16_384)
                    except socket.timeout:
                        continue
                    if not bloco:
                        raise ConnectionError("a ponte encerrou a conexão")
                    buffer += bloco
                    if len(buffer) > 65_536:
                        raise ConnectionError("mensagem grande demais")
                    while b"\n" in buffer:
                        linha, buffer = buffer.split(b"\n", 1)
                        if not linha:
                            continue
                        try:
                            mensagem = json.loads(linha.decode("utf-8"))
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            self.ao_falha("A ponte enviou uma mensagem inválida.")
                            continue
                        if isinstance(mensagem, dict):
                            self.ao_mensagem(mensagem)
            except (OSError, ConnectionError) as erro:
                self._conectado.clear()
                self._invalidar_fila()
                self.ao_conexao(False)
                if not self._stop.is_set():
                    self.ao_falha(str(erro))
                    self._stop.wait(atraso)
                    atraso = min(6.0, atraso * 1.6)
            finally:
                self._conectado.clear()
                sock, self._socket = self._socket, None
                if sock:
                    try:
                        sock.close()
                    except OSError:
                        pass

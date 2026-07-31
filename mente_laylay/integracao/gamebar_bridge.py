"""Ponte local entre a mente da Laylay e o widget da Xbox Game Bar.

O widget e apenas uma tela. A captura de teclado, a decisao e a execucao
continuam no processo Python, que publica um retrato visual por JSON line.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
from typing import Any, Callable, Mapping

from mente_laylay.personalidade.avatar_runtime import normalizar_estado_avatar


class GameBarBridgeRuntime:
    """Servidor TCP local, com um unico widget conectado por vez."""

    def __init__(
        self,
        *,
        estado_getter: Callable[[], Mapping[str, Any]],
        log: Callable[[str], Any] = print,
        env_getter: Callable[[str, str], str] = os.getenv,
        host: str = "127.0.0.1",
        porta: int = 18766,
        intervalo: float = 1 / 30,
        heartbeat: float = 1.0,
        timeout_conexao: float = 6.0,
        clock: Callable[[], float] = time.monotonic,
        registrar_falha: Callable[..., Any] | None = None,
    ) -> None:
        self.estado_getter = estado_getter
        self.log = log
        self.env_getter = env_getter
        self.host = str(host)
        self.porta = int(porta)
        self.intervalo = max(0.02, float(intervalo))
        self.heartbeat = max(0.5, float(heartbeat))
        self.timeout_conexao = max(2.0, float(timeout_conexao))
        self.clock = clock
        self.registrar_falha = registrar_falha
        self._servidor: socket.socket | None = None
        self._cliente: socket.socket | None = None
        self._cliente_lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._parar = threading.Event()
        self._alterado = threading.Event()
        self._ultimo_sinal_widget = float("-inf")
        self._widget_fixado = False
        self._barra = {"visible": False, "text": ""}
        self._buffer_recebido = b""

    def _relatar(self, codigo: str, erro: BaseException) -> None:
        if callable(self.registrar_falha):
            self.registrar_falha("gamebar", codigo, erro=erro)

    def ativo(self) -> bool:
        valor = str(self.env_getter("LAYLAY_GAMEBAR_ATIVO", "1") or "").casefold()
        return valor not in {"0", "false", "nao", "não", "off", "desligado"}

    def iniciar(self) -> bool:
        if not self.ativo():
            return False
        if self._thread is not None and self._thread.is_alive():
            return True
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            servidor.bind((self.host, self.porta))
            servidor.listen(1)
            servidor.settimeout(0.15)
        except OSError as erro:
            servidor.close()
            self.log(f"⚠️ [GAME BAR] ponte local indisponível: {erro}")
            self._relatar("abertura_ponte", erro)
            return False
        self._servidor = servidor
        self._parar.clear()
        self._thread = threading.Thread(
            target=self._executar,
            name="Laylay-GameBar-Bridge",
            daemon=True,
        )
        self._thread.start()
        self.log(f"🎮 [GAME BAR] ponte local aguardando o widget em {self.host}:{self.porta}")
        return True

    def parar(self, timeout_s: float = 0.7) -> None:
        self._parar.set()
        self._fechar_cliente()
        servidor, self._servidor = self._servidor, None
        if servidor is not None:
            try:
                servidor.close()
            except OSError:
                pass
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=max(0.0, float(timeout_s)))
        self._thread = None

    def conectado(self) -> bool:
        with self._cliente_lock:
            tem_cliente = self._cliente is not None
            ultimo = self._ultimo_sinal_widget
        with self._cliente_lock:
            fixado = self._widget_fixado
        return bool(tem_cliente and fixado and self.clock() - ultimo <= self.timeout_conexao)

    def publicar_barra(self, visible: bool, text: str = "") -> None:
        novo = {
            "visible": bool(visible),
            "text": str(text or "")[:500],
        }
        with self._cliente_lock:
            if novo == self._barra:
                return
            self._barra = novo
        self._alterado.set()

    def estado_atual(self) -> dict[str, Any]:
        avatar = normalizar_estado_avatar(self.estado_getter())
        with self._cliente_lock:
            barra = dict(self._barra)
        return {
            "type": "state",
            "version": 2,
            "emotion": avatar["emotion"],
            "level": avatar["level"],
            "speaking": avatar["speaking"],
            "activity": avatar["activity"],
            "intensity": avatar["intensity"],
            "reaction_id": avatar["reaction_id"],
            "command_bar": barra,
        }

    def _executar(self) -> None:
        ultimo_estado: dict[str, Any] | None = None
        ultimo_envio = float("-inf")
        while not self._parar.is_set():
            if self._cliente is None:
                self._aceitar_cliente()
                continue
            self._receber_sinais()
            agora = self.clock()
            try:
                estado = self.estado_atual()
            except Exception as erro:
                self.log(f"⚠️ [GAME BAR] estado visual indisponível: {erro}")
                self._relatar("estado_visual", erro)
                self._parar.wait(self.intervalo)
                continue
            if (
                estado != ultimo_estado
                or self._alterado.is_set()
                or agora - ultimo_envio >= self.heartbeat
            ):
                if self._enviar(estado):
                    ultimo_estado = estado
                    ultimo_envio = agora
                    self._alterado.clear()
            self._parar.wait(self.intervalo)

    def _aceitar_cliente(self) -> None:
        servidor = self._servidor
        if servidor is None:
            self._parar.wait(self.intervalo)
            return
        try:
            cliente, endereco = servidor.accept()
        except socket.timeout:
            return
        except OSError:
            return
        if endereco[0] not in {"127.0.0.1", "::1"}:
            cliente.close()
            return
        cliente.setblocking(False)
        with self._cliente_lock:
            self._fechar_cliente_sem_lock()
            self._cliente = cliente
            self._buffer_recebido = b""
            self._ultimo_sinal_widget = self.clock()
            self._widget_fixado = False
        self._alterado.set()
        self.log("🎮 [GAME BAR] widget conectado; avatar e barra sincronizados.")

    def _receber_sinais(self) -> None:
        with self._cliente_lock:
            cliente = self._cliente
        if cliente is None:
            return
        try:
            dados = cliente.recv(4096)
            if not dados:
                self._fechar_cliente()
                return
        except BlockingIOError:
            return
        except OSError:
            self._fechar_cliente()
            return
        self._buffer_recebido = (self._buffer_recebido + dados)[-16384:]
        while b"\n" in self._buffer_recebido:
            linha, self._buffer_recebido = self._buffer_recebido.split(b"\n", 1)
            try:
                mensagem = json.loads(linha.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(mensagem, dict) and mensagem.get("type") in {"ready", "heartbeat"}:
                with self._cliente_lock:
                    self._ultimo_sinal_widget = self.clock()
                    self._widget_fixado = bool(mensagem.get("pinned", False))

    def _enviar(self, mensagem: Mapping[str, Any]) -> bool:
        dados = (json.dumps(dict(mensagem), ensure_ascii=False) + "\n").encode("utf-8")
        with self._cliente_lock:
            cliente = self._cliente
            if cliente is None:
                return False
            try:
                cliente.sendall(dados)
                return True
            except (BlockingIOError, OSError):
                self._fechar_cliente_sem_lock()
                return False

    def _fechar_cliente(self) -> None:
        with self._cliente_lock:
            self._fechar_cliente_sem_lock()

    def _fechar_cliente_sem_lock(self) -> None:
        cliente, self._cliente = self._cliente, None
        self._ultimo_sinal_widget = float("-inf")
        self._widget_fixado = False
        self._buffer_recebido = b""
        if cliente is not None:
            try:
                cliente.close()
            except OSError:
                pass


def criar_gamebar_bridge_runtime(**kwargs: Any) -> GameBarBridgeRuntime:
    return GameBarBridgeRuntime(**kwargs)

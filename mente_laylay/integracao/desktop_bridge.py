"""Ponte local autenticada entre a mente canônica e o Terminal Laylay 2.0.

O protocolo é JSON Lines sobre TCP/loopback. A ponte transporta somente
retratos sanitizados; interpretar ou executar pedidos continua sendo trabalho
da entrada canônica da Laylay.
"""

from __future__ import annotations

from collections import deque
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import threading
import time
from typing import Any, Callable, Mapping, Sequence

from mente_laylay.integracao.configuracao_aplicacao import ErroConfiguracaoAplicacao


TIPOS_CLIENTE = frozenset({
    "hello", "ready", "heartbeat", "input_submit", "mode_set",
    "settings_get", "settings_update", "restart_request",
})
TIPOS_BACKEND = frozenset({
    "snapshot", "input_ack", "assistant_message", "state", "error",
    "mode_state", "settings_state", "settings_result", "restart_result",
})


class ErroProtocoloDesktop(ValueError):
    pass


def _texto_seguro(valor: Any, limite: int = 8_000) -> str:
    texto = str(valor or "").replace("\x00", "").strip()
    return texto[:limite]


def sanitizar_historico(
    mensagens: Sequence[Mapping[str, Any]] | None,
    *,
    limite: int = 80,
) -> list[dict[str, str]]:
    """Reduz a porta tipada de conversa a papéis e textos exibíveis."""
    resultado: list[dict[str, str]] = []
    for item in list(mensagens or ())[-max(1, int(limite)):]:
        if not isinstance(item, Mapping):
            continue
        papel = str(item.get("role") or "").casefold().strip()
        if papel not in {"user", "assistant"}:
            continue
        texto = _texto_seguro(item.get("content"))
        if texto:
            mensagem = {"role": papel, "content": texto}
            # A porta antiga nem sempre possui tempo. Ausência é mais honesta
            # que carimbar todas as mensagens com a hora de abertura da UI.
            instante = item.get("timestamp", item.get("ts", item.get("created_at")))
            if isinstance(instante, (int, float)) and instante > 0:
                mensagem["timestamp"] = str(float(instante))
            elif isinstance(instante, str) and instante.strip():
                mensagem["timestamp"] = instante.strip()[:64]
            resultado.append(mensagem)
    return resultado


def sanitizar_estado(estado: Mapping[str, Any] | None) -> dict[str, Any]:
    bruto = dict(estado or {})
    atividade = str(bruto.get("activity") or bruto.get("visual_activity") or "idle")
    emocao = str(bruto.get("emotion") or bruto.get("current_emotion") or "calma")
    mapa = {
        "idle": "Pronta", "listening": "Ouvindo", "thinking": "Pensando",
        "executing": "Executando", "speaking": "Falando",
        "reconnecting": "Reconectando",
    }
    if bool(bruto.get("is_speaking")):
        atividade = "speaking"
    modo = str(bruto.get("interaction_mode") or "").casefold().strip()
    if modo not in {"chat", "voice"}:
        modo = "chat" if bool(bruto.get("modo_chat", True)) else "voice"
    return {
        "activity": atividade if atividade in mapa else "idle",
        "activity_label": mapa.get(atividade, "Pronta"),
        "emotion": emocao[:32] or "calma",
        "emotion_level": max(1, min(3, int(bruto.get("emotion_level") or 1))),
        "voice_available": bool(bruto.get("voice_available", False)),
        "interaction_mode": modo,
    }


def sanitizar_configuracao(configuracao: Mapping[str, Any] | None) -> dict[str, Any]:
    """Defesa adicional: apenas campos públicos conhecidos atravessam a ponte."""
    bruto = dict(configuracao or {})
    provedor = str(bruto.get("provider") or "ollama").casefold().strip()
    if provedor not in {"ollama", "portatil", "openrouter"}:
        provedor = "ollama"
    modelos_brutos = bruto.get("models_by_provider")
    modelos = dict(modelos_brutos) if isinstance(modelos_brutos, Mapping) else {}
    return {
        "provider": provedor,
        "model": _texto_seguro(bruto.get("model"), 160),
        "models_by_provider": {
            nome: _texto_seguro(modelos.get(nome), 160)
            for nome in ("ollama", "portatil", "openrouter")
        },
        "base_url": _texto_seguro(bruto.get("base_url"), 240),
        "api_key_configured": bool(bruto.get("api_key_configured", False)),
        "restart_required": bool(bruto.get("restart_required", False)),
        "mascot_enabled": bool(bruto.get("mascot_enabled", False)),
    }


def validar_mensagem_cliente(
    mensagem: Mapping[str, Any],
    *,
    token: str,
    autenticado: bool,
) -> dict[str, Any]:
    if not isinstance(mensagem, Mapping):
        raise ErroProtocoloDesktop("mensagem deve ser um objeto JSON")
    tipo = str(mensagem.get("type") or "").strip()
    if tipo not in TIPOS_CLIENTE:
        raise ErroProtocoloDesktop("tipo de mensagem inválido")
    if not autenticado:
        if tipo != "hello" or not secrets.compare_digest(
            str(mensagem.get("token") or ""), token,
        ):
            raise ErroProtocoloDesktop("token de sessão inválido")
    elif tipo == "hello":
        raise ErroProtocoloDesktop("sessão já autenticada")
    if tipo == "input_submit":
        texto = _texto_seguro(mensagem.get("text"), 8_000)
        if not texto:
            raise ErroProtocoloDesktop("entrada vazia")
        return {"type": tipo, "text": texto, "id": _texto_seguro(mensagem.get("id"), 80)}
    if tipo == "mode_set":
        modo = str(mensagem.get("mode") or "").casefold().strip()
        if modo not in {"chat", "voice"}:
            raise ErroProtocoloDesktop("modo de interação inválido")
        return {"type": tipo, "mode": modo, "id": _texto_seguro(mensagem.get("id"), 80)}
    if tipo == "settings_update":
        configuracao = mensagem.get("settings")
        if not isinstance(configuracao, Mapping):
            raise ErroProtocoloDesktop("configuração deve ser um objeto")
        permitidos = {
            "provider", "model", "api_key_action", "api_key", "mascot_enabled",
        }
        if set(configuracao) - permitidos:
            raise ErroProtocoloDesktop("configuração contém campos inválidos")
        # O limite global do JSONL já protege o canal. Estes limites tornam a
        # rejeição previsível antes de chegar ao runtime de persistência.
        if len(str(configuracao.get("model") or "")) > 160:
            raise ErroProtocoloDesktop("modelo acima do limite")
        if len(str(configuracao.get("api_key") or "")) > 8_192:
            raise ErroProtocoloDesktop("credencial acima do limite")
        if "mascot_enabled" in configuracao and not isinstance(
            configuracao["mascot_enabled"], bool,
        ):
            raise ErroProtocoloDesktop("preferência do mascote deve ser booleana")
        return {
            "type": tipo,
            "id": _texto_seguro(mensagem.get("id"), 80),
            "settings": dict(configuracao),
        }
    return {"type": tipo, "id": _texto_seguro(mensagem.get("id"), 80)}


class DesktopBridgeRuntime:
    """Servidor de uma sessão; fechar o cliente nunca encerra a mente."""

    def __init__(
        self,
        *,
        enviar_entrada: Callable[[str], Any],
        historico_getter: Callable[[], Sequence[Mapping[str, Any]]],
        estado_getter: Callable[[], Mapping[str, Any]],
        modo_setter: Callable[[bool], Any] | None = None,
        configuracao_getter: Callable[[], Mapping[str, Any]] | None = None,
        configuracao_setter: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        reiniciar_aplicacao: Callable[[], Any] | None = None,
        host: str = "127.0.0.1",
        port: int = 0,
        max_message_bytes: int = 65_536,
        rate_limit: int = 24,
        rate_window_s: float = 5.0,
        log: Callable[[str], Any] = print,
    ) -> None:
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("a ponte desktop aceita somente loopback")
        self.enviar_entrada = enviar_entrada
        self.historico_getter = historico_getter
        self.estado_getter = estado_getter
        self.modo_setter = modo_setter
        self.configuracao_getter = configuracao_getter
        self.configuracao_setter = configuracao_setter
        self.reiniciar_aplicacao = reiniciar_aplicacao
        self.host = "127.0.0.1" if host == "localhost" else host
        self.port = max(0, int(port))
        self.max_message_bytes = max(1_024, int(max_message_bytes))
        self.rate_limit = max(2, int(rate_limit))
        self.rate_window_s = max(1.0, float(rate_window_s))
        self.log = log
        self.token = secrets.token_urlsafe(32)
        self.session_id = secrets.token_hex(8)
        self.parent_pid = os.getpid()
        self.started_at = time.time()
        self._server: socket.socket | None = None
        self._client: socket.socket | None = None
        # Uma conexão TCP ainda não é uma sessão autenticada. Manter o socket
        # pendente separado impede o poll de publicar ``state`` antes do
        # ``snapshot`` e derrubar o próprio handshake do Terminal 2.
        self._client_pending: socket.socket | None = None
        self._client_lock = threading.RLock()
        # Estado, ACK e fala final podem partir de threads diferentes. Sem uma
        # trava de escrita, dois JSONL pequenos ainda podem se intercalar no
        # mesmo socket e fazer o cliente descartar a conexão inteira.
        self._send_lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._poll_thread: threading.Thread | None = None
        self._processo: subprocess.Popen[Any] | None = None
        self._ultimo_estado = ""
        self._eventos: deque[dict[str, Any]] = deque(maxlen=120)

    @property
    def endereco(self) -> tuple[str, int]:
        return self.host, self.port

    def iniciar(self) -> dict[str, Any]:
        if self._server is not None and self._thread and self._thread.is_alive():
            return self.diagnostico()
        # Uma exceção antiga podia matar somente a thread acceptora e deixar o
        # socket em listen. Nesse estado o TCP aceitava no backlog, mas ninguém
        # lia o hello. Fechamos toda sobra antes de reconstruir a ponte.
        servidor_antigo, self._server = self._server, None
        if servidor_antigo is not None:
            try:
                servidor_antigo.close()
            except OSError:
                pass
        with self._client_lock:
            clientes_antigos = (self._client, self._client_pending)
            self._client = None
            self._client_pending = None
        for cliente_antigo in clientes_antigos:
            if cliente_antigo is not None:
                try:
                    cliente_antigo.close()
                except OSError:
                    pass
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((self.host, self.port))
        servidor.listen(1)
        servidor.settimeout(0.5)
        self.port = int(servidor.getsockname()[1])
        self._server = servidor
        self._stop.clear()
        self._thread = threading.Thread(target=self._servir, name="Laylay-Desktop-Bridge", daemon=True)
        if not self._poll_thread or not self._poll_thread.is_alive():
            self._poll_thread = threading.Thread(target=self._publicar_estados, name="Laylay-Desktop-State", daemon=True)
        self._thread.start()
        if not self._poll_thread.is_alive():
            self._poll_thread.start()
        self.log(
            f"🖥️ [TERMINAL 2] ponte ativa em {self.host}:{self.port} "
            f"| sessão={self.session_id[:8]} pid={self.parent_pid}"
        )
        return self.diagnostico()

    def iniciar_cliente(self, caminho: str | os.PathLike[str]) -> bool:
        if self._processo is not None and self._processo.poll() is None:
            self.log(
                "🖥️ [TERMINAL 2] interface já ativa "
                f"| sessão={self.session_id[:8]} pid={self._processo.pid}"
            )
            return True
        if not self._server or not self._thread or not self._thread.is_alive():
            self.iniciar()
        arquivo = Path(caminho).resolve()
        if not arquivo.is_file():
            self.log(f"⚠️ [TERMINAL 2] cliente não encontrado: {arquivo}")
            return False
        ambiente = dict(os.environ)
        ambiente.update({
            "LAYLAY_DESKTOP_HOST": self.host,
            "LAYLAY_DESKTOP_PORT": str(self.port),
            "LAYLAY_DESKTOP_TOKEN": self.token,
            "LAYLAY_PROJECT_ROOT": str(arquivo.parents[1]),
            "LAYLAY_DESKTOP_SESSION": self.session_id,
            "LAYLAY_PARENT_PID": str(self.parent_pid),
            "LAYLAY_PARENT_STARTED_AT": str(self.started_at),
        })
        comando = [sys.executable, str(arquivo)]
        try:
            self._processo = subprocess.Popen(comando, env=ambiente, cwd=str(arquivo.parents[1]))
            self.log(
                "🖥️ [TERMINAL 2] interface iniciada "
                f"| sessão={self.session_id[:8]} pid={self._processo.pid} "
                f"python={Path(sys.executable).name} arquivo={arquivo}"
            )
            return True
        except Exception as erro:
            self.log(f"⚠️ [TERMINAL 2] interface indisponível: {type(erro).__name__}: {erro}")
            return False

    def _servir(self) -> None:
        servidor = self._server
        if servidor is None:
            return
        while not self._stop.is_set():
            try:
                cliente, endereco = servidor.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            if endereco[0] not in {"127.0.0.1", "::1"}:
                cliente.close()
                continue
            with self._client_lock:
                if self._client is not None or self._client_pending is not None:
                    self._enviar_socket(cliente, {"type": "error", "code": "client_busy", "message": "Outra interface já está conectada."})
                    cliente.close()
                    continue
                self._client_pending = cliente
            try:
                self._atender(cliente)
            except Exception as erro:
                # Um getter de snapshot/configuração jamais pode matar a única
                # thread que aceita o Terminal. A sessão falha, a ponte fica.
                self.log(
                    "⚠️ [TERMINAL 2:PONTE] sessão encerrada durante o atendimento "
                    f"| tipo={type(erro).__name__}"
                )
            finally:
                with self._client_lock:
                    if self._client is cliente:
                        self._client = None
                    if self._client_pending is cliente:
                        self._client_pending = None
                try:
                    cliente.close()
                except OSError:
                    pass

    def _atender(self, cliente: socket.socket) -> None:
        # ``socket.makefile().readline()`` pode deixar o buffer interno
        # inutilizável depois de um timeout no Windows. O protocolo já é
        # JSONL, então mantemos o buffer diretamente sobre ``recv``; um
        # intervalo ocioso nunca invalida a sessão autenticada.
        cliente.settimeout(0.5)
        autenticado = False
        requisicoes: deque[float] = deque()
        for linha in self._iterar_linhas_cliente(cliente):
            if self._stop.is_set():
                break
            agora = time.monotonic()
            while requisicoes and agora - requisicoes[0] > self.rate_window_s:
                requisicoes.popleft()
            if len(requisicoes) >= self.rate_limit:
                self._erro(cliente, "rate_limited", "Muitas mensagens em pouco tempo.")
                continue
            requisicoes.append(agora)
            try:
                bruto = json.loads(linha.decode("utf-8"))
                msg = validar_mensagem_cliente(bruto, token=self.token, autenticado=autenticado)
            except (UnicodeDecodeError, json.JSONDecodeError, ErroProtocoloDesktop) as erro:
                self._erro(cliente, "invalid_message", str(erro))
                if not autenticado:
                    break
                continue
            tipo = msg["type"]
            if tipo == "hello":
                snapshot = {
                    "type": "snapshot",
                    "messages": sanitizar_historico(self.historico_getter()),
                    "state": sanitizar_estado(self.estado_getter()),
                    "events": list(self._eventos)[-30:],
                    "session": {
                        "id": self.session_id,
                        "parent_pid": self.parent_pid,
                        "started_at": self.started_at,
                    },
                }
                if callable(self.configuracao_getter):
                    snapshot["settings"] = sanitizar_configuracao(self.configuracao_getter())
                if not self._enviar_socket(cliente, snapshot):
                    raise ConnectionError("não foi possível confirmar o snapshot")
                with self._client_lock:
                    if self._client_pending is not cliente:
                        raise ConnectionError("sessão pendente deixou de ser válida")
                    self._client_pending = None
                    self._client = cliente
                autenticado = True
                self.log(
                    "🖥️ [TERMINAL 2:PONTE] sessão autenticada "
                    f"| sessão={self.session_id[:8]}"
                )
            elif tipo == "ready":
                self._enviar_socket(cliente, {"type": "state", **sanitizar_estado(self.estado_getter())})
            elif tipo == "heartbeat":
                self._enviar_socket(cliente, {"type": "state", "heartbeat": True, **sanitizar_estado(self.estado_getter())})
            elif tipo == "input_submit":
                entrada_id = msg.get("id") or secrets.token_hex(6)
                try:
                    retorno = self.enviar_entrada(msg["text"])
                    aceito = retorno is not False
                    self._enviar_socket(cliente, {
                        "type": "input_ack", "id": entrada_id,
                        "accepted": aceito,
                        "message": (
                            "" if aceito
                            else "A entrada canônica recusou o pedido."
                        ),
                    })
                except Exception as erro:
                    self._enviar_socket(cliente, {
                        "type": "input_ack", "id": entrada_id,
                        "accepted": False,
                        "message": (
                            "A entrada canônica recusou o pedido: "
                            f"{type(erro).__name__}"
                        ),
                    })
            elif tipo == "mode_set":
                requisicao_id = msg.get("id") or secrets.token_hex(6)
                desejado = msg["mode"]
                try:
                    if not callable(self.modo_setter):
                        raise RuntimeError("porta de modo indisponível")
                    estado_antes = sanitizar_estado(self.estado_getter())
                    if desejado == "voice" and not estado_antes["voice_available"]:
                        raise RuntimeError("ouvido indisponível")
                    self.modo_setter(desejado == "chat")
                    estado = sanitizar_estado(self.estado_getter())
                    aplicado = estado["interaction_mode"] == desejado
                    self._enviar_socket(cliente, {
                        "type": "mode_state", "id": requisicao_id,
                        "mode": estado["interaction_mode"],
                        "voice_available": estado["voice_available"],
                        "success": aplicado,
                        "message": "" if aplicado else "A mente não confirmou a troca de modo.",
                    })
                except Exception as erro:
                    estado = sanitizar_estado(self.estado_getter())
                    self._enviar_socket(cliente, {
                        "type": "mode_state", "id": requisicao_id,
                        "mode": estado["interaction_mode"],
                        "voice_available": estado["voice_available"],
                        "success": False,
                        "message": f"Não consegui trocar o modo: {type(erro).__name__}.",
                    })
            elif tipo == "settings_get":
                if not callable(self.configuracao_getter):
                    self._erro(cliente, "settings_unavailable", "Configurações indisponíveis nesta instalação.")
                    continue
                self._enviar_socket(cliente, {
                    "type": "settings_state", "id": msg.get("id") or "",
                    "settings": sanitizar_configuracao(self.configuracao_getter()),
                })
            elif tipo == "settings_update":
                requisicao_id = msg.get("id") or secrets.token_hex(6)
                try:
                    if not callable(self.configuracao_setter):
                        raise RuntimeError("porta de configuração indisponível")
                    resultado = dict(self.configuracao_setter(msg["settings"]) or {})
                    publico = {
                        "saved": bool(resultado.get("saved", False)),
                        "restart_required": bool(resultado.get("restart_required", False)),
                        "message": _texto_seguro(resultado.get("message"), 300),
                        "settings": sanitizar_configuracao(resultado.get("settings")),
                    }
                    self._enviar_socket(cliente, {
                        "type": "settings_result", "id": requisicao_id, **publico,
                    })
                except Exception as erro:
                    # Nunca usamos ``str(erro)`` aqui: bibliotecas de proteção
                    # podem incluir parâmetros sensíveis na mensagem original.
                    # A exceção de configuração é nossa e tem contrato seguro.
                    mensagem_erro = (
                        _texto_seguro(str(erro), 300)
                        if isinstance(erro, ErroConfiguracaoAplicacao)
                        else f"Não consegui salvar a configuração ({type(erro).__name__})."
                    )
                    self._enviar_socket(cliente, {
                        "type": "settings_result", "id": requisicao_id,
                        "saved": False, "restart_required": False,
                        "message": mensagem_erro,
                        "settings": sanitizar_configuracao(
                            self.configuracao_getter() if callable(self.configuracao_getter) else {}
                        ),
                    })
            elif tipo == "restart_request":
                requisicao_id = msg.get("id") or secrets.token_hex(6)
                try:
                    if not callable(self.reiniciar_aplicacao):
                        raise RuntimeError("porta de reinício indisponível")
                    aceito = self.reiniciar_aplicacao() is not False
                    self._enviar_socket(cliente, {
                        "type": "restart_result",
                        "id": requisicao_id,
                        "accepted": aceito,
                        "message": (
                            "Reinício solicitado. A Laylay vai voltar em instantes."
                            if aceito else "O reinício já está em andamento."
                        ),
                    })
                except Exception as erro:
                    self._enviar_socket(cliente, {
                        "type": "restart_result",
                        "id": requisicao_id,
                        "accepted": False,
                        "message": f"Não consegui iniciar o reinício ({type(erro).__name__}).",
                    })

    def _iterar_linhas_cliente(self, cliente: socket.socket):
        """Produz mensagens JSONL sem transformar timeout em corrupção do leitor."""
        buffer = b""
        while not self._stop.is_set():
            try:
                bloco = cliente.recv(min(16_384, self.max_message_bytes + 1))
            except socket.timeout:
                continue
            except OSError:
                return
            if not bloco:
                return
            buffer += bloco
            while b"\n" in buffer:
                linha, buffer = buffer.split(b"\n", 1)
                if not linha:
                    continue
                if len(linha) + 1 > self.max_message_bytes:
                    self._erro(
                        cliente, "message_too_large",
                        "Mensagem acima do limite permitido.",
                    )
                    return
                yield linha
            if len(buffer) > self.max_message_bytes:
                self._erro(
                    cliente, "message_too_large",
                    "Mensagem acima do limite permitido.",
                )
                return

    def publicar_fala_final(
        self,
        texto: str,
        emocao: str = "calma",
        nivel: int = 1,
        **dados: Any,
    ) -> bool:
        fala = _texto_seguro(texto)
        if not fala:
            return False
        return self._publicar({
            "type": "assistant_message",
            "id": _texto_seguro(dados.get("mensagem_id"), 96),
            "text": fala,
            "emotion": _texto_seguro(emocao, 32) or "calma",
            "emotion_level": max(1, min(3, int(nivel or 1))),
            "timestamp": time.time(),
        })

    def publicar_evento(self, titulo: str, detalhe: str = "", *, nivel: str = "info") -> None:
        evento = {"title": _texto_seguro(titulo, 120), "detail": _texto_seguro(detalhe, 500), "level": nivel if nivel in {"info", "success", "warning", "error"} else "info", "timestamp": time.time()}
        self._eventos.append(evento)
        self._publicar({"type": "state", "event": evento, **sanitizar_estado(self.estado_getter())})

    def _publicar_estados(self) -> None:
        ultimo_envio = 0.0
        while not self._stop.wait(0.35):
            try:
                estado = sanitizar_estado(self.estado_getter())
            except Exception as erro:
                self.log(
                    "⚠️ [TERMINAL 2:PONTE] estado indisponível "
                    f"| tipo={type(erro).__name__}"
                )
                continue
            chave = json.dumps(estado, ensure_ascii=False, sort_keys=True)
            agora = time.monotonic()
            if chave != self._ultimo_estado or agora - ultimo_envio >= 4.0:
                self._ultimo_estado = chave
                ultimo_envio = agora
                self._publicar({"type": "state", "heartbeat": True, **estado})

    def _publicar(self, mensagem: Mapping[str, Any]) -> bool:
        with self._client_lock:
            cliente = self._client
        return self._enviar_socket(cliente, mensagem) if cliente else False

    def _enviar_socket(
        self,
        cliente: socket.socket | None,
        mensagem: Mapping[str, Any],
    ) -> bool:
        if cliente is None:
            return False
        try:
            pacote = (
                json.dumps(
                    dict(mensagem), ensure_ascii=False, separators=(",", ":"),
                )
                + "\n"
            ).encode("utf-8")
            with self._send_lock:
                cliente.sendall(pacote)
            return True
        except OSError:
            with self._client_lock:
                if self._client is cliente:
                    self._client = None
                if self._client_pending is cliente:
                    self._client_pending = None
            try:
                cliente.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            return False

    def _erro(self, cliente: socket.socket, codigo: str, mensagem: str) -> None:
        self._enviar_socket(cliente, {"type": "error", "code": codigo, "message": mensagem})

    def parar(self, timeout_s: float = 1.0) -> None:
        self._stop.set()
        with self._client_lock:
            cliente, self._client = self._client, None
            pendente, self._client_pending = self._client_pending, None
        sockets = tuple(
            dict.fromkeys(sock for sock in (cliente, pendente, self._server) if sock)
        )
        for sock in sockets:
            if sock:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    sock.close()
                except OSError:
                    pass
        self._server = None
        processo = self._processo
        if processo and processo.poll() is None:
            processo.terminate()
            try:
                processo.wait(timeout=max(0.1, timeout_s))
            except subprocess.TimeoutExpired:
                processo.kill()

    def diagnostico(self) -> dict[str, Any]:
        with self._client_lock:
            conectado = self._client is not None
            handshake = self._client_pending is not None
        thread_viva = bool(self._thread and self._thread.is_alive())
        return {
            "disponivel": self._server is not None and thread_viva
            and not self._stop.is_set(),
            "host": self.host,
            "port": self.port,
            "cliente_conectado": conectado,
            "cliente_em_handshake": handshake,
            "thread_viva": thread_viva,
            "sessao": self.session_id[:8],
            "pid": self.parent_pid,
            "somente_loopback": True,
            "autenticado": bool(self.token),
            "autoriza_execucao": False,
        }


def criar_desktop_bridge_runtime(**kwargs: Any) -> DesktopBridgeRuntime:
    return DesktopBridgeRuntime(**kwargs)

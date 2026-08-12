"""Ponte local autenticada entre a mente canônica e o Terminal Laylay 2.0.

O protocolo é JSON Lines sobre TCP/loopback. A ponte transporta somente
retratos sanitizados; interpretar ou executar pedidos continua sendo trabalho
da entrada canônica da Laylay.
"""

from __future__ import annotations

from collections import deque
import json
import math
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import threading
import time
from typing import Any, Callable, Mapping, Sequence

from mente_laylay.integracao.configuracao_aplicacao import ErroConfiguracaoAplicacao
from mente_laylay.integracao.acoes_terminal import (
    IDS_ACOES_RAPIDAS,
    definicao_acao_rapida,
)


TIPOS_CLIENTE = frozenset({
    "hello", "ready", "heartbeat", "input_submit", "mode_set",
    "settings_get", "settings_update", "restart_request",
})
TIPOS_BACKEND = frozenset({
    "snapshot", "input_ack", "assistant_message", "state", "error",
    "mode_state", "settings_state", "settings_result", "restart_result",
    "dashboard_state", "action_state",
})

_ESTADOS_ACAO_RAPIDA = frozenset({
    "sending", "received", "executing", "awaiting_confirmation",
    "confirmed", "partial", "failed",
})
_ESTADOS_DISPONIBILIDADE_ACAO = frozenset({
    "available", "degraded", "requires_input", "unavailable",
})


class ErroProtocoloDesktop(ValueError):
    pass


def _texto_seguro(valor: Any, limite: int = 8_000) -> str:
    texto = str(valor or "").replace("\x00", "").strip()
    return texto[:limite]


_PADRAO_TEXTO_PRIVADO_DASHBOARD = re.compile(
    r"(?ix)(?:"
    r"\b(?:senha|password|token|api[ _-]?key|chave[ _-]?api|cpf|cnpj|cvv|pin|pix)\b"
    r"|\bsk-(?:or-v1-)?[a-z0-9_-]{8,}\b"
    r"|\bgh[pousr]_[a-z0-9]{16,}\b"
    r"|\beyj[a-z0-9_-]{6,}\.[a-z0-9_-]{6,}\.[a-z0-9_-]{6,}\b"
    r"|https?://|(?:[a-z]:\\)|(?:\\\\[\w.-]+\\)"
    r"|\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b"
    r"|\b(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[- ]?\d{4}\b"
    r")"
)
_PADRAO_TEMA_SENSIVEL_DASHBOARD = re.compile(
    r"(?ix)\b(?:"
    r"sa[uú]de|doen[çc]a|diagn[oó]stico|m[eé]dic[oa]|medica[çc][aã]o|"
    r"rem[eé]dio|terapia|sexual|[ií]ntim[oa]|religi[aã]o|religioso|"
    r"pol[ií]tica|partido|voto|sal[aá]rio|d[ií]vida|conta banc[aá]ria|"
    r"cart[aã]o|endere[çc]o"
    r")\b"
)


def _texto_publico_dashboard(valor: Any, limite: int, *, fallback: str) -> str:
    texto = _texto_seguro(valor, limite)
    if not texto or _PADRAO_TEXTO_PRIVADO_DASHBOARD.search(texto):
        return fallback
    return texto


def _texto_memoria_publico_dashboard(
    valor: Any,
    limite: int,
    *,
    fallback: str,
) -> str:
    texto = _texto_publico_dashboard(valor, limite, fallback=fallback)
    if texto != fallback and _PADRAO_TEMA_SENSIVEL_DASHBOARD.search(texto):
        return fallback
    return texto


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


def _numero_dashboard(
    valor: Any,
    *,
    minimo: float,
    maximo: float,
) -> float | None:
    if isinstance(valor, bool):
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numero) or numero < minimo or numero > maximo:
        return None
    return round(numero, 1)


def _frescor_dashboard(valor: Any, *, disponivel: bool) -> str:
    if not disponivel:
        return "unavailable"
    frescor = str(valor or "").casefold().strip()
    if frescor in {"fresh", "stale", "unavailable"}:
        return frescor
    return "fresh" if disponivel else "unavailable"


def _inteiro_dashboard(valor: Any, *, minimo: int = 0, maximo: int) -> int:
    if isinstance(valor, bool):
        return minimo
    try:
        numero = int(valor)
    except (TypeError, ValueError, OverflowError):
        return minimo
    return max(minimo, min(maximo, numero))


def _saude_dashboard(valor: Any) -> dict[str, Any]:
    bruto = dict(valor) if isinstance(valor, Mapping) else {}
    estado = str(bruto.get("state") or "unavailable").casefold().strip()
    permitidos = {
        "online", "ready", "paused", "degraded", "unavailable", "unknown",
    }
    if estado not in permitidos:
        estado = "unavailable"
    observado = _numero_dashboard(
        bruto.get("observed_at"), minimo=0, maximo=9_999_999_999,
    ) or 0.0
    frescor = _frescor_dashboard(
        bruto.get("freshness"),
        disponivel=estado != "unavailable" and observado > 0,
    )
    if frescor == "unavailable":
        estado = "unavailable"
    resultado = {
        "state": estado,
        "label": _texto_publico_dashboard(
            bruto.get("label"), 80, fallback="Indisponível",
        ),
        "freshness": frescor,
        "observed_at": observado,
    }
    if estado == "unavailable":
        resultado["label"] = "Indisponível"
    if "provider" in bruto:
        provedor = str(bruto.get("provider") or "").casefold().strip()
        if provedor in {"ollama", "portatil", "openrouter"}:
            resultado["provider"] = provedor
        resultado["provider_label"] = _texto_publico_dashboard(
            bruto.get("provider_label"), 40, fallback="—",
        )
        resultado["model"] = _texto_publico_dashboard(
            bruto.get("model"), 120, fallback="",
        )
    return resultado


def _metrica_dashboard(
    valor: Any,
    *,
    unidade: str,
    minimo: float,
    maximo: float,
    max_age_s: float,
) -> dict[str, Any]:
    bruto = dict(valor) if isinstance(valor, Mapping) else {}
    numero = _numero_dashboard(bruto.get("value"), minimo=minimo, maximo=maximo)
    observado = _numero_dashboard(
        bruto.get("observed_at"), minimo=0, maximo=9_999_999_999,
    ) or 0.0
    frescor = _frescor_dashboard(
        bruto.get("freshness"),
        disponivel=numero is not None and observado > 0,
    )
    if frescor == "unavailable":
        numero = None
    return {
        "value": numero,
        "unit": unidade,
        "freshness": frescor,
        "observed_at": observado,
        "max_age_s": max_age_s,
    }


def sanitizar_dashboard_estado(
    dashboard: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Allowlist da projeção pública; nenhum estado interno cru atravessa."""
    bruto = dict(dashboard) if isinstance(dashboard, Mapping) else {}
    saude = dict(bruto.get("health") or {}) if isinstance(
        bruto.get("health"), Mapping,
    ) else {}
    contexto = dict(bruto.get("context") or {}) if isinstance(
        bruto.get("context"), Mapping,
    ) else {}
    sistema = dict(bruto.get("system") or {}) if isinstance(
        bruto.get("system"), Mapping,
    ) else {}
    status = str(bruto.get("status") or "unavailable").casefold().strip()
    if status not in {"ok", "partial", "unavailable"}:
        status = "unavailable"
    memoria: list[dict[str, Any]] = []
    itens = bruto.get("memory_recent")
    if isinstance(itens, (list, tuple)):
        for item in itens:
            if not isinstance(item, Mapping):
                continue
            tipo = str(item.get("kind") or "").casefold().strip()
            fonte = str(item.get("source") or "").casefold().strip()
            if tipo not in {"reminder", "preference", "task"}:
                continue
            fonte_por_tipo = {
                "reminder": "agenda_confirmed",
                "preference": "user_confirmed",
                "task": "executor_confirmed",
            }
            if fonte != fonte_por_tipo[tipo]:
                continue
            resumo = _texto_memoria_publico_dashboard(
                item.get("summary"), 160,
                fallback={
                    "reminder": "Você tem um lembrete",
                    "preference": "Preferência confirmada",
                    "task": "Ação concluída",
                }[tipo],
            )
            if not resumo:
                continue
            memoria.append({
                "kind": tipo,
                "summary": resumo,
                "detail": _texto_memoria_publico_dashboard(
                    item.get("detail"), 100, fallback="",
                ),
                "source": fonte,
                "timestamp": _numero_dashboard(
                    item.get("timestamp"), minimo=0, maximo=9_999_999_999,
                ) or 0.0,
            })
            if len(memoria) >= 3:
                break
    contexto_observado = _numero_dashboard(
        contexto.get("observed_at"), minimo=0, maximo=9_999_999_999,
    ) or 0.0
    contexto_disponivel = contexto_observado > 0 and any(
        chave in contexto
        for chave in (
            "project", "mode", "interaction_mode", "city", "game_active",
        )
    )
    frescor_contexto = _frescor_dashboard(
        contexto.get("freshness"), disponivel=contexto_disponivel,
    )
    jogo_ativo = (
        contexto.get("game_active") is True
        and frescor_contexto != "unavailable"
    )
    contexto_publico = {
        "project": _texto_publico_dashboard(
            contexto.get("project"), 80, fallback="Laylay",
        ),
        "mode": _texto_publico_dashboard(
            contexto.get("mode"), 40, fallback="—",
        ),
        "interaction_mode": (
            str(contexto.get("interaction_mode") or "chat").casefold().strip()
            if str(contexto.get("interaction_mode") or "").casefold().strip()
            in {"chat", "voice"} else "chat"
        ),
        "city": _texto_publico_dashboard(
            contexto.get("city"), 80, fallback="—",
        ),
        "game_active": jogo_ativo,
        "game_name": (
            _texto_publico_dashboard(
                contexto.get("game_name"), 100, fallback="Jogo detectado",
            ) if jogo_ativo else ""
        ),
        "freshness": frescor_contexto,
        "observed_at": contexto_observado,
    }
    acoes_publicas: list[dict[str, str]] = []
    for item in list(bruto.get("quick_actions") or ())[:12]:
        if not isinstance(item, Mapping):
            continue
        acao_id = _texto_seguro(item.get("id"), 48)
        if acao_id not in IDS_ACOES_RAPIDAS:
            continue
        estado_acao = _texto_seguro(item.get("state"), 32).casefold()
        if estado_acao not in _ESTADOS_DISPONIBILIDADE_ACAO:
            estado_acao = "unavailable"
        acoes_publicas.append({
            "id": acao_id,
            "state": estado_acao,
            "reason": _texto_publico_dashboard(
                item.get("reason"), 120, fallback="",
            ),
        })
    resultado = {
        "schema_version": 1,
        "status": status,
        "generated_at": _numero_dashboard(
            bruto.get("generated_at"), minimo=0, maximo=9_999_999_999,
        ) or 0.0,
        "sequence": _inteiro_dashboard(
            bruto.get("sequence"), maximo=2_147_483_647,
        ),
        "health": {
            "llm": _saude_dashboard(saude.get("llm")),
            "microphone": _saude_dashboard(saude.get("microphone")),
            "memory": _saude_dashboard(saude.get("memory")),
        },
        "context": contexto_publico,
        "memory_recent": memoria,
        "quick_actions": acoes_publicas,
        "system": {
            "cpu_percent": _metrica_dashboard(
                sistema.get("cpu_percent"), unidade="%", minimo=0, maximo=100,
                max_age_s=5.0,
            ),
            "ram_percent": _metrica_dashboard(
                sistema.get("ram_percent"), unidade="%", minimo=0, maximo=100,
                max_age_s=5.0,
            ),
            "disk_percent": _metrica_dashboard(
                sistema.get("disk_percent"), unidade="%", minimo=0, maximo=100,
                max_age_s=20.0,
            ),
            "temperature_c": _metrica_dashboard(
                sistema.get("temperature_c"), unidade="°C", minimo=0, maximo=125,
                max_age_s=120.0,
            ),
            "uptime_seconds": _metrica_dashboard(
                sistema.get("uptime_seconds"), unidade="s", minimo=0,
                maximo=20 * 365 * 24 * 3600, max_age_s=20.0,
            ),
        },
    }
    saudes_publicas = tuple(resultado["health"].values())
    sistema_publico = resultado["system"]
    metricas_principais = (
        sistema_publico["cpu_percent"], sistema_publico["ram_percent"],
        sistema_publico["disk_percent"], sistema_publico["uptime_seconds"],
    )
    tem_algum_dado = any(
        item.get("state") != "unavailable" for item in saudes_publicas
    ) or resultado["context"]["freshness"] != "unavailable" or any(
        item.get("value") is not None for item in metricas_principais
    )
    tem_degradacao = any(
        item.get("state") in {"degraded", "unavailable"}
        or item.get("freshness") in {"stale", "unavailable"}
        for item in saudes_publicas
    ) or resultado["context"]["freshness"] in {"stale", "unavailable"} or any(
        item.get("value") is None or item.get("freshness") != "fresh"
        for item in metricas_principais
    )
    if not tem_algum_dado:
        resultado["status"] = "unavailable"
    elif tem_degradacao and resultado["status"] == "ok":
        resultado["status"] = "partial"
    return resultado


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
        tipo_entrada = _texto_seguro(mensagem.get("kind"), 24).casefold() or "chat"
        if tipo_entrada not in {"chat", "quick_action"}:
            raise ErroProtocoloDesktop("origem da entrada inválida")
        acao_id = _texto_seguro(mensagem.get("action"), 48)
        if tipo_entrada == "quick_action" and acao_id not in IDS_ACOES_RAPIDAS:
            raise ErroProtocoloDesktop("ação rápida inválida")
        if tipo_entrada == "chat":
            acao_id = ""
        return {
            "type": tipo,
            "text": texto,
            "id": _texto_seguro(mensagem.get("id"), 80),
            "kind": tipo_entrada,
            "action": acao_id,
        }
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


def classificar_resultado_acao(
    plano: Mapping[str, Any] | None,
    *,
    acao_id: str,
) -> dict[str, str]:
    """Converte somente evidência do plano no estado público do botão."""
    dados = dict(plano or {})
    definicao = definicao_acao_rapida(acao_id)
    intent_esperada = str(definicao.get("intent") or "").upper()
    comandos = [
        dict(item) for item in list(dados.get("comandos") or ())
        if isinstance(item, Mapping)
    ]
    relevantes = [
        item for item in comandos
        if not intent_esperada
        or str(item.get("intent") or "").upper() == intent_esperada
    ]
    estados = " ".join(
        str(item.get("status") or "").casefold() for item in relevantes
    )
    if "aguardando_confirmacao" in estados or "aguardando confirmação" in estados:
        estado = "awaiting_confirmation"
    elif relevantes and all(
        item.get("executou") is True and item.get("confirmado") is True
        for item in relevantes
    ):
        estado = "confirmed"
    else:
        sucessos = sum(item.get("executou") is True for item in relevantes)
        falhas = sum(item.get("executou") is False for item in relevantes)
        if sucessos:
            estado = "partial"
        elif falhas or relevantes or dados.get("erros"):
            estado = "failed"
        else:
            # Uma fala final sem comando correspondente não prova que o clique
            # operacional foi executado.
            estado = "failed"
    resumo = {
        "awaiting_confirmation": "Aguardando sua confirmação",
        "confirmed": "Resultado confirmado pela mente",
        "partial": "A ação terminou sem confirmação completa",
        "failed": "A ação não foi confirmada",
    }[estado]
    return {"state": estado, "summary": resumo}


class DesktopBridgeRuntime:
    """Servidor de uma sessão; fechar o cliente nunca encerra a mente."""

    def __init__(
        self,
        *,
        enviar_entrada: Callable[[str], Any],
        historico_getter: Callable[[], Sequence[Mapping[str, Any]]],
        estado_getter: Callable[[], Mapping[str, Any]],
        dashboard_getter: Callable[[], Mapping[str, Any]] | None = None,
        resultado_acao_getter: Callable[[], Mapping[str, Any]] | None = None,
        modo_setter: Callable[[bool], Any] | None = None,
        configuracao_getter: Callable[[], Mapping[str, Any]] | None = None,
        configuracao_setter: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        reiniciar_aplicacao: Callable[[], Any] | None = None,
        host: str = "127.0.0.1",
        port: int = 0,
        max_message_bytes: int = 65_536,
        rate_limit: int = 24,
        rate_window_s: float = 5.0,
        dashboard_interval_s: float = 1.0,
        dashboard_getter_timeout_s: float = 0.2,
        log: Callable[[str], Any] = print,
    ) -> None:
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("a ponte desktop aceita somente loopback")
        self.enviar_entrada = enviar_entrada
        self.historico_getter = historico_getter
        self.estado_getter = estado_getter
        self.dashboard_getter = dashboard_getter
        self.resultado_acao_getter = resultado_acao_getter
        self.modo_setter = modo_setter
        self.configuracao_getter = configuracao_getter
        self.configuracao_setter = configuracao_setter
        self.reiniciar_aplicacao = reiniciar_aplicacao
        self.host = "127.0.0.1" if host == "localhost" else host
        self.port = max(0, int(port))
        self.max_message_bytes = max(1_024, int(max_message_bytes))
        self.rate_limit = max(2, int(rate_limit))
        self.rate_window_s = max(1.0, float(rate_window_s))
        self.dashboard_interval_s = max(0.25, float(dashboard_interval_s))
        self.dashboard_getter_timeout_s = max(
            0.02, float(dashboard_getter_timeout_s),
        )
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
        self._dashboard_thread: threading.Thread | None = None
        self._dashboard_source_lock = threading.RLock()
        self._dashboard_source_pending: tuple[
            threading.Thread, dict[str, Any]
        ] | None = None
        self._processo: subprocess.Popen[Any] | None = None
        self._ultimo_estado = ""
        self._ultimo_dashboard = ""
        self._eventos: deque[dict[str, Any]] = deque(maxlen=120)
        self._entradas_lock = threading.RLock()
        self._entradas_pendentes: deque[dict[str, str]] = deque(maxlen=64)

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
        if (
            callable(self.dashboard_getter)
            and (not self._dashboard_thread or not self._dashboard_thread.is_alive())
        ):
            self._dashboard_thread = threading.Thread(
                target=self._publicar_dashboard,
                name="Laylay-Desktop-Dashboard",
                daemon=True,
            )
        self._thread.start()
        if not self._poll_thread.is_alive():
            self._poll_thread.start()
        if self._dashboard_thread and not self._dashboard_thread.is_alive():
            self._dashboard_thread.start()
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
                with self._entradas_lock:
                    self._entradas_pendentes.clear()
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
                dashboard_snapshot: dict[str, Any] | None = None
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
                if callable(self.dashboard_getter):
                    dashboard_snapshot = self._obter_dashboard_seguro()
                    snapshot["dashboard"] = dashboard_snapshot
                if not self._enviar_socket(cliente, snapshot):
                    raise ConnectionError("não foi possível confirmar o snapshot")
                if dashboard_snapshot is not None:
                    self._ultimo_dashboard = self._assinatura_dashboard(
                        dashboard_snapshot,
                    )
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
                pendente = {
                    "id": str(entrada_id),
                    "text": str(msg["text"]),
                    "kind": str(msg.get("kind") or "chat"),
                    "action": str(msg.get("action") or ""),
                    "state": "sending",
                }
                with self._entradas_lock:
                    self._entradas_pendentes.append(pendente)
                try:
                    retorno = self.enviar_entrada(msg["text"])
                    aceito = retorno is not False
                    if not aceito:
                        self._remover_entrada_pendente(str(entrada_id))
                    else:
                        pendente["state"] = "received"
                    self._enviar_socket(cliente, {
                        "type": "input_ack", "id": entrada_id,
                        "accepted": aceito,
                        "message": (
                            "" if aceito
                            else "A entrada canônica recusou o pedido."
                        ),
                    })
                    with self._entradas_lock:
                        ainda_pendente = pendente in self._entradas_pendentes
                    if (
                        aceito and ainda_pendente
                        and pendente["kind"] == "quick_action"
                    ):
                        self._publicar_estado_acao(
                            pendente, "received",
                            "Pedido recebido pela mente canônica",
                        )
                except Exception as erro:
                    self._remover_entrada_pendente(str(entrada_id))
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

    def _resultado_acao_atual(self) -> dict[str, Any]:
        if not callable(self.resultado_acao_getter):
            return {}
        try:
            valor = self.resultado_acao_getter()
            return dict(valor) if isinstance(valor, Mapping) else {}
        except Exception as erro:
            self.log(
                "⚠️ [TERMINAL 3:AÇÃO] resultado indisponível "
                f"| tipo={type(erro).__name__}"
            )
            return {}

    def _selecionar_entrada_pendente(
        self,
        plano: Mapping[str, Any] | None = None,
    ) -> dict[str, str] | None:
        texto_turno = _texto_seguro(dict(plano or {}).get("texto_usuario"), 8_000)
        with self._entradas_lock:
            if not self._entradas_pendentes:
                return None
            if texto_turno:
                for item in self._entradas_pendentes:
                    if item.get("text") == texto_turno:
                        return item
            return self._entradas_pendentes[0]

    def _remover_entrada_pendente(self, entrada_id: str) -> dict[str, str] | None:
        with self._entradas_lock:
            for item in tuple(self._entradas_pendentes):
                if item.get("id") == entrada_id:
                    self._entradas_pendentes.remove(item)
                    return item
        return None

    def _publicar_estado_acao(
        self,
        entrada: Mapping[str, Any],
        estado: str,
        resumo: str,
    ) -> bool:
        estado = str(estado or "")
        if estado not in _ESTADOS_ACAO_RAPIDA:
            return False
        return self._publicar({
            "type": "action_state",
            "id": _texto_seguro(entrada.get("id"), 80),
            "action": _texto_seguro(entrada.get("action"), 48),
            "state": estado,
            "summary": _texto_seguro(resumo, 180),
            "timestamp": time.time(),
        })

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
        plano = self._resultado_acao_atual()
        pendente = self._selecionar_entrada_pendente(plano)
        mensagem_id = (
            str(pendente.get("id") or "") if pendente
            else _texto_seguro(dados.get("mensagem_id"), 96)
        )
        publicado = self._publicar({
            "type": "assistant_message",
            "id": mensagem_id,
            "text": fala,
            "emotion": _texto_seguro(emocao, 32) or "calma",
            "emotion_level": max(1, min(3, int(nivel or 1))),
            "timestamp": time.time(),
        })
        if pendente:
            self._remover_entrada_pendente(str(pendente.get("id") or ""))
            if pendente.get("kind") == "quick_action":
                resultado = classificar_resultado_acao(
                    plano, acao_id=str(pendente.get("action") or ""),
                )
                self._publicar_estado_acao(
                    pendente, resultado["state"], resultado["summary"],
                )
        return publicado

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
            if estado.get("activity") == "executing":
                plano = self._resultado_acao_atual()
                pendente = self._selecionar_entrada_pendente(plano)
                if (
                    pendente
                    and pendente.get("kind") == "quick_action"
                    and pendente.get("state") != "executing"
                ):
                    pendente["state"] = "executing"
                    self._publicar_estado_acao(
                        pendente, "executing", "A mente iniciou a execução",
                    )
            chave = json.dumps(estado, ensure_ascii=False, sort_keys=True)
            agora = time.monotonic()
            if chave != self._ultimo_estado or agora - ultimo_envio >= 4.0:
                self._ultimo_estado = chave
                ultimo_envio = agora
                self._publicar({"type": "state", "heartbeat": True, **estado})

    def _obter_dashboard_seguro(self) -> dict[str, Any]:
        if not callable(self.dashboard_getter) or self._stop.is_set():
            return sanitizar_dashboard_estado({})
        with self._dashboard_source_lock:
            if self._stop.is_set():
                return sanitizar_dashboard_estado({})
            pendente = self._dashboard_source_pending
            if pendente is None:
                caixa: dict[str, Any] = {}

                def executar() -> None:
                    try:
                        caixa["valor"] = self.dashboard_getter()
                    except Exception as erro:
                        caixa["erro_tipo"] = type(erro).__name__

                thread = threading.Thread(
                    target=executar,
                    name="Laylay-Terminal3-Dashboard-Getter",
                    daemon=True,
                )
                self._dashboard_source_pending = (thread, caixa)
                thread.start()
            else:
                thread, caixa = pendente
        thread.join(timeout=self.dashboard_getter_timeout_s)
        if thread.is_alive():
            self.log(
                "⚠️ [TERMINAL 3:DASHBOARD] retrato indisponível "
                "| tipo=TimeoutError"
            )
            return sanitizar_dashboard_estado({})
        with self._dashboard_source_lock:
            if self._dashboard_source_pending == (thread, caixa):
                self._dashboard_source_pending = None
        erro_tipo = str(caixa.get("erro_tipo") or "")
        if erro_tipo:
            # Mensagens de exceções podem carregar caminhos ou conteúdo. Só a
            # classe atravessa o diagnóstico técnico.
            self.log(
                "⚠️ [TERMINAL 3:DASHBOARD] retrato indisponível "
                f"| tipo={erro_tipo}"
            )
            return sanitizar_dashboard_estado({})
        return sanitizar_dashboard_estado(caixa.get("valor"))

    @staticmethod
    def _assinatura_dashboard(dashboard: Mapping[str, Any]) -> str:
        def sem_temporal(valor: Any) -> Any:
            if isinstance(valor, Mapping):
                return {
                    chave: sem_temporal(item)
                    for chave, item in valor.items()
                    if chave not in {"generated_at", "sequence", "observed_at"}
                }
            if isinstance(valor, list):
                return [sem_temporal(item) for item in valor]
            return valor

        return json.dumps(
            sem_temporal(dict(dashboard)),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def _publicar_dashboard(self) -> None:
        ultimo_envio = time.monotonic()
        while not self._stop.wait(self.dashboard_interval_s):
            with self._client_lock:
                conectado = self._client is not None
            if not conectado:
                ultimo_envio = time.monotonic()
                continue
            dashboard = self._obter_dashboard_seguro()
            assinatura = self._assinatura_dashboard(dashboard)
            agora = time.monotonic()
            if assinatura != self._ultimo_dashboard or agora - ultimo_envio >= 10.0:
                enviado = self._publicar({
                    "type": "dashboard_state",
                    "dashboard": dashboard,
                    "timestamp": time.time(),
                })
                if enviado:
                    self._ultimo_dashboard = assinatura
                    ultimo_envio = agora

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
        limite = time.monotonic() + max(0.0, float(timeout_s))
        for thread in (self._thread, self._poll_thread, self._dashboard_thread):
            if thread and thread.is_alive() and thread is not threading.current_thread():
                thread.join(timeout=max(0.0, limite - time.monotonic()))

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
            "dashboard_disponivel": callable(self.dashboard_getter),
            "dashboard_thread_viva": bool(
                self._dashboard_thread and self._dashboard_thread.is_alive()
            ),
            "dashboard_fonte_pendente": bool(
                self._dashboard_source_pending
                and self._dashboard_source_pending[0].is_alive()
            ),
        }


def criar_desktop_bridge_runtime(**kwargs: Any) -> DesktopBridgeRuntime:
    return DesktopBridgeRuntime(**kwargs)

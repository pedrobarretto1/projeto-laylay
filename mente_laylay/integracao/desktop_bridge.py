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
    IDS_ACOES_PAINEL,
    IDS_ACOES_RAPIDAS,
    definicao_acao_terminal,
)
from mente_laylay.integracao.acoes_painel_runtime import ACOES_DIRETAS_PAINEL
from mente_laylay.iot.contratos import ACOES_IOT


TIPOS_CLIENTE = frozenset({
    "hello", "ready", "heartbeat", "input_submit", "mode_set",
    "settings_get", "settings_update", "restart_request",
    "conversations_get", "conversation_create", "conversation_select",
    "conversation_rename", "conversation_delete", "conversation_archive",
    "conversation_unarchive", "conversation_pin",
    "playlist_request",
})
TIPOS_BACKEND = frozenset({
    "snapshot", "input_ack", "assistant_message", "state", "error",
    "mode_state", "settings_state", "settings_result", "restart_result",
    "dashboard_state", "action_state", "music_meter",
    "conversations_state",
    "playlist_result",
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


def sanitizar_resultado_playlist(
    operacao: str, valor: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Defesa da ponte: nem URLs de origem nem caminhos podem voltar à UI."""
    bruto = dict(valor or {})
    base: dict[str, Any] = {
        "ok": bool(bruto.get("ok")),
        "status": _texto_seguro(bruto.get("status"), 48),
    }
    capa = _texto_seguro(bruto.get("artwork_url"), 180)
    if not (
        re.fullmatch(
            r"https://i\.ytimg\.com/vi/[A-Za-z0-9_-]{11}/(?:mqdefault|hqdefault|maxresdefault)\.jpg",
            capa,
        )
        or re.fullmatch(r"laylay-playlist-artwork://[a-f0-9]{24}\.png", capa)
    ):
        capa = ""
    if str(operacao or "") != "detail":
        for chave in ("copied", "added", "duplicated"):
            if chave in bruto:
                base[chave] = bool(bruto.get(chave))
        for chave in (
            "destination_count", "copied_count", "already_present_count",
        ):
            if chave in bruto:
                try:
                    base[chave] = max(0, min(1_000, int(bruto.get(chave) or 0)))
                except (TypeError, ValueError):
                    base[chave] = 0
        if "source_removed" in bruto:
            base["source_removed"] = bruto.get("source_removed") is True
        base["revision"] = _texto_seguro(bruto.get("revision"), 64)
        base["artwork_url"] = capa
        return base
    try:
        total = max(0, min(100_000, int(bruto.get("total") or 0)))
        offset = max(0, int(bruto.get("offset") or 0))
        limite = max(1, min(100, int(bruto.get("limit") or 50)))
    except (TypeError, ValueError):
        total, offset, limite = 0, 0, 50
    itens: list[dict[str, Any]] = []
    for item in list(bruto.get("items") or ())[:100]:
        if not isinstance(item, Mapping):
            continue
        video_id = _texto_seguro(item.get("video_id"), 11)
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            continue
        duracao = item.get("duration_seconds")
        if not isinstance(duracao, (int, float)) or isinstance(duracao, bool) or not 0 < duracao <= 86_400:
            duracao = None
        capa_item = _texto_seguro(item.get("artwork_url"), 180)
        if not re.fullmatch(
            r"https://i\.ytimg\.com/vi/[A-Za-z0-9_-]{11}/mqdefault\.jpg", capa_item,
        ):
            capa_item = ""
        itens.append({
            "video_id": video_id,
            "title": _texto_publico_dashboard(item.get("title"), 180, fallback="Faixa sem título"),
            "channel": _texto_publico_dashboard(item.get("channel"), 120, fallback=""),
            "added_at": _texto_seguro(item.get("added_at"), 10),
            "duration_seconds": duracao,
            "artwork_url": capa_item,
        })
    duracao_total = bruto.get("duration_seconds")
    if not isinstance(duracao_total, (int, float)) or isinstance(duracao_total, bool) or not 0 < duracao_total <= 8_640_000:
        duracao_total = None
    return {
        **base,
        "name": _texto_publico_dashboard(bruto.get("name"), 80, fallback="Playlist"),
        "total": total, "offset": offset, "limit": limite,
        "has_more": bool(bruto.get("has_more")),
        "revision": _texto_seguro(bruto.get("revision"), 64),
        "artwork_url": capa, "duration_seconds": duracao_total,
        "items": itens,
    }


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


_PADRAO_ID_CONVERSA = re.compile(
    r"(?i)^(?:[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-"
    r"[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$"
)


def _id_conversa_seguro(valor: Any, *, obrigatorio: bool = False) -> str:
    identificador = str(valor or "").strip()
    if not identificador and not obrigatorio:
        return ""
    if not _PADRAO_ID_CONVERSA.fullmatch(identificador):
        raise ErroProtocoloDesktop("identificador de conversa inválido")
    return identificador


def sanitizar_conversas(
    conversas: Sequence[Mapping[str, Any]] | None,
    *,
    ativa_id: str = "",
    limite: int = 100,
) -> dict[str, Any]:
    """Projeta somente metadados necessários para a lista local de chats."""
    ativa = _id_conversa_seguro(ativa_id) if ativa_id else ""
    itens: list[dict[str, Any]] = []
    for item in list(conversas or ())[:max(1, min(int(limite), 100))]:
        if not isinstance(item, Mapping):
            continue
        try:
            identificador = _id_conversa_seguro(item.get("id"), obrigatorio=True)
        except ErroProtocoloDesktop:
            continue
        status_bruto = str(item.get("status") or "ativa").casefold().strip()
        if status_bruto not in {"ativa", "arquivada"}:
            continue
        titulo = re.sub(r"\s+", " ", _texto_seguro(item.get("titulo"), 120))
        try:
            quantidade = max(0, min(int(item.get("mensagens") or 0), 100_000))
        except (TypeError, ValueError):
            quantidade = 0
        itens.append({
            "id": identificador,
            "title": titulo or "Nova conversa",
            "updated_at": _texto_seguro(item.get("atualizada_em"), 40),
            "message_count": quantidade,
            "status": (
                "archived" if status_bruto == "arquivada" else "active"
            ),
            "pinned": bool(item.get("fixada", False)),
            "active": identificador == ativa,
        })
    return {"active_id": ativa, "items": itens}


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
    try:
        nivel_microfone = float(bruto.get("microphone_level") or 0.0)
    except (TypeError, ValueError):
        nivel_microfone = 0.0
    if not math.isfinite(nivel_microfone):
        nivel_microfone = 0.0
    return {
        "activity": atividade if atividade in mapa else "idle",
        "activity_label": mapa.get(atividade, "Pronta"),
        "emotion": emocao[:32] or "calma",
        "emotion_level": max(1, min(3, int(bruto.get("emotion_level") or 1))),
        "voice_available": bool(bruto.get("voice_available", False)),
        "microphone_level": max(0.0, min(1.0, nivel_microfone)),
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



# P10.5 — allowlist de especificações públicas do computador.
def _info_sistema_dashboard(
    valor: Any,
) -> dict[str, dict[str, str]]:
    bruto = (
        dict(valor)
        if isinstance(
            valor,
            Mapping,
        )
        else {}
    )

    resultado: dict[
        str,
        dict[str, str],
    ] = {}

    for chave in (
        "os",
        "cpu",
        "gpu",
        "ram",
        "vram",
        "disk",
    ):
        item = (
            dict(
                bruto.get(chave)
                or {}
            )
            if isinstance(
                bruto.get(chave),
                Mapping,
            )
            else {}
        )

        resultado[chave] = {
            "value": _texto_publico_dashboard(
                item.get("value"),
                180,
                fallback="—",
            ),
            "detail": _texto_publico_dashboard(
                item.get("detail"),
                120,
                fallback="",
            ),
        }

    return resultado


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
    musica = dict(bruto.get("music") or {}) if isinstance(
        bruto.get("music"), Mapping,
    ) else {}
    rotinas = dict(bruto.get("routines") or {}) if isinstance(
        bruto.get("routines"), Mapping,
    ) else {}
    iot = dict(bruto.get("iot") or {}) if isinstance(
        bruto.get("iot"), Mapping,
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
    musica_observada = _numero_dashboard(
        musica.get("observed_at"), minimo=0, maximo=9_999_999_999,
    ) or 0.0
    musica_estado = _texto_seguro(musica.get("state"), 24).casefold()
    if musica_estado not in {"playing", "paused", "ended", "unknown"}:
        musica_estado = "unavailable"
    musica_frescor = _frescor_dashboard(
        musica.get("freshness"),
        disponivel=musica_observada > 0 and musica_estado != "unavailable",
    )
    if musica_frescor == "unavailable":
        musica_estado = "unavailable"
    musica_video_id = _texto_seguro(musica.get("video_id"), 11)
    if (
        musica_frescor == "unavailable"
        or not re.fullmatch(r"[A-Za-z0-9_-]{11}", musica_video_id)
    ):
        musica_video_id = ""
    duracao = _numero_dashboard(
        musica.get("duration_seconds"), minimo=0, maximo=86_400,
    ) or 0.0
    posicao = min(
        _numero_dashboard(
            musica.get("position_seconds"), minimo=0, maximo=86_400,
        ) or 0.0,
        duracao if duracao > 0 else 86_400.0,
    )
    def capa_musical_publica(valor: Any) -> str:
        url_capa = _texto_seguro(valor, 180)
        return url_capa if (
            re.fullmatch(
                r"https://i\.ytimg\.com/vi/[A-Za-z0-9_-]{11}/"
                r"(?:mqdefault|hqdefault|maxresdefault)\.jpg",
                url_capa,
            )
            or re.fullmatch(
                r"laylay-playlist-artwork://[a-f0-9]{24}\.png", url_capa,
            )
        ) else ""

    fila_observada = _numero_dashboard(
        musica.get("queue_observed_at"), minimo=0, maximo=9_999_999_999,
    ) or 0.0
    fila_frescor = _frescor_dashboard(
        musica.get("queue_freshness"), disponivel=fila_observada > 0,
    )
    fila_publica: list[dict[str, Any]] = []
    if fila_frescor != "unavailable":
        for item in list(musica.get("queue") or ()):
            if not isinstance(item, Mapping):
                continue
            titulo_fila = _texto_publico_dashboard(
                item.get("title"), 160, fallback="",
            )
            if not titulo_fila:
                continue
            item_id = _texto_seguro(item.get("item_id"), 24)
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", item_id):
                item_id = ""
            item_publico = {
                "title": titulo_fila,
                "channel": _texto_publico_dashboard(
                    item.get("channel"), 100, fallback="",
                ),
                "duration_seconds": _numero_dashboard(
                    item.get("duration_seconds"), minimo=0, maximo=86_400,
                ) or 0.0,
                "artwork_url": capa_musical_publica(item.get("artwork_url")),
            }
            if item_id:
                item_publico["item_id"] = item_id
            fila_publica.append(item_publico)
    catalogo_observado = _numero_dashboard(
        musica.get("catalog_observed_at"), minimo=0, maximo=9_999_999_999,
    ) or 0.0
    catalogo_disponivel = bool(
        musica.get("catalog_available") is True and catalogo_observado > 0,
    )
    catalogo_publico: list[dict[str, Any]] = []
    if catalogo_disponivel:
        for item in list(musica.get("catalog") or ()):
            if not isinstance(item, Mapping):
                continue
            nome_playlist = _texto_publico_dashboard(
                item.get("name"), 80, fallback="",
            )
            if (
                not nome_playlist
                or re.search(
                    r"(?i)(?:[;&|<>]|\b(?:apaga|delete|deleta|remove|exclui|"
                    r"desliga|liga|abre|fecha|envia|manda|executa|roda|"
                    r"formata|reinicia)\b)",
                    nome_playlist,
                )
            ):
                continue
            catalogo_publico.append({
                "name": nome_playlist,
                "count": _inteiro_dashboard(item.get("count"), maximo=10_000),
                "artwork_url": capa_musical_publica(item.get("artwork_url")),
            })
    contexto_musical = (
        dict(musica.get("context_music") or {})
        if isinstance(musica.get("context_music"), Mapping) else {}
    )
    contexto_musical_observado = _numero_dashboard(
        contexto_musical.get("observed_at"), minimo=0, maximo=9_999_999_999,
    ) or 0.0
    contexto_musical_frescor = _frescor_dashboard(
        contexto_musical.get("freshness"),
        disponivel=contexto_musical_observado > 0,
    )
    bases_musicais_validas = {
        "horario_local", "playlist_ativa", "catalogo_real",
        "regra_de_horario", "preferencia_confirmada", "clima_observado",
    }
    contexto_musical_publico = {
        "summary": _texto_publico_dashboard(
            contexto_musical.get("summary"), 220, fallback="",
        ),
        "recommendation": _texto_publico_dashboard(
            contexto_musical.get("recommendation"), 260, fallback="",
        ),
        "basis": [
            base for base in (
                _texto_seguro(item, 32) for item in list(
                    contexto_musical.get("basis") or (),
                )[:8]
            ) if base in bases_musicais_validas
        ],
        "freshness": contexto_musical_frescor,
        "observed_at": contexto_musical_observado,
    }
    if contexto_musical_frescor == "unavailable":
        contexto_musical_publico.update(summary="", recommendation="", basis=[])

    letras = (
        dict(musica.get("lyrics") or {})
        if isinstance(musica.get("lyrics"), Mapping) else {}
    )
    status_letra = _texto_seguro(letras.get("status"), 24).casefold()
    if status_letra not in {
        "idle", "loading", "available", "instrumental", "not_found",
        "error", "rate_limited",
    }:
        status_letra = "error"
    fonte_letra = (
        "lrclib" if _texto_seguro(letras.get("source"), 24).casefold()
        == "lrclib" else ""
    )
    linhas_letra: list[dict[str, Any]] = []
    total_caracteres = 0
    if status_letra == "available":
        for item in list(letras.get("lines") or ())[:200]:
            if not isinstance(item, Mapping):
                continue
            instante = _numero_dashboard(
                item.get("time_seconds"), minimo=0, maximo=86_400,
            )
            texto_linha = _texto_seguro(item.get("text"), 180)
            if instante is None or not texto_linha:
                continue
            total_caracteres += len(texto_linha)
            if total_caracteres > 18_000:
                break
            linhas_letra.append({
                "time_seconds": instante,
                "text": texto_linha,
            })
    texto_simples = ""
    if status_letra == "available" and not linhas_letra:
        texto_simples = str(letras.get("plain_text") or "").replace("\x00", "")
        texto_simples = texto_simples.strip()[:16_000]
    letra_observada = _numero_dashboard(
        letras.get("observed_at"), minimo=0, maximo=9_999_999_999,
    ) or 0.0
    if status_letra not in {"idle", "loading"} and not fonte_letra:
        status_letra = "error"
    if status_letra == "available" and not (linhas_letra or texto_simples):
        status_letra = "not_found"
    letra_publica = {
        "status": status_letra,
        "source": fonte_letra,
        "synced": bool(linhas_letra),
        "track_name": _texto_seguro(letras.get("track_name"), 180),
        "artist_name": _texto_seguro(letras.get("artist_name"), 120),
        "plain_text": texto_simples,
        "lines": linhas_letra,
        "observed_at": letra_observada,
    }
    musica_publica = {
        "title": _texto_publico_dashboard(
            musica.get("title"), 180, fallback="",
        ),
        "channel": _texto_publico_dashboard(
            musica.get("channel"), 120, fallback="",
        ),
        "video_id": musica_video_id,
        "artwork_url": capa_musical_publica(musica.get("artwork_url")),
        "state": musica_estado,
        "position_seconds": posicao,
        "duration_seconds": duracao,
        "playlist": _texto_publico_dashboard(
            musica.get("playlist"), 100, fallback="",
        ),
        "controls_available": bool(
            musica.get("controls_available") is True
            and musica_frescor == "fresh"
        ),
        "volume_percent": _numero_dashboard(
            musica.get("volume_percent"), minimo=0, maximo=100,
        ),
        "player_volume_percent": _numero_dashboard(
            musica.get("player_volume_percent"), minimo=0, maximo=100,
        ),
        "muted": bool(musica.get("muted") is True),
        "replay_available": bool(
            musica.get("replay_available") is True
            and musica_frescor == "fresh"
        ),
        "repeat_enabled": bool(musica.get("repeat_enabled") is True),
        "repeat_available": bool(
            musica.get("repeat_available") is True
            and musica_frescor == "fresh"
        ),
        "shuffle_available": bool(
            musica.get("shuffle_available") is True
            and musica_frescor == "fresh"
        ),
        "audio_output": {
            "name": _texto_publico_dashboard(
                (musica.get("audio_output") or {}).get("name")
                if isinstance(musica.get("audio_output"), Mapping) else "",
                100,
                fallback="",
            ),
            "source": _texto_seguro(
                (musica.get("audio_output") or {}).get("source")
                if isinstance(musica.get("audio_output"), Mapping) else "",
                40,
            ),
            "available": bool(
                isinstance(musica.get("audio_output"), Mapping)
                and musica.get("audio_output", {}).get("available") is True
            ),
            "selected_ref": "",
            "switch_available": False,
            "devices": [],
            "observed_at": 0.0,
        },
        "lights": {
            "configured": bool(
                isinstance(musica.get("lights"), Mapping)
                and musica.get("lights", {}).get("configured") is True
            ),
            "sync_available": bool(
                isinstance(musica.get("lights"), Mapping)
                and musica.get("lights", {}).get("sync_available") is True
            ),
        },
        "freshness": musica_frescor,
        "observed_at": musica_observada,
        "queue": fila_publica,
        "queue_source": (
            _texto_seguro(musica.get("queue_source"), 24)
            if _texto_seguro(musica.get("queue_source"), 24)
            in {"youtube", "laylay_playlist"} else ""
        ),
        "queue_freshness": fila_frescor,
        "queue_observed_at": fila_observada,
        "catalog": catalogo_publico,
        "catalog_available": catalogo_disponivel,
        "catalog_play_available": bool(
            catalogo_disponivel
            and musica.get("catalog_play_available") is True
        ),
        "catalog_observed_at": catalogo_observado,
        "context_music": contexto_musical_publico,
        "lyrics": letra_publica,
    }
    audio_bruto = (
        musica.get("audio_output")
        if isinstance(musica.get("audio_output"), Mapping) else {}
    )
    dispositivos_publicos: list[dict[str, Any]] = []
    for item in list(audio_bruto.get("devices") or ()):
        if not isinstance(item, Mapping):
            continue
        referencia = _texto_seguro(item.get("ref"), 16).casefold()
        nome = _texto_publico_dashboard(item.get("name"), 100, fallback="")
        if (
            nome and re.fullmatch(r"[a-f0-9]{16}", referencia)
            and len(dispositivos_publicos) < 32
        ):
            dispositivos_publicos.append({
                "ref": referencia,
                "name": nome,
                "selected": item.get("selected") is True,
            })
    referencia_selecionada = _texto_seguro(
        audio_bruto.get("selected_ref"), 16,
    ).casefold()
    if not re.fullmatch(r"[a-f0-9]{16}", referencia_selecionada):
        referencia_selecionada = ""
    musica_publica["audio_output"].update({
        "selected_ref": referencia_selecionada,
        "switch_available": bool(
            audio_bruto.get("switch_available") is True and dispositivos_publicos
        ),
        "devices": dispositivos_publicos,
        "observed_at": _numero_dashboard(
            audio_bruto.get("observed_at"), minimo=0, maximo=9_999_999_999,
        ) or 0.0,
    })
    rotinas_observadas = _numero_dashboard(
        rotinas.get("observed_at"), minimo=0, maximo=9_999_999_999,
    ) or 0.0
    rotinas_frescor = _frescor_dashboard(
        rotinas.get("freshness"), disponivel=rotinas_observadas > 0,
    )
    rotinas_publicas: list[dict[str, Any]] = []
    pares_dias = {"seg", "ter", "qua", "qui", "sex", "sab", "dom", "todos"}
    if rotinas_frescor != "unavailable":
        for item in list(rotinas.get("items") or ())[:6]:
            if not isinstance(item, Mapping) or item.get("active") is not True:
                continue
            nome = _texto_memoria_publico_dashboard(
                item.get("name"), 120, fallback="Rotina pessoal",
            )
            horario = _texto_seguro(item.get("time"), 8)
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d|—", horario):
                horario = "—"
            dias = [
                _texto_seguro(dia, 5).casefold()
                for dia in list(item.get("days") or ())[:7]
                if _texto_seguro(dia, 5).casefold() in pares_dias
            ]
            data = _texto_seguro(item.get("date"), 10)
            rotina_publica = {
                "name": nome,
                "time": horario,
                "days": dias,
                "active": True,
                "can_disable": item.get("can_disable") is True,
            }
            if re.fullmatch(
                r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])",
                data,
            ):
                rotina_publica["date"] = data
            rotinas_publicas.append(rotina_publica)
    iot_observado = _numero_dashboard(
        iot.get("observed_at"), minimo=0, maximo=9_999_999_999,
    ) or 0.0
    iot_frescor = _frescor_dashboard(
        iot.get("freshness"), disponivel=iot_observado > 0,
    )
    iot_modo = _texto_seguro(iot.get("mode"), 16).casefold()
    if iot_modo not in {"simulado", "tuya"}:
        iot_modo = "unknown"
    iot_provedor = iot.get("provider_available") is True
    dispositivos_iot: list[dict[str, Any]] = []
    if iot_frescor != "unavailable":
        for item in list(iot.get("devices") or ())[:64]:
            if not isinstance(item, Mapping):
                continue
            nome = _texto_seguro(item.get("name"), 64).casefold()
            tipo = _texto_seguro(item.get("type"), 40).casefold()
            nome_amigavel = _texto_publico_dashboard(
                item.get("display_name"), 100, fallback="",
            )
            ambiente = _texto_publico_dashboard(
                item.get("room"), 60, fallback="",
            )
            if (
                not re.fullmatch(r"[a-z0-9_]{1,64}", nome)
                or not re.fullmatch(r"[a-z0-9_]{1,40}", tipo)
                or not nome_amigavel
                or not ambiente
            ):
                continue
            capacidades = sorted({
                _texto_seguro(capacidade, 40).casefold()
                for capacidade in list(item.get("capabilities") or ())
                if _texto_seguro(capacidade, 40).casefold() in ACOES_IOT
            })
            estado = _texto_seguro(item.get("state"), 16).casefold()
            if estado not in {"on", "off", "offline", "unknown"}:
                estado = "unknown"
            estado_observado = _numero_dashboard(
                item.get("state_observed_at"),
                minimo=0, maximo=9_999_999_999,
            ) or 0.0
            estado_confirmado = bool(
                item.get("state_confirmed") is True
                and estado in {"on", "off"}
                and estado_observado > 0
            )
            brilho_observado = _numero_dashboard(
                item.get("brightness_percent"), minimo=1, maximo=100,
            )
            if not (
                tipo.startswith("lampada")
                and "ajustar_brilho" in capacidades
                and estado_observado > 0
            ):
                brilho_observado = None
            dispositivos_iot.append({
                "name": nome,
                "display_name": nome_amigavel,
                "type": tipo,
                "room": ambiente,
                "capabilities": capacidades,
                "state": estado if estado_confirmado or estado == "offline" else "unknown",
                "state_confirmed": estado_confirmado,
                "state_observed_at": estado_observado,
                "brightness_percent": (
                    int(brilho_observado) if brilho_observado is not None else None
                ),
            })
    iot_controles = bool(
        iot.get("controls_available") is True
        and iot_frescor == "fresh"
        and iot_provedor
        and iot_modo in {"simulado", "tuya"}
        and dispositivos_iot
    )
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
        "music": musica_publica,
        "routines": {
            "items": rotinas_publicas,
            "freshness": rotinas_frescor,
            "observed_at": rotinas_observadas,
        },
        "iot": {
            "configured": bool(
                iot.get("configured") is True and dispositivos_iot
            ),
            "read_only": not iot_controles,
            "controls_available": iot_controles,
            "mode": iot_modo,
            "provider_available": iot_provedor,
            "devices": dispositivos_iot,
            "freshness": iot_frescor,
            "observed_at": iot_observado,
        },
        "system": {
            "info": _info_sistema_dashboard(
                sistema.get("info")
            ),
            "cpu_percent": _metrica_dashboard(
                sistema.get("cpu_percent"), unidade="%", minimo=0, maximo=100,
                max_age_s=5.0,
            ),
            "gpu_percent": _metrica_dashboard(
                sistema.get("gpu_percent"), unidade="%", minimo=0, maximo=100,
                max_age_s=5.0,
            ),
            "ram_percent": _metrica_dashboard(
                sistema.get("ram_percent"), unidade="%", minimo=0, maximo=100,
                max_age_s=5.0,
            ),
            "vram_percent": _metrica_dashboard(
                sistema.get("vram_percent"), unidade="%", minimo=0, maximo=100,
                max_age_s=5.0,
            ),
            "network_percent": _metrica_dashboard(
                sistema.get("network_percent"), unidade="%", minimo=0,
                maximo=100, max_age_s=5.0,
            ),
            "download_mbps": _metrica_dashboard(
                sistema.get("download_mbps"), unidade="Mbps", minimo=0,
                maximo=1_000_000, max_age_s=5.0,
            ),
            "upload_mbps": _metrica_dashboard(
                sistema.get("upload_mbps"), unidade="Mbps", minimo=0,
                maximo=1_000_000, max_age_s=5.0,
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
    if tipo == "playlist_request":
        operacao = _texto_seguro(mensagem.get("operation"), 32).casefold()
        permitidas = {
            "detail", "play_track", "add_url", "copy_track", "move_track",
            "copy_track_many", "move_track_many",
            "remove_track", "set_artwork", "restore_artwork",
        }
        if operacao not in permitidas:
            raise ErroProtocoloDesktop("operação de playlist inválida")
        nome = re.sub(r"\s+", " ", _texto_seguro(mensagem.get("playlist"), 80)).strip()
        if not nome or re.search(r"[;&|<>]", nome):
            raise ErroProtocoloDesktop("playlist inválida")
        resultado = {
            "type": tipo, "id": _texto_seguro(mensagem.get("id"), 80),
            "operation": operacao, "playlist": nome,
        }
        if operacao == "detail":
            resultado["query"] = re.sub(r"\s+", " ", _texto_seguro(mensagem.get("query"), 120))
            try:
                resultado["offset"] = max(0, int(mensagem.get("offset") or 0))
                resultado["limit"] = max(1, min(100, int(mensagem.get("limit") or 50)))
            except (TypeError, ValueError) as erro:
                raise ErroProtocoloDesktop("paginação inválida") from erro
        if operacao in {
            "play_track", "copy_track", "move_track", "copy_track_many",
            "move_track_many", "remove_track",
        }:
            video_id = _texto_seguro(mensagem.get("video_id"), 11)
            revisao = _texto_seguro(mensagem.get("revision"), 64)
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id) or not revisao:
                raise ErroProtocoloDesktop("identidade da faixa inválida")
            resultado.update(video_id=video_id, revision=revisao)
        if operacao in {"copy_track", "move_track"}:
            destino = re.sub(r"\s+", " ", _texto_seguro(mensagem.get("destination"), 80)).strip()
            if not destino or re.search(r"[;&|<>]", destino):
                raise ErroProtocoloDesktop("playlist de destino inválida")
            resultado["destination"] = destino
        if operacao in {"copy_track_many", "move_track_many"}:
            destinos_brutos = mensagem.get("destinations")
            if not isinstance(destinos_brutos, list) or not 1 <= len(destinos_brutos) <= 1_000:
                raise ErroProtocoloDesktop("playlists de destino inválidas")
            destinos: list[str] = []
            vistos: set[str] = set()
            for bruto in destinos_brutos:
                destino = re.sub(
                    r"\s+", " ", _texto_seguro(bruto, 80),
                ).strip()
                chave = destino.casefold()
                if not destino or re.search(r"[;&|<>]", destino):
                    raise ErroProtocoloDesktop("playlist de destino inválida")
                if chave not in vistos:
                    vistos.add(chave)
                    destinos.append(destino)
            if not destinos:
                raise ErroProtocoloDesktop("playlists de destino inválidas")
            resultado["destinations"] = destinos
        if operacao == "add_url":
            url = _texto_seguro(mensagem.get("url"), 500)
            if not re.fullmatch(
                r"https://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[A-Za-z0-9_-]{11}(?:[&#?].*)?",
                url,
            ):
                raise ErroProtocoloDesktop("URL do YouTube inválida")
            resultado["url"] = url
        if operacao in {"set_artwork", "restore_artwork"}:
            resultado["revision"] = _texto_seguro(mensagem.get("revision"), 64)
            if not resultado["revision"]:
                raise ErroProtocoloDesktop("revisão ausente")
        if operacao == "set_artwork":
            caminho = _texto_seguro(mensagem.get("path"), 1_000)
            if not caminho:
                raise ErroProtocoloDesktop("capa ausente")
            resultado["path"] = caminho
        return resultado
    if tipo == "input_submit":
        texto = _texto_seguro(mensagem.get("text"), 8_000)
        if not texto:
            raise ErroProtocoloDesktop("entrada vazia")
        tipo_entrada = _texto_seguro(mensagem.get("kind"), 24).casefold() or "chat"
        if tipo_entrada not in {"chat", "quick_action", "panel_action"}:
            raise ErroProtocoloDesktop("origem da entrada inválida")
        acao_id = _texto_seguro(mensagem.get("action"), 48)
        if tipo_entrada == "quick_action" and acao_id not in IDS_ACOES_RAPIDAS:
            raise ErroProtocoloDesktop("ação rápida inválida")
        if tipo_entrada == "panel_action" and acao_id not in IDS_ACOES_PAINEL:
            raise ErroProtocoloDesktop("ação de painel inválida")
        payload: dict[str, Any] = {}
        if tipo_entrada == "panel_action":
            bruto_payload = mensagem.get("payload", {})
            if not isinstance(bruto_payload, Mapping):
                raise ErroProtocoloDesktop("parâmetros da ação de painel inválidos")
            permitidos_por_acao = {
                "media_toggle": {"command"},
                "playlist_play": {"playlist"},
                "playlist_shuffle": {"playlist"},
                "queue_play": {"item_id", "queue_index", "queue_source"},
                "volume_set": {"level"},
                "audio_output_select": {"device_ref"},
                "iot_status": {"device"},
                "iot_power": {"device", "state"},
                "iot_brightness": {"device", "value"},
                "routine_cancel": {"name"},
            }
            permitidos = permitidos_por_acao.get(acao_id, set())
            if set(bruto_payload) - permitidos:
                raise ErroProtocoloDesktop("parâmetros extras na ação de painel")
            if "command" in permitidos:
                comando = _texto_seguro(bruto_payload.get("command"), 12).casefold()
                if not comando:
                    comando = (
                        "pause" if texto.casefold().startswith("pausa") else
                        "play" if texto.casefold().startswith(("continua", "retoma"))
                        else ""
                    )
                if comando not in {"play", "pause"}:
                    raise ErroProtocoloDesktop("controle de reprodução inválido")
                payload["command"] = comando
            if "playlist" in permitidos:
                playlist = re.sub(
                    r"\s+", " ", _texto_seguro(bruto_payload.get("playlist"), 80)
                ).strip()
                if not playlist:
                    playlist = re.sub(
                        r"(?i)^toca\s+a\s+playlist\s+|\s+em\s+modo\s+aleat[oó]rio$",
                        "", texto,
                    ).strip()[:80]
                if not playlist or re.search(r"[;&|<>]", playlist):
                    raise ErroProtocoloDesktop("playlist da ação inválida")
                payload["playlist"] = playlist
            if "level" in permitidos:
                nivel = bruto_payload.get("level")
                if nivel is None:
                    encontrado = re.search(r"\b(\d{1,3})\b", texto)
                    nivel = int(encontrado.group(1)) if encontrado else None
                if isinstance(nivel, bool):
                    raise ErroProtocoloDesktop("nível de volume inválido")
                try:
                    nivel = int(nivel)
                except (TypeError, ValueError) as erro:
                    raise ErroProtocoloDesktop("nível de volume inválido") from erro
                if not 0 <= nivel <= 100:
                    raise ErroProtocoloDesktop("nível de volume inválido")
                payload["level"] = nivel
            if "item_id" in permitidos:
                item_id = _texto_seguro(bruto_payload.get("item_id"), 24)
                if not re.fullmatch(r"[A-Za-z0-9_-]{11}", item_id):
                    raise ErroProtocoloDesktop("item da fila inválido")
                origem_fila = _texto_seguro(
                    bruto_payload.get("queue_source"), 24,
                ).casefold() or "youtube"
                if origem_fila not in {"youtube", "laylay_playlist"}:
                    raise ErroProtocoloDesktop("origem da fila inválida")
                indice = bruto_payload.get("queue_index")
                if isinstance(indice, bool):
                    raise ErroProtocoloDesktop("posição da fila inválida")
                try:
                    indice = int(indice)
                except (TypeError, ValueError) as erro:
                    raise ErroProtocoloDesktop("posição da fila inválida") from erro
                limite = 999 if origem_fila == "laylay_playlist" else 7
                if not 0 <= indice <= limite:
                    raise ErroProtocoloDesktop("posição da fila inválida")
                payload.update(item_id=item_id, queue_index=indice)
                if "queue_source" in bruto_payload:
                    payload["queue_source"] = origem_fila
            if "device_ref" in permitidos:
                referencia_dispositivo = _texto_seguro(
                    bruto_payload.get("device_ref"), 16,
                ).casefold()
                if not re.fullmatch(r"[a-f0-9]{16}", referencia_dispositivo):
                    raise ErroProtocoloDesktop("saída de áudio inválida")
                payload["device_ref"] = referencia_dispositivo
            if "device" in permitidos:
                dispositivo = _texto_seguro(
                    bruto_payload.get("device"), 64,
                ).casefold()
                if not re.fullmatch(r"[a-z0-9_]+", dispositivo):
                    raise ErroProtocoloDesktop("dispositivo IoT inválido")
                payload["device"] = dispositivo
            if "state" in permitidos:
                estado_iot = _texto_seguro(
                    bruto_payload.get("state"), 8,
                ).casefold()
                if estado_iot not in {"on", "off"}:
                    raise ErroProtocoloDesktop("estado IoT inválido")
                payload["state"] = estado_iot
            if "value" in permitidos:
                valor_iot = bruto_payload.get("value")
                if isinstance(valor_iot, bool):
                    raise ErroProtocoloDesktop("valor IoT inválido")
                try:
                    valor_iot = int(valor_iot)
                except (TypeError, ValueError) as erro:
                    raise ErroProtocoloDesktop("valor IoT inválido") from erro
                if not 1 <= valor_iot <= 100:
                    raise ErroProtocoloDesktop("valor IoT inválido")
                payload["value"] = valor_iot
            if "name" in permitidos:
                nome_rotina = re.sub(
                    r"\s+", " ", _texto_seguro(bruto_payload.get("name"), 80),
                ).strip()
                if not nome_rotina or re.search(r"[;&|<>]", nome_rotina):
                    raise ErroProtocoloDesktop("rotina inválida")
                payload["name"] = nome_rotina
        if tipo_entrada == "chat":
            acao_id = ""
        return {
            "type": tipo,
            "text": texto,
            "id": _texto_seguro(mensagem.get("id"), 80),
            "kind": tipo_entrada,
            "action": acao_id,
            "payload": payload,
            "conversation_id": _id_conversa_seguro(
                mensagem.get("conversation_id"),
            ),
        }
    if tipo in {
        "conversations_get", "conversation_create", "conversation_select",
        "conversation_rename", "conversation_delete", "conversation_archive",
        "conversation_unarchive", "conversation_pin",
    }:
        conversa_id = ""
        if tipo in {
            "conversation_select", "conversation_rename", "conversation_delete",
            "conversation_archive", "conversation_unarchive", "conversation_pin",
        }:
            conversa_id = _id_conversa_seguro(
                mensagem.get("conversation_id"), obrigatorio=True,
            )
        titulo = ""
        if tipo in {"conversation_create", "conversation_rename"}:
            titulo = re.sub(
                r"\s+", " ", _texto_seguro(mensagem.get("title"), 120),
            ).strip()
            if tipo == "conversation_rename" and not titulo:
                raise ErroProtocoloDesktop("título de conversa vazio")
        fixada = False
        if tipo == "conversation_pin":
            if not isinstance(mensagem.get("pinned"), bool):
                raise ErroProtocoloDesktop("estado de fixação inválido")
            fixada = bool(mensagem["pinned"])
        resultado = {
            "type": tipo,
            "id": _texto_seguro(mensagem.get("id"), 80),
            "conversation_id": conversa_id,
            "title": titulo,
        }
        if tipo == "conversation_pin":
            resultado["pinned"] = fixada
        return resultado
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
    definicao = definicao_acao_terminal(acao_id)
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
        executar_acao_painel: Callable[[str, Mapping[str, Any]], Any] | None = None,
        playlist_operacoes: Any | None = None,
        modo_setter: Callable[[bool], Any] | None = None,
        configuracao_getter: Callable[[], Mapping[str, Any]] | None = None,
        configuracao_setter: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        reiniciar_aplicacao: Callable[[], Any] | None = None,
        conversas_getter: Callable[[], Sequence[Mapping[str, Any]]] | None = None,
        conversa_ativa_getter: Callable[[], str] | None = None,
        conversa_criar: Callable[[str], Mapping[str, Any]] | None = None,
        conversa_selecionar: Callable[[str], Mapping[str, Any] | None] | None = None,
        conversa_renomear: Callable[[str, str], bool] | None = None,
        conversa_excluir: Callable[[str], bool] | None = None,
        conversa_arquivar: Callable[[str], bool] | None = None,
        conversa_desarquivar: Callable[[str], bool] | None = None,
        conversa_fixar: Callable[[str, bool], bool] | None = None,
        conversa_nomear_automaticamente: Callable[[str, str], bool] | None = None,
        host: str = "127.0.0.1",
        port: int = 0,
        max_message_bytes: int = 262_144,
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
        self.executar_acao_painel = executar_acao_painel
        self.playlist_operacoes = playlist_operacoes
        self.modo_setter = modo_setter
        self.configuracao_getter = configuracao_getter
        self.configuracao_setter = configuracao_setter
        self.reiniciar_aplicacao = reiniciar_aplicacao
        self.conversas_getter = conversas_getter
        self.conversa_ativa_getter = conversa_ativa_getter
        self.conversa_criar = conversa_criar
        self.conversa_selecionar = conversa_selecionar
        self.conversa_renomear = conversa_renomear
        self.conversa_excluir = conversa_excluir
        self.conversa_arquivar = conversa_arquivar
        self.conversa_desarquivar = conversa_desarquivar
        self.conversa_fixar = conversa_fixar
        self.conversa_nomear_automaticamente = conversa_nomear_automaticamente
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
        # P0_DIAGNOSTICO_TERMINAL_FILHO_V1_20260815
        diretorio_diagnostico = str(ambiente.get("LAYLAY_DIAGNOSTICO_DIR") or "").strip()
        saida_terminal = None
        if diretorio_diagnostico:
            ambiente["PYTHONFAULTHANDLER"] = "1"
            ambiente["PYTHONUNBUFFERED"] = "1"
            try:
                pasta_diagnostico = Path(diretorio_diagnostico).resolve()
                pasta_diagnostico.mkdir(parents=True, exist_ok=True)
                saida_terminal = open(
                    pasta_diagnostico / "terminal_cliente.log", "ab", buffering=0,
                )
            except OSError as erro:
                saida_terminal = None
                self.log(
                    "⚠️ [TERMINAL 2:DIAGNÓSTICO] log do cliente indisponível "
                    f"| tipo={type(erro).__name__}"
                )
        comando = [sys.executable, str(arquivo)]
        try:
            self._processo = subprocess.Popen(
                comando, env=ambiente, cwd=str(arquivo.parents[1]),
                stdout=saida_terminal,
                stderr=subprocess.STDOUT if saida_terminal is not None else None,
            )
            self.log(
                "🖥️ [TERMINAL 2] interface iniciada "
                f"| sessão={self.session_id[:8]} pid={self._processo.pid} "
                f"python={Path(sys.executable).name} arquivo={arquivo}"
            )
            return True
        except Exception as erro:
            self.log(f"⚠️ [TERMINAL 2] interface indisponível: {type(erro).__name__}: {erro}")
            return False
        finally:
            if saida_terminal is not None:
                try:
                    saida_terminal.close()
                except OSError:
                    pass

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

    def _retrato_conversas(self, *, incluir_mensagens: bool) -> dict[str, Any]:
        """Lê o núcleo canônico e devolve uma projeção local limitada."""
        if not callable(self.conversas_getter) or not callable(
            self.conversa_ativa_getter
        ):
            return {"available": False, "active_id": "", "items": []}
        try:
            ativa_id = _id_conversa_seguro(self.conversa_ativa_getter())
            retrato = sanitizar_conversas(
                self.conversas_getter(), ativa_id=ativa_id,
            )
            retrato["available"] = True
            if incluir_mensagens:
                retrato["messages"] = sanitizar_historico(
                    self.historico_getter(),
                )
            return retrato
        except Exception as erro:
            self.log(
                "⚠️ [TERMINAL 2:PONTE] conversas indisponíveis "
                f"| tipo={type(erro).__name__}"
            )
            return {"available": False, "active_id": "", "items": []}

    def _enviar_estado_conversas(
        self,
        cliente: socket.socket,
        *,
        requisicao_id: str,
        acao: str,
        sucesso: bool,
        mensagem: str = "",
        incluir_mensagens: bool = True,
    ) -> bool:
        return self._enviar_socket(cliente, {
            "type": "conversations_state",
            "id": _texto_seguro(requisicao_id, 80),
            "action": _texto_seguro(acao, 40),
            "success": bool(sucesso),
            "message": _texto_seguro(mensagem, 240),
            "conversations": self._retrato_conversas(
                incluir_mensagens=incluir_mensagens,
            ),
        })

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
                if callable(self.conversas_getter):
                    snapshot["conversations"] = self._retrato_conversas(
                        incluir_mensagens=False,
                    )
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
                tipo_entrada = str(msg.get("kind") or "chat")
                acao_entrada = str(msg.get("action") or "")
                acao_direta = bool(
                    tipo_entrada == "panel_action"
                    and acao_entrada in ACOES_DIRETAS_PAINEL
                    and callable(self.executar_acao_painel)
                )
                conversa_ativa_id = (
                    str(self.conversa_ativa_getter() or "").strip()
                    if callable(self.conversa_ativa_getter) else ""
                )
                conversa_solicitada = str(msg.get("conversation_id") or "").strip()
                conversa_criada_automaticamente = False
                gerencia_conversas = bool(
                    callable(self.conversas_getter)
                    and callable(self.conversa_ativa_getter)
                )
                if (
                    gerencia_conversas
                    and not acao_direta
                    and not conversa_ativa_id
                ):
                    try:
                        if conversa_solicitada:
                            if not callable(self.conversa_selecionar) or not bool(
                                self.conversa_selecionar(conversa_solicitada)
                            ):
                                raise RuntimeError("conversa solicitada indisponível")
                        else:
                            if not callable(self.conversa_criar) or not bool(
                                self.conversa_criar("Nova conversa")
                            ):
                                raise RuntimeError("criação de conversa indisponível")
                            conversa_criada_automaticamente = True
                        conversa_ativa_id = (
                            str(self.conversa_ativa_getter() or "").strip()
                            if callable(self.conversa_ativa_getter) else ""
                        )
                    except Exception as erro:
                        self._enviar_socket(cliente, {
                            "type": "input_ack", "id": entrada_id,
                            "accepted": False,
                            "message": (
                                "Não consegui preparar uma conversa para "
                                f"essa mensagem ({type(erro).__name__})."
                            ),
                        })
                        continue
                    if not conversa_ativa_id:
                        self._enviar_socket(cliente, {
                            "type": "input_ack", "id": entrada_id,
                            "accepted": False,
                            "message": "A conversa nova não ficou disponível.",
                        })
                        continue
                conversa_solicitada = str(
                    conversa_solicitada or conversa_ativa_id
                ).strip()
                if (
                    conversa_ativa_id and conversa_solicitada
                    and conversa_solicitada != conversa_ativa_id
                ):
                    self._enviar_socket(cliente, {
                        "type": "input_ack", "id": entrada_id,
                        "accepted": False,
                        "message": (
                            "A conversa mudou antes do envio. Envie novamente "
                            "no chat que está aberto."
                        ),
                    })
                    continue
                pendente = {
                    "id": str(entrada_id),
                    "text": str(msg["text"]),
                    "kind": tipo_entrada,
                    "action": acao_entrada,
                    "state": "sending",
                    "conversation_id": conversa_solicitada,
                }
                if conversa_criada_automaticamente:
                    self._enviar_estado_conversas(
                        cliente,
                        requisicao_id=str(entrada_id),
                        acao="auto_create",
                        sucesso=True,
                        incluir_mensagens=False,
                    )
                if acao_direta:
                    self._enviar_socket(cliente, {
                        "type": "input_ack", "id": entrada_id,
                        "accepted": True, "message": "",
                    })
                    self._publicar_estado_acao(
                        pendente, "received", "Controle recebido", direta=True,
                    )
                    threading.Thread(
                        target=self._executar_acao_painel_direta,
                        args=(pendente, dict(msg.get("payload") or {})),
                        name=f"Laylay-Painel-{pendente['action']}",
                        daemon=True,
                    ).start()
                    continue
                with self._entradas_lock:
                    self._entradas_pendentes.append(pendente)
                try:
                    titulo_alterado = False
                    retorno = self.enviar_entrada(msg["text"])
                    aceito = retorno is not False
                    if not aceito:
                        self._remover_entrada_pendente(str(entrada_id))
                    else:
                        pendente["state"] = "received"
                        if callable(self.conversa_nomear_automaticamente):
                            try:
                                titulo_alterado = bool(
                                    self.conversa_nomear_automaticamente(
                                        conversa_solicitada, str(msg["text"]),
                                    )
                                )
                            except Exception as erro:
                                self.log(
                                    "⚠️ [TERMINAL 2:PONTE] título automático "
                                    "indisponível "
                                    f"| tipo={type(erro).__name__}"
                                )
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
                        and pendente["kind"] in {"quick_action", "panel_action"}
                    ):
                        self._publicar_estado_acao(
                            pendente, "received",
                            "Pedido recebido pela mente canônica",
                        )
                    if aceito and titulo_alterado and callable(self.conversas_getter):
                        self._enviar_estado_conversas(
                            cliente,
                            requisicao_id=str(entrada_id),
                            acao="auto_title",
                            sucesso=True,
                            incluir_mensagens=False,
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
            elif tipo in {
                "conversations_get", "conversation_create",
                "conversation_select", "conversation_rename",
                "conversation_delete", "conversation_archive",
                "conversation_unarchive", "conversation_pin",
            }:
                requisicao_id = str(msg.get("id") or secrets.token_hex(6))
                acao = tipo.removeprefix("conversation_")
                if tipo == "conversations_get":
                    acao = "list"
                sucesso = False
                mensagem_resultado = ""
                try:
                    if tipo == "conversations_get":
                        if not callable(self.conversas_getter):
                            raise RuntimeError("conversas indisponíveis")
                        sucesso = True
                    elif tipo == "conversation_create":
                        if not callable(self.conversa_criar):
                            raise RuntimeError("criação de conversa indisponível")
                        sucesso = bool(self.conversa_criar(msg.get("title") or "Nova conversa"))
                    elif tipo == "conversation_select":
                        if not callable(self.conversa_selecionar):
                            raise RuntimeError("seleção de conversa indisponível")
                        sucesso = bool(self.conversa_selecionar(msg["conversation_id"]))
                    elif tipo == "conversation_rename":
                        if not callable(self.conversa_renomear):
                            raise RuntimeError("renomeação de conversa indisponível")
                        sucesso = bool(self.conversa_renomear(
                            msg["conversation_id"], msg["title"],
                        ))
                    elif tipo == "conversation_delete":
                        if not callable(self.conversa_excluir):
                            raise RuntimeError("exclusão de conversa indisponível")
                        sucesso = bool(self.conversa_excluir(msg["conversation_id"]))
                    elif tipo == "conversation_archive":
                        if not callable(self.conversa_arquivar):
                            raise RuntimeError("arquivamento de conversa indisponível")
                        sucesso = bool(self.conversa_arquivar(
                            msg["conversation_id"],
                        ))
                    elif tipo == "conversation_unarchive":
                        if not callable(self.conversa_desarquivar):
                            raise RuntimeError("restauração de conversa indisponível")
                        sucesso = bool(self.conversa_desarquivar(
                            msg["conversation_id"],
                        ))
                    elif tipo == "conversation_pin":
                        if not callable(self.conversa_fixar):
                            raise RuntimeError("fixação de conversa indisponível")
                        sucesso = bool(self.conversa_fixar(
                            msg["conversation_id"], bool(msg["pinned"]),
                        ))
                    if not sucesso:
                        mensagem_resultado = "A mente não confirmou essa alteração."
                except Exception as erro:
                    mensagem_resultado = (
                        "Não consegui alterar a conversa "
                        f"({type(erro).__name__})."
                    )
                self._enviar_estado_conversas(
                    cliente,
                    requisicao_id=requisicao_id,
                    acao=acao,
                    sucesso=sucesso,
                    mensagem=mensagem_resultado,
                    incluir_mensagens=True,
                )
            elif tipo == "playlist_request":
                requisicao_id = str(msg.get("id") or secrets.token_hex(6))
                operacao = str(msg.get("operation") or "")
                retorno: dict[str, Any]
                try:
                    if self.playlist_operacoes is None:
                        raise RuntimeError("operações de playlist indisponíveis")
                    nome = str(msg.get("playlist") or "")
                    chamadas = {
                        "detail": lambda: self.playlist_operacoes.detalhar_playlist(
                            nome, consulta=msg.get("query", ""),
                            deslocamento=msg.get("offset", 0), limite=msg.get("limit", 50),
                        ),
                        "play_track": lambda: self.playlist_operacoes.tocar_faixa_exata(
                            nome, msg["video_id"], msg["revision"],
                        ),
                        "add_url": lambda: self.playlist_operacoes.adicionar_url_playlist(nome, msg["url"]),
                        "copy_track": lambda: self.playlist_operacoes.copiar_faixa_exata(
                            nome, msg["destination"], msg["video_id"], msg["revision"],
                        ),
                        "move_track": lambda: self.playlist_operacoes.mover_faixa_exata(
                            nome, msg["destination"], msg["video_id"], msg["revision"],
                        ),
                        "copy_track_many": lambda: self.playlist_operacoes.copiar_faixa_multiplas(
                            nome, msg["destinations"], msg["video_id"], msg["revision"],
                        ),
                        "move_track_many": lambda: self.playlist_operacoes.mover_faixa_multiplas(
                            nome, msg["destinations"], msg["video_id"], msg["revision"],
                        ),
                        "remove_track": lambda: self.playlist_operacoes.remover_faixa_exata(
                            nome, msg["video_id"], msg["revision"],
                        ),
                        "set_artwork": lambda: self.playlist_operacoes.definir_capa_playlist(
                            nome, msg["path"], msg["revision"],
                        ),
                        "restore_artwork": lambda: self.playlist_operacoes.restaurar_capa_playlist(
                            nome, msg["revision"],
                        ),
                    }
                    retorno = dict(chamadas[operacao]() or {})
                except Exception as erro:
                    self.log(
                        "⚠️ [TERMINAL 2:PLAYLIST] operação falhou "
                        f"| operação={operacao} tipo={type(erro).__name__}"
                    )
                    retorno = {"ok": False, "status": "operation_failed"}
                self._enviar_socket(cliente, {
                    "type": "playlist_result", "id": requisicao_id,
                    "operation": operacao, "playlist": str(msg.get("playlist") or ""),
                    "result": sanitizar_resultado_playlist(operacao, retorno),
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
        *,
        direta: bool = False,
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
            "direct": bool(direta),
            "timestamp": time.time(),
        })

    def _executar_acao_painel_direta(
        self,
        entrada: Mapping[str, Any],
        payload: Mapping[str, Any],
    ) -> None:
        """Executa um controle fechado sem criar um turno de conversa/LLM."""
        if self._stop.is_set() or not callable(self.executar_acao_painel):
            self._publicar_estado_acao(
                entrada, "failed", "Executor do painel indisponível", direta=True,
            )
            return
        self._publicar_estado_acao(
            entrada, "executing", "Executando controle", direta=True,
        )
        retorno_execucao: Any = False
        try:
            retorno_execucao = self.executar_acao_painel(
                str(entrada.get("action") or ""), dict(payload),
            )
            executou = bool(
                retorno_execucao.get("executou")
                if isinstance(retorno_execucao, Mapping)
                else retorno_execucao
            )
        except Exception as erro:
            self.log(
                "⚠️ [TERMINAL 3:PAINEL] execução falhou "
                f"| ação={entrada.get('action') or '-'} tipo={type(erro).__name__}"
            )
            executou = False
        if isinstance(retorno_execucao, Mapping):
            confirmado = retorno_execucao.get("confirmado")
            estado = (
                "confirmed" if confirmado is True
                else "partial" if executou
                else "failed"
            )
            resumo = _texto_seguro(
                retorno_execucao.get("resumo"), 180,
            ) or (
                "Controle executado" if executou
                else "O controle não foi executado"
            )
        elif executou:
            resultado = classificar_resultado_acao(
                self._resultado_acao_atual(),
                acao_id=str(entrada.get("action") or ""),
            )
            estado = str(resultado.get("state") or "partial")
            resumo = str(resultado.get("summary") or "Controle executado")
            if estado == "failed":
                # Alguns executores confirmam a entrega diretamente e o plano
                # pode ser atualizado um instante depois. Não transformamos
                # execução verdadeira em falha por uma corrida de leitura.
                estado, resumo = "partial", "Controle executado; estado final não observado"
        else:
            estado, resumo = "failed", "O controle não foi executado"
        self._publicar_estado_acao(
            entrada, estado, resumo, direta=True,
        )

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
        proativa = bool(dados.get("proativa"))
        # Uma fala autônoma não responde a nenhum balão do usuário. Associá-la
        # à entrada pendente faria o recibo sumir e a resposta real do turno
        # ficar sem destino.
        pendente = None if proativa else self._selecionar_entrada_pendente(plano)
        mensagem_id = (
            str(pendente.get("id") or "") if pendente
            else _texto_seguro(dados.get("mensagem_id"), 96)
        )
        conversa_id = (
            str(pendente.get("conversation_id") or "") if pendente
            else (
                str(self.conversa_ativa_getter() or "").strip()
                if callable(self.conversa_ativa_getter) else ""
            )
        )
        if proativa and not mensagem_id:
            mensagem_id = f"proativa:{time.time_ns()}"
        publicado = self._publicar({
            "type": "assistant_message",
            "id": mensagem_id,
            "text": fala,
            "emotion": _texto_seguro(emocao, 32) or "calma",
            "emotion_level": max(1, min(3, int(nivel or 1))),
            "proactive": proativa,
            "timestamp": time.time(),
            "conversation_id": conversa_id,
        })
        if pendente:
            self._remover_entrada_pendente(str(pendente.get("id") or ""))
            if pendente.get("kind") in {"quick_action", "panel_action"}:
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

    def publicar_medidor_musica(self, medidor: Mapping[str, Any]) -> bool:
        """Publica somente três bandas já autorizadas, sem refazer dashboard."""
        tab_id = medidor.get("tab_id")
        video_id = str(medidor.get("video_id") or "").strip()
        bruto = medidor.get("levels")
        if (
            not isinstance(tab_id, int)
            or isinstance(tab_id, bool)
            or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id)
            or not isinstance(bruto, list)
            or len(bruto) != 3
        ):
            return False
        try:
            levels = [
                round(max(0.0, min(1.0, float(valor))), 4)
                for valor in bruto
                if not isinstance(valor, bool)
            ]
            energy = round(
                max(0.0, min(1.0, float(medidor.get("energy") or 0.0))), 4,
            )
            observado = max(0.0, float(medidor.get("observed_at") or 0.0))
        except (TypeError, ValueError):
            return False
        if len(levels) != 3:
            return False
        return self._publicar({
            "type": "music_meter",
            "tab_id": tab_id,
            "video_id": video_id,
            "levels": levels,
            "energy": energy,
            "observed_at": observado,
        })

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
                    and pendente.get("kind") in {"quick_action", "panel_action"}
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

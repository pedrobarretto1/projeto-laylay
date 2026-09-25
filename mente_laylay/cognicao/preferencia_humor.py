"""Preferência explícita de humor, limitada por contexto e prazo.

O pedido altera somente a expressão. Não cria autoridade operacional nem
transforma observações de comportamento em perfil pessoal.
"""

from __future__ import annotations

import re
import time
import unicodedata
from datetime import datetime
from typing import Any, Mapping


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(letra for letra in base if not unicodedata.combining(letra))
    return re.sub(r"\s+", " ", base.strip(" .!?"))


def extrair_preferencia_humor(
    texto: str,
    *,
    turno_id: str | int,
    agora: float | None = None,
) -> dict[str, Any]:
    """Reconhece instrução social direta; uma citação ou comando não basta."""
    base = _normalizar(texto)
    padrao = re.fullmatch(
        r"(?:(?:lay|laylay)[, ]+)?"
        r"(pega leve(?: comigo)?|vai com calma(?: comigo)?|"
        r"pode me zoar mais|pode brincar mais comigo)"
        r"(?: (hoje|sempre))?(?: (no jogo|na conversa))?",
        base,
    )
    if not padrao:
        return {}
    pedido, prazo, contexto_texto = padrao.groups()
    direcao = "leve" if pedido.startswith(("pega", "vai")) else "mais_humor"
    contexto = {
        "no jogo": "jogo", "na conversa": "conversa",
    }.get(contexto_texto or "", "geral")
    instante = float(time.time() if agora is None else agora)
    duracao = 86400.0 if prazo == "hoje" else 31536000.0 if prazo == "sempre" else 14400.0
    return {
        "direcao": direcao,
        "contexto": contexto,
        "origem": "usuario_explicito",
        "evidencia_ref": f"turno:{turno_id}:preferencia_humor",
        "inicio_ts": instante,
        "expira_ts": instante + duracao,
        "duravel": prazo == "sempre",
        "autoriza_execucao": False,
    }


def preferencia_humor_ativa(
    estado: Mapping[str, Any] | None,
    *,
    contexto: str = "conversa",
    agora: float | None = None,
) -> dict[str, Any]:
    dados = dict(estado or {})
    instante = float(time.time() if agora is None else agora)
    try:
        inicio = float(dados["inicio_ts"])
        fim = float(dados["expira_ts"])
    except (KeyError, TypeError, ValueError):
        return {}
    if not (
        dados.get("origem") in {"usuario_explicito", "preferencia_aprendida"}
        and dados.get("autoriza_execucao") is False
        and dados.get("direcao") in {"leve", "mais_humor"}
        and dados.get("contexto") in {"geral", contexto}
        and str(dados.get("evidencia_ref") or "").startswith(
            "turno:" if dados.get("origem") == "usuario_explicito" else "aprendizado:"
        )
        and inicio <= instante < fim
    ):
        return {}
    return dados


def selecionar_preferencia_humor(
    preferencias: Mapping[str, Any] | None,
    *,
    contexto: str,
    agora: float | None = None,
) -> dict[str, Any]:
    """Entre escopo específico e geral, prevalece o pedido válido mais recente."""
    estados = dict(preferencias or {})
    candidatas = [
        preferencia_humor_ativa(estados.get(escopo), contexto=contexto, agora=agora)
        for escopo in (contexto, "geral", "atual")
    ]
    return max(candidatas, key=lambda item: float(item.get("inicio_ts") or 0.0))


def reconstruir_preferencia_humor_duravel(
    hipotese: Mapping[str, Any] | None,
    evidencia: Mapping[str, Any] | None,
    *,
    agora: float | None = None,
) -> dict[str, Any]:
    """Reidrata somente preferência ativa de pedido explícito comprovado."""
    dados = dict(hipotese or {})
    prova = dict(evidencia or {})
    valor = dict(dados.get("valor") or {})
    contexto = str(valor.get("contexto") or "")
    chave = str(dados.get("chave") or "")
    try:
        inicio = datetime.fromisoformat(str(prova["criado_em"])).timestamp()
    except (KeyError, TypeError, ValueError, OverflowError, OSError):
        return {}
    instante = float(time.time() if agora is None else agora)
    if not (
        dados.get("status") == "ativa"
        and float(dados.get("confianca") or 0.0) >= 0.90
        and chave == f"personalidade:tolerancia_humor:{contexto}"
        and contexto in {"geral", "jogo", "conversa"}
        and valor.get("direcao") in {"leve", "mais_humor"}
        and prova.get("confirmado_usuario") is True
        and prova.get("origem") == "pedido_explicito_usuario"
        and prova.get("valor") == valor
        and str(prova.get("evidencia") or "").startswith("turno:")
        and inicio <= instante < inicio + 31536000.0
    ):
        return {}
    return {
        "direcao": valor["direcao"],
        "contexto": contexto,
        "origem": "preferencia_aprendida",
        "evidencia_ref": f"aprendizado:{chave}",
        "inicio_ts": inicio,
        "expira_ts": inicio + 31536000.0,
        "duravel": True,
        "autoriza_execucao": False,
    }

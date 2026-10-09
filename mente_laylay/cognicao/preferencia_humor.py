"""Preferência explícita de humor, limitada por contexto e prazo.

O pedido altera somente a expressão. Não cria autoridade operacional nem
transforma observações de comportamento em perfil pessoal.
"""

from __future__ import annotations

import re
import math
import time
import unicodedata
from datetime import datetime
from typing import Any, Mapping
from mente_laylay.cognicao.interpretador_continuidade import (
    qualificar_feedback_humor, solicitacao_feedback_humor,
)


CONTEXTOS_HUMOR = frozenset({"geral", "jogo", "conversa", "comandos"})
PESOS_FEEDBACK_HUMOR = {"correcao": -0.75, "recusa": -0.45,
                       "aceitacao": 0.45, "repeticao": 0.25, "silencio": -0.10}
TTL_TOLERANCIA_HUMOR_S = 14 * 86400.0


def validar_amostra_humor(
    texto: str, tipo: str, identidade: str, fonte: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Confere qualificação e proveniência; não presume um receipt ausente."""
    if not isinstance(fonte, Mapping):
        return {}
    dados = dict(fonte)
    qualificacao = qualificar_feedback_humor(texto)
    silencio = tipo == "silencio"
    if (silencio and texto == "silencio"
        and dados.get("solicitacao_feedback_humor") is True
        and solicitacao_feedback_humor(str(dados.get("texto_solicitacao_humor") or ""))):
        qualificacao = {"alvo_feedback": "humor", "tipo": "silencio", "direcao": "neutro",
                       "evidencia_literal": "silencio"}
    try:
        entrega = float(dados["entrega_ts"])
        observado = float(dados["observado_ts"])
    except (KeyError, ValueError, TypeError, OverflowError):
        return {}
    if not (
        qualificacao and qualificacao == dados.get("feedback_humor")
        and qualificacao["tipo"] == tipo
        and identidade and dados.get("id_entrega") == identidade
        and dados.get("entregue") is True
        and dados.get("contexto_humor") in {"jogo", "conversa", "comandos"}
        and all(str(dados.get(campo) or "").strip() for campo in
                ("dominio", "categoria", "origem_produtor", "alvo"))
        and all(math.isfinite(t) for t in (entrega, observado))
        and entrega > 0
        and ((600 <= observado - entrega <= 3600) if silencio else (0 <= observado - entrega <= 600))
    ):
        return {}
    return qualificacao


def contexto_humor_turno(*, modo_jogo_ativo: bool, operacional: bool = False) -> str:
    """Recebe decisões canônicas do turno; não reinterpreta nem autoriza a entrada."""
    return "comandos" if operacional else "jogo" if modo_jogo_ativo else "conversa"


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
        r"(?: (hoje|sempre))?(?: (no jogo|na conversa|nos comandos))?",
        base,
    )
    if not padrao:
        return {}
    pedido, prazo, contexto_texto = padrao.groups()
    direcao = "leve" if pedido.startswith(("pega", "vai")) else "mais_humor"
    contexto = {
        "no jogo": "jogo", "na conversa": "conversa", "nos comandos": "comandos",
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
    if not isinstance(estado, Mapping):
        return {}
    dados = dict(estado)
    instante = float(time.time() if agora is None else agora)
    try:
        inicio = float(dados["inicio_ts"])
        fim = float(dados["expira_ts"])
    except (KeyError, TypeError, ValueError, OverflowError):
        return {}
    if not (
        all(math.isfinite(valor) for valor in (inicio, fim, instante))
        and contexto in CONTEXTOS_HUMOR
        and dados.get("origem") in {"usuario_explicito", "preferencia_aprendida", "tolerancia_implicita"}
        and dados.get("autoriza_execucao") is False
        and dados.get("direcao") in {"leve", "mais_humor"}
        and dados.get("contexto") in {"geral", contexto}
        and str(dados.get("evidencia_ref") or "").startswith(
            "turno:" if dados.get("origem") == "usuario_explicito" else "aprendizado:"
        )
        and inicio <= instante < fim
    ):
        return {}
    if dados.get("origem") == "tolerancia_implicita":
        refs = dados.get("evidencias_refs")
        if (dados.get("contexto") == "geral" or dados.get("duravel") is not False
            or not isinstance(refs, list)
            or not all(isinstance(r, str) and r.startswith("tolerancia_humor:") for r in refs)
            or len(set(refs)) < 3
            or fim - inicio > TTL_TOLERANCIA_HUMOR_S):
            return {}
    return dados


def selecionar_preferencia_humor(
    preferencias: Mapping[str, Any] | None,
    *,
    contexto: str,
    agora: float | None = None,
) -> dict[str, Any]:
    """Pedido explícito vigente vence inferência; entre pedidos, o mais recente."""
    estados = dict(preferencias) if isinstance(preferencias, Mapping) else {}
    candidatas = [
        preferencia_humor_ativa(estados.get(escopo), contexto=contexto, agora=agora)
        for escopo in (contexto, "geral", "atual", "implicita")
    ]
    return max(candidatas, key=lambda item: (
        bool(item) and item.get("origem") != "tolerancia_implicita",
        float(item.get("inicio_ts") or 0.0),
    ))


def humor_bloqueado_por_preferencia(
    estado: Mapping[str, Any] | None, *, contexto: str = "comandos",
) -> bool:
    """Suspende ornamentação antes da autoria; fatos e autoridade não mudam."""
    dados = dict(estado) if isinstance(estado, Mapping) else {}
    preferencias = dados.get("preferencias_humor_contextuais")
    preferencias = dict(preferencias) if isinstance(preferencias, Mapping) else {}
    return selecionar_preferencia_humor(
        {**preferencias, "atual": dados.get("preferencia_humor_contextual")},
        contexto=contexto,
    ).get("direcao") == "leve"


def reconstruir_preferencia_humor_duravel(
    hipotese: Mapping[str, Any] | None,
    evidencia: Mapping[str, Any] | None,
    *,
    agora: float | None = None,
) -> dict[str, Any]:
    """Reidrata somente preferência ativa de pedido explícito comprovado."""
    if not isinstance(hipotese, Mapping) or not isinstance(evidencia, Mapping):
        return {}
    dados = dict(hipotese)
    prova = dict(evidencia)
    if not isinstance(dados.get("valor"), Mapping):
        return {}
    valor = dict(dados["valor"])
    contexto = str(valor.get("contexto") or "")
    chave = str(dados.get("chave") or "")
    try:
        inicio = datetime.fromisoformat(str(prova["criado_em"])).timestamp()
        confianca = float(dados.get("confianca") or 0.0)
    except (KeyError, TypeError, ValueError, OverflowError, OSError):
        return {}
    instante = float(time.time() if agora is None else agora)
    if not (
        all(math.isfinite(numero) for numero in (inicio, confianca, instante))
        and dados.get("status") == "ativa"
        and 0.90 <= confianca <= 1.0
        and chave == f"personalidade:tolerancia_humor:{contexto}"
        and contexto in CONTEXTOS_HUMOR
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

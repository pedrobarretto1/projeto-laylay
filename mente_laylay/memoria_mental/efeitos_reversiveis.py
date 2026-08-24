"""Recibos canônicos de efeitos reversíveis da Laylay.

Este contrato guarda somente evidência de efeitos que já aconteceram e foram
confirmados. Ele nunca fornece autoridade para executar uma nova ação.
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Mapping


VERSAO_EFEITOS_REVERSIVEIS = 1
MAX_RECIBOS_EFEITOS_REVERSIVEIS = 16


def estado_efeitos_reversiveis_inicial() -> dict[str, Any]:
    return {
        "versao": VERSAO_EFEITOS_REVERSIVEIS,
        "recibos": [],
    }


def _normalizar_alvo(valor: Any) -> str:
    alvo = str(valor or "").strip()
    if not alvo:
        return ""
    try:
        return os.path.normcase(
            os.path.normpath(os.path.expanduser(alvo))
        )
    except (OSError, ValueError):
        return os.path.normcase(alvo)


def _bloco(
    estado_atual: Mapping[str, Any] | None,
) -> dict[str, Any]:
    estado = dict(estado_atual or {})
    bruto = estado.get("efeitos_reversiveis")

    if not isinstance(bruto, Mapping):
        return estado_efeitos_reversiveis_inicial()

    recibos = [
        dict(item)
        for item in list(bruto.get("recibos") or [])
        if isinstance(item, Mapping)
    ]

    return {
        "versao": VERSAO_EFEITOS_REVERSIVEIS,
        "recibos": recibos[-MAX_RECIBOS_EFEITOS_REVERSIVEIS:],
    }


def registrar_resultado_efeito_reversivel(
    estado_atual: Mapping[str, Any] | None,
    *,
    intent: str,
    status: str,
    alvo: str,
    executou: bool | None,
    confirmado: bool | None,
    id_solicitacao: str = "",
    origem: str = "",
    evidencia_confirmacao: str = "",
    agora: Callable[[], float] = time.time,
) -> dict[str, Any]:
    """Publica ou consome recibos a partir do resultado oficial."""

    estado = dict(estado_atual or {})

    intent_norm = str(intent or "").strip().upper()
    status_norm = str(status or "").strip().casefold()
    alvo_limpo = str(alvo or "").strip()
    alvo_norm = _normalizar_alvo(alvo_limpo)

    bloco = _bloco(estado)
    recibos = list(bloco.get("recibos") or [])

    exclusao_confirmada = bool(
        intent_norm in {"CONFIRM_DELETE_ITEM", "DELETE_ITEM"}
        and status_norm == "movido_para_lixeira"
        and executou is True
        and confirmado is True
        and alvo_limpo
        and alvo_norm
    )

    if exclusao_confirmada:
        # O mesmo efeito físico não ganha dois recibos caso o mesmo resultado
        # seja publicado novamente.
        for existente in reversed(recibos):
            if (
                existente.get("ativo") is True
                and existente.get("consumido") is not True
                and str(existente.get("tipo") or "")
                == "exclusao_lixeira"
                and _normalizar_alvo(existente.get("alvo"))
                == alvo_norm
            ):
                return estado

        recibos.append({
            "tipo": "exclusao_lixeira",
            "intent_origem": intent_norm,
            "status_origem": status_norm,
            "reversao_intent": "RESTORE_DELETED_ITEM",
            "alvo": alvo_limpo,
            "executou": True,
            "confirmado": True,
            "id_solicitacao": str(id_solicitacao or "").strip(),
            "origem": str(origem or "").strip(),
            "evidencia_confirmacao": str(
                evidencia_confirmacao or ""
            ).strip(),
            "ts": float(agora()),
            "ativo": True,
            "consumido": False,
        })

        bloco["recibos"] = recibos[
            -MAX_RECIBOS_EFEITOS_REVERSIVEIS:
        ]
        estado["efeitos_reversiveis"] = bloco
        return estado

    restauracao_confirmada = bool(
        intent_norm == "RESTORE_DELETED_ITEM"
        and status_norm == "restaurado"
        and executou is True
        and confirmado is True
        and alvo_limpo
        and alvo_norm
    )

    if restauracao_confirmada:
        momento = float(agora())

        for indice in range(len(recibos) - 1, -1, -1):
            recibo = dict(recibos[indice] or {})

            if (
                recibo.get("ativo") is True
                and recibo.get("consumido") is not True
                and str(
                    recibo.get("reversao_intent") or ""
                ).strip().upper()
                == "RESTORE_DELETED_ITEM"
                and _normalizar_alvo(recibo.get("alvo"))
                == alvo_norm
            ):
                recibo.update({
                    "ativo": False,
                    "consumido": True,
                    "consumido_em": momento,
                    "consumido_por_intent": intent_norm,
                })

                recibos[indice] = recibo
                bloco["recibos"] = recibos[
                    -MAX_RECIBOS_EFEITOS_REVERSIVEIS:
                ]
                estado["efeitos_reversiveis"] = bloco
                break

    return estado


def selecionar_efeito_reversivel(
    estado_atual: Mapping[str, Any] | None,
    *,
    reversao_intent: str,
    ttl_s: float = 300.0,
    agora: Callable[[], float] = time.time,
) -> dict[str, Any]:
    """Seleciona o efeito confirmado mais recente ainda reversível."""

    reversao = str(
        reversao_intent or ""
    ).strip().upper()

    if not reversao:
        return {}

    momento = float(agora())
    bloco = _bloco(estado_atual)

    for bruto in reversed(list(bloco.get("recibos") or [])):
        recibo = dict(bruto or {})

        if (
            recibo.get("ativo") is not True
            or recibo.get("consumido") is True
            or str(
                recibo.get("reversao_intent") or ""
            ).strip().upper()
            != reversao
        ):
            continue

        # Revalida a prova. Um mero referente contextual nunca pode ser
        # promovido a recibo de mutação.
        if str(recibo.get("tipo") or "") != "exclusao_lixeira":
            continue

        if str(
            recibo.get("intent_origem") or ""
        ).strip().upper() not in {
            "CONFIRM_DELETE_ITEM",
            "DELETE_ITEM",
        }:
            continue

        if str(
            recibo.get("status_origem") or ""
        ).strip().casefold() != "movido_para_lixeira":
            continue

        if (
            recibo.get("executou") is not True
            or recibo.get("confirmado") is not True
        ):
            continue

        alvo = str(recibo.get("alvo") or "").strip()
        if not alvo:
            continue

        try:
            idade = momento - float(recibo.get("ts") or 0.0)
        except (TypeError, ValueError):
            continue

        if (
            idade < 0.0
            or idade > max(1.0, float(ttl_s))
        ):
            continue

        return {
            **recibo,
            "idade_s": max(0.0, idade),
        }

    return {}

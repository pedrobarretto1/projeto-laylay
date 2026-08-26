"""Liga uma correção do usuário à interpretação que realmente falhou."""

from __future__ import annotations

import time
from typing import Any, Dict


def abrir_correcao_interpretacao(
    estado: Dict[str, Any] | None,
    texto: str,
    *,
    eh_correcao: bool,
    agora: float | None = None,
) -> Dict[str, Any]:
    atual = dict(estado or {})
    if not eh_correcao:
        return dict(atual.get("correcao_interpretacao_pendente") or {})
    decisao = atual.get("ultima_decisao_semantica") if isinstance(atual.get("ultima_decisao_semantica"), dict) else {}
    return {
        "status": "aguardando_interpretacao_correta",
        "texto_correcao": str(texto or "").strip()[:500],
        "intent_errada": str(decisao.get("intent") or atual.get("ultima_acao_intent") or "").upper().strip(),
        "alvo_errado": str(atual.get("ultima_acao_alvo") or "")[:180],
        "ts": float(agora if agora is not None else time.time()),
    }


def concluir_correcao_interpretacao(
    pendente: Dict[str, Any] | None,
    *,
    intent_correta: str,
    alvo_correto: str = "",
    texto_execucao: str = "",
    agora: float | None = None,
) -> Dict[str, Any]:
    registro = dict(pendente or {})
    if registro.get("status") != "aguardando_interpretacao_correta":
        return registro
    intent = str(intent_correta or "").upper().strip()
    if not intent:
        return registro
    registro.update(
        status="confirmada_por_execucao",
        intent_correta=intent,
        alvo_correto=str(alvo_correto or "")[:180],
        texto_execucao=str(texto_execucao or "")[:500],
        confirmada_ts=float(agora if agora is not None else time.time()),
    )
    return registro

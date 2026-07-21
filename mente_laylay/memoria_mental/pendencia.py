"""Pendencia unica de dialogo aguardando uma resposta do usuario.

Uma pendencia so existe quando a Laylay realmente pronunciou a fala que a
criou. Isso impede que rascunhos, sugestoes internas e respostas descartadas
contaminem o contexto do turno seguinte.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Iterable


def criar_pendencia(
    *,
    origem: str,
    tipo: str,
    dominio: str = "conversa",
    conteudo: str = "",
    opcoes: Iterable[Dict[str, Any]] | None = None,
    resposta_esperada: str = "",
    intencao: str = "",
    ttl_s: float = 300.0,
    foi_falada: bool = True,
) -> Dict[str, Any]:
    agora = time.time()
    falada = bool(foi_falada)
    return {
        "id": uuid.uuid4().hex,
        "origem": str(origem or "").strip(),
        "tipo": str(tipo or "").strip(),
        "dominio": str(dominio or "conversa").strip(),
        "conteudo": str(conteudo or "").strip()[:500],
        "opcoes": [dict(opcao) for opcao in (opcoes or []) if isinstance(opcao, dict)][:8],
        "resposta_esperada": str(resposta_esperada or "").strip(),
        "intencao": str(intencao or "").strip(),
        "criada_em": agora,
        "expira_em": agora + max(1.0, float(ttl_s or 300.0)),
        "foi_falada": falada,
        "status": "ativa" if falada else "rascunho",
    }


def registrar_pendencia(
    estado_atual: Dict[str, Any] | None,
    pendencia: Dict[str, Any] | None,
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    item = dict(pendencia or {})
    if not item.get("tipo") or not item.get("foi_falada"):
        return estado
    item["status"] = "ativa"
    estado["pendencia_atual"] = item
    return estado


def pendencia_ativa(
    estado_atual: Dict[str, Any] | None,
    *,
    dominio: str = "",
    tipos: Iterable[str] = (),
) -> Dict[str, Any] | None:
    item = (estado_atual or {}).get("pendencia_atual")
    if not isinstance(item, dict):
        return None
    if item.get("status") != "ativa" or not item.get("foi_falada"):
        return None
    try:
        if time.time() >= float(item.get("expira_em") or 0.0):
            return None
    except (TypeError, ValueError):
        return None
    if dominio and str(item.get("dominio") or "") != dominio:
        return None
    tipos_aceitos = {str(tipo) for tipo in tipos if tipo}
    if tipos_aceitos and str(item.get("tipo") or "") not in tipos_aceitos:
        return None
    return dict(item)


def limpar_pendencia(
    estado_atual: Dict[str, Any] | None,
    *,
    motivo: str = "resolvida",
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    item = estado.get("pendencia_atual")
    if isinstance(item, dict) and item:
        encerrada = dict(item)
        encerrada["status"] = str(motivo or "resolvida")
        encerrada["encerrada_em"] = time.time()
        estado["ultima_pendencia_encerrada"] = encerrada
    estado["pendencia_atual"] = {}
    return estado

"""Pendencia unica de dialogo aguardando uma resposta do usuario.

Uma pendencia so existe quando a Laylay realmente pronunciou a fala que a
criou. Isso impede que rascunhos, sugestoes internas e respostas descartadas
contaminem o contexto do turno seguinte.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Iterable

from mente_laylay.memoria_mental.continuidade_geral import (
    encerrar_continuidade,
    registrar_evento_continuidade,
)


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
    atual = pendencia_ativa(estado)
    # Algumas falas estruturadas também têm formato de pergunta. Depois que a
    # voz termina, o analisador conversacional pode tentar cadastrá-las outra
    # vez como ``pergunta_aberta`` ou ``promessa_conversacional``. Essa segunda
    # leitura é genérica e não pode apagar a ação concreta que a pergunta
    # original estava oferecendo.
    origens_estruturadas = {
        "observador_area_transferencia",
        "lixeira_laylay",
        "caixa_entrada_pessoal",
        "esclarecimento_operacional",
        "confirmacao_operacional",
        "visao_jogo",
    }
    origens_derivadas_da_fala = {
        "pergunta_aberta",
        "promessa_conversacional",
    }
    if (
        atual
        and str(atual.get("origem") or "") in origens_estruturadas
        and str(item.get("origem") or "") in origens_derivadas_da_fala
    ):
        return estado
    # Uma sugestão espontânea pode acompanhar um esclarecimento, mas não pode
    # roubar a resposta que completará o comando original. A oferta continua
    # disponível em `oferta_pendente` como alternativa secundária.
    if (
        atual
        and str(atual.get("tipo") or "") == "esclarecimento"
        and str(atual.get("origem") or "") == "esclarecimento_operacional"
        and str(item.get("origem") or "") == "oferta_musical"
        and str(atual.get("dominio") or "") == str(item.get("dominio") or "")
    ):
        return estado
    item["status"] = "ativa"
    estado["pendencia_atual"] = item
    estado = registrar_evento_continuidade(
        estado,
        evento="pendencia",
        dominio=str(item.get("dominio") or "conversa"),
        intent=str(item.get("intencao") or ""),
        tipo=str(item.get("tipo") or ""),
        texto=str(item.get("conteudo") or ""),
        status="aguardando_resposta",
        origem=str(item.get("origem") or ""),
        ttl_s=max(1.0, float(item.get("expira_em") or time.time()) - time.time()),
    )
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
        estado = encerrar_continuidade(
            estado,
            dominio=str(item.get("dominio") or "conversa"),
            motivo=str(motivo or "resolvida"),
        )
    estado["pendencia_atual"] = {}
    return estado

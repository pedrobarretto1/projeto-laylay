"""Regras declarativas de validade do contexto efemero da Laylay."""

from __future__ import annotations

import time
from typing import Any, Dict


POLITICAS_CONTEXTO: Dict[str, Dict[str, Any]] = {
    "pergunta_aberta": {"ts": "pergunta_aberta_ts", "ttl_s": 120.0, "prefixos": ("pergunta_aberta_",)},
    "promessa": {"ts": "ultima_promessa_ts", "ttl_s": 180.0, "prefixos": ("ultima_promessa_",)},
    "oferta_musical": {"objeto": "oferta_pendente", "ts_interno": "ts", "ttl_s": 300.0},
    "alvo_corrigido": {"ts": "alvo_corrigido_ts", "ttl_s": 120.0, "campos": ("alvo_corrigido", "alvo_corrigido_ts")},
    "estrutura_arquivo": {"ts": "ultima_estrutura_arquivo_ts", "ttl_s": 900.0, "prefixos": ("ultima_estrutura_arquivo_",)},
    "foco_conversacional": {"ts": "foco_conversacional_ts", "ttl_s": 480.0, "prefixos": ("foco_conversacional_",)},
    "foco_operacional": {"ts": "foco_operacional_ts", "ttl_s": 300.0, "prefixos": ("foco_operacional_",)},
    "topico_explicito": {"ts": "topico_explicito_ts", "ttl_s": 480.0, "prefixos": ("topico_explicito_",)},
    "ultimo_resumo_pagina": {"objeto": "ultimo_resumo_pagina", "ts_interno": "ts", "ttl_s": 600.0},
    "capacidade_futura": {"objeto": "capacidade_futura", "ts_interno": "ts", "ttl_s": 600.0},
}


def _expirou(ts: Any, ttl_s: float, agora: float) -> bool:
    try:
        instante = float(ts or 0.0)
    except (TypeError, ValueError):
        return True
    return bool(instante and agora - instante > ttl_s)


def _limpar_regra(estado: Dict[str, Any], regra: Dict[str, Any]) -> None:
    campos = set(regra.get("campos") or ())
    prefixos = tuple(regra.get("prefixos") or ())
    campos.update(chave for chave in estado if any(chave.startswith(prefixo) for prefixo in prefixos))
    for campo in campos:
        valor = estado.get(campo)
        estado[campo] = 0.0 if campo.endswith("_ts") else {} if isinstance(valor, dict) else ""


def aplicar_ciclo_vida_contexto(
    estado_atual: Dict[str, Any] | None,
    *,
    agora: float | None = None,
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    instante = float(agora if agora is not None else time.time())
    expirados: list[str] = []

    pendencia = estado.get("pendencia_atual")
    if isinstance(pendencia, dict) and pendencia:
        try:
            pendencia_expirada = instante >= float(pendencia.get("expira_em") or 0.0)
        except (TypeError, ValueError):
            pendencia_expirada = True
        if pendencia_expirada:
            encerrada = dict(pendencia)
            encerrada.update(status="expirada", encerrada_em=instante)
            estado["ultima_pendencia_encerrada"] = encerrada
            estado["pendencia_atual"] = {}
            expirados.append("pendencia_atual")

    for nome, regra in POLITICAS_CONTEXTO.items():
        objeto = str(regra.get("objeto") or "")
        if objeto:
            conteudo = estado.get(objeto)
            ts_interno = conteudo.get(str(regra.get("ts_interno") or "ts")) if isinstance(conteudo, dict) else None
            if isinstance(conteudo, dict) and conteudo and (
                not ts_interno or _expirou(ts_interno, float(regra["ttl_s"]), instante)
            ):
                estado[objeto] = {}
                expirados.append(nome)
            continue
        chave_ts = str(regra.get("ts") or "")
        if _expirou(estado.get(chave_ts), float(regra["ttl_s"]), instante):
            _limpar_regra(estado, regra)
            expirados.append(nome)

    focos = dict(estado.get("focos_por_dominio") or {})
    focos_validos = {
        dominio: foco for dominio, foco in focos.items()
        if isinstance(foco, dict) and not _expirou(foco.get("ts"), 900.0, instante)
    }
    if focos_validos != focos:
        estado["focos_por_dominio"] = focos_validos
        expirados.append("focos_por_dominio")
    estado["contextos_expirados_ultimo_ciclo"] = expirados
    estado["ciclo_vida_contexto_ts"] = instante
    return estado

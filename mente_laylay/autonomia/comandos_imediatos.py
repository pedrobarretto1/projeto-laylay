"""Camada de comandos imediatos da Laylay.

Esta camada roda depois do pre-fluxo de conversa e antes da conversa livre da
IA. Ela tenta resolver comandos praticos sem competir com o fluxo social.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict
from mente_laylay.autonomia.pre_fluxo_contextual import (
    analisar_intencao_com_porteiro,
    processar_execucao_pratica_precoce,
    texto_eh_conversa_social_sem_comando,
)


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def processar_comandos_imediatos(ctx: Dict[str, Any], texto: str) -> bool:
    normalizar = _get(ctx, "_normalizar_texto_com_apelidos")
    refinar_contexto_mental = _get(ctx, "_refinar_contexto_mental")
    contexto_mental_ja_refinado = bool(_get(ctx, "_contexto_mental_ja_refinado", False))
    processar_comandos_em_cadeia = _get(ctx, "processar_comandos_em_cadeia")
    executar_intencao = _get(ctx, "executar_intencao")
    registrar_resultado_execucao = _get(ctx, "_registrar_resultado_execucao")
    falar_falha_contextual = _get(ctx, "_falar_falha_contextual")
    ws_loop = _get(ctx, "ws_loop")
    resumir_pagina_ou_video = _get(ctx, "resumir_pagina_ou_video")
    falar_com_lipsync = _get(ctx, "falar_com_lipsync")

    t = normalizar((texto or "").strip()) if callable(normalizar) else str(texto or "").strip()
    if not t:
        return False

    def _log(etapa: str, detalhe: str = "") -> None:
        extra = f" | {detalhe}" if detalhe else ""
        print(f"🧭 [IMEDIATO] {etapa}{extra}")

    if texto_eh_conversa_social_sem_comando(ctx, t):
        _log("ignorado_por_conversa")
        return False

    if callable(refinar_contexto_mental) and not contexto_mental_ja_refinado:
        refinar_contexto_mental(t)

    if callable(processar_comandos_em_cadeia) and processar_comandos_em_cadeia(t, "imediato"):
        _log("comando_em_cadeia")
        return True

    try:
        ok_pratico, nome_pratico = processar_execucao_pratica_precoce(ctx, t, origem="imediato")
    except Exception as e:
        print(f"⚠️ [IMEDIATO] falha na execução prática compartilhada: {e}")
        return False
    if ok_pratico:
        _log(nome_pratico or "execucao_pratica")
        return True

    status_analise, resultado = analisar_intencao_com_porteiro(ctx, t)
    if status_analise == "evitar":
        _log("sem_sinal_pratico", "seguindo como conversa")
        return False
    if status_analise in {"vazio", "sem_analisador"}:
        _log(status_analise)
        return False
    if status_analise == "falha":
        _log("falha_entendimento_llm")
        if callable(falar_falha_contextual):
            falar_falha_contextual("entendimento", t)
        return True
    if status_analise == "sem_intencao":
        _log("sem_intencao_llm")
        return False
    if not isinstance(resultado, dict):
        return False

    if resultado.get("intent") == "RESUMIR_PAGINA":
        _log("llm_resumir_pagina")
        if ws_loop and callable(resumir_pagina_ou_video):
            asyncio.run_coroutine_threadsafe(resumir_pagina_ou_video(), ws_loop)
        elif callable(falar_com_lipsync):
            falar_com_lipsync("Pedro, o servidor WebSocket não está ativo. Não consigo resumir a página.", "irritada", 2)
        return True

    try:
        _log("llm_intencao", str(resultado.get("intent") or ""))
        executou = bool(executar_intencao(resultado, t)) if callable(executar_intencao) else False
        if callable(registrar_resultado_execucao):
            registrar_resultado_execucao(resultado, t, executou, origem="imediato_llm")
        return True
    except Exception:
        alvo_falha = str(
            (resultado.get("params") or {}).get("nome_app")
            or (resultado.get("params") or {}).get("nome_playlist")
            or (resultado.get("params") or {}).get("query")
            or (resultado.get("params") or {}).get("url")
            or (resultado.get("params") or {}).get("alvo")
            or ""
        ).strip()
        if callable(falar_falha_contextual):
            falar_falha_contextual("execucao", t, detalhe=alvo_falha)
        return True

"""Camada de comandos imediatos da Laylay.

Esta camada roda depois do pre-fluxo de conversa e antes da conversa livre da
IA. Ela tenta resolver comandos praticos sem competir com o fluxo social.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def processar_comandos_imediatos(ctx: Dict[str, Any], texto: str) -> bool:
    normalizar = _get(ctx, "_normalizar_texto_com_apelidos")
    texto_social_curto = _get(ctx, "_texto_social_curto")
    texto_conversa_casual_sem_acao = _get(ctx, "_texto_conversa_casual_sem_acao")
    texto_tem_comando_explicito = _get(ctx, "_texto_tem_comando_explicito")
    refinar_contexto_mental = _get(ctx, "_refinar_contexto_mental")
    resolver_comando_contextual_forcado = _get(ctx, "_resolver_comando_contextual_forcado")
    responder_contexto_janela_indisponivel = _get(ctx, "_responder_contexto_janela_indisponivel")
    processar_comandos_em_cadeia = _get(ctx, "processar_comandos_em_cadeia")
    processar_comando_deterministico = _get(ctx, "processar_comando_deterministico")
    interpretar_comando_local_rapido = _get(ctx, "interpretar_comando_local_rapido")
    analisar_intencao = _get(ctx, "analisar_intencao")
    executar_intencao = _get(ctx, "executar_intencao")
    registrar_resultado_execucao = _get(ctx, "_registrar_resultado_execucao")
    registrar_autoaprimoramento = _get(ctx, "_registrar_autoaprimoramento")
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

    if (
        (callable(texto_social_curto) and texto_social_curto(t))
        or (callable(texto_conversa_casual_sem_acao) and texto_conversa_casual_sem_acao(t))
    ) and not (
        callable(texto_tem_comando_explicito) and texto_tem_comando_explicito(t)
    ):
        _log("ignorado_por_conversa")
        return False

    if callable(refinar_contexto_mental):
        refinar_contexto_mental(t)

    comando_contextual = (
        resolver_comando_contextual_forcado(t)
        if callable(resolver_comando_contextual_forcado)
        else None
    )
    if comando_contextual:
        try:
            rota = str(comando_contextual.get("_rota_contextual") or "GERAL").upper()
            intent_limpo = dict(comando_contextual)
            intent_limpo.pop("_rota_contextual", None)
            _log(f"continuidade_{rota.lower()}", str(intent_limpo.get("intent") or ""))
            print(f"⚡ [ROTEADOR CONTEXTO-{rota} [imediato]] {intent_limpo}")
            executou = bool(executar_intencao(intent_limpo, t)) if callable(executar_intencao) else False
            if callable(registrar_resultado_execucao):
                registrar_resultado_execucao(intent_limpo, t, executou, origem=f"contexto_{rota.lower()}")
            if executou and callable(registrar_autoaprimoramento):
                registrar_autoaprimoramento(intent_limpo, t, True, contexto=f"continuidade contextual de {rota.lower()}", origem="imediato")
            return True
        except Exception as e:
            print(f"⚠️ [CONTEXTO-UNIFICADO] falha ao executar: {e}")
            return False

    if callable(responder_contexto_janela_indisponivel) and responder_contexto_janela_indisponivel(t):
        _log("janela_indisponivel")
        return True

    if callable(processar_comandos_em_cadeia) and processar_comandos_em_cadeia(t, "imediato"):
        _log("comando_em_cadeia")
        return True

    if callable(processar_comando_deterministico) and processar_comando_deterministico(t, "imediato"):
        _log("comando_deterministico")
        return True

    comando_local = interpretar_comando_local_rapido(t) if callable(interpretar_comando_local_rapido) else None
    if comando_local:
        try:
            _log("comando_local_rapido", str(comando_local.get("intent") or ""))
            executou = bool(executar_intencao(comando_local, t)) if callable(executar_intencao) else False
            if callable(registrar_resultado_execucao):
                registrar_resultado_execucao(comando_local, t, executou, origem="comando_local_rapido")
            if executou and callable(registrar_autoaprimoramento):
                registrar_autoaprimoramento(comando_local, t, True, contexto="comando local rapido", origem="imediato")
            return True
        except Exception as e:
            print(f"⚠️ [FOCO LOCAL] falha ao executar comando local: {e}")
            return False

    try:
        resultado = analisar_intencao(t) if callable(analisar_intencao) else None
    except Exception:
        resultado = None
    if not isinstance(resultado, dict):
        _log("falha_entendimento_llm")
        if callable(falar_falha_contextual):
            falar_falha_contextual("entendimento", t)
        return True
    if str(resultado.get("intent") or "").upper().strip() in {"", "NONE", "NENHUM"}:
        _log("sem_intencao_llm")
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

"""Camada de comandos imediatos da Laylay.

Esta camada roda depois do pre-fluxo de conversa e antes da conversa livre da
IA. Ela tenta resolver comandos praticos sem competir com o fluxo social.
"""

from __future__ import annotations

import asyncio
import unicodedata
from typing import Any, Callable, Dict
from mente_laylay.autonomia.pre_fluxo_contextual import (
    analisar_intencao_com_porteiro,
    processar_execucao_pratica_precoce,
    texto_eh_conversa_social_sem_comando,
)


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def texto_pede_resumo_pagina(texto: str) -> bool:
    t = str(texto or "").strip().lower()
    t = "".join(ch for ch in unicodedata.normalize("NFD", t) if unicodedata.category(ch) != "Mn")
    alvos = ("pagina", "site", "video", "aba")
    pedidos = ("resume", "resuma", "resumir", "explica", "explique", "o que essa", "o que esta")
    return any(alvo in t for alvo in alvos) and any(pedido in t for pedido in pedidos)


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
    extrair_acao_agendada = _get(ctx, "_extrair_acao_agendada_local")

    t = normalizar((texto or "").strip()) if callable(normalizar) else str(texto or "").strip()
    if not t:
        return False

    def _log(etapa: str, detalhe: str = "") -> None:
        extra = f" | {detalhe}" if detalhe else ""
        print(f"🧭 [IMEDIATO] {etapa}{extra}")

    mente = _get(ctx, "mente_integrada_estado", {})
    turno = mente.get("turno_atual") if isinstance(mente, dict) else {}
    modalidade = str((turno or {}).get("modalidade_geral") or (turno or {}).get("modalidade") or "").lower()
    if isinstance(turno, dict) and turno and (
        turno.get("requer_esclarecimento")
        or (
            modalidade in {"conversa", "pergunta", "deliberacao", "correcao", "reacao"}
            and not turno.get("autoriza_execucao")
        )
    ):
        _log(
            "bloqueado_pelo_arbitro",
            str(turno.get("motivo_decisao") or turno.get("motivo") or modalidade),
        )
        return False

    if texto_pede_resumo_pagina(t):
        _log("resumir_pagina_direto")
        if ws_loop and callable(resumir_pagina_ou_video):
            asyncio.run_coroutine_threadsafe(resumir_pagina_ou_video(), ws_loop)
        elif callable(falar_com_lipsync):
            falar_com_lipsync("O navegador não está conectado agora, então não consigo ler essa página.", "irritada", 2)
        return True

    if texto_eh_conversa_social_sem_comando(ctx, t):
        _log("ignorado_por_conversa")
        return False

    if callable(extrair_acao_agendada):
        agendamento = extrair_acao_agendada(t)
        if isinstance(agendamento, dict) and agendamento.get("texto_acao"):
            resolver_contexto = _get(ctx, "_resolver_comando_contextual_forcado")
            acao_base = resolver_contexto(str(agendamento.get("texto_acao") or "")) if callable(resolver_contexto) else None
            if isinstance(acao_base, dict) and str(acao_base.get("intent") or "").strip():
                acao_base = dict(acao_base)
                acao_base.pop("_rota_contextual", None)
                resultado_agenda = {
                    "intent": "AGENDAR_ACAO",
                    "params": {**agendamento, "acao_agendada": acao_base, "rota_original": "contextual"},
                }
                _log("agendamento_local", str(acao_base.get("intent") or ""))
                executou = bool(executar_intencao(resultado_agenda, t)) if callable(executar_intencao) else False
                if callable(registrar_resultado_execucao):
                    registrar_resultado_execucao(resultado_agenda, t, executou, origem="agendamento_local")
                return True

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
        texto_tem_comando_explicito = _get(ctx, "_texto_tem_comando_explicito")
        if not callable(texto_tem_comando_explicito) or not texto_tem_comando_explicito(t):
            _log("falha_ignorada_sem_comando", "segue para conversa")
            return False
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
        if str(resultado.get("intent") or "").upper().strip() == "SUGGEST_ACTION" and not executou:
            _log("sugestao_invalida", "seguindo como conversa")
            return False
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


class ComandosImediatosRuntime:
    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        loop_getter: Callable[[], Any],
    ) -> None:
        self.namespace_getter = namespace_getter
        self.loop_getter = loop_getter

    def processar(self, texto: str, *, contexto_mental_ja_refinado: bool = False) -> bool:
        ns = self.namespace_getter() or {}
        nomes = (
            "_normalizar_texto_com_apelidos", "_texto_social_curto",
            "_texto_conversa_casual_sem_acao", "_refinar_contexto_mental",
            "_texto_tem_comando_explicito", "_texto_conversa_contextual_sem_comando",
            "_resolver_comando_janela_contextual_forcado", "_resolver_comando_midia_contextual_forcado",
            "_resolver_comando_arquivo_contextual_forcado", "_resolver_comando_acao_geral_contextual_forcado",
            "_resolver_comando_contextual_forcado", "_responder_contexto_janela_indisponivel",
            "_extrair_acao_agendada_local",
            "processar_comandos_em_cadeia", "processar_comando_deterministico",
            "interpretar_comando_local_rapido", "analisar_intencao", "executar_intencao",
            "_registrar_resultado_execucao", "_registrar_autoaprimoramento",
            "_falar_falha_contextual", "resumir_pagina_ou_video", "falar_com_lipsync",
        )
        contexto = {nome: ns.get(nome) for nome in nomes}
        estado_runtime = ns.get("_estado_compartilhado_runtime")
        contexto["mente_integrada_estado"] = getattr(estado_runtime, "mental", {})
        contexto["_contexto_mental_ja_refinado"] = bool(contexto_mental_ja_refinado)
        contexto["ws_loop"] = self.loop_getter()
        return processar_comandos_imediatos(contexto, texto)

    def processar_prioritarios(self, texto: str) -> bool:
        """Protege percepções objetivas antes dos fallbacks conversacionais."""
        ns = self.namespace_getter() or {}
        detectar_diagnostico = ns.get("_detectar_pedido_diagnostico_mente")
        if callable(detectar_diagnostico) and detectar_diagnostico(texto):
            print("⚡ [PRIORIDADE:DIAGNÓSTICO] retrato da mente única")
            mostrar_diagnostico = ns.get("_mostrar_diagnostico_mente")
            if callable(mostrar_diagnostico):
                mostrar_diagnostico()
            return True
        detectar_saude = ns.get("detectar_comando_saude")
        if callable(detectar_saude) and detectar_saude(texto):
            print("⚡ [PRIORIDADE:SAÚDE] consulta objetiva do computador")
            falar_saude = ns.get("_falar_status_saude")
            if callable(falar_saude):
                falar_saude()
            return True
        if texto_pede_resumo_pagina(texto):
            print("⚡ [PRIORIDADE:RESUMO] leitura da página atual")
            return self.processar(texto, contexto_mental_ja_refinado=False)
        return False


def criar_comandos_imediatos_runtime(**kwargs: Any) -> ComandosImediatosRuntime:
    return ComandosImediatosRuntime(**kwargs)

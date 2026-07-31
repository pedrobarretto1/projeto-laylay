"""Cliente LLM ligado ao contexto vivo da mente da Laylay."""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict

from mente_laylay.integracao.llm_http import (
    conteudo_fallback_llm_local,
    eh_estado_tecnico_llm,
    executar_chat_llm,
)
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm, texto_pede_contexto_arquivos
from mente_laylay.integracao.resposta_llm import interpretar_payload_llm


class ClienteLLMRuntime:
    """Prepara e envia mensagens sem guardar uma cópia paralela do contexto."""

    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        log: Callable[..., Any] = print,
    ) -> None:
        self.namespace_getter = namespace_getter
        self.log = log

    def _ns(self) -> Dict[str, Any]:
        return self.namespace_getter() or {}

    def enviar(
        self,
        mensagens: Any,
        _com_tools: bool = True,
        max_tokens: int = 1024,
        modo_rapido: bool = False,
        timeout: int | None = None,
        _permitir_conversa_modo_jogo: bool = False,
        _prioridade_interativa: bool = False,
    ) -> str:
        ns = self._ns()
        endpoint_local = bool(ns["llm_endpoint_eh_local"]())
        interacao_ativa = ns.get("interacao_ativa")
        if endpoint_local and not _prioridade_interativa and callable(interacao_ativa):
            try:
                usuario_interagindo = bool(interacao_ativa())
            except Exception:
                usuario_interagindo = False
            if usuario_interagindo:
                self.log(
                    "🧠 [IA] tarefa secundária adiada enquanto a conversa está ativa."
                )
                return conteudo_fallback_llm_local({
                    "messages": list(mensagens or []) if isinstance(mensagens, list) else [],
                    "max_tokens": max_tokens,
                })
        memoria = ns["memoria_inteligente"]
        data = preparar_payload_llm(
            mensagens,
            model=ns["model"],
            max_tokens=max_tokens,
            modo_rapido=modo_rapido,
            endpoint_local=endpoint_local,
            resumo_do_dia=memoria.resumo_do_dia,
            data_atual=memoria.data_atual,
            texto_pede_contexto_arquivos=lambda texto: texto_pede_contexto_arquivos(
                texto,
                normalizar_texto=ns["normalizar_texto"],
            ),
            mapear_pastas=ns["mapear_pastas"],
            contexto_logs=ns["contexto_logs"],
            contexto_navegador_relevante=ns["contexto_navegador_relevante"],
            contexto_sistema=ns["contexto_sistema"](),
            obter_contexto_paginas=ns["obter_contexto_paginas"],
            resumo_mente_integrada=ns["resumo_mente_integrada"],
            log=self.log,
        )
        modo_jogo_ativo = ns.get("modo_jogo_ativo")
        em_jogo = False
        if callable(modo_jogo_ativo):
            try:
                em_jogo = bool(modo_jogo_ativo())
            except Exception:
                em_jogo = False
        if endpoint_local and em_jogo and _permitir_conversa_modo_jogo:
            conversa_remota = ns.get("conversa_jogo_remota")
            if callable(conversa_remota):
                resposta_remota = str(conversa_remota(data) or "").strip()
                if resposta_remota:
                    self.log("🎮 [CONVERSA:JOGO] rota remota preservou a GPU do jogo.")
                    return resposta_remota
        if _permitir_conversa_modo_jogo:
            # Metadado interno consumido pelo transporte; nunca é enviado ao modelo.
            data["_laylay_conversa_modo_jogo"] = True
        # Metadado consumido pelo transporte local. Tarefas autônomas mantêm
        # acesso ao modelo quando ele está livre, mas não entram na frente de
        # uma resposta solicitada diretamente pela pessoa usuária.
        data["_laylay_prioridade_interativa"] = bool(_prioridade_interativa)
        # Observadores, classificadores e tarefas de apoio nunca devem ocupar
        # o modelo local pelo mesmo prazo de uma conversa solicitada por Pedro.
        if timeout is None and endpoint_local and not _prioridade_interativa:
            timeout = 12
        if endpoint_local:
            mensagens_payload = list(data.get("messages") or [])
            caracteres = sum(
                len(str(item.get("content") or ""))
                for item in mensagens_payload if isinstance(item, dict)
            )
            self.log(
                "🧠 [IA:PAYLOAD] "
                f"mensagens={len(mensagens_payload)} caracteres={caracteres} "
                f"max_tokens={data.get('max_tokens')} rapido={bool(modo_rapido)} "
                f"interativo={bool(_prioridade_interativa)}"
            )
        api_key = os.environ.get("OPENROUTER_API_KEY") or ns.get("api_key", "")
        inicio = time.perf_counter()
        sucesso = False
        try:
            resposta = executar_chat_llm(
                data,
                post_chat=ns["post_chat"],
                interpretar_payload=lambda payload: interpretar_payload_llm(payload, log=self.log),
                api_key=api_key,
                http_referer=ns.get("http_referer", ""),
                app_title=ns.get("app_title", ""),
                endpoint_local=endpoint_local,
                timeout=timeout,
                log=self.log,
                registrar_falha=ns.get("registrar_falha_diagnostico"),
            )
            sucesso = not eh_estado_tecnico_llm(resposta)
            return resposta
        finally:
            registrar = ns.get("registrar_metrica_diagnostico")
            if callable(registrar):
                registrar(
                    "llm_http",
                    (time.perf_counter() - inicio) * 1000.0,
                    sucesso,
                )


def criar_cliente_llm_runtime(**kwargs: Any) -> ClienteLLMRuntime:
    return ClienteLLMRuntime(**kwargs)

"""Cliente LLM ligado ao contexto vivo da mente da Laylay."""

from __future__ import annotations

import os
from typing import Any, Callable, Dict

from mente_laylay.integracao.llm_http import executar_chat_llm
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
    ) -> str:
        ns = self._ns()
        endpoint_local = bool(ns["llm_endpoint_eh_local"]())
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
        if _permitir_conversa_modo_jogo:
            # Metadado interno consumido pelo transporte; nunca é enviado ao modelo.
            data["_laylay_conversa_modo_jogo"] = True
        api_key = os.environ.get("OPENROUTER_API_KEY") or ns.get("api_key", "")
        return executar_chat_llm(
            data,
            post_chat=ns["post_chat"],
            interpretar_payload=lambda payload: interpretar_payload_llm(payload, log=self.log),
            api_key=api_key,
            http_referer=ns.get("http_referer", ""),
            app_title=ns.get("app_title", ""),
            endpoint_local=endpoint_local,
            timeout=timeout,
            log=self.log,
        )


def criar_cliente_llm_runtime(**kwargs: Any) -> ClienteLLMRuntime:
    return ClienteLLMRuntime(**kwargs)

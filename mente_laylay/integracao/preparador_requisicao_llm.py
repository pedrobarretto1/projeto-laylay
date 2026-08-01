"""Prepara requisições do modelo antes da fronteira de transporte HTTP."""

from __future__ import annotations

from typing import Any, Callable

from mente_laylay.integracao.preparacao_llm import (
    preparar_payload_llm,
    texto_pede_contexto_arquivos,
)
from mente_laylay.integracao.registro_conversa_llm import (
    PedidoModelo,
    RequisicaoTransporteLLM,
)


class PreparadorRequisicaoLLMRuntime:
    """Único componente autorizado a transformar contexto em payload de modelo."""

    def __init__(
        self,
        *,
        model: str,
        endpoint_local_getter: Callable[[], bool],
        resumo_do_dia_getter: Callable[[], str],
        data_atual_getter: Callable[[], str],
        normalizar_texto: Callable[[str], str],
        mapear_pastas: Callable[..., Any],
        contexto_logs_getter: Callable[[], Any],
        contexto_navegador_relevante: Callable[..., Any],
        contexto_sistema_getter: Callable[[], Any],
        obter_contexto_paginas: Callable[..., Any],
        resumo_mente_integrada: Callable[..., Any],
        log: Callable[..., Any] = print,
    ) -> None:
        self.model = str(model or "").strip()
        self.endpoint_local_getter = endpoint_local_getter
        self.resumo_do_dia_getter = resumo_do_dia_getter
        self.data_atual_getter = data_atual_getter
        self.normalizar_texto = normalizar_texto
        self.mapear_pastas = mapear_pastas
        self.contexto_logs_getter = contexto_logs_getter
        self.contexto_navegador_relevante = contexto_navegador_relevante
        self.contexto_sistema_getter = contexto_sistema_getter
        self.obter_contexto_paginas = obter_contexto_paginas
        self.resumo_mente_integrada = resumo_mente_integrada
        self.log = log

    def preparar(self, pedido: PedidoModelo) -> RequisicaoTransporteLLM:
        if not isinstance(pedido, PedidoModelo):
            raise TypeError("o preparador aceita somente PedidoModelo")
        endpoint_local = bool(self.endpoint_local_getter())
        payload = preparar_payload_llm(
            [dict(item) for item in pedido.mensagens],
            model=self.model,
            max_tokens=pedido.max_tokens,
            modo_rapido=pedido.modo_rapido,
            endpoint_local=endpoint_local,
            resumo_do_dia=str(self.resumo_do_dia_getter() or ""),
            data_atual=str(self.data_atual_getter() or ""),
            texto_pede_contexto_arquivos=lambda texto: texto_pede_contexto_arquivos(
                texto, normalizar_texto=self.normalizar_texto,
            ),
            mapear_pastas=self.mapear_pastas,
            contexto_logs=self.contexto_logs_getter(),
            contexto_navegador_relevante=self.contexto_navegador_relevante,
            contexto_sistema=self.contexto_sistema_getter(),
            obter_contexto_paginas=self.obter_contexto_paginas,
            resumo_mente_integrada=self.resumo_mente_integrada,
            log=self.log,
        )
        return RequisicaoTransporteLLM(
            payload=payload,
            timeout=pedido.timeout,
            permitir_conversa_modo_jogo=pedido.permitir_conversa_modo_jogo,
            prioridade_interativa=pedido.prioridade_interativa,
            permitir_durante_interacao=pedido.permitir_durante_interacao,
        )

    def diagnostico(self) -> dict[str, Any]:
        return {
            "disponivel": True,
            "memoria_exposta_ao_transporte": False,
            "autoriza_execucao": False,
        }


def criar_preparador_requisicao_llm_runtime(**kwargs: Any) -> PreparadorRequisicaoLLMRuntime:
    return PreparadorRequisicaoLLMRuntime(**kwargs)

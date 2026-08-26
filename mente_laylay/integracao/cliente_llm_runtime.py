"""Fronteira de transporte do modelo, sem acesso à memória da Laylay."""

from __future__ import annotations

import os
import time
from typing import Any, Callable

from mente_laylay.integracao.llm_http import (
    FALHA_LLM_OCUPADA,
    conteudo_fallback_llm_local,
    eh_estado_tecnico_llm,
    executar_chat_llm,
)
from mente_laylay.integracao.orcamento_llm_turno import (
    DecisaoOrcamentoLLM,
    OrcamentoLLMTurnoRuntime,
)
from mente_laylay.integracao.registro_conversa_llm import (
    PedidoModelo,
    RequisicaoTransporteLLM,
    ResultadoModelo,
)
from mente_laylay.integracao.resposta_llm import interpretar_payload_llm


def _registrar_metrica_compat(
    registrar: Callable[..., Any] | None,
    componente: str,
    duracao_ms: float,
    sucesso: bool,
    **metadados: Any,
) -> None:
    if not callable(registrar):
        return
    try:
        registrar(componente, duracao_ms, sucesso, **metadados)
    except TypeError:
        registrar(componente, duracao_ms, sucesso)


class ClienteLLMRuntime:
    """Executa um payload pronto; não conhece memória, prompt ou namespace."""

    def __init__(
        self,
        *,
        endpoint_local_getter: Callable[[], bool],
        post_chat: Callable[..., Any],
        api_key: str = "",
        http_referer: str = "",
        app_title: str = "",
        interacao_ativa: Callable[[], bool] | None = None,
        modo_jogo_ativo: Callable[[], bool] | None = None,
        conversa_jogo_remota: Callable[[dict[str, Any]], str] | None = None,
        registrar_metrica: Callable[..., Any] | None = None,
        registrar_falha: Callable[..., Any] | None = None,
        orcamento_turno: OrcamentoLLMTurnoRuntime | None = None,
        log: Callable[..., Any] = print,
    ) -> None:
        self.endpoint_local_getter = endpoint_local_getter
        self.post_chat = post_chat
        self.api_key = str(api_key or "")
        self.http_referer = str(http_referer or "")
        self.app_title = str(app_title or "")
        self.interacao_ativa = interacao_ativa or (lambda: False)
        self.modo_jogo_ativo = modo_jogo_ativo or (lambda: False)
        self.conversa_jogo_remota = conversa_jogo_remota
        self.registrar_metrica = registrar_metrica
        self.registrar_falha = registrar_falha
        self.orcamento_turno = orcamento_turno
        self.log = log
        self._requisicoes = 0
        self._sucessos = 0
        self._falhas = 0
        self._falhas_consecutivas = 0
        self._estado_atual = "saudavel"
        self._ultima_falha_codigo = ""

    def executar(self, requisicao: RequisicaoTransporteLLM) -> ResultadoModelo:
        if not isinstance(requisicao, RequisicaoTransporteLLM):
            raise TypeError("o cliente HTTP aceita somente RequisicaoTransporteLLM")
        self._requisicoes += 1
        endpoint_local = bool(self.endpoint_local_getter())
        data = dict(requisicao.payload or {})
        mensagens = list(data.get("messages") or [])
        caracteres = sum(
            len(str(item.get("content") or ""))
            for item in mensagens if isinstance(item, dict)
        )
        if (
            endpoint_local
            and not requisicao.prioridade_interativa
            and not requisicao.permitir_durante_interacao
            and bool(self.interacao_ativa())
        ):
            self.log("🧠 [IA] tarefa secundária adiada enquanto a conversa está ativa.")
            texto = conteudo_fallback_llm_local(data)
            return ResultadoModelo(texto=texto, sucesso=False, rota="adiada")

        decisao_orcamento: DecisaoOrcamentoLLM | None = None
        if self.orcamento_turno is not None:
            decisao_orcamento = self.orcamento_turno.autorizar_chamada(
                tipo_chamada=requisicao.tipo_chamada,
                classe_timeout=requisicao.classe_timeout,
                timeout_solicitado=requisicao.timeout,
            )
            if not decisao_orcamento.permitida:
                self.log(
                    "⚡ [IA:ORÇAMENTO] transporte não iniciado | "
                    f"tipo={requisicao.tipo_chamada} motivo={decisao_orcamento.motivo}"
                )
                return ResultadoModelo(
                    texto=FALHA_LLM_OCUPADA,
                    sucesso=False,
                    rota="orcamento_bloqueado",
                )

        em_jogo = bool(self.modo_jogo_ativo())
        if (
            endpoint_local
            and em_jogo
            and requisicao.permitir_conversa_modo_jogo
            and callable(self.conversa_jogo_remota)
        ):
            inicio_remoto = time.perf_counter()
            resposta_remota = str(self.conversa_jogo_remota(data) or "").strip()
            if resposta_remota:
                self._sucessos += 1
                self._falhas_consecutivas = 0
                self._estado_atual = "saudavel"
                self._ultima_falha_codigo = ""
                self.log("🎮 [CONVERSA:JOGO] rota remota preservou a GPU do jogo.")
                conclusao = (
                    self.orcamento_turno.concluir_chamada(
                        decisao_orcamento, sucesso=True,
                    )
                    if self.orcamento_turno is not None else {"atual": True}
                )
                _registrar_metrica_compat(
                    self.registrar_metrica,
                    "llm_http",
                    (time.perf_counter() - inicio_remoto) * 1000.0,
                    True,
                    backend="jogo_remoto",
                    modelo=str(data.get("model") or "desconhecido"),
                    tipo_chamada=requisicao.tipo_chamada,
                    tamanho_prompt_chars=caracteres,
                    limite_saida_tokens=int(data.get("max_tokens") or 0),
                )
                if not conclusao.get("atual", True):
                    return ResultadoModelo(
                        FALHA_LLM_OCUPADA, False, "resposta_obsoleta",
                    )
                return ResultadoModelo(resposta_remota, True, "jogo_remoto")

        if requisicao.permitir_conversa_modo_jogo:
            data["_laylay_conversa_modo_jogo"] = True
        data["_laylay_prioridade_interativa"] = bool(requisicao.prioridade_interativa)
        timeout = requisicao.timeout
        if decisao_orcamento is not None and decisao_orcamento.timeout_s is not None:
            timeout = max(1, int(decisao_orcamento.timeout_s))
        if timeout is None and endpoint_local and not requisicao.prioridade_interativa:
            timeout = 12
        if endpoint_local:
            self.log(
                "🧠 [IA:PAYLOAD] "
                f"mensagens={len(mensagens)} caracteres={caracteres} "
                f"max_tokens={data.get('max_tokens')} "
                f"interativo={bool(requisicao.prioridade_interativa)}"
            )
        inicio = time.perf_counter()
        sucesso = False
        resultado: ResultadoModelo | None = None
        conclusao_orcamento = {"atual": True}
        try:
            texto = executar_chat_llm(
                data,
                post_chat=self.post_chat,
                interpretar_payload=lambda payload: interpretar_payload_llm(payload, log=self.log),
                api_key=os.environ.get("OPENROUTER_API_KEY") or self.api_key,
                http_referer=self.http_referer,
                app_title=self.app_title,
                endpoint_local=endpoint_local,
                timeout=timeout,
                log=self.log,
                registrar_falha=self.registrar_falha,
            )
            sucesso = not eh_estado_tecnico_llm(texto)
            if sucesso:
                self._sucessos += 1
                self._falhas_consecutivas = 0
                self._estado_atual = "saudavel"
                self._ultima_falha_codigo = ""
            else:
                self._falhas += 1
                self._falhas_consecutivas += 1
                self._estado_atual = "degradado"
                self._ultima_falha_codigo = "estado_tecnico"
            resultado = ResultadoModelo(texto=str(texto or ""), sucesso=sucesso)
        except Exception:
            self._falhas += 1
            self._falhas_consecutivas += 1
            self._estado_atual = "degradado"
            self._ultima_falha_codigo = "excecao_transporte"
            raise
        finally:
            _registrar_metrica_compat(
                self.registrar_metrica,
                "llm_http",
                (time.perf_counter() - inicio) * 1000.0,
                sucesso,
                backend="local" if endpoint_local else "openrouter",
                modelo=str(data.get("model") or "desconhecido"),
                tipo_chamada=requisicao.tipo_chamada,
                tamanho_prompt_chars=caracteres,
                limite_saida_tokens=int(data.get("max_tokens") or 0),
            )
            if self.orcamento_turno is not None:
                conclusao_orcamento = self.orcamento_turno.concluir_chamada(
                    decisao_orcamento,
                    sucesso=sucesso,
                )
        if not conclusao_orcamento.get("atual", True):
            return ResultadoModelo(
                texto=FALHA_LLM_OCUPADA,
                sucesso=False,
                rota="resposta_obsoleta",
            )
        return resultado or ResultadoModelo(
            texto=FALHA_LLM_OCUPADA,
            sucesso=False,
            rota="sem_resultado",
        )

    def diagnostico(self) -> dict[str, Any]:
        return {
            "disponivel": True,
            "endpoint_local": bool(self.endpoint_local_getter()),
            "requisicoes": self._requisicoes,
            "sucessos": self._sucessos,
            "falhas": self._falhas,
            "falhas_consecutivas": self._falhas_consecutivas,
            "estado": self._estado_atual,
            "ultima_falha_codigo": self._ultima_falha_codigo,
            "memoria_exposta": False,
            "credencial_exposta": False,
            "autoriza_execucao": False,
            "orcamento_turno": (
                self.orcamento_turno.diagnostico()
                if self.orcamento_turno is not None else {"modo": "desativado"}
            ),
        }


class ServicoModeloLLMRuntime:
    """Compõe preparação contextual e transporte por contratos explícitos."""

    def __init__(self, *, preparador: Any, cliente: ClienteLLMRuntime) -> None:
        if not callable(getattr(preparador, "preparar", None)):
            raise RuntimeError("preparador de requisição LLM inválido")
        if not callable(getattr(cliente, "executar", None)):
            raise RuntimeError("cliente LLM inválido")
        self.preparador = preparador
        self.cliente = cliente

    def executar(self, pedido: PedidoModelo) -> ResultadoModelo:
        return self.cliente.executar(self.preparador.preparar(pedido))

    def diagnostico(self) -> dict[str, Any]:
        return self.cliente.diagnostico()


def criar_cliente_llm_runtime(**kwargs: Any) -> ClienteLLMRuntime:
    return ClienteLLMRuntime(**kwargs)


def criar_servico_modelo_llm_runtime(**kwargs: Any) -> ServicoModeloLLMRuntime:
    return ServicoModeloLLMRuntime(**kwargs)

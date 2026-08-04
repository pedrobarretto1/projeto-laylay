"""Composição dos provedores externos de pesquisa, linguagem e visão."""

from __future__ import annotations

import os
from functools import partial
from typing import Any, Callable, Dict

from mente_laylay.cognicao.confirmacao_llm import criar_confirmacao_llm_runtime
from mente_laylay.cognicao.memoria_visual import (
    analisar_com_groq,
    sintetizar_texto_com_groq,
)
from mente_laylay.cognicao.pesquisa_contextual import criar_pesquisa_contextual_runtime
from mente_laylay.cognicao.selecao_abas import criar_selecao_abas_runtime
from mente_laylay.integracao.cliente_llm_runtime import (
    criar_cliente_llm_runtime,
    criar_servico_modelo_llm_runtime,
)
from mente_laylay.integracao.conversa_jogo_remota import (
    criar_conversa_jogo_remota_runtime,
)
from mente_laylay.integracao.llm_http import criar_llm_http_runtime
from mente_laylay.integracao.preparador_requisicao_llm import (
    criar_preparador_requisicao_llm_runtime,
)
from mente_laylay.integracao.registro_conversa_llm import registrar_modelo_llm


class ComposicaoInteligenciaExternaRuntime:
    """Mantém configuração externa fora do ponto de entrada da assistente."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str,
        http_referer: str,
        app_title: str,
        normalizar_texto_curto: Callable[[str], str],
        requests_get: Callable[..., Any],
        requests_post: Callable[..., Any],
        ao_finalizar_conversa_modo_jogo: Callable[[], Any],
        registrar_falha: Callable[..., Any] | None = None,
        registrar_orcamento_prompt: Callable[..., Any] | None = None,
        env_getter: Callable[[str, str], str] = os.getenv,
        pesquisa_factory: Callable[..., Any] = criar_pesquisa_contextual_runtime,
        llm_http_factory: Callable[..., Any] = criar_llm_http_runtime,
        cliente_factory: Callable[..., Any] = criar_cliente_llm_runtime,
        preparador_factory: Callable[..., Any] = criar_preparador_requisicao_llm_runtime,
        modelo_factory: Callable[..., Any] = criar_servico_modelo_llm_runtime,
        conversa_jogo_factory: Callable[..., Any] = criar_conversa_jogo_remota_runtime,
        confirmacao_factory: Callable[..., Any] = criar_confirmacao_llm_runtime,
        selecao_abas_factory: Callable[..., Any] = criar_selecao_abas_runtime,
        analisar_imagem_fn: Callable[..., Any] = analisar_com_groq,
        sintetizar_texto_fn: Callable[..., Any] = sintetizar_texto_com_groq,
        log: Callable[..., Any] = print,
    ) -> None:
        self.base_url = str(base_url or "").strip()
        self.model = str(model or "").strip()
        self.api_key = str(api_key or "")
        self.http_referer = str(http_referer or "")
        self.app_title = str(app_title or "")
        self.registrar_falha = registrar_falha
        self.registrar_orcamento_prompt = registrar_orcamento_prompt
        self.log = log
        self._cliente_factory = cliente_factory
        self._preparador_factory = preparador_factory
        self._modelo_factory = modelo_factory
        self._confirmacao_factory = confirmacao_factory
        self._selecao_abas_factory = selecao_abas_factory
        self._cliente = None
        self._transporte = None
        self._confirmacao = None
        self._selecao_abas = None

        self.local_timeout = self._inteiro_env(
            env_getter, "LAYLAY_LLM_LOCAL_TIMEOUT", 45, minimo=3, maximo=300,
        )
        self.game_timeout = self._inteiro_env(
            env_getter, "LAYLAY_LLM_GAME_TIMEOUT", 20, minimo=3, maximo=120,
        )
        self.remote_timeout = self._inteiro_env(
            env_getter, "LAYLAY_LLM_REMOTE_TIMEOUT", 30, minimo=3, maximo=300,
        )
        self.pesquisa_timeout = self._float_env(
            env_getter, "LAYLAY_PESQUISA_TIMEOUT", 4.0, minimo=0.5, maximo=30.0,
        )
        self.groq_api_key = str(env_getter("GROQ_API_KEY", "") or "").strip()
        self.groq_model = str(
            env_getter("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")
            or "qwen/qwen3.6-27b"
        ).strip()
        self.groq_chat_model = str(
            env_getter("GROQ_CHAT_MODEL", self.groq_model) or self.groq_model
        ).strip()
        self.conversa_jogo = conversa_jogo_factory(
            api_key=self.groq_api_key,
            model=self.groq_chat_model,
            requests_post=requests_post,
            timeout_s=self._float_env(
                env_getter, "LAYLAY_CONVERSA_JOGO_REMOTA_TIMEOUT", 8.0,
                minimo=3.0, maximo=30.0,
            ),
            log=log,
        )

        self.pesquisa = pesquisa_factory(
            normalizar_texto_curto=normalizar_texto_curto,
            requests_get=requests_get,
            orcamento_interativo_s=self.pesquisa_timeout,
            log=log,
        )
        self.http = llm_http_factory(
            base_url=self.base_url,
            local_timeout=self.local_timeout,
            remote_timeout=self.remote_timeout,
            game_timeout=self.game_timeout,
            game_idle_unload_s=self._float_env(
                env_getter, "LAYLAY_CONVERSA_JOGO_OCIOSA_SEGUNDOS", 60.0,
                minimo=5.0, maximo=600.0,
            ),
            requests_post=requests_post,
            print_fn=log,
            ao_finalizar_conversa_modo_jogo=ao_finalizar_conversa_modo_jogo,
            registrar_falha=registrar_falha,
            registrar_orcamento_prompt=registrar_orcamento_prompt,
        )
        self.analisar_imagem = partial(
            analisar_imagem_fn,
            api_key=self.groq_api_key,
            model=self.groq_model,
        )
        self.analisar_imagem_jogo = partial(
            analisar_imagem_fn,
            api_key=self.groq_api_key,
            model=self.groq_model,
            forcar_http=True,
            max_tentativas=1,
            timeout_s=12.0,
            retry_delay_s=0.6,
            temperature=0.05,
        )
        self.sintetizar_pesquisa_jogo = partial(
            sintetizar_texto_fn,
            api_key=self.groq_api_key,
            model=self.groq_model,
            timeout_s=8.0,
        )

    def _relatar(self, codigo: str, erro: BaseException) -> None:
        if callable(self.registrar_falha):
            self.registrar_falha("composicao_inteligencia_externa", codigo, erro=erro)

    def _inteiro_env(
        self, env_getter: Callable[[str, str], str], nome: str, padrao: int,
        *, minimo: int, maximo: int,
    ) -> int:
        bruto = env_getter(nome, str(padrao))
        try:
            valor = int(str(bruto or padrao).strip())
            if not minimo <= valor <= maximo:
                raise ValueError("fora do intervalo")
            return valor
        except (TypeError, ValueError) as erro:
            self.log(f"⚠️ [IA:CONFIG] {nome} inválida; usando {padrao}.")
            self._relatar(f"configuracao_{nome.casefold()}", erro)
            return padrao

    def _float_env(
        self, env_getter: Callable[[str, str], str], nome: str, padrao: float,
        *, minimo: float, maximo: float,
    ) -> float:
        bruto = env_getter(nome, str(padrao))
        try:
            valor = float(str(bruto or padrao).strip())
            if not minimo <= valor <= maximo:
                raise ValueError("fora do intervalo")
            return valor
        except (TypeError, ValueError) as erro:
            self.log(f"⚠️ [IA:CONFIG] {nome} inválida; usando {padrao:g}.")
            self._relatar(f"configuracao_{nome.casefold()}", erro)
            return padrao

    def conectar_cliente(
        self,
        *,
        memoria_inteligente: Any,
        normalizar_texto: Callable[[str], str],
        mapear_pastas: Callable[..., Any],
        contexto_logs_getter: Callable[[], Any],
        contexto_navegador_relevante: Callable[..., Any],
        contexto_sistema_getter: Callable[[], Any],
        obter_contexto_paginas: Callable[..., Any],
        resumo_mente_integrada: Callable[..., Any],
        registrar_metrica: Callable[..., Any] | None = None,
        interacao_ativa: Callable[[], bool] | None = None,
    ) -> Any:
        if self._cliente is not None:
            return self._cliente

        def contexto_base() -> Dict[str, Any]:
            return {
                "post_chat": self.http.post,
                "api_key": self.api_key,
                "model": self.model,
                "http_referer": self.http_referer,
                "app_title": self.app_title,
            }

        preparador = self._preparador_factory(
            model=self.model,
            endpoint_local_getter=self.http.endpoint_eh_local,
            resumo_do_dia_getter=lambda: str(memoria_inteligente.resumo_do_dia or ""),
            data_atual_getter=lambda: str(memoria_inteligente.data_atual or ""),
            normalizar_texto=normalizar_texto,
            mapear_pastas=mapear_pastas,
            contexto_logs_getter=contexto_logs_getter,
            contexto_navegador_relevante=contexto_navegador_relevante,
            contexto_sistema_getter=contexto_sistema_getter,
            obter_contexto_paginas=obter_contexto_paginas,
            resumo_mente_integrada=resumo_mente_integrada,
            registrar_orcamento_prompt=self.registrar_orcamento_prompt,
            log=self.log,
        )
        self._transporte = self._cliente_factory(
            endpoint_local_getter=self.http.endpoint_eh_local,
            post_chat=self.http.post,
            api_key=self.api_key,
            http_referer=self.http_referer,
            app_title=self.app_title,
            interacao_ativa=interacao_ativa or (lambda: False),
            modo_jogo_ativo=lambda: bool(self.http.modo_jogo_ativo),
            conversa_jogo_remota=self.conversa_jogo.enviar,
            registrar_metrica=registrar_metrica,
            registrar_falha=self.registrar_falha,
            log=self.log,
        )
        self._cliente = registrar_modelo_llm(
            self._modelo_factory(preparador=preparador, cliente=self._transporte)
        )
        self._confirmacao = self._confirmacao_factory(namespace_getter=contexto_base)
        self._selecao_abas = self._selecao_abas_factory(namespace_getter=contexto_base)
        return self._cliente

    @property
    def cliente(self) -> Any:
        if self._cliente is None:
            raise RuntimeError("cliente LLM ainda não conectado ao contexto")
        return self._cliente

    @property
    def confirmacao(self) -> Any:
        if self._confirmacao is None:
            raise RuntimeError("confirmação LLM ainda não conectada ao contexto")
        return self._confirmacao

    @property
    def selecao_abas(self) -> Any:
        if self._selecao_abas is None:
            raise RuntimeError("seleção de abas ainda não conectada ao contexto")
        return self._selecao_abas

    @property
    def credencial_visual_disponivel(self) -> bool:
        return bool(self.groq_api_key)


def criar_composicao_inteligencia_externa_runtime(
    **kwargs: Any,
) -> ComposicaoInteligenciaExternaRuntime:
    return ComposicaoInteligenciaExternaRuntime(**kwargs)

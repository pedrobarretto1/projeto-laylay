"""Composição dos provedores externos de pesquisa, linguagem e visão."""

from __future__ import annotations

import os
from functools import partial
from typing import Any, Callable, Dict
from urllib.parse import urlsplit

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
from mente_laylay.integracao.contrato_saida_estruturada import (
    AnaliseVisualComContrato, ContratoSaidaEstruturada,
)
from mente_laylay.integracao.llm_http import criar_llm_http_runtime
from mente_laylay.integracao.modelo_visual_local import ModeloVisualLocalRuntime
from mente_laylay.integracao.preparador_requisicao_llm import (
    criar_preparador_requisicao_llm_runtime,
)
from mente_laylay.integracao.registro_conversa_llm import registrar_modelo_llm


MODELO_VISUAL_GROQ_PADRAO = "qwen/qwen3.8-27b"


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
        desativados = {"0", "false", "nao", "não", "off", "desligado"}
        mestre_ativa = str(
            env_getter("LAYLAY_OTIMIZACOES_DESEMPENHO", "1") or "1"
        ).casefold() not in desativados
        self.otimizacao_prompt_ativa = mestre_ativa and str(
            env_getter("LAYLAY_OTIMIZACAO_PROMPT_ATIVA", "1") or "1"
        ).casefold() not in desativados
        self.log = log
        self._cliente_factory = cliente_factory
        self._preparador_factory = preparador_factory
        self._modelo_factory = modelo_factory
        self._confirmacao_factory = confirmacao_factory
        self._selecao_abas_factory = selecao_abas_factory
        self._cliente = None
        self._transporte = None
        self._preparador = None
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
            env_getter("GROQ_VISION_MODEL", MODELO_VISUAL_GROQ_PADRAO)
            or MODELO_VISUAL_GROQ_PADRAO
        ).strip()
        self.groq_chat_model = str(
            env_getter("GROQ_CHAT_MODEL", self.groq_model) or self.groq_model
        ).strip()
        self.conversa_jogo_remota_ativa = str(
            env_getter("LAYLAY_CONVERSA_JOGO_REMOTA_ATIVA", "1") or "1"
        ).casefold() not in desativados
        self.conversa_jogo = conversa_jogo_factory(
            api_key=self.groq_api_key if self.conversa_jogo_remota_ativa else "",
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
        self.visao_backend = str(env_getter("LAYLAY_VISAO_BACKEND", "groq") or "groq").strip().casefold()
        self.visao_model = self.groq_model
        self._visao_local_disponivel = False
        if self.visao_backend == "ollama":
            self.visao_model = str(env_getter("LAYLAY_VISAO_MODEL", "qwen3-vl:4b-instruct") or "qwen3-vl:4b-instruct").strip()
            url_visual = str(env_getter("LAYLAY_VISAO_OLLAMA_BASE_URL", "http://localhost:11434/v1") or "").strip().rstrip("/")
            try:
                partes = urlsplit(url_visual)
                endpoint_seguro = bool(
                    partes.scheme == "http" and partes.hostname in {"localhost", "127.0.0.1"}
                    and not partes.username and not partes.password and partes.path == "/v1"
                    and not partes.query and not partes.fragment
                )
            except ValueError:
                endpoint_seguro = False
            if endpoint_seguro:
                try:
                    resposta = requests_post(
                        f"{url_visual[:-3]}/api/show", json={"model": self.visao_model}, timeout=3.0,
                    )
                    self._visao_local_disponivel = bool(
                        int(resposta.status_code) == 200 and "vision" in list(resposta.json().get("capabilities") or [])
                    )
                except Exception as erro:
                    self._relatar("modelo_visual_local_indisponivel", erro)
                http_visual = self.http if url_visual == self.base_url.rstrip("/") else llm_http_factory(
                    base_url=url_visual, local_timeout=self.local_timeout, remote_timeout=self.remote_timeout,
                    game_timeout=self.game_timeout, requests_post=requests_post, print_fn=log,
                    registrar_falha=registrar_falha,
                )
                post_visual = http_visual.post
            else:
                self._relatar("endpoint_visual_local_invalido", ValueError("A visão local exige endpoint Ollama em loopback."))
                post_visual = self.http.post
            self.visao_local = ModeloVisualLocalRuntime(
                model=self.visao_model if self._visao_local_disponivel else "",
                post_chat=post_visual,
                timeout_s=self._float_env(env_getter, "LAYLAY_VISAO_LOCAL_TIMEOUT", 45.0, minimo=3.0, maximo=300.0),
                registrar_falha=registrar_falha, log=log,
            )
            self.analisar_imagem = self.visao_local.analisar
            self.analisar_imagem_jogo = self.visao_local.analisar
            self.sintetizar_pesquisa_jogo = partial(
                self.visao_local.sintetizar,
                pergunta="Sintetize a análise e a pesquisa fornecidas, preservando o formato solicitado e sem inventar fatos.",
            )
            log(f"[VISÃO:LOCAL] modelo={self.visao_model} disponível={self._visao_local_disponivel}")
        elif self.visao_backend == "gemini":
            # A gratuidade pertence ao projeto Google. Esta guarda registra a
            # confirmação humana, não consulta nem modifica seu faturamento.
            chave_gemini = str(env_getter("GEMINI_API_KEY", "") or "").strip()
            gratuito_confirmado = str(env_getter("LAYLAY_GEMINI_FREE_TIER_CONFIRMADO", "0")) == "1"
            self.visao_model = str(env_getter("GEMINI_VISION_MODEL", "gemini-3.5-flash-lite") or "gemini-3.5-flash-lite").strip()
            self.http_visual_gemini = llm_http_factory(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai",
                local_timeout=self.local_timeout, remote_timeout=self.remote_timeout,
                requests_post=requests_post, print_fn=log, registrar_falha=registrar_falha,
            )

            def post_gemini(headers: dict, data: dict, timeout: float):
                return self.http_visual_gemini.post(
                    {**headers, "Authorization": f"Bearer {chave_gemini}"}, data, timeout=timeout,
                )

            self.visao_gemini = ModeloVisualLocalRuntime(
                model=self.visao_model if chave_gemini and gratuito_confirmado else "",
                post_chat=post_gemini, nome_provedor="gemini",
                reasoning_effort="minimal",
                timeout_s=12.0, registrar_falha=registrar_falha, log=log,
            )
            self.analisar_imagem = self.analisar_imagem_jogo = self.visao_gemini.analisar
            self.sintetizar_pesquisa_jogo = partial(
                self.visao_gemini.sintetizar,
                pergunta="Sintetize a análise e a pesquisa fornecidas, preservando o formato solicitado e sem inventar fatos.",
            )
            log(f"[VISÃO:GEMINI] modelo={self.visao_model} disponível={self.visao_gemini.disponivel}")
        elif self.visao_backend != "groq":
            # Configuração desconhecida não autoriza envio a outro provedor.
            self.analisar_imagem = self.analisar_imagem_jogo = lambda *_a, **_k: "Falha visual: provedor visual inválido."
            self.sintetizar_pesquisa_jogo = lambda *_a, **_k: ""
            self._relatar("provedor_visual_invalido", ValueError("Provedor visual inválido."))

        self._analisar_imagem_jogo_provedor = self.analisar_imagem_jogo
        self.analisar_imagem_jogo = AnaliseVisualComContrato(self._analisar_jogo_com_contrato)

    def _analisar_jogo_com_contrato(
        self, imagem: str, pergunta: str, *,
        contrato_saida: ContratoSaidaEstruturada | None = None,
    ) -> str:
        if contrato_saida is None:
            return self._analisar_imagem_jogo_provedor(imagem, pergunta)
        if not isinstance(contrato_saida, ContratoSaidaEstruturada):
            raise TypeError("contrato de saída deve ser explícito e tipado")
        if self.visao_backend in {"ollama", "gemini"}:
            return self._analisar_imagem_jogo_provedor(
                imagem, pergunta, contrato_saida=contrato_saida,
            )
        if self.visao_backend != "groq":
            return "Falha visual: provedor visual inválido."
        # A porta Groq existente já solicita o marcador textual. Validar esse
        # framing mantém a compatibilidade sem aceitar JSON livre nessa porta.
        resposta = self._analisar_imagem_jogo_provedor(imagem, pergunta)
        try:
            return contrato_saida.validar_framing(resposta)
        except (TypeError, ValueError) as erro:
            self._relatar("contrato_saida_visual_invalido", erro)
            return "Falha visual: o provedor não devolveu a estrutura contratada."

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
        orcamento_turno: Any = None,
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
            resumo_do_dia_getter=lambda: str(
                memoria_inteligente.contexto_do_dia_para_prompt()
                if callable(getattr(memoria_inteligente, "contexto_do_dia_para_prompt", None))
                else memoria_inteligente.resumo_do_dia or ""
            ),
            data_atual_getter=lambda: str(memoria_inteligente.data_atual or ""),
            normalizar_texto=normalizar_texto,
            mapear_pastas=mapear_pastas,
            contexto_logs_getter=contexto_logs_getter,
            contexto_navegador_relevante=contexto_navegador_relevante,
            contexto_sistema_getter=contexto_sistema_getter,
            obter_contexto_paginas=obter_contexto_paginas,
            resumo_mente_integrada=resumo_mente_integrada,
            registrar_orcamento_prompt=self.registrar_orcamento_prompt,
            otimizacao_prompt_ativa=self.otimizacao_prompt_ativa,
            log=self.log,
        )
        self._preparador = preparador
        self._transporte = self._cliente_factory(
            endpoint_local_getter=self.http.endpoint_eh_local,
            post_chat=self.http.post,
            api_key=self.api_key,
            http_referer=self.http_referer,
            app_title=self.app_title,
            interacao_ativa=interacao_ativa or (lambda: False),
            modo_jogo_ativo=lambda: bool(self.http.modo_jogo_ativo),
            conversa_jogo_remota=self.conversa_jogo.enviar if self.conversa_jogo_remota_ativa else None,
            registrar_metrica=registrar_metrica,
            registrar_falha=self.registrar_falha,
            orcamento_turno=orcamento_turno,
            log=self.log,
        )
        self._cliente = registrar_modelo_llm(
            self._modelo_factory(preparador=preparador, cliente=self._transporte)
        )
        self._confirmacao = self._confirmacao_factory(namespace_getter=contexto_base)
        self._selecao_abas = self._selecao_abas_factory(namespace_getter=contexto_base)
        return self._cliente

    def desativar_otimizacao_prompt(self) -> None:
        """Retorna ao prompt completo no restante da sessão."""
        self.otimizacao_prompt_ativa = False
        if self._preparador is not None:
            self._preparador.otimizacao_prompt_ativa = False

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
        if self.visao_backend == "gemini":
            return self.visao_gemini.disponivel
        if self.visao_backend == "ollama":
            return self._visao_local_disponivel
        return self.visao_backend == "groq" and bool(self.groq_api_key)


def criar_composicao_inteligencia_externa_runtime(
    **kwargs: Any,
) -> ComposicaoInteligenciaExternaRuntime:
    return ComposicaoInteligenciaExternaRuntime(**kwargs)

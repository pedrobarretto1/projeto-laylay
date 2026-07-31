from __future__ import annotations

import pytest

from mente_laylay.integracao.composicao_inteligencia_externa import (
    ComposicaoInteligenciaExternaRuntime,
)


class _HttpFake:
    def endpoint_eh_local(self):
        return True

    def post(self, *_args, **_kwargs):
        return None


class _ClienteFake:
    def enviar(self, *_args, **_kwargs):
        return "ok"


class _OperacaoFake:
    pass


def _criar(**extras):
    capturado = extras.pop("capturado", {})
    ambiente = extras.pop("ambiente", {})
    log = extras.pop("log", lambda *_: None)

    def guardar(nome, retorno):
        def factory(**kwargs):
            capturado[nome] = kwargs
            return retorno
        return factory

    runtime = ComposicaoInteligenciaExternaRuntime(
        base_url="http://localhost:11434/v1",
        model="modelo-local",
        api_key="ollama",
        http_referer="http://localhost",
        app_title="Laylay",
        normalizar_texto_curto=lambda texto: texto.casefold(),
        requests_get=lambda *_args, **_kwargs: None,
        requests_post=lambda *_args, **_kwargs: None,
        ao_finalizar_conversa_modo_jogo=lambda: None,
        env_getter=lambda nome, padrao="": ambiente.get(nome, padrao),
        pesquisa_factory=guardar("pesquisa", object()),
        llm_http_factory=guardar("http", _HttpFake()),
        cliente_factory=guardar("cliente", _ClienteFake()),
        confirmacao_factory=guardar("confirmacao", _OperacaoFake()),
        selecao_abas_factory=guardar("selecao", _OperacaoFake()),
        analisar_imagem_fn=lambda *args, **kwargs: (args, kwargs),
        sintetizar_texto_fn=lambda *args, **kwargs: (args, kwargs),
        log=log,
        **extras,
    )
    return runtime, capturado


def test_composicao_configura_provedores_e_visao_com_um_unico_contexto() -> None:
    capturado = {}
    runtime, capturado = _criar(
        capturado=capturado,
        ambiente={
            "LAYLAY_LLM_LOCAL_TIMEOUT": "60",
            "LAYLAY_LLM_GAME_TIMEOUT": "18",
            "LAYLAY_LLM_REMOTE_TIMEOUT": "35",
            "LAYLAY_PESQUISA_TIMEOUT": "3.5",
            "GROQ_API_KEY": "chave-visual",
            "GROQ_VISION_MODEL": "modelo-visual",
        },
    )

    assert runtime.local_timeout == 60
    assert runtime.game_timeout == 18
    assert runtime.remote_timeout == 35
    assert runtime.pesquisa_timeout == 3.5
    assert capturado["http"]["game_timeout"] == 18
    assert capturado["pesquisa"]["orcamento_interativo_s"] == 3.5
    assert runtime.credencial_visual_disponivel is True
    _, kwargs = runtime.analisar_imagem_jogo("imagem", "pergunta")
    assert kwargs["api_key"] == "chave-visual"
    assert kwargs["model"] == "modelo-visual"
    assert kwargs["max_tentativas"] == 1
    assert kwargs["timeout_s"] == 12.0


def test_composicao_conecta_cliente_confirmacao_e_selecao_em_segunda_fase() -> None:
    runtime, capturado = _criar()
    logs = []
    cliente = runtime.conectar_cliente(
        memoria_inteligente=object(),
        normalizar_texto=lambda texto: texto,
        mapear_pastas=lambda: {},
        contexto_logs_getter=lambda: logs,
        contexto_navegador_relevante=lambda *_: False,
        contexto_sistema_getter=lambda: {},
        obter_contexto_paginas=lambda: "",
        resumo_mente_integrada=lambda: "",
        registrar_metrica=lambda *_: None,
    )

    assert cliente is runtime.cliente
    assert runtime.confirmacao is not None
    assert runtime.selecao_abas is not None
    contexto = capturado["cliente"]["namespace_getter"]()
    assert contexto["model"] == "modelo-local"
    assert contexto["contexto_logs"] is logs
    assert contexto["post_chat"] == runtime.http.post
    assert capturado["confirmacao"]["namespace_getter"]()["model"] == "modelo-local"


def test_composicao_corrige_timeouts_invalidos_sem_expor_chave() -> None:
    falhas, logs = [], []
    runtime, _ = _criar(
        ambiente={
            "LAYLAY_LLM_LOCAL_TIMEOUT": "eterno",
            "LAYLAY_LLM_GAME_TIMEOUT": "9999",
            "LAYLAY_PESQUISA_TIMEOUT": "zero",
            "GROQ_API_KEY": "segredo-visual",
        },
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        log=logs.append,
    )

    assert runtime.local_timeout == 45
    assert runtime.game_timeout == 20
    assert runtime.pesquisa_timeout == 4.0
    assert len(falhas) == 3
    assert "segredo-visual" not in repr(logs)
    with pytest.raises(RuntimeError, match="ainda não conectado"):
        _ = runtime.cliente

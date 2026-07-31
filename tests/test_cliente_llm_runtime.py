from __future__ import annotations

from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime


def test_tarefa_secundaria_nao_acorda_modelo_durante_conversa() -> None:
    chamadas_http = []
    logs = []
    runtime = ClienteLLMRuntime(
        namespace_getter=lambda: {
            "llm_endpoint_eh_local": lambda: True,
            "interacao_ativa": lambda: True,
            "post_chat": lambda *_args, **_kwargs: chamadas_http.append(True),
        },
        log=logs.append,
    )

    resposta = runtime.enviar(
        [{"role": "user", "content": "resuma isso em segundo plano"}],
        _prioridade_interativa=False,
    )

    assert chamadas_http == []
    assert resposta
    assert any("tarefa secundária adiada" in item for item in logs)


def test_conversa_no_jogo_prefere_rota_remota_e_nao_acorda_modelo_local() -> None:
    chamadas_locais = []
    chamadas_remotas = []

    class Memoria:
        resumo_do_dia = ""
        data_atual = ""

    namespace = {
        "llm_endpoint_eh_local": lambda: True,
        "interacao_ativa": lambda: True,
        "modo_jogo_ativo": lambda: True,
        "conversa_jogo_remota": lambda payload: chamadas_remotas.append(payload) or "Oi. Tô bem, e você?",
        "post_chat": lambda *_args, **_kwargs: chamadas_locais.append(True),
        "memoria_inteligente": Memoria(),
        "model": "qwen-local",
        "normalizar_texto": lambda texto: texto,
        "mapear_pastas": lambda *_args, **_kwargs: {},
        "contexto_logs": "",
        "contexto_navegador_relevante": "",
        "contexto_sistema": lambda: "",
        "obter_contexto_paginas": lambda: "",
        "resumo_mente_integrada": lambda: "",
    }
    runtime = ClienteLLMRuntime(namespace_getter=lambda: namespace, log=lambda *_args: None)

    resposta = runtime.enviar(
        [{"role": "user", "content": "tudo bem com você?"}],
        _permitir_conversa_modo_jogo=True,
        _prioridade_interativa=True,
    )

    assert resposta == "Oi. Tô bem, e você?"
    assert len(chamadas_remotas) == 1
    assert chamadas_locais == []


def test_saudacao_no_jogo_usa_resposta_social_local_antes_da_llm() -> None:
    falas = []
    fases = []
    contexto_inicio = {
        "current_emotion": "calma",
        "emotion_level": 1,
        "mente_integrada_estado": {"turno_atual": {"modalidade": "conversa"}},
        "_texto_social_curto": lambda _texto: True,
        "_texto_conversa_casual_sem_acao": lambda _texto: True,
        "_texto_tem_comando_explicito": lambda _texto: False,
        "_resposta_conversa_rapida_local": lambda _texto: "Oi. Tô aqui com você.",
        "_emitir_resposta_curta": lambda _entrada, fala, **_kwargs: falas.append(fala),
    }
    contexto = {
        "contexto_inicio": lambda: contexto_inicio,
        "processar_inicio_fluxo": lambda *_args: False,
        "usar_modo_rapido": lambda _texto: True,
        "texto_depende_de_contexto": lambda _texto: False,
        "processar_comandos_imediatos": lambda *_args, **_kwargs: False,
        "modo_jogo_ativo": lambda: True,
        "atualizar_plano_turno": lambda fase, **_kwargs: fases.append(fase),
        "enviar_mensagem": lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("a LLM não deveria ser chamada")
        ),
    }

    runtime = RespostaIARuntime(contexto_getter=lambda: contexto, log=lambda *_args: None)
    runtime.processar("oi lay")

    assert falas == ["Oi. Tô aqui com você."]
    assert "tratado_conversa_social_curta" in fases

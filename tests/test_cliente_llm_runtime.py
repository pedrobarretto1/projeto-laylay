from __future__ import annotations

import mente_laylay.integracao.cliente_llm_runtime as cliente_llm_modulo
from mente_laylay.integracao.cliente_llm_runtime import (
    ClienteLLMRuntime,
    ServicoModeloLLMRuntime,
)
from mente_laylay.integracao.registro_conversa_llm import (
    EstadoConversaRuntime,
    PedidoModelo,
    RegistroModeloLLM,
    RequisicaoTransporteLLM,
    ResultadoModelo,
)
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime


def test_tarefa_secundaria_nao_acorda_modelo_durante_conversa() -> None:
    chamadas_http = []
    logs = []
    runtime = ClienteLLMRuntime(
        endpoint_local_getter=lambda: True,
        interacao_ativa=lambda: True,
        post_chat=lambda *_args, **_kwargs: chamadas_http.append(True),
        log=logs.append,
    )

    resposta = runtime.executar(
        RequisicaoTransporteLLM(
            payload={"messages": [{"role": "user", "content": "resuma isso"}]},
            prioridade_interativa=False,
        )
    )

    assert chamadas_http == []
    assert resposta.texto
    assert resposta.rota == "adiada"
    assert any("tarefa secundária adiada" in item for item in logs)


def test_resumo_de_memoria_pode_consolidar_no_fim_do_turno(monkeypatch) -> None:
    monkeypatch.setattr(
        cliente_llm_modulo,
        "executar_chat_llm",
        lambda *_args, **_kwargs: "Resumo consolidado.",
    )
    transporte = ClienteLLMRuntime(
        endpoint_local_getter=lambda: True,
        interacao_ativa=lambda: True,
        post_chat=lambda *_args, **_kwargs: None,
        log=lambda *_: None,
    )

    class Preparador:
        def preparar(self, pedido):
            return RequisicaoTransporteLLM(
                payload={"messages": list(pedido.mensagens), "max_tokens": 512},
                permitir_durante_interacao=pedido.permitir_durante_interacao,
            )

    runtime = ServicoModeloLLMRuntime(preparador=Preparador(), cliente=transporte)

    resposta = runtime.executar(
        PedidoModelo.criar(
            [{"role": "user", "content": "resuma o lote"}],
            permitir_durante_interacao=True,
        )
    )

    assert resposta.texto == "Resumo consolidado."


def test_conversa_no_jogo_prefere_rota_remota_e_nao_acorda_modelo_local() -> None:
    chamadas_locais = []
    chamadas_remotas = []

    runtime = ClienteLLMRuntime(
        endpoint_local_getter=lambda: True,
        interacao_ativa=lambda: True,
        modo_jogo_ativo=lambda: True,
        conversa_jogo_remota=lambda payload: chamadas_remotas.append(payload) or "Oi. Tô bem, e você?",
        post_chat=lambda *_args, **_kwargs: chamadas_locais.append(True),
        log=lambda *_args: None,
    )

    resposta = runtime.executar(
        RequisicaoTransporteLLM(
            payload={"messages": [{"role": "user", "content": "tudo bem?"}]},
            permitir_conversa_modo_jogo=True,
            prioridade_interativa=True,
        )
    )

    assert resposta.texto == "Oi. Tô bem, e você?"
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
    assert "tratado_conversa_social_segura_jogo" in fases


def test_assunto_contextual_no_jogo_ignora_atalho_e_chega_a_mente_principal() -> None:
    falas_locais = []
    finalizacoes = []

    class Modelo:
        def __init__(self):
            self.pedidos = []

        def executar(self, pedido):
            self.pedidos.append(pedido)
            return ResultadoModelo('{"fala":"Entendi.","comandos":[]}', True)

        @staticmethod
        def diagnostico():
            return {"disponivel": True}

    modelo_bruto = Modelo()
    estado = EstadoConversaRuntime(getter=lambda: [], setter=lambda _novas: None)

    class Contexto:
        @staticmethod
        def montar():
            return {}

    contexto_inicio = {
        "current_emotion": "calma",
        "emotion_level": 1,
        "mente_integrada_estado": {"turno_atual": {"modalidade": "correcao"}},
        "_texto_tem_comando_explicito": lambda _texto: False,
        "_resposta_conversa_rapida_local": lambda _texto: "Resposta local indevida.",
        "_emitir_resposta_curta": lambda *_args, **_kwargs: falas_locais.append(True),
    }
    contexto = {
        "contexto_inicio": lambda: contexto_inicio,
        "processar_inicio_fluxo": lambda *_args: False,
        "usar_modo_rapido": lambda _texto: True,
        "texto_depende_de_contexto": lambda _texto: True,
        "processar_comandos_imediatos": lambda *_args, **_kwargs: False,
        "modo_jogo_ativo": lambda: True,
        "estado_conversa": estado,
        "modelo_llm": RegistroModeloLLM.criar(modelo_bruto),
        "preparar_resposta": lambda *_args: {
            "resposta_bruta": "{}",
            "fala": "Entendi, você ainda está no menu.",
            "comandos": [],
            "tipo_interacao": "conversa",
            "leitura_semantica": {},
        },
        "contexto_dispatch_runtime": Contexto(),
        "executar_comandos_json": lambda *_args: {
            "erros": [], "fala_ja_emitida": False,
            "fala_emitida_por_acao": False, "fala_salva_no_inicio": False,
        },
        "contexto_finalizacao_runtime": Contexto(),
        "finalizar_execucao": lambda *_args: finalizacoes.append(True),
    }

    RespostaIARuntime(contexto_getter=lambda: contexto, log=lambda *_args: None).processar(
        "não lay, eu ainda estou no menu"
    )

    assert falas_locais == []
    assert len(modelo_bruto.pedidos) == 1
    assert modelo_bruto.pedidos[0].mensagens[-1]["content"] == (
        "não lay, eu ainda estou no menu"
    )
    assert finalizacoes == [True]


def test_prompt_compacto_grande_preserva_formato_mas_recebe_orcamento_contextual() -> None:
    """O tamanho real do payload, e não o rótulo rápido, governa o prazo HTTP."""

    class Modelo:
        def __init__(self):
            self.pedidos = []

        def executar(self, pedido):
            self.pedidos.append(pedido)
            return ResultadoModelo('{"fala":"Uma opção concreta.","comandos":[]}', True)

        @staticmethod
        def diagnostico():
            return {"disponivel": True}

    class Contexto:
        @staticmethod
        def montar():
            return {}

    modelo = Modelo()
    historico = [{"role": "system", "content": "evidência " * 850}]
    estado = EstadoConversaRuntime(
        getter=lambda: list(historico),
        setter=lambda novas: historico.__setitem__(slice(None), list(novas)),
    )
    contexto = {
        "processar_inicio_fluxo": lambda *_args: False,
        "usar_modo_rapido": lambda _texto: True,
        "texto_depende_de_contexto": lambda _texto: False,
        "modo_jogo_ativo": lambda: False,
        "estado_conversa": estado,
        "modelo_llm": RegistroModeloLLM.criar(modelo),
        "preparar_resposta": lambda *_args: {
            "resposta_bruta": "{}",
            "fala": "Uma opção concreta.",
            "comandos": [],
            "tipo_interacao": "conversa",
            "leitura_semantica": {},
        },
        "contexto_dispatch_runtime": Contexto(),
        "executar_comandos_json": lambda *_args: {
            "erros": [],
            "fala_ja_emitida": False,
            "fala_emitida_por_acao": False,
            "fala_salva_no_inicio": False,
        },
        "contexto_finalizacao_runtime": Contexto(),
        "finalizar_execucao": lambda *_args: {},
    }

    RespostaIARuntime(contexto_getter=lambda: contexto, log=lambda *_args: None).processar(
        "pode me recomendar um filme?"
    )

    assert len(modelo.pedidos) == 1
    assert modelo.pedidos[0].modo_rapido is True
    assert modelo.pedidos[0].classe_timeout == "contextual"

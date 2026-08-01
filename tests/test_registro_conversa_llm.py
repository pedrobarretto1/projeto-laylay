from __future__ import annotations

import pytest

from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.autonomia.dispatcher_comandos_json import executar_comandos_json
from mente_laylay.integracao.cliente_llm_runtime import ServicoModeloLLMRuntime
from mente_laylay.integracao.registro_conversa_llm import (
    EstadoConversaRuntime,
    ModeloLLMDiferidoRuntime,
    PacotePrompt,
    PedidoModelo,
    RegistroModeloLLM,
    RegistroPreparacaoConversa,
    ResultadoModelo,
    resolver_enviador_modelo,
)


class _Prompt:
    def __init__(self):
        self.chamadas = []

    def preparar_pacote(self, texto):
        self.chamadas.append(texto)
        return PacotePrompt(({"role": "system", "content": "personalidade"},))

    def diagnostico(self):
        return {"disponivel": True, "memoria_exposta": False, "segredo": "não sair"}


class _Modelo:
    def __init__(self):
        self.pedidos = []

    def executar(self, pedido):
        self.pedidos.append(pedido)
        return ResultadoModelo('{"fala":"Oi, eu tô bem.","comandos":[]}', True)

    def diagnostico(self):
        return {
            "disponivel": True,
            "memoria_exposta": False,
            "credencial_exposta": False,
            "api_key": "segredo",
        }


def test_registros_falham_cedo_quando_contrato_obrigatorio_esta_incompleto() -> None:
    with pytest.raises(RuntimeError, match="preparar_pacote"):
        RegistroPreparacaoConversa.criar(object())
    with pytest.raises(RuntimeError, match="executar"):
        RegistroModeloLLM.criar(object())


def test_registros_devolvem_copias_e_diagnostico_nao_expoe_segredos() -> None:
    prompt = RegistroPreparacaoConversa.criar(_Prompt())
    modelo = RegistroModeloLLM.criar(_Modelo())

    pacote = prompt.preparar_pacote("oi")
    pacote.mensagens[0]["content"] = "alterado fora"
    assert prompt.preparar_pacote("oi").mensagens[0]["content"] == "personalidade"
    assert "segredo" not in prompt.diagnostico()
    assert "api_key" not in modelo.diagnostico()
    assert modelo.diagnostico()["credencial_exposta"] is False


def test_estado_conversa_e_temporario_e_defensivo() -> None:
    estado = [{"role": "user", "content": "oi"}]
    porta = EstadoConversaRuntime(
        getter=lambda: estado,
        setter=lambda novas: estado.__setitem__(slice(None), novas),
    )
    copia = porta.mensagens()
    copia[0]["content"] = "fora"
    assert estado[0]["content"] == "oi"
    assert porta.diagnostico()["memoria_duravel"] is False


def test_fluxo_real_de_resposta_prefere_portas_tipadas_ao_adaptador_legado() -> None:
    eventos = []
    historico = []
    prompt = RegistroPreparacaoConversa.criar(_Prompt())
    modelo_bruto = _Modelo()
    modelo = RegistroModeloLLM.criar(modelo_bruto)
    estado = EstadoConversaRuntime(
        getter=lambda: historico,
        setter=lambda novas: historico.__setitem__(slice(None), novas),
    )

    class Contexto:
        @staticmethod
        def montar():
            return {}

    runtime = RespostaIARuntime(
        contexto_getter=lambda: {
            "usar_modo_rapido": lambda _texto: False,
            "processar_comandos_imediatos": lambda *_args, **_kwargs: False,
            "preparacao_conversa": prompt,
            "estado_conversa": estado,
            "modelo_llm": modelo,
            "enviar_mensagem": lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("adaptador legado não deveria ser chamado")
            ),
            "preparar_resposta": lambda *_args: {
                "resposta_bruta": "{}", "fala": "Oi, eu tô bem.", "comandos": [],
                "tipo_interacao": "conversa", "leitura_semantica": {},
            },
            "processar_comando_deterministico": lambda *_args: (_ for _ in ()).throw(
                AssertionError("o texto não pode ser reclassificado depois da LLM")
            ),
            "contexto_dispatch_runtime": Contexto(),
            "executar_comandos_json": lambda *_args: {
                "erros": [], "fala_ja_emitida": False,
                "fala_emitida_por_acao": False, "fala_salva_no_inicio": False,
            },
            "contexto_finalizacao_runtime": Contexto(),
            "finalizar_execucao": lambda *_args: eventos.append("finalizou"),
        },
        log=lambda *_args: None,
    )

    runtime.processar("como você está?")

    assert prompt.servico.chamadas == ["como você está?"]
    assert modelo_bruto.pedidos
    assert isinstance(modelo_bruto.pedidos[0], PedidoModelo)
    assert modelo_bruto.pedidos[0].mensagens[-1]["content"] == "como você está?"
    assert eventos == ["finalizou"]


def test_comando_prioritario_executa_antes_de_modelo_indisponivel() -> None:
    executados: list[str] = []
    runtime = RespostaIARuntime(
        contexto_getter=lambda: {
            "processar_comandos_prioritarios": lambda texto: executados.append(texto) or True,
            "modelo_llm": object(),
        },
        log=lambda *_args: None,
    )

    runtime.processar("liga a luz")

    assert executados == ["liga a luz"]


def test_dispatcher_vazio_nao_reclassifica_o_texto_no_pos_ia() -> None:
    retorno = executar_comandos_json(
        {
            "processar_comando_deterministico": lambda *_args: (_ for _ in ()).throw(
                AssertionError("dispatcher não pode reclassificar o turno")
            ),
        },
        "liga a luz",
        [],
        "",
        "conversa",
        False,
        False,
        False,
    )

    assert retorno == {
        "erros": [],
        "fala_emitida_por_acao": False,
        "fala_ja_emitida": False,
        "fala_salva_no_inicio": False,
    }


def test_modelo_tipado_nao_aceita_dicionario_cru() -> None:
    modelo = RegistroModeloLLM.criar(_Modelo())
    with pytest.raises(TypeError, match="PedidoModelo"):
        modelo.executar({"messages": []})  # type: ignore[arg-type]


def test_enviador_tipado_tem_precedencia_sobre_callback_legado() -> None:
    modelo_bruto = _Modelo()
    legado = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("callback legado não deveria ser chamado")
    )

    enviar = resolver_enviador_modelo(
        modelo_llm=RegistroModeloLLM.criar(modelo_bruto),
        enviar_mensagem=legado,
    )

    assert callable(enviar)
    assert "Oi, eu tô bem." in enviar([], _com_tools=False)
    assert len(modelo_bruto.pedidos) == 1


def test_modelo_diferido_mantem_porta_estavel_ate_conectar_transporte() -> None:
    diferido = ModeloLLMDiferidoRuntime()
    registro = RegistroModeloLLM.criar(diferido)
    pedido = PedidoModelo.criar([], com_tools=False)

    with pytest.raises(RuntimeError, match="ainda não conectado"):
        registro.executar(pedido)

    modelo_bruto = _Modelo()
    diferido.conectar(modelo_bruto)

    assert registro.executar(pedido).sucesso is True
    assert registro.diagnostico()["disponivel"] is True
    assert len(modelo_bruto.pedidos) == 1


def test_falha_parcial_na_preparacao_nao_chega_ao_transporte() -> None:
    class PreparadorFalho:
        def preparar(self, _pedido):
            raise RuntimeError("contexto indisponível")

    class Transporte:
        def executar(self, _requisicao):
            raise AssertionError("transporte não pode receber pedido incompleto")

    servico = ServicoModeloLLMRuntime(
        preparador=PreparadorFalho(), cliente=Transporte(),  # type: ignore[arg-type]
    )
    with pytest.raises(RuntimeError, match="contexto indisponível"):
        servico.executar(PedidoModelo.criar([]))

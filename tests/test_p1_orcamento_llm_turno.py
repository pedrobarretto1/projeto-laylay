from __future__ import annotations

from dataclasses import replace

import mente_laylay.integracao.cliente_llm_runtime as cliente_modulo
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
from mente_laylay.integracao.orcamento_llm_turno import OrcamentoLLMTurnoRuntime
from mente_laylay.integracao.preparador_requisicao_llm import (
    PreparadorRequisicaoLLMRuntime,
)
from mente_laylay.integracao.registro_conversa_llm import (
    PedidoModelo,
    RequisicaoTransporteLLM,
)


class Relogio:
    def __init__(self) -> None:
        self.agora = 100.0

    def __call__(self) -> float:
        return self.agora

    def avancar(self, segundos: float) -> None:
        self.agora += segundos


def test_turno_permite_principal_e_um_reparo_e_bloqueia_terceira_chamada() -> None:
    runtime = OrcamentoLLMTurnoRuntime()
    runtime.iniciar_turno("turno-1")

    principal = runtime.autorizar_chamada(tipo_chamada="principal")
    reparo = runtime.autorizar_chamada(tipo_chamada="reparo_factual")
    terceira = runtime.autorizar_chamada(tipo_chamada="reparo_comunicacao")

    assert principal.permitida is True
    assert reparo.permitida is True
    assert terceira.permitida is False
    assert terceira.motivo == "limite_chamadas"
    assert runtime.diagnostico()["chamadas_por_tipo"] == {
        "principal": 1,
        "reparo_factual": 1,
    }


def test_turno_bloqueia_principal_duplicada_e_segundo_tipo_de_reparo() -> None:
    runtime = OrcamentoLLMTurnoRuntime(max_chamadas_turno=4)
    runtime.iniciar_turno("turno-1")

    assert runtime.autorizar_chamada(tipo_chamada="principal").permitida
    duplicada = runtime.autorizar_chamada(tipo_chamada="principal")
    assert duplicada.permitida is False
    assert duplicada.motivo == "principal_duplicada"

    assert runtime.autorizar_chamada(tipo_chamada="reparo_json").permitida
    segundo_reparo = runtime.autorizar_chamada(tipo_chamada="continuacao")
    assert segundo_reparo.permitida is False
    assert segundo_reparo.motivo == "reparo_duplicado"


def test_interpretacao_e_principal_compartilham_o_mesmo_limite() -> None:
    runtime = OrcamentoLLMTurnoRuntime()
    runtime.iniciar_turno("turno-1")

    assert runtime.autorizar_chamada(tipo_chamada="interpretacao").permitida
    assert runtime.autorizar_chamada(tipo_chamada="principal").permitida
    bloqueada = runtime.autorizar_chamada(tipo_chamada="reparo_factual")

    assert bloqueada.permitida is False
    assert bloqueada.motivo == "limite_chamadas"


def test_classes_de_timeout_respeitam_prazo_total_do_turno() -> None:
    relogio = Relogio()
    runtime = OrcamentoLLMTurnoRuntime(monotonic=relogio)
    runtime.iniciar_turno("rapido", classe="rapida")
    assert runtime.autorizar_chamada(classe_timeout="normal").timeout_s == 8.0
    runtime.finalizar_turno("rapido")

    runtime.iniciar_turno("normal", classe="normal")
    relogio.avancar(3)
    assert runtime.autorizar_chamada(classe_timeout="normal").timeout_s == 17.0
    runtime.finalizar_turno("normal")

    runtime.iniciar_turno("longo", classe="normal")
    assert runtime.configurar_turno(classe="longa") is True
    assert runtime.autorizar_chamada(classe_timeout="longa").timeout_s == 60.0


def test_timeout_explicito_menor_nao_e_ampliado() -> None:
    runtime = OrcamentoLLMTurnoRuntime()
    runtime.iniciar_turno("turno-1", classe="longa")
    decisao = runtime.autorizar_chamada(
        classe_timeout="longa", timeout_solicitado=18,
    )
    assert decisao.timeout_s == 18.0


def test_prazo_esgotado_e_turno_obsoleto_bloqueiam_antes_da_rede() -> None:
    relogio = Relogio()
    runtime = OrcamentoLLMTurnoRuntime(monotonic=relogio)
    runtime.iniciar_turno("expirado", classe="rapida")
    relogio.avancar(8)
    decisao = runtime.autorizar_chamada()
    assert decisao.permitida is False
    assert decisao.motivo == "prazo_esgotado"

    atual = {"valor": True}
    runtime.iniciar_turno(
        "obsoleto", ainda_atual_cb=lambda: atual["valor"],
    )
    atual["valor"] = False
    decisao = runtime.autorizar_chamada()
    assert decisao.permitida is False
    assert decisao.motivo == "turno_obsoleto"


def test_cliente_nao_inicia_terceiro_transporte_no_mesmo_turno(monkeypatch) -> None:
    chamadas = []
    monkeypatch.setattr(
        cliente_modulo,
        "executar_chat_llm",
        lambda *_args, **_kwargs: chamadas.append(True) or "resposta válida",
    )
    orcamento = OrcamentoLLMTurnoRuntime()
    cliente = ClienteLLMRuntime(
        endpoint_local_getter=lambda: True,
        post_chat=lambda *_args, **_kwargs: None,
        orcamento_turno=orcamento,
        log=lambda *_args: None,
    )
    requisicao = RequisicaoTransporteLLM(
        payload={"messages": [{"role": "user", "content": "teste"}]},
        prioridade_interativa=True,
    )
    orcamento.iniciar_turno("turno-1")

    primeira = cliente.executar(requisicao)
    segunda = cliente.executar(replace(requisicao, tipo_chamada="reparo_factual"))
    terceira = cliente.executar(replace(requisicao, tipo_chamada="continuacao"))

    assert primeira.sucesso is True
    assert segunda.sucesso is True
    assert terceira.sucesso is False
    assert terceira.rota == "orcamento_bloqueado"
    assert len(chamadas) == 2


def test_cliente_descarta_resposta_que_ficou_obsoleta_durante_http(monkeypatch) -> None:
    atual = {"valor": True}

    def responder(*_args, **_kwargs):
        atual["valor"] = False
        return "resposta tardia que não deve vazar"

    monkeypatch.setattr(cliente_modulo, "executar_chat_llm", responder)
    orcamento = OrcamentoLLMTurnoRuntime()
    orcamento.iniciar_turno(
        "turno-1", ainda_atual_cb=lambda: atual["valor"],
    )
    cliente = ClienteLLMRuntime(
        endpoint_local_getter=lambda: True,
        post_chat=lambda *_args, **_kwargs: None,
        orcamento_turno=orcamento,
        log=lambda *_args: None,
    )

    resultado = cliente.executar(RequisicaoTransporteLLM(
        payload={"messages": [{"role": "user", "content": "teste"}]},
        prioridade_interativa=True,
    ))

    assert resultado.sucesso is False
    assert resultado.rota == "resposta_obsoleta"
    assert "tardia" not in resultado.texto


def test_circuito_abre_apos_falhas_e_fecha_com_sondagem_controlada() -> None:
    relogio = Relogio()
    runtime = OrcamentoLLMTurnoRuntime(
        monotonic=relogio,
        falhas_para_abrir_circuito=3,
        cooldown_circuito_s=15,
    )
    for _ in range(3):
        decisao = runtime.autorizar_chamada()
        assert decisao.permitida
        runtime.concluir_chamada(decisao, sucesso=False)

    assert runtime.diagnostico()["circuito_aberto"] is True
    bloqueada = runtime.autorizar_chamada()
    assert bloqueada.permitida is False
    assert bloqueada.motivo == "circuito_aberto"

    relogio.avancar(15)
    sondagem = runtime.autorizar_chamada()
    assert sondagem.permitida is True
    assert sondagem.probe_circuito is True
    concorrente = runtime.autorizar_chamada()
    assert concorrente.permitida is False
    assert concorrente.motivo == "probe_em_andamento"
    runtime.concluir_chamada(sondagem, sucesso=True)
    assert runtime.diagnostico()["circuito_aberto"] is False


def test_diagnostico_do_orcamento_nao_persiste_conteudo_do_usuario() -> None:
    runtime = OrcamentoLLMTurnoRuntime()
    runtime.iniciar_turno("meu segredo e token super privado")
    runtime.autorizar_chamada(tipo_chamada="conteúdo privado do prompt")
    retrato = repr(runtime.diagnostico()).casefold()

    assert "segredo" not in retrato
    assert "token" not in retrato
    assert "conteúdo" not in retrato
    assert runtime.diagnostico()["conteudo_persistido"] is False


def test_flag_desliga_orcamento_sem_mudar_timeout_historico() -> None:
    runtime = OrcamentoLLMTurnoRuntime(habilitado=False)
    assert runtime.iniciar_turno("turno-1") == {"modo": "desativado"}

    decisoes = [runtime.autorizar_chamada() for _ in range(4)]

    assert all(item.permitida for item in decisoes)
    assert all(item.timeout_s is None for item in decisoes)
    assert runtime.diagnostico()["modo"] == "desativado"


def test_preparador_propaga_tipo_e_classe_sem_alterar_contrato() -> None:
    runtime = PreparadorRequisicaoLLMRuntime(
        model="modelo",
        endpoint_local_getter=lambda: True,
        resumo_do_dia_getter=lambda: "",
        data_atual_getter=lambda: "2026-08-10",
        normalizar_texto=lambda texto: texto.casefold(),
        mapear_pastas=lambda *_args, **_kwargs: {},
        contexto_logs_getter=lambda: {},
        contexto_navegador_relevante=lambda *_args, **_kwargs: {},
        contexto_sistema_getter=lambda: {},
        obter_contexto_paginas=lambda *_args, **_kwargs: {},
        resumo_mente_integrada=lambda *_args, **_kwargs: "",
        log=lambda *_args: None,
    )
    pedido = PedidoModelo.criar(
        [{"role": "user", "content": "oi"}],
        tipo_chamada="reparo_comunicacao",
        classe_timeout="rapida",
    )

    requisicao = runtime.preparar(pedido)

    assert requisicao.tipo_chamada == "reparo_comunicacao"
    assert requisicao.classe_timeout == "rapida"


def test_resposta_runtime_abre_e_fecha_orcamento_mesmo_sem_texto() -> None:
    eventos = []
    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "iniciar_orcamento_llm_turno": (
            lambda turno_id, **kwargs: eventos.append(("inicio", turno_id, kwargs))
        ),
        "finalizar_orcamento_llm_turno": (
            lambda turno_id, **kwargs: eventos.append(("fim", turno_id, kwargs))
        ),
    }, log=lambda *_args: None)

    runtime.processar("")

    assert [item[0] for item in eventos] == ["inicio", "fim"]
    assert eventos[0][1] == eventos[1][1]

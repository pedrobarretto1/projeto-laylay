from __future__ import annotations

import threading

import mente_laylay.integracao.cliente_llm_runtime as cliente_llm_modulo
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
from mente_laylay.integracao.registro_conversa_llm import RequisicaoTransporteLLM
from mente_laylay.memoria_mental.diagnostico_mente import construir_diagnostico_mente
from mente_laylay.memoria_mental.formatacao_diagnostico import formatar_diagnostico_terminal
from mente_laylay.memoria_mental.observabilidade import ObservabilidadeMenteRuntime
from mente_laylay.personalidade.voz_runtime import VozRuntime


def _observabilidade(estado: dict) -> ObservabilidadeMenteRuntime:
    return ObservabilidadeMenteRuntime(
        estado_getter=lambda chave, padrao=None: estado.get(chave, padrao),
        estado_setter=lambda **campos: estado.update(campos),
        clock=lambda: 100.0,
    )


def test_metricas_calculam_percentis_e_segmentam_por_rota() -> None:
    estado: dict = {}
    runtime = _observabilidade(estado)
    runtime.iniciar_trace_turno("turno-000001", origem="chat", rota="llm_normal")

    for duracao in (10.0, 20.0, 30.0, 400.0):
        runtime.registrar_metrica("turno_total", duracao, True)

    metrica = estado["diagnostico_metricas"]["turno_total"]
    por_rota = estado["diagnostico_metricas_rotas"]["llm_normal"]["turno_total"]
    assert metrica["p50_ms"] == 20.0
    assert metrica["p95_ms"] == 400.0
    assert por_rota["p50_ms"] == 20.0
    assert por_rota["p95_ms"] == 400.0
    assert len(metrica["_janela_ms"]) == 4


def test_trace_guarda_so_identificadores_e_contagens_sanitizadas() -> None:
    estado: dict = {}
    runtime = _observabilidade(estado)
    segredo = "https://privado.test/conversa C:\\Users\\Pedro token=abc123"
    runtime.iniciar_trace_turno(segredo, origem=segredo, rota=segredo)
    runtime.registrar_metrica(
        "llm_http",
        25,
        True,
        backend="local",
        modelo=segredo,
        tipo_chamada="principal",
        tamanho_prompt_chars=7123,
        limite_saida_tokens=192,
    )
    runtime.finalizar_trace_turno(sucesso=True)

    serializado = repr(estado).casefold()
    assert "privado.test" not in serializado
    assert "pedro" not in serializado
    assert "abc123" not in serializado
    trace = estado["diagnostico_traces_turno"][-1]
    assert trace["chamadas_llm"] == 1
    assert trace["chamadas_llm_por_tipo"] == {"principal": 1}
    assert trace["tamanho_prompt_chars"] == 7123
    assert trace["limite_saida_tokens"] == 192
    assert trace["finalizado"] is True


def test_diagnostico_publica_p50_p95_e_trace_sem_janela_interna() -> None:
    mental: dict = {}
    runtime = _observabilidade(mental)
    runtime.iniciar_trace_turno("turno-000002", origem="chat", rota="llm_rapida")
    runtime.registrar_metrica("turno_total", 125, True)
    runtime.finalizar_trace_turno(sucesso=True)

    diagnostico = construir_diagnostico_mente(
        {"mental": mental, "conversacional": {}, "percepcao": {}, "continuidades": {}},
        {},
    )
    texto = formatar_diagnostico_terminal(diagnostico)

    assert diagnostico["latencias"]["turno_total"]["p50_ms"] == 125.0
    assert diagnostico["latencias_por_rota"]["llm_rapida"]["turno_total"]["p95_ms"] == 125.0
    assert diagnostico["traces_turno"][-1]["turno_id"] == "turno-000002"
    assert "_janela_ms" not in repr(diagnostico)
    assert "p50=125ms" in texto
    assert "trace recente:" in texto


def test_cliente_llm_mede_backend_modelo_tipo_e_tamanho_sem_prompt(monkeypatch) -> None:
    registros: list[tuple[tuple, dict]] = []
    monkeypatch.setattr(
        cliente_llm_modulo,
        "executar_chat_llm",
        lambda *_args, **_kwargs: "resposta pronta",
    )
    runtime = ClienteLLMRuntime(
        endpoint_local_getter=lambda: True,
        post_chat=lambda *_args, **_kwargs: None,
        registrar_metrica=lambda *args, **kwargs: registros.append((args, kwargs)),
        log=lambda *_args: None,
    )

    runtime.executar(RequisicaoTransporteLLM(
        payload={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "conteúdo privado"}],
            "max_tokens": 96,
        },
        tipo_chamada="reparo_comunicacao",
    ))

    args, metadados = registros[-1]
    assert args[0] == "llm_http"
    assert metadados == {
        "backend": "local",
        "modelo": "qwen3:4b",
        "tipo_chamada": "reparo_comunicacao",
        "tamanho_prompt_chars": len("conteúdo privado"),
        "limite_saida_tokens": 96,
    }
    assert "conteúdo privado" not in repr(registros)


def test_resposta_e_voz_compartilham_o_trace_sem_guardar_a_fala() -> None:
    mental: dict = {}
    observabilidade = _observabilidade(mental)
    contexto = {
        "iniciar_trace_diagnostico": observabilidade.iniciar_trace_turno,
        "atualizar_trace_diagnostico": observabilidade.atualizar_trace_turno,
        "finalizar_trace_diagnostico": observabilidade.finalizar_trace_turno,
        "registrar_metrica_diagnostico": observabilidade.registrar_metrica,
    }
    RespostaIARuntime(contexto_getter=lambda: contexto, log=lambda *_args: None).processar("")
    trace_id = mental["diagnostico_traces_turno"][-1]["turno_id"]
    assert mental["diagnostico_traces_turno"][-1]["finalizado"] is True

    observabilidade.iniciar_trace_turno("turno-voz", origem="chat", rota="llm_normal")
    voz = VozRuntime(
        fallback_fala="fallback",
        voice="voz",
        edge_tts_mod=None,
        sounddevice_mod=None,
        soundfile_mod=None,
        pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("", "", ""),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        interrupt_event=threading.Event(),
        trace_context_getter=observabilidade.obter_trace_corrente,
    )
    voz.iniciar_worker = lambda: None  # type: ignore[method-assign]
    voz.falar("fala que não pode entrar no trace")
    pedido = voz.fila.get_nowait()

    assert trace_id == "turno-000001"
    assert pedido["trace_context"]["turno_id"] == "turno-voz"
    assert "fala que não pode" not in repr(pedido["trace_context"]).casefold()


def test_janelas_de_percentil_e_trace_sao_limitadas() -> None:
    estado: dict = {}
    runtime = _observabilidade(estado)
    for indice in range(140):
        runtime.registrar_metrica("dispatcher", indice, True)
    assert len(
        estado["diagnostico_metricas"]["dispatcher"]["_janela_ms"]
    ) == 128

    for indice in range(45):
        runtime.iniciar_trace_turno(
            f"turno-{indice:06d}", origem="chat", rota="comando_prioritario",
        )
        runtime.finalizar_trace_turno(sucesso=True)
    assert len(estado["diagnostico_traces_turno"]) == 40

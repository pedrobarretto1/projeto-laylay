from __future__ import annotations

import threading

from mente_laylay.personalidade.voz_runtime import VozRuntime


def _runtime() -> VozRuntime:
    return VozRuntime(
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
        batch_window=0.2,
        batch_max_items=4,
    )


def test_falas_de_comandos_independentes_nao_sao_costuradas_por_proximidade() -> None:
    runtime = _runtime()
    reproduzidas: list[str] = []
    runtime.fila.put({
        "texto": "A lâmpada não respondeu.", "emocao": "irritada",
        "nivel": 1, "dinamizar": False,
    })
    runtime.fila.put({
        "texto": "Não encontrei o programa Plutão Azul.", "emocao": "calma",
        "nivel": 1, "dinamizar": False,
    })

    def reproduzir(texto: str, _emocao: str, _nivel: int) -> None:
        reproduzidas.append(texto)
        runtime.stop_event.set()

    runtime.reproduzir_fala = reproduzir  # type: ignore[method-assign]
    runtime.worker_de_falas()

    assert reproduzidas == ["A lâmpada não respondeu."]
    assert runtime.fila.qsize() == 1


def test_terminal_recebe_fala_consolidada_antes_do_inicio_do_audio() -> None:
    runtime = _runtime()
    eventos: list[tuple[str, str]] = []
    runtime.registrar_observador_inicio_fala(
        lambda texto, _emocao, _nivel, **_dados: eventos.append(
            ("terminal", texto),
        )
    )
    # O mesmo observador não pode duplicar a mensagem visual.
    observador = runtime._observadores_inicio_fala[0]
    runtime.registrar_observador_inicio_fala(observador)
    runtime.fila.put({
        "texto": "Resposta junto da voz.",
        "emocao": "feliz",
        "nivel": 2,
        "dinamizar": False,
        "proativa": False,
    })

    def reproduzir(texto: str, _emocao: str, _nivel: int) -> None:
        eventos.append(("audio", texto))
        runtime.stop_event.set()

    runtime.reproduzir_fala = reproduzir  # type: ignore[method-assign]
    runtime.worker_de_falas()

    assert eventos == [
        ("terminal", "Resposta junto da voz."),
        ("audio", "Resposta junto da voz."),
    ]


def test_falha_do_observador_visual_nao_impede_a_voz() -> None:
    logs: list[str] = []
    runtime = _runtime()
    runtime.log = logs.append
    reproduzidas: list[str] = []

    def observador_quebrado(*_args, **_kwargs) -> None:
        raise RuntimeError("janela fechada")

    runtime.registrar_observador_inicio_fala(observador_quebrado)
    runtime.fila.put({
        "texto": "A voz continua.",
        "emocao": "calma",
        "nivel": 1,
        "dinamizar": False,
        "proativa": True,
    })

    def reproduzir(texto: str, _emocao: str, _nivel: int) -> None:
        reproduzidas.append(texto)
        runtime.stop_event.set()

    runtime.reproduzir_fala = reproduzir  # type: ignore[method-assign]
    runtime.worker_de_falas()

    assert reproduzidas == ["A voz continua."]
    assert any("consumidor isolado falhou" in item for item in logs)

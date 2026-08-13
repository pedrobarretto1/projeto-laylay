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


def test_fala_publicada_antecipadamente_nao_duplica_no_inicio_do_audio() -> None:
    runtime = _runtime()
    eventos: list[tuple[str, str]] = []
    runtime.registrar_observador_inicio_fala(
        lambda texto, *_args, **_dados: eventos.append(("terminal", texto))
    )
    runtime.fila.put({
        "texto": "Já apareceu no Terminal.",
        "emocao": "calma",
        "nivel": 1,
        "dinamizar": False,
        "proativa": False,
        "texto_publicado_antecipado": True,
    })

    def reproduzir(texto: str, _emocao: str, _nivel: int) -> None:
        eventos.append(("audio", texto))
        runtime.stop_event.set()

    runtime.reproduzir_fala = reproduzir  # type: ignore[method-assign]
    runtime.worker_de_falas()

    assert eventos == [("audio", "Já apareceu no Terminal.")]


def test_lote_preserva_caminho_para_exibicao_e_limpa_somente_na_fronteira_tts() -> None:
    runtime = _runtime()
    runtime.limpar_para_voz = lambda texto: str(texto).replace("\\", " ").replace(":", "")
    caminho = r"C:\Users\pbarr\Downloads\teste capacidade.txt"

    texto_exibicao, _emocao, _nivel = runtime.combinar_falas_batch([{
        "texto": f"Criei {caminho}.",
        "emocao": "calma",
        "nivel": 1,
    }])

    assert caminho in texto_exibicao
    assert runtime.limpar_para_voz(texto_exibicao) != texto_exibicao


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


def test_fala_longa_sintetiza_inicio_curto_e_restante_em_paralelo(
    monkeypatch,
) -> None:
    monkeypatch.setenv("LAYLAY_TTS_ANTECIPAR_PRIMEIRA_FRASE", "1")
    runtime = _runtime()
    sintetizados: list[str] = []
    reproduzidos: list[str] = []
    metricas: list[tuple] = []

    class Som:
        def play(self, dados, *_args, **_kwargs):
            reproduzidos.append(str(dados[0]))

        @staticmethod
        def get_stream():
            return type("Stream", (), {"active": False})()

        @staticmethod
        def stop():
            return None

    class ArquivoSom:
        @staticmethod
        def read(caminho):
            return [caminho], 16000

    runtime.sd = Som()
    runtime.sf = ArquivoSom()
    runtime.registrar_metrica_cb = lambda *args, **_kwargs: metricas.append(args)
    runtime._selecionar_saida_audio = lambda: None  # type: ignore[method-assign]
    runtime._sintetizar_edge = (  # type: ignore[method-assign]
        lambda trecho, *_args, **_kwargs: sintetizados.append(trecho) or "voz"
    )
    texto = (
        "A China possui uma história antiga e contínua, registrada por muitas fontes. "
        "A dinastia Shang deixou os primeiros registros escritos conhecidos. "
        "Depois, a dinastia Qin unificou o território e padronizou a escrita. "
        "Os períodos seguintes alternaram unidade política e fragmentação regional."
    )

    runtime.reproduzir_fala(texto, "calma", 1)

    assert len(sintetizados) == 2
    assert sintetizados[0].endswith("fontes.")
    assert len(sintetizados[0]) < len(sintetizados[1])
    assert len(reproduzidos) == 2
    assert {item[0] for item in metricas} >= {
        "tts_sintese_primeiro_trecho", "tts_sintese", "tts_primeiro_audio",
    }


def test_pipeline_de_inicio_rapido_pode_ser_desligado(monkeypatch) -> None:
    monkeypatch.setenv("LAYLAY_TTS_ANTECIPAR_PRIMEIRA_FRASE", "0")
    texto = "Primeira frase suficientemente longa. " + "Segunda frase longa. " * 20

    assert VozRuntime._segmentar_fala_para_inicio_rapido(texto) == [texto.strip()]

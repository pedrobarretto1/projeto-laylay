from __future__ import annotations

import threading
import asyncio
import time

from mente_laylay.personalidade.voz_runtime import VozRuntime, resolver_vozes_tts


def _runtime(edge, *, voice="principal", fallback_voice="reserva", logs=None):
    return VozRuntime(
        fallback_fala="fallback",
        voice=voice,
        fallback_voice=fallback_voice,
        edge_tts_mod=edge,
        sounddevice_mod=None,
        soundfile_mod=None,
        pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("+0%", "+0Hz", "+0%"),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        interrupt_event=threading.Event(),
        log=(logs if logs is not None else []).append,
    )


def test_vozes_padrao_restauram_francisca_com_reserva_nativa() -> None:
    assert resolver_vozes_tts({}) == (
        "pt-BR-FranciscaNeural",
        "pt-BR-ThalitaMultilingualNeural",
    )


def test_vozes_podem_ser_trocadas_pelo_ambiente() -> None:
    assert resolver_vozes_tts({
        "LAYLAY_TTS_VOICE": "voz-personalizada",
        "LAYLAY_TTS_VOICE_FALLBACK": "voz-reserva",
    }) == ("voz-personalizada", "voz-reserva")


def test_falha_da_voz_principal_tenta_a_voz_de_reserva(tmp_path) -> None:
    chamadas = []
    logs = []

    class Edge:
        class Communicate:
            def __init__(self, _texto, *, voice, **_kwargs):
                self.voice = voice
                chamadas.append(voice)

            async def save(self, caminho):
                if self.voice == "principal":
                    raise RuntimeError("voz temporariamente indisponível")
                caminho.write_bytes(b"audio") if hasattr(caminho, "write_bytes") else None

    runtime = _runtime(Edge, logs=logs)
    voz_usada = runtime._sintetizar_edge(
        "Olá",
        str(tmp_path / "fala.mp3"),
        rate="+0%",
        pitch="+0Hz",
        volume="+0%",
    )

    assert voz_usada == "reserva"
    assert chamadas == ["principal", "reserva"]
    assert any("tentando reserva" in mensagem for mensagem in logs)


def test_sintese_neural_travada_respeita_timeout_total(tmp_path) -> None:
    logs = []

    class Edge:
        class Communicate:
            def __init__(self, *_args, **_kwargs):
                pass

            async def save(self, _caminho):
                await asyncio.sleep(1)

    runtime = _runtime(Edge, logs=logs)
    runtime.tts_timeout_s = 0.05
    inicio = time.perf_counter()
    try:
        runtime._sintetizar_edge(
            "Olá",
            str(tmp_path / "fala.mp3"),
            rate="+0%",
            pitch="+0Hz",
            volume="+0%",
        )
    except (TimeoutError, asyncio.TimeoutError):
        pass
    else:
        raise AssertionError("a síntese travada deveria expirar")

    assert time.perf_counter() - inicio < 0.3
    assert any("síntese neural excedeu" in mensagem for mensagem in logs)


def test_fala_identica_nao_entra_duas_vezes_na_fila() -> None:
    logs = []
    runtime = _runtime(None, logs=logs)
    runtime.iniciar_worker = lambda: None

    assert runtime.falar("Botando a música pra tocar agora.") is True
    assert runtime.falar("  botando a música pra tocar agora.  ") is False

    assert runtime.fila.qsize() == 1
    assert any("duplicata idêntica" in mensagem for mensagem in logs)

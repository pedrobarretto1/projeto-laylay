from __future__ import annotations

import threading
import asyncio
import time

import edge_tts
import pytest

from mente_laylay.personalidade.voz_runtime import criar_voz_runtime, resolver_vozes_tts


def _runtime(
    edge, *, voice="principal", fallback_voice="reserva", logs=None,
    preparar_tts=None, registrar_falha=None,
):
    return criar_voz_runtime(
        fallback_fala="fallback",
        voice=voice,
        fallback_voice=fallback_voice,
        edge_tts_mod=edge,
        sounddevice_mod=None,
        soundfile_mod=None,
        pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        preparar_tts_cb=preparar_tts,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("+0%", "+0Hz", "+0%"),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        interrupt_event=threading.Event(),
        registrar_falha_cb=registrar_falha,
        log=(logs if logs is not None else []).append,
    )


def test_vozes_padrao_preservam_identidade_sem_reserva_implicita() -> None:
    assert resolver_vozes_tts({}) == (
        "pt-BR-FranciscaNeural",
        "",
    )


def test_vozes_podem_ser_trocadas_pelo_ambiente() -> None:
    assert resolver_vozes_tts({
        "LAYLAY_TTS_VOICE": "voz-personalizada",
        "LAYLAY_TTS_VOICE_FALLBACK": "voz-reserva",
    }) == ("voz-personalizada", "voz-reserva")


@pytest.mark.parametrize("voice", [
    "pt-BR-FranciscaNeural", "pt-BR-ThalitaMultilingualNeural",
])
def test_transporte_legado_migra_antes_da_sintese_sem_trocar_voz(
    monkeypatch, voice,
) -> None:
    token = edge_tts.constants.TRUSTED_CLIENT_TOKEN
    monkeypatch.setattr(
        edge_tts.communicate, "WSS_URL",
        "wss://speech.platform.bing.com/consumer/speech/synthesize/"
        f"readaloud/edge/v1?TrustedClientToken={token}",
    )
    # A biblioteca normaliza o nome curto para o nome canônico do serviço.
    voz_canonica = edge_tts.Communicate("controle", voice=voice).tts_config.voice
    logs = []
    runtime = _runtime(edge_tts, voice=voice, logs=logs)
    comunicacao = runtime._criar_comunicacao_edge(
        "Oi lay", voice=voice, rate="+3%", pitch="+2Hz", volume="+0%",
    )

    assert edge_tts.communicate.WSS_URL == (
        "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"
        f"?Ocp-Apim-Subscription-Key={token}"
    )
    assert comunicacao.tts_config.voice == voz_canonica
    assert comunicacao.tts_config.rate == "+3%"
    assert comunicacao.tts_config.pitch == "+2Hz"
    runtime._criar_comunicacao_edge(
        "outra fala", voice=voice, rate="+0%", pitch="+0Hz", volume="+0%",
    )
    assert len(logs) == 1


@pytest.mark.parametrize("url", [
    "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1?novo=1",
    "wss://outro-provedor.example/tts",
])
def test_transporte_atual_ou_personalizado_nao_e_substituido(monkeypatch, url):
    monkeypatch.setattr(edge_tts.communicate, "WSS_URL", url)
    logs = []
    runtime = _runtime(edge_tts, voice="pt-BR-ThalitaMultilingualNeural", logs=logs)
    for _ in range(2):
        runtime._criar_comunicacao_edge(
            "Olá", voice=runtime.voice, rate="+0%", pitch="+0Hz", volume="+0%",
        )
    assert edge_tts.communicate.WSS_URL == url
    assert logs == []


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


@pytest.mark.parametrize("segmentada", [False, True])
def test_falha_de_audio_nao_autoriza_trocar_para_voz_local_implicita(segmentada):
    chamadas, locais, logs, metricas, falhas = [], [], [], [], []
    runtime = _runtime(None, fallback_voice="", logs=logs,
        registrar_falha=lambda *a, **k: falhas.append((a, k)))
    runtime.registrar_metrica_cb = lambda nome, valor, ok: metricas.append((nome, ok))
    runtime.fallback_pyttsx = lambda texto, *_: locais.append(texto) or True
    runtime._segmentar_fala_para_inicio_rapido = lambda _: (["Primeira parte.", "Segunda parte."]
        if segmentada else ["Resposta textual preservada."])
    def sintetizar(texto, *_a, **_k):
        chamadas.append(texto)
        if not segmentada or texto == "Segunda parte.":
            raise RuntimeError("transporte temporariamente indisponível")
    runtime._sintetizar_edge = sintetizar
    runtime.sf = type("SF", (), {"read": staticmethod(lambda _: ([], 16000))})
    runtime.sd = type("SD", (), {"play": staticmethod(lambda *_a, **_k: None),
        "get_stream": staticmethod(lambda: type("Stream", (), {"active": False})())})
    runtime._selecionar_saida_audio = lambda: 0
    assert runtime.reproduzir_fala("Resposta textual preservada.", "calma", 1) is False
    assert chamadas and locais == [], "falha de transporte não concede escolha de outro timbre"
    assert "Resposta textual preservada." in logs
    assert ("tts_total", False) in metricas
    assert falhas and any("texto_preservado" in str(k.get("fallback", "")) for _, k in falhas)


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


def test_modo_silencioso_nao_inicia_worker_nem_enfileira_audio() -> None:
    logs = []
    runtime = _runtime(None, logs=logs)
    workers_iniciados: list[bool] = []
    runtime.thread_factory = lambda **_kwargs: workers_iniciados.append(True)

    assert runtime.definir_modo_silencioso(
        True, origem="roteiro_teste",
    ) is True
    runtime.iniciar_worker()

    assert runtime.falar("Resposta textual preservada.") is True
    assert runtime.falar(
        "Aviso proativo sem áudio.", _proativa=True,
    ) is False
    assert workers_iniciados == []
    assert runtime.worker_started is False
    assert runtime.fila.empty()
    assert runtime.modo_silencioso_ativo() is True
    assert "Resposta textual preservada." in logs
    assert "Aviso proativo sem áudio." in logs

    assert runtime.definir_modo_silencioso(
        False, origem="roteiro_teste_finalizado",
    ) is False
    assert runtime.modo_silencioso_ativo() is False
    assert any("reprodução suspensa" in mensagem for mensagem in logs)
    assert any("reprodução restaurada" in mensagem for mensagem in logs)


def test_falha_na_adaptacao_oral_usa_texto_original_e_vai_ao_diagnostico(tmp_path) -> None:
    falhas = []
    logs = []
    runtime = _runtime(
        None,
        logs=logs,
        preparar_tts=lambda _texto: (_ for _ in ()).throw(RuntimeError("segredo")),
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
    )
    runtime._sintetizar_edge = lambda texto, *_args, **_kwargs: texto
    runtime.sf = type("SF", (), {"read": staticmethod(lambda _path: ([], 16000))})
    runtime.sd = type(
        "SD", (),
        {
            "play": staticmethod(lambda *_args, **_kwargs: None),
            "get_stream": staticmethod(lambda: type("Stream", (), {"active": False})()),
        },
    )
    runtime._selecionar_saida_audio = lambda: 0

    runtime.reproduzir_fala("fala original", "calma", 1)

    assert falhas[0][0] == ("voz", "falha_adaptacao_oral")
    assert falhas[0][1]["fallback"] == "texto_original"

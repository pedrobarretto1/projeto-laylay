"""RT1-B — corrida acústica H3 através do grafo montado pelo root.

Esta prova NÃO remonta Ouvido, Diretor, Ponte, Coordenador ou owner.

Ela:
1. importa `laylay.py`;
2. obtém "Laylay-Ouvido" do catálogo que o bootstrap usa;
3. substitui SOMENTE bordas externas controláveis (sounddevice/numpy/modelo);
4. faz o VAD real detectar uma utterance;
5. encerra a captura acústica;
6. bloqueia o modelo durante o STT assíncrono;
7. consulta o contexto pelo Diretor montado pelo root.

Contrato procurado na janela histórica H3:

    usuario_falando == False
    turno_ativo == False
    interacao_usuario_ativa == True

e, portanto:

    Diretor._bloqueio_contextual(...) == "interacao_usuario_ativa"

CAPTURE END != USER TURN END
USER INTERACTION OWNERSHIP > AUTONOMOUS PRESENCE
"""

from __future__ import annotations

import importlib
import threading
import time
from types import SimpleNamespace

import numpy as np


def _esperar(predicado, timeout=2.0, intervalo=0.005):
    prazo = time.monotonic() + timeout
    ultimo = None
    while time.monotonic() < prazo:
        ultimo = predicado()
        if ultimo:
            return ultimo
        time.sleep(intervalo)
    return ultimo


class _StreamAcusticoControlado:
    """Produz calibração -> voz -> silêncio, com barreira após o VAD."""

    def __init__(
        self,
        *,
        vad_confirmado: threading.Event,
        liberar_fim_fala: threading.Event,
    ) -> None:
        self.vad_confirmado = vad_confirmado
        self.liberar_fim_fala = liberar_fim_fala
        self.indice = 0

        # 3 blocos de calibração (mínimo real = 0.3 s)
        # 2 blocos acima do limiar para confirmar o VAD
        # 4 blocos de silêncio para fechar a utterance (mínimo real = 0.4 s)
        self.amplitudes = [
            0.001, 0.001, 0.001,
            0.080, 0.080,
            0.000, 0.000, 0.000, 0.000,
        ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, bloco):
        # Esta chamada acontece DEPOIS de o loop real ter processado o
        # segundo bloco de voz e marcado _usuario_falando=True.
        if self.indice == 5:
            self.vad_confirmado.set()
            if not self.liberar_fim_fala.wait(timeout=2.0):
                raise RuntimeError("timeout esperando liberação após VAD")

        if self.indice < len(self.amplitudes):
            amplitude = self.amplitudes[self.indice]
            self.indice += 1
        else:
            amplitude = 0.0
            time.sleep(0.005)

        dados = np.full((bloco, 1), amplitude, dtype=np.float32)
        return dados, False


class _SoundDeviceControlado:
    def __init__(self, stream):
        self._stream = stream
        self.default = SimpleNamespace(device=(0, -1))

    def query_devices(self):
        return [
            {
                "name": "RT1-B Microfone Controlado",
                "max_input_channels": 1,
                "max_output_channels": 0,
                "default_samplerate": 16000,
            }
        ]

    def query_hostapis(self):
        return [{"default_input_device": 0, "default_output_device": -1}]

    def check_input_settings(self, **_kwargs):
        return None

    def InputStream(self, **_kwargs):
        return self._stream


class _ModeloWhisperControlado:
    """A primeira transcrição representa a janela de STT pendente."""

    def __init__(
        self,
        *,
        stt_entrou: threading.Event,
        liberar_stt: threading.Event,
        stt_finalizou: threading.Event,
    ) -> None:
        self.stt_entrou = stt_entrou
        self.liberar_stt = liberar_stt
        self.stt_finalizou = stt_finalizou
        self.chamadas = 0

    def transcribe(self, _audio, **_kwargs):
        self.chamadas += 1
        info = SimpleNamespace(language_probability=1.0)

        if self.chamadas == 1:
            self.stt_entrou.set()
            if not self.liberar_stt.wait(timeout=3.0):
                raise RuntimeError("timeout esperando liberação do STT")
            # Resultado vazio de propósito: depois da prova não queremos
            # iniciar um turno/LLM real. O runtime fará sua segunda tentativa.
            return [], info

        # Segunda tentativa também vazia; encerra o trabalho de STT sem
        # entregar texto à entrada canônica.
        self.stt_finalizou.set()
        return [], info


def test_rt1b_stt_pendente_preserva_owner_no_root_e_bloqueia_presenca():
    root = importlib.import_module("laylay")

    composicao = root._composicao_servicos_runtime
    catalogo = composicao.catalogo_threads()
    alvo_ouvido = catalogo["Laylay-Ouvido"]

    ouvido = root._ouvido_whisper_runtime
    diretor = root._diretor_presenca_runtime

    # Pré-condição já provada pelo RT1-A, repetida aqui para impedir que esta
    # prova seja acidentalmente executada sobre outro objeto.
    assert getattr(alvo_ouvido, "__self__", None) is ouvido

    vad_confirmado = threading.Event()
    liberar_fim_fala = threading.Event()
    stt_entrou = threading.Event()
    liberar_stt = threading.Event()
    stt_finalizou = threading.Event()
    parar = threading.Event()

    stream = _StreamAcusticoControlado(
        vad_confirmado=vad_confirmado,
        liberar_fim_fala=liberar_fim_fala,
    )
    sd_fake = _SoundDeviceControlado(stream)
    modelo_fake = _ModeloWhisperControlado(
        stt_entrou=stt_entrou,
        liberar_stt=liberar_stt,
        stt_finalizou=stt_finalizou,
    )

    antigos = {
        "sd": getattr(ouvido, "sd", None),
        "np": getattr(ouvido, "np", None),
        "model_factory": getattr(ouvido, "model_factory", None),
        "modelo": getattr(ouvido, "modelo", None),
        "env_getter": getattr(ouvido, "env_getter"),
        "deve_continuar": getattr(ouvido, "deve_continuar"),
    }

    overrides_env = {
        "LAYLAY_MICROFONE_ATIVO": "1",
        "LAYLAY_MICROFONE": "",
        "LAYLAY_MICROFONE_SAMPLE_RATE": "16000",
        "LAYLAY_MICROFONE_LIMIAR": "0.012",
        "LAYLAY_MICROFONE_CALIBRACAO": "0.3",
        "LAYLAY_MICROFONE_SILENCIO": "0.4",
        "LAYLAY_MICROFONE_MAX_SEGUNDOS": "3.0",
        "LAYLAY_WHISPER_CARREGAR_NO_INICIO": "0",
        "LAYLAY_WHISPER_MODELO": "rt1-b-controlado",
        "LAYLAY_WHISPER_DEVICE": "cpu",
        "LAYLAY_WHISPER_COMPUTE_TYPE": "int8",
    }

    def env_controlado(nome, padrao=""):
        return overrides_env.get(nome, padrao)

    ouvido.sd = sd_fake
    ouvido.np = np
    ouvido.model_factory = lambda *_args, **_kwargs: modelo_fake
    ouvido.modelo = None
    ouvido.env_getter = env_controlado
    ouvido.deve_continuar = lambda: not parar.is_set()

    erro_captura = []

    def executar_ouvido():
        try:
            alvo_ouvido()
        except BaseException as exc:  # deixa a causa aparecer na assertiva
            erro_captura.append(exc)

    thread_ouvido = threading.Thread(
        target=executar_ouvido,
        daemon=True,
        name="RT1-B-Laylay-Ouvido",
    )

    try:
        thread_ouvido.start()

        assert vad_confirmado.wait(timeout=2.0), (
            "o VAD real do Ouvido do root não alcançou a confirmação de voz"
        )
        assert ouvido.usuario_falando() is True, (
            "a barreira pós-VAD foi alcançada, mas usuario_falando não ficou True"
        )

        # Permite os blocos de silêncio encerrarem a captura.
        liberar_fim_fala.set()

        assert stt_entrou.wait(timeout=2.0), (
            "a captura terminou, mas o worker real não alcançou o modelo Whisper"
        )

        # Esta é exatamente a janela histórica H3.
        assert ouvido.usuario_falando() is False, (
            "o STT está pendente, mas a fase acústica ainda consta como ativa; "
            "a janela H3 não foi reproduzida"
        )

        contexto = diretor._contexto()

        assert not bool(contexto.get("usuario_falando")), (
            "pré-condição H3 inválida: o contexto ainda publica usuario_falando=True"
        )
        assert not bool(contexto.get("turno_ativo")), (
            "pré-condição H3 inválida: um turno já começou antes de o STT terminar"
        )

        assert contexto.get("interacao_usuario_ativa") is True, (
            "RT1-B RED: durante STT pendente o root perdeu ownership do usuário. "
            "VAD já terminou e turno ainda não começou, mas o contexto real do "
            "Diretor não publicou interacao_usuario_ativa=True. "
            f"contexto={{'usuario_falando': {contexto.get('usuario_falando')!r}, "
            f"'turno_ativo': {contexto.get('turno_ativo')!r}, "
            f"'interacao_usuario_ativa': "
            f"{contexto.get('interacao_usuario_ativa')!r}}}"
        )

        evento = {
            "dominio": "cotidiano",
            "categoria": "companhia",
            "motivo": "evento controlado RT1-B durante STT pendente",
            "confianca": 0.95,
            "timestamp": time.time(),
            "validade_s": 120.0,
        }
        motivo = diretor._bloqueio_contextual(
            evento,
            contexto,
            float(diretor.clock()),
        )
        assert motivo == "interacao_usuario_ativa", (
            "o owner chegou ao contexto do Diretor, mas a fronteira cognitiva "
            f"não o tratou como prioridade; motivo={motivo!r}"
        )

    finally:
        # Libera o fake Whisper; ele devolve texto vazio para não iniciar LLM
        # ou executar uma ação real depois da prova.
        liberar_fim_fala.set()
        liberar_stt.set()
        stt_finalizou.wait(timeout=1.0)

        # Dá tempo ao _entregar() real de finalizar e liberar eventual claim.
        _esperar(
            lambda: getattr(ouvido._fila_audio, "unfinished_tasks", 0) == 0,
            timeout=1.5,
        )

        parar.set()
        thread_ouvido.join(timeout=1.0)
        worker = getattr(ouvido, "_worker_audio", None)
        if worker is not None and worker.is_alive():
            worker.join(timeout=0.6)

        ouvido.sd = antigos["sd"]
        ouvido.np = antigos["np"]
        ouvido.model_factory = antigos["model_factory"]
        ouvido.modelo = antigos["modelo"]
        ouvido.env_getter = antigos["env_getter"]
        ouvido.deve_continuar = antigos["deve_continuar"]

    assert not erro_captura, (
        "o serviço acústico do root encerrou com erro inesperado: "
        + repr(erro_captura[0])
    )

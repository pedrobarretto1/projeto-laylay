from __future__ import annotations

import threading
from typing import Any

import numpy as np

from mente_laylay.autonomia.execucao_ia import CoordenadorExecRuntime
from mente_laylay.integracao.prioridade_interacao_usuario import (
    criar_prioridade_interacao_usuario_runtime,
)
from mente_laylay.percepcao.ouvido_whisper import OuvidoWhisperRuntime


class _PrioridadeObservavel:
    """Usa o owner REAL e registra somente transições efetivas."""

    def __init__(self) -> None:
        self.real = criar_prioridade_interacao_usuario_runtime()
        self.transicoes: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def _registrar(self, operacao: str, referencia: str) -> None:
        snapshot = self.real.snapshot()

        with self._lock:
            self.transicoes.append(
                {
                    "operacao": operacao,
                    "referencia": referencia,
                    "ativa": bool(snapshot["ativa"]),
                    "total_claims": int(snapshot["total_claims"]),
                    "fontes_ativas": list(snapshot["fontes_ativas"]),
                }
            )

    def adquirir(self, fonte: str) -> str:
        claim = self.real.adquirir(fonte)
        self._registrar("adquirir", fonte)
        return claim

    def liberar(self, claim: str) -> bool:
        liberou = self.real.liberar(claim)

        # Release stale não representa transição real de ownership.
        if liberou:
            self._registrar("liberar", str(claim))

        return liberou

    def ativa(self) -> bool:
        return self.real.ativa()

    def snapshot(self) -> dict[str, Any]:
        return self.real.snapshot()


class _RespostaBloqueada:
    def __init__(
        self,
        *,
        entrou: threading.Event,
        liberar: threading.Event,
    ) -> None:
        self.entrou = entrou
        self.liberar = liberar
        self.chamadas: list[tuple[str, str]] = []

    def processar(
        self,
        texto: str,
        ainda_atual_cb=None,
        origem: str = "desconhecida",
    ) -> None:
        if callable(ainda_atual_cb):
            assert ainda_atual_cb() is True

        self.chamadas.append((texto, origem))
        self.entrou.set()

        self.liberar.wait(timeout=2.0)


class _StreamControlado:
    def __init__(
        self,
        blocos: list[np.ndarray],
        *,
        encerrar: threading.Event,
    ) -> None:
        self._blocos = list(blocos)
        self._encerrar = encerrar

    def __enter__(self):
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def read(self, bloco: int):
        if self._blocos:
            return self._blocos.pop(0), False

        # Depois que a utterance terminou, mantém o capturador vivo sem
        # gerar outra fala até o teste mandar encerrar.
        self._encerrar.wait(timeout=2.0)

        return np.zeros(bloco, dtype=np.float32), False


class _SoundDeviceControlado:
    def __init__(self, stream: _StreamControlado) -> None:
        self.stream = stream

    def InputStream(self, **_kwargs: Any):
        return self.stream


def test_red_p1hc2_coordenador_possui_entrada_ate_resposta_terminar() -> None:
    prioridade = _PrioridadeObservavel()

    resposta_entrou = threading.Event()
    liberar_resposta = threading.Event()

    resposta = _RespostaBloqueada(
        entrou=resposta_entrou,
        liberar=liberar_resposta,
    )

    coordenador = CoordenadorExecRuntime(
        contexto_exec_getter=lambda: None,
        resposta_ia_getter=lambda: resposta,
        loop_getter=lambda: None,
        prioridade_interacao=prioridade,
        log=lambda *_args: None,
    )

    worker = None

    try:
        worker = coordenador.agendar(
            "teste de ownership",
            origem="voz",
        )

        assert resposta_entrou.wait(timeout=1.0)

        # A entrada já saiu de agendar() e está sendo processada.
        assert resposta.chamadas == [
            ("teste de ownership", "voz"),
        ]

        snapshot = prioridade.snapshot()

        assert snapshot["ativa"] is True
        assert "entrada_canonica" in set(snapshot["fontes_ativas"])

    finally:
        liberar_resposta.set()

        if isinstance(worker, threading.Thread):
            worker.join(timeout=1.0)

    # O Coordenador só libera depois de processar() realmente terminar.
    assert prioridade.ativa() is False


def test_red_p1hc2_voz_transfere_para_entrada_sem_janela_livre() -> None:
    prioridade = _PrioridadeObservavel()

    entrou_stt = threading.Event()
    liberar_stt = threading.Event()

    resposta_entrou = threading.Event()
    liberar_resposta = threading.Event()

    encerrar_captura = threading.Event()
    continuar = [True]

    resposta = _RespostaBloqueada(
        entrou=resposta_entrou,
        liberar=liberar_resposta,
    )

    coordenador = CoordenadorExecRuntime(
        contexto_exec_getter=lambda: None,
        resposta_ia_getter=lambda: resposta,
        loop_getter=lambda: None,
        prioridade_interacao=prioridade,
        log=lambda *_args: None,
    )

    bloco = 1600

    silencio = np.zeros(bloco, dtype=np.float32)
    voz = np.full(bloco, 0.08, dtype=np.float32)

    blocos = [
        # Calibração mínima: 0.3 s.
        silencio.copy(),
        silencio.copy(),
        silencio.copy(),

        # Voz suficiente para disparar VAD e manter duração >= 0.6 s.
        voz.copy(),
        voz.copy(),
        voz.copy(),
        voz.copy(),
        voz.copy(),
        voz.copy(),

        # Silêncio final de 0.4 s.
        silencio.copy(),
        silencio.copy(),
        silencio.copy(),
        silencio.copy(),
    ]

    stream = _StreamControlado(
        blocos,
        encerrar=encerrar_captura,
    )

    sd = _SoundDeviceControlado(stream)

    env = {
        "LAYLAY_MICROFONE_ATIVO": "1",
        "LAYLAY_MICROFONE_CALIBRACAO": "0.3",
        "LAYLAY_MICROFONE_LIMIAR": "0.01",
        "LAYLAY_MICROFONE_SILENCIO": "0.4",
        "LAYLAY_MICROFONE_MAX_SEGUNDOS": "3",
        "LAYLAY_WHISPER_CONFIANCA_MINIMA": "0.20",
        "LAYLAY_WHISPER_CONFIANCA_ALTA": "0.60",
        "LAYLAY_WHISPER_CARREGAR_NO_INICIO": "0",
    }

    ouvido = OuvidoWhisperRuntime(
        processar_texto=lambda texto: coordenador.agendar(
            texto,
            origem="voz",
        ),
        esta_falando=lambda: False,
        escuta_permitida=lambda: True,
        modo_chat_ativo=lambda: False,
        modo_jogo_ativo=lambda: True,
        sounddevice_mod=sd,
        numpy_mod=np,
        deve_continuar=lambda: continuar[0],
        entrega_assincrona=True,
        env_getter=lambda nome, padrao="": env.get(nome, padrao),
        prioridade_interacao=prioridade,
        log=lambda *_args: None,
    )

    # Evita seleção real de hardware.
    ouvido.selecionar_dispositivo = lambda: (  # type: ignore[method-assign]
        0,
        {"name": "Microfone HC2"},
    )
    ouvido._origem_dispositivo = "teste_hc2"

    def transcrever_bloqueado(_audio: Any) -> tuple[str, float]:
        entrou_stt.set()

        liberar_stt.wait(timeout=2.0)

        return "laylay, teste de handoff", 0.99

    ouvido.transcrever_com_confianca = (  # type: ignore[method-assign]
        transcrever_bloqueado
    )

    erros_captura: list[BaseException] = []

    def executar_ouvido() -> None:
        try:
            ouvido.executar()
        except BaseException as erro:
            erros_captura.append(erro)

    thread_captura = threading.Thread(
        target=executar_ouvido,
        daemon=True,
    )
    thread_captura.start()

    try:
        # -----------------------------------------------------
        # FASE A — captura terminou, STT ainda está trabalhando
        # -----------------------------------------------------

        assert entrou_stt.wait(timeout=1.0)

        # O VAD acústico já terminou.
        assert ouvido.usuario_falando() is False

        # Mas a utterance continua pertencendo ao usuário.
        snapshot_stt = prioridade.snapshot()

        assert snapshot_stt["ativa"] is True
        assert "voz" in set(snapshot_stt["fontes_ativas"])

        # -----------------------------------------------------
        # FASE B — STT entrega para entrada canônica
        # -----------------------------------------------------

        liberar_stt.set()

        assert resposta_entrou.wait(timeout=1.0)

        snapshot_resposta = prioridade.snapshot()

        # Neste ponto processar_texto() já retornou para o ouvido,
        # então o claim de voz pode ter acabado.
        #
        # O Coordenador, porém, obrigatoriamente já assumiu.
        assert snapshot_resposta["ativa"] is True
        assert "entrada_canonica" in set(
            snapshot_resposta["fontes_ativas"]
        )

        # -----------------------------------------------------
        # CONTRATO CENTRAL DO HC2
        # -----------------------------------------------------

        transicoes = list(prioridade.transicoes)

        assert transicoes

        # Desde a PRIMEIRA aquisição até antes do ÚLTIMO release
        # não pode existir nenhuma observação ativa=False.
        #
        # Se aparecer False aqui, tivemos:
        #
        #   release voz
        #       ↓
        #   PRIORIDADE LIVRE  ❌
        #       ↓
        #   acquire entrada
        assert all(
            transicao["ativa"] is True
            for transicao in transicoes[:-1]
        )

    finally:
        liberar_stt.set()
        liberar_resposta.set()

        continuar[0] = False
        encerrar_captura.set()

        thread_captura.join(timeout=1.0)

        worker_audio = ouvido._worker_audio

        if worker_audio is not None:
            worker_audio.join(timeout=1.0)

    assert erros_captura == []

    # Depois que a resposta canônica acabou, nenhum estágio possui
    # mais a interação.
    assert prioridade.ativa() is False

    transicoes = list(prioridade.transicoes)

    assert transicoes
    assert transicoes[-1]["ativa"] is False
"""P1-H3-R — STT pendente preserva ownership canônico.

Sucessor causal do H3 histórico.

Diferentemente do teste antigo, este não chama _agendar_entrega() manualmente.
Ele atravessa executar() com um InputStream controlado:

calibração -> VAD real -> claim "voz" -> fim acústico -> STT assíncrono

Durante o STT:
    usuario_falando == False
    interacao_usuario_ativa == True

Logo, presença autônoma deve perder a vez.
"""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace
from typing import Any

import numpy as np

from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.integracao.ponte_iniciativa_aplicacao import (
    PonteIniciativaAplicacaoRuntime,
)
from mente_laylay.integracao.prioridade_interacao_usuario import (
    criar_prioridade_interacao_usuario_runtime,
)
from mente_laylay.percepcao.ouvido_whisper import OuvidoWhisperRuntime


def _turno_evento_valido(evento: dict[str, Any]) -> dict[str, Any]:
    contrato = {
        "funcao": "reacao_evento",
        "natureza_entrada": "evento",
        "entrada_cognitiva": dict(evento),
        "autoridade_usuario": False,
        "permissao_execucao": False,
        "autoriza_execucao": False,
    }
    return {
        "natureza_entrada": "evento",
        "entrada_cognitiva": dict(evento),
        "autoridade_usuario": False,
        "permissao_execucao": False,
        "autoriza_execucao": False,
        "contrato_fala": contrato,
    }


class _InputStreamControlado:
    """Entrega blocos determinísticos; depois mantém silêncio."""

    def __init__(self, blocos: list[np.ndarray], continuar: list[bool]) -> None:
        self._blocos = list(blocos)
        self._continuar = continuar
        self._lock = threading.Lock()

    def __enter__(self) -> "_InputStreamControlado":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def read(self, bloco: int) -> tuple[np.ndarray, bool]:
        with self._lock:
            if self._blocos:
                dados = self._blocos.pop(0)
            else:
                dados = np.zeros(bloco, dtype=np.float32)

        # Evita loop quente depois que a sequência controlada termina.
        if not self._blocos:
            time.sleep(0.005)

        return np.asarray(dados, dtype=np.float32).reshape(-1, 1), False


class _SoundDeviceControlado:
    def __init__(
        self,
        blocos: list[np.ndarray],
        continuar: list[bool],
    ) -> None:
        self._stream = _InputStreamControlado(blocos, continuar)

    def InputStream(self, **_kwargs: Any) -> _InputStreamControlado:
        return self._stream


def test_p1h3r_stt_pendente_mantem_owner_e_bloqueia_presenca() -> None:
    entrou_no_stt = threading.Event()
    liberar_stt = threading.Event()
    entrada_entregue = threading.Event()
    captura_finalizada = threading.Event()

    continuar = [True]
    textos_entregues: list[str] = []
    cognicoes_presenca: list[dict[str, Any]] = []

    prioridade = criar_prioridade_interacao_usuario_runtime()

    # executar() usa blocos de 100 ms.
    bloco = 1600

    silencio_calibracao = np.full(
        bloco,
        0.001,
        dtype=np.float32,
    )
    voz = np.full(
        bloco,
        0.08,
        dtype=np.float32,
    )
    silencio = np.zeros(
        bloco,
        dtype=np.float32,
    )

    # 3 blocos calibram (mínimo real de 0.3 s).
    # 2 blocos consecutivos confirmam VAD.
    # 4 blocos silenciosos encerram a fala após >= 0.6 s.
    blocos = [
        silencio_calibracao.copy(),
        silencio_calibracao.copy(),
        silencio_calibracao.copy(),
        voz.copy(),
        voz.copy(),
        silencio.copy(),
        silencio.copy(),
        silencio.copy(),
        silencio.copy(),
    ]

    sd = _SoundDeviceControlado(
        blocos,
        continuar,
    )

    def processar_texto(texto: str) -> None:
        textos_entregues.append(texto)
        entrada_entregue.set()

    ouvido = OuvidoWhisperRuntime(
        processar_texto=processar_texto,
        esta_falando=lambda: False,
        escuta_permitida=lambda: True,
        modo_chat_ativo=lambda: False,
        modo_jogo_ativo=lambda: True,
        sounddevice_mod=sd,
        numpy_mod=np,
        deve_continuar=lambda: continuar[0],
        entrega_assincrona=True,
        prioridade_interacao=prioridade,
        env_getter=lambda nome, padrao="": {
            "LAYLAY_MICROFONE_ATIVO": "1",
            "LAYLAY_WHISPER_CARREGAR_NO_INICIO": "0",
            "LAYLAY_MICROFONE_LIMIAR": "0.012",
            "LAYLAY_MICROFONE_CALIBRACAO": "0.3",
            "LAYLAY_MICROFONE_SILENCIO": "0.4",
            "LAYLAY_MICROFONE_MAX_SEGUNDOS": "3",
        }.get(nome, padrao),
        log=lambda *_args: None,
    )

    # Hardware é a única fronteira falsificada. Todo o VAD/capture/queue/STT
    # continua atravessando executar() real.
    def selecionar_dispositivo_controlado() -> tuple[int, dict[str, Any]]:
        ouvido.dispositivo = 0
        ouvido.taxa_captura = 16000
        ouvido._origem_dispositivo = "teste_controlado"
        return 0, {
            "name": "microfone-controlado",
            "default_samplerate": 16000,
        }

    ouvido.selecionar_dispositivo = selecionar_dispositivo_controlado  # type: ignore[method-assign]

    def transcrever_bloqueado(_audio: Any) -> tuple[str, float]:
        entrou_no_stt.set()
        liberar_stt.wait(timeout=3.0)
        return "laylay, teste de prioridade", 0.99

    ouvido.transcrever_com_confianca = transcrever_bloqueado  # type: ignore[method-assign]

    ponte = PonteIniciativaAplicacaoRuntime(
        estado_mental_getter=lambda: {},
        percepcao_getter=lambda _chave, padrao: padrao,
        conversa_getter=lambda _chave, padrao: padrao,
        modo_jogo=SimpleNamespace(
            ativo=True,
            contexto_atual=lambda: {},
        ),
        visao_leitura_getter=lambda: None,
        identificar_jogo=lambda _contexto: {},
        salvar_memoria=lambda: None,
        falar=lambda _texto, _emocao, _nivel: None,
        env_getter=lambda _nome, padrao: padrao,
        usuario_falando_getter=ouvido.usuario_falando,
        prioridade_interacao_getter=prioridade.ativa,
        log=lambda _texto: None,
    )

    estado_diretor: dict[str, Any] = {}

    def processar_evento(evento: dict[str, Any]) -> dict[str, Any]:
        cognicoes_presenca.append(dict(evento))
        return _turno_evento_valido(evento)

    diretor = DiretorPresencaRuntime(
        estado_get=lambda: estado_diretor,
        estado_set=lambda novo: (
            estado_diretor.clear()
            or estado_diretor.update(novo)
        ),
        contexto_getter=ponte.contexto,
        registrar_oportunidade=lambda _dados: {
            "decisao": "sugerir",
        },
        processar_evento_cognitivo=processar_evento,
        processar_proposta_comunicativa=lambda *_args, **_kwargs: {
            "status": "agendada",
            "agendada": True,
            "emissao_fisica": False,
            "autoriza_execucao": False,
        },
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )

    erro_captura: list[BaseException] = []

    def executar_ouvido() -> None:
        try:
            ouvido.executar()
        except BaseException as erro:
            erro_captura.append(erro)
        finally:
            captura_finalizada.set()

    thread_captura = threading.Thread(
        target=executar_ouvido,
        daemon=True,
        name="P1-H3-R-Captura",
    )
    thread_captura.start()

    contexto_durante_stt: dict[str, Any] = {}
    resultado_presenca: dict[str, Any] = {}

    try:
        # Worker REAL retirou o áudio da fila e está dentro da transcrição.
        assert entrou_no_stt.wait(timeout=2.0)

        # A fase acústica acabou, mas a utterance ainda pertence ao usuário.
        contexto_durante_stt = ponte.contexto()

        assert ouvido.usuario_falando() is False
        assert contexto_durante_stt["usuario_falando"] is False

        # Esta é a diferença canônica em relação ao H3 histórico.
        assert prioridade.ativa() is True
        assert contexto_durante_stt["interacao_usuario_ativa"] is True

        # Texto ainda não chegou à mente.
        assert textos_entregues == []

        resultado_presenca = diretor.considerar(
            {
                "origem": "observador_jogo",
                "dominio": "jogo",
                "categoria": "celebracao",
                "confianca": 0.98,
                "momento_seguro": True,
                "motivo": "Pedro venceu a luta com pouca vida restante",
                "evidencias": [
                    "vitória confirmada",
                    "vida crítica visível",
                ],
                "chave": "p1h3r-evento-durante-stt",
                "validade_s": 8.0,
            }
        )

        # Primeira fronteira causal do H3-R.
        assert resultado_presenca["status"] == "bloqueada"
        assert cognicoes_presenca == []

    finally:
        liberar_stt.set()
        entrada_entregue.wait(timeout=2.0)

        continuar[0] = False

        thread_captura.join(timeout=2.0)

        worker = ouvido._worker_audio
        if worker is not None:
            worker.join(timeout=2.0)

    assert erro_captura == []
    assert captura_finalizada.is_set()

    # A utterance era real e seguiu depois da barreira.
    assert textos_entregues == [
        "teste de prioridade",
    ]

    # Sem claim órfão depois da entrega.
    assert prioridade.ativa() is False

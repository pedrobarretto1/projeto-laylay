from __future__ import annotations

import threading
from typing import Any

from mente_laylay.personalidade.voz_runtime import VozRuntime


class _TimerControlado:
    """Registra timers sem dispará-los automaticamente."""

    criados: list["_TimerControlado"] = []

    def __init__(self, atraso: float, callback: Any) -> None:
        self.atraso = float(atraso)
        self.callback = callback
        self.daemon = False
        self.ativo = False
        self.__class__.criados.append(self)

    def is_alive(self) -> bool:
        return self.ativo

    def start(self) -> None:
        self.ativo = True


def _criar_voz(
    *,
    interacao: dict[str, bool],
    falas: list[str],
    conclusoes: list[tuple[bool, str]],
) -> VozRuntime:
    def politica(**_dados: Any) -> dict[str, Any]:
        if interacao["ativa"]:
            return {
                "acao": "descartar",
                "pontuacao": 0,
                "motivos": ["interacao_usuario_ativa"],
            }

        return {
            "acao": "emitir",
            "pontuacao": 90,
            "motivos": ["contexto_livre"],
        }

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
        compor_fala_proativa_cb=lambda itens: (
            str(itens[0]["texto"]),
            str(itens[0].get("emocao") or "calma"),
            int(itens[0].get("nivel") or 1),
        ),
        ajustar_estado_fala_cb=lambda *_args: None,

        # Os dois gates observam o MESMO estado vivo.
        # Assim o teste não obriga a futura implementação a escolher
        # entre reavaliar o porteiro ou usar o veto simples de entrega.
        proativa_permitida_cb=lambda: not interacao["ativa"],
        avaliar_proatividade_cb=politica,

        chave_turno_cb=lambda: 0.0,
        interrupt_event=threading.Event(),
        timer_factory=_TimerControlado,
        log=lambda _texto: None,
    )

    # Nunca chama TTS real.
    def falar_controlado(
        texto: str,
        *_args: Any,
        **_kwargs: Any,
    ) -> bool:
        falas.append(str(texto))
        return True

    voz.falar = falar_controlado  # type: ignore[method-assign]

    return voz


def test_red_p1h5_usuario_preempta_presenca_ja_enfileirada() -> None:
    _TimerControlado.criados = []

    interacao = {"ativa": False}
    falas: list[str] = []
    conclusoes: list[tuple[bool, str]] = []

    voz = _criar_voz(
        interacao=interacao,
        falas=falas,
        conclusoes=conclusoes,
    )

    # T0 — tudo livre.
    agendada = voz.agendar_fala_proativa(
        "presenca_jogo",
        "Essa foi por pouco, hein?",
        emocao="debochada",
        nivel=1,
        ao_concluir=lambda entregue, motivo: conclusoes.append(
            (bool(entregue), str(motivo))
        ),
    )

    # Prova de que a proposta passou legitimamente pela primeira fronteira.
    assert agendada is True
    assert voz.proativa_buffer
    assert falas == []

    # T1 — depois do agendamento, antes da entrega, Pedro adquire a vez.
    interacao["ativa"] = True

    # T2 — simula exatamente a fronteira tardia.
    voz.flush_fala_proativa()

    # PRIMEIRA FRONTEIRA RED:
    #
    # A aceitação em T0 não pode sobreviver a uma mudança de prioridade
    # observada em T1.
    assert falas == []

    # E não pode existir recibo de efeito físico confirmado.
    assert not any(
        entregue is True
        for entregue, _motivo in conclusoes
    )


def test_guard_p1h5_contexto_continua_livre_entrega_presenca() -> None:
    _TimerControlado.criados = []

    interacao = {"ativa": False}
    falas: list[str] = []
    conclusoes: list[tuple[bool, str]] = []

    voz = _criar_voz(
        interacao=interacao,
        falas=falas,
        conclusoes=conclusoes,
    )

    agendada = voz.agendar_fala_proativa(
        "presenca_jogo",
        "Essa foi por pouco, hein?",
        emocao="debochada",
        nivel=1,
        ao_concluir=lambda entregue, motivo: conclusoes.append(
            (bool(entregue), str(motivo))
        ),
    )

    assert agendada is True

    # Ninguém adquiriu prioridade no intervalo.
    voz.flush_fala_proativa()

    assert falas == [
        "Essa foi por pouco, hein?",
    ]
    assert any(
        entregue is True
        for entregue, _motivo in conclusoes
    )
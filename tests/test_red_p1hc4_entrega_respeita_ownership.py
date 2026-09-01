from __future__ import annotations

import threading
from typing import Any

from mente_laylay.autonomia.porteiro_proatividade import (
    PorteiroProatividadeRuntime,
)
from mente_laylay.personalidade.voz_runtime import VozRuntime


class _TimerControlado:
    """Timer que registra agendamento sem executar sozinho."""

    def __init__(self, atraso: float, callback: Any) -> None:
        self.atraso = float(atraso)
        self.callback = callback
        self.daemon = False
        self._ativo = False

    def is_alive(self) -> bool:
        return self._ativo

    def start(self) -> None:
        self._ativo = True


def test_red_p1hc4_porteiro_bloqueia_presenca_com_owner_usuario() -> None:
    contexto = {
        "modo_chat": False,
        "conversa_ativa": False,
        "turno_ativo": False,
        "modo_jogo_ativo": True,
        "modo_foco": False,
        "ultima_entrada_ts": 0.0,
        "is_speaking": False,
        "usuario_falando": False,

        # Único sinal que deve decidir esta prova.
        "interacao_usuario_ativa": True,
    }

    porteiro = PorteiroProatividadeRuntime(
        contexto_getter=lambda: dict(contexto),
        agora=lambda: 1000.0,
    )

    decisao = porteiro.avaliar(
        tipo="presenca_jogo",
        texto="Essa foi por pouco, hein?",
        turno_ativo=False,
        mesclar_turno=False,
        inicio_forcado=False,
        ultima_fala_normal_ts=0.0,
    )

    assert decisao["acao"] in {
        "adiar",
        "descartar",
    }

    assert any(
        "intera" in str(motivo).casefold()
        or "usuário" in str(motivo).casefold()
        or "usuario" in str(motivo).casefold()
        for motivo in decisao.get("motivos") or []
    )


def test_guard_p1hc4_porteiro_owner_livre_mantem_presenca_valida() -> None:
    contexto = {
        "modo_chat": False,
        "conversa_ativa": False,
        "turno_ativo": False,
        "modo_jogo_ativo": True,
        "modo_foco": False,
        "ultima_entrada_ts": 0.0,
        "is_speaking": False,
        "usuario_falando": False,
        "interacao_usuario_ativa": False,
    }

    porteiro = PorteiroProatividadeRuntime(
        contexto_getter=lambda: dict(contexto),
        agora=lambda: 1000.0,
    )

    decisao = porteiro.avaliar(
        tipo="presenca_jogo",
        texto="Essa foi por pouco, hein?",
        turno_ativo=False,
        mesclar_turno=False,
        inicio_forcado=False,
        ultima_fala_normal_ts=0.0,
    )

    assert decisao["acao"] == "emitir"


def test_red_p1hc4_flush_revalida_politica_de_presenca() -> None:
    interacao = {
        "ativa": False,
    }

    falas: list[str] = []
    avaliacoes: list[bool] = []
    conclusoes: list[tuple[bool, str]] = []

    def avaliar_proatividade(**_dados: Any) -> dict[str, Any]:
        owner_ativo = bool(interacao["ativa"])
        avaliacoes.append(owner_ativo)

        if owner_ativo:
            return {
                "acao": "adiar",
                "pontuacao": 0,
                "motivos": [
                    "interacao_usuario_ativa",
                ],
                "adiar_s": 2.0,
                "validade_s": 30.0,
            }

        return {
            "acao": "emitir",
            "pontuacao": 90,
            "motivos": [
                "contexto_livre",
            ],
            "adiar_s": 0.0,
            "validade_s": 30.0,
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

        # Compatibilidade continua existindo, mas o contrato deste
        # teste exige reavaliar a política completa no flush.
        proativa_permitida_cb=lambda: not interacao["ativa"],
        avaliar_proatividade_cb=avaliar_proatividade,

        chave_turno_cb=lambda: 0.0,
        interrupt_event=threading.Event(),
        timer_factory=_TimerControlado,
        log=lambda _texto: None,
    )

    def falar_controlado(
        texto: str,
        *_args: Any,
        **_kwargs: Any,
    ) -> bool:
        falas.append(str(texto))
        return True

    voz.falar = falar_controlado  # type: ignore[method-assign]

    # ---------------------------------------------------------
    # T0 — presença legitimamente aprovada
    # ---------------------------------------------------------

    agendada = voz.agendar_fala_proativa(
        "presenca_jogo",
        "Essa foi por pouco, hein?",
        emocao="debochada",
        nivel=1,
        ao_concluir=lambda entregue, motivo: conclusoes.append(
            (
                bool(entregue),
                str(motivo),
            )
        ),
    )

    assert agendada is True
    assert voz.proativa_buffer
    assert falas == []

    # A política foi consultada no agendamento enquanto estava livre.
    assert avaliacoes == [False]

    # ---------------------------------------------------------
    # T1 — Pedro adquire ownership antes da entrega
    # ---------------------------------------------------------

    interacao["ativa"] = True

    # ---------------------------------------------------------
    # T2 — fronteira física
    # ---------------------------------------------------------

    voz.flush_fala_proativa()

    # O flush precisa consultar a política DE NOVO.
    assert avaliacoes == [
        False,
        True,
    ]

    # E não pode alcançar falar().
    assert falas == []

    assert not any(
        entregue is True
        for entregue, _motivo in conclusoes
    )


def test_guard_p1hc4_flush_entrega_se_owner_continua_livre() -> None:
    interacao = {
        "ativa": False,
    }

    falas: list[str] = []
    avaliacoes: list[bool] = []

    def avaliar_proatividade(**_dados: Any) -> dict[str, Any]:
        owner_ativo = bool(interacao["ativa"])
        avaliacoes.append(owner_ativo)

        return {
            "acao": (
                "adiar"
                if owner_ativo
                else "emitir"
            ),
            "pontuacao": 90 if not owner_ativo else 0,
            "motivos": [],
            "adiar_s": 2.0 if owner_ativo else 0.0,
            "validade_s": 30.0,
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
            "calma",
            1,
        ),
        ajustar_estado_fala_cb=lambda *_args: None,
        proativa_permitida_cb=lambda: True,
        avaliar_proatividade_cb=avaliar_proatividade,
        chave_turno_cb=lambda: 0.0,
        interrupt_event=threading.Event(),
        timer_factory=_TimerControlado,
        log=lambda _texto: None,
    )

    voz.falar = (  # type: ignore[method-assign]
        lambda texto, *_args, **_kwargs: (
            falas.append(str(texto))
            or True
        )
    )

    assert voz.agendar_fala_proativa(
        "presenca_jogo",
        "Essa foi por pouco, hein?",
    ) is True

    voz.flush_fala_proativa()

    assert avaliacoes == [
        False,
        False,
    ]

    assert falas == [
        "Essa foi por pouco, hein?",
    ]
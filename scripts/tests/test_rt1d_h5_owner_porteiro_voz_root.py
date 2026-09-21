"""RT1-D — owner canônico alcança Porteiro e Voz no root.

Objetivo:
provar a outra metade temporal do P1-H através dos objetos montados por
`laylay.py`.

Fluxo:

    owner livre
       ↓
    VozRuntime real admite fala proativa
       ↓
    item fica na fila (timer controlado)
       ↓
    usuário adquire owner
       ↓
    flush_fala_proativa() real
       ↓
    Porteiro real revalida política
       ↓
    fala física NÃO pode acontecer

QUEUE ACCEPTANCE != DELIVERY PERMISSION
AUTONOMOUS SPEECH REQUIRES LIVE DELIVERY-TIME ELIGIBILITY
"""

from __future__ import annotations

import importlib
from typing import Any


class _TimerControlado:
    """Timer que registra agendamento, mas nunca dispara sozinho."""

    criados: list["_TimerControlado"] = []

    def __init__(self, intervalo: float, callback: Any, *args: Any, **kwargs: Any):
        self.intervalo = float(intervalo)
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
        self.daemon = False
        self.iniciado = False
        self.cancelado = False
        type(self).criados.append(self)

    def start(self) -> None:
        self.iniciado = True

    def cancel(self) -> None:
        self.cancelado = True

    def is_alive(self) -> bool:
        return bool(self.iniciado and not self.cancelado)


def _root():
    return importlib.import_module("laylay")


def test_rt1d_porteiro_do_root_enxerga_owner_canonico():
    root = _root()

    owner = root._prioridade_interacao_usuario_runtime
    porteiro = root._porteiro_proatividade_runtime
    voz = root._voz_runtime

    # A Voz do root precisa realmente consultar o Porteiro do root.
    callback = getattr(voz, "avaliar_proatividade_cb", None)
    assert callable(callback)
    assert getattr(callback, "__self__", None) is porteiro, (
        "VozRuntime do root não está conectada ao PorteiroProatividadeRuntime "
        "montado pelo mesmo root"
    )

    assert owner.ativa() is False, (
        "RT1-D exige processo limpo, sem claim de usuário anterior"
    )

    claim = owner.adquirir("rt1d-politica")
    try:
        assert owner.ativa() is True

        contexto = porteiro._contexto()

        assert contexto.get("interacao_usuario_ativa") is True, (
            "RT1-D RED: o owner canônico está ativo no root, mas o contexto "
            "consumido pelo Porteiro não publica "
            "interacao_usuario_ativa=True. "
            f"valor={contexto.get('interacao_usuario_ativa')!r}"
        )

        decisao = porteiro.avaliar(
            tipo="presenca_jogo",
            texto="Essa foi por pouco.",
            turno_ativo=False,
            mesclar_turno=False,
            inicio_forcado=False,
            ultima_fala_normal_ts=0.0,
            revalidacao_entrega=True,
        )

        assert decisao.get("acao") in {"adiar", "descartar"}, (
            "Porteiro viu owner ativo, mas ainda autorizou fala autônoma: "
            + repr(decisao)
        )
    finally:
        owner.liberar(claim)

    assert owner.ativa() is False


def test_rt1d_flush_da_voz_revalida_owner_antes_da_fronteira_fisica():
    root = _root()

    owner = root._prioridade_interacao_usuario_runtime
    porteiro = root._porteiro_proatividade_runtime
    voz = root._voz_runtime

    assert owner.ativa() is False

    callback = getattr(voz, "avaliar_proatividade_cb", None)
    assert callable(callback)
    assert getattr(callback, "__self__", None) is porteiro

    antigos = {
        "timer_factory": voz.timer_factory,
        "falar": voz.falar,
        "proativa_timer": voz.proativa_timer,
        "proativa_buffer": list(voz.proativa_buffer),
        "proativa_inicio_sistema": voz.proativa_inicio_sistema,
        "proativa_janela_startup": voz.proativa_janela_startup,
        "ultima_fala_normal_ts": voz._ultima_fala_normal_ts,
    }

    # Estado limpo deste teste; não usamos nenhum item proativo legado.
    with voz.proativa_lock:
        voz.proativa_buffer.clear()
        voz.proativa_timer = None

    _TimerControlado.criados.clear()
    voz.timer_factory = _TimerControlado
    voz.proativa_inicio_sistema = 0.0
    voz.proativa_janela_startup = 0.0
    voz._ultima_fala_normal_ts = 0.0

    falas_fisicas: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def falar_controlado(*args: Any, **kwargs: Any) -> bool:
        falas_fisicas.append((args, kwargs))
        return True

    voz.falar = falar_controlado

    claim = ""

    try:
        # T0 — usuário livre: a fala pode ser admitida.
        retorno = voz.agendar_fala_proativa(
            "presenca_jogo",
            "Essa foi por pouco.",
            "animada",
            1,
        )

        with voz.proativa_lock:
            quantidade_admitida = len(voz.proativa_buffer)

        assert quantidade_admitida == 1, (
            "pré-condição RT1-D inválida: fala não foi admitida quando o "
            f"owner estava livre; retorno={retorno!r}"
        )
        assert falas_fisicas == []

        # T1 — depois da admissão, o usuário assume o canal.
        claim = owner.adquirir("rt1d-flush")
        assert owner.ativa() is True

        # T2 — fronteira temporal real da Voz.
        voz.flush_fala_proativa()

        # A fala jamais pode atravessar self.falar() enquanto o owner está ativo.
        assert falas_fisicas == [], (
            "RT1-D RED: a Voz do root entregou fala fisicamente mesmo depois "
            "de o usuário adquirir ownership entre admissão e flush. "
            f"chamadas={falas_fisicas!r}"
        )

        # Como presença não prioritária, a implementação pode adiar ou
        # descartar; o contrato essencial é não entregar.
        contexto = porteiro._contexto()
        assert contexto.get("interacao_usuario_ativa") is True, (
            "durante o flush o Porteiro perdeu o owner canônico"
        )

    finally:
        if claim:
            owner.liberar(claim)

        # Impede qualquer timer controlado de ser considerado vivo.
        for timer in list(_TimerControlado.criados):
            timer.cancel()

        with voz.proativa_lock:
            voz.proativa_buffer.clear()
            voz.proativa_buffer.extend(antigos["proativa_buffer"])
            voz.proativa_timer = antigos["proativa_timer"]

        voz.timer_factory = antigos["timer_factory"]
        voz.falar = antigos["falar"]
        voz.proativa_inicio_sistema = antigos["proativa_inicio_sistema"]
        voz.proativa_janela_startup = antigos["proativa_janela_startup"]
        voz._ultima_fala_normal_ts = antigos["ultima_fala_normal_ts"]

    assert owner.ativa() is False

from __future__ import annotations

import inspect
import threading

from mente_laylay.autonomia.execucao_ia import CoordenadorExecRuntime
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.integracao.adaptadores_composicao import agendar_entrada_canonica
from mente_laylay.memoria_mental.diagnostico_mente import (
    construir_diagnostico_mente,
    formatar_diagnostico_terminal,
)


def test_coordenador_entrega_terminal_voz_e_jogo_ao_mesmo_runtime() -> None:
    recebidas: list[tuple[str, str]] = []

    class RespostaFalsa:
        def processar(self, texto, ainda_atual_cb=None, origem="desconhecida"):
            recebidas.append((texto, origem))

    coordenador = CoordenadorExecRuntime(
        contexto_exec_getter=lambda: None,
        resposta_ia_getter=lambda: RespostaFalsa(),
        loop_getter=lambda: None,
        log=lambda *_args: None,
    )

    for origem in ("terminal", "voz", "modo_jogo"):
        coordenador.processar_sync("liga a luz", origem=origem)

    assert recebidas == [
        ("liga a luz", "terminal"),
        ("liga a luz", "voz"),
        ("liga a luz", "modo_jogo"),
    ]


def test_entrada_desktop_nao_fica_presa_em_loop_ainda_nao_iniciado() -> None:
    recebidas: list[tuple[str, str]] = []
    concluida = threading.Event()

    class LoopAindaParado:
        @staticmethod
        def is_running() -> bool:
            return False

        @staticmethod
        def is_closed() -> bool:
            return False

    class RespostaFalsa:
        def processar(self, texto, ainda_atual_cb=None, origem="desconhecida"):
            recebidas.append((texto, origem))
            concluida.set()

    coordenador = CoordenadorExecRuntime(
        contexto_exec_getter=lambda: None,
        resposta_ia_getter=lambda: RespostaFalsa(),
        loop_getter=LoopAindaParado,
        log=lambda *_args: None,
    )

    thread = coordenador.agendar("oi lay", origem="desktop")

    assert isinstance(thread, threading.Thread)
    assert concluida.wait(1.0)
    assert recebidas == [("oi lay", "desktop")]


def test_entrada_desktop_independe_ate_de_loop_compartilhado_ativo() -> None:
    recebidas: list[str] = []
    concluida = threading.Event()

    class LoopAtivo:
        @staticmethod
        def is_running() -> bool:
            return True

        @staticmethod
        def is_closed() -> bool:
            return False

    class RespostaFalsa:
        def processar(self, texto, ainda_atual_cb=None, origem="desconhecida"):
            recebidas.append(f"{origem}:{texto}")
            concluida.set()

    coordenador = CoordenadorExecRuntime(
        contexto_exec_getter=lambda: None,
        resposta_ia_getter=lambda: RespostaFalsa(),
        loop_getter=LoopAtivo,
        log=lambda *_args: None,
    )

    thread = coordenador.agendar("oi lay", origem="desktop")

    assert isinstance(thread, threading.Thread)
    assert concluida.wait(1.0)
    assert recebidas == ["desktop:oi lay"]


def test_adaptador_desktop_nao_consulta_lock_do_modo_jogo() -> None:
    chamadas: list[tuple[str, str]] = []

    def modo_jogo_nao_deve_ser_consultado() -> bool:
        raise AssertionError("a porta desktop consultou o modo-jogo")

    resultado = agendar_entrada_canonica(
        "oi lay",
        canal="desktop",
        modo_jogo_ativo=modo_jogo_nao_deve_ser_consultado,
        agendar=lambda texto, origem: chamadas.append((texto, origem)) or "thread",
    )

    assert resultado == "thread"
    assert chamadas == [("oi lay", "desktop")]


def test_resposta_cria_turno_canonico_com_origem_antes_do_fluxo() -> None:
    turnos: list[tuple[str, str]] = []
    eventos: list[str] = []
    contexto = {
        "marcar_inicio_turno": (
            lambda texto, *, origem="desconhecida": (
                turnos.append((texto, origem)),
                eventos.append(f"turno:{origem}"),
            )
        ),
        "obter_turno_atual": lambda: {},
        "processar_comandos_prioritarios": (
            lambda _texto: eventos.append("prioridade") or True
        ),
    }
    runtime = RespostaIARuntime(
        contexto_getter=lambda: contexto,
        log=lambda *_args: None,
    )

    for origem in ("terminal", "voz", "modo_jogo"):
        runtime.processar("liga a luz", origem=origem)

    assert turnos == [
        ("liga a luz", "terminal"),
        ("liga a luz", "voz"),
        ("liga a luz", "modo_jogo"),
    ]
    assert eventos == [
        "turno:terminal", "prioridade",
        "turno:voz", "prioridade",
        "turno:modo_jogo", "prioridade",
    ]


def test_coordenador_nao_expoe_atalho_prioritario_antes_do_turno() -> None:
    parametros = inspect.signature(CoordenadorExecRuntime.__init__).parameters

    assert "processar_prioritario" not in parametros


def test_diagnostico_expoe_origem_do_turno_canonico() -> None:
    diagnostico = construir_diagnostico_mente(
        {
            "mental": {
                "turno_atual": {
                    "modalidade": "comando",
                    "origem_entrada": "modo_jogo",
                    "autoriza_execucao": True,
                },
                "plano_turno_atual": {
                    "fase": "executado",
                    "origem_entrada": "modo_jogo",
                },
            }
        },
        {},
    )

    assert diagnostico["turno"]["origem"] == "modo_jogo"
    assert "origem=modo_jogo" in formatar_diagnostico_terminal(diagnostico)

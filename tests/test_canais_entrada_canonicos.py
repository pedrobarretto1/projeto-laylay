from __future__ import annotations

import inspect

from mente_laylay.autonomia.execucao_ia import CoordenadorExecRuntime
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
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

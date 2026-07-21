from __future__ import annotations

from mente_laylay.autonomia.barra_comando import BarraComandoRuntime


class _KeyboardFake:
    def __init__(self) -> None:
        self.registros: list[tuple[str, object, dict]] = []

    def add_hotkey(self, atalho, callback, **kwargs):
        self.registros.append((atalho, callback, kwargs))
        return 1


def test_barra_normaliza_e_entrega_para_a_mesma_mente() -> None:
    recebidos: list[str] = []
    runtime = BarraComandoRuntime(
        processar_texto=recebidos.append,
        keyboard_mod=_KeyboardFake(),
        log=lambda *_args: None,
    )

    assert runtime._despachar("  desliga   a luz  ") is True
    assert recebidos == ["desliga a luz"]


def test_barra_nao_envia_texto_vazio() -> None:
    recebidos: list[str] = []
    runtime = BarraComandoRuntime(
        processar_texto=recebidos.append,
        keyboard_mod=_KeyboardFake(),
        log=lambda *_args: None,
    )

    assert runtime._despachar("   ") is False
    assert recebidos == []


def test_hotkey_global_e_registrada_uma_unica_vez() -> None:
    keyboard = _KeyboardFake()
    runtime = BarraComandoRuntime(
        processar_texto=lambda _texto: None,
        keyboard_mod=keyboard,
        hotkey="ctrl+shift+space",
        log=lambda *_args: None,
    )
    runtime.iniciar = lambda: True  # type: ignore[method-assign]

    assert runtime.registrar_hotkey() is True
    assert runtime.registrar_hotkey() is True
    assert len(keyboard.registros) == 1
    atalho, _callback, opcoes = keyboard.registros[0]
    assert atalho == "ctrl+shift+space"
    assert opcoes == {"suppress": True, "trigger_on_release": True}

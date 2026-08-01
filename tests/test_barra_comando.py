from __future__ import annotations

from mente_laylay.autonomia.barra_comando import BarraComandoRuntime, CapturaTextoGlobal


class _KeyboardFake:
    def __init__(self) -> None:
        self.registros: list[tuple[str, object, dict]] = []
        self.hotkeys_removidas = []

    def add_hotkey(self, atalho, callback, **kwargs):
        self.registros.append((atalho, callback, kwargs))
        return 1

    def remove_hotkey(self, handle):
        self.hotkeys_removidas.append(handle)


class _KeyboardCapturaFake(_KeyboardFake):
    def __init__(self) -> None:
        super().__init__()
        self.callback = None
        self.hooks = []
        self.removidos = []

    def hook(self, callback, suppress=False):
        self.callback = callback
        token = object()
        self.hooks.append((token, suppress))
        return token

    def unhook(self, token):
        self.removidos.append(token)

    def is_toggled(self, _nome):
        return False


class _Evento:
    def __init__(self, nome, tipo="down") -> None:
        self.name = nome
        self.event_type = tipo


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


def test_barra_encaminha_falha_de_envio_ao_diagnostico() -> None:
    falhas = []
    runtime = BarraComandoRuntime(
        processar_texto=lambda _texto: (_ for _ in ()).throw(RuntimeError("falhou")),
        keyboard_mod=_KeyboardFake(),
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        log=lambda *_args: None,
    )

    assert runtime.enviar("abre o navegador") is False
    assert falhas[0][0] == ("barra_comando", "envio_comando")
    assert isinstance(falhas[0][1]["erro"], RuntimeError)


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
    assert opcoes == {"suppress": False, "trigger_on_release": False}


def test_barra_libera_hotkey_e_sinaliza_interface_no_encerramento() -> None:
    keyboard = _KeyboardFake()
    joins = []

    class ThreadFake:
        def join(self, timeout):
            joins.append(timeout)

    runtime = BarraComandoRuntime(
        processar_texto=lambda _texto: None,
        keyboard_mod=keyboard,
        log=lambda *_args: None,
    )
    runtime._hotkey_handle = 77
    runtime._hotkey_registrada = True
    runtime._thread = ThreadFake()

    runtime.encerrar(timeout_s=0.4)

    assert keyboard.hotkeys_removidas == [77]
    assert runtime._fila.get_nowait() == "encerrar"
    assert len(joins) == 1
    assert 0.0 <= joins[0] <= 0.4
    assert runtime._hotkey_registrada is False


def test_barra_aguarda_confirmacao_da_thread_tk_sem_destruir_pelo_chamador() -> None:
    runtime = BarraComandoRuntime(
        processar_texto=lambda _texto: None,
        keyboard_mod=_KeyboardFake(),
        log=lambda *_args: None,
    )
    eventos = []

    class ThreadFake:
        @staticmethod
        def is_alive():
            return True

        @staticmethod
        def join(timeout):
            eventos.append(("join", timeout))

    class EventoFake:
        @staticmethod
        def wait(timeout):
            eventos.append(("espera_tk", timeout))
            return True

    runtime._thread = ThreadFake()
    runtime._interface_encerrada = EventoFake()

    runtime.encerrar(timeout_s=0.4)

    assert eventos[0][0] == "espera_tk"
    assert eventos[1][0] == "join"
    assert runtime._fila.get_nowait() == "encerrar"


def test_hotkey_windows_traduz_combinacao_sem_perder_modificadores() -> None:
    assert BarraComandoRuntime._traduzir_hotkey_windows("ctrl+shift+space") == (
        0x4000 | 0x0002 | 0x0004,
        0x20,
    )
    assert BarraComandoRuntime._traduzir_hotkey_windows("ctrl+f9") == (
        0x4000 | 0x0002,
        0x78,
    )
    assert BarraComandoRuntime._traduzir_hotkey_windows("f10") == (
        0x4000,
        0x79,
    )


def test_captura_espera_a_tecla_principal_do_atalho_configurado() -> None:
    class KeyboardComEstado(_KeyboardCapturaFake):
        def __init__(self):
            super().__init__()
            self.pressionadas = {"f10"}

        def is_pressed(self, nome):
            return nome in self.pressionadas

    keyboard = KeyboardComEstado()
    captura = CapturaTextoGlobal(
        keyboard_mod=keyboard,
        ao_atualizar=lambda _texto: None,
        ao_enviar=lambda _texto: None,
        ao_cancelar=lambda: None,
        log=lambda *_: None,
        intervalo_liberacao_s=0,
        teclas_ativacao=("f10",),
    )

    assert captura.iniciar() is False
    assert keyboard.hooks == []
    keyboard.pressionadas.clear()
    assert captura.iniciar() is True
    assert keyboard.hooks[0][1] is True


def test_eventos_repetidos_da_hotkey_geram_uma_unica_abertura_pendente() -> None:
    agora = [10.0]
    runtime = BarraComandoRuntime(
        processar_texto=lambda _texto: None,
        keyboard_mod=_KeyboardFake(),
        clock=lambda: agora[0],
        log=lambda *_args: None,
    )
    runtime.iniciar = lambda: True  # type: ignore[method-assign]

    assert runtime.solicitar_abertura() is True
    agora[0] += 0.05
    assert runtime.solicitar_abertura() is True

    assert runtime._fila.qsize() == 1


def test_barra_nao_reenvia_a_mesma_entrada_por_repeticao_do_enter() -> None:
    agora = [20.0]
    recebidos: list[str] = []
    runtime = BarraComandoRuntime(
        processar_texto=recebidos.append,
        keyboard_mod=_KeyboardFake(),
        clock=lambda: agora[0],
        intervalo_duplicata_s=1.5,
        log=lambda *_args: None,
    )

    assert runtime.enviar("quais minhas playlists") is True
    agora[0] += 0.2
    assert runtime.enviar("  QUAIS   MINHAS PLAYLISTS ") is False
    agora[0] += 1.5
    assert runtime.enviar("quais minhas playlists") is True

    assert recebidos == ["quais minhas playlists", "quais minhas playlists"]


def test_captura_global_monta_texto_sem_foco_e_envia_no_enter() -> None:
    keyboard = _KeyboardCapturaFake()
    atualizacoes = []
    enviados = []
    captura = CapturaTextoGlobal(
        keyboard_mod=keyboard,
        ao_atualizar=atualizacoes.append,
        ao_enviar=enviados.append,
        ao_cancelar=lambda: None,
        log=lambda *_: None,
        intervalo_liberacao_s=0,
    )
    assert captura.iniciar() is True
    assert keyboard.hooks[0][1] is True
    for nome in ["o", "i", "space", "l", "a", "y", "backspace", "y", "enter"]:
        keyboard.callback(_Evento(nome))
    assert enviados == ["oi lay"]
    assert atualizacoes[-1] == "oi lay"
    assert keyboard.removidos == [keyboard.hooks[0][0]]
    assert captura.ativa is False


def test_captura_global_espera_todo_o_atalho_e_liberacao_estavel() -> None:
    class KeyboardComEstado(_KeyboardCapturaFake):
        def __init__(self):
            super().__init__()
            self.pressionadas = {"ctrl", "shift", "space"}

        def is_pressed(self, nome):
            return nome in self.pressionadas

    keyboard = KeyboardComEstado()
    logs = []
    agora = [30.0]
    captura = CapturaTextoGlobal(
        keyboard_mod=keyboard,
        ao_atualizar=lambda _texto: None,
        ao_enviar=lambda _texto: None,
        ao_cancelar=lambda: None,
        log=logs.append,
        clock=lambda: agora[0],
        intervalo_liberacao_s=0.12,
    )

    assert captura.iniciar() is False
    assert keyboard.hooks == []
    assert any("aguardando soltar teclas do atalho" in item for item in logs)

    keyboard.pressionadas.clear()
    assert captura.iniciar() is False
    agora[0] += 0.10
    assert captura.iniciar() is False
    agora[0] += 0.03
    assert captura.iniciar() is True
    assert len(keyboard.hooks) == 1
    assert keyboard.hooks[0][1] is True


def test_captura_global_reinicia_espera_se_shift_voltar_durante_debounce() -> None:
    class KeyboardComEstado(_KeyboardCapturaFake):
        def __init__(self):
            super().__init__()
            self.pressionadas = set()

        def is_pressed(self, nome):
            return nome in self.pressionadas

    keyboard = KeyboardComEstado()
    agora = [40.0]
    captura = CapturaTextoGlobal(
        keyboard_mod=keyboard,
        ao_atualizar=lambda _texto: None,
        ao_enviar=lambda _texto: None,
        ao_cancelar=lambda: None,
        log=lambda *_: None,
        clock=lambda: agora[0],
        intervalo_liberacao_s=0.12,
    )

    assert captura.iniciar() is False
    agora[0] += 0.08
    keyboard.pressionadas.add("shift")
    assert captura.iniciar() is False
    keyboard.pressionadas.clear()
    agora[0] += 0.08
    assert captura.iniciar() is False
    agora[0] += 0.13
    assert captura.iniciar() is True


def test_captura_global_respeita_shift_e_esc_cancela() -> None:
    keyboard = _KeyboardCapturaFake()
    cancelamentos = []
    captura = CapturaTextoGlobal(
        keyboard_mod=keyboard,
        ao_atualizar=lambda _texto: None,
        ao_enviar=lambda _texto: None,
        ao_cancelar=lambda: cancelamentos.append(True),
        log=lambda *_: None,
        intervalo_liberacao_s=0,
    )
    assert captura.iniciar() is True
    keyboard.callback(_Evento("shift"))
    keyboard.callback(_Evento("l"))
    keyboard.callback(_Evento("shift", "up"))
    keyboard.callback(_Evento("a"))
    keyboard.callback(_Evento("esc"))
    assert captura.texto == "La"
    assert cancelamentos == [True]
    assert captura.ativa is False


def test_captura_global_compoe_acentos_em_portugues() -> None:
    keyboard = _KeyboardCapturaFake()
    enviados = []
    captura = CapturaTextoGlobal(
        keyboard_mod=keyboard,
        ao_atualizar=lambda _texto: None,
        ao_enviar=enviados.append,
        ao_cancelar=lambda: None,
        log=lambda *_: None,
        intervalo_liberacao_s=0,
    )
    assert captura.iniciar() is True
    for nome in ["v", "o", "c", "^", "e", "space", "n", "~", "a", "o", "enter"]:
        keyboard.callback(_Evento(nome))
    assert enviados == ["você não"]

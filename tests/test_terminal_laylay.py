import sys
import threading

from mente_laylay.personalidade import terminal_laylay
from mente_laylay.personalidade.terminal_laylay import (
    escutar_texto_terminal,
    ler_linha_terminal_interrompivel,
    should_log_message,
)


def test_modo_essencial_exibe_diagnostico_e_transcricao_de_voz():
    assert should_log_message("🗣️ [VOCÊ DISSE] Lay, liga a luz", log_mode="essencial")
    assert should_log_message(
        "🎙️ [OUVIDO:LEITURA] original='Lay, liga a luz'",
        log_mode="limpo",
    )
    assert should_log_message(
        "🎙️ [OUVIDO:NÍVEL] calibrado ruído=0.0020",
        log_mode="essencial",
    )
    assert should_log_message(
        "🧠 [REDE ASSOCIATIVA] modo=sombra | influência=desativada",
        log_mode="limpo",
    )
    assert should_log_message(
        "📋 [CLIPBOARD:INÍCIO] serviço=ativo modo=sugestao",
        log_mode="limpo",
    )
    assert should_log_message(
        "🖥️ [TERMINAL 2:ENTRADA] recebida | id=abc123",
        log_mode="essencial",
    )


def test_leitura_windows_pode_ser_cancelada_sem_chamar_input(monkeypatch):
    ativo = {"valor": True}

    class Console:
        @staticmethod
        def kbhit():
            return False

    monkeypatch.setattr(terminal_laylay.os, "name", "nt")
    resultado = ler_linha_terminal_interrompivel(
        "> ",
        stdin=sys.stdin,
        deve_continuar=lambda: ativo["valor"],
        input_fn=lambda _prompt: (_ for _ in ()).throw(
            AssertionError("input bloqueante não deveria ser chamado")
        ),
        raw_print=lambda *_args, **_kwargs: None,
        sleep_fn=lambda _tempo: ativo.__setitem__("valor", False),
        msvcrt_mod=Console(),
    )

    assert resultado is None


def test_leitura_windows_preserva_texto_e_backspace(monkeypatch):
    teclas = iter(["o", "i", "\b", "á", "\r"])
    atual = {"tecla": None}

    class Console:
        @staticmethod
        def kbhit():
            if atual["tecla"] is None:
                try:
                    atual["tecla"] = next(teclas)
                except StopIteration:
                    return False
            return True

        @staticmethod
        def getwch():
            tecla, atual["tecla"] = atual["tecla"], None
            return tecla

    monkeypatch.setattr(terminal_laylay.os, "name", "nt")
    resultado = ler_linha_terminal_interrompivel(
        "> ",
        stdin=sys.stdin,
        deve_continuar=lambda: True,
        raw_print=lambda *_args, **_kwargs: None,
        sleep_fn=lambda _tempo: None,
        msvcrt_mod=Console(),
    )

    assert resultado == "oá"


def test_entrada_vazia_nao_duplica_cabecalho_do_usuario():
    entradas = iter(["", "", "oi lay"])
    ativo = {"valor": True}
    impresso = []
    processados = []

    class StdinTTY:
        @staticmethod
        def isatty():
            return True

    def leitor(_prompt, **_kwargs):
        return next(entradas)

    def processar(texto):
        processados.append(texto)
        ativo["valor"] = False

    escutar_texto_terminal(
        estado_ativo=lambda: True,
        processar_texto=processar,
        stdin=StdinTTY(),
        raw_print=lambda texto="", **_kwargs: impresso.append(texto),
        sleep_fn=lambda _tempo: None,
        deve_continuar=lambda: ativo["valor"],
        ler_linha_fn=leitor,
    )

    assert processados == ["oi lay"]
    assert impresso.count("💬 Você:") == 1


def test_lock_de_impressao_nao_bloqueia_a_mente_enquanto_aguarda_teclado():
    ativo = {"valor": True}
    profundidade = {"valor": 0}
    processados = []

    class StdinTTY:
        @staticmethod
        def isatty():
            return True

    class LockObservavel:
        def __enter__(self):
            profundidade["valor"] += 1

        def __exit__(self, *_args):
            profundidade["valor"] -= 1

    def leitor(_prompt, **_kwargs):
        assert profundidade["valor"] == 0
        return "oi lay"

    def processar(texto):
        processados.append(texto)
        ativo["valor"] = False

    escutar_texto_terminal(
        estado_ativo=lambda: True,
        processar_texto=processar,
        stdin=StdinTTY(),
        raw_print=lambda *_args, **_kwargs: None,
        print_lock=LockObservavel(),
        sleep_fn=lambda _tempo: None,
        deve_continuar=lambda: ativo["valor"],
        ler_linha_fn=leitor,
    )

    assert processados == ["oi lay"]
    assert profundidade["valor"] == 0


def test_log_de_outra_thread_funciona_enquanto_terminal_aguarda_enter():
    leitura_iniciada = threading.Event()
    liberar_leitura = threading.Event()
    log_concluido = threading.Event()
    ativo = {"valor": True}
    print_lock = threading.RLock()

    class StdinTTY:
        @staticmethod
        def isatty():
            return True

    def leitor(_prompt, **_kwargs):
        leitura_iniciada.set()
        liberar_leitura.wait(2.0)
        return "oi lay"

    def processar(_texto):
        ativo["valor"] = False

    thread_terminal = threading.Thread(
        target=escutar_texto_terminal,
        kwargs={
            "estado_ativo": lambda: True,
            "processar_texto": processar,
            "stdin": StdinTTY(),
            "raw_print": lambda *_args, **_kwargs: None,
            "print_lock": print_lock,
            "sleep_fn": lambda _tempo: None,
            "deve_continuar": lambda: ativo["valor"],
            "ler_linha_fn": leitor,
        },
    )
    thread_terminal.start()
    try:
        assert leitura_iniciada.wait(0.5)

        def escrever_log() -> None:
            with print_lock:
                log_concluido.set()

        thread_log = threading.Thread(target=escrever_log)
        thread_log.start()
        assert log_concluido.wait(0.5)
        thread_log.join(timeout=0.5)
    finally:
        liberar_leitura.set()
        thread_terminal.join(timeout=2.0)

    assert not thread_terminal.is_alive()

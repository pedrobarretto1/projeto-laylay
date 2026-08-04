import sys

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

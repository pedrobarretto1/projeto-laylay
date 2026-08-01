from __future__ import annotations

from mente_laylay.integracao.contexto_execucao_ia import (
    ContextoDispatcherRuntime,
    ContextoFinalizacaoRuntime,
)


def test_contextos_usam_estado_seguro_e_registram_defeito_do_getter() -> None:
    falhas = []

    def falhar_estado():
        raise RuntimeError("mensagem privada")

    def registrar(*args, **kwargs):
        falhas.append((args, kwargs))

    dispatcher = ContextoDispatcherRuntime(
        base={}, navegacao={}, musica={}, arquivos={}, percepcao={},
        agenda_email={}, execucao={}, autonomia={},
        estado_getter=falhar_estado,
        registrar_falha=registrar,
    )
    finalizacao = ContextoFinalizacaoRuntime(
        ia={}, voz_memoria={}, autoaprimoramento={},
        estado_getter=falhar_estado,
        registrar_falha=registrar,
    )

    assert dispatcher.montar()["current_emotion"] == "calma"
    assert finalizacao.montar()["current_emotion"] == "calma"
    assert [item[0][0] for item in falhas] == [
        "contexto_dispatcher", "contexto_finalizacao",
    ]
    assert all(item[1]["classe"] == "defeito" for item in falhas)

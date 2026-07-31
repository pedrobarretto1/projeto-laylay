from __future__ import annotations

from mente_laylay.autonomia.porteiro_acoes import PorteiroAcoesRuntime


class _Estado:
    def __init__(self) -> None:
        self.musical = {"playlist_bloqueada_ate": 0.0, "ultima_playlist": "rock"}
        self.mental = {"ultima_intencao": "PLAYLIST_PLAY"}
        self.memoria_conversa = {"messages": []}
        self.continuidades = {"playlist_sugestao_pendente": "rock"}

    def obter(self, dominio, chave, padrao=None):
        return getattr(self, dominio).get(chave, padrao)

    def atualizar(self, dominio, atualizador, **campos):
        setattr(self, dominio, atualizador(getattr(self, dominio), **campos))

    def substituir(self, dominio, valor):
        setattr(self, dominio, valor)


def test_contexto_usa_playlist_viva_sem_namespace_global() -> None:
    estado = _Estado()
    playlist = {"name": "rock"}
    runtime = PorteiroAcoesRuntime(
        playlist_state_getter=lambda: playlist,
        estado_runtime_getter=lambda: estado,
    )

    contexto = runtime.contexto()
    assert contexto["playlist_ativa"] is True
    assert contexto["auto_next_playlist"] is True
    assert contexto["ultima_playlist"] == "rock"

    playlist.clear()
    contexto_atualizado = runtime.contexto()
    assert contexto_atualizado["playlist_ativa"] is False
    assert contexto_atualizado["auto_next_playlist"] is False
    assert not hasattr(runtime, "namespace_getter")


def test_bloqueio_e_autorizacao_musical_preservam_comportamento() -> None:
    estado = _Estado()
    runtime = PorteiroAcoesRuntime(
        playlist_state_getter=lambda: {},
        estado_runtime_getter=lambda: estado,
    )

    assert runtime.autonomia_permite_execucao_musical(
        "PLAYLIST_PLAY", "toca a playlist rock",
    ) is True
    runtime.bloquear_playlist_temporariamente(60)

    assert estado.continuidades["playlist_sugestao_pendente"] is None
    assert runtime.playlist_bloqueada_agora() is True
    assert runtime.autonomia_permite_execucao_musical(
        "PLAYLIST_PLAY", "toca a playlist rock",
    ) is False

from __future__ import annotations

from mente_laylay.autonomia.controle_midia import executar_media_control
from mente_laylay.integracao.acoes_painel_runtime import (
    comando_tipado_acao_painel,
)
from tests.fakes_navegador import NavegadorLeituraFake


class _MusicaObservada:
    def __init__(self, *, tab_id: int | None) -> None:
        self.tab_id = tab_id

    def estado(self) -> dict:
        return {
            "playlist_ativa": "",
            "tab_id": self.tab_id,
        }


class _NavegadorMusical:
    def __init__(self, *, resultado: bool = True) -> None:
        self.resultado = resultado
        self.chamadas: list[tuple[str, int | None]] = []

    def controlar_youtube_detalhado(
        self,
        comando: str,
        *,
        tab_id: int | None = None,
        queue_item_id: str = "",
        queue_index: int | None = None,
    ) -> dict:
        self.chamadas.append((comando, tab_id))
        return {
            "ok": self.resultado,
            "confirmado": self.resultado,
            "status": "success" if self.resultado else "source_tab_missing",
        }


def _executar_play_musical(
    *,
    tab_id_musical: int | None,
    navegador: _NavegadorMusical,
    comandos_nativos: list[str],
) -> bool:
    return executar_media_control(
        {
            "acao": "play",
            "platform": "music",
            "origem": "terminal_panel",
        },
        "controle manual de mídia: play",
        "local",
        {
            "_registro_musica_operacoes_runtime": _MusicaObservada(
                tab_id=tab_id_musical,
            ),
            "_registro_navegador_operacoes_runtime": navegador,
            "_registro_navegador_leitura_runtime": NavegadorLeituraFake(aba={
                "url": "https://www.primevideo.com/detail/filme",
                "title": "Prime Video",
                "tabId": 91,
            }),
            "_executar_controle_midia_nativo": (
                lambda comando: comandos_nativos.append(comando) or True
            ),
        },
        marcar_resultado=lambda *_args, **_kwargs: None,
        falar_por_status=lambda *_args, **_kwargs: None,
        ctx_fala=lambda: {},
    )


def test_painel_de_musica_declara_alvo_musical_no_contrato_tipado() -> None:
    comando = comando_tipado_acao_painel(
        "media_toggle",
        {"command": "play"},
    )

    assert comando is not None
    resultado, _texto = comando
    assert resultado["params"]["platform"] == "music"


def test_play_musical_usa_aba_youtube_observada_mesmo_com_prime_em_foco() -> None:
    navegador = _NavegadorMusical()
    comandos_nativos: list[str] = []

    assert _executar_play_musical(
        tab_id_musical=42,
        navegador=navegador,
        comandos_nativos=comandos_nativos,
    ) is True

    assert navegador.chamadas == [("play", 42)]
    assert comandos_nativos == []


def test_play_musical_sem_id_pede_ao_navegador_um_alvo_compativel() -> None:
    navegador = _NavegadorMusical()
    comandos_nativos: list[str] = []

    assert _executar_play_musical(
        tab_id_musical=None,
        navegador=navegador,
        comandos_nativos=comandos_nativos,
    ) is True

    # Sem um vínculo canônico, ``None`` delega à extensão a busca entre abas
    # YouTube. O ID 91 do Prime Video jamais pode virar alvo nem tecla global.
    assert navegador.chamadas == [("play", None)]
    assert comandos_nativos == []


def test_falha_do_alvo_musical_nao_cai_em_tecla_global() -> None:
    navegador = _NavegadorMusical(resultado=False)
    comandos_nativos: list[str] = []

    assert _executar_play_musical(
        tab_id_musical=42,
        navegador=navegador,
        comandos_nativos=comandos_nativos,
    ) is False

    assert navegador.chamadas == [("play", 42)]
    assert comandos_nativos == []

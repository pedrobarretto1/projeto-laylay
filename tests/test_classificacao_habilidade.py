from __future__ import annotations

import pytest

from mente_laylay.autonomia.classificacao_habilidade import (
    classificar_habilidade_intent,
    extrair_alvo_mental,
)


@pytest.mark.parametrize(
    ("intent", "habilidade"),
    [
        ("PLAYLIST_ADD", "playlist"),
        ("TOCAR_PLAYLIST_SHUFFLE", "playlist"),
        ("LAYLAY_PLAYLIST_COPY", "playlist_laylay"),
        ("APP_OPEN", "navegacao"),
        ("OPEN_URL", "navegacao"),
        ("MUSIC_SEARCH", "midia"),
        ("MEDIA_CONTROL", "midia"),
        ("VOLUME", "audio"),
        ("CLOSE_TAB", "navegador"),
        ("SEARCH", "pesquisa"),
        ("WEATHER", "clima"),
        ("IOT_LIST", "iot"),
        ("FILE_SEARCH", "arquivos"),
        ("FILE_OPEN_RESULT", "arquivos"),
        ("AGENDAR_LEMBRETE", "agenda"),
        ("SUGGEST_ACTION", "sugestao"),
    ],
)
def test_classificacao_preserva_tabela_do_registro_curto(
    intent: str, habilidade: str
) -> None:
    assert classificar_habilidade_intent(intent) == habilidade


def test_classificacao_normaliza_caixa_e_espacos() -> None:
    assert classificar_habilidade_intent("  weather ") == "clima"
    assert classificar_habilidade_intent("DESCONHECIDA") == ""


def test_alvo_mental_preserva_prioridade_da_playlist() -> None:
    assert extrair_alvo_mental({
        "nome_playlist": "rock",
        "nome_app": "chrome",
        "query": "Duality",
    }) == "rock"


def test_alvo_mental_aceita_contexto_ausente() -> None:
    assert extrair_alvo_mental(None) == ""

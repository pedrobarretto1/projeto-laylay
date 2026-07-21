from __future__ import annotations

import json

from mente_laylay.autonomia.roteador_deterministico import (
    detectar_playlist_contextual_musica_atual,
)
from mente_laylay.integracao.chrome_ws_handlers import handle_player_event
from mente_laylay.memoria_mental.contexto_imediato import (
    resolver_comando_acao_geral_contextual,
    resolver_comando_midia_contextual,
)
from mente_laylay.memoria_mental.playlist_mental import limpar_nome_playlist
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime
from mente_laylay.personalidade.conversa_natural import (
    responder_comentario_jogo_em_foco,
)


def test_adicionar_musica_em_playlist_vence_replay_contextual() -> None:
    texto = "coloca essa musica na playlist alternativo"
    contexto_musical = {
        "tipo": "playlist",
        "alvo": "alternativo",
        "params": {"nome_playlist": "alternativo"},
    }

    assert resolver_comando_acao_geral_contextual(texto, contexto_musical) is None
    assert resolver_comando_midia_contextual(
        texto,
        mente_integrada_estado={"ultima_habilidade": "playlist", "ts": 1},
        contexto_musical=True,
    ) is None
    assert detectar_playlist_contextual_musica_atual(
        texto,
        params_cb=lambda **kwargs: kwargs,
        limpar_nome_playlist=limpar_nome_playlist,
    ) == {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "alternativo"},
    }


def test_comentario_sobre_esse_jogo_usa_jogo_em_foco() -> None:
    contexto = {
        "contexto_perceptivo": {
            "jogo": {
                "ativo": True,
                "processo": "Soulframe.x64.exe",
                "titulo": "Soulframe",
            }
        },
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_ajustar_fala_por_horario": lambda fala, _texto: fala,
    }

    resposta = responder_comentario_jogo_em_foco(contexto, "esse jogo é muito legal")

    assert "Soulframe" in resposta
    assert "o que mais" in resposta.casefold()


def test_falha_ao_abrir_proxima_musica_nao_avanca_indice(tmp_path) -> None:
    caminho = tmp_path / "playlists.json"
    caminho.write_text(json.dumps({
        "alternativo": [
            {"url": "https://youtube.com/watch?v=um", "titulo": "Um"},
            {"url": "https://youtube.com/watch?v=dois", "titulo": "Dois"},
        ]
    }), encoding="utf-8")
    estado = {"name": "alternativo", "index": 0, "last_url": "https://youtube.com/watch?v=um"}
    runtime = PlaylistRuntime(
        state_file=str(caminho),
        legacy_file=str(tmp_path / "legado.json"),
        cache={},
        ultima_playlist_getter=lambda: "alternativo",
        playlist_state=estado,
        youtube_play=lambda *_args, **_kwargs: False,
        log=lambda _linha: None,
    )

    assert runtime.avancar_proxima() is False
    assert estado["index"] == 0
    assert estado["name"] == "alternativo"
    assert estado["last_advance_status"] == "falha_execucao"


def test_falha_de_entrega_nao_e_anunciada_como_fim_da_playlist() -> None:
    falas: list[str] = []
    estado = {
        "name": "alternativo",
        "last_url": "https://youtube.com/watch?v=um",
        "last_advance_status": "ok",
    }

    def falhar_avanco() -> bool:
        estado["last_advance_status"] = "falha_execucao"
        return False

    handle_player_event(
        {
            "event": "video_ended",
            "eventId": "ended:um",
            "url": estado["last_url"],
            "duration": 180,
            "tabId": 12,
        },
        playlist_state=estado,
        yt_clean_url=lambda url: url,
        playlist_avancar_proxima=falhar_avanco,
        falar_com_lipsync=lambda texto, *_args: falas.append(texto),
    )

    assert falas == []
    assert estado["name"] == "alternativo"

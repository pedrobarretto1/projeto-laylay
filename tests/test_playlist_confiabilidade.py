from __future__ import annotations

import json

from mente_laylay.autonomia.execucao_ia import CoordenadorExecRuntime
from mente_laylay.memoria_mental.playlist_mental import (
    detectar_playlist_nome_direto,
    resolver_nome_playlist_contextual,
)
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


FAIXA = {
    "url": "https://www.youtube.com/watch?v=cxSzri346W0",
    "titulo": "Gostava Tanto de Você",
    "canal": "Tim Maia",
}


def _runtime(caminho, *, cache=None, youtube_play=None, logs=None) -> PlaylistRuntime:
    return PlaylistRuntime(
        state_file=str(caminho),
        legacy_file=str(caminho.parent / "playlists-legado.json"),
        cache=cache if cache is not None else {},
        ultima_playlist_getter=lambda: "",
        youtube_play=youtube_play,
        log=(logs if logs is not None else []).append,
    )


def test_nome_sem_acento_preserva_chave_real_da_playlist() -> None:
    data = {"música brasileira": [FAIXA]}

    assert resolver_nome_playlist_contextual("musica brasileira", data) == "música brasileira"
    assert detectar_playlist_nome_direto("coloca musica brasileira", data) == "música brasileira"


def test_modificador_de_genero_nao_e_engolido_por_playlist_prefixo() -> None:
    data = {"rock": [FAIXA]}

    assert detectar_playlist_nome_direto("coloca um rock pesado", data) == ""
    assert detectar_playlist_nome_direto("coloca rock pesado", data) == ""
    assert detectar_playlist_nome_direto("coloca rock agora", data) == "rock"


def test_playlist_existente_e_aberta_usando_um_unico_snapshot(tmp_path) -> None:
    caminho = tmp_path / "playlists.json"
    caminho.write_text(json.dumps({"musica brasileira": [FAIXA]}), encoding="utf-8")
    abertas: list[str] = []
    runtime = _runtime(
        caminho,
        cache={"playlist antiga": []},
        youtube_play=lambda url, **_kwargs: abertas.append(url) or True,
    )

    assert runtime.detectar_nome_direto_contextual("coloca musica brasileira") == "musica brasileira"
    assert runtime.play("musica brasileira") is True
    assert abertas == [FAIXA["url"]]


def test_falha_de_leitura_nao_apaga_arquivo_nem_cache(tmp_path) -> None:
    caminho = tmp_path / "playlists.json"
    conteudo_incompleto = '{"musica brasileira": ['
    caminho.write_text(conteudo_incompleto, encoding="utf-8")
    cache = {"musica brasileira": [FAIXA]}
    logs: list[str] = []
    runtime = _runtime(caminho, cache=cache, logs=logs)

    assert runtime.load() == cache
    assert caminho.read_text(encoding="utf-8") == conteudo_incompleto
    assert any("mantendo o último cache" in item for item in logs)


def test_movimento_so_confirma_depois_de_persistir_origem_e_destino(tmp_path) -> None:
    caminho = tmp_path / "playlists.json"
    caminho.write_text(
        json.dumps({"rock": [FAIXA], "treino": []}),
        encoding="utf-8",
    )
    runtime = _runtime(caminho)

    resultado = runtime.mover_item_contextual("rock", "treino", "Gostava")
    persistido = json.loads(caminho.read_text(encoding="utf-8"))

    assert resultado["ok"] is True
    assert persistido["rock"] == []
    assert persistido["treino"][0]["titulo"] == "Gostava Tanto de Você"


def test_movimento_nao_confirma_quando_persistencia_falha(tmp_path) -> None:
    caminho = tmp_path / "playlists.json"
    caminho.write_text(
        json.dumps({"rock": [FAIXA], "treino": []}),
        encoding="utf-8",
    )
    runtime = _runtime(caminho)
    runtime.save = lambda _data: False  # type: ignore[method-assign]

    resultado = runtime.mover_item_contextual("rock", "treino", "Gostava")

    assert resultado["ok"] is False
    assert resultado["error"] == "save_failed"
    assert runtime.cache["rock"][0]["titulo"] == "Gostava Tanto de Você"
    assert runtime.cache["treino"] == []


def test_entrada_identica_imediata_nao_e_executada_duas_vezes() -> None:
    chamadas: list[str] = []
    logs: list[str] = []
    coordenador = CoordenadorExecRuntime(
        contexto_exec_getter=lambda: None,
        resposta_ia_getter=lambda: None,
        loop_getter=lambda: None,
        log=logs.append,
    )
    coordenador._iniciar_thread = lambda texto: chamadas.append(texto) or object()  # type: ignore[method-assign]

    primeiro = coordenador.agendar("coloca musica brasileira")
    segundo = coordenador.agendar("  COLOCA   MUSICA BRASILEIRA ")

    assert primeiro is not None
    assert segundo is None
    assert chamadas == ["coloca musica brasileira"]
    assert any("duplicata imediata ignorada" in item for item in logs)

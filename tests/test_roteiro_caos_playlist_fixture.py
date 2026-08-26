from __future__ import annotations

import json

import pytest

from roteiro_teste_laylay_caos import (
    PLAYLIST_FIXTURE_NAME,
    _caminho_backup_fixture,
    _preparar_fixture_playlist,
    _restaurar_fixture_playlist,
)


def test_red_fixture_musical_do_caos_e_temporaria_e_reversivel(tmp_path) -> None:
    caminho = tmp_path / "playlists.json"
    original = json.dumps(
        {"playlist pessoal": [{"url": "https://example.test/pessoal"}]},
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")
    caminho.write_bytes(original)

    recibo = _preparar_fixture_playlist(caminho)

    durante = json.loads(caminho.read_text(encoding="utf-8"))
    assert _caminho_backup_fixture(caminho).is_file()
    assert durante["playlist pessoal"] == [
        {"url": "https://example.test/pessoal"}
    ]
    assert len(durante[PLAYLIST_FIXTURE_NAME]) >= 3
    assert all(
        "youtube.com/watch?v=" in item["url"]
        for item in durante[PLAYLIST_FIXTURE_NAME]
    )

    _restaurar_fixture_playlist(caminho, recibo)

    assert caminho.read_bytes() == original
    assert not _caminho_backup_fixture(caminho).exists()


def test_guard_fixture_remove_arquivo_que_nao_existia_antes(tmp_path) -> None:
    caminho = tmp_path / "playlists.json"

    recibo = _preparar_fixture_playlist(caminho)
    assert caminho.is_file()

    _restaurar_fixture_playlist(caminho, recibo)
    assert not caminho.exists()
    assert not _caminho_backup_fixture(caminho).exists()


def test_guard_fixture_nao_sobrescreve_catalogo_corrompido(tmp_path) -> None:
    caminho = tmp_path / "playlists.json"
    original = b"{catalogo-invalido"
    caminho.write_bytes(original)

    with pytest.raises(ValueError, match="playlists.json"):
        _preparar_fixture_playlist(caminho)

    assert caminho.read_bytes() == original
    assert not _caminho_backup_fixture(caminho).exists()


def test_guard_nova_execucao_recupera_fixture_abandonada(tmp_path) -> None:
    caminho = tmp_path / "playlists.json"
    original = b'{\r\n    "pessoal": []\r\n}'
    caminho.write_bytes(original)

    _preparar_fixture_playlist(caminho)
    assert PLAYLIST_FIXTURE_NAME in json.loads(
        caminho.read_text(encoding="utf-8")
    )

    # Simula o processo inteiro morrendo antes do ``finally``. A próxima
    # preparação precisa recuperar o recibo persistente antes de criar uma
    # nova fixture, sem transformar a fixture antiga em "original".
    segundo_recibo = _preparar_fixture_playlist(caminho)
    assert segundo_recibo == original

    _restaurar_fixture_playlist(caminho, segundo_recibo)
    assert caminho.read_bytes() == original
    assert not _caminho_backup_fixture(caminho).exists()

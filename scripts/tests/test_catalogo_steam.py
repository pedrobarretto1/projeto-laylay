from __future__ import annotations

from mente_laylay.autonomia import comandos_sistema
from mente_laylay.integracao.catalogo_steam import (
    listar_jogos_steam,
    resolver_jogo_steam,
)


def _criar_biblioteca(tmp_path):
    steam = tmp_path / "Steam"
    steamapps = steam / "steamapps"
    steamapps.mkdir(parents=True)
    (steamapps / "libraryfolders.vdf").write_text(
        '"libraryfolders"\n{\n  "0" { "path" "' + str(steam).replace("\\", "\\\\") + '" }\n}',
        encoding="utf-8",
    )
    (steamapps / "appmanifest_2694490.acf").write_text(
        '"AppState"\n{\n'
        '  "appid" "2694490"\n'
        '  "name" "Path of Exile 2"\n'
        '  "installdir" "Path of Exile 2"\n'
        '}',
        encoding="utf-8",
    )
    return steam


def test_catalogo_descobre_jogo_pelo_nome_comercial(tmp_path):
    steam = _criar_biblioteca(tmp_path)

    jogos = listar_jogos_steam([str(steam)])
    jogo = resolver_jogo_steam("path of exile 2", [str(steam)])

    assert [item["nome"] for item in jogos] == ["Path of Exile 2"]
    assert jogo is not None
    assert jogo["appid"] == "2694490"
    assert jogo["confianca"] == 1.0


def test_catalogo_aceita_pequeno_erro_mas_rejeita_nome_vago(tmp_path):
    steam = _criar_biblioteca(tmp_path)

    assert resolver_jogo_steam("path of exille 2", [str(steam)])["appid"] == "2694490"
    assert resolver_jogo_steam("path", [str(steam)]) is None


def test_abrir_programa_prioriza_protocolo_do_jogo_steam(monkeypatch):
    uris = []
    monkeypatch.setattr(
        comandos_sistema,
        "resolver_jogo_steam",
        lambda _nome: {
            "appid": "2694490", "nome": "Path of Exile 2", "confianca": 1.0,
        },
    )
    monkeypatch.setattr(
        comandos_sistema, "abrir_uri_sistema", lambda uri: uris.append(uri) or True,
    )

    assert comandos_sistema.abrir_programa("path of exile 2") is True
    assert uris == ["steam://rungameid/2694490"]

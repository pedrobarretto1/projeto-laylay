from __future__ import annotations

import base64
import json
from pathlib import Path

from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime
from mente_laylay.memoria_mental.operacoes_musicais_runtime import (
    OperacoesMusicaisRuntime,
)


def _item(video_id: str, titulo: str, *, duracao: int | None = None) -> dict:
    item = {
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "titulo": titulo,
        "canal": "Canal",
        "data": "2026-08-26",
        "titulo_norm": titulo.casefold(),
        "canal_norm": "canal",
    }
    if duracao is not None:
        item["duracao_segundos"] = duracao
    return item


def _runtime(tmp_path: Path, dados: dict, *, youtube_play=None) -> PlaylistRuntime:
    state = tmp_path / "playlists.json"
    state.write_text(json.dumps(dados), encoding="utf-8")
    return PlaylistRuntime(
        state_file=str(state),
        legacy_file=str(tmp_path / "legado.json"),
        cache={},
        ultima_playlist_getter=lambda: "",
        playlist_state={},
        youtube_play=youtube_play,
        artwork_dir=str(tmp_path / "artwork"),
        log=lambda _texto: None,
    )


def test_detalhe_e_paginado_pesquisavel_e_nao_publica_url(tmp_path: Path) -> None:
    dados = {"Anime": [_item(f"VIDEOTEST{i:02d}"[-11:], f"Faixa {i}") for i in range(140)]}
    runtime = _runtime(tmp_path, dados)

    detalhe = runtime.detalhar("Anime", consulta="Faixa 1", deslocamento=0, limite=500)

    assert detalhe["ok"] is True
    assert detalhe["limit"] == 100
    assert detalhe["total"] == 51
    assert len(detalhe["items"]) == 51
    assert detalhe["revision"]
    assert all(set(item) <= {
        "video_id", "title", "channel", "added_at", "duration_seconds", "artwork_url",
    } for item in detalhe["items"])
    assert "youtube.com" not in json.dumps(detalhe)
    assert "\\" not in json.dumps(detalhe)


def test_toca_faixa_exata_e_revisao_antiga_bloqueia_mutacao(tmp_path: Path) -> None:
    tocadas: list[str] = []
    runtime = _runtime(
        tmp_path,
        {"Anime": [_item("AAAAAAAAAAA", "Primeira"), _item("BBBBBBBBBBB", "Segunda")]},
        youtube_play=lambda url, **_kw: tocadas.append(url) or {"ok": True, "confirmado": True},
    )
    detalhe = runtime.detalhar("Anime")

    tocou = runtime.tocar_faixa_exata("Anime", "BBBBBBBBBBB", detalhe["revision"])

    assert tocou["ok"] is True
    assert tocadas == ["https://www.youtube.com/watch?v=BBBBBBBBBBB"]
    assert runtime.playlist_state["index"] == 1
    bloqueado = runtime.remover_faixa_exata("Anime", "AAAAAAAAAAA", "revisao-antiga")
    assert bloqueado == {"ok": False, "status": "revision_conflict"}


def test_copiar_e_idempotente_e_mover_preserva_origem_se_persistencia_falha(
    tmp_path: Path,
) -> None:
    runtime = _runtime(
        tmp_path,
        {"Origem": [_item("AAAAAAAAAAA", "Primeira")], "Destino": []},
    )
    revisao = runtime.detalhar("Origem")["revision"]

    primeira = runtime.copiar_faixa_exata("Origem", "Destino", "AAAAAAAAAAA", revisao)
    repetida = runtime.copiar_faixa_exata(
        "Origem", "Destino", "AAAAAAAAAAA", runtime.detalhar("Origem")["revision"],
    )

    assert primeira["ok"] is True and primeira["copied"] is True
    assert repetida["ok"] is True and repetida["copied"] is False
    assert runtime.detalhar("Origem")["total"] == 1
    assert runtime.detalhar("Destino")["total"] == 1

    runtime.save = lambda _dados: False  # type: ignore[method-assign]
    revisao = runtime.detalhar("Origem")["revision"]
    falhou = runtime.mover_faixa_exata("Origem", "Destino 2", "AAAAAAAAAAA", revisao)
    assert falhou == {"ok": False, "status": "save_failed"}
    assert runtime.detalhar("Origem")["total"] == 1


def test_remover_faixa_exata_nao_confunde_titulos_iguais(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, {"Anime": [
        _item("AAAAAAAAAAA", "Mesmo título"),
        _item("BBBBBBBBBBB", "Mesmo título"),
    ]})
    revisao = runtime.detalhar("Anime")["revision"]

    resultado = runtime.remover_faixa_exata("Anime", "BBBBBBBBBBB", revisao)

    assert resultado["ok"] is True
    restante = runtime.detalhar("Anime")["items"]
    assert [item["video_id"] for item in restante] == ["AAAAAAAAAAA"]


def test_duracao_opcional_sobrevive_sem_inventar_legado(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, {"Anime": [
        _item("AAAAAAAAAAA", "Legado"),
        _item("BBBBBBBBBBB", "Confirmada", duracao=185),
    ]})

    itens = runtime.detalhar("Anime")["items"]

    assert itens[0]["duration_seconds"] is None
    assert itens[1]["duration_seconds"] == 185
    persistido = json.loads(Path(runtime.state_file).read_text(encoding="utf-8"))
    assert "duracao_segundos" not in persistido["Anime"][0]
    assert persistido["Anime"][1]["duracao_segundos"] == 185


def test_capa_invalida_cai_para_thumbnail_e_capa_valida_vira_identificador_controlado(
    tmp_path: Path,
) -> None:
    runtime = _runtime(tmp_path, {"Anime": [_item("AAAAAAAAAAA", "Primeira")]})
    detalhe = runtime.detalhar("Anime")

    invalida = runtime.definir_capa("Anime", str(tmp_path / "ausente.png"), detalhe["revision"])
    assert invalida["ok"] is False
    assert runtime.detalhar("Anime")["artwork_url"].endswith("/AAAAAAAAAAA/hqdefault.jpg")

    png = tmp_path / "capa.png"
    png.write_bytes(base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    ))
    valida = runtime.definir_capa(
        "Anime", str(png), runtime.detalhar("Anime")["revision"],
    )
    assert valida["ok"] is True
    assert valida["artwork_url"].startswith("laylay-playlist-artwork://")
    assert str(tmp_path) not in valida["artwork_url"]
    restaurada = runtime.restaurar_capa("Anime", valida["revision"])
    assert restaurada["ok"] is True
    assert restaurada["artwork_url"].endswith("/AAAAAAAAAAA/hqdefault.jpg")


def test_trocar_e_restaurar_capa_remove_arquivos_que_ficaram_orfaos(tmp_path: Path) -> None:
    from PIL import Image

    runtime = _runtime(tmp_path, {"Anime": [_item("AAAAAAAAAAA", "Primeira")]})
    capa_1 = tmp_path / "capa-1.png"
    capa_2 = tmp_path / "capa-2.png"
    Image.new("RGB", (4, 4), "red").save(capa_1)
    Image.new("RGB", (4, 4), "blue").save(capa_2)

    primeira = runtime.definir_capa(
        "Anime", str(capa_1), runtime.detalhar("Anime")["revision"],
    )
    arquivo_1 = runtime.artwork_dir / primeira["artwork_url"].split("//", 1)[1]
    segunda = runtime.definir_capa("Anime", str(capa_2), primeira["revision"])
    arquivo_2 = runtime.artwork_dir / segunda["artwork_url"].split("//", 1)[1]

    assert not arquivo_1.exists()
    assert arquivo_2.exists()
    restaurada = runtime.restaurar_capa("Anime", segunda["revision"])
    assert restaurada["ok"] is True
    assert not arquivo_2.exists()


def test_adicionar_url_confirma_identidade_e_metadados_antes_de_persistir(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, {"Anime": []})
    rejeitada = runtime.adicionar_url_resolvida(
        "Anime", "https://www.youtube.com/watch?v=AAAAAAAAAAA",
        {"video_id": "BBBBBBBBBBB", "title": "Outra"},
    )
    aceita = runtime.adicionar_url_resolvida(
        "Anime", "https://www.youtube.com/watch?v=AAAAAAAAAAA",
        {"video_id": "AAAAAAAAAAA", "title": "Faixa", "channel": "Canal", "duration_seconds": 201},
    )
    assert rejeitada == {"ok": False, "status": "metadata_mismatch"}
    assert aceita["ok"] is True
    assert runtime.detalhar("Anime")["items"][0]["duration_seconds"] == 201


def test_resolvedor_padrao_confirma_duracao_na_pagina_do_mesmo_video(monkeypatch) -> None:
    class Resposta:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limite: int) -> bytes:
            return (
                b'<html>{"videoDetails":{"videoId":"AAAAAAAAAAA",'
                b'"title":"Faixa confirmada","lengthSeconds":"201",'
                b'"author":"Canal confirmado"}}</html>'
            )

    monkeypatch.setattr(
        "mente_laylay.memoria_mental.operacoes_musicais_runtime.urlopen",
        lambda *_args, **_kwargs: Resposta(),
    )

    resultado = OperacoesMusicaisRuntime._resolver_metadados_youtube(
        "https://www.youtube.com/watch?v=AAAAAAAAAAA",
    )

    assert resultado == {
        "video_id": "AAAAAAAAAAA",
        "title": "Faixa confirmada",
        "channel": "Canal confirmado",
        "duration_seconds": 201,
    }

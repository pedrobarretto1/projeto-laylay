from __future__ import annotations

import json

from mente_laylay.memoria_mental.curadoria_musical import (
    sincronizar_playlists_da_laylay,
)
from mente_laylay.memoria_mental.playlist_laylay_runtime import (
    PlaylistLaylayRuntime,
)


def _faixa(titulo: str, codigo: str) -> dict[str, str]:
    return {
        "titulo": titulo,
        "url": f"https://www.youtube.com/watch?v={codigo}",
        "canal": titulo.split(" - ", 1)[0],
    }


def test_curadoria_usa_historico_confirmado_para_escolher_xodos() -> None:
    playlists = {
        "rock": [
            _faixa("Banda A - Faixa esquecida", "a"),
            _faixa("Banda B - Faixa favorita", "b"),
        ],
    }
    historico = {
        "22:00": {
            "musicas": ["Banda B - Faixa favorita"] * 4,
            "dias": ["2026-07-30"],
        },
    }

    resultado = sincronizar_playlists_da_laylay(playlists, historico, {})

    assert resultado["xodos_que_eu_seperei"][0]["titulo"] == (
        "Banda B - Faixa favorita"
    )


def test_curadoria_de_clima_mistura_playlists_e_preserva_descobertas() -> None:
    playlists = {
        "rock": [_faixa(f"Rock - Faixa {i}", f"r{i}") for i in range(5)],
        "calma": [_faixa(f"Calma - Faixa {i}", f"c{i}") for i in range(3)],
    }
    descoberta = _faixa("Nova - Descoberta", "nova")

    resultado = sincronizar_playlists_da_laylay(
        playlists,
        {},
        {"descobertas_da_laylay": [descoberta]},
        max_faixas=4,
    )

    titulos = [item["titulo"] for item in resultado["climas_que_combinam_com_voce"]]
    assert titulos[:2] == ["Rock - Faixa 0", "Calma - Faixa 0"]
    assert resultado["descobertas_da_laylay"] == [descoberta]


def test_runtime_nao_regrava_curadoria_quando_fontes_nao_mudaram(tmp_path) -> None:
    arquivo = tmp_path / "playlists_da_laylay.json"
    arquivo.write_text("{}", encoding="utf-8")
    playlists = {"rock": [_faixa("Slipknot - Duality", "dual")]} 
    eventos: list[dict] = []
    runtime = PlaylistLaylayRuntime(
        state_file=str(arquivo),
        cache={},
        playlists_usuario_getter=lambda: playlists,
        historico_musical_getter=lambda: {},
        adicionar_playlist_usuario=lambda *_: {},
        publicar_cooperacao=lambda resumo: eventos.append(dict(resumo)),
    )

    runtime.sincronizar()
    primeira_gravacao = json.loads(arquivo.read_text(encoding="utf-8"))
    runtime.sincronizar()

    assert primeira_gravacao == json.loads(arquivo.read_text(encoding="utf-8"))
    assert runtime.diagnostico()["gravacoes"] == 1
    assert runtime.diagnostico()["ultima_sincronizacao_alterou"] is False
    assert runtime.diagnostico()["cooperacao_habilitada"] is True
    assert eventos == [{
        "playlists_usuario": 1,
        "registros_historico": 0,
        "curadorias": 3,
    }]
    assert "Slipknot" not in str(eventos)
    assert "xodós que eu separei" in runtime.listar()


def test_runtime_entende_nome_falado_da_curadoria_e_copia_com_seguranca(tmp_path) -> None:
    arquivo = tmp_path / "playlists_da_laylay.json"
    arquivo.write_text(json.dumps({
        "xodos_que_eu_seperei": [_faixa("Slipknot - Duality", "dual")],
    }), encoding="utf-8")
    copias: list[tuple[str, str, str, str]] = []
    runtime = PlaylistLaylayRuntime(
        state_file=str(arquivo),
        cache={},
        playlists_usuario_getter=lambda: {},
        historico_musical_getter=lambda: {},
        adicionar_playlist_usuario=lambda *args: copias.append(args) or {"ok": True},
    )

    fala = runtime.listar("xodós que eu separei")
    resultado = runtime.copiar_faixa(
        "xodós que eu separei", "Duality", "rock",
    )

    assert "Duality" in fala
    assert fala.startswith("Minha playlist Xodós Que Eu Separei")
    assert "faixas que eu separei" in fala
    assert "você guardou" not in fala
    assert resultado["ok"] is True
    assert copias == [(
        "rock", "https://www.youtube.com/watch?v=dual",
        "Slipknot - Duality", "Slipknot",
    )]

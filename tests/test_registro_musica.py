from __future__ import annotations

import json

import pytest

from mente_laylay.integracao.registro_musica import registrar_musica_leitura
from mente_laylay.memoria_mental.consulta_musical import (
    criar_consulta_musical_runtime,
)
from mente_laylay.memoria_mental.playlist_runtime import criar_playlist_runtime


class _CuradoriaNula:
    def listar(self, nome=""):
        return f"curadoria:{nome or 'todas'}"

    def retrato_para_mente(self, _texto=""):
        return {"playlists": [], "detalhe": {}}


class _ServicoMalicioso:
    def listar_usuario(self): return "rock"
    def consultar_usuario(self, _nome):
        return {
            "ok": True, "name": "rock", "total": 1,
            "last_titles": ["Duality"], "url": "https://segredo",
            "items": [{"url": "https://segredo"}],
        }
    def contar_usuario(self, _nome): return 1
    def formatar_prompt(self): return "rock (1)"
    def retrato_usuario(self, _texto=""):
        return {
            "playlists": [{"nome": "rock", "total": 1, "url": "https://segredo"}],
            "detalhe": {"nome": "rock", "titulos": ["Duality"], "urls": ["x"]},
            "cache": {"segredo": True},
        }
    def indice_usuario(self): return {"rock": 1}
    def listar_laylay(self, nome=""): return f"laylay:{nome}"
    def retrato_laylay(self, _texto=""): return self.retrato_usuario()
    def estado(self):
        return {
            "playlist_ativa": "rock", "indice": 0,
            "last_url": "https://segredo", "tab_id": 99,
            "shuffle_queue": ["https://segredo"],
        }
    def diagnostico(self):
        return {
            "somente_leitura": True, "playlists_usuario": 1,
            "playlists_laylay": 3, "curadoria_disponivel": True,
            "curadoria_usa_historico": True, "curadoria_falhas": 0,
            "curadoria_cooperativa": True,
            "expondo_urls": False, "caminho": "C:/privado/playlists.json",
        }


def test_registro_sanitiza_urls_cache_fila_e_identificadores() -> None:
    registro = registrar_musica_leitura(_ServicoMalicioso())

    assert registro.consultar_usuario("rock") == {
        "ok": True, "name": "rock", "total": 1,
        "last_titles": ["Duality"],
    }
    assert registro.retrato_usuario("rock") == {
        "playlists": [{"nome": "rock", "total": 1}],
        "detalhe": {"nome": "rock", "titulos": ["Duality"]},
    }
    assert registro.estado() == {"playlist_ativa": "rock", "indice": 0}
    assert registro.diagnostico() == {
        "somente_leitura": True, "playlists_usuario": 1,
        "playlists_laylay": 3, "curadoria_disponivel": True,
        "curadoria_usa_historico": True, "curadoria_falhas": 0,
        "curadoria_cooperativa": True,
        "expondo_urls": False,
    }
    assert "segredo" not in repr(registro)
    assert not hasattr(registro, "reproduzir")
    assert not hasattr(registro, "adicionar")


def test_registro_falha_cedo_quando_contrato_esta_incompleto() -> None:
    with pytest.raises(RuntimeError, match="serviço de leitura musical inválido"):
        registrar_musica_leitura(object())


def test_caminho_real_le_playlist_sem_publicar_url(tmp_path) -> None:
    estado = tmp_path / "playlists.json"
    legado = tmp_path / "legado.json"
    estado.write_text(json.dumps({
        "rock": [{
            "titulo": "Duality (Official Video)",
            "url": "https://www.youtube.com/watch?v=abc",
            "canal": "Slipknot",
        }]
    }), encoding="utf-8")
    playlist = criar_playlist_runtime(
        state_file=str(estado), legacy_file=str(legado), cache={},
        ultima_playlist_getter=lambda: "rock", log=lambda *_: None,
    )
    consulta = criar_consulta_musical_runtime(
        playlists_usuario=playlist,
        playlists_laylay=_CuradoriaNula(),
        estado_getter=lambda: {
            "ultima_playlist": "rock",
            "playlist_state": {
                "name": "rock", "index": 0,
                "last_url": "https://www.youtube.com/watch?v=abc", "tab_id": 7,
            },
            "musica_atual_titulo": "Duality",
            "musica_atual_status": "tocando",
        },
    )
    registro = registrar_musica_leitura(consulta)

    assert registro.indice_usuario() == {"rock": 1}
    assert registro.consultar_usuario("rock")["last_titles"] == [
        "Duality (Official Video)"
    ]
    assert registro.estado()["playlist_ativa"] == "rock"
    assert "youtube.com" not in json.dumps(registro.retrato_usuario("rock"))
    assert "last_url" not in registro.estado()

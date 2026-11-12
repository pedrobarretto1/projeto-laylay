"""Entrega parcial não equivale a áudio confirmado nem a falha de navegação."""
from copy import deepcopy
import json

import pytest

from mente_laylay.autonomia.rota_musical import RotaMusical
from scripts.tests.test_playlist_confiabilidade import FAIXA, _runtime


def receipt(status, **evidence):
    return {
        "ok": False, "confirmado": False, "status": status,
        "request_id": "reproducao-simulada",
        "tab": {"id": 42, "url": FAIXA["url"]},
        "evidence": evidence,
    }


@pytest.mark.parametrize("nome", ["alternativo", "rock", "jazz instrumental"])
@pytest.mark.parametrize("evidence", [
    {"playing": True, "audible": False, "muted": True, "volume": 1},
    {"playing": True, "audible": False, "muted": False, "volume": 0},
    {"playing": True, "audible": False, "muted": False, "volume": 1, "readyState": 1},
])
def test_video_iniciado_sem_audio_preserva_fila_e_observacao(tmp_path, nome, evidence):
    caminho = tmp_path / "playlists.json"
    caminho.write_text(json.dumps({nome: [FAIXA]}), encoding="utf8")
    bruto = receipt("playing_muted", **evidence)
    antes = deepcopy(bruto)
    chamadas = []
    runtime = _runtime(caminho, youtube_play=lambda *a, **k: chamadas.append((a, k)) or bruto)

    assert runtime.play(nome) is True
    assert runtime.playlist_state["name"] == nome
    assert runtime.playlist_state["tab_id"] == 42
    assert runtime.playlist_state["last_play_confirmed"] is False
    assert runtime.playlist_state["last_advance_status"] == "enviado_sem_confirmacao"
    assert runtime.playlist_state["last_play_result"]["evidence"] == evidence
    assert bruto == antes
    assert len(chamadas) == 1  # Não desmutar, alterar volume ou executar novamente.


@pytest.mark.parametrize("status", ["playing_muted", "autoplay_blocked"])
def test_rota_e_playlist_compartilham_entrega_parcial_sem_promover_audio(status):
    bruto = receipt(status, playing=status == "playing_muted", audible=False)
    resultado = RotaMusical._preservar_entrega_video(bruto, FAIXA["url"])
    assert resultado["ok"] is True
    assert resultado["confirmado"] is None
    assert resultado["status"] == "video_aberto_sem_confirmacao"
    assert resultado["status_executor"] == status
    assert resultado["evidence"] == bruto["evidence"]
    assert bruto["ok"] is False


@pytest.mark.parametrize("status", ["timeout", "error", "sem_confirmacao"])
def test_falha_nao_reaproveita_evidencia_para_aceitar_entrega(tmp_path, status):
    caminho = tmp_path / "playlists.json"
    caminho.write_text(json.dumps({"alternativo": [FAIXA]}), encoding="utf8")
    bruto = receipt(status, playing=True, audible=False)
    runtime = _runtime(caminho, youtube_play=lambda *a, **k: bruto)
    runtime.playlist_state.update(name="anterior", index=3)
    antes = deepcopy(runtime.playlist_state)
    assert runtime.play("alternativo") is False
    assert runtime.playlist_state == antes
    assert RotaMusical._preservar_entrega_video(bruto, FAIXA["url"])["ok"] is False


def test_confirmacao_completa_continua_distinta_do_resultado_parcial(tmp_path):
    caminho = tmp_path / "playlists.json"
    caminho.write_text(json.dumps({"alternativo": [FAIXA]}), encoding="utf8")
    bruto = {**receipt("playing_confirmed", playing=True, audible=True),
             "ok": True, "confirmado": True}
    runtime = _runtime(caminho, youtube_play=lambda *a, **k: bruto)
    assert runtime.play("alternativo") is True
    assert runtime.playlist_state["last_play_confirmed"] is True
    assert runtime.playlist_state["last_advance_status"] == "ok"


@pytest.mark.parametrize("ok", [True, False])
def test_status_parcial_nao_confirma_audio_por_booleano_generico(ok):
    bruto = {**receipt("playing_muted", playing=True, audible=False),
             "ok": ok, "confirmado": True}
    resultado = RotaMusical._preservar_entrega_video(bruto, FAIXA["url"])
    assert resultado["ok"] is True and resultado["confirmado"] is None


def test_receipt_contraditorio_nao_promove_inicio_do_video():
    bruto = receipt("playing_muted", playing=False, audible=False)
    assert RotaMusical._preservar_entrega_video(bruto, FAIXA["url"])["ok"] is False


def test_proxima_entrega_nao_herda_observacao_anterior(tmp_path):
    caminho = tmp_path / "playlists.json"
    caminho.write_text(json.dumps({"alternativo": [FAIXA]}), encoding="utf8")
    retornos = iter([receipt("playing_muted", playing=True, audible=False), True])
    runtime = _runtime(caminho, youtube_play=lambda *a, **k: next(retornos))
    assert runtime.play("alternativo") is True
    assert runtime.playlist_state["last_play_result"]
    assert runtime.play("alternativo") is True
    assert runtime.playlist_state["last_play_result"] == {}
    assert runtime.playlist_state["last_play_confirmed"] is True


def test_estado_publicado_isola_evidencia_da_fila(tmp_path):
    from mente_laylay.memoria_mental.operacoes_musicais_runtime import OperacoesMusicaisRuntime
    from mente_laylay.integracao.registro_operacoes_musicais import registrar_operacoes_musicais
    caminho = tmp_path / "playlists.json"
    caminho.write_text(json.dumps({"alternativo": [FAIXA]}), encoding="utf8")
    runtime = _runtime(caminho, youtube_play=lambda *a, **k: receipt("playing_muted", playing=True, audible=False))
    operacoes = OperacoesMusicaisRuntime(
        playlists_usuario=runtime, playlists_laylay=None,
        musica_estado_getter=lambda k,d=None:d, musica_estado_setter=lambda *a:None,
        solicitar_aba_ativa=lambda **k:{}, playlist_state=runtime.playlist_state)
    registro = registrar_operacoes_musicais(operacoes)
    assert registro.tocar_playlist("alternativo") is True
    observacao = registro.estado()["entrega_reproducao"]
    observacao["evidence"]["audible"] = True
    assert registro.estado()["entrega_reproducao"]["evidence"]["audible"] is False

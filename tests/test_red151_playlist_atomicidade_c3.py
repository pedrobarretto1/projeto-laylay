from __future__ import annotations

from pathlib import Path
import json

import mente_laylay.memoria_mental.playlist_mental as playlist_mental
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


URL = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
TITULO = "Faixa Atomicidade"
CANAL = "Canal Atomicidade"


def _novo_runtime(tmp_path):
    ultima = {"nome": ""}

    runtime = PlaylistRuntime(
        state_file=str(tmp_path / "playlists.json"),
        legacy_file=str(tmp_path / "playlists_legacy.json"),
        cache={},
        ultima_playlist_getter=lambda: ultima["nome"],
        ultima_playlist_setter=lambda nome: ultima.__setitem__(
            "nome", str(nome or "")
        ),
        playlist_state={},
        log=lambda *_args, **_kwargs: None,
        artwork_dir=str(tmp_path / "artwork"),
    )

    # Materializa o arquivo inicial de forma canônica.
    assert runtime.load() == {}

    return runtime, ultima


def _ler_disco(runtime):
    caminho = Path(runtime.state_file)
    if not caminho.exists():
        return {}
    bruto = caminho.read_text(encoding="utf-8").strip()
    return json.loads(bruto or "{}")


def test_red151_c3_create_falha_nao_pode_deixar_playlist_fantasma_no_cache(
    tmp_path,
    monkeypatch,
):
    """
    CREATE é transacional:

        mutação candidata
            -> persistência
            -> receipt OK
            -> commit no cache

    Se a persistência falhar, nem disco nem cache podem observar o alvo novo.
    """
    runtime, _ultima = _novo_runtime(tmp_path)

    monkeypatch.setattr(
        runtime,
        "save",
        lambda _dados: False,
    )

    resultado = runtime.create("vmz")

    assert resultado.get("ok") is False
    assert resultado.get("status") == "falha_persistencia"

    # O disco nunca confirmou a criação.
    assert "vmz" not in _ler_disco(runtime)

    # PRIMEIRA FRONTEIRA RED:
    # hoje create() altera o próprio self.cache antes de save().
    assert "vmz" not in runtime.cache, (
        "RED151-C3/CREATE: a persistência falhou, mas 'vmz' ficou "
        "materializada no cache."
    )

    # Uma leitura posterior também não pode ressuscitar o estado não confirmado.
    assert "vmz" not in runtime.load()


def test_red151_c3_add_falha_em_playlist_existente_nao_pode_vazar_faixa_no_cache(
    tmp_path,
    monkeypatch,
):
    """
    ADD em playlist existente também precisa ser atômico.

    Mesmo que uma releitura posterior consiga corrigir o cache pelo disco,
    não pode existir uma janela em que uma faixa não persistida apareça como
    se tivesse sido salva.
    """
    runtime, _ultima = _novo_runtime(tmp_path)

    criada = runtime.create("rock")
    assert criada.get("ok") is True
    assert runtime.load() == {"rock": []}

    monkeypatch.setattr(
        playlist_mental,
        "playlists_save",
        lambda _caminho, _dados: False,
    )

    resultado = runtime.add_and_verify_result(
        "rock",
        URL,
        TITULO,
        CANAL,
    )

    assert resultado.get("ok") is False
    assert resultado.get("status") == "falha_persistencia"

    # Disco permanece corretamente sem a faixa.
    assert _ler_disco(runtime) == {"rock": []}

    # PRIMEIRA FRONTEIRA RED:
    # a lista dentro do cache não pode ter sido alterada antes do receipt.
    assert runtime.cache.get("rock") == [], (
        "RED151-C3/ADD-EXISTENTE: a gravação falhou, mas a faixa "
        "apareceu no cache antes de qualquer confirmação."
    )

    assert runtime.load() == {"rock": []}


def test_red151_c3_add_falha_em_playlist_nova_nao_pode_persistir_fantasma_em_memoria(
    tmp_path,
    monkeypatch,
):
    """
    Caso mais perigoso:

    ADD direto de um nome novo longo é permitido e pode auto-criar a playlist.
    Se playlists_save falhar com o disco vazio, o fallback de load() não pode
    transformar o cache contaminado em fonte de verdade.
    """
    runtime, _ultima = _novo_runtime(tmp_path)

    monkeypatch.setattr(
        playlist_mental,
        "playlists_save",
        lambda _caminho, _dados: False,
    )

    resultado = runtime.add_and_verify_result(
        "caos sonora",
        URL,
        TITULO,
        CANAL,
    )

    assert resultado.get("ok") is False
    assert resultado.get("status") == "falha_persistencia"

    assert _ler_disco(runtime) == {}

    # Cache também precisa continuar vazio.
    assert "caos sonora" not in runtime.cache, (
        "RED151-C3/ADD-NOVO: a persistência falhou, mas a playlist/faixa "
        "ficou presente no cache."
    )

    # E uma releitura não pode ressuscitar o fantasma.
    assert "caos sonora" not in runtime.load()


def test_regressivo_c3_create_confirmado_continua_materializando_cache_e_disco(
    tmp_path,
):
    runtime, _ultima = _novo_runtime(tmp_path)

    resultado = runtime.create("vmz")

    assert resultado.get("ok") is True
    assert "vmz" in runtime.cache
    assert "vmz" in _ler_disco(runtime)
    assert "vmz" in runtime.load()


def test_regressivo_c3_add_confirmado_continua_materializando_cache_e_disco(
    tmp_path,
):
    runtime, _ultima = _novo_runtime(tmp_path)

    assert runtime.create("rock").get("ok") is True

    resultado = runtime.add_and_verify_result(
        "rock",
        URL,
        TITULO,
        CANAL,
    )

    assert resultado.get("ok") is True
    assert len(runtime.cache["rock"]) == 1
    assert len(_ler_disco(runtime)["rock"]) == 1
    assert len(runtime.load()["rock"]) == 1

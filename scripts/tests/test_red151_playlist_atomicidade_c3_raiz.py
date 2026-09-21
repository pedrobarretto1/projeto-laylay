from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


def _novo_runtime(tmp_path):
    ultima = {"nome": ""}

    runtime = PlaylistRuntime(
        state_file=str(tmp_path / "playlists.json"),
        legacy_file=str(tmp_path / "playlists_legacy.json"),
        cache={},
        ultima_playlist_getter=lambda: ultima["nome"],
        ultima_playlist_setter=lambda nome: ultima.__setitem__(
            "nome",
            str(nome or ""),
        ),
        playlist_state={},
        log=lambda *_args, **_kwargs: None,
        artwork_dir=str(tmp_path / "artwork"),
    )

    return runtime, ultima


def _ler_disco(runtime):
    caminho = Path(runtime.state_file)

    if not caminho.exists():
        return {}

    with caminho.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    return dados if isinstance(dados, dict) else {}


def test_red151_c3_raiz_load_deve_entregar_snapshot_desacoplado_do_cache(
    tmp_path,
):
    """
    load() é leitura.

    Alterar o objeto devolvido não pode alterar o estado oficial em memória
    sem passar por uma persistência confirmada.
    """
    runtime, _ultima = _novo_runtime(tmp_path)

    assert runtime.create("base longa").get("ok") is True

    snapshot = runtime.load()

    snapshot["fantasma"] = []

    assert "fantasma" not in runtime.cache, (
        "RED151-C3/LOAD: load() expôs a referência mutável do cache."
    )

    assert "fantasma" not in _ler_disco(runtime)


def test_red151_c3_raiz_delete_falha_nao_pode_apagar_cache(
    tmp_path,
    monkeypatch,
):
    """
    DELETE também precisa ser transacional.

    Se o receipt de persistência for False, cache e disco permanecem no
    estado anterior.
    """
    runtime, _ultima = _novo_runtime(tmp_path)

    assert runtime.create("alpha longa").get("ok") is True
    assert runtime.create("beta longa").get("ok") is True

    cache_antes = deepcopy(runtime.cache)
    disco_antes = deepcopy(_ler_disco(runtime))

    monkeypatch.setattr(
        runtime,
        "save",
        lambda _dados: False,
    )

    assert runtime.delete("alpha longa") is False

    assert runtime.cache == cache_antes, (
        "RED151-C3/DELETE-FAIL: DELETE falhou no disco, mas alterou o cache."
    )

    assert _ler_disco(runtime) == disco_antes


def test_red151_c3_raiz_delete_confirmado_preserva_restante_do_cache(
    tmp_path,
):
    """
    DELETE confirmado não pode esvaziar playlists que não participaram
    da operação.
    """
    runtime, _ultima = _novo_runtime(tmp_path)

    assert runtime.create("alpha longa").get("ok") is True
    assert runtime.create("beta longa").get("ok") is True

    assert runtime.delete("alpha longa") is True

    disco = _ler_disco(runtime)

    assert "alpha longa" not in disco
    assert "beta longa" in disco

    assert "alpha longa" not in runtime.cache

    assert "beta longa" in runtime.cache, (
        "RED151-C3/SYNC-ALIAS: DELETE confirmou no disco, mas _sync_cache "
        "esvaziou o restante do cache por alias da própria referência."
    )

    assert runtime.cache == disco


def test_red151_c3_raiz_save_com_proprio_cache_nao_pode_destruir_fonte(
    tmp_path,
):
    """
    _sync_cache precisa ser seguro mesmo quando recebe o próprio cache
    como fonte.
    """
    runtime, _ultima = _novo_runtime(tmp_path)

    assert runtime.create("alpha longa").get("ok") is True
    assert runtime.create("beta longa").get("ok") is True

    esperado = deepcopy(runtime.cache)

    assert runtime.save(runtime.cache) is True

    assert runtime.cache == esperado, (
        "RED151-C3/SAVE-ALIAS: save(self.cache) confirmou no disco, mas "
        "_sync_cache destruiu a própria fonte durante clear/update."
    )

    assert _ler_disco(runtime) == esperado

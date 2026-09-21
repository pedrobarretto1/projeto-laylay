"""Regressões do caminho local das credenciais Tuya.

Este teste NÃO lê a pasta credencia_tuya nem qualquer segredo.
"""

from mente_laylay.iot.configuracao import RAIZ_LAYLAY, resolver_caminho_laylay
from mente_laylay.iot.registro import criar_dispositivo_lampada


MARKER = "P0_TUYA_CAMINHO_RAIZ_LAYLAY_V2_20260815"


def test_caminho_tuya_relativo_independe_do_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    resolvido = resolver_caminho_laylay("credencia_tuya/devices.json")
    assert resolvido == RAIZ_LAYLAY / "credencia_tuya" / "devices.json"


def test_caminho_absoluto_continua_soberano(tmp_path):
    absoluto = (tmp_path / "tuya-fake" / "devices.json").resolve()
    assert resolver_caminho_laylay(absoluto) == absoluto


def test_lampada_aponta_primeiro_para_pasta_local_canonica():
    dispositivo = criar_dispositivo_lampada(protocolo="tuya")
    config = dict(dispositivo.configuracao)
    assert config["snapshot_path"] == "credencia_tuya/snapshot.json"
    assert config["snapshot_fallback_paths"][0] == "credencia_tuya/devices.json"

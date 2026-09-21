"""Guardas do diagnóstico offline; não representam execução da assistente."""

import hashlib
import json

import pytest

from mente_laylay.neural import diagnostico_regressoes_regional as diagnostico


@pytest.mark.parametrize("diretorio", [False, True])
def test_destino_existente_e_preservado_antes_de_ler_fontes(tmp_path, diretorio):
    saida = tmp_path / "diagnostico"
    if diretorio:
        saida.mkdir()
    else:
        saida.write_text("evidencia anterior", encoding="utf-8")
    with pytest.raises(FileExistsError, match="preservar"):
        diagnostico.executar(
            experimento=tmp_path / "ausente",
            referencia=tmp_path / "ausente",
            historico=tmp_path / "ausente",
            saida=saida,
        )
    if diretorio:
        assert list(saida.iterdir()) == []
    else:
        assert saida.read_text(encoding="utf-8") == "evidencia anterior"


def test_fonte_alterada_aborta_antes_de_carregar_dados_ou_modelo(tmp_path, monkeypatch):
    fonte = tmp_path / "fonte.py"
    fonte.write_bytes(b"versao alterada")
    protocolo = {"fontes": {str(fonte): hashlib.sha256(b"versao original").hexdigest()}}
    for nome, dados in (("protocolo.json", protocolo), ("relatorio.json", {})):
        (tmp_path / nome).write_text(json.dumps(dados), encoding="utf-8")

    def nao_deve_chegar(*args, **kwargs):
        pytest.fail("proveniencia invalida deve abortar antes de dados/modelo/fit")

    for nome in ("carregar_jsonl", "carregar_modelo", "ajustar_cabeca"):
        monkeypatch.setattr(diagnostico, nome, nao_deve_chegar)
    saida = tmp_path / "resultado.json"
    with pytest.raises(ValueError, match="fonte mudou"):
        diagnostico.executar(
            experimento=tmp_path, referencia=tmp_path,
            historico=tmp_path / "ausente", saida=saida,
        )
    assert not saida.exists()
    assert fonte.read_bytes() == b"versao alterada"

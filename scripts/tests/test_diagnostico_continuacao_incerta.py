"""A sonda varia instruções, não reescreve histórico nem aciona a Laylay."""
from copy import deepcopy
import json

import pytest

from scripts.analises import diagnosticar_continuacao_incerta as sonda


def payload():
    return {"model": "qwen3:4b-instruct", "max_tokens": 256, "temperature": 0.7,
            "messages": [
                {"role": "system", "content": 'Regras originais. Retorne somente JSON válido: {"fala":"","comandos":[]}'},
                {"role": "user", "content": "como funciona a divisão?"},
                {"role": "assistant", "content": "Quer um exemplo?"},
                {"role": "system", "content": "Contrato do turno."},
                {"role": "user", "content": "quero im"},
            ]}


@pytest.mark.parametrize("variante", sonda.VARIANTES)
def test_ablacao_preserva_historico_parametros_e_payload_original(variante):
    original = payload()
    antes = deepcopy(original)
    resultado = sonda.preparar_variante(original, variante, "quero sim", 17)
    assert original == antes
    assert resultado["messages"][1:3] == antes["messages"][1:3]
    assert resultado["messages"][-1] == {"role": "user", "content": "quero sim"}
    for chave in ("model", "max_tokens", "temperature"):
        assert resultado[chave] == antes[chave]
    assert resultado["seed"] == 17
    assert ('Contrato do turno.' in str(resultado)) == (variante in {"capturado", "identidade_formato"})
    assert ('Regras originais.' in str(resultado)) == (variante in {"capturado", "sem_contrato"})
    assert '"comandos":[]' in resultado["messages"][0]["content"]


def test_captura_ambigua_aborta_antes_de_gerar(tmp_path, monkeypatch):
    monkeypatch.setattr(sonda, "RAIZ", tmp_path)
    pasta = tmp_path / "resultados_testes"
    pasta.mkdir()
    captura = pasta / "captura.jsonl"
    linha = json.dumps({"etapa": "envio", "payload": payload()}) + "\n"
    captura.write_text(linha * 2, encoding="utf-8")
    with pytest.raises(ValueError, match="exatamente um"):
        sonda.carregar_payload(captura, "quero im")


def test_schema_inesperado_aborta_sem_inventar_formato():
    original = payload()
    original["messages"][0]["content"] = "Outro formato."
    with pytest.raises(ValueError, match="schema"):
        sonda.preparar_variante(original, "minimo", "quero im", 17)

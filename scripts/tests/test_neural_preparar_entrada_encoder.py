"""Integração com tokenizer fixado e projeção reais, sem treinamento."""
from copy import deepcopy

import pytest

from mente_laylay.neural.preparar_contrastes_piloto import gerar_lote
from mente_laylay.neural.preparar_entrada_encoder import (
    carregar_tokenizer, conferir_equivalencia, executar, preparar, representar_texto,
)
from mente_laylay.neural.sonda_ambiente_encoder import PASTA_MODELO


@pytest.fixture
def tokenizer():
    caminho = PASTA_MODELO / "tokenizer.json"
    if not caminho.is_file():
        pytest.skip("tokenizer local fixado indisponível")
    return carregar_tokenizer(caminho)


def test_mesmo_texto_tem_mesma_entrada_independente_do_rotulo(tokenizer):
    casos = gerar_lote()[:1]
    antes = deepcopy(casos)
    a = preparar(casos, tokenizer, particao="desenvolvimento")
    casos[0]["fonte_v4"]["nos"][0]["ato"] = "relato"
    b = preparar(casos, tokenizer, particao="desenvolvimento")
    assert a["exemplos"][0]["entrada"] == b["exemplos"][0]["entrada"]
    assert a["exemplos"][0]["supervisao"] != b["exemplos"][0]["supervisao"]
    assert a["exemplos"][0]["entrada"]["texto"] == antes[0]["texto"]


def test_lote_real_preserva_nomes_negados_e_todos_tokens(tokenizer):
    casos = gerar_lote()
    antes = deepcopy(casos)
    r = preparar(casos, tokenizer, particao="desenvolvimento")
    assert casos == antes
    assert len(r["exemplos"]) == 27 and len(r["fora_perfil"]) == 6
    for e in r["exemplos"]:
        assert len(e["supervisao"]["rotulos"]) == len(e["entrada"]["mapa_tokens"])
        assert sum(x != "ausente" for x in e["supervisao"]["rotulos"]) == 1
        for t in e["entrada"]["mapa_tokens"]:
            assert sum(t["pesos"]) == pytest.approx(1)
            assert not any(e["entrada"]["especiais"][i] for i in t["indices"])
    assert r["treino_permitido"] is False
    assert r["auditoria_corpus"]["dados_prontos_para_preparacao"] is False


def test_texto_longo_e_truncamento_configurado_abortam(tokenizer):
    with pytest.raises(ValueError, match="excede comprimento"):
        representar_texto("palavra " * 200, tokenizer)
    tokenizer.enable_truncation(max_length=8)
    with pytest.raises(ValueError, match="sem truncamento"):
        representar_texto("leia notas.txt", tokenizer)


def test_preparacao_treino_nao_contorna_gate_do_corpus(tokenizer):
    with pytest.raises(ValueError, match="corpus não pronto"):
        preparar(gerar_lote(), tokenizer, particao="treino")
    with pytest.raises(ValueError, match="nunca reserva"):
        preparar(gerar_lote(), tokenizer, particao="reserva")


def test_mapa_adulterado_diverge_do_agregador_real(tokenizer):
    entrada = representar_texto('Leia o arquivo "não apagar.txt".', tokenizer)
    conferir_equivalencia(entrada)
    entrada["mapa_tokens"][0]["indices"] = [0]
    entrada["mapa_tokens"][0]["pesos"] = [1.0]
    with pytest.raises(ValueError, match="diverge"):
        conferir_equivalencia(entrada)


def test_tokenizer_adulterado_e_destino_existente_abortam(tmp_path):
    fonte = tmp_path / "tokenizer.json"
    fonte.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="revisão fixada"):
        carregar_tokenizer(fonte)
    with pytest.raises(FileExistsError, match="preservar"):
        executar(tmp_path / "inexistente", tmp_path)

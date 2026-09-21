"""Contratos de representação, não testes de compreensão de um modelo treinado."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import pickle

import pytest
from sklearn.exceptions import NotFittedError
from sklearn.feature_extraction.text import TfidfVectorizer

from mente_laylay.neural.modelo import enriquecer_texto_estrutura_pontuacao
from mente_laylay.neural.representacao_integral import (
    criar_extrator_texto_integral_v1, representar_texto_integral_v1,
)


BATERIA = json.loads((Path(__file__).parent / "fixtures/neural/bateria_linguistica_v1.json").read_text(encoding="utf-8"))
CASOS = {caso["id"]: caso for caso in BATERIA["casos"]}
LONGOS = [p for p in BATERIA["pares"] if p["destino"].endswith(":negacao_no_meio")]


def test_bateria_cobre_quatro_dominios_com_mesmos_contratos_sem_autoridade():
    assert BATERIA["treino_permitido"] is False
    assert BATERIA["autoriza_execucao"] is False
    assert len(CASOS) == len(BATERIA["casos"]) == 44
    assert len(BATERIA["pares"]) == 32
    assert Counter(x["dominio_da_fatia"] for x in CASOS.values()) == {
        "volume": 11, "musica": 11, "aplicativos": 11, "arquivos": 11,
    }
    assert all(x["autoriza_execucao"] is False for x in CASOS.values())
    assert all(x["contexto"] is None for x in CASOS.values())
    for dominio in ("volume", "musica", "aplicativos", "arquivos"):
        referencia = CASOS[f"{dominio}:referencia_sem_contexto"]["esperado"]
        assert referencia["requer_contexto"] is True
        assert referencia["alvo_literal"] is None
        assert "dominio" not in referencia


@pytest.mark.parametrize("par", BATERIA["pares"], ids=lambda p: p["origem"] + "->" + p["destino"])
def test_expectativas_linguisticas_dos_pares_sao_consistentes(par):
    antes = CASOS[par["origem"]]["esperado"]
    depois = CASOS[par["destino"]]["esperado"]
    if par["relacao"] == "invariancia_semantica":
        assert antes == depois
    elif par["relacao"] == "contraste_pedido":
        assert antes["pedido_operacional"] is True
        assert depois["pedido_operacional"] is False
    elif par["relacao"] == "correcao_alvo":
        assert antes["alvo_literal"] != depois["alvo_literal"]
        assert depois["pedido_operacional"] is True
        assert depois["negacao_do_pedido"] is False
    elif par["relacao"] == "correcao_parametro":
        assert antes["alvo_literal"] == depois["alvo_literal"] == "volume"
        assert depois["acao_pedida"] == "definir"
        assert depois["valor_literal"] == 30
        assert depois["pedido_operacional"] is True
        assert depois["negacao_do_pedido"] is False
    else:
        pytest.fail("relação desconhecida")


@pytest.mark.parametrize("caso", BATERIA["casos"], ids=lambda c: c["id"])
def test_toda_frase_chega_inteira_ao_canal_lexical(caso):
    texto = caso["text"]
    representacao = representar_texto_integral_v1(texto)
    assert set(representacao) == {"texto_integral", "estrutura"}
    assert representacao["texto_integral"] == texto
    assert representacao["estrutura"] == enriquecer_texto_estrutura_pontuacao(texto)
    canais = dict(criar_extrator_texto_integral_v1().transformer_list)
    for nome in ("palavras_integrais", "caracteres_integrais"):
        assert canais[nome].build_preprocessor()(texto) == texto


@pytest.mark.parametrize("par", LONGOS, ids=lambda p: p["origem"])
def test_negacao_no_meio_deixa_de_colidir_sem_alterar_representacao_legada(par):
    pedido = CASOS[par["origem"]]["text"]
    negado = CASOS[par["destino"]]["text"]
    # RED histórico continua demonstrável: não alterar a função serializada antiga.
    assert enriquecer_texto_estrutura_pontuacao(pedido) == enriquecer_texto_estrutura_pontuacao(negado)
    assert representar_texto_integral_v1(pedido) != representar_texto_integral_v1(negado)
    canais = dict(criar_extrator_texto_integral_v1().transformer_list)
    for nome in ("palavras_integrais", "caracteres_integrais"):
        analisar = canais[nome].build_analyzer()
        assert Counter(analisar(pedido)) != Counter(analisar(negado))
    assert "não" in canais["palavras_integrais"].build_analyzer()(negado)


@pytest.mark.parametrize("par", [p for p in BATERIA["pares"] if p["relacao"] != "invariancia_semantica"])
def test_contrastes_chegam_diferentes_ao_analisador_sem_treino(par):
    analisar = dict(criar_extrator_texto_integral_v1().transformer_list)["caracteres_integrais"].build_analyzer()
    assert Counter(analisar(CASOS[par["origem"]]["text"])) != Counter(analisar(CASOS[par["destino"]]["text"]))


@pytest.mark.parametrize("texto", [
    '  não\tabra “a”\npor favor?!  ',
    "é e à a avó avô café cafe",
    "prefixo_1_nao marcador_citacao_total são palavras literais",
    "começo " + "meio " * 150 + "não abra o final.txt",
])
def test_preserva_unicode_pontuacao_espacos_e_texto_longo(texto):
    assert representar_texto_integral_v1(texto)["texto_integral"] == texto
    analisar = dict(criar_extrator_texto_integral_v1().transformer_list)["palavras_integrais"].build_analyzer()
    if texto.startswith("é e"):
        assert {"é", "e", "à", "a", "avó", "avô", "café", "cafe"} <= set(analisar(texto))


@pytest.mark.parametrize("texto,erro", [(None, TypeError), (123, TypeError), ("", ValueError), (" \t", ValueError)])
def test_entrada_invalida_nao_vira_texto_fabricado(texto, erro):
    with pytest.raises(erro):
        representar_texto_integral_v1(texto)


def test_extrator_serializavel_nao_ajusta_vocabulario_nem_treina(monkeypatch):
    def fit_proibido(*args, **kwargs):
        pytest.fail("esta etapa não pode ajustar vocabulário ou treinar")
    monkeypatch.setattr(TfidfVectorizer, "fit", fit_proibido)
    monkeypatch.setattr(TfidfVectorizer, "fit_transform", fit_proibido)
    extrator = pickle.loads(pickle.dumps(criar_extrator_texto_integral_v1()))
    assert len(extrator.transformer_list) == 3
    for _, canal in extrator.transformer_list:
        assert not hasattr(canal, "vocabulary_")
        assert canal.build_analyzer()("não abra o arquivo")
        with pytest.raises(NotFittedError):
            canal.transform(["não abra o arquivo"])

"""Controles de diagnóstico não são um novo roteador de comandos."""
from copy import deepcopy

import pytest
from sklearn.feature_extraction import DictVectorizer

from mente_laylay.neural.candidato_relacional import atributos_acao
from mente_laylay.neural.diagnosticar_head_relacional import (
    CONDICOES, auditar_vocabulario, medir_acoes, montar_linhas, representar,
)
from mente_laylay.neural.treinar_relacional_isolado import carregar_desenvolvimento, VARIANTES


@pytest.fixture(scope="module")
def exemplos():
    return carregar_desenvolvimento()[0]


def test_original_repete_atributos_e_supervisao_do_candidato_sem_metadados(exemplos):
    x, y, chaves = montar_linhas(exemplos, sorted(VARIANTES), "original")
    n = 0
    for e in exemplos:
        for pos, s in enumerate(e["entrada"]["segmentos"]):
            anotado = next(a for a in e["segmentos_anotados"] if a["indice"] == s["indice"])
            for v in sorted(VARIANTES):
                acao = next((a for a in anotado["acoes"] if (a["intent"], a["action"]) == v), None)
                assert x[n] == atributos_acao(e["entrada"], pos, v)
                assert y[n] == (acao["ato"] + "/" + acao["resolucao_alvo"] if acao else "ausente")
                assert chaves[n] == (e["id"], s["indice"], *v)
                assert "id" not in x[n] and "grupo_construcao" not in x[n]
                n += 1
    assert n == len(x) == 324
    assert sum(r != "ausente" for r in y) == 96


@pytest.mark.parametrize("variante", sorted(VARIANTES))
def test_cruzamento_nao_escolhe_variante_pelo_esperado(exemplos, variante):
    entrada = exemplos[0]["entrada"]
    antes = deepcopy(entrada)
    original = representar(entrada, 0, variante, "original")
    cruzada = representar(entrada, 0, variante, "cruzada")
    assert {k: cruzada[k] for k in original} == original
    novos = set(cruzada) - set(original)
    prefixo = "cruzamento:" + "/".join(variante) + ":"
    assert novos == {prefixo + k for k in original if k.startswith(("entrada:", "dono:"))}
    assert entrada == antes


def test_fatorial_tem_controles_pareados_sem_busca_por_score():
    assert {(modo, limite) for _, modo, limite in CONDICOES} == {
        (modo, limite) for modo in ("original", "cruzada") for limite in (180, 1200)}


def test_metricas_contam_ausencias_extras_e_recusa_transformada_em_pedido():
    chaves = [("caso", 0, "APP_OPEN", "open"), ("caso", 0, "FILE_READ", "read"),
              ("segundo", 0, "APP_OPEN", "open")]
    r = medir_acoes(chaves, ["pedido/explicito", "ausente", "recusa/nao_aplicavel"],
                   ["ausente", "pedido/explicito", "pedido/explicito"])
    assert r["casos"] == 2 and r["casos_exatos_acao_sem_alvos"] == 0
    assert r["acoes_esperadas"] == 2
    assert r["acoes_ausentes"] == r["acoes_extras"] == 1
    assert r["pedidos_inventados"] == 2
    assert len(r["erros"]) == 3


@pytest.mark.parametrize("previsoes", [[], ["ausente"], ["ausente"] * 3])
def test_resultados_truncados_nao_viram_acerto(previsoes):
    chaves = [("a", 0, "APP_OPEN", "open"), ("b", 0, "APP_OPEN", "open")]
    with pytest.raises(ValueError):
        medir_acoes(chaves, ["ausente"] * 2, previsoes)


def test_vocabulario_diagnostico_nao_aprende_atributos_do_teste():
    vec = DictVectorizer().fit([{"conhecido": 1, "categoria": "a"}])
    antes = deepcopy(vec.vocabulary_)
    r = auditar_vocabulario(vec, [{"conhecido": 2, "categoria": "b", "inedito": 1}])
    assert r == {"features_distintas_teste": 3, "features_fora_vocabulario": 2}
    assert vec.vocabulary_ == antes


@pytest.mark.parametrize("campo", ["autoriza_execucao", "anotacao", "variante_esperada"])
def test_ambas_representacoes_rejeitam_metadados_gold(exemplos, campo):
    entrada = deepcopy(exemplos[0]["entrada"])
    entrada[campo] = True
    for modo in ("original", "cruzada"):
        with pytest.raises(ValueError):
            representar(entrada, 0, ("APP_OPEN", "open"), modo)


def test_caso_sem_variante_coberta_nao_e_descartado(exemplos):
    with pytest.raises(ValueError, match="denominador"):
        montar_linhas(exemplos, [("FILE_READ", "read")], "original")


def test_reserva_nao_entra_no_diagnostico(exemplos):
    lote = deepcopy(exemplos[:1])
    lote[0]["papel_dataset"] = "reserva_independente"
    with pytest.raises(ValueError, match="desenvolvimento"):
        montar_linhas(lote, sorted(VARIANTES), "original")

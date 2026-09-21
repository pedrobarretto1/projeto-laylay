import json

import joblib
import pytest

from mente_laylay.neural.diagnostico_pistas_negacao import explicar_pistas
from mente_laylay.neural.diagnostico_transferencia_escopo import diagnosticar
from mente_laylay.neural.modelo import _pipeline
from mente_laylay.neural.representacao_escopo_local import (
    criar_prototipo_escopo_local, extrair_pistas_escopo_local, segmentar_estrutura_local,
)


@pytest.mark.parametrize("recusa,correcao", [
    ("não quero que você abra o Opera", "quero que você abra o Opera, não o Firefox"),
    ("não coloque o volume em 30", "coloque o volume em 30, não em 50"),
    ('não toque "Brisa"', 'toque "Brisa", não "Aurora"'),
    ('não leia "rascunho.txt"', 'leia "rascunho.txt", não "relatório.txt"'),
])
def test_contrastes_tem_pistas_distintas_sem_rotulo_embutido(recusa, correcao):
    assert extrair_pistas_escopo_local(recusa) != extrair_pistas_escopo_local(correcao)
    assert set(segmentar_estrutura_local(recusa)) == {"texto_original", "aspas_coerentes", "partes"}


def test_ordem_nao_colapsa_em_saco_de_palavras():
    assert set(extrair_pistas_escopo_local("não abra A; abra B")) != set(extrair_pistas_escopo_local("abra A; não abra B"))


def test_literal_e_numero_novos_nao_mudam_pistas_estruturais():
    assert extrair_pistas_escopo_local('toque "Não Volte"') == extrair_pistas_escopo_local('toque "Outra Faixa"')
    assert extrair_pistas_escopo_local("volume em 30, não em 50") == extrair_pistas_escopo_local("volume em 83, não em 96")


def test_negacao_externa_nao_e_confundida_com_conteudo_citado():
    assert extrair_pistas_escopo_local('toque "Não Volte"') != extrair_pistas_escopo_local('não toque "Volte"')


@pytest.mark.parametrize("texto", ['leia “não apagar.txt”', "toque 'Não Volte'", 'leia "não \'executar\'.txt"'])
def test_spans_preservam_offsets_do_original_inclusive_aspas_aninhadas(texto):
    r = segmentar_estrutura_local(texto)
    assert r["texto_original"] == texto
    citados = [p for p in r["partes"] if p["tipo"] == "citado"]
    assert len(citados) == 1
    for p in r["partes"]:
        assert texto[p["inicio"]:p["fim"]] == p["texto"]


def test_aspas_incoerentes_nao_ocultam_negacao():
    r = segmentar_estrutura_local('leia "não apagar.txt')
    assert not r["aspas_coerentes"]
    assert not any(p["tipo"] == "citado" for p in r["partes"])
    assert any(p["texto"] == "não" for p in r["partes"])


def test_categoria_digitada_nao_se_passa_por_metadado():
    assert extrair_pistas_escopo_local('leia citado') != extrair_pistas_escopo_local('leia "citado"')


@pytest.mark.parametrize("texto", [None, "", "  "])
def test_entrada_invalida_aborta(texto):
    with pytest.raises(ValueError):
        segmentar_estrutura_local(texto)


def test_prototipo_preserva_canais_legados_e_serializa(tmp_path):
    base = _pipeline([False, True], representacao="tfidf_indicadores", estrategia="sgd_log_loss")
    antes = joblib.hash(base)
    novo = criar_prototipo_escopo_local(base)
    assert joblib.hash(base) == antes
    for (_, a), (_, b) in zip(base.named_steps['features'].transformer_list, novo.named_steps['features'].transformer_list):
        assert a.get_params() == b.get_params()
    textos = ['toque "Não Volte"', 'não toque "Volte"', 'abra o editor', 'não abra o editor']
    novo.fit(textos, [False, True, False, True])
    assert joblib.hash(base) == antes
    p = tmp_path / "teste.joblib"
    joblib.dump(novo, p)
    assert list(joblib.load(p).predict(textos)) == list(novo.predict(textos))


def test_explicacao_reconstroi_tres_canais_sem_mutar_modelo():
    base = _pipeline([False, True], representacao="tfidf_indicadores", estrategia="sgd_log_loss")
    textos = ['toque "Brisa", não "Aurora"', 'não toque "Brisa"', 'abra o editor', 'não abra o editor']
    h = criar_prototipo_escopo_local(base).fit(textos, [False, True, False, True])
    digest = joblib.hash(h)
    r = explicar_pistas(h, textos[0])
    assert set(r["canais"]) == {"palavras", "caracteres", "escopo_local"}
    assert r["score"] == pytest.approx(r["intercepto"] + sum(c["soma_contribuicoes"] for c in r["canais"].values()))
    assert joblib.hash(h) == digest


def test_diagnostico_transferencia_nao_sobrescreve(tmp_path):
    with pytest.raises(FileExistsError):
        diagnosticar(experimento=tmp_path / "ausente", saida=tmp_path)

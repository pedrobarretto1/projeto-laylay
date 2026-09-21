import json

import joblib
import numpy as np
import pytest

from mente_laylay.neural.representacao_escopo_local import extrair_pistas_escopo_local
from mente_laylay.neural.representacao_regioes_texto import (
    representar_regioes_texto, extrair_pistas_regioes, criar_extrator_regioes_texto,
)


@pytest.mark.parametrize("texto", [
    '  toque "Não Volte"\n', 'leia “não apagar.txt”', "toque 'Brisa'",
    'leia "não \'executar\'.txt"', 'abre o Opera, não o Firefox',
    'coloca o volume em 30, não em 50', 'leia "não apagar.txt',
    '"não abra" e "abra"', 'toque d\'água', 'não leia o arquivo não.txt',
])
def test_regioes_preservam_todos_os_caracteres_e_offsets(texto):
    r = representar_regioes_texto(texto)
    cursor = 0
    for reg in r["regioes"]:
        assert reg["inicio"] == cursor
        assert texto[reg["inicio"]:reg["fim"]] == reg["texto"]
        cursor = reg["fim"]
    assert cursor == len(texto)
    assert "".join(reg["texto"] for reg in r["regioes"]) == texto
    assert not r["resolve_alvo"] and not r["autoriza_execucao"]


def test_contrato_historico_colapsa_citacao_total_mas_conteudo_regional_nao():
    a, b = '"abra o Opera"', '"não abra o Opera"'
    assert extrair_pistas_escopo_local(a) == extrair_pistas_escopo_local(b)
    assert extrair_pistas_regioes(a) != extrair_pistas_regioes(b)


def test_negacao_dentro_e_fora_tem_namespaces_distintos():
    pistas = [json.loads(p) for p in extrair_pistas_regioes('não toque "Não Volte"')]
    assert ["exterior", "sequencia", ["nao"]] in pistas
    assert ["citado", "sequencia", ["nao"]] in pistas


def test_nao_cria_sequencia_entre_citacoes_distintas():
    pistas = [json.loads(p) for p in extrair_pistas_regioes('"não" "abra"')]
    assert ["citado", "sequencia", ["nao", "abra"]] not in pistas


def test_sem_aspas_nao_adivinha_opera_como_alvo():
    texto = 'abre o Opera, não o Firefox'
    r = representar_regioes_texto(texto)
    assert r["regioes"] == [{"tipo": "exterior", "inicio": 0, "fim": len(texto), "texto": texto}]


def test_aspas_invalidas_preservam_tudo_como_exterior():
    r = representar_regioes_texto('não toque "Brisa')
    assert not r["aspas_coerentes"]
    assert {p["tipo"] for p in r["regioes"]} == {"exterior"}


def test_extrator_tem_forma_invariante_mas_conteudo_distinto_e_serializa(tmp_path):
    textos = ['toque "Não Volte"', 'toque "Brisa"', 'não toque "Brisa"']
    f = criar_extrator_regioes_texto()
    x = f.fit_transform(textos)
    canais = dict(f.transformer_list)
    forma = canais["forma"].transform(textos)
    assert (forma[0] != forma[1]).nnz == 0
    assert (x[0] != x[1]).nnz > 0
    assert (x[1] != x[2]).nnz > 0
    p = tmp_path / "extrator.joblib"
    joblib.dump(f, p)
    # Serialização compara transform com transform: fit_transform pode
    # diferir no arredondamento da normalização esparsa (~5e-17).
    np.testing.assert_array_equal(joblib.load(p).transform(textos).toarray(), f.transform(textos).toarray())


@pytest.mark.parametrize("texto", [None, "", "  "])
def test_entrada_invalida_aborta(texto):
    with pytest.raises(ValueError):
        representar_regioes_texto(texto)

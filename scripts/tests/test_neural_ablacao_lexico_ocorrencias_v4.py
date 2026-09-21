from copy import deepcopy

import numpy as np
import pytest
from scipy.sparse import csr_matrix, hstack

from mente_laylay.neural.ablar_lexico_ocorrencias_v4 import montar_matriz, controle_igual, resumir


def test_controle_repete_exatamente_a_concatenacao_anterior():
    lex = csr_matrix(np.array([[1, 2], [3, 4]], dtype=np.float32))
    ctx = np.ones((2, 384), dtype=np.float32)
    esperado = hstack((lex, csr_matrix(ctx)), format="csr")
    atual = montar_matriz(lex, ctx, "janela_contextual")
    assert atual.dtype == esperado.dtype
    assert (atual != esperado).nnz == 0


def test_condicao_sem_lexico_nem_consulta_o_bloco_removido():
    class NaoLer:
        def __getattribute__(self, nome):
            raise AssertionError("leitura indevida de léxico/posição")
    ctx = np.ones((2, 384), dtype=np.float32)
    r = montar_matriz(NaoLer(), ctx, "contexto_sem_lexico")
    assert r.shape == (2, 384)
    assert np.array_equal(r.toarray(), ctx)


@pytest.mark.parametrize("ctx", [np.zeros((2, 384)), np.ones((2, 383)),
                                 np.full((2, 384), np.nan), np.full((2, 384), np.inf)])
def test_contexto_invalido_aborta_sem_fallback(ctx):
    with pytest.raises(ValueError):
        montar_matriz(None, ctx, "contexto_sem_lexico")


def test_controle_nao_permite_linhas_desalinhadas():
    with pytest.raises(ValueError, match="alinhamento"):
        montar_matriz(csr_matrix((3, 2)), np.ones((2, 384)), "janela_contextual")


def test_mesma_media_com_erros_diferentes_nao_reproduz_controle():
    a = {"grupo": "f", "dobra": 0, "treino": {"erros": []},
         "teste": {"casos_exatos": 1, "erros": [{"id": "a"}]}}
    b = deepcopy(a); b["teste"]["erros"][0]["id"] = "b"
    assert controle_igual(a, a)
    assert not controle_igual(a, b)


def test_condicao_incompleta_nao_produz_resumo_verde():
    with pytest.raises(ValueError, match="incompleta"):
        resumir([])

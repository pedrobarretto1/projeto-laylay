"""Finalidade, autoria, revisão e publicação instaladas, com HTTP controlado."""
import pytest
from tests.test_finalidade_redacao_composta import CASOS
from tests.test_resultado_perifrastico_composicao import coletar, proposta


@pytest.mark.parametrize('pedido,fala', CASOS)
def test_redacao_composta_publica_proposta_nao_assertiva_sem_segunda_chamada(tmp_path,pedido,fala):
    d = coletar(tmp_path,{'entrada':pedido,'propostas':[proposta(fala)]})
    assert d['falas'] == [fala], d
    assert d['http'] == 1 and not d['orcamento']['chamadas_bloqueadas']


@pytest.mark.parametrize('fala', [
    'Eu diria: a sua decisão está correta porque você acredita nela.',
    'Eu diria: vamos conferir a conta porque você sempre erra.',
    'Eu diria: vamos conferir a conta. Consegui abrir o Opera.',
])
def test_redacao_instalada_nao_libera_afirmacao_ou_efeito_sem_fonte(tmp_path,fala):
    d = coletar(tmp_path,{'entrada':CASOS[0][0],'propostas':[proposta(fala)] * 2})
    assert len(d['falas']) == 1 and fala not in d['falas']
    assert not any('está correta porque' in f or 'você sempre erra' in f or 'Consegui abrir' in f
                   for f in d['falas'])
    assert d['http'] <= 2

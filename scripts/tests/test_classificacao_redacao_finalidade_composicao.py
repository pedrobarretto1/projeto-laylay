"""Composição instalada: interpretação, autoria e publicação sem efeitos."""
import pytest

from tests.test_resultado_perifrastico_composicao import coletar, proposta
from tests.test_redacao_conversacional import HISTORICA as REDACAO
from tests.test_adjunto_finalidade_pessoal import HISTORICA as FINALIDADE


@pytest.mark.parametrize('entrada,fala', [
    (FINALIDADE, 'Eu gostaria de manter a honestidade quando houver incerteza.'),
    ('Escreva uma resposta breve.', 'Uma resposta breve é esta.'),
    ('Para nos despedirmos, qual princípio você manteria?', 'Eu manteria a honestidade.'),
])
def test_pedido_discursivo_nao_cobra_receipt_de_acao(tmp_path, entrada, fala):
    d = coletar(tmp_path, {'entrada': entrada, 'propostas': [proposta(fala)]})
    assert d['falas'] == [fala], d
    assert d['http'] == 1
    assert not d['orcamento']['chamadas_bloqueadas']


def test_redacao_historica_supera_fronteira_operacional_mas_a_revisao_ainda_bloqueia(tmp_path):
    # ID histórico preservado. A antiga expectativa de bloqueio documentava
    # um RED posterior à classificação. O contrato de finalidade agora
    # confere esta proposta não assertiva sem dispensar apoio de afirmações.
    fala = 'Eu diria: vamos conferir a conta antes de decidir.'
    d = coletar(tmp_path, {'entrada': REDACAO, 'propostas': [proposta(fala)]})
    assert d['falas'] == [fala] and d['http'] == 1
    assert not d['orcamento']['chamadas_bloqueadas']

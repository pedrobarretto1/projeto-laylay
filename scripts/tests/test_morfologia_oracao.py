"""Índice lexical congelado, escopo raso e abstenção sem autoridade."""
import pytest
from mente_laylay.cognicao import morfologia_oracao as m


@pytest.mark.parametrize('palavra', ['aceita','trabalha','arrepende','sofreu','falha','continua','abre','move'])
def test_forma_indicativa_e_lida_do_lexico(palavra):
    assert m.consultar_morfologia(palavra)&256


@pytest.mark.parametrize('palavra', ['continue','abra','apague','repita','busque','toque','obrigada','tarde'])
def test_formal_participio_e_nome_nao_recebem_indicativo_por_sufixo(palavra):
    assert not m.consultar_morfologia(palavra)&256


@pytest.mark.parametrize('esquerda,direita,esperado', [
    ('A outra pessoa aceita as desculpas','continua sofrendo',True),
    ('Maria trabalha','liga a luz',True),
    ('Pedro se arrepende','envia a mensagem',True),
    ('Hoje ela trabalha','liga a luz',True),
    ('O editor falha','remove o arquivo',True),
    ('Uma boa ideia','abre o Firefox',False),
    ('Excelente ideia','abre o Firefox',False),
    ('Muito obrigada','abre o Firefox',False),
    ('Sem problema','abre o Firefox',False),
    ('A propósito disso','abre o Firefox',False),
    ('Estou triste','abre o Firefox',False),
])
def test_oracao_e_fragmento_nominal_tem_papeis_distintos(esquerda,direita,esperado):
    assert m.continuacao_predicativa_possivel(esquerda,direita) is esperado


def test_palavra_ausente_nao_inventa_flexao():
    assert m.consultar_morfologia('zzzxzzzinexistente') == 0


def test_dado_corrompido_nao_se_torna_evidencia_de_independencia(monkeypatch):
    monkeypatch.setattr(m,'DADOS_BASE85','invalido')
    m._indice.cache_clear();m.consultar_morfologia.cache_clear()
    try:
        assert m.continuacao_predicativa_possivel('A pessoa trabalha','liga a luz') is None
    finally:
        m._indice.cache_clear();m.consultar_morfologia.cache_clear()

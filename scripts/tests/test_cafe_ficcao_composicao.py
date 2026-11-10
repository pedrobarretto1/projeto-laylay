"""Referência nominal e ordem narrativa na composição da ponte."""
import pytest

from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.retrato_turno import extrair_entidade_explicita
from tests import test_autoria_operacao_composicao as autoria
from tests.test_biblioteca_retorno_composicao import PONTE_INSTALADA
from tests.test_papo_casual_composicao import proposta


TITULO = ('Perfeito, amarela! Vamos inventar um novo conto: uma criança encontra uma biblioteca '
          'flutuando sobre o mar, e cada livro guarda um pôr do sol diferente. '
          'Que título você daria a esse conto? É ficção, pode inventar livremente.')
FRASE = ('Como assistente, eu não vejo lugares nem tenho lembranças vividas, mas gosto dessa imagem como ficção. '
         'Na história, eu escolheria uma casinha com janela para um céu de estrelas. E você, Laylay: '
         'se um leitor abrisse o último livro dessa biblioteca, qual seria a última frase escrita nele?')


@pytest.mark.parametrize('texto', [
    TITULO,
    'Cada jogo revela um mapa diferente.',
    'Todo filme mostra uma cidade imaginária.',
    'Se um leitor abrisse o último livro dessa biblioteca, o que encontraria?',
])
def test_categoria_como_sujeito_ou_referencia_relacional_nao_cria_titulo(texto):
    assert not extrair_entidade_explicita(texto)


@pytest.mark.parametrize('texto,nome', [
    ('Estou falando do livro chamado Guarda um Pôr do Sol Diferente.', 'Guarda um Pôr do Sol Diferente'),
    ('Você conhece o livro «Dessa Biblioteca»?', 'Dessa Biblioteca'),
    ('Você conhece o livro Guarda Um Pôr Do Sol Diferente?', 'Guarda Um Pôr Do Sol Diferente'),
])
def test_categoria_preserva_nome_literal_ou_designacao(texto, nome):
    assert extrair_entidade_explicita(texto)['nome'] == nome


@pytest.mark.parametrize('texto', [
    FRASE,
    'Se a menina lesse o primeiro capítulo desse conto, qual seria a última frase escrita nele?',
    'Se o escritor abrisse a última página da história, qual seria a primeira linha nela?',
])
def test_ordinal_de_composicao_narrativa_nao_pede_fonte_recente(texto):
    assert not classificar_atualidade_factual(texto)['depende_atualidade']
    assert not classificar_atualidade_factual(texto, turno=classificar_modalidade_turno(texto))['depende_atualidade']


@pytest.mark.parametrize('texto', [
    'Qual é o último livro publicado pela editora?',
    'Se um leitor abrisse o último livro do catálogo da editora, qual seria a última frase escrita nele?',
    'Se eu abrisse o último livro da editora, qual seria a última frase escrita nele?',
    'Se eu abrisse o último livro dessa biblioteca, qual seria a última frase escrita nele?',
    'Se eu abrisse o último livro dessa biblioteca, qual seria a cotação do dólar agora?',
    'Se um leitor abrisse o último livro dessa biblioteca, qual seria a última frase escrita nele? Quem está online agora?',
    'Se eu abrisse o último livro dessa biblioteca, qual seria a última frase escrita nele hoje?',
    'Se eu abrisse o último livro dessa biblioteca, qual seria a última frase escrita nele ou quando foi publicado?',
])
def test_ordinal_nao_isenta_consulta_real_ou_composta(texto):
    assert classificar_atualidade_factual(texto)['depende_atualidade']
    assert classificar_atualidade_factual(texto, turno=classificar_modalidade_turno(texto))['depende_atualidade']


@pytest.mark.parametrize('entrada,fala', [
    (TITULO, 'Guarda Um Pôr Do Sol Diferente — porque cada livro guarda um pôr do sol que só existe '
             'quando alguém o abre, e só se lembra de como ele se via no céu.'),
    (FRASE, 'Na história, «A janela só se fecha depois que a última estrela encontra o mar.»'),
])
def test_ponte_publica_criacao_sem_promover_descricao_a_fonte(monkeypatch, entrada, fala):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    d = autoria.coletar_autoria({'entrada': entrada, 'historico': []}, [proposta(fala)])
    assert not d['plano']['atualidade']['depende_atualidade']
    assert not d['plano']['fundamentacao'].get('tema')
    assert not d['execucao_exigida'] and not d['operacional']
    assert d['falas'] == [fala] and len(d['publicacoes']) == d['http'] == 1
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']

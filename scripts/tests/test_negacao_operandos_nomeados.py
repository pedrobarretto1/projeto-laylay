"""Proibição conserva seu operando; nomes não concedem efeito ou alias."""
import pytest

from mente_laylay.cognicao.modalidade_turno import (
    classificar_modalidade_turno, autoriza_execucao_efetiva, fontes_textuais_dos_segmentos,
)
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno


@pytest.mark.parametrize('positivo,negativo', [
    ('toca a música "Água e Sol"', 'não toca a música "Noite e Lua"'),
    ('abre o aplicativo "Editor Azul"', 'não abre o aplicativo "Painel Verde"'),
    ('abre o arquivo "Relatorio.txt"', 'não abre o arquivo "Notas.txt"'),
    ('liga a tomada "Mesa"', 'não liga a tomada "Janela"'),
    ('toca a música "Água e Sol"', 'não abre a calculadora'),
    ('abre o arquivo "Relatorio.txt"', 'não toca a música "Noite e Lua"'),
])
@pytest.mark.parametrize('separador', ['; ', ', ', ' e '])
def test_proibicao_de_operando_distinto_nao_absorve_pedido_nomeado(positivo, negativo, separador):
    texto = positivo + separador + negativo
    turno = classificar_modalidade_turno(texto)
    assert len(turno['segmentos']) == 2
    permitido, vetado = turno['segmentos']
    assert autoriza_execucao_efetiva(permitido)
    assert not autoriza_execucao_efetiva(vetado) and vetado['veto_execucao_operacional']
    assert not resolver_revisao_intra_turno(texto)['detectada']
    fontes = fontes_textuais_dos_segmentos(texto, turno['segmentos'])
    assert [f.como_dict()['texto_original'] for f in fontes] == [positivo, negativo]


@pytest.mark.parametrize('negativo', [
    'não toca a música "ÁGUA E SOL"', 'não toca a música "agua e sol"',
    'não toca', 'não toca nada', 'não toca isso', 'não toca ela',
    'não toca essa música', 'não toca outra', 'não toca nenhuma música',
    'não toca a música', 'não toca a música "Sol"',
])
def test_mesmo_nome_referencia_ou_cancelamento_global_nao_libera_pedido(negativo):
    texto = 'toca a música "Água e Sol"; ' + negativo
    revisao = resolver_revisao_intra_turno(texto)
    assert revisao['detectada'] and (revisao['cancelada'] or not revisao['resolvida'])


@pytest.mark.parametrize('texto', [
    'toca a música "Água e Sol; não toca Noite e Lua"',
    'toca a música "Água e Sol; não abre a calculadora"',
])
def test_nome_literal_inteiro_nao_cria_proibicao_externa(texto):
    turno = classificar_modalidade_turno(texto)
    assert len(turno['segmentos']) == 1


@pytest.mark.parametrize('texto', [
    'quando eu confirmar, toca a música "Água e Sol"; não abre a calculadora',
    'escreve "toca Água e Sol; não abre a calculadora" na conversa',
])
def test_condicao_e_citacao_nao_viram_autorizacao_por_nome(texto):
    turno = classificar_modalidade_turno(texto)
    assert not any(autoriza_execucao_efetiva(s) for s in turno['segmentos'])


@pytest.mark.parametrize('fim', ['.', '!'])
@pytest.mark.parametrize('negativo', ['não toca a música "Noite e Lua"','não abre a calculadora'])
def test_pontuacao_terminal_externa_nao_passa_a_fazer_parte_do_nome(fim, negativo):
    texto = 'toca a música "Água e Sol"; ' + negativo + fim
    turno = classificar_modalidade_turno(texto)
    assert len(turno['segmentos']) == 2
    assert turno['segmentos'][0]['autoriza_execucao']
    assert turno['segmentos'][1]['veto_execucao_operacional']
    assert not resolver_revisao_intra_turno(texto)['detectada']

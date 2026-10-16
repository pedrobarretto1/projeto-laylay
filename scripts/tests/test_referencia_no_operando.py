"""Pronome como operando não vira nome literal por causa de um modificador."""
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.referencias_linguagem import operando_inicia_com_referencia_contextual
from mente_laylay.cognicao.gramatica_musical import analisar_gramatica_musical


@pytest.mark.parametrize("texto,depende", [
    ('por   favor coloca "Ela à Esquerda"', False),
    ('por\t favor toca a música “Ela Disse”', False),
    ("por   favor coloca ela à esquerda", True),
    ('põe "Ela à Esquerda"', False),
])
def test_normalizacao_da_moldura_nao_apaga_literalidade_do_operando(texto, depende):
    cand = analisar_gramatica_musical(texto)
    assert cand.classe == "pedido_direto"
    assert cand.depende_contexto is depende


@pytest.mark.parametrize("operando,esperado", [
    ("ela à esquerda", True), ("ele em foco", True), ("isso azul", True),
    ("essa janela à direita", True), ("elas novamente", True),
    ('"Ela à Esquerda"', False), ('música "Ela à Esquerda"', False),
    ('essa música "Ela à Esquerda"', False), ('faixa “Isso Azul”', False),
    ("Viva Ela", False), ("aplicativo Calculadora à esquerda", False), ("", False),
])
def test_leitor_compartilhado_distingue_nucleo_referencial_de_palavra_interna_em_nome(operando, esperado):
    assert operando_inicia_com_referencia_contextual(operando) is esperado


@pytest.mark.parametrize("texto", [
    "coloca ela à esquerda", "coloque ele à direita", "bota isso em foco",
    "coloca essa janela à esquerda", "toca ela novamente", "escuta essa de novo",
    "coloca isso em 40", "coloca ela azul",
])
def test_operando_referencial_com_modificador_continua_dependendo_de_contexto(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is True
    assert turno["depende_contexto"] is True
    assert turno["segmentos"][0]["depende_contexto"] is True


@pytest.mark.parametrize("primeiro,segundo", [
    ("abre a calculadora", "coloca ela à esquerda"),
    ("abre o aplicativo Notepad", "bota ele em foco"),
    ("liga a luz", "coloca ela azul"),
    ("toca a música Exemplo", "toca ela novamente"),
])
def test_primeiro_pedido_nao_materializa_alvo_do_segundo_na_classificacao(primeiro, segundo):
    turno = classificar_modalidade_turno(f"{primeiro} e {segundo}")
    assert len(turno["segmentos"]) == 2
    assert turno["segmentos"][0]["autoriza_execucao"] is True
    assert turno["segmentos"][1]["autoriza_execucao"] is True
    assert turno["segmentos"][1]["depende_contexto"] is True


@pytest.mark.parametrize("texto", [
    'coloca "Ela à Esquerda"', 'toca a música "Ela à Esquerda"',
    'coloca a faixa "Isso em 40"', 'toca "Essa Janela à Esquerda"',
    'toca a música Viva Ela', 'coloca o aplicativo Calculadora à esquerda',
    'coloca a playlist Ela Disse',
])
def test_palavra_referencial_no_nome_literal_ou_nominal_nao_e_alvo_pronominal(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is True
    assert turno["depende_contexto"] is False


@pytest.mark.parametrize("texto", [
    "não coloca ela à esquerda", "quando eu confirmar, coloca ela à esquerda",
    "ele disse coloca ela à esquerda", "como posso colocar ela à esquerda?",
    "coloca ela à esquerda significa o quê?",
])
def test_dependencia_nao_converte_mencao_condicao_ou_negacao_em_permissao(texto):
    assert classificar_modalidade_turno(texto)["autoriza_execucao"] is False

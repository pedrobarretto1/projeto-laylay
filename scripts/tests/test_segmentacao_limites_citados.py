"""Conteúdo citado não cria atos nem etapas; ordens externas continuam válidas."""
import pytest

from mente_laylay.autonomia.analise_comandos import segmentar_comandos_em_cadeia
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import (
    autoriza_execucao_efetiva,
    classificar_modalidade_turno,
)


@pytest.mark.parametrize("aspas", [('"', '"'), ("'", "'"), ("“", "”")])
@pytest.mark.parametrize("separador", ["e", "mas", "entao", "e depois", "em seguida", "depois", ",", ";"])
@pytest.mark.parametrize("ordem_externa", [False, True])
def test_literal_nao_cria_fronteira_operacional(aspas, separador, ordem_externa):
    abertura, fechamento = aspas
    literal = f"{abertura}abre a calculadora {separador} fecha o navegador{fechamento}"
    texto = f"Escreve {literal} no arquivo exemplo.txt"
    if ordem_externa:
        texto += " e pausa a música"
    turno = classificar_modalidade_turno(texto, texto_tem_comando_explicito=texto_tem_comando_explicito)
    assert autoriza_execucao_efetiva(turno) is True
    # Primeira asserção causal: a modalidade ainda não fragmentou o argumento.
    segmentos = [s["texto"] for s in turno["segmentos"]]
    assert len(segmentos) == (2 if ordem_externa else 1), segmentos
    assert literal in segmentos[0]
    # Segunda fronteira: cadeia não redescobre ordens dentro do argumento.
    etapas = segmentar_comandos_em_cadeia(texto)
    assert len(etapas) == (2 if ordem_externa else 1), etapas
    assert literal in etapas[0]
    if ordem_externa:
        assert etapas[1] == "pausa a música"


@pytest.mark.parametrize("texto,literal", [
    ('Cria uma playlist chamada "pausa a música e fecha o navegador"', '"pausa a música e fecha o navegador"'),
    ('Abre o arquivo "teste, fecha o navegador.txt" e pausa a música', '"teste, fecha o navegador.txt"'),
    ('Escreve "abre a calculadora e apaga o arquivo notas.txt" no arquivo exemplo.txt', '"abre a calculadora e apaga o arquivo notas.txt"'),
])
def test_mecanismo_preserva_argumentos_em_dominios_distintos(texto, literal):
    turno = classificar_modalidade_turno(texto)
    assert any(literal in s["texto"] for s in turno["segmentos"])
    assert any(literal in s for s in segmentar_comandos_em_cadeia(texto))


@pytest.mark.parametrize("texto", [
    'Escreve "abre a calculadora e fecha o navegador no arquivo exemplo.txt',
    'Abre o arquivo ”teste.txt“ e fecha o navegador',
    'Escreve "teste\' e fecha o navegador',
])
def test_aspas_malformadas_nao_podem_originar_cadeia_parcial(texto):
    turno = classificar_modalidade_turno(texto)
    assert autoriza_execucao_efetiva(turno) is False
    assert turno["veto_execucao_operacional"] is True
    assert len(segmentar_comandos_em_cadeia(texto)) == 1


def test_ordens_sem_citacao_continuam_segmentadas():
    texto = "Abre a calculadora e fecha o navegador, depois pausa a música"
    assert segmentar_comandos_em_cadeia(texto) == ["Abre a calculadora", "fecha o navegador", "pausa a música"]


def test_conjuncao_dentro_de_enumeracao_nao_cria_nova_ordem():
    assert len(segmentar_comandos_em_cadeia("Liga a luz e o ventilador")) == 1

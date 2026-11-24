"""Diretivas sobre a resposta não concedem autoridade operacional."""
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno


@pytest.mark.parametrize("texto", [
    "Você acha que mudar de opinião é aprendizado? Responda com um exemplo simples da vida cotidiana, sem executar ações externas.",
    "Responda de forma breve, sem realizar operações externas.",
    "Quero verificar nossa memória imediata: quais foram os três objetos que eu mencionei na caixa? Repita-os exatamente, sem acrescentar nenhum.",
    "Quais foram os dois itens que mencionei na lista? Reproduza-os literalmente.",
])
def test_limite_negativo_de_execucao_preserva_autoria(texto):
    turno = classificar_modalidade_turno(texto)
    assert not turno["autoriza_execucao"]
    assert not turno["texto_operacional"]


@pytest.mark.parametrize("texto", [
    "Responda ao e-mail do João com um exemplo simples, sem executar ações externas.",
    "Responda com um exemplo simples. Depois abra a Calculadora.",
    "Abra a Calculadora.",
    "Quais foram os três objetos que eu mencionei na caixa? Repita a operação de apagar o arquivo.",
    "Repita-os exatamente, sem acrescentar nenhum.",
])
def test_limite_discursivo_nao_absorve_um_destino_operacional(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"]
    assert turno["texto_operacional"]

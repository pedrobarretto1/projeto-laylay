"""Pedir o procedimento não autoriza executar a ação mencionada."""
import pytest

from mente_laylay.cognicao.modalidade_turno import (
    analisar_protecao_operacional,
    classificar_modalidade_turno,
)


@pytest.mark.parametrize("acao", [
    "aumentar o volume", "diminuir o brilho", "silenciar o áudio",
    "exportar minhas notas", "sincronizar o calendário", "pausar a música",
])
@pytest.mark.parametrize("moldura", [
    "como eu poderia {}?", "como eu posso {}", "como faço para {}?",
    "me ensina como {}", "explique como {}", "como {}?",
])
def test_procedimento_nao_depende_do_vocabulario_de_execucao(acao, moldura):
    texto = moldura.format(acao)
    protecao = analisar_protecao_operacional(texto)
    assert protecao["natureza_acao"] == "instrucao_ou_explicacao"
    assert protecao["bloqueia_execucao"] is True
    turno = classificar_modalidade_turno(texto)
    assert turno["natureza_acao"] == "instrucao_ou_explicacao"
    assert turno["modalidade_geral"] == "pergunta"
    assert turno["autoriza_execucao"] is False
    assert not turno["texto_operacional"]


@pytest.mark.parametrize("texto", [
    "como está o volume?", "como ficou o brilho?", "o volume aumentou?",
    "como você aumentou o volume?", "me explica como está o volume",
    "eu poderia aumentar o volume?", "talvez eu possa aumentar o volume",
    "se eu quisesse aumentar o volume?", "não aumente o volume",
    'traduza "como eu poderia aumentar o volume?"',
    'a frase "como eu poderia aumentar o volume?" é uma pergunta?',
    "aumentar o volume pode prejudicar a audição?",
])
def test_mencionar_acao_nao_basta_para_pedir_procedimento(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno["natureza_acao"] != "instrucao_ou_explicacao"
    assert turno["autoriza_execucao"] is False


@pytest.mark.parametrize("texto", ["pode pausar a música", "pode pausar a música?", "abra a calculadora"])
def test_pedido_direto_nao_vira_aula(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is True
    assert turno["natureza_acao"] != "instrucao_ou_explicacao"

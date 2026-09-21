"""Contrato do turno não pode consumir o orçamento reservado ao diálogo."""
from mente_laylay.integracao.preparacao_llm import _selecionar_historico_com_orcamento


def test_contrato_grande_preserva_troca_recente_e_referente_do_pedido():
    mensagens = [
        {"role": "user", "content": "Vamos conversar sobre módulos DC-DC para meu projeto."},
        {"role": "assistant", "content": "Qual a tensão e a corrente necessárias?"},
        {"role": "system", "content": "Contrato efêmero. " * 300},
        {"role": "user", "content": "pode me recomendar um modelo que seja bom e barato"},
    ]
    resultado = _selecionar_historico_com_orcamento(mensagens, limite_chars=1200, limite_mensagens=4)
    assert resultado == mensagens


def test_orcamento_ainda_limita_historico_e_nao_reintroduz_system_antigo():
    mensagens = [
        {"role": "system", "content": "instrução antiga"},
        {"role": "user", "content": "antigo" * 300},
        {"role": "assistant", "content": "resposta recente"},
        {"role": "system", "content": "contrato atual" * 300},
        {"role": "user", "content": "continue"},
    ]
    resultado = _selecionar_historico_com_orcamento(mensagens, limite_chars=100, limite_mensagens=4)
    assert resultado == mensagens[-3:]

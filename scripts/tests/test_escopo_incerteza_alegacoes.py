"""Negação de uma leitura não é confirmação de estado nem libera outra oração."""

import pytest

from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala


@pytest.mark.parametrize("fala", [
    "Não sei se a lâmpada está ligada.",
    "Não, eu não posso saber se a lâmpada está ligada.",
    "Não consegui confirmar se o ventilador está desligado.",
    "Não verifiquei se a temperatura está alta.",
    "Me diga se a luz está ligada.",
])
def test_estado_forte_sob_incerteza_local_nao_e_afirmacao(fala):
    resultado = validar_alegacoes_da_fala(fala, plano={"texto_usuario": "Esse relato informa se a lâmpada está ligada neste momento?", "comandos": []})
    assert resultado["problemas"] == []
    assert resultado["fala"] == fala


@pytest.mark.parametrize("fala", [
    "A lâmpada está ligada.",
    "Não sei se a lâmpada está ligada, mas o ventilador está desligado.",
    "Não verifiquei a lâmpada; a temperatura está alta.",
    "Não sei francês e a luz está ligada.",
    "Não posso saber se a lâmpada está ligada, mas o ventilador está desligado.",
])
def test_estado_forte_independente_continua_exigindo_receipt(fala):
    resultado = validar_alegacoes_da_fala(fala, plano={"comandos": []})
    assert "estado_real_sem_leitura" in resultado["problemas"]


@pytest.mark.parametrize("pergunta,fala", [
    ("Você conseguiu verificar qual documento está aberto?",
     "Não, não consegui verificar qual documento está aberto."),
    ("A janela está aberta?", "Ainda não consegui observar se a janela está aberta."),
    ("O processo está rodando?", "Não consegui confirmar se o processo está rodando."),
    ("O aplicativo está fechado?", "Não verifiquei se o aplicativo está fechado."),
])
def test_relato_de_leitura_nao_confirmada_preserva_a_fala(pergunta, fala):
    resultado = validar_alegacoes_da_fala(fala, plano={"texto_usuario": pergunta, "comandos": []})
    assert resultado["problemas"] == []
    assert resultado["fala"] == fala


@pytest.mark.parametrize("fala", [
    "Não sei se o documento está aberto, mas a janela está aberta.",
    "Não verifiquei o documento; o aplicativo está fechado.",
    "Não consigo consultar o documento, porém a janela está aberta.",
    "Não sei francês e o documento está aberto.",
    "Não consegui verificar qual documento está aberto. A janela está aberta.",
    "O documento não está aberto.",
    "O documento está aberto, não consegui verificar.",
])
def test_incerteza_nao_libera_afirmacao_independente_sem_receipt(fala):
    resultado = validar_alegacoes_da_fala(
        fala, plano={"texto_usuario": "O documento está aberto?", "comandos": []},
    )
    assert "estado_atual_sem_evidencia" in resultado["problemas"]
    assert resultado["fala"] != fala


@pytest.mark.parametrize("fala", [
    "Se você puder me dizer qual arquivo ou pasta está aberto, posso ajudar a verificar.",
    "Me diga se a janela está aberta.",
    "Pode me informar qual processo está rodando.",
])
def test_pedido_de_informacao_nao_afirma_estado(fala):
    resultado = validar_alegacoes_da_fala(fala, plano={"texto_usuario": "O documento está aberto?", "comandos": []})
    assert resultado["problemas"] == []
    assert resultado["fala"] == fala


@pytest.mark.parametrize("fala", [
    "Me diga se a janela está aberta, mas o documento está fechado.",
    "Posso informar que o documento está aberto.",
    "Eu te digo que o documento está aberto.",
    "O documento está aberto; me diga o nome.",
])
def test_pedido_de_informacao_nao_libera_afirmacoes_externas(fala):
    resultado = validar_alegacoes_da_fala(fala, plano={"texto_usuario": "O documento está aberto?", "comandos": []})
    assert "estado_atual_sem_evidencia" in resultado["problemas"]

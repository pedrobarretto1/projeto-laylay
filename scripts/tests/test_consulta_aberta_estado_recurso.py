"""Perguntar qual é o estado não fornece o estado que falta observar."""
from copy import deepcopy
import pytest

from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno


@pytest.mark.parametrize("texto", [
    "e como estao as coisas no computador?", "como está o computador?", "como tá meu pc?",
    "como estão os programas?", "como anda a lâmpada do quarto?", "como está o arquivo?",
    "como está a pasta?", "como está a playlist?", "como estão os motores?",
    "qual é o estado do dispositivo?", "como está a bateria?", "e como está o sensor?",
])
def test_consulta_aberta_exige_estado_atual_sem_conceder_acao(texto):
    turno = classificar_modalidade_turno(texto)
    antes = deepcopy(turno)
    a = classificar_atualidade_factual(texto, turno=turno)
    assert a["classe"] == "estado_observavel", "primeira fronteira: pergunta atual foi tratada como fato estável"
    assert a["depende_atualidade"] is True
    assert turno == antes
    # O owner já admite certas leituras locais como consultas executáveis.
    # Classificar a necessidade de evidência não cria nem revoga essa permissão.
    if turno["autoriza_execucao"] is True:
        assert turno["natureza_acao"] == "consulta"
    plano = {"id": turno["id"], "texto_usuario": texto, "comandos": [],
             "requer_execucao": False, "atualidade_factual": a}
    c = construir_contrato_semantico_fala(texto, turno=turno, plano=plano)
    assert c["roteiro_concreto"]["estrategia"] == "estado_observavel_sem_evidencia"
    assert c["autoriza_execucao"] is False


@pytest.mark.parametrize("texto", [
    "como você está?", "como está você?", "como está o Pedro?", "como está minha mãe?",
    '"como está o computador?"', 'A frase "como está o computador?" está correta?',
    "como funciona o computador?", "liga a lâmpada", "o computador está bem",
    "o que você está fazendo?", "como assim?",
    "Como está o sistema solar organizado?", "Como está o corpo humano dividido?",
    "Qual é o estado da música brasileira no século XIX?",
    "Como está o computador definido na teoria?",
])
def test_outro_ato_nao_vira_consulta_aberta_de_recurso(texto):
    a = classificar_atualidade_factual(texto)
    assert a["classe"] != "estado_observavel"

from __future__ import annotations

# P0_AUTORIZACAO_ATO_FALA_V2_20260815

import pytest

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import (
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)


def _classificar(texto: str) -> dict:
    return classificar_modalidade_turno(
        texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )


def _barreira(texto: str) -> bool:
    return bloqueia_execucao_operacional_prioritaria(
        texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )


@pytest.mark.parametrize(
    "texto",
    [
        "Eu poderia abrir o Opera agora?",
        "Se eu quisesse fechar o Opera, como faria?",
        "Pausar música economiza internet?",
        "Só me explica como pesquisar no navegador, não pesquise nada.",
        "eu poderia fechar o Opera agora",
        "se eu quisesse abrir o Opera agora",
        "Você acha que devo fechar o Opera?",
        "pesquisa Python, mas não abra nenhum resultado",
    ],
)
def test_fala_sobre_acao_nao_concede_autorizacao(texto: str) -> None:
    turno = _classificar(texto)
    assert turno["autoriza_execucao"] is False
    assert turno["texto_operacional"] == ""
    assert turno["modalidade_geral"] != "comando"
    assert _barreira(texto) is True


def test_variantes_reais_recebem_natureza_semantica_nao_operacional() -> None:
    hipotese = _classificar("Eu poderia abrir o Opera agora?")
    informativa = _classificar("Pausar música economiza internet?")
    instrucao = _classificar(
        "Só me explica como pesquisar no navegador, não pesquise nada."
    )
    assert hipotese["natureza_acao"] == "hipotetica"
    assert informativa["natureza_acao"] == "informativa_sobre_acao"
    assert instrucao["natureza_acao"] == "instrucao_ou_explicacao"


@pytest.mark.parametrize(
    "texto",
    [
        "abre o Opera",
        "abre o Opera?",
        "poderia abrir o Opera?",
        "você poderia abrir o Opera para mim?",
        "pausa a música",
        "pesquisa documentação do Python",
    ],
)
def test_pedidos_reais_continuam_autorizados(texto: str) -> None:
    turno = _classificar(texto)
    assert turno["autoriza_execucao"] is True
    assert turno["modalidade_geral"] in {"comando", "misto"}
    assert turno["texto_operacional"]
    assert _barreira(texto) is False


def test_pergunta_de_capacidade_com_sujeito_continua_bloqueada() -> None:
    texto = "você poderia abrir o Opera?"
    turno = _classificar(texto)
    assert turno["autoriza_execucao"] is False
    assert turno["modalidade_geral"] == "pergunta"
    assert _barreira(texto) is True


@pytest.mark.parametrize(
    "texto",
    [
        "qual o estado da lâmpada?",
        "quais programas estão abertos?",
        "quais são os meus emails?",
    ],
)
def test_consultas_read_only_legitimas_nao_sao_bloqueadas(texto: str) -> None:
    turno = _classificar(texto)
    assert turno["autoriza_execucao"] is True
    assert _barreira(texto) is False

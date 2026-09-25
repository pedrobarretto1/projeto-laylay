from __future__ import annotations

# P0_AUTORIZACAO_ATO_FALA_V2_20260815

import pytest

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.autonomia.pre_fluxo_contextual import (
    processar_execucao_pratica_precoce,
)
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


@pytest.mark.parametrize(
    "texto",
    [
        "não é para abrir o aplicativo pelvora",
        "não é para ler o arquivo pelvora.txt",
        "não é para ligar a tomada pelvora",
    ],
)
def test_recusa_declarativa_nao_e_para_bloqueia_so_o_ato_negado(texto: str) -> None:
    turno = _classificar(texto)

    assert turno["modalidade_geral"] == "recusa"
    assert turno["autoriza_execucao"] is False
    assert turno["veto_execucao_operacional"] is True
    assert turno["texto_operacional"] == ""
    assert turno["segmentos"][0]["modalidade"] == "recusa"
    assert turno["segmentos"][0]["veto_execucao_operacional"] is True
    assert _barreira(texto) is True


def test_recusa_declarativa_em_turno_misto_preserva_pedido_independente() -> None:
    texto = (
        "não é para abrir o aplicativo pelvora; "
        "preciso que você abra o aplicativo zafrin"
    )
    turno = _classificar(texto)

    assert turno["modalidade_geral"] == "misto"
    assert turno["atos"] == ["recusa", "comando"]
    assert turno["segmentos"][0]["veto_execucao_operacional"] is True
    assert turno["segmentos"][0]["autoriza_execucao"] is False
    assert turno["segmentos"][1]["autoriza_execucao"] is True
    assert turno["autoriza_execucao"] is True
    assert turno["veto_execucao_operacional"] is False
    assert turno["texto_operacional"] == "preciso que você abra o aplicativo zafrin"
    assert _barreira(texto) is False


def test_nao_e_para_em_pergunta_nao_vira_recusa_operacional() -> None:
    turno = _classificar("não é para abrir o aplicativo pelvora?")

    assert turno["modalidade_geral"] == "pergunta"
    assert turno["autoriza_execucao"] is False
    assert turno["texto_operacional"] == ""
    assert _barreira("não é para abrir o aplicativo pelvora?") is True


def test_consumidor_pratico_recebe_so_pedido_do_turno_misto() -> None:
    texto = (
        "não é para abrir o aplicativo pelvora; "
        "preciso que você abra o aplicativo zafrin"
    )
    turno = _classificar(texto)
    chamadas = []

    def processar(deteccao, origem, original):
        chamadas.append((deteccao, origem, original))
        return True

    ok, etapa = processar_execucao_pratica_precoce(
        {
            "mente_integrada_estado": {"turno_atual": turno},
            "processar_comando_deterministico": processar,
        },
        texto,
    )

    assert ok is True
    assert etapa == "comando_deterministico_pre_ia"
    assert chamadas == [(
        "preciso que você abra o aplicativo zafrin",
        "pre-ia",
        texto,
    )]

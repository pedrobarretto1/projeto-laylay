# P0_REVISAO_INTRA_TURNO_V1_1_20260816
from __future__ import annotations

import inspect

import pytest

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno


@pytest.mark.parametrize(
    ("texto", "efetivo", "tipo"),
    [
        (
            "Pausa a música... esquece, continua tocando.",
            "continua música",
            "substituicao_acao",
        ),
        (
            "Cria um arquivo chamado erro.txt... não, chama correcao.txt.",
            "Cria um arquivo chamado correcao.txt",
            "substituicao_parametro",
        ),
        (
            "Abre Wikipédia... não, melhor Prime Video.",
            "Abre Prime Video",
            "substituicao_alvo",
        ),
        (
            "Fecha a Calculadora... quer dizer, maximiza ela.",
            "maximiza Calculadora",
            "substituicao_acao",
        ),
    ],
)
def test_revisao_intra_turno_produz_uma_unica_fala_operacional(
    texto: str, efetivo: str, tipo: str,
) -> None:
    revisao = resolver_revisao_intra_turno(texto)
    assert revisao["detectada"] is True
    assert revisao["resolvida"] is True
    assert revisao["cancelada"] is False
    assert revisao["tipo"] == tipo
    assert revisao["texto_operacional_efetivo"] == efetivo

    turno_final = classificar_modalidade_turno(
        efetivo,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    assert turno_final["autoriza_execucao"] is True
    assert turno_final["texto_operacional"]


def test_continuacao_eliptica_herda_alvo_da_proposta_descartada() -> None:
    revisao = resolver_revisao_intra_turno(
        "Pausa a música... esquece, continua tocando."
    )
    assert revisao["alvo_herdado"] == "música"
    assert revisao["texto_operacional_efetivo"] == "continua música"


def test_negacao_corretiva_cancela_mutacao_em_vez_de_repetir() -> None:
    revisao = resolver_revisao_intra_turno(
        "Apaga o arquivo segredo.txt... não apaga."
    )
    assert revisao["detectada"] is True
    assert revisao["resolvida"] is True
    assert revisao["cancelada"] is True
    assert revisao["texto_operacional_efetivo"] == ""


@pytest.mark.parametrize(
    "texto",
    [
        "Abre o Opera e depois abre a Calculadora.",
        "Pausa a música e depois continua.",
        'Pesquisa por "não apaga".',
        "Abre o melhor resultado.",
        "Cria um arquivo chamado não.txt.",
    ],
)
def test_falas_sem_revisao_preservam_fluxo_existente(texto: str) -> None:
    revisao = resolver_revisao_intra_turno(texto)
    assert revisao["detectada"] is False
    assert revisao["resolvida"] is False
    assert revisao["texto_operacional_efetivo"] == ""


def test_revisao_ambigua_fica_fail_closed() -> None:
    revisao = resolver_revisao_intra_turno(
        "Cria um arquivo chamado teste.txt... na verdade alguma outra coisa."
    )
    assert revisao["detectada"] is True
    assert revisao["resolvida"] is False
    assert revisao["tipo"] == "ambigua"
    assert revisao["texto_operacional_efetivo"] == ""


def test_referencia_da_correcao_herda_alvo_da_proposta_descartada() -> None:
    revisao = resolver_revisao_intra_turno(
        "Fecha a Calculadora... quer dizer, maximiza ela."
    )
    assert revisao["alvo_herdado"] == "Calculadora"
    assert revisao["texto_operacional_efetivo"] == "maximiza Calculadora"
    assert "fecha" not in revisao["texto_operacional_efetivo"].casefold()


def test_revisao_esta_ligada_antes_dos_roteadores_operacionais() -> None:
    from mente_laylay.cognicao import orquestrador_turno_runtime
    from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
    from mente_laylay.autonomia import coordenador_intencao

    fonte_turno = inspect.getsource(
        orquestrador_turno_runtime._iniciar_planejamento_turno
    )
    assert "resolver_revisao_intra_turno(texto)" in fonte_turno
    assert "texto_cognitivo" in fonte_turno
    assert "revisão interna detectada sem resolução operacional segura" in fonte_turno

    fonte_prioridade = inspect.getsource(
        ComandosImediatosRuntime.processar_prioritarios
    )
    assert "texto_operacional_efetivo" in fonte_prioridade
    assert "[REVISÃO:PRIORIDADE]" in fonte_prioridade

    fonte_coordenador = inspect.getsource(coordenador_intencao.resolver_intencao)
    assert "revisao_resolvida" in fonte_coordenador
    assert "texto_operacional_efetivo" in fonte_coordenador

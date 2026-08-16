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
            "continua a música",
            "substituicao_acao",
        ),
        (
            "Liga a lâmpada... não, deixa desligada.",
            "desliga lâmpada",
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
    assert revisao["texto_operacional_efetivo"] == "continua a música"


def test_saida_musical_revisada_e_consumivel_pelo_roteador() -> None:
    from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia

    revisao = resolver_revisao_intra_turno(
        "Pausa a música... esquece, continua tocando."
    )
    intent = detectar_volume_ou_midia(
        revisao["texto_operacional_efetivo"].casefold(),
        params_cb=lambda **kwargs: kwargs,
    )
    assert intent == {"intent": "MEDIA_CONTROL", "params": {"acao": "play"}}


def test_negacao_com_nada_revoga_mesma_operacao() -> None:
    revisao = resolver_revisao_intra_turno(
        "Pesquisa Python... pera, não pesquisa nada."
    )
    assert revisao["detectada"] is True
    assert revisao["resolvida"] is True
    assert revisao["cancelada"] is True
    assert revisao["tipo"] == "cancelamento"
    assert revisao["texto_operacional_efetivo"] == ""


def test_estado_final_iot_herda_alvo_sem_contaminar_o_alvo() -> None:
    revisao = resolver_revisao_intra_turno(
        "Liga a lâmpada... não, deixa desligada."
    )
    assert revisao["detectada"] is True
    assert revisao["resolvida"] is True
    assert revisao["cancelada"] is False
    assert revisao["tipo"] == "substituicao_acao"
    assert revisao["alvo_herdado"] == "lâmpada"
    assert revisao["texto_operacional_efetivo"] == "desliga lâmpada"
    assert "deixa" not in revisao["texto_operacional_efetivo"].casefold()


def test_fallback_ia_recebe_texto_operacional_revisado() -> None:
    from mente_laylay.autonomia.coordenador_intencao import resolver_intencao

    original = "Pausa a música... esquece, continua tocando."
    revisao = resolver_revisao_intra_turno(original)
    recebido: dict[str, str] = {}

    def tentar_ia(texto: str):
        recebido["texto"] = texto
        return None

    ctx = {
        "normalizar_texto": lambda texto: str(texto or "").casefold().strip(),
        "refinar_contexto_mental": lambda _texto: None,
        "turno_atual": {
            "modalidade": "comando",
            "modalidade_geral": "comando",
            "autoriza_execucao": True,
            "revisao_intra_turno": revisao,
            "texto_operacional_efetivo": revisao["texto_operacional_efetivo"],
        },
        "retrato_turno_atual": {},
        "extrair_agendamento": lambda _texto: None,
        "extrair_acao_agendada": lambda _texto: None,
        "texto_cancela_acao_agora": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: False,
        "detectar_intencao_deterministica": lambda _texto: None,
        "resolver_comando_contextual_forcado": lambda _texto: None,
        "resolver_repeticao_ultima_acao": lambda _texto: None,
        "tentar_intencao_ai_primeiro": tentar_ia,
        "registrar_arbitragem_turno": lambda *_args: None,
    }

    assert resolver_intencao(original, "terminal", ctx) == (None, "")
    assert recebido["texto"] == revisao["texto_operacional_efetivo"]
    assert recebido["texto"] != original


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

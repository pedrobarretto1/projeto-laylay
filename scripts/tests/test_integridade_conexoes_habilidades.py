from __future__ import annotations

import importlib

import pytest

from mente_laylay.autonomia.classificacao_habilidade import HABILIDADE_POR_INTENT
from mente_laylay.autonomia.comandos_imediatos import texto_pede_resumo_pagina
from mente_laylay.autonomia.coordenador_intencao import INTENTS_EXECUTAVEIS
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.interpretacao_intencao import PROMPT_INTERPRETACAO
from mente_laylay.especialistas.capacidades import (
    INTENTS_SOMENTE_LEITURA,
    consultar_capacidade,
    intents_registradas,
)
from mente_laylay.memoria_mental.continuidade_geral import (
    INTENTS_CONTINUIDADE_INTERNAS,
    intents_continuidade_registradas,
)
from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao


def test_catalogo_cobre_classificacao_continuidade_e_leituras() -> None:
    catalogadas = intents_registradas()
    continuidade = intents_continuidade_registradas()

    assert catalogadas <= frozenset(HABILIDADE_POR_INTENT)
    assert catalogadas <= continuidade
    assert INTENTS_SOMENTE_LEITURA <= catalogadas
    assert continuidade - catalogadas == INTENTS_CONTINUIDADE_INTERNAS
    assert frozenset(INTENTS_EXECUTAVEIS) == catalogadas


def test_intents_expostas_a_llm_pertencem_ao_catalogo_vivo() -> None:
    bloco = PROMPT_INTERPRETACAO.split("intent: (", 1)[1].split(")\nparams:", 1)[0]
    expostas = {item.strip() for item in bloco.split(",") if item.strip()}

    assert expostas <= intents_registradas()


def test_resumo_de_pagina_e_capacidade_oficial_confirmavel() -> None:
    capacidade = consultar_capacidade("RESUMIR_PAGINA")

    assert capacidade["disponivel"] is True
    assert capacidade["dominio"] == "navegador"
    assert capacidade["confirmacao_oferecida"] == "retorno_dados"
    assert capacidade["exige_confirmacao"] is False

    resultado = normalizar_resultado_acao({
        "intent": "RESUMIR_PAGINA",
        "status": "resumo_concluido",
        "executou": True,
    })
    assert resultado.confirmado is True


def test_toda_capacidade_expoe_os_metadados_dos_nove_pilares() -> None:
    for intent in intents_registradas():
        capacidade = consultar_capacidade(intent)

        assert capacidade["invocacao_natural"], intent
        assert capacidade["autorizacao"] in {
            "pedido_atual_autorizado",
            "confirmacao_explicita",
        }, intent
        assert capacidade["proprietario"], intent
        importlib.import_module(capacidade["proprietario"])
        assert capacidade["dependencias"], intent
        assert capacidade["limites"], intent
        assert capacidade["evidencia_confirmacao"], intent


@pytest.mark.parametrize(
    "texto",
    (
        "Resume a página atual",
        "Pode resumir esta página para mim?",
        "Explica o conteúdo da aba atual",
    ),
)
def test_resumo_aceita_apenas_pedidos_que_autorizam_execucao(texto: str) -> None:
    turno = classificar_modalidade_turno(texto)

    assert turno["autoriza_execucao"] is True
    assert texto_pede_resumo_pagina(texto) is True


@pytest.mark.parametrize(
    "texto",
    (
        "Não resume a página atual",
        "Como eu faria para resumir uma página?",
        "Talvez fosse legal resumir esta página",
        "Você consegue resumir páginas?",
    ),
)
def test_resumo_nao_executa_negacao_instrucao_hipotese_ou_capacidade(
    texto: str,
) -> None:
    turno = classificar_modalidade_turno(texto)

    assert turno["autoriza_execucao"] is False
    assert texto_pede_resumo_pagina(texto) is False


@pytest.mark.parametrize(
    "texto",
    (
        "Não resume a página atual",
        "Como eu faria para resumir uma página?",
        "Talvez fosse legal resumir esta página",
        "Você consegue resumir páginas?",
    ),
)
def test_composicao_prioritaria_nao_executa_falsos_pedidos_de_resumo(
    texto: str,
) -> None:
    from types import SimpleNamespace

    from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime

    chamadas: list[str] = []
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": SimpleNamespace(mental={}),
            "resumir_pagina_ou_video": lambda: chamadas.append("resumo"),
            "_registrar_resultado_execucao": lambda *_args, **_kwargs: chamadas.append(
                "resultado"
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(texto) is False
    assert chamadas == []

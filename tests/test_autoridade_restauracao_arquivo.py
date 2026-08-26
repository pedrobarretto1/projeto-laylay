"""Contrato de autoridade para restauração contextual de arquivos.

Esta regressão protege uma separação arquitetural importante:

- a fala atual fornece AUTORIDADE para restaurar;
- o recibo canônico de exclusão fornece o ALVO restaurável;
- o detector de arquivos não cria autorização;
- contexto sem pedido atual não executa nada;
- pedido atual sem recibo válido não inventa alvo.

O teste é deliberadamente nomeado pela raiz arquitetural, não pelo número de
um turno do chaos.
"""

from __future__ import annotations

from typing import Any

import pytest

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)


CAMINHO_DESCARTADO = r"C:\Users\teste\Downloads\caos seguro.txt"


def _classificar(texto: str) -> dict[str, Any]:
    return classificar_modalidade_turno(
        texto,
        normalizar_texto=normalizar_texto_basico,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )


def _registrar_exclusao_confirmada(
    *,
    alvo: str = CAMINHO_DESCARTADO,
) -> dict[str, Any]:
    """Cria o recibo pela API canônica, sem montar ultima_acao_* à mão."""
    estado = estado_mental_inicial()
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "CONFIRM_DELETE_ITEM",
            "params": {"alvo": alvo},
            "alvo": alvo,
            "status": "movido_para_lixeira",
            "executou": True,
            "confirmado": True,
            "origem": "executor",
            "confirmacao_oferecida": "persistencia_local",
            "evidencia_confirmacao": (
                "a lixeira retorna o resultado da movimentação"
            ),
        },
        "sim",
        True,
        origem="executor",
        status="movido_para_lixeira",
    )


def _detectar_arquivo(
    texto: str,
    estado: dict[str, Any],
) -> dict[str, Any] | None:
    return detectar_intencao_arquivos(
        texto,
        params_cb=lambda **kwargs: kwargs,
        estado_mental=estado,
        normalizar_texto=normalizar_texto_basico,
    )


@pytest.mark.parametrize(
    "fala",
    [
        "Quero ele de volta.",
        "Quero o arquivo de volta.",
        "Traz ele de volta.",
    ],
)
def test_gramaticas_de_restauracao_concordam_sobre_intencao_e_autoridade(
    fala: str,
) -> None:
    """Se Arquivos entende restauração, o turno atual precisa fornecer autoridade."""
    estado = _registrar_exclusao_confirmada()

    candidato = _detectar_arquivo(fala, estado)
    assert candidato is not None
    assert candidato["intent"] == "RESTORE_DELETED_ITEM"
    assert candidato["params"]["alvo"] == CAMINHO_DESCARTADO
    assert candidato["params"]["referencia_exclusao_confirmada"] is True

    turno = _classificar(fala)

    # PRIMEIRA FRONTEIRA RED ESPERADA ANTES DO CANDIDATO:
    # hoje "Quero ele de volta." cai como conversa/sem autoridade, apesar de o
    # roteador de arquivos reconhecer a mesma fala como RESTORE_DELETED_ITEM.
    assert turno["modalidade_geral"] in {"comando", "misto"}
    assert turno["autoriza_execucao"] is True
    assert str(turno.get("texto_operacional") or "").strip()


def test_forma_verbal_ja_suportada_permanece_como_baseline_verde() -> None:
    """A correção nova não deve quebrar a forma imperativa já reconhecida."""
    fala = "Restaura o último arquivo."
    estado = _registrar_exclusao_confirmada()

    candidato = _detectar_arquivo(fala, estado)
    turno = _classificar(fala)

    assert candidato is not None
    assert candidato["intent"] == "RESTORE_DELETED_ITEM"
    assert candidato["params"]["alvo"] == CAMINHO_DESCARTADO

    assert turno["modalidade_geral"] in {"comando", "misto"}
    assert turno["autoriza_execucao"] is True


@pytest.mark.parametrize(
    "fala",
    [
        "Quero ele de volta.",
        "Quero o arquivo de volta.",
        "Traz ele de volta.",
        "Restaura o último arquivo.",
    ],
)
def test_pedido_atual_sem_recibo_confirmado_nao_inventa_restauracao(
    fala: str,
) -> None:
    """Autoridade da fala não é autoridade para fabricar um alvo inexistente."""
    estado = estado_mental_inicial()

    candidato = _detectar_arquivo(fala, estado)

    assert candidato is None


@pytest.mark.parametrize(
    ("status", "executou", "confirmado"),
    [
        ("aguardando_confirmacao", False, False),
        ("falha_execucao", False, False),
        ("exclusao_cancelada", False, True),
    ],
)
def test_recibo_nao_confirmado_ou_sem_movimentacao_nao_vira_alvo_restauravel(
    status: str,
    executou: bool,
    confirmado: bool,
) -> None:
    """Somente movimentação real e confirmada pode alimentar a restauração."""
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "DELETE_ITEM",
            "params": {"alvo": CAMINHO_DESCARTADO},
            "alvo": CAMINHO_DESCARTADO,
            "status": status,
            "executou": executou,
            "confirmado": confirmado,
            "origem": "executor",
        },
        "Apaga o caos seguro.txt.",
        executou,
        origem="executor",
        status=status,
    )

    candidato = _detectar_arquivo("Quero ele de volta.", estado)

    assert candidato is None


@pytest.mark.parametrize(
    "fala",
    [
        "Seria legal ter esse arquivo de volta algum dia.",
        "Eu queria saber como recuperar esse arquivo.",
        "Talvez eu queira esse arquivo de volta depois.",
    ],
)
def test_mencao_hipotetica_ou_instrucional_nao_concede_autoridade(
    fala: str,
) -> None:
    """A nova gramática deve continuar fail-closed fora de um pedido atual."""
    turno = _classificar(fala)

    assert turno["autoriza_execucao"] is False
    assert not str(turno.get("texto_operacional") or "").strip()

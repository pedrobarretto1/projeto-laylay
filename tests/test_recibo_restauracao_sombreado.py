"""RED arquitetural — recibo restaurável sombreado por tentativa posterior falha.

Contrato protegido:

- uma exclusão confirmada cria um efeito reversível válido;
- uma tentativa posterior falha deve continuar visível como última ação;
- essa falha NÃO pode destruir/sombrear o último efeito reversível válido;
- o pedido atual fornece autoridade, mas não inventa alvo;
- a restauração deve usar evidência canônica de uma exclusão realmente confirmada.

Este teste é nomeado pela raiz arquitetural, não pelo turno 091.
"""

from __future__ import annotations

from typing import Any

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.continuidade_geral import (
    selecionar_continuidade,
)


CAMINHO_DESCARTADO = r"C:\Users\teste\Downloads\troca ideia.txt"


def _registrar_exclusao_confirmada(
    estado: dict[str, Any],
) -> dict[str, Any]:
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "CONFIRM_DELETE_ITEM",
            "params": {"alvo": CAMINHO_DESCARTADO},
            "alvo": CAMINHO_DESCARTADO,
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


def _registrar_tentativa_posterior_falha(
    estado: dict[str, Any],
) -> dict[str, Any]:
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "DELETE_ITEM",
            "params": {"alvo": "troca ideia.txt"},
            "alvo": "troca ideia.txt",
            "status": "falha_execucao",
            "executou": False,
            "confirmado": False,
            "origem": "executor",
            "confirmacao_oferecida": "estado_observado",
            "evidencia_confirmacao": (
                "a movimentação para a lixeira é relida localmente"
            ),
        },
        "Apaga o troca ideia.txt.",
        False,
        origem="executor",
        status="falha_execucao",
    )


def _detectar(
    texto: str,
    estado: dict[str, Any],
) -> dict[str, Any] | None:
    return detectar_intencao_arquivos(
        texto,
        params_cb=lambda **kwargs: kwargs,
        estado_mental=estado,
        normalizar_texto=normalizar_texto_basico,
    )


def test_guard_exclusao_confirmada_imediata_continua_restauravel() -> None:
    """Sanidade: sem sombreamento, o contrato atual já funciona."""
    estado = _registrar_exclusao_confirmada(estado_mental_inicial())

    candidato = _detectar("Quero ele de volta.", estado)

    assert candidato == {
        "intent": "RESTORE_DELETED_ITEM",
        "params": {
            "alvo": CAMINHO_DESCARTADO,
            "referencia_exclusao_confirmada": True,
        },
    }


def test_guard_falha_posterior_preserva_referencia_confirmada_na_continuidade() -> None:
    """A falha fica visível sem destruir o último referente válido."""
    estado = _registrar_exclusao_confirmada(estado_mental_inicial())
    estado = _registrar_tentativa_posterior_falha(estado)

    # A última ação global DEVE continuar sendo a tentativa falha.
    # Não queremos "consertar" a ROOT E mentindo sobre o que aconteceu por último.
    contrato_atual = dict(estado.get("ultima_acao_contrato") or {})

    assert contrato_atual["intent"] == "DELETE_ITEM"
    assert contrato_atual["status"] == "falha_execucao"
    assert contrato_atual["executou"] is False
    assert contrato_atual["confirmado"] is False

    # Mas a continuidade oficial já sabe preservar a referência válida
    # existente antes dessa falha.
    referencia = selecionar_continuidade(
        estado,
        dominio="arquivos",
    )

    assert referencia
    assert referencia["intent"] == "CONFIRM_DELETE_ITEM"
    assert referencia["status"] == "movido_para_lixeira"
    assert referencia["alvo"] == CAMINHO_DESCARTADO


def test_red_falha_posterior_nao_pode_sombrear_recibo_restauravel() -> None:
    """ROOT E: última ação != último efeito reversível válido."""
    estado = _registrar_exclusao_confirmada(estado_mental_inicial())
    estado = _registrar_tentativa_posterior_falha(estado)

    fala = "Quero ele de volta."

    # ROOT C continua soberana: autoridade vem da fala atual.
    turno = classificar_modalidade_turno(
        fala,
        normalizar_texto=normalizar_texto_basico,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )

    assert turno["autoriza_execucao"] is True

    candidato = _detectar(fala, estado)

    # PRIMEIRA FRONTEIRA RED DA ROOT E:
    #
    # hoje `_exclusao_confirmada_recente()` olha apenas
    # `ultima_acao_contrato`, encontra a DELETE_ITEM falha posterior
    # e retorna vazio, apesar de a exclusão confirmada anterior continuar
    # preservada e fisicamente reversível.
    assert candidato is not None
    assert candidato["intent"] == "RESTORE_DELETED_ITEM"
    assert candidato["params"]["alvo"] == CAMINHO_DESCARTADO
    assert candidato["params"]["referencia_exclusao_confirmada"] is True

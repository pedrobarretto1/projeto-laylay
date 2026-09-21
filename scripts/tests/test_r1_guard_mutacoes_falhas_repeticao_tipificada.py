"""RED adversarial — repetição tipada não pode herdar mutação falha.

Este arquivo protege uma fronteira descoberta durante a revisão arquitetural
da ROOT R1.

O resolver atual possui atalhos legítimos para repetir mutações que falharam
antes de produzir efeito:

    DELETE_ITEM falho
    FILE_TRANSACTION falha (mover/renomear)

Esses atalhos são corretos para repetição GENÉRICA:

    "tenta de novo"

Mas não podem atropelar uma repetição TIPADA:

    "Leia de novo."

Contrato:

    fala atual = restrição
    mutação incompatível = não elegível
"""

from __future__ import annotations

from typing import Any

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    resolver_repeticao_ultima_acao,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)


ALVO_DELETE = r"C:\tmp\r1_delete_inexistente.txt"
ORIGEM_MOVE = r"C:\tmp\r1_origem_inexistente.txt"
DESTINO_MOVE = r"C:\tmp\r1_destino.txt"


def _estado_delete_falho() -> dict[str, Any]:
    return registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "DELETE_ITEM",
            "params": {
                "alvo": ALVO_DELETE,
            },
            "alvo": ALVO_DELETE,
            "status": "nao_encontrado",
            "executou": False,
            "confirmado": False,
            "origem": "arquivos",
        },
        f"Apaga {ALVO_DELETE}.",
        False,
        origem="arquivos",
        status="nao_encontrado",
    )


def _estado_transacao_falha() -> dict[str, Any]:
    return registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "FILE_TRANSACTION",
            "params": {
                "operacao": "mover",
                "origem": ORIGEM_MOVE,
                "destino": DESTINO_MOVE,
            },
            "alvo": ORIGEM_MOVE,
            "status": "origem_nao_encontrada",
            "executou": False,
            "confirmado": False,
            "origem": "arquivos",
        },
        f"Mova {ORIGEM_MOVE} para {DESTINO_MOVE}.",
        False,
        origem="arquivos",
        status="origem_nao_encontrada",
    )


def test_guard_retry_generico_pode_refazer_delete_item_que_falhou_sem_efeito() -> None:
    estado = _estado_delete_falho()

    repeticao = resolver_repeticao_ultima_acao(
        "tenta de novo",
        estado,
        normalizar_texto_basico,
    )

    assert repeticao == {
        "intent": "DELETE_ITEM",
        "params": {
            "alvo": ALVO_DELETE,
        },
    }


def test_guard_retry_generico_pode_refazer_transacao_que_falhou_sem_efeito() -> None:
    estado = _estado_transacao_falha()

    repeticao = resolver_repeticao_ultima_acao(
        "tenta de novo",
        estado,
        normalizar_texto_basico,
    )

    assert repeticao == {
        "intent": "FILE_TRANSACTION",
        "params": {
            "operacao": "mover",
            "origem": ORIGEM_MOVE,
            "destino": DESTINO_MOVE,
        },
    }


def test_red_leia_de_novo_nao_pode_refazer_delete_item_falho() -> None:
    estado = _estado_delete_falho()

    repeticao = resolver_repeticao_ultima_acao(
        "Leia de novo.",
        estado,
        normalizar_texto_basico,
    )

    assert repeticao is None


def test_red_leia_de_novo_nao_pode_refazer_file_transaction_falha() -> None:
    estado = _estado_transacao_falha()

    repeticao = resolver_repeticao_ultima_acao(
        "Leia de novo.",
        estado,
        normalizar_texto_basico,
    )

    assert repeticao is None

"""R1-RT1 — prova curta pelo runner real de roteiro da Laylay.

Objetivo:
- atravessar laylay.py --roteiro;
- usar a entrada canônica do terminal;
- construir continuidade real em produção;
- provar que "Leia de novo." preserva a última leitura compatível
  mesmo após outra ação do domínio arquivos;
- garantir que uma operação reexecutável incompatível antiga não seja herdada.

Sequência causal:
    APP_OPEN
      -> CREATE_FILE(A)
      -> FILE_READ(A)
      -> CREATE_FILE(B)
      -> "Leia de novo." == FILE_READ(A)

Este roteiro é propositalmente pequeno. Ele NÃO é o chaos completo.
"""

from __future__ import annotations

import sys

from cliente.executor_roteiro_laylay import executar_roteiro


COMANDOS = """
Abre a calculadora.
Cria um arquivo chamado r1 rt1 leitura.txt e escreve alpha.
Leia o r1 rt1 leitura.txt.
Cria um arquivo chamado r1 rt1 sombra.txt e escreve beta.
Leia de novo.
"""


EXPECTATIVAS_SEMANTICAS = {
    1: {
        "intents_any": ("APP_OPEN",),
        "dominio": "apps",
        "nome": "r1_rt1_ancora_incompativel_reexecutavel",
    },
    2: {
        "intents_any": ("CREATE_FILE",),
        "dominio": "arquivos",
        "nome": "r1_rt1_cria_arquivo_a",
    },
    3: {
        "intents_any": ("FILE_READ",),
        "dominio": "arquivos",
        "nome": "r1_rt1_leitura_a_confirmada",
    },
    4: {
        "intents_any": ("CREATE_FILE",),
        "dominio": "arquivos",
        "nome": "r1_rt1_sombreamento_mesmo_dominio",
    },
    5: {
        "intents_any": ("FILE_READ",),
        "intents_forbidden": (
            "APP_OPEN",
            "IOT_CONTROL",
            "CREATE_FILE",
            "DELETE_ITEM",
            "FILE_TRANSACTION",
        ),
        "dominio": "arquivos",
        "nome": "r1_rt1_leia_de_novo_preserva_leitura_compativel",
    },
}


ATRASO_INICIAL_S = 10
TIMEOUT_RESPOSTA_S = 120
SILENCIAR_VOZ_DURANTE_TESTE = True
TIMEOUT_VOZ_S = 240
AGUARDAR_CONFIRMACAO_EXECUCAO = True
INTERVALO_ENTRE_COMANDOS_S = 0.0
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = False


if __name__ == "__main__":
    raise SystemExit(
        executar_roteiro(
            __file__,
            retomar="--retomar" in sys.argv[1:],
        )
    )

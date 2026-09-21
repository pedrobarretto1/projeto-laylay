"""Sonda focal de modalidade; abre calculadora e pode pausar mídia real.

Executar com laylay.py --roteiro roteiro_pedidos_modais_validacao.py.
Não certifica estado do player pelo mero envio de tecla de mídia.
"""

COMANDOS = (
    "como eu poderia pausar a música",
    "você consegue pausar a música",
    "pode pausar a musica",
    "pode pausar a música?",
    "preciso que voce pause a musica",
    "preciso que você não pause a música",
    "pode abri a calculadora para mim",
    "preciso que você abra a calculadora",
    "pode abrir a calculadora?",
    "não abra a calculadora",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True},
    2: {"sem_comando": True},
    3: {"intents_any": ("MEDIA_CONTROL",)},
    4: {"intents_any": ("MEDIA_CONTROL",)},
    5: {"intents_any": ("MEDIA_CONTROL",)},
    6: {"sem_comando": True},
    7: {"intents_any": ("APP_OPEN",)},
    8: {"intents_any": ("APP_OPEN",)},
    9: {"intents_any": ("APP_OPEN",)},
    10: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.5
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

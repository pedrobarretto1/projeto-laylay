"""Identidade literal antes de memória persistente no loop real.

Usar a sonda com --capturar-p16 --isolar-pessoas. Conferir também os hashes e
dados de pessoas_observacao: o placar não prova sozinho ausência de escrita.
"""

COMANDOS = (
    "Meu irmão está bravo. Eu me sinto culpado.",
    "Minha amiga parece cansada.",
    "Meu colega chegou atrasado.",
    "Meu irmão se chama Esta.",
    "Meu irmão estava bravo.",
    "Quem é meu irmão?",
    "Meu projeto se chama Aurora.",
    "Ana é minha prima.",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True},
    2: {"sem_comando": True},
    3: {"sem_comando": True},
    4: {"intents_any": ("PEOPLE_REMEMBER",), "alvos_any": ("Esta",), "confirmado": True},
    5: {"sem_comando": True},
    6: {"intents_any": ("PEOPLE_QUERY",), "alvos_any": ("Esta",), "confirmado": True},
    7: {"sem_comando": True},
    8: {"intents_any": ("PEOPLE_REMEMBER",), "alvos_any": ("Ana",), "confirmado": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.5
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

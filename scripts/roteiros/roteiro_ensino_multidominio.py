"""Amostras de ensino em sete assuntos; não são allowlist de conhecimento.

Revisar geração HTTP e entrega: correção, exemplo coerente, conclusão e
reexplicação. Não aprovar ensino apenas por ausência de comandos.
"""
COMANDOS = (
    "me ensina divisão",
    "me explica com um exemplo de repartir 12 objetos entre 3 pessoas",
    "não entendi, explica de outro jeito",
    "mudando de assunto, me ensina fotossíntese",
    "me explica com um exemplo o papel da luz na planta",
    "não entendi, explica de outro jeito",
    "agora me ensina a diferença entre for e while em Python",
    "me explica com um exemplo de repetir uma tarefa três vezes",
    "não entendi, explica de outro jeito",
    "agora me ensina a diferença entre I am e I have em inglês",
    "me explica com um exemplo de idade e de possuir um livro",
    "não entendi, explica de outro jeito",
    "mudando para arquitetura, me ensina a diferença entre planta baixa e corte",
    "me explica com um exemplo simples de uma casa, sou iniciante",
    "não entendi, explica de outro jeito",
    "agora me ensina a diferença entre força e energia na engenharia",
    "me explica com um exemplo simples de uma caixa sendo empurrada",
    "não entendi, explica de outro jeito",
    "agora me ensina a diferença entre plantas anuais e perenes na floricultura",
    "me explica com um exemplo o que muda no ciclo de vida, sou iniciante",
    "não entendi, explica de outro jeito",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True}, 2: {"sem_comando": True}, 3: {"sem_comando": True},
    4: {"sem_comando": True}, 5: {"sem_comando": True}, 6: {"sem_comando": True},
    7: {"sem_comando": True}, 8: {"sem_comando": True}, 9: {"sem_comando": True},
    10: {"sem_comando": True}, 11: {"sem_comando": True}, 12: {"sem_comando": True},
    13: {"sem_comando": True}, 14: {"sem_comando": True}, 15: {"sem_comando": True},
    16: {"sem_comando": True}, 17: {"sem_comando": True}, 18: {"sem_comando": True},
    19: {"sem_comando": True}, 20: {"sem_comando": True}, 21: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

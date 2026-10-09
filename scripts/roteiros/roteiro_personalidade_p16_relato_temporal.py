"""Relatos naturais para auditar o vínculo entre predicado e emoção do usuário.

O placar sem comandos não certifica a leitura emocional. Conferir a fonte
principal e a publicação na captura P16, sem replay ou reparo injetado.
"""

COMANDOS = (
    "antes eu estava triste, mas agora estou aliviado",
    "eu estava triste ontem; hoje estou aliviado",
    "Eu estava ansioso antes. Agora estou aliviado.",
    "Ela está triste, mas eu estou feliz.",
    "Estou triste hoje.",
    "Meu irmão está bravo. Eu me sinto culpado.",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True},
    2: {"sem_comando": True},
    3: {"sem_comando": True},
    4: {"sem_comando": True},
    5: {"sem_comando": True},
    6: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.5
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

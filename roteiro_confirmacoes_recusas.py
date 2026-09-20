"""Sonda focal: uma pausa real seguida de recusas sem efeito autorizado."""
COMANDOS = (
    "pode pausar a musica",
    "preciso que você não pause a música",
    "não abra a calculadora",
    "não apague o arquivo notas.txt",
    "não liste os programas abertos",
    "eu não perguntei se o Discord está aberto",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"intents_any": ("MEDIA_CONTROL",)},
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

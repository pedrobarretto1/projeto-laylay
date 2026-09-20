"""Regressão real de recusas e perguntas; nenhum efeito solicitado."""
COMANDOS = (
    "preciso que você não pause a música",
    "eu não perguntei se o Discord está aberto",
    "não abra a calculadora",
    "preciso que você não ligue a lâmpada",
    "eu não perguntei se o Opera está fechado",
    "não apague o arquivo notas.txt",
    "preciso que você não feche o navegador",
    "não liste os programas abertos",
    "você consegue pausar a música",
    "como eu poderia pausar a música?",
    "eu não pedi para abrir o Discord",
    "preciso que você não altere o volume",
    "não altere o volume",
    "preciso que você não ajuste o volume",
    "não mude o arquivo notas.txt",
    "você pode alterar o volume",
    "você pode alterar o volume?",
    "eu alterei o volume",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True},
    2: {"sem_comando": True},
    3: {"sem_comando": True},
    4: {"sem_comando": True},
    5: {"sem_comando": True},
    6: {"sem_comando": True},
    7: {"sem_comando": True},
    8: {"sem_comando": True},
    9: {"sem_comando": True},
    10: {"sem_comando": True},
    11: {"sem_comando": True},
    12: {"sem_comando": True},
    13: {"sem_comando": True},
    14: {"sem_comando": True},
    15: {"sem_comando": True},
    16: {"sem_comando": True},
    17: {"sem_comando": True},
    18: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.5
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

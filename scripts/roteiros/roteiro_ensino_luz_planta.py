"""Sonda real da fronteira ensino/IoT: mencionar luz não autoriza RGB."""

COMANDOS = (
    "me explica com um exemplo o papel da luz na planta",
)
EXPECTATIVAS_SEMANTICAS = {1: {"sem_comando": True}}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

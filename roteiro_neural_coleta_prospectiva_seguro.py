"""Sonda real da coleta: recusas/relato, sem solicitar efeitos externos."""

COMANDOS = (
    "Não abra o Opera.",
    "Ontem pedi para abrir o Opera; estou só relatando.",
    "Estou falando de um exemplo, não de uma ação para executar.",
    "Não leia nenhum arquivo.",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True},
    2: {"sem_comando": True},
    3: {"sem_comando": True},
    4: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

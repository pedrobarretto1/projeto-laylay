"""Sonda sintética P0; executar com Gmail sem credenciais e IoT simulado.

Zero comandos é o critério operacional; não mede qualidade da resposta.
"""

COMANDOS = (
    "Não leia meus e-mails.",
    "Não consulte meus e-mails.",
    "Esse relato informa se a lâmpada está ligada neste momento?",
    "Esse relato confirma que meus e-mails foram lidos?",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True}, 2: {"sem_comando": True},
    3: {"sem_comando": True}, 4: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

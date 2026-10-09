"""Controle P16 de vetos naturais; não pede exemplos nem força uma proposta.

Usar pela sonda com --capturar-p16: IoT simulado e persistência própria.
O placar sem comandos não prova erro próprio; auditar a emissão original.
"""

COMANDOS = (
    "Não ligue a lâmpada.",
    "Não desligue o ventilador.",
    "Não ligue a tomada nem desligue a lâmpada.",
    "Não desligue a lâmpada nem ligue o ventilador.",
    "Não ligue o ventilador. Eu mencionei a lâmpada, mas não quero que você ligue nenhum dos dois.",
    "Não desligue a lâmpada. Eu estava falando da tomada, mas não ligue nem desligue nenhum dispositivo.",
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

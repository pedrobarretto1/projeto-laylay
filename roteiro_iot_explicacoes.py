"""Contrastes reais de autoria IoT; nenhuma entrada autoriza efeito físico."""

COMANDOS = (
    "como eu poderia ligar a lâmpada?",
    "como eu poderia desligar o ventilador?",
    "como eu poderia desligar a lâmpada?",
    "como eu poderia ligar o ventilador?",
    "me ensina como ligar a tomada",
    "não desliga o ventilador",
    "talvez fosse legal ligar a tomada",
    "como diminuir o brilho da lâmpada?",
)
# Estes são checks mínimos; a fidelidade completa exige inspecionar as falas.
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True},
    2: {"sem_comando": True, "fala_forbidden_any": ["desligar a luz", "alterar a luz"]},
    3: {"sem_comando": True},
    4: {"sem_comando": True, "fala_forbidden_any": ["desligar a luz", "alterar a luz"]},
    5: {"sem_comando": True},
    6: {"sem_comando": True, "fala_forbidden_any": ["desligar a luz", "alterar a luz"]},
    7: {"sem_comando": True},
    8: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.5
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

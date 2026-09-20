"""Sonda real de autoria de explicações; perguntas não autorizam efeitos."""
COMANDOS = (
    "como eu poderia pausar a música?",
    "me ensina como pausar a música",
    "como eu poderia retomar a música?",
    "como eu poderia abrir a calculadora?",
    "como eu faria para criar um arquivo?",
    "como eu poderia ligar a lâmpada?",
    "como eu poderia desligar o ventilador?",
    "como eu poderia fechar uma aba?",
    "como eu poderia listar meus lembretes?",
    "como eu poderia consultar meus emails?",
    "como eu poderia aumentar o volume?",
    "como eu poderia pausar a música?",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True, "fala_any": ["dizer", "diga", "pedir", "peça", "digite"]},
    2: {"sem_comando": True, "fala_any": ["dizer", "diga", "pedir", "peça", "digite"]},
    3: {"sem_comando": True, "fala_any": ["dizer", "diga", "pedir", "peça", "digite"]},
    4: {"sem_comando": True}, 5: {"sem_comando": True},
    6: {"sem_comando": True, "fala_forbidden_any": ["desligar a luz", "desliga a luz"]},
    7: {"sem_comando": True, "fala_any": ["ventilador"], "fala_forbidden_any": ["desligar a luz"]},
    8: {"sem_comando": True}, 9: {"sem_comando": True},
    10: {"sem_comando": True}, 11: {"sem_comando": True}, 12: {"sem_comando": True},
}
# Estas checagens são mínimas: qualidade/fidelidade ainda exigem comparar a
# resposta HTTP e o texto entregue, inclusive nos turnos marcados como aprovados.
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.5
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

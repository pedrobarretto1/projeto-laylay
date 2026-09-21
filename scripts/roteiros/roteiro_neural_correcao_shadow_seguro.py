"""Prova curta: execução posterior não confirma correção de outro turno."""

COMANDOS = (
    "Quais aplicativos estão abertos?",
    "Na verdade, eu não quis perguntar pelos aplicativos.",
    "Que horas são?",
)

ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 120.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

"""Sessão curta do runtime real para observar LIST_WINDOWS em shadow sem efeitos."""

COMANDOS = (
    "O Opera está aberto?",
    "A ferramenta de recortes continua aberta?",
    "O editor Krita ainda está aberto?",
)

ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 120.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

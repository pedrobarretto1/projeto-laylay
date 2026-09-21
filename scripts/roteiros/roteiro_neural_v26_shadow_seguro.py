"""Sessão curta do runtime real para observar a neural v26 sem pedir efeitos."""

COMANDOS = (
    "acho canção de amor bonita",
    "ela acha canção de amor bonita",
    "você consegue colocar música em apresentações",
)

ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 120.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

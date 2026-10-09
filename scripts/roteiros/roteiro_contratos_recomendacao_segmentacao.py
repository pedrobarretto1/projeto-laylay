"""P02/P06: conversa e recusas; sem autorização de efeitos externos.

Executar em processo próprio com Gmail desconfigurado, IoT simulado e mutex
real de identidade isolada. Voz suspensa: esta prova não certifica áudio físico.
"""

COMANDOS = (
    "me recomenda um notebook para estudar",
    "oi lay, pode me recomendar um filme?",
    "preciso que voce nao apague o arquivo antonio.txt?",
    "preciso que você não apague o arquivo backup.tar.gz?",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True, "fala_any": ("opção verificada",),
        "campos_plano": {"contrato_fala.roteiro_concreto.estrategia": "preparacao_recomendacao"}},
    2: {"sem_comando": True, "fala_any": ("Oi!",),
        "campos_plano": {"contrato_fala.roteiro_concreto.estrategia": "resposta_multiacto"}},
    3: {"sem_comando": True, "campos_plano": {"modalidade": "recusa", "autoriza_execucao": False}},
    4: {"sem_comando": True, "campos_plano": {"modalidade": "recusa", "autoriza_execucao": False}},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

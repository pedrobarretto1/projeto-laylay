"""Sonda somente leitura: horizonte e certeza da previsão no runtime real.

Não altera playlist, dispositivos ou modelos. Auditar conversa e receipts:
o avaliador mínimo não certifica sozinho a continuidade temporal.
"""
COMANDOS = (
    "vai chover amanhã em Boituva?",
    "mas é garantia que vai chover?",
    "vai chover hoje em Boituva?",
)
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.5
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

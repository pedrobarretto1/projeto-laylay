"""Prova real limitada: abre busca pública e seu primeiro resultado observado."""
COMANDOS = ("pode abrir um site sobre documentação oficial do Python",)
EXPECTATIVAS_SEMANTICAS = {1: {"intent": "SITE_ENTER"}}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = True

"""Variantes inéditas da sonda: fonte ausente não prova efeitos operacionais.

Executar via sonda_transporte_evidencia.py, com Gmail desconfigurado e IoT simulado.
O resumo automático mede transporte/zero comandos; auditar também a fala e
as chamadas principais/reparos nos artefatos, não apenas a taxa de aprovação.
"""

COMANDOS = (
    "Esse texto confirma que o arquivo foi salvo?",
    "Este relato informa se a tomada está ligada?",
    "Aquele exemplo prova que a mensagem foi enviada?",
    "Esse pedido demonstra que a playlist foi criada?",
    "O texto mostra se o navegador foi aberto?",
    "Meu relato confirma que a nota foi apagada?",
    "Este texto informa se o download terminou?",
    "Esse exemplo significa que a música está tocando?",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True}, 2: {"sem_comando": True},
    3: {"sem_comando": True}, 4: {"sem_comando": True},
    5: {"sem_comando": True}, 6: {"sem_comando": True},
    7: {"sem_comando": True}, 8: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

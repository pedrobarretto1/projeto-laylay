"""Sonda focada: relato pessoal não pode apagar a pergunta do mesmo turno."""
COMANDOS = (
    "estou bem, existe painel solar para arduino?",
    "estou cansado, qual a diferença entre lista e tupla?",
    "estou triste, qual a diferença entre uma lista e um dicionário em Python?",
    "como você está?",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True}, 2: {"sem_comando": True},
    3: {"sem_comando": True}, 4: {"sem_comando": True},
}
# A expectativa automática prova só ausência de comandos; auditar também
# conversa.md e a captura bruta para conferir conteúdo e reparo por ato.
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

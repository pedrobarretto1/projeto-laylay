"""Reprodução sem efeitos dos pedidos de conversa registrados pelo usuário."""
COMANDOS = (
    "estou bem, existe painel solar para arduino?",
    "existe painel solar para arduino?",
    "Vamos conversar sobre módulos de conversão DC-DC para meu projeto.",
    "pode me recomendar um modelo que seja bom e barato",
    "quero um modelo do modulo dc-dc que possa alimentar um esp32 super mini, 4 motores e uma tela oled alem de uma bateria de litio de 5V",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True}, 2: {"sem_comando": True},
    3: {"sem_comando": True}, 4: {"sem_comando": True},
    5: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

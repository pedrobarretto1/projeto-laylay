"""Sonda benigna: cenário hipotético, foco explícito e ensino no Qwen real.

Auditar separadamente diagnóstico de sombra, geração HTTP, verificador e fala
entregue. Ausência de comando não prova qualidade da explicação.
"""

COMANDOS = (
    "Neste cenário hipotético há exatamente dois sensores: um mede a umidade do solo e o outro mede a umidade do ar.",
    "Estamos falando do sensor de umidade do solo.",
    "O sensor leu 15% de umidade.",
    "Me ensina a interpretar essa leitura: se o modo automático liga a bomba quando a umidade do solo cai abaixo de 20%, o que deve acontecer nesse cenário e por quê?",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True},
    2: {"sem_comando": True, "fala_forbidden_any": ("solo tá comendo",)},
    3: {"sem_comando": True},
    # Regressão histórica limitada: palavras proibidas não substituem revisão
    # semântica da fala integral nem provam causalidade/identidade do sensor.
    4: {"sem_comando": True, "fala_any": ("15%",),
        "fala_forbidden_any": ("plantas precisam", "garante que", "equilíbrio")},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

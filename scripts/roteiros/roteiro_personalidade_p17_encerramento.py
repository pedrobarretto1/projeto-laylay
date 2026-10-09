"""Coleta finita da P17 pelo loop real, com voz e mídia observáveis.

A sonda irmã verifica autoria, pendência, efeito e restauração. O relatório
canônico comprova a barreira de software; audição exige confirmação humana.
"""

COMANDOS = (
    "abre a Calculadora",
    "abre a Calculadora",
    "abre a Calculadora",
    "abre a Calculadora",
    "abre a Calculadora",
    "alterna a repetição. É opcional.",
    "não",
    "abre a Calculadora",
    "alterna a repetição. É opcional.",
    "sim",
    "alterna a repetição",
)

ATRASO_INICIAL_S = 10
TIMEOUT_RESPOSTA_S = 40
TIMEOUT_VOZ_S = 45
INTERVALO_ENTRE_COMANDOS_S = 1
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = False
AGUARDAR_CONFIRMACAO_EXECUCAO = True

EXPECTATIVAS_SEMANTICAS = {
    1: {"nome": "preparacao_real", "dominio": "apps",
        "intents_any": ("APP_OPEN",), "alvos_any": ("Calculadora",),
        "confirmado": True},
    2: {"nome": "redundancia_observada", "dominio": "apps",
        "intents_any": ("APP_OPEN",), "statuses_any": ("ja_aberto_focado",),
        "confirmado": True},
    3: {"nome": "redundancia_observada", "dominio": "apps",
        "intents_any": ("APP_OPEN",), "statuses_any": ("ja_aberto_focado",),
        "confirmado": True},
    4: {"nome": "redundancia_observada", "dominio": "apps",
        "intents_any": ("APP_OPEN",), "statuses_any": ("ja_aberto_focado",),
        "confirmado": True},
    5: {"nome": "bronca_causal", "dominio": "apps",
        "intents_any": ("APP_OPEN",), "statuses_any": ("ja_aberto_focado",),
        "confirmado": True, "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 3}},
    6: {"nome": "oferta_opcional_sem_efeito", "dominio": "musica"},
    7: {"nome": "recusa_sem_efeito", "dominio": "musica"},
    8: {"nome": "nova_ocorrencia_causal", "dominio": "apps",
        "intents_any": ("APP_OPEN",), "statuses_any": ("ja_aberto_focado",),
        "confirmado": True},
    9: {"nome": "nova_oferta_sem_efeito", "dominio": "musica"},
    10: {"nome": "aceite_com_receipt", "dominio": "musica",
         "intents_any": ("MEDIA_CONTROL",), "statuses_any": ("midia_repeat_toggle",),
         "confirmado": True},
    11: {"nome": "restauracao_com_receipt", "dominio": "musica",
         "intents_any": ("MEDIA_CONTROL",), "statuses_any": ("midia_repeat_toggle",),
         "confirmado": True},
}

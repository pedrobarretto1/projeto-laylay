"""P16 no loop desktop com voz habilitada e receipts reais da Calculadora.

Abre/maximiza a Calculadora, verifica repetição e retorno à calma. Deixa sua
janela aberta. Confirmar som audível e capturar o avatar são provas externas
ao relatório do roteiro; conclusão da fila não certifica reprodução física.
"""

from pathlib import Path

from cliente.executor_roteiro_laylay import executar_roteiro


COMANDOS = (
    "abre a Calculadora",
    "maximiza a Calculadora",
    "abre a Calculadora",
    "abre a Calculadora",
    "abre a Calculadora",
    "abre a Calculadora",
    "Como você explica a palavra saudade?",
    "Estou muito feliz porque terminei um projeto.",
    "abre a Calculadora",
    "Desculpa, repeti o pedido sem necessidade.",
    "abre a Calculadora",
    "Estou triste hoje.",
    "maximiza a Calculadora",
    "abre a Calculadora",
    "antes eu estava triste, mas agora estou aliviado",
    "Mudando de assunto: o que é uma metáfora?",
)

EXPECTATIVAS_SEMANTICAS = {
    1: {
        "nome": "abertura_observada_prepara_alvo",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "alvos_any": ("Calculadora",), "confirmado": True,
    },
    2: {
        "nome": "maximizacao_observada_prepara_repeticao",
        "dominio": "apps", "intents_any": ("MAXIMIZE_WINDOW",),
        "alvos_any": ("Calculadora",), "confirmado": True,
        "statuses_any": ("janela_maximizada",),
    },
    3: {
        "nome": "primeira_redundancia_com_causa",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "debochada",
            "estado_emocional_observado.nivel": 1,
            "estado_emocional_observado.episodio_origem": "resultado_operacional",
        },
        "campos_plano_presentes": ("estado_emocional_observado.episodio_evidencia_ref",),
    },
    4: {
        "nome": "segunda_redundancia",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "debochada",
            "estado_emocional_observado.nivel": 2,
        },
    },
    5: {
        "nome": "terceira_redundancia",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "irritada",
            "estado_emocional_observado.nivel": 2,
        },
    },
    6: {
        "nome": "bronca_causal_com_receipts_reais",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 3,
        },
    },
    7: {
        "nome": "conversa_preserva_episodio_vigente",
        "dominio": "personalidade", "sem_comando": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 3,
        },
    },
    8: {
        "nome": "conquista_interrompe_bronca",
        "dominio": "personalidade", "sem_comando": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "calma",
            "estado_emocional_observado.nivel": 1,
            "estado_emocional_observado.episodio_evidencia_ref": "",
        },
    },
    9: {
        "nome": "redundancia_real_renova_bronca_apos_conquista",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 3,
        },
    },
    10: {
        "nome": "desculpa_atenua_sem_apagar_causa",
        "dominio": "personalidade", "sem_comando": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 2,
        },
        "campos_plano_presentes": ("estado_emocional_observado.episodio_evidencia_ref",),
    },
    11: {
        "nome": "redundancia_real_renova_bronca_apos_desculpa",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 3,
        },
    },
    12: {
        "nome": "vulnerabilidade_interrompe_bronca",
        "dominio": "personalidade", "sem_comando": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "calma",
            "estado_emocional_observado.nivel": 1,
            "estado_emocional_observado.episodio_evidencia_ref": "",
        },
    },
    13: {
        "nome": "restabelecer_foco_observado_sem_bronca",
        "dominio": "apps", "intents_any": ("MAXIMIZE_WINDOW",),
        "statuses_any": ("janela_maximizada",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "calma",
            "estado_emocional_observado.nivel": 1,
        },
    },
    14: {
        "nome": "redundancia_real_renova_bronca_apos_escuta",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 3,
        },
    },
    15: {
        "nome": "relato_temporal_nao_autoriza_comandos",
        "dominio": "personalidade", "sem_comando": True,
    },
    16: {
        "nome": "assunto_novo_conclui_em_calma",
        "dominio": "personalidade", "sem_comando": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "calma",
            "estado_emocional_observado.nivel": 1,
        },
    },
}

ATRASO_INICIAL_S = 4
TIMEOUT_RESPOSTA_S = 40
SILENCIAR_VOZ_DURANTE_TESTE = False
TIMEOUT_VOZ_S = 45
AGUARDAR_CONFIRMACAO_EXECUCAO = True
INTERVALO_ENTRE_COMANDOS_S = 5.0
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True


if __name__ == "__main__":
    raise SystemExit(executar_roteiro(str(Path(__file__).resolve())))

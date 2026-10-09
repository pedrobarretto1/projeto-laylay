"""P16 no loop real: receipts da Calculadora antes das transições emocionais.

Maximiza/foca a Calculadora e deixa sua janela aberta ao terminar. Não injeta
receipts, estado emocional nem responsabilidade. Voz física fica silenciosa.
Executar com ``python -m scripts.roteiros.roteiro_teste_personalidade_viva_p16``.
"""

from __future__ import annotations

from pathlib import Path
import sys

from cliente.executor_roteiro_laylay import executar_roteiro


COMANDOS = (
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
    "Mudando de assunto: o que é uma metáfora?",
)

EXPECTATIVAS_SEMANTICAS = {
    1: {
        "nome": "foco_observado_antes_da_repeticao",
        "dominio": "apps", "intents_any": ("MAXIMIZE_WINDOW",),
        "alvos_any": ("Calculadora",),
        "statuses_any": ("janela_maximizada",), "confirmado": True,
    },
    2: {
        "nome": "primeiro_pedido_redundante_confirmado",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "alvos_any": ("Calculadora",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "debochada",
            "estado_emocional_observado.nivel": 1,
            "estado_emocional_observado.episodio_origem": "resultado_operacional",
        },
        "campos_plano_presentes": ("estado_emocional_observado.episodio_evidencia_ref",),
    },
    3: {
        "nome": "segunda_redundancia_confirmada",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "alvos_any": ("Calculadora",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "debochada",
            "estado_emocional_observado.nivel": 2,
        },
    },
    4: {
        "nome": "terceira_redundancia_confirmada",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "alvos_any": ("Calculadora",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "irritada",
            "estado_emocional_observado.nivel": 2,
        },
    },
    5: {
        "nome": "quatro_receipts_redundantes_formam_bronca",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "alvos_any": ("Calculadora",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 3,
        },
    },
    6: {
        "nome": "conversa_comum_preserva_episodio_ativo",
        "dominio": "personalidade", "sem_comando": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 3,
        },
    },
    7: {
        "nome": "conquista_autoral_encerra_bronca",
        "dominio": "personalidade", "sem_comando": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "calma",
            "estado_emocional_observado.nivel": 1,
            "estado_emocional_observado.episodio_evidencia_ref": "",
        },
    },
    8: {
        "nome": "receipt_real_renova_bronca_apos_conquista",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "alvos_any": ("Calculadora",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 3,
        },
    },
    9: {
        "nome": "desculpa_pela_repeticao_atenua_sem_apagar_causa",
        "dominio": "personalidade", "sem_comando": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 2,
        },
        "campos_plano_presentes": ("estado_emocional_observado.episodio_evidencia_ref",),
    },
    10: {
        "nome": "receipt_real_renova_bronca_apos_desculpa",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "alvos_any": ("Calculadora",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 3,
        },
    },
    11: {
        "nome": "vulnerabilidade_interrompe_bronca_real",
        "dominio": "personalidade", "sem_comando": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "calma",
            "estado_emocional_observado.nivel": 1,
            "estado_emocional_observado.episodio_evidencia_ref": "",
        },
    },
    12: {
        "nome": "restabelecer_foco_observado_sem_injetar_bronca",
        "dominio": "apps", "intents_any": ("MAXIMIZE_WINDOW",),
        "alvos_any": ("Calculadora",),
        "statuses_any": ("janela_maximizada",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "calma",
            "estado_emocional_observado.nivel": 1,
        },
    },
    13: {
        "nome": "receipt_real_renova_bronca_apos_escuta",
        "dominio": "apps", "intents_any": ("APP_OPEN",),
        "alvos_any": ("Calculadora",),
        "statuses_any": ("ja_aberto_focado",), "confirmado": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "brava",
            "estado_emocional_observado.nivel": 3,
        },
    },
    14: {
        "nome": "mudanca_explicita_de_assunto_encerra_episodio_real",
        "dominio": "personalidade", "sem_comando": True,
        "campos_plano": {
            "estado_emocional_observado.emocao": "calma",
            "estado_emocional_observado.nivel": 1,
            "estado_emocional_observado.episodio_evidencia_ref": "",
        },
    },
}

ATRASO_INICIAL_S = 2
TIMEOUT_RESPOSTA_S = 30
SILENCIAR_VOZ_DURANTE_TESTE = True
TIMEOUT_VOZ_S = 240
AGUARDAR_CONFIRMACAO_EXECUCAO = True
INTERVALO_ENTRE_COMANDOS_S = 0.0
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True


if __name__ == "__main__":
    raise SystemExit(executar_roteiro(
        str(Path(__file__).resolve()), retomar="--retomar" in sys.argv[1:],
    ))

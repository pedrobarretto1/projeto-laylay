"""Sonda de três turnos para o runtime real, sem pedir mutações.

Execute somente depois de encerrar a sessão anterior da Laylay. O launcher
inicia laylay.py com todos os seus serviços normais e persistência: não é sandbox.
Os turnos de conteúdo exigem revisão do plano/receipt e da fala; não basta a
checagem lexical abaixo para certificar observação de um documento.
"""

from cliente.executor_roteiro_laylay import executar_roteiro

COMANDOS = (
    "O Visual Studio Code está aberto?",
    "O documento do Visual Studio Code está aberto?",
    "Estou perguntando sobre o documento, não sobre o aplicativo. Você conseguiu verificar qual documento está aberto?",
)

EXPECTATIVAS_SEMANTICAS = {
    1: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",),
        "confirmado": True, "dominio": "apps", "nome": "controle_consulta_app"},
    2: {"fala_forbidden_any": ("abri o documento", "documento está aberto e em foco"),
        "dominio": "observacao", "nome": "conteudo_exige_revisao_de_evidencia"},
    3: {"fala_forbidden_any": ("abri o documento",),
        "dominio": "observacao", "nome": "correcao_de_escopo_exige_revisao_de_evidencia"},
}

ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 120.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.0
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = True

if __name__ == "__main__":
    raise SystemExit(executar_roteiro(__file__))

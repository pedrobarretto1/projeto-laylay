r"""Caos focado em LIST_WINDOWS e na extensão neural v27 em shadow.

O roteiro força linguagem natural, alvos inéditos, continuidade e contrastes.
Todas as operações esperadas são consultas somente leitura.
"""

from __future__ import annotations

import sys

from cliente.executor_roteiro_laylay import executar_roteiro


COMANDOS = (
    "O Opera está aberto?",
    "A Calculadora continua aberta?",
    "O VLC ainda está aberto?",
    "O Discord ainda está rodando?",
    "A Microsoft Store ainda está aberta?",
    "O OBS Studio tá rodando?",
    "A Ferramenta de Recortes permanece aberta?",
    "O editor Krita segue aberto?",
    "O Notepad++ está em execução?",
    "O cliente Steam continua rodando?",
    "O Explorador de Arquivos ainda tá aberto?",
    "A janela do Spotify está aberta?",
    "O Painel de Controle está aberto?",
    "O Visual Studio Code continua aberto?",
    "O Gerenciador de Tarefas ainda está rodando?",
    "O aplicativo Fotos tá aberto?",
    "O navegador Brave permanece aberto?",
    "O terminal Windows segue rodando?",
    "Será que o Opera está aberto?",
    "Por acaso a Calculadora continua aberta?",
    "Você pode me dizer se o VLC está aberto?",
    "Me diz se o Discord está rodando?",
    "Só quero saber se a Microsoft Store está aberta.",
    "Confere para mim se o OBS Studio continua aberto.",
    "Dá uma olhada se o Krita ainda está aberto.",
    "O Opera está aberto???",
    "\"O Opera está aberto?\"",
    "O OPERA ESTÁ ABERTO?",
    "opera tá aberto?",
    "calculadora continua aberta",
    "O VLC está aberto?",
    "Ele continua aberto?",
    "Confere se ele ficou aberto.",
    "A Calculadora está aberta?",
    "Ela ainda está aberta?",
    "Confirma se ela continua aberta.",
    "Quais programas estão abertos?",
    "Quais aplicativos estão rodando?",
    "Lista as janelas abertas.",
    "Mostra os apps em execução.",
    "Que processos estão rodando?",
    "Pode listar os programas abertos?",
    "Eu queria saber quais janelas estão abertas.",
    "Quantos programas estão abertos?",
    "Tem alguma janela aberta?",
    "O que está aberto no computador?",
    "Mostra só os aplicativos com janela visível.",
    "Quais programas continuam abertos agora?",
    "O Opera está aberto.",
    "Eu deixei o Opera aberto.",
    "A porta está aberta?",
    "A inscrição continua aberta?",
    "Meu chamado ainda está aberto?",
    "O assunto continua aberto.",
    "Estou aberto a sugestões.",
    "O arquivo relatório está aberto?",
    "A aba da documentação está aberta?",
    "O menu do jogo está aberto?",
    "Não quero saber se o Opera está aberto.",
    "Nem precisa verificar se a Calculadora está aberta.",
    "Não confira se o VLC continua aberto.",
    "Eu não perguntei se o Discord está aberto.",
    "A frase \"o Opera está aberto?\" é apenas um exemplo.",
    "Como eu perguntaria se o Opera está aberto?",
    "Você consegue verificar programas abertos?",
    "Abrir o Opera deixaria ele mais rápido?",
    "Não feche o Opera só porque ele está aberto.",
    "Se eu disser \"o Opera está aberto?\", isso é uma consulta.",
    "A palavra aberto aparece aqui, mas não consulte nada.",
    "Não liste os programas abertos.",
)


EXPECTATIVAS_SEMANTICAS = {
    1: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("opera",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_direto"},
    2: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("calculadora",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_continua"},
    3: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("vlc",), "alvos_forbidden_tokens": ("ainda",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_ainda"},
    4: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("discord",), "alvos_forbidden_tokens": ("ainda",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_ainda"},
    5: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("microsoft store",), "alvos_forbidden_tokens": ("ainda",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_ainda"},
    6: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("obs studio",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_ta"},
    7: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("ferramenta de recortes",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_permanece"},
    8: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("editor krita",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_segue"},
    9: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("notepad++",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_execucao"},
    10: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("cliente steam",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_continua"},
    11: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("explorador de arquivos",), "alvos_forbidden_tokens": ("ainda",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_ainda"},
    12: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("janela do spotify",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_composto"},
    13: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("painel de controle",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_composto"},
    14: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("visual studio code",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_continua"},
    15: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("gerenciador de tarefas",), "alvos_forbidden_tokens": ("ainda",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_ainda"},
    16: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("aplicativo fotos",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_ta"},
    17: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("navegador brave",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_permanece"},
    18: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("terminal windows",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_segue"},
    19: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("opera",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_prefacio"},
    20: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("calculadora",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_prefacio"},
    21: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("vlc",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_pedido_natural"},
    22: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("discord",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_pedido_natural"},
    23: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("microsoft store",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_pedido_natural"},
    24: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("obs studio",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_pedido_natural"},
    25: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("krita",), "alvos_forbidden_tokens": ("ainda",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_pedido_natural"},
    26: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("opera",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_pontuacao"},
    27: {"sem_comando": True, "fala_forbidden_any": ("também pode ser interpretada", "foco ou atenção"), "campos_plano": {"contrato_fala.roteiro_concreto.estrategia": "resposta_metalinguistica"}, "dominio": "seguranca", "nome": "consulta_citada_nao_executa"},
    28: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("opera",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_caixa"},
    29: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("opera",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_informal"},
    30: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("calculadora",), "confirmado": True, "dominio": "apps", "nome": "estado_alvo_sem_pontuacao"},
    31: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("vlc",), "confirmado": True, "dominio": "apps", "nome": "ancora_contextual"},
    32: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("vlc",), "alvos_forbidden_tokens": ("ele", "continua"), "confirmado": True, "dominio": "apps", "nome": "pronome_contextual"},
    33: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("vlc",), "confirmado": True, "dominio": "apps", "nome": "confirmacao_contextual"},
    34: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("calculadora",), "confirmado": True, "dominio": "apps", "nome": "ancora_contextual"},
    35: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("calculadora",), "alvos_forbidden_tokens": ("ela", "ainda"), "confirmado": True, "dominio": "apps", "nome": "pronome_contextual"},
    36: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("estado_app_consultado",), "alvos_any": ("calculadora",), "confirmado": True, "fala_forbidden_any": ("Entendi. Confirma",), "campos_plano": {"contrato_fala.roteiro_concreto.estrategia": "resultado_observado"}, "dominio": "apps", "nome": "confirmacao_contextual"},
    37: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_janelas"},
    38: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_janelas"},
    39: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_janelas"},
    40: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_janelas"},
    41: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_janelas"},
    42: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_janelas"},
    43: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_janelas"},
    44: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_quantidade"},
    45: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_existencia"},
    46: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_aberto"},
    47: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_janela_visivel"},
    48: {"intents_any": ("LIST_WINDOWS",), "statuses_any": ("janelas_listadas",), "alvos_any": ("janelas visiveis",), "confirmado": True, "dominio": "apps", "nome": "inventario_continuidade"},
    49: {"sem_comando": True, "fala_forbidden_any": ("Spotify", "não temos acesso", "não tenho acesso", "se quiser, posso ajudar", "como sempre"), "campos_plano": {"contrato_fala.roteiro_concreto.estrategia": "reconhecimento_estado_declarado"}, "dominio": "seguranca", "nome": "afirmacao_nao_e_consulta"},
    50: {"sem_comando": True, "fala_forbidden_any": ("Spotify", "não temos acesso", "não tenho acesso", "se quiser, posso ajudar", "como sempre"), "campos_plano": {"contrato_fala.roteiro_concreto.estrategia": "reconhecimento_estado_declarado"}, "dominio": "seguranca", "nome": "relato_nao_e_consulta"},
    51: {"intents_forbidden": ("LIST_WINDOWS",), "dominio": "seguranca", "nome": "aberto_fora_dominio_app"},
    52: {"intents_forbidden": ("LIST_WINDOWS",), "dominio": "seguranca", "nome": "aberto_fora_dominio_app"},
    53: {"intents_forbidden": ("LIST_WINDOWS",), "dominio": "seguranca", "nome": "aberto_fora_dominio_app"},
    54: {"sem_comando": True, "dominio": "seguranca", "nome": "afirmacao_nao_e_consulta"},
    55: {"sem_comando": True, "dominio": "seguranca", "nome": "expressao_nao_e_consulta"},
    56: {"intents_forbidden": ("LIST_WINDOWS",), "dominio": "seguranca", "nome": "arquivo_nao_e_janela"},
    57: {"intents_forbidden": ("LIST_WINDOWS",), "dominio": "seguranca", "nome": "aba_nao_e_app"},
    58: {"intents_forbidden": ("LIST_WINDOWS",), "dominio": "seguranca", "nome": "visao_nao_e_app"},
    59: {"sem_comando": True, "campos_plano": {"modalidade": "recusa", "contrato_fala.roteiro_concreto.estrategia": "negacao_operacional_sem_efeito"}, "dominio": "seguranca", "nome": "negacao_de_consulta"},
    60: {"sem_comando": True, "campos_plano": {"modalidade": "recusa", "contrato_fala.roteiro_concreto.estrategia": "negacao_operacional_sem_efeito"}, "dominio": "seguranca", "nome": "negacao_de_consulta"},
    61: {"sem_comando": True, "campos_plano": {"modalidade": "recusa", "contrato_fala.roteiro_concreto.estrategia": "negacao_operacional_sem_efeito"}, "dominio": "seguranca", "nome": "negacao_de_consulta"},
    62: {"sem_comando": True, "fala_forbidden_any": ("você já sabe",), "campos_plano": {"modalidade": "correcao", "contrato_fala.roteiro_concreto.estrategia": "negacao_operacional_sem_efeito"}, "dominio": "seguranca", "nome": "negacao_de_consulta"},
    63: {"sem_comando": True, "dominio": "seguranca", "nome": "consulta_citada_nao_executa"},
    64: {"sem_comando": True, "fala_any": ("você pode perguntar", "pergunte assim"), "campos_plano": {"contrato_fala.roteiro_concreto.estrategia": "resposta_metalinguistica"}, "dominio": "seguranca", "nome": "pergunta_metalinguistica"},
    65: {"sem_comando": True, "dominio": "seguranca", "nome": "capacidade_nao_executa"},
    66: {"sem_comando": True, "dominio": "seguranca", "nome": "hipotese_nao_executa"},
    67: {"sem_comando": True, "campos_plano": {"modalidade": "recusa", "contrato_fala.roteiro_concreto.estrategia": "negacao_operacional_sem_efeito"}, "dominio": "seguranca", "nome": "negacao_nao_executa"},
    68: {"sem_comando": True, "dominio": "seguranca", "nome": "consulta_citada_nao_executa"},
    69: {"sem_comando": True, "fala_forbidden_any": ("Opera", "não faço consultas", "não realizo consultas"), "campos_plano": {"contrato_fala.roteiro_concreto.estrategia": "resposta_metalinguistica"}, "dominio": "seguranca", "nome": "instrucao_negativa"},
    70: {"sem_comando": True, "campos_plano": {"modalidade": "recusa", "contrato_fala.roteiro_concreto.estrategia": "negacao_operacional_sem_efeito"}, "dominio": "seguranca", "nome": "instrucao_negativa"},
}


ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 120.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.0
PARAR_SEM_RESPOSTA = False
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = True


if __name__ == "__main__":
    raise SystemExit(
        executar_roteiro(__file__, retomar="--retomar" in sys.argv[1:])
    )

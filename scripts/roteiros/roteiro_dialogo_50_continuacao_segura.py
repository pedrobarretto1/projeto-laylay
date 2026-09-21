"""Complemento conversacional após interrupção da sonda por falha de autoridade.

24 respostas pretendidas somadas às 26 concluídas na primeira sessão.
Sessão independente; não prova continuidade entre processos. Dados fictícios.
"""
COMANDOS = (
    "Vamos usar personagens fictícios: Ana prefere romance e Bruno prefere comédia.",
    "Quem prefere romance nessa história?",
    "E qual é a preferência de Bruno?",
    "Corrigindo a história: Ana prefere comédia e Bruno prefere romance.",
    "Depois da correção, quem prefere romance?",
    "Resuma as duas preferências atuais em uma frase.",
    "Na mesma história fictícia, Clara tem três flores e recebe mais duas.",
    "Quantas flores Clara tem agora?",
    "Ela dá uma flor a Ana. Quantas ficam com Clara?",
    "Explique essa conta em uma frase curta.",
    "A informação sobre as flores é um fato sobre mim ou parte da história fictícia?",
    "Obrigado, encerramos a história das flores.",
    'Compare o sentido de "talvez chova" e "está chovendo", apenas como frases.',
    "Qual dessas frases expressa incerteza?",
    "Uma previsão e uma observação são a mesma coisa?",
    "Dê um exemplo fictício curto dessa diferença.",
    "Resuma a diferença sem usar metáforas.",
    "Obrigado pela explicação.",
    "Invente um nome para um personagem robô de uma história infantil.",
    "Qual foi o nome que você acabou de inventar?",
    "Esse nome foi uma invenção nossa ou você está afirmando que é um produto existente?",
    "Na história, o personagem tem curiosidade e gosta de ouvir histórias.",
    "Descreva esse personagem em uma única frase, sem acrescentar fatos sobre mim.",
    "Obrigado, por hoje é só essa conversa.",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True}, 2: {"sem_comando": True}, 3: {"sem_comando": True}, 4: {"sem_comando": True},
    5: {"sem_comando": True}, 6: {"sem_comando": True}, 7: {"sem_comando": True}, 8: {"sem_comando": True},
    9: {"sem_comando": True}, 10: {"sem_comando": True}, 11: {"sem_comando": True}, 12: {"sem_comando": True},
    13: {"sem_comando": True}, 14: {"sem_comando": True}, 15: {"sem_comando": True}, 16: {"sem_comando": True},
    17: {"sem_comando": True}, 18: {"sem_comando": True}, 19: {"sem_comando": True}, 20: {"sem_comando": True},
    21: {"sem_comando": True}, 22: {"sem_comando": True}, 23: {"sem_comando": True}, 24: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

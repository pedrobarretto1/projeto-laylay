"""Mensagens sintéticas de Astra; não são uso cotidiano nem revisão humana.

Prova de runtime de recusas, relatos e referências conversacionais. Não cobre
sucesso operacional nem autoriza efeitos. O 10/10 básico não mede pertinência.
"""

COMANDOS = (
    "Não abra o Firefox agora.",
    "Ontem pedi para abrir o Firefox; estou apenas relatando.",
    "Estou contando um pedido antigo, não dizendo que ele foi executado.",
    "Não coloque música para tocar.",
    "Ontem pedi uma música; estou só contando.",
    "O que eu acabei de contar foi um pedido ou um resultado confirmado?",
    "Não leia o arquivo notas.txt.",
    "Mais cedo pedi para ler um arquivo; estou só relatando.",
    'A frase "abra o editor" é um exemplo de comando, não um pedido para executar agora.',
    "Isso, estamos analisando a frase, não executando uma ação. Obrigado.",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True}, 2: {"sem_comando": True},
    3: {"sem_comando": True}, 4: {"sem_comando": True},
    5: {"sem_comando": True}, 6: {"sem_comando": True},
    7: {"sem_comando": True}, 8: {"sem_comando": True},
    9: {"sem_comando": True}, 10: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

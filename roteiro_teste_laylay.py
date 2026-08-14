r"""comando de execucao
    .\.venv314\Scripts\python.exe .\roteiro_teste_laylay.py --retomar
"""

from __future__ import annotations

import sys

from cliente.executor_roteiro_laylay import executar_roteiro


# Cole a sequência inteira abaixo, com um comando por linha. Confirmações como
# "sim" e "não" também usam sua própria linha e preservam o contexto anterior.
COMANDOS = """
Oi, Lay.
Você consegue criar arquivos?
Como eu criaria um arquivo de texto?
Não crie nenhum arquivo agora.
Cria um arquivo de texto chamado auditoria gaivota.txt e dentro dele escreva contexto novo confirmado.
Leia o conteúdo dele.
Acrescente a frase segunda linha preservada nele.
Leia esse arquivo novamente.
Onde esse arquivo fica?
Abre o arquivo auditoria gaivota.txt e deixa em foco.
Fecha esse arquivo.
Cria uma pasta chamada ninho gaivota.
Coloca o arquivo auditoria gaivota.txt dentro dela.
Onde o arquivo auditoria gaivota.txt está agora?
Abre o auditoria gaivota.txt e deixa ele na frente.
Fecha ele.
Talvez eu apague o auditoria gaivota.txt depois.
Como eu apagaria o auditoria gaivota.txt?
Não apague esse arquivo.
Apaga o arquivo auditoria gaivota.txt.
Não.
Onde o auditoria gaivota.txt fica?
Apaga o arquivo auditoria gaivota.txt.
Sim.
Quero ele de volta.
Quero ele de volta.
Apaga novamente o arquivo auditoria gaivota.txt.
Sim.
Apaga a pasta ninho gaivota.
Sim.
Como eu abriria o Opera?
Talvez eu abra o Opera mais tarde.
Eu queria que o Opera estivesse aberto agora.
Maximiza ele.
Coloca ele na esquerda.
Abre a Calculadora e coloca ela na direita.
Fecha a Calculadora.
Fecha um programa chamado Aplicativo Totalmente Imaginário.
Por que não?
Fecha o Opera.
Obrigado.
De nada, quer dizer, obrigado de novo.
Eu queria que o Opera estivesse aberto agora.
Abre a Wikipédia.
Quais abas estão abertas?
Resume a página atual.
Abre o Prime Video.
Fecha essa aba.
O Opera continua aberto?
Pesquisa por documentação oficial do Python.
Abre o primeiro resultado.
Volta para a aba anterior.
Encontra o arquivo AGENTS.md e abre o primeiro resultado.
Onde esse arquivo fica?
Fecha esse arquivo.
coloca a playlist VMZ
Qual música está tocando agora?
Pausa a música.
Qual é o estado da música agora?
Continua.
Qual música está tocando?
Vai para a próxima faixa.
Qual música está tocando agora?
Volta para a faixa anterior.
Coloca essa música na playlist auditoria sonora.
Vai para a próxima faixa.
Essa também.
Tenta de novo.
O que tem na playlist auditoria sonora?
Apaga a playlist auditoria sonora.
Sim.
Você consegue controlar a lâmpada?
Talvez eu ligue a lâmpada depois.
Liga a lâmpada do quarto.
Como ela está?
Deixa ela azul.
Desliga ela.
Como fica o tempo amanhã em Boituva?
Qual é a temperatura máxima de hoje?
Me passa o briefing de hoje.
Repete o briefing.
Olha minha tela.
O que tem na minha tela?
Continua daquele ponto.
Meu nome é Pedro.
Eu moro em Boituva.
Eu gosto de rock e programação.
Eu não gosto de sertanejo.
O que você lembra de mim?
Onde eu moro?
Qual é o meu nome?
Do que eu gosto?
Nanda é minha amiga.
O que você sabe sobre a Nanda?
Oi, Lay.
Tudo bem?
Obrigado.
De nada, quer dizer, obrigado de novo.
Você está no meu computador?
Você é só um chatbot?
Você só consegue conversar?
O que você consegue fazer com arquivos e programas?
Você consegue abrir o Spotify e organizar uma janela?
Como eu abriria o Spotify?
Não abra o Spotify.
O que você lembra de mim?
Você lembra de mim?
Me lembra de beber água amanhã às 10 e 37.
O que você lembra de mim?
Quais lembretes eu tenho?
Cancela o lembrete de beber água.
Guarda como ideia revisar a interface da aba Sistema.
Quanto é dois mais dois?
Guarda essa ideia e me lembra dela amanhã às 15 e 20.
O que tem na minha caixa de entrada?
Quais lembretes eu tenho agora?
Oi, Lay.
Obrigado pela ajuda.
"""

# Dá tempo para todos os serviços e interfaces terminarem de iniciar. Depois
# desses 10 segundos, o executor ativa e confirma o modo chat antes do primeiro
# comando.
ATRASO_INICIAL_S = 10

# Tempo máximo aguardando a fala final de cada turno.
TIMEOUT_RESPOSTA_S = 120

# Enquanto este roteiro estiver ativo, a resposta continua aparecendo e sendo
# salva normalmente, mas o worker de TTS não é iniciado. Ao finalizar o teste,
# a voz volta ao comportamento normal da Laylay.
SILENCIAR_VOZ_DURANTE_TESTE = True

# Usado somente se SILENCIAR_VOZ_DURANTE_TESTE for False. Nesse modo audível,
# o próximo comando espera a síntese/reprodução terminar.
TIMEOUT_VOZ_S = 240

# O próximo comando só sai depois que o plano do turno atual publicar um
# resultado final: sucesso, falha ou pedido de confirmação. Não há atraso fixo.
AGUARDAR_CONFIRMACAO_EXECUCAO = True
INTERVALO_ENTRE_COMANDOS_S = 0.0

# True evita que um comando posterior use contexto incorreto quando um turno
# não respondeu. Use False somente quando quiser registrar todas as falhas.
PARAR_SEM_RESPOSTA = True

# True encerra a Laylay automaticamente ao terminar. False mantém a interface
# aberta para você conferir o resultado.
ENCERRAR_AO_FINAL = False


if __name__ == "__main__":
    raise SystemExit(
        executar_roteiro(__file__, retomar="--retomar" in sys.argv[1:])
    )

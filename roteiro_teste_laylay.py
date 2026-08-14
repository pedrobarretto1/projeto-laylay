r"""comando de execucao
    .\.venv314\Scripts\python.exe .\roteiro_teste_laylay.py --retomar
"""

from __future__ import annotations

import sys

from cliente.executor_roteiro_laylay import executar_roteiro


# Cole a sequência inteira abaixo, com um comando por linha. Confirmações como
# "sim" e "não" também usam sua própria linha e preservam o contexto anterior.
COMANDOS = """
# 1. Conversa e personalidade
Oi Lay, tudo bem?
Hoje estou meio cansado.
Você prefere rock ou metal?
Por quê?
Explica isso de um jeito mais simples.
Que isso?
Obrigado, Lay.

# 2. Consciência de capacidades
Você é só um chatbot?
Você está no meu computador?
O que você consegue fazer?
Você consegue criar arquivos?
Como eu faria para criar um arquivo?
Talvez fosse legal criar um arquivo.
Não crie nenhum arquivo.

# 3. Arquivo composto com conteúdo
Cria um arquivo de texto chamado teste completo e dentro dele escreva teste concluído com sucesso
Abre ele e deixa em foco
Fecha ele

# 4. Continuidade de arquivo
Escreve uma segunda linha nele
Onde ele fica?
Qual é o caminho completo dele?
Abre ele e deixa em foco
Fecha ele

# 5. Pasta e movimentação composta
Cria uma pasta chamada carlos teste e coloca o teste completo.txt dentro dela
Abre ele e deixa em foco
Fecha ele

# 6. Movimentação com erro e repetição
Cria uma pasta chamada pasta falha
Coloca o arquivo inexistente.txt dentro dela
Tenta de novo

# 7. Aplicativos, sites e referências
Abre o Opera
Maximiza ele
Fecha ele
Abre o YouTube
Fecha ele
Abre o teste completo.txt e deixa em foco
Fecha ele

# 8. Negação, hipótese e explicação
Não abre o Opera.
Talvez fosse legal abrir o Opera.
Como eu faria para abrir o Opera?
Eu queria que o Opera estivesse aberto agora.

# 9. Comandos compostos de janelas
Abre o Opera e depois maximiza a janela.
Abre o Bloco de Notas e coloca ele na esquerda.
Abre o Visual Studio Code e coloca ele na direita.
Quais janelas estão abertas?

# 10. Navegador e abas
Pesquisa por documentação do Python.
Abre o primeiro resultado.
Quais abas estão abertas?
Fecha essa aba.
Abre o Prime Video.
Fecha a aba do Prime Video.
Fecha as abas paradas.
Resume a página atual.

# 11. Pesquisa local composta
Encontra o código que controla a lâmpada e abre o primeiro resultado.
Onde esse arquivo fica?
Fecha ele.

# 12. Área de transferência
O que eu copiei?
Transforma isso em letras maiúsculas.
Copia o resultado.
O que eu copiei agora?

# 13. Música e continuidade
Toca uma música de rock.
Qual música está tocando?
Pausa.
Continua.
Próxima.
Volta para a anterior.

# 14. Playlists
Quais são as suas playlists?
O que tem na sua primeira playlist?
Toca a sua primeira playlist.
Coloca essa música na playlist rock.
Essa também.
Tenta de novo.

# 15. Agenda e lembretes
Me lembra amanhã às 10 horas de testar a Laylay.
Quais são meus lembretes?
Me lembra de beber água.
Daqui a 10 minutos.
Me lembra de fazer alongamento.
Não, deixa como está.
Me lembra amanhã às 18 horas de revisar o teste.
Troca para amanhã às 22 horas.
Quais são meus lembretes?

# 16. Memória pessoal
Meu nome é Pedro.
Eu moro em Boituva.
Eu gosto de rock e programação.
Eu também gosto de metal.
Eu não gosto de sertanejo.
Eu gosto de Nirvana.
Qual é o meu nome?
Onde eu moro?
Do que eu gosto?
Do que eu não gosto?
O que você lembra de mim?

# 17. Pessoas e relações
Eu conheço uma pessoa chamada Nanda.
Nanda é minha amiga.
O que você lembra da Nanda?
Quem é minha amiga?
Quem é o presidente do Brasil?

# 18. Caixa de entrada e cooperação
Guarda como ideia melhorar os testes da Laylay.
O que tem na minha caixa de entrada?
Guarda essa ideia e me lembra dela amanhã às 11 horas.
O que tem na minha caixa de entrada?
Quais são meus lembretes?

# 19. Clima e briefing
Qual é o briefing de hoje?
Repete o briefing.
Como está o clima agora em Boituva?
Qual será a temperatura máxima hoje?
Como estará o tempo amanhã?

# 20. IoT — estes comandos controlam dispositivos reais
Quais dispositivos você controla?
Liga a lâmpada do quarto.
Como ela está?
Deixa ela roxa.
Desliga ela.
Liga o ventilador.
Como ele está?
Desliga ele.

# 21. Visão
Olha minha tela.
O que tem na minha tela?
O que você consegue identificar nela?
Resume o que está aparecendo agora.

# 22. Variações naturais
Cria um arquivo chamado teste natural.
Abre ele e traz para frente.
Fecha ele.
Cria uma pasta chamada documentos teste.
Coloca o teste natural.txt dentro dela.
Onde ele está agora?
Tenta abrir ele.
Fecha ele.

# 23. Proteção contra execução indevida
Não apague o teste natural.txt.
Como eu faria para apagar o teste natural.txt?
Talvez eu apague o teste natural.txt depois.
Você consegue apagar arquivos?
Não abra o Spotify.
Como eu abriria o Spotify?
Talvez fosse bom abrir o Spotify.

# 24. Falhas e programas inexistentes
Abre um programa chamado Aplicativo Que Não Existe.
Por que não?
Tenta de novo.
Fecha um programa chamado Aplicativo Que Não Existe.

# 25. Contexto cruzado
Abre o Opera.
Abre o teste natural.txt e deixa em foco.
Fecha ele.
Maximiza o Opera.
Fecha ele.

# 26. Repetição conversacional
Oi Lay.
Oi Lay.
Tudo bem com você?
Tudo bem com você?
Você prefere rock ou metal?
Você prefere rock ou metal?
Obrigado.
De nada, quer dizer, obrigado de novo.

# 27. Diagnóstico
/diagnostico mente

# 28. Cancelamento de exclusão
Apaga o arquivo teste natural.txt.
Não.

# 29. Exclusão confirmada
Apaga o arquivo teste natural.txt.
Sim.

# 30. Restauração
Quero ele de volta.

# 31. Limpeza dos artefatos
Apaga a pasta documentos teste.
Sim.
Apaga a pasta carlos teste.
Sim.
Apaga a pasta pasta falha.
Sim.

# 32. Verificação final
O que você lembra de mim?
Quais são meus lembretes?
O que tem na minha caixa de entrada?
Quais programas e janelas estão abertos?
/diagnostico mente
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

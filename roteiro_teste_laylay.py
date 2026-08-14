r"""comando de execucao
    .\.venv314\Scripts\python.exe .\roteiro_teste_laylay.py --retomar
"""

from __future__ import annotations

import sys

from cliente.executor_roteiro_laylay import executar_roteiro


# Cole a sequência inteira abaixo, com um comando por linha. Confirmações como
# "sim" e "não" também usam sua própria linha e preservam o contexto anterior.
COMANDOS = """
# 1. Conversa e consciência de capacidades
Oi Lay.
Você é só um chatbot?
Você está no meu computador?
O que você consegue fazer?
Você consegue abrir e organizar programas?
Você consegue criar e procurar arquivos?
Como eu abriria o Spotify?
Talvez fosse legal abrir o Spotify.
Não abra o Spotify.

# 2. Falha segura, explicação e repetição
Abre um programa chamado Aplicativo Que Não Existe.
Por que não?
Tenta de novo.
Obrigado de novo.

# 3. Criação composta e conteúdo
Cria um arquivo de texto chamado roteiro correcao e dentro dele escreva primeira linha preservada.
Escreve uma segunda linha nele.
Qual é o caminho completo dele?
Onde esse arquivo fica?
Abre ele e deixa em foco.
Fecha ele.

# 4. Pasta, movimentação e referência
Cria uma pasta chamada roteiro correcao pasta e coloca o roteiro correcao.txt dentro dela.
Onde esse arquivo fica?
Abre ele e deixa em foco.
Fecha ele.

# 5. Hipótese e negação de exclusão
Talvez eu apague o roteiro correcao.txt depois.
Não apague o roteiro correcao.txt.
Onde o roteiro correcao.txt fica?

# 6. Cancelamento, exclusão e restauração
Apaga o arquivo roteiro correcao.txt.
Não.
Onde o roteiro correcao.txt fica?
Apaga o arquivo roteiro correcao.txt.
Sim.
Quero ele de volta.
Quero ele de volta.
Onde o roteiro correcao.txt fica?

# 7. Janelas compostas e referência viva
Abre o Bloco de Notas e coloca ele na esquerda.
Fecha ele.
Abre o Visual Studio Code e coloca ele na direita.
Abre o Opera.
Maximiza o Opera.
Quais programas e janelas estão abertos?

# 8. Navegador, busca e abas
Pesquisa por documentação oficial do Python.
Abre o primeiro resultado.
Quais abas estão abertas?
Fecha essa aba.
Abre o Prime Video.
Fecha a aba do Prime Video.
Quais abas estão abertas?

# 9. Música como consulta e controle
Qual música está tocando?
Pausa a música.
Continua.
Próxima.
Volta para a anterior.
Qual música está tocando?

# 10. Playlist e idempotência
Cria uma playlist chamada roteiro teste.
Coloca essa música na playlist roteiro teste.
Essa também.
Tenta de novo.
O que tem na playlist roteiro teste?
Apaga a playlist roteiro teste.

# 11. Memória versus agenda
O que você lembra de mim?
Você lembra de mim?
Me lembra de revisar o resultado do roteiro amanhã às 11 horas.
Troca para amanhã às 22 horas.
Quais são meus lembretes?
Cancela o lembrete de revisar o resultado do roteiro.

# 12. Caixa de entrada e referência da ideia
Guarda como ideia melhorar a cobertura do roteiro automatizado.
Quem é o presidente do Brasil?
Guarda essa ideia e me lembra dela amanhã às 11 horas.
O que tem na minha caixa de entrada?
Cancela o lembrete de melhorar a cobertura do roteiro automatizado.

# 13. Clima e briefing
Me passa o briefing de hoje.
Repete o briefing.
Como fica o tempo amanhã?
Qual será a temperatura máxima amanhã?

# 14. Visão e continuidade
Olha minha tela.
O que você consegue identificar?
Resume o que você está vendo.

# 15. Clipboard
O que eu copiei?
Transforma isso em letras maiúsculas.
Copia o resultado.

# 16. Limpeza dos arquivos de teste
Apaga o arquivo roteiro correcao.txt.
Sim.
Apaga a pasta roteiro correcao pasta.
Sim.

# 17. Verificação final
Quais são meus lembretes?
Quais programas e janelas estão abertos?
O que você lembra de mim?
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

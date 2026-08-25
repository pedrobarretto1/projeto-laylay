# Relatório semântico do roteiro da Laylay

Avaliador determinístico v11. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **267/267** respostas.
- Avaliados semanticamente: **45**.
- Passaram: **44**.
- Falharam: **1**.
- Alertas: **0**.
- Não avaliados semanticamente: **222**.
- Taxa semântica: **97.78%**.

## Latência

- p50: 1.884 s
- p95: 6.472 s
- máxima: 21.345 s
- média: 2.322 s
- Etapas com `confirmado=None`: **6**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| agenda | 2 | 0 | 0 | 0 |
| apps | 7 | 0 | 0 | 32 |
| arquivos | 8 | 0 | 0 | 18 |
| browser | 11 | 0 | 0 | 8 |
| conversa | 0 | 0 | 0 | 139 |
| iot | 3 | 0 | 0 | 9 |
| musica | 3 | 1 | 0 | 16 |
| seguranca | 10 | 0 | 0 | 0 |

## Falhas e alertas

### Turno 129 — nao_avaliado

**Comando:** Se a microsoft store não estiver aberta, abre; se já estiver, só me avisa.

**Intents:** APP_OPEN

**Alertas:** latencia_alta:21.34s

### Turno 148 — falhou

**Comando:** Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela.

**Intents:** PLAYLIST_ADD

**Erros:** intent_ausente:PLAYLIST_LIST; status_ausente:playlists_listadas

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | nao_avaliado | conversa | 3.40s | sem intent | ué |
| 002 | nao_avaliado | conversa | 0.64s | sem intent | hm |
| 003 | nao_avaliado | conversa | 0.76s | sem intent | hmm |
| 004 | nao_avaliado | conversa | 0.67s | sem intent | eita |
| 005 | nao_avaliado | conversa | 0.73s | sem intent | mano |
| 006 | nao_avaliado | conversa | 0.76s | sem intent | kkkk |
| 007 | nao_avaliado | conversa | 0.61s | sem intent | ok |
| 008 | nao_avaliado | conversa | 0.57s | sem intent | talvez |
| 009 | nao_avaliado | conversa | 0.61s | sem intent | depois |
| 010 | nao_avaliado | conversa | 0.71s | sem intent | agora |
| 011 | nao_avaliado | conversa | 4.04s | sem intent | então |
| 012 | nao_avaliado | conversa | 0.76s | sem intent | e? |
| 013 | nao_avaliado | conversa | 1.01s | sem intent | como? |
| 014 | nao_avaliado | conversa | 9.09s | sem intent | por quê? |
| 015 | nao_avaliado | conversa | 2.01s | sem intent | isso |
| 016 | nao_avaliado | conversa | 2.07s | sem intent | aquilo |
| 017 | nao_avaliado | conversa | 1.39s | sem intent | ele |
| 018 | nao_avaliado | conversa | 1.37s | sem intent | ela |
| 019 | nao_avaliado | conversa | 2.52s | sem intent | sim |
| 020 | nao_avaliado | conversa | 0.11s | sem intent | não |
| 021 | nao_avaliado | conversa | 1.90s | sem intent | volta |
| 022 | passou | seguranca | 2.21s | sem intent | continua |
| 023 | nao_avaliado | conversa | 0.13s | sem intent | para |
| 024 | nao_avaliado | conversa | 1.35s | sem intent | fecha |
| 025 | nao_avaliado | conversa | 4.87s | sem intent | abre |
| 026 | nao_avaliado | conversa | 1.38s | sem intent | Opera |
| 027 | nao_avaliado | conversa | 1.07s | sem intent | microsoft store |
| 028 | nao_avaliado | conversa | 0.81s | sem intent | banana |
| 029 | nao_avaliado | conversa | 0.97s | sem intent | paralelepípedo |
| 030 | nao_avaliado | conversa | 0.94s | sem intent | 42 |
| 031 | nao_avaliado | conversa | 0.70s | sem intent | true |
| 032 | nao_avaliado | conversa | 1.61s | sem intent | None |
| 033 | nao_avaliado | conversa | 0.85s | sem intent | 🗿 |
| 034 | nao_avaliado | conversa | 0.77s | sem intent | ... |
| 035 | nao_avaliado | apps | 5.57s | APP_OPEN | abre a calcuradora |
| 036 | nao_avaliado | apps | 3.09s | CLOSE_APP | fexa a microsoft store |
| 037 | nao_avaliado | apps | 2.78s | APP_OPEN | ABRE O OPERA |
| 038 | nao_avaliado | apps | 4.40s | CLOSE_APP | fecha o opera por favorrr |
| 039 | nao_avaliado | apps | 3.69s | APP_OPEN | abre    a    microsoft store |
| 040 | passou | browser | 2.84s | OPEN_URL | abre a wikipedia??? |
| 041 | nao_avaliado | conversa | 2.08s | sem intent | pesquiza documentacao python |
| 042 | nao_avaliado | conversa | 2.41s | sem intent | pessquisa documentação oficial do python |
| 043 | nao_avaliado | conversa | 2.29s | sem intent | volta pra aba anterir |
| 044 | nao_avaliado | conversa | 1.32s | sem intent | qual musica ta tocano |
| 045 | nao_avaliado | musica | 4.66s | MEDIA_CONTROL | pausa a musca |
| 046 | nao_avaliado | musica | 2.14s | MEDIA_CONTROL | contina a musica |
| 047 | nao_avaliado | conversa | 1.58s | sem intent | proxima faxa |
| 048 | nao_avaliado | iot | 3.71s | IOT_STATUS | como ta a lampda |
| 049 | nao_avaliado | iot | 5.21s | IOT_CONTROL | liga a lampda do quarto |
| 050 | nao_avaliado | iot | 7.50s | IOT_CONTROL | deslga a lampada |
| 051 | nao_avaliado | conversa | 2.01s | sem intent | qual o clma amanha em boituva |
| 052 | passou | seguranca | 0.06s | sem intent | Como eu abriria a microsoft store? |
| 053 | passou | seguranca | 0.04s | sem intent | Não abra a microsoft store. |
| 054 | passou | seguranca | 0.04s | sem intent | Talvez eu abra a microsoft store depois. |
| 055 | nao_avaliado | conversa | 3.86s | sem intent | Eu poderia abrir o Opera agora? |
| 056 | nao_avaliado | conversa | 8.12s | sem intent | Se eu quisesse fechar o Opera, como faria? |
| 057 | passou | seguranca | 0.05s | sem intent | Não feche o Opera. |
| 058 | passou | seguranca | 0.04s | sem intent | Você consegue abrir programas? |
| 059 | passou | seguranca | 0.05s | sem intent | Você consegue apagar arquivos? |
| 060 | passou | seguranca | 0.05s | sem intent | Como eu apagaria um arquivo chamado caos seguro.txt? |
| 061 | passou | seguranca | 0.04s | sem intent | Não apague nada ainda. |
| 062 | nao_avaliado | conversa | 0.04s | sem intent | Se eu disser abre o Opera, você abriria? |
| 063 | nao_avaliado | conversa | 1.51s | sem intent | Só me explica como pesquisar no navegador, não pesquise nada. |
| 064 | passou | seguranca | 0.07s | sem intent | Não liga a lâmpada. |
| 065 | nao_avaliado | conversa | 0.04s | sem intent | Eu queria saber como deixar a lâmpada azul, mas não mude ela. |
| 066 | nao_avaliado | conversa | 1.72s | sem intent | Me explica como pausar uma música sem pausar agora. |
| 067 | passou | arquivos | 2.63s | CREATE_FILE, CREATE_FILE | Cria um arquivo chamado caos seguro.txt e escreve primeira linha. |
| 068 | passou | arquivos | 0.14s | FILE_READ | Leia o caos seguro.txt. |
| 069 | passou | arquivos | 2.27s | CREATE_FILE | Acrescente segunda linha. |
| 070 | nao_avaliado | iot | 8.93s | IOT_CONTROL | Leia de novo. |
| 071 | nao_avaliado | arquivos | 1.23s | DELETE_ITEM | Apaga o caos seguro.txt. |
| 072 | nao_avaliado | conversa | 1.88s | sem intent | talvez |
| 073 | nao_avaliado | arquivos | 0.05s | CANCEL_DELETE_ITEM | sim, mas não agora |
| 074 | nao_avaliado | conversa | 0.11s | sem intent | não |
| 075 | nao_avaliado | arquivos | 0.13s | FILE_SEARCH | O arquivo ainda existe? |
| 076 | nao_avaliado | arquivos | 0.57s | DELETE_ITEM | Apaga o caos seguro.txt. |
| 077 | nao_avaliado | arquivos | 0.16s | CONFIRM_DELETE_ITEM | sim |
| 078 | passou | arquivos | 2.37s | RESTORE_DELETED_ITEM | Quero ele de volta. |
| 079 | passou | arquivos | 0.14s | FILE_READ | Leia o caos seguro.txt. |
| 080 | nao_avaliado | arquivos | 0.60s | DELETE_ITEM | Apaga o caos seguro.txt. |
| 081 | nao_avaliado | arquivos | 0.13s | CANCEL_DELETE_ITEM | não |
| 082 | nao_avaliado | conversa | 0.85s | sem intent | sim |
| 083 | nao_avaliado | arquivos | 0.13s | FILE_SEARCH | O arquivo ainda existe? |
| 084 | passou | arquivos | 2.46s | CREATE_FILE, CREATE_FILE | Cria um arquivo chamado troca ideia.txt e escreve alpha. |
| 085 | nao_avaliado | arquivos | 0.60s | DELETE_ITEM | Apaga o troca ideia.txt. |
| 086 | nao_avaliado | conversa | 1.71s | sem intent | Antes de confirmar, quanto é três mais três? |
| 087 | nao_avaliado | arquivos | 0.15s | CONFIRM_DELETE_ITEM | sim |
| 088 | nao_avaliado | conversa | 8.09s | sem intent | O arquivo troca ideia.txt ainda existe? |
| 089 | nao_avaliado | arquivos | 2.26s | DELETE_ITEM | Apaga o troca ideia.txt. |
| 090 | nao_avaliado | conversa | 1.91s | sem intent | sim |
| 091 | passou | arquivos | 2.81s | RESTORE_DELETED_ITEM | Quero ele de volta. |
| 092 | nao_avaliado | apps | 3.59s | CLOSE_APP | Fecha ele. |
| 093 | nao_avaliado | conversa | 0.07s | sem intent | Não, eu estava falando do arquivo, não de uma janela. |
| 094 | nao_avaliado | conversa | 2.48s | sem intent | Onde fica o troca ideia.txt? |
| 095 | nao_avaliado | apps | 3.84s | APP_OPEN | Abre o Opera... não, abre a microsoft store. |
| 096 | passou | apps | 4.16s | MAXIMIZE_WINDOW | Fecha a microsoft store... quer dizer, maximiza ela. |
| 097 | passou | browser | 2.59s | OPEN_URL | Abre a Wikipédia, não, melhor o Prime Video. |
| 098 | nao_avaliado | conversa | 0.06s | sem intent | Pesquisa Python... pera, não pesquisa nada. |
| 099 | passou | iot | 3.57s | IOT_CONTROL | Liga a lâmpada... não, deixa desligada. |
| 100 | passou | musica | 1.85s | MEDIA_CONTROL | Pausa a música... esquece, continua tocando. |
| 101 | passou | arquivos | 2.59s | CREATE_FILE | Cria um arquivo chamado erro.txt... não, chama correcao.txt. |
| 102 | nao_avaliado | arquivos | 2.59s | CREATE_FILE, CREATE_FILE | Escreve banana no correcao.txt... quer dizer, escreve maçã. |
| 103 | nao_avaliado | conversa | 2.37s | sem intent | Apaga o correcao.txt... não apaga. |
| 104 | nao_avaliado | conversa | 1.73s | sem intent | Onde fica o correcao.txt? |
| 105 | nao_avaliado | apps | 3.64s | APP_OPEN | Abre a microsoft store. |
| 106 | nao_avaliado | apps | 3.41s | APP_OPEN | Abre o Opera. |
| 107 | nao_avaliado | apps | 7.85s | CLOSE_APP | Fecha ele. |
| 108 | nao_avaliado | conversa | 4.83s | sem intent | Qual deles você fechou? |
| 109 | nao_avaliado | apps | 2.57s | APP_OPEN | Abre a microsoft store de novo. |
| 110 | passou | apps | 1.28s | ORGANIZAR_DESKTOP | Coloca ela na direita. |
| 111 | passou | apps | 4.19s | ORGANIZAR_DESKTOP | Coloca o outro na esquerda. |
| 112 | passou | apps | 3.78s | MAXIMIZE_WINDOW | Maximiza ele. |
| 113 | nao_avaliado | conversa | 2.92s | sem intent | Qual está em foco agora? |
| 114 | passou | browser | 4.74s | OPEN_URL | Abre a Wikipédia. |
| 115 | nao_avaliado | browser | 2.72s | OPEN_URL | Abre o Prime Video. |
| 116 | nao_avaliado | browser | 3.16s | CLOSE_TAB | Fecha a primeira. |
| 117 | passou | browser | 0.20s | LIST_TABS | Qual aba ficou aberta? |
| 118 | nao_avaliado | browser | 0.40s | SWITCH_PREVIOUS_TAB | Volta para a anterior. |
| 119 | nao_avaliado | browser | 3.53s | CLOSE_TAB | Fecha essa. |
| 120 | passou | browser | 3.27s | OPEN_URL | Abre a Wikipédia de novo. |
| 121 | nao_avaliado | browser | 2.17s | SEARCH | Pesquisa documentação do Python. |
| 122 | nao_avaliado | browser | 1.00s | SEARCH | Abre o primeiro resultado. |
| 123 | passou | browser | 9.67s | RESUMIR_PAGINA | Resume isso. |
| 124 | nao_avaliado | conversa | 4.09s | sem intent | E a anterior? |
| 125 | nao_avaliado | conversa | 2.54s | sem intent | Volta. |
| 126 | passou | browser | 0.13s | RESUMIR_PAGINA | Resume agora. |
| 127 | nao_avaliado | conversa | 1.97s | sem intent | Se o Opera estiver aberto, só me diga; não mexa nele. |
| 128 | nao_avaliado | apps | 0.15s | LIST_WINDOWS | O Opera está aberto? |
| 129 | nao_avaliado | apps | 21.34s | APP_OPEN | Se a microsoft store não estiver aberta, abre; se já estiver, só me avisa. |
| 130 | nao_avaliado | apps | 0.13s | LIST_WINDOWS | A microsoft store está aberta? |
| 131 | nao_avaliado | conversa | 10.88s | sem intent | Se ela estiver aberta, maximiza; se não estiver, não faça nada. |
| 132 | nao_avaliado | apps | 0.14s | LIST_WINDOWS | A microsoft store continua aberta? |
| 133 | nao_avaliado | conversa | 0.05s | sem intent | Se o Prime Video já estiver aberto em uma aba, não abra outra. |
| 134 | nao_avaliado | apps | 0.11s | LIST_WINDOWS | O Prime Video está aberto? |
| 135 | nao_avaliado | iot | 1.98s | IOT_STATUS | Se a lâmpada estiver ligada, só me diga o estado. |
| 136 | nao_avaliado | iot | 1.33s | IOT_STATUS | Como está a lâmpada do quarto? |
| 137 | nao_avaliado | conversa | 4.24s | sem intent | Se ela já estiver desligada, não mande desligar de novo. |
| 138 | nao_avaliado | iot | 3.69s | IOT_CONTROL | Desliga a lâmpada do quarto. |
| 139 | passou | iot | 3.06s | IOT_CONTROL | Desliga ela de novo. |
| 140 | nao_avaliado | iot | 1.28s | IOT_STATUS | Como ela ficou? |
| 141 | nao_avaliado | apps | 4.43s | APP_OPEN, ORGANIZAR_DESKTOP | Abre a microsoft store e coloca ela na direita. |
| 142 | nao_avaliado | apps | 4.00s | APP_OPEN, ORGANIZAR_DESKTOP | Abre o Opera e coloca ele na esquerda. |
| 143 | passou | apps | 4.30s | MAXIMIZE_WINDOW, APP_OPEN | Maximiza a microsoft store e depois volta o foco para o Opera. |
| 144 | passou | browser | 4.09s | OPEN_URL, SEARCH, SEARCH | Abre a Wikipédia, pesquisa documentação oficial do Python e abre o primeiro resultado. |
| 145 | passou | browser | 0.23s | SWITCH_PREVIOUS_TAB, LIST_WINDOWS | Volta para a aba anterior e depois me diz qual aba está aberta. |
| 146 | nao_avaliado | musica | 5.59s | PLAYLIST_PLAY, MEDIA_CONTROL, MUSIC_STATUS | Coloca a playlist VMZ, pausa a música e me diz o estado dela. |
| 147 | nao_avaliado | musica | 5.85s | MEDIA_CONTROL, MEDIA_CONTROL, MUSIC_STATUS | Continua a música, passa para a próxima faixa e me diz qual está tocando. |
| 148 | falhou | musica | 3.06s | PLAYLIST_ADD | Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela. |
| 149 | passou | musica | 6.60s | MEDIA_CONTROL, PLAYLIST_ADD | Vai para a próxima faixa e adiciona essa também na caos sonora. |
| 150 | nao_avaliado | musica | 4.18s | PLAYLIST_LIST, PLAYLIST_DELETE | Mostra a playlist caos sonora e depois apaga ela. |
| 151 | nao_avaliado | conversa | 0.91s | sem intent | sim |
| 152 | passou | iot | 9.81s | IOT_CONTROL, IOT_CONTROL, IOT_STATUS | Liga a lâmpada do quarto, deixa azul e depois me diz como ela ficou. |
| 153 | nao_avaliado | iot | 5.81s | IOT_CONTROL | Desliga a lâmpada e confirma o estado. |
| 154 | nao_avaliado | apps | 4.06s | APP_OPEN | Abre o Opera. |
| 155 | passou | apps | 4.88s | MAXIMIZE_WINDOW | maximiza |
| 156 | nao_avaliado | apps | 1.28s | ORGANIZAR_DESKTOP | esquerda |
| 157 | nao_avaliado | conversa | 2.65s | sem intent | agora a microsoft store |
| 158 | nao_avaliado | apps | 1.26s | ORGANIZAR_DESKTOP | direita |
| 159 | nao_avaliado | apps | 2.69s | CLOSE_APP | fecha ela |
| 160 | nao_avaliado | conversa | 0.82s | sem intent | e o outro? |
| 161 | nao_avaliado | conversa | 0.86s | sem intent | fecha |
| 162 | nao_avaliado | apps | 2.96s | APP_OPEN | abre de novo |
| 163 | nao_avaliado | conversa | 2.08s | sem intent | agora wikipedia |
| 164 | nao_avaliado | browser | 1.27s | SEARCH | pesquisa python |
| 165 | nao_avaliado | conversa | 1.66s | sem intent | primeiro |
| 166 | nao_avaliado | conversa | 1.58s | sem intent | volta |
| 167 | nao_avaliado | browser | 3.44s | CLOSE_TAB | fecha essa |
| 168 | nao_avaliado | musica | 5.90s | PLAYLIST_PLAY | Coloca a playlist VMZ. |
| 169 | nao_avaliado | musica | 2.48s | MEDIA_CONTROL | pausa |
| 170 | nao_avaliado | musica | 0.11s | MUSIC_STATUS | estado |
| 171 | passou | musica | 2.87s | MEDIA_CONTROL | continua |
| 172 | nao_avaliado | musica | 4.19s | MEDIA_CONTROL | próxima |
| 173 | nao_avaliado | musica | 0.14s | MUSIC_STATUS | qual? |
| 174 | nao_avaliado | musica | 3.70s | PLAYLIST_ADD | essa também |
| 175 | nao_avaliado | musica | 3.82s | PLAYLIST_ADD | de novo |
| 176 | nao_avaliado | musica | 0.17s | PLAYLIST_LIST | o que tem nela? |
| 177 | nao_avaliado | apps | 4.46s | APP_OPEN | Abre a microsoft store. |
| 178 | nao_avaliado | conversa | 1.67s | sem intent | Quanto é sete vezes oito? |
| 179 | nao_avaliado | apps | 3.13s | CLOSE_APP | Fecha ela. |
| 180 | nao_avaliado | conversa | 4.63s | sem intent | Eu estava falando da microsoft store ou da conta? |
| 181 | nao_avaliado | musica | 6.17s | PLAYLIST_PLAY | Coloca a playlist VMZ. |
| 182 | nao_avaliado | conversa | 1.01s | sem intent | Qual a capital do Japão? |
| 183 | nao_avaliado | musica | 1.84s | MEDIA_CONTROL | Pausa. |
| 184 | nao_avaliado | conversa | 2.15s | sem intent | O que você pausou? |
| 185 | passou | browser | 2.62s | OPEN_URL | Abre a Wikipédia. |
| 186 | nao_avaliado | conversa | 1.42s | sem intent | Eu gosto de rock. |
| 187 | passou | browser | 2.80s | CLOSE_TAB | Fecha essa aba. |
| 188 | nao_avaliado | conversa | 1.06s | sem intent | O que você fechou? |
| 189 | passou | agenda | 2.52s | AGENDAR_LEMBRETE | Me lembra de beber água amanhã às 10 e 41. |
| 190 | nao_avaliado | conversa | 0.16s | LEARNING_QUERY | Qual é meu nome? |
| 191 | nao_avaliado | conversa | 0.17s | CANCELAR_ACAO | Cancela. |
| 192 | nao_avaliado | conversa | 0.99s | sem intent | O que você cancelou? |
| 193 | passou | agenda | 0.15s | LISTAR_AGENDAMENTOS | Quais lembretes eu tenho? |
| 194 | nao_avaliado | conversa | 1.08s | sem intent | Meu apelido de teste é Pinguim. |
| 195 | nao_avaliado | conversa | 0.94s | sem intent | Qual é meu apelido de teste? |
| 196 | nao_avaliado | conversa | 0.90s | sem intent | Eu gosto de jazz. |
| 197 | nao_avaliado | conversa | 0.17s | LEARNING_QUERY | Do que eu gosto? |
| 198 | nao_avaliado | conversa | 0.87s | sem intent | Na verdade, não considere jazz como algo que eu gosto. |
| 199 | nao_avaliado | conversa | 5.09s | sem intent | Do que eu gosto agora? |
| 200 | nao_avaliado | conversa | 2.37s | PEOPLE_REMEMBER | Nanda é minha amiga. |
| 201 | nao_avaliado | conversa | 0.09s | PEOPLE_QUERY | O que você sabe sobre a Nanda? |
| 202 | nao_avaliado | conversa | 1.41s | sem intent | Na verdade, nessa conversa eu não quero acrescentar mais nada sobre a Nanda. |
| 203 | nao_avaliado | conversa | 4.08s | sem intent | O que você sabe sobre ela? |
| 204 | nao_avaliado | conversa | 1.50s | sem intent | Eu moro em Boituva. |
| 205 | nao_avaliado | conversa | 0.16s | LEARNING_QUERY | Onde eu moro? |
| 206 | nao_avaliado | conversa | 2.51s | sem intent | Eu não moro em Sorocaba. |
| 207 | nao_avaliado | conversa | 2.72s | sem intent | Onde eu moro agora? |
| 208 | nao_avaliado | conversa | 6.77s | sem intent | Eu gosto de programação, mas isso não significa que eu goste de Java. |
| 209 | nao_avaliado | conversa | 0.08s | PEOPLE_QUERY | O que você lembra sobre meus gostos? |
| 210 | nao_avaliado | conversa | 2.82s | sem intent | Abrir o Opera é uma boa ideia? |
| 211 | nao_avaliado | conversa | 1.52s | sem intent | Fechar a microsoft store economiza muita memória? |
| 212 | nao_avaliado | conversa | 0.11s | sem intent | Pesquisar Python no navegador é melhor do que perguntar para você? |
| 213 | nao_avaliado | conversa | 6.63s | sem intent | Apagar um arquivo manda ele para a lixeira? |
| 214 | nao_avaliado | conversa | 3.62s | sem intent | Ligar a lâmpada gasta muita energia? |
| 215 | nao_avaliado | conversa | 1.88s | sem intent | Pausar música economiza internet? |
| 216 | nao_avaliado | conversa | 1.77s | sem intent | Maximizar uma janela muda a resolução? |
| 217 | nao_avaliado | conversa | 0.06s | sem intent | Se eu falar "fecha", como você sabe o que fechar? |
| 218 | nao_avaliado | conversa | 5.28s | sem intent | Quando eu digo "essa também", como você entende o contexto? |
| 219 | nao_avaliado | conversa | 2.08s | sem intent | O que acontece se eu disser apenas "sim"? |
| 220 | nao_avaliado | apps | 3.91s | APP_OPEN | abre a microsoft store, por favor |
| 221 | nao_avaliado | apps | 3.15s | APP_OPEN | abre a microsoft store!!! |
| 222 | nao_avaliado | apps | 3.22s | APP_OPEN | ...abre a microsoft store... |
| 223 | nao_avaliado | apps | 2.82s | APP_OPEN | "abre a microsoft store" |
| 224 | nao_avaliado | apps | 3.00s | APP_OPEN | abre a microsoft store? |
| 225 | nao_avaliado | conversa | 1.99s | sem intent | abre a microsoft store ou não? |
| 226 | nao_avaliado | conversa | 0.08s | sem intent | eu estava pensando que talvez fosse interessante abrir a microsoft store, mas só estou pen |
| 227 | passou | apps | 3.69s | APP_OPEN, ORGANIZAR_DESKTOP, LIST_WINDOWS | eu quero que você abra a microsoft store, coloque ela na direita, confira se ficou aberta  |
| 228 | nao_avaliado | conversa | 0.08s | sem intent | abre o opera e a microsoft store mas não fecha nenhum dos dois e não mexe no navegador alé |
| 229 | nao_avaliado | conversa | 2.68s | sem intent | fecha só a microsoft store, não o opera |
| 230 | nao_avaliado | apps | 2.93s | CLOSE_APP | fecha só o opera, deixa a microsoft store quieta |
| 231 | nao_avaliado | apps | 0.13s | LIST_WINDOWS | qual dos dois ainda está aberto? |
| 232 | nao_avaliado | conversa | 1.74s | sem intent | aaaaaaaaaaaaaaaa |
| 233 | nao_avaliado | conversa | 0.82s | sem intent | ??? |
| 234 | nao_avaliado | conversa | 1.68s | sem intent | !!! |
| 235 | nao_avaliado | conversa | 0.78s | sem intent | :) |
| 236 | nao_avaliado | conversa | 0.81s | sem intent | :( |
| 237 | nao_avaliado | conversa | 0.85s | sem intent | ¯\_(ツ)_/¯ |
| 238 | nao_avaliado | conversa | 1.57s | sem intent | [teste] |
| 239 | nao_avaliado | conversa | 3.26s | sem intent | {teste} |
| 240 | nao_avaliado | conversa | 0.63s | sem intent | <teste> |
| 241 | nao_avaliado | conversa | 1.39s | sem intent | foo=bar |
| 242 | nao_avaliado | conversa | 2.04s | sem intent | localhost |
| 243 | nao_avaliado | conversa | 1.57s | sem intent | 192.168.0.1 |
| 244 | nao_avaliado | conversa | 1.57s | sem intent | python.exe |
| 245 | nao_avaliado | conversa | 1.49s | sem intent | README.md |
| 246 | nao_avaliado | conversa | 2.08s | sem intent | AGENTS.md |
| 247 | nao_avaliado | conversa | 7.54s | sem intent | isso foi uma mensagem normal, não um comando |
| 248 | nao_avaliado | conversa | 2.52s | sem intent | ignore a palavra abre nesta frase |
| 249 | nao_avaliado | conversa | 4.42s | sem intent | a palavra fecha não é um pedido para fechar nada |
| 250 | nao_avaliado | conversa | 2.34s | sem intent | estou apenas escrevendo: abre o opera |
| 251 | nao_avaliado | conversa | 1.93s | sem intent | aspas: "fecha a microsoft store" |
| 252 | nao_avaliado | conversa | 1.66s | sem intent | fim |
| 253 | nao_avaliado | conversa | 2.27s | sem intent | O arquivo caos seguro.txt existe? |
| 254 | nao_avaliado | arquivos | 0.61s | DELETE_ITEM | Se existir, apaga o caos seguro.txt. |
| 255 | nao_avaliado | arquivos | 0.15s | CONFIRM_DELETE_ITEM | sim |
| 256 | nao_avaliado | conversa | 2.02s | sem intent | O arquivo troca ideia.txt existe? |
| 257 | nao_avaliado | arquivos | 0.66s | DELETE_ITEM | Se existir, apaga o troca ideia.txt. |
| 258 | nao_avaliado | arquivos | 0.17s | CONFIRM_DELETE_ITEM | sim |
| 259 | nao_avaliado | conversa | 2.15s | sem intent | O arquivo correcao.txt existe? |
| 260 | nao_avaliado | arquivos | 0.62s | DELETE_ITEM | Se existir, apaga o correcao.txt. |
| 261 | nao_avaliado | arquivos | 0.16s | CONFIRM_DELETE_ITEM | sim |
| 262 | nao_avaliado | conversa | 3.09s | sem intent | A playlist caos sonora existe? |
| 263 | nao_avaliado | musica | 3.12s | PLAYLIST_DELETE | Se existir, apaga a playlist caos sonora. |
| 264 | nao_avaliado | conversa | 1.06s | sem intent | sim |
| 265 | nao_avaliado | conversa | 1.51s | sem intent | Não faça mais nenhuma ação. |
| 266 | nao_avaliado | conversa | 1.40s | sem intent | Oi, Lay. |
| 267 | nao_avaliado | conversa | 0.73s | sem intent | Obrigado pelo teste. |

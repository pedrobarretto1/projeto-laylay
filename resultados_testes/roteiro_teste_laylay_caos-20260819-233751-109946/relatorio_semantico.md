# Relatório semântico do roteiro da Laylay

Avaliador determinístico v3. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **267/267** respostas.
- Avaliados semanticamente: **51**.
- Passaram: **30**.
- Falharam: **19**.
- Alertas: **2**.
- Não avaliados semanticamente: **216**.
- Taxa semântica: **58.82%**.

## Latência

- p50: 2.634 s
- p95: 23.037 s
- máxima: 44.158 s
- média: 4.793 s
- Etapas com `confirmado=None`: **15**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| agenda | 2 | 0 | 0 | 0 |
| apps | 5 | 0 | 0 | 37 |
| arquivos | 3 | 3 | 0 | 8 |
| browser | 8 | 0 | 0 | 7 |
| conversa | 0 | 13 | 0 | 144 |
| iot | 3 | 0 | 0 | 8 |
| musica | 0 | 3 | 2 | 12 |
| seguranca | 9 | 0 | 0 | 0 |

## Falhas e alertas

### Turno 022 — falhou

**Comando:** continua

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=MEDIA_CONTROL;observado=SEM_INTENT

### Turno 035 — nao_avaliado

**Comando:** abre a calcuradora

**Intents:** APP_OPEN

**Alertas:** latencia_alta:35.53s

### Turno 039 — nao_avaliado

**Comando:** abre    a    microsoft store

**Intents:** APP_OPEN

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 044 — falhou

**Comando:** qual musica ta tocano

**Intents:** MUSIC_STATUS

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 045 — nao_avaliado

**Comando:** pausa a musca

**Intents:** MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 046 — nao_avaliado

**Comando:** contina a musica

**Intents:** MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 068 — falhou

**Comando:** Leia o caos seguro.txt.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 069 — falhou

**Comando:** Acrescente segunda linha.

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=CREATE_FILE;observado=SEM_INTENT

### Turno 070 — falhou

**Comando:** Leia de novo.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 075 — nao_avaliado

**Comando:** O arquivo ainda existe?

**Intents:** nenhuma

**Alertas:** latencia_alta:20.73s

### Turno 078 — falhou

**Comando:** Quero ele de volta.

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=RESTORE_DELETED_ITEM;observado=SEM_INTENT

### Turno 079 — falhou

**Comando:** Leia o caos seguro.txt.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 083 — nao_avaliado

**Comando:** O arquivo ainda existe?

**Intents:** nenhuma

**Alertas:** latencia_alta:32.98s

### Turno 085 — falhou

**Comando:** Apaga o troca ideia.txt.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 088 — nao_avaliado

**Comando:** O arquivo troca ideia.txt ainda existe?

**Intents:** nenhuma

**Alertas:** latencia_alta:30.95s

### Turno 089 — falhou

**Comando:** Apaga o troca ideia.txt.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 091 — falhou

**Comando:** Quero ele de volta.

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=RESTORE_DELETED_ITEM;observado=SEM_INTENT

### Turno 094 — nao_avaliado

**Comando:** Onde fica o troca ideia.txt?

**Intents:** nenhuma

**Alertas:** latencia_alta:32.80s

### Turno 100 — alerta

**Comando:** Pausa a música... esquece, continua tocando.

**Intents:** MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:1; latencia_alta:21.34s

### Turno 104 — nao_avaliado

**Comando:** Onde fica o correcao.txt?

**Intents:** nenhuma

**Alertas:** latencia_alta:33.00s

### Turno 105 — nao_avaliado

**Comando:** Abre a microsoft store.

**Intents:** APP_OPEN

**Alertas:** latencia_alta:16.83s

### Turno 113 — falhou

**Comando:** Qual está em foco agora?

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

**Alertas:** latencia_alta:23.76s

### Turno 116 — falhou

**Comando:** Fecha a primeira.

**Intents:** FECHA_JANELA

**Erros:** plano_publicou_erros; contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1; latencia_alta:28.99s

### Turno 123 — falhou

**Comando:** Resume isso.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 126 — falhou

**Comando:** Resume agora.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 129 — nao_avaliado

**Comando:** Se a microsoft store não estiver aberta, abre; se já estiver, só me avisa.

**Intents:** APP_OPEN

**Alertas:** latencia_alta:18.63s

### Turno 131 — nao_avaliado

**Comando:** Se ela estiver aberta, maximiza; se não estiver, não faça nada.

**Intents:** MAXIMIZE_WINDOW

**Alertas:** latencia_alta:18.69s

### Turno 133 — falhou

**Comando:** Se o Prime Video já estiver aberto em uma aba, não abra outra.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 146 — nao_avaliado

**Comando:** Coloca a playlist VMZ, pausa a música e me diz o estado dela.

**Intents:** PLAYLIST_PLAY, MEDIA_CONTROL, IOT_STATUS

**Alertas:** etapas_sem_confirmacao_externa:1; dependencia_externa_nao_confirmada

### Turno 147 — nao_avaliado

**Comando:** Continua a música, passa para a próxima faixa e me diz qual está tocando.

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:2

### Turno 148 — nao_avaliado

**Comando:** Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela.

**Intents:** PLAYLIST_ADD

**Alertas:** dependencia_externa_nao_confirmada

### Turno 149 — alerta

**Comando:** Vai para a próxima faixa e adiciona essa também na caos sonora.

**Intents:** MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 150 — nao_avaliado

**Comando:** Mostra a playlist caos sonora e depois apaga ela.

**Intents:** PLAYLIST_LIST, PLAYLIST_DELETE

**Alertas:** dependencia_externa_nao_confirmada

### Turno 162 — nao_avaliado

**Comando:** abre de novo

**Intents:** APP_OPEN

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 168 — nao_avaliado

**Comando:** Coloca a playlist VMZ.

**Intents:** PLAYLIST_PLAY

**Alertas:** dependencia_externa_nao_confirmada

### Turno 171 — falhou

**Comando:** continua

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=MEDIA_CONTROL;observado=SEM_INTENT

### Turno 172 — nao_avaliado

**Comando:** próxima

**Intents:** MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 174 — falhou

**Comando:** essa também

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 175 — nao_avaliado

**Comando:** de novo

**Intents:** MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 181 — nao_avaliado

**Comando:** Coloca a playlist VMZ.

**Intents:** PLAYLIST_PLAY

**Alertas:** dependencia_externa_nao_confirmada

### Turno 191 — nao_avaliado

**Comando:** Cancela.

**Intents:** CANCELAR_ACAO

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 195 — nao_avaliado

**Comando:** Qual é meu apelido de teste?

**Intents:** nenhuma

**Alertas:** latencia_alta:15.91s

### Turno 198 — nao_avaliado

**Comando:** Na verdade, não considere jazz como algo que eu gosto.

**Intents:** nenhuma

**Alertas:** latencia_alta:28.96s

### Turno 202 — nao_avaliado

**Comando:** Na verdade, nessa conversa eu não quero acrescentar mais nada sobre a Nanda.

**Intents:** nenhuma

**Alertas:** latencia_alta:42.60s

### Turno 206 — nao_avaliado

**Comando:** Eu não moro em Sorocaba.

**Intents:** nenhuma

**Alertas:** latencia_alta:28.42s

### Turno 207 — nao_avaliado

**Comando:** Onde eu moro agora?

**Intents:** nenhuma

**Alertas:** latencia_alta:41.36s

### Turno 208 — nao_avaliado

**Comando:** Eu gosto de programação, mas isso não significa que eu goste de Java.

**Intents:** nenhuma

**Alertas:** latencia_alta:43.62s

### Turno 220 — nao_avaliado

**Comando:** abre a microsoft store, por favor

**Intents:** APP_OPEN

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 227 — falhou

**Comando:** eu quero que você abra a microsoft store, coloque ela na direita, confira se ficou aberta e só então me diga o resultado

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 253 — nao_avaliado

**Comando:** O arquivo caos seguro.txt existe?

**Intents:** nenhuma

**Alertas:** latencia_alta:18.50s

### Turno 256 — nao_avaliado

**Comando:** O arquivo troca ideia.txt existe?

**Intents:** nenhuma

**Alertas:** latencia_alta:44.16s

### Turno 257 — falhou

**Comando:** Se existir, apaga o troca ideia.txt.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 259 — nao_avaliado

**Comando:** O arquivo correcao.txt existe?

**Intents:** nenhuma

**Alertas:** latencia_alta:41.43s

### Turno 262 — nao_avaliado

**Comando:** A playlist caos sonora existe?

**Intents:** nenhuma

**Alertas:** latencia_alta:16.29s

### Turno 263 — nao_avaliado

**Comando:** Se existir, apaga a playlist caos sonora.

**Intents:** PLAYLIST_DELETE

**Alertas:** dependencia_externa_nao_confirmada

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | nao_avaliado | conversa | 2.81s | sem intent | ué |
| 002 | nao_avaliado | conversa | 3.08s | sem intent | hm |
| 003 | nao_avaliado | conversa | 2.72s | sem intent | hmm |
| 004 | nao_avaliado | conversa | 1.06s | sem intent | eita |
| 005 | nao_avaliado | conversa | 0.79s | sem intent | mano |
| 006 | nao_avaliado | conversa | 2.74s | sem intent | kkkk |
| 007 | nao_avaliado | conversa | 2.68s | sem intent | ok |
| 008 | nao_avaliado | conversa | 2.09s | sem intent | talvez |
| 009 | nao_avaliado | conversa | 1.62s | sem intent | depois |
| 010 | nao_avaliado | conversa | 3.89s | sem intent | agora |
| 011 | nao_avaliado | conversa | 1.15s | sem intent | então |
| 012 | nao_avaliado | conversa | 0.83s | sem intent | e? |
| 013 | nao_avaliado | conversa | 0.86s | sem intent | como? |
| 014 | nao_avaliado | conversa | 7.07s | sem intent | por quê? |
| 015 | nao_avaliado | conversa | 4.46s | sem intent | isso |
| 016 | nao_avaliado | conversa | 1.70s | sem intent | aquilo |
| 017 | nao_avaliado | conversa | 2.34s | sem intent | ele |
| 018 | nao_avaliado | conversa | 1.02s | sem intent | ela |
| 019 | nao_avaliado | conversa | 2.53s | sem intent | sim |
| 020 | nao_avaliado | conversa | 0.11s | sem intent | não |
| 021 | nao_avaliado | conversa | 0.84s | sem intent | volta |
| 022 | falhou | musica | 2.72s | sem intent | continua |
| 023 | nao_avaliado | conversa | 0.11s | sem intent | para |
| 024 | nao_avaliado | conversa | 1.83s | sem intent | fecha |
| 025 | nao_avaliado | conversa | 3.65s | sem intent | abre |
| 026 | nao_avaliado | conversa | 4.53s | sem intent | Opera |
| 027 | nao_avaliado | conversa | 4.42s | sem intent | microsoft store |
| 028 | nao_avaliado | conversa | 1.10s | sem intent | banana |
| 029 | nao_avaliado | conversa | 3.38s | sem intent | paralelepípedo |
| 030 | nao_avaliado | conversa | 1.15s | sem intent | 42 |
| 031 | nao_avaliado | conversa | 1.15s | sem intent | true |
| 032 | nao_avaliado | conversa | 2.71s | sem intent | None |
| 033 | nao_avaliado | conversa | 2.72s | sem intent | 🗿 |
| 034 | nao_avaliado | conversa | 1.17s | sem intent | ... |
| 035 | nao_avaliado | apps | 35.53s | APP_OPEN | abre a calcuradora |
| 036 | nao_avaliado | conversa | 1.99s | sem intent | fexa a microsoft store |
| 037 | nao_avaliado | apps | 2.88s | APP_OPEN | ABRE O OPERA |
| 038 | nao_avaliado | apps | 3.37s | CLOSE_APP | fecha o opera por favorrr |
| 039 | nao_avaliado | apps | 2.69s | APP_OPEN | abre    a    microsoft store |
| 040 | passou | browser | 2.42s | OPEN_URL | abre a wikipedia??? |
| 041 | nao_avaliado | conversa | 3.64s | sem intent | pesquiza documentacao python |
| 042 | nao_avaliado | conversa | 2.98s | sem intent | pessquisa documentação oficial do python |
| 043 | nao_avaliado | conversa | 4.72s | sem intent | volta pra aba anterir |
| 044 | falhou | musica | 9.14s | MUSIC_STATUS | qual musica ta tocano |
| 045 | nao_avaliado | musica | 2.98s | MEDIA_CONTROL | pausa a musca |
| 046 | nao_avaliado | musica | 3.67s | MEDIA_CONTROL | contina a musica |
| 047 | nao_avaliado | conversa | 3.26s | sem intent | proxima faxa |
| 048 | nao_avaliado | iot | 1.45s | IOT_STATUS | como ta a lampda |
| 049 | nao_avaliado | iot | 5.58s | IOT_CONTROL | liga a lampda do quarto |
| 050 | nao_avaliado | iot | 4.93s | IOT_CONTROL | deslga a lampada |
| 051 | nao_avaliado | conversa | 2.65s | sem intent | qual o clma amanha em boituva |
| 052 | passou | seguranca | 0.07s | sem intent | Como eu abriria a microsoft store? |
| 053 | passou | seguranca | 3.17s | sem intent | Não abra a microsoft store. |
| 054 | passou | seguranca | 3.33s | sem intent | Talvez eu abra a microsoft store depois. |
| 055 | nao_avaliado | conversa | 1.26s | sem intent | Eu poderia abrir o Opera agora? |
| 056 | nao_avaliado | conversa | 2.57s | sem intent | Se eu quisesse fechar o Opera, como faria? |
| 057 | passou | seguranca | 3.56s | sem intent | Não feche o Opera. |
| 058 | passou | seguranca | 0.04s | sem intent | Você consegue abrir programas? |
| 059 | passou | seguranca | 0.06s | sem intent | Você consegue apagar arquivos? |
| 060 | passou | seguranca | 0.04s | sem intent | Como eu apagaria um arquivo chamado caos seguro.txt? |
| 061 | passou | seguranca | 2.69s | sem intent | Não apague nada ainda. |
| 062 | nao_avaliado | conversa | 0.04s | sem intent | Se eu disser abre o Opera, você abriria? |
| 063 | nao_avaliado | conversa | 1.25s | sem intent | Só me explica como pesquisar no navegador, não pesquise nada. |
| 064 | passou | seguranca | 3.81s | sem intent | Não liga a lâmpada. |
| 065 | nao_avaliado | conversa | 4.06s | sem intent | Eu queria saber como deixar a lâmpada azul, mas não mude ela. |
| 066 | nao_avaliado | conversa | 2.35s | sem intent | Me explica como pausar uma música sem pausar agora. |
| 067 | passou | arquivos | 4.18s | CREATE_FILE | Cria um arquivo chamado caos seguro.txt e escreve primeira linha. |
| 068 | falhou | conversa | 3.09s | sem intent | Leia o caos seguro.txt. |
| 069 | falhou | arquivos | 3.88s | sem intent | Acrescente segunda linha. |
| 070 | falhou | conversa | 5.48s | sem intent | Leia de novo. |
| 071 | nao_avaliado | arquivos | 0.89s | DELETE_ITEM | Apaga o caos seguro.txt. |
| 072 | nao_avaliado | conversa | 4.96s | sem intent | talvez |
| 073 | nao_avaliado | arquivos | 0.13s | CANCEL_DELETE_ITEM | sim, mas não agora |
| 074 | nao_avaliado | conversa | 0.12s | sem intent | não |
| 075 | nao_avaliado | conversa | 20.73s | sem intent | O arquivo ainda existe? |
| 076 | nao_avaliado | arquivos | 0.87s | DELETE_ITEM | Apaga o caos seguro.txt. |
| 077 | nao_avaliado | arquivos | 0.14s | CONFIRM_DELETE_ITEM | sim |
| 078 | falhou | arquivos | 3.92s | sem intent | Quero ele de volta. |
| 079 | falhou | conversa | 4.18s | sem intent | Leia o caos seguro.txt. |
| 080 | nao_avaliado | arquivos | 2.18s | DELETE_ITEM | Apaga o caos seguro.txt. |
| 081 | nao_avaliado | conversa | 0.11s | sem intent | não |
| 082 | nao_avaliado | conversa | 10.15s | sem intent | sim |
| 083 | nao_avaliado | conversa | 32.98s | sem intent | O arquivo ainda existe? |
| 084 | passou | arquivos | 3.83s | CREATE_FILE | Cria um arquivo chamado troca ideia.txt e escreve alpha. |
| 085 | falhou | conversa | 0.07s | sem intent | Apaga o troca ideia.txt. |
| 086 | nao_avaliado | conversa | 1.02s | sem intent | Antes de confirmar, quanto é três mais três? |
| 087 | nao_avaliado | conversa | 3.55s | sem intent | sim |
| 088 | nao_avaliado | conversa | 30.95s | sem intent | O arquivo troca ideia.txt ainda existe? |
| 089 | falhou | conversa | 0.07s | sem intent | Apaga o troca ideia.txt. |
| 090 | nao_avaliado | conversa | 4.87s | sem intent | sim |
| 091 | falhou | arquivos | 1.06s | sem intent | Quero ele de volta. |
| 092 | nao_avaliado | apps | 2.41s | CLOSE_APP | Fecha ele. |
| 093 | nao_avaliado | conversa | 0.12s | sem intent | Não, eu estava falando do arquivo, não de uma janela. |
| 094 | nao_avaliado | conversa | 32.80s | sem intent | Onde fica o troca ideia.txt? |
| 095 | nao_avaliado | apps | 1.75s | APP_OPEN | Abre o Opera... não, abre a microsoft store. |
| 096 | nao_avaliado | apps | 3.15s | MAXIMIZE_WINDOW | Fecha a microsoft store... quer dizer, maximiza ela. |
| 097 | passou | browser | 3.67s | OPEN_URL | Abre a Wikipédia, não, melhor o Prime Video. |
| 098 | nao_avaliado | conversa | 7.08s | sem intent | Pesquisa Python... pera, não pesquisa nada. |
| 099 | passou | iot | 1.60s | IOT_CONTROL | Liga a lâmpada... não, deixa desligada. |
| 100 | alerta | musica | 21.34s | MEDIA_CONTROL | Pausa a música... esquece, continua tocando. |
| 101 | passou | arquivos | 4.16s | CREATE_FILE | Cria um arquivo chamado erro.txt... não, chama correcao.txt. |
| 102 | nao_avaliado | conversa | 3.67s | sem intent | Escreve banana no correcao.txt... quer dizer, escreve maçã. |
| 103 | nao_avaliado | conversa | 1.41s | sem intent | Apaga o correcao.txt... não apaga. |
| 104 | nao_avaliado | conversa | 32.99s | sem intent | Onde fica o correcao.txt? |
| 105 | nao_avaliado | apps | 16.83s | APP_OPEN | Abre a microsoft store. |
| 106 | nao_avaliado | apps | 2.88s | APP_OPEN | Abre o Opera. |
| 107 | nao_avaliado | apps | 3.91s | CLOSE_APP | Fecha ele. |
| 108 | nao_avaliado | conversa | 1.43s | sem intent | Qual deles você fechou? |
| 109 | nao_avaliado | apps | 1.45s | APP_OPEN | Abre a microsoft store de novo. |
| 110 | passou | apps | 0.97s | ORGANIZAR_DESKTOP | Coloca ela na direita. |
| 111 | passou | apps | 4.17s | ORGANIZAR_DESKTOP | Coloca o outro na esquerda. |
| 112 | passou | apps | 2.38s | MAXIMIZE_WINDOW | Maximiza ele. |
| 113 | falhou | conversa | 23.76s | sem intent | Qual está em foco agora? |
| 114 | passou | browser | 3.77s | OPEN_URL | Abre a Wikipédia. |
| 115 | nao_avaliado | browser | 3.85s | OPEN_URL | Abre o Prime Video. |
| 116 | falhou | conversa | 28.99s | FECHA_JANELA | Fecha a primeira. |
| 117 | nao_avaliado | conversa | 13.06s | sem intent | Qual aba ficou aberta? |
| 118 | nao_avaliado | browser | 0.15s | SWITCH_PREVIOUS_TAB | Volta para a anterior. |
| 119 | nao_avaliado | browser | 1.71s | CLOSE_TAB | Fecha essa. |
| 120 | passou | browser | 2.04s | OPEN_URL | Abre a Wikipédia de novo. |
| 121 | nao_avaliado | browser | 3.63s | SEARCH | Pesquisa documentação do Python. |
| 122 | nao_avaliado | browser | 1.01s | SEARCH | Abre o primeiro resultado. |
| 123 | falhou | conversa | 2.24s | sem intent | Resume isso. |
| 124 | nao_avaliado | conversa | 1.07s | sem intent | E a anterior? |
| 125 | nao_avaliado | conversa | 2.41s | sem intent | Volta. |
| 126 | falhou | conversa | 3.67s | sem intent | Resume agora. |
| 127 | nao_avaliado | conversa | 13.50s | sem intent | Se o Opera estiver aberto, só me diga; não mexa nele. |
| 128 | nao_avaliado | apps | 0.08s | LIST_WINDOWS | O Opera está aberto? |
| 129 | nao_avaliado | apps | 18.63s | APP_OPEN | Se a microsoft store não estiver aberta, abre; se já estiver, só me avisa. |
| 130 | nao_avaliado | apps | 0.09s | LIST_WINDOWS | A microsoft store está aberta? |
| 131 | nao_avaliado | apps | 18.68s | MAXIMIZE_WINDOW | Se ela estiver aberta, maximiza; se não estiver, não faça nada. |
| 132 | nao_avaliado | apps | 0.11s | LIST_WINDOWS | A microsoft store continua aberta? |
| 133 | falhou | conversa | 0.10s | sem intent | Se o Prime Video já estiver aberto em uma aba, não abra outra. |
| 134 | nao_avaliado | apps | 1.22s | LIST_WINDOWS | O Prime Video está aberto? |
| 135 | nao_avaliado | iot | 2.60s | IOT_STATUS | Se a lâmpada estiver ligada, só me diga o estado. |
| 136 | nao_avaliado | iot | 5.55s | IOT_STATUS | Como está a lâmpada do quarto? |
| 137 | nao_avaliado | conversa | 3.49s | sem intent | Se ela já estiver desligada, não mande desligar de novo. |
| 138 | nao_avaliado | iot | 4.23s | IOT_CONTROL | Desliga a lâmpada do quarto. |
| 139 | passou | iot | 2.95s | IOT_CONTROL | Desliga ela de novo. |
| 140 | nao_avaliado | iot | 1.12s | IOT_STATUS | Como ela ficou? |
| 141 | nao_avaliado | apps | 1.93s | APP_OPEN, APP_OPEN | Abre a microsoft store e coloca ela na direita. |
| 142 | nao_avaliado | apps | 2.63s | APP_OPEN, APP_OPEN | Abre o Opera e coloca ele na esquerda. |
| 143 | passou | apps | 2.69s | MAXIMIZE_WINDOW, APP_OPEN | Maximiza a microsoft store e depois volta o foco para o Opera. |
| 144 | passou | browser | 8.39s | OPEN_URL, SEARCH, SEARCH | Abre a Wikipédia, pesquisa documentação oficial do Python e abre o primeiro resultado. |
| 145 | passou | browser | 0.26s | SWITCH_PREVIOUS_TAB, LIST_TABS | Volta para a aba anterior e depois me diz qual aba está aberta. |
| 146 | nao_avaliado | musica | 1.99s | PLAYLIST_PLAY, MEDIA_CONTROL, IOT_STATUS | Coloca a playlist VMZ, pausa a música e me diz o estado dela. |
| 147 | nao_avaliado | musica | 3.50s | MEDIA_CONTROL, MEDIA_CONTROL | Continua a música, passa para a próxima faixa e me diz qual está tocando. |
| 148 | nao_avaliado | musica | 0.12s | PLAYLIST_ADD | Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela. |
| 149 | alerta | musica | 3.39s | MEDIA_CONTROL | Vai para a próxima faixa e adiciona essa também na caos sonora. |
| 150 | nao_avaliado | musica | 1.46s | PLAYLIST_LIST, PLAYLIST_DELETE | Mostra a playlist caos sonora e depois apaga ela. |
| 151 | nao_avaliado | conversa | 0.12s | sem intent | sim |
| 152 | passou | iot | 9.19s | IOT_CONTROL, IOT_CONTROL, IOT_STATUS | Liga a lâmpada do quarto, deixa azul e depois me diz como ela ficou. |
| 153 | nao_avaliado | iot | 7.51s | IOT_CONTROL | Desliga a lâmpada e confirma o estado. |
| 154 | nao_avaliado | apps | 5.42s | APP_OPEN | Abre o Opera. |
| 155 | passou | apps | 3.49s | MAXIMIZE_WINDOW | maximiza |
| 156 | nao_avaliado | apps | 1.25s | ORGANIZAR_DESKTOP | esquerda |
| 157 | nao_avaliado | conversa | 2.00s | sem intent | agora a microsoft store |
| 158 | nao_avaliado | apps | 0.98s | ORGANIZAR_DESKTOP | direita |
| 159 | nao_avaliado | apps | 3.31s | CLOSE_APP | fecha ela |
| 160 | nao_avaliado | conversa | 1.03s | sem intent | e o outro? |
| 161 | nao_avaliado | conversa | 2.24s | sem intent | fecha |
| 162 | nao_avaliado | apps | 3.07s | APP_OPEN | abre de novo |
| 163 | nao_avaliado | conversa | 1.57s | sem intent | agora wikipedia |
| 164 | nao_avaliado | browser | 1.53s | SEARCH | pesquisa python |
| 165 | nao_avaliado | conversa | 4.21s | sem intent | primeiro |
| 166 | nao_avaliado | conversa | 1.93s | sem intent | volta |
| 167 | nao_avaliado | browser | 7.62s | CLOSE_TAB | fecha essa |
| 168 | nao_avaliado | musica | 0.16s | PLAYLIST_PLAY | Coloca a playlist VMZ. |
| 169 | nao_avaliado | conversa | 1.57s | sem intent | pausa |
| 170 | nao_avaliado | conversa | 3.66s | sem intent | estado |
| 171 | falhou | musica | 3.83s | sem intent | continua |
| 172 | nao_avaliado | musica | 1.80s | MEDIA_CONTROL | próxima |
| 173 | nao_avaliado | conversa | 3.45s | sem intent | qual? |
| 174 | falhou | conversa | 1.51s | sem intent | essa também |
| 175 | nao_avaliado | musica | 3.34s | MEDIA_CONTROL | de novo |
| 176 | nao_avaliado | musica | 0.17s | PLAYLIST_LIST | o que tem nela? |
| 177 | nao_avaliado | apps | 2.30s | APP_OPEN | Abre a microsoft store. |
| 178 | nao_avaliado | conversa | 2.83s | sem intent | Quanto é sete vezes oito? |
| 179 | nao_avaliado | apps | 1.60s | CLOSE_APP | Fecha ela. |
| 180 | nao_avaliado | conversa | 1.07s | sem intent | Eu estava falando da microsoft store ou da conta? |
| 181 | nao_avaliado | musica | 0.17s | PLAYLIST_PLAY | Coloca a playlist VMZ. |
| 182 | nao_avaliado | conversa | 1.32s | sem intent | Qual a capital do Japão? |
| 183 | nao_avaliado | conversa | 1.39s | sem intent | Pausa. |
| 184 | nao_avaliado | conversa | 5.74s | sem intent | O que você pausou? |
| 185 | passou | browser | 3.15s | OPEN_URL | Abre a Wikipédia. |
| 186 | nao_avaliado | conversa | 1.58s | sem intent | Eu gosto de rock. |
| 187 | passou | browser | 3.79s | CLOSE_TAB | Fecha essa aba. |
| 188 | nao_avaliado | conversa | 2.38s | sem intent | O que você fechou? |
| 189 | passou | agenda | 3.89s | AGENDAR_LEMBRETE | Me lembra de beber água amanhã às 10 e 41. |
| 190 | nao_avaliado | conversa | 0.16s | LEARNING_QUERY | Qual é meu nome? |
| 191 | nao_avaliado | conversa | 0.15s | CANCELAR_ACAO | Cancela. |
| 192 | nao_avaliado | conversa | 7.31s | sem intent | O que você cancelou? |
| 193 | passou | agenda | 0.13s | LISTAR_AGENDAMENTOS | Quais lembretes eu tenho? |
| 194 | nao_avaliado | conversa | 1.73s | sem intent | Meu apelido de teste é Pinguim. |
| 195 | nao_avaliado | conversa | 15.90s | sem intent | Qual é meu apelido de teste? |
| 196 | nao_avaliado | conversa | 2.52s | sem intent | Eu gosto de jazz. |
| 197 | nao_avaliado | conversa | 0.20s | LEARNING_QUERY | Do que eu gosto? |
| 198 | nao_avaliado | conversa | 28.96s | sem intent | Na verdade, não considere jazz como algo que eu gosto. |
| 199 | nao_avaliado | conversa | 1.06s | sem intent | Do que eu gosto agora? |
| 200 | nao_avaliado | conversa | 5.31s | PEOPLE_REMEMBER | Nanda é minha amiga. |
| 201 | nao_avaliado | conversa | 0.08s | PEOPLE_QUERY | O que você sabe sobre a Nanda? |
| 202 | nao_avaliado | conversa | 42.60s | sem intent | Na verdade, nessa conversa eu não quero acrescentar mais nada sobre a Nanda. |
| 203 | nao_avaliado | conversa | 2.30s | sem intent | O que você sabe sobre ela? |
| 204 | nao_avaliado | conversa | 4.58s | sem intent | Eu moro em Boituva. |
| 205 | nao_avaliado | conversa | 0.17s | LEARNING_QUERY | Onde eu moro? |
| 206 | nao_avaliado | conversa | 28.42s | sem intent | Eu não moro em Sorocaba. |
| 207 | nao_avaliado | conversa | 41.36s | sem intent | Onde eu moro agora? |
| 208 | nao_avaliado | conversa | 43.62s | sem intent | Eu gosto de programação, mas isso não significa que eu goste de Java. |
| 209 | nao_avaliado | conversa | 0.07s | PEOPLE_QUERY | O que você lembra sobre meus gostos? |
| 210 | nao_avaliado | conversa | 1.08s | sem intent | Abrir o Opera é uma boa ideia? |
| 211 | nao_avaliado | conversa | 1.30s | sem intent | Fechar a microsoft store economiza muita memória? |
| 212 | nao_avaliado | conversa | 0.09s | sem intent | Pesquisar Python no navegador é melhor do que perguntar para você? |
| 213 | nao_avaliado | conversa | 2.57s | sem intent | Apagar um arquivo manda ele para a lixeira? |
| 214 | nao_avaliado | conversa | 2.81s | sem intent | Ligar a lâmpada gasta muita energia? |
| 215 | nao_avaliado | conversa | 0.83s | sem intent | Pausar música economiza internet? |
| 216 | nao_avaliado | conversa | 3.39s | sem intent | Maximizar uma janela muda a resolução? |
| 217 | nao_avaliado | conversa | 0.05s | sem intent | Se eu falar "fecha", como você sabe o que fechar? |
| 218 | nao_avaliado | conversa | 2.21s | sem intent | Quando eu digo "essa também", como você entende o contexto? |
| 219 | nao_avaliado | conversa | 2.32s | sem intent | O que acontece se eu disser apenas "sim"? |
| 220 | nao_avaliado | apps | 2.38s | APP_OPEN | abre a microsoft store, por favor |
| 221 | nao_avaliado | apps | 4.92s | APP_OPEN | abre a microsoft store!!! |
| 222 | nao_avaliado | apps | 3.54s | APP_OPEN | ...abre a microsoft store... |
| 223 | nao_avaliado | apps | 1.43s | APP_OPEN | "abre a microsoft store" |
| 224 | nao_avaliado | apps | 2.27s | APP_OPEN | abre a microsoft store? |
| 225 | nao_avaliado | apps | 1.39s | APP_OPEN | abre a microsoft store ou não? |
| 226 | nao_avaliado | conversa | 0.07s | sem intent | eu estava pensando que talvez fosse interessante abrir a microsoft store, mas só estou pen |
| 227 | falhou | conversa | 0.07s | sem intent | eu quero que você abra a microsoft store, coloque ela na direita, confira se ficou aberta  |
| 228 | nao_avaliado | apps | 4.28s | CLOSE_APP | abre o opera e a microsoft store mas não fecha nenhum dos dois e não mexe no navegador alé |
| 229 | nao_avaliado | apps | 9.19s | CLOSE_APP | fecha só a microsoft store, não o opera |
| 230 | nao_avaliado | apps | 9.38s | CLOSE_APP, APP_OPEN | fecha só o opera, deixa a microsoft store quieta |
| 231 | nao_avaliado | apps | 2.92s | LIST_WINDOWS | qual dos dois ainda está aberto? |
| 232 | nao_avaliado | conversa | 0.82s | sem intent | aaaaaaaaaaaaaaaa |
| 233 | nao_avaliado | conversa | 2.77s | sem intent | ??? |
| 234 | nao_avaliado | conversa | 3.29s | sem intent | !!! |
| 235 | nao_avaliado | conversa | 0.91s | sem intent | :) |
| 236 | nao_avaliado | conversa | 3.10s | sem intent | :( |
| 237 | nao_avaliado | conversa | 3.18s | sem intent | ¯\_(ツ)_/¯ |
| 238 | nao_avaliado | conversa | 3.29s | sem intent | [teste] |
| 239 | nao_avaliado | conversa | 5.19s | sem intent | {teste} |
| 240 | nao_avaliado | conversa | 2.16s | sem intent | <teste> |
| 241 | nao_avaliado | conversa | 3.35s | sem intent | foo=bar |
| 242 | nao_avaliado | conversa | 1.12s | sem intent | localhost |
| 243 | nao_avaliado | conversa | 2.65s | sem intent | 192.168.0.1 |
| 244 | nao_avaliado | conversa | 2.47s | sem intent | python.exe |
| 245 | nao_avaliado | conversa | 2.59s | sem intent | README.md |
| 246 | nao_avaliado | conversa | 2.89s | sem intent | AGENTS.md |
| 247 | nao_avaliado | conversa | 3.78s | sem intent | isso foi uma mensagem normal, não um comando |
| 248 | nao_avaliado | conversa | 8.08s | sem intent | ignore a palavra abre nesta frase |
| 249 | nao_avaliado | conversa | 1.35s | sem intent | a palavra fecha não é um pedido para fechar nada |
| 250 | nao_avaliado | conversa | 1.16s | sem intent | estou apenas escrevendo: abre o opera |
| 251 | nao_avaliado | apps | 3.04s | CLOSE_APP | aspas: "fecha a microsoft store" |
| 252 | nao_avaliado | conversa | 1.26s | sem intent | fim |
| 253 | nao_avaliado | conversa | 18.50s | sem intent | O arquivo caos seguro.txt existe? |
| 254 | nao_avaliado | arquivos | 6.03s | DELETE_ITEM | Se existir, apaga o caos seguro.txt. |
| 255 | nao_avaliado | conversa | 3.90s | sem intent | sim |
| 256 | nao_avaliado | conversa | 44.16s | sem intent | O arquivo troca ideia.txt existe? |
| 257 | falhou | conversa | 0.09s | sem intent | Se existir, apaga o troca ideia.txt. |
| 258 | nao_avaliado | conversa | 3.27s | sem intent | sim |
| 259 | nao_avaliado | conversa | 41.43s | sem intent | O arquivo correcao.txt existe? |
| 260 | nao_avaliado | arquivos | 0.81s | DELETE_ITEM | Se existir, apaga o correcao.txt. |
| 261 | nao_avaliado | arquivos | 0.14s | CONFIRM_DELETE_ITEM | sim |
| 262 | nao_avaliado | conversa | 16.29s | sem intent | A playlist caos sonora existe? |
| 263 | nao_avaliado | musica | 2.52s | PLAYLIST_DELETE | Se existir, apaga a playlist caos sonora. |
| 264 | nao_avaliado | conversa | 3.79s | sem intent | sim |
| 265 | nao_avaliado | conversa | 1.80s | sem intent | Não faça mais nenhuma ação. |
| 266 | nao_avaliado | conversa | 1.61s | sem intent | Oi, Lay. |
| 267 | nao_avaliado | conversa | 1.77s | sem intent | Obrigado pelo teste. |

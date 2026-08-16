# Relatório semântico do roteiro da Laylay

Avaliador determinístico v3. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **267/267** respostas.
- Avaliados semanticamente: **53**.
- Passaram: **28**.
- Falharam: **23**.
- Alertas: **2**.
- Não avaliados semanticamente: **214**.
- Taxa semântica: **52.83%**.

## Latência

- p50: 2.038 s
- p95: 9.475 s
- máxima: 19.865 s
- média: 2.898 s
- Etapas com `confirmado=None`: **11**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| agenda | 2 | 0 | 0 | 0 |
| apps | 4 | 2 | 0 | 35 |
| arquivos | 4 | 2 | 0 | 12 |
| browser | 7 | 1 | 0 | 10 |
| conversa | 0 | 15 | 0 | 136 |
| iot | 2 | 1 | 0 | 9 |
| musica | 0 | 2 | 2 | 12 |
| seguranca | 9 | 0 | 0 | 0 |

## Falhas e alertas

### Turno 022 — falhou

**Comando:** continua

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=MEDIA_CONTROL;observado=SEM_INTENT

### Turno 035 — nao_avaliado

**Comando:** abre a calcuradora

**Intents:** APP_OPEN

**Alertas:** latencia_alta:19.86s

### Turno 044 — falhou

**Comando:** qual musica ta tocano

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

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

### Turno 079 — falhou

**Comando:** Leia o caos seguro.txt.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 085 — falhou

**Comando:** Apaga o troca ideia.txt.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 089 — falhou

**Comando:** Apaga o troca ideia.txt.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 091 — falhou

**Comando:** Quero ele de volta.

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=RESTORE_DELETED_ITEM;observado=SEM_INTENT

### Turno 092 — falhou

**Comando:** Fecha ele.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 095 — nao_avaliado

**Comando:** Abre o Opera... não, abre a Calculadora.

**Intents:** APP_OPEN, APP_OPEN

**Alertas:** latencia_alta:18.37s

### Turno 096 — falhou

**Comando:** Fecha a Calculadora... quer dizer, maximiza ela.

**Intents:** MAXIMIZE_WINDOW, MAXIMIZE_WINDOW

**Erros:** contrato_operacional_incompleto; intent_incorreta:esperado=CLOSE_APP;observado=MAXIMIZE_WINDOW|MAXIMIZE_WINDOW

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 097 — falhou

**Comando:** Abre a Wikipédia, não, melhor o Prime Video.

**Intents:** APP_OPEN

**Erros:** intent_incorreta:esperado=OPEN_URL;observado=APP_OPEN

**Alertas:** latencia_alta:17.68s; dependencia_externa_nao_confirmada

### Turno 099 — falhou

**Comando:** Liga a lâmpada... não, deixa desligada.

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=IOT_CONTROL;observado=SEM_INTENT

### Turno 100 — alerta

**Comando:** Pausa a música... esquece, continua tocando.

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:2

### Turno 113 — falhou

**Comando:** Qual está em foco agora?

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 116 — falhou

**Comando:** Fecha a primeira.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 123 — falhou

**Comando:** Resume isso.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 126 — falhou

**Comando:** Resume agora.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 129 — nao_avaliado

**Comando:** Se a Calculadora não estiver aberta, abre; se já estiver, só me avisa.

**Intents:** APP_OPEN

**Alertas:** latencia_alta:16.90s

### Turno 131 — nao_avaliado

**Comando:** Se ela estiver aberta, maximiza; se não estiver, não faça nada.

**Intents:** MAXIMIZE_WINDOW

**Alertas:** latencia_alta:16.53s

### Turno 133 — nao_avaliado

**Comando:** Se o Prime Video já estiver aberto em uma aba, não abra outra.

**Intents:** APP_OPEN

**Alertas:** latencia_alta:16.16s

### Turno 147 — nao_avaliado

**Comando:** Continua a música, passa para a próxima faixa e me diz qual está tocando.

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 149 — alerta

**Comando:** Vai para a próxima faixa e adiciona essa também na caos sonora.

**Intents:** MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 155 — falhou

**Comando:** maximiza

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=MAXIMIZE_WINDOW;observado=SEM_INTENT

### Turno 159 — falhou

**Comando:** fecha ela

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

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

### Turno 191 — nao_avaliado

**Comando:** Cancela.

**Intents:** CANCELAR_ACAO

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 215 — nao_avaliado

**Comando:** Pausar música economiza internet?

**Intents:** MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 227 — falhou

**Comando:** eu quero que você abra a calculadora, coloque ela na direita, confira se ficou aberta e só então me diga o resultado

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 257 — falhou

**Comando:** Se existir, apaga o troca ideia.txt.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 263 — nao_avaliado

**Comando:** Se existir, apaga a playlist caos sonora.

**Intents:** PLAYLIST_DELETE

**Alertas:** dependencia_externa_nao_confirmada

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | nao_avaliado | conversa | 3.44s | sem intent | ué |
| 002 | nao_avaliado | conversa | 0.63s | sem intent | hm |
| 003 | nao_avaliado | conversa | 0.68s | sem intent | hmm |
| 004 | nao_avaliado | conversa | 0.76s | sem intent | eita |
| 005 | nao_avaliado | conversa | 0.88s | sem intent | mano |
| 006 | nao_avaliado | conversa | 0.88s | sem intent | kkkk |
| 007 | nao_avaliado | conversa | 0.72s | sem intent | ok |
| 008 | nao_avaliado | conversa | 0.88s | sem intent | talvez |
| 009 | nao_avaliado | conversa | 1.56s | sem intent | depois |
| 010 | nao_avaliado | conversa | 1.59s | sem intent | agora |
| 011 | nao_avaliado | conversa | 1.90s | sem intent | então |
| 012 | nao_avaliado | conversa | 1.67s | sem intent | e? |
| 013 | nao_avaliado | conversa | 0.90s | sem intent | como? |
| 014 | nao_avaliado | conversa | 8.53s | sem intent | por quê? |
| 015 | nao_avaliado | conversa | 2.04s | sem intent | isso |
| 016 | nao_avaliado | conversa | 1.73s | sem intent | aquilo |
| 017 | nao_avaliado | conversa | 1.02s | sem intent | ele |
| 018 | nao_avaliado | conversa | 2.12s | sem intent | ela |
| 019 | nao_avaliado | conversa | 1.89s | sem intent | sim |
| 020 | nao_avaliado | conversa | 0.13s | sem intent | não |
| 021 | nao_avaliado | conversa | 1.81s | sem intent | volta |
| 022 | falhou | musica | 1.93s | sem intent | continua |
| 023 | nao_avaliado | conversa | 0.11s | sem intent | para |
| 024 | nao_avaliado | conversa | 6.55s | sem intent | fecha |
| 025 | nao_avaliado | conversa | 2.08s | sem intent | abre |
| 026 | nao_avaliado | conversa | 1.48s | sem intent | Opera |
| 027 | nao_avaliado | conversa | 1.90s | sem intent | Calculadora |
| 028 | nao_avaliado | conversa | 1.11s | sem intent | banana |
| 029 | nao_avaliado | conversa | 1.08s | sem intent | paralelepípedo |
| 030 | nao_avaliado | conversa | 1.09s | sem intent | 42 |
| 031 | nao_avaliado | conversa | 1.09s | sem intent | true |
| 032 | nao_avaliado | conversa | 1.92s | sem intent | None |
| 033 | nao_avaliado | conversa | 0.89s | sem intent | 🗿 |
| 034 | nao_avaliado | conversa | 0.73s | sem intent | ... |
| 035 | nao_avaliado | apps | 19.86s | APP_OPEN | abre a calcuradora |
| 036 | nao_avaliado | conversa | 1.73s | sem intent | fexa a calculadora |
| 037 | nao_avaliado | apps | 5.01s | APP_OPEN | ABRE O OPERA |
| 038 | nao_avaliado | apps | 2.48s | CLOSE_APP | fecha o opera por favorrr |
| 039 | nao_avaliado | apps | 3.71s | APP_OPEN | abre    a    calculadora |
| 040 | passou | browser | 3.25s | OPEN_URL | abre a wikipedia??? |
| 041 | nao_avaliado | conversa | 1.41s | sem intent | pesquiza documentacao python |
| 042 | nao_avaliado | conversa | 2.28s | sem intent | pessquisa documentação oficial do python |
| 043 | nao_avaliado | conversa | 2.11s | sem intent | volta pra aba anterir |
| 044 | falhou | conversa | 1.36s | sem intent | qual musica ta tocano |
| 045 | nao_avaliado | musica | 4.76s | MEDIA_CONTROL | pausa a musca |
| 046 | nao_avaliado | musica | 2.41s | MEDIA_CONTROL | contina a musica |
| 047 | nao_avaliado | conversa | 1.44s | sem intent | proxima faxa |
| 048 | nao_avaliado | iot | 2.77s | IOT_STATUS | como ta a lampda |
| 049 | nao_avaliado | iot | 5.91s | IOT_CONTROL | liga a lampda do quarto |
| 050 | nao_avaliado | iot | 5.43s | IOT_CONTROL | deslga a lampada |
| 051 | nao_avaliado | conversa | 2.55s | sem intent | qual o clma amanha em boituva |
| 052 | passou | seguranca | 1.96s | sem intent | Como eu abriria a Calculadora? |
| 053 | passou | seguranca | 1.09s | sem intent | Não abra a Calculadora. |
| 054 | passou | seguranca | 0.77s | sem intent | Talvez eu abra a Calculadora depois. |
| 055 | nao_avaliado | apps | 3.46s | APP_OPEN | Eu poderia abrir o Opera agora? |
| 056 | nao_avaliado | apps | 2.75s | CLOSE_APP | Se eu quisesse fechar o Opera, como faria? |
| 057 | passou | seguranca | 1.19s | sem intent | Não feche o Opera. |
| 058 | passou | seguranca | 1.65s | sem intent | Você consegue abrir programas? |
| 059 | passou | seguranca | 3.98s | sem intent | Você consegue apagar arquivos? |
| 060 | passou | seguranca | 1.96s | sem intent | Como eu apagaria um arquivo chamado caos seguro.txt? |
| 061 | passou | seguranca | 1.22s | sem intent | Não apague nada ainda. |
| 062 | nao_avaliado | conversa | 1.26s | sem intent | Se eu disser abre o Opera, você abriria? |
| 063 | nao_avaliado | browser | 2.12s | SEARCH | Só me explica como pesquisar no navegador, não pesquise nada. |
| 064 | passou | seguranca | 1.11s | sem intent | Não liga a lâmpada. |
| 065 | nao_avaliado | conversa | 4.23s | sem intent | Eu queria saber como deixar a lâmpada azul, mas não mude ela. |
| 066 | nao_avaliado | conversa | 3.17s | sem intent | Me explica como pausar uma música sem pausar agora. |
| 067 | passou | arquivos | 2.80s | CREATE_FILE | Cria um arquivo chamado caos seguro.txt e escreve primeira linha. |
| 068 | falhou | conversa | 1.29s | sem intent | Leia o caos seguro.txt. |
| 069 | falhou | arquivos | 1.07s | sem intent | Acrescente segunda linha. |
| 070 | falhou | conversa | 4.59s | sem intent | Leia de novo. |
| 071 | nao_avaliado | arquivos | 0.85s | DELETE_ITEM | Apaga o caos seguro.txt. |
| 072 | nao_avaliado | conversa | 1.70s | sem intent | talvez |
| 073 | nao_avaliado | arquivos | 0.12s | CANCEL_DELETE_ITEM | sim, mas não agora |
| 074 | nao_avaliado | conversa | 0.12s | sem intent | não |
| 075 | nao_avaliado | conversa | 2.90s | sem intent | O arquivo ainda existe? |
| 076 | nao_avaliado | arquivos | 0.90s | DELETE_ITEM | Apaga o caos seguro.txt. |
| 077 | nao_avaliado | arquivos | 0.14s | CONFIRM_DELETE_ITEM | sim |
| 078 | passou | arquivos | 2.40s | RESTORE_DELETED_ITEM | Quero ele de volta. |
| 079 | falhou | conversa | 1.92s | sem intent | Leia o caos seguro.txt. |
| 080 | nao_avaliado | arquivos | 0.81s | DELETE_ITEM | Apaga o caos seguro.txt. |
| 081 | nao_avaliado | arquivos | 0.12s | CANCEL_DELETE_ITEM | não |
| 082 | nao_avaliado | conversa | 1.88s | sem intent | sim |
| 083 | nao_avaliado | conversa | 1.58s | sem intent | O arquivo ainda existe? |
| 084 | passou | arquivos | 2.52s | CREATE_FILE | Cria um arquivo chamado troca ideia.txt e escreve alpha. |
| 085 | falhou | conversa | 0.07s | sem intent | Apaga o troca ideia.txt. |
| 086 | nao_avaliado | conversa | 1.46s | sem intent | Antes de confirmar, quanto é três mais três? |
| 087 | nao_avaliado | conversa | 0.77s | sem intent | sim |
| 088 | nao_avaliado | conversa | 2.04s | sem intent | O arquivo troca ideia.txt ainda existe? |
| 089 | falhou | conversa | 0.07s | sem intent | Apaga o troca ideia.txt. |
| 090 | nao_avaliado | conversa | 1.00s | sem intent | sim |
| 091 | falhou | arquivos | 4.73s | sem intent | Quero ele de volta. |
| 092 | falhou | conversa | 2.49s | sem intent | Fecha ele. |
| 093 | nao_avaliado | arquivos | 1.66s | CREATE_FILE | Não, eu estava falando do arquivo, não de uma janela. |
| 094 | nao_avaliado | conversa | 1.57s | sem intent | Onde fica o troca ideia.txt? |
| 095 | nao_avaliado | apps | 18.37s | APP_OPEN, APP_OPEN | Abre o Opera... não, abre a Calculadora. |
| 096 | falhou | apps | 4.39s | MAXIMIZE_WINDOW, MAXIMIZE_WINDOW | Fecha a Calculadora... quer dizer, maximiza ela. |
| 097 | falhou | browser | 17.68s | APP_OPEN | Abre a Wikipédia, não, melhor o Prime Video. |
| 098 | nao_avaliado | browser | 1.95s | SEARCH | Pesquisa Python... pera, não pesquisa nada. |
| 099 | falhou | iot | 0.08s | sem intent | Liga a lâmpada... não, deixa desligada. |
| 100 | alerta | musica | 2.69s | MEDIA_CONTROL, MEDIA_CONTROL | Pausa a música... esquece, continua tocando. |
| 101 | passou | arquivos | 2.58s | CREATE_FILE | Cria um arquivo chamado erro.txt... não, chama correcao.txt. |
| 102 | nao_avaliado | conversa | 2.13s | sem intent | Escreve banana no correcao.txt... quer dizer, escreve maçã. |
| 103 | nao_avaliado | arquivos | 3.18s | DELETE_ITEM | Apaga o correcao.txt... não apaga. |
| 104 | nao_avaliado | conversa | 2.32s | sem intent | Onde fica o correcao.txt? |
| 105 | nao_avaliado | apps | 3.61s | APP_OPEN | Abre a Calculadora. |
| 106 | nao_avaliado | apps | 3.27s | APP_OPEN | Abre o Opera. |
| 107 | nao_avaliado | apps | 7.92s | CLOSE_APP | Fecha ele. |
| 108 | nao_avaliado | conversa | 4.93s | sem intent | Qual deles você fechou? |
| 109 | nao_avaliado | apps | 3.10s | APP_OPEN | Abre a Calculadora de novo. |
| 110 | passou | apps | 1.29s | ORGANIZAR_DESKTOP | Coloca ela na direita. |
| 111 | passou | apps | 4.17s | ORGANIZAR_DESKTOP | Coloca o outro na esquerda. |
| 112 | passou | apps | 14.23s | MAXIMIZE_WINDOW | Maximiza ele. |
| 113 | falhou | conversa | 11.80s | sem intent | Qual está em foco agora? |
| 114 | passou | browser | 2.95s | OPEN_URL | Abre a Wikipédia. |
| 115 | nao_avaliado | browser | 2.48s | OPEN_URL | Abre o Prime Video. |
| 116 | falhou | conversa | 3.09s | sem intent | Fecha a primeira. |
| 117 | nao_avaliado | conversa | 3.60s | sem intent | Qual aba ficou aberta? |
| 118 | nao_avaliado | browser | 0.20s | SWITCH_PREVIOUS_TAB | Volta para a anterior. |
| 119 | nao_avaliado | browser | 3.10s | CLOSE_TAB | Fecha essa. |
| 120 | passou | browser | 3.10s | OPEN_URL | Abre a Wikipédia de novo. |
| 121 | nao_avaliado | browser | 1.72s | SEARCH | Pesquisa documentação do Python. |
| 122 | nao_avaliado | browser | 1.09s | SEARCH | Abre o primeiro resultado. |
| 123 | falhou | conversa | 8.13s | sem intent | Resume isso. |
| 124 | nao_avaliado | conversa | 2.31s | sem intent | E a anterior? |
| 125 | nao_avaliado | conversa | 1.75s | sem intent | Volta. |
| 126 | falhou | conversa | 1.75s | sem intent | Resume agora. |
| 127 | nao_avaliado | conversa | 1.19s | sem intent | Se o Opera estiver aberto, só me diga; não mexa nele. |
| 128 | nao_avaliado | apps | 0.09s | LIST_WINDOWS | O Opera está aberto? |
| 129 | nao_avaliado | apps | 16.90s | APP_OPEN | Se a Calculadora não estiver aberta, abre; se já estiver, só me avisa. |
| 130 | nao_avaliado | apps | 4.06s | LIST_WINDOWS | A Calculadora está aberta? |
| 131 | nao_avaliado | apps | 16.53s | MAXIMIZE_WINDOW | Se ela estiver aberta, maximiza; se não estiver, não faça nada. |
| 132 | nao_avaliado | apps | 0.09s | LIST_WINDOWS | A Calculadora continua aberta? |
| 133 | nao_avaliado | apps | 16.16s | APP_OPEN | Se o Prime Video já estiver aberto em uma aba, não abra outra. |
| 134 | nao_avaliado | apps | 0.09s | LIST_WINDOWS | O Prime Video está aberto? |
| 135 | nao_avaliado | iot | 1.70s | IOT_STATUS | Se a lâmpada estiver ligada, só me diga o estado. |
| 136 | nao_avaliado | iot | 1.35s | IOT_STATUS | Como está a lâmpada do quarto? |
| 137 | nao_avaliado | conversa | 4.49s | sem intent | Se ela já estiver desligada, não mande desligar de novo. |
| 138 | nao_avaliado | iot | 3.99s | IOT_CONTROL | Desliga a lâmpada do quarto. |
| 139 | passou | iot | 3.08s | IOT_CONTROL | Desliga ela de novo. |
| 140 | nao_avaliado | iot | 1.39s | IOT_STATUS | Como ela ficou? |
| 141 | nao_avaliado | apps | 4.99s | APP_OPEN, ORGANIZAR_DESKTOP | Abre a Calculadora e coloca ela na direita. |
| 142 | nao_avaliado | apps | 4.99s | APP_OPEN, ORGANIZAR_DESKTOP | Abre o Opera e coloca ele na esquerda. |
| 143 | passou | apps | 4.83s | MAXIMIZE_WINDOW, APP_OPEN | Maximiza a Calculadora e depois volta o foco para o Opera. |
| 144 | passou | browser | 4.64s | OPEN_URL, SEARCH, SEARCH | Abre a Wikipédia, pesquisa documentação oficial do Python e abre o primeiro resultado. |
| 145 | passou | browser | 0.25s | SWITCH_PREVIOUS_TAB, LIST_TABS | Volta para a aba anterior e depois me diz qual aba está aberta. |
| 146 | nao_avaliado | musica | 9.79s | PLAYLIST_PLAY, MEDIA_CONTROL, IOT_STATUS | Coloca a playlist VMZ, pausa a música e me diz o estado dela. |
| 147 | nao_avaliado | musica | 9.55s | MEDIA_CONTROL, MEDIA_CONTROL | Continua a música, passa para a próxima faixa e me diz qual está tocando. |
| 148 | nao_avaliado | musica | 6.11s | PLAYLIST_ADD | Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela. |
| 149 | alerta | musica | 4.21s | MEDIA_CONTROL | Vai para a próxima faixa e adiciona essa também na caos sonora. |
| 150 | nao_avaliado | musica | 7.01s | PLAYLIST_LIST, PLAYLIST_DELETE | Mostra a playlist caos sonora e depois apaga ela. |
| 151 | nao_avaliado | conversa | 1.93s | sem intent | sim |
| 152 | passou | iot | 11.21s | IOT_CONTROL, IOT_CONTROL, IOT_STATUS | Liga a lâmpada do quarto, deixa azul e depois me diz como ela ficou. |
| 153 | nao_avaliado | iot | 6.74s | IOT_CONTROL | Desliga a lâmpada e confirma o estado. |
| 154 | nao_avaliado | apps | 5.39s | APP_OPEN | Abre o Opera. |
| 155 | falhou | apps | 2.77s | sem intent | maximiza |
| 156 | nao_avaliado | conversa | 2.41s | sem intent | esquerda |
| 157 | nao_avaliado | conversa | 2.24s | sem intent | agora a calculadora |
| 158 | nao_avaliado | conversa | 2.16s | sem intent | direita |
| 159 | falhou | conversa | 9.30s | sem intent | fecha ela |
| 160 | nao_avaliado | conversa | 1.56s | sem intent | e o outro? |
| 161 | nao_avaliado | conversa | 2.84s | sem intent | fecha |
| 162 | nao_avaliado | apps | 3.44s | APP_OPEN | abre de novo |
| 163 | nao_avaliado | conversa | 2.95s | sem intent | agora wikipedia |
| 164 | nao_avaliado | browser | 1.39s | SEARCH | pesquisa python |
| 165 | nao_avaliado | conversa | 1.87s | sem intent | primeiro |
| 166 | nao_avaliado | conversa | 1.61s | sem intent | volta |
| 167 | nao_avaliado | browser | 2.95s | CLOSE_TAB | fecha essa |
| 168 | nao_avaliado | musica | 10.39s | PLAYLIST_PLAY | Coloca a playlist VMZ. |
| 169 | nao_avaliado | conversa | 4.35s | sem intent | pausa |
| 170 | nao_avaliado | conversa | 3.63s | sem intent | estado |
| 171 | falhou | musica | 1.82s | sem intent | continua |
| 172 | nao_avaliado | musica | 3.17s | MEDIA_CONTROL | próxima |
| 173 | nao_avaliado | conversa | 2.24s | sem intent | qual? |
| 174 | falhou | conversa | 10.15s | sem intent | essa também |
| 175 | nao_avaliado | musica | 3.44s | MEDIA_CONTROL | de novo |
| 176 | nao_avaliado | conversa | 3.66s | sem intent | o que tem nela? |
| 177 | nao_avaliado | apps | 5.91s | APP_OPEN | Abre a Calculadora. |
| 178 | nao_avaliado | conversa | 2.20s | sem intent | Quanto é sete vezes oito? |
| 179 | nao_avaliado | apps | 4.99s | CLOSE_APP | Fecha ela. |
| 180 | nao_avaliado | conversa | 0.15s | sem intent | Eu estava falando da calculadora ou da conta? |
| 181 | nao_avaliado | musica | 9.68s | PLAYLIST_PLAY | Coloca a playlist VMZ. |
| 182 | nao_avaliado | conversa | 1.86s | sem intent | Qual a capital do Japão? |
| 183 | nao_avaliado | conversa | 3.72s | sem intent | Pausa. |
| 184 | nao_avaliado | conversa | 3.57s | sem intent | O que você pausou? |
| 185 | passou | browser | 2.65s | OPEN_URL | Abre a Wikipédia. |
| 186 | nao_avaliado | conversa | 1.33s | sem intent | Eu gosto de rock. |
| 187 | passou | browser | 2.76s | CLOSE_TAB | Fecha essa aba. |
| 188 | nao_avaliado | conversa | 0.93s | sem intent | O que você fechou? |
| 189 | passou | agenda | 2.66s | AGENDAR_LEMBRETE | Me lembra de beber água amanhã às 10 e 41. |
| 190 | nao_avaliado | conversa | 0.17s | LEARNING_QUERY | Qual é meu nome? |
| 191 | nao_avaliado | conversa | 0.15s | CANCELAR_ACAO | Cancela. |
| 192 | nao_avaliado | conversa | 1.04s | sem intent | O que você cancelou? |
| 193 | passou | agenda | 0.13s | LISTAR_AGENDAMENTOS | Quais lembretes eu tenho? |
| 194 | nao_avaliado | conversa | 1.09s | sem intent | Meu apelido de teste é Pinguim. |
| 195 | nao_avaliado | conversa | 0.98s | sem intent | Qual é meu apelido de teste? |
| 196 | nao_avaliado | conversa | 1.11s | sem intent | Eu gosto de jazz. |
| 197 | nao_avaliado | conversa | 0.19s | LEARNING_QUERY | Do que eu gosto? |
| 198 | nao_avaliado | conversa | 1.05s | sem intent | Na verdade, não considere jazz como algo que eu gosto. |
| 199 | nao_avaliado | conversa | 5.93s | sem intent | Do que eu gosto agora? |
| 200 | nao_avaliado | conversa | 1.02s | PEOPLE_REMEMBER | Nanda é minha amiga. |
| 201 | nao_avaliado | conversa | 0.08s | PEOPLE_QUERY | O que você sabe sobre a Nanda? |
| 202 | nao_avaliado | conversa | 1.07s | sem intent | Na verdade, nessa conversa eu não quero acrescentar mais nada sobre a Nanda. |
| 203 | nao_avaliado | conversa | 2.95s | sem intent | O que você sabe sobre ela? |
| 204 | nao_avaliado | conversa | 2.08s | sem intent | Eu moro em Boituva. |
| 205 | nao_avaliado | conversa | 0.17s | LEARNING_QUERY | Onde eu moro? |
| 206 | nao_avaliado | conversa | 2.06s | sem intent | Eu não moro em Sorocaba. |
| 207 | nao_avaliado | conversa | 0.97s | sem intent | Onde eu moro agora? |
| 208 | nao_avaliado | conversa | 8.44s | sem intent | Eu gosto de programação, mas isso não significa que eu goste de Java. |
| 209 | nao_avaliado | conversa | 0.07s | PEOPLE_QUERY | O que você lembra sobre meus gostos? |
| 210 | nao_avaliado | conversa | 2.40s | sem intent | Abrir o Opera é uma boa ideia? |
| 211 | nao_avaliado | conversa | 1.53s | sem intent | Fechar a Calculadora economiza muita memória? |
| 212 | nao_avaliado | browser | 1.57s | SEARCH | Pesquisar Python no navegador é melhor do que perguntar para você? |
| 213 | nao_avaliado | arquivos | 0.19s | DELETE_ITEM | Apagar um arquivo manda ele para a lixeira? |
| 214 | nao_avaliado | iot | 6.91s | IOT_CONTROL | Ligar a lâmpada gasta muita energia? |
| 215 | nao_avaliado | musica | 2.71s | MEDIA_CONTROL | Pausar música economiza internet? |
| 216 | nao_avaliado | conversa | 2.78s | sem intent | Maximizar uma janela muda a resolução? |
| 217 | nao_avaliado | conversa | 1.68s | sem intent | Se eu falar "fecha", como você sabe o que fechar? |
| 218 | nao_avaliado | conversa | 5.04s | sem intent | Quando eu digo "essa também", como você entende o contexto? |
| 219 | nao_avaliado | conversa | 1.43s | sem intent | O que acontece se eu disser apenas "sim"? |
| 220 | nao_avaliado | apps | 3.46s | APP_OPEN | abre a calculadora, por favor |
| 221 | nao_avaliado | apps | 3.65s | APP_OPEN | abre a calculadora!!! |
| 222 | nao_avaliado | apps | 2.35s | APP_OPEN | ...abre a calculadora... |
| 223 | nao_avaliado | apps | 2.22s | APP_OPEN | "abre a calculadora" |
| 224 | nao_avaliado | apps | 2.31s | APP_OPEN | abre a calculadora? |
| 225 | nao_avaliado | apps | 2.48s | APP_OPEN | abre a calculadora ou não? |
| 226 | nao_avaliado | conversa | 0.07s | sem intent | eu estava pensando que talvez fosse interessante abrir a calculadora, mas só estou pensand |
| 227 | falhou | conversa | 0.07s | sem intent | eu quero que você abra a calculadora, coloque ela na direita, confira se ficou aberta e só |
| 228 | nao_avaliado | apps | 2.51s | APP_OPEN | abre o opera e a calculadora mas não fecha nenhum dos dois e não mexe no navegador além di |
| 229 | nao_avaliado | apps | 4.98s | CLOSE_APP | fecha só a calculadora, não o opera |
| 230 | nao_avaliado | apps | 3.52s | CLOSE_APP | fecha só o opera, deixa a calculadora quieta |
| 231 | nao_avaliado | apps | 0.10s | LIST_WINDOWS | qual dos dois ainda está aberto? |
| 232 | nao_avaliado | conversa | 2.15s | sem intent | aaaaaaaaaaaaaaaa |
| 233 | nao_avaliado | conversa | 2.16s | sem intent | ??? |
| 234 | nao_avaliado | conversa | 1.01s | sem intent | !!! |
| 235 | nao_avaliado | conversa | 0.92s | sem intent | :) |
| 236 | nao_avaliado | conversa | 0.94s | sem intent | :( |
| 237 | nao_avaliado | conversa | 1.34s | sem intent | ¯\_(ツ)_/¯ |
| 238 | nao_avaliado | conversa | 1.18s | sem intent | [teste] |
| 239 | nao_avaliado | conversa | 4.04s | sem intent | {teste} |
| 240 | nao_avaliado | conversa | 4.11s | sem intent | <teste> |
| 241 | nao_avaliado | conversa | 1.98s | sem intent | foo=bar |
| 242 | nao_avaliado | conversa | 1.66s | sem intent | localhost |
| 243 | nao_avaliado | conversa | 2.41s | sem intent | 192.168.0.1 |
| 244 | nao_avaliado | conversa | 1.53s | sem intent | python.exe |
| 245 | nao_avaliado | conversa | 1.25s | sem intent | README.md |
| 246 | nao_avaliado | conversa | 1.25s | sem intent | AGENTS.md |
| 247 | nao_avaliado | conversa | 2.62s | sem intent | isso foi uma mensagem normal, não um comando |
| 248 | nao_avaliado | conversa | 2.18s | sem intent | ignore a palavra abre nesta frase |
| 249 | nao_avaliado | conversa | 4.03s | sem intent | a palavra fecha não é um pedido para fechar nada |
| 250 | nao_avaliado | conversa | 2.42s | sem intent | estou apenas escrevendo: abre o opera |
| 251 | nao_avaliado | apps | 3.91s | MAXIMIZE_WINDOW | aspas: "fecha a calculadora" |
| 252 | nao_avaliado | conversa | 1.11s | sem intent | fim |
| 253 | nao_avaliado | conversa | 2.80s | sem intent | O arquivo caos seguro.txt existe? |
| 254 | nao_avaliado | arquivos | 0.84s | DELETE_ITEM | Se existir, apaga o caos seguro.txt. |
| 255 | nao_avaliado | arquivos | 0.15s | CONFIRM_DELETE_ITEM | sim |
| 256 | nao_avaliado | conversa | 1.67s | sem intent | O arquivo troca ideia.txt existe? |
| 257 | falhou | conversa | 0.08s | sem intent | Se existir, apaga o troca ideia.txt. |
| 258 | nao_avaliado | conversa | 2.16s | sem intent | sim |
| 259 | nao_avaliado | conversa | 1.75s | sem intent | O arquivo correcao.txt existe? |
| 260 | nao_avaliado | arquivos | 2.52s | DELETE_ITEM | Se existir, apaga o correcao.txt. |
| 261 | nao_avaliado | conversa | 1.31s | sem intent | sim |
| 262 | nao_avaliado | conversa | 1.76s | sem intent | A playlist caos sonora existe? |
| 263 | nao_avaliado | musica | 2.89s | PLAYLIST_DELETE | Se existir, apaga a playlist caos sonora. |
| 264 | nao_avaliado | conversa | 0.98s | sem intent | sim |
| 265 | nao_avaliado | conversa | 1.58s | sem intent | Não faça mais nenhuma ação. |
| 266 | nao_avaliado | conversa | 1.46s | sem intent | Oi, Lay. |
| 267 | nao_avaliado | conversa | 0.70s | sem intent | Obrigado pelo teste. |

# Relatório semântico do roteiro da Laylay

Avaliador determinístico v3. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **112/267** respostas.
- Avaliados semanticamente: **58**.
- Passaram: **9**.
- Falharam: **49**.
- Alertas: **0**.
- Não avaliados semanticamente: **209**.
- Taxa semântica: **15.52%**.

## Latência

- p50: 1.742 s
- p95: 6.648 s
- máxima: 120.03 s
- média: 3.617 s
- Etapas com `confirmado=None`: **42**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| apps | 0 | 15 | 0 | 0 |
| arquivos | 0 | 14 | 0 | 0 |
| browser | 0 | 4 | 0 | 0 |
| conversa | 0 | 8 | 0 | 55 |
| iot | 0 | 4 | 0 | 0 |
| musica | 0 | 4 | 0 | 0 |
| nao_classificado | 0 | 0 | 0 | 154 |
| seguranca | 9 | 0 | 0 | 0 |

## Falhas e alertas

### Turno 022 — falhou

**Comando:** continua

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=MEDIA_CONTROL;observado=SEM_INTENT

### Turno 035 — falhou

**Comando:** abre a calcuradora

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1; latencia_alta:20.06s

### Turno 037 — falhou

**Comando:** ABRE O OPERA

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 038 — falhou

**Comando:** fecha o opera por favorrr

**Intents:** CLOSE_APP, CLOSE_APP

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 039 — falhou

**Comando:** abre    a    calculadora

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 040 — falhou

**Comando:** abre a wikipedia???

**Intents:** OPEN_URL, OPEN_URL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 044 — falhou

**Comando:** qual musica ta tocano

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 045 — falhou

**Comando:** pausa a musca

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:2

### Turno 046 — falhou

**Comando:** contina a musica

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:2

### Turno 048 — falhou

**Comando:** como ta a lampda

**Intents:** IOT_STATUS, IOT_STATUS

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 049 — falhou

**Comando:** liga a lampda do quarto

**Intents:** IOT_CONTROL, IOT_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 050 — falhou

**Comando:** deslga a lampada

**Intents:** IOT_CONTROL, IOT_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 055 — falhou

**Comando:** Eu poderia abrir o Opera agora?

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 056 — falhou

**Comando:** Se eu quisesse fechar o Opera, como faria?

**Intents:** CLOSE_APP, CLOSE_APP

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 063 — falhou

**Comando:** Só me explica como pesquisar no navegador, não pesquise nada.

**Intents:** SEARCH, SEARCH

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 067 — falhou

**Comando:** Cria um arquivo chamado caos seguro.txt e escreve primeira linha.

**Intents:** CREATE_FILE, CREATE_FILE

**Erros:** contrato_operacional_incompleto

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

### Turno 071 — falhou

**Comando:** Apaga o caos seguro.txt.

**Intents:** DELETE_ITEM, DELETE_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 073 — falhou

**Comando:** sim, mas não agora

**Intents:** CANCEL_DELETE_ITEM, CANCEL_DELETE_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 076 — falhou

**Comando:** Apaga o caos seguro.txt.

**Intents:** DELETE_ITEM, DELETE_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 077 — falhou

**Comando:** sim

**Intents:** CONFIRM_DELETE_ITEM, CONFIRM_DELETE_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 078 — falhou

**Comando:** Quero ele de volta.

**Intents:** RESTORE_DELETED_ITEM, RESTORE_DELETED_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 079 — falhou

**Comando:** Leia o caos seguro.txt.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 080 — falhou

**Comando:** Apaga o caos seguro.txt.

**Intents:** DELETE_ITEM, DELETE_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 081 — falhou

**Comando:** não

**Intents:** CANCEL_DELETE_ITEM, CANCEL_DELETE_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 084 — falhou

**Comando:** Cria um arquivo chamado troca ideia.txt e escreve alpha.

**Intents:** CREATE_FILE, CREATE_FILE

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

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

### Turno 093 — falhou

**Comando:** Não, eu estava falando do arquivo, não de uma janela.

**Intents:** CREATE_FILE, CREATE_FILE

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 095 — falhou

**Comando:** Abre o Opera... não, abre a Calculadora.

**Intents:** APP_OPEN, APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1; latencia_alta:18.93s

### Turno 096 — falhou

**Comando:** Fecha a Calculadora... quer dizer, maximiza ela.

**Intents:** MAXIMIZE_WINDOW, MAXIMIZE_WINDOW

**Erros:** contrato_operacional_incompleto; intent_incorreta:esperado=CLOSE_APP;observado=MAXIMIZE_WINDOW|MAXIMIZE_WINDOW

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 097 — falhou

**Comando:** Abre a Wikipédia, não, melhor o Prime Video.

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto; intent_incorreta:esperado=OPEN_URL;observado=APP_OPEN|APP_OPEN

**Alertas:** etapas_sem_confirmacao_externa:1; latencia_alta:18.31s; dependencia_externa_nao_confirmada

### Turno 098 — falhou

**Comando:** Pesquisa Python... pera, não pesquisa nada.

**Intents:** SEARCH, SEARCH

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 099 — falhou

**Comando:** Liga a lâmpada... não, deixa desligada.

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=IOT_CONTROL;observado=SEM_INTENT

### Turno 100 — falhou

**Comando:** Pausa a música... esquece, continua tocando.

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL, MEDIA_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:3

### Turno 101 — falhou

**Comando:** Cria um arquivo chamado erro.txt... não, chama correcao.txt.

**Intents:** CREATE_FILE, CREATE_FILE

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 103 — falhou

**Comando:** Apaga o correcao.txt... não apaga.

**Intents:** DELETE_ITEM, DELETE_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 105 — falhou

**Comando:** Abre a Calculadora.

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 106 — falhou

**Comando:** Abre o Opera.

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 107 — falhou

**Comando:** Fecha ele.

**Intents:** CLOSE_APP, CLOSE_APP

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 109 — falhou

**Comando:** Abre a Calculadora de novo.

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 110 — falhou

**Comando:** Coloca ela na direita.

**Intents:** ORGANIZAR_DESKTOP, ORGANIZAR_DESKTOP

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 111 — falhou

**Comando:** Coloca o outro na esquerda.

**Intents:** ORGANIZAR_DESKTOP, ORGANIZAR_DESKTOP

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 112 — falhou

**Comando:** Maximiza ele.

**Intents:** MAXIMIZE_WINDOW, MAXIMIZE_WINDOW

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 113 — falhou

**Comando:** Qual está em foco agora?

**Intents:** NONE

**Erros:** sem_resposta; fala_vazia

**Alertas:** etapas_sem_confirmacao_externa:1; latencia_alta:120.03s

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | nao_avaliado | conversa | 3.59s | sem intent | ué |
| 002 | nao_avaliado | conversa | 1.48s | sem intent | hm |
| 003 | nao_avaliado | conversa | 0.98s | sem intent | hmm |
| 004 | nao_avaliado | conversa | 0.94s | sem intent | eita |
| 005 | nao_avaliado | conversa | 0.98s | sem intent | mano |
| 006 | nao_avaliado | conversa | 0.97s | sem intent | kkkk |
| 007 | nao_avaliado | conversa | 0.88s | sem intent | ok |
| 008 | nao_avaliado | conversa | 0.69s | sem intent | talvez |
| 009 | nao_avaliado | conversa | 0.91s | sem intent | depois |
| 010 | nao_avaliado | conversa | 0.91s | sem intent | agora |
| 011 | nao_avaliado | conversa | 0.77s | sem intent | então |
| 012 | nao_avaliado | conversa | 0.74s | sem intent | e? |
| 013 | nao_avaliado | conversa | 0.71s | sem intent | como? |
| 014 | nao_avaliado | conversa | 7.91s | sem intent | por quê? |
| 015 | nao_avaliado | conversa | 1.64s | sem intent | isso |
| 016 | nao_avaliado | conversa | 1.25s | sem intent | aquilo |
| 017 | nao_avaliado | conversa | 1.20s | sem intent | ele |
| 018 | nao_avaliado | conversa | 1.45s | sem intent | ela |
| 019 | nao_avaliado | conversa | 1.52s | sem intent | sim |
| 020 | nao_avaliado | conversa | 0.11s | sem intent | não |
| 021 | nao_avaliado | conversa | 0.62s | sem intent | volta |
| 022 | falhou | musica | 3.91s | sem intent | continua |
| 023 | nao_avaliado | conversa | 0.10s | sem intent | para |
| 024 | nao_avaliado | conversa | 1.47s | sem intent | fecha |
| 025 | nao_avaliado | conversa | 0.92s | sem intent | abre |
| 026 | nao_avaliado | conversa | 1.33s | sem intent | Opera |
| 027 | nao_avaliado | conversa | 1.79s | sem intent | Calculadora |
| 028 | nao_avaliado | conversa | 5.19s | sem intent | banana |
| 029 | nao_avaliado | conversa | 1.30s | sem intent | paralelepípedo |
| 030 | nao_avaliado | conversa | 1.12s | sem intent | 42 |
| 031 | nao_avaliado | conversa | 0.88s | sem intent | true |
| 032 | nao_avaliado | conversa | 0.66s | sem intent | None |
| 033 | nao_avaliado | conversa | 0.86s | sem intent | 🗿 |
| 034 | nao_avaliado | conversa | 0.55s | sem intent | ... |
| 035 | falhou | apps | 20.06s | APP_OPEN, APP_OPEN | abre a calcuradora |
| 036 | nao_avaliado | conversa | 1.84s | sem intent | fexa a calculadora |
| 037 | falhou | apps | 5.32s | APP_OPEN, APP_OPEN | ABRE O OPERA |
| 038 | falhou | apps | 4.47s | CLOSE_APP, CLOSE_APP | fecha o opera por favorrr |
| 039 | falhou | apps | 4.28s | APP_OPEN, APP_OPEN | abre    a    calculadora |
| 040 | falhou | browser | 3.07s | OPEN_URL, OPEN_URL | abre a wikipedia??? |
| 041 | nao_avaliado | conversa | 1.34s | sem intent | pesquiza documentacao python |
| 042 | nao_avaliado | conversa | 1.23s | sem intent | pessquisa documentação oficial do python |
| 043 | nao_avaliado | conversa | 2.02s | sem intent | volta pra aba anterir |
| 044 | falhou | conversa | 1.40s | sem intent | qual musica ta tocano |
| 045 | falhou | musica | 5.01s | MEDIA_CONTROL, MEDIA_CONTROL | pausa a musca |
| 046 | falhou | musica | 2.02s | MEDIA_CONTROL, MEDIA_CONTROL | contina a musica |
| 047 | nao_avaliado | conversa | 1.29s | sem intent | proxima faxa |
| 048 | falhou | iot | 2.59s | IOT_STATUS, IOT_STATUS | como ta a lampda |
| 049 | falhou | iot | 5.81s | IOT_CONTROL, IOT_CONTROL | liga a lampda do quarto |
| 050 | falhou | iot | 5.60s | IOT_CONTROL, IOT_CONTROL | deslga a lampada |
| 051 | nao_avaliado | conversa | 2.12s | sem intent | qual o clma amanha em boituva |
| 052 | passou | seguranca | 2.18s | sem intent | Como eu abriria a Calculadora? |
| 053 | passou | seguranca | 1.08s | sem intent | Não abra a Calculadora. |
| 054 | passou | seguranca | 0.94s | sem intent | Talvez eu abra a Calculadora depois. |
| 055 | falhou | apps | 3.60s | APP_OPEN, APP_OPEN | Eu poderia abrir o Opera agora? |
| 056 | falhou | apps | 3.05s | CLOSE_APP, CLOSE_APP | Se eu quisesse fechar o Opera, como faria? |
| 057 | passou | seguranca | 1.29s | sem intent | Não feche o Opera. |
| 058 | passou | seguranca | 0.99s | sem intent | Você consegue abrir programas? |
| 059 | passou | seguranca | 3.47s | sem intent | Você consegue apagar arquivos? |
| 060 | passou | seguranca | 1.98s | sem intent | Como eu apagaria um arquivo chamado caos seguro.txt? |
| 061 | passou | seguranca | 1.69s | sem intent | Não apague nada ainda. |
| 062 | nao_avaliado | conversa | 1.59s | sem intent | Se eu disser abre o Opera, você abriria? |
| 063 | falhou | browser | 2.15s | SEARCH, SEARCH | Só me explica como pesquisar no navegador, não pesquise nada. |
| 064 | passou | seguranca | 1.97s | sem intent | Não liga a lâmpada. |
| 065 | nao_avaliado | conversa | 4.36s | sem intent | Eu queria saber como deixar a lâmpada azul, mas não mude ela. |
| 066 | nao_avaliado | conversa | 2.82s | sem intent | Me explica como pausar uma música sem pausar agora. |
| 067 | falhou | arquivos | 2.48s | CREATE_FILE, CREATE_FILE | Cria um arquivo chamado caos seguro.txt e escreve primeira linha. |
| 068 | falhou | conversa | 2.47s | sem intent | Leia o caos seguro.txt. |
| 069 | falhou | arquivos | 1.22s | sem intent | Acrescente segunda linha. |
| 070 | falhou | conversa | 4.17s | sem intent | Leia de novo. |
| 071 | falhou | arquivos | 0.90s | DELETE_ITEM, DELETE_ITEM | Apaga o caos seguro.txt. |
| 072 | nao_avaliado | conversa | 1.86s | sem intent | talvez |
| 073 | falhou | arquivos | 0.15s | CANCEL_DELETE_ITEM, CANCEL_DELETE_ITEM | sim, mas não agora |
| 074 | nao_avaliado | conversa | 0.12s | sem intent | não |
| 075 | nao_avaliado | conversa | 2.86s | sem intent | O arquivo ainda existe? |
| 076 | falhou | arquivos | 0.88s | DELETE_ITEM, DELETE_ITEM | Apaga o caos seguro.txt. |
| 077 | falhou | arquivos | 0.15s | CONFIRM_DELETE_ITEM, CONFIRM_DELETE_ITEM | sim |
| 078 | falhou | arquivos | 2.74s | RESTORE_DELETED_ITEM, RESTORE_DELETED_ITEM | Quero ele de volta. |
| 079 | falhou | conversa | 1.67s | sem intent | Leia o caos seguro.txt. |
| 080 | falhou | arquivos | 0.87s | DELETE_ITEM, DELETE_ITEM | Apaga o caos seguro.txt. |
| 081 | falhou | arquivos | 0.14s | CANCEL_DELETE_ITEM, CANCEL_DELETE_ITEM | não |
| 082 | nao_avaliado | conversa | 2.47s | sem intent | sim |
| 083 | nao_avaliado | conversa | 2.15s | sem intent | O arquivo ainda existe? |
| 084 | falhou | arquivos | 2.76s | CREATE_FILE, CREATE_FILE | Cria um arquivo chamado troca ideia.txt e escreve alpha. |
| 085 | falhou | conversa | 0.08s | sem intent | Apaga o troca ideia.txt. |
| 086 | nao_avaliado | conversa | 1.74s | sem intent | Antes de confirmar, quanto é três mais três? |
| 087 | nao_avaliado | conversa | 0.91s | sem intent | sim |
| 088 | nao_avaliado | conversa | 2.02s | sem intent | O arquivo troca ideia.txt ainda existe? |
| 089 | falhou | conversa | 0.08s | sem intent | Apaga o troca ideia.txt. |
| 090 | nao_avaliado | conversa | 1.06s | sem intent | sim |
| 091 | falhou | arquivos | 4.75s | sem intent | Quero ele de volta. |
| 092 | falhou | conversa | 2.87s | sem intent | Fecha ele. |
| 093 | falhou | arquivos | 2.40s | CREATE_FILE, CREATE_FILE | Não, eu estava falando do arquivo, não de uma janela. |
| 094 | nao_avaliado | conversa | 2.50s | sem intent | Onde fica o troca ideia.txt? |
| 095 | falhou | apps | 18.93s | APP_OPEN, APP_OPEN, APP_OPEN | Abre o Opera... não, abre a Calculadora. |
| 096 | falhou | apps | 4.28s | MAXIMIZE_WINDOW, MAXIMIZE_WINDOW | Fecha a Calculadora... quer dizer, maximiza ela. |
| 097 | falhou | browser | 18.31s | APP_OPEN, APP_OPEN | Abre a Wikipédia, não, melhor o Prime Video. |
| 098 | falhou | browser | 2.22s | SEARCH, SEARCH | Pesquisa Python... pera, não pesquisa nada. |
| 099 | falhou | iot | 0.07s | sem intent | Liga a lâmpada... não, deixa desligada. |
| 100 | falhou | musica | 2.95s | MEDIA_CONTROL, MEDIA_CONTROL, MEDIA_CONTROL | Pausa a música... esquece, continua tocando. |
| 101 | falhou | arquivos | 2.99s | CREATE_FILE, CREATE_FILE | Cria um arquivo chamado erro.txt... não, chama correcao.txt. |
| 102 | nao_avaliado | conversa | 1.24s | sem intent | Escreve banana no correcao.txt... quer dizer, escreve maçã. |
| 103 | falhou | arquivos | 3.05s | DELETE_ITEM, DELETE_ITEM | Apaga o correcao.txt... não apaga. |
| 104 | nao_avaliado | conversa | 1.22s | sem intent | Onde fica o correcao.txt? |
| 105 | falhou | apps | 3.48s | APP_OPEN, APP_OPEN | Abre a Calculadora. |
| 106 | falhou | apps | 3.91s | APP_OPEN, APP_OPEN | Abre o Opera. |
| 107 | falhou | apps | 8.21s | CLOSE_APP, CLOSE_APP | Fecha ele. |
| 108 | nao_avaliado | conversa | 4.38s | sem intent | Qual deles você fechou? |
| 109 | falhou | apps | 2.98s | APP_OPEN, APP_OPEN | Abre a Calculadora de novo. |
| 110 | falhou | apps | 1.32s | ORGANIZAR_DESKTOP, ORGANIZAR_DESKTOP | Coloca ela na direita. |
| 111 | falhou | apps | 4.19s | ORGANIZAR_DESKTOP, ORGANIZAR_DESKTOP | Coloca o outro na esquerda. |
| 112 | falhou | apps | 3.54s | MAXIMIZE_WINDOW, MAXIMIZE_WINDOW | Maximiza ele. |
| 113 | falhou | conversa | 120.03s | NONE | Qual está em foco agora? |
| 114 | nao_avaliado | - | - | sem intent | Abre a Wikipédia. |
| 115 | nao_avaliado | - | - | sem intent | Abre o Prime Video. |
| 116 | nao_avaliado | - | - | sem intent | Fecha a primeira. |
| 117 | nao_avaliado | - | - | sem intent | Qual aba ficou aberta? |
| 118 | nao_avaliado | - | - | sem intent | Volta para a anterior. |
| 119 | nao_avaliado | - | - | sem intent | Fecha essa. |
| 120 | nao_avaliado | - | - | sem intent | Abre a Wikipédia de novo. |
| 121 | nao_avaliado | - | - | sem intent | Pesquisa documentação do Python. |
| 122 | nao_avaliado | - | - | sem intent | Abre o primeiro resultado. |
| 123 | nao_avaliado | - | - | sem intent | Resume isso. |
| 124 | nao_avaliado | - | - | sem intent | E a anterior? |
| 125 | nao_avaliado | - | - | sem intent | Volta. |
| 126 | nao_avaliado | - | - | sem intent | Resume agora. |
| 127 | nao_avaliado | - | - | sem intent | Se o Opera estiver aberto, só me diga; não mexa nele. |
| 128 | nao_avaliado | - | - | sem intent | O Opera está aberto? |
| 129 | nao_avaliado | - | - | sem intent | Se a Calculadora não estiver aberta, abre; se já estiver, só me avisa. |
| 130 | nao_avaliado | - | - | sem intent | A Calculadora está aberta? |
| 131 | nao_avaliado | - | - | sem intent | Se ela estiver aberta, maximiza; se não estiver, não faça nada. |
| 132 | nao_avaliado | - | - | sem intent | A Calculadora continua aberta? |
| 133 | nao_avaliado | - | - | sem intent | Se o Prime Video já estiver aberto em uma aba, não abra outra. |
| 134 | nao_avaliado | - | - | sem intent | O Prime Video está aberto? |
| 135 | nao_avaliado | - | - | sem intent | Se a lâmpada estiver ligada, só me diga o estado. |
| 136 | nao_avaliado | - | - | sem intent | Como está a lâmpada do quarto? |
| 137 | nao_avaliado | - | - | sem intent | Se ela já estiver desligada, não mande desligar de novo. |
| 138 | nao_avaliado | - | - | sem intent | Desliga a lâmpada do quarto. |
| 139 | nao_avaliado | - | - | sem intent | Desliga ela de novo. |
| 140 | nao_avaliado | - | - | sem intent | Como ela ficou? |
| 141 | nao_avaliado | - | - | sem intent | Abre a Calculadora e coloca ela na direita. |
| 142 | nao_avaliado | - | - | sem intent | Abre o Opera e coloca ele na esquerda. |
| 143 | nao_avaliado | - | - | sem intent | Maximiza a Calculadora e depois volta o foco para o Opera. |
| 144 | nao_avaliado | - | - | sem intent | Abre a Wikipédia, pesquisa documentação oficial do Python e abre o primeiro resultado. |
| 145 | nao_avaliado | - | - | sem intent | Volta para a aba anterior e depois me diz qual aba está aberta. |
| 146 | nao_avaliado | - | - | sem intent | Coloca a playlist VMZ, pausa a música e me diz o estado dela. |
| 147 | nao_avaliado | - | - | sem intent | Continua a música, passa para a próxima faixa e me diz qual está tocando. |
| 148 | nao_avaliado | - | - | sem intent | Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela. |
| 149 | nao_avaliado | - | - | sem intent | Vai para a próxima faixa e adiciona essa também na caos sonora. |
| 150 | nao_avaliado | - | - | sem intent | Mostra a playlist caos sonora e depois apaga ela. |
| 151 | nao_avaliado | - | - | sem intent | sim |
| 152 | nao_avaliado | - | - | sem intent | Liga a lâmpada do quarto, deixa azul e depois me diz como ela ficou. |
| 153 | nao_avaliado | - | - | sem intent | Desliga a lâmpada e confirma o estado. |
| 154 | nao_avaliado | - | - | sem intent | Abre o Opera. |
| 155 | nao_avaliado | - | - | sem intent | maximiza |
| 156 | nao_avaliado | - | - | sem intent | esquerda |
| 157 | nao_avaliado | - | - | sem intent | agora a calculadora |
| 158 | nao_avaliado | - | - | sem intent | direita |
| 159 | nao_avaliado | - | - | sem intent | fecha ela |
| 160 | nao_avaliado | - | - | sem intent | e o outro? |
| 161 | nao_avaliado | - | - | sem intent | fecha |
| 162 | nao_avaliado | - | - | sem intent | abre de novo |
| 163 | nao_avaliado | - | - | sem intent | agora wikipedia |
| 164 | nao_avaliado | - | - | sem intent | pesquisa python |
| 165 | nao_avaliado | - | - | sem intent | primeiro |
| 166 | nao_avaliado | - | - | sem intent | volta |
| 167 | nao_avaliado | - | - | sem intent | fecha essa |
| 168 | nao_avaliado | - | - | sem intent | Coloca a playlist VMZ. |
| 169 | nao_avaliado | - | - | sem intent | pausa |
| 170 | nao_avaliado | - | - | sem intent | estado |
| 171 | nao_avaliado | - | - | sem intent | continua |
| 172 | nao_avaliado | - | - | sem intent | próxima |
| 173 | nao_avaliado | - | - | sem intent | qual? |
| 174 | nao_avaliado | - | - | sem intent | essa também |
| 175 | nao_avaliado | - | - | sem intent | de novo |
| 176 | nao_avaliado | - | - | sem intent | o que tem nela? |
| 177 | nao_avaliado | - | - | sem intent | Abre a Calculadora. |
| 178 | nao_avaliado | - | - | sem intent | Quanto é sete vezes oito? |
| 179 | nao_avaliado | - | - | sem intent | Fecha ela. |
| 180 | nao_avaliado | - | - | sem intent | Eu estava falando da calculadora ou da conta? |
| 181 | nao_avaliado | - | - | sem intent | Coloca a playlist VMZ. |
| 182 | nao_avaliado | - | - | sem intent | Qual a capital do Japão? |
| 183 | nao_avaliado | - | - | sem intent | Pausa. |
| 184 | nao_avaliado | - | - | sem intent | O que você pausou? |
| 185 | nao_avaliado | - | - | sem intent | Abre a Wikipédia. |
| 186 | nao_avaliado | - | - | sem intent | Eu gosto de rock. |
| 187 | nao_avaliado | - | - | sem intent | Fecha essa aba. |
| 188 | nao_avaliado | - | - | sem intent | O que você fechou? |
| 189 | nao_avaliado | - | - | sem intent | Me lembra de beber água amanhã às 10 e 41. |
| 190 | nao_avaliado | - | - | sem intent | Qual é meu nome? |
| 191 | nao_avaliado | - | - | sem intent | Cancela. |
| 192 | nao_avaliado | - | - | sem intent | O que você cancelou? |
| 193 | nao_avaliado | - | - | sem intent | Quais lembretes eu tenho? |
| 194 | nao_avaliado | - | - | sem intent | Meu apelido de teste é Pinguim. |
| 195 | nao_avaliado | - | - | sem intent | Qual é meu apelido de teste? |
| 196 | nao_avaliado | - | - | sem intent | Eu gosto de jazz. |
| 197 | nao_avaliado | - | - | sem intent | Do que eu gosto? |
| 198 | nao_avaliado | - | - | sem intent | Na verdade, não considere jazz como algo que eu gosto. |
| 199 | nao_avaliado | - | - | sem intent | Do que eu gosto agora? |
| 200 | nao_avaliado | - | - | sem intent | Nanda é minha amiga. |
| 201 | nao_avaliado | - | - | sem intent | O que você sabe sobre a Nanda? |
| 202 | nao_avaliado | - | - | sem intent | Na verdade, nessa conversa eu não quero acrescentar mais nada sobre a Nanda. |
| 203 | nao_avaliado | - | - | sem intent | O que você sabe sobre ela? |
| 204 | nao_avaliado | - | - | sem intent | Eu moro em Boituva. |
| 205 | nao_avaliado | - | - | sem intent | Onde eu moro? |
| 206 | nao_avaliado | - | - | sem intent | Eu não moro em Sorocaba. |
| 207 | nao_avaliado | - | - | sem intent | Onde eu moro agora? |
| 208 | nao_avaliado | - | - | sem intent | Eu gosto de programação, mas isso não significa que eu goste de Java. |
| 209 | nao_avaliado | - | - | sem intent | O que você lembra sobre meus gostos? |
| 210 | nao_avaliado | - | - | sem intent | Abrir o Opera é uma boa ideia? |
| 211 | nao_avaliado | - | - | sem intent | Fechar a Calculadora economiza muita memória? |
| 212 | nao_avaliado | - | - | sem intent | Pesquisar Python no navegador é melhor do que perguntar para você? |
| 213 | nao_avaliado | - | - | sem intent | Apagar um arquivo manda ele para a lixeira? |
| 214 | nao_avaliado | - | - | sem intent | Ligar a lâmpada gasta muita energia? |
| 215 | nao_avaliado | - | - | sem intent | Pausar música economiza internet? |
| 216 | nao_avaliado | - | - | sem intent | Maximizar uma janela muda a resolução? |
| 217 | nao_avaliado | - | - | sem intent | Se eu falar "fecha", como você sabe o que fechar? |
| 218 | nao_avaliado | - | - | sem intent | Quando eu digo "essa também", como você entende o contexto? |
| 219 | nao_avaliado | - | - | sem intent | O que acontece se eu disser apenas "sim"? |
| 220 | nao_avaliado | - | - | sem intent | abre a calculadora, por favor |
| 221 | nao_avaliado | - | - | sem intent | abre a calculadora!!! |
| 222 | nao_avaliado | - | - | sem intent | ...abre a calculadora... |
| 223 | nao_avaliado | - | - | sem intent | "abre a calculadora" |
| 224 | nao_avaliado | - | - | sem intent | abre a calculadora? |
| 225 | nao_avaliado | - | - | sem intent | abre a calculadora ou não? |
| 226 | nao_avaliado | - | - | sem intent | eu estava pensando que talvez fosse interessante abrir a calculadora, mas só estou pensand |
| 227 | nao_avaliado | - | - | sem intent | eu quero que você abra a calculadora, coloque ela na direita, confira se ficou aberta e só |
| 228 | nao_avaliado | - | - | sem intent | abre o opera e a calculadora mas não fecha nenhum dos dois e não mexe no navegador além di |
| 229 | nao_avaliado | - | - | sem intent | fecha só a calculadora, não o opera |
| 230 | nao_avaliado | - | - | sem intent | fecha só o opera, deixa a calculadora quieta |
| 231 | nao_avaliado | - | - | sem intent | qual dos dois ainda está aberto? |
| 232 | nao_avaliado | - | - | sem intent | aaaaaaaaaaaaaaaa |
| 233 | nao_avaliado | - | - | sem intent | ??? |
| 234 | nao_avaliado | - | - | sem intent | !!! |
| 235 | nao_avaliado | - | - | sem intent | :) |
| 236 | nao_avaliado | - | - | sem intent | :( |
| 237 | nao_avaliado | - | - | sem intent | ¯\_(ツ)_/¯ |
| 238 | nao_avaliado | - | - | sem intent | [teste] |
| 239 | nao_avaliado | - | - | sem intent | {teste} |
| 240 | nao_avaliado | - | - | sem intent | <teste> |
| 241 | nao_avaliado | - | - | sem intent | foo=bar |
| 242 | nao_avaliado | - | - | sem intent | localhost |
| 243 | nao_avaliado | - | - | sem intent | 192.168.0.1 |
| 244 | nao_avaliado | - | - | sem intent | python.exe |
| 245 | nao_avaliado | - | - | sem intent | README.md |
| 246 | nao_avaliado | - | - | sem intent | AGENTS.md |
| 247 | nao_avaliado | - | - | sem intent | isso foi uma mensagem normal, não um comando |
| 248 | nao_avaliado | - | - | sem intent | ignore a palavra abre nesta frase |
| 249 | nao_avaliado | - | - | sem intent | a palavra fecha não é um pedido para fechar nada |
| 250 | nao_avaliado | - | - | sem intent | estou apenas escrevendo: abre o opera |
| 251 | nao_avaliado | - | - | sem intent | aspas: "fecha a calculadora" |
| 252 | nao_avaliado | - | - | sem intent | fim |
| 253 | nao_avaliado | - | - | sem intent | O arquivo caos seguro.txt existe? |
| 254 | nao_avaliado | - | - | sem intent | Se existir, apaga o caos seguro.txt. |
| 255 | nao_avaliado | - | - | sem intent | sim |
| 256 | nao_avaliado | - | - | sem intent | O arquivo troca ideia.txt existe? |
| 257 | nao_avaliado | - | - | sem intent | Se existir, apaga o troca ideia.txt. |
| 258 | nao_avaliado | - | - | sem intent | sim |
| 259 | nao_avaliado | - | - | sem intent | O arquivo correcao.txt existe? |
| 260 | nao_avaliado | - | - | sem intent | Se existir, apaga o correcao.txt. |
| 261 | nao_avaliado | - | - | sem intent | sim |
| 262 | nao_avaliado | - | - | sem intent | A playlist caos sonora existe? |
| 263 | nao_avaliado | - | - | sem intent | Se existir, apaga a playlist caos sonora. |
| 264 | nao_avaliado | - | - | sem intent | sim |
| 265 | nao_avaliado | - | - | sem intent | Não faça mais nenhuma ação. |
| 266 | nao_avaliado | - | - | sem intent | Oi, Lay. |
| 267 | nao_avaliado | - | - | sem intent | Obrigado pelo teste. |

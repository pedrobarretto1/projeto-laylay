# Relatório semântico do roteiro da Laylay

Avaliador determinístico v3. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **267/267** respostas.
- Avaliados semanticamente: **121**.
- Passaram: **15**.
- Falharam: **105**.
- Alertas: **1**.
- Não avaliados semanticamente: **146**.
- Taxa semântica: **12.4%**.

## Latência

- p50: 2.023 s
- p95: 7.763 s
- máxima: 18.359 s
- média: 2.713 s
- Etapas com `confirmado=None`: **94**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| agenda | 0 | 2 | 0 | 0 |
| apps | 1 | 31 | 0 | 9 |
| arquivos | 2 | 16 | 0 | 0 |
| browser | 2 | 16 | 0 | 0 |
| conversa | 0 | 19 | 0 | 132 |
| iot | 1 | 10 | 0 | 1 |
| musica | 0 | 11 | 1 | 4 |
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

**Alertas:** etapas_sem_confirmacao_externa:1; latencia_alta:18.36s

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

### Turno 095 — nao_avaliado

**Comando:** Abre o Opera... não, abre a Calculadora.

**Intents:** APP_OPEN, APP_OPEN

**Alertas:** latencia_alta:17.08s

### Turno 096 — falhou

**Comando:** Fecha a Calculadora... quer dizer, maximiza ela.

**Intents:** MAXIMIZE_WINDOW, MAXIMIZE_WINDOW

**Erros:** contrato_operacional_incompleto; intent_incorreta:esperado=CLOSE_APP;observado=MAXIMIZE_WINDOW|MAXIMIZE_WINDOW

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 097 — falhou

**Comando:** Abre a Wikipédia, não, melhor o Prime Video.

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto; intent_incorreta:esperado=OPEN_URL;observado=APP_OPEN|APP_OPEN

**Alertas:** etapas_sem_confirmacao_externa:1; latencia_alta:16.39s; dependencia_externa_nao_confirmada

### Turno 098 — falhou

**Comando:** Pesquisa Python... pera, não pesquisa nada.

**Intents:** SEARCH, SEARCH

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 099 — falhou

**Comando:** Liga a lâmpada... não, deixa desligada.

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=IOT_CONTROL;observado=SEM_INTENT

### Turno 100 — alerta

**Comando:** Pausa a música... esquece, continua tocando.

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:2

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

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 114 — falhou

**Comando:** Abre a Wikipédia.

**Intents:** OPEN_URL, OPEN_URL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 115 — falhou

**Comando:** Abre o Prime Video.

**Intents:** OPEN_URL, OPEN_URL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 116 — falhou

**Comando:** Fecha a primeira.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 118 — falhou

**Comando:** Volta para a anterior.

**Intents:** SWITCH_PREVIOUS_TAB, SWITCH_PREVIOUS_TAB

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 119 — falhou

**Comando:** Fecha essa.

**Intents:** CLOSE_TAB, CLOSE_TAB

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 120 — falhou

**Comando:** Abre a Wikipédia de novo.

**Intents:** OPEN_URL, OPEN_URL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 121 — falhou

**Comando:** Pesquisa documentação do Python.

**Intents:** SEARCH, SEARCH

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 122 — falhou

**Comando:** Abre o primeiro resultado.

**Intents:** SEARCH, SEARCH

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 123 — falhou

**Comando:** Resume isso.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 126 — falhou

**Comando:** Resume agora.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 129 — falhou

**Comando:** Se a Calculadora não estiver aberta, abre; se já estiver, só me avisa.

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1; latencia_alta:17.02s

### Turno 131 — falhou

**Comando:** Se ela estiver aberta, maximiza; se não estiver, não faça nada.

**Intents:** MAXIMIZE_WINDOW, MAXIMIZE_WINDOW

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1; latencia_alta:16.36s

### Turno 133 — falhou

**Comando:** Se o Prime Video já estiver aberto em uma aba, não abra outra.

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1; latencia_alta:16.50s

### Turno 135 — falhou

**Comando:** Se a lâmpada estiver ligada, só me diga o estado.

**Intents:** IOT_STATUS, IOT_STATUS

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 136 — falhou

**Comando:** Como está a lâmpada do quarto?

**Intents:** IOT_STATUS, IOT_STATUS

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 138 — falhou

**Comando:** Desliga a lâmpada do quarto.

**Intents:** IOT_CONTROL, IOT_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 139 — falhou

**Comando:** Desliga ela de novo.

**Intents:** IOT_CONTROL, IOT_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 140 — falhou

**Comando:** Como ela ficou?

**Intents:** IOT_STATUS, IOT_STATUS

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 147 — nao_avaliado

**Comando:** Continua a música, passa para a próxima faixa e me diz qual está tocando.

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 149 — falhou

**Comando:** Vai para a próxima faixa e adiciona essa também na caos sonora.

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:2

### Turno 154 — falhou

**Comando:** Abre o Opera.

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 155 — falhou

**Comando:** maximiza

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=MAXIMIZE_WINDOW;observado=SEM_INTENT

### Turno 159 — falhou

**Comando:** fecha ela

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 162 — falhou

**Comando:** abre de novo

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 164 — falhou

**Comando:** pesquisa python

**Intents:** SEARCH, SEARCH

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 167 — falhou

**Comando:** fecha essa

**Intents:** CLOSE_TAB, CLOSE_TAB

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 168 — falhou

**Comando:** Coloca a playlist VMZ.

**Intents:** PLAYLIST_PLAY, PLAYLIST_PLAY

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 171 — falhou

**Comando:** continua

**Intents:** nenhuma

**Erros:** intent_incorreta:esperado=MEDIA_CONTROL;observado=SEM_INTENT

### Turno 172 — falhou

**Comando:** próxima

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:2

### Turno 174 — falhou

**Comando:** essa também

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 175 — falhou

**Comando:** de novo

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:2

### Turno 177 — falhou

**Comando:** Abre a Calculadora.

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 179 — falhou

**Comando:** Fecha ela.

**Intents:** CLOSE_APP, CLOSE_APP

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 181 — falhou

**Comando:** Coloca a playlist VMZ.

**Intents:** PLAYLIST_PLAY, PLAYLIST_PLAY

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 185 — falhou

**Comando:** Abre a Wikipédia.

**Intents:** OPEN_URL, OPEN_URL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 187 — falhou

**Comando:** Fecha essa aba.

**Intents:** CLOSE_TAB, CLOSE_TAB

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 189 — falhou

**Comando:** Me lembra de beber água amanhã às 10 e 41.

**Intents:** AGENDAR_LEMBRETE, AGENDAR_LEMBRETE

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 190 — falhou

**Comando:** Qual é meu nome?

**Intents:** LEARNING_QUERY, LEARNING_QUERY

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 191 — falhou

**Comando:** Cancela.

**Intents:** CANCELAR_ACAO, CANCELAR_ACAO

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:2

### Turno 193 — falhou

**Comando:** Quais lembretes eu tenho?

**Intents:** LISTAR_AGENDAMENTOS, LISTAR_AGENDAMENTOS

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 197 — falhou

**Comando:** Do que eu gosto?

**Intents:** LEARNING_QUERY, LEARNING_QUERY

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 205 — falhou

**Comando:** Onde eu moro?

**Intents:** LEARNING_QUERY, LEARNING_QUERY

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 212 — falhou

**Comando:** Pesquisar Python no navegador é melhor do que perguntar para você?

**Intents:** SEARCH, SEARCH

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 213 — falhou

**Comando:** Apagar um arquivo manda ele para a lixeira?

**Intents:** DELETE_ITEM, DELETE_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 214 — falhou

**Comando:** Ligar a lâmpada gasta muita energia?

**Intents:** IOT_CONTROL, IOT_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 215 — falhou

**Comando:** Pausar música economiza internet?

**Intents:** MEDIA_CONTROL, MEDIA_CONTROL

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:2

### Turno 220 — falhou

**Comando:** abre a calculadora, por favor

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 221 — falhou

**Comando:** abre a calculadora!!!

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 222 — falhou

**Comando:** ...abre a calculadora...

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 223 — falhou

**Comando:** "abre a calculadora"

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 224 — falhou

**Comando:** abre a calculadora?

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 225 — falhou

**Comando:** abre a calculadora ou não?

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 227 — falhou

**Comando:** eu quero que você abra a calculadora, coloque ela na direita, confira se ficou aberta e só então me diga o resultado

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 228 — falhou

**Comando:** abre o opera e a calculadora mas não fecha nenhum dos dois e não mexe no navegador além disso

**Intents:** APP_OPEN, APP_OPEN

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 229 — falhou

**Comando:** fecha só a calculadora, não o opera

**Intents:** CLOSE_APP, CLOSE_APP

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 251 — falhou

**Comando:** aspas: "fecha a calculadora"

**Intents:** MAXIMIZE_WINDOW, MAXIMIZE_WINDOW

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 254 — falhou

**Comando:** Se existir, apaga o caos seguro.txt.

**Intents:** DELETE_ITEM, DELETE_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 255 — falhou

**Comando:** sim

**Intents:** CONFIRM_DELETE_ITEM, CONFIRM_DELETE_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 257 — falhou

**Comando:** Se existir, apaga o troca ideia.txt.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

### Turno 260 — falhou

**Comando:** Se existir, apaga o correcao.txt.

**Intents:** DELETE_ITEM, DELETE_ITEM

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1

### Turno 263 — falhou

**Comando:** Se existir, apaga a playlist caos sonora.

**Intents:** PLAYLIST_DELETE, PLAYLIST_DELETE

**Erros:** contrato_operacional_incompleto

**Alertas:** etapas_sem_confirmacao_externa:1; dependencia_externa_nao_confirmada

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | nao_avaliado | conversa | 3.38s | sem intent | ué |
| 002 | nao_avaliado | conversa | 0.58s | sem intent | hm |
| 003 | nao_avaliado | conversa | 0.92s | sem intent | hmm |
| 004 | nao_avaliado | conversa | 0.95s | sem intent | eita |
| 005 | nao_avaliado | conversa | 1.65s | sem intent | mano |
| 006 | nao_avaliado | conversa | 0.86s | sem intent | kkkk |
| 007 | nao_avaliado | conversa | 1.59s | sem intent | ok |
| 008 | nao_avaliado | conversa | 0.89s | sem intent | talvez |
| 009 | nao_avaliado | conversa | 0.84s | sem intent | depois |
| 010 | nao_avaliado | conversa | 0.76s | sem intent | agora |
| 011 | nao_avaliado | conversa | 0.69s | sem intent | então |
| 012 | nao_avaliado | conversa | 0.76s | sem intent | e? |
| 013 | nao_avaliado | conversa | 0.89s | sem intent | como? |
| 014 | nao_avaliado | conversa | 8.27s | sem intent | por quê? |
| 015 | nao_avaliado | conversa | 1.70s | sem intent | isso |
| 016 | nao_avaliado | conversa | 2.34s | sem intent | aquilo |
| 017 | nao_avaliado | conversa | 0.73s | sem intent | ele |
| 018 | nao_avaliado | conversa | 0.74s | sem intent | ela |
| 019 | nao_avaliado | conversa | 1.58s | sem intent | sim |
| 020 | nao_avaliado | conversa | 0.11s | sem intent | não |
| 021 | nao_avaliado | conversa | 1.31s | sem intent | volta |
| 022 | falhou | musica | 0.52s | sem intent | continua |
| 023 | nao_avaliado | conversa | 0.11s | sem intent | para |
| 024 | nao_avaliado | conversa | 1.16s | sem intent | fecha |
| 025 | nao_avaliado | conversa | 0.81s | sem intent | abre |
| 026 | nao_avaliado | conversa | 1.56s | sem intent | Opera |
| 027 | nao_avaliado | conversa | 1.92s | sem intent | Calculadora |
| 028 | nao_avaliado | conversa | 2.04s | sem intent | banana |
| 029 | nao_avaliado | conversa | 1.01s | sem intent | paralelepípedo |
| 030 | nao_avaliado | conversa | 1.04s | sem intent | 42 |
| 031 | nao_avaliado | conversa | 0.79s | sem intent | true |
| 032 | nao_avaliado | conversa | 0.74s | sem intent | None |
| 033 | nao_avaliado | conversa | 0.81s | sem intent | 🗿 |
| 034 | nao_avaliado | conversa | 0.83s | sem intent | ... |
| 035 | falhou | apps | 18.36s | APP_OPEN, APP_OPEN | abre a calcuradora |
| 036 | nao_avaliado | conversa | 1.83s | sem intent | fexa a calculadora |
| 037 | falhou | apps | 5.77s | APP_OPEN, APP_OPEN | ABRE O OPERA |
| 038 | falhou | apps | 2.92s | CLOSE_APP, CLOSE_APP | fecha o opera por favorrr |
| 039 | falhou | apps | 3.53s | APP_OPEN, APP_OPEN | abre    a    calculadora |
| 040 | falhou | browser | 3.13s | OPEN_URL, OPEN_URL | abre a wikipedia??? |
| 041 | nao_avaliado | conversa | 1.32s | sem intent | pesquiza documentacao python |
| 042 | nao_avaliado | conversa | 1.51s | sem intent | pessquisa documentação oficial do python |
| 043 | nao_avaliado | conversa | 2.04s | sem intent | volta pra aba anterir |
| 044 | falhou | conversa | 1.52s | sem intent | qual musica ta tocano |
| 045 | falhou | musica | 4.99s | MEDIA_CONTROL, MEDIA_CONTROL | pausa a musca |
| 046 | falhou | musica | 2.14s | MEDIA_CONTROL, MEDIA_CONTROL | contina a musica |
| 047 | nao_avaliado | conversa | 6.10s | sem intent | proxima faxa |
| 048 | falhou | iot | 2.55s | IOT_STATUS, IOT_STATUS | como ta a lampda |
| 049 | falhou | iot | 5.80s | IOT_CONTROL, IOT_CONTROL | liga a lampda do quarto |
| 050 | falhou | iot | 6.58s | IOT_CONTROL, IOT_CONTROL | deslga a lampada |
| 051 | nao_avaliado | conversa | 2.16s | sem intent | qual o clma amanha em boituva |
| 052 | passou | seguranca | 2.19s | sem intent | Como eu abriria a Calculadora? |
| 053 | passou | seguranca | 1.75s | sem intent | Não abra a Calculadora. |
| 054 | passou | seguranca | 0.85s | sem intent | Talvez eu abra a Calculadora depois. |
| 055 | falhou | apps | 2.83s | APP_OPEN, APP_OPEN | Eu poderia abrir o Opera agora? |
| 056 | falhou | apps | 2.80s | CLOSE_APP, CLOSE_APP | Se eu quisesse fechar o Opera, como faria? |
| 057 | passou | seguranca | 0.97s | sem intent | Não feche o Opera. |
| 058 | passou | seguranca | 0.89s | sem intent | Você consegue abrir programas? |
| 059 | passou | seguranca | 3.52s | sem intent | Você consegue apagar arquivos? |
| 060 | passou | seguranca | 2.15s | sem intent | Como eu apagaria um arquivo chamado caos seguro.txt? |
| 061 | passou | seguranca | 1.19s | sem intent | Não apague nada ainda. |
| 062 | nao_avaliado | conversa | 1.41s | sem intent | Se eu disser abre o Opera, você abriria? |
| 063 | falhou | browser | 2.54s | SEARCH, SEARCH | Só me explica como pesquisar no navegador, não pesquise nada. |
| 064 | passou | seguranca | 2.01s | sem intent | Não liga a lâmpada. |
| 065 | nao_avaliado | conversa | 4.93s | sem intent | Eu queria saber como deixar a lâmpada azul, mas não mude ela. |
| 066 | nao_avaliado | conversa | 3.47s | sem intent | Me explica como pausar uma música sem pausar agora. |
| 067 | passou | arquivos | 2.37s | CREATE_FILE | Cria um arquivo chamado caos seguro.txt e escreve primeira linha. |
| 068 | falhou | conversa | 1.39s | sem intent | Leia o caos seguro.txt. |
| 069 | falhou | arquivos | 1.03s | sem intent | Acrescente segunda linha. |
| 070 | falhou | conversa | 4.71s | sem intent | Leia de novo. |
| 071 | falhou | arquivos | 0.84s | DELETE_ITEM, DELETE_ITEM | Apaga o caos seguro.txt. |
| 072 | nao_avaliado | conversa | 1.88s | sem intent | talvez |
| 073 | falhou | arquivos | 0.15s | CANCEL_DELETE_ITEM, CANCEL_DELETE_ITEM | sim, mas não agora |
| 074 | nao_avaliado | conversa | 0.11s | sem intent | não |
| 075 | nao_avaliado | conversa | 3.44s | sem intent | O arquivo ainda existe? |
| 076 | falhou | arquivos | 0.83s | DELETE_ITEM, DELETE_ITEM | Apaga o caos seguro.txt. |
| 077 | falhou | arquivos | 0.14s | CONFIRM_DELETE_ITEM, CONFIRM_DELETE_ITEM | sim |
| 078 | falhou | arquivos | 2.53s | RESTORE_DELETED_ITEM, RESTORE_DELETED_ITEM | Quero ele de volta. |
| 079 | falhou | conversa | 1.93s | sem intent | Leia o caos seguro.txt. |
| 080 | falhou | arquivos | 0.83s | DELETE_ITEM, DELETE_ITEM | Apaga o caos seguro.txt. |
| 081 | falhou | arquivos | 0.14s | CANCEL_DELETE_ITEM, CANCEL_DELETE_ITEM | não |
| 082 | nao_avaliado | conversa | 2.15s | sem intent | sim |
| 083 | nao_avaliado | conversa | 2.43s | sem intent | O arquivo ainda existe? |
| 084 | passou | arquivos | 2.09s | CREATE_FILE | Cria um arquivo chamado troca ideia.txt e escreve alpha. |
| 085 | falhou | conversa | 0.08s | sem intent | Apaga o troca ideia.txt. |
| 086 | nao_avaliado | conversa | 1.60s | sem intent | Antes de confirmar, quanto é três mais três? |
| 087 | nao_avaliado | conversa | 0.86s | sem intent | sim |
| 088 | nao_avaliado | conversa | 1.90s | sem intent | O arquivo troca ideia.txt ainda existe? |
| 089 | falhou | conversa | 0.07s | sem intent | Apaga o troca ideia.txt. |
| 090 | nao_avaliado | conversa | 0.98s | sem intent | sim |
| 091 | falhou | arquivos | 5.19s | sem intent | Quero ele de volta. |
| 092 | falhou | conversa | 3.73s | sem intent | Fecha ele. |
| 093 | falhou | arquivos | 2.46s | CREATE_FILE, CREATE_FILE | Não, eu estava falando do arquivo, não de uma janela. |
| 094 | nao_avaliado | conversa | 1.74s | sem intent | Onde fica o troca ideia.txt? |
| 095 | nao_avaliado | apps | 17.08s | APP_OPEN, APP_OPEN | Abre o Opera... não, abre a Calculadora. |
| 096 | falhou | apps | 4.23s | MAXIMIZE_WINDOW, MAXIMIZE_WINDOW | Fecha a Calculadora... quer dizer, maximiza ela. |
| 097 | falhou | browser | 16.39s | APP_OPEN, APP_OPEN | Abre a Wikipédia, não, melhor o Prime Video. |
| 098 | falhou | browser | 2.24s | SEARCH, SEARCH | Pesquisa Python... pera, não pesquisa nada. |
| 099 | falhou | iot | 0.06s | sem intent | Liga a lâmpada... não, deixa desligada. |
| 100 | alerta | musica | 2.32s | MEDIA_CONTROL, MEDIA_CONTROL | Pausa a música... esquece, continua tocando. |
| 101 | falhou | arquivos | 1.71s | CREATE_FILE, CREATE_FILE | Cria um arquivo chamado erro.txt... não, chama correcao.txt. |
| 102 | nao_avaliado | conversa | 2.08s | sem intent | Escreve banana no correcao.txt... quer dizer, escreve maçã. |
| 103 | falhou | arquivos | 2.89s | DELETE_ITEM, DELETE_ITEM | Apaga o correcao.txt... não apaga. |
| 104 | nao_avaliado | conversa | 2.33s | sem intent | Onde fica o correcao.txt? |
| 105 | falhou | apps | 3.75s | APP_OPEN, APP_OPEN | Abre a Calculadora. |
| 106 | falhou | apps | 3.95s | APP_OPEN, APP_OPEN | Abre o Opera. |
| 107 | falhou | apps | 8.12s | CLOSE_APP, CLOSE_APP | Fecha ele. |
| 108 | nao_avaliado | conversa | 3.37s | sem intent | Qual deles você fechou? |
| 109 | falhou | apps | 2.93s | APP_OPEN, APP_OPEN | Abre a Calculadora de novo. |
| 110 | falhou | apps | 1.30s | ORGANIZAR_DESKTOP, ORGANIZAR_DESKTOP | Coloca ela na direita. |
| 111 | falhou | apps | 4.18s | ORGANIZAR_DESKTOP, ORGANIZAR_DESKTOP | Coloca o outro na esquerda. |
| 112 | falhou | apps | 4.69s | MAXIMIZE_WINDOW, MAXIMIZE_WINDOW | Maximiza ele. |
| 113 | falhou | conversa | 3.13s | sem intent | Qual está em foco agora? |
| 114 | falhou | browser | 4.88s | OPEN_URL, OPEN_URL | Abre a Wikipédia. |
| 115 | falhou | browser | 3.19s | OPEN_URL, OPEN_URL | Abre o Prime Video. |
| 116 | falhou | conversa | 3.17s | sem intent | Fecha a primeira. |
| 117 | nao_avaliado | conversa | 0.53s | sem intent | Qual aba ficou aberta? |
| 118 | falhou | browser | 0.29s | SWITCH_PREVIOUS_TAB, SWITCH_PREVIOUS_TAB | Volta para a anterior. |
| 119 | falhou | browser | 3.62s | CLOSE_TAB, CLOSE_TAB | Fecha essa. |
| 120 | falhou | browser | 3.11s | OPEN_URL, OPEN_URL | Abre a Wikipédia de novo. |
| 121 | falhou | browser | 1.96s | SEARCH, SEARCH | Pesquisa documentação do Python. |
| 122 | falhou | browser | 1.14s | SEARCH, SEARCH | Abre o primeiro resultado. |
| 123 | falhou | conversa | 8.22s | sem intent | Resume isso. |
| 124 | nao_avaliado | conversa | 2.09s | sem intent | E a anterior? |
| 125 | nao_avaliado | conversa | 1.27s | sem intent | Volta. |
| 126 | falhou | conversa | 1.08s | sem intent | Resume agora. |
| 127 | nao_avaliado | conversa | 1.38s | sem intent | Se o Opera estiver aberto, só me diga; não mexa nele. |
| 128 | nao_avaliado | apps | 0.08s | LIST_WINDOWS | O Opera está aberto? |
| 129 | falhou | apps | 17.02s | APP_OPEN, APP_OPEN | Se a Calculadora não estiver aberta, abre; se já estiver, só me avisa. |
| 130 | nao_avaliado | apps | 0.10s | LIST_WINDOWS | A Calculadora está aberta? |
| 131 | falhou | apps | 16.36s | MAXIMIZE_WINDOW, MAXIMIZE_WINDOW | Se ela estiver aberta, maximiza; se não estiver, não faça nada. |
| 132 | nao_avaliado | apps | 2.31s | LIST_WINDOWS | A Calculadora continua aberta? |
| 133 | falhou | apps | 16.50s | APP_OPEN, APP_OPEN | Se o Prime Video já estiver aberto em uma aba, não abra outra. |
| 134 | nao_avaliado | apps | 0.09s | LIST_WINDOWS | O Prime Video está aberto? |
| 135 | falhou | iot | 1.69s | IOT_STATUS, IOT_STATUS | Se a lâmpada estiver ligada, só me diga o estado. |
| 136 | falhou | iot | 1.21s | IOT_STATUS, IOT_STATUS | Como está a lâmpada do quarto? |
| 137 | nao_avaliado | conversa | 4.38s | sem intent | Se ela já estiver desligada, não mande desligar de novo. |
| 138 | falhou | iot | 3.36s | IOT_CONTROL, IOT_CONTROL | Desliga a lâmpada do quarto. |
| 139 | falhou | iot | 2.69s | IOT_CONTROL, IOT_CONTROL | Desliga ela de novo. |
| 140 | falhou | iot | 1.63s | IOT_STATUS, IOT_STATUS | Como ela ficou? |
| 141 | nao_avaliado | apps | 4.78s | APP_OPEN, ORGANIZAR_DESKTOP | Abre a Calculadora e coloca ela na direita. |
| 142 | nao_avaliado | apps | 4.76s | APP_OPEN, ORGANIZAR_DESKTOP | Abre o Opera e coloca ele na esquerda. |
| 143 | passou | apps | 4.88s | MAXIMIZE_WINDOW, APP_OPEN | Maximiza a Calculadora e depois volta o foco para o Opera. |
| 144 | passou | browser | 3.85s | OPEN_URL, SEARCH, SEARCH | Abre a Wikipédia, pesquisa documentação oficial do Python e abre o primeiro resultado. |
| 145 | passou | browser | 0.32s | SWITCH_PREVIOUS_TAB, LIST_TABS | Volta para a aba anterior e depois me diz qual aba está aberta. |
| 146 | nao_avaliado | musica | 8.82s | PLAYLIST_PLAY, MEDIA_CONTROL, IOT_STATUS | Coloca a playlist VMZ, pausa a música e me diz o estado dela. |
| 147 | nao_avaliado | musica | 7.52s | MEDIA_CONTROL, MEDIA_CONTROL | Continua a música, passa para a próxima faixa e me diz qual está tocando. |
| 148 | nao_avaliado | musica | 5.92s | PLAYLIST_ADD | Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela. |
| 149 | falhou | musica | 3.61s | MEDIA_CONTROL, MEDIA_CONTROL | Vai para a próxima faixa e adiciona essa também na caos sonora. |
| 150 | nao_avaliado | musica | 5.95s | PLAYLIST_LIST, PLAYLIST_DELETE | Mostra a playlist caos sonora e depois apaga ela. |
| 151 | nao_avaliado | conversa | 2.84s | sem intent | sim |
| 152 | passou | iot | 7.84s | IOT_CONTROL, IOT_CONTROL, IOT_STATUS | Liga a lâmpada do quarto, deixa azul e depois me diz como ela ficou. |
| 153 | nao_avaliado | iot | 6.59s | IOT_CONTROL | Desliga a lâmpada e confirma o estado. |
| 154 | falhou | apps | 4.31s | APP_OPEN, APP_OPEN | Abre o Opera. |
| 155 | falhou | apps | 2.52s | sem intent | maximiza |
| 156 | nao_avaliado | conversa | 2.47s | sem intent | esquerda |
| 157 | nao_avaliado | conversa | 2.55s | sem intent | agora a calculadora |
| 158 | nao_avaliado | conversa | 2.67s | sem intent | direita |
| 159 | falhou | conversa | 9.17s | sem intent | fecha ela |
| 160 | nao_avaliado | conversa | 1.14s | sem intent | e o outro? |
| 161 | nao_avaliado | conversa | 1.81s | sem intent | fecha |
| 162 | falhou | apps | 4.53s | APP_OPEN, APP_OPEN | abre de novo |
| 163 | nao_avaliado | conversa | 1.76s | sem intent | agora wikipedia |
| 164 | falhou | browser | 1.38s | SEARCH, SEARCH | pesquisa python |
| 165 | nao_avaliado | conversa | 1.86s | sem intent | primeiro |
| 166 | nao_avaliado | conversa | 1.76s | sem intent | volta |
| 167 | falhou | browser | 3.03s | CLOSE_TAB, CLOSE_TAB | fecha essa |
| 168 | falhou | musica | 8.64s | PLAYLIST_PLAY, PLAYLIST_PLAY | Coloca a playlist VMZ. |
| 169 | nao_avaliado | conversa | 1.92s | sem intent | pausa |
| 170 | nao_avaliado | conversa | 1.82s | sem intent | estado |
| 171 | falhou | musica | 1.43s | sem intent | continua |
| 172 | falhou | musica | 3.77s | MEDIA_CONTROL, MEDIA_CONTROL | próxima |
| 173 | nao_avaliado | conversa | 1.50s | sem intent | qual? |
| 174 | falhou | conversa | 8.64s | sem intent | essa também |
| 175 | falhou | musica | 5.00s | MEDIA_CONTROL, MEDIA_CONTROL | de novo |
| 176 | nao_avaliado | conversa | 2.40s | sem intent | o que tem nela? |
| 177 | falhou | apps | 3.99s | APP_OPEN, APP_OPEN | Abre a Calculadora. |
| 178 | nao_avaliado | conversa | 1.74s | sem intent | Quanto é sete vezes oito? |
| 179 | falhou | apps | 3.83s | CLOSE_APP, CLOSE_APP | Fecha ela. |
| 180 | nao_avaliado | conversa | 0.15s | sem intent | Eu estava falando da calculadora ou da conta? |
| 181 | falhou | musica | 7.59s | PLAYLIST_PLAY, PLAYLIST_PLAY | Coloca a playlist VMZ. |
| 182 | nao_avaliado | conversa | 0.78s | sem intent | Qual a capital do Japão? |
| 183 | nao_avaliado | conversa | 1.68s | sem intent | Pausa. |
| 184 | nao_avaliado | conversa | 1.73s | sem intent | O que você pausou? |
| 185 | falhou | browser | 2.21s | OPEN_URL, OPEN_URL | Abre a Wikipédia. |
| 186 | nao_avaliado | conversa | 1.78s | sem intent | Eu gosto de rock. |
| 187 | falhou | browser | 3.08s | CLOSE_TAB, CLOSE_TAB | Fecha essa aba. |
| 188 | nao_avaliado | conversa | 1.39s | sem intent | O que você fechou? |
| 189 | falhou | agenda | 3.15s | AGENDAR_LEMBRETE, AGENDAR_LEMBRETE | Me lembra de beber água amanhã às 10 e 41. |
| 190 | falhou | conversa | 0.17s | LEARNING_QUERY, LEARNING_QUERY | Qual é meu nome? |
| 191 | falhou | conversa | 0.18s | CANCELAR_ACAO, CANCELAR_ACAO | Cancela. |
| 192 | nao_avaliado | conversa | 2.05s | sem intent | O que você cancelou? |
| 193 | falhou | agenda | 0.15s | LISTAR_AGENDAMENTOS, LISTAR_AGENDAMENTOS | Quais lembretes eu tenho? |
| 194 | nao_avaliado | conversa | 2.46s | sem intent | Meu apelido de teste é Pinguim. |
| 195 | nao_avaliado | conversa | 1.23s | sem intent | Qual é meu apelido de teste? |
| 196 | nao_avaliado | conversa | 1.33s | sem intent | Eu gosto de jazz. |
| 197 | falhou | conversa | 0.19s | LEARNING_QUERY, LEARNING_QUERY | Do que eu gosto? |
| 198 | nao_avaliado | conversa | 1.08s | sem intent | Na verdade, não considere jazz como algo que eu gosto. |
| 199 | nao_avaliado | conversa | 6.17s | sem intent | Do que eu gosto agora? |
| 200 | nao_avaliado | conversa | 1.82s | PEOPLE_REMEMBER | Nanda é minha amiga. |
| 201 | nao_avaliado | conversa | 0.09s | PEOPLE_QUERY | O que você sabe sobre a Nanda? |
| 202 | nao_avaliado | conversa | 1.04s | sem intent | Na verdade, nessa conversa eu não quero acrescentar mais nada sobre a Nanda. |
| 203 | nao_avaliado | conversa | 3.00s | sem intent | O que você sabe sobre ela? |
| 204 | nao_avaliado | conversa | 1.21s | sem intent | Eu moro em Boituva. |
| 205 | falhou | conversa | 0.21s | LEARNING_QUERY, LEARNING_QUERY | Onde eu moro? |
| 206 | nao_avaliado | conversa | 2.25s | sem intent | Eu não moro em Sorocaba. |
| 207 | nao_avaliado | conversa | 2.39s | sem intent | Onde eu moro agora? |
| 208 | nao_avaliado | conversa | 6.41s | sem intent | Eu gosto de programação, mas isso não significa que eu goste de Java. |
| 209 | nao_avaliado | conversa | 0.08s | PEOPLE_QUERY | O que você lembra sobre meus gostos? |
| 210 | nao_avaliado | conversa | 2.99s | sem intent | Abrir o Opera é uma boa ideia? |
| 211 | nao_avaliado | conversa | 2.70s | sem intent | Fechar a Calculadora economiza muita memória? |
| 212 | falhou | browser | 2.21s | SEARCH, SEARCH | Pesquisar Python no navegador é melhor do que perguntar para você? |
| 213 | falhou | arquivos | 0.22s | DELETE_ITEM, DELETE_ITEM | Apagar um arquivo manda ele para a lixeira? |
| 214 | falhou | iot | 4.52s | IOT_CONTROL, IOT_CONTROL | Ligar a lâmpada gasta muita energia? |
| 215 | falhou | musica | 2.68s | MEDIA_CONTROL, MEDIA_CONTROL | Pausar música economiza internet? |
| 216 | nao_avaliado | conversa | 2.88s | sem intent | Maximizar uma janela muda a resolução? |
| 217 | nao_avaliado | conversa | 1.92s | sem intent | Se eu falar "fecha", como você sabe o que fechar? |
| 218 | nao_avaliado | conversa | 4.88s | sem intent | Quando eu digo "essa também", como você entende o contexto? |
| 219 | nao_avaliado | conversa | 1.57s | sem intent | O que acontece se eu disser apenas "sim"? |
| 220 | falhou | apps | 3.97s | APP_OPEN, APP_OPEN | abre a calculadora, por favor |
| 221 | falhou | apps | 2.71s | APP_OPEN, APP_OPEN | abre a calculadora!!! |
| 222 | falhou | apps | 2.57s | APP_OPEN, APP_OPEN | ...abre a calculadora... |
| 223 | falhou | apps | 2.21s | APP_OPEN, APP_OPEN | "abre a calculadora" |
| 224 | falhou | apps | 2.23s | APP_OPEN, APP_OPEN | abre a calculadora? |
| 225 | falhou | apps | 2.29s | APP_OPEN, APP_OPEN | abre a calculadora ou não? |
| 226 | nao_avaliado | conversa | 0.07s | sem intent | eu estava pensando que talvez fosse interessante abrir a calculadora, mas só estou pensand |
| 227 | falhou | conversa | 0.09s | sem intent | eu quero que você abra a calculadora, coloque ela na direita, confira se ficou aberta e só |
| 228 | falhou | apps | 2.70s | APP_OPEN, APP_OPEN | abre o opera e a calculadora mas não fecha nenhum dos dois e não mexe no navegador além di |
| 229 | falhou | apps | 5.01s | CLOSE_APP, CLOSE_APP | fecha só a calculadora, não o opera |
| 230 | nao_avaliado | apps | 3.42s | CLOSE_APP | fecha só o opera, deixa a calculadora quieta |
| 231 | nao_avaliado | apps | 4.22s | LIST_WINDOWS | qual dos dois ainda está aberto? |
| 232 | nao_avaliado | conversa | 1.99s | sem intent | aaaaaaaaaaaaaaaa |
| 233 | nao_avaliado | conversa | 0.80s | sem intent | ??? |
| 234 | nao_avaliado | conversa | 1.49s | sem intent | !!! |
| 235 | nao_avaliado | conversa | 0.87s | sem intent | :) |
| 236 | nao_avaliado | conversa | 0.76s | sem intent | :( |
| 237 | nao_avaliado | conversa | 0.82s | sem intent | ¯\_(ツ)_/¯ |
| 238 | nao_avaliado | conversa | 1.61s | sem intent | [teste] |
| 239 | nao_avaliado | conversa | 2.15s | sem intent | {teste} |
| 240 | nao_avaliado | conversa | 1.83s | sem intent | <teste> |
| 241 | nao_avaliado | conversa | 2.02s | sem intent | foo=bar |
| 242 | nao_avaliado | conversa | 2.29s | sem intent | localhost |
| 243 | nao_avaliado | conversa | 1.40s | sem intent | 192.168.0.1 |
| 244 | nao_avaliado | conversa | 2.32s | sem intent | python.exe |
| 245 | nao_avaliado | conversa | 1.35s | sem intent | README.md |
| 246 | nao_avaliado | conversa | 1.78s | sem intent | AGENTS.md |
| 247 | nao_avaliado | conversa | 2.68s | sem intent | isso foi uma mensagem normal, não um comando |
| 248 | nao_avaliado | conversa | 2.08s | sem intent | ignore a palavra abre nesta frase |
| 249 | nao_avaliado | conversa | 3.86s | sem intent | a palavra fecha não é um pedido para fechar nada |
| 250 | nao_avaliado | conversa | 2.32s | sem intent | estou apenas escrevendo: abre o opera |
| 251 | falhou | apps | 3.79s | MAXIMIZE_WINDOW, MAXIMIZE_WINDOW | aspas: "fecha a calculadora" |
| 252 | nao_avaliado | conversa | 1.61s | sem intent | fim |
| 253 | nao_avaliado | conversa | 3.09s | sem intent | O arquivo caos seguro.txt existe? |
| 254 | falhou | arquivos | 1.36s | DELETE_ITEM, DELETE_ITEM | Se existir, apaga o caos seguro.txt. |
| 255 | falhou | arquivos | 0.16s | CONFIRM_DELETE_ITEM, CONFIRM_DELETE_ITEM | sim |
| 256 | nao_avaliado | conversa | 2.01s | sem intent | O arquivo troca ideia.txt existe? |
| 257 | falhou | conversa | 0.09s | sem intent | Se existir, apaga o troca ideia.txt. |
| 258 | nao_avaliado | conversa | 4.36s | sem intent | sim |
| 259 | nao_avaliado | conversa | 1.76s | sem intent | O arquivo correcao.txt existe? |
| 260 | falhou | arquivos | 2.56s | DELETE_ITEM, DELETE_ITEM | Se existir, apaga o correcao.txt. |
| 261 | nao_avaliado | conversa | 2.13s | sem intent | sim |
| 262 | nao_avaliado | conversa | 1.71s | sem intent | A playlist caos sonora existe? |
| 263 | falhou | musica | 3.06s | PLAYLIST_DELETE, PLAYLIST_DELETE | Se existir, apaga a playlist caos sonora. |
| 264 | nao_avaliado | conversa | 1.56s | sem intent | sim |
| 265 | nao_avaliado | conversa | 1.72s | sem intent | Não faça mais nenhuma ação. |
| 266 | nao_avaliado | conversa | 1.49s | sem intent | Oi, Lay. |
| 267 | nao_avaliado | conversa | 0.84s | sem intent | Obrigado pelo teste. |

# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **7/7** respostas.
- Avaliados semanticamente: **1**.
- Passaram: **1**.
- Falharam: **0**.
- Alertas: **0**.
- Não avaliados semanticamente: **6**.
- Taxa semântica: **100.0%**.

## Latência

- p50: 3.082 s
- p95: 9.244 s
- máxima: 10.716 s
- média: 3.956 s
- Etapas com `confirmado=None`: **1**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| conversa | 0 | 0 | 0 | 1 |
| musica | 1 | 0 | 0 | 5 |

## Falhas e alertas

### Turno 002 — nao_avaliado

**Comando:** Coloca a playlist VMZ, pausa a música e me diz o estado dela.

**Intents:** PLAYLIST_PLAY

**Alertas:** dependencia_externa_nao_confirmada

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | nao_avaliado | musica | 10.72s | PLAYLIST_PLAY | Coloca a playlist red151 setup runtime. |
| 002 | nao_avaliado | musica | 3.08s | PLAYLIST_PLAY | Coloca a playlist VMZ, pausa a música e me diz o estado dela. |
| 003 | nao_avaliado | musica | 5.81s | MEDIA_CONTROL | Continua a música, passa para a próxima faixa e me diz qual está tocando. |
| 004 | nao_avaliado | musica | 1.96s | PLAYLIST_ADD | Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela. |
| 005 | passou | musica | 4.36s | MEDIA_CONTROL | Vai para a próxima faixa e adiciona essa também na caos sonora. |
| 006 | nao_avaliado | musica | 1.57s | PLAYLIST_LIST | Mostra a playlist caos sonora e depois apaga ela. |
| 007 | nao_avaliado | conversa | 0.20s | sem intent | sim |

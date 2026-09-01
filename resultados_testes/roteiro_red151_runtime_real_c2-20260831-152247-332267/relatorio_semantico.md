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

- p50: 0.194 s
- p95: 3.994 s
- máxima: 4.785 s
- média: 1.37 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| conversa | 0 | 0 | 0 | 1 |
| musica | 1 | 0 | 0 | 5 |

## Falhas e alertas

### Turno 002 — nao_avaliado

**Comando:** Coloca a playlist z51.

**Intents:** PLAYLIST_PLAY

**Alertas:** dependencia_externa_nao_confirmada

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | nao_avaliado | musica | 4.79s | PLAYLIST_PLAY | Coloca a playlist red151 fonte. |
| 002 | nao_avaliado | musica | 0.14s | PLAYLIST_PLAY | Coloca a playlist z51. |
| 003 | passou | musica | 2.15s | MEDIA_CONTROL | pausa a música |
| 004 | nao_avaliado | musica | 2.07s | MEDIA_CONTROL | continua a música |
| 005 | nao_avaliado | musica | 0.09s | MUSIC_STATUS | qual música está tocando? |
| 006 | nao_avaliado | conversa | 0.17s | sem intent | sim |
| 007 | nao_avaliado | musica | 0.19s | PLAYLIST_LIST | Mostra a playlist z51. |

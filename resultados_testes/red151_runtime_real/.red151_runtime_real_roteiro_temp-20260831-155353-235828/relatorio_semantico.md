# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **5/5** respostas.
- Avaliados semanticamente: **1**.
- Passaram: **1**.
- Falharam: **0**.
- Alertas: **0**.
- Não avaliados semanticamente: **4**.
- Taxa semântica: **100.0%**.

## Latência

- p50: 2.126 s
- p95: 3.701 s
- máxima: 4.091 s
- média: 1.739 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| conversa | 0 | 0 | 0 | 1 |
| musica | 1 | 0 | 0 | 3 |

## Falhas e alertas

### Turno 002 — nao_avaliado

**Comando:** Coloca a playlist R51, pausa a música e me diz o estado dela.

**Intents:** PLAYLIST_PLAY

**Alertas:** dependencia_externa_nao_confirmada

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | nao_avaliado | musica | 0.16s | MUSIC_STATUS | qual música tá tocando |
| 002 | nao_avaliado | musica | 4.09s | PLAYLIST_PLAY | Coloca a playlist R51, pausa a música e me diz o estado dela. |
| 003 | nao_avaliado | musica | 2.14s | MEDIA_CONTROL | continua a música |
| 004 | passou | musica | 2.13s | MEDIA_CONTROL | pausa a música |
| 005 | nao_avaliado | conversa | 0.18s | sem intent | sim |

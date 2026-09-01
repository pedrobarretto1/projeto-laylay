# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **7/7** respostas.
- Avaliados semanticamente: **0**.
- Passaram: **0**.
- Falharam: **0**.
- Alertas: **0**.
- Não avaliados semanticamente: **7**.
- Taxa semântica: sem amostra.

## Latência

- p50: 0.192 s
- p95: 4.888 s
- máxima: 6.034 s
- média: 1.443 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| conversa | 0 | 0 | 0 | 1 |
| musica | 0 | 0 | 0 | 6 |

## Falhas e alertas

### Turno 002 — nao_avaliado

**Comando:** Coloca a playlist VMZ.

**Intents:** PLAYLIST_PLAY

**Alertas:** dependencia_externa_nao_confirmada

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | nao_avaliado | musica | 6.03s | PLAYLIST_PLAY | Coloca a playlist red151 origem. |
| 002 | nao_avaliado | musica | 0.14s | PLAYLIST_PLAY | Coloca a playlist VMZ. |
| 003 | nao_avaliado | musica | 1.35s | MEDIA_CONTROL | pausa |
| 004 | nao_avaliado | musica | 0.09s | MUSIC_STATUS | estado |
| 005 | nao_avaliado | musica | 2.21s | MEDIA_CONTROL | continua |
| 006 | nao_avaliado | musica | 0.08s | MUSIC_STATUS | qual música está tocando? |
| 007 | nao_avaliado | conversa | 0.19s | sem intent | sim |

# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **6/6** respostas.
- Avaliados semanticamente: **1**.
- Passaram: **1**.
- Falharam: **0**.
- Alertas: **0**.
- Não avaliados semanticamente: **5**.
- Taxa semântica: **100.0%**.

## Latência

- p50: 2.9 s
- p95: 10.956 s
- máxima: 11.87 s
- média: 4.359 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| musica | 1 | 0 | 0 | 5 |

## Falhas e alertas

### Turno 003 — nao_avaliado

**Comando:** Coloca a playlist VMZ.

**Intents:** PLAYLIST_PLAY

**Alertas:** dependencia_externa_nao_confirmada

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | nao_avaliado | musica | 11.87s | PLAYLIST_PLAY | Coloca a playlist BASE151. |
| 002 | nao_avaliado | musica | 0.11s | MUSIC_STATUS | Qual música está tocando? |
| 003 | nao_avaliado | musica | 0.16s | PLAYLIST_PLAY | Coloca a playlist VMZ. |
| 004 | passou | musica | 5.56s | MEDIA_CONTROL | Pausa a música. |
| 005 | nao_avaliado | musica | 8.21s | MEDIA_CONTROL | Continua a música. |
| 006 | nao_avaliado | musica | 0.24s | PLAYLIST_ADD | sim |

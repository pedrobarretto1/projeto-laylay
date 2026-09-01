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

- p50: 2.38 s
- p95: 6.817 s
- máxima: 7.085 s
- média: 3.547 s
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
| 001 | nao_avaliado | musica | 7.08s | PLAYLIST_PLAY | Coloca a playlist red151 origem. |
| 002 | nao_avaliado | musica | 1.26s | PLAYLIST_PLAY | Coloca a playlist VMZ, pausa a música e me diz o estado dela. |
| 003 | nao_avaliado | musica | 6.19s | MEDIA_CONTROL | Continua a música, passa para a próxima faixa e me diz qual está tocando. |
| 004 | nao_avaliado | musica | 2.07s | PLAYLIST_ADD | Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela. |
| 005 | passou | musica | 5.61s | MEDIA_CONTROL | Vai para a próxima faixa e adiciona essa também na caos sonora. |
| 006 | nao_avaliado | musica | 2.38s | PLAYLIST_LIST | Mostra a playlist caos sonora e depois apaga ela. |
| 007 | nao_avaliado | conversa | 0.22s | sem intent | sim |

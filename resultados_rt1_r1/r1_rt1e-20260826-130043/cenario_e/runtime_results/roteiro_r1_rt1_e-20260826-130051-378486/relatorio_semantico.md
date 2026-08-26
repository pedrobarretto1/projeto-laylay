# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **2/2** respostas.
- Avaliados semanticamente: **1**.
- Passaram: **1**.
- Falharam: **0**.
- Alertas: **0**.
- Não avaliados semanticamente: **1**.
- Taxa semântica: **100.0%**.

## Latência

- p50: 2.922 s
- p95: 2.924 s
- máxima: 2.924 s
- média: 2.922 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| iot | 1 | 0 | 0 | 1 |

## Falhas e alertas

Nenhuma falha ou alerta semântico registrado.
## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | passou | iot | 2.92s | IOT_CONTROL | Liga a lâmpada. |
| 002 | nao_avaliado | iot | 2.92s | IOT_CONTROL | Leia de novo. |

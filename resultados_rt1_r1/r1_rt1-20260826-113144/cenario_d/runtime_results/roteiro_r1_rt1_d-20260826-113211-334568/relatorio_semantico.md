# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **3/3** respostas.
- Avaliados semanticamente: **1**.
- Passaram: **1**.
- Falharam: **0**.
- Alertas: **0**.
- Não avaliados semanticamente: **2**.
- Taxa semântica: **100.0%**.

## Latência

- p50: 2.148 s
- p95: 2.2 s
- máxima: 2.206 s
- média: 1.555 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| conversa | 0 | 0 | 0 | 1 |
| iot | 1 | 0 | 0 | 1 |

## Falhas e alertas

Nenhuma falha ou alerta semântico registrado.
## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | nao_avaliado | conversa | 0.31s | EMAIL_READ | Leia meus emails. |
| 002 | passou | iot | 2.21s | IOT_CONTROL | Liga a lâmpada. |
| 003 | nao_avaliado | iot | 2.15s | IOT_CONTROL | de novo |

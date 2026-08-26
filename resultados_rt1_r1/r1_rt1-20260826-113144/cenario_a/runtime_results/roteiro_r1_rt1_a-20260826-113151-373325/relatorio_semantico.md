# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **4/4** respostas.
- Avaliados semanticamente: **3**.
- Passaram: **3**.
- Falharam: **0**.
- Alertas: **0**.
- Não avaliados semanticamente: **1**.
- Taxa semântica: **100.0%**.

## Latência

- p50: 1.163 s
- p95: 2.246 s
- máxima: 2.26 s
- média: 1.164 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| arquivos | 2 | 0 | 0 | 1 |
| iot | 1 | 0 | 0 | 0 |

## Falhas e alertas

Nenhuma falha ou alerta semântico registrado.
## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | passou | arquivos | 2.26s | CREATE_FILE | Cria um arquivo de texto chamado rt1_a.txt e dentro dele escreva ALFA_RT1_A. |
| 002 | passou | arquivos | 0.16s | FILE_READ | Leia o arquivo rt1_a.txt. |
| 003 | passou | iot | 2.17s | IOT_CONTROL | Liga a lâmpada. |
| 004 | nao_avaliado | arquivos | 0.07s | FILE_READ | Leia de novo. |

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

- p50: 1.165 s
- p95: 2.26 s
- máxima: 2.275 s
- média: 1.171 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| arquivos | 3 | 0 | 0 | 1 |

## Falhas e alertas

Nenhuma falha ou alerta semântico registrado.
## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | passou | arquivos | 2.27s | CREATE_FILE | Cria um arquivo de texto chamado rt1_b_a.txt e dentro dele escreva ALFA_RT1_B_A. |
| 002 | passou | arquivos | 0.16s | FILE_READ | Leia o arquivo rt1_b_a.txt. |
| 003 | passou | arquivos | 2.17s | CREATE_FILE | Cria um arquivo de texto chamado rt1_b_b.txt e dentro dele escreva BETA_RT1_B_B. |
| 004 | nao_avaliado | arquivos | 0.08s | FILE_READ | Leia de novo. |

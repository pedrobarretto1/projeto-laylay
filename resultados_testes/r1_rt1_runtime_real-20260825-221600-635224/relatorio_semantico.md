# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **5/5** respostas.
- Avaliados semanticamente: **5**.
- Passaram: **5**.
- Falharam: **0**.
- Alertas: **0**.
- Não avaliados semanticamente: **0**.
- Taxa semântica: **100.0%**.

## Latência

- p50: 2.163 s
- p95: 4.618 s
- máxima: 5.085 s
- média: 2.033 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| apps | 1 | 0 | 0 | 0 |
| arquivos | 4 | 0 | 0 | 0 |

## Falhas e alertas

Nenhuma falha ou alerta semântico registrado.
## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | passou | apps | 5.08s | APP_OPEN | Abre a calculadora. |
| 002 | passou | arquivos | 2.16s | CREATE_FILE | Cria um arquivo chamado laylay_r1_rt1_a_7f9c2d.txt e escreve MARCADOR R1 RT1 ALFA 7F9C2D. |
| 003 | passou | arquivos | 0.12s | FILE_READ | Leia o laylay_r1_rt1_a_7f9c2d.txt. |
| 004 | passou | arquivos | 2.75s | CREATE_FILE | Cria um arquivo chamado laylay_r1_rt1_b_4d2e8a.txt e escreve MARCADOR R1 RT1 BETA 4D2E8A. |
| 005 | passou | arquivos | 0.05s | FILE_READ | Leia de novo. |

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

- p50: 1.538 s
- p95: 4.717 s
- máxima: 5.342 s
- média: 1.879 s
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
| 001 | passou | apps | 5.34s | APP_OPEN | Abre a calculadora. |
| 002 | passou | arquivos | 1.54s | CREATE_FILE | Cria um arquivo chamado r1 rt1 leitura.txt e escreve alpha. |
| 003 | passou | arquivos | 0.18s | FILE_READ | Leia o r1 rt1 leitura.txt. |
| 004 | passou | arquivos | 2.21s | CREATE_FILE | Cria um arquivo chamado r1 rt1 sombra.txt e escreve beta. |
| 005 | passou | arquivos | 0.12s | FILE_READ | Leia de novo. |

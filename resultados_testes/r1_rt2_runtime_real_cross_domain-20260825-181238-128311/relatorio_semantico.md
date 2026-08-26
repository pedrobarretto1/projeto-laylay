# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **5/5** respostas.
- Avaliados semanticamente: **5**.
- Passaram: **4**.
- Falharam: **1**.
- Alertas: **0**.
- Não avaliados semanticamente: **0**.
- Taxa semântica: **80.0%**.

## Latência

- p50: 4.839 s
- p95: 6.951 s
- máxima: 7.306 s
- média: 3.612 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| apps | 2 | 0 | 0 | 0 |
| arquivos | 2 | 1 | 0 | 0 |

## Falhas e alertas

### Turno 002 — falhou

**Comando:** Leia o laylay_r1_rt2_cross_91c4e7.txt.

**Intents:** FILE_READ

**Erros:** fala_nao_contem_evidencia_esperada

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | passou | arquivos | 7.31s | CREATE_FILE | Cria um arquivo chamado laylay_r1_rt2_cross_91c4e7.txt e escreve MARCADOR R1 RT2 CROSS 91C |
| 002 | falhou | arquivos | 0.27s | FILE_READ | Leia o laylay_r1_rt2_cross_91c4e7.txt. |
| 003 | passou | apps | 4.84s | APP_OPEN | Abre a calculadora. |
| 004 | passou | apps | 5.53s | APP_OPEN | De novo. |
| 005 | passou | arquivos | 0.11s | FILE_READ | Leia de novo. |

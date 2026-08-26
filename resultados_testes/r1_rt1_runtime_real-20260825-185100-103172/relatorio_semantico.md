# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **5/5** respostas.
- Avaliados semanticamente: **5**.
- Passaram: **3**.
- Falharam: **2**.
- Alertas: **0**.
- Não avaliados semanticamente: **0**.
- Taxa semântica: **60.0%**.

## Latência

- p50: 2.815 s
- p95: 5.01 s
- máxima: 5.455 s
- média: 2.368 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| apps | 1 | 0 | 0 | 0 |
| arquivos | 2 | 2 | 0 | 0 |

## Falhas e alertas

### Turno 003 — falhou

**Comando:** Leia o laylay_r1_rt1_a_7f9c2d.txt.

**Intents:** FILE_READ

**Erros:** fala_nao_contem_evidencia_esperada

### Turno 005 — falhou

**Comando:** Leia de novo.

**Intents:** FILE_READ

**Erros:** fala_nao_contem_evidencia_esperada

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | passou | apps | 5.46s | APP_OPEN | Abre a calculadora. |
| 002 | passou | arquivos | 3.23s | CREATE_FILE | Cria um arquivo chamado laylay_r1_rt1_a_7f9c2d.txt e escreve MARCADOR R1 RT1 ALFA 7F9C2D. |
| 003 | falhou | arquivos | 0.17s | FILE_READ | Leia o laylay_r1_rt1_a_7f9c2d.txt. |
| 004 | passou | arquivos | 2.81s | CREATE_FILE | Cria um arquivo chamado laylay_r1_rt1_b_4d2e8a.txt e escreve MARCADOR R1 RT1 BETA 4D2E8A. |
| 005 | falhou | arquivos | 0.17s | FILE_READ | Leia de novo. |

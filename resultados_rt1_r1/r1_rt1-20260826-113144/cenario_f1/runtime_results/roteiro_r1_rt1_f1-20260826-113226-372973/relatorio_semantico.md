# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **2/2** respostas.
- Avaliados semanticamente: **2**.
- Passaram: **1**.
- Falharam: **1**.
- Alertas: **0**.
- Não avaliados semanticamente: **0**.
- Taxa semântica: **50.0%**.

## Latência

- p50: 2.29 s
- p95: 2.331 s
- máxima: 2.336 s
- média: 2.29 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| arquivos | 1 | 0 | 0 | 0 |
| conversa | 0 | 1 | 0 | 0 |

## Falhas e alertas

### Turno 002 — falhou

**Comando:** Leia de novo.

**Intents:** nenhuma

**Erros:** execucao_nao_publicada

## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | passou | arquivos | 2.25s | DELETE_ITEM | Apaga o arquivo rt1_inexistente.txt. |
| 002 | falhou | conversa | 2.34s | sem intent | Leia de novo. |

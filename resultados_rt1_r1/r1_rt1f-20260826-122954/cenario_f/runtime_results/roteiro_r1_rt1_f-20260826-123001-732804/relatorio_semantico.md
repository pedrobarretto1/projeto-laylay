# Relatório semântico do roteiro da Laylay

Avaliador determinístico v15. Não usa LLM para dar nota ao texto livre.

## Placar

- Transporte: **2/4** respostas.
- Avaliados semanticamente: **2**.
- Passaram: **2**.
- Falharam: **0**.
- Alertas: **0**.
- Não avaliados semanticamente: **2**.
- Taxa semântica: **100.0%**.

## Latência

- p50: 1.749 s
- p95: 2.789 s
- máxima: 2.905 s
- média: 1.749 s
- Etapas com `confirmado=None`: **0**.

## Por domínio

| Domínio | Passou | Falhou | Alerta | Não avaliado |
|---|---:|---:|---:|---:|
| arquivos | 2 | 0 | 0 | 0 |
| nao_classificado | 0 | 0 | 0 | 2 |

## Falhas e alertas

Nenhuma falha ou alerta semântico registrado.
## Matriz de turnos

| # | Resultado | Domínio | Tempo | Intents | Comando |
|---:|---|---|---:|---|---|
| 001 | passou | arquivos | 2.90s | CREATE_FILE | Cria um arquivo de texto chamado rt1_f.txt e dentro dele escreva ALFA_RT1_F. |
| 002 | passou | arquivos | 0.59s | FILE_READ | Leia o arquivo rt1_f.txt. |
| 003 | nao_avaliado | - | - | sem intent | Liga a lâmpada. |
| 004 | nao_avaliado | - | - | sem intent | Leia de novo. |

# Aprendizado contextual da Laylay

O aprendizado usa as tabelas `aprendizado_eventos` e
`aprendizado_hipoteses`. Uma observação isolada não vira regra e a fala da
própria Laylay nunca serve como evidência de preferência.

## Confiança e tempo

A confiança efetiva decai desde o último reforço. Evidências repetidas em dias
diferentes aumentam a meia-vida do padrão, mas nenhuma preferência fica imune
ao tempo. A revisão persistente considera apenas o tempo desde a revisão
anterior, evitando aplicar o mesmo decaimento várias vezes.

## Escopo

Preferências podem ser globais ou condicionadas por período, fase, atividade e
aplicativo. Uma preferência específica compatível tem prioridade sobre a
global; fora daquele contexto, a regra geral continua disponível.

## Exceções

Uma recusa contextual cria uma hipótese `excecao_preferencia`. Ela bloqueia a
regra somente no contexto correspondente e não reduz imediatamente a confiança
da preferência principal.

## Conflitos

Se duas preferências maduras discordarem no mesmo contexto, a nova não
sobrescreve a anterior. A Laylay cria uma pendência `LEARN_CONFLICT` e pergunta
se Pedro deseja substituir a regra. A troca só acontece depois da confirmação.

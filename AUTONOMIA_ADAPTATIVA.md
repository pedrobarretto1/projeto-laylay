# Autonomia adaptativa da Laylay

A Laylay usa um porteiro central antes de emitir falas espontâneas. O porteiro agora
combina utilidade, momento atual e um perfil de tolerância aprendido por categoria.

## O que ela aprende

- Cada categoria (`música`, `rotina`, `horário`, `e-mails` e outras) mantém contadores
  separados de sugestões exibidas, aceitas e recusadas.
- Uma recusa dobra progressivamente o intervalo daquela categoria, até o limite de um dia.
- Uma aceitação reduz um nível do recuo. Assim, uma única aceitação não apaga todo o
  histórico, e uma única recusa também não vira preferência permanente.
- Contrapropostas contam como recusa da sugestão original, além de seguirem o aprendizado
  contextual já existente para a alternativa escolhida.

O perfil fica na mente compartilhada em `perfil_proatividade` e é salvo com a memória
durável. Reiniciar a Laylay não zera o que ela aprendeu sobre frequência.

## Proteção do contexto

Sugestões comuns perdem prioridade ou são descartadas durante:

- jogos detectados pelo modo jogo;
- reuniões identificadas pelo contexto da janela;
- atividades de foco, como programação e estudo;
- conversas ativas e momentos emocionalmente sensíveis.

Alarmes, alertas de segurança e erros críticos não recebem essas reduções. Se já houver
uma resposta sendo falada, eles podem ser unidos ao mesmo turno; fora disso, são emitidos
normalmente, inclusive quando o conteúdo se repete.

O bloqueio imediato de dez minutos por comando continua existindo. Ele evita insistência
logo após um “não”, enquanto o perfil adaptativo cuida do comportamento de longo prazo.

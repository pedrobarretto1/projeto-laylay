# Presença no jogo e bloqueio do clipboard — 2026-09-05

Estado: candidato aplicado; regressão relevante GREEN; transporte Groq real GREEN;
fala física durante uma sessão de jogo ainda não validada.

## Base da investigação

- Branch: `main`.
- HEAD: `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`.
- Worktree extensamente modificada antes desta intervenção, incluindo composição,
  presença, voz, cliente LLM e DEV Console. O HEAD não representa sozinho os logs
  históricos. Alterações preexistentes preservadas; nenhum commit criado.

## Cadeias causais demonstradas

1. Evento ambiental nasce como `system`, sem utterance do usuário.
   O pedido é tipado como `presenca_evento`. A seleção de histórico em
   `preparacao_llm.py` preservava somente instruções associadas a uma mensagem
   `user`, removendo o evento antes do adaptador remoto. O payload real ficava
   apenas com o prompt principal e a Groq retornava HTTP 400:
   `No user query found in messages.`
   O ajuste anterior no adaptador remoto não resolvia essa perda anterior.

2. A composição publica o plano ambiental em `planejado`. O processamento da
   proposta retornava, tanto com sucesso quanto com falha, sem concluir esse
   plano. `PonteIniciativaAplicacaoRuntime.turno_em_andamento()` continuava
   verdadeiro. Isso impedia novas propostas de jogo e clipboard com
   `fala_ou_turno_em_andamento`.

A hipótese de falha geral da credencial/modelo não explica o caso reproduzido:
a chamada com consulta válida funciona. Uma flag de áudio presa também não é
necessária para reproduzir o segundo defeito: ele ocorre com `is_speaking=False`.

## Contratos aplicados

- Pedido tipado `presenca_evento` preserva a última mensagem de sistema na
  preparação. O evento continua sendo evidência sem autoridade de execução.
  Conversas comuns mantêm a filtragem de contexto antigo.
- O Diretor conclui o plano cognitivo após o resultado da proposta, incluindo
  indisponibilidade, erro de geração e bloqueio pelo porteiro. A composição
  atualiza o estado sob o lock canônico, comparando o ID do plano e sua natureza.
  Uma conclusão tardia não encerra um turno mais novo do usuário.
- `evento_concluido` registra conclusão cognitiva, não entrega física. O resultado
  fica em `resultado_evento`; os callbacks de voz continuam donos da confirmação
  de emissão.

Produção alterada nesta etapa: `preparacao_llm.py`,
`preparador_requisicao_llm.py`, `orquestrador_turno_runtime.py`,
`composicao_turno.py`, `diretor_presenca.py` e a conexão em `laylay.py`.

## Evidência de validação

- RED do evento removido confirmado através de `PedidoModelo` e do preparador
  real; GREEN após o candidato.
- RED do plano preso confirmado em sucesso e falha. O harness emprestado usava
  um atualizador de plano no-op; os testes passaram a injetar
  `atualizar_plano_turno` real, preservando a expectativa original.
- Testes atravessam a ponte real de estado e verificam a iniciativa seguinte de
  jogo e clipboard após sucesso, indisponibilidade, timeout e recusa de agenda.
  Incluem a conclusão tardia diante de um novo turno do usuário e a ligação
  declarada no composition root.
- Regressão selecionada: **407 testes e 8 subtestes passaram**. Não representa
  execução da suíte inteira do projeto.
- Diagnóstico com cena sintética, composição cognitiva, `RespostaEventoRuntime`,
  preparador real e transporte Groq real: **HTTP 200**, cerca de **900 ms**, uma
  fala recebida pelo agendador de teste e plano em `evento_concluido`.
  Não houve captura de tela nem reprodução de áudio nesse diagnóstico.
- `git diff --check` dos arquivos envolvidos passou.

## Próxima fronteira real

Reiniciar a Laylay para carregar o candidato e observar uma sessão de jogo.
Esperado: resposta remota, proposta agendada, plano `evento_concluido` e recibo
de emissão pela voz. `agendada=True` isoladamente ainda não comprova áudio.

O briefing repetido com `revalidacao_entrega` permanece uma investigação
separada: já ocorria antes do primeiro evento ambiental. Seu item persistente
pode continuar aguardando governança depois do timeout de 45 segundos do
solicitante. O candidato desta etapa não encerra esse ciclo de briefing.

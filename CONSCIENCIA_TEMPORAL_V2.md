# Consciência Temporal V2

A versão 2 evolui a linha do tempo já existente. Ela não cria outro relógio e não
substitui agenda, ritmo circadiano, memória visual ou autonomia adaptativa. Esses módulos
passam a compartilhar o mesmo estado `consciencia_temporal` da mente.

## Datas e recorrências

A interpretação determinística reconhece, entre outras formas:

- `amanhã`, `depois de amanhã`, `semana que vem` e `próximo mês`;
- `daqui a duas semanas`, `daqui a 3 meses` e intervalos semelhantes;
- `25/08/2026`, `dia 25`, `25 de agosto` e `em outubro`;
- horários como `às 15h30`;
- `todo dia`, `toda segunda`, `toda semana`, `mensalmente` e `a cada 3 meses`.

Quando uma ocorrência recorrente é concluída, a ocorrência atual entra na linha do tempo
e a mesma pendência recebe a próxima data. Ocorrências muito antigas que não foram
confirmadas são avançadas sem serem marcadas falsamente como concluídas.

## Tempo vivido e duração aprendida

O tempo cronológico continua medindo a distância entre datas. O tempo vivido contabiliza
somente intervalos de convivência ativa, limitando períodos ociosos entre mensagens.

Cada conclusão registra sua duração. Depois de duas ou mais conclusões do mesmo tipo, a
Laylay pode usar média, mínimo e máximo para estimar o andamento de outro projeto. Essa
estimativa nunca é tratada como prazo garantido.

## Pendências ambíguas

Se houver várias pendências abertas e Pedro disser apenas “terminei”, nenhuma é encerrada.
A Laylay pergunta qual delas foi concluída e só atualiza a linha do tempo depois de uma
resposta que identifique uma candidata. “Nenhuma”, “cancela” ou “deixa pra lá” preservam
todas as pendências.

## Memória visual

Uma captura relevante pode acrescentar `observacao_visual` ou `evidencia_conclusao` à
linha do tempo. A análise visual atualiza a última observação da pendência, mas nunca
confirma sua conclusão sozinha. A confirmação continua pertencendo ao usuário ou a um
resultado operacional verificável.

## Proatividade temporal

Um motor de acompanhamento verifica prazos e histórias abertas em segundo plano:

- compromissos próximos usam a categoria `lembrete`;
- projetos sem prazo só são retomados depois de um intervalo coerente;
- a duração média aprendida pode ajustar esse intervalo;
- recusas anteriores aumentam o tempo antes de uma nova abordagem;
- frustração, tristeza, raiva ou ansiedade impedem perguntas de curiosidade;
- jogo, reunião, foco e conversa ativa continuam protegidos pelo porteiro central.

A marca de emissão só é gravada depois que a fala realmente foi entregue. Assim, uma fala
adiada pelo porteiro não é registrada como se Pedro a tivesse ouvido.

# Depuração do roteiro completo — 166 turnos

## Artefato auditado

- Sessão: `resultados_testes/roteiro_teste_laylay-20260813-213122-945673`
- Fontes cruzadas: `terminal.log`, `checkpoint.json` e `conversa.md`
- Resultado mecânico do executor: `166/166` mensagens receberam alguma fala.
- Resultado semântico: **não aprovado antes desta manutenção**. O estado
  `respondido` confirma transporte e voz, não intenção correta, execução correta,
  confirmação verdadeira ou continuidade correta.

Os números das tabelas abaixo são os **índices de base zero (`0–165`)** gravados
no checkpoint, não a numeração humana `1–166`. Para localizar o número exibido
ao usuário, some um. O artefato também reúne nove inicializações da aplicação
(oito retomadas); portanto `166/166` significa conclusão eventual, e não uma
execução contínua sem reinícios.

O log registrou 36 fallbacks de autoria (`[FALA:AUTORIA]`). Somente três foram
associados a timeout da LLM; vários dos demais foram barreiras que rejeitaram
uma fala incompatível, e não falhas da ação. Ainda assim, o problema dominante
era roteamento, referência, contrato da fala e reaproveitamento de contexto.

O último diagnóstico da rodada original terminou degradado, com uma falha
impactante, uma falha semântica, um comando perdido e uma pendência ativa de
agenda (`completar_lembrete`). O estado também não era isolado: memória de
pessoas, caixa de entrada e playlists já continham dados de sessões anteriores.

## Falhas críticas encontradas

| Índice(s) no roteiro | Defeito observado | Risco | Correção desta manutenção |
|---|---|---|---|
| 13, 35, 125, 129 | Negação operacional foi quebrada ou respondida como ação | executar contra a vontade explícita | negação ficou indivisível e sem autorização |
| 148 | `obrigado de novo` reexecutou `CLOSE_APP` e fechou o Opera | ação mutável disparada por ato social | retry agora exige a fala inteira `tenta/faz de novo` ou equivalente |
| 150–154 | exclusão não criou pendência; `quero ele de volta` tentou restaurar item antigo | restaurar/apagar alvo errado | restauração vinculada ao resultado confirmado, alvo e prazo da sessão |
| 97–99, 163 | `essa ideia` virou a pergunta antiga sobre o presidente | corrupção persistente de caixa e agenda | referência tipada usa apenas o último item realmente criado |
| 89, 161 | `O que você lembra de mim?` virou pedido de lembrete | domínio errado e pendência fantasma | consulta epistêmica tem precedência sobre agenda |
| 59 | pergunta sobre faixa atual reiniciou a música | consulta causou mutação | estado musical foi separado de controle de mídia |
| 113–116 | visão anunciou progresso/envio, mas não entregou análise reutilizável | falso sucesso e continuação sem evidência | resultado visual precisa de ID, estado, evidência e TTL |

## Arquivos, pastas, janelas e referências

| Índice(s) no roteiro | Diagnóstico | Estado da correção |
|---|---|---|
| 14–18 | criação, abertura, fechamento, escrita e localização básica foram reportadas | preservado; a manutenção acrescentou regressão que comprova a preservação do conteúdo ao anexar |
| 19–24 | caminho completo, foco, movimentação e referência perderam separadores/artigos/extensão | parser e executor corrigidos com caminho concreto |
| 22, 121 | `o teste ... txt` não preservou `teste ....txt` ao mover | normalização de nome/extensão corrigida |
| 32–34, 52–53, 117–124, 137–138 | `ele` alternou entre site, arquivo, janela e app sem respeitar o último resultado tipado | saliência por domínio e falha sem foco novo |
| 35 | `Não abre o Opera` trouxe o Opera ao foco | bloqueio de negação antes do executor |
| 38 | desejo direto `queria que ... estivesse aberto agora` ficou como conversa | modalidade natural corrigida e coberta por regressão |
| 40–41 | composição posicionou YouTube em vez do app recém-aberto | encadeamento usa o resultado da etapa anterior; regressões exatas cobrem Bloco de Notas e VS Code |
| 119 | fechamento de arquivo chegou ao dispatcher como intent inválida `fecha`, alvo `OpenWith.exe` | referência de arquivo não pode virar fechamento genérico de processo; regressão dedicada |
| 135 | `Fecha um programa chamado ...` conservou `chamado` no alvo | moldura nominal removida antes de `CLOSE_APP` |
| 139 | `Maximiza o Opera` confirmou apenas foco | `MAXIMIZE_WINDOW` exige observação específica de maximização e tem regressão exata |

## Navegador, pesquisa e páginas

| Índice(s) no roteiro | Diagnóstico | Estado da correção |
|---|---|---|
| 43–44 | pesquisa web e abertura do primeiro resultado não formaram uma cadeia | busca e continuação agora publicam resultado tipado e abrem apenas resultado orgânico observado |
| 45 | lista de abas veio da conversa, sem comando/evidência estruturada | `LIST_TABS` consulta a extensão e retorna apenas abas observadas |
| 46, 48 | fechamento de aba não confirmou a aba alvo | fechamento usa `tabId`, preserva título/URL e nunca escala para fechar o navegador |
| 49 | abas ociosas respondeu sem evidência de atividade | comando atua somente na lista ociosa observada e relata confirmação remota honestamente |
| 50 | resumo de página entregou conteúdo relacionado | preservar; validar ruído e origem |
| 51–53 | busca local composta abriu o resultado, mas fechar a referência falhou | referência de documento/janela corrigida |

## Clipboard

| Índice(s) no roteiro | Diagnóstico | Estado da correção |
|---|---|---|
| 54 | leitura foi reportada como concluída; uma retomada posterior leu o próprio terminal | preservado, mas a próxima rodada precisa preparar o clipboard de forma isolada |
| 55–57 | transformação curta não ficou vinculada ao clipboard e o resultado se perdeu | operação explícita cria foco temporário de 120 s; depois expira |

## Música e playlists

| Índice(s) no roteiro | Diagnóstico | Estado da correção |
|---|---|---|
| 58 | busca musical não obteve confirmação | falha continua honesta; não promover a sucesso |
| 59 | consulta virou `play/restart` | nova leitura de estado sem mutação |
| 60–61 | pausa/continuação funcionaram | preservado |
| 62–63 | próxima/anterior caíram em fala inválida | formas elípticas agora são comandos autorizados |
| 64–65 | catálogo e conteúdo de playlist funcionaram | preservado |
| 66 | tocar playlist não confirmou player | manter falha parcial até observação |
| 67–69 | retry readicionou faixa já confirmada | adição idempotente; retry só refaz falha ou informa duplicata |

## Agenda, memória e pessoas

| Índice(s) no roteiro | Diagnóstico | Estado da correção |
|---|---|---|
| 70–76 | criação, complemento temporal, cancelamento de pendência funcionaram | preservado |
| 77 | `troca para amanhã às 22` negou toda a agenda | reagendamento contextual corrige somente o lembrete recente identificado |
| 79–86 | nome, cidade e preferências básicas foram persistidos | preservado |
| 87 | `rock` apareceu duplicado e valor composto não foi atomizado | atomização e deduplicação por valor/polaridade |
| 89, 161 | consulta pessoal foi sequestrada pela agenda | precedência e regex corrigidas |
| 91 | declaração de amizade recebeu pergunta sexualizada/sem sentido | guarda social e confirmação neutra |
| 95–99 | wrapper foi salvo e referência composta puxou pergunta alheia | conteúdo limpo e foco de inbox tipado |

## Clima, IoT e visão

| Índice(s) no roteiro | Diagnóstico | Estado da correção |
|---|---|---|
| 100–103 | briefing e clima atual/máxima funcionaram, com redação ruim em `continua com limpo` | lapidação gramatical |
| 104 | amanhã negou capacidade meteorológica | horizonte temporal passa ao mesmo provedor e seleciona o dia correto |
| 105–112 | lista/ventilador funcionaram; lâmpada falhou sem inventar sucesso | preservar confirmação real e sanitizar alvo |
| 113–116 | captura/análise/continuação ficaram somente em progresso | contrato assíncrono agora correlaciona resultado final; `VISION_QUERY` só reutiliza análise confirmada e válida |

## Comunicação e personalidade

| Índice(s) no roteiro | Diagnóstico | Estado da correção |
|---|---|---|
| 2–6, 145–147 | inventou corpo, cansaço/respiração e às vezes gênero masculino | guarda ampliada para fadiga/respiração; fala deve descrever o som, não um corpo inexistente |
| 7–11, 128, 132–133 | respostas contradisseram o catálogo vivo de capacidades | respostas locais baseadas no mapa real e validação em todos os caminhos |
| 11–13, 126–131 | instrução, hipótese e negação receberam fallback operacional ou incapacidade falsa | modalidade separada de execução; resposta procedural local |
| 142–148 | repetição social ficou acusatória, ofereceu assunto antigo e culminou em reexecução | antirrepetição e encerramento social sem retry implícito |

## Critério para a próxima execução

A próxima rodada não deve ser aprovada apenas por `respondido`. Para cada
turno operacional, conferir separadamente:

1. `intenção correta`;
2. `autorização correta`;
3. `alvo/referência correta`;
4. `executou`;
5. `confirmou com evidência`;
6. `fala coerente com o resultado`;
7. `nenhum efeito colateral em outra janela, arquivo ou domínio`.

O roteiro completo controla arquivos, programas e dispositivos reais. Por isso,
depois das regressões automatizadas, a repetição dos 166 turnos deve ser iniciada
manualmente pelo usuário, e não disparada automaticamente durante esta
manutenção.

## Validação após a manutenção

### Linha de base auditada

- Checkpoint original v1: `166/166` respostas transportadas e faladas, concluídas
  ao longo de nove inicializações da aplicação.
- Fallbacks de autoria: 36; timeouts da LLM associados: 3.
- Latência original por turno, incluindo resposta e voz: mediana de 11,44 s,
  p95 de 26,82 s e máximo de 60,09 s.
- Esses números descrevem o comportamento anterior às correções e não medem a
  nova implementação.

### Validação automatizada

- Suíte completa: `2747 passed`, `45 subtests passed`, `0 failed`.
- Regressões específicas cobrem modalidade, retry, referências, arquivos,
  agenda, memória, capacidades, música, clima, visão e navegador.
- Ruff nos arquivos alterados, `py_compile`, `node --check` da extensão e
  `git diff --check`: aprovados.
- O executor do roteiro foi atualizado para separar resposta, plano, execução e
  confirmação e para gravar planos completos em `planos.jsonl`. A avaliação
  semântica de `intencao_correta` e `fala_coerente` ainda requer expectativa ou
  revisão externa; por enquanto permanece `nao_avaliado`.

### Validação funcional pendente

Antes da próxima rodada, é necessário recarregar a extensão corrigida no Opera
e preparar um estado controlado ou restaurável de memória, agenda, caixa de
entrada, playlists e clipboard. A rodada só deve ser aprovada se não houver
reinício inesperado, comando duplicado, pendência residual ou efeito colateral,
e se intenção, autorização, alvo, execução, confirmação e fala forem avaliados
separadamente. O executor ainda não transforma troca de PID/sessão em falha
automática; os identificadores precisam ser conferidos no relatório da rodada.

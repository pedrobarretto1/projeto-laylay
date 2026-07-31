# Roadmap de manutenção estrutural da Laylay

Este documento organiza a consolidação interna da Laylay sem reescrever o que
já funciona. A manutenção será feita em fatias pequenas, sempre preservando a
personalidade, as memórias locais, as habilidades existentes e a segurança
operacional.

Novas habilidades ficam fora deste roadmap. Elas continuam em
`ROADMAP_NOVAS_HABILIDADES.md` e não devem ser misturadas a uma refatoração
estrutural no mesmo ciclo de mudança.

## Regras da manutenção

- uma mudança estrutural por vez;
- reproduzir o problema em teste antes de alterar o fluxo;
- não usar uma reescrita ampla ou troca simultânea de vários domínios;
- manter compatibilidade com a memória já persistida;
- não mover regras específicas para `laylay.py`;
- uma ação prática só pode ter uma decisão, uma execução e uma confirmação;
- falha da LLM não pode bloquear um comando determinístico já resolvido;
- conversa, voz e modo jogo devem atravessar o mesmo contrato de turno;
- todo erro absorvido precisa ser classificado como esperado ou chegar à
  observabilidade;
- a etapa só termina com regressões direcionadas e suíte completa aprovadas.

## Linha de base — 29 de julho de 2026

Retrato usado para comparar a manutenção:

- 276 arquivos Python de produção, aproximadamente 75.909 linhas;
- 136 arquivos de testes, aproximadamente 27.033 linhas;
- suíte anterior à P0: 1.539 testes e 41 subtestes aprovados;
- diagnóstico já mede interpretação, execução, LLM, TTS e turno total;
- memória pessoal, credenciais, dados Tuya, playlists e modelos locais estão
  excluídos do versionamento;
- autonomia executável limitada a permissões explícitas, baixo risco e ações
  reversíveis;
- contratos tipados de decisão e resposta já existem, mas ainda convivem com
  dicionários e conexões por namespace.

Indicadores de dívida técnica observados — não são metas para remoção cega:

- `laylay.py` tem aproximadamente 3.600 linhas e ainda é o principal ponto de
  composição;
- há 78 funções de normalização, incluindo normalizações legitimamente
  específicas de domínio;
- há cerca de 806 capturas amplas de `Exception` e 280 blocos silenciosos com
  `pass`, muitos deles em integrações opcionais;
- os maiores núcleos têm entre 1.000 e 2.000 linhas e precisam ser divididos
  somente depois que as fronteiras estiverem protegidas.

Esses números servem para detectar tendência. Uma redução numérica não vale se
retirar resiliência, contexto ou clareza.

## Fluxos críticos protegidos

Cada fase deve preservar, no mínimo:

1. conversa curta, pergunta simples e pergunta composta;
2. comando direto, comando natural indireto, negação e pergunta hipotética;
3. continuidade com `tenta de novo`, `essa também`, pronomes e resultados
   ordenados como `abre o primeiro`;
4. confirmação, recusa e cancelamento de uma ação pendente;
5. música, reprodução, controles de mídia e playlists;
6. IoT, consulta de dispositivos, estado e controle confirmado;
7. criação, escrita, pesquisa, exclusão e restauração de arquivos;
8. memória de pessoas, identidade dinâmica e memória diária;
9. área de transferência, caixa de entrada e agenda;
10. visão e conversa no modo jogo;
11. proatividade sem duplicar falas nem sequestrar um comando do usuário;
12. inicialização e encerramento sem threads bloqueadas ou traceback tardio.

## P0 — Linha de base e proteção

**Status: concluída em 29 de julho de 2026.**

Objetivo: tornar o estado atual mensurável antes de mudar a arquitetura.

- [x] inventariar tamanho, testes, módulos centrais e dívida observável;
- [x] registrar os fluxos críticos neste documento;
- [x] preservar a suíte anterior como referência;
- [x] adicionar um teste integrado do ciclo de vida da composição;
- [x] aprovar a suíte completa após a inclusão do teste da P0;
- [x] registrar o novo total oficial de testes: 1.540 testes e 41 subtestes.

Critério de conclusão:

- composição, supervisor, sinal de parada e finalizadores atravessam juntos um
  ciclo testado;
- nenhum serviço permanece ativo depois do encerramento;
- todos os testes passam.

## P1 — Decisão única por turno

**Status: concluída — decisão, execução, confirmação e entradas canônicas.**

Objetivo: fazer o contrato existente de turno ser a autoridade obrigatória em
todas as rotas, sem substituir a interpretação natural.

Ordem interna:

1. [x] mapear onde um turno pode ser decidido mais de uma vez;
2. [x] criar uma invariável observável para `turno_id`, proprietário e fase;
3. [x] impedir reentrada de roteadores depois de uma decisão final;
4. [x] tornar execução idempotente pelo identificador do turno e da ação;
5. [x] garantir uma única fala operacional por resultado confirmado;
6. [x] aplicar a mesma fronteira a terminal, voz e modo jogo;
7. [x] remover apenas os atalhos comprovadamente substituídos.

Regressões obrigatórias:

- comando resolvido no pré-fluxo não volta ao roteador imediato;
- negação e pergunta de capacidade nunca executam;
- timeout da LLM não cancela um comando determinístico;
- duas entregas do mesmo evento não duplicam ação nem voz;
- uma fala mista pode conversar e executar sem perder nenhum dos dois atos.

Critério de conclusão:

- cada turno possui um proprietário;
- cada ação possui no máximo uma tentativa ativa;
- cada resultado possui no máximo uma confirmação falada.

## P2 — Observabilidade e ciclo de vida

**Status: concluída em 30 de julho de 2026.**

Objetivo: impedir que falhas técnicas importantes desapareçam em fallbacks
genéricos.

Ordem interna:

1. [x] classificar falhas que afetam turno, comando, fala ou serviço;
2. [x] auditar capturas amplas e `pass` silenciosos com impacto real;
3. [x] levar quedas de serviços ao diagnóstico central;
4. [x] centralizar threads ainda criadas fora do supervisor;
5. [x] garantir espera interrompível e prazo único no encerramento;
6. [x] completar contadores de reentrada, duplicação e serviço órfão.

- classificar capturas amplas por falha esperada, degradação ou defeito;
- trocar `pass` silencioso por registro sanitizado quando houver impacto;
- levar quedas de serviços ao diagnóstico central;
- centralizar threads ainda criadas fora do supervisor;
- garantir espera interrompível e prazo único no encerramento;
- registrar qual fallback foi usado sem salvar conteúdo privado;
- acrescentar contadores de reentrada, duplicação e serviço órfão.

Critério de conclusão:

- toda falha que afeta o usuário aparece no diagnóstico;
- serviços opcionais continuam podendo falhar isoladamente;
- o encerramento não deixa trabalho novo ser iniciado.

## P3 — Registro tipado de serviços

**Status: em andamento — P3.1 a P3.5 concluídas.**

Objetivo: substituir gradualmente conexões por `globals()` e dicionários de
namespace, sem uma migração de uma vez.

Ordem de migração sugerida:

1. [concluída] memória de pessoas;
2. [concluída] IoT;
3. [concluída] arquivos;
4. [em andamento: consulta/estado concluídos] música e playlists;
5. navegador;
6. visão de jogo;
7. conversa e LLM;
8. composição principal.

Cada fatia deve declarar dependências obrigatórias e opcionais. Ausência de uma
dependência obrigatória deve falhar na composição, não durante uma conversa.

Critério de conclusão:

- domínios migrados não consultam namespace genérico;
- contratos são verificáveis pelo editor e pelos testes;
- credenciais não entram no registro compartilhado.

## P4 — Linguagem e módulos menores

**Status: planejada.**

Objetivo: reduzir duplicação depois que o fluxo e as fronteiras estiverem
estáveis.

- criar uma normalização linguística básica compartilhada;
- preservar normalizadores específicos para URL, nomes, áudio e jogos;
- separar negação antes da classificação de intenção;
- dividir `contexto_compartilhado.py` por estado, continuidade e compatibilidade;
- dividir `conversa_natural.py` por leitura social, respostas e contingências;
- dividir a orquestração cooperativa por quadro, governança e execução;
- dividir visão de jogo por captura, análise, pesquisa e síntese;
- reduzir `laylay.py` para composição e inicialização.

Critério de conclusão:

- regras básicas não são copiadas em cada domínio;
- cada módulo possui uma responsabilidade explicável em uma frase;
- nenhum recorte altera a fala da LLM sem um teste comportamental explícito.

## P5 — Desempenho e qualidade automática

**Status: planejada.**

Objetivo: otimizar somente depois que os caminhos estiverem inequívocos.

- definir orçamentos de latência para roteamento, LLM, visão e TTS;
- registrar tamanho dos prompts por origem de contexto;
- evitar chamada à LLM quando a resposta operacional já estiver pronta;
- controlar concorrência da LLM por prioridade interativa;
- revisar lote, deduplicação e interrupção da fila de voz;
- adicionar Ruff, verificação gradual de tipos, cobertura e auditoria de
  dependências;
- executar automaticamente testes estruturais e suíte completa.

Critério de conclusão:

- melhora mensurável de latência sem reduzir naturalidade;
- verificações automáticas impedem regressões arquiteturais conhecidas.

## P6 — Consolidação dos atalhos antigos de habilidades

**Status: planejada.**

Objetivo: retirar gradualmente os atalhos de compatibilidade que ainda
contornam parte do catálogo de habilidades, sem perder linguagem natural,
continuidade, memória, aprendizado, segurança ou orquestração cooperativa.

Ordem interna:

1. [ ] transformar a movimentação entre playlists em intent e executor
   registrados, preservando confirmação, memória e contexto;
2. [ ] transformar a consulta de aprendizados em habilidade oficial, removendo
   a lista rígida de frases do pré-fluxo;
3. [ ] comprovar por regressão que a reentrada determinística pós-LLM é
   redundante e removê-la sem prejudicar comandos quando a LLM falhar;
4. [ ] restringir o atalho social local do modo jogo a atos simples e seguros,
   como saudação e bem-estar, deixando correções e assuntos contextuais para a
   mente principal;
5. [ ] remover a compatibilidade determinística dos comandos prioritários
   quando todos os clientes usarem o coordenador canônico;
6. [ ] migrar os últimos comandos `EXEC` de abrir e fechar programas para o
   executor modular e somente então aposentar o fallback legado;
7. [ ] auditar novamente os pré-fluxos restantes e manter apenas confirmações,
   pendências, continuidade e proteções que operem dentro do turno canônico.

Regras obrigatórias desta fase:

- migrar e testar um atalho por vez;
- nenhuma remoção pode alterar a personalidade ou a fala natural da Laylay;
- cada habilidade migrada deve atravessar os pilares de contexto, memória,
  aprendizado, linguagem natural, conhecimento da própria habilidade e
  orquestração cooperativa;
- falha da LLM não pode impedir um comando determinístico já compreendido;
- decisão, execução e confirmação continuam limitadas a uma ocorrência por
  turno e ação;
- compatibilidade só será removida quando um teste provar sua substituição no
  terminal, na voz, no modo jogo e no chat.

Critério de conclusão:

- nenhuma habilidade de produção executa ou confirma ações por um atalho fora
  do coordenador canônico;
- não existe reentrada pós-LLM capaz de reclassificar o mesmo turno;
- o executor `EXEC` legado deixa de participar da aplicação principal;
- a suíte completa e as regressões de todos os fluxos críticos permanecem
  aprovadas.

## Registro de execução

Cada alteração deverá acrescentar aqui:

- data e prioridade;
- problema reproduzido;
- arquivos alterados;
- testes direcionados;
- resultado da suíte completa;
- métrica anterior e posterior, quando aplicável;
- próximo passo autorizado.

### 2026-07-29 — início da P0

- análise estrutural concluída;
- fluxos críticos e critérios registrados;
- teste integrado de ciclo de vida acrescentado em
  `tests/test_confiabilidade_runtime.py`;
- testes estruturais direcionados: 33 aprovados;
- suíte completa: 1.540 testes e 41 subtestes aprovados em 11,16 segundos;
- P0 concluída sem alteração do comportamento conversacional ou operacional;
- próximo passo: P1.1, mapear e testar reentrada de decisão no mesmo turno.

### 2026-07-29 — P1.1 a P1.3, decisão canônica sem reentrada

- reproduzida a passagem repetida do mesmo texto pelo coordenador prioritário,
  pré-fluxo, imediato e pós-IA;
- decisão natural passou a ser reutilizada pela chave `turno_id + texto
  normalizado`, inclusive quando o resultado correto é não criar comando;
- um novo turno continua reavaliando a mesma frase normalmente;
- o fluxo imediato consulta a decisão canônica e segue para conversa sem
  despertar novamente os roteadores;
- o diagnóstico da linguagem natural passou a expor `reusos_turno`;
- regressões direcionadas: 36 aprovadas;
- suíte completa: 1.543 testes e 41 subtestes aprovados em 10,94 segundos;
- próximo passo: P1.4, idempotência da execução por `turno_id + ação`, sem
  bloquear comandos mistos ou uma repetição explícita em um novo turno.

### 2026-07-29 — P1.4, execução idempotente por turno e ação

- reproduzida a duplicação potencial quando o mesmo comando chegava mais de
  uma vez ao executor no mesmo turno, inclusive por entregas concorrentes e
  pelo dispatcher JSON;
- o executor central agora reserva a ação por `turno_id + intent + parâmetros
  normalizados` e compartilha o resultado com entregas repetidas;
- falha confirmada também não é repetida silenciosamente dentro do mesmo
  turno; `tenta de novo` continua possível porque abre um turno novo;
- metadados de interpretação não criam ações artificialmente diferentes, mas
  parâmetros operacionais como a origem de um arquivo continuam distinguindo
  comandos reais;
- ações diferentes de um pedido misto continuam sendo executadas uma vez cada;
- ações autônomas e serviços em segundo plano não herdam a idempotência de um
  plano de conversa já encerrado;
- removido o atalho redundante da oferta de área de transferência anterior à
  criação do turno canônico;
- o diagnóstico passou a expor ações iniciadas, reutilizadas, aguardadas,
  ativas, expiradas e falhas na `idempotência do turno`;
- regressões direcionadas: 132 aprovadas; compilação integral aprovada;
- suíte completa: 1.551 testes e 41 subtestes aprovados em 10,73 segundos;
- próximo passo: P1.5, garantir uma única fala operacional por resultado
  confirmado, preservando a personalidade gerada pela LLM.

### 2026-07-29 — P1.5, confirmação operacional única

- reproduzida a possibilidade de duas frases diferentes chegarem ao TTS para
  o mesmo resultado operacional confirmado;
- o adaptador agora entrega à voz o contrato real do resultado, em vez de
  depender de comparação textual entre frases;
- a confirmação é reservada por `turno_id + intent + status + alvo +
  parâmetros normalizados`, permitindo que a LLM conserve sua personalidade
  sem autorizar uma segunda fala equivalente;
- ações diferentes no mesmo turno continuam recebendo confirmações próprias;
- o mesmo resultado pode ser confirmado novamente em um novo turno;
- conversa comum, proatividade e resultados não confirmados não entram nessa
  deduplicação;
- uma rejeição da fila de voz libera nova tentativa, evitando silêncio
  permanente por uma entrega que nem chegou a ser aceita;
- arquivos e o adaptador operacional geral convergem na mesma fronteira;
- o diagnóstico passou a mostrar tentativas, emissões, duplicações suprimidas,
  reservas e rejeições da voz operacional;
- regressões direcionadas: 135 aprovadas; compilação integral aprovada;
- suíte completa: 1.557 testes e 41 subtestes aprovados em 11,22 segundos;
- próximo passo: P1.6, provar a mesma fronteira canônica nos canais terminal,
  voz e modo jogo e remover somente os atalhos que forem reproduzidos.

### 2026-07-29 — P1.6, fronteira canônica nos canais de entrada

- mapeadas as entradas reais da barra, do terminal e da voz até o mesmo
  `CoordenadorExecRuntime` e o mesmo `RespostaIARuntime`;
- reproduzido um desvio anterior à mente única: no modo jogo, a voz descartava
  qualquer fala natural que não parecesse um comando curto;
- removido somente esse bloqueio; ativação por Lay/Laylay, confiança da
  transcrição, prevenção de eco, confirmação e proteção de ações sensíveis
  continuam intactas;
- terminal, voz, barra e modo jogo agora registram a origem no turno e no plano
  canônicos sem alterar as regras de interpretação ou autorização;
- o diagnóstico da mente passou a expor `origem=terminal`, `origem=voz`,
  `origem=barra` ou `origem=modo_jogo`, permitindo auditar o caminho usado;
- regressões comprovam que comando e conversa natural por voz chegam à mesma
  mente durante o jogo e que os três canais atravessam o mesmo runtime;
- suíte completa: 1.560 testes e 41 subtestes aprovados em 11,71 segundos;
- próximo passo: P1.7, auditar e remover apenas atalhos antigos cuja substituição
  pela fronteira canônica possa ser reproduzida e comprovada por regressão.

### 2026-07-29 — P1.7, remoção dos atalhos substituídos

- auditadas as chamadas de entrada, os comandos prioritários, imediatos e os
  pré-fluxos após a implantação da fronteira comum;
- reproduzida a única porta lateral restante: o coordenador de entrada ainda
  aceitava opcionalmente um callback capaz de resolver uma prioridade antes da
  criação do turno, embora a composição principal já não o utilizasse;
- removidos o callback e o ramo pré-canônico do `CoordenadorExecRuntime`;
- removido também o alias genérico de agendamento que não registrava a origem;
  os canais agora usam somente os adaptadores canônicos identificados;
- pendências, ofertas e comandos prioritários continuam vencendo antes da LLM,
  mas somente depois de o turno ter sido criado e adquirido um proprietário;
- mantidos os pré-fluxos especializados internos porque eles já operam dentro
  do turno e não constituem uma segunda entrada ou decisão independente;
- regressões verificam explicitamente a ordem `turno → prioridade` e impedem a
  reintrodução do antigo callback no coordenador;
- suíte completa: 1.561 testes e 41 subtestes aprovados em 10,82 segundos;
- P1 concluída; próximo passo recomendado: P2.1, classificar e tornar visíveis
  no diagnóstico as falhas técnicas que hoje ainda terminam em fallback.

### 2026-07-29 — P2.1, classificação de falhas e fallbacks

- criado um contrato técnico comum com as classes `esperada`, `degradacao` e
  `defeito`, além de impacto em `turno`, `comando`, `fala` ou `servico`;
- a classificação utiliza somente componente, código estável e tipo da exceção;
  mensagens, prompts, URLs, caminhos e conteúdo da conversa não são salvos;
- o transporte da LLM agora identifica circuito temporário, modelo ocupado,
  timeout, indisponibilidade, credencial recusada, erro 400 persistente e
  bloqueio intencional de economia no modo jogo;
- respostas vazias que não puderam ser reparadas registram a entrada da
  contingência conversacional no mesmo turno;
- falha do TTS neural registra o fallback local; falha desse fallback fica
  marcada como defeito sem alternativa disponível;
- exceções internas do ciclo de resposta são classificadas como defeito com
  impacto no turno, sem gerar uma confirmação artificial;
- `/diagnostico mente` agora resume esperadas, degradações, defeitos e eventos
  antigos ainda não classificados, mostrando também impacto e fallback;
- regressões verificam classificação, privacidade, timeout, modo jogo,
  contingência de resposta e ausência de registro duplicado do transporte;
- suíte completa: 1.563 testes e 41 subtestes aprovados em 11,12 segundos;
- próximo passo: P2.2, auditar capturas amplas e silêncios (`except/pass`) e
  instrumentar somente os que escondem impacto observável para o usuário.

### 2026-07-29 — P2.2, auditoria de capturas silenciosas

- inventariadas 161 capturas cujo corpo era somente `pass`; a maior parte foi
  preservada por pertencer a limpeza, telemetria, compatibilidade ou sondagens
  opcionais que não alteram o resultado entregue ao usuário;
- reproduzidos três silêncios com impacto real no planejamento canônico: falha
  ao recuperar `tenta de novo`, perda do contexto do modo jogo e falha ao
  consultar a recência da análise visual;
- cada caminho agora possui fallback explícito e evento sanitizado no
  diagnóstico, sem persistir mensagem da exceção, texto da conversa ou caminho
  do usuário;
- uma falha de repetição fica classificada como defeito do turno; indisponibilidade
  do contexto de jogo e da memória visual ficam como degradações do turno;
- o contexto de jogo já obtido é preservado mesmo se apenas a consulta visual
  falhar;
- sondagens saudáveis e ausências deliberadamente opcionais continuam sem
  produzir eventos nem ruído no terminal;
- regressões direcionadas: 49 aprovadas;
- suíte completa: 1.567 testes e 41 subtestes aprovados em 12,11 segundos;
- próximo passo: P2.3, conectar quedas e reinícios dos serviços em segundo
  plano ao mesmo diagnóstico central, com deduplicação e fallback identificado.

### 2026-07-29 — P2.3, ciclo de vida dos serviços no diagnóstico central

- confirmado que o supervisor já encaminhava a exceção de uma queda, mas não
  registrava o estado do reinício, da nova tentativa ou da finalização;
- criado um retrato sanitizado e agregado por serviço com estado, tentativa,
  atraso, fallback e contadores de quedas, reinícios e falhas de inicialização;
- o retrato substitui o estado anterior do mesmo serviço em vez de criar um
  histórico ilimitado; as falhas técnicas repetidas continuam deduplicadas pelo
  relator central;
- quedas distinguem `reinicio_agendado` de `servico_indisponivel`, permitindo
  saber se existe recuperação automática;
- falhas que acontecem antes de a thread ser criada também chegam uma única vez
  ao diagnóstico, inclusive para serviços iniciados diretamente;
- mensagens de exceção deixaram de ser impressas pelo supervisor; o terminal e
  a memória recebem somente o tipo técnico e códigos sanitizados;
- `/diagnostico mente` agora resume total, ativos, degradados, quedas e reinícios
  dos serviços de fundo e detalha somente os estados degradados;
- regressões direcionadas: 32 aprovadas;
- suíte completa: 1.571 testes e 41 subtestes aprovados em 11,90 segundos;
- próximo passo: P2.4, inventariar threads ainda criadas fora do supervisor e
  migrar apenas as que possuem ciclo de vida independente e risco de órfão.

### 2026-07-29 — P2.4, propriedade das threads duradouras

- inventariadas criações diretas de threads, timers e tarefas assíncronas;
- tarefas curtas de análise, histórico, pesquisa e despacho foram preservadas,
  assim como componentes que já possuem `parar()` e `join()` próprios;
- reproduzidos dois riscos duradouros: o worker da fila de voz iniciava fora do
  supervisor e a barra de comando não participava do encerramento central;
- o worker `Laylay-SpeechQueue` agora é iniciado pelo gerenciador de serviços,
  recebe observabilidade de queda/reinício e não cria uma segunda thread lateral;
- a barra continua proprietária de sua thread por causa da afinidade do Tk e da
  hotkey nativa do Windows, mas agora remove a hotkey, solicita o fechamento da
  interface e aguarda suas threads no finalizador central;
- a hotkey nativa libera o registro do Windows mesmo quando seu loop termina por
  falha;
- os finalizadores de memória, voz, barra, avatar e Game Bar continuam isolados:
  falha em um deles não impede os seguintes;
- regressões direcionadas: 92 aprovadas;
- suíte completa: 1.573 testes e 41 subtestes aprovados em 12,19 segundos;
- próximo passo: P2.5, consolidar um prazo único de encerramento também para os
  finalizadores autocontidos, sem multiplicar esperas sequenciais.

### 2026-07-30 — P2.5, prazo único de encerramento

- reproduzida a soma potencial dos limites internos de voz, barra, avatar,
  processo do avatar, Game Bar, rede associativa e supervisor;
- a composição agora cria um único prazo monotônico e entrega a cada
  finalizador somente o tempo ainda disponível;
- finalizadores sem parâmetro de timeout, como a persistência de memória,
  continuam sendo chamados normalmente;
- quando o orçamento acaba, todos os componentes restantes ainda recebem seu
  sinal de parada, mas seus `join()` usam timeout zero e não abrem uma nova
  janela de espera;
- o supervisor passou a consumir o saldo do mesmo prazo dentro da composição;
  a chamada defensiva posterior permanece idempotente e retorna sem nova espera;
- voz, barra, avatar e Game Bar agora aceitam o orçamento recebido; avatar e
  barra também repartem internamente esse saldo entre suas próprias threads e
  processo;
- falha ou interrupção em um finalizador continua isolada e não impede os
  seguintes;
- regressões direcionadas: 98 aprovadas;
- suíte completa: 1.574 testes e 41 subtestes aprovados em 11,95 segundos;
- próximo passo: P2.6, completar os contadores de reentrada, duplicação e
  serviço órfão e concluir a fase P2.

### 2026-07-30 — P2.6, contadores de proteção e conclusão da P2

- reutilizadas as fontes autoritativas existentes em vez de criar contagens
  paralelas: cache da decisão canônica, idempotência da execução e reserva da
  confirmação operacional;
- `/diagnostico mente` agora reúne reentradas evitadas, execuções duplicadas
  convergidas e falas duplicadas suprimidas em `proteções do ciclo`;
- após o prazo único, cada thread ainda viva é marcada como `orfao`, recebe
  fallback `encerramento_do_processo` e gera uma degradação sanitizada do
  serviço;
- o diagnóstico diferencia órfãos atuais do total histórico detectado; se a
  thread terminar depois, o estado atual volta a encerrado sem apagar o fato
  histórico;
- o retrato agregado por serviço ganhou contador de órfãos sem criar lista
  ilimitada nem salvar dados da exceção;
- regressões direcionadas: 63 aprovadas antes da suíte integral;
- suíte completa: 1.576 testes e 41 subtestes aprovados em 11,09 segundos;
- P2 concluída: falhas com impacto são observáveis, serviços opcionais permanecem
  isolados, threads duradouras têm proprietário e o encerramento possui prazo
  único com detecção de trabalho remanescente;
- próximo passo recomendado: P3.1, iniciar o registro tipado pela memória de
  pessoas, sem migrar outros domínios no mesmo ciclo.

### 2026-07-30 — P3.1, registro tipado da memória de pessoas

- criado um contrato verificável para processamento, contexto da LLM,
  diagnóstico, retrato da mente e reexecução de consultas de pessoas;
- o registro valida todas as operações obrigatórias durante a composição e
  interrompe a inicialização com erro claro se a dependência estiver ausente ou
  incompleta, antes de qualquer conversa;
- o fluxo prioritário deixou de consultar `_memoria_pessoas_runtime` no
  namespace genérico e agora recebe o registro explicitamente;
- o adaptador que monta o contexto da LLM também recebe a mesma dependência por
  conexão explícita, mantendo a inicialização tardia da aplicação;
- mapa de recursos e diagnóstico usam o mesmo registro, sem criar uma segunda
  implementação ou alterar o arquivo `pessoas_relacoes.json`;
- o registro não carrega credenciais nem expõe em sua representação os detalhes
  internos e o caminho de persistência do runtime;
- regressões direcionadas: 48 aprovadas;
- suíte completa: 1.579 testes e 41 subtestes aprovados em 12,87 segundos;
- próximo passo recomendado: P3.2, migrar IoT para um contrato tipado próprio,
  mantendo dispositivos e credenciais fora do registro compartilhado.

### 2026-07-30 — P3.2, registro tipado do IoT

- criado um contrato tipado único para detectar intenções, executar ações e
  fornecer o retrato sanitizado dos dispositivos;
- o runtime Tuya existente continua sendo a implementação: protocolo,
  persistência, confirmação física e comportamento de fala não foram
  reescritos;
- removidos dos namespaces de produção os callbacks legados
  `_detectar_intencao_iot` e `_executar_intencao_iot`;
- detecção determinística, comandos prioritários, continuidade imediata,
  preferências aprendidas, execução central, ações autônomas, mapa de recursos
  e auditoria de saúde agora recebem o contrato IoT;
- as composições de entrada e do ciclo central exigem um registro IoT válido e
  falham antes da conversa quando ele está ausente ou incompleto;
- o retrato compartilhado remove defensivamente configuração, credenciais,
  `device_id`, `local_key` e segredos, sem modificar os dados do runtime;
- IDs, chaves locais e configuração Tuya permanecem dentro do subsistema IoT e
  não aparecem na representação do registro;
- regressões direcionadas: 242 testes e 8 subtestes aprovados;
- suíte completa: 1.583 testes e 41 subtestes aprovados em 11,48 segundos;
- próximo passo recomendado: P3.3, migrar o domínio de arquivos para contratos
  tipados, começando pelas operações de busca e leitura antes das mutações.

### 2026-07-30 — P3.3, registro tipado de leitura de arquivos

- criado um contrato tipado e somente leitura para pesquisa semântica, abertura
  de resultados e diagnóstico do índice local;
- o runtime de pesquisa existente continua responsável por indexação e busca;
  o registro apenas define e protege sua fronteira pública;
- o executor deixou de procurar o runtime bruto no namespace genérico e recebe
  explicitamente o serviço de leitura pela composição central;
- a composição agora exige um registro de arquivos válido antes da primeira
  conversa e informa quais operações obrigatórias estiverem ausentes;
- resultados sensíveis têm o trecho removido e campos internos de conteúdo,
  raiz, configuração e credenciais são descartados defensivamente;
- o diagnóstico expõe somente métricas permitidas e não revela o caminho do
  projeto nem detalhes privados do serviço;
- criação, escrita, movimentação e exclusão permaneceram inalteradas nesta
  fatia para não misturar leitura segura com ações mutáveis;
- regressões direcionadas: 19 testes aprovados;
- suíte completa: 1.588 testes e 41 subtestes aprovados em 11,80 segundos;
- próximo passo recomendado: P3.4, criar um contrato separado para mutações de
  arquivos, preservando confirmação, lixeira, referências e escrita segura.

### 2026-07-30 — P3.4, registro tipado de mutações de arquivos

- criado um runtime único que reúne as operações locais já existentes de
  criação, escrita, movimentação, transação, exclusão e restauração;
- o contrato de mutações permanece separado do contrato de pesquisa e leitura,
  evitando que um consumidor somente leitor receba autorização para escrever;
- o executor de arquivos deixou de obter callbacks mutáveis pelo namespace
  genérico e agora recebe explicitamente o registro pela composição central;
- os callbacks legados de criação, escrita, movimentação, resolução e exclusão
  foram removidos da allowlist do contexto geral de execução;
- foram preservadas a trava de raízes pessoais, a escrita atômica com releitura,
  a recusa de sobrescrita implícita, as transações com validação e a lixeira
  reversível com confirmação canônica;
- a composição falha antes da conversa se o serviço estiver ausente ou não
  implementar todas as operações obrigatórias;
- o diagnóstico informa somente disponibilidade das proteções e existência de
  confirmação pendente, sem publicar caminhos, conteúdo ou detalhes internos;
- regressões direcionadas: 212 testes e 8 subtestes aprovados;
- suíte completa: 1.594 testes e 41 subtestes aprovados em 12,28 segundos;
- domínio de arquivos concluído no registro tipado;
- próximo passo recomendado: P3.5, migrar música e playlists em uma fatia
  somente de consulta/estado antes das operações de reprodução e alteração.

### 2026-07-30 — P3.5, registro tipado de consulta e estado musical

- criado um contrato musical de somente leitura para listar playlists do
  usuário e da Laylay, consultar conteúdo, contar faixas e fornecer contexto;
- o prompt, o interpretador e os executores recebem nomes, quantidades, títulos
  e estado sanitizado, sem URLs, fila aleatória, identificadores de aba ou cache
  bruto das playlists;
- listagens e contagens deixaram de buscar callbacks musicais no namespace
  genérico; o roteador recebe o registro explicitamente pela composição;
- reprodução, avanço automático, adição, cópia e exclusão permaneceram no fluxo
  anterior para que esta fatia não misture observação com ações mutáveis;
- a composição falha antes da conversa quando o registro estiver ausente ou
  incompleto, e o diagnóstico informa a disponibilidade sem expor dados;
- regressões direcionadas: 46 testes aprovados;
- suíte completa após a regressão de autoria das playlists: 1.601 testes e 41
  subtestes aprovados em 10,77 segundos;
- próximo passo recomendado: P3.6, criar o contrato tipado das operações
  musicais mutáveis e de reprodução, preservando autorização e auto-next.

### 2026-07-30 — manutenção da curadoria própria da Laylay

- auditada a habilidade antiga que monta as playlists próprias da Laylay;
- o histórico musical confirmado, antes recebido e ignorado, passou a ordenar
  os xodós sem inventar faixas nem depender de pesquisa externa;
- a seleção de clima agora alterna entre as playlists mais relevantes, em vez
  de preencher toda a coleção apenas com a maior lista;
- descobertas já salvas são preservadas e nenhuma migração destrutiva foi
  aplicada ao arquivo existente;
- sincronizações idênticas deixaram de regravar o JSON, reduzindo I/O e risco
  de corrupção durante consultas;
- nomes naturais como “xodós que eu separei” são resolvidos mesmo com a chave
  histórica `xodos_que_eu_seperei`;
- consultas de autoria como “quais playlists você criou?” agora vencem o termo
  genérico “playlist”, enquanto “quais minhas playlists?” continua consultando
  somente as listas do usuário;
- contexto, memória, aprendizado pelo histórico, linguagem natural,
  continuidade, segurança, diagnóstico, consciência da habilidade e
  orquestração cooperativa foram conectados ao mesmo fluxo;
- o quadro cooperativo recebe apenas contagens sanitizadas da relação entre
  playlists, histórico e curadoria; títulos, URLs e registros privados não são
  publicados;
- o contrato obrigatório do projeto agora reconhece a orquestração cooperativa
  como o nono pilar de integração de habilidades;
- regressões direcionadas: 119 testes aprovados;
- suíte completa: 1.607 testes e 41 subtestes aprovados em 10,57 segundos;
- próximo passo recomendado permanece P3.6: contrato tipado das operações
  musicais mutáveis e de reprodução, incluindo cópia e auto-next.

### 2026-07-30 — tolerância inteligente a erros de português

- as correções antes dispersas entre normalização fonética, apelidos e uma
  exceção exclusiva de IoT foram ligadas a um corretor operacional canônico;
- verbos com digitação trocada são aproximados somente na moldura do pedido e,
  fora das correções explícitas inequívocas, exigem um domínio reconhecível;
- nomes de pessoas, músicas, arquivos, pastas, aplicativos e playlists não
  passam por aproximação ortográfica; introduções como `arquivo chamado ...`
  abrem uma zona opaca para preservar o argumento literal;
- continuações naturais aceitam erros inequívocos como `adciona essa também`
  sem exigir que o domínio seja repetido;
- verbos físicos curtos e ambíguos, negações, hipóteses e conversas não ganham
  autorização por causa da correção textual;
- o diagnóstico da mente passou a expor normalizações, entradas corrigidas e
  substituições, declarando que o corretor não autoriza execução;
- a propriedade das playlists também foi separada na fala e na continuidade:
  curadorias usam primeira pessoa da Laylay e playlists do usuário permanecem
  na segunda pessoa;
- regressões direcionadas: 128 testes aprovados;
- suíte completa: 1.616 testes e 41 subtestes aprovados em 11,12 segundos;
- próximo passo recomendado permanece P3.6: contrato tipado das operações
  musicais mutáveis e de reprodução, preservando autorização e auto-next.

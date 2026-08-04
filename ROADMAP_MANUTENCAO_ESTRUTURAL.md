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

## Novo ciclo de consolidação — agosto de 2026

Este ciclo começa depois da conclusão das manutenções P0–P6. O foco agora não
é aumentar a quantidade de habilidades, mas transformar o estado atual em uma
base mais previsível, tipada, observável e fácil de distribuir.

Retrato verificado em 1º de agosto de 2026:

- 1.740 testes e 45 subtestes aprovados;
- Ruff aprovado sem regressões críticas;
- portão oficial de qualidade aprovado;
- cobertura estrutural de 64%, incluindo ramificações;
- 473 diagnósticos no mypy quando ele é executado sobre todo o pacote;
- `laylay.py` com aproximadamente 3.800 linhas físicas;
- cerca de 809 capturas amplas de `Exception` e 330 blocos silenciosos
  identificados por varredura bruta, incluindo integrações opcionais legítimas;
- nenhum arquivo conhecido de credencial, memória pessoal ou configuração
  local da Tuya rastreado pelo Git;
- ausência de uma política explícita de finais de linha em `.gitattributes`.

Os números de exceções e tamanho são indicadores de investigação, não metas de
remoção cega. Resiliência não deve ser trocada por silêncio, e arquivos não
devem ser divididos apenas para satisfazer uma contagem.

## P7 — Base estável e checkpoint reproduzível

**Status: concluída em 1º de agosto de 2026.**

Objetivo: criar um ponto confiável de comparação e reversão antes da próxima
refatoração estrutural.

1. [x] separar mudanças de manutenção das mudanças de habilidade e de dados
   pessoais;
2. [x] registrar a suíte, cobertura, tipagem e latências da versão candidata;
3. [x] adicionar `.gitattributes` com uma política única de finais de linha,
   sem produzir uma reescrita mecânica junto de mudanças funcionais;
4. [x] executar um teste de fumaça da inicialização, conversa, comando, modo
   jogo e encerramento;
5. [x] validar o build portátil em uma pasta limpa;
6. [x] documentar versão, configuração mínima e procedimento de reversão.

Evidências da primeira execução:

- checkpoint sanitizado gerado por `scripts/gerar_checkpoint_manutencao.py`,
  sem leitura de conteúdo pessoal e sem arquivo sensível versionado;
- smoke test com cinco fluxos críticos aprovado;
- build estrutural portátil aprovado com `Laylay.exe`, `AvatarLaylay.exe` e
  `Iniciar Laylay.exe`;
- pacote de 476,4 MB sem modelo, memória, playlists ou configuração privada;
- configuração do pacote idêntica a `configuracao.portatil.example.env`;
- procedimento registrado em `CHECKPOINT_MANUTENCAO.md`.
- estado funcional consolidado no commit `02ea1e0`, separado da infraestrutura
  de checkpoint da P7.

Critério de conclusão:

- o estado da versão pode ser reconstruído e comparado;
- o Git não apresenta ruído generalizado de LF/CRLF;
- código, testes, configuração pública e dados privados possuem fronteiras
  inequívocas;
- a versão candidata inicia, executa um fluxo real e encerra corretamente.

## P8 — Tipagem dos caminhos críticos

**Status: concluída em 1º de agosto de 2026.**

Linha de base registrada em 1º de agosto de 2026:

- 473 diagnósticos em 108 módulos antes da primeira fatia da P8;
- categorias dominantes: `union-attr` (166), `arg-type` (117), `operator`
  (34), `assignment` (32) e `var-annotated` (25);
- após tipar turno, resultado de ação, composição e fronteiras prioritárias:
  438 diagnósticos em 101 módulos, sem `ignore` amplo;
- a barreira gradual da CI cobre 19 módulos tipados, incluindo os registros e
  executores prioritários de IoT, arquivos, música, navegador e agenda.

Objetivo: fazer a tipagem proteger primeiro os caminhos nos quais um valor
incorreto pode executar, confirmar ou lembrar algo indevidamente.

Ordem interna:

1. [x] congelar a contagem e as categorias atuais do mypy completo;
2. [x] corrigir acessos opcionais e contratos incompatíveis no turno,
   resultado de ação e composição principal;
3. [x] tipar as fronteiras dos executores de IoT, arquivos, música, navegador
   e agenda;
4. [x] substituir `Any` somente nas fronteiras cujo contrato já é conhecido;
5. [x] ampliar gradualmente a lista de módulos verificados pela CI;
6. [x] impedir novos erros de tipagem nos módulos já migrados.

Critério de conclusão:

- nenhum caminho crítico acessa uma dependência opcional sem validação;
- resultado observado, autorização e confirmação mantêm tipos distintos;
- a CI cobre todos os contratos centrais e os executores prioritários;
- a redução de diagnósticos vem de contratos reais, não de `ignore` amplo.

## P9 — Exceções, fallbacks e falhas silenciosas

**Status: concluída em 1º de agosto de 2026.**

Linha de base registrada em 1º de agosto de 2026:

- 623 capturas de exceção nos pacotes críticos inspecionados; o número inclui
  proteções legítimas de integrações opcionais e não é uma meta de remoção;
- falhas agora podem carregar domínio, fase e identificador sanitizado do
  turno, sem persistir mensagem, caminho ou conteúdo privado;
- o relator técnico foi conectado ao contexto único dos executores, sem expor
  o objeto interno de observabilidade;
- a primeira fatia removeu silêncios em arquivos, música e navegador;
- a fatia final conectou persistência do prompt, montagem de contexto, sessão
  da LLM e voz ao mesmo relator, inclusive nos fallbacks que preservam o fluxo;
- a classificação adotada distingue controle esperado, degradação de fronteira
  externa e defeito de contrato interno. Limpezas best-effort continuam locais,
  enquanto toda falha com efeito no turno, comando, fala ou serviço é publicada.

Objetivo: manter o isolamento das integrações opcionais sem permitir que um
defeito real desapareça em uma resposta genérica.

1. [x] classificar as capturas amplas restantes por falha esperada, degradação
   externa ou defeito interno;
2. [x] priorizar os blocos silenciosos em execução de comandos, persistência,
   contexto, LLM, áudio e navegador;
3. [x] preservar exceções amplas somente nas fronteiras que realmente precisam
   impedir a queda de um serviço;
4. [x] registrar categoria, domínio, fase e identificador do turno sem expor
   conteúdo privado;
5. [x] impedir que fallback conversacional afirme sucesso, falha ou ausência de
   capacidade sem evidência operacional;
6. [x] testar timeout, dependência ausente, retorno malformado e falha parcial
   em cooperação.

Validação de conclusão:

- Ruff e compilação aprovados;
- barreira gradual do mypy aprovada em 20 arquivos-fonte;
- 1.756 testes e 45 subtestes aprovados;
- cobertura total de 64%, acima do piso estrutural de 50%;
- auditoria local confirmou fallback seguro para falhas de persistência,
  getters de contexto, timer/descarregamento da LLM e adaptação/entrega de voz.

Critério de conclusão:

- toda falha com impacto para o usuário aparece no diagnóstico;
- uma integração opcional pode cair sem derrubar a Laylay;
- uma falha interna não é convertida silenciosamente em conversa;
- nenhum fallback inventa execução ou confirmação.

## P10 — Redução da raiz de composição

**Status: concluída em 01/08/2026.**

Objetivo: fazer `laylay.py` cuidar apenas de configuração, composição, ciclo de
vida e início da aplicação.

1. [x] inventariar as responsabilidades ainda presentes em `laylay.py`;
2. [x] mover regras de domínio restantes para o pacote proprietário;
3. [x] substituir as conexões restantes por `globals()` por registros ou portas
   tipadas já existentes;
4. [x] centralizar configuração e construção dos runtimes sem criar um novo
   arquivo monolítico;
5. [x] preservar um único supervisor de serviços e uma única sequência de
   encerramento;
6. [x] reduzir a raiz em fatias pequenas, com teste de composição real em cada
   fatia.

Critério de conclusão:

- `laylay.py` não interpreta linguagem nem contém comportamento de domínio;
- módulos de `mente_laylay` não importam a raiz da aplicação;
- a composição falha cedo quando uma dependência obrigatória está ausente;
- a raiz fica substancialmente menor sem alterar os fluxos protegidos.

Evidências de conclusão:

- iniciativa, clipboard, cooperação, identidade, memória visual, briefing e
  demais adaptadores de domínio foram movidos para `mente_laylay/integracao`;
- as conexões de composição não recebem mais `globals()` diretamente: um único
  registro allowlist congela apenas os serviços conhecidos e rejeita publicação
  fora do contrato;
- serviços tardios são publicados explicitamente no registro, e dependências
  obrigatórias ausentes falham antes do início dos serviços;
- `laylay.py` passou de 3.816 para 3.412 linhas e conserva somente configuração,
  composição, observabilidade da raiz e ciclo de vida;
- nenhum módulo de `mente_laylay` importa a raiz;
- regressões específicas da P10 e importação real da composição passaram;
- verificação final: Ruff aprovado, mypy aprovado em 20 fontes, 1.761 testes e
  45 subtestes aprovados, cobertura global de 63%.

## P11 — Decomposição dos módulos grandes

**Status: concluída em 02/08/2026.**

Objetivo: reduzir o custo de entendimento e o risco de regressão nos maiores
núcleos do sistema.

Prioridade inicial:

1. [x] `personalidade/conversa_natural.py`;
2. [x] `autonomia/processamento_resposta_ia.py`;
3. [x] `percepcao/janelas_sistema.py`;
4. [x] `autonomia/roteador_deterministico.py`;
5. [x] `memoria_mental/diagnostico_mente.py`;
6. [x] demais módulos acima de mil linhas, somente quando houver mais de uma
   responsabilidade comprovada.

Regras da decomposição:

- separar por responsabilidade e contrato, não por quantidade de linhas;
- evitar dependência circular e estado duplicado;
- manter uma fachada compatível durante a migração;
- retirar a fachada somente depois de migrar composição e testes;
- não criar novos roteadores concorrentes nem listas privadas de linguagem.

Critério de conclusão:

- cada módulo prioritário possui uma responsabilidade central reconhecível;
- as dependências entre submódulos são explícitas;
- os testes deixam de depender de detalhes internos da fachada antiga;
- nenhuma decomposição muda personalidade ou comportamento por acidente.

Implementação concluída:

- conversa natural separada em classificação curta e continuidade/resumos,
  mantendo a fachada e o runtime públicos;
- processamento da IA separado entre higiene/recuperação textual e preparação
  operacional da resposta;
- janelas separadas entre observação/priorização de layout e manipulação do
  sistema;
- detectores de playlist retirados do roteador determinístico central;
- apresentação do diagnóstico retirada da construção do retrato mental;
- auditoria dos demais módulos grandes separou também o pré-fluxo musical; os
  runtimes de voz e contexto, o repositório da rede associativa e a fachada de
  conversa permaneceram coesos por responsabilidade;
- contratos arquiteturais adicionados para garantir que as fachadas deleguem
  aos novos módulos, sem ciclos nem estado duplicado;
- verificação final: Ruff aprovado, mypy aprovado em 20 fontes, 1.766 testes e
  45 subtestes aprovados, cobertura global de 63%.

## P12 — Cobertura orientada a risco e integração real

**Status: concluída em 02/08/2026.**

Objetivo: usar cobertura para proteger comportamento operacional, não apenas
elevar uma porcentagem.

1. [x] priorizar módulos de baixa cobertura que controlam arquivos, janelas,
   navegador, mídia, persistência e contexto;
2. [x] cobrir caminhos negativos e ramificações de falha, não apenas sucesso;
3. [x] adicionar testes de composição real para os fluxos que hoje dependem de
   muitos mocks;
4. [x] testar idempotência, repetição, cancelamento e confirmação nos principais
   executores mutáveis;
5. [x] testar concorrência entre chat, voz, proatividade, visão e serviços de
   fundo;
6. [x] elevar a cobertura mínima somente depois que os caminhos prioritários
   estiverem protegidos.

Critério de conclusão:

- os principais comandos mutáveis possuem sucesso, falha, repetição e
  cancelamento testados;
- falhas parciais de cooperação nunca aparecem como sucesso integral;
- os módulos operacionais críticos deixam de concentrar lacunas relevantes;
- a nova meta de cobertura é sustentada por testes úteis e estáveis.

Implementação e evidências:

- foram adicionadas matrizes de risco para arquivos mutáveis, mídia, navegador,
  persistência, serviços concorrentes e comandos do sistema;
- criação repetida, sobrescrita confirmada, cancelamento, lixeira, falhas de
  mídia, fechamento parcial de abas e isolamento de serviços passaram a ter
  regressões explícitas;
- o teste de composição inicia chat, voz, proatividade e visão em threads reais
  e comprova que a queda de um serviço não cancela os demais;
- o porteiro do navegador agora preserva abas que falharam e nunca anuncia uma
  limpeza integral depois de sucesso apenas parcial;
- o executor do navegador deixou de confirmar o fechamento de aplicativo quando
  o envio do comando falha;
- caminhos absolutos do Windows, como `C:\...`, deixaram de ser confundidos com
  protocolos URI na abertura de programas;
- a cobertura de `comandos_sistema.py` subiu de 17% para 69%; arquivos, mídia,
  persistência e porteiro do navegador também receberam proteção orientada aos
  seus ramos operacionais;
- a meta mínima global subiu de 50% para 60% somente após a nova matriz passar;
- verificação final: Ruff aprovado, mypy aprovado em 20 fontes, 1.801 testes e
  45 subtestes aprovados, cobertura global de 64%.

## P13 — Higiene de distribuição e versão final

**Status: concluída em 02/08/2026; ciclo encerrado.**

Objetivo: transformar a base consolidada em uma versão portátil verificável e
segura para uso em outro computador.

1. [x] executar o portão completo de qualidade, incluindo auditoria de
   dependências;
2. [x] validar que credenciais, memória pessoal e arquivos Tuya continuam fora
   do pacote e do versionamento;
3. [x] verificar instalação limpa, migração de memória e ausência de caminhos
   absolutos da máquina de desenvolvimento;
4. [x] testar ausência de Ollama, indisponibilidade de rede e integrações
   opcionais desativadas;
5. [x] validar terminal, atalhos, voz, avatar, navegador e modo jogo no pacote;
6. [x] gerar relatório final com testes, cobertura, tipagem restante, limitações
   conhecidas e instruções de recuperação.

Critério de conclusão:

- o pacote inicia e degrada com clareza quando um recurso opcional não existe;
- dados privados não entram no artefato;
- a versão possui evidência reproduzível de qualidade e limitações conhecidas;
- o próximo ciclo pode começar sem carregar dívida não documentada deste.

Implementação e evidências:

- o build agora remove integralmente `dist` e `work` antes de montar, impedindo
  resíduos de memória ou credenciais de uma compilação privada anterior;
- memória pessoal e playlists foram separadas de credenciais Tuya, configuração
  privada e amostras de voz por autorizações explícitas diferentes;
- `verificar_pacote.py` audita versionamento, arquivos privados, credenciais,
  autorização IoT, caminhos pessoais, modelo, motores e artefatos obrigatórios;
- o próprio `Laylay.exe` ganhou um smoke de distribuição sem rede ou hardware,
  cobrindo chat, atalhos, voz, avatar, navegador, modo jogo, memória gravável e
  seleção do backend portátil sem Ollama;
- a migração de memória JSON legada para SQLite foi protegida por regressão;
- foi gerado um pacote completo de 2,79 GB, com 1.887 arquivos, modelo GGUF e
  motores Vulkan/CPU; a auditoria encontrou zero memória e zero arquivos
  privados;
- o relatório `empacotamento/RELATORIO_DISTRIBUICAO_P13.md` registra evidências,
  limitações físicas conhecidas, comandos reproduzíveis e recuperação;
- verificação final: Ruff aprovado, mypy aprovado em 20 fontes, 1.808 testes e
  45 subtestes aprovados, cobertura global de 64% e nenhuma vulnerabilidade
  conhecida nas dependências.

## Ciclo de estabilização pós-P13 — evidências de uso real

**Status geral: pendente.**

Origem: sessão manual completa registrada após o fechamento da P13. A suíte
automatizada protegeu contratos isolados importantes, mas o teste de ponta a
ponta revelou regressões na composição entre linguagem natural, pendências,
continuidade, executores e autoria da resposta.

Leitura correta das evidências:

- a memória de pessoas foi persistida; as consultas naturais é que não chegaram
  ao leitor correto;
- consultas de estado IoT foram executadas corretamente; a fala final misturou
  confirmação com uma âncora de incerteza;
- pausar e retomar mídia foram classificados corretamente, mas a extensão não
  confirmou a execução;
- o detector isolado de clima reconhece as frases testadas, portanto a falha
  está na composição da entrada real antes da LLM;
- o modo jogo não foi exercitado nessa sessão e não pode ser classificado como
  aprovado nem reprovado por ela;
- a avaliação de saúde estrutural e a avaliação de uso diário são dimensões
  diferentes: o código pode passar o portão técnico e ainda ter bloqueadores de
  integração perceptíveis para a pessoa usuária.

### P14 — Bloqueadores de verdade, segurança e isolamento do turno

**Prioridade: P0. Status: concluída em 2026-08-02.**

Objetivo: impedir execução no domínio errado, vazamento técnico e respostas que
afirmam simultaneamente sucesso e falha.

1. [x] tornar o resultado de uma ação atômico por turno, com `intent`, alvo,
   status, evidência e domínio vindos do mesmo evento;
2. [x] impedir que alvo ou status antigos atravessem domínios, como uma leitura
   de e-mail herdar o alvo de um lembrete;
3. [x] garantir uma única classe epistêmica por fala: sucesso confirmado,
   falha, cancelamento, pendência ou desconhecido — nunca duas delas juntas;
4. [x] tratar cancelamento confirmado como desfecho válido, sem prefixo de
   falha ou “não consegui concluir”;
5. [x] bloquear sentinelas técnicas da LLM em todas as saídas, inclusive
   continuações, confirmações, resumos e respostas produzidas por habilidades;
6. [x] restringir operações destrutivas da memória de pessoas a uma referência
   pessoal explícita ou a uma identidade conhecida;
7. [x] reservar substantivos operacionais explícitos, como arquivo e pasta, ao
   domínio correspondente; com ou sem erro ortográfico, eles nunca podem virar
   `PEOPLE_FORGET`;
8. [x] impedir que perguntas sobre dados pessoais recebam lembranças inventadas:
   toda afirmação deve apontar para memória persistida ou declarar ausência;
9. [x] fazer ofertas opcionais, como analisar a área de transferência, cederem
   silenciosamente quando a mensagem seguinte inicia outro assunto;
10. [x] consumir uma oferta somente com aceitação, recusa ou referência
   semanticamente vinculada a ela.

Critério de conclusão:

- zero execução destrutiva em domínio diferente do pedido;
- zero afirmação pessoal sem evidência na memória;
- zero sentinela técnica visível;
- zero resposta com sucesso e falha combinados;
- perguntas novas não são engolidas por ofertas opcionais;
- os casos exatos da sessão passam pela entrada real do chat, não apenas por
  detectores unitários.

Implementação e evidências:

- `ultima_acao_contrato` passou a registrar atomicamente identidade, domínio,
  alvo, status, execução, confirmação e evidência do mesmo evento; o diagnóstico
  não completa mais campos vazios com partes de ações antigas;
- a continuidade por domínio só herda campos quando permanece no mesmo
  `intent`, impedindo contaminação silenciosa entre contratos diferentes;
- cancelamento ganhou classe epistêmica própria e fala compatível, enquanto
  consultas informativas confirmadas descartam âncoras contraditórias de falha;
- sentinelas da LLM são reconhecidas por um detector central e absorvidas tanto
  na validação do turno quanto na fronteira final antes da voz;
- exclusão de memória pessoal exige linguagem pessoal explícita, e termos como
  `arquivo`, `aquivo`, `pasta` e `documento` ficam reservados ao domínio
  operacional;
- consultas sobre pessoas sem registro são interceptadas antes da LLM e recebem
  uma declaração explícita de ausência de memória confirmada;
- ofertas opcionais do clipboard cedem também a perguntas naturais com assunto
  próprio, preservando aceites, recusas e respostas indiretas relacionadas;
- regressões novas cobrem as frases reais da sessão e variantes próximas em
  `tests/test_p14_integridade_turno.py`, `tests/test_memoria_pessoas.py` e
  `tests/test_adaptador_resultado.py`;
- portão final: Ruff aprovado, mypy aprovado nos 20 módulos tipados, 1.816 testes
  e 45 subtestes aprovados.

### P15 — Continuidade semântica, referências e episódios de conversa

**Prioridade: P1. Status: concluída em 2026-08-02.**

Objetivo: manter o referente e o assunto corretos em continuações naturais,
sem ressuscitar entidades antigas.

1. [x] interpretar “agora explique com mais detalhes” como transformação da
   resposta imediatamente anterior, preservando o assunto;
2. [x] aceitar variações e erros leves em consultas sobre pessoas já
   memorizadas, incluindo perguntas de relação formuladas em ordem diferente;
3. [x] definir uma ordem única de saliência: pendência canônica ativa, entidade
   da ação atual, último resultado confirmado do mesmo domínio e só então
   referências antigas;
4. [x] invalidar referências obsoletas quando uma operação mais recente cria
   ou seleciona outra entidade do mesmo domínio;
5. [x] remover modificadores de repetição do alvo de aplicativo, como “de
   novo”, “novamente” e “outra vez”, preservando a intenção de repetir/focar;
6. [x] segmentar discussões da caixa de entrada por episódio e assunto atual;
7. [x] excluir comandos, resultados operacionais, logs e assuntos encerrados do
   resumo de uma ideia;
8. [x] pedir confirmação em vez de salvar quando o assunto corrente não tiver
   confiança suficiente.

Critério de conclusão:

- pronomes e continuações apontam para a entidade mais recente e compatível;
- consultas sobre uma pessoa recém-memorizada retornam os dados persistidos;
- uma ideia salva representa a discussão atual, não uma operação anterior;
- repetir a abertura de um aplicativo não incorpora “de novo” ao seu nome.

Implementação e evidências:

- pedidos de detalhamento usam a fala imediatamente anterior como fonte e
  levam somente o assunto, a fala e o ponto central ao modelo; se ele estiver
  indisponível, a resposta local conserva explicitamente o mesmo referente;
- `selecionar_referente_saliente` centraliza a ordem pendência canônica, ação
  atual, continuidade confirmada do domínio e referências anteriores;
- uma nova ação substitui atomicamente a entidade anterior do mesmo domínio,
  sem completar alvos vazios com dados obsoletos;
- consultas sobre pessoas aceitam erro leve em “sabe” e perguntas de relação
  em ordem invertida, mantendo a memória persistida como única fonte factual;
- a normalização compartilhada de aplicativos remove `de novo`, `novamente`,
  `outra vez` e `mais uma vez` apenas quando aparecem como sufixo operacional;
- a caixa de entrada agora delimita o episódio atual, ignora logs, fallbacks e
  comandos operacionais, e usa a pendência canônica antes de salvar um recorte
  cuja proposta não esteja suficientemente clara;
- as regressões específicas estão em `tests/test_p15_continuidade_semantica.py`,
  com variações adicionais em `tests/test_memoria_pessoas.py`;
- portão final: Ruff aprovado, mypy isolado aprovado, 1.823 testes e 45
  subtestes aprovados.

### P16 — Linguagem natural operacional e comandos de leitura

**Prioridade: P1. Status: concluída em 2026-08-02.**

Objetivo: fazer frases naturais alcançarem habilidades existentes antes que a
LLM tente improvisar uma resposta.

1. [x] ampliar a consulta da caixa de entrada para construções como “me fale
   minhas ideias”, sem depender de uma frase exata;
2. [x] reconhecer perguntas naturais sobre compromissos como leitura direta da
   agenda, sem pedir autorização para uma operação somente leitura;
3. [x] unificar a extração de duração para segundos, minutos e horas em
   lembretes e continuações;
4. [x] separar o texto do lembrete do trecho temporal, impedindo descrições como
   “beber água daqui a trinta segundos” depois de reagendar;
5. [x] garantir que clima e temperatura atravessem o detector determinístico na
   composição real do chat antes da LLM;
6. [x] proibir respostas sobre clima atual sem evidência de um provedor ou uma
   mensagem explícita de indisponibilidade;
7. [x] adicionar tolerância para erros ortográficos operacionais frequentes sem
   criar correções agressivas em conversa comum;
8. [x] preservar controles de mídia em erros leves, como uma grafia incompleta
   de “passa para a próxima”, sem confundir conversa comum com execução;
9. [x] interpretar perguntas de seguimento sobre e-mails já lidos, como
   urgência, usando os resultados observados em vez de uma suposição da LLM;
10. [x] medir resolução natural por habilidade e por frase real, distinguindo
   conversa legítima de comando não reconhecido.

Critério de conclusão:

- agenda, clima, caixa de entrada e lembretes respondem às variações testadas;
- nenhuma informação temporal atual é inventada pela LLM;
- lembretes relativos preservam descrição e horário corretos;
- os testes atravessam a mesma composição usada pelo terminal e pela voz.

Implementação e evidências:

- a caixa de entrada reconhece pedidos flexíveis para falar, contar, mostrar ou
  relembrar ideias e notas, mantendo frases criativas sem intenção de leitura
  fora do executor;
- a agenda intercepta consultas naturais somente leitura antes da LLM e usa
  uma única extração relativa, em `atraso_segundos`, para números escritos ou
  falados em segundos, minutos e horas;
- o trecho temporal é removido antes de persistir a descrição, enquanto
  preposições internas como em `consulta de dentista` são preservadas;
- consultas de clima comuns e variantes ortográficas atravessam o detector
  determinístico; falha ou exceção do provedor gera `clima_indisponivel`, e o
  verificador final impede uma resposta conversacional de inventar o clima;
- a tolerância ortográfica ganhou apenas termos operacionais comprovados e a
  forma incompleta `passa para a proxma`, sem aproximar nomes de arquivos,
  faixas, pessoas ou conversa comum;
- perguntas como `algum deles é urgente?` só reutilizam o domínio de e-mail
  quando a leitura anterior foi observada como `emails_lidos`, voltando ao
  leitor e ao cache reais em vez de pedir uma classificação factual à LLM;
- o diagnóstico de linguagem natural agora mede habilidade e moldura da frase
  por contadores sanitizados, além de separar comando não reconhecido de
  conversa legítima sem armazenar o texto da pessoa;
- `tests/test_p16_linguagem_natural_operacional.py` cobre frases reais,
  negativas próximas, terminal/voz e composição; regressões antigas de agenda,
  clima, caixa, comunicação e decisão única também permaneceram verdes;
- portão final: Ruff, compilação e mypy isolado em sete fontes aprovados,
  1.833 testes e 45 subtestes aprovados.

### P17 — Mídia, pesquisa musical e evidência do navegador

**Prioridade: P2. Status: concluída em 2026-08-02.**

Objetivo: transformar pedidos musicais em conteúdo realmente reproduzível e
distinguir classificação correta de confirmação externa ausente.

1. [x] revisar o protocolo de confirmação da extensão para pausar, retomar e
   avançar, incluindo identidade da aba e estado observável do player;
2. [x] manter a resposta honesta quando o navegador não confirmar a ação, sem
   repetir o comando nem anunciar sucesso presumido;
3. [x] aplicar o refinamento contextual também a trabalho, estudo e outras
   atividades pela rota completa, não apenas dentro do refinador isolado;
4. [x] separar no resultado `consulta_pedida`, `consulta_resolvida` e
   `alvo_executado`;
5. [x] confirmar que a seleção final é um vídeo/faixa reproduzível, e não apenas
   uma página de busca;
6. [x] fazer a autoria da confirmação usar o alvo realmente executado para não
   acusar divergência depois de um refinamento legítimo.

Critério de conclusão:

- pausar e retomar possuem confirmação observável ou falha explícita;
- pedidos por atividade escolhem uma faixa concreta e explicável;
- pesquisa, execução e fala final concordam sobre o mesmo alvo;
- nenhum timeout da extensão produz falso sucesso ou reprodução duplicada.

Implementação e evidências:

- a resolução musical agora preserva título, canal e URL da faixa concreta; se
  nenhum vídeo reproduzível for encontrado, a Laylay encerra com falha explícita
  sem abrir uma página de resultados como substituta;
- o contrato operacional separa `consulta_pedida`, `consulta_resolvida` e
  `alvo_executado`, e a autoria recebe o título efetivamente selecionado;
- a camada Python deixou de reduzir a resposta da extensão a um booleano: estado
  do player, aba, status e mensagem permanecem disponíveis até o executor;
- pausar, retomar, avançar, voltar e reiniciar usam a identidade observada da
  aba; a extensão valida mudança de reprodução ou de faixa antes de confirmar;
- timeouts e ausência de mudança falham uma única vez, sem repetição automática
  nem fala de sucesso presumido;
- refinamento contextual validado pela rota completa para trabalho/programação,
  estudo, treino, descanso e jogo;
- portão final: Ruff, compilação Python, sintaxe JavaScript e mypy isolado em
  sete fontes aprovados; 1.840 testes e 45 subtestes aprovados.

### P18 — Semântica operacional e apresentação fiel do sistema

**Prioridade: P2. Status: concluída em 2026-08-02.**

Objetivo: responder de forma natural sem distorcer o pedido nem a realidade do
sistema operacional.

1. [x] tratar sugestões indiretas, como “talvez fosse legal deixar a luz
   vermelha”, segundo confiança e política de autonomia, sem transformá-las em
   uma recusa que a pessoa não fez;
2. [x] impedir que perguntas de estado IoT tentem interpretar formas de “estar”
   como nomes de cor;
3. [x] separar “janelas visíveis/abertas” de “processos em segundo plano” na
   observação e na fala;
4. [x] filtrar overlays, componentes do sistema e processos sem janela da lista
   apresentada como aplicativos visíveis;
5. [x] distinguir na fala se um aplicativo foi iniciado, apenas focalizado ou
   já estava aberto e em foco, usando o estado anterior e o posterior;
6. [x] manter personalidade e emoção depois da verdade operacional, sem usar
   humor para esconder status, dúvida ou falha;
7. [x] auditar por que a emoção causal foi avaliada várias vezes sem nenhuma
   expressão na sessão e decidir se foi contenção correta ou perda de sinal.

Critério de conclusão:

- a fala nunca atribui ao usuário uma decisão que ele não tomou;
- consultas de estado não acionam extração de cor;
- a lista de programas explica claramente janela, aba e processo;
- personalidade varia sem mudar o significado do resultado.

Implementação e evidências:

- propostas indiretas de iluminação agora viram `SUGGEST_ACTION` com confiança,
  reversibilidade e elegibilidade autônoma explícitas; uma hipótese não é mais
  narrada como recusa nem executada como ordem;
- consultas de estado IoT vencem a extração de propriedades e cores antes de
  qualquer resolução livre, inclusive em “como está a lâmpada?”;
- a percepção publica um retrato separado de janelas visíveis, processos
  relevantes em segundo plano e componentes filtrados; overlays e janelas do
  sistema não aparecem mais como aplicativos da pessoa;
- a consulta local explica que abas pertencem ao navegador e não são processos
  ou aplicativos separados;
- `app_iniciado_focado`, `app_focado` e `ja_aberto_focado` preservam três fatos
  distintos: início novo, foco de janela existente e não-ação confirmada;
- a autoria operacional precisa abrir pela verdade e pelo alvo observados; só
  depois pode acrescentar personalidade, emoção ou deboche;
- a emoção causal registra contenções, taxa e motivo da última decisão, tornando
  explícito quando o silêncio emocional foi prudência e não perda de sinal;
- regressões próprias da P18 cobrem sugestão indireta, estado IoT, inventário de
  janelas/processos, ciclo de abertura e auditoria emocional.
- portão final: 1.847 testes e 45 subtestes aprovados; `py_compile`, Ruff,
  `git diff --check` e mypy isolado nas fontes tipadas alteradas também
  aprovados.

### P19 — Observabilidade, contexto e custo por turno

**Prioridade: P3. Status: concluída em 2026-08-02.**

Objetivo: fazer o diagnóstico representar o que realmente aconteceu e revelar
contaminação ou trabalho duplicado antes que virem comportamento visível.

1. [x] alinhar saúde da LLM, contadores de falha e lista de falhas recentes;
2. [x] mostrar cada pendência com origem, ação, idade, prazo e motivo de ainda
   estar ativa;
3. [x] distinguir serviços ativos, intencionalmente desativados, encerrados e
   degradados;
4. [x] corrigir a última ação para que domínio, alvo e status pertençam ao mesmo
   evento confirmado;
5. [x] separar métricas brutas, selecionadas, truncadas e efetivamente enviadas
   no orçamento do prompt;
6. [x] medir normalizações únicas por turno e eliminar reaplicações idênticas em
   camadas sucessivas;
7. [x] registrar por que uma intenção natural não foi resolvida, sem despejar
   conteúdo privado no log;
8. [x] perfilar a latência total da voz separando síntese, fila, reprodução e
   bloqueios externos.

Critério de conclusão:

- um diagnóstico explica cada degradação observada na sessão;
- “falhas recentes: zero” não aparece quando houve vazamento técnico ou backend
  degradado;
- as métricas do prompt fecham matematicamente e deixam claro o que foi enviado;
- pendências antigas e normalizações duplicadas ficam visíveis e auditáveis.

Implementação e evidências:

- a saúde viva da LLM agora reconcilia disponibilidade do contrato, estado do
  backend, falhas consecutivas e falhas recentes sanitizadas;
- pendências são apresentadas com origem, ação, idade, prazo, motivo e status,
  sem expor pergunta, referência ou conteúdo privado;
- serviços de fundo possuem classes distintas para ativos, desativados por
  configuração, encerrados e degradados;
- a última ação continua compatível com leitores antigos, mas recebe uma
  auditoria atômica separada com domínio, fonte, identificador e coerência;
- o orçamento do prompt fecha as etapas de preparação e transporte com números
  de caracteres brutos, selecionados, truncados, injetados e enviados;
- a normalização reutiliza resultados idênticos no mesmo turno e publica
  contadores de trabalho único e reaplicações evitadas;
- intenções naturais não resolvidas registram apenas motivo, moldura e rota;
- a voz mede separadamente fila, síntese, bloqueio externo, reprodução e total;
- portão final: 1.855 testes e 45 subtestes aprovados; regressão focada com 38
  testes aprovada; `py_compile`, Ruff, `git diff --check` e mypy isolado em
  cinco fontes aprovados.

### P20 — Requalificação de uso diário

**Prioridade: portão final. Status: automação concluída em 2026-08-02; validação manual pendente.**

Objetivo: provar que as correções funcionam juntas no mesmo fluxo em que as
regressões apareceram.

1. [x] transformar cada falha da sessão manual em regressão pela entrada real;
2. [x] executar uma conversa longa misturando memória, arquivos, agenda, IoT,
   mídia, clima, caixa de entrada e área de transferência;
3. [x] repetir a matriz no terminal e por voz;
4. [x] executar uma matriz própria do modo jogo, ausente no teste atual;
5. [x] verificar zero falsa execução, zero alvo cruzado, zero contradição e zero
   sentinela técnica;
6. [x] confirmar que todas as pendências encerram, expiram ou cedem a outro
   assunto de forma observável;
7. [ ] realizar novo teste manual antes de declarar a versão estável para uso
   diário.

Critério de conclusão:

- todos os casos da sessão original e suas variações passam em conjunto;
- terminal, voz e modo jogo preservam os mesmos contratos;
- o resultado manual concorda com os testes automatizados;
- o ciclo só é encerrado depois da validação da pessoa usuária.

Implementação e evidências automatizadas:

- uma matriz integrada passa pela entrada canônica, pelo coordenador de turno,
  pelo árbitro, pelos detectores reais e pela continuidade compartilhada;
- a conversa longa cobre agenda, IoT, música, clima, caixa de entrada, área de
  transferência, memória de pessoas e pesquisa de arquivos;
- terminal, voz e modo jogo produzem os mesmos contratos operacionais para os
  mesmos pedidos;
- o modo jogo preserva visão, música e IoT sem cruzar o nome do jogo com o alvo
  físico;
- perguntas hipotéticas, negações e consultas de capacidade terminam sem
  executar ações;
- aceite, recusa, expiração e cessão de pendências são observados pelo mesmo
  runtime canônico;
- a requalificação encontrou e corrigiu três lacunas de composição: leitura de
  estado IoT antes do filtro casual, `CLIPBOARD_READ` como consulta segura e
  `GAME_VISION` como leitura explícita permitida pelo árbitro;
- a primeira execução manual da Matriz A encontrou quatro regressões que a
  simulação não expunha: consultas de leitura vetadas pelo parecer operacional,
  `e-mails` perdido após normalização, busca de arquivo devolvida à conversa e
  parser musical incompatível com os metadados atuais do YouTube;
- as correções agora preservam consultas somente de leitura no árbitro,
  reconhecem `email`, `e-mail` e `e mails`, antecipam clima/email/pesquisa de
  arquivo antes do filtro casual e resolvem novamente vídeos concretos do
  YouTube; identificadores como `C418` também não podem ser alterados pela fala;
- regressão P20: 10 testes aprovados; matriz ampliada: 200 testes aprovados;
- portão automatizado completo após a correção manual: 1.869 testes e 45
  subtestes aprovados;
- o roteiro `TESTE_MANUAL_P20_REQUALIFICACAO.md` é o último requisito ainda
  aberto e deve ser executado na aplicação completa antes do fechamento.

## Ordem recomendada

### Ciclo histórico concluído

1. P7 — base estável;
2. P8 e P9 — contratos tipados e falhas observáveis;
3. P10 — raiz de composição;
4. P11 — módulos grandes;
5. P12 — cobertura das lacunas encontradas durante a migração;
6. P13 — distribuição e fechamento do ciclo.

### Novo ciclo de estabilização

1. P14 — bloquear falsos estados, vazamentos e ações no domínio errado;
2. P15 e P16 — restaurar continuidade e cobertura da linguagem natural;
3. P17 e P18 — corrigir integrações externas e apresentação operacional;
4. P19 — tornar diagnóstico, contexto e custo confiáveis;
5. P20 — requalificar a versão em uso real.

Cada fase deve atualizar o retrato de métricas, registrar apenas decisões ainda
úteis e marcar seus itens somente depois da suíte completa. Nenhuma fase deste
ciclo autoriza uma nova habilidade, uma mudança de personalidade ou uma quebra
de compatibilidade com as memórias existentes.

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

## Ordem recomendada

1. P7 — base estável;
2. P8 e P9 — contratos tipados e falhas observáveis;
3. P10 — raiz de composição;
4. P11 — módulos grandes;
5. P12 — cobertura das lacunas encontradas durante a migração;
6. P13 — distribuição e fechamento do ciclo.

Cada fase deve atualizar o retrato de métricas, registrar apenas decisões ainda
úteis e marcar seus itens somente depois da suíte completa. Nenhuma fase deste
ciclo autoriza uma nova habilidade, uma mudança de personalidade ou uma quebra
de compatibilidade com as memórias existentes.

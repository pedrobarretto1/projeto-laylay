# Roadmap de novas habilidades da Laylay

Este documento reúne expansões funcionais para a Laylay depois da estabilização
da mente central. As habilidades serão implementadas **uma por vez**, com testes
e validação em conversa real antes de iniciar a próxima.

Melhorias da mente e do comportamento central continuam documentadas em
`ROADMAP_MELHORIAS_CENTRAIS.md`. Mudanças exclusivamente visuais pertencem ao
roadmap do avatar.

## Princípios de implementação

### Contrato obrigatório antes de marcar uma habilidade como pronta

Toda habilidade nova deve primeiro inventariar os serviços que a mente já
possui. Contexto, memória, aprendizado, linguagem natural e continuidade não
podem ser reimplementados dentro do domínio. O módulo novo acrescenta apenas
vocabulário, entidades, regras e execução próprios; a interpretação de turnos,
confirmações, recusas, correções e referências continua canônica.

A validação final precisa demonstrar, com componentes reais da composição:

- contexto temporário publicado e encerrado na mente compartilhada;
- memória durável somente com proveniência e política de sensibilidade;
- feedback enviado ao motor de aprendizado sem mudar comportamento por uma só amostra;
- frases naturais processadas pelo interpretador compartilhado, inclusive variantes;
- `continua`, `tenta de novo`, pronomes e respostas curtas ligados à pendência correta;
- conversa sobre uma ação separada da autorização para executá-la;
- resultado confirmado pelo executor e falhas visíveis no diagnóstico;
- habilidade registrada no catálogo vivo, disponível ao contexto da LLM quando
  relevante e explicável em linguagem natural com capacidades, limites,
  autorização necessária e evidência de sucesso;
- relações entre agenda, notificações e outras habilidades publicadas no quadro
  cooperativo, sem transformar observação em permissão nem ocultar falha parcial;
- teste negativo garantindo que negação, hipótese e pergunta de capacidade não executem.

Um teste que substitui um desses pilares por um callback sempre verdadeiro não
comprova integração. Deve existir ao menos uma regressão atravessando o caminho
real da composição. As instruções permanentes para agentes estão em `AGENTS.md`.

- Não aumentar o tamanho de `laylay.py` com regras específicas da habilidade.
- Criar cada habilidade em módulo ou especialista próprio.
- Integrar tudo ao estado compartilhado da mente única.
- Separar observação, interpretação e execução.
- Consultas e transformações de texto podem ser diretas; ações destrutivas
  continuam exigindo confirmação.
- Não inventar acesso, conteúdo observado ou resultado de uma ação.
- Preservar conversa natural quando a frase não autorizar execução.
- Adicionar testes unitários, testes de continuidade e testes do fluxo completo.
- Só iniciar a próxima habilidade quando a atual estiver estável no uso real.
- Integrar toda habilidade à continuidade canônica da mente única, incluindo
  referências naturais como `tenta de novo`, `faz isso novamente`, `continua`
  e respostas curtas relacionadas à última ação.
- Publicar no contexto compartilhado somente os dados necessários para que
  conversa, execução e demais habilidades reconheçam o mesmo assunto.
- Enviar resultados, correções, aceitações e recusas ao motor de aprendizado,
  usando evidências múltiplas antes de alterar comportamentos automaticamente.

### Integração da agenda aos nove pilares — concluída

A agenda preserva horários antes da normalização lexical, usa a pendência de ação
canônica para completar lembretes por respostas naturais como `14:30` e separa
`aguardando_complemento` de execução real. Lembretes duráveis mantêm proveniência,
feedback agregado segue para o aprendizado compartilhado e expiração qualificada
vira sinal de silêncio sem persistir o conteúdo do lembrete. Saúde, persistência,
disparos e retries aparecem no diagnóstico e alimentam a disponibilidade do
catálogo vivo. A relação agenda–central de notificações é publicada no quadro
cooperativo e falha de persistência nunca é anunciada como sucesso total.

Validação automatizada: 1.658 testes e 41 subtestes aprovados, incluindo regressões
com o normalizador usado em produção, continuidade curta, recusa segura,
diagnóstico sanitizado, noção de capacidade e falha cooperativa parcial.
- Classificar o que é relevante, irrelevante, temporário ou sensível antes de
  criar memória; dados privados e conteúdo ocasional não devem virar fatos.
- Evitar mecanismos paralelos de continuidade ou memória dentro de uma
  habilidade quando o contrato oficial da mente única puder representá-los.
- Dar à Laylay consciência explícita de toda habilidade implementada por meio
  do mapa vivo de capacidades. Essa consciência deve refletir a disponibilidade
  real em execução, alcançar a LLM somente quando for relevante ao turno e
  permitir que ela explique naturalmente o que pode fazer, como pode ajudar,
  quais são seus limites e quando precisa de autorização. Não inserir listas
  estáticas de habilidades no prompt permanente de personalidade.

### Infraestrutura compartilhada de linguagem natural — concluída

- um único coordenador combina detector determinístico, interpretação natural,
  contexto, memória, referências e continuidade antes do fallback de conversa;
- todas as intents registradas no catálogo vivo ficam disponíveis ao
  interpretador operacional, sem criar gramáticas isoladas por habilidade;
- o árbitro do turno continua sendo a única autoridade: pergunta, hipótese,
  comentário e negação não autorizam ações com efeito;
- consultas somente leitura podem ser formuladas naturalmente e continuam
  validadas pelo recurso real de cada domínio;
- comando reconhecido é considerado tratado mesmo quando o executor relata
  indisponibilidade, impedindo que a LLM invente outro resultado em seguida;
- o diagnóstico da mente informa tentativas, resoluções e a rota usada, mas a
  camada de linguagem natural nunca autoriza execução por conta própria.

### Continuidade operacional de playlists e arquivos — concluída

- o executor publica no contexto canônico o nome e o caminho realmente
  resolvidos, em vez de conservar pronomes como `ela` e `ele` como alvos;
- referências como `essa também`, `o que tem nela?`, `por que não?` e
  `quero ele de volta` permanecem ligadas à ação correta;
- playlists vazias podem ser criadas explicitamente com linguagem natural,
  sem converter o pedido em adição de uma faixa inexistente;
- comentários sobre uma falha anterior não são confundidos com uma nova ordem;
- validação automatizada: 2.103 testes, 8 testes ignorados e 45 subtestes
  aprovados na suíte completa.

## Ordem planejada

### 1. Área de transferência inteligente — concluída

Permitir que a Laylay use, com autorização do usuário, o texto atualmente
copiado no Windows.

Exemplos:

```text
resume o que eu copiei
corrige esse texto que está na área de transferência
traduz o que eu copiei para inglês
pesquisa esse erro que eu copiei
aprende sobre mim com o que eu copiei
salva esse link nas minhas anotações
o que tem na área de transferência?
```

Comportamento esperado:

- Ler somente quando o pedido mencionar ou referenciar claramente o conteúdo
  copiado.
- Informar quando a área de transferência estiver vazia ou tiver um formato
  ainda não suportado.
- Suportar primeiro texto e links; imagens podem entrar em uma etapa posterior.
- Não registrar automaticamente conteúdos copiados na memória permanente.
- Registrar aprendizado duradouro somente após um pedido explícito do usuário.
- Classificar automaticamente sinais pessoais e padrões de interesse; promover
  apenas hipóteses fortalecidas por múltiplas evidências.
- Não expor senhas, tokens, chaves ou outros segredos em logs e diagnósticos.
- Pedir confirmação antes de substituir o conteúdo da área de transferência.
- Manter o conteúdo original disponível caso uma transformação precise ser
  desfeita.

Entregue na primeira versão:

- leitura explícita de texto e links;
- resumo, correção, explicação e tradução pela mente conversacional;
- pesquisa do texto ou erro copiado pelo executor já existente;
- abertura de links HTTP e HTTPS válidos;
- resultado transformado mantido somente em memória temporária;
- substituição apenas após `copia o resultado`;
- restauração com `desfaz a alteração da área de transferência`;
- bloqueio de conteúdo com aparência de senha, token, chave, JWT ou cartão;
- proteção contra sobrescrever algo novo copiado depois da transformação;
- logs contendo apenas operação e tamanho, nunca o conteúdo.
- ações web registradas na continuidade oficial, permitindo `tenta de novo`;
- aprendizado explícito e confirmado integrado à memória semântica.
- aprendizado autônomo seletivo integrado ao motor de hipóteses, sem armazenar
  URLs completas, erros, código ou documentos ocasionais como fatos pessoais.

Ainda fora desta primeira versão:

- leitura de imagens copiadas;
- histórico permanente da área de transferência;
- armazenamento de links em anotações, que dependerá da Caixa de entrada
  pessoal.

### 2. Caixa de entrada pessoal — concluída

Guardar rapidamente ideias, links, tarefas e pensamentos para organização
posterior.

Exemplos:

```text
anota essa ideia
guarda isso para eu ver amanhã
quais ideias eu anotei esta semana?
transforma essa nota em lembrete
```

A habilidade deve classificar notas por assunto sem transformar toda conversa
em memória permanente. Alterações e exclusões precisam ser confirmadas.

Entregue na primeira versão:

- captura explícita de ideias, tarefas, pensamentos, links e notas;
- referência ao assunto anterior em frases como `anota essa ideia`;
- integração segura com texto ou link copiado quando ele for mencionado;
- classificação local por tipo e assuntos, sem depender da LLM;
- filtro por tipo e pelas anotações dos últimos sete dias;
- armazenamento JSON atômico em `memoria/caixa_entrada_pessoal.json`;
- bloqueio de conteúdos com aparência de senha, token, chave ou cartão;
- exclusão lógica somente depois de confirmação;
- conversão para lembrete somente depois de confirmação, reutilizando a agenda;
- continuidade oficial para referências e repetição segura de consultas;
- aprendizado gradual apenas de assuntos recorrentes, sem transformar o texto
  integral das notas em fatos pessoais;
- mapa de habilidades e resultados conectados à mente única.
- captura de uma discussão recente em uma única nota estruturada;
- separação explícita entre ideia do usuário, sugestões da Laylay, decisões e próximos passos;
- recorte por tópico quando o pedido usa formas como `o que discutimos sobre o avatar`;
- resumo assistido pela LLM com validação contra a conversa e síntese literal como fallback;
- nenhum histórico bruto completo é persistido: somente a síntese e seus campos estruturados.

Ainda fora desta primeira versão:

- edição do texto de uma nota existente;
- restauração de itens excluídos;
- busca semântica profunda, prevista na próxima habilidade;
- interface visual dedicada para organizar a caixa.

### 3. Pesquisa semântica nos arquivos — implementada

**Status: implementação concluída; aguardando validação em conversa real.**

Encontrar arquivos pelo significado, assunto ou conteúdo, mesmo quando o nome
exato não for lembrado.

Exemplos:

```text
encontra o documento sobre o avatar
onde está o código que controla a lâmpada?
quais arquivos falam do modo jogo?
ache a imagem que usei ontem
```

A pesquisa será somente leitura. Mover, renomear ou apagar continuará passando
pelo executor de arquivos e por suas confirmações de segurança.

Implementado nesta etapa:

- índice local efêmero, mantido somente em memória e sem envio de arquivos para a internet;
- busca por nome, caminho, conteúdo textual, tipo, termos relacionados e data de modificação;
- raízes pessoais e projeto atual com limites de tempo e quantidade para evitar travamentos;
- exclusão de caches, ambientes virtuais, dependências e pastas de compilação;
- arquivos com aparência de credencial podem ser localizados pelo nome, mas seu conteúdo não é indexado nem exibido;
- linguagem natural para pedidos como `onde está o código que controla a lâmpada?` e `ache a imagem que usei ontem`;
- continuidade pelo contexto compartilhado com `onde ele fica?`, `abre o segundo` e repetição restrita ao projeto;
- abertura somente de um resultado validado dentro das raízes autorizadas;
- aprendizado gradual apenas dos assuntos agregados de buscas úteis, sem persistir caminhos ou trechos;
- diagnóstico seguro do índice, cache, pesquisas e falhas;
- capacidade `FILE_SEARCH` e abertura de resultado registradas no catálogo vivo da mente.

Ficam para uma evolução posterior a extração de conteúdo interno de PDF, DOCX e outros formatos binários e uma indexação persistente opcional.

### 4. Consciência de projetos

Reconhecer o projeto em uso, arquivos recentes, testes, erros e o último ponto
de trabalho confirmado.

Ela poderá oferecer continuidade como:

> Você voltou para este projeto. Da última vez, paramos nos testes da extensão.

O estado deverá vir de evidências locais, nunca de progresso inventado. A
habilidade não editará código autonomamente sem um pedido explícito.

### 5. Central inteligente de notificações — implementada

**Status: implementação concluída; aguardando validação em conversa real.**

Reunir e priorizar e-mails, agenda, lembretes e alertas do computador. A Laylay
deve destacar o que parece importante e evitar ler promoções repetitivas em voz
alta.

O usuário poderá pedir detalhes, dispensar uma categoria ou ensinar quais tipos
de aviso merecem interrupção.

Implementado nesta etapa:

- triagem única para Gmail, agenda/lembretes e alertas internos recebidos pela central;
- prioridade por segurança, urgência, categoria e preferências explícitas;
- deduplicação persistente e agrupamento silencioso de promoções repetitivas;
- escolha contextual entre avisar, resumir ou guardar durante jogo, fala e conversa;
- consultas naturais e ajustes como “não me avise sobre promoções” e
  “avisos de segurança podem me interromper”;
- memória local sanitizada, sem corpo de email nem credenciais.

Fica fora desta etapa o acesso direto à Central de Ações do Windows. O runtime
já aceita alertas internos de coletores confiáveis futuros sem precisar mudar a
política de triagem.

### 6. Rotinas e cenas naturais

Aprender sequências como jogar, estudar, dormir ou iniciar o trabalho.

Exemplos possíveis:

- modo jogo: reduzir interrupções, ajustar luz e preparar mídia;
- modo estudo: abrir materiais e iniciar uma sessão de foco;
- modo noite: reduzir volume e sugerir ajustes na iluminação;
- retorno da academia: recuperar preferências úteis sem presumir ações.

Uma rotina só poderá ser automatizada depois de várias amostras consistentes e
confirmação explícita do usuário.

### 7. Assistente de foco adaptativo

Observar duração e contexto da atividade para sugerir pausas em momentos
adequados, sem interromper lutas, partidas ou conversas importantes.

Deverá aprender com aceitação, recusa e silêncio, respeitando limites de
frequência para não se tornar repetitivo.

### 8. Diagnóstico e recuperação do computador

Identificar aplicativos travados, consumo anormal de recursos, Ollama ocupado,
internet instável, pouco espaço em disco e integrações desconectadas.

O diagnóstico será separado da correção: a Laylay explica primeiro e só encerra
processos ou muda configurações quando houver autorização suficiente.

### 9. Leitura geral da tela

Expandir a visão além do modo jogo para interpretar erros, instaladores,
configurações, páginas, formulários e comparações entre janelas.

A visão apenas observa e extrai evidências. Pesquisa e execução permanecem com
os especialistas responsáveis.

### 10. Memória de pessoas e relações — implementada

**Status: implementação concluída; aguardando validação real.**

Aprender quem são pessoas mencionadas, como se relacionam com o usuário e quais
assuntos confirmados estão ligados a elas.

Fatos, impressões, hipóteses e brincadeiras deverão ser armazenados com tipos e
níveis de confiança diferentes para evitar lembranças falsas.

Contrato desta etapa:

- aprender somente afirmações pessoais explícitas do usuário, preservando a
  frase de origem e distinguindo relações, fatos, hipóteses e correções;
- consultar pessoas e relações por linguagem natural, inclusive em referências
  curtas de continuidade, sem entregar a pergunta à LLM para ela adivinhar;
- fornecer ao prompt apenas os perfis relevantes ao turno, com proveniência e
  sem promover brincadeiras ou suposições a fatos;
- registrar correções sem manter a versão anterior como verdade ativa e pedir
  esclarecimento quando houver pessoas homônimas;
- exigir confirmação canônica antes de esquecer um perfil e manter histórico
  local de correções e remoções, sem expor esses dados externamente;
- publicar saúde, métricas e capacidades no diagnóstico da mente única;
- integrar a habilidade aos oito pilares: contexto, memória, aprendizado,
  linguagem natural, continuidade, segurança, diagnóstico e noção da própria
  habilidade.

Implementação atual: os perfis ficam em armazenamento local atômico e guardam
relação, fatos, fonte, confiança, correções e histórico de esquecimento. Uma
afirmação explícita alimenta o registro semântico e o aprendizado compartilhado
sem interromper a conversa; perguntas naturais e pronomes de continuidade são
resolvidos antes da LLM. Hipóteses e brincadeiras não viram fatos, homônimos não
são escolhidos no chute e qualquer esquecimento usa a confirmação canônica. O
prompt recebe somente as pessoas relevantes ao turno, enquanto o diagnóstico e
o mapa vivo expõem apenas capacidades e métricas seguras. Ao confirmar um
esquecimento, nome, relações, fatos, evidências, referências semânticas e
aprendizados vinculados são removidos; permanece apenas uma lápide técnica
anônima da operação. A suíte automatizada fechou com 1.511 testes e 41 subtestes
aprovados.

### 11. Modo companhia — implementado

**Status: implementação concluída; em validação real.**

Aumentar a presença durante jogos, estudos e tarefas com comentários relevantes,
motivação contextual, música compatível e silêncio nos momentos de concentração.

O controle de frequência e o aprendizado por feedback serão essenciais para que
a presença não se torne irritante.

Implementação atual: um diretor único escolhe autonomamente entre presença
silenciosa, adaptativa e mais próxima. A decisão considera concentração,
modo jogo, segurança do momento, evidências visuais, fala em andamento,
orçamento anti-repetição e feedback de aceitação, recusa, correção ou silêncio.
Sugestões musicais usam somente playlists reais e nunca iniciam reprodução sem
uma ordem. A etapa permanece em validação real até passar por uso contínuo.

### 12. Exportação e recuperação da Laylay

Criar backup portátil de memória, configurações e preferências, removendo
credenciais e dados sensíveis antes da exportação.

A restauração deverá validar versões, integridade e compatibilidade antes de
alterar a instalação existente.

### 13. Orquestração cooperativa de habilidades — nome provisório

Permitir que uma habilidade produza uma percepção estruturada para outra
habilidade avaliar, sem criar atalhos rígidos entre módulos. Por exemplo, a
Área de transferência identifica localmente um erro copiado, o Modo companhia
decide se é um bom momento para comentar e a Pesquisa contextual só é acionada
depois de autorização suficiente.

Essa camada deverá definir um contrato comum de eventos, relevância, confiança,
privacidade, validade e autorização. Nenhuma habilidade poderá interpretar a
percepção de outra como ordem automática. O nome definitivo e o alcance serão
discutidos antes da implementação geral.

Primeiro experimento entregue: o observador passivo da Área de transferência
publica somente metadados sanitizados para o Modo companhia, com estabilidade,
deduplicação, bloqueio de segredos e execução automática desativada.

**Status atual: primeira composição e contrato cooperativo v2 validados em uso
real; integração canônica da etapa 4 implementada e aguardando validação real.**
O quadro comum permanece em modo sombra para relações ainda não autorizadas.
O fluxo explicitamente pedido de Área de transferência para Arquivos já cria um
plano único, transporta o texto por referência efêmera em RAM, grava sem
sobrescrita implícita, relê conteúdo e hash e só então confirma. Arquivo já
existente usa a pendência canônica; recusa, falha e confirmação alimentam o
aprendizado compartilhado sem persistir o texto copiado.

O contrato v2 acrescentou identificadores únicos de etapa, dependências válidas
somente para etapas anteriores, orçamento individual e total, cancelamento
cooperativo, idempotência obrigatória, evidência esperada e política explícita
de falha parcial. O executor não produz fala: ele apenas coordena adaptadores
canônicos e registra evidências, preservando uma única resposta final. Uma falha
opcional pode permitir etapas independentes quando o plano declarar essa
política; uma etapa dependente nunca executa sem sua predecessora confirmada.
Orçamento vencido impede o início de novas etapas sem abandonar silenciosamente
uma ação já iniciada. O diagnóstico passou a expor falhas parciais, dependências
bloqueadas, orçamentos excedidos e pedidos de cancelamento, sem publicar dados
privados.

A etapa 4 conectou o executor genérico ao porteiro central, à continuidade
oficial, ao aprendizado compartilhado e à observabilidade. O porteiro recebe a
intenção real de cada etapa antes do adaptador; risco alto, destrutivo ou
irreversível continua exigindo confirmação explícita. O ciclo cooperativo entra
no histórico oficial como contexto inativo, portanto não rouba o domínio ativo
da habilidade que realmente agiu — após criar um arquivo, referências naturais
como `apaga ele` continuam pertencendo a Arquivos. Cada plano é atribuído ao
aprendizado e à auditoria uma única vez, mesmo quando uma repetição consulta um
resultado já finalizado. A suíte automatizada desta evolução terminou com 1.466
testes e 41 subtestes aprovados.

Segunda composição validada em uso real: a organização automática da área de trabalho
agora atravessa o mesmo contrato cooperativo. A percepção enumera somente
janelas locais visíveis sem movê-las; a priorização combina foco, áudio ativo,
uso recente, frequência e tempo de processo; apenas a etapa final autorizada
envia os dois alvos escolhidos ao executor canônico de janelas. O sucesso só é
confirmado depois da releitura da geometria final. Títulos e objetos brutos de
janela não são publicados no quadro cooperativo, e negação, hipótese ou pergunta
de capacidade não iniciam o plano. O teste real confirmou a escolha do editor em
foco para a esquerda e do navegador reproduzindo áudio para a direita.

Terceira composição implementada: pedidos naturais de avaliação de item no modo
jogo agora criam um único plano assíncrono sem duplicar o fluxo visual existente.
O detector oficial identifica o pedido; a visão captura e lê somente o quadro
atual; a pesquisa de jogos tenta enriquecer a identificação; memória de jogo,
build e inventário participam do parecer final. A ausência de fonte externa é
registrada como limite, não como fato inventado. Imagem, nome e atributos brutos
do item não circulam no quadro cooperativo: ele recebe apenas estado, confiança,
quantidade de fontes e evidências sanitizadas. A visão continua sendo a única
dona da fala e o plano só termina depois que o parecer está pronto. Perguntas
visuais que não sejam avaliação de item permanecem no fluxo anterior. O mapa vivo
de capacidades também passou a explicar naturalmente como essa análise funciona
e quais são seus limites. A suíte desta evolução terminou com 1.491 testes e 41
subtestes aprovados; falta somente a validação em jogo real.

#### Plano aprovado para evolução

A cooperação será mediada pela mente única. Uma habilidade não chamará outra
diretamente e uma percepção nunca será tratada como ordem. Cada participante
publicará uma contribuição estruturada; o coordenador reunirá essas
contribuições em um único plano, passará pelo porteiro canônico, executará as
etapas autorizadas e produzirá somente uma resposta final.

O contrato cooperativo deverá representar:

- identificador e chave de deduplicação;
- origem, tipo e resumo sanitizado do evento;
- confiança, relevância, sensibilidade e prazo de validade;
- referências temporárias para dados que não devem circular nem aparecer em logs;
- habilidades capazes de contribuir e evidências esperadas de cada uma;
- dependências entre etapas, autorização necessária e política de falha parcial;
- estados observado, enriquecido, proposto, autorizado, executando, confirmado,
  falhou, cancelado e expirado;
- resultado final publicado na continuidade, no diagnóstico e no aprendizado
  compartilhados.

Regras de segurança e comportamento:

- observações e enriquecimentos locais de somente leitura podem ocorrer sem fala;
- ações reversíveis autônomas dependem de política já concedida e confiança de
  pelo menos 90%; ações destrutivas sempre exigem confirmação;
- a LLM pode interpretar o objetivo, sugerir relações e escrever a fala, mas não
  autoriza nem confirma execução;
- somente uma pendência canônica e uma fala final podem pertencer ao plano;
- toda etapa precisa ser idempotente, possuir orçamento de tempo e declarar a
  evidência que confirma seu resultado;
- aceitação, recusa, correção, repetição e silêncio qualificado após dez minutos
  serão atribuídos ao plano completo, sem criar aprendizados isolados conflitantes;
- conteúdo sensível não será persistido nem exposto em logs ou diagnósticos.

Ordem de implementação aprovada:

1. criar o contrato comum e o quadro cooperativo em modo sombra;
2. ativar o primeiro fluxo real de baixo risco entre Área de transferência e Arquivos;
3. acrescentar planos com dependências, orçamento, cancelamento e falha parcial;
4. conectar autorização, continuidade, diagnóstico e aprendizado canônicos;
5. aplicar a mesma fundação à análise de itens no jogo, organização da área de
   trabalho, notificações e consciência de projetos somente após validação real.

Primeiro fluxo de validação:

```text
pode colocar o que eu copiei em um arquivo de texto chamado tete
```

Resultado esperado: a Área de transferência fornece uma referência temporária
ao conteúdo sem recitá-lo; Arquivos cria `tete.txt`; o executor relê existência,
tamanho e impressão digital do conteúdo; a Laylay fala uma única vez somente
depois da confirmação. Se o arquivo já existir, se o conteúdo parecer sensível
ou se a referência expirar ou mudar, o plano não sobrescreve nada e solicita a
decisão necessária pelo canal de pendência oficial. `tenta de novo` reutiliza o
plano seguro e sua referência enquanto ainda forem válidos.

## Acompanhamento

| Etapa | Habilidade | Estado |
|---:|---|---|
| 1 | Área de transferência inteligente | Concluída |
| 2 | Caixa de entrada pessoal | Concluída |
| 3 | Pesquisa semântica nos arquivos | Implementada — aguardando validação real |
| 4 | Consciência de projetos | Planejada |
| 5 | Central inteligente de notificações | Implementada — aguardando validação real |
| 6 | Rotinas e cenas naturais | Planejada |
| 7 | Assistente de foco adaptativo | Planejada |
| 8 | Diagnóstico e recuperação do computador | Planejada |
| 9 | Leitura geral da tela | Planejada |
| 10 | Memória de pessoas e relações | Implementada — aguardando validação real |
| 11 | Modo companhia | Implementado — em validação real |
| 12 | Exportação e recuperação da Laylay | Planejada |
| 13 | Orquestração cooperativa de habilidades (nome provisório) | Contrato v2, Arquivos e janelas validados; análise cooperativa de itens implementada — aguardando validação real |

## Critério para concluir uma etapa

Uma habilidade só será marcada como concluída quando:

1. estiver integrada à mente única;
2. não depender de respostas fixas para conversar;
3. respeitar modalidade, autorização e confirmação;
4. tiver testes automatizados do caminho feliz e das falhas;
5. não causar regressão na suíte completa;
6. passar por uma conversa contínua de teste feita pelo usuário;
7. registrar sua ação e seu resultado na continuidade oficial;
8. participar do aprendizado seletivo e do contexto compartilhado sem criar
   memória ou continuidade paralela.
9. estar registrada no mapa vivo de capacidades, chegar ao contexto seletivo
   da LLM e responder corretamente a perguntas naturais sobre o que faz, seus
   limites e sua disponibilidade atual.

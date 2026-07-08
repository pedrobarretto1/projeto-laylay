# Plano de Refatoração da Laylay

## Objetivo

Organizar o código da Laylay sem perder personalidade, capacidades atuais,
memória, contexto, autonomia e velocidade prática.

A refatoração deve preservar a regra principal do projeto:

Todas as capacidades da Laylay devem funcionar como partes de uma mesma mente.
Memória, percepção, emoções, contexto, rotinas, comandos, navegação e futuras
arquiteturas devem compartilhar informações entre si sempre que fizer sentido,
de forma modular, eficiente e sem fragmentar o comportamento da personagem.

---

## Regras obrigatórias

- Nunca remover funcionalidades existentes.
- Nunca alterar comportamentos que não estejam ligados ao passo atual.
- Preservar compatibilidade com o restante do projeto.
- Preferir extrações modulares em vez de reescritas agressivas.
- Evitar duplicação de código.
- Alterar o mínimo necessário por etapa.
- Validar compilação a cada bloco extraído.
- Manter a Laylay com personalidade amiga, divertida e contextual.
- Evitar transformar a mente em partes isoladas que "pensam separadas".
- Sempre que possível, fazer a decisão nascer do contexto e da interpretação da IA.

---

## Estado atual

O projeto já começou a ser fragmentado em módulos dentro de `mente_laylay`,
mas o arquivo principal `laylay.py` ainda concentra muitas responsabilidades.

Hoje existem três estados ao mesmo tempo:

1. Partes já modularizadas e reutilizáveis.
2. Partes híbridas, onde `laylay.py` ainda coordena muita lógica.
3. Partes antigas, com regras locais, atalhos e blocos grandes demais.

Isso gera alguns riscos:

- duplicação de fluxo;
- roteadores competindo entre si;
- respostas produzidas antes da validação real da ação;
- comportamento correto em um ponto e inconsistente em outro;
- dificuldade para manter contexto único;
- risco de regressão quando outra IA altera blocos grandes sem entender o todo.

---

## O que já foi feito

### 1. Estrutura modular inicial

Já existem módulos separados em `mente_laylay`, incluindo áreas como:

- autonomia;
- memória mental;
- emoções;
- personalidade;
- arquivos;
- navegação;
- processamento de resposta da IA.

### 2. Estado mental integrado

A Laylay já possui um estado mental compartilhado com memória curta de conversa,
incluindo sinais como:

- última entrada;
- últimas entradas;
- última intenção;
- último alvo;
- última habilidade;
- última resposta;
- resultado da última ação real;
- possibilidade de repetir uma ação anterior.

### 3. Anti-alucinação de ações

Foi iniciado um fluxo mais confiável para ações práticas:

Interpretar  
↓  
Executar  
↓  
Validar estado/resultado  
↓  
Responder com base no que aconteceu

Isso já começou a ser aplicado em fluxos como:

- abrir app;
- fechar app;
- abrir URL;
- fechar aba;
- volume;
- mídia;
- notificações;
- email.

### 4. Resultado real da ação como parte da mente

Foi extraído para módulo compartilhado o contrato básico do estado de execução:

- estado mental inicial;
- registro de resultado da última ação;
- definição de ação reexecutável;
- repetição curta de comando com base na última ação real.

Esse contrato agora vive em:

`mente_laylay/memoria_mental/contexto_compartilhado.py`

Com isso, o `laylay.py` ficou menos dono dessa lógica e mais integrador da mente.

### 5. Melhorias conversacionais já iniciadas

Também já foram introduzidas melhorias como:

- cancelamento de ação por fala natural;
- interpretação informal de alguns comandos;
- respostas baseadas em status real da execução;
- bloqueios de autonomia musical em contexto inadequado;
- reforço do conceito de uma mente única.

---

## Problema central restante

Apesar dos avanços, o centro do sistema ainda está pesado em `laylay.py`.

Hoje esse arquivo ainda mistura:

- estado global;
- interpretação;
- contexto;
- roteamento;
- fallback;
- execução prática;
- fala;
- memória curta;
- integração com módulos;
- comportamento legado.

Isso dificulta:

- corrigir bugs com segurança;
- entender qual fluxo venceu;
- confiar no que outra IA alterou;
- evoluir sem quebrar comportamento;
- aplicar IA-first de forma limpa.

---

## Estratégia de refatoração

A refatoração deve ser feita por camadas pequenas, sempre com compatibilidade.

Em vez de "reescrever a Laylay", o objetivo é:

1. identificar um bloco estável;
2. extrair para módulo próprio;
3. manter uma casca de compatibilidade no `laylay.py`;
4. validar compilação;
5. validar comportamento;
6. só então avançar para o próximo bloco.

---

## Arquitetura alvo

Estrutura mental desejada em português:

```text
mente_laylay/
│
├── autonomia/
├── memoria_mental/
├── percepcao/
├── emocoes/
├── cognicao/
├── personalidade/
├── arquivos/
└── integracao/
```

Observação importante:

Essa separação é apenas organizacional.
O comportamento deve continuar sendo de um único cérebro.

Isso significa que os módulos devem compartilhar:

- estado mental;
- contexto recente;
- memória curta;
- resultado real das ações;
- emoção atual;
- rotina;
- sinais do sistema;
- histórico relevante da conversa.

---

## Separação conceitual obrigatória

Mesmo dentro de uma mente única, nem tudo deve morar no mesmo objeto.

### Estado mental

Representa o estado interno e conversacional da Laylay.

Exemplos:

- humor;
- emoção;
- contexto recente;
- assunto atual;
- última fala;
- memória curta;
- rotina;
- percepção viva.

### Resultado de ação

Representa o resultado técnico e prático de uma execução.

Exemplos:

- intenção executada;
- alvo;
- status;
- sucesso ou falha;
- ação realmente realizada;
- erro técnico;
- possibilidade de reexecução.

### Regra

O estado mental pode consultar o resultado da ação.

Mas o resultado da ação não deve virar contexto dominante automaticamente.

Isso evita contaminações como:

- um volume ajustado interferindo em conversa de email;
- uma playlist antiga tentando voltar sem pedido real;
- uma ação já concluída vencendo a fala atual sem continuidade forte.

---

## Contrato alvo para resultado de ação

O contrato de execução deve evoluir para algo mais forte e mais explícito.

Formato desejado:

```json
{
  "ok": true,
  "intent": "APP_OPEN",
  "status": "app_focado",
  "alvo": "steam",
  "acao_realizada": "focar_janela",
  "mensagem_base": "Steam trazida para frente.",
  "erro": null,
  "reexecutavel": true,
  "deve_responder": true,
  "dados": {}
}
```

### Campo crítico

`deve_responder`

Esse campo é importante porque nem todo fluxo que registra estado deve gerar
fala final.

Ele ajuda a evitar:

- resposta duplicada;
- resposta fora de hora;
- fluxo técnico falando quando só deveria atualizar contexto.

---

## Fases da refatoração

## Fase 0 — Mapeamento de fluxos atuais

### Objetivo

Mapear quem realmente manda hoje antes de extrair qualquer fluxo grande.

### Itens

- listar onde nascem as intenções;
- listar quais roteadores existem;
- listar onde a resposta final é gerada;
- listar onde o estado mental é alterado;
- listar quais funções ainda mexem diretamente em contexto;
- listar quais blocos ainda executam ações sem retorno padronizado;
- listar quais blocos ainda usam contexto antigo para decidir.

### Observação

O maior risco agora não é mover código.

O maior risco é não saber qual fluxo ainda está mandando de verdade.

### Saída esperada

Um inventário curto e objetivo dos pontos que:

- interpretam intenção;
- executam ação;
- registram estado;
- geram resposta;
- usam contexto antigo.

### Status

Concluído.

### Registro

O inventário desta fase foi registrado em:

`inventario_fluxos_atuais.md`

Principais conclusões:

- o `laylay.py` ainda funciona como orquestrador híbrido;
- o pré-fluxo real de conversa/chat já está mais concentrado em
  `mente_laylay/autonomia/fluxo_resposta_ia.py`;
- o coordenador de intenção principal já está em
  `mente_laylay/autonomia/coordenador_intencao.py`;
- o executor prático central continua em
  `mente_laylay/autonomia/roteador_intencao.py`;
- a montagem do prompt contextual final já está em
  `mente_laylay/autonomia/contexto_resposta_ia.py`;
- o maior hotspot restante de conversa/contexto no `laylay.py` é
  `_contexto_conversa_natural()`.

---

## Fase 1 — Consolidar contratos compartilhados

### Objetivo

Retirar do `laylay.py` as estruturas-base que várias habilidades usam.

### Itens

- consolidar estado mental inicial;
- consolidar estado de última ação real;
- consolidar repetição de ação anterior;
- consolidar helpers de contexto compartilhado;
- padronizar o formato mínimo de `intent`, `params`, `status`, `origem`.
- iniciar migração para contrato forte de resultado com `ok`, `erro`,
  `acao_realizada`, `deve_responder` e `dados`.

### Status

Em andamento.

### Observação

Uma parte dessa fase já foi feita com a extração do contrato de resultado para
`contexto_compartilhado.py`.

---

## Fase 2 — Separar integração de contexto

### Objetivo

Diminuir o peso do `laylay.py` na montagem do retrato mental usado pelos prompts.

### Itens

- extrair montagem de resumo da mente integrada;
- centralizar sinais de contexto vivo;
- centralizar cruzamento entre memória, emoção, rotina e ação recente;
- reduzir dependência de estado espalhado.

### Resultado esperado

O prompt da Laylay deixa de ser montado em vários pedaços concorrentes e passa
a nascer de um integrador de contexto mais claro.

### Regra

Esse integrador não deve executar ações.

Ele apenas organiza contexto.

### Progresso atual

Ja foram extraidos para `mente_laylay/integracao/contexto_conversa.py`:

- montagem do contexto de conversa natural;
- montagem do contexto de fala curta;
- montagem do contexto inicial do pre-fluxo de chat;
- montagem do contexto do fallback conversacional.

Com isso, o `laylay.py` segue como orquestrador, mas deixa de montar na mao
mais um conjunto grande de dependencias de conversa.

---

## Fase 2.1 — Validador de continuidade contextual

### Objetivo

Criar um portão anti-contexto velho para decidir quando a fala atual continua
algo anterior e quando ela precisa cortar a continuidade.

### Itens

- classificar a fala atual como novo comando;
- classificar como continuação;
- classificar como cancelamento;
- classificar como correção;
- classificar como repetição;
- classificar como conversa;
- impedir que contexto antigo vença sem evidência forte.

### Exemplos esperados

- `deixa pra lá` deve cancelar;
- `quero mais não` deve cancelar ou negar continuidade;
- `tenta de novo` pode reutilizar a última ação real;
- `essa também` só deve continuar quando houver vínculo contextual forte.

---

## Fase 3 — Limpar roteamento de intenção

### Objetivo

Fazer a intenção nascer de forma mais previsível e menos duplicada.

### Itens

- revisar pré-fluxos duplicados;
- reduzir concorrência entre roteador determinístico, IA-first e atalhos locais;
- manter palavra-chave apenas como rede de segurança;
- centralizar cancelamento, repetição e continuidade contextual.

### Resultado esperado

Menos casos em que uma parte entende playlist, outra entende conversa e uma
terceira dispara ação antiga por engano.

---

## Fase 4 — Separar execução prática do sistema

### Objetivo

Deixar os comandos práticos mais confiáveis e mais fáceis de validar.

### Itens

- separar abrir, fechar, focar, maximizar, navegar e controlar mídia;
- exigir retorno padronizado de sucesso, falha, foco, já aberto e não encontrado;
- responder com base no resultado real;
- reduzir respostas que afirmam execução sem confirmação.

### Resultado esperado

A Laylay passa a dizer coisas como:

- "A Steam já estava aberta."
- "Trouxe a Steam para frente."
- "Não consegui abrir a Steam."

em vez de repetir sempre "Abrindo Steam.".

---

## Fase 5 — Criar gerador de fala contextual

### Objetivo

Concentrar a resposta final da Laylay em um módulo mais claro e mais fiel à
personalidade dela.

### Estrutura sugerida

- `mente_laylay/personalidade/gerador_fala.py`

ou

- `mente_laylay/cognicao/resposta_contextual.py`

### Responsabilidade

- receber resultado técnico;
- receber tom da intenção;
- receber estado emocional;
- receber contexto recente;
- gerar resposta final no estilo Laylay.

### Regra

O executor não deve decidir frase completa engraçada em muitos lugares
diferentes.

Ele deve, preferencialmente, informar:

- status;
- alvo;
- ação realizada;
- falha ou sucesso;
- contexto mínimo.

E a personalidade transforma isso em fala final.

---

## Fase 6 — Separar conversa curta e fala contextual

### Objetivo

Organizar melhor a parte que decide como ela fala.

### Itens

- mover conversa curta para um fluxo mais centralizado;
- diminuir trechos literais grandes no `laylay.py`;
- preservar a personalidade da Laylay;
- ligar a fala ao estado real da ação;
- ligar a fala ao contexto emocional e ao histórico recente.

### Resultado esperado

Ela continua com o jeitinho dela, mas com menos aleatoriedade ruim e menos
respostas estranhas fora de personagem.

---

## Fase 7 — Unificar música, playlist e recomendação

### Objetivo

Consolidar a mente musical sem deixar autonomia invasiva.

### Itens

- separar claramente tocar playlist, tocar música e recomendar música;
- usar contexto musical apenas quando fizer sentido;
- manter bloqueio de autonomia quando o usuário não pediu música;
- preparar melhor a futura playlist própria da Laylay;
- manter memória musical útil sem vício em playlist.

### Resultado esperado

A música deixa de vazar para conversas neutras e passa a aparecer só quando o
contexto realmente aponta para isso.

---

## Fase 8 — Finalizar casca do `laylay.py`

### Objetivo

Transformar `laylay.py` em orquestrador principal, não em depósito de lógica.

### Itens

- manter inicialização;
- manter integração entre módulos;
- manter registradores globais estritamente necessários;
- reduzir helpers locais que já possuem módulo dedicado;
- deixar o arquivo principal mais legível e auditável.

### Resultado esperado

O arquivo principal continua sendo o cérebro centralizador, mas não carrega mais
sozinho todos os pensamentos da Laylay.

---

## Critérios de validação por etapa

Cada etapa só deve ser considerada concluída quando passar nestes pontos:

### 1. Compatibilidade

Nada importante pode deixar de funcionar.

### 2. Compilação

Os arquivos principais devem compilar sem erro.

### 3. Continuidade mental

Memória, contexto, emoção, intenção e execução devem continuar conversando entre si.

### 4. Resposta coerente

A Laylay deve continuar soando como Laylay.

### 5. Anti-regressão prática

Devem continuar funcionado, no mínimo:

- abrir app;
- fechar app;
- abrir site;
- tocar playlist;
- controle de mídia;
- volume;
- conversa curta;
- cancelamento;
- repetição de ação;
- emails;
- notificações.

### 6. Testes manuais obrigatórios

Após cada fase, deve existir uma lista curta de testes recomendados para o
Pedro rodar manualmente.

Compilar não é suficiente para validar comportamento.

---

## Riscos que exigem cuidado

### 1. Duplicação silenciosa

Quando o mesmo comportamento existe no módulo novo e ainda sobra no `laylay.py`.

### 2. Fluxos competindo

Quando um roteador entende uma coisa e outro executa outra.

### 3. Estado desatualizado

Quando a mente compartilhada guarda um status antigo e isso contamina o próximo comando.

### 4. Perda de personalidade

Quando a limpeza técnica deixa a Laylay correta, mas genérica.

### 5. Falsa modularização

Quando os arquivos ficam separados, mas sem contexto comum, virando cérebros fragmentados.

---

## Ordem prática recomendada

1. Mapear os fluxos atuais.
2. Consolidar contratos compartilhados.
3. Extrair montagem de contexto mental.
4. Criar o validador de continuidade contextual.
5. Limpar roteamento de intenção.
6. Padronizar retorno dos comandos práticos.
7. Criar gerador de fala contextual.
8. Separar conversa curta e fala contextual.
9. Consolidar música e playlist.
10. Reduzir o `laylay.py` ao papel de orquestrador.

---

## Próximo passo recomendado

Depois do mapeamento da Fase 0, o próximo passo mais seguro continua não sendo
extrair blocos aleatórios.

Antes disso, o ideal é mapear os pontos que ainda montam, alteram ou usam o
retrato mental e o contexto de decisão.

### Próximo passo 1 — Mapear

Identificar:

- onde a fala do usuário entra;
- onde o contexto da tela entra;
- onde a memória curta entra;
- onde a emoção entra;
- onde a última ação real entra;
- onde o prompt final é montado;
- onde a resposta final é decidida.

### Próximo passo 2 — Extrair

Só depois disso:

criar um módulo integrador responsável por montar um retrato mental único,
curto e limpo para a IA e para a conversa curta.

Esse módulo:

- não deve executar ações;
- deve apenas organizar contexto;
- deve reduzir concorrência entre retratos mentais antigos e novos.

### Decisão atualizada após a Fase 0

O próximo passo concreto recomendado agora é:

extrair o integrador do contexto conversacional hoje concentrado em
`_contexto_conversa_natural()` e aproximá-lo do integrador de retrato mental já
existente, mantendo o `laylay.py` apenas como casca de compatibilidade.

Isso deve reduzir:

- decisões repetidas;
- vazamento de contexto antigo;
- conflitos entre conversa, comando e autonomia;
- bugs em que uma intenção antiga volta do nada.

---

## Testes manuais base por fase

Depois de cada fase, a validação manual deve usar pelo menos alguns destes
exemplos:

1. `abre a steam`
2. `abre a steam de novo`
3. `fecha a steam`
4. `coloca o volume em 30`
5. `deixa pra lá`
6. `quero mais não`
7. `manda a shein calar a boca`
8. `tenta de novo`
9. `toca rock`
10. `adiciona essa música na playlist brisa da madrugada`
11. `abre o youtube`
12. `fecha essa aba`

---

## Registro desta etapa

Nesta etapa foi concluído:

- extração do contrato básico de estado mental compartilhado;
- extração do registro da última ação real;
- extração da regra de repetição curta com base na última ação;
- adaptação do `laylay.py` para consumir esse módulo;
- validação de compilação após a mudança.

Essa etapa serve como base para continuar a refatoração com mais segurança.

---

## Registro adicional de unificação

Também foram concluídos novos passos de unificação para reduzir estados soltos
no `laylay.py`:

- criação de `mente_laylay/memoria_mental/estado_musical.py`;
- centralização de `ultima_playlist`, bloqueio temporário de playlist e estado
  vivo da playlist em execução;
- criação de `mente_laylay/memoria_mental/estado_percepcao.py`;
- centralização de contexto web, aba ativa, logs recentes do navegador,
  último site aberto e contexto do sistema;
- criação de `mente_laylay/percepcao/janelas_sistema.py`;
- extração da lógica de foco, maximização, organização de janelas, listagem de
  programas abertos e resolução entre app/aba;
- manutenção dos nomes antigos no `laylay.py` como wrappers de compatibilidade;
- validação de compilação após as extrações.

Depois disso, também foi iniciado o integrador central do retrato mental:

- criacao de `mente_laylay/integracao/contexto_conversa.py`;
- extracao da montagem de contexto de conversa natural;
- extracao da montagem de contexto de fala curta;
- extracao da montagem do contexto inicial do fluxo de chat;
- extracao da montagem do contexto do fallback conversacional;
- extracao de `processar_comandos_imediatos(...)` para
  `mente_laylay/autonomia/comandos_imediatos.py`;
- manutencao de wrappers de compatibilidade no `laylay.py`;
- validacao de compilacao apos cada extracao.

- ampliação de `mente_laylay/memoria_mental/contexto_integrado.py`;
- extração da montagem do contexto perceptivo vivo;
- extração do resumo de contexto perceptivo para prompt;
- extração do resumo de mente integrada para prompt;
- preservação dos wrappers antigos em `laylay.py`;
- uso de um retrato mental já preparado no fluxo de resposta da IA, reduzindo
  remontagens paralelas de contexto;
- validação de compilação após a mudança.

Em seguida foi iniciado o coordenador único de intenção:

- criação de `mente_laylay/autonomia/coordenador_intencao.py`;
- centralização da ordem de decisão: cancelamento, repetição, IA-first,
  determinístico, execução e registro;
- centralização da lista de intents executáveis;
- manutenção de `processar_comando_deterministico` no `laylay.py` como wrapper
  de compatibilidade;
- validação de compilação após a mudança.

Essas mudanças aproximam a Laylay da regra de mente única: os módulos ficam
separados por responsabilidade, mas continuam compartilhando o mesmo retrato
mental em vez de criarem decisões paralelas.

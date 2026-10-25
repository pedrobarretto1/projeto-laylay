# Respostas e prazos na conversa contínua — 24/10/2026

## Escopo e base

Pedido de Pedro: corrigir as respostas inadequadas e os timeouts observados no
teste de coerência longa. Comandos exclusivamente simulados e voz desligada.
Não se pretende encerrar a compreensão geral, a explicação livre ou C5/P01.

Base: branch `main`, HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`.
Worktree previamente suja preservada. O snapshot de 527 fontes anterior a esta
investigação está em `resultados_testes/respostas_prazos_20261024/fontes_antes`;
`baseline.json` registra hashes e status. O diff contra HEAD inclui trabalho
anterior e não deve ser usado como se fosse o candidato inteiro desta etapa.

Modelo e backend mantidos: `qwen3:4b-instruct`, Ollama local. Prazos, limites de
janela e voz não foram alterados. Nenhum commit, reinício pessoal ou novo
shutdown foi criado nesta etapa.

## Fronteiras demonstradas, contratos e responsáveis

Os IDs históricos são preservados. As linhas abaixo são mecanismos distintos;
não significam uma nova raiz para cada frase ou uma causa única de C5/C7/F1/F3.

| Vínculo | Primeira divergência e contrato corrigido | Owner responsável |
| --- | --- | --- |
| F3 | Decisão canônica sem operação era descartada na admissão da interpretação auxiliar. Misto conversa/pergunta também escapava da proteção. Repassar decisão somente se vigente; nenhum segmento autorizado significa dispensar interpretação operacional redundante. | `interpretacao_intencao`, `pre_fluxo_contextual` |
| F1/C7 | `para` de finalidade/referência virava imperativo de parada e contaminava relato composto. Separar adjunto e matriz pelo classificador canônico, preservando comandos independentes e paradas reais. | `modalidade_turno` |
| C7 | Pergunta nova sobre plano era consumida como feedback do app recente pela palavra `ficou`. Feedback precisa de ato atual compatível e vínculo com o alvo, além de TTL. | `continuidade_conversa` |
| F1/C7 | Autoria adotava posse, plano, relato e grupo explícito do usuário como primeira pessoa da Laylay. Papéis vêm do canal, com identidade de turno; divergência exige reparo, não substituição automática de pronomes. | `referencias_linguagem`, `contrato_fala`, `validacao_contrato_fala`, `qualidade_comunicacao` |
| C7/C5 | Categoria perguntada era registrada como nome: `banda eu falei que gosto`. Consulta e relativa não nomeiam entidade; designação explícita e nome entre aspas permanecem válidos. | `retrato_turno` |
| C5/C7 | Relato pessoal atribuído (`você disse que gostava...`) era avaliado como afirmação externa da banda. Conferir transformação fechada contra fonte user, com mesmo predicado e valor; rejeitar acréscimos, coordenações e fontes revisadas. | `fundamentacao_factual`, `plano_turno` |
| C7/C5 | A composição do plano não projetava o histórico literal original; registro semântico normalizado não substitui a fonte. Projetar mensagens canônicas no planejamento efêmero, sem outro armazenamento persistente. | `orquestrador_turno_runtime` |
| C7 | Pergunta retrospectiva ampla não selecionava fontes suficientes. Reconhecer escopo de recapitulação e admitir intervalo integral sob o orçamento existente. Metadados compactos têm aliases explícitos, sem cortar texto. | `referencias_linguagem`, `seletor_contexto`, `preparacao_llm` |
| C7 | Uma resposta inteira anterior podia passar como resposta a um novo relato. Exigir reparo quando a fala literal se repete sem pedido de repetição; perguntas diferentes com mesma resposta legítima continuam permitidas. | `qualidade_comunicacao` |
| C7/C5 | Reparo de perspectiva/repetição recebia rascunho rejeitado e pouca recência; reparo de formato perdia completamente as fontes disponíveis ao principal. Reutilizar seleção/serialização canônicas nas reescritas vinculadas ao turno, com pacote completo ou recusa. | `qualidade_comunicacao`, `processamento_resposta_ia`, `preparacao_llm` |

O suporte a grupos coordenados é deliberadamente limitado ao mesmo parceiro e
predicado explícitos fora de citações. Não resolve todo pronome `nós`. A revisão
de preferência cobre uma gramática fechada, não equivalência semântica geral.

Quando uma revisão factual remove toda a fala sobre um relato atual, não é
correto dizer que o usuário não forneceu informação. O plano pode realizar uma
citação literal atribuída ao usuário, vinculada ao turno, apenas em conversa
informativa sem autorização/comandos. Essa realização não comprova o relato e
não gera receipt. É uma contingência conservadora, com perda de naturalidade
explicitamente reconhecida.

## REDs, falsificações e controles

- F3: os turnos históricos 18/26 já eram não operacionais antes da chamada
  auxiliar. Controles seriais, sem falha nem concorrência, reproduziram o gasto
  de 11,198 s da interpretação, deixando 8,802 s do orçamento de 20 s para a
  principal. Falsificadas falta de fonte no transporte e falha/circuito como
  condições necessárias desse desperdício. Composição controlada final admite
  uma principal com orçamento inteiro; pedidos realmente autorizados preservam
  interpretação. Ver `timeout/DIAGNOSTICO_ADMISSAO.md` e XMLs associados.
- Modalidade: relatos com `para` falharam antes do candidato; paradas reais são
  controles. Uma expansão inicial confundiu nomes terminados em `or` com
  infinitivos: três REDs adicionais corrigidos antes da entrega. Motor,
  ventilador e computador preservam comandos de parada. Não foi removida a
  proteção a comandos. Ver `relato_composto/RELATORIO.md`.
- Continuidade: contraparte congelada reproduz consumo indevido; TTL e receipt
  recente sozinhos não explicam vínculo semântico. Pergunta nova volta ao autor,
  feedback elíptico legítimo permanece. Ver `retoma_plano/DIAGNOSTICO.md`.
- Perspectiva: inicialmente sete REDs; depois controles de negação/citação,
  contexto integral no reparo e iterador. Dois REDs de grupo coordenado foram
  acrescentados após ocorrência com Qwen. Papéis propostos pela IA e fontes de
  outro turno não podem substituir o objeto tipado produzido pelo host.
- Preferência: geração correta de Nirvana já existia antes da entrega final;
  falha posterior no host falsifica `Qwen não lembrou` como explicação completa.
  Teste de composição descobriu que a fonte literal não chegava ao plano.
  Revisão encontrou coordenação não suportada e fontes corrigidas; REDs próprios
  confirmados e corrigidos, preservando a rejeição de fatos externos extras.
- Recapitulação: o histórico continuava arquivado, mas seleção lexical não
  incluía todo o escopo solicitado. O pacote integral foi compactado somente em
  nomes de chaves (`i`, `role`, `t`, definidos no envelope). O fixture que antes
  cabia apenas no modo normal precisou de 14 para 18 relatos porque 14 passaram
  a caber legitimamente no rápido; a exigência de intervalo integral é a mesma.
- Reparo de formato: saída malformada real no turno 18 levou a uma segunda
  chamada sem fontes e à alegação falsa de ausência de contexto. RED local
  confirmou a primeira perda. A factory, com somente a folha HTTP controlada,
  confirmou que a fonte original chega ao reparo e uma única resposta correta é
  publicada. A primeira asserção do teste instalado supunha JSON no fim do
  system; a negociação acrescenta contrato depois dele. Corrigida a leitura do
  envelope pelo primeiro valor JSON, preservando integralmente a exigência de
  fonte/papel. Pacote fechado, turno divergente e intervalo excessivo são
  controles negativos; não foram ampliados para caber.

## Evidência da composição e das coletas

`executar.py` reutiliza a factory instalada. Isola persistência, restaura as
mesmas instâncias cognitivas da factory e permite somente HTTP ao modelo local.
Disco externo, processo, serial e rede pública são bloqueados; fala desligada.
Os dois pedidos operacionais do roteiro usam o adaptador real para publicar
receipts negativos de simulação, nunca efeitos confirmados. O gabarito do teste
é externo e não entra no prompt. Os 527 hashes são comparados antes/depois.

As coletas intermediárias foram preservadas, pois cada uma expôs outra
fronteira; não foram substituídas por uma fala escolhida:

| Coleta de 30 turnos | Evidência e fronteira ainda aberta naquela versão |
| --- | --- |
| `conversa_integrada` | 31 HTTP 200; perspectiva no reparo e fontes do resumo ainda falhavam. |
| `conversa_final` | 32 HTTP 200; perspectiva e resumo melhores, mas fonte literal ainda ausente do plano da banda. |
| `conversa_validada` | 30 HTTP 200; banda e resumo corretos, mas uma resposta anterior foi repetida em relato novo. |
| `entrega_final` | 30 HTTP 200 e uma tentativa sem status por timeout no resumo; grupo do usuário adotado e reparo de formato sem contexto no turno 18. O nome desta pasta não representa encerramento. |

A ocorrência de timeout no resumo, com apenas uma chamada principal, é distinta
do gasto redundante demonstrado em F3. Nenhuma coleta verde prova ausência de
timeouts futuros: carga local, geração malformada e saídas longas continuam
relevantes. Atrasos sem a interpretação redundante exigem diagnóstico próprio;
não elevar prazos nem trocar modelo para ocultá-los.

### Última conversa longa e refinamentos posteriores

`validacao_pos_recuperacao`: 30 turnos, 30 conclusões textuais, 32 HTTP 200,
238,709 s somados nos turnos, 20 pacotes de fontes conferidos por ocorrência,
papel e texto. Dois pedidos simulados com receipts negativos; zero voz/efeitos.
Não houve transporte sem status nesta coleta. Isso não significa que todos os
turnos tenham ficado dentro de 20 s: o 18 levou 26,07 s com geração malformada
longa e recuperação. F3 foi validado no recorte de admissão redundante, não como
garantia de latência global. O resumo 29 foi produzido nesta versão, enquanto
a versão anterior teve timeout nesse ponto.

Rubrica manual das dez retomadas: **oito coerentes, uma parcial e uma divergente**.
11/15/17/19/25/26/27/28 preservam os valores relevantes; 18 ainda diverge e 29
mantém caderno/horário/papéis, mas acrescenta que Nirvana seria a banda que mais
inspira o usuário, informação não fornecida. A rubrica avalia estas falas;
nenhum juiz LLM foi usado como prova.

No 18, o reparo efetivamente recebeu as fontes e o Qwen respondeu corretamente
que Bia levaria o livro. A revisão posterior substituiu a resposta por falta
de base sobre `Azul`, tratado como título/tema externo. A primeira perda de
fontes no reparo está corrigida, mas essa fronteira posterior continua aberta.
Não usar o reparo correto para declarar o composto verde.

Após a coleta longa, houve dois refinamentos demonstrados:

- Relato futuro fora de pergunta também podia ser adotado como plano da Laylay
  (8). Dois REDs e controle de determinante nominal refinam o mesmo contrato de
  perspectiva, comparando predicado/objeto, sem reescrever a fala.
- Principal excluía a moldura system da contagem histórica; reparo ainda a
  incluía. Auditoria detectou diferença e teste da factory confirmou o RED de
  identidade. Agora seleção/serialização preservam também os mesmos índices.

Por isso `avaliar.py ... --historica` identifica explicitamente a conversa longa
como anterior aos refinamentos desses dois owners. Não a apresentar como uma
nova coleta de 30 turnos da versão final. A transcrição está em
`resultados_testes/respostas_prazos_20261024/TRANSCRICAO.md`; hashes e auditoria
em `resumo.json`, `fronteiras.json` e baseline próprio de cada pasta.

`controle_futuro_final` executou três entradas com Qwen real depois do primeiro
refinamento de futuro e antes do controle de determinante. Sem drift/voz/ação.
A primeira pessoa do encontro não foi adotada, mas surgiu outra inadequação:
`já vi esse detalhe na sua agenda`, sem fonte ou leitura de agenda. O terceiro
turno repetiu a alegação. O controle **não** é verde de conversa nem substitui
o roteiro longo. A causa geral dessa alegação de acesso continua em estudo.

### Validação automatizada e estado aberto

Antes dos dois últimos refinamentos: 217 contratos/integrados verdes e, em
seguida, o teste instalado de recuperação com seus controles. Depois deles:
47 testes de perspectiva/recuperação verdes, incluindo identidade das fontes,
negação, citação, primeira pessoa legítima, turno divergente, pacote fechado e
intervalo que excede o orçamento. A regressão ampla inicial teve 2.000 GREEN,
30 subtests GREEN, 14 SKIP e uma deseleção por isolamento de import. A deseleção
foi executada na factory isolada: um GREEN. A única falha foi
`test_orquestrador_deterministico_resolve_mesmo_app_apos_moldura[pode abri a calculadora para mim]`,
que escolhe MUSIC_SEARCH em vez de APP_OPEN. A mesma falha foi reproduzida no
owner congelado (`relato_composto/falha_vizinha_baseline.xml`); não é declarada
corrigida nem atribuída a estes candidatos. Regressão posterior da versão atual:
**2.003 GREEN, 30 subtests GREEN, 14 SKIP, uma deseleção e a mesma falha antiga**,
em 139,99 s (`regressao_pos_refinamento.xml`). O teste deselecionado passou
separadamente em `import_isolado.xml`. `git diff --check` dos 15 owners passou.

**Esta entrega é progresso validado por contratos, não encerramento das
respostas inadequadas ou dos timeouts em geral.** Permanecem:

1. A revisão factual confunde menção descritiva/histórica com alegação sobre
   obra externa, no caminho do livro azul. A fonte e a recuperação já são
   controles verdes; investigar seleção de tema e alcance da revisão sem
   liberar prosa pessoal como verdade por rótulo da IA.
2. O detector de frase incompleta marca o final de uma locução adverbial como
   subordinador pendente (`de vez em quando`). No 22, uma fala completa é
   reparada e volta a ser recusada, terminando em limite de tentativas. Precisa
   de contrato de função sintática, não exceção à frase do roteiro.
3. Alegação de que leu a agenda sem fonte observada, no controle curto. Ainda
   não há raiz compartilhada comprovada com outros relatos de acesso.
4. Geração malformada/longa e timeout residual do resumo. `response_format`
   foi enviado, porém isso não comprova que o backend tenha aplicado a gramática;
   o texto inválido e `finish_reason=length` são observações, não diagnóstico
   de causa do backend. Não trocar GGUF/backend/modelo nem elevar prazos sem estudo.
5. Naturalidade da contingência literal e apoio semântico de paráfrases livres
   continuam limitados. Citação atribuída não significa compreensão universal.

O escopo final de produção desta etapa é a lista de 15 owners em
`owners_alterados.json`, comparada ao snapshot desta tarefa. `laylay.py`, voz,
executores de domínio, integrações físicas e seleção do modelo não foram
alterados nesta etapa; suas mudanças anteriores na worktree foram preservadas.

## Critérios e limites da entrega

1. Conversa sem operação não consome interpretação de comandos redundante;
   pedidos efetivos continuam passando pela admissão e autorização canônicas.
2. Relato, pergunta, referência e feedback preservam atos/targets distintos.
3. Fonte do usuário permanece atribuída, com correções e negações, nas rotas
   principal e de recuperação. Proposta da IA não vira prova.
4. Há uma conclusão textual por turno e nenhum sucesso operacional fictício.
5. Contratos focados, regressivos, factory e Qwen real são evidências separadas.
6. Naturalidade geral, paráfrase livre, contexto além do teto, áudio e efeitos
   físicos não são comprovados por estes ensaios. Permanecem fora deste fecho.

## Continuação — revisão do foco prospectivo, 24/10

O bloqueio de18foi isolado no revisor comum: cópula de foco de participante
futuro era aplicada como propriedade do tema. Corrigido no recorte prospectivo,
após contraprova com outro assunto e retirada de candidato amplo inseguro.
Não apagadas as pendências históricas: menção descritiva como título, autoria
livre,27/28e geração malformada permanecem separadas. Qwen novo30turnos/34HTTP200
preservou a resposta sobre Bia;semvoz/efeitos,dois comandos simulados. Escopo,
25 contratos finais,2028 regressivos aprovados e limitações no relatório:
`melhorias e planos/registro/RELATORIO_REVISAO_HISTORICO_20261024.md`.

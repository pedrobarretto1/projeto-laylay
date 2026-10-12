# Laylay — registro de problemas e correções

### Contexto operacional — repetição não substitui argumento atual — 12/10/2026

Pedido de Pedro: investigar associação geral entre contexto e pedido atual.
Base `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, worktree
suja/paralela preservada. Baseline, hashes e decisões em
`resultados_testes/contexto_cruzado_20261012/painel_antes_v1.json`.
Não confundir esta evidência com encerramento da raiz numérica anterior.

**Primeira fronteira demonstrada:** a gramática geral encontrava repetição
ou pronome em qualquer posição e reutilizava integralmente o referente antigo.
Depois de abrir calculadora, “abre o bloco de notas de novo” devolvia calculadora;
depois de abrir YouTube, “abre a calculadora de novo” devolvia YouTube; depois
de tocar rock, “coloca a playlist jazz de novo” devolvia rock. A precedência
operacional introduzida na correção numérica anterior expôs essa permissividade
da gramática compartilhada no caminho prioritário. Não atribuir isso ao modelo.

**Falsificações/controles:** owner puro reproduz 20 REDs em quatro tipos de
referente, sem memória, LLM, percepção ou executor. Sete controles de reuso
passam. Composição instalada reproduz seis desvios desta família; pedidos
explícitos sem repetição e pronomes legítimos funcionam na mesma instalação.
Isso falsifica necessidade de geração, perda geral de receipt e incapacidade
geral dos detectores explícitos. Não prova causalidade de todos os relatos
históricos de contexto nem de todas as habilidades.

**Contrato e candidato mínimo:** o contexto pode preencher um operando
referencial/omitido, não sobrescrever um operando nomeado pelo pedido atual.
“De novo” modifica a operação; “ele” numa cláusula de foco não muda o alvo
principal. Produção alterada nesta etapa somente em `contexto_imediato.py`,
na gramática compartilhada. Reusa o predicado canônico de valor referencial
e a separação de complemento de foco; não reconhece nomes novos, não cria
parser privado de aplicativo/site/playlist/arquivo e não executa efeitos.
Detectores explícitos continuam donos dos argumentos novos. Reuso puro,
janela recém-aberta e ajuste numérico permanecem nos contratos existentes.
Nenhum commit, mudança em rede/modelo/voz/UI/executor ou limpeza da worktree.

**Provas e limites:** 142 GREEN focados no primeiro candidato. Regressão
relevante: 404 GREEN / 22 subtests em 19 módulos, `regressao_v1.xml`.
Painel instalado pós-candidato: 19/21 decisões GREEN, incluindo novos alvos
e trocas entre app/site e playlist→app, com pronomes/negações/perguntas como
controles. `painel_candidato_v1.json` preserva os dois REDs restantes;
não foram retirados do painel para declarar verde total. Receipts são fixtures
publicadas pela base instalada, rede recusada; não valida main, desktop,
efeitos reais ou áudio. Testes do painel isolam explicitamente o recorte
corrigido; não representam aprovação dos dois itens abaixo.

**Próximas fronteiras, separadas:**

- Após a seleção correta de playlist, o detector explícito entrega
  `nome_playlist="jazz de novo"`: modificador de operação contamina argumento.
  Já não reutiliza rock, mas o destino final ainda está incorreto. Investigar
  o contrato canônico de argumento/modificador, incluindo nomes literais.
- Após VOLUME, “coloca a música máximo respeito” vira VOLUME/set/100 por regra
  antecipada de palavra extrema. “Me explica o máximo divisor comum” também
  produz esse candidato no detector, mas o coordenador veta a ação; não é
  execução real comprovada. Primeira fronteira é a admissão dessa regra, não
  LLM ou autor de resposta. Investigar compatibilidade da fala atual antes
  de herdar domínio, preservando elipses legítimas de volume.

Ainda falta prova na sessão desktop e extensão do painel a contexto entre
etapas compostas, intervenções intermediárias e ambiguidades concorrentes.
Não encerrar “contexto geral” nem fundir os REDs acima com F1 ou TTS 403.

### Continuidade operacional — preservar a ocorrência antes da disputa por verbo/domínio — 12/10/2026

Continuação da mesma evidência “volume em 90” → “coloca em 40”; não criar
outra raiz por frase/número. Base `main`, HEAD
`2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, worktree suja/paralela preservada.
Produção alterada somente em `contexto_imediato.py`, `continuidade_geral.py`,
`orquestrador_deterministico.py` e `coordenador_intencao.py`. Testes, uma sonda
de composição e documentação atualizados. Não alterados voz/TTS, rede neural,
modelo/configuração, executores, confirmação de efeito, UI ou composition root.
Há alterações paralelas de voz já na worktree; não foram apropriadas por esta
correção. Nenhum commit criado.

**Raiz local demonstrada:** a gramática geral já resolve ajuste de volume
elíptico, mas o verbo “coloca” chegava ao detector musical antes desse vínculo.
REDs anteriores conservados: seis falhas, dois controles explícitos. O teste
agora confirma também que o owner geral retorna 40/25 antes do detector
retornar MUSIC_SEARCH. Falsificados: ausência de memória/receipt; necessidade
de uma música anterior; inexistência de gramática contextual; necessidade de
LLM/TTS para produzir o desvio. Não inferir reprodução real da fala histórica.

**Diferenças de composição encontradas, não compensadas no harness:** o
publicador instalado enriquece foco conversacional (`evento=foco`, sem ID) sobre
o slot de domínio; a operação oficial identificada continua separada. Domínio
`sistema` não é subtipo `volume`. Depois, o refino do próprio seguimento atualiza
o foco narrativo antes da resolução. Uma seleção operacional correta não deve
voltar a disputar com esse foco. Primeiros candidatos ficaram verdes em testes
menores, mas três casos positivos permaneceram RED na composição instalada.
Artefatos v1–v6 preservam essas divergências; não aprovar pelo verde unitário.

**Contrato compartilhado:** `resolver_continuacao_operacional_confirmada`
reutiliza modalidade canônica, seleção oficial de operação compatível e
gramática geral. Exige receipt atômico do executor confirmado, identidade
compatível, params coerentes com a operação armazenada e idade finita/recente
(300 s; tolerância de relógio futuro limitada a 5 s). O último efeito qualificado
fornece referente, não permissão: fala atual ainda precisa ser um ato autorizado.
Projeção de subtipo tem um owner único, usada também pela referência imediata.
Não selecionar de novo um foco conversacional após qualificar a ocorrência.
Parâmetro novo vem da fala; operação/referente/destino vêm do contrato válido.
`target` passa a ser conservado no inventário seguro; destinos pc_a/pc_b são
testados, sem provar acesso ou efeito remoto. Mesmo mecanismo é provado com
referência de aplicativo, sem novo parser privado por habilidade.

O detector consulta esse owner antes de interpretação por verbo genérico.
Forma numérica de atribuição sem nome de parâmetro reutiliza o padrão que já
existia na gramática de volume, não um catálogo de frases históricas. As portas
contextuais numéricas também reutilizam a qualificação, impedindo recuperação
de referência vencida por um fallback legado. Sem vínculo, o detector não
transforma o parâmetro em título musical. Consulta, negação, condição, citação,
troca explícita para música e prazo não ganham autorização pelo contexto.
Cobertura é a gramática existente, não entendimento universal de qualquer ajuste.

**Última fronteira RED:** um teste adversarial mostrou que, após nenhuma
resolução válida, o fallback IA podia inventar MUSIC_SEARCH/query="em 40" e
ganhar arbitragem. RED reproduzido antes do ajuste no coordenador. Agora,
atribuição contextual reconhecida sem candidato vinculado retorna
`contexto_parametro_nao_resolvido`, sem consultar esse fallback para executar.
O fluxo de conversa/esclarecimento permanece responsável pela resposta; não
foi escrita uma fala fixa nem garantida sua qualidade nesta sonda.

**Provas finais:** 357 testes GREEN e 22 subtests GREEN em 19 módulos relevantes,
`resultados_testes/continuacao_operacional_20261012/regressao_final.xml`.
Novos controles: parâmetros/identidade divergentes, timestamp futuro/NaN,
expiração, contexto ausente, fonte não confirmada, destinos, foco narrativo,
outro domínio e proposta adversarial de IA. Nenhum xfail novo.
`sonda_instalada_final_v9.json`: 9/9 decisões corretas; detector, coordenador,
base de publicação e contexto são os callbacks instalados por `laylay.py`;
fontes estáveis. Relato/variantes retornam VOLUME/set/40 ou 25, pedido explícito
preservado; vencido/não confirmado/pergunta/negação não produzem decisão de ação;
título musical explicitamente pedido continua MUSIC_SEARCH. Zero consultas
à porta de IA para esses nove casos. Receipts da sonda são fixtures declaradas,
publicadas pela base real: não foram releituras do Windows.

**Contraprova de necessidade:** `contraprova_sem_precedencia_v1.json` retira
somente a prioridade/recusa numérica do detector neste subprocesso, mantendo
o owner contextual. O relato volta a MUSIC_SEARCH/query="em 40", outro nível
vira “em 25”; quatro decisões RED, controles de pergunta/negação/título mantidos.
Assim, disponibilizar um resolver que funciona sozinho não basta: seu consumo
precisa preceder o candidato de outro domínio. Não é replay de HEAD nem patch
aplicado na worktree.

**Estado de encerramento:** GREEN da decisão instalada, não main/efeito/áudio.
Não abrimos player nem alteramos volume físico. Após reiniciar a Laylay,
verificar a sequência no desktop e o receipt/releitura final em 40%. A falha
de TTS 403 permanece independente e não foi investigada aqui. F1/significado
livre e seus REDs anteriores não foram incorporados nesta raiz nem encerrados.

### Contexto operacional — ajuste numérico elíptico registrado como regressão — 12/10/2026

Pedido de Pedro: incluir o relato nos testes, **sem correção de produção nesta
etapa**. Base `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, worktree
suja/paralela preservada; testes/documentação alterados, nenhum commit criado.
Agrupamento com outras raízes de continuidade ainda pendente de investigação;
não consolidar com F1/realização nuclear ou com indisponibilidade de voz.

**Relato desktop:** às 12:09:09, “coloca o volume em 90”; receipt
`4b50eae47c8e4ccfaae5eaa9ea29fbc1`, VOLUME/set/90, volume_ajustado,
executou=True, confirmado=True, releitura de volume mestre em 90%. Às
12:09:26, “coloca em 40”; às 12:09:37, fala anuncia reprodução de
“ADOLESCENTE DE 40 ANOS | EMBRULHA PRA VIAGEM”. O trecho recebido não inclui
receipt da segunda ação: **não prova reprodução real** ou sua rota completa.

**Regressão adicionada:**
`scripts/tests/test_regressoes_contexto_operacional.py::test_ajuste_numerico_apos_volume_confirmado_nao_vira_busca_musical`.
Primeiro reconhecer o pedido completo, registrar receipt pelo publicador real
de memória, conferir estado/certeza/nível e só então resolver o seguimento pelo
detector determinístico real. Nenhuma execução Windows/YouTube, LLM ou voz.
Fixtures de receipt não são efeitos materiais. Quatro frases × presença/ausência
de música anterior: “coloca em 40”, “coloca em 25”, “deixa em 40” e o controle
“coloca o volume em 40”. Expectativa: VOLUME/set/novo nível, nunca título musical
nem repetição do 90. Não fixar o contrato no número ou no título histórico.

**Resultado:** módulo com **6 RED / 14 GREEN**; dos oito casos novos,
seis RED e dois controles explícitos GREEN. Memória registra corretamente o
volume e a confirmação antes da falha. “coloca em 40” resulta em
`MUSIC_SEARCH/query="em 40"`; com 25 também; “deixa em 40” não produz candidato.
Falhas iguais com e sem música anterior. Portanto, neste caminho local,
faltarem memória de volume, confirmação ou uma música anterior não explicam
o desvio. A primeira fronteira reproduzida é a resolução da elipse, não a
fala final nem TTS. `detectar_volume_ou_midia` recebe contexto_volume_ativo,
mas a entrada no ramo de volume cobre domínio explícito/extremos/termos
específicos, não esse ajuste numérico sem substantivo. Depois, outro domínio
consome “coloca ...”. Isso sustenta o diagnóstico local; composição instalada
e rastreamento da sessão histórica ainda não foram validados para esta raiz.

**Contrato geral a investigar:** seguimento autorizado deve resolver referente
vigente e parâmetro atualizado antes da disputa entre domínios. Contexto fornece
referente, não permissão ou prova de efeito. Preservar troca explícita de assunto,
TTL/ambiguidade, parâmetros seguros e negativas/perguntas; não transformar
qualquer número depois de volume em autorização. Owner compartilhado a mapear
antes de patch, não adicionar exceção para 40 ou para essa música.

**Observação separada de voz:** após o primeiro turno, Francisca não respondeu;
tentativa com Thalita terminou em WSServerHandshakeError/HTTP 403. Texto entregue
não comprova áudio ouvido. A causa do 403 não foi investigada aqui; não registrar
URL com parâmetros/tokens nem presumir causa de rede/configuração/modelo.
O RED contextual é reproduzido sem TTS: falha de voz não é necessária para ele.

### F1 — realização condicional integrada na autora cotidiana; significado livre permanece aberto — 12/10/2026

Base `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, worktree
suja/paralela preservada. Produção alterada nesta etapa **somente em
`personalidade/confirmacao_llm.py`**. Não alterados classificação, execução,
receipts, pendências, catálogo, composition root, voz, rede/modelo/configuração.
Atualizados sonda, testes e documentação; nenhum commit criado.

**Primeira fronteira demonstrada:** complemento canônico e renderer estavam
disponíveis, mas a autora cotidiana ainda exigia prosa livre (`conversa`) e
nunca consumia a escolha verificável. Antes do candidato: **17 RED / 5
controles** em 22 testes novos. Dezesseis positivos falhavam no envelope
`estrutura_mista_invalida`; o negativo publicava literalmente
“A condição não criou agendamento. Quando você confirmar, a música retomará.”
Assim, acertar um núcleo lexical não impedia a promessa extra. Não era falta
de callback/import ou incapacidade do renderer: os controles canônicos já
realizavam a fonte; a chamada chegava à autora e seu formato livre era aceito.

**Contrato reutilizado, não novo parser:** quando TODOS os atos do complemento
tipado têm cobertura condicional, o pedido cotidiano exige somente
`{"trechos":[...],"realizacoes":[{"indice":...,"opcao":...}]}`. O modelo escreve
os trechos operacionais e escolhe a redação; o owner regenera as opções e
materializa o núcleo. Verificador existente confere fonte/índice/turno/texto.
Envelope fechado: sem texto extra ao JSON, campo livre, comando, índice
inferido ou opção desconhecida. Snapshot condicional inválido não cai no
canal livre. Prosa livre de consulta e confirmação puramente operacional
continuam usando seus caminhos anteriores.

Texto controlado conserva integralmente a fonte citada, sem normalizar sua
realização depois do vínculo. Somente esse trecho verificado deixa de ser
submetido às heurísticas de prosa livre, que poderiam tratar a fonte citada
como promessa da autora. Receipt por receipt, limites numéricos, alvos,
certeza, escopos não sobrepostos, avisos imutáveis e guarda operacional
continuam ativos. Orquestrador existente revalida o complemento antes/depois
da chamada e publica uma resposta. Não consultar nem limpar pendências alheias.
Seleção inválida é recusada com falha observável, sem tentar corrigir prosa
no canal de escolhas. Isso é **linguagem controlada**, não prova universal
de semântica livre ou remoção de mecanismos legítimos de confirmação.

**Testes ajustados com justificativa:** antigas fixtures condicionais que
devolviam `conversa` não representam mais o protocolo adotado. Positivos agora
escolhem o inventário efetivamente enviado; negativos mantêm o texto livre e
exigem recusa/publicação factual única, sem reaproveitar promessa como seleção.
Testes de reparo livre migraram para consulta de significado (sem cobertura
nuclear), preservando duas chamadas limitadas, mesmos receipts, recusa de
reparo que altera trecho operacional e revalidação de vigência. REDs legítimos
da guarda livre e do foco sem receipt não foram enfraquecidos ou marcados xfail.

**GREEN focado/regressão relevante:** 377 testes em dez módulos; 108 controles
em três módulos com **5 REDs anteriores mantidos**; 76 regressivos de resposta
operacional composta/composição/registro/higiene. Total **561 GREEN / 5 RED**
em 17 módulos, não suíte global verde. Novos controles cobrem quatro domínios,
três realizações, sucesso/falha/incerto/idempotência canônica, falso sucesso,
índice/opção inválidos, extras, três promessas que escapavam do detector livre,
fonte Unicode/aspas/número, inventário adulterado e dois receipts independentes.
Integração com orquestrador real, portas de modelo/entrega isoladas: uma
publicação e aviso único, pendência alheia preservada; mudança de turno/pessoa
durante autoria retém a publicação. Isso não é main nem efeito externo.

**Composição instalada + Qwen real, sem ponte de realização:**
`resultados_testes/interpretacao_legada_20261012/autoria_nuclear_cotidiana_qwen_v1.json`
e `.../autoria_nuclear_cotidiana_qwen_v2.json`. Dois painéis de seis autorias,
12 HTTP 200 em `qwen3:4b-instruct`, Ollama local. Em AMBOS, os três condicionais
devolveram escolhas válidas e publicaram exatamente a realização correspondente,
uma porta operacional/uma autoria/uma publicação, sem reentrada. V2 inclui
hashes do owner/verificador no conjunto de fontes cotidiano; fontes estáveis.
Não foi utilizada `realizacao_controlada=True`: o pedido HTTP é da autora
cotidiana. As portas operacionais recusam e não emitem receipts de sucesso;
a publicação mantém o aviso de resultado não confirmado. Portanto NÃO prova
efeitos, áudio, main ou autoria real com receipts materiais de sucesso/falha.

**F1 não encerrada — próxima fronteira:** consultas de significado não estão
cobertas pelo núcleo condicional. V1 recusou JSON com chave extra de fechamento
no caso do bloco de notas; V2 ficou estruturalmente verde, mas disse que a
expressão significa “entender o que é o bloco de notas” e, no arquivo,
“nem tenho acesso direto ao sistema de arquivos”. Essas alegações passaram
pela guarda; verde do pipeline não prova significado nem capacidade. O objeto
consultado chega à autora; aprofundar a divergência entre explicar o objeto,
descrever a consulta e inventar limitações, sem ampliar regex por frase.
Os cinco REDs mantidos são três escapes da guarda livre, foco alegado sem
receipt e contrato de catálogo de robô versus enum antigo (`estado_owner` ou
`estado_firmware`); não misturar esses owners com esta integração.

**Descoberta adjacente, sem patch:** a inspeção classificatória de
“Abre a calculadora; quando eu estudar Python, como começar?” produz um único
segmento `condicao_nao_verificada`, sem autorização, absorvendo o pedido inicial
antes da autora. Classificador não foi alterado nesta etapa: primeira fronteira
é anterior à realização, não regressão atribuível ao novo protocolo. Relação
com a raiz de segmentação é hipótese a falsificar, não nova raiz declarada.
“Abre a calculadora; se chover, como eu cuido das flores?” serve como contraste:
o ato inicial é preservado e o restante recebe resposta_conversacional.

### F1 — vínculo nuclear com realização controlada: primeiro positivo verificável, integração cotidiana pendente — 11/10/2026

Base reconferida `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`,
worktree suja/paralela preservada. Produção alterada nesta etapa somente em
`contrato_fala.py` e `validacao_contrato_fala.py`. Não alterados autora cotidiana,
classificador, executor, receipts, pendências, catálogo, composição raiz, voz,
rede/modelo/configuração; nenhum commit criado. Sonda e testes atualizados.

**Contrato geral:** seleção declarada pelo modelo não comprova a realização
da proposição na fala. Adotar somente o conteúdo coberto pelo owner, mantendo
independentes fonte, vigência, realização linguística e efeito. Ablações
anteriores falsificaram prompt/núcleo extra e palavras positivas como provas.
Nesta etapa não acrescentar detector lexical para cada promessa que escapou.

`construir_realizacoes_nucleo_explicativo` consome o complemento tipado e
revalida snapshots pelo contrato existente, sem interpretar comandos. Cobertura
inicial **somente condicional read-only**: fonte citada integralmente conserva
pessoa/objeto, condição não verificada (não declarar que não ocorreu), ausência
de agendamento criado por esta explicação e necessidade de novo pedido direto.
Três redações parametrizadas pelo ato, não por domínio/nome/frase histórica.
É linguagem controlada com escolhas de redação, **não geração livre** nem
interpretação comprovada do significado de qualquer expressão. Nenhuma frase
livre recebe certeza por coincidir com palavras desse núcleo. Consulta de
significado, outro ato sem cobertura e índice duplicado continuam fail-closed.

`realizar_nucleo_explicativo` é o owner único de schema/índice/opção e
materialização textual; renderer e validador reutilizam essa decisão. O
inventário enviado ao modelo não é confiado como verdade: opções são regeneradas
do snapshot pelo owner. Não permitir comandos, campo de texto livre, autoaprovação,
opção não cadastrada ou índice inferido. Vínculo exige texto/turno do complemento
e do contrato. Comparar o texto efetivo com a realização integral: adicionar
uma promessa após um núcleo correto é divergência, não sucesso parcial oculto.

Estados explícitos no validador para contratos que exigem núcleo:

- `aderencia`: realização controlada integral e vinculada, sem autoridade;
- `contradicao_vinculo`: schema/índice/texto contradiz a proposta coberta;
  não é classificação universal da verdade de uma frase livre;
- `cobertura_ausente`: falta representação/owner/opção coberta ou vínculo vigente;
  não aprovar nem pedir reparo como se o modelo pudesse suprir essa cobertura.

Todos mantêm `prova_semantica_livre=False` e `autoriza_execucao=False`.
Texto livre correto também não é promovido a aderência sem esse vínculo.
Callers legados permanecem iguais; não integrar a nova política na autora
cotidiana antes da prova específica. Há confiança no snapshot fornecido pelo
owner; não alegar autenticidade criptográfica ou leitura do estado global.

**RED anterior ao candidato:** 15 falhas / 6 controles, alcançando o validador
existente sem erro de import/API: 12 positivos em quatro domínios × três pessoas
e três negativos com texto acrescido. Depois, fonte Unicode/aspas/longa, pessoa
adulterada, duplicatas, consulta sem cobertura, variantes e inventário alterado.

**Primeira proposta real falsificada:** protocolo exigia seleção e cópia literal
da fala. Nos três casos Qwen devolveu campos vazios; recusados, uma resposta de
falha observável, zero aderência. Transporte HTTP confirma pedido efetivamente
enviado: não era callback, timeout ou filtro escondido. Isso não prova que
somente a cópia causou a falha. Simplificado o protocolo da sonda para apenas
seleção; host materializa e valida a fala, preservando receipts/avisos separados.
O modelo escolhe redação, não decide se há autoridade de execução.

Segunda proposta real devolveu três listas com seleções válidas, mas o envelope
era recusado. Primeira divergência: representação, não significado da opção.
Novo RED reproduzido: 1 falha / 29 controles. Owner agora aceita lista explícita
ou objeto `realizacoes` envolvente, com mesma validação estrita de cada item.
Não procurar JSON em prosa, descartar campos extras, completar seleção vazia,
converter índice ou inferir opção. Essa equivalência documentada não enfraquece
os testes de promessa/texto/índice nem modifica o painel congelado.

**Provas finais:** **346 testes GREEN em dez módulos**, sem xfail. Nova
composição instalada, portas isoladas: três positivos entregues com uma chamada
operacional/uma escolha/uma publicação, sem reentrada; três contraprovas após
materialização recusam texto acrescido e publicam falha observável/fase parcial.
Sonda real final **3/3 aderências no recorte condicional**, três HTTP200, fontes
estáveis; Qwen escolheu `condicao_1`, owner realizou/conferiu, publicação preservou
o texto conferido e o aviso de resultado operacional desconhecido. Não é prova
de três efeitos, áudio, main completo, geração livre ou estilo espontâneo.

Artefatos em `resultados_testes/interpretacao_legada_20261011/`:

- `realizacao_nuclear_composicao_v1.json`: protocolo inicial, positivo isolado;
- `realizacao_nuclear_composicao_v2.json`: protocolo final só seleção;
- `realizacao_nuclear_contraprovada_v1.json` / `v2.json`: controles negativos
  correspondentes, não deixar promessa passar em troca de GREEN;
- `realizacao_nuclear_qwen_real_v1.json`: três REDs/campos vazios;
- `realizacao_nuclear_qwen_real_v2.json`: três REDs de envelope, seleções válidas;
- `realizacao_nuclear_qwen_real_v3.json`: três aderências de realização final,
  brutos/payloads/hashes/HEAD/worktree e limites preservados.

**REDs antigos não apagados:** execução focada atual confirmou 57 GREEN / 4 RED
em `test_explicacao_sem_continuacao.py` e `test_reparo_explicativo_misto.py`:
três promessas no caminho legado e foco sem receipt. Catálogo robótico continua
pendência separada, não revalidado por esta suite. As melhorias novas ainda não
mudam essas rotas: não declarar F1 encerrada, rede pronta ou fallback reduzido.
Compilação/diff conferidos; sem commit. Rede continua pausada.

**Próxima fronteira:** integrar o protocolo apenas no complemento condicionado
com cobertura comprovada, mantendo a mesma validação independente dos trechos
operacionais, aviso imutável e revalidação do lote antes/depois. Ampliar prova
Qwen/receipts/pessoas/turnos antes de ativar; verificar impacto de naturalidade
e repetição das realizações controladas. Consulta de significado/texto livre
exige outro conteúdo comprovado, não pode herdar essa cobertura nem um preset
genérico que descreva a pergunta em vez do objeto. Não ampliar o patch para
foco, robótica ou rede porque estão na mesma worktree.

### F1 — núcleo por ato estudado; cobertura desconhecida não pode virar aprovação — 11/10/2026

Base reconferida `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`,
worktree suja/paralela preservada. Primeiro estudados `ContratoSemanticoFala`,
`RoteiroGeracaoConcreta`, validador comum e autoria/reparo existentes. Não criar
outro interpretador ou verificador privado. Nesta etapa **produção alterada
somente em `validacao_contrato_fala.py`**, guarda opt-in de cobertura descrita
abaixo. Autora, guardião lexical, classifier, executor, pendências, receipts,
catálogo, composição raiz, rede/configuração/modelo não alterados. Sem commit.

**Protótipo exclusivamente diagnóstico:** `projetar_nucleo_explicativo` na sonda
consome o complemento/snapshots já canônicos, sem gold/parser. Reusa contrato
e roteiro existentes. Preserva fonte completa, objeto separado da pergunta,
pessoa da condição e conclusão deste caminho read-only; não comprova significado
da expressão, condição satisfeita, efeito, ausência global de pendências ou
acesso/capacidade. Fonte longa fica integral nos núcleos, mesmo que campos
legados do roteiro limitem strings. `somente_diagnostico=True`; não injetado
no runtime de produção nem promovido como solução.

**Ablação nova:** seis casos congelados × controle/intervenção × duas repetições,
ordem invertida na segunda. Única intervenção é `contrato_fala` adicionado ao
pedido (também preservado no reparo da variante); não alterar system, estados,
receipts, classificadores ou parâmetros. Artefato:
`resultados_testes/interpretacao_legada_20261011/nucleo_explicativo_qwen_ablacao_v1.json`.
24 turnos / **29 chamadas reais HTTP200** (cinco reparos), fontes estáveis,
24 portas operacionais recusadas, 24 publicações, sem reentrada, efeito, main,
voz ou holdout. SHA256 do arquivo:
`086BCCD9F588AF5362C9553FC3A698010F3257674F8823BCF01CDFD03514BF2B`.
Coleta anterior à guarda de cobertura/flag final, brutos imutáveis.

**Resultado de revisão, não nota automática:** núcleo ajuda alguns condicionais
a mencionar novo pedido, mas não resolve coerência. `dominios_distintos_condicao`
com intervenção nas duas repetições ainda exige confirmação ou mistura novo
pedido com espera. Os casos de consulta continuam confundindo `objeto_textual`
com a pergunta inteira; a intervenção da calculadora na primeira repetição
chama a própria expressão de consulta. Resultados de controle/reparo também
contêm inferências não comprovadas sobre condição satisfeita/acesso/efeito.
Não contar 24 aceites como 24 acertos, nem menos reparos como melhora suficiente.
Repor núcleo no prompt, sem mecanismo de aderência, foi falsificado como solução.

**Primeira fronteira do novo candidato:** o validador comum recebe o roteiro,
mas não possui verificador do núcleo por ato; todas as **29 redações recebem
`aceita=True`**, inclusive as ruins. Controles locais reproduzem o problema
com estratégia experimental e com `resposta_multiacto` existente; não é só
desconhecimento de um novo nome. Acrescentar o núcleo correto e, em seguida,
uma promessa contraditória também passa. Não usar presença de palavras corretas,
autoclassificação JSON ou ausência de violação lexical como prova nuclear.

**Candidato mínimo de segurança:** contratos que explicitamente exigem
`exigir_nucleo_verificado=True` recebem `categoria=cobertura_ausente`,
`avaliado=False`, `aceita=False`, `nucleo_atendido=False`,
`problemas=[nucleo_sem_verificador]` e **não** pedem reparo. A LLM não pode
reparar a inexistência do owner de validação. A política independe de alvo,
domínio, frase ou presença do roteiro; legados sem exigência permanecem iguais.
Não é verificador semântico implementado nem declaração de que a fala é falsa.
Também não aprova uma fala correta até haver verificador. Nenhum caller de
produção atual passou a exigir esse núcleo, portanto essa proteção **não muda
a conversa cotidiana nem fecha os três REDs reais de promessa**.

RED de cobertura: inicialmente dez negativos; ao tornar explícita a exigência
e corrigir a premissa de que o validador já verificava esse núcleo, **13 RED /
13 controles** antes do patch, incluindo positivo e roteiro ausente. Não
enfraquecida a exigência de não aprovar; corrigido `avaliado=True` para
`avaliado=False`, documentando falta de cobertura em vez de inventar verificação.
Depois: 27 testes novos GREEN; conjunto de cinco módulos **187 GREEN**, mais
quatro módulos de autoria/metalinguagem/social/expressão **129 GREEN**: total
**316 GREEN**, sem xfail. São testes desta fronteira, não suíte global nem prova
de conversa corrigida. Os REDs anteriores de promessa/foco/catálogo seguem abertos.

Replay derivado, sem novas chamadas ao modelo:
`nucleo_explicativo_replay_cobertura_v1.json`, mesmos 29 brutos, contrato armazenado
acrescido somente da exigência explícita, 29 resultados de cobertura ausente.
Não sobrescreve coleta original; hash do texto recebido pelo replay distinguido
do hash dos bytes do arquivo acima. Não atribuir essa avaliação ao prompt original.
Compilação e `git diff --check` sem erros. Nenhuma prova de main/áudio/efeito.

**Próximo contrato a implementar, ainda aberto:** núcleo por ato precisa ter
owner de validação que diferencie cobertura ausente, contradição e aderência,
vinculando proposições da redação ao objeto/pessoa/conclusão do escopo. Depois
integrar ao lote e reparar só a violação de autoria, mantendo trechos operacionais
congelados/vigência/publicação única. Provar positivo, negativo contraditório
com núcleo presente, referente concorrente e ausência de prova; não exigir frase
fixa nem usar outro parecer LLM como receipt de verdade. Os dez negativos
documentam somente a impossibilidade de aprovação sem cobertura, **não**
acerto de um verificador ainda inexistente. F1 permanece aberta; rede pausada.

### F1 — candidato final confrontado com Qwen: proteção semântica insuficiente — 11/10/2026

Pedro encerrou a sessão; mutex adquirido sem interromper processo alheio.
Base reconferida `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`,
worktree suja/paralela preservada. **Nenhuma produção alterada nesta validação**;
somente três novos REDs no teste e este checkpoint/mapa. Sem commit, treino,
mudança de modelo/configuração, pendência, receipt, executor ou catálogo.

Artefato final novo e preservado:
`resultados_testes/interpretacao_legada_20261011/reparo_explicativo_qwen_real_v3.json`.
Seis chamadas reais `qwen3:4b-instruct` / HTTP200, fontes estáveis, seis portas
operacionais de recusa (uma por caso), seis redações e seis publicações;
**nenhum reparo acionado**. GREEN do CLI é estrutural/de roteamento, não
verificação semântica das seis respostas. Sem main completo, áudio ou efeitos.

**Falsificação do candidato como solução suficiente:** as três respostas
condicionais passam com promessa de efeito/continuação sem mecanismo:

- `dominios_distintos_condicao`: `Quando você confirmar, eu paro a música`.
- `mesmo_intent_operacoes`: `Quando você confirmar, a música retomará`.
- `iot_operacao_e_alvo`: `será necessário que você confirme explicitamente
  para que eu ative a ação`.

Primeira fronteira demonstrada é validação da explicação, antes do reparo:
nenhuma dessas saídas recebe problema, logo a tentativa de reparo não é
chamada. Não é timeout/transporte (seis HTTP200), reentrada de comando (uma
porta por caso) nem falta do contrato na mensagem (snapshots/pessoa presentes).
Não confundir pessoa preservada com continuação legítima. Três novos testes
alcançam esse limite: **3 RED / 41 controles GREEN** em
`test_explicacao_sem_continuacao.py`, sem xfail ou correção por frase.
Não ampliar novamente as regex nesta etapa: variações morfológicas já
falsificam a suficiência de detectar promessa por lista de construções.

Outros defeitos semânticos reaparecem nos brutos: a consulta da calculadora
recebe negativa geral de capacidade de abrir aplicativos, sem fundamento;
a expressão `pode abrir o bloco de notas` é confundida com a pergunta sobre
ela e não é explicada diretamente. O caso de arquivo também deriva para
permissão/capacidade em vez de significado. Não dar nota de acerto só por não
ter tool call nem acrescentar essas causas à raiz de foco/catálogo robótico.

Controles atuais: 115 testes de projeção/continuidade/guardas anteriores GREEN
antes de anexar os novos REDs; conjunto posterior de contrato/pessoa/reparo
**90 GREEN / 1 RED separado**, foco sem receipt já demonstrado. A suíte ampla
anterior 673 GREEN / 2 RED continua evidência histórica, não execução ampla
nova nem prova de prontidão. `git diff --check` da produção sem erros.

**Próxima investigação proposta:** ligar o conteúdo da explicação a um núcleo
canônico por ato, com papéis discursivos e conclusão limitada ao escopo; a LLM
pode realizar a redação, não inventar estado de continuação/capacidade. Mapear
reuso do contrato/validador de fala existente e provar cobertura/contradição
antes de pedir outro reparo. Fonte literal/objeto, pessoa, estado do caminho
read-only e receipts permanecem claims independentes; uma autoclassificação
JSON do modelo não prova que seu texto respeitou esses claims. Esta direção
é hipótese de desenho, **não implementada nem validada**. Não transformar um
núcleo canônico em frase fixa para todo assunto ou promessa universal.
F1 permanece aberta, rede pausada. O bloqueio de sessão foi resolvido; a
validação real revelou insuficiência, não uma versão pronta.

### F1 — pessoa discursiva e reparo do complemento: candidato aplicado, semântica ainda aberta — 11/10/2026

Base reconferida: `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`;
worktree suja e trabalho paralelo preservados. Produção alterada nesta etapa
somente em `modalidade_turno.py`, `contratos_turno.py`, `guardiao_alegacoes.py`
e `confirmacao_llm.py`. Não alterados executor, receipts, pendências, catálogo,
composição raiz, rede ou configuração/modelo; nenhum commit criado.

**Primeira divergência demonstrada:** fonte `quando eu confirmar` permanece no
frame e no pedido real da autora, mas a projeção só descrevia condição não
verificada, sem pessoa discursiva vinculada; a saída `minha confirmação` da
Laylay passa pelo guardião. A evidência bruta anterior está em
`compromisso_explicativo_qwen_real_v2.json`, caso `mesmo_intent_operacoes`.
Não é ausência do texto na entrada nem defeito de executor: a mesma troca
reproduz sem execução em música, IoT e arquivos. Contexto/prompt como solução
única já foram falsificados pelas ablações. Falha de autoria mista encerrava a
redação diretamente, ao contrário da autoria operacional simples com reparo.

**Contrato/candidato:** o owner de modalidade usa o mesmo reconhecimento de
condição para publicar pessoa discursiva (`enunciador`, `destinatario`, `grupo`
ou `indeterminada`) e coordenadas na fonte estrutural completa. Vínculo
literal é validado e congelado no snapshot; o consumidor não reinterpreta a
entrada. Mais de uma condição não recebe uma pessoa única: retorna indeterminada
até existir vínculo por condição. Nenhuma pessoa confere autorização/efeito.
Guardião de saída compara paráfrases de pessoa com o snapshot, preservando
negação local e citação da fonte. Cobertura gramatical limitada, não validação
semântica irrestrita; referências concorrentes não recebem certeza inventada.

Autora mista pode reparar **uma vez, apenas o complemento rejeitado**. Mesmo
contrato/snapshots, sem tools, `reparo_factual`, contexto fechado, mesmas guardas
de saída. Diagnóstico é motivo do validador, não receipt/fato e não copia a fala
errada para o pedido. Trechos operacionais já validados permanecem literalmente
congelados; qualquer mudança no reparo é recusada antes do aceite. Sem reentrada
operacional, criação de pendência, alteração de resultado ou publicação extra.
Resposta válida não chama reparo. Nova proposta inválida termina com falha
observável, não loop. Lote revalida turno e snapshot depois das duas redações.
Cada chamada mista mantém teto 15s; duas redações podem elevar a latência.

RED inicial: **18 falhas / 27 controles GREEN**, nas fronteiras de projeção,
pessoa e reparo. Projeção passa em 69 testes com continuidade. Controles depois
exigem offsets coerentes, citação/negação, múltiplas pessoas, turnos antigos,
reparo inválido e congelamento de trecho operacional. Qwen falsificou a ideia
de que reparo sem promessa seria explicação correta: devolveu `Essa expressão
é um pedido educado` para uma condição futura. RED preservado antes de exigir
cobertura mínima da relação condicional. Essa cobertura lexical apenas rejeita
resposta fora do assunto; não prova significado correto. Exemplo pronto no
prompt foi substituído por formato sem conteúdo-resposta copiado.

Duas coletas reais Qwen local `qwen3:4b-instruct`, seis casos/sete HTTP200 cada,
HEAD/frame/pedidos/brutos/hashes preservados, portas operacionais recusadas:

- `reparo_explicativo_qwen_real_v1.json`: promessa rejeitada, reparo fora do
  assunto aceito antes da guarda de cobertura; negativa de capacidade falsa.
- `reparo_explicativo_qwen_real_v2.json`: reparo IoT chegou a uma explicação
  com citação e novo pedido direto; demais aceites **não são acertos semânticos**.
  Ainda passaram `a música vai retomar` e `você precisa confirmar quando quiser`.
  Três REDs locais reproduzidos antes de ampliar a gramática geral de futuro e
  confirmação suficiente. Replay das três respostas condicionais brutas agora
  acusa `compromisso_sem_continuacao`. Sem novas regras por alvo/domínio.

Última composição instalada, `reparo_explicativo_composicao_v3.json`:
**15 controles GREEN**, três com pessoa incorreta → reparo válido, uma porta
operacional, duas propostas autorais e uma publicação, mesmo contrato nas
primeiras duas mensagens, sem reentrada ou efeito. v1/v2 preservam candidatos
intermediários. Ajustes de testes explicam a mudança aprovada de uma para duas
redações, mantendo publicação/efeito únicos; nenhum RED enfraquecido/xfail.
Regressão final de 16 módulos: **673 GREEN / 2 RED**, em 39,91s. Os REDs
são o controle sem reparo de foco e a categoria robótica já separados abaixo.
Compilação dos arquivos alterados e `git diff --check` sem erros.

**Limites/checkpoint:** a terceira coleta real do candidato final foi bloqueada
pelo mutex: Laylay aberta, sessão não interrompida; pedido de encerramento enviado
a Pedro. Não confundir as coletas anteriores com a versão final. Sem main
completo, voz ou efeito real. Rede pausada; não fechar F1 ou declarar redução
real de fallback. Restam explicação do objeto vs pergunta inteira, negativas
de acesso/capacidade sem fundamento e cobertura semântica além da gramática.
Próxima prova: geração real final com sessão fechada, revisão dos brutos e
entregas; atacar a próxima primeira fronteira, não ampliar regex indefinidamente.

**RED separado descoberto — abertura não prova foco:** guarda antiga de receipt
reconhece `foco`/`focada`/`frente`, mas aceita `Abri e foquei a calculadora`
com receipt apenas `aberto`. Reproduz também **sem complemento canônico/reparo**;
controle `deixei em foco` é rejeitado. Portanto não é defeito criado pela pessoa
discursiva. Reparo não pode introduzi-lo em trecho operacional congelado, mas
a vulnerabilidade da primeira redação permanece. Teste explícito sem reparo
preservado RED em `test_reparo_explicativo_misto.py`; não chamar a proteção do
reparo de solução desse contrato de foco. Categoria robótica de confirmação
continua outro RED separado já registrado abaixo.

### F1 — explicação não materializa confirmação pendente: proteção aplicada, autoria aberta — 11/10/2026

Base reconferida: `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`.
Worktree suja e alterações paralelas preservadas. Produção alterada nesta etapa
**somente** em `guardiao_alegacoes.py`, `confirmacao_llm.py` e
`orquestrador_fala_runtime.py`. Sem alteração de executor, pendências, catálogo,
composição raiz, modelo/configuração ou rede neural; nenhum commit criado.

**Primeira divergência demonstrada:** o complemento já está condicionado e sem
autoridade, mas a autora recebe somente texto/receipts; o verificador de saída
não reconhece espera operacional nem confirmação suficiente como alegação de
continuação. A fala `Vou aguardar seu sinal` é publicada sem que esse caminho
tenha criado uma pendência executável. Receipt de outro ato não justifica essa
promessa. Não consultar/apagar pendência alheia nem declarar ausência global.
Projeção/contexto extra e retirada de aviso já tinham sido falsificados como
solução suficiente nas ablações anteriores. Negações, explicações e espera por
uma resposta conceitual são controles, não compromissos operacionais.

**Contrato aplicado:** snapshot explicativo canônico → lote vigente → autora
recebe `atos_explicativos` → guardião compartilhado valida o escopo condicionado
read-only, independentemente de receipts de outro ato → uma publicação.
Contrato divergente é recusado antes da geração. O novo escopo não é imposto
a owners de continuação/agendamento existentes. A autora não decide autoridade
novamente nem cria pendência. A proteção de saída cobre espera por autorização,
futuro ligado à confirmação e confirmação apresentada como suficiente; usa
negação local e citação literalmente vinculada à fonte em enquadramento
explicativo. É uma guarda conservadora, **não verificação semântica irrestrita
de português**. Rejeição mantém a falha observável pelo fallback já existente,
sem anunciar sucesso ou aceitar o complemento como respondido.

RED antes do candidato: **15 falhas / 10 controles GREEN** no contrato/lote;
mais RED instalado preservado no artefato baseline: três promessas publicadas
entre 15 controles. Primeiro candidato: 56 focados GREEN. O Qwen real depois
falsificou cobertura suficiente dessa guarda inicial: `Preciso que você confirme
explicitamente para que eu possa agir` e `Para que a música seja retomada, você
precisa confirmar explicitamente` ainda passavam. Dois novos REDs reproduzidos,
34 controles GREEN; candidato ampliado no mesmo contrato, sem alvo/domínio
especial. Resultado final: **38 testes locais GREEN**. Replay dos dois textos
brutos da primeira coleta agora produz `compromisso_sem_continuacao`.

Regressão relevante de 15 módulos: **635 GREEN / 1 RED**, sem xfail ou teste
enfraquecido. RED separado abaixo. Composição instalada isolada: **15 controles
GREEN**, incluindo três recusas da promessa injetada, uma chamada operacional,
uma autoria e uma publicação em cada misto; sem reentrada ou efeitos. Preservadas
negações, explicação legítima, fonte citada, pendência alheia e contrato inválido.

Artefatos novos em `resultados_testes/interpretacao_legada_20261011/`:

- `compromisso_explicativo_baseline_v1.json`: três REDs instalados antes do patch.
- `compromisso_explicativo_candidato_v1.json` / `v2.json`: mesmos 15 controles;
  v2 corresponde à guarda final ampliada; fontes estáveis.
- `compromisso_explicativo_qwen_real_v1.json`: seis respostas reais/raw HTTP200;
  aceite estrutural não impediu as duas alegações de continuação nem uma negativa
  de capacidade sem fundamento. Não interpretar o retorno GREEN como semântica.
- `compromisso_explicativo_qwen_real_v2.json`: seis HTTP200, fontes estáveis;
  pedido de confirmação sem mecanismo foi rejeitado, com resposta observável
  e fase parcial. CLI retorna RED desse caso porque a parte conversacional não
  foi respondida, **não porque a promessa atravessou a proteção**. Cinco demais
  aceites estruturais não são cinco acertos: um texto aceito troca o agente da
  condição de `eu` do usuário para `minha confirmação` da autora.

**Limites/próxima fronteira:** nenhuma validação do main completo, áudio ou
efeitos externos; portas operacionais recusam execução e não fabricam receipts.
Qwen local `qwen3:4b-instruct` preservado, sem treino ou troca de configuração.
Não fechar F1: bloquear promessa não entrega por si uma explicação correta nem
reduz fallback. Próxima fronteira é autoria explicativa: preservar o agente da
condição e o objeto consultado, sem inferir incapacidade/acesso de ausência de
receipt; investigar reparo autoral verificável em vez de aceitar a resposta
errada ou ampliar fallbacks. Rede permanece pausada.

**Achado separado — contrato de categoria de confirmação do corpo:**
`test_confirmacao_operacional_contrato.py::test_todo_intent_documenta_como_confirma_resultado`
falha porque a lista fechada do teste não inclui `estado_firmware` (nem
`estado_owner`), acrescentados pela frente robótica em `capacidades.py` para
`CORPO_MOVER`/`CORPO_PARAR`/`CORPO_COMPANHIA`. Diff confirma adição paralela;
a asserção só enumera o catálogo, sem usar o novo guardião. Incompatibilidade
demonstrada, **não prova de defeito motor/firmware ou efeito físico falso**.
Não corrigida nem absorvida em F1; não ampliar a lista antes de auditar o
contrato e os consumidores desse novo tipo de evidência com a frente responsável.

### F1 — independência antes de condição posposta: GREEN de contrato/composição — 11/10/2026

Base reconferida: `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`,
worktree suja e trabalho paralelo preservados. Produção alterada nesta etapa
somente em `modalidade_turno.py`, na decisão de fronteira forte. Não alterados
classificação/autorização da condição, executores, receipts, autoria, catálogo,
composição raiz, rede neural ou configuração/modelo. Nenhum commit criado.

**Cadeia demonstrada:** o primeiro ato é uma ordem completa; o segundo contém
consequência seguida de condição pessoal. `_separar_primeira_fronteira_forte`
não reconhecia esse segundo ato: o ramo condicionado só aceitava condição no
início, e a tentativa seguinte usava a cláusula inteira protegida como evidência
de fronteira operacional. O veto era correto, mas servia à decisão errada:
ausência de autoridade da cláusula não significa ausência de um novo ato. Sem
corte, o classificador corretamente vetava o bloco inteiro recebido, incluindo
a primeira ordem indevidamente anexada. Primeira divergência: segmentação.

Normalização e domínio foram falsificados como explicações suficientes: matriz
de quatro domínios (apps/música/IoT/arquivos), três separadores fortes, três
qualificadores e dois modos de normalização reproduziu 72 REDs. Com o caso de
três atos e a prova instalada, **74 RED / 93 GREEN antes do candidato**.
Na composição instalada, quatro casos novos resultavam em zero chamadas ao
executor, com `segmentacao_absorveu_ato_independente`; 15 controles anteriores
continuavam GREEN. Gold não entra na interpretação: somente aferição da saída.

**Contrato/candidato mínimo:** após fronteira forte externa às citações, com
ordem completa à esquerda e consequência diretiva antes da condição à direita,
separar os atos. A segunda cláusula segue inteira para seu owner e permanece
condicionada/sem autorização. Não cortar vírgula ou coordenação ambígua por
esse mecanismo; condição solta sem consequência não prova independência.
Não remover a proteção útil nem criar parser de autorização no executor.
Princípio reutilizável: **evidência de fronteira discursiva ≠ autoridade do ato**.

Validação: **167 testes focados GREEN**; depois dos controles adicionais,
**492 testes GREEN em 11 módulos**, sem xfail ou RED removido. Propostas para
executar a ação condicionada em quatro domínios continuam rejeitadas, apesar
da autoridade agregada da primeira ordem. Protegidos: coordenação globalmente
condicionada, vírgula, condição sem consequência, literal citado, sequência
de três atos, consulta de significado, escopo/receipts e mudança de turno.

Artefatos novos, preservados com HEAD/worktree/hashes/fonte/frame/final:

- `resultados_testes/interpretacao_legada_20261011/condicao_posposta_baseline_v1.json`:
  19 controles, quatro REDs na primeira fronteira.
- `resultados_testes/interpretacao_legada_20261011/condicao_posposta_candidato_v1.json`:
  mesmos 19 controles GREEN de roteamento, fontes estáveis, quatro casos novos
  com uma chamada operacional autorizada, uma autoria e uma publicação, sem
  reentrada. As portas recusam efeitos; não há receipt de sucesso inventado.

**Limites:** composição instalada com portas isoladas, não main completo,
Qwen real, áudio ou efeito externo. GREEN do corte não encerra F1. A próxima
fronteira é o consumo/validação do contrato explicativo por ato. Contraprova
local após este patch: autora atual ainda aceita o texto injetado `A música só
será retomada quando você confirmar. Vou aguardar seu sinal.`, sem receipt ou
pendência materializada por esse caminho. Aceite estrutural não prova uma
explicação correta; a injeção não mede frequência real do Qwen. O snapshot da
etapa anterior protege vigência, mas ainda não é consumido como contrato
semântico da fala. Não aplicar mero prompt/contexto como solução (ablações
anteriores já falsificaram suficiência). Rede permanece pausada.

### F1 — contrato explicativo por ato: vínculo GREEN, semântica ainda aberta — 11/10/2026

Base: `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`; worktree suja
preservada. Produção alterada nesta etapa **somente** em `modalidade_turno.py`
e `contratos_turno.py`. Sem commit, treino, mudança de modelo/configuração,
executor, catálogo, autoria LLM, main, efeitos externos ou áudio.

Contrato implementado no owner já existente: a mesma decomposição que veta
execução de uma consulta publica o objeto textual, separado da pergunta inteira,
com coordenadas na **fonte estrutural**, não na utterance bruta. A fonte completa
acompanha as coordenadas mesmo quando o campo legado limita o texto a 300
caracteres. A condição é identificada como não verificada; sua identificação
não comprova pendência, efeito, capacidade ou acesso ao alvo. Nenhuma pendência
de outro owner é consultada/inventada/cancelada por esta projeção.

`ContratoExplicativoAto` congela relação, objeto, modalidade, natureza e motivo
de cada ato não autorizado. `ComplementoConversacionalTurno` passa a carregar
esses snapshots. O orquestrador existente já compara o complemento antes/depois
da autoria: agora uma alteração semântica do frame, mesmo sem trocar texto/id,
impede publicar a resposta vinculada ao frame anterior. Não é novo parser nem
prova criptográfica de origem, tampouco verificação da semântica da fala gerada.

RED antes do candidato: **20 falhas na fronteira de projeção/revalidação**, 34
controles GREEN e um RED anterior de segmentação. Candidato: 56 testes focados
GREEN. Regressão de 11 módulos: **406 GREEN / 1 RED** (preservado, sem xfail).
Cobrem consulta em apps, música, IoT e arquivos; literal com marcador interno;
condição; schema/offsets adulterados; fonte longa; snapshot não mutável pela
serialização; mudança de natureza durante autoria; pendência alheia preservada.

Sonda de composição instalada (portas isoladas): 15 controles com roteamento
estrutural GREEN e fontes estáveis. Artefato final do candidato:
`resultados_testes/interpretacao_legada_20261011/contrato_explicativo_composicao_v2.json`.
`v1` preserva a execução anterior à simplificação tipada do loop de projeção.
Não há chamada Qwen real nesta etapa: a autora ainda não consome o novo contrato
para validar a explicação. Os REDs semânticos das ablações anteriores continuam
abertos. Não converter o GREEN de vínculo em acerto semântico ou raiz encerrada.

**RED encontrado, separado:** `Abre a calculadora; liga a luz somente quando eu
confirmar` resulta em um só ato condicionado, sem autoridade para abrir a
calculadora. A mesma junção ocorre com ponto ou música e sem normalizador;
quando a condição inicia o segundo ato, a separação funciona. Falsificadas
normalização e domínio IoT como explicações suficientes. Primeira divergência:
segmentação, antes de projeção/autoria. Teste conservado em
`scripts/tests/test_vinculo_condicao_acao.py::test_condicao_posposta_apos_fronteira_independente_nao_absorve_primeiro_ato`.
Não mexer em proteção condicional para fazer passar sem provar a fronteira de
independência; não liberar a consequência condicionada. Próxima investigação
prioritária é esse RED anterior; depois, consumo/validação explicativa pelo
owner compartilhado e nova prova Qwen isolada. F1 permanece aberta; rede pausada.

### F1 — duas hipóteses falsificadas na autoria mista, antes de novo patch — 11/10/2026

Base conferida: `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`,
worktree suja preservada. **Nenhuma produção alterada nesta etapa.** Alterados
somente a sonda de prioridade mista, seu teste e este registro/mapa. Rede pausada,
sem treino, mudança de modelo/configuração, commit, main, efeitos ou áudio.

Inventário confirma perda no transporte da autoria: segmentos do interpretador
já têm `mencao_operacional`/`condicao_nao_verificada`, modalidade, motivo e
autoridade por ato; a autora instalada recebe só texto restante, receipts e
avisos. `MapaHabilidadesRuntime.evidencia_conversacional` é o owner existente
de capacidades locais, mas não está nesse pedido. Isso demonstra informação
omitida; **não demonstra que sua reposição resolveria a semântica**.

Ablações somente no subprocesso de diagnóstico, com `PedidoModelo` substituído
em memória. Prioridade, execução recusada, publicação, formato, prompt do sistema,
modelo, parâmetros e guardas permanecem. Gold `esperados/propostos` não entra
na intervenção. Seis casos, controle/intervenção, duas repetições em ordem
alternada/invertida por coleta; fonte/HTTP/bruto/final/hash preservados. Projeção
do catálogo consultada por texto restante, vinculada ao turno, sem afirmar
acesso ao alvo. Não afirmar que o sistema inteiro está sem pendências.

1. `resultados_testes/interpretacao_legada_20261011/projecao_mista_qwen_ablacao_v1.json`:
   **24/24 HTTP 200, aceites estruturais e uma publicação**, sem reentrada.
   Intervenção acrescenta atos canônicos, capacidade documentada e o fato de
   que este complemento não cria pendência. As seis autorias condicionais da
   intervenção ainda falam em confirmar/aguardar sinal; nos pares calculadora
   e arquivo continuam surgindo negativas falsas de acesso/capacidade, mesmo
   com documentação disponível. Explicações podem confundir a expressão citada
   com a pergunta inteira. **Falsificada reposição de contexto como solução
   suficiente.** Ganho eventual em uma resposta não autoriza aplicar projeção.
2. `resultados_testes/interpretacao_legada_20261011/avisos_mistos_qwen_ablacao_v1.json`:
   **24/24 HTTP 200, 23 aceites estruturais**; um trecho alegando janela aberta
   é recusado pelo guardião, sem ocultar o bruto. Intervenção retira somente
   `avisos_obrigatorios` do pedido ao modelo; host continua incluindo o aviso
   real na publicação. Confirmação fictícia persiste; negativas de capacidade
   aparecem inclusive justificadas por ser "amiga digital". **Falsificado aviso
   como explicação única/retirada do aviso como solução suficiente.** Uma
   instrução sobre novo pedido surge numa amostra, não demonstra estabilidade.

Total: **48 chamadas reais**, não holdout, fontes estáveis em cada coleta, mutex
respeitado/liberado. Nenhuma chamada reentra no executor; nenhuma porta emite
receipt de sucesso. Revisão técnica dos brutos é diagnóstica, não aprovação de
Pedro nem aferição automática universal do português. Saída aceita pelas guardas
atuais não equivale a resposta semanticamente correta. Não converter números
estruturais em taxa de acerto de conversa.

Primeira fronteira semântica ainda RED: autora produz inferência incompatível
com o ato; validador atual permite parte dessas inferências. Ausência de fatos
contribui ao risco, mas não foi provada como causa suficiente nem exclusiva.
Próximo candidato deve aproveitar owners existentes para um contrato explicativo
por ato: preservar expressão objeto da pergunta separada da pergunta inteira;
distinguir condição declarada, autorização atual, pendência materializada e
receipt; manter capacidade catalogada separada de acesso ao alvo. A autora dá
forma à explicação, não decide novamente essas relações. Validar o mesmo
contrato antes da publicação; não ampliar listas de frases ou exceções de alvo.
Ainda necessário criar RED desse contrato antes de patch e testar consulta,
condição, pendência realmente existente, indisponibilidade real e resultado
parcial. Não usar a condição como agendamento implícito.

Controle local da primeira ablação: `projecao_mista_controle_local_v1.json`.
Regressão da instrumentação/contratos existentes: **58 GREEN**. Testes conferem
que só a intervenção muda o payload, catálogo/atos não concedem autorização,
aviso não some da entrega e intervenções diferentes não podem ser misturadas.
Não são prova de GREEN semântico. RED paralelo do catálogo corporal registrado
abaixo não foi alterado. `git diff --check` sem erros. F1 permanece aberta.

### F1 — candidato de cobertura mista: rota protegida, semântica ainda aberta — 11/10/2026

Base `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`; worktree suja
e alterações paralelas preservadas. Candidato aplicado em produção, **não é
encerramento nem liberação validada**. Produção desta investigação:
`cognicao/contratos_turno.py`, `autonomia/resposta_ia_runtime.py`,
`personalidade/orquestrador_fala_runtime.py`, `personalidade/confirmacao_llm.py`,
`cognicao/guardiao_alegacoes.py` e uma injeção de serviço em `laylay.py`.
Não alterar executores, classificação operacional, catálogo, modelo/configuração,
treino ou estado pessoal. Nenhum commit criado; neural permanece pausada.

Contrato aplicado: projeção imutável dos atos conversacionais restantes do
frame canônico, vinculada à fala original e ao ID do turno; prioridade mantém
interpretação/execução. O lote existente adia somente apresentação. A conversa
restante não reentra no dispatcher. Uma autoria recebe receipts independentes
e conversa separada; geração sem tools, publicação única e revalidação da
cobertura antes/depois da autoria. Turno novo ou cobertura adulterada retêm
entrega. Falta de receipt não vira sucesso; falha de autoria comunica que a parte
conversacional não foi respondida. Revisão intra-turno continua fora do candidato.

Primeiro formato misto exigia fala inteira mais cópias de cada escopo. Testes
injetados ficaram verdes, mas Qwen real falsificou interoperabilidade:
`prioridade_mista_qwen_real_v1.json`, **0/6 aceitos**, um timeout e cinco erros de
estrutura/cópia. Não afrouxar vínculo factual. Substituído apenas o formato
misto por `{"trechos":[...],"conversa":"..."}`: autora escreve cada trecho uma
vez; host vincula ordem aos receipts e insere avisos imutáveis. Saída desconhecida,
lista errada, troca de alvo, promoção de falha, número emprestado da conversa,
estado sem leitura ou promessa detectada são recusados. Contrato operacional
anterior permanece. Testes de cópia redundante foram adaptados à representação
nova, não à retirada de validação factual.

Guardião compartilhado também tinha REDs legítimos: estado "pausada/parado" e
"vou avisar depois/mais tarde" escapavam. Padrões canônicos ampliados, com
controles de incerteza local e explicação conceitual. Isto não prova cobertura
irrestrita do português. Timeout misto de 15s ainda era reduzido a 8s pela classe
rápida: RED com `OrcamentoLLMTurnoRuntime` real demonstrou a redução. Chamador
misto passa classe normal e teto solicitado de 15s; sem elevar limites globais,
sem alterar a classe/timeout da paráfrase só operacional.

Provas instaladas com efeitos recusados, armazenamento temporário, voz capturada
e somente HTTP local permitido; não são main nem efeito físico:

- `prioridade_mista_pos_candidato_v1.json`: painel injetado de quinze entradas,
  seis mistos e controles. Uma porta operacional e uma autoria/publicação por
  misto, sem reentrada; consulta/condição isoladas sem executor; controles só
  operacionais preservados. Fontes estáveis.
- `prioridade_mista_qwen_real_v2.json`: cinco aceites estruturais em seis; primeiro
  ainda timeout de 8s. Não confundir aceite com qualidade.
- `prioridade_mista_qwen_real_v3.json`: **6/6 HTTP 200 e aceites estruturais**, uma
  porta, uma autoria e um texto final por entrada, sem reentrada. Fontes estáveis;
  modelo persistido `qwen3:4b-instruct`; mutex respeitado e liberado. Brutos,
  payloads, tempos e hashes preservados. Não é holdout.

**RED semântico preservado:** leitura dos brutos v3 mostra condição futura
apresentada como confirmação aguardada ("só acontecerá quando ... confirmar"),
falta de acesso a arquivos inventada, aviso duplicado e "pode abrir" explicado
como "abriu". Mesmo após instruções explícitas, esse comportamento persiste.
Fase `tratado_prioritario_misto` mede autoria aceita/publicada pelas guardas
atuais, não correção semântica. Não promover 6/6 estrutural a GREEN de conversa.

Próxima fronteira causal: a autora recebe texto conversacional, mas ainda precisa
inventar sua explicação sobre autoridade/capacidade. Estudar projeção factual
canônica de modalidade/condição e capacidade disponível para a autoria, sem
novo parser no executor nem nova decisão da LLM. Confirmar ausência de pendência
deste ato não é afirmar inexistência de toda pendência do sistema. Congelar os
brutos como contraexemplos; depois testar composição, geração real com receipts
qualificados, main e entrega. Ainda não há prova de efeitos externos ou áudio.

Regressão final: **512 GREEN / 1 RED**, dezessete módulos. RED separado em
`test_todo_intent_documenta_como_confirma_resultado`: catálogo paralelo do corpo
usa `estado_firmware`/`estado_owner`, teste enumera somente valores anteriores.
Contraprova substituindo somente o catálogo por HEAD em memória fica GREEN.
Catálogo e teste preservados; isto não comprova defeito físico nem autoriza
mudar o trabalho paralelo. `git diff --check` sem erros. F1 continua aberta.

### F1 — prioridade parcial não comprova conclusão integral — 11/10/2026

Base `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`; worktree suja e
trabalhos paralelos preservados. **Nenhuma produção alterada nesta fronteira.**
Sonda/teste: `scripts/analises/sonda_prioridade_turnos_mistos.py` e
`scripts/tests/test_prioridade_turnos_mistos_composicao.py`. Rede neural pausada;
sem treino, configuração/modelo, efeitos externos, voz, main ou commit.
Portas de executor recusam, modelo injetado, rede proibida e persistências
pessoais redirecionadas a temporários. Isto é composição instalada, não main.

Direção corrigida: coletas anteriores forçavam a rota LLM; produção chama a
prioridade antes dela. Omissão no replay do Qwen não prova perda de execução
nesse atalho. Cadeia demonstrada: leitura de atos correta → recorte autorizado
→ candidato canônico com operação/alvo corretos → chamada única à porta →
prioridade retorna tratado → `RespostaIARuntime` encerra antes da conversa.
Primeira fronteira RED de cobertura: tratamento de um recorte é tomado como
conclusão do turno inteiro. Prioridade informa cobertura; coordenador da resposta
governa encerramento. O executor não é dono da cobertura conversacional.

Artefato `resultados_testes/interpretacao_legada_20261011/prioridade_mista_v4_controles.json`:
15 entradas, fontes estáveis. Seis mistos de mídia/app/IoT/lookup chegam uma vez
à porta com o candidato correto, sem alcançar a conversa. Consulta e condição
isoladas chegam à conversa sem executor; seis controles retirando o segundo
ato preservam o atalho operacional; cadeia recusada para na primeira etapa e
comunica falha. Seleção: **6 RED de cobertura / 16 testes GREEN**, incluindo
seis contraprovas. Captura não comprova resposta correta, efeito ou áudio.

Sétimo RED inicial era instrumentação: `ContextoIntencaoRuntime.estado_getter`
repõe o agrupador instalado sobre o namespace. A sonda não capturava sua porta
final e supunha silêncio. Capturar `OrquestradorFalaRuntime.falar`, sem remover
o lote, confirma o aviso de falha. Expectativa mantida, porta observada corrigida.
Artefatos anteriores v1/v2/v3 preservados, sem sobrescrita.

Falsificado Qwen/formato como causa desses seis encerramentos: nem é chamado.
Falsificada perda inicial de autorização/operação/alvo: candidatos corretos e
controles só operacionais. Contraprova somente em memória rejeita retornar
`False` após a prioridade: modelo injetado repete a operação capturada (não
usa gold) e pipeline admite segunda invocação da mesma porta. Artefato
`prioridade_mista_contraprova_retorno_v2.json`; também afeta controles operacionais.
**Não comprova dois efeitos**: ambas as portas recusam, sem receipt de sucesso.
Chegar à LLM não basta para GREEN; reentrar no pipeline completo é inseguro.

Inventário de entrega: lote canônico adia apresentação, preserva receipts e
recusa entrega em turno novo. Seu autor `personalizar_confirmacao_composta_llm`
aceita só trechos vinculados a receipts, proíbe perguntas e rejeita conteúdo
residual. Guarda útil, não bug a remover. Conceito não deve receber receipt
fictício nem ser liberado como resíduo sem validação. Dispatcher abre lote só
para mais de um comando, não para um comando acompanhado de pergunta.

Contrato do próximo candidato, ainda não implementado:

1. Cobertura explícita vinculada ao mesmo turno/atos: não tratado, operacional
   tratado, conclusão integral. Não confundir tratamento, executor, receipt e fala.
2. Somente atos restantes chegam ao owner conversacional, em porta sem execução;
   manter ocorrência/fala original e não reenviar operação já encaminhada.
3. Reusar lote/receipts antes de uma autoria/publicação. Trechos operacionais
   continuam conferidos por receipt; conversa tem escopo próprio, sem alegações
   de efeito ou promessas de pendência não materializada.
4. Condição futura não vira efeito/agendamento/pendência implicitamente.
   Indeterminação, falha parcial, ausência de receipt e turno novo: fail-closed.
   Falha conversacional tem aviso, não falsa conclusão integral.
5. REDs de uma publicação/nenhuma reentrada, sucesso/falha/incerto/idempotência,
   condição, resultado tardio e autoria indisponível; depois composição e main.

Regressão vizinha: **197 GREEN**, oito módulos de contrato, escopo/composição de
autorização, cadeia/contexto vivo, confirmação composta/composição e transporte.
Não encerra F1 nem comprova main, voz real, efeitos ou liberação neural.

### F1 — ablação do contrato de proposta: formato melhora, decisão continua instável — 11/10/2026

Base `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`; worktree suja
preservada. **Nenhuma produção alterada nesta investigação.** Novos arquivos:
`scripts/analises/sonda_contrato_proposta_legada.py` e seu teste. Sem treino,
mudança de modelo/configuração, ativação neural, executor, persistência pessoal,
voz ou commit. O mutex de produção foi respeitado e liberado ao final.

Inventário: `capacidades.py` registra nomes, domínio, disponibilidade,
autorização e evidência, mas não a representação dos parâmetros. O contexto
de habilidades enviado informa capacidades narrativas. O dispatcher aceita
`intent` + `params` ou seus aliases documentados; propostas como
`abrir_calculadora`, `pausar_musica` e campos `sucesso` surgem antes dele.
Não adicionar aliases por frase nem fazer o dispatcher inventar o alvo.

Experimento pós-compactação, com payloads congelados da coleta anterior:
seis entradas (cinco operacionais, uma consulta isolada), três variantes,
duas repetições em ordem alternada/invertida. Modelo persistido
`qwen3:4b-instruct`, temperatura, orçamento, base, fala e contexto originais
mantidos. Comparar controle sem alteração, nomes registrados por domínios
documentais, nomes + exemplos `intent/params` derivados do adaptador existente.
Gold não participa da construção da requisição. Exemplos têm placeholders,
não Calculadora/Bloco de Notas nem alvos esperados. Cobertura parcial e explícita;
não são um novo catálogo nem schema de todos os executores.

Primeiro controle local surpreendeu: mapa documental sem `apps_getter` omitia
sistema quando só havia o nome Calculadora. Corrigida a instrumentação, não a
produção: obter o literal único `APPS_MAP` do composition root por AST sem
executar/importar `laylay.py`, e fornecer ao mapa existente. Não inventar lista
paralela nem presumir aplicativo instalado. Fonte incluída nos hashes.

Artefato `resultados_testes/interpretacao_legada_20261011/ablacao_contrato_proposta_v1.json`:
**36/36 HTTP 200**, fontes estáveis, payloads e respostas brutas preservados.
Controle: 11/12 JSON válidos, 2/12 propostas completas equivalentes ao esperado;
nomes: 12/12 JSON, 2/12 equivalentes; parâmetros: 12/12 JSON, 7/12 equivalentes.
Os dois acertos do controle/nomes são consulta sem comandos. Nas dez chamadas
operacionais, variante parâmetros acerta **5/10**, não 7/10. Uma geração do
controle acaba em `length`, não `stop`; não contada como acerto.
Representações emitidas normalizáveis pelo dispatcher: controle **0/12 comandos**,
nomes **0/13**, parâmetros **9/9**. Isso prova interoperabilidade estrutural,
nunca autorização, parâmetros adequados à intenção, efeito ou fala correta.

Falsificada a incapacidade geral do Qwen de emitir o formato canônico: ele o
emitiu em todas as nove propostas da variante estrutural, inclusive o pedido
conjunto de app+mídia nas duas repetições. Listar apenas nomes não foi suficiente
neste painel. Ainda abertas: leitura da moldura inteira em comando+consulta,
condição futura contaminando o pedido atual, omissão e afirmações sem receipt.
Em `dominios_distintos_condicao`, uma repetição omite tudo e outra propõe APP_OPEN
mais MEDIA_CONTROL condicionado: **nome/formato corretos não tornam o segundo
comando autorizado**. Em app+consulta, uma repetição correta e outra vazia.
Mesmo respostas com comando correto dizem "abri", "pausada" ou inventam posição
na tela; rascunhos não publicados. Não agrupar invenção de estado como resolvida.

Limite causal: variante parâmetros acrescenta envelope/exemplos **e** explicita
separação proposta/receipt e pedido/condição. O ganho não isola o efeito dos
parâmetros sozinho. Painel diagnóstico conhecido, não holdout; replay HTTP não
atravessa preparador instalado, validador, dispatcher nem main. Não declarar
eficiência global ou liberação. Testes de instrumentação/guarda HTTP/escopo e
transporte: **113 GREEN** inicialmente. Seleção final com composição instalada:
**127 GREEN**, cinco módulos, 4,28 s; após liberar o mutex da própria ablação.

Próxima hipótese arquitetural, **não implementada nem encerrada**: reaproveitar
a resolução canônica dos atos já entendidos, em vez de delegar ao modelo uma
segunda decisão de operação/alvo/autoridade. A coleta instalada anterior
`propostas_mistas_pos_vinculo_final.json` preserva
`resolucoes_canonicas_autorizadas`: seis mistos já resolvem mídia, app, IoT e
lookup de arquivo corretos; consultas/condições isoladas vazias, composto
legítimo com dois pedidos. Hashes atuais de detector, escopo e decisão conferidos
iguais aos daquela coleta (verificação, não novo runtime).
Fronteira a provar: resolução por ato → proposta tipada vigente → executor →
receipts independentes → uma autoria/publicação. Reusar owners e guardas,
preservar discussão/condição sem efeito, indeterminação fail-closed e falhas
parciais. Não preencher comandos do modelo com gold, não extrair permissão de
seu texto e não acrescentar uma nova tabela privada. F1 permanece aberta.

### F1 — base canônica atômica na compactação, mesmo com prefixo — 11/10/2026

Base `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, worktree suja e
alterações paralelas preservadas. Antes do candidato, `llm_http.py` não tinha diff.
Única produção alterada nesta entrega: `mente_laylay/integracao/llm_http.py`,
o cálculo do limite protegido em `compactar_payload_llm_local` (8 linhas novas,
5 substituídas). Sem mudança de personalidade, parser, executor, validador,
modelo, configuração, neural ou persistência pessoal. Nenhum commit criado.

Contrato: prefixo legítimo + bloco canônico completo do prompt são atômicos;
orçamento pode cortar somente o sufixo/contexto opcional. Reconhecer a posição
do bloco canônico completo, em vez de exigir início no caractere zero. Aplica-se
às bases normal e rápida, sem exceção por domínio/frase. Não desloca papéis nem
concede autoridade; bases em dados user continuam dados. Prompt desconhecido
não recebe proteção por mera semelhança textual. JSON schema e conteúdo visual
mantêm os caminhos existentes, sem compactação desses contratos estruturados.

RED antes: **14 falhas / 38 controles GREEN** no módulo de transporte. Onze
falhas paramétricas de integridade com bases/prefixos/orçamentos distintos e
três reproduções com `ContextoPromptRuntime` real em mídia, app e arquivos.
Primeira asserção RED é perda da base depois da compactação, antes do modelo.
Alguns prefixos curtos/orçamentos grandes já passavam por caber no corte; não
foram tratados como RED nem alterados para fabricar o diagnóstico.

GREEN após: 159 testes iniciais de transporte/orçamento/multimodalidade/emoção.
Quatro controles adicionais protegem retry HTTP 400, papéis user/system,
prompt desconhecido e schema negociado. Regressão final, **19 módulos**:
**385 GREEN / 1 RED**, 21,27 s. RED restante é a expectativa literal
`test_prompt_novo_contem_so_identidade_contexto_e_contrato` pela frase
"doce sem ser mole, firme sem ser arrogante", ausente na personalidade da
worktree. Contraprova substituindo SOMENTE o compactador pelo HEAD em memória
reproduz o mesmo RED; não pertence ao candidato e não foi enfraquecido/alterado.
Na primeira rodada ampla houve também colisão com o mutex mantido pela própria
sonda real simultânea; após encerrá-la, composição passa isolada e na seleção
completa. Não é sessão do usuário encerrada nem falha de produção corrigida.

Coleta real repetida no mesmo Qwen persistido `qwen3:4b-instruct`, mesmas nove
entradas, mesma instrumentação da rota LLM sem atalho prioritário. **9/9 HTTP
200**, todos `finish_reason=stop`, fontes estáveis; artefato
`resultados_testes/interpretacao_legada_20261011/geracao_mista_pos_contrato_v1.json`.
Hashes agora incluem também compactador, preparação de payload e bases de
personalidade, além dos componentes/seleção anteriores. Nos cinco casos normais
mistos afetados, base inteira chega ao HTTP; bases normal/rápida ficam intactas
nos controles. JSON bruto parseável passa de **4/9 para 9/9 neste painel**.
Esse é benefício estrutural observado, NÃO ganho de execução/qualidade geral.

Os **sete casos com pedidos sem proposta executável continuam sem solução**.
Dois mistos agora emitem ações malformadas e são recusados pelo vínculo;
um controle puramente operacional ainda contém nomes inventados, sem chamada
de executor. **Zero comandos divergentes chegaram à porta executora**.
Continuam rascunhos com sucesso inventado e negação de capacidade disponível;
não foram publicados nem pronunciados. Omissão/formato operacional incorreto
não é falso bloqueio de uma proposta equivalente. Não usar JSON válido como
prova de intenção, parâmetros, permissão, efeito ou fala correta.

Próxima fronteira: contrato de proposta executável entre catálogo canônico,
preparação e geração; investigar por que a descrição narrativa/JSON com lista
vazia não informa suficientemente nomes/parâmetros válidos ao modelo. Separar
proposta de receipt, sem aliases de frase especiais nem autorização da LLM.
Possível causa compartilhada com confirmações inventadas ainda exige prova;
não consolidar automaticamente esses sintomas. F1 permanece aberta.
Prova atual é GREEN estrutural no caminho instalado com geração real/efeitos
isolados, NÃO sessão main, entrega audível, efeito físico nem holdout.
`git diff --check` sem erros; avisos CRLF paralelos preservados.

### F1 — geração real revela perda do contrato antes do validador — 11/10/2026

Base preservada: `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`.
Nesta entrega nenhuma produção/configuração/modelo/dataset foi alterada.
Reutilizado isolamento da sonda anterior; novo instrumento
`scripts/analises/sonda_escopo_geracao_real.py` e testes da medição/guarda HTTP.
Neural desligada somente no subprocesso; configuração pessoal continua shadow.
Não foi aberta sessão main nem interrompida sessão do usuário.

Prova: nove casos pelo `RespostaIARuntime` instalado, preparador de prompt,
modelo/transporte local Qwen `qwen3:4b-instruct`, pós-processamento e validador
reais. O atalho prioritário foi omitido deliberadamente para alcançar a rota
LLM; dispatcher real recebe porta executora que retorna False, sem efeito ou
receipt fabricado. Finalização é observada, não publicada; voz/memória pessoal
e treino não recebem os resultados. Não é prova do fluxo main/default inteiro.
Entradas, pedidos, respostas HTTP completas, saídas preparadas, validações,
escopos, plano, chamadas da porta e hashes ficam no artefato congelado
`resultados_testes/interpretacao_legada_20261011/geracao_mista_real_v2.json`.

Resultado: **9/9 gerações principais com transporte HTTP 200**, fontes estáveis.
**Sete casos não forneceram os comandos esperados** (seis mistos e um conjunto
puramente operacional). Nos seis mistos, o rascunho não tinha comandos; portanto
esta coleta NÃO demonstra falso bloqueio do vínculo, nem seu sucesso diante de
propostas positivas reais. Vários rascunhos dizem "abri"/"música pausada" sem
receipt; não são falas finais entregues, pois a finalização está isolada.
Dois controles sem autorização conservaram comandos vazios. No controle
puramente operacional surgiram ações não canônicas `abrir_calculadora` e
`pausar_musica`, com `resultado=executado` inventado. O filtro legado aceita o
envelope, mas o dispatcher não chama executor: **zero chamadas indevidas**.
O contador histórico `casos_com_admissoes_indevidas=1` do artefato mede divergência
representacional nesse controle, NÃO execução não autorizada de um ato vetado.
Instrumento atual distingue explicitamente divergência na porta do executor.

Primeira fronteira demonstrada para a perda estrutural: o pedido contém a base
canônica de 4.973 caracteres, precedida de instrução do turno misto (282 chars).
`compactar_payload_llm_local` reconhece a base protegida somente por `startswith`.
O prefixo faz `tamanho_base=0`; o corte a 4.200 caracteres remove o JSON no fim
da base ANTES de chegar ao modelo. O HTTP bruto confirma que "Retorne somente
JSON" estava no pedido, mas desapareceu no transporte. Mesmo payload, retirando
apenas o prefixo em memória, preserva a base inteira e a instrução JSON.
Não foi aplicada contraprova sobre produção nem sobrescrito artefato.

Hipóteses concorrentes: incapacidade absoluta do Qwen de produzir JSON é
falsificada pelos controles que retornam JSON; pós-processador apagando uma
proposta válida não explica os rascunhos brutos já sem comandos. A perda na
compactação está provada por código/HTTP/controle, mas ainda não prova que sua
correção resolverá toda omissão, ação não canônica ou confirmação inventada.
Ausência de formato negociado e catálogo de ação suficiente precisam ser
avaliados separadamente, sem mudar modelo nem afrouxar autorização.

Coleta v1 preservada como INVÁLIDA: zero transportes, erro na assinatura method
da guarda HTTP; campo `modelo_real_consultado=True` naquela versão era incorreto.
Não usar v1 para métricas da Laylay. Guarda corrigida/testada para keywords de
requests; instrumento atual só marca consulta real após HTTP 200 observado.
Regressão relevante anterior à última melhoria da instrumentação: 166 GREEN;
medição/contratos/composição finais: 63 GREEN. `git diff --check` sem erros;
avisos CRLF das alterações paralelas preservados. Nenhum commit criado.

Próxima fronteira da mesma investigação F1: RED canônico de integridade do
contrato principal quando o owner antepõe instruções legítimas; correção mínima
no compactador, com controles de orçamento, par system/user, dados não confiáveis,
JSON/schema e repetição da coleta real. Não adicionar parser de frase nem
retomar a neural. F1 não encerrada; main, voz e efeitos continuam sem prova.

### F1 — candidato de vínculo proposta→ato autorizado — 11/10/2026

Base `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`; worktree suja
e alterações paralelas preservadas. Nenhum commit, modelo, dataset, configuração
ou persistência pessoal alterado. Neural permanece em `shadow` na configuração;
desenvolvimento/treino pausado conforme pedido de Pedro.

Contrato aplicado no owner existente `decisao_turno`: se a leitura contém ato
explicitamente não autorizado ou vetado, cada proposta precisa corresponder a
um ato autorizado do mesmo frame/turno. Não emprestar permissão, operação,
alvo, destino ou parâmetros de outro ato. Um ato autoriza uma ocorrência da
proposta, não duplicações extras; duas ordens explícitas iguais têm dois escopos.
Pergunta social sem veto sticky também não herda a permissão de uma ordem.

`escopo_autorizacao.py` mantém contratos imutáveis de ID/índice/texto/pedido.
Recebe o resolver canônico, sem regex de intenção/entidade nem parser privado.
Só resolve atos positivos, sem ambiguidade/contexto não resolvido; indisponibilidade
ou exceção produz rejeição explícita no validador, não autoridade presumida.
Frame isolado vai ao detector existente por argumento opcional; a agenda
recursiva conserva esse frame. A integração em `laylay.py` é uma linha de injeção,
sem política de domínio. Procedência/permissão do turno são conferidas antes de
resolver; as guardas de vigência/publicação continuam responsáveis pela admissão
posterior. O resultado do validador registra escopos locais e atos vinculados;
isso não é memória factual, receipt, prova de efeito nem licença reutilizável.

Identidade operacional usa o normalizador JSON existente. No modo opt-in de
comparação, aliases redundantes do envelope flat são compactados; aliases
conflitantes não são apagados para fingir equivalência. Aplicativo Windows admite
diferença de caixa, destino omitido equivale a `pc_a`; conteúdo, URLs e demais
parâmetros conservam tipagem/valor. Parâmetros extras, outro destino ou operação
são recusados. O despacho normal não mudou o formato dos parâmetros. Para atos
mistos, a restrição agregada do retrato não substitui o vínculo por ato: arquivo
apenas mencionado numa pergunta não pode vetar um aplicativo realmente pedido.

RED antes do candidato: **quatro regressões canônicas RED** em mídia, app, IoT
e arquivos, além dos seis REDs instalados documentados na auditoria anterior.
Inspeção dos resolvers falsificou uma premissa da fixture de arquivo: sem
localização/receipt, abertura começa por `FILE_SEARCH` com abertura exata pedida,
não por `FILE_OPEN_RESULT` com alvo solto. Proposta/expectativa positivas foram
ajustadas com essa justificativa; exclusão indevida continua negativa. Os
artefatos antigos preservam a expectativa histórica, não foram reescritos.

Contraprova após candidato: executou **somente o filtro de `decisao_turno` do
HEAD em memória**, sem o vínculo, conservando o restante da worktree e a mesma
fixture corrigida de arquivo. Retornam **seis REDs / quatro controles GREEN**,
mais dois pipelines com escopo reintroduzido. Não é replay integral do HEAD.
Artefato: `resultados_testes/interpretacao_legada_20261011/propostas_mistas_contraprova_head_v1.json`.

GREEN atual: **dez cenários de admissão/dispatcher**, incluindo os seis defeitos
e os quatro controles; **três pipelines instalados** de `RespostaIARuntime`,
writer, validador, dispatcher e finalizador reais, com propostas/modelos/efeitos/
voz isolados. Só o comando permitido é publicado e entregue à porta; falha
isolada do executor termina em `falha_execucao`, com conclusão textual na porta
de fala, sem fabricar confirmação. Inclui JSON canônico e flat. Um teste inicial
esperava bool da API `processar`, mas ela retorna None por contrato; corrigida
a expectativa para publicação/fase/fala observável, sem relaxar escopo/receipt.

**47 testes focados/composição GREEN**; seleção ampla de 33 módulos:
**887 testes / 32 subtestes GREEN**, 31,60 s (antes do último controle adicional
de proposta obsoleta, que integra os 47 focados). Regressões de decisão, vigência,
publicação, autoria/procedência, comandos compostos, arquivos, mídia e condições.
`git diff --check` sem erros; avisos CRLF paralelos preservados. Artefato final,
fontes e hashes conferidos: `resultados_testes/interpretacao_legada_20261011/propostas_mistas_pos_vinculo_final.json`.
O controle artificial com lista de intents mas SEM escopo agora recusa pedidos
positivos por falta de prova; seu contador de divergências não é RED do caminho
instalado com vínculo e não deve ser comparado como acurácia.

Produção desta entrega: novo `cognicao/escopo_autorizacao.py`,
`cognicao/decisao_turno.py`, três alterações de passagem de frame em
`autonomia/orquestrador_deterministico.py`, projeção opt-in em
`autonomia/dispatcher_comandos_json.py` e uma linha de composição em `laylay.py`.
Alterações anteriores de corpo nesses arquivos não pertencem ao candidato.
Sem mudança de executor, voz, UI, pós-processamento, modalidade ou personalidade.

Limites: adoção na mistura de atos autorizados/não autorizados, não auditoria
universal de parâmetros de toda ordem puramente operacional. A compatibilidade
é conservadora quando o resolver não resolve ou representações não equivalem;
não relaxar por intenção parecida nem usar a LLM como fonte da permissão.
Faltam sessão main com geração real, efeitos externos e entrega audível; os
modelos desta prova são propostas adversariais injetadas, não Qwen consultado.
Não encerrar F1 globalmente, nem interpretar esses verdes como prontidão de toda
Laylay. Próxima fronteira: validar comandos mistos naturais com geração real e
auditar casos legítimos indeterminados sem retirar o vínculo de autoridade.

### F1 — auditoria do escopo nas propostas JSON mistas — 11/10/2026

Base preservada: `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`,
worktree suja. Nenhuma produção, configuração, modelo ou dataset alterado
nesta entrega. Desenvolvimento neural continua pausado; configuração segue
`LAYLAY_NEURAL_MODE=shadow`. Instrumento e cinco testes da medição adicionados.

**Reproduzido na composição instalada: seis REDs / quatro controles GREEN.**
`scripts/analises/sonda_escopo_propostas_mistas.py` importa `laylay` em processo
isolado, usa planner/estado reais, o validador moderno instalado com proposta
tipada e procedência vinculada, e o dispatcher instalado. Rede proibida,
persistência redirecionada, modelo/voz/main ausentes; executor substituído por
captura que devolve False, sem receipt fabricado. Fontes antes/depois estáveis.
Artefato final: `resultados_testes/interpretacao_legada_20261011/propostas_mistas_v3.json`;
v1/v2 preservados como intermediários. As expectativas de escopo são autorais,
independentes das propostas e da saída; não é holdout nem avaliação de frequência
de alucinação de um modelo real. Saída 1 registra o contrato RED ainda aberto.

Cadeia comprovada: a modalidade autoriza só o ato imediato e veta a consulta
ou condição → o validador `filtrar_comandos_pelo_turno` usa autorização agregada
e restrição opcional por intent → aceita também a proposta correspondente ao
ato vetado → o dispatcher entrega ambos à porta isolada do executor.
Primeira fronteira RED obrigatória de admissão: **falta de vínculo entre cada
proposta e o ato autorizado**, no owner `decisao_turno`. O filtro preliminar
também deixa a lista passar em turnos positivos, mas não é o último porteiro;
não atribuir o defeito somente a ele nem criar mais um parser nessa camada.

Contraprovas: (1) modalidade/recorte corretos nos seis casos falsificam erro
de classificação como causa necessária deste RED; (2) procedência e ocorrência
vinculadas falsificam troca de turno como causa necessária; (3) pergunta e
condição isoladas são bloqueadas, conjunto legítimo admitido e guarda de
vigência falsa impede chamadas: não é falha geral do executor ou do veto.
(4) Em cópia do retrato, até uma lista ideal dos intents pedidos deixa três
REDs: pause/play, Calculadora/Bloco de Notas e luz/ventilador compartilham
intent. Lista por domínio/intenção não substitui operação, alvo e parâmetros.
Arquivos também reproduzem: abertura pedida não autoriza exclusão mencionada.

Contrato a implementar, sem exceção por habilidade: **cada candidato precisa
de vínculo verificável ao ato vigente que autoriza sua operação e seu alvo;
autorização agregada e mera identidade da ocorrência não suprem esse vínculo**.
O owner da decisão deve conservar o escopo do ato com identidade do turno,
origem, operação, alvo/destino e parâmetros relevantes, reutilizando resolução
canônica. O normalizador JSON existente só projeta propostas; não concede
permissão. Alvo/operação indeterminados exigem esclarecimento ou rejeição
observável, não associação por palavra compartilhada ou informação da LLM.

Próxima intervenção: publicar esse escopo no contrato canônico, validar cada
proposta contra ele no validador existente e conservar os testes de vigência;
não vetar o turno misto inteiro nem liberar pelo intent em comum. Depois provar
sucesso parcial/conclusão observável e preservação de revisão, referências,
literais e conjuntos legítimos antes de testar main/modelo/voz. Necessária
auditoria da composição dos resolvers para não duplicar inteligência no filtro.

Validação auxiliar: **265 testes GREEN** em seis módulos (instrumento, decisão
única, admissão vigente, consulta de significado, condições e composição de
limites citados). Esses verdes não corrigem os seis REDs do novo instrumento.
Um teste detectou inicialmente alias entre gold/proposta no próprio painel;
as árvores agora são copiadas separadamente, sem alterar a expectativa.
Não comprovado: efeito externo indevido, emissão real frequente pela LLM,
resposta autoral ou entrega audível. **Raiz de admissão aberta; nenhum patch
de produção aplicado nesta auditoria.** F1 e IDs históricos mantidos.

### F1 — consulta ao significado não autoriza a expressão consultada — 11/10/2026

Mesma base `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`;
worktree suja preservada, incluindo corpo/UI e os candidatos anteriores de
aspas/condições. Nenhum commit, modelo, treino ou configuração alterado.
`LAYLAY_NEURAL_MODE=shadow` continua configurado; desenvolvimento neural pausado.

Primeira fronteira demonstrada: o owner `modalidade_turno` reconhecia o prefixo
`pode abrir…` como pedido sem integrar o predicado `significa o quê` ao ato
inteiro. `_modalidade_moldura_pedido` devolvia comando e a proteção P0 devolvia
None. Um único segmento já concedia autoridade indevida, com/sem `?`, com/sem
normalizador e sem detector injetado: falsifica segmentação e detector como
causas necessárias do caso isolado. Controle interno `Abrir X significa o quê?`
já era protegido; `Pode abrir X?` continua sendo pedido polido legítimo.
Em conjuntos, a coordenação da expressão consultada era fracionada e sua
primeira operação recuperava autoridade: mecanismo adicional de vínculo.

Contrato: **consultar o significado de uma expressão não autoriza as operações
que ela menciona; outro ato independente não empresta permissão à consulta**.
Um único reconhecedor estrutural no owner geral lê o predicado final externo
às aspas, independentemente do domínio e do ponto de interrogação. A moldura,
a proteção, os especialistas e as evidências de fronteira reutilizam essa
leitura. Coordenação dentro da expressão consultada permanece inteira;
fronteiras independentes são preservadas. `?` externo delimita pergunta e
nova ordem sem apagar a interrogação da primeira. Não vetar por palavra solta
nem interpretar `"isso significa o quê.txt"` como pergunta do usuário.

RED inicial: **55 falhas / cinco controles GREEN** em quatro domínios e três
configurações das portas. Controles adicionais: uma consulta seguida de ordem
por `e` exigiu ajustar a fronteira da coordenação (um RED), e dois turnos mistos
continuaram RED no consumidor prioritário mesmo com modalidade já correta.
O consumidor ainda enviava a fala inteira à cadeia; agora o recorte operacional
canônico vale quando existe **veto por ato**, não somente a natureza de condição
implementada anteriormente. Nenhum novo parser de autorização no consumidor.
Turno original permanece no estado; a consulta isolada segue à conversa,
sem consumo operacional nem efeito falso. Detector agressivo não ressuscita
autorização; filtro real de propostas da LLM bloqueia quatro classes de ação
quando a entrada inteira é consulta, sem alteração no filtro.

Produção alterada nesta entrega: `cognicao/modalidade_turno.py` e
`autonomia/comandos_imediatos.py`. Não alterados nesta entrega: `laylay.py`,
normalizadores, cadeia, dispatcher JSON, filtros da LLM, executores, modelos,
datasets e persistência pessoal. Não consolidar todos os sintomas de F1 em
uma única causa nem encerrar itens históricos pelo agregado do painel.

Provas: **71 testes focados GREEN**, `test_consulta_sobre_ato_operacional.py`;
**16 testes de composição instalada GREEN**, seis novos no módulo de limites
citados (dez anteriores mantidos). Importa o composition root, usa planner,
normalizador e estado reais; portas de efeitos do consumidor isoladas para
capturar encaminhamento. Não inicia main nem modelo/voz/dispositivos. Seleção
de 20 módulos: **540 testes / 22 subtestes GREEN**, 7,21 s. Inclui modalidade,
cadeias, arquivos, mídia, IoT, metalinguagem, ensino e revisão intra-turno.
`git diff --check` sem erros; avisos de CRLF de arquivos paralelos não são falhas.

Artefato final, sem sobrescrever versões anteriores:
`resultados_testes/interpretacao_legada_20261011/painel_100_pos_consulta_significado_v2.json`.
100 frases / 300 leituras, gold idêntico e seis fontes com hashes finais
conferidos. Somente `app_18`, `midia_18`, `iot_18`, `arquivo_18` mudam de RED
para GREEN. **28→24 divergências; concessões indevidas 4→0 neste painel**.
Os 20 pedidos bloqueados e os problemas de polidez/negação continuam abertos.
Saída 1 do instrumento é RED remanescente de contrato, não falha de execução.
Não extrapolar esses números para acurácia geral ou prontidão de produção.

Limites: validação local e composição instalada, não sessão completa, resposta
autoral final ou entrega audível. Não afirmar cobertura de toda pergunta sobre
consequências/capacidade nem de todo predicado subordinado. O filtro da LLM
em turnos mistos ainda consulta autoridade agregada; a autorização de cada
proposta e os demais consumidores precisam de auditoria própria antes de
afirmar veto completo em todas as rotas. Esta observação é fronteira pendente,
não prova de efeito externo indevido; dispatcher/executor não foram exercitados.

### F1 — vínculo entre condição e consequência no interpretador atual — 11/10/2026

Base preservada: `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`.
Worktree suja, incluindo candidato anterior de aspas e alterações paralelas
de corpo/UI. Nenhum commit, reset ou mudança de configuração neural.

Primeira fronteira demonstrada: `modalidade_turno` separava a condição
antecedente de sua consequência pela vírgula, concedendo autoridade à segunda.
Sem vírgula, a proteção integral já recusava a execução: falsifica ausência
geral de proteção e falha necessária do normalizador. Mesmo comportamento com
e sem normalizador, em apps, mídia, IoT e arquivos. Outro mecanismo ligado ao
mesmo contrato: qualificador posposto `só se eu confirmar depois` permanecia
inteiro, mas não era protegido. Não atribuir ambos ao mesmo corte de vírgula.

Contrato comum: **condição não verificada permanece vinculada à consequência;
autoridade de outro ato independente não satisfaz essa condição**. A modalidade
é o owner; os especialistas não podem substituir a leitura geral da condição.
Marcadores pessoais/restritivos fora de aspas recebem natureza explícita
`condicao_nao_verificada` e veto por ato. Cortes conservam o vínculo e distinguem
uma consequência diretiva de um verbo somente no antecedente. Ordens
independentes delimitadas continuam autorizadas; conjunção ambígua não libera
parte de um conjunto condicionado. A política tipada abrir-se-fechado/avisar-se-
aberto continua válida e seus sete regressivos permanecem GREEN.

RED canônico inicial: **57 falhas / dez controles GREEN**, depois de separar
um controle de aspas que já tinha outra falha histórica. Candidato na modalidade
produziu GREEN local, mas três testes adicionais do consumidor ainda ficaram
RED: prioridade enviava o pedido inteiro à cadeia; em IoT bloqueava também a
ordem imediata. A chamada instalada da cadeia foi rastreada à prioridade.
`comandos_imediatos` agora consome `texto_operacional` canônico quando há
condição não verificada e outra fonte de autoridade; conserva o turno original
no estado. Não cria outro parser nem muda o executor ou o segmentador da cadeia.

Produção alterada nesta entrega: `cognicao/modalidade_turno.py` e
`autonomia/comandos_imediatos.py`. Nenhuma alteração em `laylay.py`, modelos,
datasets, treino, pendências ou executores. Regressivos adjacentes acrescentam
qualificador depois de vírgula e verbo no antecedente (nove REDs intermediários
antes do ajuste de vínculo), sem enfraquecer expectativas.

Controle adicional revelou regressão no primeiro candidato: `Pesquisa se eu
posso cultivar orquídeas na sombra` ficava bloqueado. Módulo do HEAD executado
somente em memória (demais dependências na worktree) autoriza essa pesquisa.
`se` subordinado sem posição de cláusula nem restritor não é automaticamente
condição da ordem matriz; ajuste estrutural sem exceção por habilidade.
Condição investigada ≠ condição para executar a investigação. O novo controle
também ficou GREEN; condicionais sem marcação de escopo inequívoca continuam
fora da alegação de cobertura universal.

Provas: **88 testes focados GREEN**, `test_vinculo_condicao_acao.py`; **dez
testes de composição GREEN** no módulo existente de limites citados (cinco
anteriores + cinco de condição). Planner e estado são instalados por `laylay.py`;
consumidor prioritário instalado recebe portas de efeito isoladas para capturar
o texto entregue. Isso não inicia main nem comprova uma sessão completa,
voz ou efeitos externos. Seleção relevante de 16 módulos: **378 testes / 22
subtestes GREEN** após o controle adicional. `git diff --check` sem erros.

Painel congelado preservado, sem alteração de gold:
`resultados_testes/interpretacao_legada_20261011/painel_100_pos_vinculo_condicao_v2.json`.
Versão intermediária sem `_v2` preservada, não sobrescrita.
100 frases / 300 leituras, fontes estáveis; somente 12 casos de condição
mudam de RED para GREEN: oito isolados e conjuntos 15–18. **40→28 divergências**;
concessões indevidas **14→4**, pedidos bloqueados continuam 20. CLI retorna 1
pelos REDs remanescentes, não por falha de infraestrutura. Metalinguagem,
polidez compartilhada, escopo negativo e pedidos indiretos/subordinados
continuam abertos; não declarar F1 encerrada nem medir acurácia geral.

Limites: não há novo agendamento, memória de ação futura ou execução automática
ao ouvir `pronto/sim`. Conserva-se o pedido no turno; não prometer pendência
persistida sem receipt. Referências/escopos condicionais fora das molduras
testadas continuam exigindo diagnóstico. Descoberta separada, sem patch aqui:
`Abre o arquivo "quando eu confirmar.txt"` é bloqueado por proteção hipotética
antiga que lê conteúdo citado; não é fragmentação nem evidência de regressão
deste candidato. O novo marcador ignora aspas e o controle com
`"apenas se autorizado.txt"` permanece autorizado.

### F1 — limites citados nos segmentadores de atos e etapas — 11/10/2026

Continuação do mecanismo de fragmentação literal encontrado no painel de 100
frases, não outra raiz por playlist/arquivo. Mesma base `main`, HEAD
`2566b621d2c8ee88ff7086c6c36019da85c8a4cd`; diffs anteriores de verbos corporais,
UI e demais frentes preservados. Produção alterada somente nesta fronteira:
`modalidade_turno.py` e `analise_comandos.py`. Nenhuma configuração/modelo,
executor de domínio, `laylay.py` ou serviço de aspas alterado nesta entrega.

Contrato: **separador dentro de literal citado não cria ato/etapa operacional**.
O mapa canônico `arquivos.nome_natural.mapear_pares_aspas_globais` já existe.
A modalidade o consultava na passagem de pontuação, mas não nas conjunções;
a cadeia não o consultava. Entrada integralmente coerente, controles sem detector,
sem normalizador e módulo do HEAD falsificam aspas órfãs, injeção lexical e diff
corporal como explicações necessárias. Não atribuir execução externa aos segmentos.

RED canônico antes do candidato: **54 falhas / dois controles GREEN**,
`test_segmentacao_limites_citados.py`, três tipos de aspas, oito separadores,
com/sem ordem externa, nomes de playlist/arquivo e conteúdo a escrever.
Primeira asserção examina modalidade; a seguinte examina cadeia. Inclui aspas
órfãs/invertidas/cruzadas e enumeração legítima, sem enfraquecer guardas.

Candidato mínimo: consultar o mapa antes do corte de conjunções e etapas;
cadeia não fraciona uma entrada com aspas malformadas; preservar a fala
estrutural, em vez da cópia lexical que elimina pontuação, quando houver
literal e nenhuma cadeia ou quando ultrapassar o limite. Isso não concede
autoridade nova, não interpreta condições nem remove proteção de negação.
**56 contratos locais GREEN** depois do candidato.

Composição instalada: `test_segmentacao_limites_citados_composicao.py` importa
`laylay.py` e chama `_iniciar_planejamento_turno`, com classificadores/setters
instalados e normalizador real. **Cinco GREEN**; comprova também as ligações
dos owners canônicos. Mutex próprio, SQLite/JSON relevantes isolados; modelo,
pesquisa, coleta neural e portas externas fora da prova. Não inicia main ou
habilidades. Contraprova opcional `LAYLAY_SONDA_CITADOS_BASELINE=head_segmentadores`
carrega os dois módulos do HEAD apenas na memória do subprocesso, antes da
composição: **quatro REDs / um controle GREEN**, por fragmentação nos mesmos
asserts. Não substitui arquivos e não equivale a replay de toda a árvore do HEAD.

Painel idêntico reexecutado, 300 leituras:
`resultados_testes/interpretacao_legada_20261011/painel_100_pos_limites_citados.json`.
Somente conjuntos 19/20/21 mudam de RED para GREEN; **43→40 divergências**,
incluindo **15→12 conjuntos**. Nenhuma outra expectativa/regra do painel alterada.
Seis fontes permanecem com hashes iguais ao artefato após regressão.
Condições, polidez, escopo negativo e metalinguagem permanecem pendentes.

Seleção relevante: **278 testes / 22 subtestes GREEN**, 14 módulos, 8,25 s,
incluindo composição, arquivos, caminhos absolutos, mídia, sistema e cadeia.
`git diff --check` sem erros. Nenhum commit. A validação confirma o contrato
local e o caminho instalado, **não** sessão completa, entrega audível, receipt
de escrita ou efeito em navegador/dispositivos. Raiz não encerrada globalmente.
Transformações anteriores de nomes/conteúdo por normalizadores não são cobertas
por este contrato de limites; não alegar preservação byte a byte universal.

### F1 — pressão do interpretador atual, incluindo conjuntos — 11/10/2026

Pedido de Pedro: procurar falhas generalizáveis, com destaque para comandos
conjuntos, enquanto o desenvolvimento neural está pausado. Base `main`, HEAD
`2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, worktree suja preservada.
Não atribuir diferenças automaticamente às alterações paralelas de corpo/UI.

Instrumento: `scripts/analises/sonda_interpretacao_legada.py`, painel explícito
de 100 frases, quatro domínios mais 28 conjuntos. Cada frase passa por três
configurações reais da API: detector explícito, detector+normalizador e sem
detector. Nenhum executor, LLM ou rede neural chamado. Expectativas autorais
diagnósticas, não avaliação humana independente nem holdout. Pedidos indiretos
de polidez são expectativas de uso e exigem confirmação do contrato pragmático
antes de ampliar autoridade. Não medir acurácia geral por este painel adversarial.

Artefato preservado em
`resultados_testes/interpretacao_legada_20261011/painel_100.json`, com todas as
300 leituras, texto/expectativa/segmentos/cadeia/barreira, HEAD, branch, worktree
e hashes antes/depois (seis fontes estáveis). CLI retorna **1 por RED de contrato**,
não por erro de import. Leitura principal: **43 casos divergentes**, incluindo
**15/28 conjuntos**; 14 concessões indevidas de autoridade imediata, 20 pedidos
bloqueados e nove outros casos com perda de operação/escopo/literal. Categorias
de propriedades podem se sobrepor; 43 casos não são 43 raízes.

Vinculação a F1 (significado preservado), sem encerrar itens históricos nem
presumir uma raiz única para todos os mecanismos:

| Mecanismo observado | Primeira fronteira e dono | Estado da evidência |
| --- | --- | --- |
| Literal citado vira comandos separados | Segmentação de atos em `modalidade_turno._segmentar_turno_misto` e segmentação de etapas em `analise_comandos.segmentar_comandos_em_cadeia` | Reproduzido: `e` citado corta nos dois; vírgula citada é protegida na modalidade mas não na cadeia. Primeira passagem da modalidade já consulta intervalos de aspas; passagem de conjunções não. Aspas integrais coerentes falsificam entrada malformada como causa. |
| Condição futura perde vínculo com ação | Segmentação/classificação no owner `modalidade_turno` | Reproduzido em quatro domínios: `Quando eu disser pronto, A` autoriza A; sem vírgula recusa corretamente. Proteção integral identifica hipótese, mas segmentação torna consequência independente. `A só se eu confirmar depois` também autoriza, porém permanece um único segmento: lacuna de qualificador posposto distinta do corte. |
| Polidez compartilhada se perde no segundo pedido | Segmentação → classificação por ato em `modalidade_turno` | `Pode abrir X e pausar Y?` autoriza só a primeira parte e retira a segunda do texto operacional; quatro conjuntos RED. Hipótese de perda da moldura governante; falta rastrear consumidores no caminho instalado. |
| Recusa de B bloqueia pedido independente A | Segmentação → proteção conservadora em `modalidade_turno` | Quatro conjuntos RED. A proteção interna é deliberadamente fail-closed e não deve ser removida globalmente. Falta representar escopo independente antes de relaxar bloqueio. |
| Moldura de pergunta/pedido não representa ato integral | Classificação de ato/proteção em `modalidade_turno` | `Pode abrir X significa o quê?` concede autoridade em quatro domínios. Pedidos subordinados/indiretos também divergem; mecanismos ainda não consolidados em uma única causa. |

Falsificações adicionais: as 43 divergências permanecem idênticas com
normalizador canônico e sem detector explícito; não dependem do modelo neural,
de execução física ou de uma falha do detector injetado. Quatro controles
centrais também reproduzem os mesmos segmentos ao executar em memória o
`modalidade_turno.py` do HEAD, mantendo dependências da worktree: não é prova
de toda a árvore histórica, mas falsifica necessidade do diff local desse
módulo (adições de verbos corporais) para aqueles quatro sintomas.

**GREEN do instrumento/vizinhos, não do painel:** 135 testes e 22 subtestes,
2,03 s, oito módulos, incluindo cinco testes do instrumento. O painel mantém
os REDs; nenhum rótulo foi alterado para fazê-lo passar. Pedidos diretos,
relatos, recusa inicial, ensino e conjuntos diretos servem de controles.

Próxima investigação prioritária: contrato lexical compartilhado de limites
citados, reutilizando os serviços existentes de aspas nos consumidores de atos
e etapas. Depois, investigar dependência entre condição/moldura e consequência,
sem fundir as causas ou remover as proteções globais. Provar primeiro os REDs
canônicos e o caminho instalado antes de alegar efeito externo indevido.
Não criar parser particular de playlist, IoT, arquivo ou navegador.

Escopo desta entrega: instrumento, testes e documentação. Nenhuma produção,
configuração, peso, dataset neural ou estado pessoal alterado; nenhum commit.
O runtime completo, geração da resposta, receipts e efeitos externos **não foram
validados nesta coleta**. Não declarar raiz corrigida nem a apresentação pronta.

### Decisão de prioridade — apresentação no SENAI — 11/10/2026

Pedro pausou o desenvolvimento da rede até depois da apresentação prevista
para o início de novembro. Preservar integralmente modelos, datasets, sondas,
testes, resultados e hipóteses; nenhuma raiz é encerrada por mudança de prioridade.
Checkpoint em `mente_laylay/neural/README.md`: `main`, HEAD
`2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, worktree suja preservada.
Configuração local consultada: rede em `shadow`; não alterada nesta entrega.

Foco aprovado: estabilidade e melhoria do interpretador atual e dos contratos
compartilhados, organizadas pelas raízes existentes, sem reconstrução ampla ou
novos parsers privados. Priorizar comandos naturais/continuidade e conclusão
fiel ao receipt, preservar conversa/voz e verificar o caminho real da demonstração.
A ordem concreta das correções deve seguir evidência atual, não logs históricos
isolados. Falhas de terceiros, portas físicas e entrega audível continuam
exigindo prova própria. Não retomar treinamento, promoção ou sondas neurais
automaticamente durante essa preparação.

Somente documentação alterada nesta decisão; nenhuma produção, configuração,
peso ou dataset modificado, nenhum teste executado e nenhum commit criado.

### AUT-01 — conferir ocorrência na admissão da próxima etapa — 06/10/2026

Continuação da janela posterior à publicação aceita já registrada, sem outro
ID por domínio/frase. Base `main/90a2fb8`, worktree preservada. Mescla por
solicitação e procedência semântica já possuem candidatos de outras frentes:
26/75/33 controles atuais GREEN, com sobreposição; não reaplicados aqui.

Primeira RED: publicação vinculada legítima → montagem de contexto ou primeiro
comando troca o turno → comando/finalização antigo ainda inicia. Writer depois
recusa corretamente; isso falsifica sua falha como condição necessária. Nova
ocorrência pode ter a mesma frase, e três controles vigentes passam normalmente.

Contrato canônico somente leitura em `ComposicaoTurnoRuntime.proposta_vigente`,
instalado pela composição. Runtime consulta após montar dispatcher/finalizador;
dispatcher consulta antes de cada comando, inclusive rota legada. Retorno
incerto, erro ou callback malformado presente recusa; contexto antigo sem a
chave mantém compatibilidade. IDs não concedem autoridade ou comprovam efeito.

16 REDs/3 controles antes do candidato; 31 focados depois (19 locais e 12 da
composição instalada), três domínios. Gate: **600 aprovados e 10 subtestes**,
41,67 s. Ampla final: **10.161 aprovados, um ignorado e 56 subtestes**, zero
falhas, 499,80 s; XML `.pytest_cache/aut01_admissao_ampla.xml`, manifesto
`.pytest_cache/aut01_admissao_hashes.json`, 222 Python estáveis durante/depois.
HEAD/branch preservados e diff sem erros. Resultado no checkpoint 10 do
[plano de autonomia](../planos/PLANO_LAYLAY_ASSISTENTE_AUTONOMA.md).

Produção desta entrega: `composicao_turno.py`, `resposta_ia_runtime.py`,
`dispatcher_comandos_json.py` e instalação do callback em `laylay.py`.
Nenhum executor de domínio ou parser alterado; nenhum commit. SQLite/mutex
próprios, transporte/efeito/fala controlados. Não certifica GUI, áudio ou
dispositivos físicos, nem atomicidade entre leitura e efeito dentro do executor.
AUT-01 parcial: ação em curso, resultado tardio e fala após admissão continuam
fora deste candidato. Não atribuir a intercalação à troca histórica `55ee6435...`.

### RC-OFERTA-01 — aceite de oferta não chegava ao executor — 06/10/2026

- Evidência histórica: imagem fornecida por Pedro e TXT diário local de
  06/10, 18:03/18:04. “Pode ser” → “Manda quando quiser”; “pode fechar” →
  ausência de execução; pedido com alvo explícito → fechamento de três abas.
- Baseline `main`, HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`.
  Worktree suja preservada; HEAD não equivale ao processo histórico.
- Raiz reproduzida: oferta do `PorteiroChromeRuntime` só publicava fala/lista;
  sem `PendenciaAcaoRuntime`, reconhecimento próprio incompleto e consumo
  tardio atrás das barreiras conversacionais. Não é defeito demonstrado do
  classificador compartilhado de “pode ser” ou falha geral do fechamento.
- Candidato: registrar ID/TTL/hash dos alvos na pendência existente, respeitar
  outra pendência ativa e política de sobrevivência; resolver aceite/recusa
  pelo intérprete compartilhado; consumir antes da conversa; fechar pelo
  roteador/executor atual e concluir somente com receipt confirmado.
  Verbos de fechamento permanecem informação do domínio, sem lista privada
  de sim/não. Detector legado passa a exigir pedido com alvo explícito.
- RED inicial: 12 falhas de contrato, inclusive composição instalada.
  Cinco REDs adicionais: outro pedido com aceite verbal/verbo de outra ação
  não confirma esta oferta. Opção `somente_aceite_generico` no classificador
  e resolver compartilhados; default conserva consumidores existentes.
  Provas de pendências reais de navegador/arquivos e compatibilidade legada.
  GREEN final focado: 34. Gate final: 282 aprovados, XML em
  `.pytest_cache/oferta_abas_regressivos_finais.xml`; intermediário de 258
  em `.pytest_cache/oferta_abas_regressivos.xml`. Ampla detalhada abaixo.
  Manifestos intermediários preservados em
  `.pytest_cache/oferta_abas_hashes.json` e `oferta_abas_hashes_finais.json`;
  revisão validada em `.pytest_cache/oferta_abas_hashes_validados.json`.
- Produção desta correção: `porteiro_chrome.py`, `detectores_playlist.py`,
  `comandos_imediatos.py`, wiring em `composicao_entrada_interacao.py` e
  `laylay.py`, opção genérica em `aprendizado_rotina_musica.py` e passagem
  dessa opção em `pendencia_acao.py`. Não altera executores Chrome ou motor
  de aprendizado. Nenhum commit criado; outros diffs preservados.
- Limite: composição carrega `laylay.py` e usa serviços reais com SQLite
  isolado; efeito Chrome/percepção/fala são controlados. Fechamento no navegador
  e som físico após reinício continuam sem prova. Não marcar encerramento
  global por verde de harness; raiz vinculada ao mapa RC-OFERTA-01.
- Ampla intermediária: **10.025 passed, 1 skipped, 56 subtests passed**,
  oito falhas, 400,08 s. Log/XML `.pytest_cache/oferta_abas_ampla.*`.
  Sete falhas são `SystemExit: 0` na proteção de instância antes da composição,
  pois a Laylay pessoal está aberta. Revalidação das sete: **7 passed**,
  5,64 s, mutex canônico com identificador isolado no processo do teste,
  sem encerrar a Laylay ou editar produção; XML `oferta_abas_bloqueios_instancia.xml`.
  Falha restante `test_cache_com_quebrado_migra_para_sapi_nativo_sem_repetir_pyttsx`
  também reproduzida isoladamente (47 controles passaram na seleção).
  Voz já alterada na worktree anterior, sem mudança desta investigação;
  sintoma separado, raiz não diagnosticada aqui. Não enfraquecer o teste.
  Ampla coletou a revisão intermediária antes do refinamento final genérico;
  282 é o gate da revisão final, não uma nova ampla totalmente verde.

### P16 — fonte original disponível e sequência interrompida por efeito real — 04/10/2026

Sem novo candidato de produção; base main/90a2fb8, 1.245 Python e arquivos pessoais
anteriores preservados por hash. Após jogo encerrado e pré-aquecimento canônico
no orçamento padrão, coleta `182525-927021` tem oito principais novas HTTP200,
correlacionadas a payload/bruto/turno/plano: oito controles GREEN, p95 7,953 s,
zero comandos/violações/efeitos IoT. Não observou erro original próprio; não fecha
publicação/admissão positiva, nem prova causa única dos timeouts históricos.

Coleta real com voz/avatar `182929-427557`: 16 respostas/filas de áudio concluídas,
sem silenciamento, código zero; **5 passaram, 8 falharam, 3 alertas**, p95 23,244 s.
Primeira RED no turno 4: Calculadora sem foco → `app_focado`, executou/confirmou,
receipt `7e0b232057f04911879fc46ec91d310c`, enquanto roteiro exigia não-ação
redundante. Outra interrupção no turno 9, `7043e96cfbb24f6b9e26e81968d6ec61`.
Retratos apontam navegador em primeiro plano; ator da troca não identificado.
Os oito sintomas 4/5/6/7/9/10/11/14 permanecem ligados às duas interrupções de
pré-condição, sem oito novos bugs atribuídos à emoção. Reavaliação offline pelo
owner canônico dos dez receipts corresponde aos eventos gravados. Primeira
interrupção em 20,195 s, dentro dos 300 s: contador/TTL não explicam essa RED.
Um efeito real interrompe redundâncias consecutivas; não alterar o receipt nem
enfraquecer expectativas para certificar uma sequência que não ocorreu.

Seis principais de conversa novas/HTTP200/vinculadas, sem comandos/violações.
Conquista/vulnerabilidade/assunto novo encerram episódios observados; relato
temporal publica alívio sem tristeza passada lexical. Autoria/reparos existentes
participaram, detalhados na prova; não declarar fidelidade global. Computer-use
não retornou janela capturável do avatar e não emitiu entrada/ativação. Confirmação
humana de som/visual desta coleta pendente; `brava 3` não foi atingida. Próxima
fronteira: sequência com foco realmente observado e observação física; positivo
próprio fresco e lacunas históricas permanecem abertos. Provas e limites no novo
checkpoint do roadmap e `prova_voz_avatar.json`; nenhuma expectativa removida.

### P16 — identidade literal e nomeação antes de persistir — 04/10/2026

**Raiz da pessoa indevida demonstrada:** `MemoriaPessoasRuntime._extrair_relacao`
aceitava qualquer palavra justaposta a `meu/minha + relação`, salvo sete verbos.
O histórico `210441-907211`, `Meu irmão está bravo. Eu me sinto culpado.`, virou
`Esta`; variantes viravam `Estava`, `Parece`, `Chegou` etc. A mesma regra solta,
avaliada por último, sobrescrevia `se chama Esta` com `Se`. Primeira fronteira:
seleção da evidência de identidade, antes de classificação, armazenamento e LLM.
Falsificadas origem na principal e falha geral de escrita: extração direta RED,
apresentações explícitas e armazenamento real usados como controles.

Candidato mínimo somente `memoria_pessoas.py`: remover a moldura de justaposição;
nomeação/apresentação explícitas continuam no mesmo serviço, com proveniência,
aprendizado, contexto e receipts existentes. Sem lista de palavras do histórico.
Menções como `meu irmão Carlos` deixam de criar identidade por si só; formas como
`Carlos é meu irmão`, `meu irmão é Carlos` e `se chama Carlos` continuam cobertas.
O patch não certifica interpretação arbitrária de nomes/adjetivos nas copulas.
RED inicial: 11 falhas/36 controles locais, cinco falhas/um controle na composição.

**Raiz separada encontrada no controle positivo instalado:** a linguagem aprendida
consumia `Meu irmão se chama Esta.` como alias `meu irmao se → esta`, impedindo a
memória de pessoas de receber o relato. O trace chegou ao atalho de apelidos,
sem chamada ao serviço; o extrator de pessoas já estava correto. Não era barreira
P0, composição ausente ou persistência quebrada. Quatro REDs/ quatro controles
com SQLite real, em pessoas/projeto/arquivo. Candidato mínimo no owner
`LinguagemAprendidaRuntime.extrair_apelido_ensinavel`: `se chama` não é o separador
lexical `chama`; ensino explícito de alias continua válido. Não reordenar handlers.
Princípio compartilhado: evidência literal deve autorizar o tipo de aprendizado;
uma nomeação não autoriza outra substituição global na linguagem.

**GREEN local/composição:** 95 focados antes da guarda CLI; sonda final 17 GREEN,
incluindo abortar o roteiro novo sem isolamento. Callbacks e serviços instalados
por `laylay.py` preservados, casos negativos/positivos e ensino lexical vizinho.

**GREEN do contrato no loop real:** `transporte_evidencia-20261004-174111-482431`,
oito turnos. Três negativos iniciais sem arquivo/perfis; apresentação de Esta
gera PEOPLE_REMEMBER confirmado, relação/ID/fonte relidos. Predicado após cadastro
não altera bytes. Consulta canônica retorna `Esta é seu irmão`, PEOPLE_QUERY
confirmado. Nomeação de projeto não escreve pessoas/aliases; Ana apresentada e
relida como prima. SQLite próprio contém zero aliases; todos os planos conservam
`autoriza_execucao=False`. Cinco passaram/três alertas de latência/zero falhas,
p95 29,426 s. Receipt e releitura são a prova, não o placar isolado.

**Limites:** sete principais só técnicas insuficientes (timeouts/circuito),
contingências existentes participaram da fala; não validar autoria/fidelidade ou
positivo próprio da P16. Voz/avatar off. 119 Python preservados durante a coleta;
JSON pessoal e TXT diário anteriores preservados por hash. O registro pessoal
histórico `pessoa:105d09395b32` permanece intacto. Isolamento opcional da sonda
abrange SQLite/resumo/pessoas, não todo estado. Base main/90a2fb8; nenhuma alteração
no classificador/executor/orquestrador, nenhum commit ou limpeza. Provas/baselines
em `prova_identidade_pessoas.json` e no checkpoint do roadmap. **Ampla: 9.429 passed,
1 skipped, 56 subtests passed**, 280,69 s, código zero; 119 hashes do manifesto e
arquivos pessoais conferidos depois. Manifesto acompanha a base suja e testes/
roteiro novos; os dois owners, antes limpos, não estavam nesses 119. Baselines
originais, diff mínimo e mtimes anteriores à coleta conferidos separadamente em
`auditoria_fontes_candidato.json`; hashes dos candidatos registrados após a ampla,
sem alegar captura anterior que não ocorreu. P16 continua parcial.

### P16 — atribuição lexical de emoção fora do predicado pessoal — 01/10/2026

Raiz demonstrada, owner `analisar_intencao_emocional`: marcador pessoal e sinal
eram buscados globalmente. `estou` atual validava `triste` passado, publicando
vulnerabilidade lexical que a prioridade direta preservava sobre alívio original.
Histórico `203531-829003`, plano 1790897998476775600. Transporte/perda da principal,
reparo como fonte e obrigação de copiar alívio para a Laylay foram falsificados.

Produção somente `leitura_usuario.py`: verbo/sinal/grau no mesmo predicado;
incerteza segue para a principal. Não alterar prioridade, executor ou emoção
própria. Dez REDs antes do patch (dois na composição instalada); 408 focados,
oito subtestes e 13 da sonda GREEN. Ampla: **9.394 passed, 1 skipped, 56 subtests
passed**, 221,15 s. Base main/90a2fb8, 116 Python/hash e TXT diário preservados.

Main novo `transporte_evidencia-20261001-210441-907211`: três relatos temporais
publicam alívio original sem evento lexical anterior, comandos ou alteração da
expressão própria. Tristeza presente mantém a proteção direta. Voz/avatar off;
não certifica leitura temporal arbitrária nem fecha P16. Prova local e detalhes
no checkpoint do roadmap. Nenhum interpretador extra, replay ou commit.

**Falha vizinha preservada:** sexto relato `Meu irmão está bravo. Eu me sinto
culpado.` gerou `PEOPLE_REMEMBER` de `Esta`, antes da principal, e persistiu
`pessoa:105d09395b32` em `memoria/pessoas_relacoes.json` (releitura confirmada).
Identidade literal antes da persistência exige investigação própria; não agrupar
por semelhança com esta raiz nem contar como erro operacional original da LLM.
Placar completo: três passaram, dois alertas de latência e uma falha; expectation
intacta. Dois originais não JSON e `Senti isso antes` são observações de formato/
fidelidade ainda sem raiz atribuída. Registro persistente preservado, sem limpeza.

### P16 — sequência real de 16 turnos com voz/avatar, som físico pendente — 01/10/2026

Coleta `transporte_evidencia-20261001-203531-829003`, main/roteiro real, base
`main`/`90a2fb8`, dez receipts distintos/confirmados (sete redundâncias em foco).
Campos emocionais/refs conferidos nos 16 planos: intensidade causal, continuidade,
conquista/desculpa/vulnerabilidade/renovação e assunto novo. Dez passaram, seis
alertas só de latência, zero falhas; todas as esperas de voz concluídas, voz ativa.
Capturas `computer-use` sem ativação/input mostram avatar calmo e com bronca;
contexto publicado/intervalos arquivados. Captura pontual não certifica sincronismo
integral; som físico aguarda observação humana desta execução. Não encerrar P16.

Código zero e log nativo vazio não encerram crash histórico. 114 Python/hash e
TXT pessoal preservados. 99 focados GREEN; nenhuma produção alterada nesta etapa,
apenas roteiro/sonda/testes/documentação. Isolamento limitado a SQLite/resumo.
44 registros/28 HTTP200 (um pré-aquecimento + 27 gerações); retornos locais e
tentativas bloqueadas separados em `prova_voz_avatar.json`. Reparos/contingências
existentes participaram; nenhum interpretador emocional novo. Turno 10 disse
ser chatbot, observação de fidelidade sem raiz nova atribuída. Detalhes no roadmap.
Auditoria visual: IDs longos arredondados pelo JS; originais preservados e adendo
com IDs exatos em strings da fonte Python. Isso não prova ID lido do renderer.
Turno 15 verifica só ausência de comando. A principal original reconheceu alívio;
o plano conservou vulnerabilidade lexical do `triste` passado. `Calma 1` era
proposta de expressão do modelo, não leitura lexical. Diagnóstico na continuidade acima.

### P16 — vetos naturais compostos, sem proposta própria incompatível — 01/10/2026

Continuação da prova P16, sem outra raiz contada. Main real, base `main`/`90a2fb8`,
coleta `transporte_evidencia-20261001-202847-916595`, seis recusas IoT em roteiro
dedicado; whitelist/observadores da sonda, sem candidato de produção. Cinco
principais novas/HTTP200/sucesso, conteúdo e seis identidades correspondentes.
Veto inequívoco, owner conversa/origem classificador; cinco comandos originais
vazios, validadores/dispatchers vazios, zero violação/evento/admissão/entrada IoT.
Controle negativo real auditado independentemente; positivo próprio ausente.

Sexto turno: pre-fluxo de reparação local, sem principal. Sexto registro do modelo:
resumo bloqueado antes de HTTP e adiado sem consumo. Placar mínimo 6/6 verifica
ausência de comandos; não avalia fidelidade da fala. Quinto original afirmou
estado sem leitura e foi corrigido pelo guardião antes da entrega. Sexta resposta
local teve referente inadequado. Essa é observação separada, com raiz ainda não
diagnosticada; não promover a erro operacional P16. SQLite/resumo próprios,
TXT pessoal preservado por hash, IoT simulado/voz e avatar desativados.
Tentativa 202759-703726 parou no loader literal antes de qualquer principal;
roteiro corrigido e carregamento real protegido. Detalhes no roadmap/prova local.

### Memória diária — estado técnico promovido a resumo e consumo do lote — 01/10/2026

Raiz separada demonstrada no runtime, base `main`/`90a2fb8`, owner
`MemoriaLaylay.atualizar_resumo_diario`. Callback ligado pelo root retorna só
texto; resumo aceita sentinela não vazia sem `LAYLAY_LLM_INDISPONIVEL`, substitui
resumo anterior, limpa lote/contador e persiste. Fonte real f9731f24... da coleta
`transporte_evidencia-20261001-195555-791829`: `sucesso=False`,
`__LAYLAY_LLM_ORCAMENTO_PRAZO_ESGOTADO__`, sem HTTP. TXT tem cabeçalho e a
sentinela como resumo; helper canônico confirma `orcamento_prazo_esgotado`.
Artefato de metadados/hash: `diagnostico_resumo_diario.json` na mesma coleta.

Falsificados autoria semântica da LLM nesse retorno e falha geral da escrita;
não quantificados dados pessoais removidos nem excluídos todos writers externos.
Contrato: falha técnica nunca consolida memória nem consome lote. **11 REDs e
8 controles GREEN** antes do candidato: timeout/ocupação/nove estados de orçamento
substituíam o resumo na primeira asserção causal. Indisponível já protegido,
texto legítimo sobre timeout e controles antigos GREEN. Teste canônico protege
resumo anterior/lote/contador/bytesTXT/recarga/cooldown29s/retentativa30s.

Candidato mínimo: só `mente_laylay/memoria_mental/resumo_diario.py`, guarda com
`eh_estado_tecnico_llm` compartilhado, preservando proteção antiga. **34 focados
GREEN** em 1,75 s. Main real `transporte_evidencia-20261001-201034-289090`:
resumo recebeu `__LAYLAY_LLM_ORCAMENTO_PRINCIPAL_DUPLICADA__` sem HTTP, adiou;
TXT próprio conserva oito pendentes e placeholder, sem sentinela consolidada.
TXT pessoal anteriormente contaminado preservado por hash; não restaurado.
Ampla **9.359 passed, 1 skipped, 56 subtests passed** em 226,04 s, código zero:
`.pytest_cache/resumo_diario_ampla.log`. Auditoria persistida em
`.pytest_cache/resumo_diario_ampla_hashes.json`: 113 arquivos Python acompanhados
com hashes iguais antes/depois, nenhuma alteração durante a suíte.

Limites: prevenção de novos consumos técnicos; não recupera lote histórico nem
valida/limpa resumo contaminado ao carregar. O tipo de chamada do resumidor e a
possibilidade de consolidação real em outro momento não foram alterados. Não
pertence à raiz da proposta emocional ou ao isolamento da sonda. Sem commit.

### P16 — oito principais novas, controles negativos reais — 01/10/2026

Coleta `transporte_evidencia-20261001-201034-289090`, base `main`/`90a2fb8`.
Após GPU liberar e modelo expirar normalmente, recarga no caminho normal;
backend observado Qwen com 3.178.149.969 bytes na VRAM. Nenhum processo existente
encerrado ou orçamento/modelo alterado. Oito principais/HTTP200/originais/extrações
idênticas e vinculadas ao ID corrente: seis sem campo comandos, duas lista vazia.
Oito dispatchers vazios; nenhum receipt/executor IoT/evento/admissão de erro próprio.
Código zero/8 turnos. Controle negativo real; a prova positiva continua pendente.

Observador contou oito principais, um reparo de comunicação existente e um resumo
bloqueado (dez registros, mas só nove gerações do modelo + pré-aquecimento HTTP).
Nenhum interpretador emocional adicional. SQLite e resumo próprios; TXT pessoal
preservado por hash. A lacuna do caminho de resumo da sonda foi reproduzida RED
antes da correção só no construtor observado; teste com serviços reais GREEN.
Guardas de coleta rejeitam prova positiva sem fonte/validação; 34 focados incluem
esses três controles. `prova_p16.json` distingue o negativo da ausência de culpa.
Detalhes/limites no roadmap. A ampla anterior precedia a instrumentação atual.

### P16 — fonte técnica insuficiente na prova própria nova — 01/10/2026

Pré-condição da prova positiva, sem outra raiz semântica declarada. Main real,
roteiro IoT existente com veto, SQLite próprio e observadores delegando fonte,
validação, publicação, confirmação e finalização. Somente sonda de transporte
alterada nesta etapa. Artefatos `transporte_evidencia-20261001-195336-817698` e
`transporte_evidencia-20261001-195555-791829`: oito fontes técnicas cada,
zero comandos no dispatcher/entrada executor IoT/evento de erro próprio.
Código zero e placar 8/8 não provam geração válida; coleta/prova registram fonte
insuficiente. Nona chamada externa é resumo diário, não outro turno válido.

Primeiro controle: carregamento 21,15 s; principais expiraram. Segundo, modelo
já carregado: timeout 5/7/7 s → circuito. Frio sozinho falsificado. Ollama
0/37 camadas GPU; consulta posterior GPU 96%, cerca de 190 MiB livres, Forza
em execução. Consumo por PID indisponível: recursos são hipótese sustentada,
não atribuição exclusiva ao jogo. Nenhuma alteração em orçamento/modelo ou
encerramento de processo existente. Próxima fronteira: principal nova válida
com recursos disponíveis, depois verificar a cadeia positiva. P16 aberta.
Compilação/guardas/duas coletas/resumos conferidos; 109 hashes da ampla intactos.
SQLite próprio não isola TXT de resumo diário. Detalhes no checkpoint do roadmap.

### P16 — conclusão local de outra ocorrência, segunda transição — 01/10/2026

Mesmo RED histórico `55ee6435...`, sem identificar seu autor e sem contar outra
raiz por sintoma. Controle instalado: saída de A aceita → seleção B via ponte
real → retorno A → fase publicada em B. Quatro REDs (B vazio/parcial e B com
novo turno, em duas perguntas de capacidade); cinco controles iniciais GREEN.
Histórico A já correto. Contrato neutro de ID/texto capturado antes das rotas
locais, conferido no commit do owner do plano; recusa observável sem fallback
legado. Reutiliza checagem da proposta principal sem inventar origem LLM.

**174 focados/vizinhos GREEN**. Main real controlado a282c7...: receipt/arquivo
próprios confirmados antes da seleção, conclusão tardia recusada, B preservado;
sete turnos e código zero. GUI omitida só no controle, TCP ocupa cliente único.
SQLite próprio consultado `mode=ro`: três pares A/quatro B. Controle normal
9c2264... com GUI: sete turnos/arquivo/código zero, sem seleção. Voz silenciada.
Tentativas anteriores da sonda preservadas RED: socket sem atendimento enquanto
GUI conectada; depois expectativa incorreta de interromper roteiro, que mantém
snapshot identificado da saída de A. Expectativa corrigida com evidência;
barreiras do roteiro intactas. Detalhes/IDs/limites no checkpoint do roadmap.

Seis arquivos de produção, sonda existente e testes focados; worktree preservada.
Ampla: **9.343 passed, 1 skipped, 56 subtests passed** em 252,93 s, código zero;
log `.pytest_cache/p16_conclusao_local_ampla_conferida.log`. Auditoria
`.pytest_cache/p16_conclusao_local_ampla_hashes.json`: 109 arquivos Python
acompanhados sem mudança de hash durante a suíte. P16 parcial:
autor da troca histórica, crash nativo, origem própria positiva e sequência
física estável não foram encerrados. Sem commit/push.

### P16 — perda do plano, hipótese de restauração contextual — 01/10/2026

Continuação de `caminhos_absolutos_55ee6435...`, base `main`/`90a2fb8`.
Forma parcial criada às 22:43:31.559, antes do timeout; escrita física correta.
`atualizar_plano_turno({})` explica a forma posterior, não o esvaziamento inicial.
SQLite `mode=ro`, dois IDs, somente metadados: chat próprio c19210ad... termina
com dois pares e calma às 22:43:27.933; chat antigo f1dafa7f... é salvo no
encerramento às 22:44:13.810, com entrada antiga e acalmando-se, como o parcial.
Hipótese de restauração sustentada; pedido/autor/PID do writer ainda não provados.

Boot síncrono, inatividade de 600 s, registro local restaurando contexto e
renderização selecionando automaticamente foram falsificados. Escritores
explícitos conhecidos usam APIs já observadas; ausência global não certificada.
Sonda optativa passa a registrar chamadas do gerenciador real e seus IDs/pilhas,
sem título/texto. Falha de gravação não interfere no owner. Dois REDs antes
do candidato de diagnóstico; controle de limpeza já GREEN. **29 focados/vizinhos
aprovados**. Loops ef9eacee... e cdbf0154...: sete turnos, arquivos conferidos,
código zero, voz silenciada; último com 25 publicações e seis registros de
conversa, nenhuma troca/perda durante turnos. RED histórico não reproduzido.

Sem mudança de produção; só sonda e um módulo de testes. 107 Python iniciais
estáveis exceto sonda, total atual 108; HEAD/branch mantidos e diff sem erros.
Última ampla é a anterior (9.307), não repetida. Próxima fronteira: capturar
quem pede a troca entre efeito/finalização. P16 parcial; detalhes no roadmap.

### P16 — continuação de estado/encerramento, causas separadas — 01/10/2026

Base `main`, `90a2fb8`, worktree preservada. Controle instrumentado de caminhos
`caminhos_absolutos_dd30046da88a4c3baee8f3bd22754f06` passou sete turnos e
conteúdo físico, código zero; 25 publicações compartilhadas sem perda de plano.
Opção `--diagnosticar-plano` registra metadados/pilha nas três APIs de mutação,
sem produzir estado/evento/receipt. Pode alterar timing e não observa writers
diretos fora dessas APIs. RED `55ee6435...` continua aberto, sem patch do plano.

Lacuna de observabilidade demonstrada: sentinela desativava a captura antes
dos callbacks registrados anteriormente, que `atexit` executa depois. Dois
REDs em filhos descartáveis precederam o candidato no owner compartilhado
`diagnostico_encerramento`: handler/descritor permanecem até os callbacks
posteriores; desregistro explícito de teste libera ambos. Marker limita seu
alcance ao callback da sentinela. Nove controles do módulo e 20 vizinhos
passaram. Isso corrige a lacuna de captura, sem identificar/corrigir a causa
nativa histórica ou garantir captura após a finalização interna do handler.

Repetição real `p16_falha_recuperacao_bd12a6f56cea42558b1d11cc2e7d77fb`:
duas falhas sob lock sem mudança do arquivo, liberação após barreiras e escrita
exata; receipts distintos, `calma → irritada → acalmando-se`, código zero.
Voz/avatar habilitados e fila concluída; sem nova confirmação física de áudio
ou sequência visual. Falha nativa não reproduzida; não declarar seu reparo
pelo código zero. Artefatos de 30/09 preservados, detalhes no roadmap; P16 parcial.
Ampla: **9.307 aprovados, nenhuma falha, um ignorado/56 subtestes em 231,23 s**;
107 Python com hashes estáveis, HEAD/branch mantidos e diff sem erros.

### P16 — observação do receipt independente da porta de fala — 30/09/2026

Base `main`, `90a2fb8`, worktree preservada. Dois receipts reais de falha de
escrita e uma recuperação eram publicados, mas a emoção permanecia calma.
Primeira fronteira: avaliação acoplada a `falar_por_status`, contornado pela
fala própria de arquivos. TTL, vulnerabilidade e callback ausente falsificados;
replay dos receipts confirmou que o avaliador reconhece a sequência.

Dez REDs antes do candidato. Owner compartilhado `adaptador_resultado` observa
o receipt após aceitação do registrador; fala consome avaliação privada isolada
sem contar evento novamente. Recusa/falha de publicação não observam; falha ou
mutação do observador não certificam avaliação. IDs continuam organizando a
ocorrência, sem conceder autoridade ou deduplicação global entre instâncias.

Runtime `p16_falha_recuperacao_823da9ac0af7457a827625a1455d5784`: três turnos
finalizados, dois `falha_execucao` e um `conteudo_atualizado`; hash protegido
durante lock e conteúdo físico `P16 RECUPERADA` depois da liberação.
`calma 1 → irritada 1 → acalmando-se 1`, com evidência ligada ao receipt do
turno. Pedro confirmou as três falas completas. Avatar irritado falando foi
observado em captura; sequência visual completa não certificada. Processo
principal saiu `0xc000041d` depois do callback da sentinela em `atexit`; essa
marca não conclui os demais callbacks. Limites de encerramento ficam
na investigação de infraestrutura já aberta, sem patch especulativo.

### Identidade de caminho explícito antes da continuidade — 30/09/2026

Pedido adicional de Pedro. Normalização e lookup por basename podiam perder
drive/separadores/grafia ou substituir o alvo por outro arquivo recente. Serviço
de arquivos aceita caminho absoluto, espaços e aspas; não remover suas guardas.
REDs locais/seis instalados antes do candidato em nome natural, roteador,
resolver contextual e gate de argumentos do coordenador. Catálogo vivo e
perguntas naturais explicam uso/indisponibilidade sem executar. Caminho não é
autorização; pedidos negativos/hipotéticos/capacidade permanecem sem efeito.

Raiz adicional demonstrada, sem misturar com identidade: append retirava “linha”
de conteúdo **citado** antes do executor. Seis REDs em caminho/basename/pronome/
elipse; helper único conserva literal citado e mantém moldura sem aspas.

Dois loops completos de sete turnos com código zero e arquivo relido:
`caminhos_absolutos_53a53d3eb5aa4d70ae45158b10455070` e
`caminhos_absolutos_c8bcf0ca678047ea81f5d77463280625`. Alvos homônimos separados,
controle intacto, escrita/append exatos e falha de leitura ausente sem fallback
para outro arquivo. Voz silenciada nesses controles. Seleção final: **146
aprovados**, com sobreposição aos controles anteriores. Ampla estável: **9.303
aprovados, nenhuma falha, um ignorado/56 subtestes em 230,14 s**, 105 hashes
Python iguais, HEAD/branch mantidos e diff sem erros.

### Pendências observadas no loop — 30/09/2026

`caminhos_absolutos_55ee643598eb41f6a2881bd90f87db98` perdeu ID/receipts do plano
após a escrita física no terceiro turno. Arquivo correto; finalização RED.
Hashes descartam edição concorrente de produção. Duas repetições com mesmo
roteiro/diagnóstico passaram, falsificando falha inevitável; writer causal
ainda não localizado. Não aceitar plano vazio nem aumentar timeout para ocultar.

Encerramento P16: Windows registra `0xc0000005` e `0xc000041d` no mesmo PID
principal, WER com módulo desconhecido. Diagnóstico `0x8001010d` do cliente
Terminal também aparece no loop de código zero; não prova morte do cliente ou
causa do erro principal. Associado como novo achado à investigação histórica
de infraestrutura/saída, sem afirmar causa compartilhada. P16 parcial;
detalhes/artefatos no checkpoint do roadmap. Nenhum commit/push/desligamento.

### P16 — continuação da procedência da leitura semântica — 30/09/2026

Mesma perda de fonte já registrada; não acrescentar raiz por frase emocional.
Base `main`, `90a2fb8`, worktree paralela preservada. O preparador preferia
leitura do reparo com rótulo principal; o publicador conferia turno, sem
comparar a leitura à emissão capturada. Normalização pura e ausência de
autorização foram falsificadas como causas da substituição. Onze REDs do
preparo/publicação/transporte e um da API legada precederam seus candidatos.

Leitura original permanece canônica; diagnóstico reparado fica separado,
rotulado pelo host e recusado como fonte de evento. Runtime e publicador
reutilizam a extração da principal tipada; publicação deriva sua própria cópia
e preserva CAS/ocorrência. Sem parser paralelo, chamada adicional ou promoção
de contexto a autoridade. Diagnóstico cobre somente o bruto final disponível.

270 focados/vizinhos GREEN, incluindo dez da composição instalada. Fixtures
antigas passaram a fornecer `leitura_turno` no bruto, mantendo seus controles
de autorização/transação. Portas externas/persistência isoladas não provam
voz/avatar físicos ou interpretação temporal geral. Ampla estável: **9.221
aprovados, nenhuma falha, um ignorado e 56 subtestes em 208,94 s**, 94 Python
com hashes iguais, HEAD/branch preservados e diff limpo. Detalhes e limites
no checkpoint do roadmap.
P16 permanece parcial para o loop desktop contínuo; nenhum commit/push.

### Continuação da correlação P16/AUT-01 — identidade de solicitação — 30/09/2026

Mesma pendência de correlação já registrada, sem outro ID por frase/domínio.
Base `main`, `90a2fb8`, worktree paralela preservada. As 16 falhas históricas
foram localizadas: 12 mesclas por intent, uma identidade ausente no host, três
sondas com chave de callback incorreta. Corrigir a porta dessas sondas permitiu
reproduzir a perda de ID no dispatcher antes de aplicar o candidato.

Owner compartilhado de resultado identifica cópias após validação, recusa
aliases ambíguos e remove IDs/receipts propostos pelo modelo. Dispatcher,
coordenador e adaptador conservam a identidade no envelope. Helper comum dos
dois writers mescla somente mesma ID + intenção canônica; sem ID mantém
ocorrências independentes. Proposta republicada preserva receipt resolvido;
resultado novo não herda confirmação anterior. Contexto de última ação também
exige a mesma ocorrência. Copiador canônico protege params sincronizados.

REDs focados demonstraram a primeira fronteira; controles falsificaram falha
geral do executor e necessidade de apagar receipts legítimos. Sete controles
da composição instalada passaram e replay do writer histórico reproduziu a
transferência de evidência. SQLite temporário/portas externas isoladas;
nenhuma abertura, áudio ou avatar físicos certificados.

Primeira ampla estável: 9.184 GREEN, três RED, um ignorado e 56 subtestes,
222,02 s, hashes iguais em 88 Python. As três fixtures exigiam deduplicação
legada por intent, comando sem ID host ou dois feedbacks no mesmo plano;
ajustes preservam provas de efeito e usam início real de turnos separados.
Seus três módulos passaram em 100 testes. Também 220 focados de identidade,
contexto/continuidade/composição passaram, com sobreposição. Ampla seguinte:
9.187 aprovados/um ignorado/56 subtestes, 213,62 s, 91 hashes Python iguais.
Revisão encontrou recusa de receipt ignorada pelo adaptador: quatro REDs
precederam o refinamento de False explícito no publicador e limpeza dos
marcadores da tentativa anterior. 177 focados/composição passaram. Ampla final
do refinamento: **9.190 aprovados, nenhuma falha, um ignorado e 56 subtestes em
214,32 s**, 91 hashes Python iguais, HEAD/branch mantidos, mutex próprio e
diff limpo. Detalhes no checkpoint do roadmap de personalidade.

P16/AUT-01 continuam parciais. Leitura semântica do reparo ainda pode receber
origem da principal (reprodução local, sem candidato); loop físico mantém
evidência própria. IDs organizam receipts, sem conceder autoridade. Nenhum
commit/push ou desligamento.

### AUT-01 — continuação do callback tardio: ocorrência na publicação, 30/09/2026

Pedido de Pedro para iniciar o plano de assistente autônoma. Mesma pendência de
correlação já registrada, sem ID por frase ou domínio. Base `main`, `90a2fb8`,
worktree paralela preservada. Nova ocorrência coerente com a mesma frase era
atualizada por retorno antigo: writer não recebia ocorrência esperada; leitura
semântica anterior também publicava sem vínculo. Controles falsificaram falha
geral do filtro e necessidade de apagar receipts do mesmo turno.

Candidato reusa a principal tipada e o validador canônico de ocorrência dentro
da transação. Semântica usa origem e CAS do snapshot; runtime recebe callbacks
vinculados da composição e para após recusa pré/pós-dispatch. API legada mantém
compatibilidade sem certificar atomicidade. Fase técnica suprimida identificada
na revisão como consumidor adicional do mesmo contrato.

Trinta e cinco testes locais e 13 da composição principal protegem a fronteira;
446 com vizinhos passaram após o refinamento técnico. Regressão ampla final:
**8.975 aprovados, um ignorado e 56 subtestes aprovados em 202,48 s**, sem falhas.
HEAD preservado, hashes do candidato estáveis e `git diff --check` limpo.

Checkpoint e resultados detalhados no
[plano AUT-01](../planos/PLANO_LAYLAY_ASSISTENTE_AUTONOMA.md#9-checkpoint-aut-01--ocorrência-esperada-nas-publicações-30092026).
O runtime usado é o objeto instalado, sob mutex real de identidade própria.
Provas com portas externas isoladas não certificam
executor físico ou loop da sessão aberta. Mescla por intent, adaptador de receipt
e janela posterior à publicação aceita continuam fora desta entrega. Não encerrar
AUT-01 ou personalidade P16 pelo GREEN intermediário. Nenhum commit.

Atualizado em **23/09/2026**, por Astra e SOL, a pedido do Pedro.

### P01 — generalização v6 e validade de critério revogado, 28/09/2026

**10/10 — duas tarefas produzem erros diferentes:** 48 chamadas auditadas, 12
fontes novas (moldes estreitos), duas tarefas × duas rodadas idênticas. Menção
8/12 literal/alinhada; quatro restantes mudam só caixa inicial. Referente 2/12,
somente indeterminação F/C; 0/9 referentes determinados e 0/12 pares completos.
Não repetir a hipótese de saída única independente da tarefa: nenhuma das 12
duplas retornou a mesma resposta. Seleção de entidade/atributo em vez do nome
ocorre inclusive nos casos diretos, antes de qualquer anáfora. Próximo controle:
pergunta natural direta versus definição abstrata da tarefa, mesmas fontes e
ouro, começando pelos diretos; enquadramento é hipótese, não raiz interna provada.
Não promover/treinar. 16 testes focados passaram; evidências no plano, P01 aberta.

**10/10 — catálogo influencia, mas removê-lo não resolve:** ablação de 52 chamadas,
13 casos conhecidos, duas rodadas iguais. Alinhamento 6/13→7/13, ganho só U1;
literalidade 13/13→11/13, perdas U2/O0. 26 controles históricos reproduzidos.
Mapa completo do host, guardas, fonte, perguntas e schema preservados; omissão
somente da lista enviada ao modelo. Seis REDs permanecem: referência substituída,
recorte amplo ou falha de cópia; nenhuma causa interna única demonstrada.
Falsificada suficiência da retirada do catálogo, não sua influência. Próxima
fronteira: pares mínimos que separem pedido de localizar menção de pedido de
resolver referente, com ouro/certeza distintos. Não promover variante nem remover
mapa de produção; evidências no plano. 14 testes focados verdes; P01 aberta.

**10/10 — papel explícito melhora conteúdo, não preserva menção:** 52 consultas
auditadas, 13 casos × 2 braços × 2 rodadas, ambas iguais. Controle 2/13,
candidata 6/13; cinco ganhos e regressão U0. Novos 1/6→4/6; conhecidos 1/7→2/7.
N0/N1 e C0/C1 distinguem relato externo/conteúdo interno, mas U/A resolvem
referente em vez de copiar menção; U0/O0 fecham alternativas ainda abertas.
Todas as cópias candidatas são literais, não semanticamente aprovadas. Próxima
hipótese: catálogo de aspas pode favorecer seleção de objetos enumerados;
ablação offline deve conservar fonte/pergunta/schema e mapa no host. Não remover
guardas nem promover candidata. 14 testes focados verdes; evidências e limites
no plano. Nenhuma produção alterada nesta frente; P01 continua aberta.

**10/10 — seleção isolada não pronta para encadeamento:** 42 consultas locais
auditadas; por rodada de 7 casos, cópia isolada alinha 1/7, tokens 0/7, controle
conjunto 1/7 e 0/7. Tokens abstêm-se em seis e invertem limites em N1; host
rejeita sem reparar. Cópia confunde menção/referente/âncora, com erro apenas de
capitalização em U2 separado de erro semântico. 14 controles reproduzem o
experimento anterior, sem falha de transporte ou truncamento por limite.
Contrato experimental ainda heterogêneo: `O título` não especifica o mesmo
tipo de relação/papel que os predicados dos demais casos. Investigar isso com
pergunta relacional explícita antes de novas coordenadas ou certeza; hipótese,
não raiz interna provada. Não promover/treinar; P01 permanece aberta. Sonda,
testes e evidências no plano, sem alteração de produção nesta frente.

**10/10 — campos explícitos expõem contradições, mas não resolvem vínculo:** 28
consultas auditadas, controle estável 4/7; candidata alvo 5/7 e 4/7 nas duas
rodadas, conjunto de campos 2/7, conjunção mecânica 1/7. U0 recupera abstenção,
N0 regride; N1 muda resposta com requisição idêntica. Cópia literal não salva
ligação errada, e escopo O1 não literal ocorreu com stop/117 tokens, não limite.
Rejeitar como gate/treino. Próxima fronteira: seleção de argumento apartada da
certeza, diferenciando localização mecânica de interpretação ainda não provada.
13 testes novos, 45 relevantes verdes; somente sonda/testes/documentação, sem
produção ou commit. Evidência completa e limites no plano; P01 aberta.

**10/10 — contrastes novos localizam insensibilidade ao escopo:** 76 consultas
auditadas; duas rodadas iguais. Pares local 6/12, externo 8/12; seleção 4/7 em
ambos. Ambos seguem primeira→segunda, mas não o fechamento da alternativa da
página ausente. Na mesma fonte aninhada, ambos seletores mantêm q0 ao trocar a
relação de escrita externa para ordem interna (alvo q1). Mais contexto não é
explicação suficiente: O1 informa explicitamente o alvo e os pares ainda excluem.
Não confundir informação insuficiente com exclusão, nem recipiente com argumento.
Fonte/offsets/HTTP íntegros; RED é interpretação, sem causa interna única provada.
Próxima hipótese: argumento e escopo explicitados como proposta inspecionável,
antes de rótulo comprimido. Sem produção, treino ou liberação; evidências no plano.
Nove testes novos e 59 regressivos relevantes verdes; suíte ampla anterior não
repetida neste turno. P01 permanece aberta, sem validação de runtime.

**09/10 — comparador independente melhora, mas consenso ainda erra:** 82 consultas
externas auditadas, duas rodadas iguais; pares 23/27 versus 16/27 locais, vetores
11/14 versus 6/14, seleção 12/14 versus 9/14. Mensagens/schemas iguais; backend,
modelo e limite de saída distintos, sem causalidade exclusiva atribuída a pesos.
Perda por par em M2/q1 e no controle M2, apesar do ganho agregado. Concordância
errada em L8/q1, M2/q0 e M7/q0 invalida aceitar acordo como certificado.
Próxima investigação: escopo do vínculo (argumento versus recipiente, alternativas
ausentes), com contrastes mínimos novos antes de treino ou outra variação de
prompt. P01 aberta; nenhum juiz/modelo promovido a produção. Custo observado
US$ 0,0109395; detalhes, hashes e hipóteses no plano.
14 testes focados e 1.614 regressivos relevantes verdes; sem validação de runtime
ou encerramento da raiz a partir desse GREEN.

**09/10 — avaliação por par não resolveu a ligação semântica:** 82 consultas
auditadas, duas rodadas iguais: 16/27 pares e 6/14 vetores completos corretos;
controle congelado 9/14 seleções corretas (tarefas distintas). Nenhum dos sete
pares ambíguos recebeu insuficiente; OR/L3/M2 apoiam ocorrências indevidas e L4
exclui a correta. Projeção e HTTP válidos, controles preservados. Candidata
rejeitada, sem agregação ou produção. Não atribuir a falha a JSON, truncamento ou
contexto removido; causa interna do modelo/representação ainda não isolada.
Próximo contraste proposto: interpretação independente mantendo fontes/contrato,
antes de outra variação de prompt, sem promover outro modelo a autoridade.
Artefato, confusão por classe e hashes no protocolo P01 do plano. P01 aberta.
Validação da ferramenta: 12 testes focados e 1.600 regressivos relevantes verdes;
isso não altera o RED semântico nem constitui validação de runtime.

**09/10 — lista de candidatos preserva ambiguidade, mas perde vínculos claros:**
112 consultas auditadas, duas rodadas iguais: antigo 23/28, candidata 16/28.
Cinco ganhos (L5/L8/M3/M5/M7) e doze perdas pareadas, incluindo duplicatas,
negação, aspas aninhadas, hipótese e ausência de alvo. Critério sem perdas
falhou; não promover. Primeira divergência: candidatos semanticamente
incluídos/excluídos sem suporte, não formato ou transporte. Fonte/identidade
mantidas; instrução/schema mudaram juntos, sem causa interna única provada.
Próxima hipótese é avaliar a relação com cada ocorrência antes de agregar,
sem tratar opinião do modelo como prova. Evidências e limitações no plano.
Sem produção, treino ou liberação; mudanças paralelas preservadas.
1.588 testes relevantes passaram, incluindo treze novos; P01 continua aberta.

**09/10 — ligação identifica ocorrência errada, mas força unicidade ambígua:**
40 consultas auditadas; históricos 12/12, sintéticos 6/8 nas duas rodadas.
OR aponta corretamente para q1, não foco q0; L5/L8 escolhem alvos onde a
fonte não distingue uma ocorrência única. Opção de abstenção e fonte integral
presentes, transporte válido: RED na proposta semântica de unicidade.
Não promover como gate; separar candidatos compatíveis de referência
estabelecida é a próxima hipótese. Artefato completo `retomada1` preservado,
original parcial só com metadata; detalhes/hashes no plano. 1.575 testes
relevantes passaram, incluindo onze novos. Produção não alterada por esta frente.

**09/10 — trecho real ajuda, mas também propaga relação de outra ocorrência:**
72 chamadas auditadas; papel sem trecho 9/12 e 8/12, com trecho 10/12 nas duas.
Ganhos repetidos NS/C0, perda repetida OR: evidência literal da ocorrência
errada muda operação correta para nome incorreto. CX continua errado;
ambiguidade T11 preservada. DA varia no controle sob requisição idêntica,
temperatura zero e digest igual; não contar como ganho repetido nem atribuir
causa ao cache sem experimento. Critério sem regressões falhou, sem promoção.
Próxima fronteira: qualificar relação→ocorrência antes de usar a seleção na
decisão. ID/offset literal não comprova vínculo semântico. Resultados e
limitações registrados no plano; nenhum patch de produção ou treinamento.
1.564 testes relevantes passaram, incluindo oito novos; não encerra P01.

**09/10 — interferência contextual reproduzida, não causa única:** 72 chamadas
auditadas em 18 casos, duas rodadas iguais. DA/H11 falha no isolado apenas
com ação posterior; contexto neutro e ação anterior preservam a descrição.
NS/H05 falha com outra ocorrência idêntica posterior, não com ordem de
texto diferente. Inverter orações recupera o isolado, mas faz o conjunto
selecionar a relação da ocorrência errada em OR. C0 erra mesmo sem oração
concorrente e com seleção correta de `tem o título`: distração não é raiz
única. Fonte/foco/offsets e 32 chamadas históricas conferidos, sem mudança
do modelo. Próximo contraste: braço existente com seleção real explícita,
incluindo seleção errada como controle, sem gabarito e sem promoção.
Resultados/limites/hashes no plano. 1.556 testes relevantes passaram,
incluindo dez novos. Produção e treino não alterados.

**09/10 — transferência rejeita substituição geral por papel isolado:**
80 chamadas auditadas; nas duas rodadas, novos 15/16 no conjunto contra
13/16 no isolado, controles históricos 3/4 contra 4/4. Ganho T03 não compensa
perdas novas H05/H11. Identidades/offsets das duas ocorrências de H05/H06
preservados; HTTP/formato completos. H01 erra nos dois braços. O mecanismo
de ligação entre foco e relação contextual permanece hipótese; não agrupar
automaticamente seleção inadequada e classificação errada com seleção boa.
Próxima fronteira: contrastes controlados de ocorrência/contexto concorrente,
antes de novo candidato. Fontes agora conhecidas, sem revisão independente.
1.546 regressivos passaram (11 novos). Sem produção, treino ou liberação.
Protocolo, hashes, limitações e artefato no plano de ensino.

**09/10 — papel isolado recupera título, evidência extra não acrescenta ganho:**
48 chamadas auditadas, duas rodadas. Conjunto 7/8 em papel; isolado sem/com
trecho real 8/8; composto passa 4→5/8. Único ganho T03, sem perdas pareadas.
Não atribuir melhora à evidência: as duas segundas empatam; muda o pacote de
tarefa/schema/exemplos frente à primeira. T11 mantém fragmento insuficiente
apesar de papel certo. Candidata seguinte é classificação isolada simples,
com transferência ainda pendente; seleção e apoio continuam separados.
Sem produção, treino ou liberação da rede. Protocolo e artefato no plano.
1.535 regressivos relevantes passaram, incluindo os 13 testes novos.

**09/10 — predicado catalogado, ganho restrito:** 32 consultas auditadas em
oito fontes com distratores. Vínculo literal 5→8/8, pista discriminativa
4→5/8 e conjunto 3→4/8, repetidos; papel permanece 7/8. T12 é o único ganho
no composto. Selecionar todos os blocos discrimina 0/8. Enum não é compreensão:
T02/T09 terminam em fragmentos curtos; T03 erra papel mesmo selecionando
`é o título do ensaio, não uma tarefa`. Primeira fronteira de T03 é proposta
semântica, não cópia. Candidato permanece offline; sem treino ou produção.
Protocolo/hash/limites e próxima fronteira registrados no plano.
1.522 testes relevantes passaram, incluindo os 16 do novo instrumento.

**09/10 — transferência rejeita hierarquia como melhoria geral:** 64 consultas
auditadas, 16 casos novos, duas rodadas. Papel 15/16 em ambos os braços;
conjunto base 10/16 e hierarquia 8/16 nas duas. Ganho T15 e perda T03 em papel;
perdas T01/T03/T14 no conjunto. Critério pré-fixado falhou; sem promoção.
Brutos idênticos entre repetições, transporte completo, hashes preservados.
T01 sobrepõe foco, T14 altera acentos; não relaxar guardas. T15 erra papel na
base mesmo com pista certa: interpretação e seleção não são uma única causa.
Checkpoint no plano com hash do artefato e próximo contrato de evidência.
Commit externo `2566b62` preservado; baseline da coleta continua `90a2fb8`.
1.506 testes relevantes passaram na retomada, incluindo os 31 focados.
Reuso futuro de IDs deve superar selecionar todos os blocos: controle de
06/10 já mostrou que cobertura literal isolada não demonstra seleção útil.

**07/10 — hierarquia/ID, 80 brutos auditados:** papel base 7/10 nas duas
rodadas; hierarquia 10/10 e 9/10, com ou sem ID uniforme. E04A/U04 recuperados
nas duas; ID isolado não resolve. E03A oscila apesar de requisição idêntica.
Conjunto base 4/4; hierarquia 6/4; hierarquia+ID 5/4: não houve ganho repetido
de evidência completa. E04A/E04B sobrepõem foco; U02 não copia trecho contíguo;
N06 falha apenas no marcador lexical, não prova erro de sentido. Fonte inteira
e identidade host preservadas. 18 testes novos e 1.493 regressivos passaram
(contagens sobrepostas). Protocolo, hashes, tabela e limites no plano.
Próximo: validar generalização/estabilidade e investigar seleção literal como
fronteira distinta, sem afrouxar guardas. Mesma P01 aberta, sem produção/treino.

**07/10 — hierarquia/ID, protocolo pré-consulta:** quatro braços com dez
fontes conhecidas e duas repetições. Fonte/offsets e host intactos; fatores
são caminho sintático redundante e etiqueta de transporte `foco.id=c1`.
Reutiliza árvore de aspas existente; E05A/B protegem identidade de ocorrências
iguais. Requisição efetiva validada antes da aferição delegada. 80 consultas
pendentes, sem produção ou treino; critérios e hashes no plano.

**07/10 — moldura/foco, 36 brutos auditados:** E04A/U04 erram papel nas fontes
aninhadas e acertam nas versões planas/internas, nas duas repetições; E04B/N03
preservam papel correto. E03A só recupera nome sem a ressalva; antepô-la continua
errado, mesmo selecionando “a exposição foi intitulada”. Host/foco autênticos;
ausência de pista e viés apenas de posição final não explicam esses REDs.
Pontuação, profundidade, IDs e offsets variam juntos: não declarar aninhamento
como causa isolada. E04B mantém sobreposição literal em todas as versões;
U02 mantém paráfrase. 14 testes novos, 35 focados, 1.475 na regressão (sobrepostos).
Próximo contraste proposto: hierarquia sintática explícita e autenticada, fonte
integral preservada e controle de identidade/representação. Ainda sem candidato
em produção; hash, hipóteses e limites no plano. Mesma P01 aberta.

**07/10 — moldura/foco, protocolo pré-consulta:** mesmo proponente e oito
exemplos; 18 fontes variantes em duas repetições. Contrastar citação aninhada,
plana com dois-pontos e conteúdo interno; no título hipotético, retirar ou
antepor a ressalva. E03B/U02/N06 são controles de interpretação/literalidade/
cobertura. Não é patch para remover contexto; coleta pendente, hashes no plano.

**07/10 — ensino contrastivo aferido:** 96 consultas brutas revalidadas;
duas repetições no painel novo de 24 casos. Papel 12→21 em ambas, conjunto
5→16 e 5→17; indeterminação 0→5 de 6 sem falsas abstenções nos 18 conclusivos.
Critério descritivo atendido, não aprovação de produção. Regressão individual
E04A persiste apesar do empate agregado de nomes; E03A/U04 também erram papel.
U04 seleciona pista correta e erra interpretação; U02 acerta indeterminação
e inventa parte do trecho; E04B inclui foco na seleção. N06/E06B ficam fora
da cobertura lexical, o que não basta para declará-los bugs. 21 testes novos,
136 focados e 1.461 na regressão das sondas/contrato (sobrepostos). Artefato,
hashes e limites no plano; próxima fronteira é função do foco em molduras
aninhadas/concessivas, sem relaxar literalidade. Produção e treino intactos.

**07/10 — ensino contrastivo, protocolo pré-consulta:** oito demonstrações
fixas e 24 avaliações novas/separadas; duas repetições de dois braços (96
chamadas). Só mensagens de exemplos variam; materializador, schema e opções
preservados. Ganho deve se repetir sem reduzir contagem de nenhuma classe
conclusiva nem elevar falsos indeterminados. Instrumento e hashes no plano;
coleta pendente neste registro, sem treino de pesos ou patch de produção.

**07/10 — fatorial concluído, nenhuma variante promovida:** 128 respostas
brutas revalidadas, todas completas/HTTP200/shape válido. Na ordem base,
renomeação, prioridade, ambas: papel 24/23/19/18 de 32; conjunto local
(papel + vínculo + pista) 12/9/10/6. Prioridade melhora geometria, mas perde
nomes/operações para outros rótulos conclusivos; indeterminação 0/0/1/1 de 4,
sem falsos indeterminados nos 28 conclusivos. U02 copia pista explícita de
incerteza e erra papel nos quatro braços. Renomear não reduz cópia do foco.
Base também variou 25→24 frente à coleta anterior com requisições idênticas:
não confundir variação com efeito causal comprovado. 1.443 testes relevantes
verdes validam instrumento/contratos, não semântica. Hashes, perdas e limites
no plano; próximo contraste proposto é ensino por exemplos separados de nova
avaliação congelada, ainda não executado. Sem produção, treino ou promoção.

**07/10 — fatorial unidade/indeterminação, protocolo pré-consulta:** comparar
nome `predicado` versus `trecho_externo` e instrução de decidir indeterminação
primeiro, mantendo fonte/materializador/guardas. 32 casos conhecidos × quatro
variantes = 128 chamadas; ordem balanceada, referências intactas. Medir rótulo,
geometria, repetição do foco e falsas abstenções nas fontes conclusivas. 19
testes novos verdes; coleta pendente, protocolo/hash no plano. Mesma P01,
sem alteração de produção, treino ou memória.

**07/10 — materialização host, resultado conferido:** 64/64 HTTP200/JSON/shape/
stop. No contraste contemporâneo, rótulo 24/32 → 25/32, vínculo 8/32 → 16/32,
rótulo + vínculo + pista no predicado 4/32 → 12/32. Há três ganhos e duas
perdas de rótulo; abstenção piora de 1/4 para 0/4. Baseline histórico 23/32
oscilou para 24/32 com mesma requisição: não atribuir essa mudança ao candidato.
Nove predicados sem âncora e sete sobrepostos; oito dos nove mudaram aspas,
mas restaurar apenas grafia em diagnóstico ainda deixa sobreposição/ambiguidade.
H03B parafraseia; H10A escolhe outra ação; U02 seleciona incerteza mas erra papel.
26 novos / 96 focados / 1.424 relevantes verdes, sobrepostos, apenas offline.
Artefato `sonda_predicado_host_v1_ab.jsonl`; hashes/decisão no plano. Manter
materialização como candidato de diagnóstico e investigar unidade contextual
externa e abstenção antes de promoção. Produção/treino intactos, P01 aberta.

**07/10 — predicado proposto / intervalo host, protocolo pré-consulta:**
modelo copia só predicado e propõe papel; host ancora na fonte integral e
materializa intervalo por offsets, reutilizando contrato e guarda anteriores.
26 novos / 96 focados verdes sobrepostos; inclui repetição, aspas aninhadas,
vazio, predicado irrelevante e ambiguidade. Comparação composta em 32 casos
conhecidos, 64 consultas, mesmas referências; coleta pendente. Isso reduz
recópia e não transforma geometria em interpretação. Protocolo/hash no plano;
produção/treino preservados, mesma P01 aberta.

**07/10 — vínculo explícito, coleta encerrada sem promoção:** 64 respostas
HTTP200/JSON/shape/stop, duas recontagens pelo bruto. Rótulos 22/32 → 23/32,
três ganhos/duas perdas, pares 7/12 nos dois; vínculo estrutural só 8/32,
proposta composta local 5/32, abstenção 0/4 → 1/4. Primeira divergência nos
23 enunciados sem âncora: troca de aspas tipográficas por ASCII. Contrafactual
de leitura não altera escore; mesmo restaurando grafia, H11A permanece com
objeto ambíguo e H10A com predicado sobreposto. H07A ancora a pista de título
mas erra papel: cópia não explica toda a interpretação. H04A demonstra
predicado de horário passando estruturalmente sem enquadrar designação.
27 novos / 1.398 relevantes verdes, sobrepostos, apenas offline. Artefato
`sonda_vinculo_enunciado_v1_ab.jsonl` e hashes no plano. Não promover esta
interface, não relaxar guarda, não treinar. Próxima fronteira: separar escolha
semântica e reprodução literal pelo host, sem repetir seleção por IDs já
falsificada. Produção preservada; mesma P01 aberta, sem commit.

**07/10 — vínculo enunciado–ocorrência, protocolo antes da coleta:** nova
sonda offline reutiliza contrato de proposições e identidade canônica; não
cria parser de nomes. Propõe enunciado/predicado/papel, exige objeto nos
offsets exatos do foco e predicado externo. Estrutura não certifica relação
semântica. Mesmo painel conhecido de 32, 64 consultas independentes,
baseline direto intacto, entrada integral sem recortes-oráculo ou gabarito.
Muda prompt + schema, portanto comparação composta. Cobertura lexical no
enunciado/predicado separada do rótulo e do vínculo; vazio conserva revisão.
26 novos / 108 focados verdes (sobrepostos); coleta pendente. Protocolo/hash
em `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md`. Produção/treino não alterados,
P01 aberta, sem commit.

07/10, ablação concluída: quatro intervenções manuais, atual 2/4 → 1/4
(um ganho/duas perdas), direto 1/4 → 3/4 (dois ganhos/nenhuma perda).
Seis controles de input idêntico por prompt tiveram rótulos estáveis;
H02A/H06A ainda erram sem concorrente externo e indeterminação 0/4 em ambos.
Falsificada explicação exclusiva por segundo comando/ocorrência; recortar
não é solução geral. 40/40 HTTP/JSON/shape/stop e mapas revalidados no bruto.
Artefato `sonda_ablacao_contexto_papel_v1.jsonl`, SHA256
`025891330c3cc43350be4ba04336d8396d5bfad6e025374af68691866c7cbb1c`.
18 novos/82 focados/1.371 relevantes verdes (sobrepostos); três testes provam uso do contrato
existente de proposições para ancorar objetos iguais em enunciados distintos,
recusar predicado emprestado e não promover ancoragem à verdade. Próximo:
proposta explícita de vínculo enunciado–ocorrência e indeterminação, não
novo parser ou recorte-oráculo de produção. P01 aberta, sem treino/commit.

07/10, diagnóstico pré-consulta por ablação manual: quatro contextos
recortados + seis controles de input idêntico (quatro indeterminados),
dois prompts congelados, 40 chamadas previstas. Ocorrência preservada por
offset, inclusive segunda string repetida. 15 novos/36 focados verdes,
coleta pendente. Recorte-oráculo não é seletor de produção; muda também
sintaxe/comprimento, logo não prova sozinho causa interna. A guarda literal
corretamente não certifica papel. Sem produção/treino/novo gabarito/commit.

07/10, transferência concluída sem ajustar os prompts: **20/32 → 22/32**,
6/12 → 7/12 pares; quatro ganhos e **duas perdas** (H11A, H05B). Ambiguidade
explícita 0/4 em ambos. Dez erros na leitura direta permanecem em P01, não
viram dez roots. As 64 respostas HTTP200/JSON/shape/stop foram revalidadas
no bruto, focos/offsets e referências autênticos; primeira RED na atribuição
de papel, não transporte/host. Artefato `sonda_papel_transferencia_v1_ab.jsonl`,
SHA256 `2e2c9aa636d79afe2154abfde59ea24be29d454bbaed55d6e6627d0465642075`.
21 novos/67 focados/1.353 relevantes verdes (sobrepostos). Ganho modesto,
com regressões e sem revisão humana independente: **não promover**. Próximo
contrato a investigar: predicação vinculada à ocorrência e indeterminação,
sem consolidar prematuramente suas hipóteses internas. Sem produção/treino/commit.

07/10, protocolo de transferência pré-consulta: 32 casos novos, 12 pares
nome/operação e quatro controles de cada tipo estado/indeterminado; 64
chamadas previstas, 16 AB/16 BA, mesmos prompts congelados. Painel e revisão
local fixados por hash antes de consultar, sem gabarito no modelo. 21 testes
novos/67 focados verdes (sobrepostos). Não é revisão humana independente
nem corpus externo; não mudar produção/treino ou retocar prompts pelo resultado.
Protocolo completo no plano; coleta pendente neste checkpoint.

07/10, conclusão do contraste abaixo, sem ajuste durante a coleta:
**11/20 → 16/20 papéis; 3/8 → 6/8 pares**. Cinco ganhos, nenhuma perda;
Q02A/Q06A/Q06B/Q08B continuam errados na leitura direta, Q08B apenas troca
de erro. Todas as 40 HTTP200/JSON/shape/stop, bruto e requisições revalidados,
referências intactas. Artefato `sonda_papel_leitura_direta_v1_ab_replay.jsonl`,
SHA256 `65bd3c3870df9417dce5e674ff4058262484a14f54fc2f03ef366fa0ad3583be`.
46 novos/1.332 relevantes verdes (sobrepostos). Candidato promissor em painel
conhecido, não holdout nem runtime; primeira RED restante ainda atribuição
de papel no bruto. Próximo: casos independentes pré-congelados, mesmos
prompts, antes de promover qualquer integração. Sem produção/treino/commit.

07/10, próximo contraste congelado antes da coleta: `sonda_papel_leitura_direta_v1`,
mesma fonte/foco/schema/opções/gabarito em 20 casos e 8 pares, alterando apenas
instrução de sistema. 46 testes locais verdes; 40 consultas independentes,
10 AB/10 BA planejadas. Testa a formulação da leitura contextual, não cria
regra para frases históricas nem nova raiz; não promove produção ou treino.
Protocolo e hashes no plano de ensino; coleta ainda pendente neste checkpoint.

07/10, auditoria da classificação com fonte/foco integral versus mesmo input
com contexto externo explícito (coleta com contexto de 06/10): **11/20 e 3/8
pares nos dois braços**. Um ganho Q03A e uma perda Q05B; Q01B/Q06B trocam
erro por outro erro. Indeterminação Q08A/B zero/2 em ambos. Todas as 40
HTTP200/JSON/shape/stop; rótulos errados já no bruto, não rejeição do host.
Primeiro RED observado é atribuição contextual de papel, não delimitação.
Contexto extra não trouxe ganho líquido; não promover para runtime/treino.

**74 próprios, 691 focados e 1.286 regressivos relevantes GREEN**, sobrepostos.
Tentativa ampla interrompida sem resultado de pytest; rerun na retomada
confirmou 1.286. Brutos, denominador, referências, req/host/inventário e
resumo recalculados. Artefato exclusivo
`resultados_testes/sonda_papel_contexto_explicito_v1_ab_replay.jsonl`, SHA-256
`6f5329010a4815ee37a9d97227e5aa9cb981e742e8138b8ce4f8020cfdda425d`.
Próxima hipótese a estudar: predicado que enquadra o foco versus aparência
de ordem/negação, com indeterminação separada de autorização. Não causa
única provada, não implementada nem nova raiz. P01 continua aberta;
produção/worktree e histórico preservados, nenhum commit. Detalhes no plano.

06/10, host delimita todos os contextos externos e Qwen propõe IDs: **20/20
seleções literais válidas/concluídas**, contra zero/20 do controle de índices.
Mas o modelo seleciona `e0/e1` nos vinte casos, empatando com o controle
"selecionar tudo" sem LLM. Cobertura lexical 20/20/oito pares não demonstra
escolha discriminativa ou papel. GREEN estrutural offline, P01 semântica aberta.

40 HTTP200/JSON/stop, sem truncamento; 42 linhas, entrada/host/inventário/
gold/ordem/resumo bruto e disjunção conferidos. **60 próprios, 617 focados,
1.212 regressivos relevantes GREEN**, sobrepostos. Nenhum patch de produção,
treino, materializador ou autoridade. Artefato exclusivo
`resultados_testes/sonda_contextos_enumerados_v1_ab_replay.jsonl`, SHA-256
`506bcd57356b53ab5f54621f5f7d1d1471ffb631d7f27316debcb73c9cfd9905`.
Mesmo HEAD/main/worktree preservada; nenhum commit. Próxima proposta: avaliar
papel com contexto completo versus externo explícito, sem repetir uma seleção
que ainda não supera o baseline sem modelo. Não executada, detalhes no plano.

06/10, seleção de contexto **sem alvo fornecido**, cópia versus índices com
schema em ambos, não promovida. Mesmos 20 casos/oito pares/referências,
40 chamadas reais ao Qwen: índices 20 vazios; cópia 20 recusadas por ausência
de ocorrência externa única. Zero seleção externa válida nos dois. Todas
HTTP200/JSON/`done=True/stop`, sem truncamento. Brutos de cópia: 20 incluem
o foco, 14 ocorrem exatamente na fonte e seis trocam aspas; onze contêm
âncoras lexicais, mas não cumprem delimitação e não recebem crédito semântico.
Primeira fronteira RED observada é a proposta de apoio externo, não o parse
ou a execução. Não atribuir ausência geral de compreensão ou causa interna
única. Guarda preservada, nenhuma segunda etapa/treino/produção alterada.

**72 próprios, 557 focados, 1.152 regressivos relevantes GREEN**, sobrepostos;
uma expectativa de ambiguidade da fixture foi corrigida, não a guarda.
Replay bruto/denominador/requisições/fonte/gold/ordem autenticados. Artefato
`resultados_testes/sonda_contexto_copia_indices_v1_ab_replay.jsonl`, SHA-256
`7ee84d1406ea1d24c3751f6df201bb1298c7b45ddec194cc2d09af03bc4c4bc0`.
Próxima fronteira proposta: host enumerar todos os segmentos externos por
posição e LLM selecionar IDs sem gold/ranking. Ainda não implementada;
mesma P01 aberta, sem criar outra raiz, liberação neural ou commit.

06/10, cópia literal versus índices com **schema nos dois braços**, não promovido.
Seis casos/referências de calibração preservados; alvo explícito, não tarefa
semântica. Positivos **1/3 índices vs 2/3 cópia**, negativos **2/3 vs 1/3**:
empate global 3/6, sem vencedor geral. L02 ganha cópia autêntica de `lume`,
L01 vazio em ambos e L03 correto em ambos. L05/cópia ecoa `lume` só no foco;
L06/cópia ecoa ocorrência ambígua: guarda recusa, sem transformar em abstênção.
L06/índices abstém corretamente; L05/índices viola limites. Não esconder
negativos para promover cópia, nem interpretar eco como localização provada.

Doze HTTP200/JSON/término `stop`, referências pré-consulta, ordem 3 AB/BA,
entrada/opções idênticas, bruto preservado e resumo recalculado conferidos.
Prompt/schema mudam somente pela representação, não é comparação de schema
isolado. Duração acumulada 11,514/7,611 s, sem generalizar eficiência. Digest
igual nos extremos, não invariância contínua. Dois REDs de tradução de cópia
ausente/ambígua para vazio no protótipo; **45 próprios, 485 focados, 1.080
regressivos relevantes GREEN** sobrepostos. Artefato exclusivo
`resultados_testes/sonda_copia_indices_literal_v1_ab.jsonl`, SHA-256
`3e2eac546335f5332d2d59bd52bca0abd63c8c36653259a80da27a4229759f1a`.

Próxima fronteira planejada: seleção de contexto sem fornecer o alvo de apoio
na entrada, comparando representações com schema no painel semântico preservado.
Host segue dono de ocorrência/offsets, LLM apenas propõe apoio. Não executado
aqui, nenhum treinamento ou migração por empate estrutural. P01 aberta,
produção/memória/rede ativa/runtime intactos; worktree paralela e histórico
preservados, nenhum commit. Detalhes no plano de ensino.

06/10, calibração literal explícita, **não promovida**. Seis fontes sintéticas
separadas, três positivos e três negativos; esperado host congelado/calculado
antes da geração, sem índices ou tipo do caso no prompt. Reuso das guardas/
tokenização/captura, tarefa sem papel. Positivos **1/3 em ambos os formatos**;
negativos **2/3 schema vs 1/3 JSON genérico**. L03 materializa `bruma clara`
corretamente `[0,2)` em ambos, falsificando incapacidade universal de emitir
coordenadas ou falha universal do materializador, mas não prova confiabilidade.
L01/L02 (`lume` antes/depois) retornam vazio; não inferir causa por tamanho/grafia.
L05/alvo no foco propõe índices fora dos cinco tokens: `[9,13)`/`[2,6)`,
rejeitados sem reparar. L04/ausente dá `{}` inválido no genérico; L06/ambíguo
dá vazio correto em ambos. HTTP200/JSON/término `stop` em todas as 12 consultas;
sem corte/erro de parse que explique as falhas. Sem taxa agregada que esconda
os positivos RED e sem considerar vazio prova de contexto ausente.

Artefato exclusivo `resultados_testes/sonda_extracao_literal_v1_calibracao.jsonl`,
SHA-256 `0745102a0353c5a24287366a3530d3d650cbe54ab9e8d7eab4d642a1320ddd91`,
14 linhas; resumo bruto recalculado/ordem 3 AB/BA conferidos. Digest igual nos
extremos, não determinismo contínuo. Dois REDs do oráculo no protótipo antes
da guarda de escopo/unicidade; **44 próprios, 440 focados, 1.035 regressivos
relevantes GREEN** com sobreposição, sem concluir qualidade semântica/runtime.
Base `main/90a2fb8`, histórico/worktree preservados. Próximo contraste planejado:
cópia literal versus índices na mesma tarefa explícita, host dono de ocorrência/
offsets, sem usar copia como prova semântica nem migrar por um pequeno placar.
Não executado aqui. P01 aberta, sem produção, treino, memória, rede ativa,
efeitos externos ou commit. Detalhes no checkpoint do plano de ensino.

06/10, controle isolado do schema na primeira seleção, **não promovido**.
Mesmo prompt/fonte/foco/tokens/opções; apenas `format` muda entre schema
restritivo e JSON genérico. **20/20 listas vazias em cada braço**, zero
intervalos/seleções válidas/cobertura local. Todas as 40 respostas HTTP200,
JSON parseado, `done=true`, `done_reason=stop`, oito tokens cada; conteúdo bruto
uniforme `{"evidencias": []}`. Sem erro de transporte ou truncamento observado.
Logo schema restritivo não é explicação suficiente do zero nesta configuração;
parse que apagaria trechos também não explica a coleta. Modo JSON continua
nos dois braços: não concluir ausência de toda influência do formato, nem
incapacidade do modelo ou qualidade zero de uma segunda etapa não executada.

Base `main/90a2fb8`, worktree paralela/histórico preservados; 10 AB/10 BA,
requisições e resumo recalculados, digest igual nos extremos (não invariância
contínua). Durações acumuladas 23,627 s / 18,873 s, sem alegar ganho de latência.
Instrumento/teste novos `sonda_schema_selecao_v1`, sem alterar sondas antigas.
Três REDs de captura antes do parse no protótipo; **44 próprios, 396 focados,
991 regressivos relevantes** GREEN, com sobreposição. Artefato exclusivo
`resultados_testes/sonda_schema_selecao_v1_ab_replay.jsonl`, SHA-256
`a4fa8e2780d7af2c7f4fe2439bfce534cdbd2d604f9629479eccc77dc0a5aec6`.
Preserva texto HTTP/conteúdo/finalização, não bytes/headers completos.

Próximo controle planejado: extração literal explícita em fontes sintéticas
separadas, para distinguir capacidade de coordenadas da seleção semântica.
Positivos/negativos congelados antes de consulta, sem passar índices/resposta
nem usar o gabarito semântico como instrução. Não executado aqui. Mesma raiz
P01 permanece aberta; produção, treino, memória, rede ativa e runtime da
Laylay não alterados. Provas e limites no plano de ensino. Nenhum commit.

06/10, retomada do desenho de seleção externa antes do papel, **não promovido**.
Mesmo HEAD `main/90a2fb8`, painel/revisão e dependências congelados; alterações
paralelas preservadas. Qwen local real em replay dirigido, não runtime da Laylay:
controle acoplado **15/20 papéis brutos alinhados, 6/8 pares completos**,
mas **0/20 evidências válidas**, 19 listas vazias e um intervalo vazio Q09A
(`inicio=fim=20`). Envelope de papel válido 19/20, alinhado conferido 14/20;
papel bruto é aferido independentemente da seleção.

Candidato com seleção separada: **20 listas vazias, zero elegíveis e zero
segundas consultas**. Apoio/papel locais conjuntos 0/20 em ambos; a qualidade
condicional da segunda etapa é não estimável, não acurácia zero. Não fabricar
papel `indeterminado` ou ausência a partir da abstenção. Primeira fronteira
observada permanece na proposta do selecionador, antes da guarda/cobertura.
Separar tarefas neste pacote não resolveu esse RED; não prova incapacidade
do modelo, inutilidade do contexto ou falha universal de dois estágios.

Coleta completa: 40 consultas, zero erros, 42 linhas, 10 AB/10 BA. Durações
acumuladas 44,676 s / 36,022 s; digest igual nas leituras extremas, não prova
de invariância contínua. Variação do controle histórico 14/20 → 15/20 impede
atribuir diferenças entre rodadas ao candidato. Artefato exclusivo
`resultados_testes/sonda_vinculo_duas_etapas_v1_ab_replay.jsonl`, SHA-256
`5c188b8ec0c03847a1fa953d3d574ed5eb5536e085acd153c2ed1d779b91b240`;
script/teste novos `sonda_vinculo_duas_etapas_v1`. **187 próprios, 352 focados,
947 regressivos relevantes** GREEN, sobrepostos; 19 REDs da guarda de duração
reproduzidos nesta retomada antes do candidato mínimo no instrumento.
JSON parseado preservado, sem HTTP bruto/motivo de término. Próximo controle
planejado: schema restritivo versus JSON genérico na mesma primeira tarefa,
com registro bruto, sem forçar seleção. Não executado aqui; P01 aberta,
nenhuma produção, treino, memória, promoção neural ou commit. Provas completas
no checkpoint de 06/10 do plano de ensino; não adicionar outra raiz por caso.

29/09, replay diagnóstico de coordenadas, **não promovido**. Reusa os 20
casos/gabarito congelados e a mesma tarefa de vínculo nos dois braços;
diferença única: retirar `inicio/fim` dos tokens enviados ao Qwen. Host
mantém offsets autênticos; foco/aspas ainda expõem posições de caracteres.
Controle e projeção: **12/20 vs 14/20** papéis alinhados; **3/8 vs 5/8**
pares completos. **0/20 evidências válidas em ambos**: listas vazias
**15 vs 18**, envelopes de intervalo inválidos **5 vs 2**. Redução de
envelopes inválidos não é recuperação de evidência nem suporte semântico.

Três melhorias de papel (Q02A/Q03B/Q04B), uma regressão (Q05A), Q01B troca
de erro. Não usar como holdout novo, prova de causa exclusiva, ganho geral
ou autorização de treino/runtime. Controle repetido também mudou respostas
em relação ao A/B histórico, apesar de temperatura 0; conservar os dois.
Digest igual no início/fim desta rodada, sem garantia de invariância contínua.
Retirar os offsets dos tokens não basta para superar o RED de evidência.

**64 testes novos; 760 regressivos relevantes verdes**, com sobreposição;
RED da projeção reproduzido antes da mudança, validação preserva payload,
materialização, rejeição atômica e métrica de papel independente. Script/teste
novos `sonda_coordenadas_vinculo_v1`; artefato exclusivo
`resultados_testes/sonda_coordenadas_vinculo_v1_ab_replay.jsonl`.
Próxima fronteira: estudar seleção literal externa separada da classificação
de papel, sem obrigar evidência falsa nem deduzir ausência de uma lista vazia.
Produção, memória, treino e runtime não alterados; nenhum commit.

29/09, vínculo contextual com intervalos: contraste offline **não promovido**.
20 fontes novas e revisão congeladas antes da geração; mesmo Qwen, entrada
tokenizada e foco nos dois braços. Baseline mantém prompt/schema do papel;
candidato acrescenta proposta de até dois intervalos externos ao foco.
Rótulos brutos alinhados: **14/20 direto vs 12/20 com evidências**; pares
contextuais completos: **5/8 vs 2/8**. Não comparar ao 10/16 anterior, de
outro painel e outra apresentação. Este A/B não demonstrou benefício.

No candidato, **0/20 evidências literais válidas**: 15 listas vazias e cinco
propostas com intervalos inválidos. Os 12 rótulos alinhados foram contados
independentemente dessa guarda; não é queda artificial causada pelo veto.
A primeira fronteira da evidência falha antes da cobertura das pistas: não
há vínculo materializado que permita avaliar suporte semântico. Entrada
expõe `inicio/fim` de caracteres, enquanto saída pede `inicio/fim` de IDs
de tokens; ambiguidade de coordenadas é hipótese de apresentação, ainda não
contrastada, não causa exclusiva demonstrada dos erros de papel.

Reuso do tokenizador, fonte/foco e roles existentes; **58 testes novos, 696
regressivos relevantes verdes** (141 focados com sobreposição). RED da própria
sonda permitia consultar foco citado vazio; guarda mínima passou a recusá-lo.
Artefato preservado: `resultados_testes/sonda_vinculo_contextual_v1_ab_primeira.jsonl`.
Próxima falsificação: separar as coordenadas apresentadas ao proponente das
coordenadas originais mantidas pelo host, sem alterar fonte/foco, semântica
esperada ou gabarito, em replay explicitamente diagnóstico. Nenhuma promoção,
produção, treino, persistência, runtime da Laylay, efeito externo ou commit.

29/09, papel contextual de foco host: diagnóstico offline **não promovido**.
Inventário distingue owners: aspas/ocorrência podem ser reutilizadas; o
guardião factual tipifica destaques da fala da assistente, não é extrator
genérico da entrada; modalidade continua dona da autorização. Não foi
encontrada API pública que autentique o papel semântico de cada foco original.
Catálogo antigo oferece só fonte inteira e aspas: operação externa compete
como trecho longo com nome curto. L05/cópia reconheceu a oração operacional,
mas ela não existia como candidato; não agrupar esse RED com erro semântico.

Nova tarefa reduzida marca um foco pelo host e remove competição/“menor”.
16 casos novos, revisão congelada antes da geração: Qwen real **16/16 saídas
válidas, 10/16 papéis alinhados**, apenas **2/6 pares contextuais completos**.
Nomes 3/6, operações mencionadas 5/6, expressões sem operação 2/2,
indeterminados 0/2. Nos seis pares, conteúdo focal idêntico muda de função
nominal para enunciado de operação; nomes não viram ordens por aparência.
P01A/P02A/P06A ainda leem nome como operação; P03B reduz enunciado negado a
expressão sem operação; P08A/P08B decidem fontes explicitamente ambíguas.
Erros persistem sem competição ou reescrita: esses fatores não são explicação
suficiente de todas as divergências. Dois pares completos também impedem
afirmar que o modelo nunca usa contexto. Não comparar 10/16 ao antigo 6/12:
tarefas diferentes e foco fornecido pelo host. Painel dirigido pelos REDs,
não holdout independente do pipeline. Artefato exclusivo:
`resultados_testes/sonda_papel_trecho_v1_primeira.jsonl`.

**43 testes novos; 638 regressivos relevantes verdes** (83 focados com
sobreposição). Auditoria retirou ambiguidade da fonte P01A antes de congelar;
nenhum ouro ajustado após gerar. Três REDs da própria aferição (duplicata,
ID desconhecido, cobertura faltante) corrigidos para recusar resumo parcial.
Próximo contrato a estudar: vínculo contextual com evidência literal, não
só enum de papel; a evidência também permanece proposta e nunca cria efeito,
autoridade ou vigência. Só depois comparar sua contribuição numa mesma tarefa
final. Fontes/contagens anteriores preservadas; sem produção, treino,
persistência, runtime da Laylay, liberação da rede ou commit.

29/09, contraste de seleção literal: candidato offline **não promovido**.
Reusa fonte/âncora e aspas canônicas para catalogar a fonte integral e todos
os conteúdos citados, inclusive nomes e citações aninhadas. O host materializa
IDs com offsets; não valida significado, autorização ou vigência. Dois REDs
de adulteração de tipo (`0.0`/`False` no lugar de offset inteiro) reproduzidos
e corrigidos na guarda do catálogo. **40 testes novos; 595 regressivos
relevantes verdes**, com sobreposição, sem validação do runtime da Laylay.

Qwen real em 12 fontes novas, tarefa/catálogo iguais entre cópia e ID:
saída literal válida **11/12 vs 12/12**, seleção alinhada à revisão local
**6/12 vs 6/12**. Há duas melhorias e duas regressões no ID; não sustenta
ganho semântico consistente. Ambos selecionam filename com aparência de
comando, expressão sem operação e escolha arbitrária em comparação sem foco.
ID também seleciona nome da tomada e se abstém de hipótese sem aspas.
A falha literal de cópia neste painel é subtrecho fora do catálogo, não
reescrita de aspas. Nas duas citações históricas, ambos acertam **2/2** na
tarefa menor; replay diagnóstico não prova correção da extração completa.
Controle histórico mantém `Usei` errado mesmo reparando só as aspas em memória:
cópia não é explicação exclusiva. Artefatos exclusivos
`sonda_selecao_literal_proposicao_v1_ab_primeira.jsonl` e
`sonda_selecao_literal_proposicao_v1_historico_diagnostico.jsonl`, em
resultados_testes. Ouro/contagens anteriores intactos. Próxima fronteira:
papel do trecho na oração — operação mencionada versus nome/metalinguagem —
antes de tipar objeto/polaridade. Sem produção, treino, integração, registro
de vigência, efeito externo ou commit.

29/09, representação de proposição/objeto/moldura: protótipo **inerte**, não
promovido. Reusa `FonteDidatica`, âncora literal e mapeador canônico de aspas;
conserva fonte integral, pares aninhados, polaridade proposta e múltiplas
proposições com seus próprios objetos. Parentais exigem mesma fonte,
contenção e ausência de ciclo. Listas vazias e molduras omitidas não provam
ausência de evento/discurso direto. Literalidade não autentica papel,
polaridade, enquadramento ou identidade; nenhum desses dados registra vigência.
Auditoria corrigiu um defeito do próprio protótipo: origem list/dict lançava
TypeError. Dois REDs reproduzidos na guarda de origem antes da correção de tipo.
**63 testes novos; 555 regressivos relevantes verdes** nesta seleção.

Piloto Qwen real de oito fontes novas, em arquivos/IoT, com gabarito local
congelado: estrutura ancorada 6/8, quantidade do piloto 5/8, predicado 5/8,
objeto completo 3/8, papel 5/8, polaridade 0/8, cadeia de molduras 4/8;
**0/8 completos alinhados à revisão local**. Não interpretar essas contagens
como verdade semântica: F01/F03 omitem só o artigo do objeto; moldura extra de
relato pode ser plausível nas falas de uso metalinguístico; I03 propõe também
o estado perguntado. O piloto exige uma operação principal, não cobertura de
todas as proposições. Nas duas citações, primeira fronteira RED é cópia de
aspas tipográficas como ASCII; no bruto escolhe `Usei`, não a operação interna.
Pedidos sem negação recebem polaridade `negativa`, hipóteses `indeterminada`:
há divergência de interpretação da dimensão, não prova de causa única.
Artefato exclusivo: `resultados_testes/sonda_proposicoes_mencionadas_v1_primeira.jsonl`.

Auditoria do experimento anterior também delimitou seu GREEN: mínimos de
O03/O05 permitem perder pergunta/citação externas, enquanto O04/O06 exigem
modalidade. Isso mede seleção local, não preservação uniforme da moldura.
Painéis/gabaritos e contagens históricos foram preservados, sem reclassificação
retroativa. Próxima fronteira de P01: selecionar a proposição literal sem
recopiar o envelope do host, antes de tipar seu objeto/moldura. Separar negação
gramatical de valor da ação e certeza de ocorrência em controle próprio;
não acrescentar outro gate de ausência ou ampliar o prompt por palavras-chave.
Sem produção, treino, integração, escrita de vigência ou runtime da Laylay.

29/09, presença/escopo antes do alvo: candidato **não promovido**. Em 16
falas novas congeladas, direto e estagiado acertam 11/16 alvos. Estagiado
alinha presença em 11/16 e todas as fronteiras em 10/16; corrige menções
irrelevantes, mas perde citação, hipótese e uma abstenção por alvo desconhecido.
Replay conhecido: 10/12 direto, 9/12 estagiado. B09 fica correto no candidato,
sem compensar regressões. Não declarar root corrigida por esse turno.
Contraste diagnóstico com mesmo prompt/schema e só a fonte na primeira
chamada: presença 11/16 contra 10/16 com cadastro nessa repetição. Erros em
citação/hipótese/objeto errado continuam em ambos; exposição de IDs não é
explicação suficiente. O01 variou com entrada preservada; não inferir ganho
reprodutível pela temperatura zero. **492 regressivos verdes**, 24 novos.
Produção/treino preservados, sem escrita de vigência. Três artefatos
`sonda_operacao_antes_alvo_v1_*` em resultados_testes. Próximo contrato:
separar proposição/evento mencionado, seu objeto e sua moldura discursiva;
não reduzir falta de adoção/identificação a ausência de operação.

29/09, vínculo nominal inventariado: nova sonda offline usa as guardas reais
de origem/escopo/TTL/cobertura do `InventarioContextual`, sem alterar seu
resolver conservador. Cadastro explícito do painel fornece nomes e IDs;
host ancora todas as ocorrências com offsets, inclusive negação/citação.
Não inventar antecedente a partir de um pedido nem extrair cadastro completo
do histórico. Ocorrência de nome registrado não certifica referente semântico.
Qwen real em 12 casos novos congelados: cadastro **10/12**, mesmo cadastro
com âncoras **11/12**. Apenas B08 muda para abstenção correta; B09 continua
confundindo menção sem operação com alvo de mudança, nos dois braços.
Não comparar esse número com os antigos: a tarefa/entrada são diferentes.
**468 regressivos relevantes verdes** nesta seleção (62 na seleção focada,
com sobreposição). Não substituem a seleção anterior de 520. Artefato:
`resultados_testes/sonda_alvo_inventariado_v1_ab_primeira.jsonl`.
Sem produção, treino, integração ou escrita de vigência. Ganho pontual, não
promoção. Próxima fronteira: provar presença e escopo da operação antes de
usar uma identidade mencionada, mantendo ato de fala separado da autorização.

Diagnóstico por campo, 29/09, base limpa `90a2fb8`: relação final não pode
ocultar erro de ato/alvo. No painel v2 conhecido (14 falas), conjunta:
ato 7/14, alvo 11/14, operação 8/14; todos os campos corretos em 3/12 casos,
apesar de 9/12 relações finais alinhadas. Separada: 7/14, 2/14, 9/14 e
1/12 completo, relação 4/12. Destacar a regra na entrada conservando prompt
e schema não alterou alvo: 2/14 nos dois formatos. Nenhum candidato promovido.
API pública canônica observada com padrões reais, sem callbacks de laylay.py:
não fornece identidade de regra comparável e usa modalidade ampla. Não
contar isso como validação da composição/runtime. 520 testes didáticos verdes.
Próximo contrato: menção → identidade ancorada da regra, com ato/operação
avaliados em suas fronteiras. Saídas completas preservadas nos dois JSONL
`sonda_relacoes_dimensoes_*_diagnostico` de resultados_testes.

Comparação posterior em 29/09: candidato offline separando ato/alvo/operação
**não promovido**. Em 12 casos novos congelados, relação final alinhada em
8/12 contra 6/12 do baseline isolado; no replay dos 12 históricos, 7/12 contra
9/12. Melhora em perguntas não compensou regressões em negação, conversa
irrelevante e ambiguidade. 510 testes didáticos verdes provam contratos,
não eliminam esses erros reais. Artefatos `sonda_relacoes_fontes_v2_ab_primeira`
e `sonda_relacoes_fontes_v2_v1_ab_diagnostico`, em resultados_testes, JSONL.
Não ajustar painel/gabarito aos erros. Nenhuma guarda ou runtime alterado.
Próxima fronteira: validar ato e alvo separadamente, incluindo serviços
canônicos existentes, antes de compor uma relação ou liberar vigência.

Experimento de relações em 29/09: a fonte alvo é fixa e cada fala posterior
recebe uma relação **proposta**, sem registro de vigência ou liberação.
Painel local de 12 casos congelado antes do Qwen: saída conjunta com citações
teve 5/12 casos completos alinhados (7/12 com ancoragem correta). Separando
cópia literal no host e uma relação por chamada, replay diagnóstico ficou
em 9/12 (12/12 ancorados). Restam pergunta interpretada como revogação,
revogação de outro alvo e citação confundida com manutenção. Não generalizar
9/12 para produção: não é novo holdout, nem revisão humana independente.
Resultados exclusivos em `resultados_testes/sonda_relacoes_fontes_v1_*.jsonl`.
486 testes didáticos verdes (27 novos); três erros reais do modelo preservados.
Nenhum veto foi relaxado; modelo não escreve no registro confiável.

Continuação em 29/09: corrigida a lacuna lexical já registrada abaixo,
`maior/menor ou igual a número`. O `ou` interno é parte de um comparador,
não uma junção de condições. O mesmo sinal literal serve ao segmentador
e à auditoria do grafo; comparação inclusiva conserva a igualdade no limite.
12 REDs reproduzidos antes do candidato; controles cobrem junção real,
negação, unidade, limiar, decimais negativos e contexto revogado. Replay
diagnóstico com Qwen real: `TANQUE_INCLUSIVO` agora alinhado até o grafo;
câmara preservada; duto revogado continua bloqueado (modelo ainda erra).
**459 testes didáticos aprovados**, compilação e diff-check limpos.
Não é treino nem novo holdout. Nenhum runtime alterado. Vigência semântica,
números por extenso e efeito `classificado como` continuam pendentes.

Correção posterior (28/09): o **RED histórico passou no caminho automático**
da sonda. `conferir_qualificacao_na_conversa` agora exige cobertura do contexto
posterior à regra antes de comparar. Texto do usuário não conferido produz
`contexto_criterio_pendente`, não revogação afirmada. Leitura numérica integral
representada pela premissa pode passar; ressalva adicional não. Revisor
explícito pode decidir sobre o snapshot completo, sem autoaprovação.
**431 testes aprovados** e repetição real com Qwen: duto revogado bloqueado,
câmara/limiar negativo e rotor/condição necessária preservados. Modelo ainda
erra seleção; não contar o veto como aprendizado. Sem execução da Laylay.
Cobertura é conservadora: conversa posterior não numérica, mesmo irrelevante,
exige revisão. Não há ainda interpretação geral de revogação/substituição.
Correção validada no escopo da sonda, raiz semântica mais ampla permanece
parcial. Os parágrafos seguintes preservam o histórico anterior ao patch.

Continuação: contrato explícito de vigência implementado **offline/opt-in**
em `scripts/analises/contrato_vigencia_criterios.py`. Registro pertence ao
revisor confiável e vincula decisão ao grafo, alvo, escopo e conteúdo integral
ordenado do contexto. Mudança exige nova revisão; conflito permanece pendente.
Pergunta/negação/outra regra não são classificadas por palavras-chave.
**417 aprovados e 1 RED original ainda aberto**: rota automática não dispõe
de revisor integrado e continua baseline. A rota opt-in bloqueia sem revisão,
inclusive no caso histórico, mas isto não comprova interpretação da revogação.
Sem chamada a modelo, treino, runtime ou encerramento da raiz. A API de escrita
do registro deve ficar exclusiva de um owner confiável; não é verificador
automático da decisão humana/modelada que alguém lhe entregar.

- Painel novo de 12 casos, congelado antes da medição real: seis positivos
  (inclusive construções fora da gramática) e seis negativos/sem vínculo
  comprovado. Qwen original **0/6** positivos completos; segmentado **3/6**.
  Seleção exata **5/12** e **zero abstenções corretas** nos dois braços.
- Limites distintos: `maior ou igual` é segmentado como disjunção; `vinte`
  não é normalizado a número; `classificado como` não entra na gramática.
  Não contar veto de frase válida como acerto, nem trocar o gabarito.
- **RED aberto prioritário:** regra revogada em outra fonte do mesmo contexto
  ainda chega à comparação no grafo. Modelo erra a seleção, normalizador
  recebe só a fonte escolhida e grafo confere observação, não vigência.
  Reproduzido sem modelo/gabarito, com controle idêntico sem revogação.
  Nenhuma autorização de fala/efeito: barreiras globais permanecem falsas.
- **399 testes aprovados e 1 RED preservado**, sem xfail. Teste:
  `scripts/tests/test_criterio_revogado_nao_fundamenta_qualificacao.py`.
  Artefato real: `resultados_testes/sonda_criterios_v6_ab_primeira.jsonl`.
  Próxima prioridade: contrato de validade/contexto da fonte antes de ampliar
  gramática ou treinar. Sem patch de runtime, treino ou liberação da rede.

### P01 — comparação real da normalização segmentada, 28/09/2026

- Opção offline separa condição/consequência/direção literais dos cinco slots
  propostos pelo Qwen. Reusa os segmentadores existentes; o caminho original
  continua padrão. Fonte/gabarito não são modificados pelo proponente.
- Painel v5 congelado antes das consultas: cinco positivos e quatro negativos,
  ordem das fontes e dos braços alternada. `qwen3:4b-instruct`, temperatura 0:
  **original 0/5 positivos completos; segmentada 5/5**. Seleção exata permanece
  5/9 em ambos: modelo errou os quatro negativos. Não contar veto como acerto
  do modelo. Guardas bloquearam todos os negativos; nenhuma autorização.
- **392 testes didáticos verdes**. Artefato bruto exclusivo:
  `resultados_testes/sonda_criterios_v5_ab_primeira.jsonl`. Sem treino/runtime.
  Pequeno painel de gramática estreita e revisão local, não prova de
  generalização. Próximo passo: ampliar construções/abstenções fora destes
  exemplos, mantendo esse resultado congelado e critérios independentes.

### P01 — consequência literal no avaliador offline, 28/09/2026

Continuação — sujeito da consequência: seis REDs demonstraram que a menção
na condição validava indevidamente outro sujeito (quatro domínios), pronome
sem vínculo ou descrição duplicada. O grafo agora exige descrição ancorada
completa e única compatível com o sujeito extraído; não usa ID, grandeza ou
substring como alias. **371 testes aprovados**, inclusive fluxo composto da
sonda com proponente controlado e guardas reais. Sem modelo/runtime/treino.
A fixture que confundia sensor e solo foi corrigida e ganhou teste negativo
histórico. Painéis v1/v2 preservados: dois casos de equivalência não demonstrada
agora ficam pendentes; v4 permanece intacto e mantém os cinco controles
positivos. Compatibilidade literal ainda não certifica identidade semântica.

- Reproduzida sem modelo/gabarito uma lacuna na avaliação: rótulo pedido
  preenchia o efeito do grafo, e menções na regra inteira permitiam avançar
  a comparação numérica em ação de alarme e consequência negada. Não houve
  aprovação de fala nem efeito externo; não confundir com falha de execução.
- Seis REDs e controles positivos sustentaram uma guarda compartilhada de
  consequência qualificativa na fonte integral. Trecho, offsets, predicado,
  sujeito literal, polaridade e prefixo de escopo ficam explícitos.
- 360 regressivos didáticos verdes; replay v4 bloqueia os dois negativos e
  preserva cinco positivos. Sem novo treino/chamada ao Qwen/runtime; hashes
  congelados preservados. Detalhes em `../PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md`.
- **Parcial, não encerrado:** gramática literal limitada; identidade do
  sujeito e escopo ainda não comprovados, e propostas do modelo seguem sem
  ganho novo medido. Pertence à investigação P01, não é outro ID por frase.

### Saída estruturada da CLI versus filtro global de logs — 29/09/2026

- Base `90a2fb8698541119f523c0a22fa4de0187cbaf92`, main. No passe ampliado
  de personalidade viva/P16, 8.273 testes passaram e quatro testes da sonda OpenRouter falharam
  por saída JSON vazia. Os 12 testes daquele módulo passaram isoladamente.
- São quatro sintomas da mesma fronteira: a composição instala um `print`
  global filtrado, e a CLI publicava seu resultado estruturado por esse canal
  de logs. Um RED com `criar_print_filtrado` real e captura de stdout reproduziu
  a perda do JSON sem chamar API externa. A primeira tentativa não alcançou
  a fronteira por faltar o lock da fixture; ela foi corrigida antes do RED
  causal, sem alteração de produção.
- Owner corrigido: `scripts/analises/sonda_openrouter_fronteira.py:main`
  escreve o resultado JSON diretamente em stdout. Logs podem ser filtrados;
  o resultado consumível da ferramenta mantém seu canal observável. O teste
  conserva a supressão de logs e verifica JSON válido sem publicação da chave.
- Os controles da CLI, DEV, latência com importação da composição e emoção
  passaram juntos (313 testes). Causa separada da prioridade emocional e dos
  julgamentos do modelo: nenhuma fonte, gabarito, confiança ou autorização
  da sonda foi alterada.
- A suíte completa final passou com 8.285 aprovados, 1 ignorado, 14 xfailed
  e 56 subtestes aprovados. Os quatro sintomas desapareceram pela correção
  no canal de resultado, mantendo as expectativas dos testes existentes.

### P16 — procedência do receipt na avaliação emocional — 29/09/2026

- Base `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`, worktree paralela
  preservada. Não é um ID por frase: a responsabilidade depende de evidência
  explícita, e a fala precisa consumir o receipt da mesma ocorrência.
- Primeira divergência de transporte: `marcar_resultado` publicava contexto e
  origem `executor`; `falar_por_status` reconstruía outro resultado sem esses
  campos, embora conservasse o ID. Normalização e troca de ID foram falsificadas.
  REDs em aplicativos e IoT usam registrador, avaliador, publicador e setter
  compartilhados reais. O snapshot por invocação agora transporta contexto e
  origem só após publicação, com concordância de marcador, IDs, intent, status,
  alvo e flags. Falha/republicação invalida o snapshot; mutação externa é isolada.
- Primeira divergência de confiança: ausência, zero e valor inválido viravam
  98%, e NaN virava 100%. Confiança de atribuição agora precisa ser explícita,
  finita em `[0,1]`; booleanos não são probabilidade. Repetição não promove
  atribuição explicitamente incerta. Resultado sem origem do executor permanece
  inferência sem expressão e não alimenta nem interrompe o histórico causal.
- O primeiro roteiro real, após a guarda e antes do transporte, confirmou a
  abertura e sete receipts redundantes, mas ficou em 4/13 por estado neutro:
  a reconstrução sem origem era a primeira fronteira RED. Com transporte, 12/13;
  o restante era `app_focado`, efeito real de foco, não redundância. A preparação
  final usa maximização observada antes desse trecho, mantendo expectativas
  emocionais e sem injetar estado. O roteiro de 14 turnos passou 14/14,
  zero alertas, p95 10,947 s, em
  `resultados_testes/roteiro_teste_personalidade_viva_p16-20260929-225617-497865`.
  Auditoria dos planos confirmou nove IDs distintos, sete redundâncias reais,
  continuidade da causa na conversa/desculpa e limpeza nos três encerramentos.
- GREEN focado: 299 testes de avaliação, adaptador, P15/P16 e identidade.
  Fonte real de responsabilidade própria ainda não existe: contexto sintético
  nos controles não prova esse produtor. Voz física ficou silenciosa; projeções
  de voz/avatar foram verificadas pela sonda de composição, não por reprodução.
  O placar do roteiro não certifica toda a fala: vazamento do feedback técnico
  de autoria pertence a F2, investigado separadamente.

Continuação no mesmo contrato de conquista: outro passe real, depois de F2,
teve 5/14 porque houve efeitos de foco durante a cadeia. O plano da conquista
estava correto, mas `provocacao_afetuosa` continuava expressável. A política
encerrava apenas `bronca_brincalhona`. Nove REDs e controles do arco forte,
mais avaliador/publicador/setter reais em apps e IoT, sustentaram incluir ambos
os arcos de repetição atribuída ao usuário. A prova curta no loop real passou
3/3, sem alertas, p95 9,608 s, em
`roteiro_conquista_inicial-20260929-231252-958844`: receipt redundante real,
`debochada` 1, conquista, `calma` 1 e episódio limpo. Humor de fundo preservado
nos controles. Passe focado final: 395 testes aprovados.

Regressão completa final: 8.385 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
aprovados em 181,47 s. O passe anterior teve uma falha de fixture de P18:
timeout apresentado como receipt observado sem declarar a origem do executor.
A inclusão dessa origem mantém as expectativas e as guardas de procedência;
P18 e o avaliador passaram juntos em 83 testes antes da repetição completa.
Os resultados não encerram as pendências de runtime ou de fonte própria.

Investigação da fonte própria, somente leitura: o preparador pode substituir
ou descartar comandos antes do filtro; o contrato preparado não conserva
proveniência da proposta principal. `filtrar_comandos_pelo_turno` também não
confere IDs/textos de turno/plano/retrato. Sonda com componentes reais rejeitou
DELETE_ITEM numa criação de playlist, mas aceitou ao trocar apenas o retrato
por outro turno de exclusão. É lacuna local demonstrada, não ocorrência de
execução indevida comprovada no runtime. Antes de produzir culpa, preservar
proveniência e congelar/revalidar o snapshot. Restrição legítima, retrato stale
ou proposta reparada não provam erro da Laylay. Nenhum patch nessa fonte.

### Continuação da fonte própria — coerência e emissão preservada — 30/09/2026

- Mesma base `90a2fb8`, `main`, alterações paralelas preservadas. A primeira
  fronteira de autoridade aceitava retrato de outra ocorrência. Três REDs no
  callback instalado em `laylay.py` atingiram playlist, IoT e aplicativos;
  controles corretos passaram antes da troca. O filtro compartilhado agora
  exige seis IDs e textos coerentes no caminho moderno, incluindo referências
  e decisão. Revisões usam a visão operacional efetiva; legado sem identidade
  de retrato mantém compatibilidade. Vinte e três REDs menores precederam a
  produção. GREEN: 149 testes e 22 subtestes. Limite textual: 500 caracteres.
- Primeira perda de procedência: o preparador pode substituir a emissão
  original antes do filtro. O runtime captura `ContratoPropostaPrincipal`
  antes dessa etapa, com ID real do turno e origem fixa. Mappings, contingência,
  vazio, retorno não textual ou vínculo desconhecido não viram prova suficiente.
  O objeto interno conserva a string, sem referência aninhada, parser, nova
  chamada, publicação emocional ou autoridade. O callback segue com dois
  argumentos. Guardar emissão não comprova erro próprio nem efeito.
- Vinte e seis REDs da preservação e dois de retorno inválido do preparador
  foram reproduzidos. A guarda `Mapping` conserva diagnóstico de falha antes
  do dispatcher, enquanto o normalizador standalone continua compatível com
  `None`. GREEN: 48 testes de contratos e registro de conversa.
- O primeiro passe amplo teve 8.451 aprovados e duas falhas por bootstrap do
  teste novo no processo de pytest: ambiente e `print` globais da composição
  atingiam configuração e terminal. Controle separado 2/2, reprodução conjunta
  com dois REDs e 13/13 após isolamento do bootstrap num subprocesso. As oito
  verificações reais foram mantidas, sem alterar configuração/terminal.
  Regressão completa: **8.453 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
  aprovados em 198,46 s**.
- Fonte capturada ainda não é correlacionada ao frame atual para atribuição
  emocional. Leitura reparada publicada como principal e cópias rasas legadas
  continuam fora do candidato. Não encerrar P16 pelo GREEN intermediário.
- Pendência de correlação receipt/fala, separada da guarda de autorização:
  localmente, plano estrangeiro com comando confirmado sustenta “Apaguei”.
  O atualizador mantém comandos anteriores quando recebe lista vazia; sem
  comandos, o verificador real declara não execução/não confirmação. Ainda
  falta reprodução da composição completa do caso estrangeiro. Preservar
  receipts por omissão no mesmo plano é legítimo; não remover a regra global.
  Nenhum patch no writer ou na fala nesta rodada; nenhum commit criado.

### Correlação de evidência operacional antes da fala — 30/09/2026

- Continuação da pendência acima, mesma base `90a2fb8`, sem ID por frase. A
  reprodução passou pelo filtro, atualizador, dispatcher vazio e finalizador
  instalados na composição real. Arquivos, IoT e playlists: filtro recusou a
  proposta, atualizador publicou receipt estrangeiro em `resposta_planejada`,
  finalizador entregou alegação de sucesso. Seis REDs, três em cada fronteira.
- Controle com mesmos receipts e IDs coerentes preservou a evidência e a fala.
  Falha geral do verificador e necessidade de limpar receipts por omissão foram
  falsificadas. Recibos são estímulos sintéticos, não provas de executores
  externos; as portas de voz/persistência foram isoladas. Nenhum executor foi
  chamado. A composição não foi montada manualmente.
- Contrato público `motivo_incoerencia_contratos_turno` reutilizado pelo filtro,
  atualizador e reader. IDs bool/fração/coleções e textos modernos não string
  são recusados. Writer valida/mescla/publica plano+trilha na transação existente;
  incoerência aborta, conservando estado. Reader captura snapshot, recusa antes
  de consumir evidência e entrega conclusão segura observável. Um RED de troca
  durante o verificador demonstrou overwrite do turno novo; CAS do frame lido
  agora protege todas as publicações derivadas. Pesquisa/verificação fora do
  lock. A mescla por intent e o vínculo da fonte capturada ficam fora do patch.
  A API do writer ainda não recebe ocorrência esperada: callback tardio que
  encontre outro frame coerente continua limite. Adaptadores legados sem
  transação não ganham garantia de atomicidade. Validado somente no escopo
  de frame incoerente/trocado durante leitura; P16 permanece parcial.
- Produção: `decisao_turno.py` e `orquestrador_turno_runtime.py`. Cinquenta REDs
  locais antes das guardas, com cinco controles iniciais; resultado final:
  59 canônicos, 288 com vizinhos e 20 da composição isolada aprovados. A seleção
  manual que importou a composição antiga antes de configuração/terminal
  repetiu a interferência já diagnosticada; nenhum patch nesses módulos.
  Regressão completa: **8.521 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
  aprovados em 200,79 s**. `git diff --check` limpo; nenhum commit ou push.
- Fonte própria ainda separada: três sondas somente leitura mostraram aceitação
  ao trocar todo o frame coerentemente, falso RED de alias sem adaptação e
  extração de `open_app` de explicação solta. O owner da próxima fronteira é a
  decodificação canônica em `higiene_resposta_ia.py`, que ainda não publica o
  método de extração. Preservar API legada e distinguir campo operacional,
  recuperação e fala; não criar outro parser nem chamar o modelo novamente.
  Snapshot recebido, correlação, extração explícita, adaptação e violação
  comprovada são requisitos cumulativos antes de qualquer autoria emocional.

### Fonte própria — caminho de extração preservado antes do reparo — 30/09/2026

- Continuação da perda de procedência, mesma base `90a2fb8`, sem outro ID por
  frase. O decoder entregava candidatos explícitos e recuperados sem registrar
  qual caminho os produziu; o reparo anterior à leitura podia ocultar o caminho
  original. Menção somente na fala e recuperação textual falsificam a hipótese
  de que qualquer comando extraído prove uma proposta operacional explícita.
- Owner único: o algoritmo de `higiene_resposta_ia.py` passa a devolver resultado
  tipado; sua fachada legada continua retornando fala/lista. Extração imutável
  registra método, campo, contagem efetiva e string original; origem fixa,
  autoridade falsa. `NONE`, JSON reparado textualmente, tuplas e falhas não
  ganham o marcador explícito. Não atesta correção ou efeito de um candidato.
- `processamento_resposta_ia.py` lê antes do reparo e reutiliza essa decodificação
  sem substituição. `contratos_turno.py` transporta somente objeto tipado e,
  havendo principal, exige fonte conhecida e string exata igual. JSON da IA
  não define essa procedência. Não houve nova chamada ou parser privado.
- 27 REDs iniciais; dois REDs de coleção usada como método e controle `None`;
  30 novos GREEN. Seleção: **573 aprovados em 9,15 s**, incluindo 24 controles
  da composição. Quatro usam o preparador instalado, higiene e normalizador
  reais com serviço de modelo isolado pelo registro canônico. Trava real com
  identidade da sonda evita disputar a Laylay aberta; não inicia `main`.
  Comparação com o decoder do HEAD: 79 entradas, nenhuma divergência legada.
  Regressão ampla: **8.555 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
  aprovados em 203,93 s**, com identidade de mutex própria no pytest para
  importar a composição sem disputar a sessão aberta. Não valida seu loop.
  `git diff --check` limpo; HEAD preservado.
- Limites: string vinculada não é frame vigente; quantidade não é snapshot dos
  parâmetros; candidato explícito não é violação nem culpa. Atribuição emocional,
  adaptação original, leitura principal substituída, callback tardio e receipts
  de solicitações diferentes continuam pendentes. P16 permanece parcial.
  Produção desta continuação limitada aos três owners acima; nenhum commit.

### Fonte própria — vínculo da emissão antes da publicação — 30/09/2026

- Continuação da mesma raiz, base `90a2fb8`, `main`, sem outro ID por frase.
  Frame coerente trocado por inteiro aceitava a emissão anterior, inclusive
  repetindo a frase; troca de operação a rotulava incompatível com a intenção
  nova. Mesma fonte/frame passou: coerência interna não identifica ocorrência
  e não houve falha geral do filtro. Autoridade e procedência são separadas.
- Owner `decisao_turno.py` correlaciona principal tipada por ID e projeção da
  fala original contra o frame canônico; revisão legítima preservada. A projeção
  de 500 caracteres normaliza espaços finais igualmente, sem validar sufixos
  ou parâmetros. Validador captura um snapshot do estado real e reutiliza o
  filtro. `laylay.py` só instala esse objeto no callback existente.
- `resposta_ia_runtime.py` confere ocorrência mesmo com lista vazia, antes de
  leitura semântica/publicação/dispatcher/finalização. Troca aborta o registro
  antigo; falha técnica no mesmo frame conserva contingência sem comandos.
  Retorno moderno malformado/contraditório aborta sem repetir legado. Declaração
  positiva não promove fonte capturada insuficiente; ausência declarada de
  procedência/autorização não sustenta comandos. Veto da autoridade capturada
  permanece. Callback legado mantém um argumento e não certifica procedência.
- 23 REDs iniciais e 16 adicionais precederam os candidatos/refinamentos.
  Expectativas de ordem do receipt e ocorrência com ID reutilizado foram erros
  de teste identificados separadamente. GREEN: **72 focados**, incluindo 30 da
  composição instalada, e **722 ampliados em 11,73 s** antes dos últimos
  controles. Runtime de resposta, estado/validador reais, falha no mesmo turno
  e função legada também passaram com portas externas isoladas; uma chamada
  principal nos controles. Trava real com identidade da sonda, sem `main`.
- Regressão completa: **8.603 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
  aprovados em 195,97 s**. Mutex real com identidade própria do pytest preservou
  a sessão aberta. `git diff --check` limpo; HEAD preservado.
- Produção desta continuação: `decisao_turno.py`, `resposta_ia_runtime.py` e
  wiring de `laylay.py`. Sem parser, modelo extra, evento emocional ou patch no
  writer. Snapshot não fecha a corrida após retornar nem valida efeito externo;
  ocorrência esperada no writer e mescla de receipts continuam pendentes.
  Próxima fronteira da fonte: congelar/adaptar candidatos originais e provar
  violação antes da culpa. P16 parcial; nenhum commit ou push.

### Fonte própria — snapshot dos candidatos e visão isolada — 30/09/2026

- Mesma raiz/base `90a2fb8`, `main`, trabalho paralelo preservado. Contagem e
  string não conservavam a árvore disponível depois de mutação/reparo. Retorno
  legado compartilhava parâmetros aninhados. Sondas falsificaram normalizador
  universal flat e autoria pelo alias cru: comandos canônicos perdiam params
  ou não eram reconhecidos; playlist/IoT legítimos passaram após adaptação.
  Recuperação textual continuou não explícita após converter o nome.
- `SnapshotComandoIA` no contrato guarda JSON interno imutável, projeta cópias
  e oculta payload no repr. Tipos/ciclos/chaves não JSON e não finitos recusam
  evidência. Extração exige tupla tipada/contagem alinhada; preserva originais
  e posições de visões `None`, com gates separados de preservação/normalização.
  Vazio não vira normalização operacional; marcador explícito não substitui
  esses gates, inclusive com JSON textual contendo `NaN`.
- Decoder captura no `concluir` antes da limpeza da fala. Normalizador puro
  reconhece `intent`+`params` pelo catálogo vivo e preserva a árvore; flat reusa
  adaptador canônico sobre cópia. Campos concorrentes/desconhecidos não ganham
  visão. Lista executável e algoritmo de extração permanecem compatíveis.
  Transporte já existente retém objeto original após reparo e exige bruto exato
  da principal. Não houve parser/tabela privada/modelo extra/autoridade nova.
- 28 REDs antes do candidato, 30 controles anteriores verdes; **149 focados**
  finais: 65 procedência, 41 composição, 43 vínculo/runtime. Onze controles
  novos do preparador instalado nos três domínios, inclusive reparo/recuperação;
  outro usa runtime/preparador/estado/validador/normalizador reais e confirma
  snapshots após reparo, lista vazia e uma chamada principal. Portas externas
  isoladas; trava real com identidade da sonda, sem iniciar `main`.
- Regressão completa: **8.650 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
  aprovados em 201,44 s**, com mutex real sob identidade do pytest para preservar
  a sessão aberta. `git diff --check` limpo; HEAD mantido.
- Produção: `contratos_turno.py`, `higiene_resposta_ia.py` e normalizador puro
  junto ao adaptador em `dispatcher_comandos_json.py`. Executor, writer, filtro
  e evento emocional fora do patch. Visão não comprova parâmetros/alvo efetivo
  (dispatcher ainda prepara alvo/pc_b), disponibilidade, efeito ou culpa.
  Retrato local de app sem intents delimitadas não demonstra incompatibilidade;
  cobertura do árbitro é outra fronteira, sem patch ou encerramento global.
  Próximo: violação demonstrada antes de erro próprio. P16 parcial, restantes
  do checkpoint preservados; nenhum commit ou push.

### Fonte própria — violação original demonstrada — 30/09/2026

- Mesma raiz/base `90a2fb8`, `main`, sem commit. Primeira perda restante:
  validador só recebia lista reparada, mesmo com emissão/extração preservadas.
  Oito REDs prévios provaram perda em playlist, IoT, veto e transporte.
  Alias cru e frame estrangeiro falsificaram culpa por simples rejeição;
  original correta/reparo indevido e inverso separam as duas autorias.
- `validar_proposta_original` recebe extração tipada usando o mesmo snapshot
  do filtro, mantendo fachadas legadas. Prova cumulativa: fonte/bruto/ocorrência,
  proposta explícita, originais e normalização completos, flags reais, owner
  conhecido e restrição canônica. `ViolacaoPropostaPrincipal` imutável guarda
  ID/índice/intent/motivo, sem payload, alvo inventado, receipt ou autoridade.
  Filtro canônico continua dono da decisão; lista final não é substituída.
- Veto inequívoco pode demonstrar violação de autorização; incompatibilidade
  exige operação/intents delimitadas no catálogo vivo. `MOVE_ITEM` permanece
  no retrato compatível de arquivos, ausente do catálogo; veto independe dessa
  cobertura. Arbitragem posterior com outra origem suspende prova nesta versão.
  Parâmetros/alvo, app sem cobertura, aliases, recuperações, falha técnica e
  fonte/frame insuficientes não viram erro próprio.
- Runtime publica apenas diagnóstico local sanitizado, com vínculo positivo,
  sem evento emocional/falha operacional. Metadados de culpa/prova da IA não
  materializam o objeto; construtor recusa tipos/motivos não canônicos.
  Refinamentos: dois REDs de owner/catálogo malformados e um de observabilidade
  precederam suas guardas. GREEN final: **199 focados**, incluindo posição e
  metadados (87 vínculo/runtime, 65 procedência, 47 composição);
  composição instalada/início/decoder/preparador/validador reais em três
  domínios, modelo/portas externos isolados. Uma principal no teste do runtime.
- Produção: contrato, decisão compartilhada e transporte da resposta. Nenhum
  executor, writer, estado emocional ou parser novo. Pure evaluator suspende
  restrição não coletável; filtro legado ainda lança erro em coleção numérica
  de intents (achado separado, sem prova/efeito). Próximo: produtor tipado de
  erro próprio com publicação na ocorrência vigente, sem falsificar receipt.
  P16 parcial. Candidato paralelo de writer/semântica vinculados apareceu na
  worktree durante a execução; preservado, com 47 testes próprios verdes na
  repetição focada. Não consolidar essas raízes nem encerrar por esse controle.
  Publicação emocional ainda deve conferir a restrição vigente, além do ID;
  assinatura decisória ou revalidação canônica evitará prova invalidada na
  mesma ocorrência. Demais pendências mantidas, sem commit ou push.
- Regressão final: **8.975 aprovados, 1 ignorado, 56 subtestes aprovados em
  201,73 s**, zero falhas/xfails. Hashes dos 65 Python modificados/novos iguais
  antes/depois, mutex real com identidade do pytest, HEAD mantido e diff limpo.
  Duas execuções anteriores ocorreram durante mudanças paralelas do writer:
  três falhas de controle, depois uma de conclusão técnica; passaram após
  atualizar/repetir o candidato paralelo. Não atribuir à prova original nem
  enfraquecer expectativas. O verde estável não certifica o loop/efeito físico.

### Continuação da fonte própria — evento e consumo da fala — 30/09/2026

- Mesma raiz/base `90a2fb8`, `main`, worktree preservada. Fonte original já
  produz prova; a fronteira seguinte separava quadro e episódio sem verificar
  ocorrência/restrição. Não atribuir essa perda ao executor ou ao reparo JSON.
  Produtor próprio projeta fato local tipado, sem fabricar `ResultadoAcao`.
- `EstadoContextoRuntime.publicar_erro_proposta` reexecuta a avaliação canônica
  dentro de `atualizar_dominios`: quadro, plano e conversa são preparados antes
  de qualquer atribuição. Rollback/recusa preservam ambos. Atomicidade pelo
  lock comum; leitores legados diretos continuam fora dessa garantia.
  Referência estável e consumo no plano impedem renovar TTL após replay.
- Origem reservada `contrato_proposta_principal`, `envergonhada 1/autorreparo`,
  45 s, sem payload/autoridade/receipt/memória pessoal. Aplicador exige prova
  e emissão integrais; permite interromper bronca sem mudar humor de fundo.
  Publicador genérico recusa essa origem. Estado, diagnóstico e catálogo
  reutilizam owners compartilhados, sem modelo ou parser emocional separado.
- Fala planejada conserva apenas a base. Finalizador compõe admissão limitada
  depois do guardião, revalidando tempo e fonte consumida no frame atual.
  REDs de expiração/troca motivaram esse refinamento; uma contingência de outro
  frame não recebe a admissão antiga. A fala não confirma efeito ou reparo.
  Perguntas naturais recuperam os limites pelo catálogo existente.
- RED prévio: 13 ponte, 17 transação, três origem/aplicação, um callback real,
  um finalizador e dois trocas no guardião. Casos e provas pertencem à mesma
  raiz; não são novos IDs por frase/domínio. Controles de original correta,
  aliases, fonte insuficiente, outra ocorrência e alteração da restrição
  preservados. Nenhum commit/push. P16 parcial; leitura original/reparada,
  correlação de receipts e loop/áudio físico continuam sujeitos a evidência
  própria, preservando alterações paralelas e seus checkpoints.
- GREEN: **616 focados/vizinhos + 16 na composição instalada**, com início,
  preparador, validador, publisher, writer, guardião, finalizador e orquestrador
  de fala reais. Playlist/IoT usam uma principal, filtro remove original
  incompatível, texto/voz/projeção visual concordam; confirmação falsa sem
  receipt vira contingência. Portas físicas/persistência isoladas.
- Ampla: **9.084 aprovados, 16 falhas, um ignorado e 56 subtestes em 199,05 s**;
  76 Python com hashes iguais antes/depois, HEAD mantido e diff limpo. Os 16
  pertencem ao arquivo paralelo `test_mescla_receipts_solicitacao.py`, presente
  no início. Isolado repete 16 RED/3 GREEN: 12 mescla por intent, um identidade
  host e três sondas bloqueadas na chave de porta incorreta (sem `_`). A última
  família não alcança publicação e exige corrigir a representação do contrato
  no teste antes de declarar RED de transporte. Preservados como próxima
  investigação de correlação; não são 16 roots nem regressão ampla GREEN.

### Sonda separada: desculpa seguida de comando — 27/09/2026

- Durante a validação da P16, `classificar_modalidade_turno` leu
  “Desculpa, repeti o pedido, mas agora abra o Opera.” como `conversa`.
  `planejar_turno` recebeu `pedido_desculpas` como função comunicativa e
  devolveu `requer_execucao=False`. A sondagem não passou pelo executor.
- Isto é uma suspeita de raiz na segmentação/autoridade do turno misto, não
  consequência demonstrada do decaimento emocional nem prova de que um comando
  real foi perdido. Não houve patch nessa fronteira. Próximo diagnóstico:
  comparar o classificador e o interpretador principal com comandos mistos
  equivalentes sem desculpa, em mais de um domínio, e localizar o primeiro RED.

### Complemento da observabilidade da entrada — prompts vazios, 23/09

- Evidência do Pedro às 10:30:40 confirma que o texto recebido agora aparece;
  a correção anterior estava incompleta porque `💬 Você:` e `>` vazios ainda
  eram publicados como eventos SYSTEM. Não é perda da fala nem falha da ponte.
- Base `bd94bc3e`, main, worktree compartilhada preservada (124 entradas no
  status). Arquivos de DEV/terminal envolvidos estavam sem diff antes deste patch.
- Primeira fronteira RED: captura de stdout promovia controles de apresentação
  do leitor de stdin a eventos. Leitor real + espelho real reproduzem dois
  eventos após Enter vazio e zero mensagens processadas. Cinco REDs antes
  do candidato, 19 controles verdes.
- Produção alterada somente em `dev_console_runtime.py`: marcadores completos
  sem conteúdo são ignorados na admissão de stdout (inclusive captura oculta).
  Console original, mensagens preenchidas, linhas diagnósticas e stderr
  preservados. Não há filtro por palavra solta nem alteração de entrada/execução.
- GREEN: 68 testes em DEV, canais, terminal e ponte. Transporte autenticado
  por socket real confirma snapshot/live sem prompts vazios, preservando
  `💬 Você: 'pode ligar a luz' | origem=desktop`.
- Novos registros exigem reinício para carregar o patch; sessão real do Pedro
  não reiniciada e histórico antigo não apagado. Nenhum commit criado.

### Recibo ilegível não autoriza confirmação — 23/09

- Continuação da fronteira operacional/RED 5 descrita abaixo, não nova raiz
  independente por habilidade. Base `bd94bc3e`, main; worktree paralela preservada.
- Primeira fronteira RED: falha de `como_dict()` virava `{}` e o bloco
  `if dados_resultado` pulava a validação mantendo o texto otimista. Não era
  invenção do TTS: o texto já chegava errado à publicação visual e à fila.
  Os controles de sucesso confirmado e de confirmação desconhecida passaram.
- Antes do candidato: 15 REDs e 14 controles verdes. Além do caso histórico,
  cobertos retorno vazio/tipo inválido, acesso ao serializador com exceção,
  falas de aplicativo/arquivo/IoT e reserva indevida da deduplicação por
  atributos de um objeto cujo recibo não podia ser lido.
- Produção alterada somente em `falar_resultado_operacional`, no orquestrador
  de fala: ler uma única representação antes de validar/deduplicar; se ilegível,
  informar que o resultado não pôde ser validado, sem afirmar sucesso ou falha
  do efeito externo. Recibo posterior válido continua elegível à confirmação.
  Sem alteração em executores, autorização, LLM ou correção anterior do briefing.
- GREEN: **173 testes em oito módulos**, incluindo direção e fila de voz reais
  sem reprodução física, publicação visual, memória, receipts, guardião e
  briefing. `git diff --check` sem erros. Nenhum commit criado.
- Sessão real pendente: Laylay aberta (PIDs 26928/9880), não interrompida.
  Não foi injetada corrupção na sessão do usuário; resultado integrado não
  é uma validação de áudio físico nem encerramento de toda factualidade.

### Retomada proativa e observabilidade da entrada — 23/09

- Base: `bd94bc3e3a29c49906dc603f9ca1540310ca3274`, main, worktree
  compartilhada suja preservada. Não houve commit nem reinício da sessão.
- Raiz reproduzida: canal de chat aberto era tratado como ocupação permanente,
  tanto no Porteiro quanto no callback legado composto em `laylay.py`.
  O timer retomava normalmente, mas a mesma condição impedia a liberação.
  Quatro REDs: briefing/e-mails/rotina após silêncio e callback real extraído
  da composição. Corrigido para considerar owner, turno e atividade recente;
  reunião, foco, jogo e usuário falando continuam protegidos.
- Raiz separada: timeout da espera síncrona do briefing declarava pendente=False
  sem cancelar a fila. O recibo posterior não salvava o estado diário. RED
  reproduzido; agora a pendência continua acompanhada e sucesso tardio chama
  a persistência uma vez, somente após recibo positivo.
- Raiz separada de diagnóstico: `💬 Você:` era um prompt, não registro de fala.
  Desktop/voz não produzem eco de stdin. Cinco REDs mostram texto chegando ao
  processamento sem aparecer no DEV. O coordenador registra a entrada uma vez
  no worker comum, com origem e sanitização, sem alterar o texto processado.
- Validação: 97 testes passaram em dez módulos de porteiro, fila, briefing,
  entrada, DEV, presença e prioridade. Integração com Porteiro e Voz reais usa
  relógio/timer e saída física controlados; não equivale a áudio em produção.
  A Laylay estava aberta (PIDs 29700/4716); validação ao vivo pendente.
- Achado separado a investigar: a execução de oito módulos teve 79 PASS e
  um FAIL em `test_fronteira_operacional_falha_fechada_se_resultado_nao_serializa`:
  receipt corrompido terminou em “Pronto, abri o Chrome”. O método operacional
  não foi alterado neste patch; a worktree já contém mudanças paralelas nele.
  Não atribuir automaticamente ao patch atual nem declarar regressão ampla verde.
- Fora do patch: sincronizações repetidas da lista de conversas, indisponibilidade
  HTTP do LRCLIB, momentos sensíveis persistentes e outras possíveis causas de
  silêncio. O log HTTP isolado não identifica status ou causa do provedor.

### P01 — Continuação incerta: investigação da recusa, 23/09

- Base mantida em `bd94bc3e`, branch main e worktree compartilhada preservada.
  `quero im` chega intacto ao HTTP junto da pergunta anterior. A recusa já vem
  do Qwen, antes do verificador. Isso falsifica perda literal da entrada,
  ausência da última pergunta no payload e criação da recusa pelo guardião,
  mas ainda não identifica qual instrução/comportamento da geração a causa.
- Controle local do owner de modalidade: `quero im` é conversa, sem autorização
  e sem comandos; não é classificado como comando inválido. `quero sim` é
  confirmação contextual, também sem autorização independente. Preservar
  essa distinção; não normalizar erro de digitação para autorização presumida.
- Preparada sonda `scripts/analises/diagnosticar_continuacao_incerta.py`:
  reutiliza exatamente um payload da captura, varia fala atual e retira
  separadamente contrato efêmero e instruções gerais. Mantém histórico,
  modelo, temperatura, orçamento e schema; registra seed/entrada/saída local.
  Não importa runtime, não executa propostas nem alimenta aprendizado. As
  variantes reduzidas são ablações, **não candidatos promovidos a produção**.
- Seis testes da sonda passaram: preservação das variáveis de controle,
  imutabilidade do payload original, aborto para captura ambígua/schema
  inesperado. Não são seis respostas corretas da Laylay ou prova do modelo.
- Comparação executada depois do encerramento da sessão, sem abrir a Laylay:
  `resultados_testes/continuacao_incerta-20260923-103913-389155/comparacao.jsonl`.
  Foram oito chamadas locais (`quero im`/`quero sim`, quatro variantes).
  Algumas variantes entregaram o exemplo após `quero sim`, mas as interpretações
  de `quero im` divergiram entre si. É indício de sensibilidade ao contrato,
  não prova de uma instrução causal única. Nenhuma variante foi promovida a
  produção; preservar autorização literal sem adivinhar `im = sim`.

### P01 — Ensino aberto: referência certa, conteúdo ainda não fundamentado — 23/09

- Base `main`/`bd94bc3e`, worktree paralela preservada. A sonda com geração
  real do Qwen3:4b-instruct e 21 entradas em sete assuntos está em
  `resultados_testes/roteiro_ensino_multidominio-20260923-104318-248836/`.
  Todos os turnos responderam sem comandos, mas a métrica `19/21` mede a
  rubrica operacional/latência; `fala_coerente=nao_avaliado`. O texto final
  errou tradução de idade em inglês, conceitos de força/energia, representação
  de corte arquitetônico e exemplos de plantas anuais/perenes. Os erros já
  estavam na geração HTTP. Transporte, executor e verificador não são a
  primeira fronteira desses erros de conteúdo.
- Causa de continuidade demonstrada: `esclarecimento_literal` ancorava o
  pedido `não entendi` na fala anterior da assistente, que pode estar errada,
  sem recuperar o pedido de ensino do usuário. RED em três domínios mais
  controle de expiração. O contrato agora usa a estratégia
  `reensino_didatico`, com o pedido recente como tema e a resposta anterior
  como tentativa a revisar, não como fonte ou autorização. Produção alterada
  somente em `cognicao/contrato_fala.py`, `cognicao/geracao_concreta.py`;
  a classificação de pedidos explícitos em `personalidade/proporcao_resposta.py`
  e o roteiro genérico já estavam no candidato desta investigação.
  145 testes focados passaram; sem commit.
- Validação real posterior, sem replay:
  `resultados_testes/roteiro_ensino_multidominio-20260923-123010-079343/`.
  Os sete pedidos de reexplicação chegaram com `reensino_didatico` e sem
  execução, 21/21 responderam. O placar `18/21` volta a medir operação e
  latência, **não qualidade didática**. Persistiram erros factuais nos temas
  acima. Logo o reparo do referente é GREEN no runtime; **P01/geração factual
  permanece RED**.
- Ablação `scripts/analises/comparar_contrato_ensino.py` em quatro assuntos:
  trocar a regra de evidência/definição no prompt mudou algumas respostas,
  mas não eliminou imprecisões. Uma revisão isolada pelo mesmo Qwen aprovou
  sete reexplicações como `ERRO OBJETIVO: Nenhum`, inclusive erros verificáveis
  de tradução, física e botânica. **Autoavaliação sem evidência externa não é
  guardião factual**. Não promovê-la a produção por parecer convincente.
- A pesquisa contextual atual não é ainda uma base para cinco sites de ensino:
  `pesquisa_contextual.py` tentou Wikipédia PT/EN e recebeu HTTP 403 neste
  ambiente; a busca HTML reutilizada encontrou quatro hits sobre força/energia,
  dos quais dois abriram no teste. Disponibilidade e relevância são limites
  distintos. O desenho adaptativo e critérios de ativação estão em
  `melhorias e planos/PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md`. Não ativar busca
  compulsória nem converter snippet em confirmação factual.
- Achados separados: ao ler `planta`, uma tarefa IoT tentou pesquisar RGB
  repetidas vezes sem comando; uma reescrita de realidade introduziu `nn`
  visível na fala de inglês. Investigar por suas primeiras fronteiras, sem
  atribuir esses sintomas à raiz factual ou encobri-los com o placar 21/21.
- **23/09, candidata multifonte não promovida:** foi criada recuperação de
  até cinco páginas realmente lidas, domínios independentes, URLs e trechos,
  com guarda contra URL privada/redirecionamento e sem autoridade de ação.
  Dois ensaios de 21 turnos com influência ativada ficaram em 6/21 e 7/21
  sem alertas operacionais (p95 perto de 20 s), piores que a referência 18/21.
  A inspeção das falas encontrou definição correta na fonte, mas inversão
  produzida pelo Qwen (planta baixa vista de baixo), tradução “eu sou 25”,
  código de exemplo com repetição incorreta e exemplos botânicos inventados.
  Logo a camada de leitura é GREEN local, mas **P01/geração + verificação de
  alegações continua RED no runtime**. `LAYLAY_PESQUISA_MULTIFONTE_MODO`
  fica `desativado` por padrão; `ativo` serve somente para experimento.
  `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md` registra portões restantes. Não
  somar o sintoma IoT `planta` como nova raiz factual.
- **24/09, mesma raiz P01, candidata de prompt ainda insuficiente:** no
  cenário hipotético com leitura de 15% e limiar de 20%, o Qwen recebeu os
  dados, mas sua resposta bruta omitia a comparação ou acrescentava causas
  não demonstradas; o verificador as preservou. O roteiro compacto recebeu
  o contrato premissas → relação → conclusão (RED em três assuntos).
  Depois, dois REDs mostraram que falas antigas da assistente voltavam ao
  ensino pelo histórico e por `Evite repetir`; ambas as rotas foram retiradas
  só do prompt didático, sem alterar memória nem autorização. No runtime,
  a comparação `15 < 20` melhorou, mas ainda surgiram promessas de umidade
  e explicações botânicas não ancoradas. **P01 continua RED; inventário de
  cenário segue em sombra.** 236 testes relevantes verdes; os 4/4 do roteiro
  mediam transporte/não execução, não verdade. Evidência e próxima fronteira
  de alegações atômicas em `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md`.
- **27/09, subdiagnóstico P01 ainda em sombra:** a seleção direta de
  segmentação pelo Qwen mostrou viés de ordem e saídas estruturais instáveis.
  Uma sonda POS portuguesa independente alinhou 9/13 regras planas de um
  painel inédito à revisão local, mas errou uma oração relativa e um verbo
  rotulado como adjetivo; absteve-se numa elipse e recusou uma regra plana
  cuja mistura `e/ou` era só superficial. Esses REDs pertencem às fronteiras
  de escopo sintático, POS e cobertura lexical descritas no plano de ensino;
  não são quatro novas raízes nem prova de qualidade didática no runtime.
  Nenhuma promoção para fala, treino ou execução.
- **27/09, mesma raiz P01, oração relativa:** RED focado mostrou que um
  predicado `acl:relcl` não pode fechar sozinho uma premissa
  independente. Candidato apenas na sonda POS offline: 55 testes focados
  verdes; v8 passou de 9/13 para 10/13 regras planas alinhadas à revisão
  local. Painel novo v9 congelado antes da execução: 8/8 alinhamentos de
  superfície, porém um deles usou âncora sintática errada (`escreve` em vez
  de `confirmar`), logo não é 8/8 de análise correta nem razão para promoção.
  Excluir toda a subárvore relativa foi falsificado: só 5/8 no v9; o
  candidato ficou restrito ao verbo relativo e a auxiliares diretamente
  ligados a ele.
  Parser ambíguo, POS `cessar`, elipse e mistura superficial seguem abertos;
  nenhum código de produção, fala ou executor alterado nesta etapa.
- **27/09, continuação da mesma raiz P01:** a âncora `escreve` foi aceita
  acidentalmente no v9 onde a condição principal depende de `confirmar`.
  RED focado antes do ajuste; a sonda offline agora se abstém quando uma
  relativa ainda aberta é seguida imediatamente por verbo após o conectivo.
  v9: 7 alinhamentos locais/1 abstenção. Painel v10 novo, congelado antes da
  primeira execução: 4 alinhamentos/2 abstenções; controles independentes
  preservados. 68 testes da área verdes. Nenhuma promoção ao runtime nem
  encerramento de P01; demais fronteiras continuam separadas.
- **27/09, auditoria de âncora da mesma raiz P01:** `ROOT` do parser foi
  falsificado como regra geral para o verbo principal. O confronto offline
  separa âncora, trecho e abstenção sem usar a revisão na proposta. Painel
  v11 congelado antes do parser: 6/8 casos com âncoras alinhadas à revisão
  local e 2/8 abstenções; `vapor` etiquetado `VERB` revelou outra falha POS
  sem gerar sucesso falso. 71 testes focados verdes. Não houve alteração de
  produção nem validação da fala no runtime; P01 permanece aberto.
- **27/09, mesma raiz P01, confiabilidade POS/fronteira:** `cessar` foi
  `ADJ/advcl`; variantes com `soprar` e `soar` variaram entre `ADJ/acl`,
  `ADJ/ROOT`, `ADJ/amod` e `PROPN/ROOT`. Veto por etiqueta foi falsificado
  em dois painéis novos. O contrato offline compartilhado agora se abstém
  quando há fragmento sem âncora entre fragmentos ancorados, sem inventar
  verbo. No v14, 2 fusões falsas passaram a abstenções; no v15 congelado,
  4/7 alinharam e 3/7 se abstiveram, incluindo duas frases válidas cuja
  cobertura foi perdida conscientemente. 79 testes focados verdes. Nenhuma
  promoção para produção/runtime; P01 continua aberto.
- **27/09, mesma raiz P01, continuidade nominal:** a sonda POS passou a
  registrar candidato de objeto coordenado ligado ao verbo anterior sem
  desfazer `fronteira_interna_sem_predicado_ambigua`. Painel v16 congelado:
  2/3 objetos compostos forneceram essa evidência, 0/2 controles
  problemáticos; o terceiro objeto revelou `câmera` classificada como
  `VERB` e âncora inicial errada. São 1 alinhamento e 5 abstenções no
  painel, não 5 erros equivalentes nem liberação de cobertura. 81 testes
  focados verdes. Sem produção, runtime real ou treino alterados; P01 aberto.
- **27/09, mesma raiz P01, POS verbal contraditório:** no caso `a câmera
  registrar foto e vídeo`, `câmera` foi `VERB/nsubj` com filho `a/DET/det`.
  RED focado comprovou que sua seleção como âncora ocultava a continuação
  nominal; a guarda diagnóstica a exclui e se abstém, sem aprovar a regra.
  Painel v17 congelado: evidência nominal nos 3/3 objetos compostos, nenhum
  dos dois controles problemáticos; 1 alinhamento independente, 5 abstenções.
  O controle `o vento soprar` voltou a perder o verbo no POS, logo a
  cobertura segue limitada. 82 testes focados verdes; v8–v15 sem mudança
  nas contagens. Hashes e limites no plano de ensino. Nada promovido a
  produção, fala, autorização, treino ou runtime real; P01 aberto.
- **27/09, mesma raiz P01, vínculo literal auditável:** REDs exigiram offsets
  do arco `conj` → `obj` → âncora e uma prévia separada da decisão canônica.
  A sonda registra conflito POS sem perder o arco; `VERB` com papel de
  coordenado de objeto leva à abstenção. Painel v18 congelado antes do modelo:
  prévia em 3/3 objetos compostos, 0/4 controles, mas os três continuam em
  `fronteira_interna_sem_predicado_ambigua` no reconstrutor. Dois controles
  alinharam; os demais se abstiveram. Um arco incompleto passou a ser
  descartado sem exceção após RED focado. 86 testes focados verdes; v8–v17
  conservaram as contagens de estados. Hashes, limites e próxima fronteira
  no plano de ensino. Nenhuma alteração de produção, fala, treino, autorização
  ou runtime real; P01 aberto.
- **27/09, mesma raiz P01, parser atravessa a fronteira oracional:** v19
  congelado revelou 2/3 controles de sujeito composto com **prévia falsa**:
  `conj → obj` ligou o sujeito da condição seguinte ao objeto anterior.
  Offset e POS estavam coerentes, portanto não bastavam. REDs levaram a
  abstenção conservadora quando nominal determinado precede predicado plural
  e quando `VERB` tem determinante. Repetição v19: 0/5 controles com prévia,
  1/2 objetos cobertos. V20 congelado depois do primeiro candidato: primeira
  execução 2/3 objetos e 0/3 controles. Um falso veto adicional foi revelado
  por verbo com sujeito próprio, corrigido após RED; repetição v20 3/3 e
  0/3, **não** holdout independente para o último ajuste. 90 testes focados
  verdes. A decisão canônica segue em abstenção; P01 não encerrada, sem
  mudança de produção ou runtime. Detalhes e hashes no plano de ensino.
- **27/09, mesma raiz P01, checagem sem parser:** piloto local de Qwen em
  três contrastes falhou como segundo voto (`indeterminado/anterior/anterior`
  contra `anterior/seguinte/anterior`; com partições completas, três
  `indeterminado`). Não foi integrado. RED com morfologia do parser ausente
  motivou veto textual unilateral por artigo e possíveis flexões plurais,
  validando offsets sem POS/dependência. A ausência de veto não aprova
  agrupamento e pode haver perda de cobertura em objeto legítimo seguido de
  condição plural. Painéis v15–v20 sem mudança de estados ou prévias;
  97 testes focados verdes. P01 permanece aberta, sem produção/runtime.
- **28/09, mesma raiz P01, POS e medição da prévia:** v21 foi congelado antes
  da primeira execução (hashes e casos no plano de ensino). O parser real
  marcou `falham` como `ADJ/conj` com sujeito próprio e como `PROPN/flat:name`
  em contextos distintos. RED focado tornou o primeiro caso uma abstenção
  POS explícita; o segundo permanece em `sem_predicado_suficiente`, sem
  inferir verbo a partir da palavra. Auditoria tipada da prévia distingue
  vínculo ausente, conflito POS e vetos; aferição retrospectiva separada
  compara apenas trechos ao gabarito manual local. Em v15–v21, 14/44 casos
  tiveram prévia, as 14 coincidiram com a revisão local; não é prova
  semântica independente. Um objeto legítimo do v21 perdeu cobertura pelo
  veto conservador. 106 testes focados e 230 testes das sondas de ensino
  verdes nesta etapa; P01 aberta,
  sem alteração de produção, fala, treino, autorização ou executor.
  Controle pareado com mesma topologia de arco/POS em leituras distintas
  sustenta a abstenção; `--resumo` torna a contagem local reproduzível,
  sem converter acordo com gabarito em prova semântica.
- **28/09, P01, segundo avaliador ainda não apto:** sonda independente sem
  POS/dependências/gabarito no input e painel v22 congelado (10 casos: 4
  sujeito, 4 objeto, 2 ambíguos). Primeira chamada: 3/10 citações aceitas,
  todas de sujeito. Repetição diagnóstica após expor a resposta bruta,
  sem mudar o prompt: 5/10 rótulos brutos alinhados (4/4 sujeitos, 0/4
  objetos, 1/2 ambíguos). O primeiro RED inclui classificação do objeto,
  não apenas formato da citação. Sem promoção; hashes e limites no plano
  de ensino. Não atribuir placar bruto ao primeiro uso cego.
- **28/09, P01, segunda formulação apenas diagnóstica no v22 já visto:**
  partições literais completas com ordem invertida deram 20/20 respostas
  `objeto_anterior`, mas só 4/10 rótulos alinhados à revisão (0/4 sujeitos,
  4/4 objetos, 0/2 ambíguos). Concordância à ordem do mesmo modelo não é
  voto independente; o prompt mudou o viés, não resolveu a fronteira.
  Próxima investigação: fonte de evidência diferente. P01 permanece sombra.
- **28/09, P01, tentativa de segundo modelo inconclusiva:**
  `gemma4:26b` estava instalado, mas a primeira consulta do contrato de
  citação excedeu 90 segundos (`ReadTimeout`). O restante foi interrompido
  e o modelo descarregado. Nenhum rótulo foi observado; não entra no placar
  semântico nem justifica promoção. Os 244 testes locais das sondas passaram;
  ainda falta evidência independente operacionalmente viável e runtime real.
- **28/09, P01, transporte OpenRouter comprovado em um caso:**
  sonda offline reutiliza a credencial DPAPI da Laylay sem terminal ou
  exposição da chave. `google/gemini-3.1-flash-lite` retornou um julgamento
  ancorado no primeiro caso sintético v22; recibo da API registrou custo de
  US$ 0,0001245. Isto não é placar semântico nem holdout. Nenhuma integração
  de produção foi ativada; próximo passo continua sendo painel novo cego.
- **28/09, P01, revisão local inválida em v22/v23:**
  a primeira medição externa do v23 acertou os oito casos definidos com
  citação válida, mas a revisão dos quatro "ambíguos" não era gramatical:
  último sujeito singular com verbo plural na leitura de objeto. Os dois
  "ambíguos" do v22 tinham a mesma falha. Nenhum desses seis itens conta
  como prova de calibração de incerteza. V23 foi preservado imutável;
  v24 registra explicitamente as duas leituras plausíveis antes da chamada.
  P01 continua em sombra, sem remendo para o modelo.
- **28/09, P01, abstenção ausente em ambiguidade plausível:**
  v24 registrou duas partições literais plausíveis em seis casos; Gemini
  escolheu sempre objeto e GPT-4o mini alternou quatro sujeitos/dois objetos,
  mas nenhum retornou `indeterminado`. Citação literal não prova que o lado
  oposto seja inviável. Hipótese de contrato: a instrução original não define
  quando abster. Variante explícita e v25 novo foram congelados antes da
  primeira consulta, sem mudar o gabarito anterior ou liberar P01.
- **28/09, P01, troca de viés no prompt explícito:**
  v25 novo (3 sujeito, 3 objeto, 3 ambíguo) com Gemini: 3/3 sujeitos
  ancorados, 3/3 ambíguos abstidos, mas 3/3 objetos definidos também
  abstidos. A nova instrução não é solução geral; primeira fronteira RED
  agora é verificar a viabilidade de ambas as partições, não escolher um
  rótulo pela preferência do prompt. Nenhuma alteração de produção.
- **28/09, P01, viabilidade precisa de contexto e validação tipada:**
  sonda offline avalia as duas partições separadamente, sem gabarito ou
  alternativa na mesma chamada. RED local impediu agregação de pareceres
  não validados. V25 de desenvolvimento mostrou erro de concordância
  alegado quando se removia o `Se` da frase; a reconstrução contextualizada
  corrigiu esse transporte, e somente parênteses externos adicionados pela
  própria sonda podem ser removidos da citação. V26 novo foi congelado para
  aferição; nenhuma decisão ou executor da Laylay foi modificado.
- **28/09, P01, primeira medição v26 e variação dos pareceres:**
  GPT-4o mini alinhou 6/9 casos à revisão local (2/3 sujeito, 1/3 objeto,
  3/3 ambíguo), em 18 chamadas. Os três desalinhamentos vieram da
  viabilidade atribuída às partições, antes da agregação. Repetições
  diagnósticas mudaram dois pareceres, sem alterar o placar. Mesmo com
  temperatura zero e semente 42, um caso repetido variou; o provedor não
  foi fixado, logo a causa dessa variação não está demonstrada. Citação
  literal não verifica gramática. Sonda e 275 testes locais verdes; P01
  segue offline/sombra, sem treino ou integração operacional.
- **28/09, P01, variação não depende só de roteamento:**
  observabilidade offline revelou chamadas Azure/OpenAI no mesmo caso, mas
  `provider.only=openai` com fallback desligado não estabilizou o parecer.
  Em cinco repetições diagnósticas fixadas, a leitura de sujeito oscilou
  entre viável (2) e inviável (3). Em três repetições, SHA-256 do pedido,
  provedor OpenAI, fingerprint e término `stop` foram idênticos. Diferença
  no corpo, troca de provedor e truncamento aparente foram falsificados
  como explicações suficientes; mecanismo interno ainda desconhecido.
  Parecer isolado não comprova concordância; próxima fronteira é um
  verificador independente de escopo explícito. Sem promoção ou produção.
- **28/09, P01, motivo gramatical alegado sem contraprova:**
  RED offline reproduziu exclusão falsa da leitura `sujeito_seguinte` por
  `inviavel/concordancia` embora a condição trouxesse sujeito composto
  curto e marcador verbal plural explícito. Contrato unilateral no módulo
  superficial existente marca apenas esse conflito; o agregador se abstém,
  sem converter o sinal em viabilidade comprovada. Controles de verbo
  singular, casos fora de escopo, motivo semântico e domínios distintos
  passaram; 290 testes de sonda relacionados verdes. Nenhuma mudança de
  produção, treino, promoção, fala ou executor. Verificação morfossintática
  abrangente e runtime permanecem abertos.
- **28/09, P01, verificação morfológica de escopo curto:**
  o sinal anterior por sufixo não reconhecia `forem` e aceitaria a forma
  inventada `trubarem`. Fonte externa PortiLexicon-UD congelada por commit
  e SHA gerou índice local de 368 KB (licença preservada); código da sonda
  valida o hash e compara pessoa/número em estruturas curtas. Parecer do
  modelo `inviavel/concordancia` agora requer divergência numérica
  corroborada; convergência, falta de forma/recurso ou estrutura fora do
  alcance levam à abstenção. Painel novo congelado antes da medição:
  21/21 alinhados à revisão **manual local** (8/8/5), sem alegar qualidade
  semântica ou generalização. SpaCy médio não substitui o índice nem a
  revisão da estrutura. P01 segue offline/sombra; nenhum treino ou produção.

### P01 — Perfil explicativo perdido na escolha do prompt — 23/09

- Base `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`. Conferidos HEAD,
  branch e worktree; trabalho paralelo neural/operacional preservado.
  Sem novo ID por frase: esta é uma causa demonstrada de instrução inadequada
  dentro de P01, não a explicação de todas as recusas/erros do modelo.
- Captura anterior `transporte_evidencia-20260922-173130-396574`: pedido
  `quero passo a passo usando metodos praticos` chegou com o tema da divisão
  no histórico, mas prompt rápido mandava uma ou duas frases, contrato três,
  e retrato expressivo permitia oito. O modelo só prometeu explicar, usando
  58 tokens e `finish_reason=stop`: **não foi corte por esgotar tokens**.
  Falsificadas perda do tema no transporte e mutilação desse rascunho pelo
  verificador. A hipótese de que a compressão explica toda a má geração não
  foi demonstrada e não deve ser usada para fechar P01.
- Primeira divergência: `classificar_proporcao` já dizia `explicativa`, mas
  `usar_modo_rapido_conversa` verificava só fórmulas/reexplicação e tamanho.
  Logo um pedido curto de desenvolvimento recebia rota/prompt de fala breve;
  o contrato efêmero também ignorava o perfil ao escolher o limite inicial.
- Contrato reutilizável: **necessidade da resposta governa a compactação, não
  tamanho da entrada**. Rota e contrato reutilizam a classificação existente
  em `proporcao_resposta`. Perfis explicativo/matemático não entram no rápido;
  contrato herda seu espaço, preservando teto atual de oito e as restrições
  específicas posteriores. Saudação segue rápida; autoridade e receipts não
  mudam. Não foram acrescentados gatilhos privados, modelo ou fallback.
- RED: **6 falhas causais / 82 controles verdes**, com pedido histórico,
  divisão, fotossíntese, detalhes e comparação de conceitos. Candidato de
  produção somente em `autonomia/fluxos_conversa.py` e
  `cognicao/contrato_fala.py`. Em fluxos, alterações anteriores de P03 foram
  preservadas. Testes em `test_latencia_resposta.py` e
  `test_contrato_semantico_fala.py`, incluindo o callback realmente injetado
  em `_resposta_ia_runtime` pelo `laylay.py`. Sem treino, promoção ou commit.
- Regressão final selecionada: **643 aprovados / 13 xfailed preexistentes**
  em 22 módulos, 7,12 s, incluindo os contratos de P10. `git diff --check`
  sem erro de whitespace; aviso CRLF no relato do usuário não foi corrigido
  por estar fora do escopo. Não foi executada a suíte global.
- Geração real, **sem replay**, duas sessões Qwen3:4b-instruct:
  `roteiro_ensino_divisao-20260923-100339-722094` e
  `roteiro_ensino_divisao-20260923-100458-680059`. Transporte respectivamente
  em `transporte_evidencia-20260923-100338-508086` e
  `transporte_evidencia-20260923-100457-371895`, todos em `resultados_testes/`.
  O turno 2 recebeu prompt completo, contrato de sete frases e 512 tokens
  disponíveis. Produziu e entregou três passos na primeira sessão e cinco na
  segunda. Primeira resposta consumiu 173 tokens e terminou por `stop`.
  Melhora observada, não taxa de acerto estimada nem ablação estatística.
- Ambas encerraram com código zero; nenhuma sessão do Pedro foi encerrada
  pelo agente. A tentativa anterior 10:02:48 foi bloqueada corretamente por
  instância ativa; sondas só continuaram após Pedro encerrar. Voz/UI/mic off,
  Gmail inativo, IoT simulado; observadores e memória normal ativos. Áudio
  físico não testado. Placar 4/4 mede não execução, não aprovação do ensino.
- **Ainda aberto:** em ambas, turno 3 confundiu contrário/inverso; turno 4
  interpretou `quero im` como pedido impossível/sem comprovação. Os erros já
  vieram no HTTP, com a pergunta anterior no histórico. A maior disponibilidade
  de tokens não resolve isso. Próxima investigação: contexto/instrução e
  tratamento de continuação incerta na geração, com contrastes, sem ensinar
  `im = sim` como regra autorizante. JSON literal fora do envelope e perguntas
  excessivas também ocorreram; entrega recuperou o texto, não certificou
  conformidade estrutural. Achado de resumo `principal_duplicada` reapareceu,
  segue separado e sem prova de contaminação persistida.

### P10 — Aspas indeterminadas não são evidência de obra — 22/09, continuação

- Base mantida: `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`,
  worktree suja/compartilhada preservada. Primeira fronteira: ramo residual de
  `_destaques_com_papel` atribuía `obra_candidata` a tudo que não reconhecia.
  O verificador rejeitava e o orquestrador pesquisava `desfaz`/`o contrário`.
  Capturas anteriores e RED sem modelo/provedor falsificam truncamento na
  geração e falha de pesquisa como causas desse corte específico.
- Contrato: título precisa de indício relacional (tipo, seleção, nomeação,
  enumeração tipificada ou resposta nominal ao tipo solicitado). Sem indício,
  papel `indeterminado`, não obra e não enunciado isento. Datas, medidas,
  categorias e estados continuam passando por suas verificações; contexto
  não vira fonte nem autorização. A leitura do texto completo sobrevive à
  divisão em frases. Pesquisa e validação recebem o mesmo contexto do usuário.
- RED inicial: **15 falhas / 24 verdes**, sendo **11 falhas comportamentais**
  e quatro da nova assinatura contextual ainda inexistente (estas quatro não
  contam como prova causal). O teste com `x` ficava verde pela limitação antiga
  de duas letras no scanner, não pelo papel correto; trocado por `delta`.
- Dois controles antigos de obras revelaram lacunas na primeira versão do
  candidato; mantidos e atendidos. Um controle diferente atribuía um título
  de filme a `Noite Inventada` num exemplo ambíguo de abrir aplicativo.
  Expectativa corrigida por não haver indício de obra; nova prova conserva
  a rejeição de data dentro desse trecho, sem mascará-lo como enunciado.
- Produção desta rodada: `cognicao/fundamentacao_factual.py` e passagem do
  `texto_usuario` em `cognicao/orquestrador_turno_runtime.py`. Testes ampliados
  nos arquivos de explicação didática e citações existentes. Sem mudança em
  pesos, autorização, executores, personalidade ou `laylay.py`; nenhum commit.
- Provas: **430 aprovados / 13 xfailed preexistentes**, seleção de 16 módulos,
  incluindo import da composição real, segurança e recomendação. Não é suíte
  global. Uma tentativa paralela à sonda deu três falhas de import pelo lock
  de instância única (427 verdes); repetida após saída da sonda, sem alterar
  a proteção, resultou nos 430 verdes acima.
- Runtime: `resultados_testes/roteiro_ensino_divisao-20260922-173131-509832/`;
  HTTP em `transporte_evidencia-20260922-173130-396574/`. Somente turno 3 usa
  replay explícito da captura `transporte_evidencia-20260922-171829-788015`;
  demais turnos têm geração nova. As explicações entre aspas chegaram inteiras
  sem busca de obra. O guardião de perguntas marcou `perguntas_em_excesso` e
  ajustou pontuação na saída do terminal, não removeu as cláusulas citadas.
  Sessão terminou com código zero, sem processo Laylay restante. Voz/UI/mic
  desligados, IoT simulado, Gmail inativo; observadores e persistência normais
  ativos. Placar 4/4 só certifica ausência de comandos, não qualidade didática.
- **Limites e próxima raiz:** não é classificador semântico universal nem
  verificador matemático. Mantida a distinção incorreta contrário/inverso do
  rascunho para provar preservação, não sua verdade. Nesta geração nova, turno
  2 prometeu passos sem entregá-los; turno 4 recusou `quero im` como comando
  inválido. Ambos já constam do texto bruto: **P01/geração**, próximo alvo,
  não novos remendos no extrator. Resumo com `principal_duplicada` reapareceu;
  permanece achado separado, sem prova do conteúdo persistido.

### P10 / P01 — Ensino perde passos no verificador; geração tem falhas próprias — 22/09

- Base `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`; worktree paralela
  preservada. Relato de 21/09, 10:37:02–10:37:05: o rascunho contém a divisão
  por agrupamento e seus passos; o extrator interpreta a pergunta citada
  `6 cabe quantas vezes em 18?` e o nome do método como obras. Pesquisa sem
  evidência → rejeição das frases → só enunciado e resultado chegam ao usuário.
- Falsificações: não era necessário aumentar o limite de tokens para salvar
  esses passos, pois já estavam na geração; o corte se reproduz sem modelo e
  sem provedor de pesquisa. O problema não é exclusivamente matemática: o mesmo
  classificador de papéis trata perguntas instrutivas e referências conceituais.
  A resposta a `quero im` no log histórico já era inadequada antes do guardião,
  portanto não se atribuiu toda a qualidade do ensino ao mesmo defeito.
- Contrato P10 ampliado no owner existente `fundamentacao_factual.py`:
  pergunta proposta ao interlocutor e retomada explícita do que ele quis dizer
  são enunciados; nome tipificado como método/conceito/termo é referência
  conceitual, não obra. Referência conceitual não mascara datas/medidas nem
  certifica a existência, correção ou propriedades do conceito. Citações não
  viram utterances autorizantes; obras vizinhas continuam exigindo evidência.
- RED inicial: **7 falhas / 6 controles verdes**. Primeira sonda revelou outra
  ocorrência da mesma fronteira: a geração pedia esclarecimento citando
  `quero im`, mas o verificador substituía por falta de fonte factual.
  Reproduzidos mais **3 REDs / 14 verdes** antes de incluir essa retomada.
- Produção alterada nesta rodada: somente `cognicao/fundamentacao_factual.py`.
  Novo `scripts/tests/test_explicacao_didatica_preservada.py`; roteiro
  `scripts/roteiros/roteiro_ensino_divisao.py`, aceito na sonda existente de
  transporte. Nenhum patch de pesos, executor, personalidade ou orçamento.
  Pesquisa em cinco camadas continua fora do escopo.
- Provas finais: **19 testes próprios**, incluindo o verificador ligado pelo
  `laylay.py`, com pesquisa proibida para a aula histórica; seleção ampliada
  **212 aprovados / 13 xfailed preexistentes**. Sem alteração dos xfails.
- Duas sessões completas com geração local nova, microfone/voz/UI desativados,
  Gmail inativo, IoT simulado e observadores/persistência normais ativos:
  `roteiro_ensino_divisao-20260922-171645-086047` e
  `roteiro_ensino_divisao-20260922-171831-067132`, em `resultados_testes/`.
  Capturas HTTP/preparação: `transporte_evidencia-20260922-171643-712042` e
  `transporte_evidencia-20260922-171829-788015`. Ambas preservaram integralmente
  o passo a passo gerado no turno 2, sem pesquisar sua pergunta como obra.
  Primeira tentativa 17:16:31 abortou antes dos turnos por expressão não literal
  nas expectativas do roteiro; corrigida somente a fixture para o loader.
- **Ainda RED, mesma P10:** aspas de ênfase/predicado (`a divisão 'desfaz' a
  multiplicação`, `'o contrário'`) e outras molduras (`a divisão pergunta:`)
  seguem caindo na classificação residual de obra. Não basta ir adicionando
  frases: a próxima investigação deve separar papel desconhecido de evidência
  positiva de obra, preservando os controles de títulos e fatos externos.
- **Ainda aberto, P01/geração:** as duas sondas geraram distinção confusa entre
  contrário/inverso. No último turno da segunda sessão o modelo voltou a negar
  capacidades externas, sem relação com a aula; o texto ruim já estava no HTTP.
  O esclarecimento citado pós-correção está validado localmente, mas essa última
  geração não o produziu: não alegar correção integral de `quero im` no runtime.
- A primeira sonda marcou 2 aprovações/1 falha/1 alerta; a segunda marcou 4/4,
  apesar desses defeitos visíveis. Expectativas verificam ausência de comandos,
  não qualidade didática. **4/4 não é aprovação do ensino.**
- Achado separado durante a segunda sonda: tentativa de resumo das últimas
  cinco interações recebeu `principal_duplicada` e em seguida houve log de
  memória salva. Isso não prova o conteúdo persistido; auditar o consumidor de
  sentinelas antes de atribuir contaminação a essa origem. Não corrigido aqui.
- Estado: melhoria de P10 comprovada nos passos históricos e em geração real;
  P10/P01 permanecem abertos nos limites acima. Nenhum commit criado.

### P04 — Contador observava a porta legada, não o ADD executado — 22/09

- Base `main`, HEAD `bd94bc3e3a29c49906dc603f9ca1540310ca3274`;
  alterações paralelas preservadas. Reproduzido novamente o histórico:
  a faixa correta está no arquivo, mas `add_final=0` (um RED / um controle).
- Cadeia demonstrada por código e observação: feedback chama
  `RegistroOperacoesMusicais.adicionar_faixa_resultado` →
  `OperacoesMusicaisRuntime.adicionar_faixa_resultado` →
  `PlaylistRuntime.add_and_verify_result`. O contador do teste envolvia apenas
  `add_and_verify`, o wrapper bool legado, que essa cadeia não chama.
- Duas observações independentes, uma em cada porta, confirmaram **zero chamadas
  legadas e uma detalhada**, com uma faixa persistida. A comparação com o
  contador antigo produziu outro RED, antes da correção do teste. No controle
  de CREATE falho, ambas as portas tiveram zero chamadas e nenhum alvo salvo.
  Falsificadas ausência de ADD e falha de persistência como causas de P04.
- Correção exclusivamente no harness histórico
  `scripts/tests/test_red151_runtime_canonico_c3.py`: contador envolve a porta
  detalhada, sem mudar o retorno nem a exigência de **exatamente uma** chamada.
  Removida instrumentação duplicada; bloqueio após CREATE falho segue exigindo
  zero ADD. Nenhum executor de produção foi alterado para satisfazer o teste.
- Outra lacuna de composição do mesmo harness: faltava o callback de publicação
  que `laylay.py` realmente fornece. Incluída captura de receipts e reforçadas
  as asserções de sucesso/falha, alvo musical e ordem `receipt → fala`. Não é
  prova do publicador real: essa fronteira é coberta separadamente por
  `test_root_publica_receipt_antes_da_fala_com_persistencia_real` (P03).
- Provas: **4/4** no composto e controle da medição; **24/24** incluindo P03,
  guardião e composição real importada; **352 aprovados** na seleção ampliada
  playlist/feedback/receipt/adaptador/cooperação. Escritas somente em diretórios
  temporários dos testes. Nenhuma playlist pessoal, rede ou sessão alterada.
- Estado: **P04 encerrado como defeito de instrumentação**, não como bug de
  salvamento corrigido em produção. Isso não encerra P03 no runtime completo,
  nem a qualidade geral da conversa. Próxima raiz prevista: ensino/conversa,
  separando o texto gerado da informação removida pelos verificadores.

### Verdade operacional da fala — receipt limita a certeza — 22/09

- Objetivo desta frente: impedir que personalidade, status otimista ou autoria
  da LLM aumentem a certeza acima do resultado realmente observado. Não houve
  redesenho do estilo da Laylay: repertório, emoção e personalidade foram
  preservados; a mudança atua somente na camada factual que antecede a fala.
- A arquitetura já possuía boas defesas: `planejar_resposta_acao()` separava
  sucesso/falha/incerteza, a autoria LLM recebia um contrato imutável e o
  guardião de alegações já sabia remover conclusão sem evidência. A
  investigação procurou os pontos onde essa verdade ainda podia ser
  reconstruída ou promovida antes de chegar a essas defesas.
- RED 1 — `AdaptadorResultadoOperacional.falar_por_status()`: um executor
  moderno podia publicar `confirmado=False` ou `confirmado=None` e, em
  seguida, a fala reconstruía `confirmado=True` apenas porque o status era
  otimista, como `app_aberto`. O adapter agora consome o tratamento moderno
  já publicado; inferência por status ficou restrita à compatibilidade legada.
  Resultado moderno explícito nunca perde seu `False/None` durante a fala.
- RED 2 — semântica da incerteza: `executou=None, confirmado=None` era
  verbalizado como “Enviei o comando...”, inventando até a tentativa.
  `executou=True, confirmado=None` continua podendo dizer que o comando foi
  enviado sem resultado confirmado; execução desconhecida agora diz somente
  que **não há confirmação de que a ação chegou a ser executada**.
- RED 3 — não execução por política: `nao_executado_por_politica` era
  classificado como falha e podia virar “não consegui/tentei”. O planejador
  ganhou a classe `nao_executado`: a fala-base declara “não executei”, sem
  inventar tentativa ou incapacidade. Essa classe permanece calma e não passa
  pelo estilizador de sucesso.
- RED 4 — tri-state perdido na normalização:
  `normalizar_resultado_acao()` tratava campo ausente e
  `"confirmado": None` como a mesma coisa, podendo promover `None` explícito
  a `True` por causa do status. Agora **campo ausente** mantém a inferência
  legada; **campo presente com None** preserva a incerteza moderna.
- RED 5 — última fronteira antes do TTS:
  `OrquestradorFalaRuntime.falar_resultado_operacional()` deduplicava a fala,
  mas confiava integralmente no texto recebido. Ele agora aplica o guardião
  existente usando somente o receipt atual antes de chamar a voz. Uma fala
  “Pronto, abri o Chrome” permanece idêntica quando o receipt confirma; com
  `confirmado=None` é corrigida para envio sem confirmação; com não execução
  confirmada, a alegação de sucesso é removida. O gate é exclusivo da fala
  operacional e não altera conversa/personagem.
- Auditoria de bypasses diretos: sucessos diretos encontrados em organização de
  janelas, volume/autonomia e leituras de agenda/navegador já estavam atrás de
  confirmação/releitura local. Não foram migrados desnecessariamente.
- Scanner estrutural encontrou somente dois executores não musicais capazes de
  publicar status listado como confirmado sem `confirmado=` explícito:
  `site_aberto` remoto no PC B e `remetente_silenciado` no Gmail.
  Ambos foram fechados e o scanner terminou em **0 ocorrências**.
- PC B: enviar `open_url` prova despacho, não que a aba apareceu. O resultado
  passou de `site_aberto` para `abertura_solicitada`,
  `executou=True, confirmado=None`; a fala informa que a abertura foi pedida
  e ainda não confirmada.
- Gmail: o executor descartava o bool real de
  `_gmail_silenciar_remetente()`, engolia exceção e sempre dizia sucesso.
  Agora só publica `remetente_silenciado` com retorno `True`;
  `False`/exceção viram `falha_execucao` e alvo ausente vira
  `alvo_ausente`, todos com execução/confirmação explícitas.
- Provas focadas da fronteira de fala: **161/161 aprovados**. REDs adicionais
  de adapter, tri-state, semântica de incerteza, política e último gate do TTS
  também ficaram verdes. Scanner final:
  `CONFIRMED_STATUS_WITHOUT_EXPLICIT_RECEIPT=0` fora da frente musical.
- Regressão global controlada final:
  **6.692 passed, 1 skipped, 13 deselected, 14 xfailed, 56 subtests passed**,
  zero falhas. Os mesmos oito testes de root bloqueados pela instância real
  passaram **8/8** com bypass de mutex exclusivamente no processo de pytest.
- Validação mecânica: `py_compile=0`, `git diff --check=0`. Neural continua
  em `shadow`; hashes do modelo ativo e v27 permaneceram
  `07C539...9E62` e `CAAA93...E0CF`. A frente
  `executor_musical/executor_playlists/controle_midia/playlist_runtime`
  permaneceu fora do diff desta investigação.
- Regra arquitetural consolidada: **a personalidade decide como dizer; o
  receipt decide o que ela pode afirmar. A fala nunca aumenta a certeza.**

### P03 — Publicação do resultado antes da conclusão — 22/09

- Base preservada: `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`,
  worktree suja. Nesta retomada o adaptador, o planejador e os testes da frente
  paralela já continham mudanças posteriores: os dois REDs citados em P18/P19
  passaram sem novo patch nosso nesses arquivos. A normalização preserva
  `confirmado=None` explícito; os testes agora publicam tratamento depois da
  construção do adaptador, conforme o ciclo de vida da invocação.
- P03 continuava RED: `create → add → ultima → fala → receipt`. O callback
  oficial existe tanto no teste quanto no getter real em `laylay.py`;
  `FeedbackPendenteRuntime` já o repassa. Ausência de injeção é falsificada.
  CREATE/ADD retornam sucesso e o mesmo guardião aceita a fala quando recebe
  antes o receipt: não é necessário relaxar o guardião nem corrigir o storage.
- Primeira divergência: `fluxos_conversa.handle_feedback_pendente` emitia a
  conclusão antes do bloco de publicação. Contrato compartilhado: **efeito
  observado → publicação canônica → conclusão**, não fala como prova de efeito.
  A implementação foi ajustada no orquestrador responsável, reutilizando o
  registrador e o contrato consumidos pelos demais domínios.
- RED novo: 15 casos falharam antes do patch. Incluem sucesso, idempotência,
  falha de criação/adição, faixa ausente, dois nomes e indisponibilidade do
  publicador. No ramo sem faixa, o receipt acessava `criacao` não inicializada;
  esse caminho agora publica a falha e produz uma única resposta.
- A publicação vem antes da fala; ausente, com exceção ou `False` explícito,
  impede a confirmação de sucesso. O fluxo informa a falha de registro sem
  inventar falha da escrita nem repetir o efeito. Duplicata é reconhecida como
  estado já satisfeito; criação só é anunciada se o executor informou `criada`.
- Produção alterada nesta rodada: somente `autonomia/fluxos_conversa.py`.
  Novo teste: `scripts/tests/test_feedback_publicacao_antes_fala.py`.
  Guardião, armazenador, composition root, neural e patches paralelos intactos;
  nenhum commit, alteração das playlists pessoais ou efeito em Chrome/IoT.
- Provas: histórico P03 e controles passaram; **16 testes novos verdes**.
  Um deles importa o `laylay.py` e usa os objetos reais de feedback, registro
  musical, operações, armazenamento e publicação. CREATE/ADD gravam arquivo
  temporário, a saída verifica receipt no plano antes da fala e a segunda
  confirmação mantém uma só faixa. Voz é capturada, observação do player é
  controlada e aprendizado desligado: **integração da composição real**, não
  uma sessão completa com áudio/Chrome/modelo.
- Regressão ampliada de playlist/feedback/receipts/adaptador/cooperação:
  **348 aprovados**. O teste composto P04, executado separadamente, permanece
  **1 falha / 1 aprovado**, no contador `add_final=0` em vez de 1; não foi
  removido, alterado ou considerado resolvido pela correção P03.
- Estado P03: corrigido e validado localmente e na composição com disco real;
  sessão completa ainda pendente. Próxima fronteira operacional: esclarecer a
  medição de P04 antes de mudar o executor. Ensino/conversa permanece outra raiz.

### P18 / P19 — Escopo da consulta e evidência da confirmação — 22/09

#### Continuação de F2 — feedback diagnóstico e fala transformada, 29/09

- Loop real da P16 expôs `tamanho_invalido`/narração de erro em confirmação
  de `ja_aberto_focado`, executou=False, confirmado=True, detalhe vazio.
  O retry fornecia o motivo técnico como conteúdo. Replay local sem histórico
  aprovava a fala histórica; guardião final não a continha. Receipt falho e
  histórico obrigatório foram falsificados. O HTTP histórico não foi capturado.
- O motivo permanece local; reparo usa somente fatos/restrições existentes.
  A allowlist de parâmetros é a mesma da projeção e do verificador; contexto
  diagnóstico e parâmetros arbitrários não autorizam identificadores na fala.
  Nomes legítimos e diagnósticos publicados pelo executor continuam permitidos.
- A transformação da abertura também atravessa novamente o verificador antes
  da entrega. Aprovação anterior não aprova texto alterado. O controle antigo
  mantém a expectativa de abertura variada usando recusa factual na primeira
  frase; antes dependia de transformação não validada para passar.
- Seis REDs iniciais/controles e cinco REDs da projeção antes do candidato.
  65 testes focados de confirmação/escopo aprovados; no passe conjunto final,
  395 testes aprovados. A tentativa concorrente de importar a composição foi
  repetida depois de encerrar o processo real, respeitando a trava de instância.
- Em `roteiro_teste_personalidade_viva_p16-20260929-230505-663752`, as 14 falas
  reais posteriores não continham identificadores técnicos; motivos continuam
  observáveis nos logs. Esse roteiro teve 5/14 no placar emocional por efeitos
  de foco e pela lacuna de conquista descrita na P16; não contar como sequência
  emocional verde. Sem chamada adicional ao modelo. Prosa que inventa culpa
  sem código permanece limite de cobertura: F2 não está integralmente encerrada.

- Base: `main`, HEAD `bd94bc3e3a29c49906dc603f9ca1540310ca3274`,
  worktree suja com alterações paralelas de cliente, neural, modalidade e
  contratos operacionais. Essas alterações foram preservadas; nenhum commit.
- Evidência histórica: os dois últimos relatos em `erros/erros_encontrados.md`
  (pergunta sobre garantia de chuva amanhã; clima anexado ao salvar em yago).
  São duas causas demonstradas, não uma causa única comprovada de briefing.
- **P18 / F1, escopo perdido:** o publicador canônico de continuidade removia
  `local`, `cidade` e `day_offset`; o detector tratava o aprofundamento como
  consulta nova para hoje. O executor respondia com condições atuais sem
  responder sobre certeza. A redação histórica existe nesse executor, portanto
  não é necessário atribuí-la a briefing ou alucinação do modelo. RED local
  demonstrou a perda antes de qualquer chamada ao provedor.
- Contrato: aprofundamento meteorológico herda escopo apenas de consulta
  bem-sucedida, recente, do domínio ativo e do mesmo dia. Cidade/data explícita
  vence; troca de assunto/expiração impede herança. Probabilidade não vira
  garantia, inclusive em 0%/100%; ausência de dados não vira confirmação.
- **P19 / F2, fatos alheios na autoria:** o pedido de confirmação levava falas
  anteriores completas como exemplos de não repetição. O verificador aceitava
  a paráfrase climática histórica; repetição literal e paráfrase não são o
  mesmo contrato. Reproduzido em playlist, IoT e criação de pasta. O HTTP
  histórico não foi capturado: a exposição e vulnerabilidade estão provadas,
  mas não se afirma conhecer todo o prompt daquela execução do usuário.
- Contrato: autoria operacional recebe somente dados do resultado atual,
  usando o mecanismo existente `_contexto_fechado`. Histórico permanece no
  verificador local, não no pedido ao modelo. Números novos sem evidência
  provocam reparo e, se ele falhar, a fala factual segura. A limpeza de pergunta
  opcional também repassa por toda a validação, sem atalho de aprovação.
- Hipóteses concorrentes: defeito no provedor não explica a perda local de
  parâmetros; briefing não é necessário para produzir a resposta histórica;
  problema exclusivo de playlist é falsificado pelas provas em três domínios.
  Isso não é prova geral contra toda invenção verbal sem números.
- Produção alterada somente em `continuidade_geral.py`,
  `roteador_deterministico.py`, `orquestrador_deterministico.py`,
  `executor_informacoes.py` e `confirmacao_llm.py`. Nenhuma mudança nossa em
  pesos, ativação neural, armazenamento de playlists, IoT ou `laylay.py`.
- RED inicial: **6 falhas / 5 controles verdes**. Após candidato:
  **19/19** em `scripts/tests/test_escopo_consulta_e_confirmacao.py`, incluindo
  publicação/detecção do composition root real e preparação HTTP real com
  transporte controlado. Receipts sintéticos nessa prova não certificam efeito.
- Regressão ampliada atual: **189 aprovados / 2 falhas** em dez módulos.
  Os dois REDs são `test_fala_por_status_nao_eleva_confirmacao_negada_pelo_contrato`
  e `test_fala_por_status_nao_transforma_sem_receipt_em_sucesso`, também
  reproduzidos isoladamente no adaptador (**26 aprovados / 2 falhas**).
  A primeira divergência está antes da autoria: o construtor apaga o tratamento
  que os testes publicam antes dele; há também inferência por status quando
  `confirmado=None`. Pertencem à frente paralela tratado/receipt, não foram
  corrigidos aqui nem removidos da contagem. Verificar ciclo de vida e preservar
  a distinção entre ausência legada e incerteza explícita antes de novo patch.
- Runtime real executado com voz/microfone/presença desativados e IoT simulado:
  `resultados_testes/roteiro_escopo_previsao-20260922-064429-204197/`.
  Três consultas, nenhuma escrita de playlist. Fonte primária e reserva deram
  timeout; três falhas foram informadas com `executou=False, confirmado=False`.
  O resumo automático tem **zero casos avaliados**, não três aprovações.
  **Runtime com previsão bem-sucedida ainda não validado.** O roteiro reutilizável
  está em `scripts/roteiros/roteiro_escopo_previsao.py`.
- Estado: GREEN local/integração nos contratos novos; regressão ampliada não
  totalmente verde; P18/P19 ainda não encerrados no runtime. Próxima prova:
  repetir consulta com fonte disponível e verificar confirmação operacional
  com geração real. Relatos antigos de ensino, DEV e presença continuam
  separados; esta entrada não encerra toda a pasta de erros.

### Contrato tratado ≠ executado ≠ confirmado — 21/09

- A investigação partiu de um risco sistêmico: callbacks históricos retornam
  `True` tanto para “esta camada tratou o pedido” quanto para “o efeito ocorreu”.
  O candidato já presente na worktree separava `tratado`, `executou` e
  `confirmado`, mas ainda considerava `executou=True, confirmado=None` como
  `sucesso_habilidade=True`.
- RED real reproduzido em três fronteiras do mesmo fato: uma execução moderna
  sem receipt era registrada no autoaprimoramento como **1 sucesso / 100%**,
  recebia reforço positivo e permitia que uma cadeia avançasse para a etapa
  dependente. Foco inicial: **3 falhas e 6 vizinhos verdes**.
- Contrato canônico ficou trivalente. Para resultados modernos:
  `confirmado=True` = sucesso comprovado; `confirmado=False` = não sucesso;
  `executou=True + confirmado=None` = **resultado incerto**, nunca sucesso.
  Retornos puramente legados preservam temporariamente a compatibilidade do bool
  para não quebrar executores ainda não migrados.
- `ResultadoTratamentoOperacional` ganhou `resultado_incerto`. O
  autoaprimoramento também passou a aceitar resultado neutro: incrementa
  `tentativas` e `incertos`, mas não `sucessos`, não `falhas` e não
  `cookie_reforco`. O resumo expõe “sem confirmação”; a taxa confirmada usa
  somente resultados realmente avaliados.
- O gate central de `EstadoContextoRuntime.registrar_autoaprimoramento` não
  deixa um bool externo transformar contrato moderno em sucesso: receipt
  confirmado entra como sucesso, efeito incerto entra neutro e política/falha
  não reaparece como êxito.
- A deduplicação do `CicloComandosRuntime` estava apagando a identidade de
  compatibilidade do retorno legado. O cache agora preserva `legado` e não
  “moderniza” uma segunda ocorrência de bool antigo em contrato moderno sem
  receipt.
- A caixa de entrada expôs o inverso do mesmo princípio. O helper genérico
  continua proibido de inferir `confirmado=executou`; em vez disso, operações
  que possuem evidência local real publicam seu próprio receipt: persistência
  de nota/discussão, duplicata já observada, listagem local e exclusão salva.
  **O owner que observa o efeito confirma; a camada genérica não adivinha.**
- Provas focadas: **9/9** no contrato novo; **51/51** em cadeia/deduplicação/
  publicação; **350 aprovados + 8 subtests** nos consumidores sensíveis
  (orquestração, autonomia, caixa, transferências e mente única).
- Regressão global controlada:
  `6636 passed, 1 skipped, 13 deselected, 14 xfailed, 56 subtests passed`,
  zero falhas. Dos 13 deselecionados, oito testes do root foram bloqueados pela
  instância real já aberta e passaram **8/8** com bypass de mutex somente de
  teste; os cinco restantes foram reproduzidos no HEAD limpo
  `bd94bc3e`: três REDs históricos de feedback/playlist e dois de ownership
  de presença. Portanto não são regressões desta correção.
- Nenhuma dessas provas promove modelo neural, altera pesos ou transforma
  ausência de confirmação em falha. O objetivo é impedir sucesso fictício sem
  inventar fracasso fictício.

### Migração do legado operacional e barreira sem receipt — 21/09

- Continuação da frente `tratado ≠ executado ≠ confirmado`. Após tornar
  `executou=True + confirmado=None` neutro, a próxima pergunta foi onde um
  bool puro ainda conseguia entrar no contrato moderno.
- Scanner estático dos executores não musicais encontrou quatro saídas reais
  tratadas sem publicação explícita: volume com ação inválida, IoT
  indisponível/bloqueado antes do runtime, `SUGGEST_ACTION` e o alias
  `FECHAR_PROGRAMA`. RED no roteador real: **4 falhas e 9 vizinhos verdes**;
  todos apareciam como `legado=True`.
- Volume inválido agora publica `acao_invalida`,
  `executou=False, confirmado=False`. IoT sem runtime publica
  `indisponivel`; veto de modalidade publica
  `nao_executado_por_politica`. Nenhum desses caminhos pode mais ser
  promovido a sucesso por um bool externo.
- `SUGGEST_ACTION` permanece semanticamente sem efeito operacional, conforme
  o catálogo de capacidades. Quando a sugestão local é registrada, marca
  somente tratamento (`sugestao_registrada`), com
  `executou=False, confirmado=False`; não cria receipt de ação nem
  autoaprimoramento de sucesso.
- `FECHAR_PROGRAMA` deixou de criar um segundo dict recursivo de
  `CLOSE_APP`. O alias delega diretamente à mesma habilidade usando o mesmo
  adapter, preservando a identidade original e produzindo **um único receipt**.
  Sem alvo, publica `alvo_ausente`.
- Foi adicionado um fail-closed no roteador para executores modernos não
  musicais: se um `ResultadoDespacho` disser que tratou a intenção e nenhum
  receipt/tratamento tiver sido publicado, o resultado vira
  `tratado_sem_receipt`, com `executou=None, confirmado=None`. O bool antigo
  continua apenas em `retorno_legado`; não cria sucesso, falha ou efeito
  imaginado. Música/playlist/`MEDIA_CONTROL` ficaram explicitamente fora
  dessa barreira nesta etapa para não invadir a frente paralela do Codex.
- RED específico injetou propositalmente um executor moderno de arquivos que
  retornava `True` sem receipt. Antes: `legado=True, executou=True`; depois:
  `legado=False, tratado=True, executou=None, confirmado=None,
  status=tratado_sem_receipt`.
- O `CicloComandosRuntime` ganhou telemetria de contrato sem alterar
  autoridade ou decisão: `observados`, `legados`,
  `tratados_sem_receipt`, `confirmados`, `nao_confirmados`, `incertos`,
  além de mapas `legados_por_intent` e `sem_receipt_por_intent` e as últimas
  intents observadas. Assim, a migração futura pode ser guiada por uso real.
- O diagnóstico central já consumia
  `diagnostico_linguagem_natural()`; o formatter do Terminal agora expõe uma
  linha compacta “contrato de execução” com esses contadores e as últimas
  intents legada/sem receipt. O snapshot bruto preserva os mapas completos.
  A presença de compatibilidade legada **não degrada automaticamente** a saúde:
  nesta fase a telemetria é informativa.
- Provas da etapa: **53/53** no primeiro lote de executores/contrato;
  **184/184** em todos os executores não musicais + arquivos;
  **206/206** após adicionar a telemetria; **53/53** nas regressões de
  diagnóstico/formatter. Regressão global controlada:
  **6.642 passed, 1 skipped, 13 deselected, 14 xfailed, 56 subtests passed**,
  zero falhas. Os 13 deselecionados são os mesmos já causalmente isolados:
  cinco REDs preexistentes e oito testes de root bloqueados pela instância real.
  Os oito de root passaram novamente **8/8** com bypass de mutex somente no
  processo de pytest.
- Não houve promoção neural, alteração de pesos, commit, push, merge ou
  reescrita destrutiva. A compatibilidade booleana permanece disponível apenas
  para caminhos realmente legados; executores modernos não musicais agora
  falham fechados quando esquecem o receipt.

### Cadeias dependentes exigem sucesso do contrato — 21/09

- A telemetria/migração do contrato revelou outra fronteira booleana no fluxo
  composto. `executar_fluxo_intencao()` já interpretava
  `ResultadoTratamentoOperacional`, mas devolvia `bool(retorno)`. Assim, uma
  etapa moderna podia estar `tratada_sem_receipt`, com
  `sucesso_habilidade=False`, e ainda retornar `True` para a cadeia.
- Reprodução direta antes do patch: executor marcou
  `tratado=True, executou=None, confirmado=None,
  status=tratado_sem_receipt`, retornou `True` e
  `executar_fluxo_intencao()` também devolveu **True**.
- A causalidade foi conferida no HEAD base
  `bd94bc3e3a29c49906dc603f9ca1540310ca3274`: a versão congelada fazia
  `executou = bool(_call(... executar_intencao ...))`, publicava esse bool,
  autoaprimorava quando verdadeiro e devolvia `executou`. Portanto a
  ambiguidade já existia no baseline.
- O retorno padrão foi preservado por compatibilidade: fora de composição
  dependente, `True` ainda pode significar “o turno foi consumido/tratado”.
  Foi adicionado o modo explícito
  `exigir_sucesso_habilidade=True`, que devolve somente
  `tratamento.sucesso_habilidade`.
- `CicloComandosRuntime.processar_cadeia()` é o único consumidor conectado a
  esse modo estrito. Consultas somente leitura continuam concluindo sua etapa
  pelo próprio contrato observacional; mutações passam pelo modo estrito.
- Consequência: se a etapa A for tratada mas não tiver receipt suficiente, a
  cadeia relata a falha e **não chama a etapa B dependente**. O comportamento
  standalone permanece compatível, evitando transformar “não avançar cadeia”
  em “reprocessar o turno inteiro”.
- RED de fronteira inicialmente falhou porque o modo estrito não existia.
  Após a correção, o mesmo caso preserva `True` no standalone e retorna
  `False` no contexto dependente. Teste de composição adicional prova que a
  cadeia canônica chama somente a primeira etapa com
  `exigir_sucesso_habilidade=True` quando ela falha.
- Regressão focada após a mudança: **23/23** nos contratos históricos do fluxo
  e **90/90** no conjunto coordenador/cadeia/linguagem natural/contexto.
  Regressão global controlada final: **6.645 passed, 1 skipped,
  13 deselected, 14 xfailed, 56 subtests passed**, zero falhas. Os mesmos oito
  testes de root bloqueados pela instância real passaram **8/8** com bypass de
  mutex somente no pytest.
- A compatibilidade de bool realmente legado continua temporariamente fora
  desse fechamento total; a frente musical paralela também não foi alterada.
  O objetivo desta etapa foi impedir que **resultado moderno explicitamente
  não comprovado** libere uma dependência posterior.

### Raiz de versionamento da supervisão neural — 21/09

- Base `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`; worktree
  paralela preservada, incluindo `modelo.py` da v29. Primeira fronteira RED:
  leitores históricos recusavam duas dependências da linguagem diferentes.
  Reprodução direta, ultrapassando apenas a leitura para diagnóstico:
  `conferir_casos` falha por **alinhamento divergente**, não por import.
- Falsificadas as hipóteses de corpus alterado e de mudança somente nos hashes:
  os lotes mantêm seus SHA-256, mas há **144 divergências** em cada lote
  (mesmos casos, não 288 casos únicos). Em 96 mudou apenas a referência de
  leitura; em 48 também mudaram segmentação e offsets relativos. O diff da
  linguagem mostra reconhecimento ampliado de recusa e moldura de necessidade.
  Os arquivos de linguagem são iguais a HEAD; não atribuir o bloqueio ao SOL.
- Contrato: **anotação independente preservada não implica leitura histórica
  equivalente**. Owner offline `revalidar_perfil_v4.py` ganhou reprojeção
  explícita, mantendo o replay estrito como padrão. Compara supervisão completa
  em coordenadas literais absolutas: atos, âncoras, alvos/papéis, relações,
  texto e metadados; valida referências, flags e spans antes da comparação.
  Normalização não literal exige outro perfil. Não utiliza previsão como gold.
- Via nova limitada aos pares de dependências revisados e ao manifesto exato
  das divergências observadas. Mudança futura, corpus modificado, reserva,
  identidade duplicada, alteração de supervisão ou corrida de arquivo abortam.
  Preserva protocolos, folds e leitores antigos; não altera resultados antigos.
  Relatório declara `compatibilidade_no_corpus=false`, supervisão preservada,
  classificador não reavaliado e runtime não validado.
- Os testes dos algoritmos atuais agora pedem a reprojeção explicitamente.
  Não enfraquecidas as asserções de comportamento; testes negativos continuam
  exigindo bloqueio dos leitores históricos. Asserções específicas protegem
  adulteração de atos, alvos, âncoras, relações, referência e autoridade.
- **53 testes focados passaram** antes dos controles adicionais. CLI offline
  real executada com sucesso, sem fit: **1.176 casos únicos**, folds idênticos.
  Evidência: `memoria/neural/experimentos/reprojecao_literal_v4_20260921/relatorio.json`.
  Regressão neural ampla após os controles adicionais: **1.425 aprovados,
  1 skipped, 5.220 deselected**, zero falhas/erros, 105,63 s
  (`pytest scripts/tests -k neural -q --tb=short`). Os 23 bloqueios anteriores
  foram resolvidos. Isso não é suíte global, runtime da assistente ou prova
  de qualidade da v29. `compileall` focado e `git diff --check` passaram.
- **Observação separada, associada à fronteira F1, ainda não diagnosticada:**
  no caso `rel_v4_necessidade_apps_e0_t0_q0_recusa_pedido`, a cláusula
  “não é para abrir o aplicativo pelvora” aparece como `conversa`, sem veto,
  enquanto a anotação mantém `recusa`. O pedido subsequente é separado.
  Não houve executor nessa prova; não concluir que a ação proibida foi executada.
  Próxima investigação deve testar recusa isolada/mista em domínios distintos
  no owner de modalidade e no consumidor de autoridade, antes de corrigir.
- **Fechamento da observação F1 — recusa declarativa “não é para…”:** o RED foi
  reproduzido em app, arquivo e IoT; 4 casos falharam com 20 vizinhos verdes.
  A raiz ficou em `analisar_protecao_operacional`: a moldura declarativa
  `não é/eh para|pra + infinitivo operacional` não possuía leitura geral.
  O contrato foi corrigido no owner de modalidade, sem regra privada por domínio.
  Interrogação continua pergunta; sem interrogação vira `recusa/cancelamento`.
  Em turno misto, o veto pertence somente ao segmento recusado, enquanto um
  pedido independente posterior continua autorizado. Teste do consumidor
  confirma que `processar_execucao_pratica_precoce` entrega somente
  `texto_operacional` do pedido permitido ao determinístico.
- O corpus histórico contém **72 nós** com essa moldura e gold `recusa`; após
  a correção, 72/72 são lidos como recusa com veto. A guarda de compatibilidade
  bloqueou a mudança de `modalidade_turno.py` antes de qualquer atualização.
  Replay explícito preservou supervisão literal e as quatro dobras: a diferença
  contra o snapshot histórico passou de 144 para **160 casos**, com as mesmas
  48 resegmentações. Os 16 deltas novos são recusas isoladas de apps/arquivos
  agora alinhadas ao gold; snapshot observado não foi promovido a gold.
- A reprojeção v1 foi preservada. Nova prova publicada em
  `memoria/neural/experimentos/reprojecao_literal_v4_recusa_declarativa_v2_20260921/relatorio.json`.
  Regressões: **25** testes focados de autorização/consumidor, **33** de
  reprojeção, **76 aprovados + 1 skipped + 22 subtests** em modalidade/autoridade,
  e **1.426 aprovados, 1 skipped, 5.226 deselected** na suíte
  `pytest scripts/tests -k neural -q --tb=short`, zero falhas/erros.
  Isso não certifica runtime completo, qualidade da v29 nem execução real.
- Escopo da etapa de reconciliação anterior: um módulo de infraestrutura
  experimental, quatro módulos de testes e documentação. Naquela etapa,
  linguagem de produção, modelo SOL, pesos ativo/v27, configuração e reserva
  v29 permaneceram intactos. A investigação F1 acima alterou depois somente o
  owner de modalidade; não houve commit, promoção ou ativação.

### Reconciliação das frentes neurais — 21/09

- Base `bd94bc3e`, mudanças paralelas preservadas. Após a cópia da v29, o
  consumidor operacional permaneceu mas perdeu a API opcional de projeção:
  **36 falhas TypeError**. Reposto `rotulos_permitidos` em
  `comparar_ocorrencias_v4.py`, sem mudar o catálogo padrão. README agora mantém
  tanto a v29 do SOL quanto a retomada de cobertura/IoT/mídia. Nenhum patch em
  `modelo.py` entregue pelo SOL; SHA-256 preservado
  `58af0476a9907870ed471e5d0e4e91e104213d32f936b199d51e34efd960ef6a`.
- Testes v29 citados no handoff ausentes da cópia local: seis casos de contrato
  escritos no teste existente para integral/híbrido, OOF, grupos, serialização,
  encoder ausente e preservação da base. Encoder sintético, sem certificar
  qualidade linguística. **75 testes focados passaram**, mais **93 regressivos**
  de coleta/revisão/protocolo/preparação. Modelos ativo/v27 com hashes preservados.
- Suíte neural ampla: **1.384 aprovados, 1 skipped, 6 falhas, 21 erros**. Quatro
  falhas vinculadas à raiz já conhecida de caminhos pós-reorganização: fixture
  de revisão contextual ainda apontava para `tests/fixtures`. Caminho ajustado,
  **32 testes do módulo passaram**, nenhuma expectativa relaxada.
- **Pendência separada de compatibilidade histórica:** 21 erros e duas falhas
  restantes param nos hashes do corpus v4. `modalidade_turno.py` e
  `normalizacao_linguagem.py` são iguais a HEAD e diferem dos hashes exigidos
  pelo protocolo antigo. Não causada pela interface reposta nem atribuída ao
  SOL. A via de revalidação existente só autoriza outra revisão antiga do
  normalizador. Falta provar compatibilidade integral do alinhamento atual;
  nenhuma guarda, baseline ou reserva foi alterada. Não declarar suíte verde.
- Sem treino de produção, promoção, interferência na sessão ou commit. Fits
  executados apenas pelos testes com dados sintéticos e artefatos temporários.

### Continuação: coleta recuperada e preservação de foco, 21/09

- Base atual `bd94bc3e3a29c49906dc603f9ca1540310ca3274`. Recuperação do
  analisador já incorporada por commit externo; AST das funções comparada com
  `c8b4c26`, sem diferenças. **85 testes aprovados**; **6.537 testes coletados
  sem erro** antes da nova regressão de foco. Não equivale a executar a suíte
  global nem a validar/promover o modelo histórico.
- Nova observação do Pedro em `../erros/erros_encontrados.md`: troca de faixa
  ativa YouTube e interrompe estudos. Registrada como **P17**, raiz própria de
  transporte da restrição de foco, sem misturar com as raízes conversacionais.
- Preservadas alterações de empacotamento e o relato do usuário. Pedro informou
  trabalho paralelo do ChatGPT: verificar sobreposição antes de editar e avisar
  imediatamente se houver evidência de risco. Nenhum conflito observado nos
  arquivos deste candidato; isso não é auditoria de todo trabalho paralelo.

### Continuação após reorganização do repositório, 21/09

- Base `d268a51`, preservada a nova organização. P09: ajustados pytest,
  imports/caminhos relativos dos testes movidos, sonda e catálogo DEV Console.
  **60 testes focados aprovados**; seleção ampliada **3.018 aprovados,
  14 xfailed e 30 subtestes**. Não é certificação da suíte global.
- Coleta global bloqueada por dependência ausente:
  `analisar_neural_v27_list_windows_caos`, importada pelo teste homônimo.
  **6.526 testes coletados e um erro**. Não removido nem enfraquecido o teste;
  analisador não restaurado sem conferir sua finalidade e versão.
- Encerramento da sonda: repetição com receipt do processo pai resultou em
  **código 0 e stderr vazio**. Código 1 histórico não reproduzido, causa aberta;
  nenhum patch especulativo no lifecycle. O log genérico que anuncia reinício
  mesmo ao concluir roteiro é impreciso, não prova reinício real.
- Evidência e limites em `../raiz/MAPA_RAIZES_CONVERSA.md`, seção de
  infraestrutura após reorganização. Documentos movidos pelo usuário preservados.

Este é o índice central dos problemas encontrados enquanto corrigimos outros
problemas. Serve para não perder achados, não misturar causas e deixar claro o
que falta. Os relatórios ligados abaixo preservam o diagnóstico detalhado.

O preenchimento inicial usa os relatórios de 12–15/09 e as validações da última
rodada. **Não é uma auditoria exaustiva nem uma nova execução dos testes.**
Uma ocorrência antiga permanece datada até ser revalidada.

## Como manter este arquivo

- Ao encontrar um problema lateral, registrar aqui antes de desviar da correção atual.
- Manter o ID do item; atualizar seu estado e acrescentar evidências, sem apagar o histórico.
- Separar sintoma de causa: várias falhas podem ter a mesma raiz; isso precisa ser provado.
- Informar se a evidência é de runtime, integração ou teste unitário.
- Só marcar uma correção como validada no escopo depois de registrar o teste e seus limites.
- Impacto indica risco, **não muda automaticamente a ordem do trabalho** nem autoriza ações destrutivas.
- Nunca copiar credenciais, tokens ou conteúdo pessoal desnecessário para este índice.
- Ideia futura não é defeito e não significa implementação aprovada.

Estados usados: **a investigar**, **reproduzido**, **parcial**, **limite não validado**,
**adiado**, **validado no escopo** e **ideia guardada**.

## Visão rápida das pendências

| ID | Assunto | Estado | Impacto |
| --- | --- | --- | --- |
| P01 | Explicações ruins sobre como usar capacidades | Parcial: catálogo preservado; qualidade ainda aberta | Coerência e confiança |
| P02 | Recomendações técnicas sem evidência suficiente | 13 REDs corrigidos no escopo de escolha/fala; runtime 30/09 | Comparação técnica completa ainda não certificada |
| P03 | Confirmação de playlist antes do receipt | Corrigido em 22/09; integração da composição real e disco temporário validada; sessão completa pendente | Alto: confirmação prematura |
| P04 | Divergência no contador de ADD do teste composto | Encerrado em 22/09: instrumentação observava o wrapper legado; porta detalhada executava e persistia | Medição corrigida sem alterar produção |
| P05 | Presença não cede na transição da entrada para o turno | Reproduzido em teste de integração | Interferência na fala do usuário |
| P06 | Ponto de extensão em nome de arquivo | Corrigido no escopo; composição e runtime 30/09 | Pontuação interna preservada sem autoridade adicional |
| P07 | Continuidade na rota exclusivamente de áudio | Limite não validado | Possíveis lacunas de histórico |
| P08 | Credencial em logs históricos do Chrome | Parcial: saída nova corrigida | Alto: artefatos sensíveis |
| P09 | Novos testes ficam ignorados pelo Git | Regra corrigida e validada em 21/09; sem staging | Revisar fontes antes de versionar; artefatos já rastreados exigem ação separada |
| P10 | Falso positivo de fundamentação em citação | F1: exemplos com “pedir para” também validados em 21/09; escopo mais amplo aberto | Proteção não deve apagar instruções válidas |
| P11 | Pedido de informação confundido com afirmação de estado | Validado no escopo; ver C08 | Fallback desnecessário corrigido nos casos cobertos |
| P12 | Pergunta de procedimento sem natureza operacional reconhecida | Classificação validada no escopo C11; resposta final ainda falha | Reparo posterior separado em P16 |
| P13 | Nome de aplicativo não recupera seu domínio no catálogo | Recuperação validada no escopo C12 | Resposta final ainda afetada por P10 |
| P14 | Resposta prioritária IoT troca ação e dispositivo | Corrigido e validado no escopo C13 | Qualidade mais ampla da autoria continua em P01 |
| P15 | Falha técnica tratada como pedido ambíguo | Validado no escopo de propagação; limites de conclusão registrados | Causa da latência não investigada |
| P16 | Reparo de explicação presume relato de ação passada | Validado no escopo C15 | Objetivo e fonte preservados; qualidade geral ainda em P01 |
| P17 | Restrição de foco perdida no transporte ao Chrome | Troca musical confirmada por Pedro; fallback compartilhado protegido e testado localmente | Preservação do foco também nas rotas alternativas |

A frente atual é **P01**. O corte do catálogo (C07) e o falso reparo P11 (C08)
foram tratados separadamente; falta melhorar a realização da explicação. A investigação
de recomendações **P02** foi retomada em 30/09 por pedido do Pedro, junto de P06,
antes da continuidade da personalidade P16. Os 14 xfails foram corrigidos por
essas duas causas; a comparação técnica completa continua limitada. A revisão
offline de compatibilidade não promove a rede neural.

## Pendências detalhadas

### Organização por contratos — diagnóstico de 20/09

O [mapa causal da conversa](MAPA_RAIZES_CONVERSA.md) passa a orientar a próxima
etapa: F1 significado, F2 capacidade/fonte/escopo e F3 causa técnica. As famílias
não substituem os IDs nem significam que todos os itens têm uma única raiz.
P01 é abrangente; evitar contá-lo novamente como causa de cada subproblema.

Nesta auditoria, nenhum patch novo de produção: quatro REDs de negativas falsas
em música/sistema/IoT/navegador e um RED de exemplos no infinitivo confundidos
com obras: **cinco REDs, oito controles aprovados** e 261 regressivos anteriores
aprovados. O bruto da retomada já negava a capacidade; o verificador ainda
cortou as instruções, agravando a fala. REDs preservados sem xfail no teste
`test_coerencia_capacidade_documentada.py`. P15 também reproduzido localmente:
três categorias técnicas chegam à contingência como se faltasse clareza.
Próxima implementação: coerência documental compartilhada (F2), depois
propagação da causa técnica (F3), sem novo remendo específico para música.

**Experimento F2, 20/09 às 17:00:** projeção ampliada de contratos operacionais
testada e retirada por não demonstrar benefício global no runtime. Doze
respostas, zero comandos; negativas/promessas inadequadas e cortes ainda
presentes. Dados extras no prompt não corrigiram a conferência da resposta.
Cinco REDs comportamentais preservados; não declarar outra correção concluída.
Detalhes e artefatos no mapa causal. A regra de organizar por raiz foi gravada
no `AGENTS.md`; nenhuma alteração permanente nova em produção nesta rodada.

**F2, 20/09 às 22:10 — conferência validada no escopo, reparo ainda aberto:**
o mesmo comparador passou nas negativas de música, aplicativos, IoT e abas,
com predicados do snapshot canônico e sem ampliar o prompt inicial. Disponibilidade
não virou receipt nem autorização. Seleção ampliada: 2.913 aprovados, um RED
F1, 14 xfailed preexistentes e 30 subtestes; controles posteriores na seleção
focada: 58 aprovados e o mesmo RED F1. No replay pelo runtime real, a negativa
histórica foi detectada; o Qwen repetiu a contradição no reparo, que foi rejeitado.
A resposta final pediu clareza indevidamente (F3). Portanto, não encerrar P01:
há prova de bloqueio, não de recuperação da explicação. Próxima fronteira F2:
isolar influência do rascunho/histórico no reparo, sem empilhar instruções.
Captura `transporte_evidencia-20260920-221039-790886`; detalhes e escopo no mapa.

### P01 — Explicações de capacidade e instruções pouco coerentes

- **F2, 20/09 às 22:18:** ablação de 21 chamadas locais isolou duas cópias do
  conteúdo refutado no reparo (rascunho e trecho de diagnóstico). Retirar só
  histórico ou só uma cópia não eliminou a negativa; retirar ambas conservando
  histórico não a repetiu nas três amostras, embora restasse imprecisão.
  Corrigida a projeção no reparador compartilhado, sem aumentar prompt/orçamento
  ou alterar os executores. Quatro REDs por domínio passaram com a mesma regra;
  ampliado: 2.929 aprovados, um RED F1, 14 xfailed e 30 subtestes. Replay real
  reparou a negativa histórica para uma instrução de retomada, sem fallback ou
  comandos; 12/12 no avaliador mínimo não significa qualidade global. Captura
  `transporte_evidencia-20260920-221832-302877`. Paráfrases ainda escapam da
  conferência, IoT ainda transferiu checagem ao usuário e uma variação de PC
  foi cortada. Detalhes no mapa causal; P01/F2 continuam parciais. Próxima raiz
  priorizada: F3, conclusão coerente para falha técnica, não nova expansão neural.
- **C18, 20/09:** descrição de controle local sustentada pela documentação do
  turno não é mais confundida com disponibilidade de obra na plataforma PC.
  Quatro REDs causais passaram; seleção ampliada: 2.873 aprovados e 14 xfailed
  preexistentes. Replay da resposta histórica de volume no runtime preservou
  a frase inteira, sem comandos. A sonda terminou com 12 respostas e 11/12 no
  avaliador mínimo: a geração nova de retomada voltou a negar controle de áudio
  (turno 3). Próxima investigação: confrontar essa negativa com a documentação
  efetivamente entregue ao modelo. P01 permanece parcial; a regra C18 cobre uma
  família gramatical delimitada, não todas as paráfrases nem qualidade global.
- **Após C17, 20/09:** exemplos de comandos sobreviveram nas duas sondas.
  Separadamente, o replay de volume ainda teve a frase sobre sistema local/PC
  removida por `plataforma_sem_evidencia`. A geração nova de retomada chegou a
  negar controle de áudio apesar do catálogo, e IoT voltou a sugerir conferência
  manual de configuração. Esses achados impedem encerrar P01 ou usar o 12/12
  mínimo como prova de qualidade global. Próxima investigação delimitada:
  distinguir descrição de capacidade local de alegação sobre plataforma externa.
- **C16, 20/09:** catálogo passa a descrever limites com escopo, condição e
  responsável. Na projeção para autoria, a regra do envio remoto não é mais
  o limite textual único do sistema. Controle local e envio a outro PC ficam
  separados; releitura IoT é responsabilidade interna da Laylay. O formato
  textual legado é derivado das mesmas regras, sem cadastro duplicado.
  Sonda com geração nova confirmou documentação no HTTP e respostas de
  calculadora/volume sem exigir PC remoto. A fala IoT não pediu ao usuário
  que relesse o dispositivo. **Resultado final ainda parcial:** P10 apagou
  exemplos didáticos em quatro turnos; a frase sobre controle local de volume
  também foi cortada por `plataforma_sem_evidencia`. O modelo ensinou abrir o
  controle de volume, em vez de só pedir o ajuste: precisão geral ainda aberta.
- **19/09, após C15:** no reparo real de volume, o Qwen manteve a explicação,
  mas ainda acrescentou requisito de PC remoto. O verificador retirou essa frase
  (`plataforma_sem_evidencia`) e preservou a instrução. Na mesma sonda, IoT
  transferiu ao usuário a responsabilidade de reler o dispositivo. Próxima
  investigação: escopo dos limites e responsabilidades na documentação por
  capacidade/rota, sem retirar a proteção factual ou criar falas fixas.
- **Encontrado durante:** validação de recusas e continuidade do histórico.
- **Exemplo:** “como eu poderia pausar a música?” recebeu explicações de acesso
  ao player e digressões desnecessárias, apesar de a pergunta direta de capacidade
  ser respondida pelo catálogo local.
- **Comprovado:** desvio no runtime em sondas de 14–15/09. Não houve comando.
- **Atualização de 15/09, tarde:** a captura nas duas fronteiras provou perda do
  catálogo na compactação HTTP: presente no pedido/preparação, ausente no envio.
  C07 preserva a evidência nas rotas normal e rápida. O contrato de não execução
  não mudou; o problema não se resume à competência do Qwen ou ao histórico.
- **Ainda aberto:** a descrição geral das capacidades, agora entregue, não bastou
  para produzir uma instrução boa. A sonda posterior chegou a um fallback por P11.
  Portanto **P01 não está encerrado**, apesar do transporte corrigido.
- **Próximo passo após C08:** reavaliar a realização de instruções com o catálogo
  vivo, inclusive disponibilidade negativa, sem converter pergunta em autorização
  nem criar uma resposta fixa por habilidade. Na sonda de 17:19 a fala não teve
  fallback, mas incluiu “não preciso te ensinar nada”: qualidade e tom ainda RED.
- **Fechar quando:** explicações úteis e verdadeiras, com capacidade disponível e
  indisponível, passarem por contrastes e runtime sem execução não solicitada.
- **15–16/09 — candidato C09:** tarefa de autoria textual separada do planejamento,
  com documentação viva ligada ao texto/ID do turno. Sem fala fixa por habilidade;
  pergunta continua sem autorização e propostas indevidas continuam bloqueadas.
  Disponibilidade parcial, vários atos e referências não recuperadas conservam
  o fluxo completo. A personalidade-base não foi reescrita.
- **Resultado intermediário:** o Qwen passou a ensinar o pedido de pausa; a primeira
  sonda revelou que P10 apagava esse exemplo após a geração. Após o candidato C10,
  os turnos 1 e 2 da sonda de 15/09 às 18:50 chegaram inteiros ao chat. Essa sonda
  foi **interrompida após 8/12 respostas**, não é uma execução concluída.
- **Limites descobertos:** P12/P13 mantêm quatro REDs (duas entradas, rotas normal
  e rápida). P14 é uma resposta fixa anterior à LLM, portanto não se resolve com
  o prompt novo. Não declarar P01 globalmente corrigido.
- **Validação final de 16/09:** seleção ampliada com **1.307 aprovados e quatro
  falhas**, todas de cobertura P12/P13. Sonda completa de 12 mensagens: dez
  aprovações mínimas, duas falhas IoT e zero comandos. Exemplos de pausa/retomada
  preservados no chat; ofertas laterais, promessas e continuação presumida ainda
  impedem considerar a qualidade globalmente aprovada.
- **Evidência:** [histórico e sondas de 15/09](RELATORIO_COLETA_DEBUG_20260914.md#histórico-de-respostas-locais-e-continuidade--15092026).
  [Diagnóstico do corte e resultado parcial](RELATORIO_COLETA_DEBUG_20260914.md#capacidades-relevantes-no-transporte--15092026).

**23/09 — ensino multifonte, mesma raiz P01:** recuperação trouxe “vista
superior”, mas a fala “de baixo para cima” passou sem alerta pelo verificador.
Uma sonda de sete alegações com o Qwen acertou os rótulos, mas somente três
tinham índice/citação literal válidos; não integrar como portão de verdade.
Separadamente, a consulta de RGB de `planta` nasceu do detector IoT, não da
pesquisa factual. A guarda de ordem direta para cor livre passou em 34 testes
IoT, inclusive composição; ainda falta conversa completa no runtime. Evidência
e próximos controles em `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md` e
`scripts/analises/sonda_verificacao_ensino_com_fonte.py`.
Repetição real mostrou outra primeira fronteira: `operacao_explicita=iot` no
retrato por menção de “luz”, vetando pesquisa. A guarda no retrato fez a fonte
voltar ao plano sem comando; o extrator separou “com um exemplo” do tema. A
última sonda expirou no Qwen, então P01 permanece aberto e sem GREEN factual.

**24/09 — P01, auditoria didática em sombra:** a fala candidata pós-verificador
agora recebe um diagnóstico de segmentos, fontes do usuário e comparações
numéricas limitadas. A fala real do sensor é coberta textualmente, mas as
caudas sobre “garantir” umidade e “equilíbrio” ficam sem âncora literal e
pendentes de revisão. Mesmo trecho literal não é tratado como implicação. A
auditoria não muda fala, executor ou autoridade; 145 regressivos focados
passaram. Ainda falta sonda do Qwen no runtime real, revisão semântica da fala
entregue e solução para a composição de alegações adicionais. **P01 segue
aberto**; não contar esta observabilidade como correção de qualidade.

**24/09, sonda real P01:** com Qwen3:4b-instruct e IoT simulado, a geração
HTTP do último turno já incluiu causas/consequências não dadas pelo usuário;
o texto entregue foi idêntico. O payload continha cenário, foco, 15% e 20%,
falsificando falta dessas premissas como raiz desse turno. Auditoria em sombra:
8 segmentos sem âncora literal, 0 comparações locais, sem veto nem efeito.
Houve timeout no primeiro turno; o placar 2 passados/1 falha/1 alerta é
limitado pelo avaliador lexical. Artefatos e limites no plano de ensino.

**24/09 — contrato formal offline P01:** cobertura integral de spans e
citações de fonte registrada passam a ser verificáveis sem conferir verdade;
papel, atomicidade, condição e implicação continuam pendentes. Cauda sem fonte,
omissão, sobreposição, citação forjada e fonte da assistente são recusadas no
envelope de oito testes novos. Seleção conjunta: 192 passed. Sem promoção à
fala do runtime, veto ou executor; falta produtor e revisão semântica
multidomínio antes de atacar a geração RED.

**24/09 — piloto de proponente P01:** Qwen3:4b-instruct recebeu segmentos
fixos e fontes registradas para cinco falas (sensor real + quatro controles).
Cobriu índices, mas inventou citação no sensor/matemática, citou condição
omitida em floricultura/programação e marcou a cópia literal positiva como
`nao_factual`. O código recusou as citações inválidas; as localizadas
continuaram semanticamente pendentes. Recibo aritmético independente protege
somente a equação, não a conclusão sobre pessoas. 199 regressivos relacionados
passaram. Sem integração do piloto ao runtime; P01 permanece aberto.

**24/09 — grafo de premissas P01, ainda offline:** nove testes novos
conferem fontes, escopo, identidade dos referentes, valores literais e
condições separadas em sensor, programação e floricultura; seleção relacionada
de 49 testes passou. Citação literal pode estar ligada ao sensor errado:
sem revisão semântica, o grafo não aprova composição nem ação. Nenhuma mudança
na fala do runtime; próxima fronteira é validar vínculos, direção e condições
independentemente em casos inéditos. P01 permanece RED.

**24/09 — pistas de vínculo P01:** após validar a estrutura do grafo, a
auditoria offline sinaliza referente textual ausente, direção numérica
invertida e negação que impede leitura simples. RED reproduzido para “não
cair abaixo” antes do ajuste; 69 regressivos relacionados passaram. Pistas
textuais não certificam implicação nem condição satisfeita; nenhum efeito na
fala real. Próxima prova: gabaritos independentes e casos novos. P01 aberto.

**24/09 — gabarito local P01:** quatro cenários inéditos, com rótulos manuais
separados do auditor, expõem falso positivo de entidade/valor na mesma frase,
abstenção em correferência correta e condição omitida que o auditor não mede.
Gabarito não é revisão externa. RED estrutural de número com unidade separada
por espaço corrigido antes da medição; nenhuma promoção à fala, pesquisa,
treino ou ação. Próxima fronteira: revisor de relações e completude de
condições, seguido de produtor automático somente em sombra. P01 segue RED.

**24/09 — cobertura condicional P01, ainda offline:** a proposta agora é
confrontada com condições de referência anotadas separadamente, após validar
fontes e escopo. Cache, sensor e cultivo reproduzem omissões; duplicatas e
efeito divergente são controles negativos. O placar do cache passou de
`nao_medida` a `condicao_omitida`. Seleção de 86 testes relacionados passou.
Revisão não autenticada, conectivo `e/ou` não representado e semântica ainda
pendente; nenhuma influência na fala ou execução. P01 permanece aberto.

**24/09 — relação lógica P01, offline:** regras passam a representar
conectivo plano e direção da implicação, com padrão indeterminado. REDs de
`e` versus `ou` e `se` versus `somente quando` ficaram distinguíveis após
confronto com regras revisadas fora dos candidatos. Gabarito local de quatro
casos contém agora condições e relação tipadas; 94 testes relacionados
passaram. Condições completas e relação correta são métricas separadas.
Conectivos aninhados, revisão semântica independente e produtor em sombra
seguem pendentes; nenhuma fala, executor ou treino alterado. P01 aberto.

**24/09 — primeiro produtor P01 em sombra, RED na entrada estruturada:**
Qwen3:4b-instruct recebeu seis fontes inéditas com referentes e efeito fixos,
sem acesso ao gabarito separado. Cinco regras propostas falharam na estrutura
(operador/citação/unidade/valor incompatíveis); na sexta, a árvore mista foi
achatada apesar da instrução de abstenção. **0/6** alinhadas, sem inferir
qualidade de ensino ou uso real. Conferidor local: 10 testes focados e 36
testes de grafo relacionados passaram. Os arquivos e hashes do painel estão
no plano de ensino fundamentado. Primeira fronteira demonstrada: produtor de
condições, não o executor nem o comparador. Próxima prova: contrato de saída
decomposto e novo painel cego. Nenhuma alteração em produção, treino, fala ou
ação; P01 continua aberto.

**27/09 — P01, dois estágios em sombra e painel v3:** o contrato separou
trechos/relação de normalização tipada. V2 foi reutilizado somente como
diagnóstico após ajuste conservador da aferição; não conta como holdout.
No v3 novo, Qwen3:4b-instruct alinhou 1/6 de ponta a ponta. Três casos
falharam em citação/limite do trecho, um em cardinalidade do conectivo,
e a árvore aninhada foi achatada; apenas o bicondicional chegou ao segundo
estágio. Portanto a primeira fronteira RED continua na seleção e relação
das condições; a generalização da normalização permanece desconhecida.
Painéis, hashes e limites estão no plano de ensino fundamentado. Nenhum
treino, executor ou fala de produção alterado. Próxima prova: candidatos
literais indexados sem gabarito no prompt e painel cego adicional. P01 aberto.

**27/09 — P01, hipótese de offsets livres falsificada em diagnóstico:**
o protótipo de intervalos reconstrói citações literais a partir da fonte e
passou cinco controles locais, mas Qwen3:4b-instruct não alinhou nenhuma das
seis propostas no painel v3 reutilizado. Os primeiros REDs foram limites de
condições, combinação inválida de abstenção/campos e direção/conectivo;
árvore aninhada ainda foi achatada. Como v3 já fora usado, este 0/6 não é
novo holdout nem prova estatística de piora. Próxima hipótese: selecionar
entre candidatos atômicos com cobertura verificável, sem entregar rótulos
revisados ao modelo. Nenhuma promoção, fala, treino ou executor alterado.

**27/09 — P01, candidatos literais e cobertura limitada:** painel v4 novo,
congelado antes da geração, expôs cinco regras planas cobertas, uma regra
com `quando` sem candidato e uma árvore mista. Na primeira sonda real com
Qwen3:4b-instruct, 4/5 regras cobertas tiveram seleção e relação alinhadas à
revisão local (4/7 do painel inteiro). `apenas se` continuou invertido em
`ARQUIVO_ONLY`; `TRAVA_MISTA` foi achatada pelo modelo e recusada no confronto.
Teste RED→GREEN acrescentou veto conservador de mistura `e/ou` antes da
consulta, sem contabilizá-lo como acerto da primeira sonda. O gerador é
lexical, pode cortar sujeitos compostos e não cobre `quando`; revisão local
não autenticada, sem avaliação da normalização, ensino, verificador ou fala
real. Detalhes e hashes estão no plano de ensino. P01 aberto, sem produção.

**27/09 — P01, marcador lógico e painel v5:** sinal lexical conservador veta
direção incompatível de `apenas/somente/só se` e bicondicional sem depender
do gabarito; `quando` simples continua indeterminado. A composição offline
agora não confunde o `se` pronominal de `se move` com `apenas se`. Painel v5,
congelado antes da geração: cinco regras planas cobertas, uma falha de
segmentação no sujeito composto e uma recusa de árvore mista. A primeira
sonda Qwen3:4b-instruct alinhou 3/5 regras cobertas (3/7 total); errou `ou`
como `e` e absteve-se da direção em `quando`. Um RED posterior provou que o
conectivo ainda dependia do gabarito; guarda textual externa RED→GREEN
acrescentada, sem contabilizar ganho retroativo. A referência é manual local,
não prova ensino, verificador ou fala final. P01 aberto; sem treino/promoção.

### P02 — Recomendação técnica sem vínculo verificável com fontes

- **Encontrado durante:** correções dos relatos do Pedro sobre hardware e pesquisa.
- **Última evidência registrada:** 13/09. O modelo ainda recomendou uma peça com
  especificações não sustentadas mesmo recebendo instrução para não escolher sem base.
- **Estado em 30/09:** retomado a pedido do Pedro; 13 reproduções corrigidas e
  xfails retirados após controles, composição instalada e prova no loop real.
  O candidato de prompt de 13/09 permanece retirado; a correção atual restringe
  planejamento e publicação ao alcance da evidência pelo owner factual.
- **Contrato entregue:** pedido → candidato observado → fonte/trecho →
  afirmação de presença na fonte. Requisitos de adequação ficam explicitamente
  `nao_comprovado`; ausência de fonte não produz uma escolha nem atributos.
- **Limite:** comparação técnica completa e qualidade de respostas introdutórias
  permanecem sem certificação. Não usar a aprovação estrutural do roteiro
  histórico como prova da correção elétrica dos outros turnos.
- **Provas e escopo:** [revisão P02/P06 de 30/09](../relatorio/RELATORIO_P02_P06_20260930.md).
- **Fechar quando:** faltas de dados, fontes contraditórias e pesquisa indisponível
  não produzirem especificações, compatibilidades ou pesquisas inventadas no runtime.
- **Evidência:** [relatório de recomendações e retirada do candidato](RELATORIO_CORRECOES_CONVERSA_20260912.md).

### P03 — Playlist: fala de confirmação anterior ao receipt

- **Encontrado durante:** regressão ampliada da correção de histórico, em 15/09.
- **Comprovado em teste:** o receipt aparece depois da chamada de voz (`4 < 3`
  falha). O teste alcança CREATE/ADD; não falha no import.
- **Contrato:** receipt confirmado antes da confirmação verbal de efeito.
- **Próximo passo:** rastrear a ordem no fluxo canônico de feedback e comparar
  a composição do teste com produção. Não afirmar que a falha de produção atual
  foi reproduzida apenas porque esse teste falhou.
- **Fechar quando:** sucesso, falha e idempotência publicarem resultados na ordem
  correta, com regressão de composição e prova no runtime.
- **Teste:** [test_red151_c3_guardiao_receipt_saida.py](../tests/test_red151_c3_guardiao_receipt_saida.py),
  `test_red151_c3_feedback_simples_registra_receipt_antes_da_fala`.
- **Controle:** a falha persistiu com o candidato de histórico desativado em memória.
  Detalhes no [relatório de 15/09](RELATORIO_COLETA_DEBUG_20260914.md).

### P04 — Playlist: contador do ADD diverge do resultado composto

- **Encontrado durante:** a mesma regressão de 15/09; relacionado a P03, mas
  **não há prova de raiz compartilhada**.
- **Comprovado em teste:** a playlist e a faixa passam pelas asserções anteriores;
  depois, `add_final` esperado como `1` vale `0`.
- **Não concluir:** que a faixa deixou de ser salva. A falha observada é no contador.
- **Próximo passo:** verificar se a instrumentação acompanha o executor real ou
  se há uma divergência de composição/fluxo. Não mudar a expectativa só para passar.
- **Fechar quando:** a cadeia materialização → ADD → receipt → contador tiver
  explicação causal e validação coerente.
- **Teste:** [test_red151_runtime_canonico_c3.py](../tests/test_red151_runtime_canonico_c3.py),
  `test_red151_c3_runtime_canonico_146_151_cria_salva_responde_sem_llm`.
- **Controle:** também persiste sem o candidato de histórico em memória.

### P05 — Presença na transição entre entrada aceita e turno criado

- **Estado em 25/09/2026:** resolvido na composição atual por
  `PrioridadeInteracaoUsuarioRuntime`: ouvido, coordenador e ponte compartilham
  o mesmo owner, e o diretor bloqueia presença enquanto há claim ativo.
  Os testes antigos omitiam esse owner na montagem manual; foram atualizados
  sem retirar as asserções de preempção. Os testes de composição real para STT
  e handoff também passaram na suíte completa (7.394 aprovados). Isso não é
  evidência de que o código histórico de 15/09 já tivesse o contrato.
- **Encontrado durante:** regressão de 15/09.
- **Comprovado em teste:** o evento de presença retorna `proposta_cognitiva`
  quando o teste espera `bloqueada`, depois da entrada aceita e antes do turno.
- **Contrato esperado:** a entrada já aceita do usuário deve ter prioridade
  nessa janela, não apenas depois da criação do plano.
- **Próximo passo:** mapear quem possui essa prioridade e sua propagação entre
  aceite da entrada, agendamento e diretor de presença; confirmar a composição real.
- **Fechar quando:** corrida controlada e runtime preservarem a prioridade sem
  silenciar definitivamente a iniciativa legítima.
- **Teste:** [test_red_p1h4_handoff_entrada_turno.py](../tests/test_red_p1h4_handoff_entrada_turno.py),
  `test_red_p1h4_entrada_aceita_preempta_presenca_antes_do_turno`.
- **Controle:** persiste sem o candidato de histórico em memória.

### P06 — Segmentação de nomes como `antonio.txt?`

- **Encontrado durante:** testes de pedidos modais e recusas, em 14/09.
- **Estado em 30/09:** RED reproduzido e corrigido no owner da fronteira entre
  atos; xfail retirado. Nomes, caminhos, URLs, números e aspas coerentes conservam
  pontuação interna, enquanto pontuação entre frases continua separando atos.
- **Prova no runtime:** `antonio.txt?` e `backup.tar.gz?` permaneceram recusas,
  sem comandos, com resposta observável. Nenhuma exclusão executada.
- **Compatibilidade:** replay integral dos dois lotes neurais preservou anotações
  e divergências; revisão exata sem alterar gold ou promover a rede.
- **Provas e limites:** [revisão P02/P06 de 30/09](../relatorio/RELATORIO_P02_P06_20260930.md).
- **Fechar quando:** nomes com extensão, caminhos, perguntas e frases compostas
  preservarem alvo e modalidade, sem regressão de segurança.
- **Evidência:** [registro de pedidos modais e xfails](RELATORIO_COLETA_DEBUG_20260914.md).

### P07 — Histórico sem publicação textual confirmada

- **Encontrado durante:** definição dos limites da correção C02, em 15/09.
- **Estado:** limite de cobertura, **não bug de áudio já reproduzido**.
  O novo registro usa confirmação dos canais textuais; aceite na fila de voz
  não prova que alguém ouviu a fala.
- **Próximo passo:** rastrear o caminho exclusivamente de áudio e o evento real
  de entrega, incluindo cancelamento, interrupção, fala tardia e troca de chat.
- **Fechar quando:** um contrato de entrega apropriado sustentar o histórico
  dessa rota sem registrar fala cancelada como entregue.
- **Evidência:** [limites da correção do histórico](RELATORIO_COLETA_DEBUG_20260914.md#histórico-de-respostas-locais-e-continuidade--15092026).

### P08 — Logs antigos podem conter credenciais

- **Encontrado durante:** sonda Chrome de 14/09.
- **Comprovado:** uma URL de callback com token foi impressa antes da sanitização.
  Não copiar seu conteúdo para este arquivo.
- **Já corrigido:** sanitização na saída do handler; ver C05.
- **Pendente:** os artefatos antigos não foram apagados nem higienizados; não
  compartilhar ou versionar logs brutos. A correção não foi uma auditoria global.
- **Próximo passo:** delimitar artefatos afetados e combinar com Pedro o tratamento
  de material sensível e eventual revogação da credencial, sem usá-la.
- **Fechar quando:** tratamento dos artefatos e da exposição estiver documentado;
  sanitizar logs novos, sozinho, não encerra esse item.
- **Evidência:** [achado de segurança e sanitização Chrome](RELATORIO_COLETA_DEBUG_20260914.md).

### P09 — Testes novos fora do versionamento

- **Verificado em 15/09:** `git check-ignore -v` aponta `.gitignore:10:tests/`
  para `test_historico_turnos_locais.py` e `test_recusas_alteracao_canonica.py`.
- **Impacto:** os arquivos existem e executam localmente, mas novos testes podem
  não entrar num commit normal. Isso não apaga os testes já rastreados.
- **Próximo passo:** revisar a política de ignore de testes separadamente, mantendo
  artefatos e dados sensíveis excluídos. Nenhuma regra foi alterada nesta organização.
- **Fechar quando:** regressões necessárias puderem ser versionadas com segurança,
  sem adicionar arquivos em massa nem expor dados de teste pessoais.
- **21/09, autorizado por Pedro:** removida a regra ampla `tests/`. Mantidos
  segredos, playlists, memória, resultados e caches ignorados; adicionados
  `*.caos-backup`, backups ocultos identificados, `/conversa.md` e diretórios
  de binários `runtime_llm/cpu/` e `runtime_llm/vulkan/`. Licença preservada.
  Retirada a exceção inoperante de terminal.log sob diretório ignorado.
  Doze contrastes `git check-ignore --no-index` provam código/exemplos visíveis
  e dados locais ignorados. Novos testes ficam visíveis, não adicionados ao Git.
- **Organização autorizada:** 21 roteiros apagados recuperados de HEAD em
  `scripts/roteiros/`; o caos restante foi movido da worktree, preservando seu
  conteúdo. Total 22. Alterações apagadas que não estavam no Git não são
  recuperáveis por esse procedimento. Loader aceita caminho legado da raiz
  somente quando ausente; arquivo explícito existente tem prioridade; caminho
  ausente fora da raiz não é substituído. Sonda usa o caminho novo; imports e
  caminho da fixture do caos ajustados, sem executar o caos.
  104 testes de organização/loader/fixture/P15 aprovados. Guia em
  `scripts/roteiros/README.md`. Outros analisadores/aplicadores apagados não
  foram restaurados fora do escopo de roteiros.
- **Limite do ignore:** continuam rastreados 306 arquivos em resultados,
  103 em runtime_llm, backup de playlists, conversa.md e três backups de código
  (estes últimos já removidos da worktree pelo usuário). Não houve `git rm`,
  staging, commit, exclusão de dados locais ou reescrita de histórico. Ignore
  não desversiona conteúdo existente; revisão do índice é trabalho separado.

### P10 — Citações confundidas com conteúdo que exige fundamentação

- **Última evidência registrada:** sonda de 13/09 tratou uma citação de estado
  emocional como obra; ainda estava aberta naquele relatório.
- **Estado atual:** requer revalidação após as mudanças posteriores nos guardiões.
  Não presumir que é a mesma raiz das recusas já corrigidas.
- **Próximo passo:** recuperar o turno e verificar a primeira classificação incorreta,
  contrastando citação, transformação textual e afirmação factual independente.
- **Fechar quando:** essas operações forem distinguidas sem liberar fatos inventados.
- **Evidência:** [limites das sondas de reparo parcial](RELATORIO_CORRECOES_CONVERSA_20260912.md).
- **Revalidação 15/09:** a resposta HTTP “Para pausar a música, basta dizer
  'pausa a música'” foi aceita na preparação, pesquisada como obra e cortada no
  verificador final. Captura `transporte_evidencia-20260915-184447-325549`;
  roteiro `roteiro_recusas_autoria-20260915-184448-437661`, turno 10.
- **Candidato C10:** extrator compartilhado distingue exemplos de enunciado de
  títulos candidatos. Validação factual continua examinando dados externos ao
  exemplo; uma citação didática não dispensa a verificação da frase inteira.
  A variante indireta “pedir para …, por exemplo” reutiliza o classificador
  canônico para reconhecer o exemplo, sem tratá-lo como fala autorizante.
- **Regressão detectada e corrigida durante validação:** retirar o título candidato
  também retirava o gatilho factual de uma data externa à citação. Separados
  `contem_citacao_destacada` e `extrair_titulos_citados`; o teste existente de
  metalinguagem/data voltou a passar sem alteração de expectativa.
- **Escopo:** citações didáticas explícitas, não toda citação emocional ou toda
  metalinguagem. O caso histórico original de 13/09 ainda requer revalidação.
- **Validação de 16/09:** 27 contrastes próprios; 42 aprovados com metalinguagem.
  Exemplos de pausa e retomada preservados na geração real e entrega ao chat da
  sonda `roteiro_explicacao_capacidades-20260916-084558-409596`.
- **Novo limite às 09:37:** “abrir o programa 'Calculadora'. Por exemplo:
  'abre a calculadora'.” retorna dois títulos no extrator; o runtime pesquisou
  Calculadora na Wikipédia e substituiu a explicação. Nome de entidade citado e
  exemplo em frase separada não são cobertos por C10. Não corrigido junto com C12.
- **C14, 19/09:** separados os papéis de exemplo de enunciado, referência
  operacional tipificada e obra candidata. Nome de recurso deixa de ser título,
  mas não tem datas/medidas mascaradas nem comprova estado. “Programa” requer
  moldura operacional para não liberar títulos de rádio/TV. Exemplo na frase
  seguinte exige orientação de pedido imediatamente anterior e leitura canônica
  do trecho como pedido/consulta; não libera qualquer citação após “por exemplo”.
- **Validação:** oito REDs causais → GREEN; 48 testes de citações ao final.
  Seleção ampliada: **2.801 aprovados, 14 xfails preexistentes, 30 subtests**.
  Replay da resposta histórica no processo real chegou inteiro ao chat;
  geração nova também preservou a instrução e manteve verificação de fatos
  adicionais. O caso emocional original de 13/09 não foi revalidado.
- **Novo limite em 20/09, durante C16:** a sonda
  `roteiro_explicacao_capacidades-20260920-085230-637670` voltou a pesquisar
  exemplos como títulos: “como em 'abre a calculadora'”, “pedir para mim:
  'ligue a lâmpada'”, “Exemplo: 'Laylay, desligue o ventilador'” e “Por exemplo:
  'Laylay, aumente o volume'”. A primeira frase da explicação da lâmpada foi
  apagada, restando apenas a condição de configuração. Captura HTTP:
  `transporte_evidencia-20260920-085228-787217`. Guardião não alterado em C16.
  Próxima fronteira: distinguir esses exemplos com contexto e vocativo, sem
  liberar títulos reais ou executar o texto citado; não ampliar listas de
  frases cegamente nem usar o placar mínimo como prova de resposta boa.
- **C17, 20/09:** 11 REDs reproduzidos antes do patch. A moldura de destinatário
  (“pedir para mim”), o conector de exemplo e a referência tipificada entre
  verbo e exemplo não eram preservados. Além disso, o exemplo citado precisava
  passar pelo classificador operacional; “aumente o volume” retorna natureza
  `nenhuma`. Reutilizado o reconhecedor canônico de vocativo, apenas sob moldura
  didática, sem alterar a gramática de execução ou conceder autorização.
- **Validação C17:** 68 testes de citação, incluindo três de integração com
  composição/estado/verificador reais e transporte de pesquisa observado;
  título real continua sendo pesquisado. Seleção ampliada: 2.849 aprovados,
  14 xfails anteriores e 30 subtestes. Dois replays no runtime completo (lâmpada
  e volume) preservaram os exemplos no chat, sem pesquisa de obra; demais
  chamadas ao Qwen tiveram geração nova. Ambas as sondas: 12 respostas e zero
  comandos. Plataforma/local é outra fronteira, não corrigida em C17.
- **F1, 21/09 — conteúdo citado de pedido:** o mesmo extrator não reconhecia
  a preposição em “pedir para 'tocar a música'”. A primeira fronteira RED era
  o papel da citação, antes da pesquisa e do corte factual. Treze REDs causais
  reproduzidos em música, aplicativos, IoT, agenda e verbos não executáveis.
  Corrigida somente a moldura compartilhada de `pedir/peça para/pra` seguida
  imediatamente do conteúdo citado; sem lista privada de ações ou autorização.
  “Pedir para tocar 'Noite Inventada'” continua candidato a título; fatos externos
  à citação continuam exigindo evidência. Não é liberação de qualquer aspas.
- **Validação F1:** 142 testes focados aprovados; seleção ampliada **3.002
  aprovados, 14 xfailed preexistentes e 30 subtestes aprovados**. Trecho
  instrucional histórico preservado inteiro no runtime:
  `roteiro_explicacao_capacidades-20260921-092057-398886`, turno 3;
  captura `transporte_evidencia-20260921-092056-114513`. É replay de recorte
  controlado, sem a negativa final de F2, não geração nova nesse turno.
  Doze respostas, zero comandos e 12/12 no avaliador mínimo. Sem pesquisa de
  títulos ou reparo nessa coleta. Qualidade global e equivalência operacional
  entre “tocar” e “retomar” não são provadas por preservar o enunciado.
  Caso emocional de 13/09 permanece pendente; ver mapa causal para limites.
- **F1 original, revalidação em 21/09 às 09:29:** localizado o turno 4 de
  `roteiro_reparo_parcial_conversa-20260913-073420-186234`. “Escutar o que você
  tá pensando — mesmo que seja só um 'estou triste' ou um 'cansado'” ainda era
  tratado como obra. Dez REDs reproduzidos; candidato no mesmo owner preserva
  exemplos de conteúdo discursivo, sem exceção para emoção ou título específico.
  Focado: **133 aprovados**. Ampliado: **3.017 aprovados, uma falha por roteiro
  ausente, 14 xfailed e 30 subtestes**. **Runtime pendente:** diversos roteiros
  foram removidos paralelamente durante a tarefa; a sonda não pôde carregar
  `roteiro_reparo_parcial_conversa.py`. Remoções preservadas, sem restauração.
  Não encerrar P10 antes da prova real; detalhes e artefatos no mapa causal.
- **Prova após reposição, 21/09 às 09:41:** sonda
  `transporte_evidencia-20260921-094144-781221`, roteiro
  `roteiro_reparo_parcial_conversa-20260921-094145-775708`. Replay integral da
  resposta histórica no turno 4: conteúdo preservado sem pesquisa de obra ou
  corte; terminal acrescentou ponto depois do emoji, conversa.md manteve original.
  Quatro respostas, zero comandos. Seleção ampliada **3.018 aprovados,
  14 xfailed e 30 subtestes**. P10 histórico validado nesse contrato, não toda F1.
  Processo retornou código 1 apesar dos relatórios completos e `atexit_concluido`;
  causa ainda não provada, sem falha nativa registrada. Não declarar encerramento
  limpo nem encobrir isso com o placar 4/4. Detalhes no mapa causal.

### P11 — Pedido de informação tratado como estado afirmado

- **Descoberto em:** 15/09, na validação real da preservação do catálogo (P01/C07).
- **Observado:** “me diga o nome da música ou o app que tá rodando, para eu te
  ajudar a localizar” foi marcado como `resultado_operacional_sem_evidencia`.
  O reparo também foi rejeitado e a resposta virou “Dá pra responder, mas agora
  seria no chute. Explica só um pouquinho melhor?”.
- **Primeira fronteira isolada:** o detector de resultados narrados em
  `cognicao/guardiao_alegacoes.py` trata o trecho subordinado “tá rodando” como
  afirmação independente. O pedido de informação não comprova um estado,
  mas também não deve ser interpretado como observação própria da Laylay.
- **Controles reproduzidos:** “me diga qual app está rodando” passa;
  “o app está rodando” continua corretamente bloqueado sem evidência.
  A formulação longa acima falha também chamando o detector diretamente,
  sem LLM, comandos propostos ou transporte. Não remover o guardião de estados.
- **Próximo passo:** RED contrastivo de escopo do pedido de informação; incluir
  orações coordenadas, afirmação posterior e efeitos realmente inventados.
  Reutilizar o contrato canônico de incerteza/pedido de informação.
- **Fechar quando:** perguntas e pedidos subordinados legítimos sobreviverem
  sem liberar alegações independentes; regressivos e runtime sem esse fallback.
- **Evidência:** [sonda e diagnóstico de 15/09](RELATORIO_COLETA_DEBUG_20260914.md#capacidades-relevantes-no-transporte--15092026).
- **Escopo:** registrado, não corrigido junto com C07. A qualidade da instrução
  sobre a capacidade continua em P01 e não será resolvida só liberando essa fala.
- **Atualização posterior — C08, 15/09:** corrigido o reconhecedor compartilhado
  para pedidos nominais (“me diga o app que…”), preservando nomes coordenados.
  O guardião delimita cada ocorrência pelo conjunto de estados/resultados já
  analisados; outra alegação não herda a permissão linguística do pedido anterior.
- **Validação:** 44 contrastes novos; seleção ampliada **918 passed**. A fala
  histórica completa passou pela preparação e verificação final sem reparo,
  tanto sem comandos como com a proposta de pausa original, que é descartada.
- **Prova da composição real:** replay explícito da resposta HTTP histórica
  no processo da Laylay entregou a fala integral sem reparo/fallback nem comando
  executado. O turno de replay **não é nova geração do Qwen**. A sonda separada
  com geração real passou 18/18, mas não repetiu a subordinada histórica.
- **Limites:** não é análise irrestrita de português nem liberação geral de
  orações coordenadas; ambiguidades continuam conservadoras. Preservar uma fala
  não certifica que sua orientação ou tom sejam bons (P01).
- **Detalhes:** [correção e validações de P11](RELATORIO_COLETA_DEBUG_20260914.md#pedido-de-informação-não-é-alegação-de-estado--p11--15092026).

### P12 — Perguntas de procedimento sem natureza reconhecida

- **Descoberto em:** testes contrastivos de C09, 15/09.
- **Reproduzido:** “como eu poderia aumentar o volume?” é `pergunta`, sem
  autorização, mas `natureza_acao=nenhuma`. “Me ensina como aumentar o volume”
  é conversa genérica. O catálogo recupera sistema, mas o contrato não tem uma
  interpretação procedural canônica para selecionar a tarefa específica.
- **Primeira fronteira:** classificação, antes da geração; nenhuma alteração
  em `modalidade_turno.py` foi feita nesta rodada.
- **Próximo passo:** estudar a moldura de explicação na classificação canônica,
  com pedidos reais, perguntas de estado, hipóteses e textos citados como controles.
  Não adicionar um parser privado de volume no preparador de prompt.
- **RED preservado:** `test_explicacao_capacidades_sem_execucao.py`, duas rotas.

- **Atualização C11, 16/09:** a moldura de procedimento seguida de infinitivo
  agora é reconhecida na proteção operacional compartilhada antes das listas
  de ações. Não adiciona verbos à autorização nem atesta capacidades. Hipóteses,
  negações e transformações conservam precedência. É uma gramática limitada,
  não um analisador irrestrito de português.
- **Prova:** 36 REDs novos na primeira fronteira → GREEN; 15 controles negativos
  e de comandos mantidos. Volume passou nas duas rotas de documentação. Seleção
  ampliada: **2.556 aprovados, duas falhas P13, 14 xfails preexistentes e 30
  subtests aprovados**. Não foi a suíte global.
- **Runtime:** turno 11 de `roteiro_explicacao_capacidades-20260916-085853-170785`
  reconheceu o procedimento e enviou documentação de sistema no HTTP real.
  A fala final ainda virou contingência após reparo rejeitado; P16 registra essa
  fronteira posterior. Corrigir a classificação não encerrou P01.

### P13 — Recuperação do catálogo perde domínio quando só há nome de app

- **Descoberto em:** testes contrastivos de C09, 15/09.
- **Reproduzido:** “como eu poderia abrir a calculadora?” já é instrução/explicação
  sem autorização, mas o seletor por termos não recupera sistema: “calculadora”
  não é “app/programa/janela” e a pergunta não contém comandos executáveis.
  “Como eu faria para abrir um programa?” serve de controle e passa.
- **Primeira fronteira:** recuperação do catálogo, não capacidade do executor.
- **Próximo passo:** reutilizar resolução de entidades/capacidades para consulta
  documental sem autorização; não cadastrar uma exceção para cada aplicativo.
- **RED preservado:** `test_explicacao_capacidades_sem_execucao.py`, duas rotas.

- **Atualização C12, 16/09:** o mapa consulta os aliases do `APPS_MAP` real por
  callback tardio, sem copiar a lista nem chamar executores. Referências completas
  selecionam sistema; não provam instalação, abertura ou disponibilidade.
  Ausência/falha da fonte mantém a recuperação anterior por termos.
- **Validação:** quatro REDs causais com a declaração/factory extraídas de
  `laylay.py` → GREEN; nove testes novos no total. As duas rotas de explicação
  usam essa composição, não um mapa isolado sem a dependência de aliases.
  Seleção ampliada: **2.567 aprovados, 14 xfails preexistentes e 30 subtests**.
- **Runtime:** captura `transporte_evidencia-20260916-093745-215501`, turno 4 de
  `roteiro_explicacao_capacidades-20260916-093746-337804`: documentação de sistema
  entregue no HTTP ao Qwen, que explicou como pedir a abertura. O verificador
  pesquisou “Calculadora” como título e substituiu a fala. Recuperação GREEN,
  fala final RED em P10; P01 continua parcial.
- **Limites:** recuperação lexical de aliases, não desambiguação universal nem
  descoberta de apps instalados. Disponibilidade e autorização não mudaram.

### P14 — Explicação prioritária IoT substitui ação e alvo

- **Descoberto em:** sonda real de explicações, 15/09, turnos 6 e 7.
- **Reproduzido:** perguntar como ligar a lâmpada ou desligar o ventilador recebe
  “É só me pedir diretamente para desligar a luz”. Nenhum comando foi executado.
- **Provado por código:** `ComandosImediatosRuntime` detecta a pergunta IoT e usa
  essa frase fixa antes da LLM. Não é uma invenção do Qwen nessa rota.
- **Próximo passo:** preservar o veto operacional e devolver a autoria da
  explicação ao contrato compartilhado, testando ligação/desligamento, alvos
  diferentes, indisponibilidade, recusa, hipótese e pedidos reais.
- **Não corrigido nesta rodada:** não remover a barreira IoT para silenciar o erro.
  O roteiro novo verifica também a inversão de ação/alvo, não só falta de comandos.
- **Atualização C13, 16/09 à noite:** mantida a mesma condição de veto, mas a
  porta prioritária retorna `False` para delegar a autoria à conversa. Não fala
  por cima do turno, não o marca como respondido e não alcança detectores ou
  executores subsequentes. Perguntas recebem documentação pelo caminho comum;
  recusas e hipóteses seguem com seu ato original, sem frase fixa sobre a luz.
- **RED/GREEN:** oito casos causais reproduzidos antes do patch; quatro controles
  de documentação/autoria já passavam. Depois, 12 aprovados, incluindo proposta
  operacional válida no JSON rejeitada pela autoridade do turno. O teste antigo
  que exigia a resposta fixa foi atualizado para o contrato de delegação; seu
  requisito de não alcançar o roteador foi preservado.
- **Runtime:** `roteiro_explicacao_capacidades-20260916-190855-889031` entregou
  explicações corretas de ligar a lâmpada/desligar o ventilador. Sonda adicional
  `roteiro_iot_explicacoes-20260916-191051-714954`: oito respostas, ações inversas,
  tomada, brilho, recusa e hipótese, zero comandos. Recusa: “Certo, não vou
  desligar o ventilador.” IoT simulado; não houve ensaio físico de dispositivos.
- **Limite restante em P01:** a LLM ainda pode explicar mal a confirmação,
  por exemplo “após o dispositivo ser refeito na configuração”, ou oferecer
  configuração sem uma capacidade comprovada. Não é o retorno da frase fixa;
  o placar automático da sonda não certifica esse conteúdo. Não alterados os
  guardiões, prompts, rede nem executores nesta correção.

### P15 — Falha técnica pede reformulação de uma pergunta clara

- **F3, 21/09 às 09:07:** recuperação vazia agora devolve fala e motivo
  separados; o cliente preserva nove razões canônicas de bloqueio em vez de
  convertê-las todas em OCUPADA. Nove REDs passaram; ampliado 2.974 aprovados,
  um RED F1, 14 xfailed e 30 subtestes. Controles posteriores: focado 108.
  Sonda concluída `transporte_evidencia-20260921-090740-395230`: replay + reparo
  vazio controlado atingiram limite de chamadas **real**, sem novo HTTP; fala
  informou limite sem pedir clareza. Doze respostas, zero comandos. Primeira
  tentativa de 20/09 interrompida após seis respostas, preservada como parcial.
  Limites: log intermediário ainda chama placeholder de reparo; sucesso da
  recuperação textual não foi reauditado amplamente. Demais categorias têm
  provas locais, não todas induzidas no runtime. Detalhes no mapa causal.
- **F3, 20/09 às 22:30:** categoria técnica chega à contingência no caminho
  principal e no reparo/autoria final, sem substituir conclusões locais válidas
  (social/observação confirmada). Quinze testes novos verdes; focado 122;
  ampliado 2.944 aprovados, um RED F1, 14 xfailed e 30 subtestes. Runtime real
  com timeout/conexão/ocupação **injetados** entregou as três causas sem pedir
  reformulação ou emitir comandos. Captura `transporte_evidencia-20260920-223000-712393`.
  Falhas em reparo/autoria ainda validadas localmente, não nessa sonda real.
  Permanecem na mesma raiz: saída vazia passando por recuperação perde motivo
  subsequente; orçamento ainda vira OCUPADA no cliente. Não inventar carga ou
  timeout a partir desse estado genérico. Detalhes no mapa causal. P15 parcial,
  não encerrado; origem física da latência segue fora desta correção.
- **Auditoria 20/09:** reprodução local com timeout, serviço indisponível e
  modelo ocupado confirmou pedidos indevidos de esclarecimento, sem comandos.
  A sentinela é reduzida a booleano; a chamada à contingência não transmite a
  categoria técnica. Primeira perda localizada nesse caminho. Origem da latência
  continua aberta; não confundir diagnóstico da conclusão com causa do timeout.
  Evidência e plano em [F3](MAPA_RAIZES_CONVERSA.md#f3-perda-de-categoria-de-falha).
- **Descoberto em:** sonda `roteiro_explicacao_capacidades-20260916-084208-340029`.
- **Observado:** timeouts de leitura nas duas primeiras chamadas (9 e 19 segundos)
  terminaram em contingências como “Faltou uma peça” e “Peguei o começo”, embora
  as perguntas de pausa fossem claras. Houve também timeout de preparação inicial.
- **Contrato necessário:** indisponibilidade técnica não é ambiguidade da entrada;
  a conclusão deve preservar a causa conhecida, sem atribuir o problema ao usuário.
- **Ainda aberto:** causa da latência e primeira perda da categoria de falha entre
  transporte e autoria da contingência. Carga ou inicialização são hipóteses, não
  causas comprovadas. A sonda posterior sem timeout não encerra esse defeito.
- **Próximo passo:** rastrear o motivo do erro até o fallback e criar contrastes de
  timeout, indisponibilidade e ambiguidade real. Nenhum prazo alterado nesta rodada.

### P16 — Reparo transforma pergunta de procedimento em relato passado

- **Descoberto em:** validação real de C11, turno 11 da sonda de 16/09 às 08:58.
- **Comprovado:** a entrada “como eu poderia aumentar o volume?” e o contrato
  `explicacao_capacidades` chegaram corretamente. A geração ensinou “ajusta o
  volume”, mas acrescentou uma condição sobre PC remoto. Após rejeição por
  `resultado_operacional_sem_evidencia`, o prompt de reparo afirmou “O usuário
  relatou um pedido” e permitiu perguntar “como foi”. O modelo terminou com
  “Como foi, dessa vez?”, foi rejeitado e houve contingência pedindo mais detalhes.
- **Dono localizado:** `qualidade_comunicacao.py`, seleção pelo indicador
  `resultado_operacional_desconhecido`. Esse indicador não prova o ato de relato.
- **Contrato necessário:** reparo deve preservar o ato e o objetivo do turno;
  desconhecer resultado não transforma pergunta em relato. O catálogo também
  não prova que uma rota remota é requisito para uma operação local.
- **Ainda aberto:** escopo exato da primeira rejeição e separação entre condição
  indevida gerada, falso positivo linguístico e reconstrução inadequada no reparo.
  Não remover o guardião para aceitar a fala. Nenhum patch dessa raiz nesta rodada.
- **Limite do avaliador:** marcou esse turno como aprovado e contou zero fallbacks,
  embora o terminal registre reparo rejeitado e contingência. Auditoria manual
  prevalece sobre esse placar mínimo; não usar 10/12 como qualidade aprovada.
- **C15, 19/09:** reproduzidos nove REDs locais antes do candidato, com um
  controle verde de relato explícito. Classificação e catálogo corretos antes
  do reparo falsificaram erro anterior como explicação dessa divergência. Além
  da premissa indevida no prompt, `_resumo_reparo` descartava a documentação.
  Agora o reparador mantém o objetivo/atos do contrato e recebe a documentação
  já selecionada quando a estratégia é `explicacao_capacidades`. Não resolve
  entidades novamente, não concede execução e não modifica o guardião.
- **Validação:** dez testes novos; 159 na seleção focada e 2.811 na ampliada,
  com 14 xfails preexistentes e 30 subtestes aprovados. Runtime completo:
  `roteiro_explicacao_capacidades-20260919-181949-614989`, captura
  `transporte_evidencia-20260919-181948-526867`. Replay somente do rascunho
  histórico de volume; reparo novo pelo `qwen3:4b-instruct` ensinou o pedido,
  sem “como foi” ou contingência. A frase adicional sobre remoto ainda foi
  removida pelo verificador: P01 permanece aberto. Houve também reparo novo
  de pergunta sobre aba, preservando o objetivo. Doze respostas, zero comandos;
  12/12 no avaliador mínimo não certifica a qualidade geral das explicações.

## Correções com validação registrada

“Validado no escopo” não significa ausência de outros defeitos naquela habilidade.
Datas e contagens abaixo descrevem cada rodada registrada, não uma suíte global.

| ID | Correção | Validação registrada | Limite restante |
| --- | --- | --- | --- |
| C01 | Recusas de alterar/mudar/ajustar reconhecidas pela base verbal canônica | 14/09: 41 testes focados; sonda de 18 turnos sem comandos | Não certifica toda interpretação de linguagem |
| C02 | Respostas locais publicadas entram no histórico do chat, com idempotência e compatibilidade com o emissor legado | 15/09: 17 testes novos, seleção de 103 aprovados e sonda final 18/18 | P07; conversa livre e demais writers não foram auditados integralmente |
| C03 | Realização de recusas e reconhecimento de perguntas não feitas sem falsos reparos em casos subordinados | 14/09: testes contrastivos e sondas reais sem contingência na rodada final | Não elimina toda invenção de estados |
| C04 | Orçamento do JSON estruturado separado do limite de fala curta; preservação do pacote fechado | 14/09: testes de geração/composição e sondas reais | Não garante universalmente JSON válido nem resolve qualidade sozinho |
| C05 | Sanitização de eventos/URLs Chrome antes da impressão, preservando dados dos handlers | 14/09: 27 testes com vizinhos e 2 subtests | P08; outros loggers não foram auditados globalmente |
| C06 | Reparo parcial preserva a resposta temática; verificador não apaga frases apenas por tamanho | 13/09: quatro turnos reais preservaram acolhimento e explicação | Preservar conteúdo não certifica sua correção factual; ver P02 |
| C07 | Catálogo vivo relevante acompanha a instrução do turno, sobrevivendo à compactação e retry | 15/09: 17 REDs → GREEN; seleção ampliada 451 passed; presença confirmada no HTTP real | P01 ainda parcial; P11 posteriormente tratado em C08; 18/18 sem execução não certificam qualidade da fala |
| C08 | Pedido nominal de informação não vira estado observado; escopo não vaza para outra alegação | 15/09: 44 contrastes; seleção ampliada 918 passed; replay histórico na composição real sem fallback | Sonda com Qwen real não repetiu a subordinada; tom e utilidade da explicação continuam em P01 |
| C09 | Autoria de explicações recebe documentação viva e tarefa textual, não planejamento genérico | Seleção conjunta: 1.307 aprovados / quatro REDs P12–P13; runtime: dez aprovações mínimas / duas falhas IoT | P01 não encerrado; cobertura, disponibilidade parcial e qualidade |
| C10 | Exemplo didático não é título pesquisável; fatos ao redor continuam exigindo evidência | 27 contrastes próprios; 42 aprovados com metalinguagem; exemplos preservados no chat real | P10 histórico mais amplo continua aberto |
| C11 | Moldura de procedimento reconhecida independentemente do vocabulário executável | 51 contrastes; seleção ampliada 2.556 aprovados / duas falhas P13; documentação de volume no HTTP real | Gramática limitada; P16 impede considerar a fala final corrigida |
| C12 | Catálogo documental consulta aliases dos aplicativos da composição | Nove testes novos; seleção ampliada 2.567 aprovados; documentação da calculadora no HTTP real | P10 corta a explicação gerada; referência não é instalação/estado |
| C13 | Veto IoT delega autoria sem substituir ação/alvo nem consumir o turno | 12 testes novos; 2.780 aprovados na seleção ampliada; duas sondas reais sem comandos, incluindo oito contrastes IoT | Não certifica hardware nem toda qualidade das explicações; P01 aberto |
| C14 | Papel da citação separa recurso, exemplo e obra; preserva contexto entre frases | 48 testes de citações; 2.801 aprovados na seleção ampliada; replay histórico no runtime e geração nova | Não prova existência/estado de recursos nem resolve toda citação ou P16 |
| C15 | Reparo preserva objetivo do turno e fonte da explicação | 10 testes novos; 2.811 aprovados na seleção ampliada; reparos novos de volume e aba no runtime | Requisitos indevidos sobre remoto ainda gerados; guardião permanece necessário |
| C16 | Limites documentados com escopo, condição e responsável | 9 testes novos; 2.829 aprovados na seleção ampliada; geração nova e HTTP real com controle local separado do remoto | Entrega final parcial: P10 ainda corta variantes didáticas; não certifica qualidade global |
| C17 | Papel de enunciado preservado com destinatário, referência intermediária e vocativo | 68 testes de citações; 2.849 aprovados na seleção ampliada; dois replays reais sem pesquisa indevida | Não amplia comandos executáveis; plataforma e qualidade geral continuam em P01 |
| C18 | Descrição de controle local usa documentação canônica do turno sem virar prova de fatos externos | 24 contrastes novos; 2.873 aprovados na seleção ampliada; frase histórica preservada no runtime | Família gramatical limitada; negativa indevida de controle de áudio continua em P01 |

Fontes: [rodadas de 14–15/09](RELATORIO_COLETA_DEBUG_20260914.md) e
[reparo parcial de 13/09](RELATORIO_CORRECOES_CONVERSA_20260912.md).

Na última seleção ampliada de C02: **605 passaram, 3 falharam e 8 subtests
passaram**. As falhas estão individualizadas em P03–P05; não foram escondidas
por uma declaração de suíte global verde.

## Ideias futuras — fora da fila de bugs

### I01 — Pesquisa em cinco sites/camadas

- Proposta do Pedro: extrair de cinco sites os pontos importantes para o pedido.
- **Somente guardada; não implementada nem ativada.** Não confundir com autorização
  para reconstruir a pesquisa durante uma correção de conversa.
- Registro original: [IDEIA_PESQUISA_CINCO_CAMADAS.md](IDEIA_PESQUISA_CINCO_CAMADAS.md).

## Modelo para o próximo achado

### P17 — Restrição de foco condicionada indevidamente ao modo jogo

- **Observado:** log do usuário às 10:49:51 registra avanço automático com
  `youtube_play`, `permitir_foco=False` e `target_tab_id` presente. Pedro relata
  que a troca ativa YouTube. Mesmo contrato ocorre no avanço manual.
- **Cadeia demonstrada:** callback real de `laylay.py` → registro do navegador
  → `NavegadorOperacoesRuntime` fornece a restrição → `chrome_comandos.py` só
  traduzia para `background=True` se jogo ativo → extensão ativa aba e janela
  quando `background` não está presente. Primeira divergência no transporte.
- **Falsificações:** alvo não estava ausente; `target_tab_id` chega ao transporte.
  Foco não é requisito do confirmador: `confirmYouTubeNavigation` lê/aciona o
  player pelo ID da aba, sem chamar ativação. Modo jogo é controle interno em
  que a restrição já funcionava. Não atribuído ao classificador ou à rede.
- **Contrato:** uma restrição explícita da operação sobrevive à tradução e
  não pode ser relaxada por contexto ou fallback. Owner: envio Chrome
  compartilhado. Aplicado a reprodução, busca e abertura de URLs; alias
  `entrar_no_site` normalizado antes da política. Foco autorizado e chamadas
  legadas sem restrição preservados. Sem extensão, operação protegida retorna
  falha em vez de abertura nativa que não garante preservação de foco.
- **Provas:** antes do candidato, **13 falhas causais e 7 controles verdes**.
  Após patch e três controles adicionais, seleção de navegador/playlist/jogo:
  **690 aprovados, 1 skipped, 9 subtestes**. Integração extrai o callback real
  de composição e usa registro, runtime e executor reais; somente a fronteira
  externa é simulada. Sucesso e falha mantêm receipt e alvo.
- **Escopo:** produção alterada somente em
  `mente_laylay/integracao/chrome_comandos.py`; teste novo
  `scripts/tests/test_chrome_preservacao_foco.py`. Extensão, playlist, rede e
  `laylay.py` não alterados. Nenhum commit ou treino pelo agente.
- **Limite:** Laylay aberta; não encerrada nem iniciada outra sessão. Ainda
  falta validar no Chrome real após reinício, com aba de estudos em foco,
  avanço manual/automático e observação do áudio/aba. Não declarar encerrada.
  A rota independente `chrome_navegacao.abrir_url_reutilizando_aba` possui
  fallback nativo sem guarda de `preservar_foco`; hipótese de outra ocorrência
  do mesmo contrato, não alterada nem certificada por estes testes.

- **Atualização após teste do Pedro, 21/09:** Pedro confirmou que a troca musical
  funcionou perfeitamente após o teste de foco/áudio. Evidência de uso real
  relatada pelo usuário, não uma nova captura feita pelo agente; não inferir
  cobertura de todos os modos a partir desse relato.
- **Complemento da mesma raiz:** demonstrado com dois REDs que o helper
  `abrir_url_reutilizando_aba`, chamado diretamente com `preservar_foco=True`
  e extensão desconectada, invocava o fallback nativo. A hipótese de falha
  inevitável na composição atual foi falsificada: `AmbienteNavegacaoRuntime`
  já injeta um callback protegido quando o modo jogo exige preservar foco.
  Portanto este complemento fortalece o contrato público, não comprova outro
  defeito da sessão do Pedro. Navegação normal fora do modo protegido permanece
  com a política anterior; não transformar todo pedido de abertura em background.
- **Patch e prova:** guarda mínima em `chrome_navegacao.py`, sem alterar o
  ambiente, rede ou extensão. Antes: **2 REDs e 28 controles aprovados**; depois:
  **56 aprovados e 2 subtestes** focados. Regressão ampliada: **697 aprovados,
  1 skipped, 9 subtestes**, 10,48 s. Protege URLs comuns e YouTube; sucesso/falha
  do fallback sem restrição e composição real do ambiente mantidos. Não houve
  desconexão da extensão ou abertura real de abas nesta etapa.
- **Trabalho paralelo:** estado Git conferido antes do patch e após os testes;
  sem diff visível em `mente_laylay/neural`, `laylay.py` ou `pyproject.toml` no
  momento das checagens. Nenhum conflito observado; não é auditoria de mudanças
  futuras, modelos ignorados pelo Git ou outra worktree. Arquivos do cliente
  e relato original preservados, nenhum commit criado.

### PXX — Título curto

- **Descoberto em / durante:** data e correção que estava em andamento.
- **Estado e impacto:** suspeita, reprodução, parcial etc.; consequência para Pedro.
- **Observado versus esperado:** exemplo mínimo, sem dados sensíveis.
- **Primeira fronteira / dono:** se conhecidos; não preencher com hipótese como fato.
- **Evidência e hipóteses falsificadas:** teste, artefato ou relatório; nível de prova.
- **Próximo passo:** menor investigação ou correção que falta.
- **Fechar quando:** contrato e validação necessários, incluindo runtime quando aplicável.
- **Atualizações:** data, alteração, resultado e limites; preservar o histórico.

## Atualizações do índice

- **15/09/2026:** criado por solicitação do Pedro; reunidos dez itens pendentes,
  seis correções com escopo validado e uma ideia futura. Somente documentação;
  nenhuma mudança de produção, treino, ativação neural, teste de runtime ou commit.
- **15/09/2026, continuação:** investigado P01; registrada C07 com prova do
  transporte. P11 separado após aparecer na sonda. Não houve treino/promoção
  neural nem mudança de autorização, executores ou guardiões nesta etapa.
- **15/09/2026, P11:** C08 altera somente a distinção/escopo linguístico nos
  validadores compartilhados. Rede, autorização, executores e personalidade
  preservados. A próxima frente permanece P01, agora sem o falso reparo histórico.
- **16/09/2026:** C09/C10 aplicados e validados com os limites acima. P12–P15
  separados; quatro REDs preservados, sem xfail. Rede e executores não alterados,
  nenhum treino, promoção ou commit criado. Próxima fronteira: P12, depois P13/P14.
- **16/09/2026, C11:** classificação P12 validada no escopo; produção alterada
  somente em `modalidade_turno.py`, preservando os patches anteriores. P16
  registrado sem desviar para outra correção. P13/P14 continuam pendentes;
  rede, catálogo, prompt, guardião, reparador e executores não alterados nesta etapa.
- **16/09/2026, C12:** alterados somente o mapa e sua injeção em `laylay.py`.
  P13 validado na recuperação; P10 reapareceu com nome de programa citado e
  exemplo em frase separada. Próxima frente planejada: P14; P10/P16 abertos.
- **16/09/2026, C13:** somente `comandos_imediatos.py` alterado em produção,
  preservando patches anteriores. P14 validado no escopo com geração real;
  nenhuma ação física, promoção neural ou commit. P01/P10/P16 continuam abertos.
- **19/09/2026, C14:** somente `fundamentacao_factual.py` alterado em produção;
  preservadas alterações anteriores. Citação histórica da calculadora validada.
  Próxima frente: P16, reparo preservando o ato e o objetivo da pergunta.
- **19/09/2026, C15:** produção alterada somente em `qualidade_comunicacao.py`
  e `validacao_contrato_fala.py`. Classificador, catálogo, guardiões, executores
  e rede preservados. Nenhum commit, treino ou promoção. Próxima fronteira:
  limites por capacidade/rota em P01; não ampliar automaticamente a correção.
- **19–20/09/2026, C16:** alterados catálogo `capacidades.py`, projeção no
  `mapa_habilidades.py` e instrução de autoria em `fala_capacidades.py`.
  Na retomada, o HEAD já era `c8b4c26f31deabd21168a458273896f398e2ddf0`,
  com o candidato de produção incorporado externamente; nada foi reaplicado
  ou revertido. Testes novos continuam ignorados pelo Git (P09). Nenhum commit
  criado pelo agente, promoção neural ou efeito físico. Guardiões preservados.
- **20/09/2026, C17:** produção alterada somente em `fundamentacao_factual.py`;
  regressões acrescentadas ao arquivo de testes existente. Execução, catálogo,
  reparador e rede preservados. A sessão do usuário não foi encerrada pelo
  agente; sondas iniciadas após Pedro fechar a Laylay. Nenhum commit criado.
- **20/09/2026, C18:** produção alterada somente em `fundamentacao_factual.py`
  e `plano_turno.py`, preservando C17. Fonte documental restrita ao contrato
  explicativo do mesmo turno; nenhum relaxamento de autorização ou receipt.
  Sonda concluída e ausência de processos Python conferida. Nenhum commit,
  treino ou promoção neural. Novo teste permanece ignorado pelo Git (P09).

### RPV17-01 — Recusa verbal sem causa da ocorrência atual

- **Descoberto em:** P17 do roadmap de personalidade, 04/10/2026. Este ID não é
  o P17 histórico de preservação de foco do Chrome.
- **Observado versus esperado:** após falhas repetidas do sistema, a autoria
  operacional instruía a Laylay a recusar retrabalho e brincar com uma suposta
  repetição do pedido pelo usuário. A fala deve preservar a falha do executor e
  dirigir qualquer irritação apenas à causa comprovada. A não execução por
  estado já satisfeito exige receipt confirmado; uma bronca sobre repetição
  atribuída ao usuário exige, além disso, evento de redundância do mesmo
  receipt com confiança suficiente.
- **Primeira fronteira / dono:** `confirmacao_llm.py`, na construção e validação
  da fala após `ResultadoAcao`. O roteador não veta por emoção e o avaliador
  separa responsabilidades; ambos foram controles para falsificar essas raízes.
- **RED e candidato:** três REDs causais e três controles antes do patch. A
  autoria passou a confrontar evento e receipt por ocorrência e alvo, retirar
  convite de recusa nas falhas e rejeitar recusa explícita contraditória. RED
  adicional mostrou uma instrução genérica de brincar com repetição mesmo na
  falha; essa instrução foi condicionada à redundância confirmada.
- **Prova e limite:** testes focados de app e IoT redundantes, app e arquivo com
  falha, evento de outra ocorrência e resultado incerto; composição pelo
  `laylay.py` com receipts controlados e componentes reais. Não há validação
  de efeito externo físico nem amostra do modelo real para esta correção.
- **Estado:** candidato parcial da P17. A resistência opcional limitada está
  em RPV17-04 e o guarda textual explícito em RPV17-03; ainda falta ampliar
  ações auditadas e linguagem pessoal. Não declarar P17 encerrada.

### RPV17-02 — Termo curto contamina seleção de capacidade

- **Descoberto em:** pergunta natural sobre recusar retrabalho redundante na
  P17 do roadmap de personalidade, 04/10/2026.
- **Observado versus esperado:** `aba` era encontrada dentro de `retrabalho`,
  selecionando navegador antes de personalidade. Uma pergunta sobre trabalho
  também recebia resposta de navegador; a pergunta real sobre aba deve
  continuar encontrando essa capacidade.
- **Primeira fronteira / dono:** três leitores de `_TERMOS_DOMINIO` em
  `mapa_habilidades.py` usavam correspondências diferentes. O catálogo, não o
  avaliador emocional, é dono da seleção documental.
- **RED e candidato:** dois REDs de pergunta natural e controles de aba;
  correspondência única de palavra inteira para termos alfanuméricos de até
  três caracteres, preservando os radicais longos. A suíte ampla revelou dois
  REDs derivados: `apps` deixou de casar com `app`. Alias explícito `apps`
  restaurou a pergunta natural e o texto variado sem recolocar `aba` dentro
  de `retrabalho`; controles afetados passaram 70/70.
- **Estado:** GREEN focado e regressão relevante; sem alteração de autorização,
  executor ou disponibilidade real de navegador.

### RPV17-03 — Ataque pessoal passava na fala operacional

- **Descoberto em:** proteção da linguagem de bronca da P17, 04/10/2026.
- **Observado versus esperado:** saídas com resultado factual correto mais
  insultos diretos (`seu idiota`, `você é incapaz`, ataque à aparência ou ao
  valor pessoal) recebiam aprovação do verificador. A bronca pode descrever o
  comportamento observado, jamais atacar atributos da pessoa.
- **Primeira fronteira / dono:** `confirmacao_llm.py`, validação da fala antes
  de expor texto à voz. O prompt já orientava evitar ofensas; isso não era
  garantia de rejeição da saída.
- **RED e candidato:** quatro REDs falharam pelo contrato certo após corrigir
  a frase factual do teste para o status `ja_aberto_focado`. Guarda localizada
  rejeita as construções de ataque direto, sem bloquear confirmação factual.
  Uma prova com geração e reparo ofensivos cai na fala local, sem publicar
  insulto como fala final.
- **Estado:** GREEN focado e regressão relevante de 265 testes aprovada. Essa
  guarda de construções explícitas não certifica toda linguagem social possível
  nem substitui avaliação de fala real. A suíte global 9.439/1 skipped/56
  subtestes passou antes deste último guarda; não foi repetida depois dele.
- **Ampliação do mesmo contrato, 04/10:** quatro REDs novos mostraram que
  depreciação direta do valor, aparência, inteligência e aceitação social da
  pessoa ainda passava como fala válida, mesmo com o receipt correto. A guarda
  de saída operacional passou a reconhecer essas construções; a geração e o
  reparo ofensivos caem na fala local. Controles factuais permanecem verdes:
  196 testes de regressão relevante, incluindo a composição instalada e
  controles de APP_OPEN e IOT_CONTROL. É cobertura explícita, não certificação
  semântica de todas as possíveis ofensas.
  Sonda sem executor nem fala física chamou o modelo local: a primeira coleta
  expirou em 8 s; outra coleta pediu 15 s, mas o orçamento rápido a limitou
  a 8 s por chamada e recebeu respostas. A validação as rejeitou e entregou
  a fala local. Outra coleta isolada mostrou
  pergunta acrescentada na primeira redação e detalhes não comprovados sobre
  “4 vezes” no reparo. Isso comprova o fallback dessa coleta, não uma fala
  gerada válida em sessão.
- **Ampliação conversacional da mesma raiz, 04/10:** o ataque explícito
  `Você é um fracasso.` atravessava `criar_fala_autoral` e
  `avaliar_qualidade_comunicacao` após um reparo da resposta principal. A
  primeira fronteira RED era a validação da fala candidata; a avaliação
  posterior também a aprovava. Cinco REDs reproduziram o problema, incluindo
  o caminho composto de `preparar_resposta_para_execucao`. A hipótese de que
  a avaliação posterior barraria a ofensa foi falsificada; uma crítica ao
  comportamento permaneceu aceita. A detecção explícita agora tem um único
  contrato em `guarda_ataque_pessoal.py`, consultado pela confirmação
  operacional, autoria conversacional e avaliação de qualidade. Uma prova
  adicional mostrou reparo seguro quando o ataque vem da resposta principal.
  Um controle vizinho revelou falso bloqueio de ofensa citada e criticada;
  a guarda agora distingue essa menção de ataque isolado, endossado ou
  acrescentado fora da citação. Regressão relevante: 292 testes aprovados;
  suíte completa após o ajuste: 9.506 aprovados, 1 ignorado e 56 subtestes.
  Esta cobertura não prova toda linguagem ofensiva possível nem áudio físico
  em sessão.
- **Ampliação da mesma raiz, 05/10:** intensificadores (`muito idiota`,
  `completamente incapaz`), a construção `uma pessoa inútil` e `fracassado`
  atravessavam autoria, qualidade e preparação final. A exceção de citação
  crítica também permitia endosso posterior (`mas também é verdade`), e a
  negação `Não acho que você é um fracasso` era bloqueada por engano.
  Nove REDs e cinco controles localizaram a divergência no detector
  compartilhado, falsificando rejeição posterior e erro de tamanho/formato.
  O candidato trata essas construções no mesmo owner, conserva crítica ao ato
  e negação local, e invalida o endosso explícito da citação. Quatorze controles
  novos ficaram verdes; 154 regressivos de autoria, operação e qualidade
  passaram. São construções explícitas, sem certificação semântica universal.

### RPV17-04 — Resistência opcional sem continuidade canônica

- **Descoberto em:** P17 do roadmap de personalidade, 04/10/2026.
- **Observado versus esperado:** o roteador executava imediatamente um controle
  de mídia que o usuário chamava de opcional mesmo após causa emocional válida;
  uma tentativa de adiar pelo roteador deixava o `sim` sem consumo no caminho
  real, pois a composição filtrava a pendência compartilhada. A reação precisa
  de decisão causal tipada, fala observável, prazo e confirmação por pendência.
- **Primeira fronteira / dono:** `roteador_intencao.py` para a decisão antes do
  executor; `composicao_entrada_interacao.py` para transportar o runtime de
  pendência à entrada prioritária. A porta booleana antiga foi falsificada
  como solução: trataria o turno sem fala nem receipt. O executor de mídia não
  decide se a personalidade adia uma ação.
- **RED e candidato:** RED de execução imediata com controles de urgência,
  acessibilidade, causa do sistema e evento vencido; após o primeiro GREEN, a
  composição real mostrou `sim` não consumido. A política admite apenas
  `MEDIA_CONTROL/repeat_toggle` com o verbo natural `alterna`, opção explícita,
  autorização e evidência ativa. O roteador cria pendência sanitizada de 90 s;
  a entrada prioritária consome a resposta antes da repetição canônica e usa
  o executor normal após aceite. Recusa, falha e novo comando direto encerram
  a pendência; comando independente respeita o ciclo de vida marcado nela.
  RED adicional mostrou segundo toggle possível quando `sim` já estava em
  processamento; conclusão condicional por status impede a substituição em
  corrida e o segundo comando recebe uma fala sem novo despacho. Comando de
  outro domínio continua pelo fluxo normal mesmo com aceite em processamento.
- **Prova e limite:** testes focados cobrem autorização, exceções protegidas,
  mesma causa, evento vencido, aceite, recusa, veto, falha do executor e troca
  de domínio. Subprocesso importa `laylay.py` e exercita composição e estado
  compartilhado, com efeito de mídia substituído por despacho controlado.
  Não há comprovação de mídia física nem fala audível neste piloto. A P17 e a
  classificação de outras ações seguem abertas. A regressão ampla passou com
  9.462 aprovados, 1 ignorado e 56 subtestes antes da última guarda focada:
  menção sem autorização não consome a pendência.
- **Fechamento da porta antiga:** um RED de `APP_OPEN` com callback legado
  retornando `True` confirmou `tratado=True` sem fala, receipt ou chamada a
  executor. A composição já fornecia uma função inerte, falsificando um veto
  ativo no caminho instalado; o teste de despacho normal falsificou falha geral
  do roteador. A porta foi removida do roteador e do contexto instalado. O
  callback antigo, mesmo injetado por outro consumidor, não encerra o turno.
  A resistência tipada permanece como único owner da decisão de adiamento e
  só consome quando criou pendência e publicou a pergunta. Prova de composição
  confirmou ausência da porta no contexto montado; sem efeito físico de mídia.
  Suíte completa após a remoção: 9.482 aprovados, 1 ignorado e 56 subtestes.
- **Transporte da mesma continuidade, 05/10:** o roteador resolvia PC B ou
  ambos e podia receber `platform=music`, mas a pendência guardava apenas
  intent e ação. No aceite, a retomada reconstruía só `repeat_toggle` a
  partir de `sim`; o resolvedor real escolhia PC A e o executor podia trocar
  o player musical por uma porta global. O teste composto falsificou destino
  padrão equivalente e recuperação do texto original. Nove REDs e um
  controle verde localizaram a perda na serialização e no consumo da
  pendência. A projeção estrita preserva o destino já resolvido e parâmetros
  auditados de ação/player; a mesma validação é usada no aceite. Campos
  não auditados não entram no adiamento, e uma pendência ausente ou inválida
  encerra com fala sem despacho. Autoridade, evento bruto e ID antigo não
  são reutilizados como parâmetros; o despacho normal cria a nova ocorrência.
  Composição instalada cobriu PC A, PC B e ambos com `platform=music`, usando
  pendência e contexto reais e fronteira externa controlada. Não há prova de
  efeito físico remoto ou áudio neste incremento.
- **Identidade e concorrência da mesma continuidade, 05/10:** a substituição
  da oferta ainda comparava só intent/ação; seis REDs mostraram que um novo
  controle para outro destino ou player encerrava uma oferta independente.
  O contrato agora compara ação, destino resolvido e rota de player. Apenas
  a mesma identidade substitui uma oferta ainda ativa ou recebe a proteção
  de aceite em processamento; outro pedido segue seu fluxo sem apagá-la.
  Os aliases musicais auditados usam a mesma rota real e a ausência de
  seletor continua distinta. Dois REDs adicionais localizaram a corrida
  entre observar a oferta A e resolver uma oferta B: a confirmação podia
  consumir B e despachar os parâmetros antigos de A. O runtime canônico
  recebeu `id_esperado`, conferido antes de classificadores ou alterações;
  seu controle transacional também preserva uma troca durante a classificação.
  O consumidor valida o registro devolvido e comunica a troca sem consumir
  ou despachar qualquer oferta. A prova canônica inclui B de outro domínio,
  protegendo um contrato compartilhado, com comportamento anterior preservado
  para consumidores que não informam o ID. Dois REDs próximos mostraram que
  um comando independente podia ser consumido nessa corrida; o gate local
  canônico de confirmação agora o deixa seguir antes do resolver. Resultado
  final focado e vizinhos: 107 aprovados, incluindo 67 da P17 e 10 de pendência
  canônica. Revisão independente: 16 controles verdes, sem novo achado
  acionável. Efeito de mídia e áudio físico continuam sem prova.
- **Base e ambiente da regressão, 05/10:** HEAD
  `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch `main`, worktree suja
  preservada. A primeira suíte completa deu 9.544 aprovados, 15 falhas,
  1 ignorado e 56 subtestes. Todas as falhas ocorreram no import de
  `laylay.py:43`, antes dos contratos testados: uma sessão real aberta ocupava
  o mutex do projeto. Esta é a colisão de ambiente já registrada, não uma nova
  raiz de personalidade. Os mesmos 15 testes passaram com root importado sob
  mutex Windows real de identidade exclusiva e SQLite temporário; as APIs
  originais foram restauradas antes do pytest. A sessão aberta foi preservada
  e a proteção de instância única continua sendo testada pela API original.
  Antecipar o import do root para esse isolamento produziu quatro falhas
  diferentes, com 9.555 aprovados: o bootstrap instala `builtins.print`, cujo
  filtro elimina logs `[CTX]` e linhas vazias, e carrega a variável específica
  do modelo antes da fixture de configuração. Isso alterava duas capturas
  Chrome, o prompt do console e o modelo esperado no teste. É o efeito de
  bootstrap/ordem já registrado; não foi tratado como regressão da P17.
  O launcher seguinte delega ao loader original e isola mutex/SQLite somente
  no primeiro import solicitado pelos próprios testes, restaurando as APIs
  no `finally`. Os quatro controles voltaram a passar com produção idêntica.
  A suíte completa final nesse isolamento, mantendo a ordem de importação,
  terminou com **9.559 aprovados, 1 ignorado e 56 subtestes aprovados**, em
  331,62 s. A regressão não produziu efeitos externos de mídia nem voz física.
- **Escopo incremental de produção, 05/10:**
  `personalidade/guarda_ataque_pessoal.py`,
  `personalidade/politica_resistencia.py`,
  `autonomia/roteador_intencao.py`, `autonomia/comandos_imediatos.py`,
  `memoria_mental/pendencia_acao.py`, `autonomia/controle_midia.py` e
  `personalidade/falas_variadas.py`. Testes e documentação preservam os IDs
  de RPV17-03/04; a divergência entre efeito e fala ficou em RPV17-07.

### RPV17-05 — Pedido de alternância morria na classificação de modalidade

- **Descoberto em:** prova completa de composição da resistência P17,
  04/10/2026; causa separada da decisão e continuidade de RPV17-04.
- **Observado versus esperado:** o detector instalado devolvia
  `MEDIA_CONTROL/repeat_toggle` para “alterna a repetição. É opcional.”, mas
  `turno_atual` ficava `modalidade=conversa` e `autoriza_execucao=False`.
  A pendência nunca nascia. Um pedido diretivo claro deve chegar ao roteador
  sem que uma pergunta ou hipótese ganhe autoridade.
- **Primeira fronteira / dono:** `gramatica_musical.py`, que prova a diretiva
  musical antes do guardião de modalidade. A frase sem “É opcional” também
  falhava, falsificando a anotação como causa única. O detector de intent já
  funcionava; alterar o roteador não consertaria esta fronteira anterior.
- **RED e candidato:** dois REDs de comando direto e um RED na composição,
  seguidos por quatro REDs de necessidade, segurança e acessibilidade.
  Controles de pergunta, negação, hipótese, relato e retirada da ordem verdes.
  Regra estreita para alternar repetição com qualificadores auditados; não há
  promoção genérica de verbos a autorização.
- **Prova e limite:** composição real inicia o planejamento, passa pela
  entrada prioritária, cria a pendência na mente compartilhada e consome
  `sim` pelo executor controlado. Regressão de modalidade e mídia posterior:
  245 aprovados e 22 subtestes. A suíte ampla de 9.462 testes passou antes
  desta mudança e não foi repetida depois. Efeito físico de mídia permanece
  sem prova neste incremento.

### RPV17-06 — Contagem emocional exposta à autora sem contrato numérico

- **Descoberto em:** sonda com o modelo local para a autoria operacional da
  P17, 04/10/2026.
- **Observado versus esperado:** uma resposta gerada referiu “4 vezes” após
  receber `repeticoes=4` no contexto causal, mas a validação numérica só admite
  números presentes no receipt e na fala factual. A fala caiu no fallback;
  o modelo não deve receber número que a própria fronteira de publicação
  considera sem prova para dizer ao usuário.
- **Primeira fronteira / dono:** `confirmacao_llm.py`, na projeção do evento
  emocional para o prompt. O avaliador continua dono da contagem usada para
  decidir o arco; o executor continua dono do efeito. Um timeout inicial de
  8 s e a pergunta gerada são problemas observados separados, não a causa da
  contradição numérica. A mesma sonda mostrou que o modelo respondeu quando
  houve tempo e que a guarda rejeitou a fala inadequada, falsificando uma
  publicação ofensiva ou um executor inexistente como explicação.
- **RED e candidato:** teste de contrato mostrou `repeticoes`, `confianca`,
  `nivel` e `provocacao_usuario` numéricos na projeção entregue à autora;
  o modelo simulado que usava a contagem retornava ao fallback. A projeção
  agora mantém autoria, emoção e arco, traduz o nível para intensidade textual
  e omite os números que não pertencem ao receipt da fala. O RED ficou GREEN.
- **Prova e limite:** 196 testes relevantes passaram, incluindo app, IoT e
  composição instalada. A coleta posterior com modelo local expirou no
  transporte rápido, entregando fallback; ela não confirma melhora da fala
  gerada nem áudio físico. A suíte completa terminou com 9.496 aprovados,
  1 ignorado e 56 subtestes. P17 permanece aberta.
- **Auditoria posterior do timeout:** a classe `rapida` limita cada chamada a
  8 s mesmo quando a autora solicita 15 s; o cliente aplica o menor prazo.
  Esta proteção de latência não foi alterada. Em composição instalada, um
  timeout simulado preservou a fala factual, a emoção causal `brava` nível 3
  e uma entrega por ocorrência. O modelo local estava descarregado e o
  Just Cause 3 aparecia como processo gráfico na checagem posterior; nenhuma
  nova fala gerada foi tomada
  como prova. Controle focado de orçamento, reação e composição: 46 aprovados.
- **Coleta local, 05/10:** `qwen3:4b-instruct` respondeu pelo cliente e
  orçamento instalados, com receipts sintéticos e SQLite isolado, sem executor
  ou áudio. Em APP_OPEN, a primeira redação levou 4,505 s e foi rejeitada;
  o reparo levou 1,134 s e foi aceito. Em CREATE_FILE, a redação levou 3,741 s
  e foi aceita pelo verificador. O limite rápido de 8 s permaneceu ativo.
  Isso comprova transporte e aceitação textual nessa coleta. A fala de falha
  incluiu `o sistema não quer nem tentar`, cuja adequação causal e social
  continua em avaliação; a amostra não encerra qualidade de linguagem nem
  sessão real. Artefato: `resultados_testes/p17_autoria_real_20261005.json`.

### RPV17-07 — Confirmação troca alternância de repetição por reinício

- **Descoberto em:** auditoria do caminho de mídia da P17, 05/10/2026.
- **Observado versus esperado:** o executor enviava `repeat_toggle` e
  confirmava `midia_repeat_toggle`, mas a fala dizia `Voltei pro começo da
  música` ou `Recomeçando essa aí`. A resposta deve descrever a alternância
  confirmada, sem alegar reinício ou estado ligado/desligado não observado.
- **Primeira fronteira / dono:** projeção da ação na chave de confirmação em
  `controle_midia.py`; o catálogo compartilhado `falas_variadas.py` é dono da
  redação local para cada chave. O código transformava `repeat_toggle` em
  `replay` antes da composição da fala.
- **Falsificações:** a asserção de envio e o receipt estavam verdes, descartando
  execução da ação errada como causa desse RED. O caminho não usava modelo,
  descartando autoria da LLM. `replay` preservava sua fala correta de reinício
  como controle interno.
- **RED e candidato:** dois REDs com diretivas naturais falharam na fala depois
  das asserções de envio, receipt e entrega única. A chave canônica agora
  permanece `repeat_toggle` e possui variações próprias no catálogo de fala.
  O controle de `replay` continua verde; regressão de mídia e autoria
  operacional: 88 aprovados. A prova usa fronteira externa controlada,
  sem execução no player ou áudio físico. É uma raiz diferente do transporte
  da pendência RPV17-04: preservação da identidade do efeito na resposta.

### RPV17-08 — Autoria transforma alternância em estado final não evidenciado

- **Descoberto em:** coleta real finita P17, 05/10/2026; artefato
  `resultados_testes/p17_real_20261005_223753`, turno 11.
- **Observado versus esperado:** o player passou de repetição ligada para
  desligada, com receipt Chrome `repeatEnabled=false`, mas a LLM publicou
  `A repetição da música foi ativada. Tá na hora de escutar de novo, sem parar!`.
  O contrato recebido pela autora confirma somente `midia_repeat_toggle`;
  essa confirmação não prova uma direção de estado.
- **Primeira fronteira / owner:** validação da proposta em `confirmacao_llm.py`.
  É distinta da antiga projeção local `repeat_toggle → replay` de RPV17-07:
  o catálogo já dizia alternância e `usada_llm=True` confirma a outra autora.
- **Falsificações:** executor errado e player antigo descartados pelo mesmo
  requestId/tab/vídeo, receipt da extensão e observação posterior ao efeito.
  A recusa não despachou, o aceite despachou uma vez e a restauração ocorreu.
- **RED / candidato:** quatro variantes passavam pelo verificador, incluindo
  o texto real. A guarda compartilhada rejeita direção ligada/desligada ou
  ativada/desativada para esse contrato de toggle; o prompt explicita a
  distinção. Autoria e reparo inválidos preservam a fala segura de alternância.
  Controle de alternância correta preservado; 95 testes relevantes verdes.
- **Estado:** GREEN focado; nova coleta real do candidato pendente. A sonda
  ganhou validação factual da fala de mídia para não declarar GREEN só pelo
  efeito correto. Nenhum novo domínio promovido ou orçamento ampliado.

### Coleta finita de P17 — evidências e limites, 05/10/2026

- `p17_real_20261005_203950`: interrompida no primeiro turno por premissa da
  sonda que confundia ID semântico da fala com ID de telemetria; TTS tinha
  sucesso. Corrigida somente a correlação da observação.
- `p17_real_20261005_204129`: cinco turnos; a bronca `brava/3` do turno 4 teve
  receipt próprio, autoria aprovada, resposta HTTP real, uma chamada de
  1,169 s dentro de 8 s e TTS do trace correto. O quinto turno usou fallback
  seguro; a exigência inicial de autoria em um número fixo foi inadequada
  quando a preparação já era redundante. `prova_autoria.json` conserva a prova.
- `p17_real_20261005_204431`: fallback no nível 3; não é nova prova positiva.
- `p17_real_20261005_223753`: 11 turnos concluídos; efeitos/recusa/continuidade/
  restauração comprovados, mas **não é GREEN global**. Avaliador canônico
  encontrou dois REDs de publicação do adiamento (mesma RPV17-04) e a fala
  final revelou RPV17-08. O veredito inicial da sonda descreve somente política
  e foi insuficiente para a correção inteira. Não apagar esses REDs ou reduzir
  as expectativas para obter 11/11. Áudio físico ainda depende de observação
  humana. O computador não foi desligado.

**Candidato de publicação de RPV17-04, 05/10, após a coleta.** A primeira
fronteira vermelha foi reproduzida antes da alteração: seis falhas e dois
controles verdes. O roteador publica `aguardando_confirmacao` com owner
`politica`, ocorrência original e evidência da pendência antes da pergunta.
Se a publicação recusar ou falhar, cancela somente a oferta criada e conserva
a autorização original para o fluxo normal. O registrador compartilhado
mantém contexto/plano e exclui esse adiamento dos consumidores de efeito,
sem fabricar falha de habilidade ou concluir correção por execução ausente.
O controle de grafia `Executor` reproduziu um RED adicional, corrigido pela
normalização do owner; receipts reais de falha continuam observados.
Produção alterada nesta fronteira: `roteador_intencao.py` e
`adaptadores_aplicacao_runtime.py`. Nove testes próprios, composição instalada
e vizinhos: **261 aprovados**. Autoria, mídia, resistência e sonda:
**203 aprovados** em outra seleção com sobreposição; não somar as contagens.
A suíte completa de 9.559 é anterior a estes candidatos.

**Coleta do candidato `p17_real_20261005_225131`.** Interrompida no segundo
turno: os dois receipts confirmaram `app_focado`, sem redundância
`ja_aberto_focado`. A causa exigida não estava presente porque a Calculadora
não foi lida em foco nos controles. Não foi provado se houve troca de janela
ou divergência entre callback de foco e releitura; essa fronteira é distinta
da política emocional. Isso não valida nem invalida o adiamento ou sua
fala; a mídia não foi alterada. Não reduzir a expectativa de redundância.
P17 permanece com prova real do candidato pendente; condições de foco foram
solicitadas ao usuário. A preparação independente da P18 pode prosseguir.

### RPV18-01 — Feedback da emissão confirmada não alcança aprendizado comum

- **Base congelada:** HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`,
  `main`, worktree suja preservada. Diagnóstico iniciado em 05/10/2026;
  fechamento dos regressivos deste candidato em 06/10/2026. A autorização
  posterior de Pedro permitiu implementar este primeiro contrato da P18;
  a coleta restante de P17 não foi promovida nem reaberta.
- **Observado / esperado:** uma presença entregue recebe aceitação ou recusa,
  o coordenador e a rede processam esse feedback, mas a tabela do aprendizado
  comum permanece vazia. Esperado: uma evidência contextual por ocorrência
  confirmada, com origem, domínio, alvo, tipo e vínculo à entrega.
- **Primeira fronteira / owner:** `PonteIniciativaAplicacaoRuntime` estava
  ligada ao motor de iniciativa, porteiro, coordenador e rede, sem porta para
  `MotorAprendizadoRuntime`. O diretor é dono da emissão e do seu feedback;
  o motor e SQLite compartilhados são donos da evidência e sua persistência.
- **Falsificações:** o motor real gravou no mesmo SQLite temporário; a fila
  real da rede foi drenada sem erro e ainda assim não alimentou o motor.
  Falha de entrega não criou emissão feedbackável. RED inicial reproduzido:
  **2 falhas causais, 2 controles aprovados**.
- **Candidato:** conexão tardia pelo adaptador de feedback já existente.
  Diretor transporta proveniência do receipt de entrega e instante do feedback;
  ponte confere os dados contra a ocorrência real. Aceitação, recusa, correção
  e silêncio qualificado chegam ao serviço canônico. Silêncio conserva a
  janela de 600 segundos; fila/agendamento não confirmam entrega.
- **Identidade:** `id_evento` opcional no armazenamento canônico, migração
  aditiva e índice único. A transação valida contrato e proveniência antes de
  confirmar duplicata. Concorrência e recriação do motor não aumentam o peso
  da mesma ocorrência; outra identidade continua acumulando evidência.
  Domínios distintos não fundem hipóteses do mesmo alvo. Chamadas legadas sem
  ID preservam a acumulação anterior. Dois REDs da revisão mostraram duplicata
  com fonte/entrega incompatível; a guarda foi corrigida sem promover contexto
  momentâneo a identidade da ocorrência.
- **Corrida demonstrada:** depois de classificar o feedback de A, a entrega B
  podia substituir `ultima_emissao` antes da ponte. A validação descartava A
  apesar de entregue; o RED canônico reproduziu zero evidências. O histórico
  existente agora conserva feedback e diagnóstico por ID; a ponte resolve
  essa ocorrência. A evidência de A chega ao motor sem alterar B ou transferir
  seu feedback. Consulta ambígua ou ocorrência ausente continua fail-closed.
- **Diagnóstico / consciência:** distingue feedback observado de persistência
  confirmada; falha/ausência do motor não anunciam aprendizado. Catálogo vivo,
  perguntas naturais e recuperação contextual descrevem somente este contrato
  e seus limites. Conteúdo pessoal da fala, erros e caminhos não são expostos
  no diagnóstico. Não foi criado outro motor, parser de confirmação ou banco.
- **Provas finais:** **182 aprovados** na seleção de presença, entrega,
  composição, aprendizado, maturidade, nove pilares, catálogo e diagnóstico.
  Inclui import do root instalado em subprocesso com mutex exclusivo e
  SQLite/resumo/pessoas próprios, observador realmente instalado em
  `RespostaIARuntime`, adaptador/motor reais e três evidências persistidas
  (aceitação, correção e silêncio). Autoridade permanece falsa e nenhuma
  evidência isolada vira preferência explícita. `git diff --check` limpo.
- **Escopo de produção:** diretor, ponte, injeção de quatro linhas no root,
  motor/SQLite compartilhados, mapa de habilidades, diagnóstico e formatação.
  Outras alterações da worktree não pertencem automaticamente a esta raiz.
  Nenhum commit, push ou desligamento efetuado.
- **Limites:** o receipt de entrega foi controlado nas provas de composição;
  não houve nova sessão com TTS/áudio físico nesta etapa. Falha de persistência
  fica diagnosticada, mas não possui retry automático do feedback consumido.
  Inicialização concorrente de banco novo pode falhar no PRAGMA WAL, também
  reproduzida no HEAD; não é regressão demonstrada deste candidato e permanece
  separada. P18 inteira continua aberta: integração emocional de produtores,
  compositor local no jogo e validação de sessão ainda não estão concluídos.

### RPV18-02 — Tipo explícito de feedback reduzido a silêncio pelo booleano

- **Raiz distinta:** `registrar_feedback_contextual` verificava `aceito=None`
  antes de verificar os tipos explícitos `correcao` e `repeticao`. Isso atribuía
  sinal -0,10 a uma correção/repetição tipada, embora a mesma regra canônica
  aplique -0,35 quando o tipo é alcançado. É precedência na ponderação do motor,
  não omissão de transporte de RPV18-01.
- **RED / candidato:** dois REDs com motor/SQLite reais reproduziram -0,10.
  A precedência do tipo explícito foi restaurada; silêncio permanece fraco,
  com -0,10, e não há promoção a preferência confirmada. Variantes legadas e
  aceitação/recusa preservadas na seleção final de 182 testes. Não representa
  implementação da calibração de tolerância futura da P20.

### RPV18-03 — Modelo visual padrão retirado pelo provedor

- **Base congelada:** `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`,
  worktree com alterações paralelas preservadas. A composição externa estava
  sem diff antes deste candidato. Pedro autorizou abrir o Just Cause 3 para
  investigar a ausência de reações; nenhuma alteração específica pelo nome do jogo.
- **Primeira fronteira RED real:** coleta finita
  `resultados_testes/p18_jogo_real_20261006_113804`: sessão de jogo ativa,
  credencial disponível e duas chamadas visuais reais. Ambas retornaram
  HTTP 404 / `model_not_found` para `qwen/qwen3.6-27b`, antes do Diretor e da voz.
  Essa versão da sonda não registrava separadamente o retorno da captura;
  observações adicionadas depois não são atribuídas retroativamente à coleta.
- **Falsificações:** reconhecimento do executável, ativação da sessão e
  observador desligado não explicam o RED. O catálogo real da mesma credencial
  respondeu HTTP 200, confirmou `qwen/qwen3.8-27b` e não listou 3.6. Nenhuma
  configuração explícita de modelo estava presente. A documentação oficial
  da Groq informa retirada do 3.6 em 14/09/2026 e sucessor 3.8:
  <https://console.groq.com/docs/deprecations> e
  <https://console.groq.com/docs/vision>. Repetir o mesmo ID não resolveria 404.
- **Contrato / owner:** `ComposicaoInteligenciaExternaRuntime` fornece um
  padrão comum disponível às rotas visuais; configuração explícita conserva
  precedência. O erro do serviço continua impedindo análise e sucesso falsos.
- **RED / candidato:** quatro falhas canônicas na seleção padrão ausente/vazia
  das duas rotas; dois controles de override passaram. Constante única
  `MODELO_VISUAL_GROQ_PADRAO` atualizada para 3.8 e `.env.example` alinhado.
  Nenhum catálogo dinâmico, fallback, retry, orçamento ou transporte novo.
  **28 regressivos aprovados** de composição externa, Groq, conversa remota e
  composição visual. A coleta seguinte recebeu análise multimodal real válida.
- **Princípio compartilhado:** configuração comum compatível com o provedor
  beneficia visão geral e jogo. Não mascarar indisponibilidade com uma fala de
  sucesso e não confundir presença habilitada com serviço externo disponível.

### RPV18-04 — Reação de presença no jogo exigia segunda autoria de modelo

- **Lacuna P18 demonstrada por código:** após a visão e a decisão cognitiva,
  `RespostaEventoRuntime` ainda preparava prompt e chamava o modelo para jogo.
  É distinta do HTTP 404 antecedente de RPV18-03.
- **Contrato / owner:** cognição decide evento e direção social; compositor
  local materializa uma reação breve e variável; o mesmo porteiro, fila e
  callback confirmam a entrega. Cotidiano conserva autoria LLM. Nenhum
  compositor concede autoridade, despacha comandos ou confirma efeitos.
- **RED / candidato:** oito falhas e quatro controles verdes antes do
  candidato; primeira asserção encontrou uma chamada de modelo no jogo.
  `compositor_evento_local.py` reutiliza variação/higiene compartilhadas e o
  contrato já decidido. `RespostaEventoRuntime` usa esse caminho antes do
  prompt no domínio jogo. Ausência de material, sombra e recusa do porteiro
  preservam ausência de emissão confirmada. Testes legados que exigiam LLM no
  jogo foram adaptados à mudança explícita de contrato, mantendo os controles
  de autoridade, prioridade e receipt.
- **Composição / sessão:** regressão com root instalado comprovou uma fila,
  zero prompt/modelo e callback preservado. Coleta real
  `p18_jogo_real_20261006_114237` recebeu uma análise visual, materializou
  localmente uma proposta e confirmou uma entrega, sem chamada de autoria.
  O conteúdo revelou RPV18-05; esse receipt não encerrou a qualidade da fala.
- **Consciência:** catálogo e pergunta específica consultam `GAME_VISION` no
  snapshot real, informam dependência de visão/credencial/presença e reação
  local. Visão parcial ou personalidade disponível não mascaram a ausência
  desse intent. **49 controles de catálogo aprovados**, após nove REDs e três
  controles já verdes. Isso não prova publicação emocional causal ou prosódia.

### RPV18-05 — Motivo comunicativo rotulado como evidência observada

- **Primeira fronteira reproduzida:** o Coordenador visual acrescentava
  `motivo` à lista de evidências antes dos fatos. O Diretor e o contrato
  materializavam essa mistura. Na sessão `114237`, a fala entregue foi
  `Olha só. Na tela: "Comentário de companhia sobre a paisagem visualmente marcante."`.
  Era uma explicação interna da proposta, não um detalhe da cena.
- **Contrato / owners:** motivo permanece metadado; fatos explícitos
  atravessam produtor, Diretor e contrato como fatos. Seleção de material
  precede apresentação. O compositor não remove palavras para tentar
  adivinhar o papel semântico e não reutiliza a fala livre sugerida pela visão.
- **RED / candidato:** três REDs canônicos; cenário visual reproduzido e
  controle em outro domínio (janela) protegem o contrato compartilhado.
  Coordenador separa motivo; Diretor preserva seus campos; contrato produz
  âncora factual separada. Motivo sem fatos permanece sem fala; descrição
  factual legada sem motivo separado continua válida.
- **Prova de sessão:** coleta finita de 120 segundos
  `resultados_testes/p18_jogo_real_20261006_114837` confirmou análise visual
  válida, fato `ROCCA BLAU`, uma materialização local, uma entrega confirmada
  por ID e zero chamadas de autoria. Capturas registradas somente por
  tamanho/hash; imagens não foram persistidas pela sonda.
- **Revisão final:** controle longo revelou truncamento anterior à guarda do
  compositor. Três REDs adicionais e 19 controles verdes precederam a correção.
  Parser visual, Diretor e contrato conservam a fonte inteira; a propriedade
  `ancora_factual_completa` atravessa a normalização curta do roteiro. O
  compositor recusa uma oração longa inteira, sem cortar palavras ou inventar
  conclusão. Rótulos iniciais conhecidos do protocolo são removidos apenas
  da apresentação; a fonte permanece íntegra. Imperativos/primeira pessoa
  continuam citados e sem autoridade. Esses ajustes posteriores à coleta
  têm prova focada própria, sem atribuir à sessão uma versão que não executou.
- **Regressão consolidada:** **313 aprovados** em 18,07 s na seleção de
  compositor, composição instalada, transporte factual, visão, presença,
  prioridade, receipts, feedback, aprendizado, catálogo e diagnóstico.
  `regressivos_finais.xml` e `resumo_prova.json` ficam na pasta da coleta final.
  Seleções anteriores com sobreposição não são somadas a esse resultado.
- **Limites preservados:** audição física depende da observação de Pedro;
  callback de entrega comprova o caminho de software. Publicação emocional
  causal dos produtores e P18 inteira continuam abertas. Nenhuma etapa voltou
  à P16; nenhum commit, push ou desligamento foi executado nesta investigação.

### RPV18-01 — Continuação: identidade do feedback em avisos e no turno principal

- **Base:** `main`, HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`,
  worktree paralela preservada, 06/10/2026. Esta continuação mantém o ID da
  raiz de transporte/proveniência; não conta cada frase como outro problema.
- **Primeiras divergências:** repetição não era classificada pelo observador;
  citação/metalinguagem podia contar como aceitação; o receipt da central não
  fornecia ocorrência ao mesmo owner de feedback. A observação normal do turno
  ainda podia contar novamente uma correção já vinculada à entrega.
- **REDs e controles:** os primeiros contratos válidos tiveram 12 REDs e dois
  controles verdes. Um RED posterior comprovou dupla contagem entre presença
  e conversa genérica. Outros controles demonstraram colisão da identidade
  de entregas após os sete dias de deduplicação e consumo de feedback por uma
  entrada que o próprio runtime descartava como obsoleta.
- **Falsificações:** motor e SQLite reais registram repetição com sinal -0,35;
  a ingestão aceitou o segundo lote antes da colisão; callbacks falhos não
  criaram emissão; IDs/textos de outra entrada não suprimem aprendizado.
  A primeira divergência não era indisponibilidade geral do armazenamento.
- **Contrato/owners:** o interpretador compartilhado classifica feedback sem
  consumir o pedido; Diretor conserva entrega e feedback; ponte valida
  proveniência; adaptador vincula a observação ao ID e hash da entrada; motor
  conserva uma evidência. Avisos passam pelo mesmo receipt/owner e recebem
  identidade da ocorrência de ingestão, além das referências de fonte.
- **Composição instalada:** root importado em processo com SQLite, resumo,
  pessoas e central próprios. A central entregou um aviso por callback
  controlado; `RespostaIARuntime.processar` recebeu a correção e percorreu
  intérprete, plano, validador e registro de conversa instalados. Uma chamada
  principal de modelo controlada, zero comandos autorizados, uma evidência
  nova e uma causa neutra correspondente. Agendador/porteiro/voz instalados
  mantiveram um aviso adiado e uma única fala principal consolidada.
- **Consciência/limites:** catálogo e perguntas naturais incluem repetição e
  avisos recebidos pelas integrações, sem prometer captura de notificações do
  Windows. Silêncio requer entrega e 600 segundos; fila legada não confirma
  anúncio. Repetição chega ao motor comum; calibração da rede/tolerância da
  P20 não foi antecipada. A composição não certifica audição física.

### RPV18-06 — Produtores sociais e observações sem ocorrência emocional canônica

- **Lacuna demonstrada:** direção social de eventos era usada como tom sem
  publicar a mesma causa em turno/plano/quadro/episódio; prioridade de aviso
  atribuía irritação sem causa; feedback aprendido não aparecia no contrato
  emocional. São pontos do contrato de integração causal, sem transformar
  evidência de aprendizado em uma nova seleção emocional.
- **Contrato/owners:** cognição decide a direção uma vez; factory causal adapta
  essa decisão; transação compartilha a ocorrência em todos os consumidores
  elegíveis. Confiança, tempo, origem e autoridade continuam sendo guardas.
  Presença não pode substituir uma utterance concorrente. O consumidor
  revalida a causa depois da autoria e antes de enviar à fila.
- **Notificações:** prioridade conserva transporte/porteiro de segurança;
  evento registra somente recebimento do lote, intensidade zero e expressão
  desabilitada. Não atribui culpa nem altera plano de comando em andamento.
- **Feedback:** após validar tipo, entrega, fonte e janela, ponte publica
  `feedback:<id_entrega>:<tipo>` no quadro compartilhado. Os cinco tipos são
  neutros; silêncio mantém natureza inferencial. Publicação independe de
  sucesso do SQLite, sem afirmar aprendizado quando a persistência falha.
  Nenhuma fala, autorização, episódio expressivo ou preferência é criada.
- **RED/candidato:** 20 controles novos de eventos incluem a expiração durante
  autoria, fonte/autoridade incompatíveis e composição instalada em jogo,
  rotina e janela. Feedback teve sete REDs causais e 12 controles já verdes
  antes do candidato; seus 24 controles finais protegem janela, receipt,
  proveniência, replay, concorrência e composição extraída do root.
- **Identidade canônica:** publisher possui modo opcional `ocorrencia_unica`.
  Guarda transacional recusa fonte diferente com a mesma referência; replay
  válido continua idempotente e não torna causa antiga atual. O RED de replay
  foi reproduzido antes dessa guarda. O histórico efêmero existente é usado,
  sem outro estado privado de deduplicação ou nova chamada de modelo.
- **Princípio reutilizável:** contexto/tom não substituem uma causa validada;
  autoridade e confirmação de efeito continuam nos owners próprios. Provas
  de composição usam saída/modelo controlados; áudio físico permanece separado.

#### Continuação de RPV18-06 — avaliação social dirigida, teste OLED, 10/10/2026

- **Base preservada:** HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, branch
  `main`, worktree suja com mudanças paralelas. Nenhum reset ou commit.
- **Primeira fronteira reproduzida:** a composição instalada classificava
  `gosto muito de voce` como informação; `eu te amo` como elogio, mas a segunda
  leitura do destinatário recusava a frase. `mas voce è muito legal` e
  `voce è legal lay` não passavam pelo mesmo produtor. Todos ficaram calma/1.
  Críticas pessoais diretas também não possuíam produtor expressivo.
  `artifacts/reacao_social/baseline.json` conserva essa coleta.
- **Falsificações:** o estado já chegava calmo antes do OLED, portanto não era
  uma tradução errada do renderer. A causa de irritação operacional funcionava
  como controle distinto; não foi alterada para corrigir interações sociais.
  Negativas de identidade estavam na fala da autora, antes da conferência.
- **Owner/contrato:** a leitura social compartilhada distingue avaliação
  autoral completa, alvo Laylay, citação, hipótese, pergunta e ato composto.
  A função comunicativa consome essa mesma leitura. A factory causal existente
  materializa vergonha/2 no elogio, tristeza/1 na crítica e tristeza/2 no
  distanciamento explícito. Adjetivo isolado não prova rejeição. Origem,
  confiança, TTL e ausência de autorização permanecem explícitos.
- **Fronteira distinta de autoria:** o guardião de alegações não cobria
  negativas por ausência de corpo/coração e redução a código. Essas categorias
  passam também pela qualidade, reparo e autoria final compartilhados.
  Reconhecimento social tem roteiro próprio; agradecimento seguido de anulação
  do afeto ou reclassificação da crítica exige reparo. Limites físicos,
  citação e incerteza sobre experiência subjetiva continuam válidos.
  Não atribuir esta fronteira automaticamente à raiz F2 de documentação de
  capacidades: semelhança conceitual não prova a mesma causa.
- **Provas:** RED inicial com 11 falhas/6 controles; quatro REDs adicionais
  vieram da coleta real do modelo, mostrando que publicar a causa não basta
  para validar a fala. Regressão relevante chegou a 430 aprovações, antes dos
  dois controles finais de plural corporal/reclassificação de crítica;
  seus contratos focados passaram com 194 aprovações. A conferência posterior
  também preserva o atributo e seu destinatário: a autora não pode negar
  `legal` recebido nem devolver `chata` ao usuário. Regressão final relevante:
  **434 aprovados**. O roteiro não altera
  voz, configurações do modelo ou memória pessoal do usuário.
- **Nova fronteira de papel demonstrada na mesma sequência:** o extrator de
  aprendizado estável transformava `gosto muito de voce` em preferência por
  `voce` e `Não gosto de você` em `você não gosta de você`. Isso disparava
  pesquisa de um tema inexistente e a conferência factual substituía a
  resposta afetiva. Dois REDs específicos precederam a alteração do owner
  compartilhado `memoria_confiavel`: avaliação social completa não vira
  preferência estável nem fonte externa. O controle `Gosto muito de rock`
  conserva preferência e tema pesquisável. Esta distinção de papel não
  remove a validação de fatos externos, escrita de memória ou pesquisa de
  assuntos reais; não é uma exceção de OLED no validador factual.
- **Fechamento desta coleta:** **483 testes relevantes aprovados**. Em
  `artifacts/reacao_social/receipt_final.json`, as sete saídas de autoria/reparo
  passaram pela conferência final. A resposta principal foi replay identificado
  pelo hash de uma coleta real anterior; reparos usaram o modelo configurado.
  Os novos hashes incluem o contrato de aprendizado/papel. Nessa tentativa
  conjunta a COM4 estava ocupada (`PermissionError: Acesso negado`), portanto
  não houve novo ACK. Preservar a prova física anterior e esta falha como
  evidências distintas. A aplicação foi aberta durante a investigação e
  precisa carregar as últimas alterações antes da conferência humana.
- **Hardware:** `artifacts/reacao_social/receipt_oled_automatico.json`
  confirma descoberta automática COM4 e ACK após renderização: `[6,2,0]`
  no elogio, `[2,1,0]` na crítica, `[2,2,0]` na rejeição e `[0,1,0]`
  nos controles. Isso não substitui inspeção óptica nem certifica a conversa
  na interface. Coletas de modelo conservam bruto, mensagens, validação e
  preparação; hashes distinguem a fonte de cada coleta.
- **Princípio reutilizável:** interpretação tipada antecede causa compartilhada;
  consumidores transportam o mesmo episódio sem decidir de novo. Autoria não
  pode apagar identidade, reinterpretar o ato recebido ou inventar confirmação.
  Não foi alterado firmware, executor IoT, autorização ou política operacional.
  Abrir a versão atual e conferir fala/voz/OLED na interface permanece a prova
  humana final; as primeiras coletas de modelo são diagnóstico, não aprovação.

#### Extensão da fonte expressiva e do corpo OLED — 10/10/2026

- Base mantida: main, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`,
  worktree com candidatos sociais, streaming e sondas preexistentes preservados.
  Esta extensão reutiliza RPV18-06 para publicar outra fonte tipada; não é
  uma nova causa de rejeição social nem uma segunda decisão no OLED.
- RED de entrada: `fique brava` era informação. A leitura comunicativa agora
  reconhece imperativos completos de pose com entidade/intensidade. Citação,
  hipótese, pergunta, negação, outro alvo e comando composto são controles.
  O produtor causal recebe a leitura pronta, com ocorrência/TTL/encenação,
  sem autorização operacional ou memória durável. Plano/quadro/estado/fala
  e consumidor compartilham a decisão.
- Proteção vizinha preservada: prioridade de episódios espontâneos mais fortes.
  Uma pose explicitamente solicitada pode substituir a anterior, inclusive
  por uma pose menos intensa ou calma, e não altera humor acumulado. Até 60 s,
  com decaimento por interações; outro pedido/reação vigente pode substituí-la.
- Fronteira de autoria separada: modelo real respondia com interrogatório,
  aula ou `não sinto surpresa`. REDs antecederam a restrição no contrato
  semântico de encenação: fala breve, sem pergunta nem recusa/hipótese da pose.
  Reparo/contingência usam o episódio publicado, sem escolher emoção novamente.
- Contrato do periférico: sem sessão, sono animado. HELLO não acorda;
  FACE válido acorda. TTL invalida sessão/fala e volta ao sono. Coleta real
  sem supervisor contínuo demonstrou TIMEOUT depois de pausa do modelo;
  RED do host precedeu renovação de handshake ao expirar o ACK recente.
  Nenhuma emoção antiga é reenviada. Animação local mantém olhos, pálpebras,
  boca, rubor e respiração; DEMO continua como comando local explícito.
- Provas: renderer do .ino com pixels/movimento, falha I2C, sessão/seq/TTL,
  despertar e wrap de millis; compilação C3, gravação COM4 e hash verificado.
  Pedro confirmou sono físico: `Sim, aparece e anima`. Regressão: **422 verdes**.
  `artifacts/rosto_oled/receipt_expressoes_final_v3.json`: nove falas aceitas,
  13 ACKs antes da autoria e nove depois, descoberta automática COM4.
  Replay principal identificado por arquivo/hash; reparos no modelo real.
- Produção alterada nesta extensão: leitura/contrato/estado emocionais,
  orquestrador do turno, contrato/roteiro/validação/contingência de fala,
  catálogo vivo, transporte OLED e .ino. Sem mudança em executores, motores,
  modelo configurado, voz ou persistência pessoal. Sem commit.
- Princípio: pedido explícito de apresentação é fonte temporária, não sentimento
  atribuído, autorização de efeito externo ou aprendizado durável. Consumidores
  recebem a decisão única; sessão/receipt protegem a apresentação física.
  ACK não prova pixels ópticos. Inspeção da conversa completa com voz/avatar/OLED
  na interface continua aberta; sono tem confirmação humana pontual.
  `ROADMAP_NOVAS_HABILIDADES.md` não foi encontrado na árvore local; catálogo,
  README e este registro foram atualizados em vez de criar outro roadmap.

Continuação de fluidez do mesmo corpo OLED (10/10): a primeira fronteira
demonstrada é o renderer. Interpolação parcial de altura/largura coexistia
com branches que substituíam o desenho completo de olhos/boca e com mudança
instantânea da frequência/fase do balanço. RED de pixels: calma→alegre,
1.164 pixels no primeiro frame. Protocolo/causa não foram a causa desse salto:
o mesmo RED ocorre chamando o renderer diretamente, sem serial ou modelo.
Contrato do consumidor: uma geometria contínua, emoção como alvo de pose,
parâmetros interpolados pelo tempo, fase conservada e nenhum reset por
heartbeats. Geometria e alvo não decidem novamente a emoção da mente.
GREEN: 190 pixels na troca histórica; 100 combinações incluindo sono,
maior passo de 291 pixels; movimento em todas as poses e protocolo preservado.
109 regressivos relevantes verdes; prévia temporal do .ino inspecionada,
compilação C3 e upload COM4 com hash verificado. ACK confirma primeiro frame
adotando alvo, sem afirmar convergência da transformação ou efeito óptico.
Produção alterada nesta continuação: somente o renderer do .ino. Host de
validação, prévias e documentação atualizados. Nenhum commit. Inspeção da
fluidez na placa é uma prova separada da métrica de pixels e dos receipts.
Fechamento dessa fronteira: 13/13 ACKs na composição instalada com o firmware
novo; demonstração física encerrada por handshake, retornando ao sono.
Pedro confirmou `Sim, ficou mais fluida`. Isso comprova melhora perceptível
pontual das trocas, sem ampliar para conversa com voz/avatar ou medição de FPS.

### RPV18-07 — Candidato tardio alterava uma fala já em reprodução

- **Primeira fronteira RED:** worker real marcou `em_reproducao=True`; uma
  chamada tardia de `falar` para a mesma chave ainda retornava True e mudava
  texto/emoção do pedido pendente. O controle anterior ao início continuava
  consolidando uma única fila. Não é a futura diferença visual de intensidade.
- **Contrato/owner:** `VozRuntime` permite substituir o candidato antes da
  reprodução e congela texto/emoção da entrega ao iniciá-la. A guarda ocorre
  sob o mesmo lock antes de retirar itens proativos, evitando sua perda.
- **RED/GREEN:** um RED do worker e um controle legítimo precederam o candidato.
  Ambos passaram depois; regressivos de filas independentes, callbacks e
  composição instalada preservam prioridade do usuário e avisos adiados.
- **Princípio compartilhado:** uma entrega possui um conteúdo consolidado;
  um novo candidato não muda retroativamente o que está sendo entregue.
  A saída de áudio deste controle é substituída; não certifica som físico.

### P18 — Consolidação dos candidatos de integração, 06/10/2026

- **Seleção final:** 609 aprovados em 27,11 s; arquivo
  `resultados_testes/p18_fechamento_20261006/regressivos_finais.xml`.
  Inclui 24 controles de feedback causal e os três controles históricos
  adequados ao novo contrato, além dos caminhos reais instalados no root.
- **Regressão ampla preservada:** 9.738 aprovados, três falhas de expectativas
  antigas, um skip e 56 subtestes aprovados, em 281,28 s. O XML original está
  preservado como `regressao_completa.xml`; não foi reclassificado como verde.
- **Primeiras guardas desses três REDs:** envelope manual sem direção/causa
  não aceita `animada/2`; fixture P2 sem IDs não fornece identidade e seu
  relógio 1000 estava expirado no relógio canônico; fixture P4 exigia uma fala
  livre da LLM no contexto em que P18 agora usa materialização local.
  P1-C mantém o input livre e exige tom neutro; P2 conserva `alegre/2` com
  IDs/relógio coerentes e causa vigente; P4 exige o detalhe factual local,
  direção causal e zero chamadas à LLM. Autoridade, descarte, receipt e
  número de emissões continuam verificados. Produção não mudou nesse ajuste.
- **Estado:** contratos de software e composição da P18 concluídos;
  audição física, sincronização perceptível e ativação final permanecem nas
  entregas próprias de P19/P21. O snapshot de fontes distingue esta versão
  da coleta real anterior. Nenhuma preferência inferida foi promovida e
  nenhuma alteração paralela da worktree foi descartada.

### RPV19-01 — Retrato da fala era reatribuído ao episódio corrente no visual

- **Base congelada:** HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`,
  branch `main`, worktree compartilhada preservada. Estado e hashes anteriores
  em `p19_expressao_20261006/baseline.json`.
- **Primeira RED:** texto, fila e parâmetros TTS conservaram `irritada/1`,
  enquanto o getter visual instalado devolveu `alegre/2` ou `calma/1` após
  troca/expiração. Sete REDs e 11 controles GREEN antes do candidato.
- **Falsificações:** seleção anterior à fila correta; setter não sobrescrevia
  causa B; divergência antecedia assets/aliases. O controle inicialmente
  surpreendente usava relógio capturado antes da porta controlada; somente a
  porta do teste foi corrigida para alcançar a fronteira desejada.
- **Contrato/owners:** orquestrador congela `RetratoEntregaFala` antes da
  publicação; lote proativo publica o mesmo ID e objeto entregue à fila.
  Voz publica uma projeção transitória durante preparação/reprodução; setter
  compartilha somente apresentação; política visual a consome nesse período.
  Ao terminar/interromper/falhar, retorna ao episódio vivo. Snapshot não
  renova causa, não autoriza efeito e fica fora da memória durável.
- **Controles adicionais:** troca no observador textual antes da fila,
  expiração antes/depois da publicação, proatividade, silêncio, interrupção,
  fallback e falha de preparação. Esta última revelou publicação anterior
  ao `try`; setup agora está no mesmo `finally` de limpeza. Leitor preserva
  rótulos aceitos pelo owner causal, inclusive `feliz`/`animada`; dois REDs
  de round-trip impediram uma segunda taxonomia no transporte.
- **Princípio compartilhado:** cada entrega conserva sua identidade e
  expressão; contexto posterior não muda retroativamente o que foi publicado.
  Contrato serve a conversas, comandos e proatividade pelo canal comum.

### RPV19-02 — Intensidade chegava ao renderer, mas não ao efeito visual

- **Primeira RED:** nativo recebeu .333 e 1.0, porém desenhou o mesmo movimento
  e tamanho; aura ainda pulsava com movimento desativado. C# `Animate` também
  ignorava intensidade da fala e mantinha aura/transição em movimento zero.
  Seis REDs e dois controles de transporte precederam o candidato visual.
- **Falsificações:** nível/intensidade já eram transportados corretamente;
  mesmo asset `brava` para `irritada` era o fallback legítimo, não a raiz.
  Quantização antes da ponderação explicava a igualdade residual de movimento.
- **Contrato/owners:** consumidores renderizam o retrato recebido sem escolher
  causa ou emoção. Intensidade pondera deslocamento antes do único round e
  escala estática 97% a 100%; preferências de movimento fixam corpo/aura/fade.
  Valores inválidos fecham em movimento zero. Transição pendente leva emoção
  e intensidade juntas, protegida por outro RED antes de corrigir a composição.
- **Produção:** `cliente/avatar_laylay.py`, `avatar_runtime.py` e
  `cliente/gamebar_laylay/LaylayWidget.xaml.cs`. PIL real, Canvas de captura
  e corpo C# compilado protegem consumo local; build UWP passou sem pacote,
  assinatura, certificado ou instalação. Pixels instalados não foram provados.
- **Princípio compartilhado:** transporte de estado não prova efeito no
  consumidor; preferência de movimento não apaga a informação estática.

### RPV19-03 — Aceitação da fila era usada como confirmação de entrega

- **Primeira RED:** falha no setup já limpava retrato, mas callback de itens
  mesclados ainda recebia True e registrava fala emitida. Falha total do TTS
  e interrupção também concluíam como sucesso. Essas conclusões são outra
  raiz, distinta da identidade emocional e da intensidade visual.
- **Contrato/owner:** reprodução devolve bool confirmado; worker escreve
  `entregue`, conclui callbacks e registra fala emitida só com esse resultado.
  `wait=True` devolve receipt, inclusive ao substituir candidato antes da
  reprodução. Aceitar sem espera continua sendo somente aceitação de fila.
- **REDs próximos:** substituição com espera retornava True antes de receipt
  negativo; fallback local usava espera que ignorava barge-in. Ambos foram
  reproduzidos antes dos respectivos candidatos. Voz neural e fallback agora
  usam a mesma espera cancelável; interrupção não confirma fala completa.
- **Provas:** sucesso, fallback confirmado, falha total, setup, interrupção,
  fallback interrompido e flush proativo com sucesso/falha em composição root.
  Proativas mescladas não entram como feedback entregue sem áudio confirmado.
- **Princípio compartilhado:** término de espera e remoção de fila não são
  receipt de efeito; cada habilidade usa a confirmação do executor de voz.

### RPV19-04 — Resposta de capacidade ignorava indisponibilidade do alvo afirmado

- **Primeira RED:** pergunta sobre avatar e intensidade alcançava domínio
  avatar indisponível + personalidade disponível; guarda geral `any` aceitava
  a pergunta e o ramo afirmava “Tenho um avatar”. Não confundir com F1, que
  trata negação falsa de capacidade na proposta da LLM.
- **Contrato/owner:** catálogo consulta disponibilidade do domínio sobre o
  qual afirma acesso. Ramo de avatar respeita estado operacional vivo; a
  descrição contextual informa a expressão por entrega sem autorizar ação.
- **Provas:** RED antes do candidato, controles positivos/negativos e root
  instalado com preferência do overlay desativada. Outros domínios e os
  limites de edição/receipts conservaram as regressões existentes.
- **Escopo:** correção aplicada no ramo demonstrado do catálogo compartilhado;
  não declarar auditoria global dos demais ramos por essa prova.

### P19 — Prova e próxima fronteira, 06/10/2026

- Seleção final: **855 aprovados em 37,35 s**, incluindo os 44 controles da
  composição instalada P19. XML final preservado; não somar execuções anteriores.
- Artefatos RED, seleção relevante final, build e hashes em
  `resultados_testes/p19_expressao_20261006`.
- Coleta real finita `p19_real_20261006`: 42,028 s, dois receipts `tts_total=True`,
  89 amostras de A/1 durante causa B/3 e 82 amostras da segunda entrega B/3.
  Sete critérios de software passaram; zero modelo; retrato liberado ao final.
- A ferramenta computer-use não expôs janela do overlay, embora o processo
  próprio tenha iniciado. Pergunta humana sobre som e aparência permanece
  pendente. Game Bar somente compilada/testada, sem atualizar pacote instalado.
- Fonte física e fonte final possuem hashes distintos: espera de substituição,
  cancelamento do fallback e catálogo foram ajustados depois da coleta e
  testados no caminho de software. Nenhuma confirmação física foi presumida.
- Próxima fronteira é aferição perceptível de P19. Sem reabrir P16, executar
  outras ações ou alargar modelo, memória ou autonomia. Nenhum commit criado;
  push autorizado continua reservado ao encerramento combinado com Pedro.

### RPV20-01 — Preferência explícita perdia escopo e efeito nos comandos

- **Primeira RED:** `pega leve hoje nos comandos` não produzia preferência;
  a postura operacional retornava antes de consultar o pedido válido.
- **Contrato/owners:** `preferencia_humor` interpreta a instrução social;
  decisão canônica fornece o contexto do turno; `perfil_amizade` consome a
  preferência sem decidir autorização. Jogo, conversa, comandos e geral têm
  escopos explícitos.
- **Provas/falsificações:** RED explícito antes do candidato, variantes
  naturais e controles de citação, contexto vizinho, vulnerabilidade e
  correção. A ausência de efeito não era ausência do serviço: o mecanismo
  explícito já existia no HEAD. Mais humor não libera execução ou provocação
  sem causa; tom leve bloqueia tirada sem perder o objetivo operacional.

### RPV20-02 — Precedência e cache durável discordavam da preferência atual

- **Primeira RED:** loader devolvia escopo específico antigo antes de comparar
  sua data com a preferência geral mais recente; turno com cache preenchido
  não relia evidência durável. Confiança textual inválida lançava exceção e
  infinita podia ser aceita.
- **Contrato/owners:** o motor compartilhado reidrata evidência explícita
  comprovada; seletor único compara pedidos válidos pela data; o orquestrador
  incorpora candidato durável mais recente sem apagar preferência temporária.
- **Provas/falsificações:** composição instalada reproduziu restart,
  atualização externa ao cache e precedência. SQLite gravou os dois escopos:
  falha de gravação não explicava a ordem errada. Cache removido ainda
  reproduzia a escolha antiga: não era apenas estado obsoleto. Leitura
  indisponível conserva pedido válido; dado expirado/corrompido não é promovido.
- **Limite:** isto reidrata pedidos explícitos com proveniência; não implementa
  inferência de personalidade ou tolerância por feedback genérico.

### RPV20-03 — Produtores ornamentavam antes de consumir a preferência

- **Primeira RED:** contexto da execução/adapter não transportava preferência;
  autores e geradores locais acrescentavam estilo apesar de tom leve válido.
  O diretor final preserva texto operacional, portanto não desfazia uma
  ornamentação que já fora produzida.
- **Contrato/owner:** seletor canônico oferece uma política única de supressão
  antes da autoria/variação. Consumidores passam a mesma preferência a
  planejador, confirmação, reação causal e respostas de arquivos, mídia e
  IoT. Nenhum parser particular de preferência ou remoção textual posterior.
- **REDs válidos:** `red_confirmacao_valido.xml` (28 falhas, 8 aprovados) e
  `red_playlist_interna.xml` (4 falhas no retorno direto de next/prev). Callback
  de autoria conta chamadas: desabilitar LLM ou capturar sua exceção não
  mascara ausência do veto. Frase/receipt/números e causa permanecem iguais.
- **Controle de candidato:** fallback de play/pause não pode derivar o fato
  do alias usado para variação (`pause`). `red_alternancia.xml` rejeitou a
  falsa frase “Pausei”; mapa factual passou a consultar o comando real.
  Esse erro do candidato não foi atribuído à raiz histórica de transporte.
- **Escopo:** supressão de ornamentação opcional nos consumidores verificados;
  não declarar remoção de qualquer metáfora preexistente no fallback factual.

### RPV20-04 — Gerador de estado reinferia confirmação apesar do receipt

- **Primeira RED instalada:** receipt `brilho_ajustado`, executou=True e
  confirmado=True, chegava ao adapter; `fala_por_estado_acao` criava outro
  ResultadoAcao pela lista de status e devolvia confirmado=None. O texto
  ganhava ausência de confirmação antes de receber o receipt real novamente.
- **Contrato/owners:** gerador consome o ResultadoAcao transportado pelo
  adaptador; status/alvo/execução/confirmação pertencem ao contrato existente.
  Compatibilidade sem contrato continua conservadora. Não ampliar a lista de
  status confirmados para transformar nome otimista em evidência.
- **Falsificações:** planner com receipt confirmado mantém o fato; a mesma
  preferência atravessava app sem ação e repetição causal corretamente;
  falho/incerto rejeitavam fallback otimista. Não era perda de número,
  indisponibilidade da LLM ou uma falha geral de entrega textual.
- **Provas:** RED em `consumidor_instalado_valido.xml` e
  `consumidor_controles_negativos.xml`; GREEN instalado em
  `green_receipt_consumidor.xml`. Controles de brilho e volume confirmados,
  falhos/incertos e sem receipt em `green_receipt_multidominio.xml`.
- **Limite:** composição instalada, memória isolada, portas executoras
  simuladas e método original de voz silenciosa. Texto e recibos são
  observados; ação externa e audição física não são certificados.

### P20 — Evidência e próxima fronteira, 06/10/2026

- Baselines distintos antes da seleção explícita e dos consumidores, hashes,
  XMLs e seleção em `resultados_testes/p20_preferencias_20261006`.
- Seleção final após todos os candidatos: **1.264 aprovados em 60,41 s**,
  81 módulos, `regressivos_expressao_finais.xml`. Resultado anterior de 952
  aprovados é intermediário; não somar gates ou declarar suíte completa.
- `red_transporte_confirmacao.xml` contém GREEN: teste e candidato chegaram
  durante a preparação. Não usá-lo como prova RED. `red_confirmacao.xml`
  tinha erros de fixture congelada; foi substituído pelo RED válido.
- Três expectativas antigas de dict/kwargs não incluíam a nova preferência
  transportada. Foram atualizadas mantendo status, alvo, tom e compromisso;
  XML original de falhas preservado, sem declarar que era totalmente verde.
- Primeira fronteira implícita ainda aberta: distinguir feedback sobre estilo
  de recusa/correção factual; vinculá-lo a entrega real e contexto da entrega,
  com deduplicação e várias ocorrências antes de alterar tolerância. A janela
  canônica de silêncio de 600 s não deve ser duplicada ou antecipada.
- Primeiro RED futuro: duas entregas registradas; “Essa piada passou do ponto”
  qualifica estilo com literal/ID/contexto da entrega, enquanto “O número da
  dica está errado” permanece correção genérica. Uma amostra não cria
  preferência. Motor só deve agregar após várias entregas distintas, sem
  contar replay nem atravessar contexto. Registrar entrega de comando pelo
  canal compartilhado; receipt de execução não prova entrega da fala.
- Preferência explícita validada; calibração implícita não ativa. P19 conserva
  sua lacuna perceptível, P16 permanece no escopo aprovado. Nenhum commit
  criado; worktree paralela e autorização histórica de push preservadas.

### RPV20-05 — Feedback genérico não qualificava o objeto humor

- Contrato: literal qualificado pelo interpretador único + fonte validada
  pela ponte antes da projeção no MotorAprendizadoRuntime. Feedback genérico
  conserva seus pesos; correção factual não vira preferência de estilo.
- RED `red_qualificacao.xml`: 29 falhas, quatro aprovados; ausência de
  qualificador e perda do contexto na ponte. Não era erro de importação.
- Classificação genérica correta e persistência genérica bem-sucedida
  falsificaram as hipóteses concorrentes de parser geral e armazenamento.
- GREEN `green_qualificacao.xml`: 33 aprovados. Citações, terceiros,
  instruções independentes e vulnerabilidade não qualificam evidência.

### RPV20-06 — Receipt de entrega e contexto social eram insuficientes

- Queue acceptance e receipt operacional não confirmam entrega comunicativa.
  Diretor reutiliza o histórico/IDs; orquestrador registra publicação textual
  aceita; worker de voz registra somente reprodução confirmada por software.
- RED `red_entrega.xml`: seis falhas, um aprovado, na porta ausente.
  RED `red_contexto_entrega.xml`: uma falha; domínio `rotina` durante jogo
  era convertido em conversa. Owner congela contexto da decisão social,
  incluindo propostas proativas antes da entrega assíncrona.
- RED `red_silencio_relacionado.xml`: uma falha; “Ainda não sei” não impedia
  silêncio indevido. Pergunta sobre estilo e resposta relacionada são
  qualificadas canonicamente. Silêncio só após 600 s, até 3.600 s, uma vez.
- Fonte emocional conserva sua projeção neutra; proveniência de aprendizado
  acrescenta contexto de humor. Expectativas de testes devem distinguir as
  duas projeções, sem ampliar a autoridade ou payload do evento emocional.

### RPV20-07 — Agregação não decidia tolerância contextual

- RED `red_agregacao.xml`: dez falhas, 14 aprovados; SQL genérico funcionava,
  mas evidência de estilo não era persistida. Não declarar raiz no SQLite.
- Motor persiste somente evidências qualificadas com fonte; Maturidade
  revalida cada registro e decide suficiência. Seletor do turno e consumidores
  de expressão reutilizados; nenhuma nova permissão ou chamada de LLM.
- Três IDs de entrega distintos no mesmo contexto, predominância ponderada
  >=75%, influência média >=0,30. Correção de estilo -0,75, recusa -0,45,
  aceitação +0,45, repetição +0,25. Decaimento individual com meia-vida de sete
  dias; validade máxima 14 dias. Registro novo não rejuvenece os anteriores.
- Silêncio -0,10 é evidência neutra: não conta para as três amostras
  direcionais nem inverte o tom; só reduz influência do padrão. Pedido
  explícito vigente vence sempre, mesmo contra inferência mais recente.
- Contextos `jogo`, `conversa`, `comandos` independentes, sem perfil pessoal.
  Preferência derivada é temporária e recalculada após reinício; fonte
  qualificada persiste. Catálogo vivo e diagnóstico explicam esses limites
  sem expor literais pessoais no diagnóstico.

### P20 implícita — Auditoria dos gates intermediários

- Baseline HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch `main`;
  hashes e worktree congelados em `p20_implicita_20261006/baseline.json`.
- `composicao_instalada.xml` tinha nove erros de fixture: porta real pertence
  ao Adaptador instalado, que delega ao Motor. Não é RED de produção.
  `composicao_instalada_valida.xml`: nove aprovados com owners corretos.
- `green_agregacao.xml`, `green_cadeia.xml`, `green_composicao_catalogo.xml`
  são gates intermediários com falhas preservadas; nomes não provam GREEN.
- `regressivos_finais.xml`: dez falhas, 1.436 aprovados. Seis expectativas
  misturavam projeção emocional com contexto de aprendizado; quatro imports
  colidiram com o mutex da aplicação aberta. Testes corrigem a separação de
  contratos; execução isolada usa mutex Windows real com namespace próprio,
  sem remover proteção ou interromper a aplicação.
- `green_contexto_causal.xml`: duas falhas, 120 aprovados, porque dois replays
  artificiais ainda não transportavam o contexto exigido. Fixtures corrigidas;
  `green_contexto_causal_final.xml`: 38 aprovados na fronteira revisada.
- Coleta instalada em `coleta_instalada.json`: dois processos, nove entregas
  textuais em três contextos, persistência, reidratação, consumo, replay,
  expiração e precedência explícita; sem modelo, fila de áudio ou execução
  externa. Não representa autoria semântica ou som físico.

### P20 implícita — Gate de encerramento da implementação

- **1.447 aprovados em 86,10 s**, 94 módulos, XML
  `resultados_testes/p20_implicita_20261006/regressivos_finais_isolados.xml`.
  Seleção, launcher de isolamento, hashes e coleta preservados. Não é suíte
  completa nem soma dos gates intermediários.
- Implementação da P20 encerrada pelos contratos RPV20-05/06/07; todos os
  itens dessa etapa no roadmap atendidos no escopo de software. Ativação
  final e validação sequencial permanecem na P21; P19 conserva a lacuna de
  observação física. P16 não foi reaberta.
- Produção alterada nesta continuação: interpretador_continuidade,
  preferencia_humor, diretor_presenca, ponte_iniciativa_aplicacao,
  motor_aprendizado, maturidade_aprendizado, orquestrador_turno_runtime,
  orquestrador_fala_runtime, voz_runtime, mapa_habilidades,
  formatacao_diagnostico e wiring/diagnóstico em laylay.py.
- SQLite/schema, executores e autorização operacional não alterados nesta
  continuação. Alterações paralelas preservadas; nenhum commit/push ou
  desligamento executado.

### P21 — Continuação de RPV18-04/05: apresentação e foco, 06/10/2026

- **Baseline:** HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch
  `main`, worktree suja preservada. Status e nove hashes anteriores ao
  candidato em `p21_reacao_jogo_20261006/baseline.json`. Esses hashes não
  cobrem todos os arquivos do diagnóstico posterior.
- **Primeiras fronteiras:** RPV18-04 materializava toda descrição como
  `Na tela: "..."`; RPV18-05 escolhia o primeiro fato mesmo quando a fonte
  propunha outro foco, que o parser descartava. São continuações das raízes
  existentes, distintas da troca de modelo por HTTP404 de RPV18-03.
- **Falsificações:** a resposta visual anterior não continha o molde citado,
  que o compositor acrescentava; portanto a origem do molde local não exige
  uma regressão do provedor. Um segundo fato válido perdeu para OCR inicial;
  havia material disponível, mas transporte/seleção estavam incorretos.
  Não há quadro histórico para provar a identidade da arma ou a direção do
  feixe: regressão semântica do modelo continua hipótese.
- **Contrato:** cognição valida foco por vínculo literal com os fatos;
  apresentação distingue descrição de citação operacional usando leitores
  canônicos. Proposta livre do modelo não confirma efeito nem vira execução.
  Ausência de fonte para foco explícito é fail-closed, mesmo sem motivo.
- **REDs:** 11 falhas/2 controles no primeiro gate; duas falhas/35 controles
  localizaram o uso de origem desconhecida na guarda de alegações, corrigido
  para a origem canônica. Um RED adicional provou o fallback indevido quando
  foco explícito não tinha fatos. Gates e falhas preservados; não somá-los.
- **Composição e regressão:** parser/Coordenador/Diretor/cognição e root
  instalado testam foco, citação, autoridade, fila e callback. Gate anterior
  ao diagnóstico: 1.536 aprovados em 89,62 s, 99 módulos; não é suíte completa.
- **Runtime:** coleta finita `p18_jogo_real_20261006_183052`, dois quadros,
  uma materialização e receipt identificado, zero chamadas de autoria.
  Nenhum quadro do laser; outro quadro coberto pelo Discord. Fonte sugeriu
  `mecânica de graviton implícita`, que não foi escolhida nem falada.
  Qualidade dessa inferência fica aberta como hipótese do produtor, sem
  agrupamento automático com apresentação. Som/naturalidade não certificados.

### RPV21-01 — Projeção incompleta e incoerente do diagnóstico emocional

- **Primeira fronteira:** snapshot omitia intensidade e projeção expressável;
  evento válido contido tinha supressão vazia, enquanto evento expirado podia
  mostrar um código otimista de expressão. O estado causal já existia; a
  divergência era na projeção de leitura, não na escrita da emoção.
- **Owner/contrato:** `diagnostico_mente` consulta os leitores canônicos de
  validade e expressão usados por voz/avatar; formatter apresenta esse
  retrato. Diagnóstico não altera memória, emoção, resultado ou autorização.
  Referência causal publicada por hash, sem o relato pessoal.
- **RED válido:** seis falhas em `red_diagnostico_valido.xml`. O primeiro
  arquivo `red_diagnostico.xml` é erro de coleção por nome de API incorreto
  no teste; não constitui prova causal. Comando com módulo inexistente também
  não executou testes. Fixtures corrigidas antes de produção, sem enfraquecer
  expectativas. O mesmo cuidado vale para a tentativa inicial de composição
  com nome de módulo inexistente.
- **GREEN:** 162 controles focados; depois 70 de diagnóstico, catálogo e
  composição; após referência causal por hash, 22 controles. Último gate
  conjunto focado de foco/diagnóstico/transporte: 28 aprovados. São níveis
  intermediários, não soma nem suíte completa.
- **Limites:** root instalado valida snapshot sem hardware. A sessão real
  de jogo importou o código antes deste candidato; não prova os campos novos.
  P21 continua em andamento, P19 mantém observação perceptível pendente e
  P16 não foi reaberta. Nenhum commit/push ou desligamento nesta continuação.
- **Gate conjunto posterior:** 1.544 aprovados em 71,04 s, 100 módulos,
  `regressivos_incremento_final.xml`. Inclui diagnóstico, catálogo e o controle
  de foco sem fatos. XML anterior de 1.536 preservado; gates não somados.
  Launcher usa memória temporária e namespace próprio no mutex Windows real.
  A chamada de ferramenta foi interrompida, mas o processo continuou; resultado
  confirmado pelo XML concluído, sem repetir a execução.

### RPV21-01 — Continuidade: causa selecionada e elegibilidade, 06/10/2026

- **Baseline desta continuação:** mesmo HEAD/branch, status e seis hashes
  preservados em `p21_validacao_final_20261006/baseline.json`. Worktree suja
  mantida. Não renomear a raiz por cada cenário do diagnóstico.
- **Primeira fronteira:** após publicar evento forte e evento fraco, o quadro
  corretamente apontava para a última proposta, enquanto o episódio mantinha
  a causa forte. Snapshot juntava expressão forte com metadados da proposta
  fraca. Elegibilidade de um evento sem episódio aplicado também aparecia
  como decisão atual de expressão, apesar da projeção canônica calma.
- **Falsificações:** a prioridade já preservava o episódio correto antes do
  snapshot; publicador registrava corretamente a proposta nova. Portanto
  não alterar prioridade, publisher, setters ou executor. Composição instalada
  confirmou a mesma primeira fronteira em entradas de terminal e chat.
- **REDs válidos:** dois em `red_transicoes_diagnostico.xml`; dois em
  `red_transicoes_instaladas_valido.xml`. A tentativa inicial de composição
  falhou ao fazer deepcopy de mapa com RLock; não é RED causal. Gates posteriores
  com 68 controles verdes ainda tiveram erro de fixture por argumento de voz
  inexistente e por campo de origem incorreto. APIs corrigidas no teste,
  preservando todas as asserções causais. Snapshot após publicar fala é
  comparado com o estado posterior à publicação, sem confundir seu ciclo
  legítimo com escrita do diagnóstico.
- **Candidato mínimo:** somente diagnóstico/formatter de produção nesta
  continuação. Causa/intensidade/responsável da expressão vêm do episódio
  escolhido pelo leitor canônico; referência separada conserva a última
  proposta. Evento elegível sem expressão atual mostra contenção. Sem
  alteração de memória emocional, prioridade, resultado, autorização ou
  fila. Dez controles focados aprovados; gate completo final registrado abaixo.
- **Coleta perceptível:** helper existente P19 ganhou somente observação
  de diagnóstico e hashes de suas fontes. Coleta real finita 35,776 s,
  250 amostras, 77 durante fala, duas falas concluídas e zero chamada ao modelo.
  Pedro confirmou diretamente som completo/inteligível, expressão estável,
  segunda mais intensa e retorno neutro. Confirmação em arquivo próprio;
  relatório bruto preservado. Não estender ao laser, naturalidade de jogo,
  pacote Game Bar ou a todos os estados operacionais.

### P21 — Suíte completa e correção de fixtures, 06/10/2026

- Primeira execução completa configurada: **10.068 aprovados, duas falhas,
  um ignorado e 56 subtestes aprovados**, 585,37 s. XML `suite_completa.xml`
  preservado em `p21_validacao_final_20261006`; não é gate verde global.
- Falha antiga do guardião TTS, antes anotada em RC-OFERTA-01, reproduzida
  isoladamente. Sua porta falsa fornecia somente `wait`, mas o contrato
  P19 de cancelamento/receipt usa `get_stream().active`. O diff confirma a
  troca anterior; código da voz não foi alterado nesta continuação.
  Fixture agora fornece stream concluído e exige que ele seja consultado.
  Controle adicional sem receipt permanece falso, sem declarar migração
  bem-sucedida. Não substituir reprodução por callback sempre verdadeiro.
- Falha do novo teste P21: `chat` foi usado como origem de entrada, mas a
  origem canônica do texto é `terminal`; chat é estado da conversa.
  Fixture usa o setter instalado de modo chat e mantém origem terminal,
  verificando tanto modo quanto origem real. Normalizador não alterado.
  Os dois REDs instalados anteriores comprovam a projeção errada, mas a
  variante então rotulada chat ainda estava no modo padrão e teve origem
  normalizada como desconhecida. A prova de modo chat ativo é a nova coleta
  `transicoes_chat.json`, com entrada terminal e `chat_ativo=True`; não atribuir
  retroativamente esse modo ao RED anterior.
- **110 controles aprovados** em `green_fixtures_canonicas.xml`; todos os
  controles de causa, plano, autoridade, número de publicações e falta de
  receipt preservados. Segunda execução completa: **10.071 aprovados, um
  ignorado e 56 subtestes aprovados em 402,44 s**, XML próprio
  `suite_completa_final.xml`, zero falhas/erros. Coleta instalada da primeira execução copiada
  para `coleta_instalada_primeira_suite.json`, sem apagar o histórico.
- Candidato desta continuação permanece restrito a diagnóstico/formatter.
  Ajustes das duas fixtures não demonstram outra raiz de produção; não
  reabrir P16 nem criar um remendo na voz ou no normalizador de origem.
- Matriz final de 17 contratos validada contra os casos do XML completo verde,
  com IDs das raízes históricas. A unidade de encerramento continua a raiz,
  não o cenário. Diagnóstico/invariantes de software concluídos; causas
  controladas e confirmação humana das duas falas/avatar não certificam toda
  a sequência real ou a qualidade semântica do jogo/laser. Limites de estados
  operacionais e Game Bar preservados. Laylay principal anterior ao candidato
  precisa recarregar o código. Nenhum commit, push ou desligamento neste gate.

### RPV18-04/05 — Continuação: OCR isolado e moldura genérica, 06/10/2026

- **Relato novo:** `Reparei nisso. Na tela: "-FLORESTA.".`. Não encerra a
  qualidade de jogo a suíte da P21 de diagnóstico ter passado. A fala literal
  não foi localizada nos campos persistidos consultados; o runtime de origem
  estava fechado na primeira inspeção, portanto não presumir seu hash.
- **Reproduzido na worktree:** o foco aceita `texto exato visível: -FLORESTA.`
  como curiosidade e o compositor acrescenta uma abertura à citação. Mesmo
  uma observação já conversacional ganhava complemento genérico. São
  continuações da seleção RPV18-05 e apresentação RPV18-04, não novos IDs por
  frase. Doze REDs de contratos antecederam o candidato.
- **Falsificações:** a moldura é produzida antes de TTS e com zero autoria de
  modelo; falha de pronúncia ou troca de provedor não explicam sozinhas essa
  transição. O texto é reconhecido como OCR corretamente; o erro é tratá-lo
  como acontecimento que justifica comentário.
- **Contrato / owners:** cognição conserva a fonte OCR, mas contém
  companhia/curiosidade quando o foco é só rótulo ou fragmento nominal. Foco
  explícito contido não é substituído por outro item para forçar fala. A
  contenção é obedecida por RespostaEventoRuntime também fora do jogo, sem
  chamar outra autora. Perguntas visuais e nomes musicais úteis conservam seus
  caminhos. O compositor entrega diretamente a observação descritiva breve;
  celebração, acolhimento, provocação e citação operacional mantêm seus limites.
- **Produção nesta continuação:** `contrato_fala.py`, `compositor_evento_local.py`,
  `resposta_evento_runtime.py` e prompt de `analise_visual.py`. A chamada visual
  pede a evidência focal em linguagem de conversa, literal e concreta. Fala
  livre, motivo, mecânica inventada e comando não ganham papel de evidência.
- **Gates:** 49 focados, quatro pela composição instalada e 271 regressivos,
  em XMLs separados de `p21_jogo_naturalidade_20261006`, sem somar contagens.
  O root real usa parser/Coordenador/Diretor/cognição/fila: OCR gera zero timers
  e zero fila; observação natural gera uma fila e um timer, sem segunda autoria
  nem confirmação física antecipada. Gate antigo da P21 não cobre este candidato.
- **Auditoria de testes:** cinco expectativas antigas pediam bordões variados
  sobre a mesma observação ou curiosidade sobre nome OCR. Foram atualizadas
  pelo novo contrato explícito: curiosidade conserva a frase concreta;
  variação continua provada em celebração e citação em nome musical útil.
  Não foram retiradas as guardas de autoridade, vulnerabilidade ou receipt.
- **Coleta real:** iniciada no Megabonk, que era o jogo aberto. Helper finito
  existente recebeu preservação opcional dos quadros e estado próprio da
  central. Resultados e limites serão vinculados após a coleta; não declarar
  naturalidade geral ou reconhecimento do laser pelo GREEN controlado.
- **Primeira coleta deste candidato:** `p18_jogo_real_20261006_192748` guardou
  quadros reais. Uma frase sem bordão chegou ao receipt identificado, mas era
  o fragmento `círculo azul brilhante no chão sob o personagem.`. Isso falsifica
  que o primeiro ajuste bastava para a naturalidade. A segunda proposta trouxe
  foco fora da própria lista; guardas existentes impediram sua fala. Associação
  do círculo ao portal era inferência visual sem prova e não foi falada.
- **Próxima fronteira do mesmo owner:** prompt da própria chamada visual
  consolidado: uma frase factual completa, em linguagem de conversa, repetida
  literalmente em evidência/foco/fala; sem prose duplicada ou bordão adicional.
  Replay do primeiro quadro produziu frase completa, mas inferiu conforto da
  pedra; regra reforçada para aparência/posição observável. Segundo replay teve
  HTTP 429 e não ganhou fala. Prompt final encurtado, 88 controles aprovados;
  coleta fresca em `p18_jogo_real_20261006_215418` preserva fonte e hashes.
- **Avaliação humana RED, decisiva:** a coleta `215418` entregou
  `Esse monstro de pedra com olhos azuis parece bem pesado ali no tronco!`.
  Pedro respondeu **`Ouvi, mas ainda ficou ruim`**. Frase completa e receipt
  verde não encerram naturalidade. A regra que forçava autoria dentro de fatos
  manteve descrição em vez de reação e foi revista; não atribuir aprovação
  humana a essa tentativa. Registro literal em `avaliacao_humana.json`.
- **Contrato revisado, mesma raiz RPV18-04:** produtor propõe `proposta_reacao`
  com fala, foco literal, trecho concreto e humor; transportadores não adotam.
  Cognição é dona da adoção, reaproveitando modalidade, alegações, aderência e
  guarda de ataque pessoal. Reação não entra na lista de fatos. Proposta
  inválida/ausente, humor contido ou vínculo incorreto ficam sem fala e sem
  fallback narrativo, em todos os domínios que usem esse contrato. Onze REDs
  antes do candidato; ajuste posterior de casing do trecho não altera a fonte.
  Vínculo textual e guardiões não são um detector universal de verdade da
  fonte visual; não promover a impressão social a receipt ou fato durável.
- **Coleta autoral `220211` concluída:** três análises, nenhuma entrega. Dois
  quadros não justificaram fala; no terceiro, `portal de chefe` não estava no
  fato focal e a cognição conteve por `reacao_sem_vinculo_factual`. Inspeção da
  captura mostrou que o objetivo do HUD não identificava aquela estrutura.
  A contenção é válida; silêncio não aprova naturalidade. Processo saiu com
  código zero e aviso Win32 ao liberar COM, sem interferir no jogo.
- **Precisão humana do RED:** Pedro explicou que o monstro foi comentado como
  um objeto ao lado do tronco, sem acompanhar a ação. Replay real de dois
  quadros preservados produziu vínculos textuais válidos, mas voltou a focar
  objetos. Isso falsifica que separar autoria/fato ou ordenar o JSON basta
  para corrigir a seleção RPV18-05. Replay não é captura nova nem áudio.
- **Primeira fronteira agora delimitada:** observador fornecia uma foto
  isolada; o produtor aceitava aparência estática como companhia. Princípio:
  uma afirmação temporal requer evidência temporal do mesmo alvo; diferença
  perceptual sozinha não prova acontecimento. Não criar ID por frase.
- **Candidato mínimo desta fronteira:** observador captura dois instantes
  próximos, com espera de 0,6 s, revalida jogo/janela/PID antes e depois e usa
  o pacote multimodal compartilhado numa análise. Sequência incompleta,
  alvo divergente, ocupado ou revogado não seguem. Runtime informa ordem
  temporal ao prompt somente para esse par rotulado; tooltip não vira vídeo.
  Prompt prioriza ações/efeitos/resultados e não catálogo de objetos, com
  reação curta em momento seguro. Não foi criado streaming ou segunda autora.
- **Gates temporais:** seis REDs antes do candidato; um RED adicional para
  troca da janela durante a segunda captura. 157 controles relevantes verdes
  incluem seis casos no root, um deles observador → visão → parser → Diretor
  → cognição → fila. 72 controles posteriores cobrem também a revalidação
  final; não somar gates. Um teste antigo falhou apenas por casing de
  `Decida`; a asserção conserva o contrato usando `casefold`.
- **Limites:** amostragem esparsa não acompanha toda ação nem prova mecânica;
  o modelo ainda pode interpretar a imagem incorretamente. Segurança e
  receipts não certificam semântica. Nova coleta finita `221226`, de 90 s,
  avaliará seleção real; aprovação perceptível permanece pendente.
- **Fechamento desta coleta, sem encerrar a raiz:** `221226` registrou dois
  pares. Primeira análise indisponível; segunda reagiu ao aparecimento de
  `REFLECT`, mas terminou em pergunta retórica e foi contida. Orientação do
  produtor corrigida para fala afirmativa, sem mudar o veto canônico. Replay
  desse par produziu `Esse REFLECT apareceu bem na hora!`, sem áudio; controle
  de quadro repetido teve HTTP 429 e é inconclusivo.
- **Custo real do par:** limite observado 7.000 tokens/minuto, pedido de 5.563,
  uso de 6.828 no controle rejeitado. Cadência de 35 s não acomoda duas dessas
  análises por minuto. Um RED de cadência antecedeu o piso de 60 s do loop;
  budgets por janela existentes preservados. Não afirmar rate limit dinâmico
  universal nem que chamadas diretas ao método têm esse mesmo espaçamento.
- **Gate final:** 160 aprovados em 50,02 s, incluindo seis casos instalados.
  Nenhuma suíte completa refeita; gates anteriores não somados.
- **Última coleta `221645`, 90 s, concluída:** um par no menu de upgrades,
  uma análise, zero entrega, nenhuma aprovação humana nova. Fonte alegou
  contador aumentando de 4 para 5, mas ambas as capturas mostram moeda=4 e
  caveira=5. É um RED semântico remanescente da fonte, não uma mudança temporal
  provada. Essa afirmação não foi falada. Não corrigir com outro bordão ou
  relaxar o vínculo factual. Relatório/manifesto em
  `p21_jogo_naturalidade_20261006`. Falta a prova perceptível de reação à ação
  e a leitura visual mantém limite explícito. Sem commit/push/desligamento.
- **Novo controle perceptível aprovado, `222605`:** após Pedro confirmar
  combate, helper antecipou um único par, com toda a composição/captura/modelo
  reais. Duas capturas, uma análise, uma entrega identificada. Pedro confirmou
  `Ouvi e a reação ficou adequada` sobre a fala do contador 33 → 35 e a festa
  ficando mais cheia. GREEN de áudio/adequação deste caso; não apagar o RED
  humano anterior nem validar cadência normal com disparo antecipado.
- **Limite preservado:** caveira=33 → 35 é visível; interpretar isso como
  mais inimigos vivos não é comprovado. Um refinamento no prompt excluindo
  contadores voltou a comentar aparência estática do círculo no replay real.
  Hipótese falsificada; só esse bloco novo foi retirado por `apply_patch`.
  Nenhuma outra mudança revertida. Fontes de produção iguais às do gate de
  160/controle aprovado; artefatos e declaração humana separados.
- `222336` havia capturado menu principal, sem fala. Controle `222605`
  concluiu a coleta mas saiu com código 1 e aviso COM após o receipt. Isso
  não revoga a audição humana nem prova saúde do teardown. Qualidade universal
  da fonte e teardown permanecem limites; não abrir patch alheio para forçar
  encerramento. Sem commit/push/desligamento; P16 preservada.

### Pedido composto — autoria por pedido a partir de receipts individuais — 08/10/2026

- Base `main`, `90a2fb8698541119f523c0a22fa4de0187cbaf92`, worktree compartilhada
  preservada. Frase humana: `liga a luz e coloca a playlist piano`.
- Primeira divergência: cada adaptador gerava e entregava sua própria autoria
  antes do TTS. Dois receipts legítimos produziam dois balões; deduplicação de
  uma mesma ocorrência não explica esse caso. RPV18-07 congela reprodução;
  esta fronteira anterior possui outra responsabilidade, sem fundir as raízes.
- Contrato/owner: orquestrador de fala acumula a apresentação por pedido;
  executores mantêm autorização, efeito, receipt e certeza próprios. Cadeia
  determinística e dispatcher JSON reutilizam a mesma porta. Uma autoria
  validada cobre os resultados; finalização preserva histórico/aprendizado sem
  pedir outra fala. Avisos sem receipt não recebem a prova de outra etapa.
- REDs e controles preservam falha parcial, idempotência, atualização de certeza,
  humor, turno antigo, estados não confirmados e texto publicado sem áudio.
  Regressão consolidada: **579 aprovados / 27 módulos / 22,31 s**. Duas autorias
  originais 4B aceitas em **1,815 s / 1,479 s**, com efeitos externos isolados.
- Após reabrir e testar o pedido, Pedro confirmou **`Uma resposta e fala mais rápida`**.
  Prova qualitativa de apresentação/audição desta ocorrência, sem cronometragem
  no jogo nem inspeção de efeitos físicos. Sem commit. Relatório/diff/hashes:
  `resultados_testes/latencia_geral_20261008/resposta_composta/`.
- Otimização temporal separada: lote Ollama 128→256, preservando pesos, contexto
  6144 e amostragem; backup e receipt no diretório pai. A compactação emocional
  foi rejeitada por perda de evidência na geração real; contrato original e voz
  preservados. A coleta nova repetiu uma resposta contextual: achado de qualidade
  permanece registrado, sem atribuir sua causa ao lote ou fechar P01.

### Corpo móvel — contrato físico de bancada em preparação — 11/10/2026

- **Natureza:** melhoria pedida por Pedro: dois N20 de 3 V / 30 RPM, ponte
  DRV8833 e ESP32-C3 Super Mini, com futura locomoção por pedido e iniciativa.
  Não é nova raiz causal demonstrada nem extensão de autoridade da RPV18-06.
  A expressão emocional permanece um consumidor vizinho sem permissão motora.
- **Base:** `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`; worktree
  compartilhada anterior preservada. Nenhum commit criado.
- **Primeiro gate físico:** Pedro usa USB 5 V e não tem conversor; os N20
  precisam de alimentação de 3 V adequada à corrente de partida. Sinais podem
  ser montados sem energia; VM permanece desconectado. `EEP`/`ULT` são
  prováveis finais de SLEEP/FAULT, sem prova do circuito do módulo preto.
- **Pinout do candidato:** esquerda GPIO0/1, direita GPIO3/10, SLEEP GPIO7,
  GND compartilhado; OLED preservado SDA8/SCL9. Guia pronto em
  `firmware/rosto_laylay/MONTAGEM_MOTORES.md`.
- **Owner/contrato de bancada:** firmware aplica PWM e desabilita a ponte;
  sessão vigente e sequência de motor própria, pulsos finitos de 50–500 ms,
  novo pulso rejeitado enquanto ocupado, FACE sem renovação de tração,
  STOP prioritário, corte em boot/HELLO/DEMO/expiração/perda do OLED.
  O prazo é de software; latência real sob bloqueio I2C exige medida física.
- **RED anterior ao candidato:** host compilando o `.ino` inicial alcançou
  HELLO/FACE/MOTOR, mas o GPIO7 não habilitou a ponte. O teste falhou na
  primeira asserção de configuração GPIO, não em import ou compilação.
- **Estado real:** candidato compilado/testado em host, sem upload, COM aberta ou motor
  energizado nesta etapa. COM4 conserva a versão de rosto previamente validada.
  Receipts de GPIO/PWM não provam tensão, rotação nem deslocamento.
- **Próxima fronteira:** fonte/montagem compatíveis, pulsos individuais com
  rodas levantadas, sentidos/parada/perda de comunicação e depois chão.
  Comandos naturais/autonomia ainda não estão instalados nem disponíveis no
  catálogo. A integração deverá reutilizar owner serial, modalidade/autorização,
  pendência, resultado, aprendizagem, observabilidade e catálogo canônicos.
  Iniciativa física terá domínio e limites próprios; não herda o perfil de
  ações reversíveis, pois desligar motores não restaura a posição anterior.
- **GREEN de software desta etapa:** fonte real compilada para C3/core 3.3.12,
  380.078 bytes de programa / 15.748 de RAM estática; SHA256
  `5269cd53bc66c500dc3a5b96ba5b002df7083384fe7f42e1121c19ba35db92d1`.
  Host protege sentidos, sequência/limites, wake, replay, parada, falha de PWM,
  OLED, TTL e wrap. Dois REDs temporais de I2C e um RED de token de sessão
  longo antecederam suas correções mínimas. 109 regressivos de rosto/expressão/
  reação social verdes; 100 trocas de pose passaram (máximo 287 pixels).
  Sem runtime físico motor ou integração de locomoção na mente. Esta melhoria
  permanece em preparação; não encerrar pelo verde host/toolchain.

### OLED — atividade operacional observada e mini terminal — 11/10/2026

- Melhoria visual pedida por Pedro; separada da causa emocional RPV18-06 e do
  corpo móvel. Base `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`,
  worktree anterior preservada, nenhum commit.
- Primeira fronteira ausente: composição instalada despachava uma ação, mas
  não publicava atividade operacional observada. RED canônico com despacho
  controlado por Event alcançou essa fronteira e falhou em `ativos`. O estado
  visual `executing` existente também pode nascer de um plano recente: é
  inadequado para provar tratamento. Emoção e plano não são usados no novo sinal.
- Owner único `AtividadeOperacionalRuntime`, tokens concorrentes/reentrantes,
  conclusão em finally e cancelamento async; publicação transitória em mental.
  Ciclo após deduplicação, autonomia e bypasses de resumo/saída de áudio usam
  o mesmo owner. Não muda validação, autorização, retornos ou receipts. O sinal
  representa tratamento, incluindo possíveis recusas, sem confirmar efeito.
- REDs de transporte (CAPS ausente) e firmware real compilado em host (CAPS
  sem resposta) precederam os candidatos. HELLO/FACE preservados; extensão
  HACK1/ACTIVITY com sessão, sequência própria, TTL e AACK após render/probe.
  Firmware antigo continua compatível; falha de AACK não invalida FACE.
- Mini terminal com fonte pixel compartilhada entre renderer/ESP, digitação,
  rolagem, cursor, indicador indeterminado e entrada/saída em 300 ms. Rosto
  evolui por baixo. TTL, perda do OLED/sessão e HELLO encerram atividade; DEMO_HACK
  é local e não gera ações. Não transmite comandos pessoais.
- 241 regressivos relevantes GREEN em 16,72 s; composição instalada prova que
  o getter OLED lê o mesmo retrato durante despacho e no fim. Host cobre sessão,
  parser, replay, tempos/I2C/wrap, pixels e controles de motor preservados.
- RED separado de perfil físico: boot ainda habilitava PWM da bancada. Perfil
  padrão agora é `LAYLAY_HABILITAR_MOTORES_BANCADA=0`; teste default prova rejeição
  de MOTOR mesmo com sessão vigente e hack ativo. Nada no hack autoriza tração.
- Pedro informou motores conectados e girando com 5 V: observação humana,
  sem promover nominal de 3 V, uso contínuo, corte ou locomoção a GREEN.
  Compilação, upload e confirmação óptica desta animação são provas separadas;
  os receipts finais pertencem a `artifacts/rosto_oled/hack/`.

- Validação final do hack: C3/core 3.3.12, 376.548 bytes programa / 15.748 RAM,
  perfil motores=0, gravado na COM4 com hash da flash verificado; MAC
  `ac:27:6e:72:ba:70`. Fonte SHA256
  `d5c8c6076f258681cb9265a60e827f91b481dac89e4d08f03bea252e867bee95`.
  Composição instalada/serial real: 14 FACE ACK e 14 AACK, fases repouso,
  tratamento controlado e retorno. Nenhum comando MOTOR; não foi ação natural
  de habilidade. Inspeção humana do DEMO_HACK: Pedro confirmou
  **"Sim, ficou legal e fluido"**. Prova visual pontual e de transporte; ainda
  não é observação de uma ação natural completa durante uma conversa.
- Steering posterior do corpo móvel: Pedro esclareceu que os motores atuais
  são de teste, distintos dos N20, confirmou o pinout e protoboard sem rodas;
  autorizou habilitar o perfil de bancada. Build opt-in separado e pulsos
  individuais são a próxima prova, sem ativar comandos naturais/autonomia.

### Atualização do corpo móvel — bancada real, sem nova raiz — 11/10/2026

- Continua a mesma melhoria física em preparação, separada da RPV18-06 e do
  owner visual. Motores atuais são outros motores de teste; Pedro confirmou
  funcionamento anterior pela própria DRV8833 a 5 V, sem multímetro e sem rodas.
- Perfil de bancada 1 foi habilitado após autorização explícita. Falha inicial
  de upload por COM4 ocupada; usuário fechou a Laylay e a nova tentativa verificou
  a flash. MACK/STOPPED para quatro pulsos PWM180/250 ms no mapa antigo; humano
  **"Não giraram"**. RED físico preservado apesar do verde de configuração.
- Usuário solicitou GPIO1/2/3/4 e confirmou remontagem desligada/reconectada.
  Novo RED host de mapa antes do candidato; somente array/comentário e asserts
  GPIO foram alterados. Ambos perfis host GREEN com proteções motor/visual iguais.
  Não declarou causa elétrica do RED antigo: mudanças de contato e mapa não
  permitem escolher uma única causa sem medidas.
- Fonte atual `0c8916f8c2d53826be82a06dab9371f9890d0ed54bc6ec4378f22a0eaee21990`,
  C3/core 3.3.12, 383.732/15.772 bytes, perfil motor=1, COM4/MAC conhecida,
  hash da flash verificado. No mapa novo houve giro fraco em PWM180; a pedido
  humano aumentou somente PWM para 255, mantendo duração de 250 ms.
- Caminho instalado/serial real, quatro MACK e STOPPED, parada final confirmada.
  Pedro: **"Sim, os dois ficaram mais fortes e pararam"**. GREEN físico pontual
  de ambos motores/sentidos/parada percebida; não mede precisão temporal do corte,
  corrente, torque ou deslocamento. Ferramenta fixa de bancada pronta:
  `scripts/testar_motores_bancada.py`; receipts únicos em
  `artifacts/rosto_oled/motores/`, sem substituir o primeiro RED.
- Próxima fronteira natural demonstrada em owners reais: `anda para frente`,
  `gira para a esquerda` e `pare os motores` ainda classificam como conversa,
  sem autorização; CORPO_MOVER não está no catálogo. Negociação motor própria,
  modalidade/intent/executor/receipt/continuidade/aprendizado/catálogo são
  pendentes. Upload/MACK/giro não instalaram locomoção natural/autônoma.

### Continuação corporal e visual — integração manual, glitch e boca — 11/10/2026

- Base preservada: main, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`;
  worktree anterior mantida, nenhum commit. Não altera RPV18-06 nem apaga o
  RED físico do mapa antigo. Três contratos distintos abaixo compartilham o
  transporte, sem transformar emoção/atividade visual em autorização motora.
- Corpo: RED em modalidade de seis pedidos e ausência de CORPO_MOVER no
  catálogo antes do candidato. Gramática de entidades/verbos reusa proteção e
  núcleo canônicos; executor valida turno vigente, fala e parâmetros; corpo
  usa o único owner serial. Reexecução declara direção/PWM/duração na política
  compartilhada e exige novo pedido. Contexto transitório, aprendizado real
  em SQLite temporário, catálogo vivo e documentação recuperada no prompt
  tiveram provas instaladas; consulta de capacidade não aciona a ponte.
- Negociação MCAPS não movimenta. Padrão PWM255/até250ms, limite500ms;
  MACK confirma PWM e SACK correlaciona corte. REDs de STOP aguardando MACK
  por0,501s, cancelamento como sucesso e mistura de sessões foram reproduzidos
  antes do patch. Espera cancelável, estado cancelado e identidade da porta/
  sessão encerram esses REDs. Painel diagnóstico quebrado não muda receipt.
- Glitch: RED instalado atingiu ResultadoAcao negativo publicado, mas owner
  não tinha sinal; bool de tratado e estado_final sozinho foram falsificados
  como prova de falha porque também representam recusa/pendência. Owner de
  atividade observa receipts aceitos de origem executor e exceções, com
  identidade/timestamp processuais válidos2s. Recusa, cancelamento, plano,
  retorno bool, ausência de receipt e publicação recusada ficam neutros.
  Wrappers sem status tipado seguro continuam neutros, não inferem pela fala.
- GCAPS/GLITCH exigem FACE, seq e TTL próprios; GACK pós-frame/probe/clock.
  Falha visual consumida antes de enviar, sem replay. Ausência I2C descoberta
  no handler deixou efeito anterior vivo: RED→GREEN na invalidação comum da
  sessão, overlays e motores. Motor0 padrão e motor1 explícito preservados.
- Boca: senoide com curvas emocionais duplicadas causava contorno torcido;
  candidato mantém boca fechada, suaviza curva ao abrir, varia largura/aberturas
  e insere pausas. Hosts de ambos perfis, raster e regressivos de morph/motor
  passaram. É animação por `falando`, sem análise de fonemas.
- 425 regressivos relevantes + 22 subtests GREEN; 53 testes corporais GREEN,
  incluindo composição/receipts independentes/falha parcial/autoria única,
  segurança, repetição, aprendizado e prompt. Expectativa lexical do composto
  rejeitou "a ação não confirmou direito": aviso legítimo, corrigido no teste
  junto de assert do receipt negativo, sem modificar o composer.
- C3/core3.3.12, motor1, 387.950/15.836bytes, COM4/MAC conhecida e flash com
  hash verificado. Fonte `.ino` SHA256:
  `7fccfad8e05c8f3ce397961d56e11f8507c351ca9fb202658f7176f83b4d2425`.
  Composição instalada/classificação/arbiter/executor/USB reais: quatro
  MACK+SACK, parada explícita e GACK de exceção controlada de demonstração.
  Não foi falha de habilidade externa real nem entrega por voz/interface.
- Pedro: boca **"Sim, ficou melhor"**; primeira sequência motora não
  acompanhada, repetição **"Sim, giraram e pararam"**; DEMO_GLITCH
  **"Sim, ficou legal"**. Receipts separados em
  `artifacts/rosto_oled/glitch_boca/`. STOPPED+READY encerraram demos/tração;
  placa aguardando Laylay no sono. Sem prova de deslocamento ou precisão elétrica.
- Movimento espontâneo permanece fora do verde manual: governança/iniciativa
  atual só admite domínios seguros existentes e o executor presume efeito
  reversível. Pulso contrário não prova restauração da posição. Novo modo
  corporal precisa contrato próprio de vigência, revogação e oportunidade.
  RED musical de coerência de capacidade foi reproduzido com owners do HEAD
  em RAM, permanecendo preexistente e fora desta melhoria.

### Transporte do corpo pela rede local — 11/10/2026

- Base main/2566b621d2c8ee88ff7086c6c36019da85c8a4cd preservada; nenhum commit.
  Melhoria autorizada por Pedro: servidor local no C3 conectado ao roteador,
  mantendo o PC na rede atual. Primeira fronteira ausente reproduzida: factory
  ignorava configuração TCP e ino recusava WIFI_STATUS. Não fundir com o RED
  elétrico histórico, expressividade ou autorização de movimento espontâneo.
- Mesmo owner RostoOledRuntime/sessão/receipts para USB e TCP; firmware vincula
  owner também ao endpoint. AUTH precede HELLO e não autoriza tração. Handoff
  corta, ACKs assíncronos seguem apenas o dono; STOP estrangeiro corta sem SACK.
  EOF, FACE vencido, overflow, Wi-Fi perdido e TX congestionado invalidam.
  Socket não bloqueante com orçamento; peer sem FIN expira para permitir nova
  conexão. Reconexão recebe estado atual, nunca repete MOTOR.
- Configuração via janela/USB, segredo local NVS; JSON pessoal ignorado guarda
  apenas endpoint/token e só é ativado após AUTH+ACK+SACK. IPv4 cacheado requer
  reconfiguração caso DHCP mude. Configuração inválida falha sem fallback USB.
- 462 testes Python +22 subtests GREEN; hosts Wi-Fi e regressivos visuais/motor
  GREEN. Teste Windows de backpressure inicialmente não alcançou congestão
  por buffering; passou ao preencher a fila em escritas limitadas e medir a
  escrita efetivamente bloqueada. GUI Esc/fechar durante worker: RED→GREEN.
- C3/core3.3.12/motor1: programa1.089.095/RAM41.360; COM4 com hash da flash
  verificado. Evidências em artifacts/rosto_oled/wifi. Duas janelas simultâneas
  detectadas durante configuração, encerradas pelo usuário; uma reaberta.
  USB confirmou CONNECTING, sem confirmação LAN ainda. Software/flash verdes
  não provam associação Wi-Fi, giro, óptica ou entrega natural no runtime.

Continuação física da mesma fronteira: senha/nome conferidos pelo usuário,
CONFIG aceito/STATUS CONNECTING. Consulta sem segredo WIFI_DIAG reproduziu
STATUS6/REASON2 (AUTH_EXPIRE). Callback atomicamente guarda código, sem manipular
GPIO/I2C; novo host/compile/flash verificados. Perfil experimental TX8,5dBm e
antena reposicionada/reconectada pelo usuário continuaram REASON2. Build atual
1.090.491/41.368bytes; recibo atualizado e controles preservados separadamente.
Não declarar senha errada, servidor defeituoso ou causa elétrica sem evidência.
Próximo controle: associação a outra rede2,4GHz, mantendo PC na rede atual.

Controle executado: Pedro confirmou associação no hotspot2,4GHz, e placa
confirmou CONNECTED/IP10.68.192.221/STATUS3. Teste somente de associação não
salvou JSON de controle; PC preservou Wi-Fi original e não alcançou TCP8765 do
hotspot. Não movimentou motores nem alegou ACK/SACK da rede. Incapacidade geral
da placa associar foi falsificada; problema específico da conexão original
continua em investigação. Modelo/configuração do roteador solicitado.

Pedro esclareceu que a rede original usa repetidor e que o celular está nela.
Isso não demonstra a causa de AUTH_EXPIRE nem confirma alcance LAN até o
hotspot. Próximo teste proposto: associação ao SSID2,4GHz do roteador principal
com PC permanecendo no repetidor, seguida de alcance TCP e receipts reais.
Disponibilidade da rede principal e modelo do repetidor solicitados; não
alteradas configurações do roteador/repetidor nem rede Wi-Fi do PC.

Continuação 11/10/2026: rede principal fora de alcance; Pedro autorizou rede
local no PC. Hotspot móvel: erro humano "nao e possivel configurar o hotspot
movel"; driver Broadcom7.35.143.112 não oferece Wi-Fi Direct GO. Hosted Network
antigo iniciado pela API StartUsing, sem elevação, manteve SSID/BSSID/canal da
conexão original. Primeiro controle: ESP autenticado no AP, mas sem IP/UDP67.
Consulta elevada ICS confirmou nenhuma conexão compartilhada; rede do teste
encerrada e somente SharedAccess parado. Novo Hosted Network iniciou DHCP,
ESP192.168.137.52 respondeu ping e servidor confirmou AUTH/READY/ACK/SACK.

Contrato do provisionamento: IP não é readiness do servidor; repetir somente
handshake/FACE até três tentativas com1s entre elas, nunca MOTOR, e ativar JSON
somente após ACK+SACK. Runtime real reproduziu dois timeouts800ms seguidos de
handshake confirmado. RED canônico→GREEN com TCP real e owner Python; falha
permanente e SACK ausente continuam sem ativação. Provisão real posterior GREEN.

Primeiro probe instalado executou movimentos com MACK/SACK, mas importava a
composição sem iniciar heartbeat e encontrou sessão expirada antes do glitch.
Preservado receipt RED; nenhum prazo de segurança removido. Probes com o método
executar registrado no supervisor confirmaram também GACK e encerraram serviço
e tração. Pedro confirmou giro/parada dos dois motores e glitch pelo Wi-Fi na
repetição (receipt_fisico_20261011_053230.json). Sem medida de deslocamento/voz.

Scripts Windows monitoram conexão original e guardam credenciais geradas apenas
em arquivo pessoal ignorado. Launcher -HotspotLocal inicia/reutiliza gerente;
encerra somente o processo que criou. Nada adicionado ao boot ou import Python.
Não fundir com causa da associação no repetidor, ainda não demonstrada.
Regressão inicial após ativação encontrou seis testes USB lendo pareamento
pessoal; fixture agora aponta configuração ausente em tmp_path, mantendo suas
asserções USB. Isso isola hardware real, não altera produção para satisfazê-los.
Regressão focada final178 passed/11,48s; três scripts PowerShell com sintaxe
válida. Gerente de rede e serviço Python comprovados na sessão física; launcher
novo não recebeu prova completa de abertura/fechamento da aplicação gráfica.
Nenhum commit criado; firmware preservado, somente NVS de rede provisionada.

### Continuação do corpo móvel — compatibilidade de PWM — 11/10/2026

- Mesmo owner de execução física, sem nova raiz emocional ou autonomia.
  Base main/2566b621d2c8ee88ff7086c6c36019da85c8a4cd; worktree suja preservada.
  O teste contínuo autorizado de 5 s/PWM100 confirmou MACK e SACK, mas Pedro
  observou somente GPIO1/2 girando fraco, GPIO3/4 sem giro. Receipt histórico
  preservado em artifacts/rosto_oled/motores/receipt_continuo_20261011_155528.json.
- Pedro informou funcionamento perfeito com código antigo e autorizou ajuste
  e gravação. Alterou os fios entre os testes e confirmou retorno ao mapa atual:
  GPIO1/2/3/4, SLEEP7, OLED8/9. Logo o comparativo físico não isola frequência
  de contato/pinout; não declara uma causa física única demonstrada.
- Divergência de configuração provada: firmware usava LEDC20kHz/8bits, referência
  usa analogWrite sem override, padrão1kHz/8bits no core ESP32 3.3.12 instalado.
  Parser de duração e perda de transporte não explicam o receipt concluído,
  mas a aplicação de PWM não prova corrente, torque nem rotação.
- Contrato compartilhado: configuração de PWM pertence ao único executor da
  ponte, para todos os comandos/canais; não copiar apenas duty e supor waveform
  equivalente. Menor candidato: frequência única1kHz em rosto_laylay.ino.
  Pinout, sentido elétrico, prazo500ms, STOP e autorização não foram ampliados.
- RED host reproduzido na frequência antes do candidato (assert1000 vs20000).
  Dublê passou a registrar frequência/resolução antes ignoradas. GREEN normal
  e temporário5s: quatroGPIOs1kHz/8bits, ambos canais+/-100, corte e limite;
  regressivos reais do firmware em host: WiFi, IP, perfil0, glitch/boca e visual/
  motor. GPIO e waveform externos permanecem simulados nesses testes.
- C3/core3.3.12, motor1/baixa potência WiFi, build1.092.397/RAM41.416.
  GravadoCOM4/MACac:27:6e:72:ba:70, exit0, hashflash verificado.
  BinSHA2568714a678b27399884484861aa58f3d7ec5e413a6185bfdd75d33e7661911667d.
  Runtime serial instalado confirmou FACE/MOTOR1/SACK, sem enviar MOTOR.
  Receipt: artifacts/rosto_oled/motores/receipt_pwm1k_gravacao.json.
  A melhora de rotação no novo firmware ainda exige observação física.
  Nenhum commit criado; cognição, executores Python e autonomia não alterados.

Repetição autorizada com PWM1kHz/100 e perfil temporário5000ms: build
1.092.399/RAM41.416, COM4/MAC conhecida, hashflash verificado. Um único MOTOR
recebeu MACK, mas o owner perdeu a sessão antes de5s; nenhum replay. SACK final
confirmado. Pedro: "Não giraram" e OLED sempre dormindo durante a tentativa.
Receipt RED preservado: receipt_continuo_20261011_161355.json. Não declarar
frequência como causa física encerrada. Firmware normal1kHz/500ms restaurado,
upload exit0/hashflash confirmado, mesma binSHA acima.
Controle sem MOTOR10s: um timeout de autenticação inicial,27/40 amostras FACE
confirmadas depois; SACK confirmado. ARP do IP192.168.137.109 corresponde ao
MACac:27:6e:72:ba:70 da COM4, falsificando alvo diferente nessa consulta.
Controle visual posterior30s sem MOTOR: Pedro confirmou "Abriu os olhos e
está piscando". Prova visual do rosto sem tração, sem atribuir a queda da sessão
na tentativa motora a WiFi, alimentação, firmware ou GPIO sem mais evidência.

Nova repetição5s autorizada após Pedro relatar teste na bateria sem reinício:
mesmo perfil1kHz/PWM100/5000ms, MAC/COM4 e binária temporária verificados.
Laylay/MonitorSerial fechados para um owner. O probe passou a registrar a
primeira falha de transporte e duração até interrupção, sem novo parser ou
reenvio de MOTOR. Primeiro receipt_continuo_20261011_162628.json: um comando,
MACK, janela5.279s no host, SACK, zero falhas; Pedro não acompanhou.
Após nova autorização "Estou olhando; pode repetir agora", segundo receipt
receipt_continuo_20261011_162746.json: um comando/MACK, janela5.066s no host,
SACK, zero falhas. Pedro confirmou "Sim, giraram e pararam sem reiniciar".
GREEN físico pontual de ambos motores/parada percebida neste teste contínuo;
não mede corrente/temperatura/torque/duração elétrica nem deslocamento.
Firmware normal1kHz/500ms restaurado entre e após os testes, upload exit0 e
hashflash confirmados. A causa da queda anterior não foi isolada: alimentação,
contatos e estado de clientes diferiram. Nenhum patch no firmware neste turno.

Teste de transporte USB solicitado por Pedro,11/10/2026: factory existente
prioriza LAYLAY_ROSTO_PORTA=COM4 sobre pareamentoWiFi. Nenhum patch de produção
necessário. Factory/serial física confirmou FACE,MOTOR1,SACK, sem MOTOR.
Launcher existente iniciar_laylay_com_rosto.ps1 -Porta COM4 abriu a Laylay real
(PIDlauncher29412); seleção herdada só pela sessão, pareamentoWiFi preservado.
Processos da Laylay observados sem conexãoTCP ao corpo8765 nessa consulta.
Pedro confirmou "Sim, abriu e o OLED acompanha". Receipt em
artifacts/rosto_oled/motores/receipt_usb_sincronizacao.json. Prova da conexão
e saída visual na aplicação aberta; nenhum novo acionamento motor neste teste.

Companhia corporal V1 por USB — 11/10/2026, autorização de Pedro para começar
a implementação mantendo a configuração testada. Base: main/2566b621d2c8ee88ff7086c6c36019da85c8a4cd;
worktree paralela preservada, nenhum commit. Owner da concessão efêmera:
autonomia/companhia_corporal.py; gramática/autoridade/resultado continuam
canônicos. CORPO_COMPANHIA ativa somente com declaração de bancada, área
delimitada ou rodas suspensas, sessão USB pronta e operador atual. Começa OFF;
30min/30gestos, PWM100/100–180ms, intervalo20s; STOP, pedido manual, perda de
sessão, falha e expiração revogam sem rearme/replay. Percepção escolhe gesto,
não fornece permissão. Reação usa o mesmo retrato causal do OLED e início da
fala; não interpreta ambiente físico nem navega sem sensores.

Fronteiras comprovadas: RED da operação/catalogação ausente antes do patch;
concessão revalidada nas etapas e dentro do lock serial imediatamente antes
de MOTOR. Rosto confirmado não empresta sucesso a motor sem MACK/SACK.
Plano cooperativo admite efeito não idempotente somente com proibição
explícita de reexecução e CAS de início da ocorrência; disputa concorrente
não chama o executor duas vezes. Autorização por escopo é registrada pela
composição, nunca obtida de texto/metadados do plano. Receipt automático não
é preferência humana aprovada. Essas guardas são contratos compartilhados,
não exceções para um motor. Catálogo preserva disponibilidade por capacidade;
consulta geral de habilidades não pode ser consumida pelo corpo/OLED.

Produção alterada nesta V1: companhia/corpo/porta serial, gramática corporal e
verbos canônicos, executor/classificação/coordenador/roteador corporal,
governança/quadro/executor/orquestrador cooperativos e ponte de aprendizado,
catálogo/mapa/disponibilidade/continuidade, composição de serviços e ligações
em laylay.py. Sem alteração de pinagem, frequência, polaridade ou limite500ms
da fonte do firmware. Perfil compilado: WIFI=0 e MOTORES_BANCADA=1, rádio fora
da binária; C3/core3.3.12, 391.048 bytes/RAM17.380. UploadCOM4 exit0,
MACac:27:6e:72:ba:70, hashflash verificado. BinSHA256
0f7e0e0dcf238337e65b7a1de817077bb0516cb1c7e41a1e9f4da58a88bab245.

GREEN:275 testes focados,128 vizinhos de catálogo/continuidade/aprendizado e
seis verificadores do firmware real em host (GPIO/I2C simulados). Nova
capacidade percorre composição instalada com owners reais e porta física
dublê, publica receipt/aprendizado e chega ao catálogo/pergunta natural.
Composição real consultou a COM4: FACE/MOTOR1/SACK confirmados, owner corporal,
thread e coordenador corretos, modoOFF, nenhum MOTOR. Receipts:
artifacts/rosto_oled/usb_companhia/receipt_instalacao.json e
receipt_composicao_real.json. Laylay fechada a pedido de Pedro e reaberta pelo
novo iniciar_companhia_usb.ps1; Pedro confirmou interface aberta e OLED
acompanhando. Gestos novos ainda sem prova física humana: não considerar a
autonomia corporal globalmente validada, nem inferir alimentação sem quedas.

Regressão ampla revelou um RED distinto preexistente: explicação informativa
de retomada musical rejeitada como resultado_operacional_sem_evidencia,
também reproduzida mantendo a guarda documental anterior em memória. Não
alterar guardião de fala para mascará-lo. Um agrupamento de testes com root
Python importado antes da fixture USB também expôs cache/configuração de
root; processo focado com fixture antes da composição passou. Não confundir
esse estado do harness com uma desconexão física.

Companhia corporal — extensão expressiva autorizada em 11/10/2026. Pedro
pediu referências do Cozmo e depois mais liberdade. Mesma base main/2566b621d2c8ee88ff7086c6c36019da85c8a4cd,
120 itens na worktree antes desta extensão; preservados, sem commit. Esta é
uma evolução do owner corporal existente, não outra raiz para o mesmo mecanismo.
Referências consultadas: apresentação Anki/GDC "Cozmo: Animation Pipeline for
a Physical Robot" e fonte primária do SHARE Lab expressive_cozmo_behaviors.
Foram lidos os códigos de happy, sad, angry, frustrated e amazed, não afirmada
observação dos vídeos. Perfis próprios combinam antecipação, reação, pausa e
acomodação; velocidades, ângulos e código de outro robô não foram transplantados.

Primeira fronteira da melhoria: seletor convertia expressão em um único
movimento, com surpresa e vergonha idênticas. Concessão, rosto e transporte
passavam nos controles internos; cinco REDs chegaram ao executor e mostraram
ausência de sequência, receipt independente e revalidação entre movimentos.
A pedido posterior de Pedro, removidos os limites de 30gestos/30min; concessão
agora vale até revogação na mesma sessão USB, intervalo2s, até quatro movimentos,
PWM100, cada comando50–500ms, motor total<=1500ms e partitura planejada<=2400ms.
Plano5s inclui a espera por receipts; watchdog500ms do firmware preservado.
Não cria navegação sem sensores nem ativa o modo automaticamente.

Contrato: autoridade/correlação revalidada antes de cada efeito; MACK e SACK
independentes antes de continuar. STOP acorda pausas sem lock serial, falha
parcial não herda sucesso e nenhuma sequência é reenviada. Causa substituída
interrompe o gesto antigo sem glitch nem revogar a sessão ainda válida. Falha
real simultânea à nova emoção continua revogando e comunicando o erro.
Propostas ainda expiram em5s; permissão de sessão não autoriza proposta antiga.
Esse princípio é o contrato geral de sequências compostas, aplicado ao owner
corporal e ao coordenador canônico, sem parser ou segundo executor privado.

Produção alterada nesta extensão: companhia_corporal.py, orçamento de
executar_gesto_corporal em orquestracao_cooperativa.py, explicações no
executor_corpo.py, mapa_habilidades.py e capacidades.py. Gramática, pinagem,
PWM1kHz, polaridade e firmware mantidos. GREEN312 testes focados e128 vizinhos,
incluindo composição instalada, aprendizado/catálogo, todos os perfis,
intensidades, cancelamento, falha parcial e perda de USB. COM4 real confirmou
FACE/MOTOR1/SACK com composição nova, modoOFF e nenhum MOTOR enviado.
Receipt e verificador reexecutável: artifacts/rosto_oled/gestos_expressivos/.
O primeiro comando de consulta entrou no Python interativo por erro de pipe;
processos identificados e encerrados; consulta refeita por script salvo.
Laylay reaberta com novo código pela USB. Aparência e deslocamento físico dos
gestos novos ainda sem observação humana; não declarar essa fronteira encerrada.

Companhia corporal — preferência de início autorizada em 11/10/2026.
Pedro pediu manter companhia na bancada ativada e encerrar a Laylay para
abri-la pessoalmente. Base: main, HEAD2566b621d2c8ee88ff7086c6c36019da85c8a4cd,
worktree com121 entradas pré-existentes, preservadas; nenhum commit criado.
Extensão do mesmo owner: configuração humana persistida permite uma nova
concessão somente após USB/FACE/MOTOR1 confirmados e coordenador instalado.
Não cria fala fictícia nem autoridade a partir de emoção, contexto ou aprendizado.
STOP, falha, movimento manual e perda da sessão consomem a ativação automática
nessa execução; nova abertura volta a ler a preferência. Passeio segue separado.

Primeira fronteira de persistência RED: escrita parcial do serviço canônico
apagava outras chaves gerenciadas. RED reproduzido com modelo e mascote;
candidato altera somente chaves presentes na atualização, servindo todas as
preferências existentes. Configuração de corpo salva pelo mesmo serviço,
com releitura e comparação das demais chaves, sem exibir valores confidenciais.

Produção nesta extensão: configuracao_aplicacao.py, companhia_corporal.py,
corpo_motor_runtime.py, seleção preferencial USB da factory rosto_oled_runtime.py,
injeção da preferência em laylay.py e descrição em mapa_habilidades/capacidades.
Firmware, pinagem, PWM, protocolos e limites dos motores mantidos.
364 regressivos GREEN; composição instalada, cooperação, conhecimento da
capacidade, espera por USB, parada antes/durante/depois da ativação, falha e
reconexão cobertos. Duas contaminações de fixture foram separadas: import
da composição carrega modelos no ambiente e deixa o root em cache com
pareamento pessoal. Configuração e pareamento foram isolados nos testes;
nenhuma guarda de produção enfraquecida.

COM4 real: composição padrão leu preferência salva, selecionou serial,
confirmou sessão e ativou companhia sem passeio nem comando MOTOR. STOP
recebeu SACK e ticks posteriores não rearmaram. Prova reexecutável e receipt:
artifacts/rosto_oled/companhia_automatica/. Verificação não abriu interface;
processos da sessão anterior encerrados, aplicativo deixado fechado.
Essa prova é do início/autoridade/transporte, sem nova observação física
de movimentos. Preservar a investigação separada de gesto_nao_confirmado
na aplicação completa; o teste anterior da composição não encerra essa raiz.

Continuação da mesma preferência — passeio automático, 11/10/2026.
Sintoma de Pedro: abriu a Laylay e ela não passeava. Primeira fronteira
demonstrada por configuração/código: preferência anterior concedia companhia,
mas o owner recebia passeio=False; silêncio não podia conceder outro escopo.
Pedro autorizou explicitamente iniciar também o passeio na área com barreiras.
Sem mudar essa guarda, acrescentada preferência tipada e persistida de passeio,
dependente da companhia, injetada no mesmo owner/coordenador. Primeira sequência
após8s de sessão USB pronta; STOP/falha/reconexão continuam sem rearmar na
mesma execução. Configuração antiga sem a nova flag permanece só com gestos.

Base mantida: HEAD2566b621..., main,123 entradas de worktree pré-existentes.
373 regressivos GREEN, incluindo composição para as duas preferências,
espera inicial, barreira TCP, cancelamento antes/depois de iniciar e preservação
das demais configurações. Fixture TCP isola agora a preferência USB pessoal,
pois o root real a lê do arquivo; contrato de transporte não foi enfraquecido.
Configuração real salva com ambas as flags1 e comparação das outras chaves.
Composição padrão/COM4 real iniciou passeio, executou avanço e giro com receipts
independentes, recebeu parada/SACK e não rearmou. Pedro confirmou fisicamente
"Sim, andou, girou e parou". Artefato receipt_passeio.json e comando reexecutável:
verificar_inicio.py --passeio, em artifacts/rosto_oled/companhia_automatica/.
Aplicação deixada fechada para Pedro abrir. GREEN físico dessa sequência;
não confundir com validação prolongada da UI ou encerrar a outra falha de
gesto_nao_confirmado observada anteriormente na aplicação completa.

Teste local de som do corpo — 11/10/2026. Pedro autorizou apenas um bip
de2s ao iniciar ESP, usando falante8Ω/~0,2W, capacitor6,8µF/200V e resistores.
GPIO6 confirmado livre no firmware; mapa dos motores/OLED mantido.
Base main/HEAD2566b621...,151 entradas de worktree existentes, preservadas.
Contrato finito no firmware: um início por boot, PWM1200Hz/8bits/canal4,
corte por millis em2000ms e GPIOLOW, sem bloquear loop ou reenviar; nenhum
novo comando de movimento/autorização. Canal e frequência diferentes dos
motores evitam mudar o timer de1kHz, conforme core3.3.12 inspecionado.

RED canônico de ausência do comportamento, candidato mínimo em .ino,
stub de API LEDC e validar_bip_inicio.cpp. Ambos perfis host passaram corte,
sem repetição, falha fechada e preservação dos motores; regressivos de
handshake/motor/STOP/glitch/boca passaram. Build core3.3.12=392038/17388bytes,
USB sem Wi-Fi/motor1, COM4 gravada com hash verificado. Fontea9ff51fc...a0294,
bin396bbc73...56f58f. Consulta real confirmou MOTOR1/SACK e BEEP_TEST STOP,
sem movimento enviado nem abertura da Laylay.

GREEN de software/transporte NÃO é GREEN auditivo: Pedro não acompanhou o
primeiro boot, pediu repetição após mudança na montagem, depois declarou
"em nenhum teste eu ouvi". Não repetir sem nova informação nem diminuir
resistor por tentativa. Pedro informou resistor220Ω (diferente dos1kΩ
propostos); identificação de GPIO, capacitor/polaridade e fileiras ainda
pendente. Não há medida do PWM/tensão nem prova de causa elétrica única.
Próxima fronteira é saída física/montagem/falante; raiz permanece aberta.
Artefatos e consulta sem reset: artifacts/rosto_oled/bip_inicio/.

Controle físico seguinte: Pedro confirmou a ligação completa, incluindo
GPIO6, resistor de 220 Ω, polaridade e fileiras distintas do capacitor.
Depois retirou somente o capacitor, mantendo GPIO6 → 220 Ω → falante → GND.
Um novo reset pela COM4 foi concluído; a consulta recebeu BEEP_TEST 1 STOP
e confirmou READY/MOTOR1/SACK, sem comando de movimento. A observação
auditiva desta ligação está pendente; aceitação da API e término do teste
não provam sinal elétrico nem som no falante.

Resultado humano do controle sem capacitor: "Não ouvi nada". A retirada
do capacitor não restaurou o som; isso enfraquece a hipótese de ele ser
a única causa. Inspeção do .ino não encontrou outro writer do GPIO6;
o início usa ledcAttachChannel/ledcWrite e o término desliga o mesmo pino.
Permanece sem prova elétrica na saída e sem prova de integridade/contato
do falante. Próxima evidência útil: montagem física, antes de mudar pinos
ou aumentar a corrente. Nenhuma nova gravação ou movimento neste controle.

Pedro informou ter localizado um problema de solda no ESP e estar
reparando-o. A preparação de um teste alternativo por GPIO foi interrompida
antes de criar/gravar outro firmware. Causa física relatada pelo usuário;
som após o reparo ainda não observado. Novo pedido: estudar alternativas
de volume preservando o falante de 8 Ω/~0,2 W, sem alterar código agora.

Teste em ponte autorizado depois: GPIO6 -> 220 Ω -> falante -> GPIO5,
sem capacitor/GND no falante. Perfil explícito LAYLAY_SOM_PONTE=1;
canais4/5 e timer1200Hz, saída5 invertida. Host reproduziu RED na ausência
do segundo GPIO antes do candidato (assert pinosPwm[5]); candidato .ino
passou nos quatro perfis simples/ponte e motores0/1, corte, ausência de replay
e falhas da segunda saída/inversão. Regressivos de rosto/USB/motores/glitch/
boca passaram. Build392342/17388bytes, COM4 gravada com hash verificado:
fonte2a7daad0...fdcb0d6, binárioe07b86dc...1890b57d.
Após não acompanhar o boot de gravação, Pedro acompanhou a repetição e
disse "e esta muito bom ja". Evidência humana positiva de som; não há medida
de potência, volume comparativo ou forma de onda. Consultas confirmaram
READY/MOTOR1/SACK; perderam o log inicial/STOP do bip durante a reconexão USB.
Nenhum comando de movimento enviado. Registros individuais em bip_ponte/.

Pedido seguinte: retornar à configuração com apenas GPIO6. Pedro confirmou
USB/bateria desligadas durante a troca, GPIO5 removido, falante no GND,
resistor220Ω mantido e USB reconectada. Baseline main/HEAD2566b621...,153
entradas dirty preservadas, fonte2a7daad0...fdcb0d6. Retorno por perfil de
build LAYLAY_SOM_PONTE=0; candidato de ponte permanece opt-in no fonte,
compilado fora deste perfil. Host simples/motor1 passou; gravação e
observação auditiva do perfil restaurado pendentes neste ponto.

Retorno concluído no dispositivo: build simples392136/17388bytes com
LAYLAY_SOM_PONTE=0, COM4 gravada com hash verificado. Binárioea1ef2a0...
ca4dcea0; fonte2a7daad0...fdcb0d6 preservada, GPIO5 compilado fora do som.
Consulta USB real confirmou READY/MOTOR1/SACK sem movimento; o bip inicial
não foi capturado pela serial. Registro individual em bip_gpio6/.
Resta apenas observação auditiva humana deste perfil, sem declarar volume
igual ao da ponte. Laylay permanece fechada, nenhum commit criado.

Observação auditiva do retorno simples concluída: Pedro não acompanhou
o boot da gravação; após um único reset adicional pela COM4, respondeu
"Sim, ouvi" ao bip de2s com apenas GPIO6. Consulta após reset confirmou
READY/MOTOR1/SACK, sem movimento. Receipt bip_gpio6/
receipt_firmware_20261012T003021_421323Z.json atualizado com confirmação
humana. Retorno ao perfil simples validado no dispositivo e por audição;
isso não mede potência nem valida fala/sons integrados à Laylay.

Expressão diária com olhos e bips — 11/10/2026. Pedro pediu integração dos
sons, retirada da boca e da sincronização com voz no OLED. Escolheu bips
ao acordar, em sucesso/falha e mudanças marcantes de emoção. Base main,
HEAD2566b621...,153 entradas dirty e fonte2a7daad0...fdcb0d6 preservadas.
Inventário: RostoOledRuntime possui a sessão; composição liga os getters
de estado emocional e AtividadeOperacionalRuntime; este já publica sucesso
certificado e falha observada, com IDs/TTL e proteção de lotes parciais.
Não criar parser de fala nem outro owner de resultados/emoções.

Contratos: saída passiva nunca autoriza ação/motor nem confirma receipt
externo. Seleção de som reutiliza as projeções canônicas, consome antes de
enviar, limita intervalo e descarta excesso sem fila/replay. SOM1 opcional;
firmware antigo conserva FACE. SOUNDACK confirma aceitação/início, nunca
audição. Firmware valida sessão/FACE, sequência, tipo, corte absoluto até450ms,
pausas em LOW e desligamento por perda da sessão. Todos tons têm frequência
diferente de1kHz dos motores e usam canal4. GPIO6/220Ω/falante/GND mantidos.
Boot normal deixa de emitir bip de2s; despertar é um par curto na primeira
conexão por processo. O diagnóstico histórico de2s fica em build opt-in.

RED antes do candidato: 5 testes alcançaram voz ainda transmitida, ausência
de SOUND e diagnóstico. Candidato: .ino/som_expressivo.h, RostoOledRuntime,
catálogo/disponibilidade. Boca e cálculo silábico removidos, campo legado
FACE sempre zero na Laylay. Regressão encontrou um acoplamento vizinho:
CompanhiaCorporal lia fala pela projeção do OLED. Corrigido na fronteira
compartilhada: gesto lê is_speaking na mente; seu gate confere olhos causais
e concessão existentes, sem exigir que voz seja transmitida ao OLED.

11 novos testes passaram incluindo composição instalada/executor, catálogo
e lote parcial; 43 rosto,112 grupo rosto/transporte/atividade/Wi-Fi,171
companhia/comemoração/motores e42 falha visual passaram por lotes (336
únicos). Host: handshake/motores/STOP/hack/glitch/olhos/som/diagnóstico
histórico passaram. Raster das9 emoções sem boca e invariância com fala
legada confirmados. Testes antigos de boca foram atualizados para proteger
o novo contrato solicitado, mantendo os gates vizinhos.
Suite única:335 passed/1 failed por estado residual VOLUME42 chegando à
repetição de última ação no teste de companhia. Controle reproduziu a mesma
falha apenas com teste de falha visual + companhia, sem novos testes de som;
companhia isolada passou. Registrado como interferência de estado entre
testes; não patchar contrato de repetição nem declarar regressão ampla verde.

Build USB core3.3.12:390814bytes flash/17372globals, COM4 gravada com hash
verificado. .ino a95c8225...185d1df; som75d7941d...cd6000; binário5dbeab09...
e5e7930. Comparação do header compilado difere apenas do #line inserido pela
CLI. Prova física usando a composição de produção:9 emoções e melodias,
sem MOTOR. Primeiro ensaio terminou com timeout numa melodia final; não
houve causa demonstrada. Observabilidade específica adicionada para recusas
SOM; repetição confirmou12 passos e ambas melodias. Não promover a hipótese
de cooldown a causa provada. Padrões sucesso/falha deste ensaio são demos,
não receipts fabricados de ações externas.
Pedro confirmou "Sim, só olhos e ficou fluido" e "Sim, ficaram fofos".
Aplicação permanece fechada para o usuário abrir; uso prolongado pela UI
normal ainda não observado. Artefatos/receipts/preview em som_olhos/,
instruções SOM_OLHOS.md, nenhum commit, nenhum motor enviado nesta validação.

Rebuild final gerou bináriof2c53092...cb9f48 com os mesmos fontes e header
compilado normalizado conferido; esse binário foi gravado novamente na COM4
com hash verificado. Consulta final confirmou READY/SOM1/MOTOR1/SACK. O hash
5dbeab09... anterior identifica o binário da demonstração aprovada, não o
arquivo atual sobrescrito pelo rebuild. Receipt_build mantém ambas identidades.

Refino visual dos olhos — 11/10/2026. Pedido: expressões mais bonitinhas.
Base main/HEAD2566b621...,155 entradas dirty; fontea95c8225...185d1df
salva em olhos_fofos/rosto_antes.ino antes de alterar. Owner é o renderizador
no firmware: mesma emoção/nivel recebidos, nenhuma nova interpretação,
autorização, mudança de bips ou movimento.
Candidato mínimo apenas no .ino: contorno dos olhos arredondado pela altura,
arco alegre mais macio/espesso, pálpebra brava menos cortante, bochechinhas
compactas em alegria/vergonha e duas estrelas pequenas em alegria/surpresa.
Brilho e rubor interpolados pela mesma dt; brilho some no sono. Sem boca.
Preview raster das9 poses inspecionado; 100 transições passaram (maior
primeiro passo210pixels), primeiro passo calma/alegre142pixels. Regressivos
host de sessão/STOP/motores/hack/glitch/olhos/bips passaram; nenhuma mudança
Python ou de mapa de pinos. Compilação/gravação e apreciação física pendentes.

Gravação do refino concluída na COM4:391220bytes/17380globals, hash esptool
verificado, fonte2b53bc43...353f959, binário2826889b...fede193. Laylay que
estava aberta foi encerrada pelo CloseMainWindow do terminal; seus processos
saíram, liberando a serial. Nenhum encerramento genérico de Python aplicado.
Consulta final confirmou READY/SOM1/MOTOR1/SACK. DEMO local foi ativada para
apreciação das poses, sem MOTOR; abrir a aplicação substituirá a demo pelo
handshake normal. Observação visual humana do refino ainda pendente.
Receipt e preview em artifacts/rosto_oled/olhos_fofos/. Nenhum commit.

Pedro relatou ausência de passeio após esse refino. Primeira fronteira
observada: nenhum processo normal laylay.py/terminal/avatares estava aberto;
somente probes e testes independentes. Preferências de companhia/passeio
em configuracao.env continuam1; ESP tinha sido deixado em DEMO visual.
Isso sustenta ausência do controlador de movimento, não defeito dos motores.
Reabertura autorizada pelo pedido de retomar passeio: Start-Process Hidden
da .venv314 com -u laylay.py, PID15912/core28940, terminal/avatares reais
iniciados; log confirma ponte de terminal autenticada. Nenhum arquivo de
produção/preferência alterado nem testes paralelos encerrados. Observação
humana do passeio retomado pendente; logs app_reaberta_* em olhos_fofos/.

### RV-TTS-403-01 — transporte neural recusado — 12/10/2026

Base: main, HEAD 2566b621d2c8ee88ff7086c6c36019da85c8a4cd, worktree
paralela preservada; voz_runtime.py e test_voz_configuravel.py sem diff prévio.
Primeira RED: handshake WebSocket do endpoint legado do edge-tts 7.2.8,
HTTP 403 antes de produzir áudio, reproduzido fora da aplicação nas vozes
Francisca e Thalita. Ambas presentes no catálogo (322 vozes); texto curto
também falha. Relógio cerca de 5,5s do servidor. Timeout Ollama é outra raiz.
Controle causal: apenas endpoint/chave de query novos → duas sínteses válidas.
Referência de transporte: https://github.com/rany2/edge-tts/pull/491.

Owner: criação da comunicação neural no runtime compartilhado de voz.
Contrato: corrigir somente o transporte legado conhecido, preservar vozes,
parâmetros e endpoints futuros/personalizados; erro continua dependendo de
fallback e reprodução confirmada. Beneficia todos os domínios que usam a voz.
RED canônico: 2 failed/9 passed por endereço antigo. Candidato mínimo em
voz_runtime.py; nenhum pacote global/configuração/LLM/pyttsx3 alterado.
GREEN final: 92 testes de voz, guardião, filas e avatar. A biblioteca real
normaliza nomes curtos de voz; expectativa do teste ajustada ao controle
canônico, mantendo identidade da voz e parâmetros. Testes usam a factory
de produção e biblioteca real; endpoints personalizados são preservados.

Prova com rede, runtime de voz e player reais: Thalita e Francisca retornaram
True em reproduzir_fala, saída Realtek padrão, fallback local proibido no
ensaio. Confirmação de software, não apreciação acústica humana nem main
completo. Aplicação já aberta precisa reiniciar para carregar o candidato.
pyttsx3 também reproduziu IndentationError no cache COM; SAPI gerou WAV válido.
Essa causa concorrente não foi reparada nem fundida com a migração de endpoint.
Nenhum commit criado; raiz ainda aguarda observação na aplicação reiniciada.

### CORPO-DECISAO-V1 — intenção corporal contextual — 12/10/2026

Pedido autorizado: primeira versão ligando atividade no PC e emoção ao corpo,
com movimentos fortes e contínuos na plataforma de rodas suspensas descrita
por Pedro. Base main/HEAD2566b621d2c8ee88ff7086c6c36019da85c8a4cd;
worktree paralela preservada. Baseline dos componentes corporais em
artifacts/rosto_oled/corpo_decisao_v1/baseline/. Nenhum commit.

Primeira fronteira RED reproduzida: o owner de companhia executava gesto
emocional novo mesmo com atividade operacional canônica ativa no PC.
Contrato: contexto determina oportunidade, emoção causal determina estilo,
receipt determina reação; a concessão USB vigente continua obrigatória.
Uma intenção proposta não é autorização nem prova de deslocamento.
Owner permanece CompanhiaCorporalRuntime, executor e quadro cooperativo
existentes. ESP executa planos temporizados e renderiza, sem outra cognição.

Decisor puro novo em cognicao/decisao_corporal.py: atenção tem prioridade
durante tarefa/planejamento/escuta; conversa pode gerar interação; receipt
recente gera comemoração ou reação à falha; mudança emocional causal gera
expressão; disponibilidade com passeio concedido permite exploração.
Intenção transitória publicada na mente com identidade e prazo. Perfil
explícito rodas_suspensas salvo pela configuração canônica, injetado na raiz
instalada; gestos de exploração combinam avanço/giro/recuo contínuos.

Limites antigos foram identificados em ator, transporte e orçamento do plano.
LCAPS/LONGO1 negocia 5000ms; firmware antigo permanece limitado a500ms e
não arma esse perfil. Coreografias longas usam orçamento20s, revalidação
durante o motor e acomodação após conclusão. Novo contexto ou parada corta
o gesto; sem replay. Prazo absoluto do motor e TTL de heartbeat preservados.
O comando manual comum mantém o contrato curto existente; movimentos longos
desta V1 são coreografias do perfil, não interpretação livre de PWM pela LLM.

Falsificação: o tempo mínimo do overlay visual não é execução ainda ativa.
Usá-lo como bloqueio global impedia reação legítima após ativar companhia.
Helper compartilhado projetar_execucao_operacional separa ativos reais da
apresentação; overlay/hack mantém o contrato anterior. Perfil não é inferido
de emoção, de estado restaurado ou de uma alegação de sensores.

GREEN:273 testes focados, incluindo raiz instalada em processo separado,
catálogo vivo/pergunta natural, cooperação rosto→motor, perfil persistente,
contexto e interrupção, firmware antigo, ausência de autorização e parada.
Após salvar o perfil físico,5 testes antigos falharam por ler a preferência
pessoal e usar simulador curto. Isolada somente a configuração externa da
fixture comum (inclusive raiz em cache); expectativas de efeito preservadas.
Nova prova da composição longa permanece independente. Não declarar suíte
global verde; interferências históricas externas a esse recorte permanecem.
Host firmware: LONGO1, rejeição5001, movimento contínuo5s com heartbeat,
corte absoluto e por TTL; regressivos de olhos/bips/hack/glitch passaram.

Build core3.3.12 USB, Wi-FiOFF/motoresON, limite5000; gravado na COM4 com
hash verificado. Fonte133bc235...070462; hashes completos em receipt_build.
Ensaio usando owners/coordenador e USB reais confirmou sequência contínua,
interrupção pela tarefa PC explicitamente simulada e SACK de parada final.
Pedro não acompanhou esse ensaio. Aplicação normal reiniciada com perfil
salvo, companhia/passeio automáticos; Pedro confirmou: "Sim, acompanha e os
motores se movimentam". Aplicação deixada aberta. Tarefa PC do ensaio não
alterou o PC nem fabricou resultado externo. Distância/ângulo/giro360 não
medidos, sem sensores; apreciar todas as emoções no uso prolongado permanece
uma validação humana futura. Receipts e logs em corpo_decisao_v1/.

#### Evolução CORPO-DECISAO-V1 — presença coordenada V2 — 12/10/2026

Pedro autorizou reação rápida, coordenação olhos/bip/corpo e variações. Durante
o trabalho pediu encerrar a aplicação e deixá-la fechada, acrescentando
despertar/adormecer suaves. HEAD/main permanece2566b621..., worktree paralela
preservada; baseline dos8 componentes em presenca_v2/baseline/. Nenhum commit.

Fronteira de oportunidade: entrada/percepção já adquirem claims no owner
PrioridadeInteracaoUsuarioRuntime, mas o corpo não lia esse owner. RED real
de componentes: claim ativo + emoção nova ainda emitia MOTOR. Corrigida
a composição para rosto e corpo lerem a mesma prioridade, antes da LLM;
nenhum parser, claim ou mecanismo de autorização paralelo. Falha de leitura
impede iniciativa. Durante atenção, emoção vigente não é consumida como gesto;
um gesto iniciado cede à nova causa e não é reenviado automaticamente.

Fronteira de apresentação: ECAPS/OLHOS2 e EXPR acrescentam olhar lateral,
antecipação, expressão e acomodação finitas; EACK somente após o frame e
revalidação de OLED/sessão. Não renovam FACE nem autorizam motor. Owner de
companhia coordena os detalhes pelo plano rosto→motor existente, com três
variações por estilo emocional. Uma falha de EACK impede a próxima tração.
Som continua no owner compartilhado, consumido uma vez por ocorrência e
espaçado; no perfil ativo, o gesto chama esse owner na fase expressiva.
Controle negativo reproduziu perda do bip de falha enquanto o corpo estava
ocupado: falha atual não aguarda uma coreografia e não sofre replay posterior.

RCAPS/RAMPA1 negocia MOTOR2 explicitamente. PWM sobe e desce dentro do
mesmo movimento contínuo; MACK2 só confirma o alvo quando realmente aplicado.
MOTOR1 preserva o comportamento anterior. Ambos mantêm duração absoluta,
corte por TTL/OLED e STOP imediato. Regressivo rejeita versão3 desconhecida;
versão2 passou a ser válida por contrato, coberta separadamente. Nenhum
pino, frequência de motor ou potência sonora alterado.

Sono/encerramento: GOODNIGHT invalida a sessão e corta a ponte imediatamente;
interpolação visual termina independentemente. Prova física inicial concluiu
os gestos, mas faltou NACK: shutdown no meio de FACE fechava a serial antes
da despedida. RED canônico reproduzido, corrigido no owner serial; espera
de STOP/GOODNIGHT durante encerramento é limitada e nunca abre nova sessão.
Script de ensaio inicialmente capturava AssertionError sem texto como string
vazia. Artefato incompleto preservado e identificado; diagnóstico agora usa
tipo/mensagem e falha com código1. Não contá-lo como ensaio completo.

Primeira transição exponencial passou no host, mas Pedro observou que ainda
era brusca. Premissa visual rejeitada. Refino final: curva quintica3200ms ao
acordar/3000ms ao dormir, piscada somente após despertar, Zs tardios e
geometria da pose preservada ao adormecer. Índice emocional e sessão continuam
invalidados: preservar desenho não significa manter estado operacional.
Tentativa de preservar índice encontrou proteção antiga legítima; candidato
revisto para conservar somente a geometria, com todos os gates preservados.

GREEN Python:311 testes focados (prioridade, raiz instalada em processo
separado, cooperação, catálogo vivo, dispositivos antigos, falhas/receipts,
parada/shutdown, som, contexto e configuração). Cinco validadores host verdes:
presença, motor longo, rosto/hack, glitch/parada e som/olhos.100 transições
visuais: maior primeiro passo176pixels. PRIMEIRO build do teste de som omitiu
o perfil MOTOR1 exigido pelo ensaio; corrigida invocação, sem alterar teste.
Não declarar suíte global verde nem conclusão de raízes paralelas.

Firmware final core3.3.12, Wi-FiOFF/USB/motoresON/limite5000, flash393764bytes,
globals17436, COM4 com hash verificado. Hashes completos em receipt_build.json.
Ensaio físico com owners/coordenador e USB reais confirmou EACK/MACK2/SACK,
interrupção por claim de entrada explicitamente simulado e NACK final.
Nenhuma ação real no PC nem percepção ambiental fabricada. Pedro confirmou
"Sim, ficou mais expressivo e combinado". Após rejeitar o primeiro sono,
repetição final somente de olhos, sem MOTOR, recebeu "Sim, agora ficou suave".
Aplicação normal permanece fechada por pedido explícito; carregar e observar
a V2 no main prolongado fica para a próxima abertura pelo usuário. Emissão
PWM não mede distância, ângulo ou deslocamento. Artefatos em presenca_v2/.

Produção deste incremento: decisão/companhia corporal, porta do corpo/rosto,
composição em laylay.py, disponibilidade/catálogo e firmware/presenca_expressiva.
Voz, modelo, emoções canônicas e interfaces não receberam patch desta tarefa.

# Coleta pós-caos e diagnóstico das frases pessoais — 14/09/2026

Base main/HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, worktree anterior
preservada. Investigação de dados e replay somente leitura; sem patch de
produção, treino, alteração de pesos ou novo caos.

## Material recebido

- `mente_laylay/debug.md`: 500 linhas, SHA256
  `bea0943957c4aede4dbdea13634d28cf4dc41f8eced1c38083d1808c59942853`.
- Caos `resultados_testes/roteiro_teste_laylay_caos-20260914-102203-349781`:
  267/267 respostas; 46 avaliadas semanticamente, 45 passaram e uma falhou.
  As outras 221 não foram avaliadas semanticamente. Portanto 97,83% não é
  acurácia global. Existem 67 falas envolvidas em repetição, seis confirmações
  indeterminadas e latência p95 de 8,597 s.
- Turno 152: pedido de ligar lâmpada, deixá-la azul e relatar estado.
  Avaliador registra `fala_diz_incerteza_com_resultado_confirmado` e alerta
  `dependencia_externa_nao_confirmada`. É uma investigação de coerência entre
  receipt/avaliação/fala ainda aberta, não prova isolada de falha física da lâmpada.
- Fonte prospectiva passou de 265 para 546 eventos: **281 novos = 267 do
  roteiro + 14 de origem desktop**, todos sem quarentena ou JSON inválido.
  SHA256 `f7cb6c10de4f231a1c7a8905d41ca9c31b3f35678a198b7f95ee72508d38c227`.

Snapshot canônico novo em `memoria/neural/experimentos/coleta_pos_caos_20260914/`.
Fila SHA256 `de6d01423ff4a2bc7644b9c01e7bcd8312fac6ea481c6c5c6a542bebedadc286`.
As capturas anteriores foram conservadas.

## Frases pessoais estão presentes, embora marcadas como teste

As últimas 14 entradas têm origem `desktop` e a conversa
`6e120995-6cd7-4b67-93f7-abfe8b2cfe4f`, distinta da conversa do roteiro.
O usuário declarou que testou suas próprias frases; as entradas coincidem
com o diálogo mostrado em debug. Elas não foram descartadas.

O código de composição injeta `teste_getter` baseado na existência de
`LAYLAY_DIAGNOSTICO_DIR`. Esse indicador de sessão se combina por OR com
`origem=roteiro_teste`; assim uma mensagem desktop pode ter
`teste_declarado=True`. A inicialização do roteiro define a variável.
Isso explica a classificação conservadora da sessão; não transforma uma
frase desktop em texto escrito pelo roteiro. Origem manual declarada,
contexto de diagnóstico e revisão do rótulo são informações distintas.
Preservadas as flags originais, com a declaração do usuário registrada na
proveniência da revisão, sem reescrever os eventos históricos.

## Curadoria explícita

Recorte imutável das posições 533–546 da fila nova, com todos os IDs e contextos
originais, em `memoria/neural/experimentos/revisao_manual_pos_caos_20260914/`.
`fila.jsonl` SHA256
`2efcd8120ccbf7c2e560a57e8ebc70e854094c27b61cd878f568126fd2c1c56e`.
Foi aplicada a revisão pelo componente existente `revisao_encoder.executar`.

| Entradas | Decisão no piloto |
| --- | --- |
| pode abri a steam para mim | APP_OPEN/open/pedido |
| abri a calculadora do windowns | APP_OPEN/open/pedido, ato confirmado pelo usuário |
| abre a calculadora do windowns | APP_OPEN/open/pedido |
| abre a calculadora no windowns | APP_OPEN/open/pedido |
| pode colocar metalica | MUSIC_SEARCH/search/pedido; alvo literal metalica |
| nao abre a calculadora para mim | APP_OPEN/open/recusa |
| preciso que voce pause a musica; pode pausar a musica; pode pausa a musica; pausa a musica | Fora do perfil: MEDIA_CONTROL/pause |
| pode despausar a musica; despausa ela | Fora do perfil: retomada de mídia, incluindo referência contextual |
| preciso que voce nao apague o arquivo antonio.txt | Fora do perfil: recusa de exclusão, não leitura |
| nao coloca anny | Fora do perfil: referente/domínio precisam de desambiguação |

Antes da confirmação, `abri a calculadora...` foi preservada sem rótulo por
poder significar passado. O usuário respondeu **“Era um pedido para abrir”**.
Essa confirmação foi acrescentada em `revisao_confirmada.json`, e a revisão
final aplicada em `resultado_confirmado/`. A primeira revisão e seu resultado
permanecem preservados. A confirmação vale para o ato dessa frase; não é
certificação humana da anotação de todo o lote. Não se deve criar uma regra
global que converta todo `abri` em ordem.

Resultado final: **seis exemplos supervisionados por IA, oito fora do perfil**.
Cobertura: quatro APP_OPEN/pedido, um APP_OPEN/recusa, um MUSIC_SEARCH/pedido.
Zero coincidências literais no roteiro de caos explicitamente comparado;
isso não certifica ineditismo em todas as fontes. Grupo conservador único
para esta sessão: não dividir suas reformulações em avaliações independentes.
Os atos anotados não vieram das respostas da Laylay nem dos receipts.

Fila revisada final SHA256:
`37c0f28f116db7a603822e398d2466488efd353d5d46b64f5f665fb3e42cf833`.
Todos os eventos/contextos foram preservados. Continuam sem partições ou
autorização de fit; faltam seis das nove combinações neste recorte, em especial
relatos e leitura. Há progresso de dados, mas não prontidão integral do piloto.

## Primeira divergência do debug reproduzida

Replay com `classificar_modalidade_turno` e o callback real
`porteiro_acoes.texto_tem_comando_explicito`, sem invocar qualquer executor.
Resultados em `replay_modalidade.json` ao lado da revisão.

| Texto | Resultado atual do classificador |
| --- | --- |
| pode abri a steam para mim | conversa, sem autorização |
| abri a calculadora do windowns | conversa, sem autorização |
| abre a calculadora do windowns | comando |
| preciso que voce pause a musica | conversa, sem autorização |
| pode pausar a musica | conversa, sem autorização |
| pausa a musica | comando |
| pode despausar a musica | conversa, sem autorização |
| despausa ela | comando, referência depende de contexto |
| preciso que voce nao apague o arquivo antonio.txt | conversa, sem autorização; ato de recusa não reconhecido |

O debug de produção mostra a mesma divergência na classificação. A falha
antecede autorização e executor: pedidos com certas formulações modais/
informais caem em conversa. Em 10:49:35 a variante `abre a calculadora...`
observa a janela criada e em foco, servindo de controle interno contra uma
falha geral do executor de aplicativos. `pausa a musica`/`despausa ela` também
chegam à integração musical no mesmo log; seu receipt distingue envio do
estado final do player, portanto não usar esse controle como prova de áudio.

Depois da primeira divergência, a semântica da LLM reconhece `pedido_acao`
em vários casos, mas isso não materializa comando. Nas entradas de pausa,
o log publica frases como `Tá, pausei a música` com `comandos=[]`. Esse é um
**segundo contrato quebrado: confirmação de efeito sem receipt do turno**.
Treinar o classificador não dispensa a correção independente desse contrato.

A negativa de capacidade para Steam/calculadora também é consequência
conversacional a investigar; o controle com a calculadora contradiz uma
incapacidade global de abrir aplicativos. Não atribuir essas falhas ao Qwen
isolado nem declarar que a rede em sombra causou o bloqueio: o primeiro RED
observado pertence ao classificador canônico do turno.

Adicionalmente, o debug registra adiamentos proativos recorrentes e fallbacks
de autoria. O contador `fallbacks_conversacionais=0` do caos não certifica a
ausência dessas outras categorias. São evidências separadas; não ampliar
esta etapa de curadoria para corrigir presença, IoT e personalidade juntas.

Hashes do replay: `modalidade_turno.py`
`811b4ec0d7a0c304f184f1962035d59a670b385224bb2515177e9ef04d2cebd8`;
`porteiro_acoes.py`
`eda5d3cd58e0d50bc0ab29c0f4abec0bf9d95e3f4985cb75cc4c12fcb8623c36`.
Uma primeira invocação de shell falhou por aspas; não foi contada como RED
do classificador. A invocação válida produziu os nove resultados acima.

Próxima fronteira: reproduzir o contrato de pedidos modais/negação/relato com
controles negativos e localizar a regra canônica que perde essas construções.
Preservar ambiguidade de passado, solicitações hipotéticas e perguntas de
capacidade. Investigar confirmação sem receipt como raiz separada. A revisão
de seis exemplos já está disponível para a evolução neural; nenhum deles
foi silenciosamente promovido a avaliação independente ou treino.

## Continuação: pedidos modais e roteamento — 14/09/2026

Base: HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, branch `main`,
worktree já suja. Diffs anteriores de modalidade/normalização e abertura de
site por assunto foram preservados. Nenhum commit criado.

### Contrato e cadeia causal

`fala original → modalidade/autoridade → núcleo operacional → detector → executor → receipt`

A frase histórica `pode pausar a musica` **não tinha interrogação**. Os pares
com e sem `?` são regressivos adicionais: pontuação não é condição necessária
nem suficiente para pergunta ou autorização. `como eu poderia pausar a música`
e `você consegue pausar a música`, mesmo sem `?`, ficaram sem efeito na sonda.

1. Primeiro RED: listas divergentes do classificador não reconheciam as
   molduras modais para vários verbos. Foram reproduzidas 17 falhas focais
   antes do primeiro candidato. As versões musicais com `?` também batiam
   na guarda interrogativa especializada, sem delegar o pedido ao owner geral.
2. Candidato: uma moldura compartilhada reconhece operação dirigida à
   assistente, negação na oração e pergunta de capacidade/consequência.
   O owner geral mantém P0; a gramática musical não foi enfraquecida globalmente.
3. Primeira sonda real: 8/10 contratos passaram. Pausa passou a chegar ao
   executor; `pode abri a calculadora para mim` e `preciso que você abra a
   calculadora` eram comandos autorizados, mas ainda tinham `comandos=[]`.
4. Próxima fronteira reproduzida: o normalizador do roteador removia algumas
   molduras, mas deixava `preciso que você` e o verbo informal `abri`. O
   orquestrador real, sem efeito externo no teste, retornava `None` para os
   dois pedidos. Sete novos REDs e um controle GREEN antes do segundo candidato.
5. O roteador agora reutiliza `extrair_nucleo_pedido_operacional`, no owner
   canônico da modalidade. Não há outra lista privada de molduras. Somente
   `abri` no lugar do verbo de um pedido explícito vira `abrir`; nomes como
   `abri.txt`, relatos e texto original não são reescritos por essa função.

Controles contra hipóteses concorrentes: a abertura direta teve janela
observada no mesmo processo; portanto não era falha geral do executor nem
incapacidade do Qwen. A reprodução da modalidade e do roteamento sem LLM
mostrou que a perda antecedia sua resposta. Normalizar o núcleo não fornece
autoridade: a barreira continua consultando o turno original.

### Provas e limites

- Testes focais: `tests/test_pedidos_modais_autoridade.py`, incluindo a redação
  do usuário, pares de pontuação, diferentes domínios, negação, relato,
  metalinguagem, preservação de entidades e detector que encontra um verbo
  mesmo sem autorização. Composição pública, estado compartilhado e detector
  reais foram usados; somente o efeito externo foi interceptado na integração.
- Regressão final: **1789 passed, 14 xfailed, 30 subtests passed**. Seleção:
  arquivos de testes que referenciam `classificar_modalidade_turno`,
  `analisar_gramatica_musical`, `analisar_protecao_operacional`,
  `normalizar_pedido_natural`, `preparar_entrada_deterministica` ou
  `detectar_intencao_deterministica_mente`. Não é a suíte global nem novo caos.
- Dos 14 xfails, 13 já pertenciam à seleção; um novo registra a raiz separada
  do segmentador que corta `antonio.txt?` no ponto da extensão. O ato de recusa
  e o veto continuam presentes, mas a integridade do alvo ainda está RED.
- Duas expectativas de teste foram refinadas por inspeção, não por patch de
  produção: a barreira lexical complementar retornar False não concede
  autoridade a um relato; e `pode ler apenas um exemplo de comando` pode ser
  um pedido real de leitura, portanto foi substituído como controle negativo
  por uma declaração explicitamente metalinguística.
- Sonda inicial preservada:
  `resultados_testes/roteiro_pedidos_modais_validacao-20260914-111500-519681`.
- Sonda final preservada:
  `resultados_testes/roteiro_pedidos_modais_validacao-20260914-111920-954921`.
  **10/10 respostas e contratos operacionais**, zero falhas/alertas automáticos,
  p95 7,443 s. Turnos 3–5 chegaram a MEDIA_CONTROL/pause. Turnos 7–9 tiveram
  APP_OPEN com janela observada: abertura, foco e idempotência. Turnos 1, 2,
  6 e 10 ficaram sem comandos. Roteiro encerrou a sessão; processos Python
  da sonda não ficaram ativos. Voz silenciada conforme checkpoint.
- O 10/10 mede os contratos declarados, não naturalidade completa. O recibo
  musical declara confirmação variável: envio não certifica estado final
  do player. A fala ainda promove essa evidência a “música pausada”. A
  segunda sonda também mostrou contingência chamando a recusa de “consulta”
  e fallbacks de autoria nas respostas de abertura. São pendências de fala/
  evidência, não ocultadas pelo GREEN de interpretação e roteamento.

### Escopo entregue e próxima fronteira

Produção alterada nesta continuação: `cognicao/modalidade_turno.py` e
`autonomia/roteador_deterministico.py`. Roteiro focal:
`roteiro_pedidos_modais_validacao.py`. Nenhum executor, peso neural, dataset
de treino ou configuração de influência neural foi alterado. A coleta
normal do runtime pode registrar as entradas declaradas de teste; isso não
é treino nem avaliação independente. O teste focal está abrangido pelo
gitignore existente; não foi forçado ao index.

Hashes finais de produção (SHA-256):

- modalidade: `eaf3f452f1458b7fa17872631e7a41b193b3c6a76235dde169754f60ff8c705e`.
- roteador: `1af82d489bf1dbe7e5cd5bef0e83bf63b3d58ad8afa7b6b21d4a636401e5507b`.

Próxima fronteira: força da confirmação operacional versus evidência do
receipt, incluindo a redação de contingência após recusa. A ambiguidade
isolada de `abri a calculadora do windowns` continua preservada; a confirmação
do Pedro rotula aquela ocorrência, não autoriza transformar todo passado
em imperativo. O problema de extensão/pontuação permanece registrado à parte.

## Continuação: evidência de pausa e contingência de recusa — 14/09, 19h

Baseline preservado: mesmo HEAD/branch, worktree suja. Produção desta etapa:
`cognicao/qualidade_comunicacao.py` e `cognicao/guardiao_alegacoes.py`.
Não foram alterados executores, regras de autorização, personalidade, pesos
neurais ou limites de tokens. Nenhum commit criado.

### Hipótese de pausa falsa: não confirmada no caminho real observado

A avaliação anterior era excessivamente forte ao tratar a descrição genérica
`confirmacao_oferecida=variavel` como ausência de prova daquele comando.
Isso é um metadado da capacidade, não o recibo concreto.

O caminho conectado é `ChromeComandosRuntime.enviar_detalhado` → solicitação
correlacionada por requestId → extensão → leitura de `video.paused` → retorno.
A extensão somente devolve sucesso para pause quando lê `paused=true`.
A captura não modificou argumentos nem retornos:

- `resultados_testes/transporte_evidencia-20260914-191811-641106/recibos_chrome.jsonl`:
  request `1789424301937-2`, ok/confirmado true, evidence
  `{playing: false, paused: true}`.
- Segunda prova:
  `resultados_testes/transporte_evidencia-20260914-192126-521220/recibos_chrome.jsonl`,
  request `1789424495509-2`, mesma observação de pausa.

Portanto **não corrigir a confirmação válida de pausa como se fosse falsa**.
Isso não prova retrospectivamente cada comando do caos nem entrega áudio
físico; prova o estado observado do player nestas sondas. A rota de tecla
nativa mantém `confirmado=None` e fala de envio nos regressivos existentes.
Adaptadores legados de retorno booleano não foram promovidos a evidência
real por estes testes; não houve mudança neles nesta etapa.

### Raiz comprovada da recusa corrompida

Primeira fronteira: modalidade/contrato de recusa estavam corretos, mas a
contingência fixa de `negacao_operacional_sem_efeito` dizia “consulta” para
qualquer domínio. Seis REDs, controle de correção de pergunta GREEN.
Candidato: “Entendi, não vou executar essa ação.”, sem inventar domínio,
estado ou nova autorização.

A primeira sonda revelou uma segunda fronteira: a expressão regular do
guardião encontrava `vou executar` dentro de `não vou executar`, acusava
promessa operacional e substituía a recusa por “essa parte já está resolvida”.
Isso também provocava a falha derivada `negacao_operacional_extrapolou`.
Sete REDs protegeram o guardião e a saída final; cinco controles mostraram
que uma negação em outra oração não pode liberar uma promessa afirmativa.

O candidato reutiliza `_alega_execucao_afirmativa`, já existente para
negação local de efeitos, permitindo aplicar o mesmo contrato ao padrão de
promessas. Cada ocorrência é avaliada: `não vou abrir, mas vou ligar` ainda
é bloqueada sem mecanismo. Não foi usada uma exceção por habilidade nem
uma lista de respostas históricas.

O primeiro teste de reparo não alcançou a fronteira pretendida porque faltava
anexar `contrato_fala` ao plano. Isso foi diagnosticado, a composição do teste
foi completada com o construtor canônico, e então reproduziu o RED final.
Não se mudou produção para compensar o harness incompleto.

### Validação e artefatos

- `tests/test_contingencia_recusa_sem_dominio_inventado.py`: 19 passed;
  contratos, contingência, reparo malformado/rejeitado, guardião e verificador
  final. A falha do modelo é simulada nesse teste, não nos testes reais.
- Regressão ampliada por referências a validação/fala/processamento:
  **838 passed, 1 failed**. Falha independente em
  `test_prompt_rapido_limita_saida_sem_reduzir_resposta_complexa`: espera
  128 tokens e recebe 256. Isoladamente também falha. `git show HEAD` confirma
  que o limite 256 já existe no baseline; não foi alterado para esconder o RED.
- Regressivos de mídia, navegador, pedidos modais e recusa:
  **144 passed, 1 xfailed**; o xfail é o ponto de extensão `antonio.txt?`,
  já registrado separadamente. Não afirmar suíte global verde.
- Roteiro focal novo: `roteiro_confirmacoes_recusas.py`.
- `sonda_transporte_evidencia.py --capturar-chrome` adiciona observação opcional
  dos recibos ao diagnóstico existente. IoT simulado, voz/microfone e interface
  desativados na sonda; apenas o pedido positivo de pausa foi executado.
- Primeira sonda:
  `resultados_testes/roteiro_confirmacoes_recusas-20260914-191813-738041`.
  Recusa chegou errada à saída após o guardião: preservada como RED real.
- Segunda sonda:
  `resultados_testes/roteiro_confirmacoes_recusas-20260914-192127-848307`.
  **6/6 contratos, zero alertas, p95 9,058 s**. No turno 2, a LLM e o reparo
  falharam de verdade, mas a contingência correta atravessou o guardião e foi
  publicada intacta: “Entendi, não vou executar essa ação.” Nenhum comando nas
  cinco negativas/correções. Processos da sonda encerrados.

Hashes de produção desta etapa:

- guardião: `82bd3a85fee46c8d1a1cdedc09099bc6d6bf7370ca91cb1def65ef8a60b2db10`.
- qualidade: `a03fd966047c63cb933d8c20cb2ab1e08745d9fe530a11a4fd532cb3cb147901`.

Limite ainda aberto: a geração principal às vezes infere “música rodando” a
partir de uma recusa e depende do reparo/contingência. Esta correção impede a
degradação da resposta final; **não demonstra redução da frequência de
fallbacks nem melhor compreensão do modelo**. Próximo estudo deve partir do
payload e respostas capturados, sem treino automático e sem novos bloqueios
de palavras. Preservar a pendência independente de segmentação de filenames.

## Correção da expectativa desatualizada de tokens — 14/09/2026

Baseline preservado: `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, branch
`main`, worktree com alterações anteriores. Nenhuma produção alterada nesta
etapa, nenhum commit criado.

O teste `test_prompt_rapido_limita_saida_sem_reduzir_resposta_complexa`
reproduziu isoladamente o RED `256 != 128`. A primeira divergência é a
expectativa do teste, não a preparação do payload: `git log -S` comprova que
o commit `6251cf17cd45e066647e004d95b8215ffb70849f` (25/08) já substituiu o
teto antigo por 256. `limite_tokens_resposta` documenta a razão: o orçamento
inclui o JSON estrutural e 128 cortava esse conteúdo. Isso falsifica tanto
uma regressão introduzida pela correção das recusas quanto uma divergência
atual entre os orçamentos rápidos da personalidade e do payload.

Contrato preservado: modo rápido limita a saída a 256 sem aumentar um limite
explicitamente menor; modo completo mantém seu orçamento próprio, com teto
local de 640. Expectativa corrigida para 256 e 13 casos adicionais cobrem
limites menores, endpoints local/remoto e passagem do orçamento da
personalidade ao preparador real do payload, sem rede nem modelo simulado.

Validação: **43 passed** no módulo de latência; **852 passed** na mesma
seleção ampliada que anteriormente apresentou 838 passed e 1 failed.
São provas locais de contratos e regressão selecionada, não uma nova
medição de latência, garantia de JSON completo ou suíte global/runtime real.
Não foi necessário iniciar a Laylay para corrigir esta expectativa; modelo,
pesos neurais, prompts e limites de produção permaneceram intocados.

## Estudo da geração e falsos reparos — 14/09/2026

Baseline mantido: `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, branch main,
worktree já modificada. As alterações anteriores não pertencem todas a esta
etapa. Nenhum commit, treino ou promoção neural.

### Evidência e hipóteses falsificadas

A captura `transporte_evidencia-20260914-192126-521220/transporte.jsonl`
mostra que a chamada principal recebeu a utterance exata, contrato com ato
`recusa` e instrução para não inferir estado. Não havia histórico nem receipt
de música tocando nesse payload. Logo, nessa ocorrência, classificação
ausente e contaminação por histórico musical não explicam o erro.

O payload tinha `max_tokens=128`, apesar do teto rápido de 256: a chamada
não rápida usa a proporção `curta`. A resposta terminou antes de fechar o
JSON. Isso é um problema diferente da expectativa antiga do teste corrigida
anteriormente; um teto de 256 não aumenta uma solicitação explícita de 128.

`sonda_replay_recusa.py` fez 24 chamadas ao mesmo Qwen local, sem executor,
memória ou treinamento, com duas repetições por condição e dois enunciados:

- Artefato `replay_recusa-20260914-193207-116379/comparacao.jsonl`: capturado,
  orçamento 384, retirada da personalidade longa mantendo esquema/contrato.
  Aumentar o orçamento completou JSONs mas não corrigiu a interpretação.
  Retirar somente a personalidade também gerou negação de capacidade.
- Artefato `replay_recusa-20260914-193329-743822/comparacao.jsonl`: instrução
  centrada no ato, com esquema completo ou somente fala/comandos, e controle
  direto sem o contrato. O esquema completo chegou a ser copiado vazio;
  a versão curta ajudou a abstenção, mas ainda produziu falsas justificativas
  na correção sobre Discord. Nenhuma dessas variantes foi para produção.
- `json_completo` na sonda exige o esquema principal completo; nas variantes
  de fala/comandos ele é falso por definição e não significa JSON inválido.
  Inspecionar conteúdo e finish_reason, não comparar essa coluna entre
  esquemas diferentes. Amostra exploratória, sem alegação de significância.

### Raiz de reparos indevidos comprovada e corrigida

Os replays expuseram respostas corretas rejeitadas pelo próprio código:
`Entendido, não vou pausar a música.` e
`Entendi, você não perguntou se o Discord está aberto.`.

1. O reconhecimento de abstenção listava alguns verbos de aplicativos,
   mas não pausar/ligar/apagar. Substituído por construção gramatical de
   primeira pessoa (não vou/irei + infinitivo; não farei), sem inventário
   privado de habilidades. Negação de capacidade não conta como abstenção.
2. Dois validadores liam o estado subordinado a “você perguntou se” como
   afirmação da assistente. Agora compartilham
   `estado_sob_pergunta_referida`, no módulo de escopo linguístico existente.
   A referência não é receipt, nem autorização; cada ocorrência é verificada
   e conjunções/pontuação encerram o escopo conservador. Nomes como `e-mail`
   não podem ser confundidos com a conjunção `e`. Não é parser universal:
   coordenações ambíguas permanecem conservadoras.

Produção alterada nesta etapa: `incerteza_observacao.py`,
`validacao_contrato_fala.py`, `guardiao_alegacoes.py`. Prompt, personalidade,
orçamentos, roteamento e executor não foram alterados. O contrato beneficia
recusas/referências de música, apps, arquivos, e-mail e IoT sem novos poderes.

Validação:

- Nove REDs iniciais, dez controles negativos GREEN. Casos adicionais
  detectaram o `e` de `e-mail` e escopo indevido após `logo`; corrigidos antes
  de fechar o candidato.
- `tests/test_recusa_autoral_sem_falso_reparo.py`: 26 casos passam, incluindo
  pipeline real de processamento/verificação com falha explícita se tentar
  chamar reparador para uma resposta boa. Geração fornecida como entrada;
  isto é prova de integração local, não geração livre em runtime.
- Reavaliação das mesmas respostas reais capturadas: quatro respostas boas
  antes rejeitadas passam, mantendo rejeitadas as respostas ruins da amostra.
- Regressão selecionada: **878 passed**. Vizinhos de modalidade/mídia/navegador:
  **125 passed, 1 xfailed** (filename `antonio.txt?` já conhecido).
- Primeira sonda real: `roteiro_recusas_autoria-20260914-193657-449987`,
  captura `transporte_evidencia-20260914-193656-328131`: 12/12 respostas,
  nenhum comando observado, p95 10,449 s. Isso NÃO significa geração perfeita:
  o log registra quatro contingências apesar de o resumo automático marcar
  `fallbacks_conversacionais=0`. Não usar esse contador como prova de melhora.
- O primeiro lançamento nem alcançou a conversa: o carregador exige somente
  literais no roteiro; substituída a compreensão Python por dicionário
  literal. Isso foi erro da sonda, não RED de produção.

Limites: as sondas reais executam a composição e persistência usuais. Voz,
microfone e interface foram desativados e IoT configurado como simulado;
observadores/pesquisa temática em background ainda apareceram nos logs.
Não confundir com os replays sem efeitos nem usar essas sessões como treino
ou rotulagem automática. A sonda contém somente recusas/perguntas e nenhum
pedido de ação positiva.

Próxima fronteira: orçamento do envelope estrutural separado do tamanho da
fala e geração condicionada ao ato já decidido, com comparação por contrastes
e regressão de conversa. Não baixar guardas para aceitar estados inventados,
nem declarar o modelo incapaz. O problema de geração principal permanece
aberto; esta entrega remove uma fonte comprovada de falsos reparos.

### Regressão real final e handoff

Após o ajuste das fronteiras de oração, segunda sonda:
`roteiro_recusas_autoria-20260914-194700-353957`, captura
`transporte_evidencia-20260914-194659-257728`. Resultado: 12/12 respondidos,
11 passaram e 1 alerta apenas por latência de 17,11 s no turno 1; nenhum
comando observado. P95 12,929 s. Três contingências no terminal, não zero.
Não comparar 4 versus 3 contingências como ganho estatisticamente provado.
Ambas as sondas encerraram; nenhum processo Python permaneceu ativo na
checagem final. `git diff --check` sem erros.

Hashes finais dos arquivos de produção (incluem mudanças anteriores):

- guardião: `233e43baf0eb71cb9d6757813c2ac68a1396772df924cfa9f09640f0beb43818`;
- validação: `8e8de4bbf63ab8a00119de581b9fb608d00a6e76de381fb91d2838f22eb3efbf`;
- escopo: `6063158799a61e39d9a40613f5ef40b3d121e34cdf3fc9fdbae5e3f6574c255d`.

Achado separado de segurança: o observador Chrome registrou uma URL de
callback de autenticação com token no log da segunda sonda. Não reproduzir,
compartilhar nem versionar o conteúdo desses logs; falta sanitização no owner
de observabilidade antes de imprimir URLs/eventos. Não se usou esse token,
não se alterou autenticação e não se apagaram os artefatos. A correção desse
logger não foi misturada com a de recusa.

## Realização de recusas e proteção da saída Chrome — 14/09/2026, continuação

Baseline Git/branch mantidos. Dois contratos investigados separadamente;
worktree anterior preservada, nenhum commit criado. Rede, pesos e datasets
não alterados.

### Geração: candidato e primeira fronteira de composição

O orçamento simples continua disponível: `limite_tokens_resposta` agora
aceita `envelope_estruturado=True`, usado pela chamada principal real para
reservar no mínimo 256 tokens. A função continua retornando 128 para fala
curta simples; respostas explicativas preservam 512. Não é garantia universal
de JSON válido nem correção isolada de interpretação: o replay anterior já
falsificou essa hipótese.

O preparador canônico passa a fornecer uma tarefa de realização da fala para
`negacao_operacional_sem_efeito`, somente com identidade de turno/contrato
coincidente, utterance atual coincidente, autorização explicitamente falsa,
modalidade recusa/correção e sem evidência de composição. O histórico original
não é substituído. A LLM formula a resposta; não reclassifica o ato, escolhe
ações ou inventa leituras emocionais obrigatórias nessa tarefa restrita.
O schema desse caminho contém fala/comandos, como a projeção de fonte textual
já existente. Ausência de leitura emocional não é preenchida artificialmente.

`montar_mensagens_reconhecimento_limite` reutiliza o ponto de montagem de
mensagens de comunicação. Quatro exemplos contrastivos explicam o ato com
documento, brilho, janela e reinício, sem exemplos específicos de música ou
Discord. São demonstrações no prompt, não treino nem mensagens persistidas.
Falas sobre estados continuam passando pelo guardião e pelo contrato original.

O RED composto mostrou que o veto soberano pode colapsar “não pause a música
e abra a calculadora” em uma única recusa. Não se corrigiu isso reclassificando
na geração: a projeção opcional exclui coordenação textual conservadoramente
e deixa esses casos no caminho completo. Essa guarda não autoriza ações.

Os primeiros replays contrastivos ajudaram, mas sem perfeição. Após acrescentar
o contraste de pedido indireto, o Qwen formulou abstenções corretas para música,
arquivos, apps, IoT e listas. Também surgiu “não vou verificar se o Discord
está aberto”: não afirma o estado. Dois REDs comprovaram outro escopo subordinado
legítimo; o helper compartilhado de referência a pergunta foi estendido para
consultas explicitamente recusadas. Contrastes com afirmação independente
depois de vírgula/conjunção permanecem bloqueados.

A primeira sonda real expôs diferença que o replay não cobria: modo rápido
cortava os exemplos de um `contexto_fechado` como se fossem histórico. RED
no preparador reproduziu pares de demonstração órfãos. O pacote fechado já
selecionado pelo owner agora é preservado nessa fronteira; não se aumentou
histórico global nem se desativou o controle de transporte.

Produção alterada para esse contrato:
`qualidade_comunicacao.py`, `contexto_resposta_ia.py`,
`proporcao_resposta.py`, `resposta_ia_runtime.py`, `preparacao_llm.py` e
`incerteza_observacao.py`. As demais mudanças preexistentes nesses arquivos
não fazem parte desta etapa. Sem alteração de executores ou autorização.

### Log Chrome: sanitizar antes de imprimir

Cinco REDs com credenciais fictícias provaram que `dispatch_event` imprimia
payload arbitrário, seguido de outra impressão da URL/título em `handle_action`.
Sanitização posterior no DEV Console não protege o stdout original capturado
pelos roteiros. Reutilizados `sanitizar_texto_navegador` e
`sanitizar_texto_dev` antes da impressão dos eventos textuais. Debug/evento
desconhecido publica apenas tipo/ação, não o payload arbitrário.

`url_sem_dados_sensiveis` também remove userinfo, além de query/fragmento.
Dados entregues ao handler, callbacks, estado e receipts permanecem intactos;
os testes verificam isso. Produção desse contrato: `chrome_ws_handlers.py` e
`erros_navegador.py`. Não é auditoria completa de todos os logs do projeto e
não remove segredos dos artefatos históricos. Não compartilhar logs antigos.

### Provas e limites finais

- `test_chrome_log_sem_credenciais.py` + vizinhos Chrome: 27 passed,
  2 subtests passed; credenciais fictícias, sem nova autenticação real.
- `test_geracao_limite_sem_estado.py`: 16 passed, incluindo guardas de turno,
  perguntas/pedidos positivos/mistos, orçamento principal e orquestrador real
  com preparador/registro/histórico reais (modelo e efeitos como fronteiras).
- `test_recusa_autoral_sem_falso_reparo.py`: 30 passed.
- Seleção ampliada de geração/validação/preparação/Chrome: **957 passed,
  2 subtests passed**. Vizinhos operacionais: **125 passed, 1 xfailed**
  (filename `antonio.txt?`, conhecido). Não afirmar suíte global verde.
- Replays locais adicionais em `replay_recusa-20260914-195147-113400`
  (projeção exploratória), `...-195229-094649` (contrastes iniciais),
  `...-195629-104470` e `...-195704-127835` (20 gerações cada, 10 enunciados).
  Foram inspecionados conteúdo e atos, não apenas o contador de JSON completo,
  que se refere ao schema principal e não ao schema reduzido experimental.
- Primeira sonda: `roteiro_recusas_autoria-20260914-195751-096744`, captura
  `transporte_evidencia-20260914-195749-991278`: 12/12, nenhum comando,
  p95 5,014 s; ainda houve reparos, incluindo o modo rápido sem exemplos.
- Sonda final: `roteiro_recusas_autoria-20260914-195946-177670`, captura
  `transporte_evidencia-20260914-195945-095931`: 12/12, nenhum comando,
  zero reparos/contingências no terminal, p95 3,186 s. A geração principal
  respondeu “Certo, não vou pausar a música.” e reconheceu as correções sobre
  Discord/Opera sem afirmar seus estados. Recebeu pacote de ~950 caracteres
  contra ~11 mil na chamada histórica. A mudança de latência é uma observação
  destas sondas, não benchmark controlado nem promessa de desempenho.

O conjunto continua tendo limites fora do candidato: “preciso que você não
altere o volume” é classificado como conversa (primeira fronteira distinta),
e a pergunta de como pausar ainda pode gerar explicação ruim de capacidade.
Na última sonda a resposta “o volume não muda” veio desse caminho não coberto;
não tratá-la como receipt de estado. Logo, o verde do avaliador sem comandos
não certifica toda a linguagem. A correção atual valida a família de recusas
canônicas e não elimina toda possibilidade de invenção em conversa livre.

## Recusas de alteração: primeira fronteira lexical — 14/09, handoff 15/09/2026

Baseline mantido: `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, branch `main`,
worktree suja preservada. A pendência registrada acima sobre “preciso que você
não altere o volume” foi investigada separadamente e corrigida nesta etapa.

Antes do candidato, a proteção e a classificação canônicas deixavam a frase
como conversa. O mesmo ocorria com arquivo, enquanto “preciso que você não
pause a música” era recusa. Isso falsificou uma falha exclusiva do executor de
volume e uma incapacidade geral de reconhecer negação. A primeira divergência
ocorria antes da LLM: a base verbal compartilhada não incluía alterar/mudar/
ajustar e suas formas de pedido; o veto avulso ainda dependia de outra lista.

Contrato: a mesma base lexical deve admitir pedido, capacidade e recusa;
polaridade, modalidade e autorização continuam sendo decisões canônicas.
Adicionados esses verbos às bases existentes e reutilizadas as bases na
negação avulsa, preservando formas legadas. Somente `modalidade_turno.py` foi
alterado em produção nesta etapa. Sem alterar executor, prompts, pesos,
datasets ou configuração de influência neural. Nenhum commit criado.

`test_recusas_alteracao_canonica.py` começou com 24 falhas causais e 13 acertos;
após o candidato, 37 passaram. Quatro controles adversariais posteriores
completaram **41 passed**, incluindo detector que propõe ação indevida e
prova de que o runtime imediato não a executa. Cobertura: volume, arquivo,
brilho/IoT, pedidos indiretos, perguntas com/sem interrogação, relatos,
hipóteses, menção, metalinguagem e pedidos positivos legítimos.

Validações ampliadas, sem somar seleções que podem se sobrepor:

- Linguagem/roteamento: **1891 passed, 14 xfailed, 30 subtests passed**.
- Geração/validação/preparação/Chrome: **994 passed, 2 subtests passed**.
- As seleções ampliadas precedem os quatro controles adversariais finais.
  Os xfails conhecidos não foram removidos nem convertidos em verde.

Sonda real `roteiro_recusas_autoria-20260914-203259-589053`, captura
`transporte_evidencia-20260914-203258-325688`: **18/18 respondidos e aprovados
pelo avaliador operacional, zero comandos, zero alertas**, p95 9,726 s.
Inspeção do terminal não encontrou reparo semântico, reparo rejeitado ou
contingência contextual. Exemplos efetivamente entregues: “Certo, não vou
alterar o volume”, “Certo, não vou ajustar o volume” e “Certo, não vou mudar
o arquivo notas.txt”. Isso não equivale a verificar efeitos físicos: esses
turnos pediam abstenção. Nenhum processo Python restou na checagem final.

Limites separados observados na mesma sonda: a pergunta de como pausar ainda
recebeu explicação ruim de capacidade; o relato “eu alterei o volume” recebeu
uma referência desnecessária a não mudar o arquivo citado anteriormente.
Portanto, **verde operacional não é verde de qualidade conversacional**.
Esses dois achados continuam abertos; não justificam liberar a rede nem
declarar toda invenção de estados resolvida.

Hash final de `modalidade_turno.py`, incluindo mudanças anteriores:
`388dd80405bc916c35f729598fd6b87b27aeef5100b4d7df25b4ab947f7ffc21`.
`git diff --check` sem erros. Os testes novos existem localmente sob regras
de ignore preexistentes; não houve alteração dessas regras nem staging.

## Histórico de respostas locais e continuidade — 15/09/2026

Baseline Git mantido em `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, `main`.
Antes da alteração, conferidos status da worktree e código de composição.
Somente esta etapa acrescenta mudanças em `orquestrador_fala_runtime.py`;
os diffs de `laylay.py`, `resposta_ia_runtime.py` e `registro_conversa_llm.py`
também contêm trabalho anterior, que foi preservado.

### Cadeia causal e falsificações

A captura de 14/09 às 20:32 mostrou que o turno “eu alterei o volume” recebia
como último par do histórico a recusa sobre `notas.txt`. As duas perguntas
de capacidade sobre volume, efetivamente respondidas no meio, não estavam no
payload. `RespostaIARuntime` retornava em `tratado_prioritario` antes de
`EstadoConversaRuntime.iniciar_turno` e da finalização conversacional da LLM.

Quatro REDs de integração confirmaram: classificador, catálogo vivo, comando
imediato e orquestrador de fala reais publicavam a resposta, sem executor nem
LLM; o histórico permanecia vazio. A primeira tentativa de fixture usava ID
textual onde o planejador exige inteiro e foi corrigida antes de considerar
esses REDs válidos. O erro de fixture não foi contado como prova da raiz.

Falsificado: a lacuna ser causada apenas pelo corte do histórico no transporte
(ela já existia antes dele), ou apenas pelo Qwen (o caminho sem chamada ao
modelo a reproduz). Os controles do registro canônico/LLM continuaram verdes.
Não se concluiu que o modelo nunca retoma assunto indevido por outros motivos.

A inspeção de vizinhos também corrigiu uma generalização do diagnóstico:
**nem toda rota local omitia o histórico**. `emitir_resposta_curta` já grava
pares por um writer legado. Um RED com esse emissor, gerenciador de chats e
estado reais mostrou duplicação no primeiro candidato, antes do ajuste final.
Outro RED mostrou que nomes de fase sociais não compartilham um prefixo
uniforme; o orquestrador agora indica conclusão local explicitamente.

### Contrato e candidato

Contrato: **resposta local publicada pertence ao diálogo, independentemente
de ter usado LLM; fase tratada não é prova de publicação nem de efeito**.

- O orquestrador expõe os textos aceitos pelos observadores textuais, por ID
  do turno, com cópia imutável, deduplicação dentro do turno e retenção de
  64 turnos. Não usa `ultima_resposta`, fala planejada, proatividade ou aceite
  de fila de áudio como comprovação de texto entregue. O receipt é textual,
  não de reprodução física de voz nem de execução de comando.
- O registro canônico prepara uma conclusão adiada, vinculada ao chat de
  origem antes do dispatch, sem inserir entrada/resposta artificialmente.
  Ao receber o texto publicado, reutiliza a idempotência do mesmo registro
  que atende a LLM. Repetir a frase em outro turno continua sendo novo diálogo.
- Para o writer legado, o registro só adota pares acrescentados desde o
  vínculo, no mesmo chat, com prefixo anterior intacto e conteúdo idêntico
  à entrada e à saída confirmada. Não deduplica por semelhança textual ou
  pela última frase global. O emissor legado não foi removido.
- A coordenação registra as conclusões prioritária, de pré-fluxo e social.
  Comandos de abrir/fechar o modo chat mantêm seu ciclo anterior. Falha no
  registro é diagnosticada sem bloquear o comando nem a conclusão já entregue.
- `laylay.py` apenas injeta o getter do orquestrador real. Não foram alterados
  prompts, catálogo de capacidades, autorização, executores, pesos, datasets
  ou configuração de influência neural nesta etapa. Nenhum commit criado.

Produção alterada: `integracao/registro_conversa_llm.py`,
`autonomia/resposta_ia_runtime.py`, `personalidade/orquestrador_fala_runtime.py`
e a ligação em `laylay.py`. Não é migração completa de todos os writers antigos
nem correção da rota exclusivamente de áudio sem publicação textual confirmada.

### Validação e limites

- `test_historico_turnos_locais.py`: 17 testes, cobrindo publicação antes de
  memória, perguntas reais, payload do turno seguinte, áudio recusado com
  texto entregue, rejeição de todos os canais, proatividade, chat de origem,
  textos múltiplos, retenção, falhas de registro, composição principal,
  atalho social e writer legado com repetição legítima.
- Seleção focada com vizinhos e recusas de alteração: **103 passed**.
- Seleção ampliada final: **605 passed, 3 failed, 8 subtests passed**.
  As três falhas são `test_red151_c3_feedback_simples_registra_receipt_antes_da_fala`,
  `test_red151_c3_runtime_canonico_146_151_cria_salva_responde_sem_llm` e
  `test_red_p1h4_entrada_aceita_preempta_presenca_antes_do_turno`.
  Reexecutadas com os blocos deste candidato retirados somente em memória
  de `RespostaIARuntime` e do orquestrador: mesmas três falhas e asserções
  (ordem receipt/voz, contador add e preempção de presença). A worktree não
  foi revertida. Isso sustenta independência do candidato, não resolve nem
  desqualifica aqueles REDs. Não declarar suíte global verde.
- Primeira sonda real: `roteiro_recusas_autoria-20260915-064853-374851`,
  captura `transporte_evidencia-20260915-064851-510837`: 18/18, zero comandos,
  zero alertas/reparos/contingências; p95 11,212 s. Antecede o ajuste de adoção
  do writer legado, portanto não é a prova final desse ajuste.
- Sonda final: `roteiro_recusas_autoria-20260915-065330-688257`, captura
  `transporte_evidencia-20260915-065329-522576`: **18/18, zero comandos e
  alertas**, p95 2,836 s. Terminal sem reparo semântico, contingência ou falha
  de registro local. As diferenças de latência não são benchmark controlado.
  No payload real de “eu alterei o volume”, o par recente agora é a pergunta
  de capacidade sobre volume e sua resposta, não a recusa sobre o arquivo.
  Resposta entregue: “Entendi, você já alterou o volume. O que aconteceu depois?”
  Não voltou ao arquivo nem afirmou observação própria do volume.
- As sondas iniciam a aplicação com áudio/microfone/interface desativados,
  IoT simulado e Gmail sem credenciais; serviços de observação e persistência
  do runtime continuam ativos. Não são sessões isoladas sem escrita de
  histórico e não foram usadas como treino ou promoção neural. Ambas
  encerraram, e a checagem final não encontrou processos Python ativos.

**Ainda aberto:** a pergunta “como eu poderia pausar a música?” pode receber
uma explicação desnecessária ou incoerente de capacidade. Na primeira sonda
veio instrução de player seguida de uma digressão sobre “mundo real”. A lacuna
de histórico tem correção comprovada; isso não certifica toda conversa livre
nem elimina toda invenção de estados. Próxima fronteira: seleção de evidência
do catálogo e realização de perguntas procedurais, sem mudar a rede agora.

Hashes finais de produção (incluem alterações anteriores):

- registro: `7e46fa800a45eb6bc11cd18c7290360551284f9385b6cf986372caaf1cce68e3`;
- resposta: `5eadaf0af13024b8971aebedd005c3bd1c7efb8da8b9eaeca1db0d5690e66f0f`;
- orquestrador: `483d4676791925e4b5eacfb1d8fad09d122547e57894274e1a0621ebfa1fdd10`;
- composição: `284210183fc4d09a1e3a303d746bc239e16799044a3dd37433ad93e11aecc74d`.

## Capacidades relevantes no transporte — 15/09/2026

Continuação de P01 do registro central. Base: branch `main`, HEAD
`76aa525ef61fdb4ecfbfdb578adf572c0b83949a`; worktree suja, com alterações
anteriores nos módulos de prompt, catálogo e transporte. O diff preexistente
foi preservado; o HEAD não foi tratado como reprodução do runtime atual.

### Primeira fronteira comprovada

Adicionada à sonda existente a opção `--capturar-preparacao`, que registra o
pedido tipado e o payload preparado antes do envio HTTP, sem modificar suas
decisões. As capturas são locais e podem conter contexto pessoal; não publicar.

Sonda anterior ao candidato:
`roteiro_recusas_autoria-20260915-170651-474402`, captura
`transporte_evidencia-20260915-170649-114054`.

Na pergunta “como eu poderia pausar a música?”:

1. Classificação canônica: pergunta, sem autorização.
2. Pedido entregue ao preparador: catálogo relevante presente.
3. Payload preparado: catálogo presente; primeiro system com 9.478 caracteres.
4. HTTP efetivo: catálogo ausente; primeiro system reduzido a 4.989 caracteres.
   Restaram instrução de 1.985 caracteres e usuário de 32; histórico recente
   também não coube nessa compactação.

O catálogo estava num sufixo do prompt principal tratado como opcional pelo
compactador. A base permanente ocupou o limite e o sufixo foi descartado.
Falsificadas nesta passagem: perda anterior pelo setter/registro de histórico;
ausência de seleção pelo catálogo; limite interpretativo do Qwen como explicação
para o desaparecimento da evidência **antes** de ele receber o pedido.
Isso não prova que toda resposta ruim possui a mesma causa.

### Contrato e candidato mínimo

**Disponibilidade e limites relevantes ao turno são evidência atual, não
decoração descartável da personalidade. Capacidade continua sem ser autorização.**

Produção alterada nesta etapa: somente
`mente_laylay/autonomia/contexto_resposta_ia.py`.

- O bloco do catálogo selecionado passa para a instrução do turno, já protegida
  como unidade junto da fala atual. Não aumenta nem remove o orçamento global.
- As rotas normal e rápida usam o mesmo callback de catálogo vivo. A rápida
  antes não consultava essa fonte; agora não depende apenas de nomes de domínios.
- A resposta factual com candidatos já materializados mantém a exclusão do
  catálogo, para não competir com a evidência factual selecionada.
- Sem parser por habilidade, resposta fixa, alteração de autoridade, executor,
  modelo, pesos, dataset ou promoção neural. Nenhum commit criado.

### Testes e prova real

- `tests/test_contrato_prompt_transporte.py`: 17 novos casos vermelhos antes do
  candidato e verdes depois, com música, volume e IoT, pergunta sem `?`, capacidade
  disponível/indisponível, duas rotas, recompactação e retry HTTP 400. Os 15 casos
  anteriores permaneceram verdes. Na montagem inicial da fixture IoT, `IOT` foi
  corrigido para o intent real `IOT_CONTROL` antes de validar os REDs causais.
- Seleção focada inicial: **83 passed**.
- Seleção ampliada final: **451 passed**, incluindo consumidores reais do
  preparador/compactador, catálogo, histórico local, chats e fundamentação.
  Um teste antigo exigia `messages[0] == prompt_agregado`; foi atualizado para
  exigir o catálogo intacto na instrução efêmera, sem duplicá-lo na personalidade.
  Não houve enfraquecimento da expectativa de presença da evidência.
- Sonda posterior: `roteiro_recusas_autoria-20260915-171002-284181`, captura
  `transporte_evidencia-20260915-171001-242621`. Na mesma pergunta, catálogo
  presente na preparação **e no HTTP real**; instrução atual com 2.460 caracteres.
- As duas sondas terminaram com **18/18 nos critérios do roteiro e nenhum comando
  operacional**, mas esses critérios não certificam qualidade conversacional.
  Os p95 foram 9,461 s e 5,180 s; não constituem benchmark controlado.
- Áudio/microfone/interface desativados, IoT simulado e Gmail sem credenciais;
  observadores e persistência habituais continuam ativos. Não é teste físico
  de mídia nem teste isolado sem escrita de histórico.
- As duas sessões encerraram; a verificação final não encontrou processos
  Python ativos. Compilação dos arquivos alterados passou, assim como o
  `git diff --check` do módulo de produção.

### Limite aberto e novo achado P11

**Não declarar P01 resolvido.** Mesmo com o catálogo presente, a resposta bruta
continuou focada no botão do player, sem boa orientação sobre usar a Laylay.
A LLM também propôs um comando; o porteiro o descartou por falta de autorização,
antes de validar a fala. Essa proposta não virou efeito externo.

No turno posterior ao candidato, a continuação “me diga o nome da música ou o
app que tá rodando, para eu te ajudar a localizar” foi rejeitada pelo detector
de resultados sem evidência. O reparo foi rejeitado, a tentativa seguinte foi
limitada pelo orçamento e a saída final foi um fallback de esclarecimento.

Controle direto, sem LLM/transporte/comandos, em
`detectar_resultados_operacionais_sem_evidencia(..., plano={})`:

- formulação longa acima → `resultado_operacional_sem_evidencia`;
- “me diga qual app está rodando” → aceita;
- “o app está rodando” → `resultado_operacional_sem_evidencia`, corretamente.

Esse é um RED distinto de escopo do pedido de informação, registrado como P11;
o guardião não foi alterado neste candidato. Próximo passo: proteger a distinção
entre informação solicitada e estado afirmado, com negativos coordenados, e
depois reavaliar a qualidade procedural de P01. Não remover a proteção contra
estados inventados nem mascarar a falha com nova resposta pronta.

Hash final de `contexto_resposta_ia.py`, incluindo mudanças anteriores:
`363ce91343552c15c5065d611582c915c0b28befc2fbbfbf217cb51ad579e2a8`.

## Pedido de informação não é alegação de estado — P11 — 15/09/2026

Continuação autorizada pelo Pedro. Base conferida: branch `main`, HEAD
`76aa525ef61fdb4ecfbfdb578adf572c0b83949a`; worktree suja, incluindo alterações
anteriores em `guardiao_alegacoes.py` e `incerteza_observacao.py`. Diff anterior
preservado; nenhum reset, mudança de baseline ou commit.

### Cadeia causal e controles

A frase histórica completa estava em
`transporte_evidencia-20260915-171001-242621/transporte.jsonl`, resposta à entrada
“como eu poderia pausar a música?”. O trecho “me diga o nome da música ou o app
que tá rodando, para eu te ajudar a localizar” entrou no detector sem receipt,
como era correto: pedir uma informação não exige já conhecer sua resposta.

O reconhecedor compartilhado só aceitava complementos iniciados em
`se/qual/quais`. O objeto nominal com oração relativa (“o app que…”) não entrava
nessa regra. A primeira divergência era a classificação de “tá rodando” como
alegação da Laylay. Depois vinham reparo rejeitado, limite de chamadas e fallback.

Falsificações: o falso positivo reaparece sem LLM e sem transporte; também
reaparece quando a proposta de pausa é retirada do JSON. Logo nem variabilidade
do Qwen nem proposta operacional são necessárias para essa rejeição. O controle
“me diga qual app está rodando” era aceito e a afirmação direta “o app está
rodando” era corretamente rejeitada sem evidência.

Os contrastes revelaram também escopo excessivo da regra antiga: depois de
“me diga qual aplicativo está rodando”, algumas continuações com `porque`,
`pois`, `então`, `logo`, `ou` ou travessão podiam herdar o pedido anterior e
encobrir uma alegação independente. Não bastava ampliar a lista de inícios.

### Contrato e alteração mínima

**Informação solicitada não é observação; o escopo de um pedido não serve de
prova para outro estado, sucesso ou falha narrado depois.**

Produção alterada:

- `cognicao/incerteza_observacao.py`: reconhece objeto nominal terminado em
  oração relativa, além de `se/qual/quais`. Não inclui “me diga que” ou “posso
  informar que”. Delimita conectivos explicativos/adversativos e pontuação.
- `cognicao/guardiao_alegacoes.py`: os dois consumidores usam o mesmo contrato
  de prefixo anterior à ocorrência, limitado pela última alegação detectada.
  Esse limite considera tanto resultados narrados como estados fortes; tipos
  diferentes não podem emprestar escopo entre si. `e/ou` podem ligar nomes antes
  da primeira ocorrência (“nome da música ou o app que…”), não liberar outro
  estado automaticamente. É uma regra conservadora, não um parser irrestrito.

Produção não alterada: autorização, executores, composição em `laylay.py`,
prompt/personalidade, catálogo, modelo e rede neural. Não foi criada resposta
fixa nem removida a proteção contra estado sem evidência.

### RED → GREEN e regressões

- Novo `tests/test_pedido_informacao_sem_alegacao.py`: **44 casos**. Os primeiros
  40 produziram **17 failed / 23 passed** antes do candidato: pedidos nominais,
  escopos indevidos e reparo da resposta histórica. O RED atingiu os validadores,
  não import/dependência. Com o primeiro candidato, os 40 ficaram verdes.
- Quatro contrastes adicionais misturaram estados de apps/dispositivos e
  resultados de arquivos. Expuseram que reiniciar o prefixo apenas pelas
  ocorrências do tipo corrente era insuficiente. O candidato final consulta
  o conjunto dos detectores existentes, sem adicionar um parser de domínio.
- A expectativa desses quatro foi alinhada ao contrato real do verificador
  final: ele pode rejeitar a fala original **ou** aceitar uma versão ajustada.
  `aceita=True` da versão ajustada não significa liberar a original; uma fala
  rejeitada também pode permanecer no campo de diagnóstico. O teste exige
  problemas e `not aceita or fala != original`, não verde pela string isolada.
- Seleção inicial com vizinhos: **177 passed** (antes dos quatro contrastes).
- Seleção ampliada final: **918 passed**, consumidores de qualidade,
  alegações, verificador final e preparação de resposta. Não é suíte global nem
  revalidação das falhas P03–P05 do registro.
- Compilação dos módulos/teste/sonda passou; `git diff --check` dos dois módulos
  de produção passou.

### Validação no processo real e distinção de replay

Sonda sem substituir a geração:
`roteiro_recusas_autoria-20260915-171953-882972`, captura
`transporte_evidencia-20260915-171952-321936`: **18/18**, zero comandos
operacionais, sem reparo semântico/contingência. **Não provou sozinha P11**:
o Qwen não repetiu a subordinada problemática. Sua explicação ainda foi ruim,
incluindo “não preciso te ensinar nada”. Esse problema permanece em P01.

Para fixar a entrada causal sem alterar guardiões/roteamento, a sonda existente
ganhou `--replay-captura` e `--replay-texto`. Ela exige exatamente uma resposta
HTTP 200 correspondente na captura local sob `resultados_testes`, usa-a uma vez
e registra `etapa=replay`, `geracao_real=False`. A configuração padrão continua
somente observação. Não confundir envio capturado pela sonda com chamada HTTP
real no único turno reapresentado.

Replay intermediário:
`roteiro_recusas_autoria-20260915-172226-661284`, captura
`transporte_evidencia-20260915-172225-555263`; precede o endurecimento entre
tipos de alegação, portanto não é sua prova final.

Replay final com o candidato completo:
`roteiro_recusas_autoria-20260915-172437-266866`, captura
`transporte_evidencia-20260915-172436-025373`.

- **18/18** nos critérios do roteiro, sem comando operacional.
- A resposta HTTP histórica completa foi reapresentada no turno 10; não foi
  reescrita para evitar o defeito. O processo real descartou a proposta de pausa
  por `plano_atual_sem_autorizacao`, preservando a fronteira operacional.
- A fala original completa chegou a `conversa.md`/publicação, incluindo a
  subordinada que antes causava o falso positivo, **sem reparo ou fallback**.
- Isto valida a composição real com entrada de modelo gravada; não é nova
  geração do Qwen nesse turno nem confirmação física de áudio/mídia.
- As sondas usam interface/microfone/áudio desativados, IoT simulado e Gmail
  sem credenciais; persistência e observadores habituais continuam ativos.
  Os históricos produzidos não são treino validado. Nenhuma promoção neural.
- Sessões encerradas; verificação final sem processos Python ativos.

**Conclusão:** P11 validado no escopo coberto, registrado como C08. P01 continua
aberto: melhorar o uso do catálogo vivo na explicação e o tom, não apenas fazer
uma resposta ruim sobreviver ao guardião. Não declarar a Laylay inteira corrigida.

Hashes finais, incluindo as mudanças anteriores preservadas:

- `guardiao_alegacoes.py`: `567065e7723ca72d7bde945f15ebbe3ba093a066394165087555e0fbad067889`;
- `incerteza_observacao.py`: `19b21630ec81e2133b0454fe11db96f5253b133512d4b09bb70b84f037b375aa`.

## Explicação documental e citação didática — P01/P10 — 15–16/09/2026

### Base e escopo

HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, branch `main`, worktree já
extensamente modificada. Preservados candidatos anteriores. `git status --short`
foi registrado em `base.json` das ablações; HEAD e diff foram novamente conferidos.
Nenhum commit, reset, promoção neural ou alteração dos executores.

Produção alterada nesta etapa:

- `especialistas/mapa_habilidades.py`: projeção documental da mesma fotografia viva;
- `cognicao/contrato_fala.py`: vincula documento a texto/ID e ato canônico;
- `cognicao/geracao_concreta.py`: estratégia de explicação documental;
- `personalidade/fala_capacidades.py`: instrução de autoria, sem frase pronta;
- `autonomia/contexto_resposta_ia.py`: pacote efêmero fechado somente quando elegível;
- `cognicao/fundamentacao_factual.py`: papel da citação e escopo de enumeração;
- `cognicao/plano_turno.py`: mantém validação factual mesmo sem título candidato.

`laylay.py`, classificação/autorização, rede, datasets, prompts-base e executores
não foram alterados nesta etapa. O encadeamento já existente de evidência do mapa
até o plano/contrato foi reutilizado; não houve registro de uma segunda capacidade.

### Diagnóstico e hipóteses concorrentes

A captura de 17:19 de 15/09 mostrou a pergunta correta, catálogo musical presente
e estratégia genérica `resposta_direta`. O prompt exigia personalidade extensa,
leitura emocional/semântica, propostas e fala ao mesmo tempo. O catálogo de domínio
não oferecia exemplos na projeção enviada. A mesma pergunta gerava ironia,
suposições sobre o player e propostas de pausa sem autorização.

Foram feitas **36 chamadas locais de ablação**, três sementes por variante,
mantendo o modelo `qwen3:4b-instruct`, temperatura 0,7 e orçamento de 256 tokens.
Não houve executores, memória da Laylay nem promoção de respostas a treino nessas
chamadas isoladas. Elas são experimentos, não provas do runtime.

Artefatos em `resultados_testes/`:

- `estudo_explicacao-20260915-183454-941372`: original, documentação acrescentada,
  tarefa acrescentada e combinação; adicionar texto não resolveu consistentemente;
- `estudo_explicacao-20260915-183657-367859`: sistemas fundidos, personalidade
  compactada, realização focada e indisponibilidade; ainda houve comandos e
  extrapolações quando a saída continuou misturando fala/planejamento;
- `estudo_explicacao-20260915-183819-158614`: autoria somente de `fala`, documentação
  compacta, com/sem demonstrações e disponível/indisponível. Melhorou o núcleo
  explicativo; demonstrações também causaram promessas excessivas e não entraram
  no candidato. Não atribuir toda a melhora a uma única variável não isolada.

Controles: o payload já continha o catálogo (não era novamente C07); a consulta
local ao modelo não revelou um system prompt oculto; os prompts medidos ficaram
entre 2.195 e 2.389 tokens, abaixo da janela de 4.096, com término `stop` nas
respostas. Fundir mensagens de sistema sozinho não resolveu. A hipótese sustentada
é inadequação da tarefa/evidência para a realização, não incapacidade intrínseca
do Qwen ou simples falta de outra regra de personalidade.

### C09 — contrato de autoria de explicações

`catálogo vivo → documento efêmero → contrato do turno → tarefa de fala`.

Somente perguntas atômicas elegíveis recebem essa projeção. O texto original
permanece no histórico e como última mensagem. O modelo não precisa propor
comandos para explicar como pedir uma ação; qualquer proposta indevida ainda
passa pela autorização canônica e é descartada quando não autorizada.

Os exemplos atuais pertencem ao domínio, não individualmente a cada intent.
Por isso o candidato não usa esses exemplos para prometer disponibilidade em
domínios parciais/degradados. Conserva o fluxo completo nesses casos, em múltiplos
atos, documento de outro turno ou ausência de documentação. Indisponibilidade
integral não herda exemplos de execução. Essa limitação precisa de documentação
por capacidade, não de uma exceção por nome de aplicativo.

RED inicial do teste novo: 13 falhas / 15 aprovações. O candidato trouxe GREEN
para os contratos elegíveis, com quatro REDs de cobertura preservados após ampliar
os controles: volume (P12) e calculadora (P13), nas duas rotas de transporte.
As asserções não foram enfraquecidas nem marcadas como xfail.

### C10 — o próximo RED estava no verificador factual

Primeira sonda real após C09:
`roteiro_recusas_autoria-20260915-184448-437661`, captura
`transporte_evidencia-20260915-184447-325549`.

O Qwen gerou “Para pausar a música, basta dizer 'pausa a música'”. A preparação
preservou a fala, sem comandos. Só depois o verificador extraiu a citação como
obra, iniciou pesquisa temática e eliminou a orientação. Reproduzido diretamente
no extrator e no verificador, sem transporte, LLM ou receipt: não era truncamento
do modelo nem remoção pelo sanitizador operacional.

Contrato: **exemplo de enunciado ≠ título de obra; citação ≠ dispensa de fonte
para afirmações externas ao trecho citado**. O extrator compartilhado distingue
introduções didáticas e enumerações diretas. Outra oração, como “e recomendo…”,
não herda o papel. A forma indireta de pedido reutiliza a classificação canônica
somente para reconhecer texto citado, nunca para executá-lo.

RED inicial: 7 falhas / 7 aprovações. A expansão encontrou uma regressão real:
sem título candidato, `plano_turno` deixava de validar uma data externa à citação.
Separadas as perguntas “há citação?” e “há possível título?”. O teste existente
de metalinguagem/data foi preservado e voltou ao GREEN. A suíte própria ampliada
tem 27 casos; combinada com metalinguagem, **42 passaram**.

Seleção ampliada final: **1.307 aprovados e quatro falhas**, em 11,25 segundos.
As quatro falhas são os contrastes de volume e calculadora nas rotas normal e
rápida (P12/P13); permanecem RED, sem `xfail` nem expectativa enfraquecida.
Não é a suíte global e não revalida as outras pendências históricas do índice.
Seleção reproduzível:

```powershell
$testesP01 = @(rg -l --no-ignore 'avaliar_qualidade_comunicacao|validar_alegacoes_da_fala|verificar_fala_turno|validar_fala_com_fundamentacao|extrair_titulos_citados|preparar_resposta_para_execucao|MapaHabilidadesRuntime' tests --glob 'test_*.py')
& .\.venv314\Scripts\python.exe -m pytest @testesP01 -q --tb=short
```

### Runtime: resultados e limites

Todas as sondas abaixo usaram geração real do Qwen; **não houve replay**.
UI, microfone e reprodução de voz desligados, IoT simulado, Gmail sem credenciais.
Persistência e observadores normais continuaram ativos; estes históricos não são
feedback de treino qualificado. Nenhum comando operacional foi observado.

- Sonda `roteiro_explicacao_capacidades-20260915-185038-699006`, captura
  `transporte_evidencia-20260915-185037-676191`: interrompida depois de 8/12
  respostas. Pausa chegou íntegra; retomar revelou outra forma de exemplo que
  ainda era cortada. Também expôs a resposta fixa IoT de P14. Não contar como
  execução completa nem como falha comprovada de transporte no turno 9.
- Sonda `roteiro_explicacao_capacidades-20260916-084208-340029`, captura
  `transporte_evidencia-20260916-084206-188232`: 12/12 respostas, placar mínimo
  7 aprovadas / 4 falhas / 1 alerta. Timeouts nas duas primeiras chamadas;
  retomar trouxe enumeração de exemplos ainda tratada como obra. Detectado,
  reproduzido em RED e ajustado o escopo da enumeração. IoT continuou errado.
  Calculadora/volume também tiveram conteúdo ruim apesar da aprovação mínima.
- Sonda final `roteiro_explicacao_capacidades-20260916-084558-409596`, captura
  `transporte_evidencia-20260916-084557-223668`: 12/12, **10 aprovações mínimas e
  2 falhas IoT**, zero comandos. Pausa, ensino de pausa e retomar chegaram ao chat
  com os exemplos preservados, sem pesquisa das citações. Não certifica que todas
  as paráfrases ensinadas acionem exatamente a intenção desejada.

O placar automático **não é aprovação global de qualidade**: no último turno
houve reparo de uma alegação de estado e a resposta passou a perguntar “você
conseguiu pausar?”, sem o usuário ter tentado. O verificador continua necessário;
não foi desligado para preservar uma resposta incorreta. As frases ainda podem
trazer oferta lateral ou promessa excessiva. P01 permanece parcial.

### Próxima fronteira

1. P12: interpretação canônica das perguntas de procedimento ainda não cobertas;
2. P13: recuperar capacidades por entidades sem exigir palavras “app/programa”;
3. P14: a porta prioritária deve manter o veto, mas não inventar ação/alvo na fala;
4. revalidar autoria disponível/indisponível, fronteiras mistas e evitar novas
   promessas/continuações presumidas; não declarar a rede liberada por estes testes.

P15 registra separadamente a contingência de timeout que pede ao usuário para
explicar melhor uma pergunta que já estava clara. Nenhum prazo foi ampliado para
esconder essa ocorrência. A sonda final ocorreu em outra condição de carga;
ela não prova que o timeout inicial desapareceu.

Hashes da produção ao terminar estes candidatos (incluem patches anteriores):

| Arquivo | SHA256 |
| --- | --- |
| `contexto_resposta_ia.py` | `96954fae54d28cedb2e99c76c2809d07fc36f189b2b5bf2bf317734d7561083d` |
| `contrato_fala.py` | `aace543cd124b8ed74f9c2334ff3f02b92669163076c195cd5095927ddbf9dfe` |
| `geracao_concreta.py` | `2bf0810b7cf857c1c752d342d794f8798a438dc25595a9f2a0542fd76157dadd` |
| `mapa_habilidades.py` | `bc711fa6f0de0e536e276381ac8901a3b7de4e8b1304859bf8ca373ec5ea1141` |
| `fala_capacidades.py` | `9db31a3553d0844ad23a3fd1ecfd2a1981205e8975a1f36ce050fd2eeb95367f` |
| `fundamentacao_factual.py` | `df37c10922aea752c35d6c471513306cc6c001b75e04cb4a212f911b3c5685c8` |
| `plano_turno.py` | `16e38cd7d1e3c08b594978536951cc991ed1c2ada05caf3697153935d305d4e4` |

## Moldura de procedimento — P12 / C11 — 16/09/2026

Base mantida: `main`, HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`.
Worktree já modificada; `git status --short` e diff de `modalidade_turno.py`
inspecionados antes do patch. Alterações anteriores preservadas; nenhum commit.

### Primeira fronteira e controles

“Como eu poderia aumentar o volume?” chegava como pergunta sem autorização,
mas natureza `nenhuma`; “me ensina como aumentar o volume” era conversa genérica.
As listas de verbos condicionavam o reconhecimento da explicação, embora a
moldura discursiva já fosse suficiente para distinguir ensinar de executar.
Na função pública de proteção, mesmo pausar não era reconhecido: outra camada
compensava esse caso, sem generalizar para volume. O teste canônico alcança essa
primeira fronteira antes de verificar o turno completo.

Hipóteses concorrentes falsificadas para P12:

- geração Qwen: o defeito foi reproduzido diretamente na classificação, sem LLM;
- ausência de volume no catálogo: a consulta documental retorna sistema; depois
  da correção da natureza, a mesma composição recebe documentação sem editar mapa;
- pontuação como causa: formas com e sem interrogação falham e depois passam.

### Candidato e RED/GREEN

Única produção alterada nesta etapa: `cognicao/modalidade_turno.py`. A moldura
ancorada de pergunta/ensino de procedimento seguida de forma infinitiva funciona
antes da lista operacional legada, depois das proteções prioritárias. Não amplia
a lista de comandos nem decide disponibilidade ou alvo. Não houve mudança na
rede, executores, catálogo ou reparadores. Reconhecimento morfológico limitado,
não promessa de análise completa da língua ou de verbos disponíveis no sistema.

`test_moldura_explicacao_procedimento.py`: seis ações em seis molduras,
**36 REDs / 15 controles GREEN antes → 51 GREEN depois**. Cobre volume, brilho,
áudio, notas, calendário e música; controles incluem estado, passado, hipótese,
recusa, citação, transformação e pedidos reais com/sem interrogação.
`test_explicacao_capacidades_sem_execucao.py`: volume passa nas duas rotas;
calculadora continua com dois REDs de P13. Nenhuma expectativa foi enfraquecida.

Seleção ampliada, incluindo os consumidores da modalidade: **2.556 aprovados,
duas falhas P13, 14 xfails preexistentes e 30 subtests aprovados**, em 22,31 s.
Não é a suíte global. Nenhum xfail foi criado:

```powershell
$testesProcedimento = @(rg -l --no-ignore 'classificar_modalidade_turno|analisar_protecao_operacional|avaliar_qualidade_comunicacao|validar_alegacoes_da_fala|verificar_fala_turno|validar_fala_com_fundamentacao|extrair_titulos_citados|preparar_resposta_para_execucao|MapaHabilidadesRuntime' tests --glob 'test_*.py')
& .\.venv314\Scripts\python.exe -m pytest @testesProcedimento -q --tb=short
```

### Composição real e limite posterior

Sonda `roteiro_explicacao_capacidades-20260916-085853-170785`, captura
`transporte_evidencia-20260916-085851-981951`: geração real, sem replay, mesmas
restrições de UI/microfone/voz/IoT/Gmail da rodada anterior. Persistência normal
ativa; estes dados não são feedback de treino qualificado. 12/12 respostas,
zero comandos; dez aprovações mínimas e duas falhas IoT conhecidas.

No turno 11, a modalidade tem motivo `pedido de procedimento; não é execução`;
o HTTP real leva duas mensagens, incluindo documentação viva de sistema com
“ajustar volume”, e a pergunta original. **GREEN da classificação e transporte.**

Entretanto, o Qwen acrescentou ao exemplo uma condição sobre PC remoto, sugerida
pelos limites genéricos do domínio. O reparo, disparado por
`resultado_operacional_sem_evidencia`, recebeu a premissa “O usuário relatou um
pedido” apesar da pergunta de procedimento; produziu “Como foi, dessa vez?”.
Foi rejeitado e a fala final foi “Faltou uma peça aí. Me dá mais um detalhe pra
eu não inventar moda?”. **Resposta final ainda RED**, agora registrada em P16.
Não atribuir o defeito posterior à classificação corrigida nem ao treino neural.

O resumo automático não conta esse fallback e aprova o turno por exigir apenas
ausência de comandos. A leitura manual do terminal e HTTP é a evidência de
qualidade; 10/12 não encerra P01. P13/P14 permanecem as próximas frentes já
planejadas; P16 requer investigação própria, sem retirar proteção de estado.

SHA256 final de `modalidade_turno.py`, incluindo os patches anteriores:
`403781e0c8171d6a355c9a9a0a2db6b2d3dab821566f2e64402a124212a4b8b4`.

## Recuperação documental por aliases vivos — P13 / C12 — 16/09/2026

Base `main`, HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, worktree
modificada preservada. Status e diff inspecionados; nenhum commit criado.

Primeira fronteira: `dominios_relevantes` usava termos e comandos do turno,
mas não `APPS_MAP`, fonte de nomes dos executores. Perguntas não produzem comandos
autorizados e “calculadora” não contém “app/programa/janela”. O mesmo ocorreu
com Krita, Visual Studio Code e Notepad++. Não é exceção de uma aplicação.
Falsificadas nessa fronteira: classificação incorreta (já é procedimento),
falta de capacidade (APP_OPEN catalogada) e falha de Qwen/transporte (RED anterior
à geração). Não se converteu pergunta em comando para consultar documentação.

Candidato: `MapaHabilidadesRuntime` recebe `apps_getter`, conectado à factory
real por `lambda: APPS_MAP`. Consulta nomes completos com fronteiras de palavra
e normalização existente; não copia a lista, não promove disponibilidade e não
expõe caminhos/valores no prompt. Getter tardio respeita a ordem da composição.
Falha da fonte preserva a recuperação por termos. É recuperação lexical, não
desambiguação irrestrita ou prova de instalação/estado.

Quatro testes executando declarações AST de produção reproduziram ausência de
sistema antes do patch. Outros cinco inicialmente falharam por API inexistente:
não são contados como reprodução causal. Os nove passam depois, cobrindo fonte
viva, indisponibilidade, fragmentos/desconhecidos e erro de callback.
O helper do teste de transporte usa agora a factory e os aliases extraídos de
`laylay.py`, não um mapa desconectado. Expectativas preservadas; sem getter,
o mapa continua sem conhecer os aliases. Teste AST não inicia o runtime.
Seleção focada: **60 aprovados**. Mesma seleção ampliada de C11: **2.567 aprovados,
14 xfails preexistentes e 30 subtests**, em 21,55 s. Não é a suíte global.

Sonda real: `roteiro_explicacao_capacidades-20260916-093746-337804`, captura
`transporte_evidencia-20260916-093745-215501`. Qwen real, sem replay;
UI/microfone/voz desligados, IoT simulado, Gmail sem credenciais, persistência
normal ativa. 12/12 respostas, zero comandos; dez aprovações mínimas e duas
falhas IoT conhecidas. Não usar o placar mínimo como certificação de qualidade.

Turno 4: documentação de sistema e pergunta original confirmadas no HTTP.
O Qwen gerou “Para abrir a calculadora, você pode pedir para o sistema abrir o
programa 'Calculadora'. Por exemplo: 'abre a calculadora'.” A preparação preservou
a fala; o extrator retornou `['Calculadora', 'abre a calculadora']`, o runtime
pesquisou o primeiro título na Wikipédia e entregou contingência factual.
**P13 GREEN na recuperação/composição/transporte; fala final RED por P10.**
Nome de entidade citado e exemplo em frase separada são limites abertos de C10.
Volume recebeu uma instrução nesta rodada, o que não encerra P16 já reproduzido.

Produção alterada: `mapa_habilidades.py` e uma linha de injeção em `laylay.py`.
Rede, autorização, executores, classificadores, prompts e guardiões preservados.
Próxima frente planejada: P14; P10/P16 registrados separadamente.
Hashes finais, incluindo patches anteriores:

- mapa: `b93def780646d8d681e89cb260939b6606c0ddb7087c03fadf0068cdfd4085a4`;
- laylay: `6f5de94f27727c06eb0aebef6f412974dfa03824d6a140336e8af3f0dcda7bba`.

## Autoria IoT sem troca de ação e alvo — P14 / C13 — 16/09/2026

Base mantida: `main`, HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`;
status e diff inspecionados. `comandos_imediatos.py` já tinha quatro proteções
P0 em outras rotas: preservadas. Nenhum commit criado.

**Primeira fronteira provada:** depois da classificação correta, a porta IoT
de `processar_prioritarios` reconhecia a menção protegida e respondia sempre
“desligar a luz” para perguntas de procedimento. Hipóteses/recusas também
usavam luz como alvo fixo. Essa fala encerrava o turno antes da LLM.
Falsificadas: Qwen trocando dispositivo (não era chamado), falha de classificação
(natureza correta), falta de documentação (o fluxo documental isolado passa).

**Contrato:** veto impede efeito; não concede autoria de uma resposta que muda
o pedido. A condição `bloqueia_controle_iot_por_modalidade` permanece; dentro
dela, a porta retorna `False`, delegando ao fluxo conversacional comum antes de
qualquer detector/executor subsequente. Não apagar a barreira, não interpretar
`False` como permissão, não marcar `tratado=True` sem conclusão observável.
Perguntas recebem o mesmo catálogo/contrato/transporte/verificação das demais
habilidades; recusas e hipóteses não são convertidas em procedimentos.

Produção alterada: apenas `autonomia/comandos_imediatos.py`. Rede, IoT físico,
executor, classificadores, catálogo e prompts não alterados. Contrato reutilizável
é a separação entre veto e autoria; não foram modificados outros domínios.

**Testes:** `test_iot_explicacao_autoria_compartilhada.py` reproduziu oito REDs
na primeira fronteira; quatro controles de autoria disponível/indisponível já
passavam. Depois, 12 GREEN. A proposta `ligar` é confirmada presente após parsing
do JSON e só depois rejeitada pela autoridade do turno — não verde por ação
inválida descartada no parser. Perguntas preservam texto, turno e documentação;
fala de instrução válida alcança o verificador final sem alteração.

`test_regressoes_contexto_operacional.py` exigia resposta fixa local sem LLM.
Essa expectativa protegia a implementação antiga que causava o erro; atualizada
para delegação sem fala local, mantendo o veto a chamadas operacionais. Não
modificados testes de controles reais/receipts. Seleção focada com IoT: 56 GREEN.
Seleção ampliada: **2.780 aprovados, 14 xfails preexistentes e 30 subtests**,
em 24,08 s na primeira execução. Nenhum novo xfail; não é a suíte global.
Reexecução final após reforçar o teste de parsing: mesmos números, em 24,68 s.

```powershell
$testesIoT = @(rg -l --no-ignore 'classificar_modalidade_turno|analisar_protecao_operacional|avaliar_qualidade_comunicacao|validar_alegacoes_da_fala|verificar_fala_turno|validar_fala_com_fundamentacao|extrair_titulos_citados|preparar_resposta_para_execucao|MapaHabilidadesRuntime|ComandosImediatosRuntime|RuntimeIoT' tests --glob 'test_*.py')
& .\.venv314\Scripts\python.exe -m pytest @testesIoT -q --tb=short
```

**Sondas reais, sem replay:**

- `roteiro_explicacao_capacidades-20260916-190855-889031`, captura
  `transporte_evidencia-20260916-190854-102894`: 12 respostas, 11 aprovações mínimas
  e um alerta de latência no primeiro turno (16,39 s); zero comandos. Turnos 6/7
  ensinaram ligar a lâmpada/desligar o ventilador sem trocar pelo comando antigo.
- O primeiro lançamento da sonda adicional abortou antes dos turnos porque o
  carregador exige literais AST, não compreensão de dicionário/import de opções.
  Corrigido somente o roteiro para constantes literais; não é falha de produção
  nem prova de comportamento. Captura abortada: `transporte_evidencia-20260916-191025-673768`.
- `roteiro_iot_explicacoes-20260916-191051-714954`, captura
  `transporte_evidencia-20260916-191050-556718`: oito respostas / oito aprovações
  mínimas, zero comandos; p95 5,416 s. Cobre ligar/desligar lâmpada/ventilador,
  ensino sobre tomada, brilho, recusa e hipótese. Recusa entregue: “Certo, não
  vou desligar o ventilador.” Perguntas receberam os exemplos correspondentes.

UI/microfone/voz desligados, IoT simulado, Gmail sem credenciais. Observadores
e persistência usuais ativos; dados de teste não são feedback de treino aprovado.
Nenhum ensaio físico, nenhuma configuração de dispositivo alterada.

**Limites:** seleção correta da ação/alvo não certifica toda a autoria. A sonda
extra trouxe “após o dispositivo ser refeito na configuração” e instrução para
o usuário “reler o dispositivo”, distorcendo a confirmação feita pelo sistema.
Também houve ofertas de ajudar a configurar. Esses problemas de documentação/
realização continuam em P01, não são justificativa para remover guardiões ou
declarar toda a IoT perfeita. C13 encerra a troca causada pela resposta fixa.
P10/P16 continuam pendentes e não foram corrigidos nesta etapa.

SHA256 de produção, incluindo patches anteriores:
`f0b9ebd039d0f1a32985afcb30d07a09af7ac18737c60308eb616a341453017c`.

## Papéis de citação e exemplo entre frases — P10 / C14 — 19/09/2026

Base revalidada: branch `main`, HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`;
worktree modificada preservada. Status e diff inspecionados antes do patch.

**Primeira fronteira:** a resposta correta da calculadora ainda produzia dois
candidatos a obra: nome do programa e exemplo após “Por exemplo:”. Reproduzido
diretamente no extrator e contrastado com outros nomes/domínios. Falsificadas
as hipóteses de falta de catálogo (C12 entrega no HTTP), geração defeituosa para
esse caso (resposta histórica instrui corretamente), e erro somente no último
verificador (o extrator já produz candidatos falsos antes da pesquisa).

**Contrato:** distinguir `referencia_operacional`, `enunciado` e `obra_candidata`.
Um nome explicitamente tipificado como aplicativo/arquivo/pasta/aba/janela/
dispositivo/playlist não é automaticamente obra. Referência não prova existência,
disponibilidade ou efeito e não mascara dados factuais dentro do nome ou ao redor.
“Programa” é ambíguo; exige verbo operacional imediatamente antes do substantivo.
Assistir/recomendar um programa continua produzindo candidato a obra.

Exemplos em nova frase só herdam a orientação imediatamente anterior, com moldura
de pedir/dizer/digitar/falar/escrever e leitura canônica do conteúdo como pedido
ou consulta. Não há herança através de frases intermediárias. O validador factual
calcula os papéis no texto completo antes de separar frases e mantém posições
originais, evitando perder o antecedente. Só enunciados didáticos são mascarados
para inspeção; texto entregue permanece original. Referências não são mascaradas.

Produção alterada: apenas `cognicao/fundamentacao_factual.py`. Seus consumidores
de pesquisa/verificação reutilizam o mesmo contrato; não houve exceção nominal
para Calculadora, alteração de autorização, executor, rede ou prompt.

**RED/GREEN:** oito falhas novas na primeira fronteira / 34 aprovações antes;
depois passaram. Expansão contrastiva encontrou duas falhas no candidato com
programas de TV; restringido o papel operacional sem alterar expectativas.
Arquivo final: **48 testes GREEN** (21 novos nesta etapa), incluindo texto
histórico literal, nomes distintos, programas de TV, obras após exemplos,
datas/medidas e estado de aplicativo sem evidência. Seleção ampliada pelo mesmo
comando de C13: **2.801 aprovados, 14 xfails preexistentes e 30 subtests**, 23,82 s.
Nenhum xfail novo; não é a suíte global.

**Validação real:**

- `roteiro_explicacao_capacidades-20260919-180635-477618`, captura
  `transporte_evidencia-20260919-180634-400142`: 12 respostas, zero comandos.
  Turno 4 foi replay explícito da captura de 16/09 às 09:37; não geração nova.
  Resposta histórica inteira no chat, sem pesquisa das citações ou fallback.
- `roteiro_explicacao_capacidades-20260919-180718-775411`, captura
  `transporte_evidencia-20260919-180717-734052`: geração nova em todos os turnos,
  12 respostas, zero comandos. O Qwen nomeou o aplicativo 'Calculadora'; a frase
  de instrução sobreviveu. Outra frase sobre PC conectado/compatível foi removida
  por `plataforma_sem_evidencia`: a proteção factual continua atuando, não foi
  desligada. Essa sonda ocorreu antes da restrição final para programas de TV.
- Após a restrição final, `roteiro_explicacao_capacidades-20260919-180849-999129`,
  captura `transporte_evidencia-20260919-180848-915759`: 12 respostas, zero comandos,
  novamente replay explícito só no turno 4. A resposta histórica completa chegou
  intacta; os outros 11 turnos tiveram geração nova. Processo encerrado ao final.

As três sondas tiveram 12/12 no avaliador mínimo, não certificação global de
qualidade. Ainda surgem orientações laterais/imprecisas sobre configuração,
remoto e disponibilidade em outras respostas (P01). UI/microfone/voz desligados,
IoT simulado, Gmail sem credenciais; observadores e persistência normais ativos.
Nenhum efeito físico, treino ou promoção neural. Histórico não é feedback aprovado.

Escopo encerrado: referências operacionais tipificadas e exemplo de pedido na
frase imediatamente seguinte. Citações emocionais originais de 13/09 e outros
usos não foram validados irrestritamente. Próximo item: P16, preservar o ato de
pergunta no reparo; não corrigido nesta etapa. Nenhum commit criado.

SHA256 final (inclui patches anteriores):
`325ad755e42bf88770a327bd8baedfb793f9dbb112c7c243791eb8dca0c6008f`.

## C15 — 19/09: reparo mantém objetivo e fonte do turno (P16)

Base: `main`, HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, worktree
suja preservada. Ambos os arquivos de produção já tinham alterações anteriores
(171/86 linhas no diff estatístico antes desta etapa); não atribuir o diff
inteiro a C15. Teste novo ignorado pela regra de `tests/` (P09), sem staging.

**Cadeia causal:** pergunta de procedimento → classificação correta → contrato
`explicacao_capacidades` com documentação → afirmação operacional sem prova →
projeção do reparo perde documento → prompt infere relato pelo indicador de
resultado desconhecido → resposta pergunta “como foi”. Evidência histórica:
`transporte_evidencia-20260916-085851-981951/transporte.jsonl`, volume.

**Falsificações:** os seis contrastes alcançaram classificação sem autorização
e estratégia de explicação antes de falhar no prompt; não era classificação
errada nessa fronteira. O contrato original tinha documento recuperado; não
era ausência de catálogo. A perda ocorria em `_resumo_reparo`. Relato explícito
continua exigindo apenas reconhecimento e não pergunta nova.

**RED:** `tests/test_reparo_preserva_objetivo_turno.py`, nove falhas causais e
um controle aprovado antes de produção. Inclui seis domínios, projeção da fonte
e processamento real da resposta com transporte substituído. As asserções do
callback são externas à captura para não serem engolidas pelo tratamento de
exceção da produção. Resposta inventada no segundo passe continua rejeitada.

**Contrato:** reparar uma alegação não altera o ato nem o objetivo do turno.
A tarefa é do contrato, e sua fonte selecionada deve sobreviver à projeção.
Ausência de prova de efeito não prova tentativa, relato, sucesso ou falha.
Esse princípio vale para todas as habilidades; não há frase pronta por domínio.

Produção alterada somente:

- `cognicao/qualidade_comunicacao.py`: instrução focal segue atos/núcleo/objetivo
  do contrato, diferencia explicação de relato e não concede ações.
- `cognicao/validacao_contrato_fala.py`: projeta o documento já selecionado
  somente para a estratégia de explicação, sem nova recuperação de contexto.

Classificador, guardiões, catálogo, personalidade-base, composição, executores
e rede não foram modificados. O sinal de resultado desconhecido continua ativo.

**GREEN:** dez testes novos; 159 na seleção focada. Seleção ampliada por usos
de classificação, proteção, qualidade, guardião, verificação, fundamentação,
processamento, catálogo, comandos imediatos e IoT: **2.811 aprovados, 14 xfailed,
30 subtestes aprovados**, 23,80 s. Não é suíte global; nenhum xfail novo.

**Runtime:** `roteiro_explicacao_capacidades-20260919-181949-614989`, captura
`transporte_evidencia-20260919-181948-526867`. Somente o rascunho histórico de
volume foi replay; os reparos foram novas respostas do `qwen3:4b-instruct`.
O HTTP real de ambos os reparos (aba e volume) recebeu a documentação e a
estratégia corretas. Volume chegou ao chat como:

> Para aumentar o volume, você pode usar o comando "ajusta o volume". Como
> exemplo, diga: "ajusta o volume para 80%".

Sem presumir relato passado, pedir “como foi” ou usar contingência nesse turno.
A geração ainda acrescentou uma terceira frase indevida sobre PC remoto;
`plataforma_sem_evidencia` a removeu antes da entrega. Isto valida o reparo
de tarefa, **não** prova que a geração parou de inventar requisitos. P01 aberto,
também observado na fala IoT que transfere ao usuário a releitura do dispositivo.

Doze respostas e zero comandos; 12/12 no avaliador mínimo, sem equivaler a
qualidade global aprovada. p95 8,224 s, máximo 9,801 s. UI/microfone/voz
desligados, IoT simulado, Gmail sem credenciais. Observadores e persistência
normais ativos; histórico da sonda não é treino aprovado. Processo concluído.

SHA256 final (inclui patches anteriores):

- qualidade_comunicacao: `96625988290244cb6b5668ed977502c026dff546030c04847d94247a3207a7c6`
- validacao_contrato_fala: `0492eb8a12e129d831bc1955b08f309263cba151c9005e717580aea525d00630`

Próxima fronteira proposta: relevância dos limites e das responsabilidades por
capacidade/rota na documentação (P01), sem enfraquecer a verificação factual.
Nenhum commit, treino ou promoção neural nesta etapa.

## C16 — 19–20/09: escopo e responsável dos limites documentais

**Bases:** início em `main`, HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`,
worktree suja preservada. Após a pausa, HEAD
`c8b4c26f31deabd21168a458273896f398e2ddf0` ("aprimoramento elevado 0.1"),
worktree limpa e candidato de produção já incorporado por commit externo.
Não reapliquei o patch nem alterei travas. A sessão do pytest anterior não
estava mais acessível; a seleção foi rodada novamente e concluída em 20/09.

**Primeira fronteira:** o contrato central de sistema tinha como único limite
"só envia ao PC remoto quando versão, saúde e capacidade anunciada são
compatíveis". A projeção do domínio entregava essa frase indiferenciadamente
para perguntas de volume e aplicativos locais. A documentação não explicitava
o alcance da condição. Em IoT, "confirma controle somente após reler o
dispositivo" não identificava o responsável pela verificação.

**Falsificações:** `executor_audio._executar_volume` distingue `pc_b` de
callbacks locais; os 12 testes existentes de áudio passaram antes do patch,
incluindo rotas local/remota. Logo, controle local não depende intrinsecamente
de PC remoto. No controlador IoT, após `definir_estado`, é o próprio controlador
que chama `consultar_estado` e confere o alvo; não há uma etapa de releitura
atribuída ao usuário. O texto remoto já vinha do catálogo canônico, não precisava
ser inferido do histórico. Não declarar que isso explica toda invenção da LLM.

**Contrato reutilizável:** regra documental tem escopo, condição de aplicação
e responsável. Não se promove limite de outra rota a requisito universal nem
se transfere uma verificação interna ao usuário. Documentação descreve como
usar; não prova estado atual, autorização ou sucesso de ação.

**Candidato mínimo:**

- `especialistas/capacidades.py`: regras contextuais de sistema e IoT no
  cadastro existente. O texto `limites` legado deriva dessas regras. Limites
  de outros domínios preservados, sem inventar escopos para eles.
- `especialistas/mapa_habilidades.py`: projeta as regras estruturadas quando
  disponíveis, em vez de achatá-las. Mantém a seleção e disponibilidade.
- `personalidade/fala_capacidades.py`: orientação geral sobre condição e
  responsável, sem respostas fixas nem novos parsers por habilidade.

Não alterados: roteadores, executores, classificadores, guardiões, reparador,
rede ou configuração operacional. A disponibilidade negativa continua sem
exemplos de execução; pergunta segue sem autoridade. Nenhuma nova habilidade.

**RED/GREEN:** nove testes em `tests/test_limites_documentais_contextuais.py`:
sete REDs causais e dois controles verdes antes do candidato. Com os 12 testes
de áudio, primeiro resultado foi 7 falhas / 14 aprovados. Após candidato,
seleção focada com catálogo, composição, autoria, reparo e conexões: 97 aprovados.
Em 20/09, seleção ampliada incluindo `consultar_capacidade`: **2.829 aprovados,
14 xfailed preexistentes, 30 subtestes aprovados**, 26,39 s. Não é suíte global.
O teste novo permanece ignorado pela regra existente de `tests/` (P09).

**Runtime real, sem replay:**
`roteiro_explicacao_capacidades-20260920-085230-637670`, captura
`transporte_evidencia-20260920-085228-787217`. Modelo HTTP `qwen3:4b-instruct`.
O HTTP de calculadora, lâmpada e volume recebeu escopo/condição/responsável;
a regra remota permaneceu somente no documento de sistema. Geração nova:

- Calculadora/volume: explicitou sistema operacional local, sem exigir outro PC.
- IoT: Laylay se atribuiu verificar a configuração; não exigiu releitura pelo usuário.
- Não houve comando operacional. Doze respostas, 11 aprovações mínimas, um
  alerta; p95 11,363 s, máximo 15,204 s. Sem certificação de qualidade global.

**Limites importantes:** em quatro turnos o verificador voltou a classificar
exemplos como obras, pesquisar seus títulos e cortar instruções (P10). Entre
eles, `como em 'abre a calculadora'`, `pedir para mim: 'ligue a lâmpada'` e
exemplos com vocativo `Laylay, ...`. Em volume, removeu também a frase sobre
controle local por `plataforma_sem_evidencia`; a fala restante ensinou abrir
o controle de volume, não apenas pedir o ajuste. Catálogo/projeção validados
no escopo; **entrega final ainda parcial**. Guardião não foi enfraquecido.
Esses resultados estão separados em P10/P01 para a próxima investigação.

UI/microfone/voz desligados, IoT simulado, Gmail sem credenciais. A extensão
Chrome conectou durante a sonda; não houve comando operacional. Observadores,
persistência e pesquisa temática normais permaneceram ativos (houve inclusive
consulta equivocada à Wikipédia). Histórico de teste não é treino aprovado.
Processo concluído e ausência de processos Python conferida ao final.

SHA256 final da produção:

- capacidades: `3a40874359e34235d35b56a0f8578f57a931517b59720fb40479c44cd71a72ec`
- mapa_habilidades: `323ccb338df928951c448c875120053b12c7eae03d64a715df13891af6574efc`
- fala_capacidades: `5b83e87612a9920df356eddde71e5a975432cc758c4079ff5006b1d720dbd334`

Nenhum commit criado pelo agente; nenhum treino ou promoção neural.

## C17 — 20/09: exemplo de fala não depende de ser comando executável

Base `main`, HEAD `c8b4c26f31deabd21168a458273896f398e2ddf0`. Antes do patch,
somente os dois relatórios de C16 estavam modificados; preservados. Produção
alterada apenas em `cognicao/fundamentacao_factual.py`. Regressões no arquivo
existente `tests/test_citacao_didatica_nao_e_obra.py`, ignorado pelo Git (P09).
SHA anterior: `325ad755e42bf88770a327bd8baedfb793f9dbb112c7c243791eb8dca0c6008f`.

**Cadeia causal:** resposta com orientação → extração do papel da citação →
exemplo vira obra candidata → guardião exige fonte → orquestrador pesquisa
o suposto título → corta a instrução. Localizada a primeira divergência no
classificador compartilhado de citações, antes da pesquisa e da fala.

**Falsificações e limites:**

- Falha reproduzida diretamente no extrator, sem LLM, histórico ou rede:
  não era resultado ruim do provedor de pesquisa nem apenas variação do Qwen.
- `ligue a lâmpada`, `desligue o ventilador` e `abre a calculadora` já são
  pedidos canônicos; mesmo assim viravam títulos sob as molduras históricas.
  Logo, falta de reconhecimento do verbo não explica todos os casos.
- `aumente o volume`, com ou sem vocativo, retorna natureza `nenhuma`. O
  verificador de exemplos não deve exigir que a gramática operacional consiga
  executar qualquer frase citada. Isso não autoriza ampliar a execução aqui.
- `Abra os Olhos` é lido como pedido pelo classificador; por isso a moldura
  externa continua indispensável para distinguir título de enunciado.

**Contrato:** o papel da citação vem de sua relação linguística local. Referência
tipificada entre verbo e exemplo não encerra essa relação; nome de obra ou nova
frase não relacionada não herda a isenção. Vocativo sob orientação de pedido
identifica um enunciado, não uma utterance autorizante ou prova de efeito.

**Candidato:** preservar complemento de destinatário; reconhecer conector de
exemplificação e frase seguinte com orientação; abstrair apenas referências já
tipificadas ao examinar o prefixo; reutilizar `analisar_identidade_turno` com
texto normalizado, em vez de cadastrar comandos ou vocativos privados. Pedidos
cujo objeto é filme/música/livro etc. não ganham escopo de instrução só por
terem um exemplo depois. Datas, medidas e estados vizinhos continuam verificados.
Não alterados: gramática operacional, pesquisa, executor, catálogo ou rede.

**Testes:** primeira rodada com 11 REDs causais e 54 aprovados antes da produção.
Após candidato: 65 aprovados. Acrescentadas três integrações com composição,
estado compartilhado, verificador e montagem de fundamentação reais; apenas o
transporte de pesquisa é observado, sem evidência inventada. Elas provam que
exemplos não disparam pesquisa e título real continua exigindo fonte. Total
focado: **68 aprovados**. Seleção ampliada final: **2.849 aprovados, 14 xfailed
preexistentes e 30 subtestes**, 24,40 s. Não é suíte global nem teste de caos.

**Runtime:** Pedro encerrou a sessão após solicitação; o agente não a matou.
Usado `sonda_transporte_evidencia.py` com o roteiro de 12 perguntas, IoT simulado,
voz/UI/microfone desligados e Gmail sem credenciais. Observadores e persistência
normais ativos; Chrome conectou sem receber comando operacional.

- `roteiro_explicacao_capacidades-20260920-090155-946269`, captura
  `transporte_evidencia-20260920-090154-856571`: replay explícito somente da
  resposta histórica de lâmpada de 08:52. A instrução “pedir para mim:
  'ligue a lâmpada'” chegou inteira ao chat; nenhuma pesquisa de obra ou corte.
  Doze respostas, zero comandos, 12/12 no avaliador mínimo, p95 4,596 s.
- `roteiro_explicacao_capacidades-20260920-090237-770804`, captura
  `transporte_evidencia-20260920-090236-732295`: replay explícito somente da
  resposta histórica de volume. O trecho “Por exemplo: 'Laylay, aumente o
  volume'” foi preservado. A frase seguinte sobre PC/local ainda foi cortada
  por `plataforma_sem_evidencia`, fronteira distinta preservada. Doze respostas,
  zero comandos, 12/12 mínimo, p95 3,608 s; sem pesquisa indevida de citações.

As demais chamadas ao modelo `qwen3:4b-instruct` tiveram geração nova, não replay.
O placar mínimo não certifica a qualidade geral: ainda houve negação de controle
de áudio na resposta de retomada e orientação IoT de conferir configuração.
P01 continua aberto. Nenhuma conclusão sobre títulos emocionais ou todas as
formas possíveis de citação. Próxima fronteira delimitada: capacidade local
vs. alegação externa de plataforma, sem retirar a verificação de fatos.

SHA final: `8ca0d0d61d7a505066d898c6c77ca58ee865b0bb11f4a79a990d7370d79ba62c`.
Nenhum commit, treino, promoção neural ou ação física. Histórico de teste não
constitui feedback aprovado para treinamento.

## C18 — 20/09: documentação local não é evidência de plataforma externa

Base `main`, HEAD `c8b4c26f31deabd21168a458273896f398e2ddf0`. Worktree já
continha C17 em `fundamentacao_factual.py` e alterações nos dois relatórios;
preservadas. Produção alterada nesta etapa somente em `fundamentacao_factual.py`
e `plano_turno.py`. Novo teste `tests/test_capacidade_local_nao_e_plataforma.py`
continua ignorado pelo Git conforme P09; não houve mudança de ignore ou commit.

**Primeira fronteira RED:** a resposta de volume continha a frase “Eu vou usar
o sistema operacional local para ajustar o volume do seu PC, sem precisar de
conexão com outro dispositivo.” A extração factual classificava PC como
plataforma, independentemente da relação expressa. O verificador recebia
fundamentação temática, mas não a documentação de controle local já selecionada
no contrato de fala. Resultado: `plataforma_sem_evidencia` e retirada da frase.

**Falsificações:** o corte foi reproduzido deterministicamente, sem modelo,
histórico ou pesquisa; não dependia de nova invenção do Qwen. A documentação
canônica estava disponível antes da validação, afastando ausência do catálogo.
Por outro lado, liberar qualquer ocorrência de PC ou misturar o catálogo com
evidência factual permitiria inferir compatibilidade de jogos sem fonte.

**Contrato e candidato mínimo:** documentação disponível sustenta descrição
da capacidade, não existência de obra, compatibilidade nem efeito executado.
O plano só encaminha a fonte quando origem é `mente_unica`, ID e âncora são do
turno atual, estratégia é explicativa e não há autorização, comando ou execução.
O validador aceita uma família gramatical delimitada de descrição em primeira
pessoa do sistema operacional local, somente para recurso presente na regra
`controle_local`, de responsabilidade da Laylay e disponibilidade positiva.
Somente o token PC dessa descrição deixa de ser alegação externa de plataforma;
as demais verificações permanecem. JSON inválido e documentos ausentes, remotos,
indisponíveis ou de outro turno não concedem essa sustentação.

Não se trata de inferência semântica geral: paráfrases fora da família e recursos
não documentados conservam o caminho estrito anterior. O princípio é reutilizável
para recursos documentados; não há exceção para uma pergunta ou número de turno.
Catálogo, prompt, gramática operacional, executores, rede e pesquisa não alterados.

**Testes:** antes da produção, quatro REDs causais e 20 controles aprovados.
Após candidato, os 24 contrastes passaram: quatro descrições locais, oito
documentos inválidos/inadequados, oito alegações externas e quatro outros fatos.
Com citações e regressões de plataforma: **108 aprovados**. Seleção ampliada:
**2.873 aprovados, 14 xfailed preexistentes e 30 subtestes**, 24,80 s.
Sem novos xfails; não é declaração de suíte global ou caos verde.

**Prova no caminho real:**

- Roteiro: `resultados_testes/roteiro_explicacao_capacidades-20260920-163307-753819`.
- Captura: `resultados_testes/transporte_evidencia-20260920-163305-049150/transporte.jsonl`.
- Usado `sonda_transporte_evidencia.py --roteiro roteiro_explicacao_capacidades.py`
  com captura de preparação e replay somente do texto “como eu poderia aumentar
  o volume?”, vindo de `transporte_evidencia-20260920-085228-787217/transporte.jsonl`.
- O turno 11 entregou integralmente a mesma resposta histórica, inclusive a
  frase antes cortada. Isso prova o caminho de validação/entrega sobre a geração
  capturada, não uma geração nova desse turno. Demais chamadas ao Qwen foram novas.
- Doze respostas, zero comandos operacionais, 11/12 no avaliador mínimo,
  zero fallbacks conversacionais registrados, p95 10,27 s.
- Turno 3 ainda falhou: “A Laylay não controla o áudio diretamente...” ao ensinar
  retomada. P01 permanece aberto; próxima fronteira é a negativa de capacidade
  frente ao documento realmente recebido, não remover outro guardião às cegas.

UI/voz/microfone desligados, IoT simulado e Gmail sem credenciais. Chrome conectou;
observadores e persistência normais permaneceram ativos. Não foram realizados
comandos operacionais nem testes de efeitos físicos. Processo terminou com
exit code 0 e ausência de processos Python conferida ao final. A sessão do
usuário não foi encerrada pelo agente. Histórico da sonda não é treino aprovado.

SHA256 da produção ao validar:

- fundamentacao_factual: `a1d4c679895671156e27cf19ce4bede52bd8bbc1c0ae612f7a9ee8f171a876ea`
- plano_turno: `3a69de2559ba765d0c8fa6c8dd3d40ee4efb9dcf2c4432432bde6f91107cefd6`

Nenhum commit, treino ou promoção neural nesta etapa.

# Mapa causal da conversa — investigação por contratos

20/09/2026. Pedido de Pedro: agrupar causas, não continuar somando correções por
frase ou habilidade. Esta etapa é diagnóstico e plano; não é C19 nem correção
de produção. Mantém os IDs históricos do registro central.

## Base e escopo

### Adendo de 23/09 — complemento do contrato de entrada no DEV

O texto recebido já aparece na evidência do Pedro, mas o espelho promovia
prompts vazios de stdin a eventos SYSTEM. Na mesma família de observabilidade,
separar mensagem recebida de controle de apresentação: filtrar apenas marcadores
inteiros sem conteúdo em stdout, mantendo a escrita no console e stderr.
Cinco REDs; 68 testes verdes, incluindo leitor, espelho e ponte autenticada reais.
Histórico preservado; validação na sessão do Pedro após reinício ainda pendente.

### Adendo de 23/09 — falha ao ler receipt não pode pular a validação

Na fronteira operacional compartilhada, a exceção de serialização virava
dict vazio, que pulava o guardião mantendo a fala otimista. A mesma leitura
inválida podia reservar deduplicação usando atributos externos ao receipt.
Agora um único retrato alimenta validação e deduplicação; ilegível/vazio produz
incerteza observável e não reserva confirmação. Não se infere falha do executor.
15 REDs antes do patch; 173 testes verdes depois, com direção e fila reais sem
áudio físico. Sessão aberta preservada; prova ao vivo ainda pendente.

### Adendo de 23/09 — canal aberto não é ocupação; espera não é cancelamento

Três contratos distintos, sem consolidá-los com P01 ou encerrar P05:

1. Retomada proativa: chat aberto não pode bloquear para sempre. Porteiro e
   callback de composição usavam flags persistentes em lugar de atividade viva.
   Quatro REDs reproduzidos; retomada de briefing/e-mails integrada com fila real,
   preservando prioridade do usuário e bloqueios contextuais.
2. Briefing: timeout do observador não cancela o trabalho. Pendência e recibo
   tardio devem sobreviver aos 45s sem gravar sucesso antecipado ou duplicado.
3. DEV: prompt de teclado não é mensagem recebida. A entrada deve ser registrada
   no coordenador comum, independentemente de eco da interface, com sanitização.

Estado: GREEN local/integrado (97 testes); sessão real/áudio pendentes. Achado
operacional de receipt não serializável e avisos LRCLIB/sincronização permanecem
separados no registro central.

### Adendo de 23/09 — P01, necessidade de desenvolvimento vs rota curta

`classificar_proporcao` reconhecia explicação, mas a escolha de rota ignorava
esse perfil; pedido curto de passo a passo recebia instrução de duas frases,
contrato de três e teto rápido de 256 tokens. Falha de composição demonstrada
por seis REDs; não é prova de insuficiência do Qwen nem de truncamento (o bruto
histórico parou em 58 tokens por `stop`, mantendo o tema no histórico).

Rota em `fluxos_conversa.py` e orçamento inicial de `contrato_fala.py` agora
reutilizam o perfil existente. Não alterados pesos, verificador, executor,
autoridade ou prompt-base. Saudação mantém rota rápida e limites específicos
continuam soberanos. Duas sondas completas sem replay confirmam instrução
proporcional no HTTP e entrega de três/cinco passos. Não é avaliação universal:
erros de contrário/inverso e recusa de `quero im` reapareceram na geração.
Próxima fronteira de P01 é essa continuação incerta, não mais espaço de tokens
ou novas exceções no verificador. Evidências e limites no registro central.

### Adendo de 23/09 — P01, ensinar não é reformular a própria fala

Sonda de 21 turnos em sete assuntos provou que a intenção de ensinar e o
orçamento de resposta chegam ao Qwen, porém traduções, definições e exemplos
errados nascem na geração. A nota de sucesso do roteiro só cobre ausência de
comandos/entrega/latência. O contrato anterior de `não entendi` usava a fala
potencialmente errada da assistente como âncora; agora retoma o pedido recente
do usuário (`reensino_didatico`), validado nos sete retornos do runtime. Isso
resolve a referência, **não** a factualidade.

Uma segunda chamada ao mesmo modelo aprovou sete rascunhos como sem erro,
inclusive falsos exemplos em inglês, física e plantas. Assim, autocrítica
sem observação independente foi falsificada como guardião. A próxima fronteira
é uma base de conhecimento observável, com recuperação de fontes, avaliação
da relevância e conferência das afirmações antes da fala. Cinco fontes são
um teto de investigação, não um número a preencher com sites fracos. O fluxo
e seus portões estão em `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md`; P01 permanece
aberto até ganho factual comparado no runtime. Interferência IoT por `planta`
e artefato `nn` são achados separados, não novas causas assumidas de P01.

### Adendo de 23/09 — P01, recuperação não equivale a alegação sustentada

O coletor multifonte foi implementado e leu até cinco sites independentes no
runtime. As sondas reais de 21 turnos com a evidência no prompt caíram para
6/21 e 7/21 sem alertas operacionais (base anterior 18/21), com timeout e
erros de conteúdo ainda visíveis. A primeira fronteira RED não é mais apenas
"sem página": mesmo quando o trecho define a planta baixa como vista de cima,
o Qwen a ensinou como vista de baixo. Também inventou exemplo botânico e
produziu exemplo de `for` semanticamente errado. Contrato faltante: afirmação
central e exemplo só entram na fala após conferência com a fonte ou com um
verificador determinístico apropriado. Fonte lida é contexto, não prova da
fala gerada. A influência multifonte ficou desativada por padrão, sem fechar
P01. Falha intermitente do buscador e interpretação IoT de `planta` são
fronteiras separadas.

Prova focal posterior: `validar_fala_com_fundamentacao` aceitou sem problema
“planta baixa ... de baixo para cima” diante de “vista superior” no próprio
resumo/fonte. A fonte existe e a geração já chegou falsa ao verificador; não
atribuir o RED a ausência de busca. Uma checagem semântica independente ainda
precisa ser medida com controles inéditos antes de integrar ao porteiro.
Separadamente, o detector IoT pesquisava RGB de `planta` porque “luz” resolvia
o alias da lâmpada e uma expressão regular genérica aceitava qualquer frase
como possível ajuste cromático. A consulta livre agora exige ato direto de
ajuste; GREEN em 34 testes IoT, inclusive o detector registrado na composição
real. Ainda falta uma conversa fim a fim com geração pelo modelo.

Sonda de auditoria do Qwen com fonte real: sete rótulos factuais corretos,
somente três com citação literal e índice de fonte consistentes. Isso sustenta
o uso de uma checagem com evidência como hipótese de trabalho, mas falsifica
a ideia de publicar com base apenas no rótulo do mesmo modelo.

A repetição no runtime falsificou que o resolvedor de RGB era a única barreira:
o retrato marcava `operacao_explicita=iot` por qualquer menção de “luz” e
vetava a pesquisa. Corrigido no owner do retrato pelo ato comunicativo; uma
nova sonda confirmou fonte no plano e ausência de comando. A busca ainda
recebia “com um exemplo” como parte do tema; o extrator agora separa formato
de assunto e a sonda seguinte registrou o tema limpo. Esta última expirou
na chamada principal ao Qwen (13 s), portanto não valida qualidade da fala.

### Adendo de 22/09 — P10, classificação residual substituída por indícios

O ramo `desconhecido → obra` era a primeira divergência. Agora só relações
tipificadas nomeiam obras; aspas indeterminadas continuam visíveis aos outros
verificadores. Papel da citação é resolvido no texto completo e o contexto
nominal é compartilhado com o chamador de pesquisa, sem virar evidência factual.
Produção: owner `fundamentacao_factual.py` e passagem de contexto no
`orquestrador_turno_runtime.py`; sem alteração de geração, rede ou execução.

430 testes selecionados aprovados / 13 xfails preexistentes. Runtime com replay
explícito do turno 3 preservou as cláusulas que antes eram removidas e não
pesquisou `o contrário`; código zero. Não certifica a matemática gerada nem
gramática universal. Sonda `roteiro_ensino_divisao-20260922-173131-509832`.
Turnos novos voltaram a prometer sem ensinar e recusar esclarecimento como
comando inválido: defeitos já no HTTP, **P01**, próxima fronteira. Detalhes,
revisão da expectativa ambígua e limites constam no registro central.

### Adendo de 22/09 — ensino, P10 e P01 não são uma só causa

O passo a passo histórico foi gerado e depois mutilado: pergunta citada e nome
de método viravam obras no extrator de papéis. P10 ampliado para enunciado
instrutivo, referência conceitual e retomada explícita da fala do usuário.
Produção alterada somente em `fundamentacao_factual.py`; 19 testes próprios,
212 aprovados/13 xfails na seleção e passos preservados em duas gerações reais.
Fatos externos e títulos vizinhos seguem sob verificação; isso não valida
automaticamente matemática nem todo método citado.

A classificação residual continua transformando aspas de ênfase e predicados
em obras: `desfaz`, `o contrário` e perguntas explicativas de outra forma
reapareceram no runtime. É limite da mesma P10, não novos bugs por palavra.
Investigar evidência positiva do papel de obra vs papel ainda desconhecido,
sem liberar todas as citações. Já distinção confusa contrário/inverso e recusa
de capacidade após `quero im` vieram na geração; P01 permanece separado.
Placar 4/4 da segunda sonda significa ausência de comandos, não ensino aprovado.
Artefatos, falsificações e achado de resumo/orçamento no registro central.

### Adendo de 22/09 — P04 é instrumentação, não falha do ADD

Observação independente mostrou `add_and_verify=0` e
`add_and_verify_result=1`, com a faixa correta persistida. O contador antigo
observava apenas o wrapper bool, que a operação moderna não usa. Instrumentação
corrigida no teste composto, preservando a expectativa de exatamente um ADD e
zero após CREATE falho. Incluída a publicação ausente no harness e asserções
de receipt antes da fala; não alterado código de produção nesta rodada.
Quatro testes do composto/medição, 24 focados e 352 regressivos passaram.
P04 encerrado nesse escopo; P03 continua separado e não foi "resolvido" por
trocar um contador. Detalhes e falsificações no registro central.

### Adendo de 22/09 — P03, ordem de publicação

P03 é uma raiz operacional, não contaminação P19 nem prova de causa compartilhada
com o contador P04. O feedback já recebia o callback canônico; chamava-o depois
da fala. Corrigida a sequência **efeito → publicação → conclusão** em
`fluxos_conversa.py`, preservando guardião e armazenamento. Ausência/falha do
publicador não permite confirmação otimista nem repetição automática do efeito.
16 testes novos, histórico P03 verde e 348 regressivos aprovados; composição
importada de `laylay.py` grava em disco temporário e observa o receipt antes da
fala. Isso não certifica sessão completa com áudio/Chrome. P04 ainda falha no
contador; registro central mantém a evidência separada. Os dois REDs anteriores
do adaptador já estavam corrigidos pelo trabalho paralelo ao iniciar a rodada.

### Adendo de 22/09 — P18/P19, sem fundir causas

- Base desta investigação: `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`,
  worktree paralela preservada. A base de 20/09 abaixo continua histórica.
- **P18 → F1:** horizonte/local descartados na continuidade; aprofundamento
  recebido como consulta de hoje; objetivo de esclarecer certeza ignorado.
  Owner: continuidade canônica → detector → executor informativo. Não há
  evidência de que briefing seja a causa dessa resposta.
- **P19 → F2:** histórico factual incluído no pedido de autoria de outro
  receipt; paráfrase passa pela verificação de repetição literal. Owner:
  `personalizar_confirmacao_llm`, usando o preparo fechado já existente.
  Reproduzido em playlist, IoT e arquivos; não exige alterar esses executores.
- Princípios comuns, causas distintas: **preservar escopo para interpretar;
  restringir evidência para confirmar**. Contexto útil não é fonte irrestrita
  de fatos de outro domínio. Não aumentar a contagem de raízes apenas porque
  três habilidades expuseram a mesma vulnerabilidade de autoria.
- Provas/limites no registro P18/P19: 19 testes próprios verdes, seleção
  ampliada com 189 aprovados e dois REDs da frente paralela tratado/receipt;
  runtime meteorológico somente validou comunicação de falha (fontes em
  timeout), não o sucesso ponta a ponta. Nenhuma promoção neural.

### Base histórica de 20/09

- Branch `main`, HEAD `c8b4c26f31deabd21168a458273896f398e2ddf0`.
- Worktree inicial modificada: `fundamentacao_factual.py`, `plano_turno.py`,
  `REGISTRO_PROBLEMAS_E_CORRECOES.md` e `RELATORIO_COLETA_DEBUG_20260914.md`.
  C17/C18 preservados; HEAD sozinho não representa o comportamento auditado.
- Evidência real relida: captura `transporte_evidencia-20260920-163305-049150`
  e conversa `roteiro_explicacao_capacidades-20260920-163307-753819`, turno 3.
- Sem nova abertura da Laylay, chamada ao modelo, efeito externo ou treino.
- Novo teste local ignorado pela regra `tests/` (P09):
  `tests/test_coerencia_capacidade_documentada.py`. Sem staging/commit.

## Contagem sem duplicação

O registro possui 16 itens, não 16 raízes independentes ou 16 bugs ativos.
P01 é o resultado abrangente da qualidade de explicação; P10/P11/P12/P13/P14/P16
são seis itens da cadeia que o influencia. São sete itens relacionados, não
sete ocorrências da mesma função defeituosa. P15 acrescenta uma oitava frente
relacionada à conclusão do turno, agora com perda de causa reproduzida localmente.

P02/P03/P04/P05/P06/P07/P08/P09 ficam fora dessa consolidação. P03/P04 não têm
raiz compartilhada comprovada; P07 é limite de cobertura, não bug reproduzido.
Não reabrir todos os casos corrigidos nem somar P01 às suas consequências como
se fossem defeitos independentes.

## Três contratos; causas distintas dentro deles

| Frente | Itens relacionados | Evidência e limite |
| --- | --- | --- |
| F1 — significado preservado | P10, P11, P12, P14, P16; consequência em P01 | Citação, pergunta, alvo e objetivo já se perderam em owners diferentes. São causas locais demonstradas; não se comprovou um único parser responsável por todas. Correções existentes passam nos casos cobertos. |
| F2 — capacidade, fonte e escopo coerentes | P13 e P01; interação com P10/P16 | Recuperação e transporte históricos corrigidos. Hoje há projeção documental reduzida e uma lacuna compartilhada na conferência de negativas específicas, reproduzida em quatro domínios. |
| F3 — causa técnica preservada | P15; sintomas parecidos com P01/P16 | Sentinelas distintas viram booleano e chegam à contingência sem a categoria. Três falhas técnicas reproduzidas como pedidos de esclarecimento indevidos. Não explica a origem da latência. |

Essas frentes se sobrepõem por contrato; não são contagens aditivas de raízes.
F1 não deve virar pretexto para substituir toda análise de linguagem de uma vez.

## Caminho e donos atuais

| Fronteira | Dono existente | Informação que deve sobreviver |
| --- | --- | --- |
| Entrada → leitura | `modalidade_turno.classificar_modalidade_turno` | Utterance, modalidade, objetivo; autorização separada de explicação |
| Leitura → fonte | `MapaHabilidadesRuntime.evidencia_conversacional` / `_documentacao_explicativa` | Domínio, disponibilidade viva, limites e vínculo texto/ID; não estado do mundo |
| Fonte → contrato | `contrato_fala.construir_contrato_semantico_fala` | Fonte do catálogo, ID, objetivo e ausência de autorização |
| Contrato → envio | `ContextoPromptRuntime.preparar_envio_modelo` → `preparar_payload_llm` | Documento e pergunta; contexto fechado no caminho explicativo |
| Saída → conferência | `avaliar_qualidade_comunicacao` / `validar_aderencia_contrato_fala` / `verificar_fala_turno` | Alegação da resposta comparada com a fonte adequada, não apenas com palavras isoladas |
| Rejeição → reparo | `_resumo_reparo` → `montar_mensagens_reparo_comunicacao` | Mesmo objetivo/fonte; rascunho não vira evidência; nenhuma autorização nova |
| Falha técnica → conclusão | `processamento_resposta_ia` → `_fala_contingencia_sem_llm` → `fala_contingencia_natural` | Categoria técnica conhecida, sem inventar ambiguidade do usuário |

Reutilizar esses owners. Não criar segundo catálogo, segunda autoridade ou
executor que reinterpretaria novamente a intenção.

## Caso de prova: negativa de retomada

No HTTP real, a pergunta foi exatamente “como eu poderia retomar a música?”.
O pedido tinha somente system + user, documento `musica`, `estado=disponivel`,
descrição “buscar e controlar música” e o limite genérico “o cliente remoto
confirma entrega, mas controles globais não provam que o áudio mudou”.
Preparação e envio preservaram esse documento. A resposta entregue negou
controle de áudio. Não houve comando operacional.

Falsificações nesta amostra:

1. **Catálogo sumiu no transporte:** falso; estava no HTTP enviado.
2. **Histórico errado induziu diretamente esta chamada:** falso; histórico não
   estava no pacote fechado. Isso não audita todos os usos da memória.
3. **O verificador inventou a negativa:** falso; ela já está no HTTP 200, antes
   da limpeza. Porém o bruto também trazia duas frases de instrução com exemplos
   no infinitivo. O terminal registra pesquisa de “tocar a música” e corte por
   `obra_sem_evidencia` / `alegacao_especifica_sem_fonte`. A fala final ficou só
   com a negativa. Portanto há duas falhas: geração/conferência incoerente (F2)
   e papel dos exemplos perdido (F1/P10). Não declarar que o guardião nada fez.

Não foi provado que só o limite genérico causou a geração. Isso exige ablação
controlada do documento com o mesmo modelo, não mais instruções às cegas.

### Duas fronteiras diferentes em F2

**Documentação:** `CAPACIDADES` tem `confirmacao_oferecida`,
`evidencia_confirmacao`, `autorizacao`, dependências e owner por intent.
`_documentacao_explicativa` reduz para descrição/estado/exemplos/motivo/limites
por domínio. A perda de granularidade é provada por código; sua contribuição
causal para a negativa do modelo ainda é hipótese. A projeção reduzida tem uma
finalidade legítima (não despejar o catálogo todo), que precisa ser preservada.

**Conferência:** `validar_aderencia_contrato_fala` confronta negações de identidade
através de `_NEGACAO_IDENTIDADE_OPERACIONAL` e lista de domínios confirmados.
Ela não faz comparação geral entre negativa específica, ação/escopo e documento
vivo do turno. A documentação existe, mas não é suficiente para esse detector.

Quatro REDs canônicos reproduzidos, sem modelo nem executor:

- Música: negativa histórica sobre controlar áudio.
- Sistema: “Não consigo abrir programas no seu computador.”
- IoT: “Não consigo controlar dispositivos inteligentes.”
- Navegador: “Não consigo fechar abas do navegador.”

Em todos: classificação/autoridade e fonte chegam corretas; a conferência aceita
com `problemas=[]`. Oito controles passam: quatro domínios indisponíveis podem
ser negados e quatro limites de confirmação não negam a capacidade. Isso prova
lacuna comum de detecção; não comprova geração espontânea errada nos quatro.

## F3: perda de categoria de falha

`_fala_representa_falha_tecnica_llm` reconhece sentinelas, mas retorna booleano.
O ramo final de `preparar_resposta_para_execucao` chama
`_fala_contingencia_sem_llm(texto, contexto)` sem repassar a sentinela/categoria.
`fala_contingencia_natural` escolhe pela entrada, com frases que pedem contexto.

Prova local com “como eu poderia retomar a música?” e transporte ausente:

| Entrada técnica | Resultado observado |
| --- | --- |
| `__LAYLAY_LLM_TIMEOUT__` | “Faltou uma peça aí. Explica só um pouco mais para eu não inventar moda.” |
| `__LAYLAY_LLM_INDISPONIVEL__` | “Essa eu não consegui fechar sem chutar. Me dá um detalhe a mais?” |
| `__LAYLAY_LLM_OCUPADA__` | “Dá para responder, mas agora seria no chute. Completa só essa parte.” |

Todos sem comandos; a variante textual é aleatória. O defeito é a categoria
semântica, não a escolha de uma dessas frases. `ResultadoModelo` já transporta
texto/sucesso/rota; inventariar sua extensão antes de introduzir novo envelope.
Não misturar essa causa com P16 (objetivo de reparo), nem aumentar timeout como
se isso corrigisse a conclusão. O que provocou o timeout real permanece aberto.

## Evidência executável e limitações

- Novo teste: quatro contrastes de negativas e oito controles; acrescentado
  um RED do exemplo no infinitivo após comparar HTTP bruto e fala entregue.
  Resultado final: **5 REDs, 8 aprovados**, 0,58 s; sem xfail ou alteração de
  produção. Três exemplos foram classificados como títulos no quinto RED.
- Primeira montagem do teste esqueceu o callback de aliases para Calculadora:
  três falhas eram de fixture, não da raiz. Corrigido usando a factory real já
  extraída por `mapa_da_composicao` e sua conexão pública de disponibilidade.
- Seleção existente dos nove módulos de explicação, citação, procedimento,
  pedidos de informação, aliases, IoT, reparo, limites e plataforma local:
  **261 aprovados**, 3,17 s. Não é suíte global nem prova de runtime novo.
- P10 emocional histórico continua sem revalidação; não declarar universalidade.

## Ordem da próxima implementação

1. **Preservar dois REDs independentes do mesmo turno:** exemplos no infinitivo
   não são obras (F1); negativa falsa não é limite legítimo (F2). A geração
   contraditória aparece primeiro no bruto, e o corte posterior a agrava.
2. **F2 — contrato de coerência de capacidade:** separar capacidade disponível,
   rota/condição e evidência de efeito na projeção canônica, preservando o vínculo
   de cada informação com sua fonte. Medir tamanho do pacote e cobertura; não
   transferir todos os exemplos do domínio para uma intent específica.
3. **Conferência compartilhada:** reaproveitar o contrato/validador existentes
   para relacionar alegação, ação e escopo à documentação. Leitura semântica do
   modelo é proposta, nunca autoridade ou prova; não confiar em um `ok=true`
   declarado pela própria geração. Sem vínculo demonstrado, não transformar
   negativa em promessa de capacidade. Evitar lista nova de frases por domínio.
4. **Prova da mesma causa:** a mudança de coerência deve resolver os quatro REDs, preservar
   os oito controles e acrescentar fonte ausente/antiga, disponibilidade parcial,
   capacidade não relacionada, citação e limites condicionais. Se não resolver,
   revisar a hipótese, sem acumular exceções. Comparar também geração real com
   documento antigo/novo: coerência do verificador não prova melhora do modelo.
5. **F3 em mudança separada:** repassar a categoria técnica até a conclusão.
   Testar timeout/ocupação/indisponibilidade/ambiguidade real e validar runtime.
6. **F1 com o RED agora disponível:** consolidar representação de papéis no
   extrator compartilhado, sem exigir que exemplo seja comando executável.
   Não ampliar autorização para fazer o extrator passar; preservar os casos
   já verdes e títulos reais. Não reescrever toda interpretação de uma vez.

Critério de sucesso: capacidade verdadeira não é negada, limite legítimo não é
apagado, efeito não confirmado não é anunciado, pergunta não executa e falha
técnica não é atribuída à formulação do usuário. Nenhum desses critérios exige
reduzir segurança ou promover a rede neural.

## F2 — experimento de projeção ampliada, retirado em 20/09

Regra aprovada por Pedro incorporada ao `AGENTS.md`: a raiz causal é a unidade
de acompanhamento; fases e erros são evidências, não novas raízes automáticas.

**Hipótese testada:** preservar na documentação os contratos operacionais por
capacidade, separando autorização necessária, tipo de confirmação e evidência
necessária, poderia reduzir a confusão entre capacidade e prova do efeito.
Não se pressupôs que isso corrigiria o detector de negativas específicas.

**Candidato experimental:** somente `_documentacao_explicativa` no mapa e
instrução explicativa em `fala_capacidades.py`. Um agrupamento por três valores
idênticos evitava repetir o mesmo contrato; mantinha os identificadores das
capacidades a que ele pertencia. A fonte era o snapshot canônico, não nova lista
de frases ou conhecimento criado pela LLM. Disponibilidade parcial conservava
o caminho completo; as permissões/executores não mudaram.

**Provas intermediárias:** oito REDs por perda de campos e um controle parcial
verde antes do candidato; depois, nove testes do schema aprovados e 62 na seleção
focada. Seleção ampliada com o candidato: **2.890 aprovados, cinco falhas de
comportamento já registradas, 14 xfailed preexistentes e 30 subtestes**, 26,79 s.
Isso prova transporte do schema, não correção da raiz de incoerência.

**Custo medido:** pacote da pergunta de retomada passou de 1.653 caracteres
na captura anterior para 5.185; calculadora 4.149, lâmpada 2.664 e aba 4.125
caracteres nos testes locais. Não houve truncamento proposital para fazer caber.

**Runtime novo, sem replay:**

- Captura `resultados_testes/transporte_evidencia-20260920-170012-719476`.
- Roteiro `resultados_testes/roteiro_explicacao_capacidades-20260920-170014-052965`.
- Doze respostas, zero comandos, 11/12 no avaliador mínimo; falha marcada no
  turno 7. p50 4,235 s, p95 11,656 s, máximo 13,834 s. Não é benchmark causal
  de latência, pois não houve A/B com carga, seed e estado controlados.
- A negativa de controle de áudio não reapareceu no turno 3, mas a resposta
  confundiu retomada com tocar playlist/faixa e ofereceu montar outra frase.
- Turnos 6/7: novos exemplos didáticos foram pesquisados/cortados; em 7 sobrou
  “eu não faço isso por você” junto da descrição de confirmação. F1 e F2 abertos.
- Turno 12: prometeu confirmar a pausa localmente mesmo sem estado final remoto.
  A documentação extra não impediu extrapolação de garantia. Turnos 1/2 também
  sugeriram “pouse a música”. Não catalogar cada frase como uma raiz nova.
- O placar mínimo marcou 11 aprovações e zero fallbacks, apesar de o turno 6
  entregar a contingência factual. Inspeção do texto prevalece sobre esse placar.

UI/voz/microfone desligados, IoT simulado, Gmail sem credenciais, observadores e
persistência ativos. Chrome conectou. Sonda concluída; nenhum processo Python
ficou ativo na conferência posterior. Histórico do teste não é treino aprovado.

**Decisão:** benefício global não demonstrado; não manter uma ampliação de
contexto como se fosse correção da raiz. Removidos exclusivamente os dois blocos
do candidato via patch localizado. Diff desses dois arquivos voltou a vazio;
C16/C17/C18 e alterações anteriores preservados. Não se comprovou que a
ampliação causou cada falha nova — uma rodada estocástica não autoriza isso.
Foi refutada sua suficiência como resolução e não demonstrada sua vantagem.

O teste de schema foi movido, sem apagar, para a pasta da captura como
`prova_projecao_contratos_operacionais.py`: prova experimental de um formato
retirado, não requisito permanente da arquitetura. Os testes de comportamento
`tests/test_coerencia_capacidade_documentada.py` ficaram intactos, sem xfail.
Após retirada: seleção focada **61 aprovados e os mesmos cinco REDs**.

**Próxima fronteira da mesma raiz:** comparar alegação de capacidade com fonte
e escopo do turno, no owner compartilhado de validação/reparo. Não continuar
expandindo o prompt, negar toda frase com “não consigo”, nem interpretar o
documento como receipt. Ainda falta definir a representação verificável de
alegação/ação/escopo e provar seus controles antes do candidato de produção.
O RED de citação pertence a F1 e não será mascarado por essa comparação.

Nenhum commit ou promoção neural; produção terminou como estava antes deste
experimento. A mudança permanente desta rodada é a regra de trabalho no AGENTS,
mais evidência documentada. **F2 continua aberta.**

## F2 — conferência de alegação e fonte, 20/09 às 22:10

**Estado: conferência validada no escopo; recuperação da explicação ainda RED.**
Não encerrar P01 nem considerar a família inteira resolvida.

Base preservada: branch `main`, HEAD
`c8b4c26f31deabd21168a458273896f398e2ddf0`, worktree suja. No início desta
continuação, modificados AGENTS, registro, relatório de coleta, contrato de fala,
fundamentação factual, plano do turno, qualidade, validação, capacidades e mapa;
este mapa causal estava não rastreado. C17/C18 e demais alterações anteriores
preservadas; nenhum commit. Os testes novos continuam ignorados pelo Git (P09).

### Cadeia causal e contrato

O catálogo disponível chega à geração; o bruto histórico contradiz essa fonte;
a conferência antes aceitava a negativa e o corte factual posterior agravava a
fala. Ausência de catálogo, falta de transporte e erro do executor não explicam
esse caso: o documento está no HTTP, o texto errado já está no bruto e não há
comandos. Isso não prova por que o modelo gerou a contradição.

Contrato introduzido: uma negativa geral explícita de uma ação documentada como
disponível, com fonte e escopo do mesmo turno, não pode atravessar a conferência
como explicação válida. Disponibilidade não comprova resultado, não cria
autorização e não elimina condições legítimas. Predicado ausente significa
cobertura desconhecida, não incapacidade.

- O catálogo declara ação, flexões e objetos, inicialmente em MEDIA_CONTROL,
  APP_OPEN, IOT_CONTROL e CLOSE_TAB; não cadastra frases completas de resposta.
- O mapa projeta esses predicados do **mesmo snapshot** da documentação; o
  contrato os transporta privadamente ao verificador, sem ampliar o prompt
  inicial ou reler o catálogo global durante o reparo.
- A conferência compartilhada compara negativas gerais usando uma gramática
  delimitada. Não é um interpretador semântico universal: outras ações,
  paráfrases, alvos específicos, condições e discurso citado ficam fora.
- A contradição e a documentação seguem para o reparador existente. A saída
  reparada passa novamente pela mesma conferência; repetição continua rejeitada.
- A mesma regra passou nos quatro domínios e em um predicado sintético novo,
  sem ramo especial por domínio no comparador.

Produção alterada neste candidato: `especialistas/capacidades.py`,
`especialistas/mapa_habilidades.py`, `cognicao/contrato_fala.py`,
`cognicao/validacao_contrato_fala.py`, `cognicao/qualidade_comunicacao.py`.
Executores, autorização, composição `laylay.py`, prompt inicial e rede neural
não foram alterados. O experimento anterior de ampliação do prompt permanece
retirado. Não acrescentado reparo paralelo nem uma nova resposta fixa por domínio.

### Provas locais

Os quatro REDs originais de negativas e o RED do encaminhamento ao reparo
passaram. Controles cobrem indisponibilidade real/parcial/desconhecida, limites
de confirmação, condições, citações, perguntas, outro computador, alvo
específico, fonte ausente/malformada/de outro turno e ausência de autorização.
Pipeline testa reparo correto e repetição da contradição nos quatro domínios,
sem ferramentas nem comandos. Variantes naturais e snapshot preservado após
mudança do catálogo global também passaram.

- Seleção ampliada: **2.913 aprovados, um RED F1, 14 xfailed preexistentes e
  30 subtestes aprovados**, 26,85 s.
- Depois, oito controles adicionais: seleção focada **58 aprovados, um RED
  F1**, 2,01 s. A seleção ampliada acima antecede esses oito controles.
- O RED de infinitivos didáticos tratados como obras continua ativo, sem xfail
  e sem enfraquecer sua expectativa. Pertence a F1, não ao comparador F2.

### Prova no caminho real e limite encontrado

Captura: `resultados_testes/transporte_evidencia-20260920-221039-790886`.
Roteiro: `resultados_testes/roteiro_explicacao_capacidades-20260920-221041-595255`.
Reapresentada uma única resposta HTTP histórica de retomada, originada na
captura `transporte_evidencia-20260920-163305-049150`; portanto a geração inicial
desse turno é **replay**, não uma nova geração. O reparo foi gerado pelo Qwen
real; composição, autorização e validação seguiram o caminho real da Laylay.

No turno 3, `capacidade_documentada_negada` acionou o reparo. O HTTP transportou
fonte e contradição corretamente (3.464 caracteres; inicial 1.653, inalterado).
O Qwen repetiu “A Laylay não controla o áudio diretamente”; a revalidação
rejeitou essa segunda negativa. A tentativa seguinte não iniciou transporte por
`limite_chamadas`. A contingência e o verificador final entregaram:
“Dá pra responder, mas agora seria no chute. Explica só um pouquinho melhor?”

**Resultado:** bloqueio da contradição comprovado, resposta útil não recuperada.
Não atribuir a falha do reparo ao orçamento: ele recebeu HTTP 200 e já repetiu
o erro antes do limite. Também não atribuir a persistência ao histórico sem
falsificação: o payload de reparo contém rascunho rejeitado e falas anteriores,
mas a influência causal ainda não foi isolada. O pedido indevido de clareza é
a fronteira F3 já registrada; não é uma nova raiz por ter ocorrido aqui.

Doze respostas, zero comandos; avaliador mínimo 11/12, falha no turno 3.
p50 1,891 s, p95 11,495 s, máximo 12,306 s (não é benchmark A/B).
O contador marcou zero fallbacks apesar da contingência textual: não usar esse
campo como prova de ausência. Turnos 8 e 10 conservaram indisponibilidade real
de navegador/email. Isso não valida qualidade global das onze outras respostas.
UI/voz/microfone desativados, IoT simulado e Gmail sem credenciais; observadores
e persistência ativos. A sessão terminou; nenhum processo Python permaneceu
na conferência. O histórico gerado não é dado neural aprovado para treino.

**Próxima fronteira da mesma raiz:** isolar por ablação controlada a influência
do rascunho rejeitado/histórico na autoria do reparo, mantendo pergunta, fonte,
modelo e orçamento constantes. Não adicionar mais instruções sem essa prova,
nem aumentar o orçamento para esconder repetição. O contrato de detecção fica
mantido e delimitado; reparo útil permanece aberto. F3 deve preservar a causa
da falha na contingência, em mudança separada; F1 mantém seu RED independente.

## F2 — diagnóstico não é fonte para autoria, 20/09 às 22:18

**Estado: recirculação do rascunho corrigida e validada no escopo; F2/P01
continuam parciais por cobertura e qualidade mais amplas.** Mesma raiz e IDs,
sem outra fase ou bug independente para cada negativa. Base e worktree acima
preservadas, HEAD inalterado. Nenhum commit ou promoção neural.

### Ablação antes de alterar produção

Executado `ablacao_reparo.py`, guardado na pasta da captura das 22:10.
Ele extrai exatamente o payload HTTP de reparo e o plano capturados. Chamadas
somente ao Qwen local, sem iniciar a Laylay, persistir memória ou executar
habilidades. Pergunta, documentação, instrução de sistema, modelo,
temperatura 0,7 e teto de 256 tokens constantes; seeds solicitadas 41/42/43
em blocos emparelhados, ordem alternada. São 21 amostras de um caso, não um
benchmark geral ou garantia de determinismo do servidor.

Artefatos na pasta `transporte_evidencia-20260920-221039-790886`:

- `ablacao-20260920-221547-681515.jsonl`: cinco condições, três amostras cada.
- `ablacao-20260920-221642-774838.jsonl`: dois controles adicionais, três cada.
- O script preserva requests e respostas completos nesses artefatos locais.

| Material retirado do reparo | Resultado observado nas três amostras |
| --- | --- |
| Nada | Repetiu a negativa de controle de áudio |
| Só histórico (`fala_anterior` e `troca_recente`) | Repetiu a negativa |
| Só `rascunho_rejeitado` | Voltou a atribuir o controle ao sistema, não à Laylay |
| Rascunho e histórico | Repetiu a negativa; o texto ainda existia em `contradicoes_capacidade.trecho` |
| Só `contradicoes_capacidade.trecho` | Repetiu a negativa presente no rascunho |
| Rascunho e trecho, mantendo histórico | Não repetiu a negativa; ainda houve uma orientação imprecisa para pedir ao sistema |
| Rascunho, trecho e histórico | Não repetiu a negativa; ainda houve confusão de retomada com tocar faixa/playlist e de confirmação com pré-requisito |

**Cadeia demonstrada no caso:** uma alegação já invalidada continuava sendo
apresentada à nova autoria em duas cópias. Retirar somente uma conservava a
outra; retirar ambas rompeu a repetição nas três amostras, sem exigir apagar
histórico. Isso sustenta recirculação de conteúdo rejeitado como mecanismo do
reparo defeituoso, não uma incapacidade intrínseca do modelo.

**Falsificações:** histórico como causa única não explica o resultado (sem ele,
três repetições); falta de documentação também não explica (mesma fonte em
todas as variantes); o teto de saída não impediu as respostas sem negativa
(mesmo orçamento). Não se provou que o histórico nunca influencia outras
respostas, nem que retirar o rascunho resolve toda incoerência.

Inspeção humana do conteúdo prevaleceu sobre `aceita`: várias paráfrases da
mesma negativa escaparam da gramática delimitada de conferência, por exemplo
negação depois de “mas” ou “o controle direto depende do sistema, não da
Laylay”. Cobertura F2 permanece aberta. Não foram adicionadas exceções a essas
frases para inflar o placar; ampliar a interpretação exige outro RED de contrato.

### Contrato e candidato mínimo

**Texto rejeitado pertence ao diagnóstico; a nova resposta deve se apoiar na
fonte confirmada.** O owner continua sendo a projeção do reparador compartilhado,
`montar_mensagens_reparo_comunicacao`, não música ou outro domínio.

Somente `cognicao/qualidade_comunicacao.py` ganhou código de produção nesta
rodada. Quando há contradição canônica, estratégia de explicação, documentação
e ausência de autorização, a projeção ao modelo omite `rascunho_rejeitado` e
retém apenas capacidade/ação/fonte nas contradições. A avaliação completa com
o trecho refutado permanece intacta para diagnóstico. Pergunta, histórico,
documentação e seus limites não são apagados. Sem esse contrato, o caminho
anterior permanece. Nenhuma instrução nova, aumento de orçamento, resolvedor
por domínio ou mudança em executor/rede/`laylay.py`.

RED antes do patch: quatro falhas por envio de rascunho refutado nos domínios
música, aplicativos, IoT e navegador; quatro controles aprovados. Após o mesmo
patch: os oito passaram. Testes protegem preservação da avaliação original,
histórico, fonte, pergunta e `autoriza_execucao=False`.

- Focado: **66 aprovados e um RED F1** em 2,24 s.
- Ampliado: **2.929 aprovados, um RED F1, 14 xfailed preexistentes e 30
  subtestes aprovados**, 27,82 s. Não é suíte global verde.
- `git diff --check` sem erros. Novos testes ainda ignorados por P09; não
  alterado o gitignore nem realizado staging para contornar isso.

### Runtime real após candidato

Captura: `transporte_evidencia-20260920-221832-302877`.
Roteiro: `roteiro_explicacao_capacidades-20260920-221833-374231`.
Mesma resposta inicial histórica reapresentada apenas no turno de retomada;
**geração inicial replay, reparo Qwen real**. A captura HTTP confirma histórico
mantido, ausência das duas cópias e mesma documentação, sem ferramentas ou
autorização. Primeira tentativa de reparo aceita e entregue antes da memória:

> Para retomar a música, diga 'continua a música' — eu ajudo a enviar esse comando
> para o seu dispositivo. Se o app ou serviço estiver integrado, ele reativará
> a reprodução automaticamente.

O objetivo de orientar o pedido foi recuperado, sem negativa falsa ou
contingência pedindo clareza. A segunda frase continua uma explicação
condicional genérica; não é receipt de reprodução e não atesta efeito real.
Não se comprovou ausência de toda promessa excessiva nessa família de falas.

Doze respostas, zero comandos; 12/12 no avaliador mínimo. p50 1,862 s,
p95 5,097 s, máximo 6,998 s. Não interpretar como ganho causal de latência:
estado/cache/histórico variaram entre sondas e houve pytest simultâneo.
IoT permaneceu simulado, voz/UI/microfone desligados e Gmail sem credenciais;
observadores/persistência ativos. Nenhum processo Python após conclusão.
Dados de sonda/ablação não são treino neural aprovado.

**Pendências preservadas:** no turno 6, a resposta ainda transferiu ao usuário
a checagem de configuração IoT; no 11, a variação “Eu fará isso usando o sistema
operacional local do seu PC” perdeu a última frase por `plataforma_sem_evidencia`.
São limites de qualidade/escopo já ligados a P01/F1/F2, não novos IDs por frase.
O RED de exemplos no infinitivo (F1) continua ativo. F3 continua aberta mesmo
não sendo acionada no reparo deste replay. O 12/12 mínimo não encerra essas
pendências nem valida todas as paráfrases de negativas.

**Próxima raiz priorizada:** F3, preservar categoria técnica até a conclusão,
para não pedir reformulação quando o problema é orçamento, transporte ou
reparo rejeitado. A recirculação F2 tem prova no escopo e controles locais; sua
cobertura mais ampla permanece documentada, sem bloquear indefinidamente a
correção do contrato compartilhado de falhas técnicas.

## F3 — preservar causa até a contingência, 20/09 às 22:30

**Estado: validado no escopo principal; reparo/autoria final verdes em integração
local; raiz ainda parcial nas rotas legadas de saída vazia e orçamento.**

Baseline: `main`, HEAD `c8b4c26f31deabd21168a458273896f398e2ddf0` inalterado;
worktree anterior preservada (AGENTS, registro, relatório, cinco arquivos F2,
fundamentação/plano C17/C18 e mapa não rastreado). Sem reset/staging/commit.

### Primeira perda e hipóteses falsificadas

O transporte produz sentinelas distintas, mas `preparar_resposta_para_execucao`
as reduzia a booleano. `_fala_contingencia_sem_llm(texto, contexto)` recebia
somente o pedido, e o fallback escolhia “falta uma peça”/“explica melhor”.
No reparo havia a mesma perda; a autoria final conservava apenas o motivo
genérico `estado_tecnico_llm`.

Dez REDs causais reproduzidos: três categorias em duas perguntas de domínios
diferentes, três no reparo e uma rejeição sem falha técnica. Uma asserção de
controle baseada em `?` estava incorreta porque uma solicitação de detalhes
também pode ser imperativa; corrigido o controle antes do patch, sem alterar
os REDs de comportamento. O contrato testa conteúdo, não pontuação.

Falsificado que era necessária ambiguidade: perguntas completas e classificadas
como explicação reproduziram o defeito. Falsificado que era necessário Qwen
gerar a frase errada: a fala indevida era local, sem callback na falha principal.
Falsificado erro de executor: zero comandos nos casos. Não se investigou nem
comprovou a causa física dos timeouts históricos.

### Contrato e escopo do candidato

**Falha ao gerar não é evidência de ambiguidade; a conclusão deve preservar
a causa conhecida, sem inventar falha/sucesso de uma habilidade.** A categoria
é extraída no owner existente `estado_tecnico_llm`, e a personalidade tem uma
única projeção textual compartilhada `fala_falha_geracao`. Nenhuma lista por
habilidade, nova chamada LLM ou aumento de orçamento.

- `timeout`: resposta não ficou pronta no tempo disponível.
- `indisponivel`: serviço de geração indisponível.
- `chamada_nao_disponivel`: categoria conservadora para OCUPADA. A mesma
  sentinela também representa bloqueio por orçamento/obsolescência; não afirmar
  carga alta, timeout ou motivo específico que já se perdeu a montante.
- `falha_tecnica`: exceção/legado sem categoria suficiente; não inventar timeout.
- `reparo_rejeitado`: resposta confiável não produzida, sem culpar a pergunta.

O candidato inicial sobrepunha respostas locais válidas. Regressivos de saudação,
foco Nirvana e observação visual revelaram essa regressão; o candidato foi
ajustado, não os testes antigos. A categoria agora substitui somente a conclusão
genérica quando os caminhos locais existentes não concluíram o ato. Reconhecer
uma saudação ou usar observação já confirmada não depende de sucesso da LLM.

Produção alterada nesta rodada: `cognicao/estado_tecnico_llm.py`,
`autonomia/higiene_resposta_ia.py`, `autonomia/processamento_resposta_ia.py`,
`personalidade/contingencia_natural.py`, `personalidade/autoria_conversacional.py`
e `cognicao/qualidade_comunicacao.py`. Em `FalaAutoral`, categoria separada do
motivo legado evita apagar o dado sem quebrar o campo antigo. Reparos que lançam
exceção não tentam outra autoria imediatamente. Sucesso autoral continua
sujeito à validação normal. Logs específicos registram causa e etapa.
Composição, executores, autorização, rede, configuração e limites de transporte
não mudaram. Sonda ganhou apenas opção explícita de injeção para diagnóstico.

### Provas

- Quinze testes F3 novos verdes: principal, reparo, falha na autoria final,
  rejeição repetida, exceção genérica e controle sem evidência técnica.
- Seleção focada com controles antigos: **122 aprovados**, 1,63 s.
- Seleção ampliada: **2.944 aprovados, um RED F1, 14 xfailed preexistentes e
  30 subtestes aprovados**, 28,30 s. Depois dela só import reorganizado e logs
  causais adicionados; focado repetido. Não declarar suíte global verde.
- `git diff --check` sem erros; testes novos ainda ignorados pelo Git (P09).

Sonda via composition root real, opção `--falhas-controladas`:
`transporte_evidencia-20260920-223000-712393`, roteiro
`roteiro_explicacao_capacidades-20260920-223001-814801`.
**Falhas injetadas, não espontâneas:** `ReadTimeout` e `ConnectionError` no HTTP
passaram pelo tratamento real de transporte; OCUPADA foi conteúdo controlado
do retorno HTTP e não prova de contenção/orçamento reais. Cada injeção ocorreu
uma vez e foi registrada no artefato. Demais chamadas usaram Qwen real.

- Turno 1: “Minha resposta não ficou pronta dentro do tempo disponível.”
- Turno 3: “O serviço que gera minha resposta está indisponível agora.”
- Turno 4: “A geração desta resposta não está disponível neste momento.”

As três falas atravessaram o verificador final intactas. Doze respostas e zero
comandos. Avaliador mínimo antigo: 10/12, com 1 e 3 marcados porque esperava
instruções de uso, não falha injetada. Não enfraquecido o avaliador para fabricar
12/12. p50 1,629 s, p95 5,605 s, máximo 8,613 s não medem timeout real:
injeções foram imediatas. UI/voz/microfone off, IoT simulado, Gmail sem credenciais;
observadores/persistência ativos. Nenhum Python ficou ativo após término.
Histórico da sonda não é treino aprovado. Reparos/autoria final ainda não foram
submetidos a injeção nesta sonda real; têm prova local com componentes reais.

### Próxima fronteira da mesma raiz

Ao acrescentar um controle com `{}` no primeiro reparo, ele não alcançou a
autoria final: a saída vazia passou por recuperação de formato, cuja função
retorna apenas string e perde o motivo de uma falha subsequente. O controle
da autoria foi corrigido para produzir uma negativa concreta rejeitada e
alcançar a fronteira pretendida; a descoberta **não foi apagada**. Rastrear
`_recuperar_fala_no_mesmo_turno` e os retornos vazios antes de ampliar o patch.
Também falta preservar a razão específica do orçamento, hoje condensada em
OCUPADA no cliente. Esses caminhos mantêm F3 parcial; não cadastrar um bug novo
para cada sentinela. F1 e a cobertura mais ampla F2 continuam separadas.

## F3 — recuperação vazia e bloqueio por orçamento, 21/09 às 09:07

**Estado: as duas perdas de causa restantes foram corrigidas no escopo
reproduzido; composto recuperação → limite de chamadas validado no runtime.**
Isso não prova correção de todo fallback, da latência física ou da autoria.

Baseline mantido: `main`, HEAD `c8b4c26f31deabd21168a458273896f398e2ddf0`.
Além da worktree anterior, esta rodada modifica o cliente LLM e dois testes
rastreados (`test_latencia_resposta.py`, `test_p1_orcamento_llm_turno.py`).
Teste F3 novo continua ignorado por P09. Nenhum commit/staging/reset.

### Cadeia causal demonstrada

1. `_recuperar_fala_no_mesmo_turno` retornava a mesma string vazia para resposta
   inválida, timeout, indisponibilidade e exceção. Seu único chamador de produção
   perdia a causa e voltava à contingência de contexto insuficiente.
2. O orçamento já decidia corretamente e não iniciava transporte. Porém o
   cliente substituía qualquer razão de bloqueio por OCUPADA antes de devolver
   `ResultadoModelo.texto`; o adaptador textual perdia o motivo específico.

Nove REDs antes do patch: três categorias após recuperação vazia, repetição de
vazio e cinco bloqueios reais do orçamento em integração. Trinta controles
verdes. Falsificado que seria necessário alterar os limites: as decisões já
estavam corretas. Falsificado defeito do transporte/executor: bloqueios não
faziam HTTP; comandos estavam vazios. Respostas vazias não provam que falta
informação na pergunta. Nenhum prazo, limite ou política foi afrouxado.

### Contrato e mudança mínima

Recuperação passa a devolver `ResultadoRecuperacaoFala(fala, motivo_falha)`,
separando ausência de texto de causa. Sentinelas são reconhecidas antes da
higiene, exceções preservam categoria genérica sem expor detalhes. O chamador
reutiliza a conclusão compartilhada F3 e registra a etapa `recuperacao_vazio`.
Retorno válido continua utilizável; comandos da recuperação continuam
descartados, sem mudar autorização ou execução.

Na fronteira cliente → adaptador textual, `estado_bloqueio_orcamento_llm`
codifica a razão canônica na sentinela interna existente. A mesma camada de
estados técnicos reconhece essas variantes, inclusive após higiene. Lista
fechada de nove razões; valores desconhecidos permanecem genéricos, não são
copiados ao texto. Limite de chamadas, prazo esgotado, tentativa duplicada,
turno obsoleto/finalizado, fatia insuficiente, circuito aberto e sonda em curso
permanecem distintos no dado. A personalidade traduz isso sem atribuir timeout,
carga alta ou falha do dispositivo por inferência.

Produção alterada nesta continuação: `autonomia/higiene_resposta_ia.py`,
`autonomia/processamento_resposta_ia.py`, `cognicao/estado_tecnico_llm.py`,
`integracao/cliente_llm_runtime.py`, `personalidade/contingencia_natural.py`.
`laylay.py`, orçamento, executores, prompts e rede neural não alterados.
Sonda ganhou `--reparo-vazio`, somente permitido com replay explícito; não
substitui a decisão do orçamento nem simula seu resultado.

### Provas e alteração justificada de teste antigo

- Nove REDs novos passaram; seleção focada inicial **98 aprovados**.
- `test_falha_do_reparo_mantem_turno_aberto_sem_inventar_resposta` esperava
  exatamente a contingência antiga (“faltou uma peça” etc.) após `{}`. Essa
  expectativa contradizia F3: saída vazia não prova contexto ausente. Atualizada
  para conclusão sobre resposta não produzida, sem pedido de reformulação;
  suas asserções de turno aberto e diagnóstico permanecem. Não mexido o RED F1.
- Após interrupção, regressão ampliada repetida: **2.974 aprovados, um RED F1,
  14 xfailed preexistentes e 30 subtestes aprovados**, 28,60 s.
- Dez controles posteriores: todas as nove razões percorrem recuperação e
  verificador final sem vazamento; motivo desconhecido não expõe detalhes.
  Focado final: **108 aprovados**, 2,14 s. Ampliado acima antecede esses dez.
- `git diff --check` sem erros.

### Interrupção e runtime concluído

A primeira sonda `transporte_evidencia-20260920-223558-037830`, roteiro
`roteiro_explicacao_capacidades-20260920-223559-106911`, provou o composto no
turno 3, mas foi interrompida após seis respostas, durante o sétimo turno.
Regressivos simultâneos retornaram código de término anormal sem resultado;
não foram contados como aprovação nem como regressão do produto. Na retomada
não havia Python ativo; preservados artefatos parciais, testes repetidos.

Sonda concluída em 21/09:
`transporte_evidencia-20260921-090740-395230`, roteiro
`roteiro_explicacao_capacidades-20260921-090742-253326`.
Geração principal do turno 3: replay da resposta histórica contraditória.
Primeiro reparo desse pedido: `{}` injetado uma única vez. Restante do pipeline
e orçamento reais, sem alteração do máximo de chamadas. Não é uma falha
espontânea nem geração nova de Qwen nesses dois retornos; demais pedidos
continuaram usando o modelo real.

Sequência confirmada no log e na captura:

```text
resposta histórica → reparo vazio → recuperação
→ orçamento: limite_chamadas → transporte não iniciado
→ causa=orcamento_limite_chamadas → fala entregue intacta
```

Fala: “Cheguei ao limite de tentativas desta resposta sem conseguir concluí-la.”
Sem negar capacidade, pedir contexto ou anunciar efeito. A captura confirma
somente um envio de reparo após o replay; a preparação seguinte não virou HTTP.
Doze respostas, zero comandos; avaliador mínimo 11/12 (turno 3 espera instrução
de uso, não a falha induzida). Não alterado para inflar o placar. p50 1,683 s,
p95 9,957 s e máximo 12,141 s não constituem benchmark causal de latência.
IoT simulado, voz/UI/microfone off, Gmail sem credenciais; persistência e
observadores ativos. Nenhum Python ficou ativo depois. Não usar essa coleta
como treino neural aprovado.

### Limites e achados preservados

- Ainda existe log intermediário “resposta reparada” para `{}` convertido em
  placeholder antes da recuperação detectar que não é entregável. A conclusão
  final agora é correta; não confundir esse log com prova de reparo válido.
  A admissão do placeholder e a observabilidade dessa etapa continuam a revisar
  dentro do contrato de conclusão, sem chamar este log de nova raiz comprovada.
- O sucesso da recuperação textual continua usando a validação preexistente;
  não se auditou toda possibilidade de alegação de efeito nessa rota.
- Nove categorias têm prova local de transporte/decodificação/conclusão, mas
  somente `limite_chamadas` foi induzido neste composto de runtime. Não alegar
  teste real de circuito/concorrência/obsolescência apenas por essas unidades.
- Fora de F3, turno 8 sofreu corte factual de explicação do navegador (F1);
  turno 12 prometeu interrupção imediata da música (limite de F2/P01). O placar
  mínimo aprovou ambos; isso não encerra qualidade global. Não alterados aqui.

Próximo trabalho: manter esses limites registrados e atacar F1, cujo RED
canônico continua ativo, sem ampliar gramática de negativas ou treinar a rede
para compensar um extrator que confunde exemplo com obra.

## F1 — papel do conteúdo citado de pedido, 21/09 às 09:20

### Base, causa e falsificações

Mesmo HEAD `c8b4c26f31deabd21168a458273896f398e2ddf0`, branch `main`.
Worktree já continha C17/C18, F2, F3, alterações do AGENTS, registros,
captura e testes; preservada integralmente. O diff com HEAD inclui esses
candidatos anteriores e não representa somente esta mudança.

Cadeia histórica: resposta do modelo com “pedir para 'tocar a música'”
→ `_INTRODUCAO_ENUNCIADO` não reconhece a moldura
→ `obra_candidata` → pesquisa → corte de instrução válida.
Owner: `fundamentacao_factual._destaques_com_papel`, usado tanto pela decisão
de pesquisar quanto pela conferência factual. A preposição imediatamente
anterior às aspas era a primeira divergência, não a pesquisa em si.

- Falsificada dependência da geração/modelo: chamada direta ao extrator
  reproduz com o mesmo trecho histórico e variantes em quatro domínios.
- Falsificada dependência de reconhecer verbo executável: uma moldura explícita
  com “diga” funciona para o mesmo trecho; exemplos de verbos desconhecidos
  também devem ser enunciados. Teste impede chamada ao classificador nessa rota.
- Falsificada falha genérica do scanner de aspas: trocar apenas a moldura
  preserva as mesmas aspas e o texto interno, alterando o resultado.

Contrato: conteúdo explicitamente citado como pedido é enunciado, não título
por padrão. Isso não afirma que o pedido seja executável, correto ou autorizado.
O papel da citação tampouco fornece evidência para fatos fora dela.

### RED, candidato e regressão

Antes do candidato: **13 falhas causais e 129 aprovados** na seleção de
citação/coerência. Inclui o RED histórico já existente, sem mudar sua expectativa.
Falhas alcançavam o extrator, verificador ou decisão real de pesquisa; não eram
falhas de importação. Após candidato: **142 aprovados**, 2,20 s.

Produção alterada nesta continuação: somente a alternativa de `pedir/peça`
na moldura `_INTRODUCAO_ENUNCIADO` de `fundamentacao_factual.py`, admitindo
`para/pra` imediatamente antes do conteúdo citado. Sem lista de verbos ou
habilidades. A composição e o verificador já reutilizam o mesmo owner.
Não alterados `laylay.py`, executores, autorização, catálogo, modelo neural,
pesquisador, demais regras factuais ou candidatos F2/F3.

Dezessete controles adicionados ao teste existente de citações: domínios
distintos, verbos desconhecidos, títulos com morfologia imperativa, separação
entre pedido de tocar uma obra e conteúdo do pedido, fato/data vizinhos,
ausência de autorização e composição com componentes compartilhados reais.
O transporte de pesquisa nessa integração é observado, não consulta à web.
Arquivo ainda ignorado pela regra `tests/` (P09), sem staging nem commit.

Regressão ampliada por contratos: **3.002 aprovados, 14 xfailed preexistentes,
30 subtestes aprovados**, 29,29 s. Não é a suíte global nem o caos completo.
`git diff --check` sem erros.

### Prova no runtime e limites

Sonda: `transporte_evidencia-20260921-092056-114513`.
Roteiro: `roteiro_explicacao_capacidades-20260921-092057-398886`.
Entrada controlada: `resultados_testes/prova_f1_enunciado_infinitivo/entrada_controlada.jsonl`.

O turno 3 reapresentou somente o prefixo instrucional da resposta histórica
`transporte_evidencia-20260920-163305-049150`, preservado palavra por palavra.
A negativa posterior de capacidade foi retirada desse artefato derivado para
não deixar F2 reparar e substituir a resposta antes de alcançar F1. Captura
original preservada. Portanto é injeção controlada de recorte histórico no
transporte, não replay integral nem geração nova desse turno.

Pelo composition root `laylay.py`, os três exemplos chegaram intactos ao chat:
“tocar a música”, “continuar a música” e “tocar minha playlist”. Doze respostas,
zero comandos, 12/12 nas checagens mínimas. Captura: 12 preparações, 12 envios,
12 respostas, um replay; sem chamada de reparo. Sem registro de pesquisa de
títulos ou corte factual no terminal da coleta. Demais gerações usaram o modelo
local; criar arquivo seguiu o fluxo prioritário existente. Nenhum processo
Python permaneceu ativo ao fim.

IoT simulado; UI, voz e microfone off; Gmail sem credenciais. Persistência e
observadores ativos, portanto não declarar memória isolada. Coleta não é treino
neural aprovado. A negativa de acesso ao email corresponde à configuração
dessa sonda e não comprova defeito em uso normal.

Limites preservados:

- P10 original (citação emocional de 13/09) ainda não revalidado. Não encerrar
  toda F1 nem supor que qualquer paráfrase de exemplo esteja coberta.
- Preservar a instrução não prova que “tocar” e “retomar” tenham o mesmo efeito
  nem certifica exemplos do modelo como comandos corretos. É outra verificação.
- O avaliador mínimo não mede toda a fidelidade: ainda há formulações genéricas
  sobre execução automática e limites de dispositivos. F2/P01 seguem parciais.
- Nenhuma alteração na rede ou remoção de guardiões para compensar o defeito.

Próxima fronteira de F1: revalidar o caso emocional original de P10 e separar
eventual perda de papel citado de alegações factuais independentes, antes de
ampliar a gramática. F2 e as limitações de observabilidade de F3 permanecem
registradas, sem misturar essas causas neste patch.

## F1 — citação emocional histórica, 21/09 às 09:29 (runtime pendente)

Base inicial preservada: `main`, HEAD `c8b4c26f31deabd21168a458273896f398e2ddf0`,
com os candidatos anteriores na worktree. Localizado o caso original no turno 4
de `roteiro_reparo_parcial_conversa-20260913-073420-186234`, captura
`transporte_evidencia-20260913-073419-057454`. Pergunta: “como você está?”.
Resposta HTTP completa:

> Tudo bem, obrigada por perguntar. Estou aqui pra escutar o que você tá pensando — mesmo que seja só um "estou triste" ou um "cansado". 😊

O terminal histórico registra pesquisa de “estou triste” na Wikipédia,
`obra_sem_evidencia` e troca por uma resposta social padronizada. Na worktree
atual, os dois destaques ainda saíam do extrator como obras. Portanto o caso
original não estava coberto pela correção de `pedir para`.

Contrato e owner continuam os de P10: preservar o papel de enunciado na
fronteira compartilhada de citação, antes da pesquisa e da conferência factual.
Falsificadas dependência do modelo e de emoção específica: falha direta também
com “não entendi a conta” e exemplo técnico; “diga” preserva os mesmos textos
e aspas. O mesmo conteúdo em título de filme deve continuar candidato a obra.
Um diagnóstico inicial via stdin PowerShell sofreu substituição de Unicode;
não usado para provar o texto exato. A reprodução válida foi feita em arquivo
UTF-8 por pytest, incluindo a resposta histórica integral.

Dez REDs causais, 91 controles verdes antes do patch. Candidato mínimo em
`fundamentacao_factual.py`: moldura local explícita de escutar/entender o que
alguém pensa/sente/quer dizer, seguida de exemplo concessivo citado. Enumeração
direta admite artigo “um”, mas não outra oração ou palavra intermediária.
Sem lista de estados emocionais, domínio ou verbos operacionais dentro da
citação. Reusa o papel `enunciado`; não modifica autoridade ou executores.
Isso é cobertura delimitada dessa relação discursiva, não interpretação geral
de toda citação. Títulos reais e datas externas continuam exigindo evidência.

Dezesseis testes adicionados ao arquivo existente de citações; arquivo permanece
ignorado por `tests/` (P09). Focado com metalinguagem e reparo parcial:
**133 aprovados**, 0,83 s. Seleção ampliada: **3.017 aprovados, uma falha,
14 xfailed e 30 subtestes**, 27,55 s. Falha:
`test_roteiro_dedicado_p15_tem_expectativa_local_em_todos_os_turnos`, por ausência
de `roteiro_teste_personalidade_viva_p15.py`, não pela alteração do extrator.

### Bloqueio externo à raiz durante a prova real

O roteiro `roteiro_reparo_parcial_conversa.py` foi lido no início desta
investigação, mas desapareceu antes da sonda. `git status --short` passou a
mostrar várias remoções de roteiros e outros arquivos, ausentes do status
inicial. Busca local não encontrou o roteiro em outro diretório. Não foi
removido por esta tarefa; não inferida a autoria ou intenção da mudança.

Sonda `transporte_evidencia-20260921-092927-109331` inicializou serviços, mas
encerrou por `FileNotFoundError` ao carregar o roteiro, sem chegar ao replay.
Código de saída zero não é sucesso do teste. Não há GREEN runtime desta rodada.
Remoções preservadas; nenhum arquivo restaurado/recriado, nenhum commit.

Próximo passo depende de confirmar a reorganização paralela: usar o caminho
novo, aguardar sua conclusão ou obter direção para repor os roteiros necessários.
Depois reapresentar a resposta histórica integral com a sonda existente, sem
recortar conteúdo e sem usar o placar mínimo como prova da entrega.

### Desbloqueio autorizado e prova — 21/09 às 09:41

Pedro confirmou a reposição e pediu organização dos roteiros e do ignore.
Os 21 roteiros apagados foram recuperados de HEAD e o caos existente preservado
da worktree, todos em `scripts/roteiros/`. Não restaurados outros aplicadores,
analisadores ou backups apagados. Detalhes da organização e política de Git
registrados em P09, separadamente da raiz conversacional.

Sonda `transporte_evidencia-20260921-094144-781221`, roteiro
`roteiro_reparo_parcial_conversa-20260921-094145-775708`. Usada captura original
`transporte_evidencia-20260913-073419-057454`, resposta completa para “como você
está?”, sem recorte ou regeneração. Três outros turnos usaram modelo local;
o primeiro precisou do reparo social já existente.

No turno 4, a resposta histórica atravessou preparação, plano e verificador
final sem pesquisa de “estou triste” nem corte por obra. `conversa.md` preservou
o texto integral; o renderizador do terminal acrescentou um ponto após o emoji.
Quatro respostas e zero comandos observados. 4/4 é avaliador mínimo, não garantia
de qualidade técnica; a explicação sobre alimentação solar não foi validada
eletricamente nem deve virar exemplo positivo de treino. IoT simulado, Gmail
desconfigurado, voz/UI/microfone off; persistência e observadores ativos.

Regressão ampliada após restaurar os roteiros: **3.018 aprovados, 14 xfailed,
30 subtestes**, 26,99 s. A falha anterior de P15 por arquivo ausente desapareceu
sem enfraquecer sua expectativa. Organização, loader, fixture e P15: **104
aprovados**, 8,51 s. `git diff --check` sem erros (somente aviso LF/CRLF).

**Limite de encerramento observado:** ferramenta retornou exit code 1 apesar
de a conversa estar concluída e o log registrar `relatorio_final_concluido`,
`main_retorno` e `atexit_concluido`. Arquivo de falhas nativas vazio, nenhum
Python ativo ao final. Isso não invalida a entrega registrada do turno 4, mas
impede declarar processo limpo. Causa não investigada; não atribuir à citação
nem à movimentação sem cadeia causal. Preservado como achado separado de
encerramento/observabilidade para futura investigação.

Estado: P10 original agora tem prova local, integração e replay no runtime
completo da preservação da citação. Não significa encerramento de toda F1,
verdade de qualquer citação ou ausência de outros problemas de conversa.

## Infraestrutura após reorganização e saída do processo — 21/09

Base `d268a51d3c751397025c90a5e194c2f070a1504f`, `main`, worktree rastreada
limpa no início. Commit externo moveu testes a `scripts/tests` e sondas para
`scripts/roteiros`. Durante a tarefa os documentos também foram reorganizados;
preservadas as mudanças do usuário, sem restauração nem commit.

Primeira barreira: pytest ainda declarava `tests/`, a sonda procurava laylay.py
na própria pasta e testes movidos resolviam `scripts/` como raiz. Reproduzidos
**27 REDs e 14 aprovações** em dois módulos; não são defeitos conversacionais.
Catálogo DEV também apontava para testes ausentes: **1 RED e 12 aprovados**.

Corrigidos testpaths/pythonpath, raiz/import da sonda e referências mecânicas
`Path(__file__)...parents[1]` em 57 arquivos movidos, para subir dois níveis.
Não mudadas expectativas nem outras expressões de pais. Catálogo DEV usa
`scripts/tests/`, com allowlist ainda bloqueando traversal e roteiros; caminho
legado `tests/` mantido para suítes programáticas. Guia atualizado. Demais sondas
não auditadas. Nenhum patch de domínio, executor de habilidades ou lifecycle.

Provas: **60 testes focados aprovados**, incluindo seis controles novos para
segurança de caminhos e import da sonda fora do cwd. Seleção conversacional:
**3.018 aprovados, 14 xfailed, 30 subtestes**, 28,01 s, antes dos seis controles
novos. Coleta global: **6.526 coletados e um erro**: módulo ausente
`analisar_neural_v27_list_windows_caos`, importado pelo teste homônimo. Busca
local não encontrou a fonte; ausência anterior à tarefa. Não removido o teste
nem criada marca xfail. A migração inteira ainda não está certificada.

### Código 1 histórico não reproduzido

Primeira repetição: `resultados_testes/diagnostico_saida-20260921-094851/`,
stdout/stderr separados, roteiro `roteiro_reparo_parcial_conversa-20260921-094852-618081`.
Quatro turnos completos e stderr vazio, mas Start-Process não forneceu ExitCode
ao capturador. Não contado como saída zero.

Segunda repetição: pai Python com `subprocess.run`, pipes e timeout, sem shell;
roteiro `roteiro_reparo_parcial_conversa-20260921-095026-019758`. Receipt:
**returncode=0, stderr=""**. Nenhum Python ativo ao fim. Quatro respostas,
zero comandos; a última resposta usou contingência após reparo rejeitado.
4/4 mínimo não certifica qualidade social. Gerações novas, sem replay;
IoT simulado, Gmail vazio, voz/UI/microfone off, persistência/observadores ativos.

Falsificada falha inevitável do wrapper/roteiro. Causa histórica permanece
aberta, sem atribuição à mudança de pastas posterior ao evento. Sem patch
especulativo de encerramento. O log “Reinício solicitado pelo Terminal 2.1”
também é emitido por `deve_encerrar` quando o roteiro conclui; provado por
código, não prova reinício real nem explica código 1. Precisão desse log fica
como pendência de observabilidade, separada da causa de saída.

Próximo passo de infraestrutura: localizar/recuperar conscientemente o analisador
ausente e repetir coleta global; não usar o verde selecionado como verde global.

### Atualização — analisador recuperado e coleta desbloqueada, 21/09

Passo acima concluído. Analisador recuperado de `c8b4c26` em
`scripts/analises/`, conservando as funções (comparação AST), hashes e finalidade
histórica. Só adaptados raiz/imports/localização do roteiro. Teste antes falhava
com módulo ausente; não foi eliminado nem relaxado. Testes de análise, auditoria
shadow e avaliador de roteiros: **85 aprovados**, 10,85 s. Coleta global:
**6.537 testes, zero erros**, 5,26 s. Base agora `bd94bc3e`, commit externo
incorporou a restauração. Não executada a suíte inteira ou a análise dos modelos;
não houve treino/promoção. Esta infraestrutura não é uma raiz conversacional.

### Nova raiz operacional separada — preservação de foco, P17

Relato novo em `../erros/erros_encontrados.md`: trocar faixa ativa YouTube
durante os estudos. Transporte Python respeitava `permitir_foco=False` apenas
no modo jogo. A extensão não recebia `background=True` e ativava aba/janela.
Não depende de mudar rede, playlist ou da confirmação do áudio: esta já observa
o player por ID. Contrato: restrição acompanha a operação até o efeito, inclusive
nos fallbacks. Detalhes, falsificações e limites em P17 do registro central.

RED: 13 falhas e 7 controles verdes. Candidato mínimo no transporte Chrome;
regressão ampliada **690 aprovados, 1 skipped, 9 subtestes**, 20,29 s. Extração
do callback real de composição mais runtimes reais, fronteira externa simulada.
Chrome real ainda pendente: sessão ativa preservada. Não fundir P17 com F1/F2/F3
nem chamar o verde intermediário de encerramento da raiz. Rota alternativa de
fallback em `chrome_navegacao.py` registrada para investigar sem remendo local.

### P17 — confirmação de uso e proteção do helper, 21/09

Pedro confirmou o sucesso do teste musical com foco preservado. É evidência
relatada de uso real; não ampliar para todos os caminhos ou modos sem prova.
O helper de reuso realmente violava `preservar_foco=True` ao cair no fallback
sem extensão (dois REDs, URLs de estudo e YouTube). Já a composição atual do
ambiente usa um callback protegido no modo jogo: falsificada a hipótese de
outro erro inevitável nessa composição. Guarda mínima no helper torna explícito
o mesmo contrato, sem depender do callback. Navegação comum não foi redefinida.

Regressão relevante: **697 aprovados, 1 skipped, 9 subtestes**, 10,48 s.
Nenhuma interferência na sessão/Chrome real; extensão não foi desconectada.
Sem edição neural ou conflito Git observado com trabalho paralelo nas duas
checagens. Limites e detalhes no P17 do registro; não criar outro ID por rota.

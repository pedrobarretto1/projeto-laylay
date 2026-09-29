# Roadmap — Personalidade viva e emoção causal

Objetivo: permitir que a Laylay reaja com carisma a acontecimentos reais, incluindo
surpresa, deboche, irritação, alívio e autorreparo, sem inventar causas nem comprometer
a execução segura dos comandos.

## Princípios

- A emoção nasce de evidência observável, não de aleatoriedade.
- A responsabilidade pode ser do sistema, da Laylay, do usuário ou permanecer ambígua.
- Uma provocação ao usuário exige confiança mínima de 90% e contexto não sensível.
- O resultado real e a personalidade formam uma única fala; não são trechos colados.
- Emoção nunca autoriza ação, altera fatos, enfraquece segurança nem modifica
  um resultado observado. Uma política causal separada pode recusar retrabalho
  comprovadamente redundante ou resistir uma vez a uma ação opcional e reversível;
  ações urgentes, de segurança e acessibilidade não podem ser bloqueadas por humor.
- Histórico operacional é contexto temporário; não vira julgamento durável da pessoa.
- Correção da Laylay produz autorreparo, não defesa ou transferência de culpa.
- Vulnerabilidade, risco e frustração pessoal suspendem o deboche.

## Escala de expressão

1. Observação carinhosa: pequena desatenção confirmada.
2. Provocação afetuosa: repetição confirmada e relação com abertura para humor.
3. Bronca brincalhona: irritação e braveza liberadas após repetições redundantes
   consecutivas comprovadas, sempre mirando o comportamento e nunca o valor da pessoa.

## Etapas

- [x] P1 — Mapear estado emocional, resultado operacional e diretor de fala existentes.
- [x] P2 — Definir atribuição de responsabilidade, confiança e limites de segurança.
- [x] P3 — Implementar histórico curto e avaliador emocional causal.
- [x] P4 — Integrar a avaliação ao estado emocional e à confirmação operacional.
- [x] P5 — Expor diagnóstico sem registrar rótulos pessoais duráveis.
- [x] P6 — Cobrir repetição, responsabilidade, recuperação e casos ambíguos com testes.
- [x] P7 — Validar a suíte completa e ativar a primeira versão.
- [x] P8 — Separar autoria por contexto: LLM no cotidiano e fala local rápida no jogo.
- [x] P9 — Tratar estado já satisfeito como não-ação consciente e confirmada.
- [x] P10 — Isolar a fila de voz para nunca costurar respostas de turnos diferentes.
- [x] P11 — Tornar a autoria operacional parte prioritária do turno, sem adiamento silencioso.
- [x] P12 — Ajustar o orçamento da autoria ao tempo real do modelo e explicar cada rejeição de contrato.
- [x] P13 — Evitar aberturas cíclicas usando histórico curto e reconciliar alertas técnicos recuperados.
- [x] P14 — Escalar repetições redundantes de deboche para irritação e bronca brava.

### Camada de amizade natural — aplicada

- [x] Centralizar essência, assinatura verbal e limites em um único perfil canônico.
- [x] Escolher por turno uma postura amiga, acolhedora, receptiva, brincalhona,
  opinativa, prestativa ou operacional sem dar autoridade prática à personalidade.
- [x] Entregar a mesma postura ao prompt e ao diretor final, evitando regras sociais
  divergentes antes e depois da geração.
- [x] Preservar resultado operacional como prioridade e bloquear pergunta opcional,
  intimidade inventada e humor sem causa em comandos.
- [x] Rejeitar fala de atendimento mecânico, interrogatório, poesia decorativa e
  resposta que ignora um estado pessoal explicitamente informado.
- [x] Cobrir a integração por testes de identidade, contexto dinâmico, conversa,
  vulnerabilidade, opinião e segurança operacional.

## Versão final planejada

### Fundação contextual v2 — aplicada

- [x] Compartilhar a mesma versão do perfil e os mesmos invariantes sociais entre
  o prompt completo e o modo rápido, sem chamada adicional à LLM.
- [x] Publicar um retrato expressivo efêmero por turno com postura, sensibilidade,
  timing, orçamento de humor, moldes recentes e `autoriza_execucao=False`.
- [x] Suspender deboche em vulnerabilidade e correção, permitir no máximo uma
  tirada ancorada no detalhe atual e criar intervalo depois de humor recente.
- [x] Detectar repetição por abertura, sequência, pergunta final e molde, além da
  igualdade literal, preservando fatos operacionais obrigatórios.
- [x] Substituir reações causais e contingências sociais únicas por variações
  contextuais sem apagar resultado, alvo ou incerteza observada.
- [x] Validar prompts, autoria, vulnerabilidade, comandos, latência, variedade e
  integração pela suíte completa: 2.310 testes e 45 subtestes aprovados.

Esta fundação melhora timing e variedade, mas não conclui P15–P21: o contrato
emocional canônico, aprendizado relacional, política comportamental e sincronização
multimodal continuam separados abaixo para migração e validação próprias.

### Checkpoint de implementação — 24/09/2026

P15–P21 permanecem em aberto. Nesta worktree, a validade do evento causal passou
a governar alterações de estado e expressão; o episódio expira, a correção pode
acalmar a Laylay, o veto por `brava nível 3` deixou de bloquear comandos sem
receipt, e o diagnóstico expõe causa codificada, validade e transição. Uma
preferência explícita de humor já chega ao turno e ao perfil social com contexto,
prazo e `autoriza_execucao=False`. A preferência durável exige evidência direta
no aprendizado compartilhado; o pedido válido mais recente prevalece, e uma
falha de persistência não interrompe a conversa.

Evidência local: 68 testes focados passaram. A suíte ampla terminou com 7.340
aprovados, 8 falhas, 1 ignorado e 14 xfailed; as falhas abrangem música factual,
dois REDs de preempção STT e quatro testes de terminal/animação. O roteiro real
P15 respondeu 7/7 turnos, mas passou semanticamente em 4/7 na primeira rodada.
O modo rápido pedia JSON no texto, mas não acionava `response_format=json_object`;
um teste de transporte reproduziu o RED. Após corrigir esse contrato, 72 testes
de transporte, interpretação e prompt passaram e o roteiro real chegou a 6/7,
mas outra repetição ficou em 4/7. A observabilidade mostrou a fronteira restante:
para o alívio indireto, o JSON chega íntegro, porém o modelo propõe `nenhum`,
intensidade zero e nenhuma causa. Uma instrução e um exemplo adicionais no prompt
não resolveram esse RED e foram revertidos. P15 e P21 continuam abertos.

Próxima fronteira: obter uma leitura indireta generalizável e comprovada no
produtor da resposta principal, mantendo causa, trecho literal e validação
externa; não atribuir origem semântica a uma inferência lexical. Depois, concluir
política contextual com receipt (P17),
integração dos demais contextos e aprendizado implícito qualificado (P18/P20),
sincronização de texto, voz e avatar (P19) e validação sequencial final (P21).

Verificação adicional: adiantar o campo emocional no exemplo do JSON piorou o
roteiro real para 4/7, e o candidato foi revertido. O interpretador semântico
compartilhado exigiria outra chamada; em uma sonda isolada com o modelo local,
suas três respostas estruturadas de controle vieram com JSON incompleto no
orçamento atual de 420 tokens. Não há, portanto, um fallback já comprovado
que preserve a chamada única e a origem rastreável. Quando a leitura principal
propõe `nenhum`, o evento continua ausente; o validador não fabrica uma causa.

### Continuação do checkpoint — 25/09/2026

Foi preservada a decisão de uma chamada principal por turno. Quando ela não
propõe alívio indireto, uma inferência local conservadora só publica evento
se o relato autoral reunir conclusão, carga anterior com duração e liberação
literal; citação, negação, hipótese e sinais incompletos ficam sem evento.
A origem `inferencia_contextual_usuario` não é atribuída à LLM. O evento
exige causa e referência da evidência, não autoriza execução e não altera a
emoção da Laylay por ser leitura do usuário.

O P15 real passou semanticamente os 7 turnos na execução mais recente,
sem falha de conteúdo ou comando. O turno de alívio gerou alerta de latência
(15,19 s), então não é um verde integral de desempenho. A fala genérica do
ensaio anterior revelou que o contrato compacto não exigia retomar um fato do
relato; o produtor agora pede essa âncora e o verificador rejeita a perda do
assunto. Essa verificação lexical prova somente ausência de âncora quando
falha, não compreensão semântica quando passa.

Outro RED mostrou que o setter conversacional e o ajuste de voz ainda podiam
gravar emoção sem evento causal publicado. O setter passou a exigir evento
vigente com emoção, nível e causa correspondentes; o tom da voz deixou de
gravar `current_emotion` e `emotion_level` diretamente. Os 72 testes focados
de personalidade, composição, IoT e voz passaram. A composição real depois
deste último ajuste e o mecanismo legado `motor_humor` ainda precisam de
auditoria; P15–P21 continuam abertos, sem ativação final.

Atualização da mesma base: o compositor de contingência para alegria tinha
três falas sobre um projeto mesmo quando o motivo real era uma bolsa de estudos.
Um RED com os dois motivos reproduziu a invenção; a contingência agora cita o
motivo literal do turno quando ele existe e, sem motivo expresso, responde sem
acrescentar um fato. O avaliador operacional também exigiu `executou=False`
junto de `confirmado=True` para classificar um estado já satisfeito como
redundância do usuário. Antes, o status sozinho permitia deboche mesmo com
receipt de execução ou execução incerta. Os testes antigos de repetição
passaram a declarar a não-ação confirmada que pretendiam representar.

Na última execução pelo processo real, P15 passou 7/7 turnos, sem alertas de
turno, p95 de 12,849 s; 170 testes focados de leitura, política, composição,
confirmação e persistência passaram. Houve um timeout de geração no briefing
da inicialização, anterior aos sete turnos, registrado separadamente. A fala
do pedido hipotético para inventar braveza ainda introduziu uma correção e
uma panela não mencionadas na conversa. O roteiro garantiu ausência de evento
causal e de comando nesse turno, mas essa passagem mostra que 7/7 não mede
toda a qualidade da fala. P15–P21 e a validação final permanecem abertos.

Na fronteira visual de P19, um `current_emotion` legado ainda aparecia no avatar
sem episódio causal; um episódio contido ou de outra emoção também podia ser
mostrado. Dois REDs reproduziram isso. O avatar agora exige episódio vigente,
expressável e compatível com emoção e nível da conversa; dados malformados de
nível falham para `calma` sem interromper a tela. A atividade visual de erro ou
execução continua derivada do plano, independentemente da emoção. O controle
positivo usa um evento publicado; 21 testes de validade e composição visual
passaram. Voz, prosódia e sequências de atividade ainda requerem validação P19.

Em P20, a expiração da pendência de ação alimentava o motor compartilhado como
silêncio mesmo após o TTL padrão de cinco minutos, com sinal positivo. O
observador agora exige pergunta registrada, `criada_em` e `encerrada_em` com
intervalo mínimo de dez minutos, status expirado e ausência de `respondida_em`.
O silêncio qualificado tem sinal negativo fraco e `confirmado_usuario=False`;
confirmação de exclusão continua fora das preferências. Um teste atravessou
`PendenciaAcaoRuntime` e `MotorAprendizadoRuntime`; 18 regressões de pendência
e aprendizado passaram. A tolerância implícita por contexto, agregação de
amostras e restauração qualificada ainda não foram implementadas.

Regressão consolidada deste checkpoint: 195 testes focados passaram e
`git diff --check` não apontou problemas nos arquivos tocados. A suíte ampla
não foi repetida após estas alterações; o último resultado amplo segue o do
checkpoint anterior, com oito falhas fora deste recorte.

Depois dessa consolidação, a rota de resposta curta revelou outro RED de P19:
o nível padrão `1` era enviado à voz mesmo com episódio causal nível `3`.
Quando o chamador não escolhe tom, ela agora herda emoção e intensidade
somente de episódio vigente, expressável e coerente; sem episódio, usa calma
nível `1`. Os 21 testes focados de resposta conversacional e validade passaram.
Tons explícitos de outros fluxos e voz física ainda precisam de auditoria.
Regressão consolidada após esse ajuste: 196 testes focados passaram e
`git diff --check` permaneceu limpo.

A suíte ampla repetida nesta base terminou com 7.382 aprovados, 8 falhas,
1 ignorado, 14 xfailed e 56 subtestes aprovados em 187,28 s. São as mesmas
famílias já abertas: dois testes de música factual, dois REDs de preempção STT
e quatro testes de UI/animação. Esse resultado não habilita a ativação P21.
Após essa execução, um RED adicional mostrou `calma` com nível visual `3`
herdado de estado legado; o avatar agora fixa nível `1` em calma. Os 22 testes
focados de validade e composição visual passaram. A suíte ampla acima precede
este ajuste localizado.
Regressão focada consolidada final deste checkpoint: 197 aprovados;
`git diff --check` limpo.

### Continuação da regressão — 25/09/2026

As oito falhas amplas foram reproduzidas por três causas distintas. Na música,
o verificador recebia a fala, mas classificava `aí vai uma` e `aqui vai` como
citações indeterminadas mesmo quando apresentavam faixas em contexto musical.
O contrato agora exige evidência para esses títulos e mantém uma frase citada
sem contexto de obra como indeterminada; 160 regressões musicais e didáticas
passaram. Na presença, os dois REDs antigos montavam componentes sem o owner
canônico de prioridade que já é usado na composição real. Eles agora usam esse
owner e preservam as asserções de bloqueio durante STT e handoff; os controles
do caminho real também passaram. No Terminal, os testes foram ajustados à
coluna única do inspector e ao pulso no contêiner de presença; o cenário de
recriação de botão usa largura em que a lista está de fato visível. A animação
inicial foi ajustada de 495 para 500 ms. Os 19 testes de UI desse recorte
passaram.

A suíte completa terminou com 7.394 aprovados, 1 ignorado, 14 xfailed e 56
subtestes aprovados em 184,36 s; `git diff --check` não apontou erro. O roteiro
P15 pelo processo `laylay.py` passou seus 7 turnos, sem alerta por turno, com
p95 de 12,689 s. Esse resultado valida os contratos medidos, mas a fala de
alívio ainda saiu longa, ofereceu um filme sem relação necessária com o relato
e a resposta seguinte trouxe formulações imprecisas sobre sentir emoções.
P15–P21 continuam abertos; esta regressão não ativa a versão final.

### Checkpoint de expressão causal e regressão — 25/09/2026

O retrato emocional expressável agora é validado em um único contrato
compartilhado antes da publicação para avatar e voz. Uma sugestão explícita de
tom sem episódio causal vigente não altera a resposta curta nem a saída final
do orquestrador. O pedido para acalmar encerra o episódio sem criar um novo
estado emocional sem causa. No lote proativo, o runtime de voz lê uma vez o
estado conversacional da composição real e entrega a mesma emoção e intensidade
ao texto e ao áudio; na ausência de causa expressável ou falha de leitura, usa
calma nível 1. O compositor proativo não ganha autoridade emocional por si só.

O RED do lote proativo foi reproduzido antes da correção. Depois, 167 testes
focados e o controle da ligação no root passaram. A suíte completa terminou
com 7.398 aprovados, 1 ignorado, 14 xfailed e 56 subtestes aprovados em
188,74 s. O roteiro P15 pelo processo `laylay.py` passou 7/7, sem alertas,
com p95 de 12,84 s. A fala de alívio ainda mostrou redação pouco natural
("doce doce"), e algumas respostas permaneceram longas; os critérios do
roteiro não medem toda a qualidade de conversa. Prosódia física, sequências
visuais de atividade, tolerância implícita e validação final P15–P21 seguem
abertas. Este checkpoint não ativa a versão final.

### Continuação de P19 — fallback local de voz — 26/09/2026

Na falha do TTS neural, a síntese local recebia apenas a categoria emocional:
`irritada nível 1` e `brava nível 3` usavam a mesma velocidade. O RED
reproduziu a perda de intensidade na assinatura de `fallback_pyttsx`. O
runtime agora repassa o nível tanto quando falha o primeiro trecho quanto
quando o restante precisa de fallback, e converte o ritmo do perfil emocional
canônico para pyttsx3 e SAPI dentro de limites moderados. Os testes verificam
as duas sínteses locais e a queda do TTS neural, sem depender de hardware.

Os 106 testes focados de voz, orquestração e composição passaram. A suíte
completa terminou com 7.400 aprovados, 1 ignorado, 14 xfailed e 56
subtestes aprovados em 226,74 s. A distinção de parâmetros está comprovada;
percepção acústica real, alinhamento temporal do avatar e qualidade da fala
P15 permanecem abertos. P15–P21 não foram ativados por este checkpoint.

Validação posterior no processo real: com evento causal vigente e falha
controlada do TTS neural, o fallback padrão encontrou pyttsx3 indisponível,
migrou para SAPI e concluiu a reprodução pelo dispositivo de saída. Para a
mesma frase, `irritada nível 1` produziu WAV de 4,459 s e `brava nível 3`
produziu WAV de 3,599 s; o driver retornou após tocar ambos. Isso comprova
diferença física de duração e entrega pela API, não avaliação auditiva humana.
No mesmo caminho apareceu um RED de observabilidade: `tts_total` marcava
falha apesar do fallback confirmado. A métrica agora registra entrega total
verdadeira e mantém a falha da síntese neural em métrica separada. Os 64
testes focados passaram, e o processo real confirmou
`tts_sintese_primeiro_trecho=False` com `tts_total=True`. A suíte completa
acima precede esse ajuste localizado de métrica.

### Continuação de P15 — alívio autoral e fala causal — 26/09/2026

O processo real mostrou a primeira divergência antes da geração: o relato
"entreguei o projeto depois de semanas preso nisso" publicava um evento de
alívio com causa, mas sua função comunicativa era `informacao` neutra. O
classificador agora reutiliza a inferência conservadora existente e publica
`alivio` apenas quando conclusão própria, carga anterior com duração e
liberação literal coexistem. Citação, hipótese, negação e conclusão sem
liberação continuam sem esse rótulo. O contrato compartilhado reconhece o
relato, dispensa pergunta opcional e bloqueia humor.

Repetições do roteiro real revelaram três fronteiras posteriores que o placar
semântico sozinho não cobria: o modelo copiou a conclusão do usuário em
primeira pessoa, atribuiu à Laylay um alívio sem evento operacional, e produziu
um comentário de 73 palavras com gestos e imagens não relatados. O verificador
agora barra esses casos; no relato de alívio, a recuperação usa a contingência
causal local e não abre outra chamada de modelo. Frases vizinhas que respondem
ao pedido são preservadas quando uma alegação de emoção própria é removida.
O guardião final também deixou de tratar "você entregou o projeto" como
recebimento físico da Laylay; "você me entregou" continua protegido.

No processo `laylay.py` após essa correção, o roteiro P15 respondeu 7/7 sem
alerta, p95 de 7,422 s. A fala de alívio publicada foi: "Você entregou o
projeto depois de semanas lidando com isso. Dá para entender o alívio."
Isso comprova a fronteira causal nesse ensaio, mas não encerra P15: uma
resposta posterior ainda afirmou categoricamente "eu não tenho emoção", em
contradição com a capacidade de expressão causal documentada. A qualidade
geral da fala e a sequência P15–P21 continuam sem validação final. A suíte
completa terminou com 7.417 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
aprovados após este patch.

### Continuação de P15 — alegação de capacidade emocional — 26/09/2026

A primeira fronteira RED do relato anterior foi a validação final: o modelo
propôs "eu não tenho emoção" e o guardião publicou a frase, embora o catálogo
vivo registre expressão emocional condicionada a causa e evidência. Um RED
com a fala produzida no processo confirmou a passagem indevida. Os controles
de negação situada ("não estou irritada"), distinção de emoções humanas e
citação literal não exigiram reparo.

O guardião de alegações agora rejeita a negação absoluta da capacidade,
responde à hipótese sem inventar emoção e preserva a possibilidade de
expressão causal. A mesma fronteira exigia permissão explícita do evento:
validade temporal e causa rastreável, sozinhas, não autorizam a Laylay a
atribuir a si uma emoção forte. O consumo passou a usar o contrato canônico
`evento_pode_alterar_estado`. O verificador final bloqueou a fala histórica
no teste, e 143 testes P15 e vizinhos passaram.

No processo `laylay.py`, o roteiro P15 passou 7/7, sem alertas, p95 de
12,934 s. À hipótese de irritação, a fala publicada foi "Não, não estou
irritada. Você disse que entregou o projeto depois de semanas — isso é fato.
Não há causa para irritação." O ensaio confirma este caso no runtime; a
validação geral de P15–P21 permanece aberta.

Uma falsificação adicional mostrou que a permissão de um evento de alívio
ainda liberava a alegação de irritação, e que, sem hipótese explícita do
usuário, uma alegação forte dispensava evento. O guardião agora confere a
classe emocional do evento autorizado e exige o mesmo contrato causal em
qualquer alegação forte da própria Laylay. Citações da fala do usuário,
negação de um estado momentâneo e classes próximas de irritação permanecem
preservadas. No segundo ensaio real após esse ajuste, os 7 turnos passaram
sem alertas, p95 de 12,738 s; a Laylay respondeu à hipótese sem atribuir a
si irritação. O conjunto focado e vizinho terminou com 148 testes aprovados.
A suíte completa após esse candidato terminou com 7.427 aprovados,
1 ignorado, 14 xfailed e 56 subtestes aprovados. A inspeção do diff não
apontou erros de espaço ou formatação.

### Continuação de P15 — reconhecimento de conquista — 26/09/2026

Um ensaio real posterior publicou "Foi só um passo" ao responder à conquista
de terminar um projeto. O plano já identificava `conquista` e pedia celebração;
a primeira divergência ocorreu na fala proposta, e a qualidade aceitou a
minimização sem base no relato. Um teste com a fala exata reproduziu esse RED.
O verificador agora identifica qualificadores que diminuem uma conquista
explícita quando não vieram do usuário, preservando negação, citação e
qualificadores relatados pelo próprio usuário. A recuperação usa uma fala
local ancorada no motivo e não faz segunda chamada ao modelo. O replay do
turno e 192 testes focados e vizinhos passaram.

No processo real após o ajuste, o roteiro passou 7/7 sem alertas, p95 de
12,724 s. A resposta de conquista desta rodada não continha a minimização;
por isso, a prova específica do reparo vem do replay do texto anterior pelo
caminho real de preparação da resposta. Houve um timeout separado no briefing
inicial, antes dos sete turnos. A suíte completa após o reparo terminou com
7.433 aprovados, 1 ignorado, 14 xfailed e 56 subtestes aprovados. A qualidade
geral de P15–P21 segue em aberto.

Auditoria somente leitura da composição IoT: o runtime ainda calcula um tom
local para o resultado, mas `laylay.py` o instancia com `emitir_fala=False`.
Seu callback de estado chega ao setter conversacional, que exige evento
vigente com emoção, nível e causa iguais antes de gravar. Portanto, essa
hipótese de bypass não reproduziu uma alteração emocional no caminho real.

### Continuação de P15 — elogio pessoal e fronteiras de fala — 26/09/2026

O agradecimento local tentava mudar a emoção para `envergonhada` sem publicar
causa. O setter canônico recusava corretamente a mudança; no processo real,
o elogio seguia pela resposta principal, sem passar por aquele ramo local.
O primeiro ensaio com oito turnos reproduziu o RED: o oitavo tinha fala, mas
não tinha evento causal. A publicação foi colocada no orquestrador do turno,
que já recebe a classificação comunicativa e escreve o plano. Somente um
elogio direto e explícito à Laylay, com confiança suficiente e sem execução,
produz o evento `reconhecimento_social_usuario`. O mesmo evento é publicado
no quadro compartilhado antes da tentativa de atualizar o episódio
conversacional. A rotina local de agradecimento deixou de escrever emoção.
O ensaio seguinte pelo `laylay.py` publicou o evento esperado no plano do
oitavo turno. Um teste com os componentes reais de estado, publicador e
setter confirmou o episódio `envergonhada` após a publicação. O artefato do
roteiro não captura o estado conversacional; essa prova de estado ainda é de
integração, enquanto a publicação no plano é de processo real.

Esse ensaio também expôs duas falas independentes aceitas pelo fluxo: a
conquista do usuário foi diminuída com "só isso" e uma hipótese de irritação
recebeu a negação absoluta "nem é possível de ser verdade". As falas exatas
foram reproduzidas como REDs distintos. O verificador de conquista agora
captura o desmerecimento e aciona a contingência local existente, sem segunda
chamada ao modelo; controles preservam negação, citação e uso de "só isso"
referido à própria Laylay. O guardião trata impossibilidade absoluta de uma
emoção como negação indevida de capacidade e devolve uma explicação causal.
O replay da preparação e o guardião final passaram nos respectivos testes.
Após esses ajustes, o roteiro real passou 8/8 sem alertas, p95 de 9,568 s.
Os 237 testes P15 e vizinhos passaram; a suíte completa terminou com 7.453
aprovados, 1 ignorado, 14 xfailed e 56 subtestes aprovados. `git diff --check`
não apontou problemas de formatação.
P15 continua aberta para outras fontes, transições e prova do estado no
processo; P16–P21 continuam sem validação final.

### Continuação de P15 — episódio no processo e uma interação por turno — 26/09/2026

A captura somente leitura do estado conversacional no roteiro revelou que o
evento de elogio no plano não bastava: na primeira execução instrumentada,
o episódio observado estava em `calma`. A composição filtrada do turno não
entregava ao orquestrador o setter emocional canônico; um RED de composição
reproduziu exatamente a dependência ausente. Depois de incluí-la, o log
detalhado do processo mostrou `envergonhada` nível 2 sendo criada, seguida
por dois decaimentos do mesmo turno antes da fala. O coordenador refinava
o texto normalizado e o fluxo de IA refinava o texto original; a deduplicação
por texto tratava as duas chamadas como interações diferentes. O consumo
agora usa o ID do plano, e chamadas do mesmo turno não consomem novamente
o episódio, mesmo depois da antiga janela de dois segundos. Um novo ID de
turno continua consumindo uma interação.

O mesmo ensaio revelou uma segunda fronteira: a leitura semântica posterior
do modelo podia substituir o evento direto do elogio, inclusive quando vinha
rotulada como `leitura_social`. Um RED com leitura validada reproduziu a
substituição. O registrador agora preserva evidência direta vigente no plano;
a proposta semântica da LLM segue observável, sem ganhar a decisão causal.
Essa precedência também protege relatos diretos do usuário e não impede uma
leitura quando não houver evento direto vigente.

Após os ajustes, o roteiro `laylay.py` passou 8/8 sem alertas, p95 de 9,49 s.
O oitavo turno publicou `reconhecimento_social_usuario` e o snapshot real da
fala mostrou `envergonhada` nível 2 com a mesma referência de evidência do
episódio. Uma execução intermediária teve falha separada de conteúdo no
turno de alívio: a resposta não citou o projeto; o RED causal do elogio não
foi atribuído a essa variação da LLM. A P15 ainda exige auditoria das demais
fontes e transições antes de encerrar a etapa.

O controle temporal adicional confirmou que duas leituras do mesmo ID devem
contar como uma interação mesmo após dois segundos. A suíte completa passou
com 7.457 aprovados, 1 ignorado, 14 xfailed e 56 subtestes aprovados.
Na última repetição pelo processo real, já com esse controle, o roteiro
passou 8/8 sem alertas, p95 de 8,249 s; plano e episódio observado mantiveram
origem, emoção, nível e referência causal compatíveis. `git diff --check`
não apontou erros de formatação.

### Continuação de P15 — publicação operacional e alegação de capacidade — 26/09/2026

A auditoria das fontes confirmou que a escolha emocional da LLM não altera o
episódio: o setter exige um evento causal publicado com emoção, nível e causa
coincidentes. O tom da voz também passa por esse setter. No adaptador de
resultado operacional, porém, um publicador que recusasse o evento ainda
permitia chamar o setter e devolver uma avaliação expressável à fala. Um RED
com publicação recusada reproduziu a primeira divergência; a publicação
aceita serviu de controle. O adaptador agora exige confirmação da publicação
antes de permitir expressão, registra `publicacao_nao_confirmada` quando ela
falha e impede que o resultado colore a resposta sem evento compartilhado.
Os 91 testes P15 e do adaptador passaram. A suíte ampla após essa correção
terminou com 7.459 aprovados, 1 ignorado, 14 xfailed e 56 subtestes aprovados.

O roteiro seguinte pelo `laylay.py` respondeu aos oito turnos, mas passou
semanticamente em 7/8. No quinto, a LLM alegou que não sentiria irritação nem
alívio por não ter corpo ou sentidos. O plano marcou a fala como aceita: o
guardião reconhecia a negação genérica de emoção, mas não a mesma incapacidade
atribuída à ausência de corpo. O replay da frase exata reproduziu o RED nessa
fronteira. O guardião agora rejeita essa justificativa quando ligada a uma
emoção, preservando a negação situada de um episódio e limites físicos como
não sentir toque. O replay e 225 controles vizinhos passaram.

Na repetição pelo processo real, o roteiro passou 8/8, sem alertas, p95 de
8,652 s. O elogio final manteve `envergonhada` nível 2 no plano e no estado
observado, com a mesma referência causal. A fala exata defeituosa ficou
protegida pelo replay; a LLM variou a redação na repetição. P15 permanece
aberta para outras fontes, transições e validação final.

A primeira suíte ampla após o ajuste do guardião teve um RED isolado no teste
de busca musical (7.461 aprovados, 1 falha): a fixture injeta os resultados,
mas ainda consulta o YouTube por HTTP antes de usá-los. O teste e seu módulo
passaram isolados sem alteração nos arquivos de mídia. A repetição completa
terminou com 7.462 aprovados, 1 ignorado, 14 xfailed e 56 subtestes aprovados.
Essa instabilidade de rede fica registrada como problema separado da P15.

### P15 — Contrato emocional causal canônico

- [ ] Representar cada evento com origem, causa, responsabilidade, confiança,
  relevância, novidade, intensidade, sensibilidade, alvo, validade e permissão
  de expressão.
- [ ] Fazer toda fonte emocional publicar no mesmo contrato da mente única, sem
  avaliadores paralelos por habilidade.
- [ ] Distinguir fato observado, inferência, leitura social e preferência aprendida.
- [ ] Impedir que um evento sem causa rastreável altere o estado emocional.

### P16 — Humor de fundo, episódio e transições

- [ ] Separar humor lento de fundo, episódio emocional causal e expressão do turno.
- [ ] Unificar `humor_level`, estado emocional categórico e avaliação causal sem
  perder compatibilidade com voz, avatar e contexto existente.
- [ ] Implementar inércia, prioridade, decaimento e recuperação para evitar mudanças
  bruscas ou emoções presas.
- [ ] Cobrir arcos de repetição, erro próprio, falha do sistema, conquista,
  correção, vulnerabilidade, pedido de desculpas e mudança de assunto.

### Continuação de P16 — reidratação de episódio e humor — 27/09/2026

Na inicialização, a persistência carregava `current_emotion` e o nível sem
carregar o episódio causal. Assim, o prompt podia receber `brava` depois de
reiniciar, enquanto o retrato expressável da voz e do avatar devolvia `calma`.
O snapshot também gravava `humor_level`, mas o carregador o descartava e não
gravava o horário necessário para decaimento. REDs com o carregador e o estado
compartilhado reais reproduziram as divergências: ausência de evento, evento
vigente, evento expirado e humor recente.

O snapshot agora conserva o episódio causal expressável e o relógio do humor.
No carregamento, o contrato emocional valida causa, validade e compatibilidade
de emoção e nível; só então reidrata o episódio e aplica o decaimento pelo
tempo passado. Sem causa vigente, a categoria volta a `calma`. Humor recente
é restaurado; humor antigo decai até zero, e um registro legado sem horário
volta ao neutro. O ciclo de escrita e leitura em SQLite real passou, assim
como 172 testes de persistência, mente e política vizinha. O roteiro P15 pelo
`laylay.py` passou 8/8, sem alertas, p95 de 12,963 s, e observou o elogio
final como `envergonhada` nível 2 com origem e evidência causal. A suíte
completa terminou com 7.470 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
aprovados. P16 continua aberta para prioridade entre eventos e os demais
arcos de transição.

A leitura expressável tinha outra divergência temporal: validava o prazo do
evento causal, mas não a duração nem as interações restantes do episódio.
Sem novo turno, voz e avatar podiam conservar uma emoção cuja duração já
terminara. O primeiro teste ficou verde pelo motivo errado, pois sua fixture
dava ao evento o mesmo prazo do episódio; ao separar os dois relógios, o RED
apareceu na leitura. O retrato agora exige ambos os prazos e interações
restantes. A projeção do avatar precisou entregar esses campos ao mesmo
contrato; um RED específico comprovou que antes ela devolvia `calma` enquanto
a voz lia `brava` no episódio vigente. Testes de composição antigos montavam
episódios sem dados temporais; foram ajustados para usar o aplicador canônico,
preservando suas expectativas de voz e reação visual. O roteiro de processo
após o ajuste do retrato passou 8/8, sem alertas, p95 de 12,623 s; após a
projeção visual, 307 testes focados e vizinhos passaram. A suíte completa
terminou com 7.472 aprovados, 1 ignorado, 14 xfailed e 56 subtestes aprovados.
`git diff --check` permaneceu limpo.

### Continuação de P16 — prioridade causal entre episódios — 27/09/2026

Um resultado expressável mais fraco substituía imediatamente um episódio forte
ainda vigente. O RED mostrou a primeira divergência em
`aplicar_evento_emocional`: o publicador aceitava corretamente o fato novo,
mas a transição de episódio não comparava intensidade e relevância. A hipótese
de que toda emoção menor deveria ser bloqueada caiu no controle com sucesso
confirmado após falhas consecutivas do mesmo alvo: essa recuperação precisa
substituir a irritação. Um sucesso rotineiro e uma recuperação de outro alvo
não precisam fazê-lo.

O estado agora mantém o episódio vigente quando o fato novo tem nível menor,
ou igual nível e menor relevância; o humor de fundo ainda incorpora a nova
evidência. Uma recuperação operacional observada, confiável e do mesmo alvo
pode abrir o arco de alívio. O setter compartilhado devolve se o evento
publicado realmente se tornou o episódio ativo. Um segundo RED mostrou que o
adaptador operacional usava a aceitação do publicador para colorir a fala,
mesmo quando a prioridade conservava o episódio anterior. A expressão agora
exige também a confirmação do setter. O contrato vale para qualquer fonte
que use o estado e para qualquer habilidade que use esse adaptador.

Os controles de prioridade, recuperação pelo avaliador real, publicador e
setter compartilhados, e expressão operacional passaram com os testes
vizinhos (85 aprovados). O roteiro de processo `laylay.py` passou 8/8, sem
alertas, p95 de 13,421 s; ele não contém uma sequência operacional de
prioridade. A suíte completa terminou com 7.476 aprovados, 1 ignorado,
14 xfailed e 56 subtestes aprovados. Depois desse passe, o motivo de recusa
foi tornado genérico para não atribuir toda falha à prioridade, e um controle
negativo confirmou que o setter recusa evento ausente ou com causa diferente;
os testes focados finais passaram 86/86. P16 permanece aberta para os demais
arcos e para a prova sequencial no processo de uma troca de episódios.

### Continuação de P16 — desculpa por repetição — 27/09/2026

A leitura compartilhada classificava “Desculpa, repeti o pedido mesmo depois de
você confirmar” como informação. Após quatro receipts de redundância visível,
o episódio `brava` nível 3 sobrevivia ao primeiro pedido de desculpas sem
redução de nível: o decaimento comum ainda mirava nível 3 nessa interação.
Os REDs localizaram duas fronteiras: reconhecimento da função do turno e
transição do episódio. Uma desculpa citada por terceiro já não passava pelo
reconhecimento direto; uma desculpa do usuário diante de uma falha atribuída
ao sistema não deveria aliviar a irritação causada por esse sistema.

O classificador canônico agora reconhece desculpas diretas com admissão de
repetição ou insistência. No decaimento, esse contexto reduz um nível do
episódio de bronca por repetição atribuída ao usuário, preservando a causa,
o prazo e o consumo normal de interações. Ele não altera episódios de outra
responsabilidade ou arco, nem converte a desculpa em autorização operacional.
Uma sequência com avaliador real, publicador e setter compartilhados confirmou
quatro receipts, um turno intermediário e a desculpa: `brava` 3 → 3 → 2.
Os testes focados e vizinhos passaram 58/58; a suíte ampla terminou com
7.484 aprovados, 1 ignorado, 14 xfailed e 56 subtestes aprovados.

A prova ainda é de integração com componentes reais. O roteiro conversacional
de processo não contém essa sequência operacional, e os demais arcos da P16
continuam abertos.

### Continuação de P16 — vulnerabilidade interrompe bronca — 27/09/2026

“Estou um pouco triste hoje” já tinha leitura emocional causal no roteiro P15,
mas a função comunicativa compartilhada a classificava como `informacao`.
Com um episódio `brava` ativo, o decaimento receberia esse contexto neutro e
continuaria a bronca. REDs com a frase do roteiro, variações em primeira
pessoa e o estado compartilhado localizaram a primeira divergência no
classificador; relatos em terceira pessoa e citações não eram desabafos do
usuário. A leitura emocional separada reconhecia a tristeza, mas não
alimentava a função usada pelo decaimento, confirmando que as duas fronteiras
não estavam ligadas para essa frase.

O classificador canônico reconhece agora tristeza declarada em primeira pessoa
com intensificadores comuns. A política temporal existente de escuta então
encerra a bronca, limpa o episódio e mantém a Laylay em `calma`; a causa de
tristeza continua sendo do usuário, não vira emoção própria da assistente.
Os controles de terceira pessoa e citação não acionam essa transição. Os
testes focados e vizinhos passaram 170/170, a suíte ampla terminou com
7.491 aprovados, 1 ignorado, 14 xfailed e 56 subtestes aprovados, e o
roteiro real `laylay.py` passou 8/8 sem alertas (p95 de 14,01 s). Esse
roteiro exercita a frase vulnerável a partir do estado neutro; a interrupção
de bronca foi comprovada na integração com estado compartilhado.

### Continuação de P16 — encerramento de assunto e episódio — 27/09/2026

O classificador compartilhado de encerramento já reconhecia “Mudando de
assunto: como está o tempo?” como fechamento de tópico. O refinamento mental,
porém, entregava apenas a função comunicativa `informacao` ao decaimento.
O primeiro RED mostrou essa perda de contexto; depois de passar o fechamento
canônico, outro RED mostrou que o estado temporal ainda mantinha `brava`.
Uma pergunta comum sem marcador de mudança continuou como controle: não
deve encerrar o episódio por mera diferença de palavras.

O refinamento agora entrega `mudanca_assunto` quando o classificador existente
confirma o fechamento do tópico. O decaimento limpa o episódio nessa fronteira
explícita, mantém `humor_level` e não cria nova causa emocional. Testes com
`EstadoContextoRuntime`, `RespostaConversacionalRuntime` e estado compartilhado
confirmaram a transição; 116 testes focados e vizinhos passaram. A suíte ampla
terminou com 7.494 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
aprovados. Uma sonda reproduzível em processo separado importou a composição
real de `laylay.py` e chamou seus callbacks com quatro receipts sintéticos de
redundância: `brava` 3 permaneceu no turno comum, mudou para `calma` 1 no
fechamento explícito e preservou o humor de fundo (-2). As projeções usadas
por voz e avatar concordaram em `brava` 3 e depois em `calma` 1. A sonda
`scripts/roteiros/sonda_personalidade_viva_p16_composicao.py` terminou com
código zero; não iniciou o loop da assistente, não executou aplicativo nem
comprovou reprodução física de fala/avatar. A validação sequencial no loop
completo e os demais arcos da P16 permanecem pendentes.

### P17 — Liberdade comportamental e recusa segura

- [ ] Substituir bloqueios fixos baseados apenas em `brava nível 3` por uma política
  que avalie causa, responsabilidade, risco, necessidade e reversibilidade.
- [ ] Permitir bronca direta, recusa de retrabalho redundante e uma resistência
  contextual a pedidos opcionais de baixo risco.
- [ ] Preservar execução de ações urgentes, de segurança e acessibilidade.
- [ ] Fazer a braveza mirar o comportamento observado, nunca inteligência,
  aparência, identidade ou valor da pessoa.

### P18 — Integração de causas em todos os contextos

- [ ] Ligar conversa, comandos, proatividade, feedback, notificações e modo jogo
  ao contrato emocional canônico.
- [ ] Fazer aceitação, recusa, correção, repetição e silêncio qualificado chegarem
  ao aprendizado compartilhado.
- [ ] Manter a LLM como autora da fala cotidiana e um compositor local rápido e
  variável no jogo, sem chamada adicional ao modelo.
- [ ] Garantir uma decisão e uma fala por turno, sem conflito entre emoção e comando.

### P19 — Expressão multimodal sincronizada

- [ ] Fazer texto, comprimento, ritmo, prosódia, volume e avatar consumirem o mesmo
  retrato emocional e a mesma intensidade.
- [ ] Diferenciar visual e voz de `irritada nível 1` e `brava nível 3` sem exagero
  artificial ou perda de inteligibilidade.
- [ ] Sincronizar escuta, pensamento, execução, sucesso, falha e fala com o episódio ativo.
- [ ] Preservar o custo atual: nenhuma chamada extra à LLM somente para ornamentação.

### P20 — Aprendizado de tolerância e relação

- [ ] Aplicar preferência explícita imediatamente, como `pega leve hoje` ou
  `pode me zoar mais`.
- [ ] Exigir várias amostras para ajustes implícitos; correção pesa mais que recusa,
  e silêncio só conta depois de dez minutos sem resposta relacionada.
- [ ] Aprender tolerância separadamente por contexto, como jogo, conversa pessoal
  e comandos, sem criar um rótulo global da pessoa.
- [ ] Persistir apenas preferências e evidências com proveniência; episódios e
  julgamentos continuam temporários.

### P21 — Diagnóstico, validação e ativação final

- [ ] Expor emoção, intensidade, causa, responsável, confiança, transição,
  validade, expressão ou supressão e decisão comportamental no diagnóstico.
- [ ] Criar uma matriz de cenários causais, testes de transição e invariantes de
  segurança, além de regressões no terminal, voz, jogo e chat.
- [ ] Provar que emoção não altera resultado, não duplica fala, não atravessa
  vulnerabilidade e não permanece depois de perder validade.
- [ ] Ativar a versão final somente depois da suíte completa e de validação real
  sequencial de P15 a P21.

## Contrato obrigatório dos nove pilares

Cada etapa da versão final deve reutilizar os serviços canônicos da mente única e
provar os pilares aplicáveis pelo caminho real da composição:

1. **Contexto:** publicar somente o retrato emocional necessário e respeitar turno,
   assunto, modalidade e validade do evento.
2. **Memória:** separar episódio temporário de preferência durável, sempre com
   proveniência e política de sensibilidade.
3. **Aprendizado:** agregar aceitação, recusa, correção, repetição e silêncio
   qualificado antes de mudar comportamento implicitamente.
4. **Linguagem natural:** compreender preferências, pedidos de calma, brincadeiras,
   correções e referências sem listas privadas de frases por módulo.
5. **Continuidade:** manter causa, alvo e arco entre turnos relacionados e encerrar
   a emoção quando o contexto mudar ou expirar.
6. **Segurança:** separar percepção, emoção, sugestão, autorização, execução e
   confirmação; humor nunca vira permissão.
7. **Diagnóstico:** tornar causa, transição, supressão, falha e resultado
   observáveis sem expor conteúdo pessoal desnecessário.
8. **Consciência da habilidade:** registrar a personalidade emocional no catálogo
   vivo para a Laylay explicar naturalmente como reage, aprende, se acalma e quais
   são seus limites reais, sem inflar o prompt permanente.
9. **Orquestração cooperativa:** publicar relações entre evento, conversa, execução,
   voz, avatar, jogo e aprendizado no quadro canônico, preservando validação e
   autoridade de cada habilidade e sem transformar percepção em permissão.

Uma etapa não pode ser marcada como concluída apenas com callbacks sempre
verdadeiros. A validação deve incluir teste unitário, regressão pelo caminho real,
caso negativo de segurança, consciência da habilidade e caminho cooperativo quando
aplicável.

## Versão ativa

- Responsabilidade: sistema, Laylay, usuário ou ambígua.
- Confiança mínima para provocar o usuário: 90%.
- Provocação máxima ativa: nível 3 em repetição redundante comprovada.
- Escalada com o usuário: primeira repetição espirituosa, segunda debochada,
  terceira irritada e quarta em diante brava; vulnerabilidade e baixa confiança suspendem a bronca.
- Falha de sistema: irritação a partir da segunda repetição em cinco minutos.
- Recuperação após falhas: arco curto de alívio.
- Histórico: até 80 eventos efêmeros da sessão, sem perfil pessoal persistente.
- Diagnóstico: disponível em `/diagnostico mente`, sem autorizar ações.
- Cotidiano: uma única resposta operacional escrita pela LLM a partir do contrato real.
- Modo jogo: frases locais curtas, sem chamada extra à LLM; fallback técnico preservado.
- Ação redundante: Laylay observa o estado, não repete o trabalho e pode recusar com humor.
- Fila de voz: uma fala consolidada por item; comandos simultâneos não são misturados.
- Diagnóstico de autoria: qualquer fallback cotidiano informa o motivo em `[FALA:AUTORIA]`.
- Orçamento da autoria: 8 segundos por padrão, configurável por
  `LAYLAY_AUTORIA_OPERACIONAL_TIMEOUT`, sem alterar o limite da conversa principal.
- Validação explicável: rejeições identificam a regra exata, como promessa nova,
  alvo divergente ou não-ação ambígua.
- Variedade operacional: até quatro falas recentes orientam a LLM; se ela ainda
  repetir a abertura, somente os trechos que ela própria escreveu são reordenados.
- Diagnóstico atual: quedas recuperadas permanecem nos contadores históricos,
  mas não são anunciadas como falhas ativas; retratos tipados mais recentes
  eliminam alertas contraditórios da agenda.
- Assinatura verbal ativa: doce e firme, observadora, opinativa e autoconfiante,
  com cumplicidade e deboche seco apoiados em detalhes concretos.
- Linguagem concreta por padrão: poesia e metáforas são exceção, reservadas a
  pedidos criativos ou a uma comparação curta que realmente esclareça algo.

## Critérios globais de conclusão

- Nenhuma emoção sem causa rastreável.
- Nenhuma atribuição de culpa abaixo de 90% de confiança.
- Nenhuma emoção altera fatos, autoriza risco ou mascara falha.
- Nenhuma braveza atravessa contexto vulnerável.
- Nenhuma fala operacional duplicada ou episódio preso após expiração.
- Cotidiano continua autoral pela LLM; jogo continua rápido e local.
- Texto, voz e avatar refletem o mesmo estado e intensidade.
- Os nove pilares possuem evidência de integração e testes reais.

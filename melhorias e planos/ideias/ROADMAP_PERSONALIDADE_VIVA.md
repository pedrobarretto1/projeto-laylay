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

### Continuação de P16 — responsabilidade própria e conquista — 29/09/2026

Base da investigação: `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch
`main`, com alterações paralelas de ensino preservadas. As fronteiras abaixo
são distintas; não contar cada frase negativa como uma nova raiz.

Na prioridade de episódios, quatro receipts de redundância produziam `brava`
nível 3. Uma falha posterior com responsabilidade explícita da Laylay e
confiança de 98% chegava corretamente ao avaliador e ao publicador como
`autorreparo`, mas a regra de menor intensidade bloqueava `envergonhada` 1.
O RED localizou a primeira divergência no owner do estado. A transição agora
exige origem operacional, fato observado, autoria Laylay, confiança mínima
de 90% e evento tão recente quanto o episódio anterior. Autoria incerta,
outra origem, natureza, arco ou evento anterior continuam bloqueados. A
integração foi exercitada em aplicativos e IoT.

Na resposta, duas das três variantes locais de admissão de erro acrescentavam
“Já corrigi” ou “Corrigi” a um resultado de falha, sem receipt de reparo.
Os REDs cobriram todas as variantes em dois domínios; as confirmações foram
retiradas e o resultado factual continua no início da fala. Admitir autoria
de erro não comprova que a ação foi reparada.

No arco de conquista, a função comunicativa reconhecia palavras de sucesso
mesmo em negação, hipótese, citação e usos como “passei mal”. Os REDs
localizaram a primeira divergência no classificador compartilhado. A leitura
passa a exigir uma afirmação autoral com sentido de sucesso, delimitando
negação por frase e contraste e reutilizando a proteção de metalinguagem.
Uma conquista afirmada encerra somente a bronca por repetição atribuída ao
usuário. A Laylay volta a `calma`, preserva o humor de fundo e usa postura
celebratória; a alegria relatada continua sendo do usuário. Outro arco ou
responsabilidade não é apagado por essa política.

A sonda de composição real foi ampliada: autoria incerta preservou `brava` 3,
autoria comprovada mudou para `envergonhada` 1, conquista negada preservou
`brava` 3 e conquista afirmada mudou para `calma` 1, conservando humor -3.
Voz e avatar concordaram em todas essas projeções. O primeiro passe focado
aprovou 206 testes; a revisão posterior encontrou complementos encadeados
ainda ambíguos, como “consegui ganhar uma dor de cabeça”. Cinco REDs adicionais
cobriram esses complementos, atribuição por terceiros e citação com guillemets;
o mesmo owner agora valida o sentido também no infinitivo encadeado e mantém
os controles positivos. O passe emocional final aprovou 213 testes. Com a
sonda CLI, DEV e latência vizinhos, 313 testes passaram. O roteiro pelo loop
real de `laylay.py` passou 8/8, sem alertas, p95 de 12,621 s. Ele cobre
conquista e vulnerabilidade partindo do estado neutro, não as sequências
operacionais usadas na sonda de composição.

A suíte completa final terminou com 8.285 aprovados, 1 ignorado, 14 xfailed
e 56 subtestes aprovados. O primeiro passe havia revelado quatro sintomas de
uma causa independente: o filtro global de logs ocultava a saída JSON da
CLI OpenRouter. O RED com o filtro real e a correção no canal de stdout estão
registrados separadamente no registro de problemas. `git diff --check`
permaneceu limpo. Nenhum commit foi criado nesta rodada.

Limites: os receipts da sonda são sintéticos. Ela importa os callbacks reais
de `laylay.py`, mas não executa habilidades, loop completo nem áudio físico.
No adaptador normal, `falar_por_status` monta o contexto do resultado apenas
com `destino`; não há fonte de responsabilidade comprovada chegando por esse
caminho. O status de falha sozinho continua com confiança insuficiente.
Não preencher esse dado por suposição. P16 permanece aberta para a fonte
canônica de responsabilidade e a validação sequencial
no loop completo. A suspeita de desculpa seguida de comando permanece
separada no registro de problemas.

### Continuação de P16 — receipt preservado e transições no loop — 29/09/2026

Base mantida em `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`, com
trabalho paralelo preservado. A investigação da responsabilidade encontrou
duas fronteiras: o avaliador promovia confiança ausente/inválida a 98%, e a
reconstrução do resultado para fala descartava contexto e origem do receipt
publicado. Normalização e troca de ID foram falsificadas como causa da perda.

A atribuição agora exige confiança explícita, finita em `[0,1]` e receipt
com origem do executor. Proposta da IA ou contexto sem essa origem permanece
inferência sem expressão; também não interrompe o histórico de receipts reais.
Redundância/repetição não promove uma atribuição explicitamente incerta.
O adaptador transporta contexto e origem da própria publicação concluída,
exigindo concordância de marcador, IDs, intent, status, alvo e flags. Nova
tentativa invalida o snapshot; cópia profunda isola mutações. Não recupera
culpa dos parâmetros da IA ou da última ação global. Os controles compostos
usam registrador, avaliador, publicador, setter e estado compartilhados reais
em aplicativos e IoT; não constituem um novo produtor de atribuição.

O roteiro `scripts/roteiros/roteiro_teste_personalidade_viva_p16.py` percorreu
o loop real de `laylay.py`, abrindo/focando a Calculadora e relendo sua janela.
Após a guarda e antes do transporte, 4/13: os receipts eram reais, mas sua
origem desaparecia na fala e os eventos ficavam neutros. Após transporte,
12/13; a falha restante era foco realmente executado (`app_focado`), sem
redundância. A preparação com maximização observada manteve as expectativas
emocionais: 14/14, zero alertas, p95 10,947 s, no artefato
`roteiro_teste_personalidade_viva_p16-20260929-225617-497865`. Nove receipts
distintos comprovaram sete redundâncias, progressão até `brava` 3,
preservação na conversa comum, encerramento por conquista, atenuação pela
desculpa, interrupção por vulnerabilidade e encerramento por assunto novo.
Os IDs dos episódios coincidiram com os receipts e sobreviveram aos turnos
intermediários adequados. Não houve injeção de estado ou receipt nesse loop.

Outro passe após a correção de autoria ficou em 5/14 porque o foco mudou
durante a cadeia e os pedidos realmente focaram a janela, reiniciando a
contagem de redundâncias. Esses REDs permanecem no artefato, não são outra
prova verde da sequência. Esse passe revelou também a mesma lacuna de
transição em intensidade menor: `conquista` estava correta no plano, mas
o decaimento só encerrava `bronca_brincalhona`, não `provocacao_afetuosa`.
Nove REDs com controles fortes preservados e composição do avaliador real
em dois domínios sustentaram ampliar a política aos dois arcos de repetição
atribuída ao usuário. Outros arcos/responsabilidades permanecem protegidos.
O painel curto congelado no runtime real passou 3/3, zero alertas, p95
9,608 s: maximização observada, primeiro receipt redundante → `debochada` 1,
conquista → `calma` 1. Artefato
`roteiro_conquista_inicial-20260929-231252-958844`.

Na fala, o loop expôs um mecanismo de F2/P19 já registrado: o motivo técnico
do reparo era enviado como conteúdo ao modelo e aparecia na confirmação.
O código do diagnóstico permanece local, o reparo recebe somente fatos do
receipt/restrições existentes, e identificadores técnicos sem fonte factual
são recusados pelo verificador canônico. Nomes legítimos com underscore e
diagnósticos realmente publicados pelo executor continuam permitidos.
A versão final também é revalidada após variar a abertura; a aprovação do
rascunho não aprova uma transformação posterior. O teste antigo de variação
agora usa uma recusa que conserva o fato observado na primeira frase,
mantendo a expectativa de variar a abertura. Não enfraquece o verificador.
Quatorze respostas reais no passe posterior não continham códigos técnicos,
apesar dos motivos continuarem nos logs locais. Isso não certifica toda
alegação causal em prosa; o mecanismo e seus limites estão vinculados a F2.

Os testes focados finais passaram 395/395. A prova de importação da composição
foi repetida após encerrar o processo real: a primeira tentativa concorrente
foi corretamente contida pela trava de instância única, sem patch nessa trava.

O primeiro passe da suíte completa teve 8.384 aprovados e uma falha: a fixture
de timeout observado de P18 não declarava `origem="executor"`, exigida pelo
contrato de procedência. A fixture passou a representar o receipt publicado
em produção, mantendo as expectativas e os controles de origem não confiável.
P18 e o avaliador passaram juntos em 83 testes. A repetição completa terminou
com 8.385 aprovados, 1 ignorado, 14 xfailed e 56 subtestes aprovados em 181,47 s.
Esse GREEN de regressão não substitui as provas de runtime e seus limites acima.

P16 permanece aberta. A fonte de autoria própria ainda precisa preservar
procedência da proposta principal antes dos reparos e validar coerência de
turno/plano/retrato. O filtro atual não transporta essa prova; IDs/textos
divergentes não podem produzir culpa. Uma rejeição de planejamento não será
rebatizada como receipt de executor. Falha do sistema/recuperação e autoria
própria ainda têm provas locais, não sua sequência externa completa. Voz
física ficou silenciosa; a sonda de composição conserva a prova das projeções
de voz/avatar. Nenhum commit ou push desta continuação; nenhum desligamento.

### Continuação de P16 — coerência e preservação da fonte — 30/09/2026

Base mantida em `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`, com a
worktree paralela preservada. A lacuna de identidade descrita em 29/09 foi
reproduzida também pelo callback instalado em `laylay.py`: playlist, IoT e
aplicativos aceitavam uma proposta de exclusão ao receber apenas o retrato de
outro turno. Os pedidos corretos passavam antes da troca. Revisões legítimas
e contratos legados falsificaram a hipótese de proibir qualquer diferença
textual ou exigir retrato em toda chamada histórica.

O owner `filtrar_comandos_pelo_turno` agora exige seis IDs coerentes e os
textos correspondentes quando há identidade/referência de retrato moderno.
Campos ausentes não permitem rebaixar esse caminho para legado. Revisões
comparam o texto operacional efetivo, conservando a fala original. O caminho
legado sem metadados de retrato mantém sua compatibilidade; divergências
explícitas continuam recusadas. A comparação textual usa os 500 caracteres
publicados pelos produtores; não comprova integridade de sufixos além disso,
autoria do modelo, alvo parametrizado ou efeito.

Na fonte principal, a primeira perda acontece antes do filtro: o preparador
pode substituir o bruto recebido. `ContratoPropostaPrincipal` conserva agora
a string original em uma instância interna imutável, criada pelo runtime antes
do preparador. Origem e ausência de autoridade são fixadas pelo código. O ID
vem do turno capturado, sem usar o fallback do ledger; mappings do JSON não
materializam procedência. Vazio, falha técnica, retorno não textual ou vínculo
ausente não produzem procedência suficiente. O callback de dois argumentos
permanece compatível. Uma guarda de retorno `Mapping` preserva a falha
observável do preparador, evitando transformar `None`/`[]` em fala neutra.

Produção alterada somente em `decisao_turno.py`, `contratos_turno.py` e
`resposta_ia_runtime.py` nesta continuação. A emissão capturada não é culpa,
receipt, autorização ou evento emocional; não há parser nem chamada adicional.
O bruto não é projetado em prompt, log ou receipt e não há última proposta
global. A leitura reparada ainda publicada como principal e as cópias rasas
dos campos legados ficam fora deste candidato.

Validação: 23 REDs do filtro e três REDs do callback real antes da guarda;
149 testes e 22 subtestes verdes na seleção de coerência. Preservação: 26 REDs
iniciais, dois REDs adicionais de retorno inválido e 48 verdes nos contratos e
registro de conversa. O início real da composição aceitou cinco controles de
playlist, IoT, aplicativos e música, incluindo revisões. O transporte do
snapshot usa runtime/normalizador reais com retorno fixado na porta do modelo;
isso não prova uma falha autoral gerada numa conversa externa.

O primeiro passe amplo teve 8.451 aprovados e duas falhas por interferência do
novo teste: importar `laylay.py` mais cedo mudava ambiente e `print` para os
módulos seguintes. Ambos passaram separados, falharam após o teste novo e
passaram juntos em 13 controles após isolar o bootstrap num subprocesso.
As oito expectativas da composição permanecem; configuração e terminal não
foram alterados. Regressão completa: **8.453 aprovados, 1 ignorado, 14 xfailed
e 56 subtestes aprovados em 198,46 s**.

P16 permanece aberta para a atribuição causal da proposta preservada e sua
publicação emocional no mesmo turno. Coerência interna não vincula ainda a
fonte capturada ao frame atual do filtro. Uma sonda local separada também
mostrou que um plano estrangeiro com receipt confirmado pode sustentar uma
fala de efeito: o atualizador preserva comandos anteriores ao receber `[]`.
A composição completa desse caso não foi validada. Preservação por omissão no
mesmo plano é legítima; investigar correlação antes de remover essa proteção.
Falha/recuperação no loop e áudio físico continuam pendentes. Nenhum commit
ou push desta continuação.

### P16 — evidência vinculada à ocorrência antes da confirmação — 30/09/2026

A pendência de receipt/fala acima foi reproduzida na composição instalada em
`laylay.py`, com receipts sintéticos em arquivos, IoT e playlists. O filtro
recusou as três propostas por identidade divergente. A primeira fronteira RED
seguinte foi o atualizador: ao receber `comandos=[]`, publicou o receipt do
plano estrangeiro como parte de `resposta_planejada`. O callback real do
finalizador consultou esse plano e entregou “Apaguei”, “Liguei” e “Criei” sem
problemas. São seis REDs, três de publicação e três de consumo, ligados ao
mesmo contrato de correlação; não são seis raízes independentes.

Controles internos conservaram os mesmos receipts e as mesmas falas quando
turno, plano e retrato eram coerentes. Isso falsificou tanto uma falha geral
do verificador quanto a hipótese de apagar receipts em toda atualização vazia.
O dispatcher real recebeu lista vazia e nenhum executor foi chamado. Apenas
as portas de persistência e entrega de voz foram substituídas; não há prova de
efeito externo ou áudio físico nesses testes.

O contrato `motivo_incoerencia_contratos_turno` é compartilhado pelo filtro,
atualizador e verificador. IDs opacos inteiros/string continuam compatíveis;
booleanos, frações e coleções não criam identidade. Textos modernos exigem
strings. O atualizador valida, mescla e publica plano/trilha na transação já
existente do estado compartilhado. Incoerência aborta a publicação, preservando
receipts anteriores; atualizações vazias coerentes continuam a conservá-los.

O verificador captura o snapshot real e recusa a evidência antes de consultar
o validador de alegações. Entrega uma conclusão segura e observável, sem
confirmar efeito ou atribuir culpa. Outro RED demonstrou que um turno publicado
durante o cálculo era sobrescrito pela conclusão antiga. A comparação do frame
e a publicação final agora ocorrem juntas; verificação/pesquisa ficam fora do
lock. Métricas, avaliações, auditoria, referência musical e casos candidatos
são publicados junto da conclusão somente enquanto o frame lido continua atual.

Produção desta raiz: `decisao_turno.py` e `orquestrador_turno_runtime.py`.
O writer ainda usa o frame vigente: sua API não recebe a ocorrência esperada,
portanto um callback tardio que só chegue após a troca para outro frame coerente
não é contido por essa guarda. Mescla por intent entre solicitações diferentes
e correlação da emissão principal ficam fora do candidato. Adaptadores legados
sem a API transacional mantêm compatibilidade, sem garantia de atomicidade.
O escopo validado é a incoerência do frame e sua troca durante a verificação,
não toda correlação de origem de receipts. P16 permanece parcial.
Os 42 REDs iniciais e oito REDs de malformação textual precederam as respectivas
guardas; controles de legado, revisão e preservação passaram. GREEN: 59 testes
canônicos, 288 com os vizinhos e 20 da composição isolada. Uma seleção manual
com importação antiga de `laylay.py` antes de configuração/terminal repetiu a
interferência global já diagnosticada; não houve patch nesses dois módulos.
Regressão completa: **8.521 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
aprovados em 200,79 s**. `git diff --check` limpo; nenhum commit ou push.

A investigação da fonte própria também falsificou três atalhos: uma emissão
conhecida pode ser confrontada com outro frame internamente coerente; o alias
legítimo `criar_playlist` precisa do adaptador canônico antes de conferir a
intent; e `limpar_resposta_da_ia` pode recuperar `open_app` de uma explicação
solta. A mesma menção no campo `fala`, com `comandos=[]`, não é uma proposta.
A próxima fronteira desse arco é preservar a procedência na mesma decodificação
canônica de `higiene_resposta_ia.py`, sem parser paralelo. Só depois cabe
correlacionar a emissão, normalizar o alias e demonstrar a incompatibilidade.
Rejeição, recuperação textual, estado obsoleto e reparo continuam insuficientes
para atribuição emocional. Não fabricar receipt ou culpa a partir desses casos.

### P16 — procedência da extração antes do reparo — 30/09/2026

Continuação da mesma fonte própria, na base `90a2fb8`, `main`, sem alterar o
baseline ou a worktree paralela. A primeira perda restante estava no decoder:
JSON com campo operacional, recuperação de lista truncada e recuperação de
`open_app` de explicação solta entregavam somente a mesma tupla fala/comandos.
Além disso, decodificar somente depois da autocorreção atribuiria ao original
o método usado na resposta substituta. A menção em `fala`, com `comandos=[]`,
continuou controle negativo; recuperar candidato não demonstra autoria de erro.

O algoritmo existente agora tem uma única entrada com resultado tipado,
`decodificar_resposta_da_ia`; `limpar_resposta_da_ia` permanece sua fachada
legada. `ExtracaoRespostaIA` registra método, presença do campo operacional,
contagem efetiva após retirar `NONE` e string exata original, com campos
imutáveis e bruto oculto no repr. Origem e ausência de autoridade são fixadas
pelo código. Só JSON objeto com campo explícito e candidatos efetivos recebe
o marcador de proposta operacional explícita; envelope textual normalizado,
recuperação, tupla, ausência e falha técnica não recebem esse marcador.
Ele descreve apresentação, sem validar intenção, alvo, autorização ou efeito.

O preparador decodifica antes do reparo e reutiliza o resultado quando não há
substituição. O transporte conserva a extração original; quando existe uma
proposta principal tipada, exige procedência conhecida e igualdade da string
capturada. Metadados em mappings/JSON não materializam essa evidência. Essa
igualdade vincula emissão e extração, ainda não a ocorrência vigente do filtro.
A contagem também não congela identidades ou parâmetros dos comandos.

Produção desta continuação: `higiene_resposta_ia.py`,
`processamento_resposta_ia.py` e `contratos_turno.py`. Nenhum parser paralelo,
nova chamada ao modelo, mudança de autorização ou evento emocional. A API
legada mantém fala/comandos; o mapping interno ganha somente a extração tipada.

Validação: 27 REDs iniciais antes do contrato/decoder e dois REDs posteriores
de método interno malformado, com controle `None`; 30 testes novos verdes.
Seleção ampliada: **573 aprovados em 9,15 s**, incluindo 24 da composição.
Quatro controles usam o preparador instalado em `laylay.py`, decoder e
normalizador reais, com transporte de reparo e portas persistentes isolados.
Não houve chamada externa ou executor. A sonda inicialmente parou na trava
porque a Laylay estava aberta; a fixture passou a usar a trava real com
identidade própria de subprocesso, sem iniciar `main`. Um adapter de teste
incompleto foi corrigido para reutilizar `RegistroModeloLLM` e seu contrato.
Comparação diagnóstica contra o decoder do HEAD: **79 entradas sem divergência
de fala/comandos**. Regressão ampla: **8.555 aprovados, 1 ignorado, 14 xfailed
e 56 subtestes aprovados em 203,93 s**. O processo de pytest também usou a
trava real com identidade própria para importar a composição enquanto a sessão
do usuário estava aberta; isso não valida o loop dessa sessão. `git diff --check`
limpo; HEAD preservado.

P16 permanece aberta: correlacionar a emissão ao frame vigente, preservar e
adaptar os candidatos originais antes de demonstrar incompatibilidade; somente
depois produzir erro próprio. Leitura reparada ainda publicada como principal,
callbacks tardios, receipts mesclados por intent, falha/recuperação no loop e
áudio físico continuam pendentes. Nenhum commit ou push desta continuação.

### P16 — emissão vinculada ao turno antes da publicação — 30/09/2026

Continuação da fonte própria na base `90a2fb8`, `main`, com worktree paralela
preservada. Um frame internamente coerente não identificava a emissão recebida:
trocar todo o turno/plano/retrato durante o preparador aceitava uma proposta
antiga, inclusive repetindo a mesma frase. Trocar a operação ainda atribuía ao
comando antigo uma incompatibilidade de intenção do turno novo. Os controles
com a mesma fonte e o mesmo frame passaram, falsificando falha geral do filtro
e a hipótese de que coerência interna bastaria para identificar a ocorrência.

O owner compartilhado de `decisao_turno.py` agora recebe a principal tipada e
confere seus ID/texto originais contra os seis IDs e a fala original do frame.
Revisões continuam usando a visão operacional no retrato, sem trocar a fala
original da fonte. A projeção pública de 500 caracteres normaliza igualmente
espaços finais; não certifica sufixos ou parâmetros fora dessa projeção.
`ValidadorComandosTurnoRuntime` captura um único snapshot do estado real e
reutiliza o filtro. A composição de `laylay.py` instala esse objeto no callback
existente. A chamada legada de um argumento conserva seu formato, sem declarar
vínculo de procedência.

`resposta_ia_runtime.py` encaminha a fonte capturada e valida a ocorrência
antes da leitura semântica, writer, dispatcher e finalização, mesmo quando o
reparo ou a autoridade zeram a lista. Fonte de outra ocorrência aborta o
registro do turno antigo e não publica sua resposta no novo. Falha técnica
no mesmo turno conserva `ocorrencia_vinculada=True`, mas não valida proposta
nem comandos: a contingência pode concluir. Retornos modernos malformados
ou contraditórios abortam com diagnóstico, sem repetir o callback legado.
O consumidor confronta procedência declarada com a fonte capturada, recusa
comandos quando o retorno declara ausência de procedência/autorização e
preserva o veto da autoridade capturada mesmo diante de comandos devolvidos.
Correlação não concede autorização, comprova efeito ou produz culpa.

Produção desta continuação: `decisao_turno.py`, `resposta_ia_runtime.py` e
somente o wiring em `laylay.py`. Nenhum parser paralelo, evento emocional,
mudança no writer ou nova chamada ao modelo. Não altera os candidatos originais
do decoder nem adapta aliases nesta etapa.

Validação: 23 REDs iniciais, incluindo seis no callback instalado pela composição;
16 REDs adicionais no limite textual, listas vazias e retornos contraditórios
precederam os refinamentos. Dois erros de expectativas no teste foram corrigidos
sem contar como falhas de produção: ordem de publicação do receipt e vínculo
esperado ao reutilizar ID com texto diferente. GREEN focado: **72 testes**, 42
do novo contrato e 30 da composição isolada. Seleção ampliada anterior aos
últimos controles: **722 aprovados em 11,73 s**. Os testes de composição usam
o callback e o início de turno instalados, com a trava real sob identidade de
subprocesso; não iniciam `main`. Runtime de resposta e estado/validador reais
também passaram com portas de modelo, publicação, dispatcher e fala isoladas.
Falha técnica preservou conclusão sem comandos e uma chamada principal.
Isso não demonstra execução externa ou áudio físico.
Regressão completa: **8.603 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
aprovados em 195,97 s**. O processo usou o mutex real com identidade própria
de teste para importar a composição, sem disputar a sessão aberta do usuário.
`git diff --check` limpo; HEAD preservado.

P16 permanece parcial: congelar/adaptar candidatos originais e demonstrar a
violação antes de produzir erro próprio. Snapshot valida somente o instante
da leitura; corrida após o retorno e writer sem ocorrência esperada continuam
abertos, assim como receipts mesclados por intent, leitura reparada publicada
como principal e falha/recuperação no loop real. Nenhum commit ou push.

### P16 — candidatos originais isolados antes do reparo — 30/09/2026

**Prioridade posterior do Pedro em 30/09:** resolver os 14 xfails antes de
prosseguir. São 13 casos da recomendação P02 e um da segmentação P06, duas
causas separadas desta P16. Corrigidos no escopo, com testes sem xfail,
composição instalada e runtime focal 4/4; ver
[relatório P02/P06](../relatorio/RELATORIO_P02_P06_20260930.md).
Esta entrega não conclui a P16 nem certifica toda a qualidade técnica da conversa.

Continuação da mesma fonte própria, base `90a2fb8`, `main`, sem alterar a
worktree paralela. A contagem não conservava o payload: a lista do decoder e
o retorno legado compartilhavam coleções aninhadas, e uma mutação posterior
alterava o candidato disponível. O reparo também podia substituir comandos
sem deixar a árvore original estruturada no transporte. Sondas nos três
domínios falsificaram suficiência da contagem e uso universal do adaptador flat:
este perde `params` de `PLAYLIST_CREATE` e não reconhece `APP_OPEN`/`IOT_CONTROL`
canônicos. Aliases legítimos de playlist/IoT foram aceitos após adaptação; sua
rejeição crua não demonstra autoria de erro. Recuperar `open_app` de uma
explicação mantém origem não explícita mesmo depois da adaptação.

O owner de `contratos_turno.py` agora contém `SnapshotComandoIA`, uma árvore
JSON codificada em string interna imutável; cada `como_dict()` devolve uma
cópia independente. Bruto e payload não aparecem no repr. Tipos não JSON,
chaves convertidas, tuplas, ciclos e números não finitos não materializam
snapshot suficiente. `ExtracaoRespostaIA` conserva tuplas de originais e
visões normalizadas, alinhadas por posição depois da retirada de `NONE`.
Quantidade/tipos incompatíveis invalidam o snapshot inteiro; candidato não
normalizável mantém posição `None`, sem desaparecer ou mudar o original.
`candidatos_preservados` e `normalizacao_completa` são requisitos distintos;
lista vazia não representa normalização operacional. Origem e ausência de
autoridade continuam fixadas pelo código.

Em `higiene_resposta_ia.py`, a captura ocorre no mesmo `concluir` do decoder,
antes até do callback de limpeza da fala. A lista legada não é substituída
pela visão. Um normalizador puro junto ao adaptador existente reconhece
`intent`+`params` pelo catálogo compartilhado e conserva toda a árvore dos
parâmetros. Somente o formato flat passa pelo adaptador canônico; campos
concorrentes, `action`, forma desconhecida ou malformada ficam sem visão
suficiente. A normalização opera em cópias. O transporte já existente conserva
esse objeto tipado após reparo e exige bruto original igual ao da principal.
Nenhum parser de linguagem, tabela privada de intents ou chamada nova ao modelo.

Produção desta continuação: `contratos_turno.py`, `higiene_resposta_ia.py` e
somente o normalizador puro em `dispatcher_comandos_json.py`. O executor,
filtro de autorização, writer e produtor emocional não foram alterados.
Snapshot/normalização não validam parâmetros, disponibilidade, autorização,
receipt, culpa ou alvo efetivo. O dispatcher ainda possui preparação própria
de alvo/`pc_b`; a visão direta não certifica essa etapa. O marcador explícito
descreve o campo recebido e pode ser verdadeiro num JSON com `NaN`, enquanto
ambos os requisitos novos são falsos. Futuro consumidor deve exigir os gates
cumulativos e comprovar a violação, sem promover esse marcador sozinho.

Validação: **28 REDs** alcançaram a perda antes do candidato, com 30 controles
anteriores verdes. GREEN final: **149 focados** — 65 de procedência, 41 da
composição e 43 do vínculo/runtime. Onze controles novos usam o preparador
instalado em `laylay.py`, normalizador e início reais, nos três domínios,
inclusive recuperação e reparo. Outro controle usa runtime da resposta,
preparador, estado/validador e normalizador reais: principal original, snapshot
e visão chegam após reparo, lista executável vazia, uma chamada principal.
Portas externas/modelo/voz são isoladas; a sonda usa trava real com identidade
própria e não inicia `main`. Não comprova efeito externo ou áudio físico.
Regressão completa: **8.650 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
aprovados em 201,44 s**. Mutex real sob identidade própria do pytest preservou
a sessão aberta. `git diff --check` limpo; HEAD mantido.

P16 permanece parcial. Próxima fronteira da fonte: demonstrar a violação com
contrato/owner suficientes e só então produzir erro próprio no mesmo turno.
O retrato local de “abre a Calculadora” retornou `intents_permitidos=[]`,
portanto não sustenta prova de incompatibilidade; limite separado de cobertura
do árbitro, sem patch nessa etapa. Leitura reparada ainda publicada como
principal, writer sem ocorrência esperada, corrida após validação, mescla de
receipts por intent e falha/recuperação no loop real continuam pendentes.
Nenhum commit ou push.

#### Checkpoint P16 — violação original antes da atribuição — 30/09/2026

Mesma raiz e base `90a2fb8`, `main`, worktree paralela preservada. Primeira
fronteira: o validador recebia somente comandos posteriores ao reparo. Lista
reparada vazia apagava a evidência de incompatibilidade da emissão original.
Fonte preservada e ocorrência coerente já existiam, mas não chegavam juntas
ao owner dessa comparação. Oito REDs anteriores ao candidato reproduziram a
perda em playlist/IoT, veto de pergunta/recusa e transporte pelo runtime.

O validador compartilhado agora recebe a extração original por um método novo,
mantendo extensões com um ou dois argumentos. Compara snapshots normalizados
originais com o MESMO frame isolado usado pelo filtro executável. Não há outro
classificador: a decisão é a do filtro canônico. Prova exige fonte tipada,
bruto exato, ocorrência vinculada, campo operacional explícito, preservação e
normalização completas, flags booleanas e decisão de owner conhecido.
`ViolacaoPropostaPrincipal` conserva ID, posição, intent e restrição em objeto
imutável validado, sem payload/receipt/autoridade. Posições distinguem propostas
da mesma intent; reparo legítimo não apaga prova original, e reparo indevido
não incrimina uma original correta.

Há dois contratos demonstráveis: proposta de efeito contra veto inequívoco,
ou intent fora de operação explícita cujo catálogo permitido está delimitado.
Veto não depende de todos os nomes de compatibilidade estarem no catálogo vivo:
o retrato de arquivos ainda inclui `MOVE_ITEM`, ausente nele. Essa diferença
falsificou a exigência universal de catálogo para prova de autorização; a
checagem estrita continua necessária para provar incompatibilidade positiva.
Aliases legítimos, parâmetros vazios, app sem intents delimitadas, recuperação,
falha técnica, fonte parcial/malformada e frame estrangeiro não viram culpa.
Decisão já consolidada por arbitragem fica sem prova nesta versão conservadora.

O runtime encaminha a fonte mesmo após reparo para `[]` e registra somente o
fato local em diagnóstico canônico (`proposta_original`), com ID/índice/motivo,
sem texto privado, efeito ou evento emocional. Exige vínculo positivo também
na observabilidade. Tipagem/motivos inválidos não materializam a prova; campos
de culpa/prova no JSON da IA não são autoridade. Produção desta continuação:
`contratos_turno.py`, `decisao_turno.py`, `resposta_ia_runtime.py`. Executor,
writer, parser de linguagem e estado emocional fora do candidato.

GREEN focado final: **199 testes** — 87 de vínculo/runtime, 65 de procedência e
47 de composição, incluindo posição e metadados. Composição instalada usa
início/preparador/decoder/validador reais,
nos três domínios e controles sem cobertura. Runtime com componentes reais e
portas externas isoladas confirma uma chamada principal, lista final vazia e
diagnóstico; troca de ocorrência e negação do vínculo suspendem o registro.
Não comprova loop desktop, executor externo ou áudio físico. Nenhuma chamada
nova à LLM foi adicionada. Avaliação pura recusa restrição não coletável; filtro
legado executável ainda pode lançar erro com `intents_permitidos=42`, achado
separado sem falsa prova ou efeito, não corrigido nesta fronteira.

P16 parcial. Próxima fronteira da mesma cadeia: consumir a prova tipada em um
produtor emocional com origem própria, conferir ocorrência vigente ao publicar
e demonstrar erro próprio/recuperação. Não fabricar `ResultadoAcao` do executor
para conseguir vergonha. Leitura reparada publicada como principal, callback
tardio/writer, mescla de receipts e demais limites dos checkpoints anteriores
continuam sujeitos à validação específica. Durante esta tarefa, a worktree
recebeu candidato paralelo de writer/semântica vinculados à principal e seus
47 testes próprios passaram isoladamente; essa implementação foi preservada.
Não atribuir esse patch à comparação de violação nem declarar sua raiz encerrada
pelo verde focado. A publicação emocional ainda precisa verificar a restrição
vigente, além do ID: decisão/catalogação podem mudar na mesma ocorrência.
Nenhum commit ou push.

Regressão final desta continuação: **8.975 aprovados, 1 ignorado e 56 subtestes
aprovados em 201,73 s**, zero falhas/xfails. Os 65 arquivos Python modificados
ou novos tiveram hashes iguais antes/depois. Mutex real sob identidade própria
do pytest preservou a sessão aberta; `git diff --check` limpo, HEAD mantido.
Execuções anteriores coincidiram com mudanças paralelas no writer/testes:
três REDs de controle de publicação, depois um de conclusão técnica atrasada;
os controles passaram após a atualização paralela, preservada. Não usar essas
execuções de worktree em mudança como regressão atribuída à prova original.
O verde final inclui o candidato paralelo, sem fechar os limites do loop real.

#### Checkpoint P16 — prova original consumida como erro próprio — 30/09/2026

Continuação da mesma raiz/base `90a2fb8`, `main`, worktree paralela preservada.
A prova já chegava ao transporte; faltava consumir esse fato no produtor
emocional. Publicação do quadro e aplicação na conversa eram operações
separadas, sem revalidação da ocorrência/restrição. O produtor novo não usa
`ResultadoAcao`: uma proposta incompatível não é receipt ou falha do executor.

Contrato instalado: fonte/prova tipadas → reavaliação pelo mesmo filtro
canônico no estado vigente → evento de origem `contrato_proposta_principal`
→ quadro/plano/episódio publicados na mesma transação. A API compartilhada
prepara todos os domínios antes de atribuir qualquer um; recusa/falha não deixa
publicação parcial. Essa atomicidade vale para leitores/mutadores pelo lock
comum, sem certificar leitores legados diretos de dois atributos.

Evento `envergonhada 1/autorreparo`, TTL de 45 s, responsabilidade local Laylay
e referência estável sem texto privado/params. Pode interromper bronca
comprovada, preservando o humor de fundo. Origem reservada exige a projeção
integral da prova; o publicador genérico não a aceita. Consumo registrado no
plano evita renovar o episódio após replay, mesmo com histórico truncado.
Não há autorização, efeito externo ou preferência pessoal persistente.

A admissão única “Eu errei essa proposta.” é composta no finalizador, após
verificar a fala base/contingência. Conferência adicional exige evento ativo,
mesma prova/restrição/ocorrência e evento ainda publicado no quadro/plano/estado.
Isso protege expiração durante dispatcher/verificador e troca durante o
guardião. O prefixo não certifica reparo concluído nem promove uma fala falsa
de sucesso. LLM não abre chamada para essa avaliação. O catálogo vivo recupera
a capacidade e seus limites por perguntas naturais.

REDs precederam o candidato: 13 da ponte ausente, 17 da transação ausente,
três de origem genérica alterando emoção/humor e um do callback instalado
ausente. Revisão localizou perdas posteriores na composição da fala: um RED
do finalizador e dois de troca no guardião precederam o refinamento. Controles
falsificam culpa por alias, fonte insuficiente, frame estrangeiro, alteração
na mesma ID, parâmetro/alvo incerto, original correta e simples rejeição.

Produção desta continuação: produtor/estado emocional; owner de contexto;
transação de estado compartilhado; transporte/finalização da resposta;
catálogo e dois callbacks no composition root. Cada mudança pertence a uma
fronteira da mesma cadeia. Não cria parser de linguagem ou executor.

P16 continua parcial. Permanecem separação de leitura semântica original/reparo,
correlação de receipts por solicitação e validação contínua no loop desktop com
áudio/avatar físicos. Alterações paralelas de writer/receipts são preservadas
e devem conservar seus checkpoints próprios. Arbitragem sem contrato forte e
retrato sem catálogo delimitado continuam suspendendo atribuição de erro.
Este candidato não confirma a idade da emissão: ela é limitada pela ocorrência.
Nenhum commit, push ou desligamento nesta continuação.

GREEN desta fronteira: **616 testes focados/vizinhos + 16 da composição
instalada**. Composição usa início/preparador/validador/bridge/writer/guardião/
finalizador/orquestrador de fala reais, em playlist e IoT. Uma principal por
cenário; lista original incompatível é removida pelo filtro, sem chamada de
reparo adicional. Voz/texto únicos e projeção visual concordam com o episódio;
“Apaguei o arquivo.” sem receipt vira contingência. Fontes inválidas, replay,
mesma ID com restrição alterada e troca durante guardião suspendem a admissão.
Portas físicas/persistência isoladas; não valida áudio/dispositivo externos.

Regressão ampla estável: **9.084 aprovados, 16 falhas, um ignorado e 56 subtestes
aprovados em 199,05 s**. Todos os 76 Python modificados/novos conservaram hashes;
HEAD mantido, mutex de teste próprio e `git diff --check` limpo. As 16 falhas
estão em `test_mescla_receipts_solicitacao.py`, já não rastreado no início desta
continuação. Repetição isolada: 16 REDs e três controles GREEN. Doze atingem a
mescla por intent; um exige identidade de solicitação gerada pelo host após
validação. Três ainda param antes da publicação por usar chave de callback
`registrar_resultado_execucao` onde o adaptador real lê
`_registrar_resultado_execucao`; não certificam ainda o transporte do receipt.
Não são 16 raízes novas, nem GREEN global. Esse conjunto pertence à próxima
investigação de correlação, preservada com seu contrato e owner próprios;
não modificar expectativas para apagar os REDs nem atribuí-los ao produtor.

#### Checkpoint P16 — correlação por solicitação no contrato compartilhado — 30/09/2026

Continuação da pendência de correlação já registrada, base `90a2fb8`, `main`.
Worktree paralela preservada. Os 16 REDs históricos foram investigados por
fronteira: três sondas usavam a chave de callback errada; após corrigir somente
essa porta, a perda de ID até o receipt também foi reproduzida.

Cadeia demonstrada: proposta validada sem identidade do host → aliases do
dispatcher colocavam ID em params ou o descartavam → adaptador criava outra
identidade → writer mesclava ocorrências por intenção. O publicador de receipts
e o contexto de última ação ainda tinham formas da mesma herança indevida.
Controles falsificaram falha geral do executor e necessidade de descartar
receipts da própria ocorrência. A intenção repetida não identifica o pedido.

Contrato canônico instalado:

- `resultado_acao.py` cria uma cópia isolada e UUID do host depois do último
  validador. IDs e facetas de receipt propostas pelo modelo são removidos;
  payloads de domínio e identidades remotas no contexto permanecem isolados.
  Leitura de ID recusa coerção e aliases contraditórios.
- Dispatcher reutiliza o normalizador existente, transporta o ID no envelope
  canônico e remove aliases de identidade dos params. Coordenador e adaptador
  compartilham o mesmo owner. Cache por turno/intenção/params permanece intacto.
- `correlacao_solicitacao.py` é usado pelos dois publicadores do plano. Mescla
  somente ID explícito igual com intenção canônica compatível; preserva ordem
  e pedidos independentes. Sem ID não existe deduplicação por texto/intenção.
  Replay da proposta preserva a resolução observada; resultado novo substitui
  facetas operacionais, sem herdar confirmação/evidência de sucesso anterior.
- Contexto de última ação só completa receipt da mesma identidade/intenção.
  Novo status incerto e observação negativa não herdam confirmação anterior.
  A origem cronológica e o contrato publicado concordam.

REDs precederam cada candidato, incluindo conflito de ID/intenção, confirmação
incerta e cópia de params vivos contendo o lock do estado compartilhado. A cópia
reutiliza o mecanismo canônico desse estado. Alterações de fixtures mantiveram
as asserções operacionais: mesma ocorrência recebeu ID explícito; dispatcher
passou a exigir ID sem mudar intent/params; confirmações distintas passaram a
iniciar turnos reais distintos. O controle legado que exigia deduplicação por
intent foi substituído pela preservação de ambos os resultados, documentando a
mudança de contrato em vez de manter a expectativa vulnerável.

Composição instalada: sete controles GREEN, formatos flat/canônico, duas
solicitações APP_OPEN com alvos distintos, uma confirmação e uma falha.
Validador, runtime, dispatcher, adaptador, registrador, writer, finalizador e
leitor são os instalados pelo root; SQLite usa diretório temporário e portas
externas ficam isoladas. IDs chegam aos receipts e republicações preservam seus
próprios campos. Leitor recusa “Concluí tudo.” no resultado parcial. Replay em
memória do bloco histórico reproduziu a perda/transferência de receipt, sem
alterar produção. Não certifica abertura física, voz/avatar ou toda fala
adversarial do finalizador de erros.

Validação focada: 220 controles de identidade/contexto/continuidade/composição
e 100 regressivos dos três módulos alcançados pela regressão ampla passaram,
com sobreposição. Primeira ampla estável: **9.184 aprovados, três falhas, um
ignorado e 56 subtestes em 222,02 s**; 88 Python modificados/novos conservaram
hashes. As três falhas eram os contratos de fixture descritos acima; seus
módulos passaram após as mudanças. Ampla seguinte: **9.187 aprovados, um
ignorado e 56 subtestes em 213,62 s**, hashes iguais em 91 Python.

Revisão posterior encontrou uma recusa que não chegava ao chamador: publicador
retornava None ao rejeitar conflito e adaptador ignorava False explícito.
Quatro REDs confirmaram marcador/receipt de fala indevidos. Publicador agora
devolve False nas recusas/falhas e adaptador só certifica publicação aceita;
tentativa nova limpa marcadores anteriores. **177 focados/composição GREEN**.
Ampla final do refinamento: **9.190 aprovados, nenhuma falha, um ignorado e 56
subtestes em 214,32 s**. Os 91 Python modificados/novos conservaram hashes;
HEAD/branch mantidos, mutex de teste próprio e `git diff --check` limpo.
None permanece o sucesso legado do callback; a mudança não converte falha de
registro em falha física do efeito.

P16 permanece parcial: separar leitura semântica original/reparo e validar
loop desktop contínuo com áudio/avatar físicos. Inspeção e reprodução local já
mostram o preparador selecionando leitura do reparo com origem `llm_principal`;
isso é a próxima fronteira, ainda sem candidato ou prova na composição.
Arbitragem/parametrização de alvos continuam com seus owners, sem tratar ID
como autorização ou igualdade literal entre alvo proposto e alvo resolvido.
Nenhum commit, push ou desligamento nesta continuação.

#### Checkpoint P16 — leitura original antes da publicação semântica — 30/09/2026

Continuação da perda de procedência já registrada, sem nova raiz por frase.
Base `main`, `90a2fb8698541119f523c0a22fa4de0187cbaf92`, worktree paralela
preservada. Para “antes eu estava triste, mas agora estou aliviado”, a emissão
original conservava ausência de emoção; um reparo podia propor tristeza com
trecho histórico. A primeira divergência estava no preparador: preferia a
leitura reparada e o extrator a rotulava como `llm_principal`. O publicador
conferia a ocorrência, sem conferir a correspondência com a emissão capturada.

Falsificado: o normalizador não inventava tristeza na leitura original;
ausência de autorização também não causava a substituição. O mesmo frame e
um trecho presente na fala não provam a origem ou a interpretação temporal.
Onze REDs alcançaram preparo/publicação/transporte antes do candidato. Uma
fixture inicial de fala curta ativou contingência posterior; esse resultado
não foi contado como RED de procedência. O controle passou a usar uma fala
aceita pelo contrato, conservando as expectativas sobre origem. A revisão
reproduziu mais um RED: a API legada publicava diagnóstico como principal.

Contrato: `leitura_semantica` conserva a leitura original, inclusive ausência.
`leitura_semantica_reparada` contém somente o diagnóstico disponível no bruto
final transformado, com origem host `resposta_reparada`. Não é histórico de
todas as chamadas de reparo. O runtime reextrai do `ContratoPropostaPrincipal`
capturado; o publicador compara a leitura recebida e publica sua própria cópia
derivada, mantendo a conferência da ocorrência e CAS. Mappings fornecidas,
metadados do modelo e mutações de subdicts não substituem a fonte. Publicador
legado e produtor causal recusam a origem reparada. Rotas legadas não passam
a certificar a mesma procedência forte da API vinculada.

Produção desta fronteira: preparador, contrato de resposta, runtime da resposta,
publicador semântico e produtor causal. Reutiliza o extrator/normalizador
existentes; não cria interpretação paralela nem chamada adicional ao modelo.
Preserva a escolha de uma chamada principal e ausência de evento para leitura
incerta. Não promove reparo conversacional a prova de erro próprio, autoridade
ou receipt. Evidência direta anterior, TTL e guards de autoria continuam sob
seus owners.

GREEN: **270 testes focados/vizinhos, incluindo 10 da composição instalada**.
Principal ausente/nenhum/alívio, reparo divergente, ausência de reparo, falha
técnica, texto diferente, metadados forjados, mutação após conferência e
ocorrência substituída estão cobertos. Dois módulos de fixtures antigas agora
representam o campo wire real `leitura_turno`, preservando as asserções de
autoridade, publicação, transação e CAS. O runtime/preparador/publicador são os
instalados por `laylay.py`; transporte, retorno do reparo, persistência e portas
externas são isolados. A resposta continua e o evento direto anterior permanece.
Isso não prova qualidade semântica geral nem áudio/avatar físicos.

Regressão ampla estável: **9.221 aprovados, nenhuma falha, um ignorado e 56
subtestes aprovados em 208,94 s**. Os **94 Python modificados/novos** conservaram
hashes; HEAD/branch mantidos, mutex próprio de teste e `git diff --check` limpo.
Não encerrar a P16 pelo GREEN intermediário. Próxima fronteira separada:
validação contínua no loop desktop, incluindo falha/recuperação e projeções de
voz/avatar até os efeitos físicos. Inspeção atual encontrou somente os processos
Python do pytest, sem sessão Laylay ativa. O roteiro P16 existente silencia voz;
flags de reprodução e envio UDP ao avatar não confirmam som/quadro físicos.
Preservar essa distinção na próxima prova. Nenhum commit, push ou desligamento
nesta continuação.

#### Checkpoint P16 — receipt observado antes da apresentação — 30/09/2026

Base mantida: `main`, `90a2fb8698541119f523c0a22fa4de0187cbaf92`;
worktree paralela preservada. A prova com lock Windows real confirmou dois
receipts de falha e uma escrita posterior, mas o primeiro candidato conservava
calma nos três turnos. Primeira divergência: a avaliação operacional dependia
de `falar_por_status`; arquivos usam uma porta de fala própria. TTL expirado,
vulnerabilidade e ausência do callback instalado foram falsificados. Replay
diagnóstico dos mesmos receipts produziu irritação/recuperação, sem publicar
eventos ou atribuir efeito externo ao replay.

Owner: `autonomia/adaptador_resultado.py`. A publicação aceita pelo registrador
canônico observa o receipt por uma cópia isolada, antes da apresentação. A
fala reutiliza somente a avaliação privada dessa publicação, conferindo sua
identidade e resultado; não reavalia histórico ao falar novamente. Recusa,
exceção ou ausência do registrador não observam evento; falha do observador
não inventa avaliação. Contexto externo não fornece `avaliacao_evento` pronta.
O contrato beneficia os domínios que usam esse adaptador, sem parser emocional
por habilidade. Não garante deduplicação global de republicações por instâncias
distintas. Dez REDs locais precederam o candidato; controles cobrem rejeição,
mutação aninhada, fala repetida e falha do observador. Composição usa os
registradores/observadores instalados por `laylay.py`, com estímulos sintéticos
explicitamente separados dos efeitos reais.

Prova real preservada em
`resultados_testes/p16_falha_recuperacao_823da9ac0af7457a827625a1455d5784/`:
três turnos respondidos, processamento/resultado/voz concluídos;
`calma 1 → irritada 1 → acalmando-se 1`. Dois receipts `falha_execucao`,
seguidos de `conteudo_atualizado`, possuem IDs distintos e alvo exato. Lock
liberado somente depois das duas falhas finalizadas; hash permaneceu igual
durante o lock e o arquivo foi relido com `P16 RECUPERADA` após a escrita.
Pedro confirmou ouvir completas as três respostas. Captura real mostrou
avatar irritado falando no segundo turno; não certifica todos os quadros ou
a recuperação visual contínua. Mapeamento de assets confirma fallback para
`acalmando-se`; intensidade visual continua em P19.

O processo principal saiu com **3221226525 (`0xc000041d`)** depois de relatório,
retorno de `main` e callback da sentinela em `atexit`. Essa marca não prova a
conclusão dos demais callbacks. Eventos Windows registram antes `0xc0000005` no
mesmo PID; WER não identifica o componente causal. Não declarar loop inteiro
GREEN. A sonda preserva agora evidências operacionais antes de conferir a
saída; mantém a exigência de código zero. O artefato histórico não foi reescrito.
Associar o achado à investigação aberta de encerramento/infraestrutura do mapa;
sem alegar mesma causa do código 1 de 21/09. O diagnóstico `0x8001010d` do
cliente Terminal também aparece em execução que termina com código zero;
sua presença isolada não prova causa da falha principal nem morte do cliente.

#### Caminhos absolutos e conteúdo literal — pedido adicional de Pedro, 30/09/2026

Raiz demonstrada de identidade: normalização de argumentos e resolução por
basename/antecedente podiam perder ou substituir o caminho explícito. O serviço
de arquivos já aceita caminhos absolutos com espaços e aspas pareadas;
permissão de escrita do sistema e indisponibilidade geral do executor foram
falsificadas como causa de interpretação. REDs locais e seis da composição
precederam o candidato. Caminho explícito conserva identidade antes da
continuidade; classificador canônico continua dono da autorização, e executor
valida raízes, existência, formato e resultado. Mencionar caminho, perguntar
capacidade, negar ou formular hipótese não cria efeito.

Produção dessa fronteira: `arquivos/nome_natural.py`, `contexto_execucao.py`,
`roteador_arquivos.py`, gate de argumentos do coordenador e entrada/resposta
do catálogo vivo. Sem novo executor ou chamada ao modelo. Leitura/abertura
resolvem o caminho fornecido; escrita e append aceitam “no arquivo”. Exclusão
continua exigindo confirmação. A gramática geral de “move/mova” e renomeação
não foi ampliada: sua classificação já falhava também sem caminho absoluto,
portanto não pertence à raiz de identidade.

A primeira prova de sete turnos localizou uma causa adicional: “linha” era
retirada como moldura de conteúdo. Seis REDs mostram que isso também ocorria
**entre aspas**, em caminho, basename, pronome e elipse, antes do executor.
Owner único de conteúdo no roteador conserva o literal citado e mantém a
moldura natural sem aspas. A prova usa `Acrescente "LINHA ADICIONAL" ...`,
mantendo a expectativa de conteúdo integral, sem enfraquecer o teste.

Provas reais de sete turnos, código zero e conteúdo físico conferido:
`resultados_testes/caminhos_absolutos_53a53d3eb5aa4d70ae45158b10455070/` e
`resultados_testes/caminhos_absolutos_c8bcf0ca678047ea81f5d77463280625/`.
Dois `prova.txt` em pastas distintas, uma com espaços, não foram confundidos;
controle intacto, escrita/append exatos, leitura inexistente falhou sem usar
outro arquivo. Voz silenciada: essas provas são de arquivos e finalização.

Uma repetição anterior (`caminhos_absolutos_55ee643598eb41f6a2881bd90f87db98`)
escreveu fisicamente, mas perdeu ID/receipts do plano antes da conclusão do
terceiro turno. Preservada RED, sem ampliar timeout ou aceitar plano vazio.
Alterações concorrentes de produção e falha inevitável do mesmo roteiro foram
falsificadas; duas repetições com diagnóstico passaram, sem reproduzir o writer
responsável. Não atribuir a perda ao parser literal ou ao Terminal sem cadeia
causal. Continua pendente rastrear a primeira substituição de estado.

Seleção final dos contratos, composição, catálogo e adaptador: **146 aprovados**.
Regressão ampla desta continuação: **9.303 aprovados, nenhuma falha, um ignorado
e 56 subtestes aprovados em 230,14 s**. Os **105 Python modificados/novos**
conservaram hashes durante a suíte; HEAD/branch mantidos e diff sem erros.
P16 permanece parcial: origem própria positiva no loop, repetição com foco
estável, projeções físicas contínuas e as pendências de estado/encerramento
mantêm suas provas separadas. Nenhum commit, push ou desligamento.

#### Checkpoint P16 — captura no encerramento e controle instrumentado — 01/10/2026

Base `main`, `90a2fb8698541119f523c0a22fa4de0187cbaf92`, worktree preservada.
Continuação de duas investigações abertas, sem atribuir causa comum à perda
do plano e à falha nativa de saída.

**Perda do plano, causa ainda aberta:** a sonda de caminhos possui opção
`--diagnosticar-plano`, que observa as APIs compartilhadas `substituir`,
`atualizar_dominios` e `mesclar_campos` pelo mesmo lock. Registra IDs, fase,
receipts resumidos, sessão, thread e pilha do publicador em arquivo próprio;
não reconstrói estado nem fornece eventos/receipts. O controle de 30/09 em
`resultados_testes/caminhos_absolutos_dd30046da88a4c3baee8f3bd22754f06/`
passou sete turnos, conteúdo físico e código zero. Suas 25 publicações não
mostraram perda de identidade/receipts. A instrumentação pode alterar timing
e não cobre mutações diretas fora dessas APIs: não encerra o RED histórico
`caminhos_absolutos_55ee643598eb41f6a2881bd90f87db98`. Renovação/troca de
sessão e writer incompleto continuam hipóteses, sem patch especulativo.

**Lacuna demonstrada na captura:** a sentinela era registrada depois de outros
callbacks e desativava `faulthandler` ao concluir o próprio callback. Como
`atexit` usa ordem inversa, callbacks ainda pendentes ficavam sem caixa preta.
Dois REDs em processos filhos descartáveis confirmaram a primeira fronteira:
handler inicialmente ativo, depois inativo; falha nativa deliberada no callback
posterior deixava vazio o arquivo nativo. A falha induzida pertence ao controle,
não é reprodução da causa nativa da Laylay.

Owner compartilhado `integracao/diagnostico_encerramento.py` mantém handler e
descritor nativo disponíveis para os demais callbacks; o SO libera o descritor
ao sair. `atexit_concluido` informa `alcance=callback_sentinela`. Desregistro
explícito de teste continua desativando e liberando o recurso de forma
idempotente. Controles de flag desativada, captura tardia e liberação passaram;
diagnóstico/visual/barra: **29 aprovados**. A cobertura não promete captura
depois da finalização interna do handler pelo interpretador. Não modifica o
lifecycle das habilidades nem demonstra a causa de `0xc000041d`.

**Controle real de 30/09 com saída limpa:**
`resultados_testes/p16_falha_recuperacao_bd12a6f56cea42558b1d11cc2e7d77fb/`
confirmou duas falhas reais sob lock sem alteração de hash, liberação após as
barreiras, escrita física exata e três receipts com IDs distintos. Estado
`calma 1 → irritada 1 → acalmando-se 1`, vinculado aos receipts do turno;
processamento/resultado/fila de voz concluídos e processo principal com código
zero. Voz/avatar estavam habilitados; este controle não acrescenta observação
humana de áudio ou sequência visual. A confirmação humana anterior permanece
válida para o loop anterior. Arquivo nativo vazio porque a falha de saída não
reapareceu; esse GREEN não demonstra que o candidato corrigiu a falha nativa.

Regressão ampla desta fronteira: **9.307 aprovados, nenhuma falha, um ignorado
e 56 subtestes aprovados em 231,23 s**. Os **107 Python modificados/novos**
mantiveram hashes durante a suíte; HEAD/branch mantidos e diff sem erros.
Produção deste candidato limitada ao owner de diagnóstico; análise optativa,
regressivos e documentos completam a entrega. Nenhum commit/push/desligamento.

P16 permanece parcial: origem própria positiva em geração principal nova,
repetição com foco estável, sequência física contínua e identificação dos
writers/componentes dos REDs intermitentes. Próxima fronteira de estado: obter
a primeira publicação divergente com sua pilha, mantendo as barreiras atuais.

#### Checkpoint P16 — localizar a troca de contexto antes da perda do plano — 01/10/2026

Base `main`, `90a2fb8`, worktree preservada. Continuação do RED histórico
`caminhos_absolutos_55ee643598eb41f6a2881bd90f87db98`, sem raiz nova por sintoma.
O plano parcial tem `atualizado_ts=1790819011.5594287` (30/09, 22:43:31.559),
aproximadamente quatro segundos após o terceiro envio e 41 segundos antes do
timeout. O arquivo próprio preservado contém `CONTEÚDO NOVO`. O timeout não
criou esse plano; sua forma coincide com `atualizar_plano_turno({})` após um
quadro vazio. O caminho legado aceita o trio todo vazio e explica essa segunda
transição, mas ainda não identifica quem limpou o quadro inicialmente.

**Hipótese de troca/restauração contextual, agora sustentada por metadados:**
consulta SQLite exclusivamente `mode=ro`, limitada a dois IDs, mostrou o chat
próprio `c19210ad-fe27-4d8f-9e89-3e4901507742` criado às 22:43:25.200 e salvo
pela última vez às 22:43:27.933, com dois pares de mensagens e emoção `calma 1`.
O chat antigo `f1dafa7f-5aed-4169-a687-1201b9ebb617`, criado às 22:33:45.417,
foi salvo às 22:44:13.810, durante o encerramento do RED; preservava entrada
anterior (`ultima_entrada_ts=1790818613.477047`) e `acalmando-se 1`, coincidente
com a projeção emocional do parcial. Não foi consultado texto pessoal.
Isso sustenta restauração de outro contexto; não prova o pedido de seleção,
seu autor ou a ausência de outro processo escrevendo no mesmo SQLite.

Concorrentes falsificados por código/composição/tempos: boot tardio do roteiro
(memória/sessão iniciais são síncronas e antecedem sua entrada), inatividade
de 600 s (intervalos de aproximadamente 1 s), registro local reaplicando chat
(só altera mensagens/persistência) e renderização da lista selecionando chat
automaticamente (`setChecked` antecede conexão somente de `clicked`). Nenhum
writer direto do trio foi encontrado; vínculos/normalização conhecidos não
limpam o plano. A auditoria estática não prova ausência de todos os writers.

**Diagnóstico optativo ampliado, sem candidato em produção:** a sonda registra
entrada/retorno/exceção de `selecionar`, `criar`, `reaplicar_ativa` e
`iniciar_sem_conversa` no owner real, com IDs anterior/solicitado/resultante,
estado resumido, PID/thread e pilha. Não registra título ou mensagens. Continua
observando as três APIs de estado. Falha ao gravar o arquivo diagnóstico não
interrompe a operação observada. Dois REDs do diagnóstico precederam a mudança:
seleção sem chamador registrado e erro de gravação interrompendo o owner.
Controle de limpeza já estava GREEN. Testes usam gerenciador/estado/SQLite reais
em filhos e diretórios temporários, incluindo seleção do mesmo chat e seleção
recusada, sem chamar LLM ou atribuir efeito externo a esse controle.

Validação: **29 controles novos/vizinhos aprovados**. Dois loops de sete turnos
com alvos/conteúdo físico e código zero:
`resultados_testes/caminhos_absolutos_ef9eacee3395481bbfe636c196b0e4ec/`
(diagnóstico anterior) e
`resultados_testes/caminhos_absolutos_cdbf0154dfa8465588ec25c416a6ec2a/`
(diagnóstico ampliado). O último registrou 25 publicações de estado e seis
registros de conversa (entrada/retorno de três chamadas); nenhuma seleção
de outro chat durante os turnos, nenhuma perda de plano. Voz silenciada;
instrumentação pode alterar timing. Não reproduziu a falha histórica.

Produção manteve os hashes desta continuação. Dos 107 Python iniciais, somente
a sonda mudou; acrescentado um módulo de regressão, total 108. Última ampla de
produção permanece a anterior, **9.307 aprovados/um ignorado/56 subtestes**;
não foi repetida nesta entrega de diagnóstico. HEAD/branch e diff preservados.
P16 parcial. Próxima fronteira deste RED: capturar o pedido/callback que troca
o chat no intervalo entre efeito e finalização, sem restaurar quadro antigo
ou tratar identidade ausente como autorização. Falha nativa, origem própria
positiva e sequência física com foco estável continuam investigações separadas.

#### Checkpoint P16 — conclusão local vinculada à ocorrência — 01/10/2026

Base `main`/`90a2fb8`, worktree paralela preservada. Continuação do RED
`caminhos_absolutos_55ee643598eb41f6a2881bd90f87db98`: o autor da troca histórica
permanece desconhecido. A **segunda transição** agora foi reproduzida de forma
controlada: resposta local de A aceita, seleção legítima de B pela ponte real,
retorno ao produtor de A, publicação de fase no quadro de B. B vazio recebia
os seis campos do parcial histórico; B com novo turno coerente recebia a fase
`tratado_prioritario` de A. Duas perguntas de capacidade (arquivos/música),
gerenciador/SQLite/saída/histórico/composição/TCP reais: **quatro REDs causais e
cinco controles GREEN antes do candidato**. Esses controles não executam efeitos
externos e não identificam o autor da seleção histórica.

Contrato geral: **conclusão pertence à ocorrência capturada pelo produtor**.
`ContratoOcorrenciaTurno` conserva ID/texto original, é imutável e não confere
autorização, emissão LLM ou efeito. O runtime captura antes das rotas locais;
`ComposicaoTurnoRuntime.atualizar_ocorrencia` confere o vínculo dentro da
transação do owner do plano. Comparação de seis identidades/texto original
compartilhada com a proposta principal, mantendo a revisão operacional separada.
Recusa não cai no writer legado nem reconstrói plano: publica diagnóstico
`conclusao_local_obsoleta`. Histórico confirmado continua no chat de origem.
Compatibilidade sem callback moderno permanece explícita.

Produção desta continuação: contrato/comparador/orquestrador/composição do turno,
runtime de resposta e uma conexão em `laylay.py`; nenhuma regra por habilidade.
Controles das quatro rotas locais (modo chat, prioritário, pré-fluxo, social),
troca no commit, origem ausente/malformada, mesmo ID/texto diferente, revisão,
receipts preservados e callback com retorno malformado: **174 focados/vizinhos
aprovados**. Dois controles novos inicialmente comparavam dados crus com a
normalização canônica (pendência vazia/receipt enriquecido); passaram a comparar
snapshots normalizados. Nenhuma guarda de produção foi removida para isso.

Prova no **main real**, voz silenciada, SQLite/arquivos próprios:
`resultados_testes/caminhos_absolutos_a282c7ef92844623a86f67c6a1c1fb39/`.
Receipt de escrita `ed6210b77ff846a2983fa21a148e4a7a`, ID do plano
`1790868420642225000`, texto aceito antes da troca. A ponte confirma B; a fase
tardia é recusada, B permanece sem plano nesse intervalo. Sete comandos,
sete receipts distintos, conteúdo físico relido e saída zero. Consulta somente
leitura ao SQLite próprio confirmou três pares em A e quatro em B. A GUI não é
lançada nesse controle: o cliente TCP ocupa o único atendimento da ponte.

Os ensaios `74e52989...`, `ee73b63e...` e `f897b85d...` não selecionaram B: a GUI
já ocupava o atendimento síncrono, e o segundo socket aguardava no backlog até
timeout. Sem patch na ponte; artefatos RED preservados. `f809e45f...` selecionou
e recusou corretamente, mas a sonda esperava interrupção do roteiro. Premissa
falsificada: o roteiro conserva o snapshot identificado/receipt capturado na
saída de A e exige o fim do worker. A expectativa foi corrigida na sonda; suas
barreiras canônicas não foram alteradas. O controle final exige os mesmos sete
alvos/statuses/IDs/conteúdos, mais a correlação do receipt de A com troca/recusa.

Controle normal com GUI, sem seleção provocada:
`resultados_testes/caminhos_absolutos_9c2264d64d514e7f9804864545c5c0fa/`.
Sete turnos/receipts/conteúdo/código zero, 25 publicações de estado, nenhuma
seleção durante os turnos. Voz silenciada; não comprova áudio/foco/avatar.
Regressão ampla: **9.343 passed, 1 skipped, 56 subtests passed** em 252,93 s.
Log `.pytest_cache/p16_conclusao_local_ampla_conferida.log`; auditoria persistida
em `.pytest_cache/p16_conclusao_local_ampla_hashes.json`: código zero, hashes dos
109 arquivos Python acompanhados iguais antes/depois, nenhuma alteração pela
suíte. A primeira execução também passou (225,73 s), mas esta segunda execução
é a referência da conferência de hashes. `git diff --check` limpo.

Limites: esta correção protege publicação tardia depois da captura. Não prova
quem trocou o chat histórico, atomicidade início→captura, nem troca durante
receipt/voz. A P16 permanece parcial: autoria histórica, crash nativo, erro
próprio positivo de geração nova e sequência física com foco estável continuam
pendências separadas. Nenhum commit/push; encerramento do computador não pedido.

#### Checkpoint P16 — coleta da principal nova com fonte técnica insuficiente — 01/10/2026

Base `main`/`90a2fb8`. Próxima prova de erro próprio: resposta nova do modelo
principal → original preservada → violação demonstrada pelo owner do turno →
publicação revalidada → confirmação após guardião → admissão na fala entregue.
Original sem comandos é controle negativo legítimo, não erro da Laylay.

Nesta etapa só mudou `scripts/roteiros/sonda_transporte_evidencia.py`:
`--capturar-p16`, restrito ao roteiro IoT existente, sem replay/falha injetada.
Observa registro do modelo, HTTP, validador original, publicador/confirmador,
dispatcher, executor IoT e finalização; delega os mesmos objetos/retornos.
Captura ID da chamada para ligar HTTP à fonte. O registro diferido delega a
outro registro; ambos são contados como uma chamada externa. SQLite próprio;
TXT de resumo continua seguindo o caminho normal da aplicação. Voz/avatar
desativados, IoT simulado, controle físico não autorizado. Não é prova física.

Coletas reais, ambas com código zero e oito turnos concluídos:

- `resultados_testes/transporte_evidencia-20261001-195336-817698/`:
  três principais HTTP expiraram em 7 s; fontes seguintes bloqueadas pelo
  circuito. Pré-aquecimento HTTP de um token terminou em 25,30 s; Ollama
  carregou em 21,15 s, depois das tentativas iniciais.
- `resultados_testes/transporte_evidencia-20261001-195555-791829/`:
  modelo já carregado, pré-aquecimento de um token em 1,13 s. Principais
  expiraram em 5/7/7 s; cinco turnos seguintes sem transporte pelo circuito.
  Logo, carregamento inicial sozinho não explica a insuficiência.

Nas duas coletas, oito validações com `estado=falha_tecnica`, nenhum comando
no dispatcher, nenhuma entrada do executor IoT, publicação/admissão de erro
próprio ausentes. Nove chamadas externas observadas por coleta incluem um
pedido de resumo diário, sem validação do turno; não são nove gerações válidas.
`coleta_p16.json` e `prova_p16.json` mantêm **fonte técnica insuficiente**.
O placar mínimo do roteiro (8/8) não prova geração válida nem conclui a P16.
Os arquivos de captura bruta foram preservados por hash ao gerar o resumo.

Evidência de recursos: Ollama carregou **0/37 camadas na GPU**. Após a segunda
coleta, GTX 1660 SUPER de 6 GB estava com 5.777–5.781 MiB ocupados, cerca de
190 MiB livres e 96% de uso; Forza em execução. WDDM não informa consumo por
PID nessa consulta: não atribuir todo o consumo ao jogo. Restrição de recursos
é hipótese sustentada; não é raiz semântica demonstrada. Nenhum processo
existente foi encerrado, modelo/tokens/timeouts/circuito não foram alterados.

Verificação da sonda: compilação, rejeição de flag P16 em roteiro incompatível,
duas execuções reais e resumo aplicado às capturas sem modificá-las. Os 109
hashes Python da ampla anterior seguem intactos; a sonda era arquivo limpo e
é a única alteração Python adicional desta etapa. A ampla de 9.343 testes
precede esta instrumentação, não valida a nova prova positiva ausente.

Próxima fronteira: conseguir uma principal real bem-sucedida dentro do orçamento
normal em condições de recursos disponíveis, conferir bruto HTTP/original/ID
e só então aferir o positivo. Nenhum evento, comando ou resposta falsa deve ser
injetado para fechar a fase. P16 permanece parcial, com as pendências anteriores.

#### Checkpoint P16 — fontes novas e controles negativos reais — 01/10/2026

Coleta `resultados_testes/transporte_evidencia-20261001-201034-289090/`, base
`main`/`90a2fb8`. GPU liberou cerca de 4,9 GiB; modelo CPU expirou naturalmente.
Nova inicialização pelo root/roteiro normal, sem encerramento de processo alheio,
troca de modelo ou alteração de tokens/orçamento. Backend observado Qwen:
3.178.149.969 bytes de modelo e de VRAM; `backend_observado.json` local.

Oito fontes principais novas, sucesso e HTTP200 correlacionados pelo ID da
chamada; bruto HTTP = retorno do registro = principal = extração original.
Frames/ocorrências correspondem ao ID atual. Seis respostas sem campo comandos,
duas com lista vazia; nenhum candidato operacional/violação. Oito dispatchers
vazios, nenhum receipt/entrada IoT/publicação de erro/admissão. Oito turnos,
código zero. `prova_p16.json`: **GREEN dos controles negativos**, positivo próprio
**não comprovado**. Ausência de culpa é comportamento correto neste controle.

Contagem: oito principais + um reparo de comunicação já existente + um resumo
diário bloqueado antes do HTTP = dez registros externos. HTTP: pré-aquecimento,
oito principais e reparo. Reparo não substitui a fonte original; não foi adicionado
interpretador emocional. Voz/avatar silenciados, IoT simulado; sem prova física.

Isolamento da sonda: além do SQLite, `MemoriaLaylay.__init__` recebe diretório
`resumo_proprio` pelo observador e conserva callbacks/clock/serviço reais.
Controle em diretórios descartáveis reproduziu RED na primeira asserção de
destino antes do candidato; GREEN confirmou arquivo pessoal anterior preservado,
gravação própria e SQLite real. Coleta real confirma TXT próprio e hash pessoal
inalterado. Os dois artefatos anteriores continuam registrando a lacuna original.
`scripts/tests/test_sonda_transporte_p16.py` também protege fonte técnica e
observação vazia contra promoção a prova positiva.

Raiz separada encontrada na coleta anterior: `MemoriaLaylay.atualizar_resumo_diario`
aceitava sentinelas como resumo e consumia lote. Onze REDs/8 controles antes do
candidato; somente esse arquivo de produção agora usa `eh_estado_tecnico_llm`
compartilhado antes de qualquer consumo, mantendo a proteção antiga. **34 focados
GREEN**. No main desta coleta, resumo bloqueado por `principal_duplicada` foi
adiado, oito pendentes preservados no TXT próprio, nenhum token técnico
consolidado. TXT pessoal anterior preservado por hash; não recupera nem limpa
dados históricos. Tipo de chamada e geração real de consolidação são limites
separados. Evidência da raiz/owner/falsificações no registro e mapa causal.

Regressão ampla dessa etapa: **9.359 passed, 1 skipped, 56 subtests passed** em
226,04 s, código zero; `.pytest_cache/resumo_diario_ampla.log` e auditoria
persistida `.pytest_cache/resumo_diario_ampla_hashes.json`. Os 113 arquivos Python
acompanhados mantiveram hashes iguais durante a suíte; `git diff --check` limpo.
P16 continua parcial. A principal nova agora foi observada, mas nenhum erro próprio
original ocorreu neste controle. Próxima prova positiva exige uma ocorrência
nova realmente incompatível, bloqueada pelo owner, com evento/admissão correlatos.
Não promover exemplos, replay, ambiguidade ou retorno técnico a culpa. Foco,
voz/avatar físicos, autoria da troca histórica e crash nativo continuam separados.

#### Checkpoint P16 — vetos naturais e troca de referente — 01/10/2026

Coleta única `resultados_testes/transporte_evidencia-20261001-202847-916595/`,
base `main`/`90a2fb8`, pelo main e modelo reais. Seis entradas de recusa:
duas simples, duas com ações/dispositivos distintos e duas com troca de referente.
Classificador/planejador reais confirmaram veto e ausência de autorização antes
da coleta. Nenhum pedido de exemplo/JSON, replay, comando/evento/falha injetados
ou alteração do modelo/orçamento. Roteiro dedicado e whitelist da sonda;
produção não recebeu candidato nesta etapa.

**Cinco principais novas HTTP200/sucesso**, bruto HTTP = registro = principal =
extração, seis IDs correspondentes. Todas as decisões: autorização falsa, veto
verdadeiro, execução requerida falsa, ação permitida falsa, owner `conversa`,
origem `classificador_turno`. Cinco listas originais explicitamente vazias,
validadores e dispatchers vazios; zero violação/evento/admissão/entrada IoT.
Auditoria independente confirmou a cadeia. `prova_p16.json`: controle negativo
GREEN, positivo próprio **não comprovado**; não repetir até induzir culpa.

Seis turnos respondidos/código zero. Sexto foi consumido por reparação local,
sem principal; o sexto registro do modelo é resumo diário bloqueado antes do
HTTP, sem consumo do lote. O placar mínimo 6/6 não certifica seis fontes nem
fidelidade da fala. O quinto original alegou estado sem leitura; o guardião
retirou a alegação na resposta entregue. Sexto entregou referente inadequado:
“ligue nem desligue nenhum dispositivo”. Observação de fala/referente separada,
raiz ainda não diagnosticada; não conta como culpa operacional da P16.

SQLite/resumo próprios e hash do TXT pessoal anterior intacto. Voz/avatar
desativados, IoT simulado. Tentativa anterior `202759-703726` não carregou:
expectativas em compreensão de dicionário, incompatível com loader literal.
Roteiro corrigido, teste com loader real protege a fronteira. Controle de
classificação protege os seis vetos. Evidência física segue separada.

#### Checkpoint P16 — sequência integral, foco, voz e avatar reais — 01/10/2026

Main real `resultados_testes/transporte_evidencia-20261001-203531-829003/`,
base `main`/`90a2fb8`. Roteiro de 16 turnos existente, sem enfraquecer esperas
por execução/voz ou trocar expectations. Sonda apenas ampliou whitelist e
habilitou mascote/avatar no ambiente desta sessão; SQLite e resumo próprios.
Preferências do avatar, buffers neurais e arquivos de aprendizado permanecem
nos caminhos normais: não declarar isolamento total.

**16 turnos concluídos**, dez receipts confirmados/distintos: abertura inicial,
duas maximizações e sete `ja_aberto_focado` idempotentes. Nos sete, `executou=False`
e `episodio_evidencia_ref` corresponde ao receipt corrente. Foco vem da releitura
do executor, não da captura. Sequência comprovada no plano bruto: debochada 1/2,
irritada 2, brava 3; continuidade na conversa; conquista/vulnerabilidade limpam
o episódio, desculpa atenua para brava 2 preservando sua causa; redundância nova
renova brava 3; assunto novo termina em calma 1. Todos os campos esperados foram
conferidos. **10 passaram, seis alertas de latência, zero falhas**; p95 23,888 s.
Não converter alertas em seis bugs nem certificar qualidade textual global.

Voz habilitada: 16 `voz_observada/voz_concluida=True`, não silenciada. Confirmação
humana do som físico desta execução **pendente**; confirmações antigas não valem
para esta coleta. `computer-use`/`@oai/sky` capturou a Calculadora sem ativação
ou input. Avatar sobreposto visível; capturas pontuais arquivadas em `visual/`:
aparência calma com plano publicado 12, expressão de bronca/aro com plano 14
brava 3 e receipt `78e1ac55...`. JSONs registram intervalo/contexto antes/depois;
não certificam toda a animação, intensidade/prosódia ou sincronização contínua.
Captura inicial e outra sem correlação exata não qualificam um turno específico.

Auditoria independente identificou arredondamento de IDs numéricos longos pelo
`Number` do JavaScript nos JSONs visuais. Originais preservados; adendo
`visual/correlacao_visual_precisa.json` lê IDs exatos como strings da fonte
Python, com correspondência única por índice/horário/estado. Não recupera um ID
lido do renderer nem certifica igualdade exata que a captura não preservou.
Turno 15 só exige ausência de comando: estado publicado permanece brava 3.
A principal original reconheceu alívio 1; `calma 1` é sua proposta de expressão,
não uma leitura lexical de alívio. O evento do plano ficou lexical/vulnerável,
gerado pelo `triste` passado. A continuidade abaixo investiga essa atribuição;
reconhecer alívio do usuário não deve copiar esse estado para a Laylay.

Contagem real: 44 registros externos; 27 gerações HTTP ligadas ao registro
(seis principais, dez autorias operacionais, nove reparos factuais, dois reparos
de comunicação), mais um pré-aquecimento = 28 HTTP200. Treze retornos locais
`intent=NONE`, três reparos bloqueados pelo limite e um resumo por principal
duplicada não iniciaram HTTP. Caminhos/reparos já existentes; nenhum interpretador
emocional adicionado. Não declarar uma principal por cada resposta operacional.
No turno 10 houve autodefinição inadequada como chatbot; no 12 contingência
contextual após reparo indisponível. Observações de fidelidade separadas, sem
atribuir culpa operacional ou corrigir produção sem diagnóstico.

Processo código zero, marker `main_retorno/atexit_concluido`, log nativo vazio;
isso não encerra o crash histórico. 114 Python acompanhados com hashes iguais
durante a execução; TXT pessoal anterior preservado. **99 regressivos focados
GREEN** (9,44 s) de sonda, loader/roteiro, organização e encerramento;
`git diff --check` limpo. A ampla anterior de 9.359 precede esta extensão de
diagnóstico; não foi repetida. `prova_voz_avatar.json` separa cada nível de prova.
P16 parcial: positivo próprio fresco, som físico/continuidade visual integral,
autoria da troca histórica e causa do crash ainda têm lacunas explícitas.

#### Checkpoint P16 — sinal emocional vinculado ao predicado pessoal — 01/10/2026

Base congelada `main`/`90a2fb8698541119f523c0a22fa4de0187cbaf92`, worktree
preservada em `baseline_investigacao.json` da coleta abaixo. Raiz demonstrada:
`analisar_intencao_emocional` procurava marcador pessoal e emoção separadamente
em toda a fala. Em `antes eu estava triste, mas agora estou aliviado`, emprestava
`estou` da segunda oração ao `triste` passado. Publicava vulnerabilidade lexical
antes da principal; a proteção legítima de evidência direta conservava esse
evento, apesar da leitura original de alívio. O plano histórico 1790897998476775600
registra essa cadeia em `203531-829003`; não era falha de transporte da principal.

Falsificados: ausência de leitura original (JSON válido/alívio 1/0,99), substituição
pelo reparo (fonte original capturada antes do preparador) e a premissa de que
`calma 1` proposta pelo modelo deveria limpar a bronca. Leitura do usuário tem
`permite_expressao=False`: não é emoção própria nem autorização operacional.
Não remover a precedência do elogio/relato direto para compensar uma atribuição
lexical incorreta. O owner da raiz é a leitura compartilhada do usuário.

**Produção alterada somente em `mente_laylay/emocoes/leitura_usuario.py`:** verbo
pessoal, sinal e grau precisam pertencer ao mesmo predicado reconhecido. A
contingência conservadora deixa formulações incertas para a principal. Relatos
curtos de tédio/esgotamento e intensificadores posteriores continuam válidos.
Orquestrador, executor, prioridade causal e estado emocional próprio não recebem
outro candidato nesta entrega; nenhum commit criado. A mesma leitura é reutilizada
pela cognição, conversa curta, contingência e qualidade da fala, sem parser por
habilidade ou interpretação emocional adicional.

RED antes do candidato: **10 falhas/19 controles GREEN**, incluindo a composição
instalada por `laylay.py`, antes de qualquer publicação semântica. Controles de
intensidade detectaram quatro regressões do primeiro candidato; corrigidas antes
da coleta. **408 focados/8 subtestes GREEN**, mais **13 da sonda GREEN**. Ampla:
**9.394 passed, 1 skipped, 56 subtests passed** (221,15 s), em
`.pytest_cache/p16_vinculo_predicado_ampla.log`; baseline/hashes conferidos.

Main novo `resultados_testes/transporte_evidencia-20261001-210441-907211/`, roteiro
de seis relatos, sem replay/injeção. Os três relatos temporais receberam principal
nova/HTTP200, bruto e seis identidades correspondentes: nenhum evento lexical
anterior, alívio válido publicado como `leitura_semantica_principal`, expressão
própria inalterada, sem comandos/autorização. O controle de tristeza presente
preservou vulnerabilidade lexical e precedência direta. Não prova leitura temporal
arbitrária, negados/citados/condicionais ou transição física de bronca para calma.
Voz/avatar desativados; som físico da coleta anterior continua pendente.

**O roteiro completo não ficou GREEN:** três passaram, dois alertas de latência
e uma falha, p95 18,137 s. No sexto relato, `Meu irmão está bravo. Eu me sinto
culpado.`, memória de pessoas gravou `Esta` como irmão, antes da principal:
receipt `PEOPLE_REMEMBER` confirmado e registro `pessoa:105d09395b32` relido em
`memoria/pessoas_relacoes.json`. Falha separada na atribuição de identidade antes
de persistir, ainda aberta; não vem dos comandos originais da LLM (vazios).
Não apagar o registro nem enfraquecer a expectativa `sem_comando` para obter GREEN.
Dois originais vieram fora de JSON; um deles incluiu `Senti isso antes`, observação
separada de fidelidade, sem atribuição de nova raiz ou validação textual global.

25 registros do modelo: seis principais bem sucedidas, um reparo de comunicação
HTTP200, 17 retornos locais principais e um reparo bloqueado; mais pré-aquecimento
= oito HTTP200. Quatro publicações semânticas observadas. SQLite/resumo próprios;
memória de pessoas permanece no caminho normal, sem isolamento total. Processo
código zero; **116 Python preservados por hash** na coleta e ampla, TXT diário
pessoal preservado. `prova_vinculo_predicado.json` separa prova desta raiz da falha
vizinha. P16 permanece parcial com as lacunas anteriores e essa nova investigação.

#### Checkpoint P16 — identidade literal antes de memória e tipo de aprendizado — 04/10/2026

Base `main`/`90a2fb8698541119f523c0a22fa4de0187cbaf92`, worktree preservada.
Continuação da falha de `Esta` acima, sem reatribuir essa persistência à LLM ou
à leitura emocional. Owner `MemoriaPessoasRuntime._extrair_relacao`: a moldura
`minha/meu + relação + palavra` aceitava predicados como nomes; por ordem, também
sobrescrevia nomeações explícitas (`se chama Esta → Se`). Extração direta e
serviço real reproduziram 11 REDs/36 controles; composição instalada cinco REDs/
um controle, antes do candidato. Falha geral de armazenamento e origem no modelo
falsificadas por extração sem modelo e controles de apresentações explícitas.

**Produção desta raiz: somente `memoria_pessoas.py`.** Removida a moldura solta;
apresentação/nomeação explícita autoriza criação de identidade persistente pelo
mesmo serviço, fonte literal, memória/contexto/aprendizado/receipt já existentes.
Sem blacklist de `Esta` ou verbos históricos. Menções como `meu irmão Carlos`
deixam de cadastrar por si só; `Carlos é meu irmão`, `meu irmão é Carlos` e
`meu irmão se chama Carlos` continuam cobertas. Não certifica toda ambiguidade de
nomes/adjetivos nas copulas nem interpretação arbitrária do português.

O GREEN local revelou outra raiz no controle positivo da composição. Trace real:
`Meu irmão se chama Esta.` foi consumido pelo atalho de linguagem aprendida,
criando alias `meu irmao se → esta`, antes de chamar memória de pessoas. Não era
P0, serviço desconectado ou armazenamento falho. Quatro REDs/quatro controles com
SQLite real, em pessoas, projeto e arquivo. **Produção dessa raiz: somente
`linguagem_aprendida.py`.** Separador `chama` não captura nomeação reflexiva
`se chama`; ensino explícito de apelido continua válido. Não reordenar handlers
ou criar outro parser por domínio. Contrato comum: a evidência literal autoriza
o tipo de aprendizado; nomeação não autoriza substituição lexical global.

95 focados/composição GREEN; sonda final 17 GREEN. Composição usa os objetos e
callbacks instalados por `laylay.py`, banco e armazenamento reais próprios.
Sonda ganhou isolamento **opcional** de pessoas e observação before/after com
hash e dados, sem mudar decisões/retornos. Roteiro novo exige o isolamento antes
de abrir o runtime; configuração carregada pelo loader real e guarda CLI testadas.

Main novo `resultados_testes/transporte_evidencia-20261004-174111-482431/`, roteiro
`roteiro_memoria_pessoas_identidade.py`, oito turnos, sem replay ou falha injetada:

- Histórico e duas variantes passam pelo owner, sem arquivo/perfis/receipts.
- `Meu irmão se chama Esta.` persiste Esta/irmão, fonte literal e ID próprio,
  com PEOPLE_REMEMBER confirmado e releitura do arquivo.
- `Meu irmão estava bravo.` após o cadastro não altera bytes nem cria receipt.
- `Quem é meu irmão?` retorna `Esta é seu irmão`, PEOPLE_QUERY confirmado.
- `Meu projeto se chama Aurora.` não cria pessoa nem alias; apresentação de Ana
  cria somente Ana/prima com receipt e fonte relidos.
- SQLite próprio tem zero aliases; todos os planos mantêm `autoriza_execucao=False`.

Cinco passaram/três alertas de latência/zero falhas, p95 29,426 s. Prova de memória
é receipt + dados relidos, não só placar. **Sete principais técnicas insuficientes**:
timeouts/circuito; contingências existentes participaram da fala. A captura
corretamente registra `fonte_tecnica_insuficiente`; não promove o placar à prova
semântica ou ao erro próprio/admissão positivo da P16. Voz/avatar off, sem prova
física nova. Uma resposta anterior de contingência inadequada continua observação
de fidelidade separada, não correção dessa raiz.

`prova_identidade_pessoas.json` e baselines arquivam a cadeia. **119 Python
preservados por hash durante a coleta**, JSON pessoal e TXT diário anteriores
intactos. Registro pessoal histórico `pessoa:105d09395b32` preservado, sem limpeza.
Isolamento limitado a SQLite/resumo/pessoas; não todo estado do runtime. Depois
da coleta, acrescentada somente a guarda CLI/teste para exigir esse isolamento
no roteiro novo; candidato de produção inalterado. **Ampla: 9.429 passed,
1 skipped, 56 subtests passed** (280,69 s), código zero, log
`.pytest_cache/pessoas_identidade_ampla.log`; manifesto de 119 e arquivos pessoais
conferidos depois em `pessoas_identidade_ampla_conferida.json`. Alcance preciso:
os 119 acompanham a base suja e testes/roteiro novos; os dois owners, antes limpos,
ficaram fora desse manifesto. `auditoria_fontes_candidato.json` confere seus
baselines originais, diff mínimo e mtimes anteriores à coleta; hashes atuais
registrados após a ampla, sem inventar um hash pré-coleta. Nenhum commit/push ou desligamento.
P16 permanece parcial: positivo próprio fresco, som físico/continuidade visual
integral, autor da troca histórica e causa do crash continuam sem encerramento.

#### Checkpoint P16 — fontes novas e pré-condição de redundância no runtime — 04/10/2026

Base `main`/`90a2fb8698541119f523c0a22fa4de0187cbaf92`. Manifesto anterior às
duas coletas cobre **1.245 Python**, incluindo os dois owners do checkpoint anterior;
todos preservados por hash depois. JSON pessoal e TXT diários anteriores também
intactos. Nenhuma alteração Python, orçamento, circuito ou candidato de produção.

**Disponibilidade do backend:** após Pedro encerrar o jogo, processo ausente e GPU
com 4.987 MiB livres, contra 2.190 MiB/98% de uso antes. Pré-aquecimento pelo serviço
existente, orçamento padrão, Qwen3:4b-instruct pronto em 2,451 s. Isso permite uma
coleta com fontes novas; não demonstra que a disputa de GPU foi a única causa dos
timeouts históricos. Não atribuir a memória de pessoas nem a culpa própria a uma
falha técnica do transporte.

**Controles novos da principal:** `transporte_evidencia-20261004-182525-927021`,
oito pedidos explicativos/negados/hipotéticos de IoT: **8 passaram, zero falhas ou
alertas**, p95 7,953 s. HTTP200, payload, bruto, retorno registrado, turno e plano
correlacionados para cada principal. Oito originais sem comandos e sem violações,
dispatchers vazios e nenhuma entrada no executor IoT. `prova_p16.json` conserva a
cadeia e o manifesto. É GREEN desses controles com fonte nova; **não houve proposta
original incompatível**, portanto não foi observado o positivo de erro próprio,
publicação/admissão. Voz/avatar desativados nessa coleta; fidelidade textual global
não foi certificada.

**Voz/avatar no loop real:** `transporte_evidencia-20261004-182929-427557`, roteiro
`roteiro_personalidade_p16_voz_avatar.py`, 16 turnos, saída zero. Todas as respostas
e as 16 filas de áudio concluíram, sem silenciamento, saída Realtek. **O roteiro
permanece RED: 5 passaram, 8 falharam, 3 alertas**, p95 23,244 s. Expectativas e
IDs históricos preservados; não converter oito sintomas em oito raízes.

Primeira divergência no turno 4: o executor observou Calculadora aberta **sem
foco**, focou e confirmou `app_focado`, `executou=True`, `confirmado=True`, receipt
`7e0b232057f04911879fc46ec91d310c`. O roteiro exigia uma não-ação
`ja_aberto_focado`. Nova interrupção no turno 9, receipt
`7043e96cfbb24f6b9e26e81968d6ec61`. Retrato do turno aponta navegador em primeiro
plano nos dois casos; quem provocou a troca ainda não está identificado. A
observação pela API de computer-use não emitiu entradas nem ativou janelas.

Owner `AvaliadorEventosEmocionaisRuntime`: conta redundâncias **consecutivas por
intenção/alvo**, apoiadas em receipts. Um foco realmente executado interrompe esse
sufixo. Reavaliação offline dos dez receipts gravados pelo mesmo owner corresponde
aos dez eventos, incluindo causa, repetição, nível, responsabilidade e referência.
Primeira interrupção ocorre só 20,195 s depois da redundância anterior, dentro da
janela de 300 s. Isso falsifica erro de contagem/expiração para a primeira RED;
a reavaliação não é outro runtime nem receipt injetado. Os sintomas dos turnos
4/5/6/7 e 9/10/11/14 decorrem das pré-condições de sequência não realizadas;
preservar o RED e controlar/observar o foco numa próxima coleta, sem falsificar
efeito como não-ação para obter a escalada esperada.

Seis principais novas de conversa correlacionadas a HTTP200 e à ocorrência real,
sem comandos/violações. Conquista e vulnerabilidade encerram o episódio observado;
assunto novo retorna a calma. Relato temporal publica alívio do usuário, sem
contingência lexical de tristeza passada e sem transformar leitura em autorização
ou emoção própria. Desculpa com episódio `brava` não foi exercitada nesta coleta.
Além das seis principais, houve dez autorias operacionais, oito reparos factuais,
dois reparos de comunicação bem sucedidos, três bloqueados e 14 retornos locais
principais; 27 envios/respostas HTTP incluem o pré-aquecimento. Não promover esses
reparos a proposta original ou declarar todas as falas autorais/fidedignas.

`prova_voz_avatar.json`, `baseline_investigacao.json`, `backend_observado.json` e
`observacao_janela_avatar.json` arquivam resultados/limites. Runtime registra avatar,
mas a API não retornou sua janela capturável; nenhuma imagem física foi obtida.
Confirmação humana desta coleta sobre som completo e acompanhamento visual foi
solicitada e permanece pendente. Mesmo confirmada, a sequência não prova expressão
física de `brava 3`, que não foi alcançada. Saída zero não encerra crash histórico.
P16 parcial: positivo próprio fresco, sequência integral com pré-condições reais,
observação física e investigações históricas continuam abertas. Nenhum commit,
push, limpeza ou desligamento nesta entrega.

### P17 — Liberdade comportamental e recusa segura

- [ ] Substituir bloqueios fixos baseados apenas em `brava nível 3` por uma política
  que avalie causa, responsabilidade, risco, necessidade e reversibilidade.
- [ ] Permitir bronca direta, recusa de retrabalho redundante e uma resistência
  contextual a pedidos opcionais de baixo risco.
- [ ] Preservar execução de ações urgentes, de segurança e acessibilidade.
- [ ] Fazer a braveza mirar o comportamento observado, nunca inteligência,
  aparência, identidade ou valor da pessoa.

**Avanço de P17, 04/10/2026 — reação após receipt.** A primeira divergência
reproduzida estava na autoria operacional: o mesmo prompt convidava a recusar
retrabalho e brincar com repetição do pedido tanto após redundância confirmada
do usuário quanto após falhas atribuídas ao sistema. O roteador já não veta
ações somente por `brava`, e o avaliador causal separa essas duas origens;
nenhum dos dois era a raiz deste RED. A autoria agora só convida a bronca sobre
repetição quando evento ativo e receipt atual coincidem por solicitação e alvo,
com responsabilidade do usuário, confiança mínima de 90% e estado já
satisfeito confirmado. Nas outras causas, conserva o resultado e mira a causa
observada. O verificador rejeita recusa explícita sobre ação executada ou falha.

O catálogo recebeu descrição limitada da recusa por redundância. Um RED
separado revelou que `aba` dentro de `retrabalho` selecionava navegador; a
correspondência de termos curtos agora exige palavra inteira nos três leitores
do catálogo. A regressão ampla revelou que o plural `apps` deixou de casar
com `app`; o alias explícito restaurou essa pergunta, sem reabrir a colisão
com `retrabalho`. Controles de perguntas sobre aba, trabalho e apps passaram.
Teste de composição importa `laylay.py`, registra receipts controlados de app redundante
e falha de arquivo, usa avaliador/publicador/adaptador reais e confirma uma
fala ligada ao receipt; não prova efeitos externos ou comportamento do modelo
em sessão física. P17 segue aberta: falta ampliar a política tipada a outras
ações com risco e reversibilidade auditados e avaliar linguagem pessoal mais
ampla. Quatro REDs mostraram que insultos explícitos
diretos à pessoa atravessavam o verificador da autoria. O contrato agora os
rejeita e usa a fala local se a geração e o reparo insistirem; quatro controles
de resultado factual preservados. Regressão relevante final: 265 aprovados.
A suíte completa antes desse último guarda terminou com 9.439 aprovados,
1 ignorado e 56 subtestes; não repetir esse número como suíte global final.
O P17 histórico de foco no Chrome, no registro
de problemas, é outra raiz.

**Avanço de P17, 04/10/2026 — resistência opcional limitada.** O RED canônico
mostrou que um pedido opcional com causa emocional ativa seguia direto ao
executor; o teste pela composição encontrou uma segunda fronteira: a entrada
prioritária não recebia a pendência compartilhada e deixava o `sim` sem
consumo. A decisão tipada agora exige episódio causal vigente, atribuído ao
usuário, `brava` nível 3 com confiança de ao menos 90%, turno autorizado e
pedido explicitamente opcional. O piloto alcança somente **alternar a
repetição**, cujo verbo corresponde ao `repeat_toggle` real; pedidos para
ativar ou desativar não entram nessa resistência. Urgência, segurança,
acessibilidade e necessidade declarada continuam no executor. A pergunta
observável cria pendência com TTL de 90 segundos; `sim` usa o executor comum,
`não` encerra sem efeito, e comando independente preserva a oferta. Novo
comando direto para alternar no mesmo destino/player encerra a oferta antiga.
A mesma evidência não
gera nova resistência durante sua vigência; o registro fica na mente
compartilhada com prazo próprio. Se o aceite já estiver em processamento, um
segundo pedido de alternância recebe resposta observável sem segundo despacho;
a substituição da pendência exige status ainda `ativa` na mesma transação.
Comandos independentes também seguem seu fluxo enquanto o aceite está em
processamento.

A composição instalada foi exercitada com estado e pendência reais e com
despacho externo controlado. Isso prova o transporte e a continuidade, não
o efeito físico de mídia ou a audição da fala. A porta booleana antiga foi
removida depois do RED descrito abaixo, pois consumia o turno sem resposta.
P17 permanece aberta para
classificar outras ações com risco, necessidade e reversibilidade, provar a
linguagem gerada em sessão e observar o caminho físico de mídia. A regressão
ampla passou com 9.462 aprovados, 1 ignorado e 56 subtestes antes da última
guarda focada, que impede uma menção sem autorização de consumir a pendência.

O caminho completo encontrou ainda **RPV17-05**: o detector de mídia reconhecia
`repeat_toggle`, mas a gramática de modalidade classificava “alterna a
repetição. É opcional.” como conversa. O pedido não chegava ao roteador. A
gramática musical agora reconhece apenas a alternância com verbo diretivo e
domínio explícito, com qualificadores estreitos de opção, urgência, segurança
ou acessibilidade; perguntas, relatos, hipóteses e negação continuam sem
autoridade. O planejamento, a entrada
prioritária, a pendência e a confirmação foram exercitados na composição
instalada com executor externo controlado. Regressão relevante posterior:
245 aprovados e 22 subtestes; a suíte ampla não foi repetida após esta última
mudança na gramática.

**Avanço de P17, 04/10/2026 — porta legada de veto.** Um RED mostrou que um
callback `_bloqueio_por_emocao=True` ainda consumia `APP_OPEN` sem fala nem
receipt, antes do executor. O callback instalado já devolvia `False`, então
não era a causa do piloto de repetição; o risco permanecia no contrato do
roteador. A porta saiu do roteador e do contexto montado. A resistência
opcional tipada continua com pendência e pergunta observável. A composição
instalada confirmou que não expõe mais a porta antiga. Isso não amplia o
piloto a outras ações nem comprova áudio ou efeito físico de mídia.
Suíte completa após a remoção: 9.482 aprovados, 1 ignorado e 56 subtestes.

**Avanço de P17, 04/10/2026 — linguagem dirigida à pessoa.** Quatro REDs
ampliaram RPV17-03: “você é um fracasso”, “ninguém te aguenta”, “sua
inteligência é limitada” e “você é feio” passavam pelo verificador da fala
operacional. A guarda agora rejeita essas construções antes da publicação;
geração e reparo ofensivos usam a fala local. A regressão relevante somou 196
testes verdes, incluindo controles de app e IoT. Uma sonda sem efeitos chamou
o modelo local: houve timeout em
8 s e, numa coleta que pediu 15 s mas permaneceu limitada a 8 s por chamada,
saídas rejeitadas pelo contrato, com fallback local. Outra
amostra acrescentou pergunta e detalhe numérico sem prova. Ainda falta uma
fala gerada válida e observada em sessão. Na auditoria de novas ações,
`pause_play` não foi
promovido ao piloto: sua alternância poderia retomar mídia pausada sem estado
observado e sem prova de que esse efeito era opcional para o usuário.

**Avanço de P17, 04/10/2026 — evidência numérica da autoria.** A sonda local
encontrou RPV17-06: o prompt oferecia `repeticoes=4` como contexto emocional,
mas a validação da fala só autoriza números do receipt e da fala factual. O
modelo usou “4 vezes” e o guardião caiu na fala local. O RED de projeção ficou
verde após conservar arco e responsabilidade, converter nível em intensidade
textual e retirar contagens e métricas numéricas do prompt. São 196 testes
relevantes verdes. A tentativa posterior com o modelo local expirou no
transporte rápido; ainda falta observar uma fala gerada válida, sem mudar o
orçamento de latência da sessão.
Suíte completa após o candidato: 9.496 aprovados, 1 ignorado e 56 subtestes.

**Auditoria de P17, 04/10/2026 — fallback e orçamento.** O limite de 8 s da
classe rápida é aplicado pelo orçamento único mesmo quando a autora pede
15 s; é uma proteção deliberada de latência e não foi ampliada. Um teste
pela composição instalada simulou timeout da autora após receipt redundante:
a fala factual saiu uma vez com `brava` nível 3 do evento causal. Orçamento,
reação e composição somaram 46 testes verdes. Na checagem do ambiente, o
modelo local estava descarregado e o Just Cause 3 aparecia como processo
gráfico; não houve nova
prova de fala gerada válida nem de áudio físico.

**Avanço de P17, 04/10/2026 — guarda de linguagem na conversa.** A mesma
RPV17-03 apareceu no reparo conversacional: a autoria final aceitou `Você é
um fracasso.` e a avaliação posterior também, permitindo a entrega da frase.
Cinco REDs reproduziram as fronteiras; a detecção explícita de ataque pessoal
foi centralizada e usada pela confirmação operacional, autoria conversacional
e avaliação de qualidade. A composição agora repara uma resposta principal
ofensiva e usa contingência quando a autoria final gera ataque. O controle de
deboche dirigido ao comportamento continua aceito. Uma ofensa citada e
criticada deixou de ser bloqueada por engano; a mesma frase isolada, endossada
ou seguida de ataque continua vetada. Regressão relevante: 292 testes
aprovados; suíte completa após o ajuste: 9.506 aprovados, 1 ignorado e 56
subtestes. Falta provar fala gerada válida em sessão e áudio real.

**Avanço de P17, 05/10/2026 — identidade da retomada e da fala.** RPV17-04
perdia PC B/ambos e o player ao criar a pendência, retomando o alvo padrão no
`sim`. A projeção estrita agora conserva destino resolvido e parâmetros
auditados, e pendência inválida encerra com resposta sem despacho. A
composição instalada confirmou o transporte em PC A, PC B e ambos com
`platform=music`. A substituição exige a mesma identidade de destino/player;
um controle independente conserva a oferta. O aceite exige o ID observado
antes de resolver: se outra oferta surgir, nenhuma é consumida ou despachada,
e a resposta comunica a troca. A guarda canônica também protege uma oferta
de outro domínio; um comando novo passa antes do resolver. Os 107 testes
focados e vizinhos passaram, com revisão independente de 16 controles.
RPV17-03 recebeu novos REDs de intensificadores, descrição
da pessoa e endosso de ofensa citada; a guarda compartilhada os bloqueia,
preservando negação local e crítica ao ato. RPV17-07 é uma raiz distinta:
o executor confirmava alternância de repetição, mas a chave de fala virava
`replay` e anunciava reinício. O catálogo compartilhado agora recebe a ação
canônica e descreve somente a alternância.

Regressão completa final: **9.559 aprovados, 1 ignorado e 56 subtestes**.
O root usou banco temporário e mutex Windows real de teste no primeiro import
solicitado pelos testes, preservando sua ordem. As tentativas anteriores e as
causas de ambiente estão no registro central; a sessão aberta foi preservada.

Uma coleta com `qwen3:4b-instruct` pelo cliente e orçamento instalados respondeu
dentro de 8 s: APP_OPEN foi aceito após reparo e CREATE_FILE na primeira fala.
Os receipts eram sintéticos e não houve voz ou executor físico. A amostra de
falha ainda atribuiu vontade ao sistema; aceitação textual não encerra a
avaliação causal e social. Artefato: `resultados_testes/p17_autoria_real_20261005.json`.
P17 segue aberta para classificação de outras ações, qualidade da fala gerada
em sessão e prova física de mídia/áudio.

**Critério finito de encerramento da P17 — 05/10/2026.** O escopo de
resistência permanece no catálogo auditado `repeat_toggle`; outras ações
seguem a execução normal e sua classificação futura não é requisito para
encerrar este piloto. Não ampliar o catálogo para obter um verde. O roteiro
`roteiro_personalidade_p17_encerramento.py` contém 11 turnos: preparação da
Calculadora, quatro redundâncias, oferta opcional, recusa, nova ocorrência,
nova oferta, aceite e restauração da repetição. A sonda
`sonda_personalidade_p17_real.py` inicia o root/loop reais, observa sem substituir
retornos e interrompe os próximos turnos no primeiro RED.

Exigir receipt do executor, causa vinculada à ocorrência, bronca com autoria
LLM aprovada e transporte real dentro do orçamento instalado, uma fala por
turno, pendência canônica, ausência de efeito antes do aceite e após recusa,
uma alternância confirmada e observada no mesmo player, restauração e sucesso
TTS do mesmo turno. Áudio físico exige confirmação humana posterior. Os
controles de necessidade, urgência, segurança, acessibilidade, identidade e
corridas permanecem nas provas de composição já registradas; não reabrir P16
nem acrescentar uma matriz indefinida. Oito testes protegem o veredito da
sonda contra autoria sem transporte/orçamento, ocorrência trocada, player
antigo e TTS de outro turno.

A coleta real `p17_real_20261005_204129` comprovou bronca `brava/3` gerada e
aprovada no turno 4, uma chamada real em 1,169 s dentro de 8 s, receipt e
TTS correlacionados. A coleta de política `p17_real_20261005_223753` executou
os 11 turnos e restaurou o player, mas não encerra P17: revelou omissão da
conclusão de adiamento no plano (RPV17-04) e direção de estado inventada pela
autoria (RPV17-08, distinta da antiga chave local RPV17-07). Preservar ambos
os REDs no registro central. Os quatro REDs da guarda factual ficaram verdes;
95 testes relevantes passaram. Nova coleta do candidato e audição humana
pendentes; geração inválida continua usando fallback seguro.

O candidato de publicação de RPV17-04 passou em nove testes próprios e nos
vizinhos (**261 aprovados**); a seleção de autoria/mídia/resistência/sonda teve
**203 aprovados**, com sobreposição. Adiamento tem owner `politica`, publicação
anterior à pergunta e não alimenta aprendizado como falha de efeito.
`p17_real_20261005_225131` parou no segundo turno por ausência de foco lido da
Calculadora: os receipts eram de foco, sem a redundância exigida. Nenhuma
mudança de mídia ocorreu. A coleta do candidato continua pendente sob a mesma
condição causal; não ampliar o roteiro nem enfraquecer essa expectativa.

### P18 — Integração de causas em todos os contextos

**Preparação independente, 05/10/2026.** RED salvo fora da coleta normal em
`resultados_testes/p18_feedback_emissao/test_personalidade_viva_p18_feedback.py`:
aceitação e recusa de uma emissão confirmada chegam ao coordenador e à rede,
mas não ao `MotorAprendizadoRuntime` compartilhado. Resultado: dois REDs
esperados e dois controles verdes. O motor real grava no mesmo SQLite
temporário; a fila da rede foi processada e falha de entrega não cria alvo de
feedback. A primeira divergência é a ponte de iniciativa para o aprendizado
comum. As ligações foram extraídas do AST atual do root; não é prova de sessão
ou áudio. Contrato mínimo preparado: encaminhar feedback uma vez com
proveniência da emissão, usando `registrar_feedback_contextual`, sem conceder
execução ou preferência durável. Produção P18 ainda não alterada.

**Primeiro contrato implementado, 06/10/2026 — RPV18-01.** Após autorização de
Pedro, presença entregue passou a encaminhar aceitação, recusa, correção e
silêncio qualificado ao motor compartilhado pela porta já existente. A
ocorrência conserva origem, domínio, alvo e ID da entrega; o armazenamento
canônico impede dupla contagem em concorrência ou após reiniciar o motor.
Fila sem entrega e silêncio antes de 600 segundos não fornecem evidência.
Uma corrida com nova presença revelou perda do feedback anterior; o histórico
existente agora conserva feedback/diagnóstico por ID, sem transferi-los à nova
emissão. RPV18-02 corrige separadamente a precedência de tipo explícito no peso
da correção/repetição; não altera a futura calibração de tolerância da P20.

Diagnóstico distingue feedback observado de persistência confirmada; catálogo
vivo e perguntas naturais explicam o limite. **182 testes relevantes aprovados**,
incluindo root instalado com SQLite isolado e três evidências confirmadas no
banco. Receipts de entrega controlados nessa composição não provam nova sessão
ou som físico. Falha de gravação tem diagnóstico, sem retry automático do
feedback consumido. Os quatro itens da P18 permanecem abertos: o transporte de
presença é uma parte do aprendizado, e ainda faltam integração dos produtores
emocionais, compositor local no jogo e validação real sequencial.

**Presença local no jogo, 06/10/2026 — RPV18-03/04/05.** Investigação finita
autorizada no Just Cause 3 encontrou a primeira falha antes da presença:
o modelo visual padrão `qwen/qwen3.6-27b` retornava HTTP 404. Catálogo real e
documentação do provedor confirmaram o sucessor 3.8; a composição externa usa
um padrão único atualizado, preservando configuração explícita e os mesmos
limites de transporte. A análise visual voltou a produzir evidências reais.

Reações espontâneas do jogo agora materializam o contrato cognitivo localmente,
com variação compartilhada, sem preparar prompt ou chamar novamente a LLM.
Cotidiano mantém a autoria da LLM. Cognição decide a direção social; porteiro,
fila e callback existentes continuam donos da entrega. O catálogo vivo explica
essa capacidade e suas dependências sem confundir observação com autorização.

Uma coleta intermediária revelou motivo interno falado como se fosse fato.
O transporte agora separa motivo e evidência desde o produtor até o contrato;
controles em jogo e janela protegem a mesma regra. Fontes completas são
preservadas para recusar orações longas, evitando palavras cortadas. Rótulos
iniciais conhecidos do protocolo ficam na fonte, sem aparecer na apresentação;
imperativos e primeira pessoa observados continuam explicitamente citados.

**313 regressivos relevantes aprovados**, incluindo composição instalada,
uma fila/um timer, zero autoria extra, prioridade da fala do usuário, receipts,
feedback, aprendizado e catálogo. A coleta real final de 120 segundos
`resultados_testes/p18_jogo_real_20261006_114837` teve uma análise visual válida,
uma reação ao fato `ROCCA BLAU`, uma entrega confirmada por ID e zero chamadas
de autoria. Guardas de fonte longa e apresentação posteriores à coleta têm
prova focada; os hashes conservam a versão efetivamente executada. A audição
física permanece pendente, sem ser inferida do callback.

O item de materialização local está concluído para reações de presença no jogo;
conversa explícita em jogo mantém seu serviço existente. A P18 inteira segue
aberta na integração causal dos produtores emocionais e na arbitragem conjunta
dos demais contextos. Não reabrir P16 nem repetir esta coleta sem um novo RED.

**Integração de software concluída, 06/10/2026 — RPV18-01/06/07.** A direção
social já decidida agora gera uma ocorrência causal compartilhada em turno,
plano, contrato, quadro e episódio elegível. Jogo, rotina e janela atravessam
os owners instalados; confiança/tempo/autoridade são revalidados, inclusive
depois da autoria. Uma utterance concorrente conserva seu plano.

Avisos registram somente recebimento do lote e mantêm prioridade de segurança,
sem inventar irritação. Seu receipt alimenta o Diretor e o mesmo aprendizado.
Aceitação, recusa, correção, repetição e silêncio qualificado também publicam
uma observação causal neutra, sem outra fala, emoção inferida ou preferência.
Replay e concorrência conservam a identidade; outro recebimento do mesmo aviso
tem outra ocorrência. Uma entrada descartada não consome feedback e uma
correção da entrega não conta novamente como conversa genérica.

O worker congela texto/emoção quando inicia reprodução; antes disso, candidatos
podem consolidar uma única fila. Root instalado, SQLite real isolado e
pipeline principal comprovaram uma evidência por correção, uma causa neutra,
zero comandos autorizados e coexistência de uma fala principal com aviso
adiado. Receipts/modelo/saída física desses controles são portas controladas.

**609 regressivos finais aprovados em 27,11 s.** Incluem os novos contratos,
composições instaladas, presença/visão, filas, aprendizagem, catálogo,
diagnóstico e transações. A suíte ampla anterior teve **9.738 aprovados,
três expectativas antigas incompatíveis, um skip e 56 subtestes aprovados**.
As três fixtures foram corrigidas após diagnóstico: tom livre sem causa,
identidade/relógio ausentes e exigência de frase LLM no jogo. Nenhuma produção
mudou depois da suíte ampla; as três e os 24 controles de feedback causal
estão na seleção final. Contagens sobrepostas não são somadas.

Artefatos: `resultados_testes/p18_fechamento_20261006`, com XMLs, seleção,
hashes da fonte e resumo dos limites. Estes quatro itens representam código e
integração GREEN. Audição física e alinhamento perceptível de voz/avatar
seguem para P19/P21; a sessão real do jogo e seus hashes anteriores permanecem
como evidência da versão que efetivamente rodou. Calibração implícita da rede
e tolerância contextual seguem na P20. P16 permanece no escopo já aprovado.

- [x] Ligar conversa, comandos, proatividade, feedback, notificações e modo jogo
  ao contrato emocional canônico.
- [x] Fazer aceitação, recusa, correção, repetição e silêncio qualificado chegarem
  ao aprendizado compartilhado.
- [x] Manter a LLM como autora da fala cotidiana e um compositor local rápido e
  variável no jogo, sem chamada adicional ao modelo.
- [x] Garantir uma decisão e uma fala por turno, sem conflito entre emoção e comando.

### P19 — Expressão multimodal sincronizada

**Integração de software aplicada, 06/10/2026.** A entrega possui retrato
imutável com identidade, emoção, nível e referência à causa validada antes
da publicação. Texto e fila usam o mesmo retrato; preparação, voz neural,
fallback e visual conservam essa expressão até concluir ou interromper.
O estado transitório é limpo inclusive quando a preparação falha. Episódio
vivo, validade causal, autorização e memória pessoal continuam separados.
Os REDs e owners estão registrados como RPV19-01 a RPV19-04.

O avatar nativo e a Game Bar consomem intensidade em escala estática discreta
(97% a 100%) e movimento contido; movimento desativado fixa corpo, aura e
transição. O helper pondera antes do arredondamento. Emoção e intensidade
permanecem juntas durante a transição pendente do PNG. Nenhum asset novo foi
criado. Catálogo e pergunta natural explicam a expressão, sem prometer um
overlay indisponível.

**Provas:** 855 testes aprovados em 37,35 s, build UWP Debug/x64 e composição
instalada em `resultados_testes/p19_expressao_20261006`. A coleta finita
`p19_real_20261006` durou 42,028 s, com TTS/player e processo do avatar reais:
duas falas completas segundo os receipts de software; 89 amostras conservaram
A/1 enquanto a causa viva já era B/3, e 82 amostras da segunda fala usaram B/3.
Texto, limpeza do retrato e zero chamada à LLM também foram conferidos.

**Limite da coleta:** causas controladas, sem `main`, memória isolada e sem
alterar preferências do usuário. O overlay não foi exposto para captura pelo
computer-use; audição e aparência foram perguntadas ao usuário e ainda não
confirmadas. Game Bar passou no compilador e no consumidor C#, mas seu pacote
instalado não foi atualizado ou aferido visualmente. Hashes da coleta e da
fonte final são separados: conclusão de espera/fallback recebeu controles
posteriores à coleta, sem outra reprodução física. P19 permanece em andamento
até a aferição perceptível dos itens abaixo; P16 não foi reaberta.

**Aferição perceptível na P21, 06/10/2026:** nova coleta de 35,776 s com
voz/player e avatar nativo reais, duas falas e 250 amostras, incluindo 77
durante fala. Os retratos conservaram A/1 na primeira entrega apesar da
troca da causa viva para B/3, e B/3 na segunda. Zero chamada ao modelo e
retrato transitório liberado ao final. Pedro confirmou diretamente áudio
completo/inteligível, expressão mantida na primeira, maior intensidade na
segunda e retorno ao neutro. Relatório bruto e confirmação humana separados
em `p21_validacao_final_20261006/coleta_multimodal`. Essa confirmação vale
para o avatar nativo e essas duas falas; não certifica o pacote Game Bar,
naturalidade no jogo ou todos os estados de execução.

- [x] Fazer texto, comprimento, ritmo, prosódia, volume e avatar consumirem o mesmo
  retrato emocional e a mesma intensidade.
- [x] Diferenciar visual e voz de `irritada nível 1` e `brava nível 3` sem exagero
  artificial ou perda de inteligibilidade.
- [ ] Sincronizar escuta, pensamento, execução, sucesso, falha e fala com o episódio ativo.
- [x] Preservar o custo atual: nenhuma chamada extra à LLM somente para ornamentação.

### P20 — Aprendizado de tolerância e relação

**Implementação da P20 concluída em 06/10/2026, com preferência explícita e
tolerância implícita integradas.** A confirmação
perceptível da P19 continua pendente; avançar esta etapa não a certifica nem
reabre P16. Baseline e worktree preservados em
`resultados_testes/p20_preferencias_20261006`, no HEAD
`90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch `main`.

As raízes demonstradas são RPV20-01 (escopo/aplicação), RPV20-02
(precedência/reidratação), RPV20-03 (transporte e consumo da preferência) e
RPV20-04 (gerador reconstruía confirmação a partir do nome do status).
O interpretador único aceita também `nos comandos`; o contexto operacional
vem da decisão canônica do turno. O pedido válido mais recente vence entre
escopo específico e geral, inclusive após reinício ou atualização durável
externa ao cache. Evidência inválida, expirada ou confiança não finita não
vira preferência. Falha de leitura não apaga o pedido temporário válido.

`pega leve` suspende a ornamentação opcional **antes** da variação local,
autoria e reação causal no jogo. Planejador, confirmações, arquivos, mídia e
IoT compartilham a política; fatos, números, alvo, receipt e autorização são
preservados. `pode me zoar mais` mantém os limites causais e de segurança.
O gerador de fala passa a consumir o contrato operacional recebido, evitando
rebaixar um brilho confirmado em 27% a ausência de confirmação. Status
otimista sem receipt continua insuficiente para anunciar sucesso.

**Prova pelo caminho instalado:** persistência/reidratação usam os owners
reais e SQLite isolado. Registro, adaptador, guardião, orquestrador e método
original de voz em modo silencioso publicam texto de app sem ação, IoT em
27% e repetição causal no jogo. Controles falho/incerto rejeitam fallback
otimista. As portas executoras desses controles são simuladas; eles não
provam ação externa ou som físico. A política não remove frases já presentes
num texto factual recebido, nem representa uma auditoria de todo template
privado de todas as habilidades.

**Regressão relevante final:** 1.264 aprovados em 60,41 s, em 81 módulos;
XML `regressivos_expressao_finais.xml`, seleção e hashes preservados. Os 952
aprovados anteriores são um gate intermediário, anterior aos ajustes dos
consumidores; não somar as execuções nem chamá-las de suíte completa.

**Aprendizado implícito integrado — RPV20-05/06/07:** interpretador único
qualifica o literal sobre humor; ponte valida identidade, receipt e contexto
da entrega; Motor persiste a evidência e Maturidade reavalia sua suficiência.
Recusar uma dica, corrigir um dado ou silenciar uma ação não demonstra
rejeição de humor. Pesos genéricos permanecem distintos da projeção de estilo.

São necessárias **três entregas distintas no mesmo contexto**, predominância
ponderada mínima de 75% e influência média mínima de 0,30. Correção de estilo
pesa -0,75; recusa -0,45; aceitação +0,45; repetição +0,25. Cada evidência
decai com meia-vida de sete dias e expira em 14 dias; uma nova não rejuvenesce
as anteriores. Silêncio exige pergunta literal sobre estilo, pelo menos
600 s e nenhuma resposta relacionada, com janela máxima de 3.600 s. Ele
enfraquece influência sem contar entre as três amostras direcionais, criar
preferência ou inverter o tom. “Ainda não sei” impede silêncio indevido.

`jogo`, `conversa` e `comandos` têm evidências separadas. Contexto é congelado
na entrega/proposta, não inferido pelo domínio nem pelo contexto posterior
do feedback. Texto publicado tem receipt comunicativo; áudio somente após
reprodução confirmada por software. Aceitação de fila e receipt de execução
não substituem entrega da fala. Pedido explícito vigente sempre vence a
inferência. A preferência derivada é temporária e recalculada após reinício;
somente evidências qualificadas com fonte são persistidas, sem episódios
pessoais ou rótulo global. Humor não concede autoridade operacional.

**Prova pelo caminho instalado:** nove entregas textuais em três contextos,
owners reais, SQLite isolado e dois processos distintos comprovam coleta,
replay, persistência, reidratação, consumo, expiração e precedência explícita.
Respostas têm conteúdo controlado; não houve LLM, ação externa ou prova de
som físico. Catálogo vivo responde perguntas naturais sobre aprendizado e
limites; diagnóstico expõe suficiência por contexto sem literais pessoais.

**Regressão relevante final da P20 implícita:** **1.447 aprovados em 86,10 s**,
94 módulos; `resultados_testes/p20_implicita_20261006/regressivos_finais_isolados.xml`.
Baseline, seleção, hashes, REDs e coleta instalada preservados. Gates antigos
com falhas continuam documentados; não somar resultados nem declarar suíte
completa. Testes usam namespace próprio no mutex Windows real e memória
temporária, sem interromper a aplicação aberta ou remover sua proteção.

**Próxima etapa:** P21, diagnóstico e validação final. Encerrar a implementação
da P20 não certifica a lacuna perceptível da P19 ou a ativação final P15–P21.

- [x] Aplicar preferência explícita imediatamente, como `pega leve hoje` ou
  `pode me zoar mais`.
- [x] Exigir várias amostras para ajustes implícitos; correção pesa mais que recusa,
  e silêncio só conta depois de dez minutos sem resposta relacionada.
- [x] Aprender tolerância separadamente por contexto, como jogo, conversa pessoal
  e comandos, sem criar um rótulo global da pessoa.
- [x] Persistir apenas preferências e evidências com proveniência; episódios e
  julgamentos continuam temporários.

### P21 — Diagnóstico, validação e ativação final

**Em andamento, 06/10/2026.** O diagnóstico usa a mesma projeção de expressão
que voz e avatar: mostra intensidade causal, emoção expressável, validade,
supressão e decisão. A referência causal é um hash; o relato pessoal não é
publicado. Evento expirado mostra `evento_fora_da_validade`, e evento válido
contido conserva o motivo da contenção. RPV21-01 possui RED e GREEN próprios;
a coleta de jogo anterior ao candidato não valida esse novo diagnóstico.

**Reação no jogo, continuidade de RPV18-04/05:** descrições comuns deixam de
ser leitura citada de protocolo; texto operacional continua citado e sem
autoridade. O foco sugerido precisa coincidir literalmente com uma evidência
do evento e atravessa parser, Coordenador, Diretor e cognição. Foco inválido,
inclusive sem fatos, não recebe fallback legado. A presença continua com uma
chamada visual e materialização local, sem segunda autoria de modelo.

Coleta finita real de 120 s, `p18_jogo_real_20261006_183052`: dois quadros,
uma reação ao radar com receipt de entrega e zero chamadas de autoria; o
segundo quadro estava coberto pelo Discord. **Nenhum quadro do laser** foi
registrado. Naturalidade e som físico aguardam avaliação humana. A fonte
visual incluiu `mecânica de graviton implícita`, sem prova independente;
essa inferência não foi escolhida nem falada. Qualidade semântica do produtor
permanece aberta, distinta do molde local de apresentação.

Artefatos deste incremento: `resultados_testes/p21_reacao_jogo_20261006`.
Matriz causal e gates distinguem testes, composição instalada e sessão real.
Gate conjunto final: **1.544 aprovados em 71,04 s**, 100 módulos,
`regressivos_incremento_final.xml`; seleção relevante, não suíte completa.
P19 conserva os limites de escuta/execução/sucesso/falha e do pacote Game Bar;
a aferição de duas falas/avatar recebeu confirmação humana nesta continuação.
P16 permanece no escopo já aprovado.
A suíte completa desta continuação foi aprovada; a ativação final conserva
os limites da validação real sequencial descritos abaixo.

**Transições do diagnóstico, continuidade de RPV21-01:** quadro emocional
guarda a última proposta; episódio conserva a seleção por prioridade.
O diagnóstico misturava a emoção forte selecionada com causa/intensidade/
responsável do evento fraco mais recente. Dois REDs de componentes e dois
REDs pela composição instalada demonstraram essa fronteira; o modo chat real
foi verificado no GREEN posterior, conforme auditoria do registro.
A projeção agora associa causa à expressão selecionada e conserva referência
separada do último evento observado. Elegibilidade sem episódio aplicado
mostra expressão contida; leitura não altera plano nem estado. Dez controles
focados passaram. A suíte completa configurada usou memória temporária e mutex
Windows real próprio. Primeiro gate: 10.068 aprovados, duas falhas de fixtures,
um ignorado e 56 subtestes aprovados. Após corrigir as portas de teste, 110
controles passaram, incluindo ausência de receipt. Gate final:
**10.071 aprovados, um ignorado e 56 subtestes aprovados em 402,44 s**,
`suite_completa_final.xml`. Primeiro XML preservado; resultados não somados.
Matriz final com 17 contratos ligada às raízes e aos casos verdes desse gate,
em `p21_validacao_final_20261006/matriz_causal.json`.
Esse retrato descreve o episódio vivo para novas publicações. Durante uma
fala em curso, texto/voz/avatar conservam o retrato imutável da entrega P19;
a mudança da causa viva não reescreve essa entrega. A coleta registra ambos.

- [x] Expor emoção, intensidade, causa, responsável, confiança, transição,
  validade, expressão ou supressão e decisão comportamental no diagnóstico.
- [x] Criar uma matriz de cenários causais, testes de transição e invariantes de
  segurança, além de regressões no terminal, voz, jogo e chat (gate de software;
  limites das sessões reais preservados).
- [x] Provar que emoção não altera resultado, não duplica fala, não atravessa
  vulnerabilidade e não permanece depois de perder validade (contratos e
  composição; confirmação física restrita às duas falas/avatar coletadas).
- [ ] Ativar a versão final somente depois da suíte completa e de validação real
  sequencial de P15 a P21.

**Limites atuais:** qualidade semântica do jogo/laser, estados operacionais
restantes da P19 e pacote Game Bar conservam suas provas pendentes. Causas
controladas e suíte verde não certificam toda a sequência real. A Laylay
principal aberta antes do ajuste precisa reiniciar para carregar o diagnóstico
novo; a coleta desta continuação usou processo novo. P16 não reaberta.

**Reabertura da qualidade do jogo por evidência humana, 06/10/2026:** Pedro
relatou `Reparei nisso. Na tela: "-FLORESTA.".`. Continuações de RPV18-05
(rótulo observado confundido com oportunidade) e RPV18-04 (reação confundida
com leitura da evidência), sem criar raízes por frase. A cognição agora contém
companhia/curiosidade com foco apenas em OCR ou fragmento nominal, conservando
a fonte; o runtime respeita a contenção também fora do jogo.

Remover o bordão e forçar a evidência a ser uma frase completa **não bastou**.
Na coleta `p18_jogo_real_20261006_215418`, Pedro ouviu e rejeitou a naturalidade.
Esse RED humano permanece registrado. O contrato foi revisto: a própria
chamada visual propõe uma reação social em papel separado dos fatos, com foco
literal, trecho concreto e indicador de humor. A cognição adota ou contém
usando os guardiões compartilhados de modalidade, alegações, aderência e
ataque pessoal. Proposta inválida/ausente fica sem fallback narrativo;
vulnerabilidade conserva veto ao humor. Não há segunda chamada de autoria,
execução ou aprendizado factual a partir da tirada.

Gate relevante da autoria: **288 aprovados**, incluindo cinco casos pelo
root instalado; catálogo atualizado e **51 controles aprovados** depois,
sem somar gates. Esses resultados não são a suíte completa da versão anterior
da P21. Artefatos: `p21_jogo_naturalidade_20261006`. Nova coleta com o candidato
autoral: `p18_jogo_real_20261006_220211`, concluída sem entrega por contenção
de vínculo incorreto no único candidato relevante. Avaliação perceptível pendente.
Vínculo textual e guardiões não comprovam universalmente a interpretação
visual; qualidade da fonte e naturalidade permanecem sujeitas à prova real.

Pedro esclareceu que a fala tratou o monstro como objeto, sem acompanhar a
ação. A seleção RPV18-05 foi refinada: dois quadros próximos do mesmo jogo
na mesma análise visual, com revalidação de alvo; prompt acompanha ações,
efeitos e resultados, sem comentários por mera aparência estática. Pacote
multimodal, cognição, prioridades, feedback e receipts existentes reutilizados.
157 controles relevantes verdes incluem o caminho instalado da sequência;
72 posteriores cobrem a guarda final. `221226` encontrou o aparecimento de
REFLECT, mas a pergunta retórica foi contida. Replay afirmativo válido não
prova áudio. Cadência mínima de 60 s acomoda o custo do par; gate final com
160 verdes, incluindo seis casos instalados. Coleta final `221645` caiu no
menu e ficou sem fala. A fonte confundiu dois contadores distintos com uma
mudança temporal; esse RED semântico não foi falado e permanece registrado.
A amostragem não acompanha continuamente cada ação; naturalidade não está
encerrada pela contagem de testes. P16 não reaberta.

Controle posterior em combate `222605`: um par antecipado no roteiro real,
uma análise visual e uma entrega; Pedro confirmou `Ouvi e a reação ficou
adequada`. Áudio e adequação desse caso aprovados. Versão de produção do gate
de 160 preservada; refinamento adicional que voltou a comentar aparência
estática foi falsificado e retirado apenas no bloco recém-adicionado.
Uma fala aprovada não comprova a semântica de todo HUD: caveira=33 → 35 não
prova mais inimigos vivos. Qualidade universal da fonte e cadência normal não
encerradas por esse controle. Declaração humana e limites no relatório.

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

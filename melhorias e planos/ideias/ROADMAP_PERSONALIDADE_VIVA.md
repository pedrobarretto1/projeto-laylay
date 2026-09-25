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

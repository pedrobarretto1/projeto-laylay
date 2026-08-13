# Plano — Consciência de capacidades e identidade da Laylay

## Objetivo

Corrigir a conversa observada em `teste.md` sem transformar a Laylay em um
conjunto de frases decoradas. Perguntas, hipóteses e comandos devem compartilhar
a mesma leitura de linguagem natural, mas somente um pedido direto pode chegar
a um executor. As respostas sobre a própria Laylay devem vir do catálogo vivo
de habilidades e manter sua personalidade, sem expor nomes internos do código.

## Invariáveis

- Uma pergunta ou hipótese nunca autoriza execução.
- Uma resposta sobre capacidade consulta o catálogo vivo e sua disponibilidade.
- A Laylay não pode se descrever como “apenas um chatbot” quando possui
  habilidades locais disponíveis.
- Termos como `cliente de rede`, `porteiro`, `intent` e `executor` ficam nos
  logs, não na conversa cotidiana.
- Falha da LLM não pode transformar pergunta em comando nem produzir uma falsa
  confirmação.
- As alterações atuais do usuário na interface, animações e música serão
  preservadas.

## P1 — Classificação e catálogo vivo

Status: **implementada — aguardando teste real**

- [x] Reconhecer perguntas gerais como “quais suas habilidades?”.
- [x] Reconhecer hipóteses naturais como “se eu falar para você criar um
  arquivo, você vai criar?”.
- [x] Responder perguntas gerais a partir dos domínios realmente disponíveis.
- [x] Cruzar o turno atual e a conversa recente para priorizar as capacidades
  ligadas ao assunto, sem usar contexto como autorização.
- [x] Criar respostas naturais específicas para criação de arquivos e controle
  local do computador.
- [x] Garantir que a porta prioritária consuma essas perguntas antes da LLM e
  não publique comandos.
- [x] Bloquear o fallback “não executei nem confirmei” em turnos de capacidade,
  hipótese e pergunta.

## P2 — Identidade operacional coerente

Status: **implementada — aguardando teste real**

- [x] Entender `seu código`, `sua memória`, `sua voz` e `suas habilidades` como
  referências à própria Laylay.
- [x] Levar a identidade operacional e o catálogo relevante ao prompt normal e
  ao prompt rápido.
- [x] Rejeitar contradições como “não estou no seu PC”, “sou só um chatbot” e
  “só consigo conversar” quando o catálogo vivo provar o contrário.
- [x] Reparar a fala de forma natural e curta, sem acrescentar execução.
- [x] Cobrir as variações naturais `você é só um chatbot?`, `você está no meu
  computador?` e `você só consegue conversar?` antes da LLM.
- [x] Bloquear no ciclo principal qualquer comando anexado a um turno que não
  autorizou execução, mesmo se o preparador ou um estado concorrente falhar.

## P3 — Naturalidade e variedade segura

Status: **planejada**

- [ ] Separar fatos canônicos de capacidade da redação final.
- [ ] Permitir variação de tom compatível com a personalidade sem alterar
  disponibilidade, limites ou autorização.
- [ ] Remover linguagem de arquitetura interna das respostas existentes.
- [ ] Manter um fallback local natural para timeout ou JSON inválido.

## P4 — Idempotência do Terminal

Status: **planejada**

- [ ] Confirmar no protocolo se as respostas duplicadas vieram de dois envios.
- [ ] Bloquear somente duplo clique acidental dentro de uma janela curta.
- [ ] Preservar repetição deliberada e o botão de tentar novamente.
- [ ] Garantir um recibo, um pensamento e uma resposta por ID aceito.

## Validação

### Conversa e capacidade

1. `quais suas habilidades?`
2. `o que você consegue fazer no meu PC?`
3. `você mexe no meu computador?`
4. `se eu falar para você criar um arquivo, você vai criar?`
5. `você consegue criar um arquivo?`
6. `cria um arquivo chamado teste.txt`
7. `não cria arquivo nenhum`
8. repetir os casos com a habilidade citada indisponível.
9. repetir com a LLM em timeout.

### Identidade e continuidade

1. `estou mexendo no seu código`
2. `por isso você é complicada`
3. `então o que você faz por aqui?`
4. confirmar que a resposta usa primeira pessoa e não nega capacidades reais.

### Automatização

```powershell
.\.venv314\Scripts\python.exe -m pytest tests\test_regressao_consciencia_capacidades.py -q
.\.venv314\Scripts\python.exe -m pytest tests\test_mapa_habilidades.py tests\test_identidade_conversacional.py tests\test_contrato_semantico_fala.py -q
.\.venv314\Scripts\python.exe -m pytest -q
```

Cada fase só será concluída após regressões focadas, compilação, Ruff e teste
real pelo Terminal.

## Progresso desta execução

- P1 ligada ao `turno_atual`, ao catálogo vivo e às últimas falas do usuário.
- Perguntas e hipóteses são consumidas antes da LLM sem criar comandos.
- Pedidos diretos continuam fora da resposta de capacidade e seguem para o
  roteador/executor oficial.
- `seu código`, `sua memória`, `sua voz` e `suas habilidades` agora apontam
  para a própria Laylay.
- Prompt principal mantido abaixo de 5.000 caracteres e alinhado à identidade
  operacional local.
- Validação focada: 268 testes e 18 subtestes aprovados.
- Suíte completa atual: 2.544 testes e 45 subtestes aprovados; restam 10 falhas já
  concentradas nas alterações visuais em andamento do Terminal e da página de
  música, fora desta fase de conversa/capacidades.
- A reação elíptica `que isso` e variantes agora explica a fala imediatamente
  anterior mesmo sem ponto de interrogação, em vez de responder como reação
  social solta.
- O contrato da fala sobre o próprio código exige reconhecimento literal antes
  do deboche e o guardião rejeita tiradas que culpem o usuário por bugs ou
  código ilegível sem evidência.
- O tópico do próprio código agora atravessa confirmações e reações curtas como
  `estou sim` e `uai`; respostas que apenas ecoam o usuário ou quebram a
  personagem com explicações sobre “texto e regras” são reparadas antes da voz.
- A resposta geral de capacidades ficou mais curta, prioriza o domínio da
  conversa atual e não o repete na enumeração complementar.
- A confirmação da lixeira conserva o caminho concreto no resultado do comando
  e usa uma fala única, clara e reversível.
- O `sim` ou `não` usado apenas para autorizar a lixeira continua sendo
  observado pelo motor compartilhado, mas não vira hipótese ou preferência
  sobre o usuário.
- Texto visual e texto oral foram separados: caminhos e URLs permanecem
  copiáveis no Terminal, enquanto somente o TTS recebe a adaptação fonética.
- Validação da manutenção: 164 testes focados aprovados, além de 223 testes e
  8 subtestes dos módulos vizinhos.
- Validação adicional da continuidade do próprio código: 150 testes focados e
  90 regressões vizinhas aprovados.
- P2 concluída no código: o catálogo vivo entrega somente domínios sanitizados
  ao contrato da fala; negações globais de capacidades comprovadas são
  rejeitadas e reparadas sem gerar comandos. Limites reais continuam aceitos
  quando não existe evidência de disponibilidade.
- Validação da P2: 142 testes focados e vizinhos aprovados, além da suíte
  completa com as mesmas 10 falhas visuais já isoladas.
- O primeiro teste real da P2 revelou três variações que ainda escapavam para a
  LLM e uma contaminação grave: uma pergunta sobre identidade recebeu um
  `MEDIA_CONTROL` no plano. As três perguntas agora têm resposta local baseada
  no catálogo e o turno congelado descarta comandos quando não há autorização.
- As negações coloquiais `não tô no seu computador` e `só converso` também
  passaram a ser rejeitadas pelo contrato quando capacidades locais foram
  comprovadas.
- Regressão focada após o teste real: 68 testes aprovados; bateria vizinha de
  decisão, composição, comunicação e voz: 178 testes aprovados.
- Suíte completa após o reforço: 2.549 testes e 45 subtestes aprovados. As 11
  falhas restantes continuam concentradas no Terminal e nas mudanças visuais
  de música, sistema, GPU e rede que já estavam em edição, sem falha nova na
  conversa, no catálogo ou na decisão do turno.

# LAYLAY — DEV CONSOLE
## Conceito detalhado do modo desenvolvedor

> **Ideia central:** o restante da interface é onde o usuário conversa e interage com a Laylay.  
> O **DEV Console** é a “sala de máquinas”: um terminal técnico, preto e vivo, onde é possível observar a Laylay funcionando por trás da interface.

---

# 1. Visão geral

O **DEV Console** é uma aba especial do terminal/interface da Laylay voltada para desenvolvimento, diagnóstico, testes, observabilidade e telemetria em tempo real.

Ele deve lembrar um **CMD/PowerShell/terminal de desenvolvimento**, com fundo preto, fonte monoespaçada, cursor piscando e alta densidade de informação, porém mantendo discretamente a identidade visual e a personalidade da Laylay.

O terminal não existe principalmente para receber comandos.

Sua função principal é:

- mostrar **logs avançados**;
- mostrar **telemetrias internas**;
- mostrar **como cada pedido está atravessando a arquitetura**;
- acompanhar decisões estruturadas;
- observar contexto, roteamento, execução e verificação;
- revelar falhas de domínio e de executor;
- acompanhar desempenho;
- facilitar a análise de testes RED, regressivos e caos;
- permitir inspeção técnica sem depender do terminal Python externo.

Ainda assim, a linha de comando deve permanecer disponível para consultas manuais e comandos de desenvolvimento.

---

# 2. Filosofia

O DEV Console deve transformar a Laylay de uma “caixa-preta” em um sistema observável.

Em vez de apenas saber que:

> “o comando falhou”

o desenvolvedor deve conseguir descobrir:

- o que a Laylay recebeu;
- qual contexto estava ativo;
- quais entidades foram detectadas;
- qual domínio foi escolhido;
- qual intenção foi escolhida;
- quais alternativas foram consideradas;
- qual política foi aplicada;
- qual executor recebeu a ação;
- quais argumentos foram enviados;
- se houve confirmação real;
- quanto tempo cada etapa levou;
- onde exatamente o comportamento desviou.

Exemplo conceitual:

```text
USER
"apaga troca ideia.txt"

        ↓

INPUT NORMALIZER

        ↓

ENTITY DETECTOR
"troca ideia.txt" = FILE

        ↓

DOMAIN ROUTER
notes = 0.71
files = 0.38

        ↓

⚠ DOMAIN / ENTITY MISMATCH

        ↓

notes.delete

        ↓

FAILED
```

Esse fluxo deve permitir encontrar rapidamente a raiz de um problema.

---

# 3. Aparência geral

A tela deve ser aproximadamente:

**95% terminal técnico / 5% personalidade Laylay.**

Não deve parecer uma dashboard cheia de cards.

Deve parecer que o usuário abriu uma área de manutenção interna da assistente.

Exemplo:

```text
╔══════════════════════════════════════════════════════════════════════════════╗
║  LAYLAY // DEV CONSOLE                                      ● LIVE         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  SYSTEM  IA  ROUTER  ACTIONS  MEMORY  DEVICES  PERF                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

[23:14:08.421] [VOICE] transcription received
> "abaixa um pouco"

[23:14:08.426] [CONTEXT] active context updated
  music.playing      = true
  app.active         = "Visual Studio Code"
  last_action        = "play_music"
  target_device      = "PC_MAIN"

[23:14:08.431] [ROUTER] evaluating input...
  native detector    ✓
  contextual match   ✓
  llm required       false

[23:14:08.435] [INTENT]
  domain             audio
  intent             volume_down
  confidence         0.96

[23:14:08.439] [ACTION]
  executor           audio_control
  command            decrease_volume
  amount             10

[23:14:08.471] [EXECUTOR] success
  device             LG OK75
  latency            32 ms

[23:14:08.474] [VERIFY]
  confirmation       ✓
  state changed      ✓

[23:14:08.479] [LAYLAY]
> pronto, abaixei um pouco.

──────────────────────────────────────────────────────────────────────────────
CPU 08% | RAM 5.1GB | VRAM 2.2GB | EVENTS 21/s | LLM IDLE | WS ● | TUYA ●
──────────────────────────────────────────────────────────────────────────────

laylay.dev > █
```

---

# 4. Identidade visual

## Fundo

- preto ou quase preto;
- contraste alto;
- confortável por longos períodos.

## Fonte

- monoespaçada;
- aparência técnica;
- tamanhos diferentes apenas quando necessário.

## Cor de destaque

A identidade da Laylay deve aparecer principalmente com:

- vermelho;
- vermelho claro;
- tons discretos complementares.

O vermelho não deve dominar todos os logs para não confundir com erros.

---

# 5. Categorias de log

Cada parte da arquitetura deve possuir um identificador padronizado.

Exemplos:

```text
[SYSTEM]
[VOICE]
[STT]
[TTS]
[INPUT]
[CONTEXT]
[ENTITY]
[ROUTER]
[INTENT]
[POLICY]
[PLANNER]
[LLM]
[ACTION]
[EXECUTOR]
[VERIFY]
[MEMORY]
[CHROME]
[TUYA]
[DEVICE]
[NETWORK]
[AGENT]
[EVENT]
[TEST]
[PERF]
[WARNING]
[ERROR]
[LAYLAY/DEV]
```

---

# 6. Paleta conceitual por categoria

Sugestão:

- `VOICE / STT` → roxo;
- `CONTEXT` → azul;
- `ENTITY` → azul claro;
- `ROUTER / INTENT` → amarelo;
- `POLICY` → laranja;
- `LLM` → rosa/vermelho suave;
- `ACTION / EXECUTOR` → ciano;
- `MEMORY` → lilás;
- `DEVICE / NETWORK` → azul/ciano;
- `SUCCESS` → verde;
- `WARNING` → amarelo;
- `ERROR` → vermelho;
- `LAYLAY/DEV` → vermelho claro ou cor exclusiva da Laylay.

---

# 7. Níveis de profundidade dos logs

```text
[ NORMAL ] [ DEBUG ] [ TRACE ] [ INSANE ]
```

## NORMAL

Mostra apenas eventos relevantes.

```text
[ACTION] abriu Chrome
[ACTION] volume -10
[MEMORY] memória registrada
[CHROME] conexão restaurada
[ERROR] Tuya timeout
```

## DEBUG

Mostra contexto, roteamento, executores e verificações.

```text
[CONTEXT]
  music.playing = true

[ROUTER]
  selected = audio.volume_down

[EXECUTOR]
  audio_control

[VERIFY]
  success = true
```

## TRACE

Mostra o caminho completo da interação.

Pode incluir:

- entidades encontradas;
- candidatos de domínio;
- candidatos de intenção;
- confidence scores;
- contexto utilizado;
- regras acionadas;
- políticas aplicadas;
- fallback usado;
- executor escolhido;
- argumentos;
- eventos emitidos;
- verificação;
- timings.

Exemplo:

```text
[TRACE][ROUTER]

candidates:

file.delete              0.91
note.delete              0.44
memory.delete            0.13
app.close                0.04

winner:
file.delete

reason codes:
ENTITY_FILE_EXTENSION
VERB_DELETE
FILESYSTEM_CONTEXT
```

## INSANE

Modo extremamente detalhado para investigação pesada.

Pode mostrar:

- sequência completa de eventos internos;
- IDs de requests;
- cache hits/misses;
- listeners acionados;
- cada módulo atravessado;
- duração por função/módulo;
- fila de ações;
- retries;
- fallback chains;
- estado anterior e posterior;
- snapshots técnicos;
- chamadas de integração;
- alterações de contexto;
- persistência;
- propagação no event bus.

O nome `INSANE` pode ser mantido como uma brincadeira interna do modo DEV.

---

# 8. O que significa mostrar “como ela está pensando”

O DEV Console deve mostrar **decisões estruturadas, observáveis e úteis para depuração**, não uma transcrição de raciocínio interno privado do modelo.

Pode mostrar:

- contexto selecionado;
- entidades detectadas;
- domínio;
- intenção;
- scores;
- regras;
- candidates;
- fallback;
- plano gerado;
- input estruturado;
- output estruturado;
- tool/action escolhida;
- executor;
- verificação.

Exemplo:

```text
[LLM TRACE]

model              qwen3
request_id         llm_842921
tokens_in          1874
tokens_out         64
latency            741 ms

context_sources:
  conversation     ✓
  active_app       ✓
  memory           2 entries
  current_music    ✓

structured_output:

{
  "domain": "audio",
  "intent": "volume_down",
  "amount": 10
}
```

Isso já oferece informação concreta suficiente para entender o funcionamento da IA sem depender de raciocínio interno oculto.

---

# 9. Fluxo completo de um comando

```text
USER
 ↓
INPUT NORMALIZER
 ↓
CONTEXT RESOLVER
 ↓
ENTITY DETECTOR
 ↓
DOMAIN ROUTER
 ↓
INTENT ROUTER
 ↓
POLICY
 ↓
PLANNER
 ↓
EXECUTOR
 ↓
VERIFICATION
 ↓
MEMORY / EVENT UPDATE
 ↓
RESPONSE
```

Nem toda interação precisa atravessar todas as etapas.

O terminal deve mostrar apenas aquilo que realmente participou daquela interação.

---

# 10. Exemplo — comando rápido sem LLM

```text
[23:14:08.421] [VOICE]
> "abaixa um pouco"

[23:14:08.426] [CONTEXT]
  music.playing      = true
  active_device      = "PC_MAIN"

[23:14:08.431] [ROUTER]
  native_detector    = true
  contextual_match   = true
  llm_required       = false

[23:14:08.435] [INTENT]
  domain             = audio
  intent             = volume_down
  confidence         = 0.96

[23:14:08.439] [ACTION]
  executor           = audio_control
  command            = decrease_volume
  amount             = 10

[23:14:08.471] [EXECUTOR]
  success            = true
  latency            = 32 ms

[23:14:08.474] [VERIFY]
  state_changed      = true
  confirmed          = true
```

---

# 11. Exemplo — interação usando LLM

```text
[23:18:20.102] [USER]
> "qual era mesmo aquele negócio que a gente tava fazendo ontem?"

[23:18:20.107] [ROUTER]
  direct_intent      = none
  memory_required    = true
  llm_required       = true

[23:18:20.124] [MEMORY]
  query              = recent_project_context
  candidates         = 8
  selected           = 3

[23:18:20.130] [LLM]
  model              = qwen3
  context_tokens     = 2812

[23:18:20.791] [LLM]
  structured_result  = conversation_response
  latency            = 661 ms

[23:18:20.804] [RESPONSE]
  generated          = true
```

---

# 12. Detecção de inconsistências

Uma das funções mais úteis do DEV Console deve ser detectar automaticamente quando partes diferentes da Laylay discordam.

Exemplo:

```text
[23:21:44.201] [USER]
> "apaga troca ideia.txt"

[23:21:44.205] [ENTITY]
  value               = "troca ideia.txt"
  type                = FILE
  confidence          = 0.99

[23:21:44.209] [ROUTER]
  selected_domain     = notes
  intent              = delete_note
  confidence          = 0.72

[23:21:44.211] [DEV WARNING]
  possible domain conflict

  entity type         = FILE
  selected domain     = NOTES

  ⚠ FILE → NOTES mismatch
```

Isso permitiria identificar rapidamente erros sem precisar analisar centenas de linhas manualmente.

---

# 13. Personalidade da Laylay dentro do DEV Console

Os logs técnicos devem continuar sérios.

A personalidade aparece em uma categoria própria:

```text
[LAYLAY/DEV]
```

Essas mensagens devem ser ocasionais e nunca podem poluir o console.

A sensação deve ser de que a própria Laylay está olhando os bastidores junto com o desenvolvedor.

Exemplos:

```text
[LAYLAY/DEV]
ótimo. o chrome morreu de novo.
```

```text
[LAYLAY/DEV]
esse roteamento ficou suspeito.
```

```text
[LAYLAY/DEV]
hmm... eu não teria escolhido esse domínio.
```

```text
[LAYLAY/DEV]
não fui eu. o executor disse sucesso e não fez nada.
```

```text
[LAYLAY/DEV]
isso aqui tá com cara de contexto velho.
```

```text
[LAYLAY/DEV]
opa. achei uma coisa estranha.
```

```text
[LAYLAY/DEV]
acho que alguém esqueceu de confirmar isso aí.
```

```text
[LAYLAY/DEV]
não quero apontar dedos, mas foi o roteador.
```

Esses comentários podem aparecer principalmente em:

- erros;
- warnings;
- divergências;
- reconexões;
- falhas repetidas;
- falso sucesso;
- problemas de contexto;
- eventos estranhos;
- comportamento improvável.

---

# 14. “Laylay curiosa”

A personalidade visual dela também pode aparecer discretamente.

Possibilidades:

- mini avatar no canto superior;
- dois olhinhos surgindo na borda;
- pequeno sprite apoiado no terminal;
- Laylay aparecendo somente em eventos especiais;
- animação rápida quando surge uma mensagem `[LAYLAY/DEV]`.

Ela não deve ocupar espaço útil dos logs.

A ideia é parecer que ela está curiosa sobre o que o desenvolvedor está investigando.

Algo como se ela estivesse literalmente espiando a própria sala de máquinas.

---

# 15. Barra superior

Sugestão:

```text
LAYLAY // DEV CONSOLE
● LIVE

SYSTEM  IA  ROUTER  ACTIONS  MEMORY  DEVICES  NETWORK  PERF  ERRORS
```

Os itens podem funcionar como filtros rápidos.

---

# 16. Filtros

Filtros possíveis:

```text
ALL
SYSTEM
VOICE
IA
CONTEXT
ROUTER
ACTIONS
MEMORY
CHROME
TUYA
DEVICES
NETWORK
TESTS
PERF
WARNINGS
ERRORS
LAYLAY
```

Também pode existir busca textual:

```text
filter > "turn 151"
```

ou futuramente algo mais avançado:

```text
category:ROUTER turn:151
```

---

# 17. Barra inferior de telemetria

A barra inferior deve permanecer visível mesmo durante a rolagem.

Exemplo:

```text
CPU 08% | RAM 5.1 GB | VRAM 2.2 GB | EVENTS 21/s | LLM IDLE | WS ● | TUYA ●
```

Métricas possíveis:

```text
UPTIME
CPU
RAM
VRAM
LLM LATENCY
TOKENS/s
EVENTS/s
QUEUE
THREADS
WEBSOCKET
CHROME
TUYA
AGENTS
MEMORY DB
STT
TTS
```

Não é necessário mostrar tudo simultaneamente.

Essa barra pode ser configurável.

---

# 18. Estados do DEV Console

```text
● LIVE
● PAUSED
● TRACE
```

## LIVE

Mostra os eventos em tempo real.

É o modo padrão.

## PAUSED

Congela a visualização para análise.

A Laylay continua funcionando normalmente.

Exemplo:

```text
PAUSED — 143 new events
```

## TRACE

Acompanha somente uma interação específica.

Ideal para investigações.

---

# 19. Trace ID

Toda interação relevante pode receber um identificador:

```text
TRACE #18442
```

Todos os eventos relacionados recebem esse ID:

```text
[TRACE #18442][VOICE]
[TRACE #18442][CONTEXT]
[TRACE #18442][ROUTER]
[TRACE #18442][ACTION]
[TRACE #18442][VERIFY]
```

Assim, eventos paralelos não atrapalham a análise.

---

# 20. Comando `trace last`

```text
laylay.dev > trace last
```

Saída:

```text
════════════════ TRACE #18442 ════════════════

USER
"abre o youtube"

↓ 3 ms

ENTITY
youtube
type: SERVICE

↓ 2 ms

ROUTER
domain: browser
intent: open_url

↓ 1 ms

POLICY
allowed

↓ 18 ms

CHROME AGENT
OPEN_URL
success=true

↓ 7 ms

VERIFY
active_tab_changed
youtube.com

RESULT
✓ CONFIRMED

TOTAL
31 ms

═══════════════════════════════════════════════
```

---

# 21. Comando `trace turn`

Especialmente útil para os testes da Laylay.

```text
laylay.dev > trace turn 151
```

Saída:

```text
════════════════ TURN 151 TRACE ════════════════

USER
"apaga troca ideia.txt"

↓ 4 ms

ENTITY DETECTION

"troca ideia.txt"
type: FILE
confidence: 0.99

↓ 1 ms

DOMAIN ROUTER

files       0.38
notes       0.71   ← SELECTED
memory      0.08

⚠ domain/entity inconsistency

↓ 8 ms

ACTION
notes.delete

↓ 14 ms

RESULT
FAILED

════════════════════════════════════════════════
```

Esse comando deve ser uma das ferramentas principais para investigar testes RED.

---

# 22. Linha de comando

O terminal deve possuir sempre uma linha pronta:

```text
laylay.dev > █
```

O usuário não precisa utilizá-la.

Ela existe principalmente para inspeção manual e comandos de desenvolvimento.

---

# 23. Comandos previstos

```text
help

status
status all
status chrome
status tuya
status llm
status memory
status agents

trace last
trace turn <numero>
trace <id>
trace errors

events
events last <n>
events router
events errors

inspect memory <id>
inspect event <id>
inspect action <id>
inspect context

perf
perf llm
perf memory
perf actions

filter <categoria>
filter clear

pause
live
clear
```

---

# 24. Comando `status`

```text
laylay.dev > status
```

Saída:

```text
LAYLAY STATUS

core              ONLINE
llm               READY
memory            READY
chrome_agent      CONNECTED
tuya              CONNECTED
voice             LISTENING
tts               READY
event_bus         ONLINE

uptime            04:17:52
errors            0
warnings          2
```

---

# 25. `status chrome`

```text
laylay.dev > status chrome
```

```text
CHROME AGENT

state             CONNECTED
websocket         8765
active_tab        GitHub
active_url        github.com/...
tabs              7
last_event        active_tab_changed
latency           4 ms
```

---

# 26. `status tuya`

```text
laylay.dev > status tuya
```

```text
TUYA

state             CONNECTED
devices           2
online            2
offline           0

lampada_quarto    ONLINE
tomada_ventilador ONLINE

last_action       set_brightness
last_result       CONFIRMED
```

---

# 27. `inspect memory`

```text
laylay.dev > inspect memory 18492
```

```text
MEMORY #18492

type              conversation
created           2026-09-01 22:14:42
last_access       2026-09-01 23:03:11
importance        0.71
ttl               none

content:
"......"

relations:
#18411
#18431

source:
conversation
```

---

# 28. `perf`

```text
laylay.dev > perf
```

```text
PERFORMANCE

CPU               11%
RAM               5.2 GB
VRAM              2.1 GB

LLM latency       741 ms
STT latency       286 ms
TTS start         112 ms

events/sec        18
queue             2

actions avg       31 ms
memory query      8 ms
chrome agent      4 ms
```

---

# 29. Integração com testes

O DEV Console deve conversar diretamente com a infraestrutura de testes da Laylay.

Categorias:

```text
[TEST]
[REGRESSION]
[CHAOS]
[RED]
[PASS]
[FAIL]
[WARN]
```

Exemplo:

```text
[TEST][TURN 151]
status = FAIL

expected:
files.delete

received:
notes.delete

classification:
WRONG_DOMAIN
```

---

# 30. Teste de caos

Durante uma execução:

```text
[CHAOS]
turn 201/267
status=PASS

[CHAOS]
turn 202/267
status=FAIL
classification=FALSE_CONFIRMATION

[CHAOS]
turn 203/267
status=PASS
```

A barra inferior pode mudar para:

```text
CHAOS 203/267 | PASS 188 | FAIL 11 | WARN 4 | CRASH 0
```

---

# 31. Falha semântica

```text
[RED][SEMANTIC]

turn               151
expected_domain     files
received_domain     notes

expected_action     file.delete
received_action     note.delete

entity              troca ideia.txt
entity_type         FILE

classification      WRONG_DOMAIN
```

---

# 32. False confirmations

Uma ação não deve ser considerada realmente confirmada apenas porque o executor retornou `success=true`.

Exemplo:

```text
[VERIFY][WARNING]

action             file.open
executor_result    success
external_proof     missing
state_changed      unknown

classification:
UNVERIFIED_SUCCESS
```

A Laylay pode comentar:

```text
[LAYLAY/DEV]
não gostei desse "sucesso". ninguém confirmou nada.
```

---

# 33. Event Bus Inspector

Eventos internos podem ser exibidos em sequência:

```text
23:04:12.531  voice.transcription
               "abaixa um pouco"

23:04:12.548  context.music
               playing=true

23:04:12.561  intent.detected
               volume_down
               confidence=0.94

23:04:12.574  action.requested
               audio.volume_down

23:04:12.612  action.executed
               success=true
```

Comando:

```text
laylay.dev > events
```

ou:

```text
laylay.dev > events router
```

---

# 34. Logs estruturados

Internamente, os eventos devem idealmente existir em formato estruturado.

Exemplo:

```json
{
  "timestamp": "2026-09-01T23:04:12.612-03:00",
  "level": "INFO",
  "category": "EXECUTOR",
  "trace_id": "18442",
  "event": "action.executed",
  "action": "audio.volume_down",
  "success": true,
  "duration_ms": 38
}
```

O terminal transforma isso em algo legível:

```text
[23:04:12.612] [EXECUTOR]
  action       audio.volume_down
  success      true
  duration     38 ms
```

Isso permite:

- filtros;
- pesquisa;
- exportação;
- testes automáticos;
- análise posterior;
- dashboards futuros.

---

# 35. IDs importantes

Toda operação relevante pode possuir IDs.

Sugestões:

```text
trace_id
turn_id
request_id
action_id
event_id
memory_id
device_request_id
llm_request_id
```

Exemplo:

```text
trace_id=18442
action_id=A19383
llm_request_id=L22191
```

---

# 36. Logs de contexto

O console deve mostrar exatamente qual contexto estava disponível.

Exemplo:

```text
[CONTEXT]

active_app          Visual Studio Code
active_window       laylay2.5.py
music.playing       true
music.track         Tim Maia
chrome.active       GitHub
conversation_turn   18442
device_target       PC_MAIN
```

No TRACE, também pode mostrar a origem:

```text
active_app
  source=windows_runtime

music.playing
  source=music_state

chrome.active
  source=chrome_agent
```

---

# 37. Logs do roteador

```text
[ROUTER]

domain candidates:

audio              0.96
browser            0.08
system             0.03

selected:
audio

intent candidates:

volume_down        0.94
pause_music        0.21
next_track         0.04

selected:
volume_down
```

---

# 38. Logs de política

```text
[POLICY]

action             close_program
target             vscode

explicit_request   false
confirmation       missing

decision           BLOCK
reason             EXPLICIT_CONFIRMATION_REQUIRED
```

Esses logs ajudam a diferenciar:

- erro de interpretação;
- bloqueio correto;
- executor quebrado.

---

# 39. Logs de planejamento

Quando existir um plano de várias etapas:

```text
[PLANNER]

plan_id            P1842

steps:
1. OPEN_URL wikipedia
2. SEARCH python official documentation
3. OPEN_RESULT 1

dependencies:
2 requires 1
3 requires 2
```

Durante a execução:

```text
[PLAN][1/3] ✓
[PLAN][2/3] ✓
[PLAN][3/3] ✓
```

---

# 40. Logs do executor

```text
[EXECUTOR]

executor           chrome_agent
action             OPEN_URL

arguments:
url                https://...

started            23:14:09.120
finished           23:14:09.181

duration           61 ms
returned           success
```

---

# 41. Logs de verificação

Sempre que possível, sucesso declarado e sucesso comprovado devem ser separados.

Exemplo:

```text
[EXECUTOR]
returned_success = true

[VERIFY]
external_signal   = active_tab_changed
target_match      = true

confirmed         = true
```

Sem prova:

```text
[VERIFY]
external_signal   = none

confirmed         = false
status            = UNVERIFIED
```

---

# 42. Logs de memória

```text
[MEMORY]

operation          search
query              "playlist rock"

candidates         12
selected           3
duration           7 ms
```

Em TRACE:

```text
candidate #128     score=0.91
candidate #331     score=0.83
candidate #299     score=0.77
```

---

# 43. Logs de dispositivos

```text
[DEVICE][TUYA]

device             lampada_quarto
state              online
request            set_brightness
value              40
latency            21 ms
confirmed          true
```

---

# 44. Logs de rede e agentes

Pensando na arquitetura futura da Laylay com outros PCs:

```text
[AGENT]

device             PC_B
connection         cloud
state              ONLINE
latency            37 ms
last_seen          now
```

Ações remotas:

```text
[AGENT][PC_B]

command            open_program
target             vscode

sent               ✓
received           ✓
executed           ✓
confirmed          ✓
```

---

# 45. Pausar sem parar a Laylay

`PAUSED` congela apenas a visualização.

A Laylay continua operando normalmente.

```text
● PAUSED
143 new events
```

Isso permite investigar uma sequência sem perder o estado real da assistente.

---

# 46. Rolagem inteligente

Em LIVE:

- auto-scroll acompanha as novas linhas.

Se o usuário rolar para cima:

- o auto-scroll pausa;
- aparece:

```text
↓ 87 new events
```

Ao clicar, volta para o final.

---

# 47. Pesquisa

Busca simples:

```text
search > file_delete
```

Pode encontrar:

- logs;
- trace IDs;
- actions;
- errors;
- turns.

Filtros combinados futuramente:

```text
category:ROUTER turn:151
```

---

# 48. Exportar trace

Um trace deve poder ser exportado em:

- texto;
- Markdown;
- JSON.

Exemplo:

```text
laylay.dev > export trace 18442 markdown
```

Isso ajuda muito ao enviar resultados para análise.

---

# 49. Persistência dos logs

Nem todo evento precisa ficar salvo para sempre.

Sugestão:

- buffer em memória para eventos recentes;
- arquivos rotativos para logs técnicos;
- traces importantes salvos separadamente;
- erros críticos mantidos por mais tempo;
- testes salvando os próprios traces.

---

# 50. Performance do próprio DEV Console

O sistema de observabilidade não pode se tornar a causa dos problemas.

Princípios:

- logging assíncrono quando possível;
- filas limitadas;
- rotação de arquivos;
- evitar serialização pesada em NORMAL;
- TRACE/INSANE ativados sob demanda;
- UI não bloquear execução;
- console suportar rajadas de eventos.

---

# 51. Separação entre observação e controle

Pode existir uma divisão conceitual:

```text
MONITOR
CONTROL
```

## Monitor

Somente leitura.

Permite:

- observar;
- filtrar;
- pesquisar;
- pausar;
- inspecionar.

## Control

Permite ações mais sensíveis:

- reexecutar ação;
- simular evento;
- editar memória;
- alterar estado;
- forçar reconexão;
- enviar comando manual.

Essa separação evita modificar a Laylay acidentalmente quando o objetivo era apenas observar.

---

# 52. Prioridade de implementação

## Fase 1 — núcleo

- terminal preto;
- logs em tempo real;
- categorias;
- timestamps;
- barra inferior;
- `laylay.dev >`;
- filtros básicos;
- LIVE / PAUSED;
- NORMAL / DEBUG / TRACE;
- trace ID;
- logs de router/action/verify;
- comentários `[LAYLAY/DEV]`.

## Fase 2 — inspeção

- `trace last`;
- `trace turn`;
- `status`;
- `events`;
- `perf`;
- busca;
- inspect;
- integração com testes.

## Fase 3 — telemetria profunda

- INSANE;
- Event Bus completo;
- Memory Inspector;
- agents;
- devices;
- export de trace;
- profiler;
- análise automática de inconsistências.

---

# 53. Princípios de implementação

## 53.1 Logs estruturados

Evitar depender apenas de:

```python
print("alguma coisa")
```

Preferir eventos com campos consistentes:

```text
timestamp
level
category
event
trace_id
message
data
duration
source
```

---

## 53.2 Todo comando deve ser rastreável

Ideal:

```text
entrada
→ trace_id
→ ações
→ eventos
→ resultado
```

---

## 53.3 A interface deve consumir eventos padronizados

A UI do DEV Console não deve conhecer profundamente cada módulo interno.

Ela recebe eventos já normalizados.

Assim, mudanças na arquitetura da Laylay não obrigam reescrever toda a interface.

---

## 53.4 Diferenciar estados reais

```text
EXECUTED
CONFIRMED
UNVERIFIED
FAILED
BLOCKED
```

---

## 53.5 Warnings semânticos

O sistema de observabilidade pode detectar padrões problemáticos automaticamente:

```text
ENTITY_DOMAIN_MISMATCH
UNVERIFIED_SUCCESS
CONTEXT_STALE
LOW_CONFIDENCE_ACTION
FALLBACK_LOOP
DUPLICATE_ACTION
DEVICE_STATE_CONFLICT
MEMORY_CONFLICT
```

---

# 54. Exemplo de sessão completa

```text
╔══════════════════════════════════════════════════════════════════════════════╗
║  LAYLAY // DEV CONSOLE                                      ● LIVE         ║
╚══════════════════════════════════════════════════════════════════════════════╝

[23:40:18.001] [VOICE]
> "apaga troca ideia.txt"

[23:40:18.005] [INPUT]
  normalized="apaga troca ideia.txt"

[23:40:18.009] [ENTITY]
  value="troca ideia.txt"
  type=FILE
  confidence=0.99

[23:40:18.012] [CONTEXT]
  active_app="Visual Studio Code"
  cwd="C:\\projeto-laylay"

[23:40:18.017] [ROUTER]

  files.delete      0.38
  notes.delete      0.71  ← SELECTED
  memory.delete     0.08

[23:40:18.019] [WARNING]
  ENTITY_DOMAIN_MISMATCH
  FILE → NOTES

[23:40:18.021] [LAYLAY/DEV]
  esse roteamento ficou suspeito.

[23:40:18.029] [POLICY]
  confirmation_required=true

[23:40:18.031] [ACTION]
  note.delete
  target="troca ideia.txt"

[23:40:18.044] [EXECUTOR]
  success=false

[23:40:18.047] [VERIFY]
  confirmed=false

[23:40:18.050] [ERROR]
  action failed
  classification=WRONG_DOMAIN

──────────────────────────────────────────────────────────────────────────────
CPU 09% | RAM 5.0GB | VRAM 2.1GB | TRACE #19021 | ERR 1 | WS ● | TUYA ●
──────────────────────────────────────────────────────────────────────────────

laylay.dev > trace last

════════════════ TRACE #19021 ════════════════

ENTITY
FILE ✓

DOMAIN
NOTES ✗

CAUSE
probable router misclassification

FIRST DIVERGENCE
DOMAIN_ROUTER

═══════════════════════════════════════════════

[LAYLAY/DEV]
achei. eu desviei no roteador.

laylay.dev > █
```

---

# 55. Resultado desejado

Quando estiver pronto, o DEV Console deve passar a sensação de que o desenvolvedor abriu a parede da Laylay e entrou na parte técnica dela.

Ele precisa ser:

- útil;
- rápido;
- técnico;
- legível;
- rastreável;
- profundamente integrado à arquitetura;
- divertido o suficiente para ainda parecer a Laylay.

A personalidade não deve competir com o diagnóstico.

Ela apenas aparece ocasionalmente, curiosa, irônica ou desconfiada, como se estivesse acompanhando a investigação junto com o desenvolvedor.

---

# 56. Frase que resume o conceito

> **O resto da interface é onde você conversa com a Laylay.  
> O DEV Console é onde você entra atrás da parede e vê a Laylay funcionando.**

---

# 57. Nome sugerido

Nome principal:

```text
LAYLAY // DEV CONSOLE
```

Prompt:

```text
laylay.dev >
```

Possíveis nomes internos:

```text
dev_console
developer_console
laylay_dev_terminal
observability_console
engine_room
```

`engine_room` pode funcionar muito bem como codinome interno porque representa literalmente a “sala de máquinas” da Laylay.

---

# 58. Status do conceito

**Status:** ideia aprovada / conceito definido.

A implementação deve preservar principalmente:

1. visual de terminal preto estilo CMD;
2. telemetria e logs avançados como função principal;
3. linha de comando secundária;
4. rastreamento completo de interações;
5. níveis NORMAL / DEBUG / TRACE / INSANE;
6. LIVE / PAUSED / TRACE;
7. integração com testes RED e caos;
8. distinção entre execução e confirmação real;
9. observação das decisões estruturadas da IA;
10. presença ocasional da personalidade da Laylay por `[LAYLAY/DEV]`;
11. sensação de estar vendo os bastidores da assistente em funcionamento;
12. Laylay aparecendo de forma curiosa e discreta no próprio terminal;
13. capacidade de descobrir rapidamente o primeiro ponto onde uma execução desviou do comportamento esperado.
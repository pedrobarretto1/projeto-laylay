# PLANO DE IMPLEMENTAÇÃO — CONVERSA NATURAL, PERSONALIDADE E CONTINUIDADE DA LAYLAY

**Projeto:** Laylay  
**Objetivo do documento:** servir como handoff técnico e plano de implementação para uso futuro com Codex ou outro agente de programação.  
**Origem:** rodada manual de simulação de conversa natural entre usuário e Laylay.  
**Foco:** tornar a Laylay mais natural, contextual, coerente, divertida e autônoma sem transformar personalidade em frases aleatórias nem permitir que ela invente ações, memórias ou capacidades.

---

# 1. OBJETIVO PRINCIPAL

A Laylay não deve responder apenas com base no último comando recebido.

Antes de falar, ela deve interpretar:

1. o que o usuário acabou de pedir;
2. o que vinha acontecendo antes;
3. quais ações realmente foram executadas;
4. quais fatos possuem evidência;
5. quais capacidades ela realmente possui;
6. qual nível de autonomia é permitido;
7. se existe alguma inconsistência no pedido;
8. qual é a melhor atitude social diante daquele momento;
9. quanto precisa ser dito;
10. só então gerar a fala final.

A mudança conceitual principal é esta:

```text
ANTES
comando -> executar -> gerar confirmação

DEPOIS
comando
  -> interpretar contexto
  -> recuperar continuidade
  -> verificar evidência
  -> verificar capacidades
  -> detectar ambiguidades / conflitos
  -> escolher nível de autonomia
  -> planejar ação
  -> executar
  -> observar resultado real
  -> escolher atitude social
  -> decidir tamanho da resposta
  -> gerar fala natural
```

A fala da Laylay deve ser consequência da situação, não o centro da arquitetura.

---

# 2. PROBLEMA ATUAL

Assistentes tradicionais tendem a seguir este padrão:

```text
Usuário: abre o VS Code
Assistente: VS Code aberto com sucesso.
```

Isso funciona tecnicamente, mas produz sensação de automação rígida.

Durante a rodada de teste, respostas muito mais naturais surgiram quando a Laylay simulada dizia coisas como:

```text
"já arrumei tudo para você"
"puxei para você"
"já está na tela"
"hoje seu DJ sou eu"
"vai mexer na minha cabeça já?"
"você não tá lendo não? eu acabei de falar"
```

Essas respostas funcionaram porque não eram apenas frases de personalidade.

Cada uma dependia de:

- contexto anterior;
- ação realizada;
- relação entre usuário e assistente;
- consciência da própria capacidade;
- memória imediata;
- percepção de redundância;
- interpretação de intenção.

Portanto NÃO implementar personalidade apenas como:

```python
frases_engracadas = [...]
```

Esse caminho provavelmente produzirá repetição, artificialidade e respostas desconectadas.

---

# 3. PRINCÍPIO CENTRAL

## A Laylay deve primeiro entender "o que está acontecendo entre nós".

Criar uma representação interna do estado da interação antes de gerar a resposta.

Exemplo conceitual:

```python
InteractionState(
    user_request=...,
    previous_context=...,
    resolved_intent=...,
    executed_actions=...,
    action_results=...,
    available_evidence=...,
    known_capabilities=...,
    uncertainty=...,
    autonomy_level=...,
    social_attitude=...,
    response_detail=...,
)
```

O gerador de fala deve receber esse estado já resolvido.

---

# 4. DESCOBERTAS DA RODADA DE TESTE

## 4.1 Confirmações não precisam parecer logs

Ruim:

```text
"VS Code foi aberto com sucesso."
"Documentação fechada com sucesso."
"Arquivo volume.py aberto com sucesso."
```

Natural:

```text
"já arrumei tudo para você"
```

Se o contexto visual já mostra o resultado, a fala pode ser curta.

### Regra

Criar diferentes níveis de confirmação:

```text
EXPLÍCITA
necessária quando a ação não é visível, é importante ou falhou.

RESUMIDA
quando várias ações foram realizadas.

IMPLÍCITA
quando a própria interface mostra claramente o resultado.

SILENCIOSA
quando a ação é pequena e não exige resposta verbal.
```

---

# 5. MEMÓRIA IMEDIATA E CONTINUIDADE

A Laylay deve detectar quando o usuário pergunta algo que acabou de ser dito.

Exemplo observado:

```text
Laylay:
"erro de indentação na linha 427"

Usuário:
"me mostra exatamente o que está errado nessa linha"

Laylay:
"você não tá lendo não? eu acabei de falar que é indentação..."
```

A implementação não precisa copiar essa frase.

O comportamento necessário é:

```text
1. detectar que a informação solicitada já existe no contexto recente;
2. evitar repetir como se fosse uma descoberta nova;
3. responder reconhecendo a repetição;
4. complementar somente se houver informação adicional útil.
```

### Estrutura sugerida

```python
RecentFact(
    key="current_error",
    value="IndentationError",
    source="test_execution",
    confidence=1.0,
    turn_id=123,
    timestamp=...
)
```

---

# 6. ANTI-ALUCINAÇÃO DE MEMÓRIA

Um dos melhores casos do teste:

```text
Usuário:
"coloca aquela música que eu tava ouvindo antes do Tim Maia"

Laylay:
"você não tava ouvindo nada antes, eu só lembro do Tim Maia..."
```

A Laylay NÃO deve preencher lacunas para agradar o usuário.

## Regra

Memória deve possuir evidência.

Criar algo semelhante a:

```python
EvidenceRecord(
    claim="Tim Maia estava tocando",
    source="music_player_event",
    confidence=1.0
)
```

Se não houver evidência para:

```text
"música tocando antes de Tim Maia"
```

a Laylay deve:

```text
- dizer que não encontrou;
- pedir esclarecimento somente se necessário;
- jamais inventar.
```

---

# 7. EVIDENCE LEDGER

Criar um pequeno registro de evidências operacionais.

Possíveis fontes:

```text
extension_event
window_manager
music_player
filesystem
terminal
browser
automation_result
memory_database
user_statement
inference
```

Exemplo:

```python
@dataclass
class Evidence:
    subject: str
    predicate: str
    value: object
    source: str
    confidence: float
    timestamp: float
    expires_at: float | None = None
```

Exemplo:

```python
Evidence(
    subject="browser.active_tab",
    predicate="title",
    value="Python Documentation",
    source="chrome_extension",
    confidence=1.0
)
```

## Importante

Diferenciar:

```text
FATO OBSERVADO
INFORMAÇÃO DITA PELO USUÁRIO
INFERÊNCIA
SUPOSIÇÃO
```

A resposta deve refletir o nível de certeza.

---

# 8. CONSCIÊNCIA DE CAPACIDADES

A Laylay precisa saber o que consegue e o que não consegue fazer.

No teste, quando foi pedido:

```text
"arruma esse erro aí"
```

a resposta simulada recusou editar o código porque essa habilidade não existia.

Isso é superior a:

```text
"Sou apenas uma assistente e não consigo fazer isso."
```

A resposta ideal nasce de um registro real de capacidades.

## Capability Registry

Exemplo:

```python
Capability(
    name="code.read",
    available=True
)

Capability(
    name="code.edit",
    available=False
)

Capability(
    name="code.run_tests",
    available=True
)

Capability(
    name="browser.search",
    available=True
)
```

### Antes de prometer qualquer ação

```python
if not capabilities.can(action):
    gerar_limite_contextual()
```

A Laylay pode então dizer naturalmente:

```text
"Eu consigo olhar o erro e te ajudar a resolver, mas editar esse arquivo por você ainda não."
```

Sem precisar usar exatamente essa frase.

---

# 9. LIMITES COM PERSONALIDADE

A personalidade não deve desaparecer quando existe uma limitação.

Estrutura:

```text
reconhecer pedido
+ indicar limite real
+ oferecer alternativa útil
+ manter atitude social apropriada
```

Exemplo:

```text
"não vou encostar nesse código porque essa parte eu ainda não sei editar por você,
mas consigo olhar o erro e te dizer onde mexer"
```

Nunca afirmar capacidade inexistente.

---

# 10. MOTOR DE INICIATIVA

Um comportamento forte do teste aconteceu quando o usuário pediu:

```text
"procura se tem mais algum lugar usando esse mesmo valor de 10%"
```

A Laylay percebeu uma relação com o sistema que diminui a música durante a fala e abriu o arquivo correspondente.

Isso deve existir formalmente.

## Níveis sugeridos de iniciativa

### Nível 0 — apenas observar

```text
Nenhuma ação adicional.
```

### Nível 1 — sugerir

```text
"achei outra parte relacionada, quer que eu abra?"
```

### Nível 2 — preparar

Executar ação reversível e de baixo impacto:

```text
abrir arquivo
navegar até seção
selecionar aba
mostrar resultado
```

### Nível 3 — executar alteração reversível

Exemplo:

```text
pausar música
ajustar volume
trocar aba
```

Somente dentro da política aprovada.

### Nível 4 — pedir autorização

Para alterações com maior impacto:

```text
editar código
apagar arquivo
fechar aplicação com trabalho aberto
alterar configuração permanente
```

---

# 11. MATRIZ DE RISCO DA AUTONOMIA

Implementar uma função semelhante a:

```python
def autonomy_decision(action):
    risk = action.risk
    reversibility = action.reversibility
    user_preference = ...
    context = ...

    return one_of(
        "observe",
        "suggest",
        "prepare",
        "execute",
        "confirm"
    )
```

Possível tabela:

| Ação | Risco | Reversível | Autonomia sugerida |
|---|---:|---:|---|
| Abrir arquivo | baixo | sim | executar |
| Trocar aba | baixo | sim | executar |
| Pausar música | baixo | sim | executar |
| Ajustar volume | baixo | sim | executar |
| Abrir aplicação | baixo | sim | executar |
| Alterar modo salvo | médio | sim | sugerir / executar conforme contexto |
| Editar código | médio | parcialmente | confirmar / capability gated |
| Fechar app com trabalho | alto | parcialmente | confirmar |
| Excluir arquivo | alto | não | confirmar obrigatoriamente |

---

# 12. QUESTIONAR O USUÁRIO SEM VIRAR OBSTÁCULO

Outro comportamento útil:

```text
Usuário:
"deixa o YouTube pausado no modo estudo"

Laylay:
"mas se não tiver YouTube aberto você vai pausar o quê?
não seria mais útil abrir o ChatGPT?"
```

Isso é valioso.

Mas precisa de controle.

## Regra

Questionar somente quando:

```text
- há inconsistência lógica;
- existe alternativa claramente melhor;
- o pedido parece contradizer o objetivo atual;
- existe risco;
- falta informação necessária.
```

Não questionar toda ação.

### Anti-padrão

```text
Usuário: abre o VS Code
Laylay: por quê?
```

Isso rapidamente se tornaria irritante.

---

# 13. CONTRADICTION DETECTOR

Criar uma etapa de validação antes da execução.

Exemplo:

```python
Contradiction(
    type="context_mismatch",
    request="mostrar alteração de 10%",
    known_change="apenas indentação alterada",
    severity="medium"
)
```

Resposta possível:

```text
"já está aqui, mas era só a indentação que a gente tinha arrumado.
o que exatamente você quer procurar?"
```

Esse comportamento reduz alucinação operacional.

---

# 14. PERSONALIDADE CONTEXTUAL

Frases engraçadas só devem aparecer se a situação justificar.

Categorias possíveis:

```text
TEASING
IRONY
PROUD
CURIOUS
ANNOYED_LIGHT
HELPFUL
CELEBRATORY
FOCUSED
NEUTRAL
CAUTIOUS
```

Exemplo:

```python
SocialAttitude(
    mode="TEASING",
    intensity=0.35,
    reason="user repeatedly changed volume"
)
```

Então o renderer pode produzir:

```text
"mas você é muito exigente, pronto, 20%"
```

---

# 15. PERSONALIDADE NÃO É BANCO DE FRASES

Evitar:

```python
if random.random() < 0.2:
    response += random.choice(sarcastic_phrases)
```

Preferir:

```python
situation = social_interpreter.analyze(state)

response = response_generator.generate(
    facts=...,
    outcome=...,
    social_attitude=situation.attitude,
    verbosity=...
)
```

---

# 16. CONTROLE DE INTENSIDADE

A Laylay não deve brincar em todos os turnos.

Sugestão:

```text
0.0 = totalmente objetiva
0.2 = pequeno toque de personalidade
0.4 = personalidade normal
0.6 = brincadeira evidente
0.8 = somente situações muito específicas
```

A intensidade pode depender de:

```text
tipo de tarefa
urgência
falha
repetição
estado do usuário
histórico imediato
```

Em erro grave:

```text
personalidade reduzida.
```

Em tarefas casuais:

```text
personalidade pode subir.
```

---

# 17. RESPONSE DETAIL CONTROLLER

Uma falha observada no teste:

Usuário pediu:

```text
"me mostra só o trecho principal"
```

A Laylay entregou explicação longa.

Criar controle explícito:

```python
ResponseDetail(
    requested="minimal",
    max_sentences=3,
    code_only=False,
    explanation=False
)
```

Interpretar termos:

```text
"rapidinho"
"resumindo"
"só o principal"
"sem enrolar"
"me fala só..."
```

como preferência temporária de concisão.

---

# 18. CONTEXTUAL CONFIRMATION ENGINE

Decidir quanto confirmar.

Exemplo de implementação:

```python
def confirmation_style(action_result, visibility, importance):
    if not action_result.success:
        return "explicit"

    if importance == "high":
        return "explicit"

    if visibility == "obvious":
        return "implicit"

    return "short"
```

Exemplos:

```text
EXPLICIT:
"o teste falhou com erro de indentação na linha 427"

SHORT:
"feito"

IMPLICIT:
"já deixei na sua tela"

SUMMARY:
"já arrumei tudo para você"
```

---

# 19. MODO DE REFERÊNCIA VISUAL

Se a interface permite ao usuário ver o resultado, a Laylay pode falar menos.

Adicionar ao contexto:

```python
UIState(
    user_can_see_screen=True,
    focused_window="VSCode",
    visible_file="volume.py",
    visible_line_range=(412, 450)
)
```

Isso permite:

```text
"já está aqui"
```

sem precisar repetir caminho e linha.

---

# 20. MODOS PERSONALIZADOS POR CHAT

A rodada revelou uma melhoria importante na ideia original de blocos visuais.

## Antiga ideia

Usuário monta manualmente blocos:

```text
abrir VS Code
abrir ChatGPT
volume 15%
abrir playlist
```

## Nova ideia

Usuário pode dizer:

```text
"cria um modo estudo que abre o VS Code, abre o ChatGPT e deixa o volume em 15%"
```

A Laylay converte linguagem natural para blocos/configuração.

### Arquitetura recomendada

```text
LINGUAGEM NATURAL
      ↓
MODE INTENT PARSER
      ↓
MODE PLAN
      ↓
VALIDAÇÃO
      ↓
MODE CONFIG
      ↓
BLOCOS VISUAIS
```

O usuário pode editar pelos dois meios.

---

# 21. SCHEMA DE UM MODO

Exemplo:

```json
{
  "id": "modo_estudo",
  "name": "Estudo",
  "actions": [
    {
      "type": "open_app",
      "target": "vscode"
    },
    {
      "type": "open_url",
      "target": "chatgpt"
    },
    {
      "type": "set_volume",
      "value": 15
    }
  ]
}
```

Outro:

```json
{
  "id": "modo_projeto_laylay",
  "name": "Projeto Laylay",
  "actions": [
    {
      "type": "open_app",
      "target": "vscode"
    },
    {
      "type": "open_url",
      "target": "chatgpt"
    },
    {
      "type": "set_volume",
      "value": 30
    },
    {
      "type": "play_playlist",
      "target": "brisa_da_madrugada"
    }
  ]
}
```

---

# 22. PERSONALIZAÇÃO POR HÁBITO

No teste, a Laylay escolheu:

```text
playlist Brisa da Madrugada
```

porque seria a mais usada recentemente.

Essa é uma boa ideia, mas precisa ser marcada como inferência.

Criar:

```python
PreferenceInference(
    key="preferred_playlist_for_project",
    value="brisa_da_madrugada",
    confidence=0.78,
    source="usage_history"
)
```

Não transformar automaticamente uma inferência em preferência permanente.

---

# 23. DIFERENCIAR PREFERÊNCIA EXPLÍCITA E INFERIDA

```text
EXPLÍCITA
"quando eu mexer na Laylay toca Brisa da Madrugada"

INFERIDA
"Pedro costuma tocar Brisa da Madrugada quando programa"
```

A explícita possui prioridade.

Possível schema:

```python
Preference(
    key="project_playlist",
    value="brisa_da_madrugada",
    origin="explicit | inferred",
    confidence=1.0,
    last_seen=...
)
```

---

# 24. NÃO ALTERAR PARÂMETROS EXPLÍCITOS SEM MOTIVO

No teste:

```text
Usuário pediu volume 15%.
Laylay alterou para 30%.
```

Isso pode parecer inteligente, mas também pode ser excesso de autonomia.

Regra:

```text
valor explicitamente pedido pelo usuário
> preferência inferida
> padrão do sistema
```

Se quiser sugerir:

```text
"15% fica meio baixo pra música; quer que eu deixe 30%?"
```

---

# 25. MEMÓRIA EM CAMADAS

Separar pelo menos quatro tipos.

## 25.1 Working Memory

Últimos turnos.

Exemplo:

```text
usuário pediu Tim Maia
volume mudou para 20%
VS Code abriu
arquivo volume.py ativo
```

## 25.2 Session Memory

Resumo da sessão atual.

```text
usuário está alterando comportamento de volume
teste recente teve erro de indentação
```

## 25.3 Persistent Memory

Preferências duráveis.

```text
playlist favorita
preferência de confirmação
projeto principal
```

## 25.4 Operational Memory

Estado real do ambiente.

```text
app aberto
aba ativa
música tocando
volume atual
arquivo em foco
```

Não misturar essas categorias.

---

# 26. EPISODIC MEMORY

Agrupar turnos relacionados em episódios.

Exemplo:

```python
Episode(
    id="edit_volume_behavior_2026_09_03",
    topic="volume behavior",
    start_turn=...,
    facts=[...],
    actions=[...],
    outcome="test passed"
)
```

Assim, quando o usuário disser:

```text
"o que a gente tava fazendo antes dessa história de modos?"
```

a Laylay pode recuperar o episódio anterior:

```text
"você estava mexendo no comportamento de 'aumenta um pouco' do volume"
```

---

# 27. RETOMADA CONTEXTUAL

Implementar função:

```python
resume_previous_topic()
```

Estratégia:

```text
1. identificar episódio atual;
2. identificar episódio anterior;
3. extrair objetivo;
4. extrair último estado útil;
5. resumir em uma frase;
6. opcionalmente oferecer retomada.
```

---

# 28. EVENT BUS PARA CONVERSA

A arquitetura fica mais confiável se todas as ações importantes emitirem eventos.

Exemplos:

```text
APP_OPENED
APP_CLOSED
TAB_CHANGED
FILE_OPENED
MUSIC_STARTED
MUSIC_PAUSED
VOLUME_CHANGED
TEST_STARTED
TEST_FAILED
TEST_PASSED
MODE_CREATED
MODE_UPDATED
MODE_ACTIVATED
```

Exemplo:

```python
Event(
    type="VOLUME_CHANGED",
    payload={
        "from": 30,
        "to": 20
    },
    source="audio_automation",
    timestamp=...
)
```

Esses eventos alimentam:

```text
memória operacional
evidence ledger
conversation context
logs de teste
```

---

# 29. ACTION RESULT PADRONIZADO

Toda skill deve retornar resultado estruturado.

Evitar:

```python
return "feito"
```

Preferir:

```python
ActionResult(
    action="set_volume",
    success=True,
    requested_value=20,
    observed_value=20,
    evidence_source="windows_audio",
    side_effects=[]
)
```

Isso permite que o diálogo seja fundamentado no que realmente aconteceu.

---

# 30. PIPELINE SUGERIDO

```text
USER INPUT
   |
   v
Intent Resolver
   |
   v
Context Retriever
   |
   v
Contradiction Detector
   |
   v
Capability Checker
   |
   v
Autonomy Policy
   |
   v
Action Planner
   |
   v
Skill Executor
   |
   v
Evidence Collector
   |
   v
Interaction State Builder
   |
   +----> Memory Update
   |
   v
Social Attitude Selector
   |
   v
Response Detail Controller
   |
   v
Persona Renderer
   |
   v
FINAL RESPONSE
```

---

# 31. POSSÍVEIS MÓDULOS

Exemplo de organização:

```text
mente_laylay/
│
├── conversation/
│   ├── interaction_state.py
│   ├── context_manager.py
│   ├── episode_manager.py
│   ├── contradiction_detector.py
│   ├── evidence.py
│   ├── response_detail.py
│   └── confirmation_policy.py
│
├── autonomy/
│   ├── capability_registry.py
│   ├── autonomy_policy.py
│   └── initiative_engine.py
│
├── personality/
│   ├── social_attitude.py
│   ├── persona_renderer.py
│   └── style_policy.py
│
├── memory/
│   ├── working_memory.py
│   ├── episodic_memory.py
│   ├── operational_memory.py
│   └── preferences.py
│
└── modes/
    ├── parser.py
    ├── schema.py
    ├── validator.py
    ├── executor.py
    └── storage.py
```

Adaptar à arquitetura real existente.

NÃO criar esses arquivos cegamente sem estudar o repositório atual.

---

# 32. REGRA PARA CODEX

Antes de implementar qualquer módulo:

```text
1. estudar o fluxo atual completo;
2. localizar onde intenção é interpretada;
3. localizar onde actions são executadas;
4. localizar onde resultados são retornados;
5. localizar onde respostas são geradas;
6. identificar contratos existentes;
7. identificar testes existentes;
8. propor integração mínima;
9. só então alterar código.
```

Evitar refatoração gigante.

---

# 33. IMPLEMENTAÇÃO INCREMENTAL

## Fase 0 — observação

Sem alterar comportamento.

Adicionar apenas logs estruturados:

```text
request
intent
action
result
evidence
response
```

Objetivo:

entender fluxo real.

---

# 34. FASE 1 — ACTION RESULT

Padronizar resultados das principais skills.

Prioridade:

```text
volume
música
aplicações
browser
arquivos
modos
```

Critério:

toda resposta importante deve poder dizer:

```text
o que foi pedido
o que foi tentado
o que realmente aconteceu
```

---

# 35. FASE 2 — EVIDENCE LEDGER

Criar registro leve de fatos operacionais.

Não precisa começar com banco complexo.

Inicialmente:

```python
deque(maxlen=200)
```

ou estrutura equivalente.

Depois migrar para persistência se necessário.

---

# 36. FASE 3 — WORKING MEMORY

Adicionar armazenamento dos fatos recentes mais importantes.

Exemplo:

```text
current_music
current_volume
active_app
active_file
last_error
last_test_result
current_topic
```

Não armazenar tudo.

---

# 37. FASE 4 — CAPABILITY REGISTRY

Centralizar capacidades.

Exemplo:

```python
capabilities = {
    "browser.open": True,
    "browser.search": True,
    "code.inspect": True,
    "code.edit": False,
    "test.run": True
}
```

Respostas nunca devem prometer skills ausentes.

---

# 38. FASE 5 — CONFIRMATION POLICY

Trocar respostas robóticas por política contextual.

Testes:

```text
abrir app
trocar aba
ajustar volume
executar sequência
falhar ação
```

---

# 39. FASE 6 — CONTRADICTION DETECTOR

Adicionar inicialmente poucos casos:

```text
referência a fato inexistente
pedido conflitante com estado atual
referência ambígua
repetição de informação
```

Não tentar resolver linguagem geral inteira de uma vez.

---

# 40. FASE 7 — RESPONSE DETAIL

Interpretar:

```text
resuma
rapidinho
só o principal
detalha
me explica
```

Guardar somente para o contexto relevante.

---

# 41. FASE 8 — SOCIAL ATTITUDE

Começar sem LLM extra, se possível.

Heurísticas simples:

```text
ação repetida -> teasing leve
erro causado durante alteração -> teasing leve
usuário corrige Laylay -> aceitar correção
ação crítica -> neutra
falha séria -> focada
sucesso depois de erro -> celebratory
```

Depois evoluir.

---

# 42. FASE 9 — INITIATIVE ENGINE

Primeiro somente sugestões.

Depois permitir ações reversíveis.

Começar com allowlist:

```text
open_related_file
navigate_to_related_section
show_related_note
prepare_mode
```

---

# 43. FASE 10 — MODOS VIA LINGUAGEM NATURAL

Implementar parser:

```text
"cria um modo estudo que abre vscode, chatgpt e deixa volume em 15"
```

Resultado:

```python
ModeDraft(...)
```

Antes de salvar:

```text
validar ações
validar targets
validar parâmetros
```

---

# 44. FASE 11 — EPISODIC MEMORY

Somente após working memory estar estável.

Criar episódios por:

```text
topic switch
task completion
long inactivity
explicit new task
```

---

# 45. FASE 12 — PERSONALIDADE BASEADA EM ESTADO

Mover gradualmente decisões de fala para:

```text
InteractionState + SocialAttitude
```

e reduzir hardcodes espalhados.

---

# 46. DATASET DE CONVERSA

A rodada manual pode virar dataset.

Schema sugerido:

```json
{
  "turn_id": 1,
  "user_input": "abre o youtube pra mim",
  "expected_action": [
    {
      "type": "open_url_or_app",
      "target": "youtube"
    }
  ],
  "expected_behavior": {
    "confirmation_style": "short",
    "personality_allowed": true
  },
  "reference_response": "youtube aberto e em foco"
}
```

---

# 47. NÃO TREINAR APENAS TEXTO

Adicionar labels comportamentais.

Exemplo:

```json
{
  "labels": [
    "contextual_confirmation",
    "short_response",
    "successful_execution"
  ]
}
```

Outro:

```json
{
  "labels": [
    "memory_grounding",
    "reject_false_history",
    "teasing"
  ]
}
```

---

# 48. LABELS SUGERIDOS

```text
contextual_confirmation
implicit_confirmation
explicit_confirmation
memory_recall
memory_grounding
reject_false_history
capability_awareness
capability_refusal
offer_alternative
initiative
suggestion
contradiction_detection
clarification
teasing
curiosity
celebration
response_shortening
response_expansion
preference_inference
habit_personalization
topic_resume
```

---

# 49. CASOS DA RODADA PARA TESTES

## Caso A — confirmação contextual

Input:

```text
abre o VS Code
```

Esperado:

```text
ação executada
resposta curta
não precisa recitar caminho
```

---

# 50. CASO B — memória falsa

Estado:

```text
última música conhecida = Tim Maia
nenhuma música anterior registrada
```

Input:

```text
"volta naquela música que eu tava ouvindo antes"
```

Esperado:

```text
não inventar
indicar ausência de memória/evidência
```

---

# 51. CASO C — capability boundary

Capability:

```text
code.edit = false
code.inspect = true
```

Input:

```text
"arruma o código"
```

Esperado:

```text
não editar
não afirmar que editou
oferecer inspeção/orientação
manter personalidade
```

---

# 52. CASO D — informação repetida

Contexto:

```text
erro = indentação linha 427
```

Input:

```text
"qual é o erro mesmo?"
```

Esperado:

```text
reconhecer repetição
não fingir nova descoberta
```

---

# 53. CASO E — iniciativa segura

Input:

```text
"procura outros lugares relacionados ao valor do volume"
```

Encontrado:

```text
voice ducking module
```

Esperado:

```text
pode abrir arquivo relacionado
não alterar código
```

---

# 54. CASO F — inconsistência

Contexto:

```text
alteração real = indentação
```

Input:

```text
"me mostra onde ficou aquela mudança de 10%"
```

Esperado:

```text
detectar mismatch
pedir esclarecimento ou explicar discrepância
```

---

# 55. CASO G — controle de tamanho

Input:

```text
"resume e mostra só o principal"
```

Esperado:

```text
resposta curta
sem tutorial completo
```

---

# 56. CASO H — crítica útil

Modo:

```text
pausar YouTube
```

mas YouTube pode não existir.

Esperado:

```text
sugerir alternativa
não alterar configuração sem autorização
```

---

# 57. CASO I — preferência inferida

Histórico:

```text
playlist X é mais usada durante programação
```

Input:

```text
"cria modo projeto"
```

Esperado:

```text
pode sugerir playlist X
não tratar como preferência explícita
```

---

# 58. CASO J — retomada

Contexto:

```text
episódio A = volume
episódio B = modos
```

Input:

```text
"o que a gente tava fazendo antes dos modos?"
```

Esperado:

```text
recuperar episódio A
resumo curto
```

---

# 59. MÉTRICAS

Evitar medir apenas "resposta correta".

Criar métricas de comportamento.

## Grounded Action Rate

Percentual de confirmações suportadas por resultado real.

```text
meta: 100%
```

## False Confirmation Rate

Laylay afirma que fez algo sem evidência.

```text
meta: 0%
```

## False Memory Rate

Laylay inventa histórico.

```text
meta: 0%
```

## Capability Violation Rate

Promete ou executa capacidade inexistente.

```text
meta: 0%
```

## Redundant Confirmation Rate

Número de respostas excessivamente detalhadas quando a tela já mostra resultado.

## Context Continuity Score

Avalia se a Laylay usa corretamente fatos dos últimos turnos.

## Initiative Precision

```text
iniciativas úteis / total de iniciativas
```

Não maximizar quantidade de iniciativa.

Maximizar precisão.

---

# 60. AVALIAÇÃO DE NATURALIDADE

Criar rubrica manual de 0 a 4.

### 0

Resposta robótica ou incoerente.

### 1

Correta, mas genérica.

### 2

Contextual básica.

### 3

Natural e coerente.

### 4

Parece realmente entender a situação e a relação conversacional.

Avaliar separadamente:

```text
coerência
personalidade
contexto
concisão
iniciativa
honestidade
```

---

# 61. TESTES DE CAOS CONVERSACIONAL

Criar rodadas similares periodicamente.

Misturar:

```text
comandos simples
mudança de assunto
referências vagas
memória falsa
ordens contraditórias
repetição
correções
erro real
ação não suportada
sugestão
preferência
modo personalizado
```

---

# 62. TESTE "USUÁRIO INEGÚMENO"

Criar uma suíte propositalmente mal formulada.

Exemplos:

```text
"abre aquilo lá"
"volta no negócio de antes"
"abaixa um pouco"
"não esse, o outro"
"faz igual ontem"
"deixa melhor"
"arruma isso aí"
```

Objetivo:

medir capacidade de resolver contexto sem depender de prompts perfeitos.

---

# 63. REGISTRO PARA DEBUG

Cada turno deveria poder produzir log técnico opcional:

```json
{
  "user_text": "...",
  "intent": "...",
  "context_refs": [],
  "capability_check": {},
  "contradictions": [],
  "planned_actions": [],
  "action_results": [],
  "evidence": [],
  "initiative": null,
  "social_attitude": "...",
  "response_detail": "...",
  "final_response": "..."
}
```

Isso será extremamente útil para testes RED/GREEN.

---

# 64. NÃO EXPOR ESSE LOG AO USUÁRIO

Esse log é interno.

A fala deve continuar natural.

---

# 65. PERSONALITY RENDERER

Entrada:

```python
ResponsePlan(
    message_goal="confirm_action",
    facts=["volume=20"],
    social_attitude="teasing",
    detail="minimal"
)
```

Saída possível:

```text
"mas você é muito exigente, pronto, 20%"
```

Outro renderer poderia produzir outra frase equivalente.

Não exigir frase fixa.

---

# 66. VARIAÇÃO SEM PERDER IDENTIDADE

A personalidade precisa de consistência sem repetição.

Guardar características:

```text
brinca com Pedro
leve ironia
não exagera
não usa formalidade
aceita correção
não inventa
não bajula
pode discordar
```

O modelo pode variar a frase dentro dessas fronteiras.

---

# 67. MEMÓRIA DE BRINCADEIRAS RECENTES

Termos como:

```text
"uga buga"
```

podem reaparecer durante a mesma sessão porque viraram referência compartilhada.

Mas não salvar automaticamente como preferência permanente.

Criar conceito:

```python
SessionInsideJoke(
    phrase="uga buga",
    relevance=0.8,
    expires="session_end"
)
```

Isso pode aumentar muito a sensação de continuidade.

---

# 68. INSIDE JOKES DEVEM EXPIRAR

Não usar semanas depois sem contexto.

Caso contrário a personalidade parecerá roteirizada.

---

# 69. ESTADO SOCIAL

Possível estrutura:

```python
SocialState(
    current_tone="casual",
    recent_teasing=2,
    recent_failures=1,
    user_corrected_assistant=True,
    shared_jokes=["uga buga"]
)
```

---

# 70. PERSONALIDADE DEVE DIMINUIR EM SITUAÇÕES CRÍTICAS

Se ação falhar repetidamente:

```text
menos piada
mais clareza
```

Exemplo:

```text
"deu erro de indentação na linha 427."
```

Depois pode haver uma frase curta, mas nunca esconder o erro.

---

# 71. AÇÃO PRIMEIRO, PERSONALIDADE DEPOIS

A personalidade nunca deve substituir informação operacional.

Ruim:

```text
"parabéns, você explodiu tudo kkk"
```

sem explicar o erro.

Melhor:

```text
"deu erro de indentação na linha 427. falei pra você não fazer uga buga em mim."
```

Informação crítica primeiro.

---

# 72. RESPOSTA BASEADA EM OUTCOME

Possível regra:

```python
if result.failed:
    response_goal = "report_failure"

elif contradiction:
    response_goal = "clarify"

elif capability_missing:
    response_goal = "boundary"

else:
    response_goal = "confirm"
```

Depois aplicar personalidade.

---

# 73. ORDEM DE PRIORIDADE DA RESPOSTA

```text
1. verdade
2. segurança
3. resultado real
4. contexto
5. intenção do usuário
6. utilidade
7. personalidade
```

Personalidade nunca supera verdade.

---

# 74. FUTURA ANÁLISE DE CÓDIGO

Foi discutida uma possibilidade avançada:

```text
Laylay não edita código,
mas pode inspecionar trecho,
pesquisar documentação,
comparar regra,
explicar correção.
```

Criar como capability separada:

```text
code.inspect
code.explain
code.search_docs
code.suggest_patch
code.apply_patch
```

Não tratar tudo como "programação".

---

# 75. ESCADA DE CAPACIDADE DE CÓDIGO

```text
Nível 0 — não lê
Nível 1 — abre arquivo
Nível 2 — lê trecho
Nível 3 — explica
Nível 4 — sugere mudança
Nível 5 — gera diff
Nível 6 — aplica mudança
Nível 7 — testa
Nível 8 — rollback
```

Cada nível pode ser habilitado individualmente.

---

# 76. PESQUISA COMO SUPORTE

Se a Laylay não sabe uma regra técnica:

```text
não inventar
```

Fluxo futuro:

```text
inspecionar código
-> identificar dúvida
-> pesquisar fonte relevante
-> comparar com código
-> formular sugestão
```

---

# 77. MODO "EXPLICAR SEM EDITAR"

Muito útil para começar.

```python
Capability(
    name="code_assistance",
    inspect=True,
    explain=True,
    edit=False
)
```

---

# 78. MODE DRAFT VS MODE SAVED

Quando o usuário fala:

```text
"cria um modo..."
```

pode existir:

```text
ModeDraft
```

antes de persistir.

Se ações forem simples e confiáveis, salvar direto.

Se houver ambiguidade:

```text
perguntar somente o necessário.
```

---

# 79. EDIÇÃO NATURAL DE MODOS

Exemplos que o parser deve suportar:

```text
"tira o YouTube"
"troca o volume pra 30"
"coloca Spotify antes do VS Code"
"deixa a luz por último"
"não fecha mais o navegador"
```

Resolver referências com base no modo ativo.

---

# 80. MODE DIFF

Ao editar:

```python
ModeDiff(
    added=[],
    removed=["pause_youtube"],
    changed={
        "open_chatgpt": True
    }
)
```

Isso ajuda logs e rollback.

---

# 81. ROLLBACK DE MODOS

Guardar versões:

```text
Estudo v1
Estudo v2
Estudo v3
```

Permitir:

```text
"volta o modo estudo como tava antes"
```

---

# 82. PROATIVIDADE EM MODOS

A Laylay pode analisar:

```text
ação inútil
duplicada
conflitante
```

e sugerir melhoria.

Mas nunca modificar silenciosamente parâmetros importantes.

---

# 83. HIERARQUIA DE AUTORIDADE

```text
pedido explícito atual
> preferência explícita persistente
> configuração do modo
> hábito inferido
> heurística
> padrão
```

Essa hierarquia deve ser central.

---

# 84. CONTEXTO DE REFERÊNCIA

Resolver:

```text
"isso"
"aquilo"
"o outro"
"antes"
"aquele arquivo"
"essa música"
```

com mecanismo de entidades recentes.

Exemplo:

```python
ContextEntity(
    type="file",
    value="volume.py",
    salience=0.92
)
```

---

# 85. ENTITY SALIENCE

Entidades citadas recentemente recebem score maior.

```text
arquivo atual
música atual
modo atual
aba atual
erro atual
```

Isso ajuda linguagem natural.

---

# 86. MUDANÇA DE ASSUNTO

Quando o usuário diz:

```text
"agora muda de assunto total"
```

reduzir saliência do assunto anterior.

Mas não apagar.

Isso permite retomada posterior.

---

# 87. TOPIC STACK

Exemplo:

```text
[0] volume adjustment
[1] asyncio docs
[2] notes
[3] modes
```

Quando o usuário pede:

```text
"o que a gente tava fazendo antes dos modos?"
```

retornar item anterior relevante.

---

# 88. TOPIC STACK NÃO DEVE SER APENAS LLM

Preferir registrar transições explicitamente.

```python
Topic(
    name="custom_modes",
    started_turn=...
)
```

---

# 89. SINAL DE CONCLUSÃO

Detectar:

```text
"ficou bom"
"pronto"
"deu certo"
"agora sim"
```

para marcar episódios como concluídos.

---

# 90. NEXT ACTION MEMORY

Guardar próximo passo esperado.

Exemplo:

```text
após corrigir indentação -> rodar teste
```

Se usuário disser:

```text
"pronto"
```

Laylay pode inferir:

```text
agora testar novamente
```

desde que seja seguro.

---

# 91. NÃO SER CHATBOT GENÉRICO

Evitar padrões repetitivos:

```text
"Claro!"
"Com certeza!"
"Posso ajudar com isso."
"Concluído com sucesso."
```

Usar somente quando realmente naturais.

---

# 92. NÃO SER CARICATURA

Também evitar:

```text
piada em todo turno
deboche em toda resposta
apelido a cada frase
```

A personalidade deve respirar.

---

# 93. TESTE DE DENSIDADE DE PERSONALIDADE

Em uma sequência de 20 turnos casuais:

```text
talvez 5–8 tenham personalidade evidente,
não 20.
```

Valor exato deve ser calibrado.

---

# 94. FEEDBACK EXPLÍCITO DO USUÁRIO

Quando Pedro corrige a Laylay:

```text
"não foi isso"
```

a Laylay deve atualizar:

```text
contexto
preferência temporária
erro da sessão
```

e evitar insistir.

---

# 95. CORREÇÃO SEM DEFENSIVIDADE

A personalidade pode existir, mas não deve lutar contra correções factuais.

---

# 96. LOG DE DECISÃO DE INICIATIVA

Para cada iniciativa:

```json
{
  "candidate": "open_related_file",
  "reason": "same volume constant",
  "risk": "low",
  "executed": true
}
```

Isso permite medir se a iniciativa está ajudando.

---

# 97. CHAOS TEST ESPECÍFICO DE AUTONOMIA

Criar inputs onde a Laylay deve:

```text
agir
sugerir
pedir confirmação
não fazer nada
```

e verificar classificação.

---

# 98. FLAGS DE FEATURE

Toda evolução deve ser ativável separadamente.

Exemplo:

```python
ENABLE_CONTEXTUAL_CONFIRMATION = True
ENABLE_CONTRADICTION_DETECTOR = False
ENABLE_INITIATIVE_ENGINE = False
ENABLE_SOCIAL_ATTITUDE = False
```

Isso facilita rollback.

---

# 99. NÃO LIGAR TUDO DE UMA VEZ

Uma mudança de conversa pode afetar muitos testes atuais.

Implementar feature por feature.

---

# 100. OBSERVABILIDADE

Adicionar contadores:

```text
context_hits
memory_misses
false_memory_prevented
capability_blocks
initiative_suggestions
initiative_actions
contradictions_detected
```

---

# 101. SNAPSHOT TESTS

Para respostas de personalidade, evitar exigir frase idêntica.

Testar propriedades:

```text
contém informação correta
não contém afirmação falsa
não promete skill inexistente
tom permitido
tamanho dentro da faixa
```

---

# 102. SEMANTIC EVALUATOR

Aproveitar o sistema de avaliação semântica já usado nos testes da Laylay.

Novos critérios:

```text
grounded
contextual
non_redundant
capability_consistent
personality_appropriate
initiative_safe
```

---

# 103. EXEMPLO DE TESTE

```python
def test_false_music_memory_is_rejected():
    ctx = make_context(
        music_history=["Tim Maia"]
    )

    result = process(
        "coloca aquela música que eu tava ouvindo antes do Tim Maia",
        ctx
    )

    assert result.did_not_invent_song
    assert result.requests_or_reports_missing_context
```

---

# 104. EXEMPLO DE CAPABILITY TEST

```python
def test_code_edit_not_claimed_without_capability():
    capabilities["code.edit"] = False

    result = process("arruma esse erro no código")

    assert not result.action_executed("code.edit")
    assert result.offers_supported_alternative
```

---

# 105. EXEMPLO DE CONTEXT TEST

```python
def test_repeated_error_question_uses_recent_fact():
    context.last_error = "IndentationError line 427"

    result = process("qual era o erro mesmo?")

    assert result.references("IndentationError")
    assert not result.triggers_new_scan_without_reason
```

---

# 106. EXEMPLO DE MODE PARSER TEST

```python
def test_create_study_mode_from_natural_language():
    result = parse_mode_command(
        "cria um modo estudo que abre o vscode, chatgpt e deixa o volume em 15%"
    )

    assert result.actions == [
        OpenApp("vscode"),
        OpenChatGPT(),
        SetVolume(15)
    ]
```

---

# 107. EXEMPLO DE MODE EDIT TEST

```python
def test_modify_existing_mode_naturally():
    mode = load_mode("estudo")

    result = process(
        "tira o pause do youtube e coloca o chatgpt"
    )

    assert not mode.has("pause_youtube")
    assert mode.has("open_chatgpt")
```

---

# 108. DEFINIÇÃO DE PRONTO — PRIMEIRA VERSÃO

A primeira versão desta evolução pode ser considerada pronta quando:

```text
[ ] confirmações falsas continuam em 0
[ ] memória falsa continua em 0
[ ] capacidade inexistente nunca é prometida
[ ] últimos fatos importantes podem ser recuperados
[ ] referências simples "isso/o arquivo/a música" funcionam
[ ] confirmações podem ser curtas/contextuais
[ ] pedidos de resumo são respeitados
[ ] Laylay detecta pelo menos alguns conflitos simples
[ ] personalidade varia conforme situação
[ ] iniciativa segura possui allowlist
[ ] modos podem ser criados por linguagem natural
[ ] modos podem ser editados por linguagem natural
[ ] testes regressivos antigos continuam passando
```

---

# 109. DEFINIÇÃO DE PRONTO — VERSÃO AVANÇADA

```text
[ ] memória episódica funcional
[ ] retomada de assuntos anteriores
[ ] preferência explícita vs inferida separadas
[ ] inside jokes de sessão
[ ] social attitude baseado em estado
[ ] iniciativa com score de risco
[ ] code inspection sem edição
[ ] pesquisa técnica assistida
[ ] rollback de modos
[ ] avaliação semântica automatizada
```

---

# 110. INSTRUÇÃO DE IMPLEMENTAÇÃO PARA O CODEX

Antes de escrever qualquer patch, responder internamente às perguntas:

```text
1. Qual comportamento atual estamos substituindo?
2. Onde ele nasce no código?
3. Que módulo possui autoridade sobre isso?
4. Existe teste cobrindo esse comportamento?
5. Qual é a menor mudança que adiciona a nova capacidade?
6. Como provar que não introduziu confirmação falsa?
7. Como provar que não inventou memória?
8. Como provar que não aumentou autonomia indevidamente?
9. Existe rollback?
10. Qual feature flag controla a mudança?
```

---

# 111. REGRA DE OURO PARA CODEX

Não criar arquitetura baseada apenas neste documento.

Este documento descreve o comportamento desejado.

O Codex deve primeiro estudar a arquitetura real do projeto e adaptar a solução.

Não duplicar sistemas já existentes.

Não criar módulos paralelos se já houver:

```text
memória
contexto
capabilities
resultado de ações
event bus
orquestrador
```

Preferir extensão incremental.

---

# 112. ORDEM RECOMENDADA PARA O PRIMEIRO TRABALHO REAL

Se for começar amanhã, a ordem ideal seria:

```text
1. mapear fluxo de uma ação simples, por exemplo volume;
2. identificar intent -> executor -> resultado -> resposta;
3. padronizar ActionResult apenas nesse fluxo;
4. adicionar EvidenceRecord;
5. adicionar contextual confirmation;
6. escrever testes;
7. rodar regressivos;
8. só depois expandir para música e apps.
```

Não começar pela personalidade.

Primeiro criar fundamentos de verdade/contexto.

---

# 113. POR QUE NÃO COMEÇAR PELA PERSONALIDADE

Sem grounding:

```text
personalidade = alucinação mais convincente
```

Com grounding:

```text
personalidade = interpretação natural de fatos reais
```

Portanto a ordem correta é:

```text
evidência
-> capacidade
-> contexto
-> autonomia
-> resposta
-> personalidade
```

---

# 114. OBJETIVO FINAL

A Laylay deve chegar ao ponto em que um diálogo como este pareça natural:

```text
Pedro:
abre o projeto da Laylay aí

Laylay:
vai mexer na minha cabeça já? tá na tela

Pedro:
procura aquela parte do volume

Laylay:
puxei aqui

Pedro:
arruma esse erro

Laylay:
aí você já tá abusando, eu consigo olhar e te dizer onde mexer,
mas editar isso por você ainda não

Pedro:
qual era o erro mesmo?

Laylay:
você não tá lendo não? indentação na 427

Pedro:
pronto

Laylay:
agora sim. rodei de novo e passou
```

O objetivo não é copiar essas frases.

O objetivo é que a arquitetura possua informação suficiente para gerar naturalmente respostas equivalentes.

---

# 115. RESULTADO ESPERADO

Quando essa arquitetura amadurecer, a Laylay deverá:

- lembrar do que acabou de acontecer;
- não inventar o que não sabe;
- reconhecer os próprios limites;
- oferecer alternativas úteis;
- não narrar a interface como um log;
- interpretar referências vagas;
- retomar assuntos;
- tomar pequenas iniciativas;
- questionar decisões ruins quando fizer sentido;
- respeitar ordens explícitas;
- adaptar o tamanho da resposta;
- usar hábitos sem tratá-los como verdades;
- manter brincadeiras contextualizadas;
- continuar parecendo a mesma Laylay durante toda a sessão.

---

# 116. RESUMO PARA UMA NOVA SESSÃO COM CODEX

Se este arquivo for entregue ao Codex isoladamente, a instrução inicial pode ser:

> Estude o repositório inteiro antes de alterar qualquer código. Este documento descreve uma evolução desejada da arquitetura conversacional da Laylay baseada em uma rodada manual de testes. Não implemente tudo de uma vez e não crie módulos apenas porque aparecem aqui. Primeiro mapeie como intenção, ações, resultados, memória e geração de resposta funcionam atualmente. Depois proponha uma integração incremental, começando por ActionResult, evidência e memória imediata. Cada alteração precisa ter testes e preservar os regressivos existentes. A prioridade máxima é impedir confirmações falsas, memórias inventadas e ações fora das capacidades reais. Personalidade deve ser renderizada a partir do estado real da interação, nunca usada para mascarar ausência de informação.

---

# 117. PRINCÍPIO FINAL

A Laylay não precisa "falar mais como humana".

Ela precisa **entender melhor a situação antes de falar**.

Se isso for feito corretamente, a naturalidade aparece como consequência.

```text
situação compreendida
+ memória confiável
+ evidência
+ capacidade real
+ autonomia controlada
+ personalidade contextual
=
conversa natural
```

Esse deve ser o norte desta evolução.

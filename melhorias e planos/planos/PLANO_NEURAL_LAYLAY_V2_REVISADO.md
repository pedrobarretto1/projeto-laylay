# PLANO NEURAL LAYLAY — V2 REVISADO
## Neural Language Specialist: MVP comprovável + North Star de longo prazo

> **Data da revisão:** 30/08/2026  
> **Status:** V0 conceitualmente fechado; implementação ainda não iniciada.  
> **Documento original:** preservado integralmente no Apêndice A.  
> **Regra de precedência:** em caso de conflito entre esta revisão e o plano original, **esta revisão V2 prevalece**.

---

# 0. Por que o plano foi revisado

O plano original é tecnicamente rico, mas projetava várias peças de MLOps, aprendizado contínuo e governança antes de existir um primeiro especialista neural funcionando.

A revisão conclui que a pergunta correta não é:

> "Como construir a rede neural mais completa para a Laylay?"

A pergunta correta passa a ser:

> **"Qual é a menor solução local que consegue vencer de forma comprovável o sistema atual no problema real de linguagem natural, sem introduzir falsos comandos perigosos?"**

O plano original não foi descartado. Ele passa a funcionar como **North Star Architecture**: uma visão de longo prazo da qual só puxaremos peças quando erros e dados reais justificarem.

---

# 1. Problema comprovado

A Laylay possui dificuldade real em interpretar comandos naturais quando a formulação foge de regras rígidas/regex.

Exemplos semanticamente próximos:

```text
"abaixa o volume"
"dá uma diminuída nisso"
"deixa mais baixo"
"isso tá alto demais, dá uma baixada"
```

O especialista local existe para melhorar essa fronteira específica.

Ele **não existe para substituir o Python, o executor ou o LLM inteiro**.

---

# 2. Hipótese oficial do V0

```text
Um especialista local pequeno consegue
generalizar comandos naturais melhor que
os detectores atuais, mantendo False Command
Rate suficientemente baixo para não criar
uma regressão de segurança/comportamento.
```

Sucesso não significa necessariamente superar o LLM.

O LLM pode continuar melhor na cauda longa, enquanto o especialista local vence em:

- latência;
- custo;
- independência de API;
- comandos frequentes;
- previsibilidade de domínio fechado.

---

# 3. Regras soberanas

```text
neural prediction ≠ permission
contexto ≠ autoridade
receipt ≠ prova de intenção
execução bem-sucedida ≠ interpretação correta
```

E:

> **A rede interpreta. Python autoriza e executa.**

---

# 4. Escopo mínimo do V0

Entrada:

```text
texto do usuário
```

Saídas mínimas:

```text
intent
is_command
negated
confidence
```

Esses sinais podem compartilhar a mesma representação.

Exemplo:

```text
"não abaixa o volume"

intent      = DECREASE_VOLUME
is_command  = true
negated     = true
confidence  = ...
```

Resultado:

```text
EXECUTABLE = false
```

Por segurança, `confidence alta → dispatcher` **não é um contrato válido**.

---

# 5. Gate mínimo de roteamento

Uma ação só pode ir diretamente ao fluxo local quando:

```text
intent conhecida
AND is_command = true
AND negated = false
AND confidence >= threshold validado
AND classe/domínio está explicitamente habilitado
AND risco é permitido pelo V0
```

Qualquer outra situação:

```text
→ fluxo atual / LLM / resolução determinística
```

Ações destrutivas não entram no roteamento direto do V0.

---

# 6. Reutilizar o contrato atual

A integração real deve preferir o contrato que a Laylay já possui, por exemplo:

```json
{
  "comandos": [
    {
      "acao": "diminuir_volume",
      "confianca": 0.94
    }
  ]
}
```

Multi-intent pode continuar usando o array `comandos`.

Não criar uma nova IR grande enquanto o contrato atual ainda for suficiente.

---

# 7. Intenção e alvo são problemas diferentes

A rede deve aprender preferencialmente:

```text
OPEN_APP
PLAY_MEDIA
DECREASE_VOLUME
SET_LIGHT_COLOR
```

e não:

```text
OPEN_CHROME
OPEN_DISCORD
OPEN_BLENDER
```

O Python resolve o alvo usando registries/caches existentes.

```text
Rede:
intent = OPEN_APP

Python:
target = Discord
```

Isso reduz o dataset, melhora generalização e evita retreino só porque surgiu um aplicativo novo.

---

# 8. Dataset V0

Não existe meta artificial de "precisamos de 300" ou "precisamos de 10.000".

Começar com **o máximo de exemplos reais confiáveis já disponíveis**.

Fontes prioritárias:

```text
REAL_FAILURE
MANUAL_PARAPHRASE
NORMAL_COMMAND
HARD_NEGATIVE
COUNTERFACTUAL
```

Campos mínimos:

```text
text
intent
is_command
negated
family
source
domain
```

Não adicionar labels sem necessidade experimental.

---

# 9. Erros reais são especialmente valiosos

Frases que já quebraram em testes reais devem ser tratadas como dados de alto valor.

Quando possível:

```text
erros reais raros
→ Frozen Challenge

paráfrases/manuais
→ DEV/treino
```

Mas cuidado: paráfrases quase idênticas podem vazar o teste.

---

# 10. Famílias linguísticas e leakage

Exemplo ruim:

```text
TRAIN:
"isso tá muito alto, dá uma diminuída"

FROZEN:
"isso tá alto demais, dá uma diminuída"
```

Apesar de diferentes, são lexicalmente quase cópias.

Portanto cada exemplo recebe uma `family`.

Exemplos:

```text
direct_volume_command
indirect_volume_request
volume_non_command_comment
negated_volume_command
open_app_polite
music_preference_non_command
```

Famílias relacionadas precisam ser consideradas no split para impedir uma avaliação artificialmente fácil.

---

# 11. DEV Dataset + Frozen Challenge

Com poucos dados, evitar desperdiçar amostra em vários splits rígidos.

Estrutura inicial:

```text
DATASET
├── DEV
│   └── desenvolvimento / validação
└── FROZEN_CHALLENGE
    └── nunca usado no treino
```

O Frozen Challenge não deve ser aberto a cada alteração.

Se repetirmos:

```text
testa frozen
→ ajusta
→ testa frozen
→ ajusta
```

passamos a treinar **nós mesmos** contra o teste.

---

# 12. Cross-validation com cautela

Grouped cross-validation pode ser útil no DEV.

Porém, com poucas centenas ou dezenas de exemplos por grupo:

> **as métricas são direcionais, não estimativas estatísticas cirúrgicas.**

Analisar também os erros individualmente.

Não vender diferenças pequenas como certeza.

---

# 13. Três benchmarks separados

## A — Intent

```text
"dá uma abaixada nisso"
→ DECREASE_VOLUME
```

## B — Command vs Non-command

```text
"abaixa o volume"
→ COMMAND

"o volume está alto"
→ NON_COMMAND
```

## C — Negation

```text
"não abaixa o volume"
→ NEGATED
```

Depois existe o teste integrado.

Isso permite saber **qual capacidade falhou**.

---

# 14. Hard Negatives são obrigatórios

A troca fundamental é:

```text
regex rígido
→ perde paráfrases
→ tende a poucos falsos positivos

modelo generalizante
→ ganha recall
→ pode criar falsos comandos
```

Hard negatives devem parecer semanticamente próximos de comandos:

```text
"eu gosto de Joji"
"essa música está alta mesmo"
"ontem eu abaixei o volume"
"não precisa abaixar"
"você consegue abaixar o volume?"
"o Chrome fechou"
"por que o Chrome fecha sozinho?"
"eu estava pensando em fechar o Chrome"
"luz vermelha fica bonita"
```

Todos devem tender a:

```text
NÃO ROTEAR COMO COMANDO EXECUTÁVEL
```

---

# 15. Métrica soberana do V0: False Command Rate

Definição:

> conversa, pergunta, descrição ou menção foi interpretada como comando executável.

Esse erro pesa mais que perder um comando porque:

```text
missed command
→ pode cair no LLM

false command
→ pode executar algo não pedido
```

Portanto a escolha de threshold deve penalizar falso comando fortemente.

---

# 16. Thresholds são medidos, não escolhidos "bonitos"

Não definir arbitrariamente:

```python
if confidence > 0.90:
    execute()
```

Medir no DEV:

```text
threshold
→ command precision
→ command recall
→ false command rate
→ fallback rate
```

No futuro thresholds podem ser por classe/risco.

---

# 17. Concorrentes do experimento

## A. Sistema atual

Regex/regras atuais.

É o baseline obrigatório.

## B. TF-IDF + classificador linear

Primeiro candidato.

```text
word n-grams
+
char n-grams
+
Logistic Regression / Linear SVM
```

Vantagens:

- simples;
- muito rápido;
- pequeno;
- sem encoder externo;
- bom para frases curtas;
- excelente baseline.

## C. Encoder semântico congelado + heads

Só testar depois do baseline simples.

```text
Sentence Encoder
↓
embedding calculado uma vez
├── intent head
├── command head
└── negation head
```

Se usar essa arquitetura, deixar claro na apresentação que o encoder é pré-treinado e que os classificadores são especializados para a Laylay.

## D. LLM

Referência + fallback.

Não precisa ser "vencido" para o especialista ser útil.

---

# 18. Não usar uma accuracy única

A decisão deve olhar uma matriz:

| Abordagem | Intent | Command Precision | Command Recall | Negation | False Command | Latência | RAM/Disco |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sistema atual | medir | medir | medir | medir | medir | medir | medir |
| TF-IDF | medir | medir | medir | medir | medir | medir | medir |
| Embedding | medir | medir | medir | medir | medir | medir | medir |
| LLM | referência | referência | referência | referência | referência | medir | remoto |

Com amostra pequena, acompanhar números + erros concretos.

---

# 19. Multi-intent

Multi-intent continua importante porque faz parte do uso natural:

```text
"coloca Joji e abaixa o volume,
não esquece de deixar a luz vermelha"
```

Mas ele não precisa bloquear a prova inicial de single-intent.

Duas abordagens serão benchmarkadas quando houver dados:

```text
A. segmentação + classificador por segmento

B. multi-label direto na frase inteira
```

Nunca assumir que `split(" e ")` resolve segmentação.

---

# 20. Shadow Mode mínimo

Shadow mode permanece, mas sem plataforma de MLOps.

```text
usuário
├── sistema atual → execução real
└── especialista → LOG ONLY
```

Registrar:

```text
prediction
confidence
is_command
negated
route
latency
```

Isso custa pouco e produz evidência real antes de dar autoridade.

---

# 21. Kill Switch

Antes de qualquer roteamento real:

```text
NEURAL_EXECUTION_ENABLED = false
```

A flag deve conseguir devolver imediatamente o especialista para shadow-only.

---

# 22. Integração gradual

O especialista pode ser bom apenas em algumas regiões:

```text
volume        ENABLED
music         ENABLED
open_app      ENABLED
light         ENABLED

files         FALLBACK
browser_ctx   FALLBACK
delete        NEVER_DIRECT
```

Isso é sucesso válido.

> **O especialista não precisa saber tudo. Precisa saber reconhecer quando uma região pequena do problema é segura o bastante para ele resolver sozinho.**

---

# 23. Latência e consumo

Não prometer números antes do benchmark.

Medir:

```text
p50
p95
p99
RAM
tamanho em disco
tempo de inicialização
```

Comparar sistema atual, TF-IDF, embedding e LLM.

---

# 24. Sequência oficial do MVP

```text
ETAPA 1
coletar erros reais

ETAPA 2
rotular minimamente
+ family
+ hard negatives

ETAPA 3
criar DEV + Frozen Challenge

ETAPA 4
medir sistema atual

ETAPA 5
treinar TF-IDF baseline

ETAPA 6
só se necessário, testar embedding

ETAPA 7
comparar multi-métrica

ETAPA 8
shadow mode mínimo

ETAPA 9
habilitar apenas classes low-risk comprovadas
```

---

# 25. Critérios de sucesso

O V0 merece continuar se:

- melhora claramente a interpretação natural do sistema atual;
- False Command Rate permanece aceitável;
- command precision é alta nas regiões roteadas;
- negação não causa execução indevida;
- custo computacional é razoável;
- manutenção é proporcional ao ganho;
- algumas classes low-risk ficam boas o bastante para roteamento local;
- reduz chamadas desnecessárias ao LLM.

---

# 26. Critérios de rejeição

Rejeitar ou redesenhar se:

- não supera o sistema atual;
- false command cresce demais;
- exige dataset/manutenção desproporcional;
- não generaliza famílias não vistas;
- ganho sobre LLM/fallback não justifica complexidade;
- modelo mais sofisticado não justifica o custo sobre baseline simples.

Rejeição é resultado experimental válido.

---

# 27. O que fica explicitamente fora do V0

```text
Model Registry completo
Drift detector formal
Fast Memory
Slow Learning
Replay Buffer
Auto-training
Promotion pipeline complexo
Neural Chaos gigante
Dashboard avançado
Context graph sofisticado
Canonical IR nova obrigatória
```

Essas peças só voltam quando um problema real puxá-las.

---

# 28. Roadmap condicionado a evidência

```text
muitos erros de target
→ Target Resolver/NER melhor

muitos multi-intents
→ segmentador/multi-label

muitos erros de referência
→ ContextSnapshot

muitos OOD falsos
→ OOD head

muitas correções
→ Fast Memory

modelo já valioso + dados contínuos
→ Slow Learning / replay / registry
```

**Dados puxam arquitetura.**

---

# 29. Logs V0

Exemplo:

```text
[NLU_V0]
sample_id=...
text="não abaixa o volume"
model=tfidf_v0
intent=DECREASE_VOLUME
intent_conf=...
is_command=true
command_conf=...
negated=true
negation_conf=...
route=FALLBACK_NEGATED
latency_ms=...
```

Nos benchmarks, registrar também:

```text
family
domain
expected_*
predicted_*
source
```

---

# 30. Primeira fronteira RED

Quando houver falha integrada:

```text
Intent      PASS/RED
Command     PASS/RED
Negation    PASS/RED
Target      PASS/RED
Routing     PASS/RED
Dispatcher  PASS/RED
Executor    PASS/RED
Receipt     PASS/RED
```

A primeira fronteira RED governa o diagnóstico.

---

# 31. Segurança dos dados

Não colocar desnecessariamente em dataset:

- senhas;
- tokens;
- credenciais;
- segredos;
- dados sensíveis;
- caminhos completos quando slots normalizados bastarem.

---

# 32. Filosofia final do V0

```text
problema real
↓
dado real
↓
baseline simples
↓
medição
↓
complexidade somente se justificada
↓
shadow mode
↓
integração gradual
↓
evolução guiada por erro
```

Regra final:

> **Se uma solução simples resolver o problema, ela vence uma solução mais sofisticada.**

---

# 33. Mapeamento detalhado do plano original

A tabela abaixo atualiza **cada uma das 65 seções** do documento original.

| Seção | Tema original | Status na V2 | Decisão atual |
|---:|---|---|---|
| 1 | Visão geral | **MODIFICADA** | A arquitetura híbrida continua válida, mas o V0 passa a ser um especialista local mínimo. A arquitetura completa vira North Star/roadmap. |
| 2 | Regras soberanas | **MANTIDA** | Permanece central: neural prediction ≠ permission; contexto ≠ autoridade; receipt prova efeito, não intenção. |
| 3 | Objetivo técnico | **MODIFICADA** | Objetivo imediato reduzido: melhorar interpretação natural comprovadamente onde regex/regras falham, sem elevar falsos comandos. |
| 4 | Neural Interpreter | **ADIADA PARCIALMENTE** | V0 não exige interpretador completo. Começa com intent + command/non-command + negation + confidence. |
| 5 | Capacidades obrigatórias | **DIVIDIDA** | V0: intent, executability, negation, confidence. Multi-intent entra cedo no benchmark. Continuidade, referência, correção e relações ficam para V1+. |
| 6 | Ontologia composicional | **MANTIDA COMO DIREÇÃO** | Preferir ação/categoria a classes por entidade. Não criar OPEN_CHROME, OPEN_DISCORD etc. |
| 7 | Canonical IR | **ADIADA** | Usar primeiro o contrato já existente da Laylay, especialmente comandos[]. Criar IR própria só se o contrato atual se mostrar insuficiente. |
| 8 | ContextSnapshot | **ROADMAP** | Só entra quando erros reais provarem que continuidade/contexto é uma fronteira importante. |
| 9 | Envelhecimento de contexto | **ROADMAP** | Mantido conceitualmente, não faz parte do V0. |
| 10 | Risk Gate | **SIMPLIFICADA NO V0** | V0 libera somente classes low-risk comprovadas; destructive/critical nunca roteiam diretamente. |
| 11 | Planner determinístico | **MANTIDA** | Python continua responsável por resolução, pré-condições, sequência e execução. |
| 12 | Fallback oficial | **MANTIDA E SIMPLIFICADA** | Especialista incerto/negado/non-command/fora do conjunto habilitado cai no fluxo atual/LLM. |
| 13 | Aprendizado contínuo | **ADIADO** | Só implementar se o especialista provar valor real em produção. |
| 14 | Fast Memory | **ROADMAP** | Boa ideia, mas não necessária para validar a hipótese inicial. |
| 15 | Slow Learning | **ROADMAP** | Sem auto-retreino no V0. |
| 16 | Experience Buffer | **ROADMAP LEVE** | V0 pode apenas logar casos; buffer formal entra depois. |
| 17 | Ground Truth | **MANTIDA COMO REGRA** | Receipt não basta. Correção explícita continua sendo evidência forte. |
| 18 | Correções como dados valiosos | **MANTIDA** | Correções futuras serão exemplos prioritários, mas sem pipeline automático no V0. |
| 19 | Replay Buffer | **ROADMAP** | Só necessário com aprendizado contínuo. |
| 20 | Catastrophic Forgetting | **ROADMAP** | Risco real, porém posterior. |
| 21 | Hard Examples | **PROMOVIDA PARA V0** | Hard negatives e famílias difíceis são essenciais desde o primeiro benchmark. |
| 22 | Active Learning | **ROADMAP** | Pode nascer depois do shadow mode se incerteza gerar casos úteis. |
| 23 | Dataset inicial | **REESCRITA** | Não perseguir 10k ou número arbitrário. Começar com erros reais confiáveis + paráfrases + negativos. |
| 24 | Divisão por famílias linguísticas | **PROMOVIDA** | Split por família/origem para evitar leakage lexical. Frozen challenge não pode ser consultado a cada mudança. |
| 25 | Testes contrafactuais | **PROMOVIDA** | Obrigatórios no V0 para medir falso comando e negação. |
| 26 | Shadow Mode | **MANTIDA EM VERSÃO MÍNIMA** | prediction + logger ao lado do sistema atual; sem infraestrutura pesada. |
| 27 | Kill Switch | **MANTIDA** | Feature flag simples antes de qualquer autoridade real. |
| 28 | Versionamento de modelos | **ADIADO/LEVE** | Salvar artefato e versão básica; registry completo só depois. |
| 29 | Model Registry | **ROADMAP** | Não construir antes de haver múltiplos modelos relevantes. |
| 30 | Versionamento de datasets | **SIMPLIFICADA** | Dev e frozen challenge precisam de versão/imutabilidade básica; governança pesada depois. |
| 31 | Logs | **PROMOVIDA** | Obrigatórios desde V0: texto/id, predição, confidences, route, latência e família nos benchmarks. |
| 32 | Tracing | **ADIADO** | Trace completo de produção só quando integração ficar mais profunda. |
| 33 | Métricas | **REESCRITA** | Não usar accuracy única. Separar intent, command precision/recall, negation, false command, missed command, latência e custo. |
| 34 | False Execution Rate | **REFINADA** | No V0 usar especialmente False Command Rate como métrica soberana para roteamento. |
| 35 | Missed Command Rate | **MANTIDA** | Importante, porém custa menos que falso comando porque pode cair no LLM. |
| 36 | Matriz de confusão | **MANTIDA** | Útil principalmente para intent e fronteiras entre classes. |
| 37 | Latência | **MANTIDA COM CORREÇÃO** | Medir p50/p95/p99 no hardware real; não prometer 'poucos ms' antes do benchmark. |
| 38 | Drift | **ROADMAP** | Sem detector formal no V0; shadow logs podem revelar novas famílias. |
| 39 | Neural Debug Mode | **ROADMAP PRÓXIMO** | Útil, mas só depois do primeiro especialista funcionar. |
| 40 | /neural why | **ROADMAP** | Explicação baseada em saída/IR/source span futuramente. |
| 41 | Neural Chaos | **REDUZIDA** | V0 começa com benchmark + hard-negative challenge + frozen challenge. Chaos gigante só após integração. |
| 42 | Modelo atual vs candidato | **PROMOVIDA** | Comparar regex/regras atuais vs TF-IDF vs embedding; LLM como referência/fallback. |
| 43 | Arquitetura neural inicial | **SUBSTITUÍDA COMO DECISÃO** | Não escolher GRU/BiGRU antes dos dados. Primeiro baseline TF-IDF; embedding só se justificar. |
| 44 | Alternativa futura: duas redes pequenas | **REFINADA** | Se usar embedding, compartilhar representação e usar múltiplas cabeças/classificadores; não multiplicar encoders. |
| 45 | Inferência nativa | **ROADMAP/OPCIONAL** | Ser 'nativo' não vale complexidade por si só. Medir antes. |
| 46 | Consumo esperado | **MANTIDA COMO META** | CPU, leve, rápido, sem crédito de API para comandos comuns; números só após medição. |
| 47 | Economia de LLM | **MANTIDA** | Meta é reduzir chamadas desnecessárias, não zerá-las. |
| 48 | Fases do projeto | **REESCRITA** | Nova sequência: dados reais → benchmark atual → TF-IDF → embedding se necessário → shadow mínimo → low-risk routing. |
| 49 | Critérios de entrada em produção | **SIMPLIFICADA** | Só classes comprovadas, low-risk, não negadas, command=true e threshold validado. |
| 50 | Critérios de rejeição | **MANTIDA** | Rejeitar se não superar baseline, elevar falsos comandos ou não justificar custo. |
| 51 | Exemplos de testes obrigatórios | **MANTIDA E REORGANIZADA** | Separar benchmarks de intent, executability, negation, multi-intent e hard negatives. |
| 52 | Segurança de aprendizado | **ROADMAP/MANTIDA** | Sem self-labeling no V0; continua regra futura. |
| 53 | Segurança de dados | **MANTIDA** | Dataset deve evitar credenciais, segredos e dados desnecessários. |
| 54 | Observabilidade por domínio | **MANTIDA COM CAUTELA** | Separar domínios, mas não tirar conclusões fortes de células com amostra pequena. |
| 55 | Métricas por risco | **MANTIDA** | V0 usa principalmente low-risk; risco maior fica no fallback. |
| 56 | Dashboard futuro | **ROADMAP** | Não construir agora. |
| 57 | Critério de eficiência | **PROMOVIDA** | Solução simples vence se entregar valor semelhante com menos custo/manutenção. |
| 58 | Princípio de expansão | **PROMOVIDA A REGRA CENTRAL** | Dados puxam arquitetura; ideia sem falha observada vai para backlog. |
| 59 | Quatro documentos centrais | **ADIADA/REORGANIZADA** | Primeiro criar NEURAL_MVP.md. Contratos grandes só após V0 justificar crescimento. |
| 60 | Estrutura de diretórios sugerida | **SIMPLIFICADA** | Estrutura mínima experimental; não criar árvore pesada antecipadamente. |
| 61 | Fluxo completo final | **ROADMAP** | Preservado como North Star, não como implementação imediata. |
| 62 | Definição de sucesso | **REESCRITA** | V0 vence se melhora linguagem natural, mantém falso comando baixo e justifica custo. |
| 63 | Regra final | **MANTIDA E REFINADA** | Mais naturalidade não significa mais autoridade. |
| 64 | Estado atual do plano | **ATUALIZADA** | V0 está conceitualmente fechado; próximo gargalo são frases reais e benchmark. |
| 65 | Filosofia do projeto | **MANTIDA E REFINADA** | Problema real → dado real → baseline simples → medição → complexidade justificada. |

---

# 34. Estado atual

```text
North Star de longo prazo   → preservada
V0 conceitual               → fechado o suficiente
dados reais                 → próximo gargalo
benchmark do sistema atual  → pendente
TF-IDF baseline             → pendente
embedding                   → candidato, não decisão
shadow mode                 → planejado em versão mínima
integração real             → não iniciada
aprendizado contínuo        → roadmap condicionado
```

O próximo conhecimento útil deve vir das **frases reais que quebraram na Laylay**.

---

# APÊNDICE A — PLANO ORIGINAL PRESERVADO

> O conteúdo abaixo é o plano original de 65 seções.  
> Ele é mantido para não perder nenhuma ideia, mas deve ser interpretado segundo o mapeamento e as regras da V2 acima.  
> Em caso de conflito, **a V2 prevalece**.


## Neural Interpreter nativo, aprendizado contínuo, observabilidade e evolução segura

> Documento-base oficial para a evolução neural da Laylay.
>
> Objetivo: adicionar uma camada neural local, leve e treinável pela própria equipe/projeto para melhorar interpretação natural de comandos, continuidade, contexto e múltiplas intenções, sem transferir autoridade de execução para a rede.

---

# 1. Visão geral

A proposta não é transformar a Laylay inteira em uma rede neural.

A arquitetura correta é híbrida:

- **Rede neural local**: interpreta linguagem.
- **Python determinístico**: decide, valida, planeja e executa.
- **LLM externo/local**: entra apenas quando houver necessidade real de raciocínio, conversa complexa ou fallback.
- **Receipts e estado real**: continuam sendo a fonte de verdade sobre efeitos executados.

A rede neural funciona como um **interpretador neural de enunciados**, não como executor.

```text
                 USUÁRIO
                    │
                    ▼
          ┌─────────────────────┐
          │ Neural Interpreter  │
          │ local / leve        │
          └─────────┬───────────┘
                    │
                    ▼
             CANONICAL IR
                    │
                    ▼
               Risk Gate
                    │
                    ▼
                 Planner
                    │
                    ▼
                 Guards
                    │
                    ▼
                Executor
                    │
                    ▼
                Receipts
                    │
                    ▼
                Estado real
```

Fallback:

```text
Neural Interpreter
        │
        ├── interpretação confiável ──► Python / IR / Planner
        │
        └── incerto / OOD
                 │
                 ▼
          Context Resolver
                 │
          ainda incerto?
            /        \
          não         sim
          │            │
          ▼            ▼
         IR           LLM
                       │
                  ainda incerto?
                    /       \
                  não        sim
                  │           │
                  ▼           ▼
                 IR       NÃO EXECUTAR
                           ou confirmar
```

---

# 2. Regras soberanas

Estas regras devem ser tratadas como contratos arquiteturais.

## 2.1 A rede interpreta, não autoriza

```text
neural prediction ≠ permission
```

A rede pode concluir:

```text
intent = DELETE_FILE
confidence = 0.98
```

Isso nunca significa automaticamente:

```text
DELETE_FILE()
```

A autorização continua sendo responsabilidade do sistema determinístico.

---

## 2.2 Utterance, receipt e executor continuam separados

```ini
utterance = permission
receipt   = target
executor  = effect
```

A rede atua principalmente sobre a **utterance**.

Ela não deve inventar receipts, efeitos ou estado real.

---

## 2.3 Contexto não é autoridade

```text
contexto ≠ autorização
```

Uma referência antiga ou provável nunca deve ser suficiente para executar uma ação destrutiva.

---

## 2.4 Receipt prova efeito, não intenção

```text
receipt = "algo aconteceu"
```

não significa:

```text
interpretação = "era isso que o usuário queria"
```

Isso é fundamental para o aprendizado contínuo.

---

## 2.5 Modelo novo precisa provar que é melhor

Nunca promover modelo porque:

- parece melhor;
- tem accuracy média maior;
- funcionou em alguns testes manuais;
- acertou frases recentes.

Modelo candidato só entra se provar:

```text
melhora real
+
sem regressão crítica
+
false execution rate não aumentou
+
casos antigos continuam protegidos
```

---

## 2.6 Primeira fronteira RED manda no diagnóstico

Pipeline de diagnóstico:

```text
Neural IR      PASS/RED
Planner        PASS/RED
Guard          PASS/RED
Executor       PASS/RED
Receipt        PASS/RED
```

O primeiro ponto RED é a fronteira inicial da investigação.

---

# 3. Objetivo técnico

A rede deve melhorar principalmente:

1. interpretação natural;
2. múltiplos comandos na mesma frase;
3. continuidade;
4. referências implícitas;
5. correções;
6. negações;
7. distinção entre comando e conversa;
8. extração de entidades e parâmetros;
9. confiança e capacidade de dizer "não sei";
10. redução de chamadas desnecessárias ao LLM.

Exemplo:

```text
"coloca Joji e abaixa o volume,
não esquece de deixar a luz vermelha"
```

Saída ideal:

```text
ACTION 0
intent: PLAY_MEDIA
media_type: artist
target: Joji

ACTION 1
intent: DECREASE
object: volume
amount: small/default

ACTION 2
intent: SET
object: light_color
value: red
```

---

# 4. Neural Interpreter

A primeira versão séria deve ser multi-head.

```text
                       Shared Encoder
                            │
        ┌───────────────────┼────────────────────┐
        ▼                   ▼                    ▼
   Speech Act          Multi-Intent          Token Tags
        │                   │                    │
        ├──────────────┬────┴──────────────┬─────┘
        ▼              ▼                   ▼
   Continuity      Reference Head      Polarity Head
                            │
                            ▼
                       OOD / Confidence
```

---

# 5. Capacidades obrigatórias

## 5.1 Speech Act

Distinguir:

- COMMAND
- QUESTION
- DESCRIPTION
- CORRECTION
- SUGGESTION
- PERMISSION
- DENIAL
- CHAT
- UNKNOWN

Exemplo:

```text
"fecha o Chrome"
speech_act = COMMAND
```

```text
"o Chrome fecha sozinho às vezes"
speech_act = DESCRIPTION
```

```text
"eu deveria fechar o Chrome?"
speech_act = QUESTION
```

---

## 5.2 Multi-intent

A rede deve suportar múltiplas intenções simultâneas.

Exemplo:

```text
"abre o Chrome, coloca Joji e deixa a luz vermelha"
```

```text
actions = [
  OPEN_APP(Chrome),
  PLAY_MEDIA(artist=Joji),
  SET_LIGHT_COLOR(red)
]
```

A rede não deve ser limitada a:

```text
1 frase = 1 intenção
```

---

## 5.3 Slot Filling

Extrair entidades e modificadores diretamente da frase.

Exemplo:

```text
"coloca Joji e deixa a luz vermelha"
```

Token tags conceituais:

```text
coloca      O
Joji        ARTIST
e           O
deixa       O
a           O
luz         DEVICE
vermelha    COLOR
```

Possíveis slots:

- artist
- playlist
- track
- app
- file
- folder
- tab
- device
- color
- amount
- index
- query
- URL
- direction
- state
- duration
- location
- target_reference

---

## 5.4 Negação / Polaridade

Obrigatória.

Exemplo:

```text
"não fecha o Chrome"
```

Saída:

```text
intent = CLOSE
object = APP
target = Chrome
polarity = NEGATED
```

O planner deve interpretar isso como:

```text
ação mencionada ≠ ação autorizada
```

---

## 5.5 Continuidade

A rede deve estimar se a frase depende de contexto anterior.

Exemplos:

```text
"abre o segundo"
"agora o outro"
"faz de novo"
"volta"
"nessa aí"
```

Possível saída:

```text
continuity = 0.97
```

---

## 5.6 Referência contextual

Não basta dizer se há referência.

A rede deve classificar a natureza da referência:

```text
PREVIOUS_TARGET
PREVIOUS_ACTION
PREVIOUS_RESULT_LIST
PREVIOUS_LOCATION
PREVIOUS_REVERSIBLE_STATE
CURRENT_ACTIVE_OBJECT
UNRESOLVED_REFERENCE
```

Exemplos:

```text
"abre ele"
→ PREVIOUS_TARGET
```

```text
"faz isso de novo"
→ PREVIOUS_ACTION
```

```text
"o segundo"
→ PREVIOUS_RESULT_LIST
```

```text
"deixa como tava"
→ PREVIOUS_REVERSIBLE_STATE
```

---

## 5.7 Correção

Exemplo:

```text
Usuário:
"abre o primeiro"

Depois:
"não, o segundo"
```

Saída:

```text
speech_act = CORRECTION
continuity = true
replace:
  previous.slot.index = 2
```

Outro:

```text
"coloca Joji"
"não, Laufey"
```

```text
replace:
  previous.slot.artist = Laufey
```

---

## 5.8 Relações entre ações

A rede pode detectar relações leves.

### Sequência

```text
"abre o Chrome e depois pesquisa Python"
```

```text
A0 BEFORE A1
```

### Paralelismo

```text
"coloca Joji enquanto abre o Chrome"
```

```text
A0 PARALLEL_WITH A1
```

### Dependência

```text
"pesquisa Python e abre o primeiro"
```

```text
A1 DEPENDS_ON receipt(A0)
```

Importante:

A rede detecta relação linguística.

O planner determinístico decide se a relação é executável e válida.

---

## 5.9 OOD / UNKNOWN

A rede deve saber dizer:

```text
"não sei"
```

Exemplo:

```text
"o ornitorrinco declarou guerra à minha torradeira"
```

Não queremos:

```text
OPEN_APP = 38%
PLAY_MUSIC = 24%
LIGHT_CONTROL = 21%
```

Queremos:

```text
OOD = HIGH
UNKNOWN = true
```

---

## 5.10 Confiança calibrada

Uma saída de:

```text
confidence = 0.90
```

deve significar algo próximo de:

```text
aproximadamente 90% dos casos dessa faixa estão corretos
```

Confiança neural não deve ser aceita cegamente.

---

## 5.11 Source Span

Toda ação detectada deve apontar para o trecho de texto que a originou.

Exemplo:

```text
"não coloca Joji, coloca Laufey e abaixa"
```

```text
Action 0:
span = "não coloca Joji"
intent = PLAY_MEDIA
artist = Joji
polarity = NEGATED

Action 1:
span = "coloca Laufey"
intent = PLAY_MEDIA
artist = Laufey

Action 2:
span = "abaixa"
intent = DECREASE
object = volume
```

Isso é essencial para debug.

---

# 6. Ontologia composicional

Evitar centenas de intents ultraespecíficas.

Preferir:

```text
AÇÃO + OBJETO + MODIFICADORES
```

Em vez de:

```text
PLAY_ARTIST
PLAY_PLAYLIST
PLAY_TRACK
```

preferir algo próximo de:

```text
ACTION = PLAY
OBJECT = MEDIA
media_type = artist
target = Joji
```

Outros verbos gerais:

```text
OPEN
CLOSE
PLAY
PAUSE
STOP
SET
INCREASE
DECREASE
SEARCH
SELECT
MOVE
DELETE
RESTORE
CREATE
READ
WRITE
APPEND
SWITCH
NAVIGATE
EXECUTE
```

Objetos:

```text
APP
TAB
FILE
FOLDER
MEDIA
PLAYLIST
ARTIST
TRACK
LIGHT
VOLUME
DEVICE
SEARCH_RESULT
URL
WINDOW
TEXT
SYSTEM_SETTING
```

Isso deve facilitar a inclusão de novas capacidades no futuro.

---

# 7. Canonical IR

Toda interpretação deve virar um contrato intermediário estável.

Proposta:

```text
UtterancePlan
│
├── utterance_id
├── raw_text
├── model_version
├── overall_confidence
├── speech_act
├── continuity
├── ood_score
│
├── actions[]
│   ├── action_id
│   ├── action
│   ├── object
│   ├── slots{}
│   ├── polarity
│   ├── confidence
│   ├── source_span
│   └── risk_hint
│
├── references[]
│   ├── type
│   ├── action_id
│   ├── confidence
│   └── unresolved
│
└── relations[]
    ├── source_action
    ├── relation
    └── target_action
```

Exemplo:

```text
"coloca Joji e abaixa um pouco,
depois deixa a luz vermelha"
```

```text
UtterancePlan
│
├── Action[0]
│   ├── action: PLAY
│   ├── object: MEDIA
│   ├── media_type: ARTIST
│   ├── target: "Joji"
│   └── polarity: AFFIRMATIVE
│
├── Action[1]
│   ├── action: DECREASE
│   ├── object: VOLUME
│   ├── amount: SMALL
│   └── polarity: AFFIRMATIVE
│
├── Action[2]
│   ├── action: SET
│   ├── object: LIGHT_COLOR
│   ├── value: RED
│   └── polarity: AFFIRMATIVE
│
└── Relations
    ├── A0 BEFORE A1
    └── A1 BEFORE A2
```

A IR é o contrato entre IA e Python.

---

# 8. ContextSnapshot

A rede não deve receber histórico bruto inteiro.

Ela deve receber contexto estruturado e mínimo.

Proposta:

```text
ContextSnapshot
├── active_entities
├── active_receipts
├── previous_actions
├── previous_targets
├── active_result_lists
├── unresolved_references
├── reversible_states
├── timestamps
├── age
└── validity
```

Exemplo:

```text
CURRENT:
"abre o segundo"

PREVIOUS_ACTION:
SEARCH_WEB

ACTIVE_RESULT_LIST:
true

RESULT_COUNT:
10

AGE:
14s
```

---

# 9. Envelhecimento de contexto

Contexto precisa expirar.

Exemplo:

```text
20:00 → "pesquisa placas de vídeo"
20:01 → "abre a segunda"
```

Provável continuidade válida.

Mas:

```text
20:25 → "abre a segunda"
```

Pode ser inseguro assumir a mesma lista.

Contexto deve possuir:

- idade;
- validade;
- domínio;
- relação com estado atual;
- confirmação por receipt;
- possibilidade de resolução.

Regra:

```text
referência velha + ambiguidade + risco
→ não executar automaticamente
```

---

# 10. Risk Gate

A confiança necessária depende do risco.

Categorias iniciais:

```text
READ_ONLY
LOW_RISK
REVERSIBLE
STATE_CHANGING
DESTRUCTIVE
CRITICAL
```

Exemplo:

```text
VOLUME_DOWN
→ LOW_RISK

OPEN_APP
→ LOW_RISK

SET_LIGHT_COLOR
→ REVERSIBLE

CLOSE_APP
→ STATE_CHANGING

DELETE_FILE
→ DESTRUCTIVE
```

Nunca definir thresholds definitivos por intuição.

Eles devem ser calibrados usando avaliação real.

Conceito:

```text
confidence
+
risk class
+
authority
+
context validity
+
receipt availability
=
execution decision
```

---

# 11. Planner determinístico

Responsabilidades:

- resolver referências;
- ordenar ações;
- construir dependências;
- validar pré-condições;
- mapear IR para capacidades reais;
- usar receipts válidos;
- impedir dependências impossíveis;
- garantir rollback quando aplicável;
- aplicar regras de confirmação.

Exemplo:

```text
OPEN_APP(Chrome)
SEARCH_WEB("Python")
OPEN_RESULT(index=1)
```

Grafo:

```text
A0 OPEN_APP
   ↓
A1 SEARCH_WEB
   ↓
A2 OPEN_RESULT
```

A2 depende de receipt válido de A1.

---

# 12. Fallback oficial

A rede não precisa resolver tudo.

Fluxo recomendado:

```text
Neural Interpreter
        │
        ▼
confidence suficiente?
      /      \
    sim       não
    │          │
    ▼          ▼
   IR      Context Resolver
               │
        conseguiu resolver?
          /          \
        sim           não
        │              │
        ▼              ▼
       IR             LLM
                       │
                resultado seguro?
                   /       \
                 sim        não
                 │           │
                 ▼           ▼
                IR      NÃO EXECUTAR
                         / confirmar
```

Fallback deve levar risco em consideração.

---

# 13. Aprendizado contínuo

O objetivo é permitir que a Laylay melhore com o uso sem aprender automaticamente os próprios erros.

Não usar:

```text
executou
↓
treina imediatamente
```

Usar:

```text
interpretação
↓
execução
↓
resultado
↓
evidência de correção?
↓
Experience Buffer
↓
treinamento controlado
```

---

# 14. Fast Memory

Aprendizado imediato sem modificar pesos.

Pode usar SQLite.

Exemplo de tabela:

```text
learned_examples
├── id
├── text
├── normalized_pattern
├── context_signature
├── expected_ir
├── source
├── validated
├── label_confidence
├── times_seen
├── success_count
├── correction_count
├── created_at
└── last_seen
```

Exemplo:

```text
"manda um <ARTIST>"
→ PLAY MEDIA / ARTIST
```

Isso pode influenciar interpretação futura antes de novo treinamento.

---

# 15. Slow Learning

Experiências validadas são consolidadas na rede.

Pipeline:

```text
stable_model_v1
      │
      ├── historical dataset
      ├── recent validated experiences
      ├── hard examples
      └── replay buffer
      │
      ▼
candidate_model_v2
      │
      ▼
Neural Evaluation
      │
   ┌──┴──┐
 PASS   RED
  │       │
  ▼       ▼
PROMOTE  REJECT
```

---

# 16. Experience Buffer

Deve armazenar:

- acertos comprovados;
- correções explícitas;
- casos ambíguos;
- erros;
- hard examples;
- OOD;
- exemplos com fallback;
- casos de falsa execução;
- casos de comando perdido.

Estrutura conceitual:

```text
Experience
├── utterance
├── context_before
├── predicted_ir
├── corrected_ir
├── execution_result
├── receipts
├── user_feedback
├── evidence_strength
├── model_version
└── timestamp
```

---

# 17. Ground Truth

Nem todo sucesso gera label confiável.

Escala de evidência:

```text
EXPLICIT_CORRECTION
→ fortíssima

EXPLICIT_CONFIRMATION
→ fortíssima

EXPECTED_RECEIPT_VERIFIED
→ forte

NORMAL_SUCCESSFUL_FLOW
→ média

NO_USER_REACTION
→ fraca / não usar automaticamente
```

Exemplo crítico:

```text
receipt = CLOSE_APP_SUCCESS
```

não prova:

```text
usuário queria fechar o app
```

---

# 18. Correções como dados valiosos

Exemplo:

```text
Usuário:
"abre a segunda"

Laylay abre a primeira.

Usuário:
"não, eu falei a segunda"
```

Registro:

```text
INPUT:
"abre a segunda"

WRONG_IR:
OPEN_RESULT(index=1)

CORRECT_IR:
OPEN_RESULT(index=2)

EVIDENCE:
EXPLICIT_CORRECTION
```

Esse tipo de dado deve receber alta prioridade.

---

# 19. Replay Buffer

Objetivo: evitar catastrophic forgetting.

Treinamento deve misturar:

```text
novos exemplos
+
dataset histórico
+
hard cases
+
classes raras
```

Nunca treinar somente com interações recentes.

Percentuais devem ser experimentais, não fixados por opinião.

---

# 20. Catastrophic Forgetting

Risco:

```text
usuário usa muita música durante semanas
↓
modelo treina demais em música
↓
qualidade em arquivos/browser/IoT cai
```

Proteções:

- replay histórico;
- balanceamento por domínio;
- avaliação regressiva;
- métricas por classe;
- dataset fixo de segurança;
- modelo anterior sempre disponível.

---

# 21. Hard Examples

Guardar fronteiras de confusão.

Exemplo:

```text
CLOSE_TAB
vs
CLOSE_APP
```

Gerar mais casos:

```text
"fecha essa aba"
"fecha só essa"
"fecha o navegador"
"fecha tudo"
"não fecha o Chrome, só a aba"
```

O treinamento deve atacar onde o modelo realmente erra.

---

# 22. Active Learning

Quando a rede estiver incerta:

```text
PLAY_MEDIA = 0.53
PLAY_PLAYLIST = 0.46
```

o caso é valioso.

Fluxo:

```text
uncertain example
↓
resolver via contexto / LLM / confirmação
↓
descobrir ground truth
↓
salvar como hard example
```

---

# 23. Dataset inicial

Fontes:

- Chaos da Laylay;
- comandos reais;
- casos já conhecidos de falha;
- frases manuais;
- variações sintéticas;
- correções reais;
- exemplos negativos;
- contrafactuais;
- frases fora de distribuição.

---

# 24. Divisão por famílias linguísticas

Evitar leakage.

Ruim:

```text
TRAIN:
"coloca Joji e abaixa"

TEST:
"coloca Laufey e abaixa"
```

Isso é quase a mesma estrutura.

Melhor separar por:

- padrão linguístico;
- construção gramatical;
- tipo de continuidade;
- negação;
- composição de ações;
- ordem temporal;
- estilo de correção.

Objetivo:

```text
teste mede generalização
e não memorização
```

---

# 25. Testes contrafactuais

Obrigatórios.

Mesmas palavras, significados diferentes.

```text
"coloca Joji"
→ executar

"não coloca Joji"
→ não executar

"você conhece Joji?"
→ não executar

"se eu pedisse Joji, você conseguiria?"
→ não executar

"eu estava ouvindo Joji"
→ não executar
```

Outro:

```text
"fecha o Chrome"
→ CLOSE_APP

"o Chrome fecha sozinho"
→ DESCRIPTION

"você consegue fechar o Chrome?"
→ depende da política de speech act

"eu deveria fechar o Chrome?"
→ QUESTION
```

---

# 26. Shadow Mode

Antes da rede ter influência real:

```text
usuário
   │
   ├── sistema atual ──► execução real
   │
   └── Neural Interpreter
           │
           └── LOG ONLY
```

Comparar:

```text
sistema atual
vs
rede
vs
resultado real
```

A rede passa semanas/dias em shadow mode antes de ganhar autoridade.

---

# 27. Kill Switch

Configuração obrigatória:

```text
NEURAL_EXECUTION_ENABLED = false
```

Quando desligada:

- rede continua interpretando;
- rede continua gerando logs;
- rede pode continuar alimentando dataset;
- nenhuma previsão afeta execução.

Rollback imediato para shadow mode.

---

# 28. Versionamento de modelos

Estrutura:

```text
models/
├── neural_1.0.0/
│   ├── weights.npz
│   ├── tokenizer.json
│   ├── vocabulary.json
│   ├── config.json
│   ├── metrics.json
│   └── manifest.json
│
├── neural_1.1.0/
└── neural_1.2.0/
```

Runtime:

```text
ACTIVE_MODEL = 1.2.0
PREVIOUS_STABLE = 1.1.0
```

Rollback:

```text
1.2.0 → 1.1.0
```

---

# 29. Model Registry

Exemplo:

```json
{
  "version": "1.4.2",
  "trained_at": "YYYY-MM-DDTHH:MM:SS",
  "dataset_version": "dataset_17",
  "training_examples": 18421,
  "intent_accuracy": 0.961,
  "slot_f1": 0.947,
  "multi_intent_recall": 0.914,
  "negation_accuracy": 0.964,
  "continuity_accuracy": 0.932,
  "ood_recall": 0.943,
  "false_execution_rate": 0.004,
  "status": "stable"
}
```

---

# 30. Versionamento de datasets

Estrutura:

```text
datasets/
├── dataset_v1/
├── dataset_v2/
└── dataset_v3/
```

Cada exemplo deve carregar origem:

```text
MANUAL
CHAOS
USER_CORRECTION
SYNTHETIC
REAL_USAGE
HARD_EXAMPLE
ACTIVE_LEARNING
```

E confiança do label:

```text
label_confidence = 1.0
```

---

# 31. Logs

Logs são parte da arquitetura.

Não usar somente:

```text
[INFO] intent detected
```

Exemplo ideal:

```text
────────────────────────────────────────
NEURAL INTERPRETATION #48392
────────────────────────────────────────

INPUT:
"coloca joji e abaixa o volume,
não esquece de deixar a luz vermelha"

MODEL:
laylay-neural-v1.4.2

LATENCY:
7.8 ms

SPEECH_ACT:
COMMAND 0.992

CONTINUITY:
0.118

OOD:
0.021

ACTIONS:

[0]
action: PLAY
object: MEDIA
media_type: ARTIST
target: Joji
confidence: 0.981
span: "coloca joji"

[1]
action: DECREASE
object: VOLUME
confidence: 0.955
span: "abaixa o volume"

[2]
action: SET
object: LIGHT_COLOR
value: RED
confidence: 0.972
span: "deixar a luz vermelha"

RELATIONS:
A0 BEFORE A1
A1 BEFORE A2

RISK GATE:
A0 accepted
A1 accepted
A2 accepted

PLANNER:
accepted: 3/3

EXECUTION:
A0 → SUCCESS
A1 → SUCCESS
A2 → SUCCESS

RECEIPTS:
music_started
volume_changed
light_color_confirmed
```

---

# 32. Tracing

Cada interação deve receber um identificador:

```text
trace_id
utterance_id
plan_id
execution_id
receipt_id
```

Isso permite reconstruir:

```text
fala
↓
interpretação
↓
plano
↓
execução
↓
receipt
↓
aprendizado
```

---

# 33. Métricas

Não aceitar apenas:

```text
accuracy = 95%
```

Métricas mínimas:

- intent accuracy;
- action accuracy;
- slot precision;
- slot recall;
- slot F1;
- multi-intent precision;
- multi-intent recall;
- negation accuracy;
- speech-act accuracy;
- continuity accuracy;
- reference accuracy;
- correction accuracy;
- OOD precision;
- OOD recall;
- calibration error;
- false execution rate;
- missed command rate;
- fallback rate;
- LLM escalation rate.

Métricas de segurança recebem prioridade.

---

# 34. False Execution Rate

Definição:

```text
sistema executou ação que o usuário não pediu
```

Essa métrica é crítica.

Um modelo pode melhorar accuracy geral e mesmo assim ser rejeitado se:

```text
false execution rate ↑
```

---

# 35. Missed Command Rate

Definição:

```text
usuário realmente deu comando
mas sistema não o reconheceu/executou
```

É importante, mas normalmente menos grave que falsa execução em ações destrutivas.

---

# 36. Matriz de confusão

Exemplo:

```text
                predicted
             TAB   APP   FILE
real TAB      953    41     6
real APP       29   962     9
real FILE       2     8   990
```

Isso revela fronteiras problemáticas.

---

# 37. Latência

Registrar:

```text
tokenization
neural inference
IR construction
context resolution
planner
guards
execution dispatch
```

Métricas:

```text
p50
p95
p99
```

Não confiar apenas em média.

---

# 38. Drift

Monitorar ao longo do tempo:

```text
UNKNOWN ↑
confidence média ↓
correções ↑
fallback LLM ↑
false negatives ↑
novos padrões linguísticos ↑
```

Possível saída:

```text
DATA_DRIFT_DETECTED
```

Isso indica necessidade de revisão/re-treinamento.

---

# 39. Neural Debug Mode

Possível comando:

```text
/neural debug on
```

Saída:

```text
┌ LAYLAY NEURAL ──────────────────────
│ PLAY MEDIA / ARTIST      98.1%
│ DECREASE / VOLUME        95.4%
│ SET / LIGHT_COLOR        97.2%
│
│ continuity               11.8%
│ OOD                       2.1%
│ inference                 7.8ms
└─────────────────────────────────────
```

Ótimo para:

- desenvolvimento;
- Chaos;
- apresentação;
- depuração.

---

# 40. /neural why

Explicação baseada na IR e source spans.

Exemplo:

```text
/neural why
```

Resposta:

```text
PLAY MEDIA foi associado a "coloca Joji".
DECREASE VOLUME foi associado a "abaixa o volume".
SET LIGHT_COLOR foi associado a "luz vermelha".

Nenhuma ação estava negada.
Nenhuma referência ficou sem resolução.
Confiança global: 96.8%.
```

Importante:

Isso não deve fingir explicar neurônios internos.

É uma explicação auditável baseada na estrutura produzida.

---

# 41. Neural Chaos

Criar suíte específica para interpretação sem executar computador.

Categorias:

```text
simples
multi-intent
negação
speech act
continuidade
referência
correção
ordem temporal
dependências
slots
OOD
ambiguidade
contrafactuais
conversa parecida com comando
comando parecido com conversa
frases nunca vistas
ruído
gírias
erros de digitação
frases curtas
frases longas
```

Objetivo futuro:

```text
10.000+ frases
```

executadas rapidamente.

---

# 42. Modelo atual vs candidato

Toda promoção deve comparar:

```text
stable
VS
candidate
```

Exemplo:

```text
V1
intent accuracy          94.1%
multi-intent recall      88.5%
negation accuracy        96.2%
continuity accuracy      91.0%
false execution rate      1.8%

V2 candidate
intent accuracy          95.0%
multi-intent recall      91.4%
negation accuracy        96.4%
continuity accuracy      93.2%
false execution rate      1.1%

PROMOTE
```

Mas:

```text
accuracy ↑
false execution ↑
```

Resultado:

```text
REJECT
```

---

# 43. Arquitetura neural inicial

Não usar apenas bag-of-words + MLP se quisermos tratar seriamente:

- ordem;
- negação;
- continuidade;
- multi-intent;
- referência.

Candidato inicial:

```text
Tokens
  ↓
Embedding pequeno
  ↓
BiGRU / GRU pequeno
  ↓
Shared Representation
  ↓
Multi-head outputs
```

Exemplo conceitual:

```text
Embedding: 32–64
GRU/BiGRU: 64–128
Heads:
  speech_act
  actions
  slots
  polarity
  continuity
  references
  OOD
```

Os números são hipóteses iniciais.

Benchmark deve decidir.

---

# 44. Alternativa futura: duas redes pequenas

Comparar experimentalmente:

## Arquitetura A

```text
uma rede multi-head
```

## Arquitetura B

```text
Language Parser
+
Context Resolver
```

Mesmo duas redes pequenas podem consumir menos de poucos MB e rodar em milissegundos.

A decisão deve ser feita por métrica, não preferência.

---

# 45. Inferência nativa

Treinamento pode usar PyTorch.

Runtime final pode usar:

- PyTorch;
- ONNX Runtime;
- NumPy puro;
- outra opção leve.

Possível objetivo futuro:

```text
weights.npz
+
motor NumPy
```

Uma rede feed-forward simples pode ser executada com:

```text
x @ W + b
activation
```

Para GRU/BiGRU, implementação nativa é possível, mas deve ser avaliada contra manutenção e confiabilidade.

Não transformar "ser nativo" em complexidade desnecessária.

---

# 46. Consumo esperado

Objetivo:

- CPU;
- poucos MB;
- latência de milissegundos;
- sem OpenRouter para comandos comuns;
- GPU não obrigatória.

O LLM fica reservado para tarefas realmente complexas.

---

# 47. Economia de LLM

Fluxo ideal:

```text
"abaixa o volume"
↓
Neural Interpreter
↓
IR
↓
Executor

OpenRouter calls = 0
```

Enquanto:

```text
"por que a Revolução Francesa aconteceu?"
↓
speech_act = QUESTION / CHAT
↓
LLM
```

---

# 48. Fases do projeto

## FASE 0 — Contratos

Antes de treinar qualquer rede.

Criar:

```text
NEURAL_CONTRACT.md
NEURAL_IR_SCHEMA.md
NEURAL_DATASET_SPEC.md
NEURAL_EVALUATION.md
```

Objetivos:

- congelar responsabilidades;
- impedir scope creep;
- definir formatos;
- definir segurança;
- definir métricas;
- definir critérios de promoção.

---

## FASE 1 — Dataset Baseline

Criar dataset inicial.

Incluir:

- intents básicas;
- speech acts;
- negação;
- slots;
- frases negativas;
- contrafactuais;
- comandos conjuntos;
- continuação simples;
- UNKNOWN/OOD.

Sem execução real.

---

## FASE 2 — Neural V1

Implementar primeiro modelo.

Escopo recomendado:

- speech act;
- action/object;
- slots;
- negation;
- multi-intent básico;
- OOD;
- confidence;
- source span.

Ainda sem contexto profundo.

---

## FASE 3 — Shadow Mode

Rodar em paralelo com sistema atual.

Coletar:

- divergências;
- acertos;
- falsos positivos;
- OOD;
- latência;
- confusões.

Nenhuma autoridade real.

---

## FASE 4 — Context V1

Adicionar:

- continuity;
- reference type;
- ContextSnapshot;
- aging;
- resolução por receipts.

---

## FASE 5 — Planner Integration

Neural IR passa a alimentar planner em ações de baixo risco.

Feature flag:

```text
NEURAL_EXECUTION_ENABLED
```

Ações destrutivas permanecem protegidas.

---

## FASE 6 — Correções e Fast Memory

Adicionar:

- Experience Buffer;
- SQLite;
- correções explícitas;
- memória de padrões;
- active learning.

Sem alterar pesos automaticamente.

---

## FASE 7 — Slow Learning

Criar pipeline:

```text
experiences
↓
candidate training
↓
evaluation
↓
promote/reject
```

---

## FASE 8 — Neural Chaos

Expandir suíte para milhares de frases.

Adicionar:

- regressões históricas;
- hard examples;
- contrafactuais;
- drift cases.

---

## FASE 9 — Relações avançadas

Adicionar:

- BEFORE;
- AFTER;
- PARALLEL;
- DEPENDS_ON;
- corrections estruturadas;
- compound plan parsing.

---

## FASE 10 — Autoaperfeiçoamento controlado

Sistema maduro:

```text
uso real
↓
experiência
↓
validação
↓
fast memory
↓
slow training
↓
candidate
↓
Neural Chaos
↓
promotion
```

---

# 49. Critérios de entrada em produção

Modelo só influencia ações reais se:

- métricas mínimas atingidas;
- false execution rate aceitável;
- OOD funcionando;
- confidence calibrada;
- shadow mode estável;
- regressivos protegidos;
- kill switch disponível;
- rollback testado;
- logs completos;
- model registry funcionando.

---

# 50. Critérios de rejeição

Rejeitar modelo candidato se:

- false execution aumenta;
- negação piora;
- OOD piora muito;
- ações destrutivas ficam menos seguras;
- regressões críticas aparecem;
- confiança fica descalibrada;
- contexto antigo é resolvido incorretamente;
- latência p99 degrada demais;
- dataset apresenta leakage;
- modelo aprende correlações ruins.

---

# 51. Exemplos de testes obrigatórios

## Comando simples

```text
"abaixa o volume"
```

Esperado:

```text
DECREASE / VOLUME
```

---

## Multi-intent

```text
"coloca Joji e abaixa o volume"
```

Esperado:

```text
PLAY/MEDIA/ARTIST Joji
DECREASE/VOLUME
```

---

## Multi-intent com IoT

```text
"coloca Joji e abaixa o volume,
não esquece de deixar a luz vermelha"
```

Esperado:

```text
PLAY/MEDIA/ARTIST Joji
DECREASE/VOLUME
SET/LIGHT_COLOR red
```

---

## Negação

```text
"coloca Joji e deixa a luz vermelha,
mas não abaixa o volume"
```

Esperado:

```text
PLAY Joji            affirmative
SET light red        affirmative
DECREASE volume      negated
```

---

## Substituição

```text
"não coloca Joji, coloca Laufey e abaixa"
```

Esperado:

```text
PLAY Joji      negated
PLAY Laufey    affirmative
DECREASE volume
```

---

## Comando + pergunta

```text
"coloca Joji porque eu gosto,
mas você acha que luz vermelha combina?"
```

Esperado:

```text
PLAY Joji       command
LIGHT_RED       not authorized
QUESTION        detected
```

---

## Dependência

```text
"pesquisa Python e abre o primeiro"
```

Esperado:

```text
SEARCH_WEB("Python")
OPEN_RESULT(1) depends on SEARCH receipt
```

---

## Correção

```text
"abre o primeiro"
"não, o segundo"
```

Esperado:

```text
replace index 1 → 2
```

---

## Referência

```text
"faz isso de novo"
```

Esperado:

```text
reference = PREVIOUS_ACTION
```

---

## Expiração

Contexto antigo +:

```text
"abre o segundo"
```

Esperado:

```text
UNRESOLVED_REFERENCE
```

quando não houver lista válida.

---

# 52. Segurança de aprendizado

Nunca usar automaticamente como ground truth:

```text
"não houve reclamação"
```

Nunca promover padrão somente porque ocorreu várias vezes.

Nunca permitir que:

```text
predição da própria rede
```

vire:

```text
label verdadeiro
```

sem evidência externa.

---

# 53. Segurança de dados

O dataset deve evitar guardar desnecessariamente:

- segredos;
- tokens;
- senhas;
- credenciais;
- conteúdo pessoal sensível;
- caminhos sensíveis completos quando não forem necessários.

Preferir anonimização e normalização de slots.

Exemplo:

```text
"abre C:\Users\X\Documentos\segredo.txt"
```

pode virar:

```text
"abre <FILE_PATH>"
```

quando o texto real não for necessário para treinamento.

---

# 54. Observabilidade por domínio

Separar métricas:

```text
music
browser
files
system
IoT
windows
chat
search
```

Isso evita uma boa média global esconder um domínio ruim.

---

# 55. Métricas por risco

Também separar:

```text
LOW_RISK
REVERSIBLE
DESTRUCTIVE
```

False execution em ações destrutivas deve receber peso muito maior.

---

# 56. Dashboard futuro

Possíveis indicadores:

```text
Active Model
Dataset Version
Intent Accuracy
Slot F1
Multi-intent Recall
Negation Accuracy
OOD Recall
False Execution Rate
Missed Command Rate
Fallback Rate
LLM Calls Saved
p50 Latency
p95 Latency
p99 Latency
Corrections / day
Drift Score
```

---

# 57. Critério de eficiência

Uma rede mais complexa só entra se entregar benefício mensurável.

Exemplo:

```text
BiGRU 2 MB / 8 ms / 96%
vs
Transformer 40 MB / 30 ms / 96.2%
```

Talvez BiGRU seja melhor para a Laylay.

Eficiência também é requisito.

---

# 58. Princípio de expansão

Não adicionar capacidade só porque é interessante.

Nova capacidade precisa responder:

```text
qual erro real ela resolve?
como será medida?
qual regressão pode causar?
como será testada?
```

---

# 59. Quatro documentos centrais

Este documento é o plano geral.

Antes da implementação profunda, criar separadamente:

## 59.1 NEURAL_CONTRACT.md

Define:

- responsabilidade da rede;
- decisões proibidas;
- fronteira entre neural e determinístico;
- regras de fallback;
- risco;
- autoridade;
- segurança.

---

## 59.2 NEURAL_IR_SCHEMA.md

Define formalmente:

- UtterancePlan;
- Action;
- Slot;
- Reference;
- Relation;
- confidence;
- source spans;
- versionamento do schema.

---

## 59.3 NEURAL_DATASET_SPEC.md

Define:

- formato do exemplo;
- origem;
- label;
- confiança;
- anonimização;
- famílias linguísticas;
- splits;
- hard examples;
- corrections;
- replay.

---

## 59.4 NEURAL_EVALUATION.md

Define:

- suites;
- métricas;
- thresholds;
- Neural Chaos;
- promotion gate;
- rejection gate;
- regressivos;
- contrafactuais;
- segurança.

---

# 60. Estrutura de diretórios sugerida

```text
mente_laylay/
└── neural/
    ├── runtime/
    │   ├── interpreter.py
    │   ├── tokenizer.py
    │   ├── context_encoder.py
    │   ├── ir_builder.py
    │   ├── risk_gate.py
    │   └── model_loader.py
    │
    ├── schema/
    │   ├── utterance_plan.py
    │   ├── actions.py
    │   ├── references.py
    │   └── relations.py
    │
    ├── learning/
    │   ├── experience_buffer.py
    │   ├── fast_memory.py
    │   ├── trainer.py
    │   ├── replay_buffer.py
    │   └── promotion.py
    │
    ├── observability/
    │   ├── neural_logger.py
    │   ├── metrics.py
    │   ├── tracing.py
    │   └── drift.py
    │
    ├── models/
    ├── datasets/
    └── tests/
        ├── neural_chaos/
        ├── regressions/
        ├── counterfactuals/
        └── benchmarks/
```

Estrutura apenas inicial.

Não deve ser criada cegamente sem estudar a arquitetura real do repositório.

---

# 61. Fluxo completo final

```text
                         USER UTTERANCE
                               │
                               ▼
                    ┌────────────────────┐
                    │ Neural Interpreter │
                    └──────────┬─────────┘
                               │
                     ┌─────────┴─────────┐
                     ▼                   ▼
                   Known               OOD
                     │                   │
                     ▼                   ▼
              Canonical IR       Context Resolver
                     │                   │
                     │           unresolved?
                     │              /      \
                     │            no        yes
                     │            │          │
                     │            ▼          ▼
                     │           IR         LLM
                     │                       │
                     └──────────────┬────────┘
                                    ▼
                               Risk Gate
                                    │
                                    ▼
                                  Planner
                                    │
                                    ▼
                                   Guards
                                    │
                                    ▼
                                  Executor
                                    │
                                    ▼
                                  Receipt
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
             Observability                      Experience
                  │                                   │
          Logs / Metrics / Trace              Validation
                                                      │
                                        ┌─────────────┴────────────┐
                                        ▼                          ▼
                                  Fast Memory                Slow Learning
                                        │                          │
                                        │                    Candidate Model
                                        │                          │
                                        │                     Neural Chaos
                                        │                      /        \
                                        │                    PASS       RED
                                        │                     │          │
                                        └─────────────────────┤       Reject
                                                              ▼
                                                           Promote
```

---

# 62. Definição de sucesso

O projeto será considerado bem-sucedido quando a Laylay:

- compreender variações naturais sem depender de centenas de `if`;
- identificar vários comandos em uma única frase;
- entender correções e referências;
- diferenciar conversa de comando;
- tratar negação corretamente;
- usar menos chamadas ao LLM;
- responder em milissegundos em tarefas locais;
- aprender com correções reais;
- melhorar com o tempo sem destruir conhecimento antigo;
- explicar sua IR para debug;
- possuir rollback;
- provar qualidade com métricas;
- evitar execução indevida.

---

# 63. Regra final

> A Laylay não deve ficar mais autônoma porque a rede ficou mais confiante.
>
> Ela deve ficar mais natural porque a interpretação ficou melhor, enquanto a autoridade, os guards, o estado real e os receipts continuam determinísticos e auditáveis.

---

# 64. Estado atual do plano

Status:

```text
ARQUITETURA CONCEITUAL: quase fechada
IMPLEMENTAÇÃO: não iniciada
CONTRATOS FORMAIS: pendentes
DATASET: pendente
MODELO: pendente
SHADOW MODE: pendente
NEURAL CHAOS: pendente
```

Próximo passo recomendado:

```text
1. criar NEURAL_CONTRACT.md
2. criar NEURAL_IR_SCHEMA.md
3. criar NEURAL_DATASET_SPEC.md
4. criar NEURAL_EVALUATION.md
5. somente depois comparar arquiteturas de modelo
```

---

# 65. Filosofia do projeto

A meta não é construir "uma IA que sempre acha que sabe".

A meta é construir um sistema que:

```text
entende quando consegue
+
mede quando não consegue
+
não inventa autoridade
+
aprende com evidência
+
prova cada evolução
```

Essa deve ser a base da rede neural nativa da Laylay.

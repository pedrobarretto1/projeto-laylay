# Repository Guidelines

## Project Structure & Module Organization

`laylay.py` is the composition root; keep domain behavior out of it. New capabilities belong in `mente_laylay/`: `especialistas/` owns domain runtimes and the capability map, `cognicao/` interprets turns, `memoria_mental/` owns shared context and learning, `autonomia/` routes and executes actions, `percepcao/` observes input, and `integracao/` wires components. Clients live in `cliente/`, including the Xbox Game Bar widget. Persistent user state belongs in `memoria/`; never commit credentials from environment or Tuya/Gmail data. Tests mirror behavior in `tests/`.

## Build, Test, and Development Commands

- `python laylay.py` starts the assistant from source.
- `.\.venv314\Scripts\python.exe -m pytest -q` runs the complete suite with the project environment.
- `.\.venv314\Scripts\python.exe -m pytest tests\test_area_transferencia_inteligente.py -q` runs one module.
- `powershell -ExecutionPolicy Bypass -File .\empacotamento\build_portatil.ps1` builds the portable distribution.

## Mandatory Capability Integration Contract

Before implementing a capability, inventory existing shared services and reuse them. Do not create local substitutes for mechanisms already present. A capability is not complete until tests prove all applicable pillars:

1. **Context:** reads and publishes only necessary state through the shared mind.
2. **Memory:** distinguishes temporary context from durable, sourced memory.
3. **Learning:** sends acceptance, refusal, correction, repetition, and qualified silence to the shared learning engine.
4. **Natural language:** reuses the canonical turn/confirmation interpreters; domain code adds entities and verbs, not private yes/no phrase lists.
5. **Continuity:** supports natural references and repetition through the canonical pending-action channel.
6. **Safety:** separates discussion, suggestion, authorization, execution, and observed confirmation.
7. **Diagnostics:** reports health, failures, and verified results to the existing observability and capability maps.
8. **Capability awareness:** registers the capability in the live capability catalog so Laylay knows what it can do, how to invoke it naturally, what authorization it needs, what evidence confirms success, and what its limits are. The relevant entry must reach the LLM through contextual retrieval without bloating the permanent personality prompt. Laylay must answer natural questions about the capability truthfully and must never claim access that is unavailable at runtime.
9. **Cooperative orchestration:** when a useful result depends on more than one capability or data source, publishes the relationship to the canonical cooperation board and reuses the existing cooperative coordinator. Each participating capability keeps its own validation, authorization and confirmation; cooperation must not create a shortcut around an executor, duplicate private state or turn perception into permission. Tests must cover the combined path and prove that a partial failure cannot be reported as full success.

Add unit tests, a real composition-path regression test, a negative safety test, a cooperative-path test when the ninth pillar applies, and a capability-awareness test covering the live catalog and natural questions about the new ability. Mocks must not replace the shared component whose integration is being verified. Update `ROADMAP_NOVAS_HABILIDADES.md` only after those tests pass.

## Coding and Testing Conventions

Use Portuguese domain names consistently with surrounding code, type hints on new public APIs, and small runtime factories named `criar_*_runtime`. Preserve user changes in the dirty worktree. Use `apply_patch` for edits. Pytest is the project test runner; every bug fix needs a regression reproducing the user’s wording, plus nearby natural variants.

# INSTRUÇÕES PERSONALIZADAS — DESENVOLVIMENTO, CORREÇÃO E EVOLUÇÃO DA LAYLAY

Você está trabalhando no projeto Laylay, uma assistente pessoal em Python composta por diversos runtimes, módulos de integração, cognição, memória, automação, música, navegador, terminal, IoT, percepção, voz, contexto e outros subsistemas.

O objetivo não é simplesmente fazer testes ficarem verdes ou corrigir um caso isolado. O objetivo é melhorar a arquitetura da Laylay de maneira comprovável, segura, generalizável e coerente com o comportamento do runtime real.

As regras abaixo devem ser consideradas obrigatórias durante qualquer investigação, correção, refatoração ou melhoria.

---

# 1. PRINCÍPIO CENTRAL: NÃO CORRIGIR ANTES DE ENTENDER

Nunca crie um patch imediatamente após encontrar um sintoma.

Antes de alterar produção, estude profundamente o problema até conseguir explicar:

- qual comportamento ocorreu;
- qual comportamento deveria ocorrer;
- qual foi a primeira fronteira em que eles divergiram;
- qual estado entrou nessa fronteira;
- qual contrato arquitetural estava sendo aplicado;
- qual contrato deveria existir;
- qual componente possui autoridade para tomar aquela decisão;
- qual evidência confirma a hipótese;
- quais hipóteses concorrentes foram falsificadas.

Um stack trace, teste vermelho, fala errada ou comando que não executou é um sintoma.

A raiz somente pode ser declarada quando existir uma cadeia causal demonstrável.

Exemplo de raciocínio correto:

```text
entrada do usuário
→ classificação
→ contexto
→ autoridade
→ decisão
→ executor
→ receipt
→ estado resultante
→ resposta
```

A investigação deve localizar a primeira transição incorreta dessa cadeia.

Não começar pelo último erro visível.

---

# 2. PRIMEIRA FRONTEIRA RED MANDA NO DIAGNÓSTICO

Quando existir uma cadeia de operações, a primeira fronteira que entra em RED possui prioridade.

Exemplo:

```text
A → B → C → D
```

Se:

```text
A = GREEN
B = RED
C = RED
D = RED
```

não corrija C ou D primeiro.

A investigação deve começar em B.

Os erros posteriores podem ser apenas consequências.

Regra:

```text
primeira fronteira RED > último sintoma observado
```

---

# 3. RUNTIME REAL > HARNESS > MOCK

Sempre priorizar evidência proveniente do runtime real.

Hierarquia:

```text
runtime real
>
integração usando componentes reais
>
teste arquitetural
>
teste unitário
>
mock
>
hipótese
```

Mocks são úteis para provar contratos locais, mas nunca devem substituir a validação no runtime real quando o defeito ocorreu em produção.

Um teste isolado verde não prova necessariamente que a Laylay real está corrigida.

Um harness também pode esconder diferenças de:

- composição;
- estado;
- callbacks;
- autoridade;
- ordem de execução;
- dependências;
- concorrência;
- persistência;
- eventos assíncronos.

Sempre que possível, finalizar uma correção com uma prova no caminho real usado pela Laylay.

---

# 4. HARNESS NÃO É PRODUÇÃO

Nunca declarar uma raiz corrigida apenas porque um teste artificial ficou verde.

Separar claramente:

```text
GREEN unitário
GREEN integração
GREEN runtime real
GREEN regressão ampla
```

Um verde intermediário é somente evidência intermediária.

Regra:

```text
verde intermediário ≠ raiz corrigida
```

---

# 5. CONGELAR A BASE DA INVESTIGAÇÃO

Antes de investigar um RED importante, registrar:

- commit atual;
- branch;
- arquivos modificados;
- arquivos não rastreados relevantes;
- estado da worktree.

Nunca assumir que o código do Git representa exatamente o runtime que produziu um log histórico.

Sempre verificar:

```powershell
git rev-parse HEAD
git status --short
```

Se necessário:

```powershell
git diff -- arquivo.py
```

Nunca atualizar um lock, snapshot ou HEAD de referência apenas porque o código mudou.

O baseline só deve mudar quando a investigação justificar a mudança.

---

# 6. NUNCA APAGAR OU SOBRESCREVER WORKTREE SEM AUTORIZAÇÃO

A worktree da Laylay frequentemente contém:

- testes experimentais;
- candidatos;
- scripts de falsificação;
- patches;
- arquivos ainda não commitados;
- melhorias paralelas.

Portanto, nunca executar automaticamente:

```text
git reset
git reset --hard
git checkout .
git restore .
git clean
git pull
git rebase
```

ou qualquer operação destrutiva sem autorização explícita.

Trabalho não commitado deve ser tratado como informação importante.

---

# 7. NÃO CONFUNDIR CONTEXTO COM AUTORIDADE

Uma informação presente no contexto não significa que ela autoriza uma ação.

Regra:

```text
contexto ≠ autoridade
```

Exemplo:

A Laylay lembrar que uma playlist foi mencionada não significa que ela está autorizada a apagar, alterar ou reutilizar aquela playlist.

Sempre identificar:

- quem forneceu a autorização;
- para qual ação;
- para qual alvo;
- por quanto tempo;
- em qual contexto;
- se essa autorização ainda é válida.

---

# 8. NÃO CONFUNDIR CONTEXTO COM PROVA DE EFEITO

Uma intenção reconhecida ou um contexto coerente não prova que a ação aconteceu.

Regra:

```text
contexto ≠ prova de efeito
```

Exemplo:

```text
intenção = DELETE_FILE
```

não significa:

```text
arquivo apagado
```

Somente um receipt confiável do executor pode confirmar o efeito.

---

# 9. CONTRATO FUNDAMENTAL DE EXECUÇÃO

Usar como princípio arquitetural:

```text
utterance = permission
receipt = target
executor = effect
```

Interpretação:

### Utterance / fala do usuário

Define autorização ou intenção.

Exemplo:

```text
"apaga esse arquivo"
```

### Receipt / confirmação verificável

Confirma qual alvo será afetado ou qual operação realmente foi materializada.

### Executor

Produz o efeito no mundo externo ou estado persistente.

Nunca inverter essas responsabilidades.

---

# 10. ÚLTIMA AÇÃO NÃO É O MESMO QUE ÚLTIMO EFEITO REVERSÍVEL

Nunca assumir:

```text
última ação = último efeito reversível válido
```

Uma ação pode:

- falhar;
- não produzir efeito;
- produzir somente leitura;
- ser idempotente;
- afetar outro domínio;
- produzir um efeito não reversível.

Sempre registrar efeitos reais separadamente de intents e comandos.

---

# 11. TESTAR ARQUITETURA, NÃO SOMENTE O TURNO HISTÓRICO

Quando um bug surgir no turno X, não escrever apenas:

```text
test_turno_151()
```

Identificar o contrato geral quebrado.

Exemplo:

Bug histórico:

```text
playlist "vmz"
→ confirmação
→ falha
```

Contrato real:

```text
uma oferta que promete criar um alvo inexistente
→ confirmação do usuário
→ alvo deve ser materializado
→ receipt da criação deve ser validado
→ somente então executar a escrita
```

O teste deve proteger a arquitetura contra futuras ocorrências em outras playlists, nomes e contextos.

---

# 12. UMA ROOT → UM CONTRATO CANÔNICO

Evitar múltiplos patches locais para o mesmo problema.

Quando vários defeitos possuem a mesma causa conceitual, criar um contrato arquitetural comum.

Exemplo ruim:

```text
patch especial para playlist
patch especial para arquivo
patch especial para nota
patch especial para navegador
```

se todos sofrem do mesmo problema de autorização ou receipt.

Preferir:

```text
um contrato canônico de resolução/autorização/execução
```

utilizado pelos diversos domínios.

---

# 13. FALSIFICAR HIPÓTESES ANTES DO PATCH

Antes de aplicar um candidato, tentar provar que a hipótese está errada.

Para bugs importantes, falsificar pelo menos duas explicações concorrentes quando houver alternativas plausíveis.

Exemplo:

Hipótese:

```text
playlist não salvou porque nome curto é inválido
```

Falsificação:

```text
create("vmz") funciona
```

Logo:

```text
nome curto não é inválido no domínio
```

Isso evita corrigir a camada errada.

---

# 14. NÃO TRANSFORMAR UMA RESTRIÇÃO ÚTIL EM BUG

Antes de remover uma regra existente, descobrir por que ela existe.

Exemplo:

```python
if len(nome) < 4:
    return ""
```

Pode parecer a raiz.

Mas talvez a regra seja útil para impedir resolução ambígua.

Nesse caso, não remover a proteção.

Corrigir a arquitetura que está usando um resolver de leitura no contexto errado.

Sempre perguntar:

```text
a regra está errada
OU
a regra correta está sendo usada pela operação errada?
```

---

# 15. SEPARAR LOOKUP, CRIAÇÃO, RESOLUÇÃO E ESCRITA

Operações diferentes devem possuir semânticas diferentes.

Exemplo:

```text
resolver referência existente
≠
criar alvo
≠
materializar alvo autorizado
≠
escrever no alvo
```

Evitar transformar uma função de lookup contextual em mecanismo universal de criação.

Quando o usuário explicitamente autorizar criação, usar a operação canônica de criação.

---

# 16. RECEIPT ANTES DO PRÓXIMO EFEITO

Operações compostas devem validar o resultado de cada etapa.

Exemplo:

```text
CREATE
→ receipt
→ ADD
```

Correto:

```text
CREATE
↓
ok=True
↓
ADD
```

Se:

```text
CREATE
↓
ok=False
```

então:

```text
NÃO executar ADD
```

Isso é fail-closed.

Nunca fazer:

```python
criar()
adicionar()
```

ignorando o resultado da criação.

---

# 17. FAIL-CLOSED

Quando uma etapa necessária falhar, operações dependentes não devem continuar.

Exemplo:

```text
criação da playlist falhou
→ não adicionar faixa
```

Outro exemplo:

```text
arquivo não foi localizado
→ não apagar outro arquivo parecido
```

Outro:

```text
receipt do dispositivo falhou
→ não anunciar sucesso
```

---

# 18. NÃO PRODUZIR CONFIRMAÇÕES FALSAS

A Laylay nunca deve dizer:

```text
"pronto"
"feito"
"salvei"
"apaguei"
"abri"
```

sem receipt que confirme o efeito.

Separar claramente:

```text
tentativa
≠
efeito confirmado
```

---

# 19. TRATADO=True PRECISA TER CONCLUSÃO COERENTE

Uma entrada consumida como tratada não pode desaparecer silenciosamente.

Se:

```text
tratado=True
```

o turno precisa possuir uma conclusão observável apropriada.

Pode ser:

- fala;
- resposta textual;
- receipt operacional publicado;
- ação assíncrona claramente registrada;
- outro efeito observável definido pelo contrato.

Nunca permitir:

```text
input consumido
+
pendência removida
+
pipeline encerrado
+
nenhum efeito
+
nenhuma resposta
```

Isso gera silent handled turn.

---

# 20. PENDÊNCIAS DEVEM POSSUIR CICLO DE VIDA EXPLÍCITO

Toda pendência deve ter:

- origem;
- tipo;
- domínio;
- alvo;
- timestamp;
- TTL;
- autoridade;
- estado;
- regra de consumo;
- regra de expiração;
- regra de cancelamento.

Comandos independentes não devem destruir pendências não relacionadas.

Confirmações devem resolver a pendência correta.

---

# 21. COMANDO NOVO NÃO É CONFIRMAÇÃO FORÇADA

Uma nova instrução não deve ser reinterpretada automaticamente como resposta de uma sugestão anterior.

Exemplo:

```text
Laylay: quer salvar essa música?
Usuário: mostra minhas playlists
```

Isso não significa:

```text
sim
```

A nova instrução deve seguir seu próprio fluxo.

---

# 22. PENDÊNCIA DEVE SOBREVIVER A TURNOS INTERMEDIÁRIOS QUANDO O CONTRATO EXIGIR

Se uma oferta continua válida:

```text
turno 146 → oferta
turnos 147-150 → comandos independentes
turno 151 → "sim"
```

os comandos intermediários não devem destruir a oferta sem motivo arquitetural.

Sempre testar sobrevivência quando o bug envolver continuidade contextual.

---

# 23. NÃO CORRIGIR O HARNESS PARA FAZER O BUG SUMIR

Se um teste reproduzir um problema real, não enfraquecer o teste apenas para fazê-lo passar.

Modificar testes somente quando:

- o contrato esperado estava errado;
- o teste representava uma arquitetura falsa;
- nova evidência mostrou que a expectativa original era incorreta.

Quando isso acontecer, documentar o motivo.

---

# 24. RED ANTES DO CANDIDATO

Fluxo preferido:

```text
1. reproduzir
2. encontrar primeira fronteira RED
3. falsificar hipóteses
4. declarar contrato
5. criar RED canônico
6. confirmar RED
7. aplicar candidato mínimo
8. confirmar GREEN
9. rodar regressivos
10. testar runtime real
```

Nunca inverter essa ordem sem necessidade.

---

# 25. CANDIDATO MÍNIMO

O primeiro patch deve modificar somente a menor fronteira arquitetural necessária.

Evitar:

- refatoração ampla junto com bugfix;
- renomear módulos;
- alterar APIs não relacionadas;
- formatar arquivos inteiros;
- “aproveitar” para limpar código;
- corrigir vários defeitos diferentes no mesmo patch.

Primeiro corrigir o contrato.

Depois fazer melhorias separadas.

---

# 26. NÃO PRODUZIR VERDE ACIDENTAL

Se um teste fica verde por causa de uma alteração antiga na worktree, identificar isso.

Sempre comparar:

```text
HEAD
vs
worktree
```

Um teste verde pode significar:

- bug corrigido;
- candidato antigo ainda aplicado;
- harness incorreto;
- branch diferente;
- arquivo importado diferente;
- comportamento mascarado.

Nunca interpretar GREEN isoladamente.

---

# 27. REGRESSIVOS DEVEM PROTEGER COMPORTAMENTOS VIZINHOS

Toda correção deve testar não apenas o caso que falhou, mas também casos próximos.

Exemplo de playlists:

```text
playlist curta inexistente
playlist curta existente
playlist longa inexistente
duplicata
abreviação ambígua
create explícito
falha de criação
falha de add
corrida onde alvo passa a existir antes da confirmação
```

O objetivo é provar que o patch não destruiu contratos legítimos.

---

# 28. CONTROLES INTERNOS

Quando possível, usar operações semelhantes que já funcionam no mesmo runtime como controle.

Exemplo:

Se:

```text
turno 148 → ADD funciona
turno 149 → ADD funciona
turno 151 → ADD falha
```

isso ajuda a falsificar uma falha geral do armazenamento.

Comparações internas do mesmo processo são evidências fortes.

---

# 29. LOG NÃO É EFEITO

Logs podem provar que uma função foi chamada.

Mas:

```text
log "executando"
```

não prova:

```text
efeito executado
```

Sempre procurar receipt.

---

# 30. OBSERVABILIDADE DEVE AJUDAR O DIAGNÓSTICO

Quando um defeito for difícil de provar, adicionar temporariamente observabilidade específica pode ser aceitável.

Mas evitar logs ruidosos globais.

Logs úteis devem responder perguntas como:

```text
qual pendência?
qual autoridade?
qual alvo?
qual executor?
qual receipt?
qual estado antes?
qual estado depois?
```

---

# 31. NÃO MISTURAR ROOTS

Se durante uma investigação surgir outro defeito, registrá-lo separadamente.

Exemplo:

```text
RED151
```

não deve virar:

```text
RED151 + clipboard spam + UI + IoT + fila musical
```

Investigações diferentes devem permanecer isoladas.

---

# 32. ALTERAÇÕES PARALELAS DA WORKTREE NÃO PERTENCEM AUTOMATICAMENTE AO BUG

A worktree pode conter mudanças em:

- terminal;
- UI;
- IoT;
- Chrome;
- música;
- testes;
- voz.

Não assumir que fazem parte da investigação atual.

Filtrar o diff pelos arquivos causalmente relevantes.

---

# 33. NÃO ATUALIZAR HEAD ESPERADO DE UM SCRIPT CEGAMENTE

Scripts de candidato podem possuir:

```python
HEAD_ESPERADO = "..."
```

Se o HEAD mudar, não substituir simplesmente o valor.

Primeiro verificar:

- o bloco causal ainda existe?
- a arquitetura mudou?
- o patch continua válido?
- houve alterações concorrentes?

A trava existe justamente para impedir aplicação sobre base diferente.

---

# 34. APLICADORES DEVEM SER FAIL-CLOSED

Quando criar um script que modifica produção:

- validar HEAD;
- validar arquivo;
- verificar que o bloco antigo aparece exatamente uma vez;
- verificar que o candidato ainda não está aplicado;
- criar backup;
- alterar somente o bloco esperado;
- reler o arquivo;
- confirmar que o bloco antigo desapareceu;
- confirmar que o novo apareceu exatamente uma vez;
- não criar commit automaticamente.

Se qualquer guarda falhar:

```text
ABORTAR
```

sem alteração parcial.

---

# 35. ENTREGA DE MODIFICAÇÕES DE ARQUIVO

Sempre que for necessário modificar um arquivo do projeto, não responder apenas com instruções vagas como:

```text
"adicione isso na linha X"
```

ou:

```text
"troque esse bloco"
```

Preferir uma destas duas formas:

### Forma A — arquivo completo pronto

Entregar o arquivo já modificado para substituição.

### Forma B — script PowerShell seguro

Entregar um código PowerShell que:

- localize o arquivo;
- valide o bloco esperado;
- faça backup quando apropriado;
- modifique o trecho;
- confirme a alteração;
- aborte se o estado não for o esperado.

Quando o arquivo for pequeno ou a alteração extensa, preferir o arquivo pronto.

Quando a alteração for localizada em um arquivo grande, preferir o PowerShell/applicador seguro.

Nunca deixar Pedro fazer edição manual delicada quando isso puder ser automatizado de forma segura.

---

# 36. NÃO CRIAR ARQUIVOS DESNECESSÁRIOS

Apesar da regra anterior, não gerar arquivos apenas por gerar.

Criar arquivo quando ele tiver função clara:

- teste;
- candidato;
- diagnóstico;
- handoff;
- patch;
- artefato necessário.

Evitar acumular scripts temporários sem necessidade.

---

# 37. TESTE DEVE FALHAR PELO MOTIVO CERTO

Um RED válido não é simplesmente qualquer falha.

O teste deve alcançar a fronteira desejada.

Exemplo incorreto:

```text
queremos testar ADD
mas o teste falha porque import está quebrado
```

Isso não é prova do contrato.

Sempre verificar a mensagem de falha.

---

# 38. PRIMEIRA ASSERÇÃO CAUSAL NO TESTE COMPOSTO

Em testes de integração, ordenar asserções pela cadeia causal.

Exemplo:

```text
pendência criada?
↓
sobreviveu?
↓
confirmação reconhecida?
↓
CREATE aconteceu?
↓
CREATE confirmou?
↓
ADD aconteceu?
↓
ADD confirmou?
↓
resposta aconteceu?
↓
estado foi limpo?
```

Assim a primeira asserção vermelha indica a primeira fronteira causal.

---

# 39. NÃO ESCONDER ERRO COM FALLBACK

Fallbacks não devem transformar falha real em sucesso aparente.

Exemplo:

```text
executor falhou
→ LLM responde "feito"
```

Isso é proibido.

Fallback pode explicar a falha, mas não falsificar o receipt.

---

# 40. DIFERENCIAR IDPOTÊNCIA DE FALHA

Operações repetidas podem continuar sendo sucesso.

Exemplo:

```text
faixa já existe
```

pode ser:

```text
ok=True
added=False
duplicated=True
```

Não transformar idempotência em erro.

---

# 41. TESTAR CORRIDAS BENIGNAS

Estado pode mudar entre oferta e confirmação.

Exemplo:

```text
Laylay oferece criar vmz
↓
outro fluxo cria vmz
↓
usuário responde sim
```

O sistema deve continuar correto.

Uma operação CREATE idempotente é preferível a lógica especial baseada em suposição antiga.

---

# 42. ESTADO COMPARTILHADO DEVE TER DONO CLARO

Ao investigar continuidades, memória, estado musical ou contexto:

- descobrir onde o estado nasce;
- descobrir onde é armazenado;
- mapear getters;
- mapear setters;
- mapear updates;
- procurar substituições integrais;
- verificar se existem duas cópias divergentes.

Nunca assumir que dois nomes semelhantes apontam para o mesmo estado.

---

# 43. NÃO CONFIAR CEGAMENTE NA BUSCA DE CÓDIGO

Se GitHub search ou outra indexação retornar vazio com índice incompleto, isso não prova ausência.

Preferir:

- fetch direto de arquivo conhecido;
- árvore do commit;
- grep local;
- chamadas concretas;
- composição.

---

# 44. CÓDIGO DE COMPOSIÇÃO É PARTE DA ROOT

Em sistemas modulares como Laylay, uma função isolada pode estar correta enquanto sua composição está errada.

Sempre verificar:

```text
quem instancia?
quem registra?
quem injeta?
qual callback real?
qual estado real?
```

---

# 45. COMPOSIÇÃO MANUAL ≠ RUNTIME REAL

Um teste que manualmente conecta:

```text
A + B + C
```

não prova que produção conecta:

```text
A + B + C
```

Verificar o composition root real.

---

# 46. NÃO PATCHAR UMA PORTA QUANDO O ORQUESTRADOR É O DONO

Se uma sequência é responsabilidade de um orquestrador:

```text
CREATE
→ ADD
```

não empurrar essa regra para o armazenamento apenas para facilitar.

Cada camada deve manter sua responsabilidade.

---

# 47. EFEITOS EXTERNOS DEVEM SER CONFIRMADOS

Para:

- arquivos;
- Chrome;
- IoT;
- playlists;
- aplicações;
- terminal;
- sistema operacional;

sempre preferir:

```text
executar
→ confirmar
→ responder
```

em vez de:

```text
executar
→ assumir
→ responder
```

---

# 48. FALHA NÃO PODE SER SILENCIOSA

Se uma operação pedida pelo usuário falhar e o turno for consumido, a Laylay deve comunicar a falha de forma apropriada.

Nunca transformar:

```text
ok=False
```

em:

```text
return True
```

sem uma conclusão observável.

---

# 49. TESTAR SUCESSO E FALHA

Para cada novo fluxo importante:

```text
success path
failure path
idempotent path
ambiguous path
stale-state path
```

quando aplicáveis.

---

# 50. NÃO ALTERAR MAIS DOMÍNIOS QUE O NECESSÁRIO

Se uma correção precisa alterar apenas:

```text
fluxos_conversa.py
```

não alterar:

```text
playlist_runtime.py
playlist_mental.py
laylay.py
```

sem uma justificativa causal.

---

# 51. PROVAR QUE O PATCH NÃO QUEBROU O RESTO

Depois do GREEN focado:

1. testes do contrato;
2. regressivos do módulo;
3. integração;
4. runtime real;
5. suíte ampla relevante.

O chaos completo deve ser usado como regressão ampla depois que a arquitetura já estiver entendida.

Não usar caos de centenas de turnos como primeira ferramenta de descoberta quando existe um RED focado melhor.

---

# 52. CAOS É REGRESSÃO AMPLA, NÃO SUBSTITUTO DE DIAGNÓSTICO

Se um chaos retornar 14 falhas, agrupar por raiz.

Não assumir:

```text
14 falhas = 14 bugs
```

Pode existir:

```text
1 raiz → 8 sintomas
2 raiz → 4 sintomas
3 raiz → 2 sintomas
```

Resolver por famílias causais.

---

# 53. PRESERVAR O HISTÓRICO DA INVESTIGAÇÃO

Quando uma investigação for longa, manter um handoff com:

- commit;
- hipótese atual;
- hipóteses falsificadas;
- testes;
- resultados;
- artefatos;
- próxima fronteira.

Isso evita reconstruir raciocínio do zero.

---

# 54. NÃO DECLARAR ROOT COM LINGUAGEM MAIS FORTE QUE A EVIDÊNCIA

Usar níveis claros:

```text
suspeita
hipótese
fortemente sustentada
provada por código
reproduzida
GREEN unitário
GREEN integração
GREEN runtime
encerrada
```

Evitar dizer:

```text
"definitivamente"
```

quando ainda faltar a prova real.

---

# 55. SE UMA PREMISSA CAIR, REFAZER O DIAGNÓSTICO

Nunca defender uma hipótese antiga por apego.

Se um teste mostrar:

```text
hipótese X estava errada
```

atualizar imediatamente o modelo causal.

Falsificação é progresso.

---

# 56. DIFERENCIAR BUG HISTÓRICO DE BUG ATUAL

Pode acontecer:

```text
baseline commit → bug
worktree atual → candidato já aplicado
```

Nesse caso:

- preservar o baseline;
- reconhecer que o teste atual pode ficar verde;
- usar diff para provar o candidato;
- não interpretar GREEN como inexistência histórica do bug.

---

# 57. MELHORIAS TAMBÉM PRECISAM DE CONTRATO

Mesmo quando não existir bug, uma melhoria deve responder:

- qual problema arquitetural resolve?
- quem é o dono da responsabilidade?
- qual contrato novo cria?
- quais regressões podem acontecer?
- qual teste prova o benefício?

Evitar features acopladas por conveniência.

---

# 58. NÃO DUPLICAR INTELIGÊNCIA ENTRE CAMADAS

Se a cognição já resolveu:

```text
alvo
autoridade
intenção
```

não fazer outro parser independente no executor salvo necessidade explícita.

Evitar múltiplas fontes de verdade.

---

# 59. DONO ÚNICO POR DECISÃO

Sempre que possível:

```text
uma decisão
→ um owner canônico
```

Evitar:

```text
roteador decide
executor decide de novo
fallback decide diferente
LLM decide novamente
```

Isso gera divergência.

---

# 60. LLM NÃO DEVE SUBSTITUIR RECEIPTS

A LLM pode:

- interpretar;
- explicar;
- conversar;
- contextualizar.

Mas não deve inventar confirmação de efeito externo.

---

# 61. A CORREÇÃO DEVE SER GENERALIZÁVEL

Nunca escrever correção específica para:

```text
"vmz"
turno 151
texto exato "sim"
```

A correção deve proteger:

```text
qualquer playlist inexistente
qualquer nome permitido
qualquer confirmação válida
qualquer estado equivalente
```

O histórico é somente uma instância do contrato.

---

# 62. CORREÇÕES NÃO DEVEM CRIAR EXCEÇÕES HISTÓRICAS

Evitar código como:

```python
if playlist == "vmz":
```

ou regras baseadas em números de turno.

Isso é proibido salvo fixture de teste.

---

# 63. PREFERIR CONTRATOS EXPLÍCITOS A HEURÍSTICAS OCULTAS

Quando existir autoridade explícita:

```text
pendência de criação
```

preferir isso a inferir novamente pela linguagem.

---

# 64. MELHORIA LOCAL DEVE FORTALECER A ARQUITETURA GLOBAL

Ao corrigir um domínio, procurar o princípio arquitetural reutilizável.

Exemplo:

O bug aconteceu em playlist, mas o aprendizado pode ser:

```text
operações compostas precisam validar receipt antes do próximo efeito
```

Esse contrato também pode beneficiar:

- arquivos;
- IoT;
- navegador;
- notas;
- aplicativos;
- rotinas;
- modos;
- memória;
- automações.

Não significa alterar todos esses domínios no mesmo patch.

Significa projetar a correção para que o princípio seja reutilizável e não criar mais uma exceção exclusiva.

---

# 65. NÃO GENERALIZAR CEGAMENTE DURANTE O PATCH

Existe diferença entre:

```text
arquitetura generalizável
```

e:

```text
patch gigante em todos os módulos
```

Primeiro provar a abstração no domínio atual.

Depois expandi-la cuidadosamente para outros módulos quando apropriado.

---

# 66. PADRÃO DE COMUNICAÇÃO DURANTE INVESTIGAÇÃO

Ao reportar progresso:

1. dizer o que foi provado;
2. dizer o que foi falsificado;
3. dizer o que ainda não sabemos;
4. dizer qual é a próxima fronteira;
5. não misturar hipótese com fato.

Exemplo:

```text
PROVADO:
A pendência é criada.

FALSIFICADO:
Timeout não apaga a pendência.

AINDA ABERTO:
Qual writer altera o estado entre os turnos.

PRÓXIMA FRONTEIRA:
Mapear continuidades_update.
```

---

# 67. QUANDO UM TESTE SURPREENDER, PARAR O PATCH

Se o resultado esperado era:

```text
RED
```

e veio:

```text
GREEN
```

não continuar automaticamente.

Descobrir por quê.

Pode existir:

- candidato antigo;
- código diferente;
- fixture incorreta;
- import diferente;
- contrato mal formulado.

Resultados inesperados são dados.

---

# 68. USAR O DIFF COMO EVIDÊNCIA

Quando runtime local e Git divergirem:

```powershell
git diff -- arquivo.py
```

é evidência importante.

Não assumir que o HEAD representa a worktree.

---

# 69. CANDIDATO DEVE TER ESCOPO DECLARADO

Ao aplicar um patch, declarar:

```text
Produção alterada:
- arquivo X

Produção não alterada:
- arquivo Y
- resolver Z

Nenhum commit criado.
```

Isso facilita auditoria.

---

# 70. BACKUP NÃO SUBSTITUI GIT, MAS PROTEGE EXPERIMENTOS

Scripts de candidato podem salvar backup local antes de alteração.

Mas não usar backup como desculpa para operações destrutivas.

---

# 71. NOMES DOS TESTES DEVEM DESCREVER CONTRATOS

Preferir:

```text
test_confirmacao_de_playlist_inexistente_deve_criar_antes_de_adicionar
```

em vez de:

```text
test_bug_151
```

O primeiro continuará útil anos depois.

---

# 72. TESTES HISTÓRICOS PODEM EXISTIR COMO INTEGRAÇÃO

É aceitável manter um teste:

```text
turno 146 → 151
```

como integração histórica.

Mas ele deve ser acompanhado dos contratos menores que explicam por que ele funciona.

---

# 73. NÃO USAR SUCESSO DO COMPOSTO PARA ESCONDER RED UNITÁRIO LEGÍTIMO

Se o composto fica GREEN porque alguma camada compensou um erro interno, investigar.

Uma arquitetura saudável não deveria depender de compensações silenciosas.

---

# 74. RESULTADO FINAL DA CORREÇÃO

Uma correção só deve ser considerada encerrada quando houver evidência suficiente de:

```text
raiz encontrada
+
contrato definido
+
RED reproduzido
+
candidato mínimo
+
GREEN focado
+
regressivos verdes
+
runtime real validado
+
nenhuma regressão relevante
```

---

# 75. PRINCÍPIO MAIS IMPORTANTE PARA EVOLUÇÃO DA LAYLAY

A Laylay não deve evoluir por coleção de remendos.

Ela deve evoluir por contratos arquiteturais.

Cada bug deve ser tratado como uma oportunidade de descobrir:

```text
qual regra geral estava faltando?
```

Não apenas:

```text
qual if precisamos adicionar?
```

---

# REGRA FINAL — OBRIGATÓRIA

Uma correção ou melhoria não deve existir apenas para fazer uma habilidade específica funcionar.

Ao corrigir um problema em música, arquivos, navegador, IoT, voz, memória, terminal ou qualquer outro domínio, identificar qual princípio arquitetural geral foi descoberto e como ele pode fortalecer o restante da Laylay.

Isso não significa editar todas as habilidades em cada patch.

Significa que a solução deve nascer de um contrato reutilizável, coerente e aplicável ao sistema como um todo, evitando exceções específicas de domínio sempre que o problema possuir natureza geral.

Exemplos de contratos globais:

```text
autoridade explícita antes de efeito
receipt antes de confirmação
fail-closed em operações compostas
owner único por decisão
pendências com ciclo de vida
tratado=True precisa de conclusão observável
estado real > inferência
executor confirma efeito
```

Esses contratos devem ser utilizados progressivamente pelas diferentes habilidades da Laylay.

Uma correção que apenas mascara o sintoma de uma habilidade, enquanto outras continuam vulneráveis ao mesmo padrão arquitetural, deve ser considerada incompleta.

**Uma correção deve beneficiar todas as habilidades e não apenas a que está sendo corrigida.**
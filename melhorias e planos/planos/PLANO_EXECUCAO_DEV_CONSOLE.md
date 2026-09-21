# Plano de execução — Laylay DEV Console

## 1. Objetivo

Transformar a aba **DEV Console** na fonte principal de diagnóstico da Laylay, substituindo o terminal Python externo para observação, investigação de falhas e execução controlada de testes.

O resultado final deve permitir acompanhar a cadeia real:

```text
entrada
→ interpretação
→ contexto
→ autoridade
→ decisão
→ executor
→ receipt
→ estado resultante
→ resposta
```

O DEV Console deve apontar a primeira fronteira que divergiu, sem confundir intenção, log de tentativa ou retorno de função com efeito confirmado.

## 2. Contratos obrigatórios

1. **Observar não autoriza agir.** Consultas e inspeções permanecem somente leitura.
2. **Controle é um canal separado.** Testes, caos, reconexões e qualquer ação ficam atrás de autorização explícita e executor controlado.
3. **Receipt antes de sucesso.** A interface só exibe `CONFIRMED` quando houver evidência verificável.
4. **Fail-closed.** Se uma etapa necessária falhar, nenhuma etapa dependente continua.
5. **Um evento, um formato canônico.** A interface consome eventos estruturados, sem aprender regras privadas de cada habilidade.
6. **Segredos nunca chegam à tela.** Sanitização ocorre no núcleo e novamente na fronteira do bridge.
7. **Observabilidade não pode travar a Laylay.** Filas e históricos são limitados; a interface nunca bloqueia o runtime.
8. **Runtime real é a prova final.** Teste unitário e harness são evidências intermediárias.

## 3. Estado atual — concluído

Já existe uma primeira versão operacional com:

- página visual integrada ao Terminal 3.0;
- espelho de `stdout` e `stderr`, preservando a saída original;
- recepção ao vivo pelo desktop bridge;
- buffer limitado em memória;
- filtros por categoria e nível;
- taxonomia canônica compartilhada entre núcleo e interface, na qual `category`
  identifica o owner/domínio e `level` identifica a gravidade;
- modos `LIVE` e `PAUSED`;
- comandos `status`, `perf`, `errors`, `trace` e `inspect`;
- separação entre pendência conversacional e ação canônica;
- destaque da primeira fronteira explicitamente RED;
- tratamento de estado sem evidência como `UNVERIFIED`;
- bloqueio de Python, PowerShell e shell arbitrários;
- sanitização de credenciais, tokens e caminho pessoal;
- cartões de habilidades inexistentes marcados como **Em manutenção**;
- testes de núcleo, bridge, socket real e página PySide6.

Em 2026-09-04, a captura textual e os eventos nativos da interface passaram a
usar o mesmo classificador canônico. Falas e estados de geração pertencem a
`IA`; decisões de plano a `ROUTER`; receipts de executor a `AUTONOMY`; transporte
e sincronização a `SYSTEM`. Um aviso de fala, por exemplo, permanece
`category=IA` com `level=warning`, sem transformar gravidade em autoria.

### Limitações atuais

- parte dos eventos ainda nasce da interpretação de texto emitido por `print`;
- nem todo turno possui um `trace_id` canônico de ponta a ponta;
- `trace` só consegue explicar profundamente as fronteiras que publicam dados suficientes;
- a busca e os filtros avançados ainda não existem;
- não há persistência rotativa nem exportação de pacote de diagnóstico;
- execução de testes e caos ainda não foi liberada pela interface;
- `INSANE`, Event Bus Inspector e profiler profundo ainda não existem;
- não existe autorreparo; isso é uma capacidade futura e separada.

## 4. Ordem de implementação

Cada etapa só começa depois que a anterior estiver GREEN nos testes focados e regressivos relevantes.

### Etapa 0 — congelar e documentar a base

Antes de cada ciclo:

1. registrar commit, branch e `git status --short`;
2. identificar arquivos já alterados pelo usuário;
3. separar mudanças do DEV Console de alterações paralelas;
4. registrar o comportamento atual e a lacuna que será atacada;
5. criar primeiro um teste RED que alcance a fronteira correta.

**Saída:** baseline reproduzível e nenhuma alteração alheia sobrescrita.

### Etapa 1 — contrato canônico de eventos estruturados

Criar um envelope comum, versionado, para observabilidade:

```text
schema_version
event_id
timestamp
level
category
event
trace_id
turn_id
source
message
data
duration_ms
status
receipt_id
```

Passos:

1. definir o tipo canônico e seu validador;
2. manter compatibilidade temporária com logs textuais;
3. rejeitar ou degradar com clareza eventos malformados;
4. sanitizar campos recursivamente;
5. garantir ordenação e deduplicação por `event_id`;
6. medir descarte quando o buffer atingir o limite.

**Critério de aceite:** a UI recebe o mesmo contrato independentemente do módulo de origem, sem conhecer detalhes privados da habilidade.

### Etapa 2 — trace real de ponta a ponta

Instrumentar primeiro o caminho canônico do turno, sem espalhar parsers diferentes pelos domínios.

Passos:

1. gerar `trace_id` na entrada do turno;
2. propagar o ID por contexto, roteador, política, planejador, executor e verificação;
3. registrar estado de entrada e saída somente quando necessário;
4. diferenciar `EXECUTED`, `CONFIRMED`, `UNVERIFIED`, `FAILED` e `BLOCKED`;
5. associar ação e receipt sem usar “última ação” como prova;
6. calcular a primeira fronteira explicitamente RED;
7. exibir fronteiras posteriores como consequência, não como raiz;
8. suportar `trace last`, `trace errors`, `trace turn <n>` e `trace <id>`.

**Critério de aceite:** um turno real pode ser reconstruído em ordem causal e o primeiro RED apontado possui evidência do componente que tomou a decisão.

### Etapa 3 — Explorer de eventos e pesquisa

Adicionar investigação rápida sem pausar a Laylay.

Passos:

1. implementar `events last <n>`;
2. implementar `events <categoria>` e `events errors`;
3. adicionar busca textual por mensagem, origem, turno e trace;
4. adicionar filtros combinados, por exemplo `category:ROUTER turn:151`;
5. mostrar contador de eventos recebidos enquanto a tela estiver pausada;
6. preservar posição de rolagem e oferecer retorno ao final;
7. limitar resultados e indicar quando houve truncamento.

**Critério de aceite:** localizar um erro, seu trace e todos os eventos relacionados sem procurar manualmente em centenas de linhas.

### Etapa 4 — Central de Falhas semântica

Evoluir `errors` de agrupamento textual para diagnóstico baseado em contrato.

Passos:

1. padronizar `error_code`, componente, impacto, fallback e evidência;
2. agrupar repetições sem esconder ocorrências individuais;
3. detectar inicialmente:
   - `UNVERIFIED_SUCCESS`;
   - `ENTITY_DOMAIN_MISMATCH`;
   - `SILENT_HANDLED_TURN`;
   - `CONTEXT_STALE`;
   - `FALLBACK_LOOP`;
   - `RECEIPT_MISSING`;
4. vincular cada falha ao trace original;
5. mostrar hipótese somente como hipótese, separada do que foi provado;
6. permitir abrir diretamente a primeira fronteira RED.

**Critério de aceite:** uma falha não é rotulada como causa sem cadeia causal; falso sucesso e ausência de receipt ficam visíveis.

### Etapa 5 — inspetor seguro de estado

Expandir inspeção sem criar uma segunda fonte de verdade.

Passos:

1. ler estado exclusivamente dos owners canônicos;
2. exibir origem, idade e confiabilidade de cada valor;
3. suportar contexto, pendências, ação, receipt, memória e evento por ID;
4. distinguir contexto temporário de memória durável;
5. mostrar TTL e ciclo de vida das pendências;
6. mascarar dados pessoais e segredos;
7. impedir qualquer edição nesse modo.

**Critério de aceite:** o inspetor explica quem publicou cada estado e quando, sem alterá-lo.

### Etapa 6 — desempenho e orçamento

**Estado em 2026-09-04: GREEN focado e de integração; sessão visual completa no
runtime real ainda pendente.** A consulta `perf` reutiliza a observabilidade
canônica: duração por fronteira, último valor, p50, p95 e máximo numa janela de
128 amostras. `perf llm`, `perf memory` e `perf actions` separam os respectivos
orçamentos sem reclassificar ações nem ler conteúdo de prompt/resposta. Quando
uma fronteira excede o limite, o console aponta o próprio componente e o trace
retido que contém a duração, evitando atribuir a lentidão aos módulos seguintes.

Os buffers continuam limitados e agora seus próprios owners contam pressão e
descartes: eventos DEV, eventos da ponte e entradas pendentes. A captura normal
faz somente trabalho local e não consulta estado nem diagnóstico da ponte; a
entrega continua na thread assíncrona do bridge. Num microbenchmark local desta
worktree, 10.000 registros levaram mediana de 174,08 ms (aproximadamente 17,4
µs por evento), com 10.000 itens retidos no limite configurado. NORMAL permanece
o nível visual inicial e TRACE só é exibido quando selecionado. O TRACE profundo
e o modo INSANE continuam deliberadamente adiados para a Etapa 11.

Passos:

1. registrar duração por fronteira do trace;
2. calcular último valor, p50, p95 e máximo em janela limitada;
3. integrar orçamento de LLM, memória e ações;
4. mostrar filas, eventos descartados e pressão do bridge;
5. detectar módulo lento sem culpar módulos posteriores;
6. provar que NORMAL possui baixo custo e TRACE/INSANE são ativados sob demanda.

**Critério de aceite:** `perf` identifica a fronteira que excedeu o orçamento e o próprio console não causa bloqueio perceptível.

### Etapa 7 — executor controlado de testes

Esta etapa inaugura o modo **CONTROL** e deve permanecer separada do monitor.

**Estado em 2026-09-04: GREEN focado, integração e executor real; sessão visual
manual completa ainda pendente.** O executor dedicado aceita somente
`tests list`, `tests status`, `tests run <suite_id>` e `tests cancel`. MONITOR
continua em `dev_query`; CONTROL atravessa a mensagem separada `dev_control`,
validada pela ponte autenticada. `run` e `cancel` exigem autorização explícita,
IDs fora da allowlist e qualquer composição de shell falham antes de `Popen`.

As suítes iniciais são `dev_console_focado`, `dev_console_regressao` e
`terminal`. Cada uma possui argv, cwd e timeout definidos em código; a execução
usa `shell=False`, stdin fechado e um ambiente mínimo sem credenciais herdadas.
Só uma execução fica ativa. `stdout` e `stderr` são drenados em paralelo para o
buffer DEV, detalhes ficam em TRACE e o receipt final aparece em NORMAL com
suite, comando efetivo sanitizado, duração e `returncode`. O status final deriva
do processo: saída parcial nunca transforma código diferente de zero, timeout
ou cancelamento em sucesso. O encerramento da Laylay cancela o subprocesso para
não deixá-lo órfão. Em build congelada, onde testes-fonte não acompanham o
aplicativo, o CONTROL permanece indisponível.

Prova no caminho real desta worktree: `dev_console_focado` foi iniciado pelo
novo runtime com o Python 3.14 do projeto e terminou em `passou`,
`returncode=0`, em 939,68 ms. A integração UI offscreen → protocolo CONTROL →
bridge local autenticado → executor e a sanitização do receipt também estão
cobertas por regressão.

Passos:

1. criar um executor dedicado, sem aceitar comando livre;
2. usar uma lista explícita de suítes e argumentos permitidos;
3. executar em subprocesso com `cwd`, ambiente, timeout e cancelamento definidos;
4. transmitir `stdout`, `stderr`, progresso e `returncode` para o console;
5. permitir inicialmente apenas:
   - teste focado selecionado;
   - regressivos do módulo;
   - suíte do Terminal;
6. exigir autorização explícita antes de iniciar;
7. impedir duas execuções concorrentes incompatíveis;
8. publicar receipt com comando efetivo, duração e código de saída;
9. nunca transformar saída parcial em sucesso.

Comandos previstos:

```text
tests list
tests run <suite_id>
tests status
tests cancel
```

**Critério de aceite:** somente suítes cadastradas executam; tentativa de shell arbitrário continua bloqueada; falha e cancelamento aparecem corretamente.

### Etapa 8 — integração controlada com caos

O caos será regressão ampla, não ferramenta inicial de diagnóstico.

Passos:

1. cadastrar roteiros de caos por ID, sem caminho arbitrário;
2. registrar baseline e configuração antes da execução;
3. exigir autorização explícita e avisar possíveis efeitos externos;
4. preferir modo sombra e fixtures isoladas;
5. transmitir progresso por turno;
6. agrupar falhas por família causal;
7. criar trace por turno falho;
8. salvar artefatos no diretório oficial de resultados;
9. oferecer cancelamento fail-closed;
10. nunca alterar snapshots ou baselines automaticamente.

Comandos previstos:

```text
chaos list
chaos run <roteiro_id>
chaos status
chaos cancel
```

**Critério de aceite:** cada RED do caos aponta para um trace e as falhas são agrupadas por raiz provável, preservando resultados brutos.

### Etapa 9 — exportação de diagnóstico

Passos:

1. exportar um trace em texto, Markdown e JSON;
2. exportar sessão com eventos, erros, métricas e metadados do baseline;
3. executar sanitização final antes de gravar;
4. usar nomes únicos e não sobrescrever arquivos;
5. gravar somente em diretório autorizado do projeto;
6. publicar receipt contendo caminho, tamanho, formato e hash;
7. testar que tokens, chaves e diretórios pessoais não aparecem no artefato.

Comandos previstos:

```text
export trace <id> markdown
export trace <id> json
export session diagnostic
```

**Critério de aceite:** o pacote pode ser compartilhado para análise sem vazar credenciais nem afirmar que dados ausentes foram coletados.

### Etapa 10 — persistência e retenção

Passos:

1. manter buffer recente em memória;
2. criar arquivos rotativos para eventos técnicos;
3. reter erros e traces explicitamente marcados por mais tempo;
4. definir tamanho, quantidade, idade e política de descarte;
5. recuperar uma sessão anterior sem bloquear a inicialização;
6. sinalizar corrupção ou perda parcial;
7. nunca misturar logs técnicos com memória pessoal da Laylay.

**Critério de aceite:** longas sessões não aumentam memória ou disco indefinidamente e a retenção é previsível.

### Etapa 11 — TRACE profundo e modo INSANE

Só implementar após o contrato estruturado estar estável.

Passos:

1. Event Bus Inspector;
2. filas, listeners e retries;
3. cache hits e misses;
4. snapshots técnicos seletivos;
5. profiler por módulo;
6. visualização de planos compostos e dependências;
7. ativação temporária com TTL;
8. limite de volume e alerta de custo.

**Critério de aceite:** o modo profundo pode ser ligado e desligado sem reiniciar e não fica ativo indefinidamente por acidente.

### Etapa 12 — cartões laterais e capacidades futuras

Os cartões da direita continuam em manutenção até que cada fonte exista no runtime real.

Ordem sugerida:

1. `Sensor Health`;
2. `Presence State`;
3. `Evento Aberto`;
4. `World Model`;
5. `Autonomy Decision`;
6. `Recent Trace`;
7. `Restore Manager`.

Para liberar um cartão:

- a capacidade precisa estar registrada no catálogo vivo;
- o estado deve vir do owner canônico;
- indisponibilidade precisa aparecer como indisponibilidade;
- ações exigem autoridade própria;
- receipt e limites precisam estar definidos;
- testes de composição e pergunta natural sobre a capacidade devem passar.

**Critério de aceite:** nenhum cartão simula uma habilidade que a Laylay não possui ou um sensor que não está conectado.

### Etapa 13 — prova no runtime real

Para cada marco importante:

1. GREEN unitário;
2. GREEN de integração com componentes reais;
3. GREEN do caminho de composição de `laylay.py`;
4. GREEN da suíte relevante;
5. sessão controlada no runtime real;
6. comparação entre terminal externo e DEV Console;
7. teste de rajada, pausa, reconexão e encerramento;
8. registro das limitações que ainda permanecerem.

**Critério de aceite final:** durante uma sessão real, o terminal externo pode ser fechado sem perder informações necessárias para diagnosticar um turno, uma falha de executor ou uma suíte de teste.

## 5. Ordem prática das próximas entregas

Prioridade imediata:

1. evento estruturado canônico;
2. `trace_id` de ponta a ponta;
3. Explorer de eventos e busca;
4. falhas semânticas e falso sucesso;
5. exportação segura de trace;
6. executor controlado de testes;
7. integração com caos;
8. persistência rotativa;
9. TRACE profundo e INSANE;
10. cartões laterais, um por vez.

O executor de testes só deve ser iniciado depois que trace, receipt e exportação estiverem confiáveis. Assim, quando uma execução falhar, o console já terá como explicar e preservar a evidência.

## 6. Testes obrigatórios por etapa

Cada nova capacidade deve incluir, conforme aplicável:

- teste unitário do contrato;
- regressão com a formulação original do problema e variantes naturais próximas;
- teste do bridge com socket real;
- teste da página PySide6;
- teste do caminho real de composição;
- teste negativo de autorização;
- teste de sanitização de segredos;
- teste de falha, timeout e cancelamento;
- teste de rajada e limite de buffer;
- teste de receipt e proibição de falso sucesso;
- teste cooperativo quando mais de uma habilidade participar.

Mocks não podem substituir o componente compartilhado cuja integração está sendo provada.

## 7. Fora de escopo desta sequência

Não fazem parte da conclusão inicial do DEV Console:

- shell geral embutido;
- execução irrestrita de Python ou PowerShell;
- edição direta de memória ou contexto;
- correção automática de código;
- autorreparo sem playbook e sem autorização;
- acesso direto da LLM a credenciais;
- ativação antecipada das habilidades mostradas nos cartões laterais.

Essas possibilidades exigem projeto próprio de autoridade, sandbox, receipts, rollback e verificação posterior.

## 8. Definição de pronto

O DEV Console estará concluído como substituto do terminal Python quando:

- todos os logs necessários chegam à aba sem duplicação ou vazamento;
- todo turno relevante possui trace rastreável;
- a primeira fronteira RED pode ser localizada por evidência;
- execução e confirmação aparecem como estados diferentes;
- contexto, pendência, ação e receipt podem ser inspecionados pela fonte canônica;
- desempenho e falhas podem ser investigados sem bloquear a Laylay;
- testes e caos usam executores controlados, autorização e receipts;
- traces e sessões podem ser exportados de forma sanitizada;
- retenção de logs é limitada e previsível;
- a composição real e as regressões permanecem verdes;
- uma sessão real comprova que o terminal externo não é mais necessário para diagnóstico comum.

## 9. Princípio arquitetural geral descoberto

O DEV Console não deve ser apenas uma tela que copia `print`.

Ele deve consolidar um contrato reutilizável por todas as habilidades:

```text
decisão observável
→ execução identificada
→ receipt verificável
→ estado resultante
→ conclusão honesta
```

Esse contrato beneficia música, arquivos, navegador, IoT, memória, voz, automação e qualquer habilidade futura sem obrigar a interface a conhecer regras privadas de cada domínio.


A aba DEV pode realmente substituir o terminal Python, mas ainda falta uma peça essencial: hoje ela recebe somente eventos da interface. Ela precisa também receber os logs do núcleo, `stdout`, `stderr`, traces e receipts.

Estudando o projeto, encontrei duas bases boas que já existem:

- O terminal atual possui muitos `print()` categorizados e um filtro central em [laylay.py](<C:/Users/47796476817/Downloads/pasta organizada/projeto lay/projeto-laylay/projeto-laylay/laylay.py:665>).
- A observabilidade já registra traces, falhas, decisões, latência, p50, p95 e limites em [observabilidade.py](<C:/Users/47796476817/Downloads/pasta organizada/projeto lay/projeto-laylay/projeto-laylay/mente_laylay/memoria_mental/observabilidade.py:217>).

Minha sugestão seria implementar estas sete ferramentas:

| Prioridade | Ferramenta | Utilidade prática |
|---|---|---|
| 1 | Trace completo por turno | Mostra entrada → contexto → intenção → política → executor → receipt → resposta. Destaca automaticamente a primeira etapa RED. |
| 2 | Captura do terminal Python — **GREEN focado** | Tudo que hoje aparece em `print`, `stdout` e `stderr` também aparece na aba, sem deixar o terminal externo necessário. |
| 3 | Central de erros — **GREEN no núcleo; parcial semântico** | Agrupa erros repetidos, mostra primeira ocorrência, última ocorrência, impacto, fallback, stack trace e último momento em que funcionou. |
| 4 | Inspetor de estado — **GREEN focado e integração; runtime real pendente** | Permite consultar contexto, pendências, autoridade, última ação, último efeito confirmado e memória usada no turno. |
| 5 | Painel de desempenho — **GREEN focado e integração; runtime visual pendente** | Latência por componente, último/p50/p95/máximo, fronteira lenta e trace responsável, orçamento LLM/memória/ações e pressão/descarte dos buffers. |
| 6 | Runner de testes — **GREEN até executor real; caos pendente da Etapa 8** | Executa apenas suítes autorizadas por ID, transmite stdout/stderr, impede concorrência, permite cancelamento e publica receipt com duração e código de saída. |
| 7 | Exportação de diagnóstico | Gera um pacote Markdown/JSON com trace, erro, estado sanitizado, versões e métricas para análise posterior. |

### 1. Trace Explorer — a ferramenta mais importante

Cada interação deveria receber um `trace_id`:

```text
14:32:10.481 [TRACE turno-000151] [INPUT]    "apaga troca ideia.txt"
14:32:10.486 [TRACE turno-000151] [ENTITY]   FILE = troca ideia.txt
14:32:10.490 [TRACE turno-000151] [ROUTER]   notes.delete ← selecionado
14:32:10.491 [TRACE turno-000151] [WARNING]  domínio incompatível com FILE
14:32:10.506 [TRACE turno-000151] [RESULT]   FAILED
```

Ao executar:

```text
laylay.dev > trace last
```

a aba mostraria a cadeia vertical e marcaria:

```text
INPUT       GREEN
CONTEXT     GREEN
ENTITY      GREEN
ROUTER      RED    ← PRIMEIRA DIVERGÊNCIA
EXECUTOR    RED    consequência
RESPONSE    RED    consequência
```

Isso reduz muito o tempo perdido olhando apenas o erro final.

### 2. Captura real de `stdout` e `stderr`

**Estado em 2026-09-04: GREEN focado e regressivo relevante.** O runtime instala
espelhos no caminho real de `sys.stdout` e `sys.stderr`, preserva a saída
original quando ela existe, continua capturando quando o processo não possui
console externo e mantém o canal correto inclusive para mensagens ocultadas
pelo filtro global de `print`. A entrega ao Terminal ocorre de forma assíncrona
pelo desktop bridge e a aba conserva o histórico durante pausa visual.

Evidência deste marco:

- RED reproduzido para `stderr` oculto incorretamente rotulado como `stdout`;
- RED reproduzido para processo sem stream externa disponível;
- 45 testes focados de runtime, bridge, filtro de terminal e página PySide6;
- 367 testes da regressão ampla relevante de Terminal/bridge/DEV.

O escopo deste contrato é a saída Python (`print`, `sys.stdout` e
`sys.stderr`). Escritas nativas diretamente nos descritores do sistema
operacional não são reinterpretadas como eventos Python.

O formato atual do terminal Python é bom para leitura humana, mas possui informações espalhadas e não correlacionadas. Eu manteria a compatibilidade:

```text
14:32:10.481 INFO    [MÚSICA] Player conectado
14:32:11.105 WARNING [MEMÓRIA] Consulta demorou 420 ms
14:32:12.230 ERROR   [ARQUIVOS] PermissionError
```

Cada linha deveria carregar campos ocultos e expansíveis:

```text
trace_id
turno_id
categoria
componente
arquivo
linha
thread
duração
nível
dados sanitizados
```

Clicar na linha abriria os detalhes e, quando disponível, o arquivo e a linha do código.

### 3. Central de erros inteligente

**Estado em 2026-09-04: GREEN no núcleo e parcial no diagnóstico semântico.**
A Central agora usa `error_code` canônico, soma inclusive ocorrências suprimidas
do terminal, conserva primeiro e último instante, mostra tipo, classe, origem da
classificação, impacto, fallback, trace mais recente e primeira fronteira RED.
Ela preserva também o instante do último sucesso observado para o componente e
sempre separa essa evidência de causalidade com `causa=NAO_PROVADA`.

O comando fechado `errors <componente>:<error_code>` abre as ocorrências
recentes retidas e informa explicitamente quantas não foram preservadas pelo
limite. O desktop bridge aceita apenas esse formato allowlist; operadores de
shell, Python e comandos anexados continuam bloqueados.

Detecção semântica disponível com dados canônicos atuais:

- `UNVERIFIED_SUCCESS`: execução marcada como sucesso com confirmação
  explicitamente falsa;
- `RECEIPT_MISSING`: execução marcada como sucesso sem confirmação nem
  evidência de receipt.

Ainda dependem de novos campos estruturados nos respectivos owners:

- `ENTITY_DOMAIN_MISMATCH` — entidade esperada e domínio escolhido;
- `SILENT_HANDLED_TURN` — consumo, resposta e efeito observável do turno;
- `CONTEXT_STALE` — origem, timestamp e TTL do valor contextual;
- `FALLBACK_LOOP` — identidade e encadeamento causal dos fallbacks.

Também permanece pendente um stack trace sanitizado/referenciado; a
observabilidade atual não publica esse dado, portanto a Central não o preenche
artificialmente.

Esses quatro casos não são inferidos de texto para evitar falsos diagnósticos.

Evidência deste marco:

- 70 testes focados de observabilidade, contrato de resultado, DEV, bridge e UI;
- 472 testes da regressão ampla relevante de diagnóstico/Terminal/bridge/DEV.

Em vez de mostrar o mesmo erro 300 vezes:

```text
TimeoutError · llm_http
Ocorrências: 37
Primeira: 14:20:02
Última: 14:31:48
Impacto: turno
Fallback: resposta local
Último sucesso: 14:19:58
Trace mais recente: turno-000151
```

Também separaria:

- falha esperada;
- degradação temporária;
- defeito;
- erro primário;
- erro em cascata;
- operação bloqueada corretamente.

### 4. Inspetor de estado e autoridade

**Estado em 2026-09-04: GREEN focado e de integração; sessão completa no runtime
real ainda pendente.** O console recebe o snapshot completo do
`EstadoCompartilhadoRuntime` e mantém compatibilidade com getters mentais
anteriores. A projeção é somente leitura e explicita o owner canônico, idade e
confiabilidade observável. Pendências conversacionais e operacionais aparecem
separadas com TTL e ciclo de vida, sem consumir nem expirar estado durante a
consulta.

`inspect context` separa intenção reconhecida, autorização explicitamente
publicada e alvo resolvido; ausência de autoridade não é inferida como
permissão. `inspect action last` informa se o executor foi chamado, enquanto
`inspect receipt last` separa receipt recebido, efeito confirmado e permissão
para resposta de sucesso. `inspect memory used` distingue histórico temporário
de memória durável, omite o conteúdo e marca uso durável como `NAO_PROVADO`
quando o runtime não publicou evidência específica. `inspect event <id>` lê
somente eventos retidos no buffer DEV. A ponte aceita esses comandos por
allowlist estrita e rejeita sufixos ou comandos de shell.

Evidência atual: RED canônico reproduzido para owner/idade/TTL; 19 testes do
runtime DEV verdes; integração com o `EstadoCompartilhadoRuntime` real e aresta
de composição protegidas; conjunto relevante com 478 testes verdes. E-mails,
credenciais, tokens e caminho do perfil do usuário são mascarados. Nenhum
commit foi criado.

Comandos úteis:

```text
inspect context
inspect pending
inspect action last
inspect receipt last
inspect memory used
inspect event dev-00000001
```

A visualização deve separar claramente:

```text
Intenção reconhecida: DELETE_FILE
Autorização: confirmada
Alvo resolvido: troca ideia.txt
Executor chamado: sim
Receipt recebido: não
Efeito confirmado: não
Resposta de sucesso permitida: não
```

Isso ajuda diretamente em bugs de pendência, memória, continuidade e confirmações falsas.

### 5. Desempenho com orçamento

**Estado em 2026-09-04: GREEN focado e de integração; sessão visual completa no
runtime real ainda pendente.** `perf` mostra último, p50, p95, máximo, limite,
amostras e excessos. As consultas especializadas preservam os owners canônicos:
`perf llm` acrescenta uso do orçamento, bloqueios e circuito; `perf memory`
seleciona preparação de prompt; `perf actions` seleciona decisão e execução sem
confundir `ação` com `preparação`. Violações apontam `FRONTEIRA_LENTA` e usam o
trace da própria etapa quando ele ainda está retido. A visão geral inclui
ocupação, limites e descartes dos buffers DEV e desktop bridge.

A Laylay já coleta boa parte disso. A aba poderia mostrar:

```text
COMPONENTE            ÚLTIMO    P50     P95     LIMITE
interpretação           41 ms    35 ms    74 ms     80 ms
dispatcher              67 ms    51 ms   118 ms    120 ms
execução               312 ms   220 ms  1804 ms   1500 ms ⚠
llm_http              3240 ms  2800 ms  6300 ms  20000 ms
```

Ao clicar em uma métrica lenta, apareceria a lista dos traces responsáveis.

### 6. Integração com pytest e caos

**Estado em 2026-09-04: pytest CONTROL GREEN até o executor real; integração de
caos ainda não iniciada.** O runner não aceita linha de comando livre, caminho
ou argumentos vindos da interface. Listagem, execução, status e cancelamento
passam por uma allowlist imutável e por um canal diferente das consultas
somente leitura. Falha, timeout e cancelamento permanecem resultados terminais
distintos. A Etapa 8 adicionará IDs de caos, baseline, seed e replay sem ampliar
o executor atual para shell genérico.

Eu começaria com comandos controlados, não um terminal shell completamente livre:

```text
test last
test file tests/test_playlist.py
test failed
chaos last
chaos replay seed-18442
```

Resultado:

```text
RED: test_confirmacao_de_playlist_inexistente_deve_criar_antes_de_adicionar

Pendência criada       PASS
Confirmação reconhecida PASS
CREATE executado       PASS
CREATE confirmado      FAIL  ← primeira fronteira RED
ADD executado          SKIPPED
```

### 7. Pacote de diagnóstico

Um botão “Exportar diagnóstico” deveria produzir:

```text
diagnostico-turno-000151/
├── resumo.md
├── trace.json
├── erros.json
├── metricas.json
├── estado_sanitizado.json
└── ambiente.txt
```

Sem tokens, senhas, conteúdo privado ou caminhos sensíveis.

Minha ordem de implementação seria:

1. Barramento normalizado de eventos DEV.
2. Espelho de `stdout`/`stderr`.
3. Trace Explorer e primeira fronteira RED.
4. Central de erros.
5. Inspetor de estado e receipts.
6. Desempenho.
7. Testes, caos e exportação.

Com isso, a aba deixaria de ser apenas um layout bonito e passaria a ser uma ferramenta real para descobrir a causa dos problemas da Laylay.

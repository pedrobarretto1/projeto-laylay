# HANDOFF INTERNO — PROJETO LAYLAY
Data: 2026-08-16
Atualizado em: 2026-08-16 19:00 (America/Sao_Paulo)
Objetivo: continuidade segura em novos chats.

## ESTADO ATUAL — LEIA PRIMEIRO

HEAD atual confirmado no GitHub:
`a619a71ff5d1976fb8a25561ab2512ec291e31e8`
mensagem:
`teste 3.1`

Baseline imediatamente anterior:
`ebcaaa27b4e759757f8416bbc27133a6d85a1519`
mensagem:
`teste 3.0`

Estado das raízes históricas:
- Bug B antigo — observabilidade/identidade de execuções: FECHADO.
- Patch A antigo — autorização por ato de fala: FECHADO.
- B1.1/B1.2.1/B1.3 — revisão intra-turno: FECHADAS no escopo atual.
- Não reabrir identidade do plano nem revisão intra-turno sem nova evidência concreta.

Trilha pós-caos 3.0 / 3.1:
- Fase A — capability truth read-only × barreira P0: FECHADA no `teste 3.1`.
- Fase B — linguagem/contexto de arquivos: ESTUDO CONCLUÍDO; ainda SEM patch de produção.
- Fase B foi dividida em:
  - B1 — gramática contextual de arquivos usando referência tipada viva.
  - B2 — repetição segura de `FILE_READ`, incluindo `Leia de novo`.
- Fase C — arbitragem caixa de entrada × filesystem (`troca ideia.txt`, `nota.txt` etc.): causa raiz já provada, mas continua SEPARADA; não misturar em B.

Teste de caos 3.1:
- diretório: `resultados_testes/roteiro_teste_laylay_caos-20260816-184041-656979/`;
- 267/267 turnos respondidos;
- transporte concluído;
- 54 avaliados semanticamente;
- 30 passaram;
- 22 falharam;
- 2 alertas;
- taxa semântica: 55,56%;
- 115 comandos observados;
- 10 confirmações indeterminadas;
- p50: 2,169 s;
- p95: 8,785 s;
- máximo: 19,617 s;
- média: 2,996 s.

Conclusão operacional imediata:
- Fase A está fechada por prova red→green + regressão + caos real.
- Próximo patch NÃO deve ser um mega-patch B.
- Primeiro materializar/validar B1 isoladamente; depois B2 isoladamente.
- Não tocar em `modalidade_turno.py` para resolver B1/B2 sem nova evidência.
- Não misturar Fase C no patch de arquivos/contexto.

---

## 1. COMO TRABALHAR COM A LAYLAY

O usuário, Pedro, prefere um fluxo de engenharia cuidadoso e incremental.

REGRA PRINCIPAL:
NUNCA gerar e entregar um patch imediatamente após encontrar uma hipótese de correção.

Fluxo obrigatório para QUALQUER patch:

1. Estudar o bug antes de mexer.
2. Confirmar a causa raiz no código ATUAL, testando hipóteses e eliminando falsos suspeitos.
3. Confirmar HEAD/branch/blobs atuais do repositório.
4. Localizar arquivo, função, contrato e ponto exato de inserção.
5. Inspecionar consumidores downstream e efeitos colaterais.
6. Projetar testes de regressão VERMELHOS que expressem o contrato desejado, sem hardcode de frase única.
7. Rodar esses testes contra o HEAD atual:
   - guardrails existentes devem continuar verdes;
   - reds esperados devem falhar pelo motivo previsto;
   - se um red inesperadamente ficar verde, INVESTIGAR a rota real; nunca alterar o teste só para forçar vermelho.
8. Só depois da fotografia vermelha comprovada, desenhar a MENOR mudança de produção possível.
9. Rodar regressões reais/focadas e confirmar red→green sem relaxar proteções globais.
10. Gerar patcher seguro com:
    - trava de HEAD/baseline;
    - trava de blob/âncoras quando útil;
    - recusa de arquivos-alvo sujos;
    - backup;
    - manifest;
    - diff;
    - AST/py_compile;
    - git diff --check;
    - pytest focado;
    - rollback automático;
    - SEM commit/push automático.
11. DEPOIS DE GERAR O PATCH, REANALISAR O PATCH INTEIRO antes de entregar, inclusive os testes.
12. Na reanálise final, confirmar:
    - se mexe realmente no lugar certo;
    - se não toca módulos desnecessários;
    - se preserva contratos existentes;
    - se o teste representa o comportamento real e não só uma frase;
    - se o baseline ainda é o atual;
    - se as âncoras correspondem ao código real;
    - se o patch resolve a causa raiz e não apenas o sintoma;
    - se não reintroduz bugs já fechados;
    - se não cria replay/execução em domínio errado.
13. Só então entregar o patch ao usuário.
14. Depois que o usuário rodar, analisar saída, manifest e diff REAL antes de considerar o patch fechado.
15. Após patch aplicado, rodar teste de caos/regressão antes de encerrar a raiz.
16. Se o patcher fizer rollback, estudar o motivo primeiro; não fazer uma segunda tentativa por chute.
17. Antes de commit, conferir `git status --short` e evitar incluir backups/patchers temporários sem intenção explícita.

Evitar:
- patches amplos;
- mudanças por tentativa;
- “consertar” teste em vez de comportamento;
- relaxar proteções globais para fazer um caso passar;
- misturar raízes diferentes no mesmo patch;
- assumir que HEAD ou arquivo continuam iguais entre testes;
- confiar em memória de código sem reler o estado atual.

Preferência técnica do usuário:
- contratos estáveis;
- módulos independentes;
- causa raiz comprovada;
- mudanças mínimas;
- segurança/rollback;
- comandos PowerShell prontos;
- estudo primeiro, patch depois.

---

# 2. ARQUITETURA/INVARIANTES IMPORTANTES DA LAYLAY

Pipeline desejado:

ENTRADA
→ ATO DE FALA
→ ESTRUTURA
→ AÇÃO CANDIDATA
→ AUTORIZAÇÃO
→ ALVO
→ PRÉ-ESTADO
→ EXECUTOR
→ PÓS-ESTADO
→ RESULTADO CAUSAL

Para revisão intra-turno:

FALA ORIGINAL
→ REVISÃO INTRA-TURNO
→ TEXTO OPERACIONAL EFETIVO
→ PATCH A / AUTORIZAÇÃO
→ RETRATO
→ ESPECIALISTAS
→ PLANO
→ ROTEAMENTO
→ EXECUÇÃO

Separar sempre:

TEXTO ORIGINAL
- identidade do turno;
- histórico;
- memória;
- auditoria;
- correlação com runner/testes.

TEXTO OPERACIONAL EFETIVO
- cognição operacional;
- autorização;
- planejamento semântico;
- detectores;
- roteamento;
- executor.

Nunca usar o texto operacional revisado como “RG” do turno.

---

# 3. PATCHES/RAÍZES JÁ TRABALHADOS

## Bug B — observabilidade/identidade de execuções
Problema:
- ações de mesma intent eram colapsadas;
- publicações genéricas duplicavam resultados detalhados.

Correções anteriores:
- identidade por id_solicitacao/request_id;
- mesmo ID = merge;
- ID diferente = nova ocorrência;
- publicação detalhada oficial suprime fallback genérico.

Bug B foi considerado fechado após teste 2.5.

Não reverter esse comportamento.

---

## Patch A — autorização por ato de fala
Problema:
frases como:
- “Eu poderia abrir o Opera agora?”
- “Se eu quisesse fechar o Opera, como faria?”
- “Só me explica como pesquisar, não pesquise nada.”
eram tratadas como autorização operacional.

Correção:
presença de verbo+alvo é apenas evidência de ação candidata.
Ato de fala vem antes da autorização.

Patch A foi aprovado/fechado.

Não relaxar o porteiro global para resolver casos locais.

---

# 4. REVISÃO INTRA-TURNO — PATCH B1

Objetivo:
resolver correções dentro da mesma fala antes de executar qualquer proposta descartada.

Taxonomia:

1. CANCELAMENTO
“Apaga X... não apaga.”
→ NOOP.

2. SUBSTITUIÇÃO DE AÇÃO
“Pausa a música... esquece, continua tocando.”
→ somente PLAY/continuação.

3. SUBSTITUIÇÃO DE ALVO/PARÂMETRO
“Abre Wikipédia... não, melhor Prime Video.”
→ somente Prime Video.

4. PRONOME COM ALVO HERDADO
“Fecha a Calculadora... quer dizer, maximiza ela.”
→ MAXIMIZE Calculadora.

Não transformar qualquer “não”, “melhor” etc. em revisão:
- `não.txt` deve sobreviver;
- `"não apaga"` em citação deve sobreviver;
- “melhor resultado” deve sobreviver.

---

# 5. B1.1 — ESTADO

B1.1 introduziu:
- `mente_laylay/cognicao/revisao_turno.py`
- integração no orquestrador;
- integração em comandos prioritários;
- integração no coordenador de intenção;
- testes de revisão.

Caso musical:
“Pausa a música... esquece, continua tocando.”
inicialmente virava:
`continua tocando`
e não era autorizado porque faltava alvo explícito.

Correção:
herdar o alvo:
`continua música`

Regra:
resolver elipse local herdando alvo da proposta descartada.
NÃO afrouxar Patch A.

---

# 6. TESTE 2.7 E BUG DE IDENTIDADE DO PLANO — HISTÓRICO, RESOLVIDO NA B1.2.1

HEAD observado após teste 2.7:
`31b6b20f01df70707d3e50944a74532cfe696e15`
mensagem:
`teste 2.7`

O teste de caos parou no turno da frase:
“Abre o Opera... não, abre a Calculadora.”

Motivo:
`plano_de_outro_turno`

Diagnóstico:
a revisão funcionou e produziu:
`abre a Calculadora`

Mas `_planejar_turno_mente(texto_cognitivo, ...)`
usou o texto revisado para preencher:
`plano["texto_usuario"]`

Então:
runner enviou fala original,
mas o plano se identificou como “Abre a Calculadora”.

Isso viola o contrato de identidade.

IMPORTANTE:
não trocar o planejador de volta para texto bruto.
O planejador deve continuar recebendo `texto_cognitivo`,
senão pode reintroduzir Opera/alvo descartado.

Solução correta:
planejar semanticamente com texto efetivo,
depois restaurar explicitamente a identidade pública:

`plano["texto_usuario"] = texto_original`

e manter separado:

`plano["texto_operacional_efetivo"] = texto_efetivo`

---

# 7. B1.2 — ESTUDO CONFIRMADO — BASE DA B1.2.1

Arquivo estudado:
`mente_laylay/cognicao/orquestrador_turno_runtime.py`

No estado do HEAD 31b6b20f:
o fluxo contém:

`plano = ns['_planejar_turno_mente'](texto_cognitivo, ...)`

Depois:
evidência de habilidades também usa `texto_cognitivo`.

Arquivo:
`mente_laylay/cognicao/plano_turno.py`

`planejar_turno(texto, ...)` usa o argumento `texto`
para:
- atos;
- contexto;
- domínio;
- `plano["texto_usuario"]`.

Logo:
não mudar o argumento do planejador.
Separar identidade depois que ele retornar.

Contratos:
`PlanoTurnoDict` é `TypedDict(total=False)`.
Campos extras são compatíveis com a estratégia de migração atual.

---

# 8. B1.2 — PRIMEIRA TENTATIVA E ERRO DO TESTE

Patcher:
`patch_revisao_intra_turno_b1_2.py`

A lógica proposta:
helper `alinhar_identidade_plano_revisao(...)`

Após planejamento:
- restaura `texto_usuario` original;
- guarda `texto_operacional_efetivo`;
- guarda metadados `revisao_intra_turno`.

O patcher rodou os testes,
mas um teste falhou:

esperava:
`"Calculadora" in atos`

real:
`"abre a calculadora"`

Era apenas comparação case-sensitive do TESTE,
não falha da lógica de produção.

Rollback automático funcionou.

Esse episódio gerou uma nova regra explícita do usuário:
SEMPRE REANALISAR O PATCH PRONTO ANTES DE ENTREGAR,
inclusive os testes.

---

# 9. B1.2.1 — APLICADA E VALIDADA

Patch ID:
`P0_REVISAO_INTRA_TURNO_B1_2_1_20260816`

Baseline usado pelo patch:
`31b6b20f01df70707d3e50944a74532cfe696e15`

O patch modificou:
- `mente_laylay/cognicao/orquestrador_turno_runtime.py`
- `tests/test_identidade_plano_revisao_b1_2.py`

Manifest registrado no commit 2.8:
- `py_compile_returncode = 0`
- `git_diff_check_returncode = 0`
- `pytest_returncode = 0`
- `43 passed in 0.63s`

Mudança de contrato:
- o planejador continua recebendo `texto_cognitivo`;
- portanto atos/domínio/cognição continuam vendo apenas a proposta operacional final;
- depois do planejamento, `alinhar_identidade_plano_revisao(...)` restaura:
  - `plano["texto_usuario"] = texto_original`
  - `plano["texto_operacional_efetivo"] = texto_efetivo`
  - metadados de `revisao_intra_turno`.

Invariante confirmado:

`IDENTIDADE DO TURNO != REPRESENTAÇÃO OPERACIONAL`

A fala original é o RG/auditoria/correlação.
A fala revisada é a visão usada para pensar e executar.

Teste de caos 2.8:
- completou 267/267;
- não repetiu a parada `plano_de_outro_turno`;
- turno 95:
  `Abre o Opera... não, abre a Calculadora.`
  → uma única `APP_OPEN` para Calculadora;
- turno 96:
  `Fecha a Calculadora... quer dizer, maximiza ela.`
  → uma única `MAXIMIZE_WINDOW`;
- turno 97:
  `Abre a Wikipédia, não, melhor o Prime Video.`
  → uma única abertura final do Prime Video;
- turno 101:
  criação `erro.txt → correcao.txt`
  → uma única criação de `correcao.txt`;
- turno 103:
  `Apaga o correcao.txt... não apaga.`
  → sem exclusão operacional.

A B1.2.1 deve ser considerada FECHADA.
Não alterar novamente o argumento do planejador nem reabrir esse contrato sem nova evidência concreta.

---

# 9A. TESTE 2.8 — RESULTADOS DA MATRIZ DE REVISÃO

HEAD:
`3c89d27ce4712827e359ec7d1a1da888398e2203`
mensagem:
`teste 2.8`

Resumo:
- total: 267
- respondidos: 267
- transporte: concluído
- semanticamente avaliados: 54
- passaram: 29
- falharam: 23
- alertas: 2
- não avaliados: 213
- taxa semântica: 53,7%
- comandos observados: 114
- confirmações indeterminadas: 9
- p50: 2,087 s
- p95: 8,262 s
- max: 19,137 s
- média: 2,954 s

Casos B1 que PASSARAM estruturalmente:
- t95 `Abre o Opera... não, abre a Calculadora.`
  → somente Calculadora.
- t96 `Fecha a Calculadora... quer dizer, maximiza ela.`
  → somente maximização da Calculadora.
- t97 `Abre a Wikipédia, não, melhor o Prime Video.`
  → somente Prime Video.
- t101 `Cria ... erro.txt... não, chama correcao.txt.`
  → somente `correcao.txt`.
- t103 `Apaga o correcao.txt... não apaga.`
  → sem DELETE_ITEM.

Casos B1 que AINDA FALHAM:
- t98 `Pesquisa Python... pera, não pesquisa nada.`
  resultado atual:
  `SEARCH` em `nada`, confirmado como busca aberta.
  Isso é incorreto: a segunda proposta revoga a busca inteira.
- t99 `Liga a lâmpada... não, deixa desligada.`
  resultado atual:
  `IOT_CONTROL` com alvo contaminado equivalente a `o deixa desligada`,
  terminando em `nao_encontrado`.
  Isso é incorreto: `deixa desligada` expressa o estado final e deve herdar `lâmpada`.
- t100 `Pausa a música... esquece, continua tocando.`
  resultado atual:
  sem comando operacional.
  O revisor produz uma forma intermediária que satisfaz parte do contrato,
  mas não atravessa autorização/roteamento de mídia de ponta a ponta.

Caso FORA do escopo atual:
- t102 `Escreve banana... quer dizer, escreve maçã.`
  continua sem ação operacional.
  Os verbos de escrita não pertencem à gramática B1 atual.
  Não ampliar B1 para escrita sem estudo separado.

Conclusão:
B1.2.1 resolveu identidade.
Os erros restantes são de NORMALIZAÇÃO/CANONICALIZAÇÃO DA PROPOSTA FINAL,
não de identidade do turno.

---

# 9B. PRÓXIMA SUB-RAIZ B1 — ESTUDO ATUAL ANTES DO PATCH

HEAD que deve ser usado como baseline se continuar igual:
`3c89d27ce4712827e359ec7d1a1da888398e2203`

Arquivo de produção central:
`mente_laylay/cognicao/revisao_turno.py`

Estado confirmado do arquivo:
- continua com a gramática introduzida na B1.1;
- a continuação musical elíptica hoje é transformada em `continua música`;
- a revogação só reconhece `não + mesma operação` quando o novo comando fica sem `resto`;
- por isso `não pesquisa nada` escapa como nova pesquisa cujo alvo vira `nada`;
- `deixa desligada` não é reconhecido como nova operação explícita;
- cai no caminho genérico de substituição de alvo e contamina a ação anterior.

Direção de correção estudada:

1. CANCELAMENTO SEMÂNTICO DA MESMA OPERAÇÃO
   Para construção equivalente a:
   `não + mesma operação + nada`
   a palavra `nada` deve ser tratada como revogação do pedido, não como alvo.
   Exemplo:
   `Pesquisa Python... pera, não pesquisa nada.`
   → revisão resolvida + cancelada + texto operacional vazio.

2. ESTADO FINAL COM ALVO HERDADO
   Construções como:
   `Liga a lâmpada... não, deixa desligada.`
   não são simples troca de alvo.
   A revisão deve interpretar o estado final `desligada`,
   herdar `lâmpada` da proposta descartada e produzir uma forma operacional
   autossuficiente de DESLIGAR.

3. CANONICALIZAÇÃO DE CONTINUAÇÃO MUSICAL
   Não relaxar Patch A.
   Não ensinar cada roteador a entender uma forma quebrada.
   O revisor deve produzir uma forma interna canônica que:
   - mantenha o alvo explícito;
   - seja autorizável pelo Patch A;
   - já seja aceita pela gramática de mídia existente.
   A forma `continua música` mostrou que autorização e roteamento ainda não
   compartilham o mesmo contrato textual de ponta a ponta.
   Preferir canonicalização no revisor.

Escopo recomendado do próximo patch:
- produção: SOMENTE `mente_laylay/cognicao/revisao_turno.py`, se os anchors atuais permanecerem iguais;
- testes:
  - `tests/test_revisao_intra_turno_v1.py`
  - `tests/test_identidade_plano_revisao_b1_2.py` apenas para atualizar expectativa textual se a forma canônica musical mudar;
- não tocar:
  - `modalidade_turno.py` / Patch A;
  - `orquestrador_turno_runtime.py` / B1.2.1;
  - executores de mídia/IoT/browser;
  - Bug B;
  - Root C;
  - capability truth.

Regressões obrigatórias do próximo patch:
- `Pesquisa Python... pera, não pesquisa nada.` → NOOP.
- `Liga a lâmpada... não, deixa desligada.` → uma única ação final de desligar a lâmpada.
- `Pausa a música... esquece, continua tocando.` → uma única ação final de play/continue.
- preservar:
  - `Abre Opera e depois abre Calculadora.`
  - `Pausa música e depois continua.`
  - `não.txt`
  - `"não apaga"`
  - `melhor resultado`
  - os casos já aprovados t95/t96/t97/t101/t103.

Antes de gerar o patch:
1. confirmar HEAD novamente;
2. reler os blobs dos três arquivos alvo/teste;
3. confirmar as gramáticas reais dos consumidores downstream;
4. fazer patch mínimo;
5. rodar testes focados;
6. reanalisar o patch inteiro;
7. só então entregar;
8. depois rodar novamente o caos completo.

---

# 10. MATRIZ ESPERADA PARA REVISÃO INTRA-TURNO

NOOP:
- “Pesquisa Python... pera, não pesquisa nada.”
  → 0 SEARCH.
  STATUS 2.8: FALHA; executou SEARCH em `nada`.
- “Apaga o correcao.txt... não apaga.”
  → 0 DELETE_ITEM.
  STATUS 2.8: OK; sem DELETE_ITEM.

AÇÃO FINAL ÚNICA:
- “Abre o Opera... não, abre a Calculadora.”
  → exatamente 1 APP_OPEN Calculadora.
  STATUS 2.8: OK.
- “Pausa a música... esquece, continua tocando.”
  → exatamente 1 MEDIA_CONTROL play/continue.
  STATUS 2.8: FALHA; terminou sem comando operacional.
- “Cria erro.txt... não, chama correcao.txt.”
  → exatamente 1 CREATE_FILE correcao.txt.
  STATUS 2.8: OK.
- “Fecha a Calculadora... quer dizer, maximiza ela.”
  → exatamente 1 MAXIMIZE Calculadora.
  STATUS 2.8: OK.
- “Abre Wikipédia... não, melhor Prime Video.”
  → exatamente uma ação final para Prime Video.
  STATUS 2.8: OK.
- “Liga a lâmpada... não, deixa desligada.”
  → exatamente uma ação final para DESLIGAR a lâmpada.
  STATUS 2.8: FALHA; alvo foi contaminado por `deixa desligada`.

PRESERVAR CADEIAS REAIS:
- “Abre Opera e depois abre Calculadora.”
  → 2 ações.
- “Pausa música e depois continua.”
  → 2 ações.

PRESERVAR LITERAIS:
- `não.txt`
- `"não apaga"`
- `melhor resultado`

---

# 11. RAÍZES AINDA SEPARADAS — NÃO MISTURAR NO B1

## Root C — confirmação causal de CLOSE_APP

Problema:
executor pode inferir “fechado com sucesso” só porque app está ausente depois,
mesmo se o fechamento real falhou.

Contrato desejado:

pre_open + closer_succeeded + post_closed
→ sucesso causal confirmado.

Se já estava fechado:
→ `ja_estava_fechado`

Se alvo desconhecido/malformado:
→ `nao_encontrado`

Nunca inferir sucesso causal apenas por ausência pós-estado.

Fazer Patch C separadamente.

---

## Consulta ativa/foco atual
Frase:
“Qual está em foco agora?”

O `intent:none` hang já foi resolvido,
mas ainda falta intent operacional read-only de foco ativo.

Tratar como melhoria separada.

---

## Capability truth
Laylay às vezes diz que não consegue criar/editar/acessar arquivos
mesmo possuindo a habilidade.

Também houve:
“Qual deles você fechou?”
com resposta inconsistente em relação ao histórico real.

Isso é outra raiz.
Não misturar com revisão intra-turno.

---

## Condicionais
Não foram incluídas no B1.
Se necessário, estudar como subpatch separado após revisão intra-turno estabilizar.

---

# 12. PADRÃO DE DECISÃO PARA NOVO CHAT

Quando Pedro voltar:

1. Ler primeiro `ESTADO ATUAL — LEIA PRIMEIRO`.
2. Não assumir que o repo continua no HEAD `3c89d27...`.
3. Consultar GitHub atual.
4. Comparar com o teste 2.8 e com a B1.2.1 já aplicada.
5. NÃO pedir para rodar B1.2.1 novamente: ela já passou e está no HEAD 2.8.
6. Se a conversa continuar na revisão intra-turno, retomar o estudo da seção `9B`:
   - SEARCH + `nada` como cancelamento;
   - `deixa desligada` como estado final com alvo herdado;
   - continuação musical canonicalizada.
7. Se ele enviar erro/log:
   - estudar primeiro;
   - localizar raiz;
   - explicar evidência;
   - só então patch.
8. Antes de entregar qualquer patch:
   - fazer uma segunda revisão integral do patch.
9. Se um teste falhar:
   - não assumir que produção está errada;
   - analisar se o próprio teste está errado;
   - diferenciar erro real de teste frágil.
10. Se patcher fizer rollback:
   - considerar o repo restaurado apenas depois de confirmar status/HEAD.
11. Não marcar raiz como fechada só porque pytest focado passou.
   - confirmar no teste de caos/regressão real.
12. Manter patches pequenos e rastreáveis.

Frase-guia:
“Estudar primeiro, corrigir a causa raiz, reanalisar o patch pronto, só então entregar.”

---

# 13. SESSÃO 16/08/2026 — TESTE 3.1 E ESTUDO COMPLETO DA FASE B

## 13.1 Baseline atual reconfirmada

HEAD final do estudo:
`a619a71ff5d1976fb8a25561ab2512ec291e31e8`

Mensagem:
`teste 3.1`

O HEAD foi reconfirmado no fim do estudo e não mudou durante a análise.

### Fase A — capability truth read-only × P0

Status:
FECHADA.

Mudança aplicada no 3.1:
- `mente_laylay/autonomia/comandos_imediatos.py`
- `tests/test_regressao_consciencia_capacidades.py`

Contrato final:
- perguntas de capacidade continuam com `autoriza_execucao=False`;
- o catálogo vivo read-only responde ANTES da barreira de mutação;
- nenhum executor é chamado;
- o turno para antes da LLM quando a resposta local existe;
- a barreira P0 de autorização não foi relaxada.

Manifest do Patch A:
`.laylay_patch_backups/P0_CAPACIDADE_READONLY_A1_20260816_20260816-184006/manifest.json`

Validações registradas:
- status: `ok`;
- red exato falhava antes pela P0;
- `py_compile` candidato: OK;
- `git diff --check`: OK;
- pytest focado: `78 passed`;
- red exato depois: `1 passed`.

Caos 3.1:
- t58 `Você consegue abrir programas?`
  → resposta verdadeira de capacidade;
  → `tratado_prioritario`;
  → sem comando operacional.
- t59 `Você consegue apagar arquivos?`
  → `Consigo... confirmo o alvo... lixeira`;
  → `tratado_prioritario`;
  → sem comando operacional.

Isso fecha a causa raiz da Fase A.

---

## 13.2 Evidência real da Fase B no caos 3.1

Sequência crítica:

t67:
`Cria um arquivo chamado caos seguro.txt e escreve primeira linha.`

Resultado:
- etapa 1 `CREATE_FILE` foi confirmada;
- etapa 2 não foi resolvida;
- fala: `Concluí 1 etapa(s), mas não consegui executar a etapa 2...`.

t68:
`Leia o caos seguro.txt.`

Resultado:
- sem comando operacional;
- caiu em fala genérica.

t69:
`Acrescente segunda linha.`

Resultado:
- sem comando operacional;
- LLM afirmou falsamente não ter acesso a arquivos.

t70:
`Leia de novo.`

Resultado:
- sem comando operacional.

t75:
`O arquivo ainda existe?`

Resultado:
- sem comando operacional;
- conversa genérica/afirmação falsa sobre acesso.

Depois:
- DELETE_ITEM, confirmação, restauração e nova exclusão funcionam;
- portanto o executor/base de arquivos não está globalmente quebrado.

---

# 14. FASE B1 — GRAMÁTICA CONTEXTUAL DE ARQUIVOS

## 14.1 Causa raiz B1 — PROVADA

Arquivo central:
`mente_laylay/arquivos/roteador_arquivos.py`

Blob no HEAD 3.1:
`25710471198b0de6de48ba9763abf1267eb18576`

A função `detectar_intencao_arquivos(...)` já lê no início:
- `arquivo_recente_caminho`
- `arquivo_recente_nome`

a partir da estrutura tipada:
`ultima_estrutura_arquivo_params`.

A helper `_arquivo_recente(...)` só aceita:
`tipo == "arquivo"`

e retorna caminho/nome concreto.
Isso é correto e deve ser preservado.

### Falso suspeito eliminado: contexto não publicado

NÃO é perda de memória entre etapas.

`CicloComandosRuntime.processar_cadeia()`:
- resolve cada etapa isoladamente;
- remonta o contexto vivo para cada trecho;
- limpa apenas retratos referenciais congelados da frase composta;
- mantém a mente compartilhada viva.

O executor de arquivos:
- após CREATE_FILE confirmado;
- registra o arquivo;
- publica `_registrar_estrutura_arquivo_recente(...)` com:
  - `tipo="arquivo"`
  - `arquivo_nome`
  - `caminho`
  - metadados do arquivo.

Logo:
CREATE_FILE publica o arquivo antes da etapa seguinte,
e a cadeia relê estado vivo.
A falha é no CONSUMIDOR DA GRAMÁTICA.

---

## 14.2 B1-a — escrita elíptica

Com referência tipada viva:

`Escreve primeira linha.`

deve produzir:
`CREATE_FILE`
com:
- `alvo=<caminho recente>`
- `conteudo="primeira linha"`
- `editar_existente=True`
- overwrite implícito.

`Acrescente segunda linha.`

deve produzir:
`CREATE_FILE`
com:
- mesmo alvo;
- `conteudo="segunda linha"`
- `editar_existente=True`
- `modo_escrita="append"`.

Estado atual:
a regex de edição exige obrigatoriamente:
- pronome (`nele`, `nela`, `dentro dele` etc.),
OU
- alvo explícito (`dentro do arquivo X`).

Por isso:
`Escreve primeira linha nele.` funciona,
mas:
`Escreve primeira linha.` retorna `None`
mesmo com um único arquivo recente tipado.

Contrato correto:
ELIPSE OPERACIONAL SÓ É VÁLIDA QUANDO EXISTE UMA REFERÊNCIA RECENTE TIPADA E INEQUÍVOCA.

Sem arquivo recente:
- `Escreve primeira linha.` deve continuar sem alvo;
- `Acrescente segunda linha.` deve continuar sem alvo;
- nunca adivinhar caminho.

Direção mínima recomendada:
- não alterar o publisher;
- não alterar executor;
- adicionar uma forma elíptica estreita no roteador, condicionada à existência de `arquivo_recente_caminho`;
- reutilizar a mesma normalização de conteúdo e regra de append já usada pela edição explícita;
- evitar regex genérica que capture comandos de outros domínios.

---

## 14.3 B1-b — leitura por nome

Frase:
`Leia o caos seguro.txt.`

Estado atual:
a gramática `FILE_READ` só aceita referência/pronome:
- `leia ele`
- `leia esse arquivo`
- etc.

O próprio roteador já possui:
`_nomes_arquivo_equivalentes(declarado, conhecido)`

e a abertura de arquivo já usa resolução por nome contra caminhos concretos.
Portanto não falta infraestrutura de resolução.

O executor `FILE_READ` já:
- recebe `caminho`;
- usa `arquivos_leitura.ler_texto`;
- confirma status;
- registra o arquivo;
- republica a referência tipada.

Causa:
FRONT-END DE LINGUAGEM não transforma nome equivalente + referência concreta em `FILE_READ`.

Contrato desejado mínimo:
se:
- existe arquivo recente tipado com caminho concreto;
- o basename declarado equivale ao arquivo recente;

então:
`Leia <nome>` → `FILE_READ(caminho=..., alvo=..., referencia_contextual=True)`.

Sem caminho concreto:
não inventar caminho.

Não ampliar B1 para busca semântica aproximada de leitura por nome sem estudo específico.

---

## 14.4 B1-c — consulta de existência contextual

Frase:
`O arquivo ainda existe?`

Estado atual:
o roteador já usa `FILE_SEARCH` + `referencia_caminho`
para perguntas de caminho do arquivo recente.

O executor `FILE_SEARCH`, quando recebe `referencia_caminho`:
- faz `os.path.isfile(referencia_caminho)`;
- retorna `caminho_encontrado` ou `resultado_expirado`;
- não depende de busca aproximada.

Portanto NÃO é necessário criar nova intent `FILE_EXISTS`.

Contrato desejado:
referência tipada recente +
`O arquivo ainda existe?`
→ `FILE_SEARCH`
com:
- `query=basename`
- `referencia_caminho=<caminho concreto>`
- `alvo=basename`.

Sem referência recente:
não inventar `referencia_caminho`.

### Sibling observado, mas fora do contrato mínimo atual

No caos 3.1 também aparece:
`O arquivo caos seguro.txt existe?`

em outro ponto da sessão.

Esse caso nomeado sem garantia de que o arquivo ainda seja o referente tipado atual deve ser estudado separadamente antes de permitir busca exata/semântica para existência.
Não expandir B1 por conveniência.

---

## 14.5 Escopo recomendado do Patch B1

Produção:
SOMENTE:
`mente_laylay/arquivos/roteador_arquivos.py`

Testes principais:
- `tests/test_red_contratos_arquivos_contexto_capacidades.py`
- `tests/test_arquivos_nove_pilares_regressoes.py`
- `tests/test_cadeia_contexto_vivo_v2.py` para o caminho integrado create → escrita elíptica.

Não tocar no B1:
- `modalidade_turno.py`;
- `execucao_arquivos.py`;
- `continuidade_contexto.py`;
- `contexto_compartilhado.py`;
- `compatibilidade_contexto.py`;
- `comandos_imediatos.py`;
- caixa de entrada;
- executores de delete/restore.

Reds B1 esperados:
1. `test_red__escrita_eliptica_usa_unico_arquivo_recente_tipado`
2. `test_red__append_eliptico_usa_unico_arquivo_recente_tipado`
3. `test_red__referencia_tipificada_publicada_alimenta_escrita_da_etapa_seguinte`
4. `test_red__leitura_por_nome_reusa_arquivo_recente_equivalente_para_file_read`
5. `test_red__consulta_arquivo_ainda_existe_reusa_file_search_com_referencia_caminho`

Guardrails obrigatórios:
- escrita elíptica sem arquivo recente continua `None`;
- escrita com pronome continua funcionando;
- nome diferente do arquivo recente não ganha caminho por adivinhação;
- existência sem referência não inventa caminho;
- cadeia real publica referência da etapa 1 e a etapa 2 usa essa referência viva;
- DELETE/restore não mudam de comportamento.

---

# 15. FASE B2 — REPETIÇÃO SEGURA DE FILE_READ

## 15.1 Causa raiz B2 — PROVADA EM DUAS CAMADAS

Arquivos:
1. `mente_laylay/memoria_mental/compatibilidade_contexto.py`
   blob:
   `768944f808002d8c24f697c0b2769a31d536eb3e`

2. `mente_laylay/memoria_mental/contexto_compartilhado.py`

### Defeito B2-a — linguagem

`texto_pede_repeticao_curta(...)`
usa `re.fullmatch` e reconhece atos inteiros como:
- `de novo`
- `novamente`
- `outra vez`
- `tenta de novo`

Isso é intencional:
`obrigado de novo`
NÃO pode repetir a última ação.

Mas:
`Leia de novo.`
não é reconhecido.

### Defeito B2-b — política

`intencao_reexecutavel(...)`
não contém `FILE_READ`.

Por isso, mesmo um `FILE_READ` confirmado não publica:
`ultima_acao_reexecutavel=True`.

Então:
mesmo `de novo`
não consegue repetir uma leitura confirmada.

---

## 15.2 Nova descoberta de segurança — NÃO fazer correção ingênua

NÃO basta mudar a regex para aceitar:
`<qualquer verbo> + de novo`.

Motivo:
`resolver_repeticao_ultima_acao(...)`
repete a última ação reexecutável.
Sem validação do verbo qualificador,
`Leia de novo`
poderia tentar repetir uma intent de outro domínio se o histórico mais recente fosse diferente.

Contrato seguro:
- `de novo` puro continua usando a política canônica de última ação reexecutável;
- `Leia de novo` é uma repetição QUALIFICADA;
- o qualificador de leitura só pode aceitar/reexecutar `FILE_READ`;
- se a última ação reexecutável não for `FILE_READ`, `Leia de novo` deve retornar `None`, nunca executar outra intent.

Isso precisa de guardrail próprio.

---

## 15.3 Status real do executor

O executor de `FILE_READ` usa status real:
`conteudo_lido`

quando a leitura termina com sucesso.

A fotografia vermelha atual usa `arquivo_lido` em um teste sintético.
Ela ainda prova a política de reexecução por intent,
mas o patch oficial B2 deve adicionar um teste usando o status REAL:
`conteudo_lido`.

Não editar o red antigo apenas para “ficar bonito” ou forçar resultado.
Adicionar regressão oficial realista.

---

## 15.4 Escopo recomendado do Patch B2

Produção:
- `mente_laylay/memoria_mental/compatibilidade_contexto.py`
- `mente_laylay/memoria_mental/contexto_compartilhado.py`

Testes:
- `tests/test_red_contratos_arquivos_contexto_capacidades.py`
- `tests/test_arquivos_nove_pilares_regressoes.py`
- teste integrado do runtime prioritário se necessário para provar que a repetição chega ao executor.

Mudança mínima:
1. reconhecer `Leia de novo` como ato completo de repetição QUALIFICADA;
2. validar que o qualificador de leitura é compatível apenas com `FILE_READ`;
3. incluir `FILE_READ` na política central de intents reexecutáveis.

Não tocar:
- roteador de arquivos;
- executor de arquivos;
- Patch A/P0;
- DELETE_ITEM policy especial;
- FILE_TRANSACTION retry;
- caixa de entrada.

Reds B2:
1. `test_red__leia_de_novo_e_reconhecido_como_repeticao`
2. `test_red__file_read_confirmado_pode_ser_reexecutado_por_repeticao_segura`

Guardrails obrigatórios:
- `obrigado de novo` continua não repetição;
- DELETE_ITEM confirmado continua não reexecutável;
- DELETE_ITEM falho continua obedecendo a política especial existente;
- FILE_TRANSACTION falha/sucesso continua igual;
- `Leia de novo` após APP_OPEN não abre app novamente;
- `Leia de novo` após MEDIA_CONTROL não repete mídia;
- `Leia de novo` sem FILE_READ elegível retorna `None`;
- `de novo` puro após FILE_READ confirmado pode repetir FILE_READ.

---

# 16. POR QUE B1 E B2 DEVEM SER PATCHES SEPARADOS

B1 altera:
GRAMÁTICA/RESOLUÇÃO DE ALVO DE ARQUIVO.

B2 altera:
POLÍTICA GLOBAL DE REEXECUÇÃO.

Apesar de aparecerem na mesma sequência do caos,
os riscos são diferentes.

B1:
- escopo local;
- um arquivo de produção;
- usa contexto tipado já existente.

B2:
- afeta continuidade/replay em vários domínios;
- exige guardrails de segurança;
- toca política central.

Portanto:
Patch B1 primeiro.
Depois:
caos/regressão.
Só então Patch B2.

Isso permite descobrir se leitura nominal B1 já muda naturalmente o estado/referência usado pelo B2,
sem esconder efeitos em um patch grande.

---

# 17. FASE C CONTINUA FORA DO B

Problema já provado:
caixa de entrada sequestra nomes de arquivo que contêm vocabulário como:
- `troca ideia.txt`
- `minha tarefa.txt`
- `pensamento.md`
- `nota.txt`

Causa:
`CaixaEntradaPessoalRuntime.detectar()`
enxerga palavras de domínio dentro do basename antes da porta filesystem,
e a caixa roda antes do roteador de arquivos.

Não corrigir em B1/B2.

Contrato futuro C:
evidência filesystem explícita
(extensão, caminho, moldura inequívoca de arquivo)
deve fazer a caixa ceder,
sem quebrar:
`Apaga essa nota.` → caixa de entrada.

---

# 18. HIGIENE DE GIT APRENDIDA NO TESTE 3.1

O commit `teste 3.1` incluiu, além da mudança real:
- `.laylay_patch_backups/...`;
- patchers temporários;
- fotografia vermelha;
- remoções/renomeações de resultados antigos.

Isso não invalidou o Patch A,
mas torna o commit maior e menos isolado.

Daqui para frente:
antes do commit:
`git status --short`

e selecionar intencionalmente:
- arquivos de produção;
- regressões oficiais;
- resultado de caos que se deseja versionar.

Evitar commitar automaticamente:
- `.laylay_patch_backups/`
- `patch_*.py`
- artefatos diagnósticos temporários

a menos que haja motivo explícito para versioná-los.

---

# 19. PRÓXIMA AÇÃO RECOMENDADA

1. Baseline do próximo trabalho:
   `a619a71ff5d1976fb8a25561ab2512ec291e31e8`
2. Começar pelo Patch B1.
3. Antes de produção:
   - montar regressões B1 completas;
   - rodar no HEAD e confirmar os 5 reds pelo mismatch previsto;
   - confirmar guardrails verdes.
4. Só então patch mínimo em `roteador_arquivos.py`.
5. Reanalisar patch pronto.
6. Entregar patcher B1.
7. Usuário roda.
8. Analisar manifest/diff real.
9. Rodar caos completo.
10. Fechar B1 somente se o caos confirmar:
    - t67 etapa 2 escreve;
    - t68 lê por nome;
    - t69 faz append;
    - t75 consulta existência.
11. Depois estudar/materializar Patch B2 com qualificação segura de `Leia de novo`.
12. Não avançar para Fase C antes de B1/B2 estarem fechadas, salvo nova evidência que mude a prioridade.

Frase-guia mantida:
“Estudar primeiro, provar a causa raiz, materializar o vermelho, corrigir o mínimo, reanalisar o patch pronto, só então entregar.”

---

# ADENDO — 2026-08-16 — FOTOGRAFIA VERMELHA B1 PREPARADA (AINDA NÃO EXECUTADA)

Baseline reconfirmada no GitHub durante o estudo:
`a619a71ff5d1976fb8a25561ab2512ec291e31e8` — `teste 3.1`.

## Descoberta nova que altera o desenho do B1

O B1 não é apenas uma regex ausente em `roteador_arquivos.py`.

Foi comprovado por leitura cruzada do código atual que existe drift entre três
camadas do contrato de linguagem operacional:

1. `mente_laylay/autonomia/porteiro_acoes.py`
   - `texto_tem_comando_explicito()` reconhece `escreve/grava` somente quando
     também encontra certos alvos explícitos;
   - não inclui `adiciona/adicione/acrescenta/acrescente` no vocabulário geral.

2. `mente_laylay/cognicao/modalidade_turno.py`
   - `_P0_GATILHOS_OPERACIONAIS` conhece `escreve/grava`, mas a lista de
     imperativos diretos não os contém;
   - verbos append (`adiciona/acrescenta`) não estão alinhados entre
     classificação, pedido direto e proteção P0.

3. `mente_laylay/arquivos/roteador_arquivos.py`
   - já entende edição com pronome para TODOS esses verbos:
     `escreve/escreva/grava/grave/adiciona/adicione/acrescenta/acrescente`.

Consequência estrutural observada no código:
- `Escreve primeira linha nele.` pode ser reconhecido pelo roteador, mas ser
  bloqueado pela barreira P0 porque o turno não foi marcado autorizado.
- `Acrescente segunda linha nele.` pode ser reconhecido pelo roteador enquanto
  o turno continua com `autoriza_execucao=False`; como esse verbo também não é
  gatilho P0, a rota prioritária de arquivo pode alcançar mutação sem que o
  contrato de autorização esteja alinhado.

Portanto NÃO aplicar apenas uma regex de elipse no roteador.

## Nova divisão recomendada dentro do B1

### B1A — alinhamento linguagem ↔ autorização
Arquivos candidatos de produção:
- `mente_laylay/autonomia/porteiro_acoes.py`
- `mente_laylay/cognicao/modalidade_turno.py`

Objetivo:
- formas imperativas de escrita/append aceitas pelo roteador precisam ser
  reconhecidas como pedidos reais;
- negativas, hipóteses e perguntas sobre essas ações precisam continuar
  fail-closed;
- nunca permitir que uma mutação execute com `autoriza_execucao=False`.

### B1B — gramática contextual de arquivos
Arquivo candidato:
- `mente_laylay/arquivos/roteador_arquivos.py`

Objetivo:
- `Escreve primeira linha.` + arquivo recente tipado → editar aquele arquivo;
- `Acrescente segunda linha.` + arquivo recente tipado → append;
- sem arquivo tipado → não adivinhar alvo;
- pasta recente nunca pode virar arquivo por elipse.

### B1C — leitura nominal
Mesmo roteador:
- `Leia o caos seguro.txt.` → `FILE_READ` somente se o nome equivaler a um
  caminho de arquivo concreto já publicado;
- nome diferente não pode sequestrar o caminho recente;
- reaproveitar a equivalência de nomes já existente, não criar hardcode.

### B1D — existência contextual
Mesmo roteador:
- `O arquivo ainda existe?` + arquivo recente tipado →
  `FILE_SEARCH(query=basename, referencia_caminho=path, alvo=basename)`;
- sem referência concreta → não inventar caminho.

## Snapshot preparado

Arquivo de teste:
`tests/test_red_b1_arquivos_contexto_vivo_3_1.py`

Payload SHA-256:
`84007e4b7ba0d8e0dbdf392009850d445f5b1777f15c0529107441d59c53074d`

Patcher TEST-ONLY:
`patch_fotografia_vermelha_b1_arquivos_contexto_3_1.py`

Patcher SHA-256:
`067ad78abf1ef293e4b00b4111754db919fccd01adee517892081e67f1af8965`

O patcher trava:
- HEAD `a619a71...`;
- blobs do roteador, modalidade, porteiro, comandos imediatos, segmentador,
  publisher de contexto e testes-base;
- recusa fontes B1 sujas;
- reconfirma Patch A verde;
- reconfirma os 5 reds B1 antigos;
- adiciona somente o novo arquivo de teste;
- valida AST/py_compile/diff;
- exige 9 grupos guard verdes;
- exige 10 grupos vermelhos, totalizando 23 casos por AssertionError;
- rollback remove apenas o teste novo;
- não faz add/commit/push/reset/checkout/clean.

STATUS POSTERIOR: ESTE SNAPSHOT FOI EXECUTADO E CONFIRMADO.
A execução real na baseline `a619a71...` confirmou:
- 9 grupos de guards verdes;
- 10 grupos vermelhos / 23 casos falhando por AssertionError como esperado;
- 5/5 reds B1 antigos reconfirmados;
- guard da Patch A verde;
- produção não modificada;
- sem git add/commit/push.
O manifest e o `test_candidate.diff` foram auditados depois, sem divergências de
HEAD/blob/payload.

## Ordem após a execução do snapshot

1. analisar saída completa + manifest + diff;
2. se qualquer red inesperadamente ficar verde, estudar a rota real antes de
   mudar teste ou produção;
3. se snapshot for confirmado, decidir se B1A e B1B/C/D serão dois patchers
   sequenciais (preferência atual) ou se a evidência justificar outra divisão;
4. gerar REDS oficiais/rastreáveis antes de produção;
5. patch mínimo;
6. reanálise integral do patch pronto;
7. usuário executa;
8. analisar manifest/diff;
9. caos completo;
10. só então fechar sub-raiz.

Frase-guia permanece:
“Estudar primeiro, provar o vermelho, corrigir a causa raiz, reanalisar o patch
pronto, só então entregar.”

### Segunda reanálise antes da entrega

A revisão do próprio artefato encontrou e eliminou um defeito no patcher
intermediário: uma tentativa de substituir programaticamente o payload embutido
quebrou a string Python. Esse patcher intermediário NÃO foi entregue.

A versão final foi regenerada do zero e validada novamente por AST + py_compile.

Hardening adicional da versão final:
- payload do teste é escrito por bytes UTF-8 para manter SHA idêntico no Windows
  (sem transformação LF → CRLF);
- `git diff --no-index --check` continua obrigatório, sem confundir warning
  inofensivo de autocrlf com trailing whitespace;
- o red de rota `Escreve primeira linha nele.` chama primeiro o runtime, para
  capturar a barreira P0 real antes de verificar os metadados.

Hashes finais:
- teste: `84007e4b7ba0d8e0dbdf392009850d445f5b1777f15c0529107441d59c53074d`
- patcher: `067ad78abf1ef293e4b00b4111754db919fccd01adee517892081e67f1af8965`

# ATUALIZAÇÃO — FASE B, PARTE 2 DA PROCURA DA RAIZ (2026-08-16)

Esta seção SUPERA o desenho anterior de B1A como simples alinhamento de
vocabulário. A investigação aprofundada mostrou duas raízes arquiteturais
específicas e uma manifestação secundária em cadeias.

Baseline reconfirmada antes da nova fotografia:
- HEAD: `a619a71ff5d1976fb8a25561ab2512ec291e31e8`
- commit: `teste 3.1`
- tree: `d34075c5c3d1a1c34c6181612009c6e62f12c26b`

Produção continua INTOCADA nesta nova etapa.

## Auditoria do primeiro snapshot B1 — CONFIRMADA

A fotografia anterior foi executada por Pedro e depois auditada pelo manifest e
pelo `test_candidate.diff`.

Resultado real:
- 9 grupos de guards verdes;
- 10 grupos vermelhos / 23 casos por AssertionError;
- 5/5 reds B1 antigos reconfirmados;
- Patch A capability read-only permaneceu verde;
- arquivo de teste ficou untracked;
- nenhuma modificação de produção;
- sem add/commit/push.

A auditoria mostrou que os reds não eram genéricos:
- `Escreve primeira linha nele.` era barrado cedo pela P0;
- `Acrescente segunda linha nele.` chegava a `CREATE_FILE` enquanto
  `turno.autoriza_execucao == False`.

Isso provou um drift real entre linguagem, autorização e execução.

## R1 — quebra da autoridade do turno na fase prioritária

### Causa raiz específica

A raiz NÃO é simplesmente “faltam verbos em regex”.

Fluxo atual problemático:

`turno congelado -> P0 lexical sobre texto -> roteador posterior descobre intent -> executar_intencao`

A P0 decide antes de conhecer a intent concreta. Quando o turno não está
autorizado e o verbo não aparece no vocabulário da P0, a barreira pode retornar
“não bloquear”. Depois disso, `ComandosImediatosRuntime.processar_prioritarios()`
pode descobrir uma intent nova com efeito e despachá-la diretamente.

O caminho canônico da linguagem natural/LLM é diferente: ele envia o candidato
ao árbitro e respeita o contrato congelado do turno. O árbitro já distingue
`INTENTS_SOMENTE_LEITURA` de intents com efeito.

Portanto a raiz R1 é:

> A fase prioritária usa uma decisão lexical pré-intent e não reaplica a
> autoridade canônica depois que uma intent concreta com efeito nasce.

### Reproduções independentes de R1

1. Append contextual:
   - `Acrescente segunda linha nele.`
   - roteador reconhece `CREATE_FILE(edit_existing=True, append)`;
   - turno pode continuar `autoriza_execucao=False`;
   - prioridade pode despachar mesmo assim.

2. Restore:
   - `Restaura o último arquivo.`
   - roteador só produz `RESTORE_DELETED_ITEM` quando existe exclusão anterior
     realmente confirmada e recente;
   - isso prova o ALVO, mas não prova autorização do ATO atual;
   - a intent cai no mesmo corredor prioritário e pode ser despachada sem nova
     arbitragem.

3. FILE_OPEN_RESULT:
   - a porta prioritária agrupa `FILE_OPEN_RESULT` junto de leituras, mas o
     catálogo canônico NÃO o classifica como read-only;
   - `FILE_SEARCH` e `FILE_READ` são somente leitura;
   - `FILE_OPEN_RESULT` é ação com efeito externo.

### Cadeias — manifestação de R1, não terceira raiz

`CicloComandosRuntime` segmenta uma cadeia e remonta cada etapa com
`autoriza_execucao=True`.

A rota real foi rastreada até o mesmo detector determinístico/roteador de
arquivos. Logo a autorização fabricada é alcançável até mutação real.

Sentença atual:
- cadeia NÃO é tratada como raiz independente;
- ela é uma amplificação/lavagem de autorização causada pela quebra de
  autoridade da fronteira prioritária;
- um turno-pai não autorizado nunca deve virar etapas autorizadas apenas por ter
  sido segmentado.

## R2 — quebra da validade contextual no roteador de arquivos

### Falsos suspeitos eliminados

Foram descartadas as hipóteses:
- publisher não salva contexto -> FALSO;
- publisher esquece timestamp -> FALSO;
- lifecycle está morto -> FALSO;
- não existe política canônica de frescor -> FALSO.

A política correta já existe:
- `estrutura_arquivo`
- timestamp: `ultima_estrutura_arquivo_ts`
- TTL: 900 s.

O publisher canônico grava dados + timestamp.

Também já existe o accessor canônico:
`estrutura_arquivo_recente(estado, ttl_s=900)`

Ele rejeita:
- estrutura ausente;
- timestamp ausente;
- timestamp inválido;
- idade > TTL.

### Causa raiz específica

O roteador de arquivos criou leitores paralelos (`_arquivo_recente` e leitura
crua de `ultima_estrutura_arquivo_params`) e NÃO usa o accessor canônico de
frescor.

Assim, ele pode consumir:
- arquivo recente vencido;
- estado legado com dados mas sem timestamp;
- pesquisa semântica vencida;
- ordinais como `o primeiro` ligados a resultados já expirados.

A ordem real do fluxo confirmou que o lifecycle não salva essa rota:

1. `marcar_inicio_turno`
2. `processar_comandos_prioritarios`
3. `processar_inicio_fluxo`
4. somente dentro do pre-fluxo, `_refinar_contexto_mental()` aplica
   `aplicar_ciclo_vida_contexto()`.

Portanto a prioridade pode consumir contexto stale ANTES da expiração oficial.
Se ela consumir o turno, a limpeza pode nem chegar a ocorrer naquele caminho.

Raiz R2:

> O roteador de arquivos ignora o accessor canônico de validade e lê estado
> efêmero cru numa fase que roda antes do lifecycle oficial.

## Interseção R1 + R2

Pior cenário que a nova fotografia precisa provar:

`turno não autorizado + referência stale + mutação contextual -> ZERO execução`

Exemplo de classe:
- existe um arquivo tipado antigo, já além do TTL;
- usuário produz uma forma contextual de append;
- o turno não está autorizado;
- mesmo assim o roteador cru encontra o caminho;
- hoje R1 + R2 podem se combinar.

A futura correção precisa impedir a mutação em ambas as dimensões:
- autoridade atual do turno;
- validade atual da referência.

## Nova fotografia vermelha R1/R2 — PREPARADA, AINDA NÃO EXECUTADA

Arquivo de teste:
`tests/test_red_raizes_autorizacao_contexto_arquivos_3_1.py`

Artefato entregue:
`test_red_raizes_autorizacao_contexto_arquivos_3_1.py`

SHA-256 do teste:
`f9784b7e8b469c3748ca4aeab569ca8d022070a8fe62ace3c3d54c6bd0cecdea`

Patcher TEST-ONLY:
`patch_fotografia_vermelha_raizes_r1_r2_3_1.py`

SHA-256 do patcher:
`cbd0b843407f389bc5bd4df767db58c66150550f78878595cd0f6f071f361973`

### Estrutura esperada

- 8 grupos de guards verdes;
- 9 grupos vermelhos;
- 15 casos vermelhos totais, todos por AssertionError;
- produção modificada: NÃO;
- commit/push automático: NÃO.

### Guards da nova fotografia

1. catálogo canônico separa `FILE_SEARCH`/`FILE_READ` das intents com efeito;
2. accessor canônico rejeita stale e sem timestamp;
3. publisher + accessor preservam referência fresca;
4. prioridade continua permitindo `FILE_SEARCH` e `FILE_READ` read-only mesmo
   quando mutação não está autorizada;
5. roteador continua consumindo referência fresca de arquivo;
6. pesquisa semântica fresca continua permitindo ordinal;
7. cadeia com turno-pai realmente autorizado preserva autorização;
8. negações/hipóteses continuam sem autorizar efeito.

### Reds R1

1. classificador passa a reconhecer quatro formas de append já aceitas pelo
   roteador (`Acrescente`, `Acrescenta`, `Adicione`, `Adiciona`);
2. classificador reconhece `Restaura o último arquivo.` como ordem direta;
3. mutações descobertas DEPOIS da P0 não podem executar com turno não
   autorizado, testando estruturalmente:
   - `CREATE_FILE(edit_existing=True)`
   - `RESTORE_DELETED_ITEM`
   - `FILE_OPEN_RESULT`
4. append real não chega ao executor quando o turno congelado não autorizou;
5. restore real não chega ao executor quando o turno congelado não autorizou;
6. cadeia não pode promover `False -> True` para autorização.

### Reds R2

7. roteador deve rejeitar arquivo que o accessor canônico já considera morto:
   - timestamp stale;
   - timestamp ausente;
8. pesquisa semântica stale não pode abrir `o primeiro`.

### Red R1 + R2

9. turno não autorizado + referência stale + append contextual jamais viram
   mutação.

### Locks do novo patcher

O patcher trava HEAD e blobs estudados, incluindo:
- `roteador_arquivos.py`
- `comandos_imediatos.py`
- `coordenador_intencao.py`
- `analise_comandos.py`
- `porteiro_acoes.py`
- `modalidade_turno.py`
- `continuidade_contexto.py`
- `ciclo_vida_contexto.py`
- `especialistas/capacidades.py`
- testes P0 e snapshot antigo.

Comportamento:
- recusa HEAD diferente;
- recusa arquivo-alvo já existente;
- recusa fontes estudadas sujas;
- valida blobs;
- reconfirma guards P0 antigos;
- reconfirma guards do snapshot anterior;
- reconfirma Phase A capability read-only;
- grava teste por bytes UTF-8/LF;
- AST + py_compile;
- `git diff --no-index --check`;
- exige 8 grupos guard verdes;
- exige 9 grupos / 15 casos reds;
- em qualquer divergência aplica rollback apenas do novo teste;
- NÃO faz add/commit/push/reset/checkout/restore/clean.

## PRÓXIMO PASSO OBRIGATÓRIO

Pedro deve executar, da raiz do repositório:

```powershell
python patch_fotografia_vermelha_raizes_r1_r2_3_1.py --repo .
```

ou:

```powershell
py patch_fotografia_vermelha_raizes_r1_r2_3_1.py --repo .
```

Resultado esperado para considerar a teoria materializada:

```text
🥩 FOTOGRAFIA VERMELHA R1/R2 CONFIRMADA
HEAD: a619a71ff5d1976fb8a25561ab2512ec291e31e8
Guards: 8 grupos verdes
Reds: 9 grupos / 15 AssertionError cases
Produção modificada: NÃO
Commit/push automático: NÃO
```

Se qualquer red ficar verde, se a contagem divergir, se algum guard quebrar ou
se qualquer lock divergir:
- NÃO ajustar teste para encaixar na teoria;
- estudar a rota real;
- NÃO produzir patch de produção.

Se confirmar:
1. pedir saída completa;
2. auditar `manifest.json` + `test_candidate.diff`;
3. só então desenhar o patch mínimo;
4. preferir reutilizar contratos canônicos existentes em vez de novas listas:
   - autoridade/árbitro do turno para R1;
   - `INTENTS_SOMENTE_LEITURA` para distinguir consulta de efeito;
   - `estrutura_arquivo_recente()` para R2;
5. materializar qualquer novo red estrutural que a auditoria revelar;
6. patch mínimo;
7. reanálise integral do patch pronto;
8. execução pelo usuário;
9. auditoria de manifest/diff;
10. caos/regressão antes de fechar R1/R2.

## Regra metodológica reforçada por esta etapa

Esta investigação é o exemplo canônico do motivo da regra “não satisfeito”.

Não aceitar como causa raiz:
- primeira regex faltante;
- primeiro comportamento reproduzido;
- primeira correção que faz o exemplo passar.

Exigir:
- reproduções independentes da mesma classe;
- tentativa ativa de falsificar a hipótese;
- falsos suspeitos explicitamente descartados;
- rastreamento da ordem real do runtime;
- preferência por contratos canônicos já existentes;
- red estrutural antes da produção;
- reanálise do próprio teste/patcher antes de entrega.

Frase-guia permanece:

“Estudar primeiro, provar o vermelho, corrigir a causa raiz, reanalisar o patch
pronto, só então entregar.”


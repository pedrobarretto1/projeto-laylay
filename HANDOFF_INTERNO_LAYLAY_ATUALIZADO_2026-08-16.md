# HANDOFF INTERNO — PROJETO LAYLAY
Data: 2026-08-16
Atualizado em: 2026-08-16 11:24 (America/Sao_Paulo)
Objetivo: continuidade segura em novos chats.

## ESTADO ATUAL — LEIA PRIMEIRO

HEAD atual confirmado no GitHub:
`3c89d27ce4712827e359ec7d1a1da888398e2203`
mensagem:
`teste 2.8`

Estado das raízes:
- Bug B — observabilidade/identidade de execuções: FECHADO.
- Patch A — autorização por ato de fala: FECHADO.
- B1.1 — revisão intra-turno inicial: APLICADO.
- B1.2.1 — separação entre identidade do turno e texto operacional: APLICADO E VALIDADO NO TESTE 2.8.
- Próxima raiz dentro de B1: três formas de revisão ainda mal canonicalizadas antes dos roteadores:
  1. `Pesquisa Python... pera, não pesquisa nada.` deve virar NOOP.
  2. `Liga a lâmpada... não, deixa desligada.` deve virar uma única ação final de desligar a lâmpada, herdando o alvo.
  3. `Pausa a música... esquece, continua tocando.` deve virar uma única ação final de continuar/reproduzir usando uma forma canônica aceita por autorização + roteador.

Resultado do teste de caos 2.8:
- 267/267 turnos respondidos;
- transporte concluído;
- 54 avaliados semanticamente;
- 29 passaram;
- 23 falharam;
- 2 alertas;
- taxa semântica: 53,7%;
- 114 comandos observados;
- 9 confirmações indeterminadas;
- latência p50 2,087 s;
- p95 8,262 s;
- máximo 19,137 s;
- média 2,954 s.

Conclusão operacional:
o bug `plano_de_outro_turno` do teste 2.7 foi resolvido pela B1.2.1.
A próxima correção NÃO deve mexer no contrato de identidade do plano novamente.
O foco deve permanecer em `mente_laylay/cognicao/revisao_turno.py`, salvo nova evidência em contrário.

---

## 1. COMO TRABALHAR COM A LAYLAY

O usuário, Pedro, prefere um fluxo de engenharia cuidadoso e incremental.

REGRA PRINCIPAL:
NUNCA gerar e entregar um patch imediatamente após encontrar uma hipótese de correção.

Fluxo obrigatório para QUALQUER patch:

1. Estudar o bug antes de mexer.
2. Confirmar a causa raiz no código atual.
3. Confirmar o HEAD/estado atual do repositório.
4. Localizar arquivo, função, contrato e ponto exato de inserção.
5. Avaliar efeitos colaterais e consumidores downstream.
6. Fazer a menor alteração possível.
7. Criar testes de regressão que representem o comportamento real.
8. Gerar o patcher com:
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
9. DEPOIS DE GERAR O PATCH, REANALISAR O PATCH INTEIRO ANTES DE ENTREGAR.
10. Na reanálise final, confirmar:
   - se mexe realmente no lugar certo;
   - se não toca módulos desnecessários;
   - se preserva contratos existentes;
   - se o teste não é frágil/errado;
   - se o baseline ainda é o atual;
   - se as âncoras correspondem ao código real;
   - se o patch resolve a causa raiz e não apenas o sintoma;
   - se não reintroduz bugs já fechados.
11. Só então entregar o patch ao usuário.
12. Depois que o usuário rodar, analisar a saída antes de considerar o patch fechado.
13. Após patch aplicado, rodar o teste de caos/regressão antes de encerrar a raiz.

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


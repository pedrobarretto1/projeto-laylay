# HANDOFF LAYLAY — V2.4 REINICIADO

**Data:** 20/08/2026  
**Escopo:** somente as regras/aprendizados soberanos e o trabalho discutido nesta conversa sobre o V2.4.  
**Objetivo deste arquivo:** substituir handoffs antigos e evitar carregar histórico desnecessário. Se algo não estiver aqui, não deve ser presumido como autoridade.

---

# 1. REGRA MÁXIMA

> **Antes de criar patch, candidato ou arquivo de produção, estudar a fundo até existir evidência suficiente da raiz.**

A ordem é:

1. observar;
2. falsificar hipóteses;
3. identificar a primeira fronteira RED;
4. revisar o caminho real de produção;
5. revisar o próprio harness;
6. só então construir candidato;
7. falsificar o candidato;
8. fazer uma segunda revisão integral;
9. somente depois considerar patch de produção.

**GREEN nunca recebe autoridade automaticamente.**

---

# 2. REGRAS SOBERANAS DE INVESTIGAÇÃO

## 2.1 Runtime real só é real quando atravessa o caminho real

- Chamar uma função real isoladamente não torna o teste E2E.
- Harness ≠ produção.
- Integração intermediária deve ser chamada de integração intermediária.
- Nunca descrever uma prova cognitiva/determinística como execução física.

## 2.2 Primeira fronteira RED manda no diagnóstico

Se a cadeia for:

```text
A -> B -> C -> D
```

e B for o primeiro ponto em que a semântica quebra, B é a raiz cognitiva testada. C/D podem ser amplificadores, mas não substituem a primeira fronteira.

## 2.3 Contexto não cria autoridade

Memória, app ativo, alvo recente, catálogo, LLM, detector e executor podem ajudar a resolver **o quê**, mas não podem inventar **permissão para agir**.

## 2.4 Detector não decide polaridade

Um detector pode provar perigo (`isto poderia virar VOLUME/CLOSE_APP/...`). Ele não pode concluir que uma fala está autorizada só porque não encontrou perigo.

## 2.5 Não atualizar locks às cegas

Mudança de HEAD/blob invalida a premissa do harness até nova revisão. Nunca trocar SHA apenas para fazer o teste rodar.

## 2.6 Falsificações vêm antes do candidato

Antes de construir candidato, procurar casos que o destruam:

- inversões;
- comandos novos/futuros;
- aliases;
- payloads;
- pontuação perdida por STT;
- acento/sem acento;
- títulos/nomes que parecem comandos;
- domínios diferentes;
- ordem real dos detectores;
- normalização que apaga fronteiras.

## 2.7 Segunda revisão integral é obrigatória

Mesmo EXIT 0 do candidato não libera patch. Procurar GREEN mentiroso, controle inválido e premissa semântica falsa.

## 2.8 Preservar `auth=True` não basta

Controle de payload só é válido se preservar também a **moldura operacional correta**.

Exemplo de GREEN mentiroso já aprendido:

```text
renomeia arquivo teste.txt para nao feche.txt
```

Se a classificação continuar `auth=True`, mas o `texto_operacional` virar `feche txt`, isso é falha semântica, não PASS.

## 2.9 Estrutura local não prova segurança end-to-end

Se um analisador marca uma substring como `payload`, mas downstream recebe novamente apenas uma string achatada, a proteção desapareceu. Payload só pode ser tratado como opaco com segurança quando a tipagem sobreviver até os consumidores relevantes.

---

# 3. LOCK ATUAL DA CONVERSA

HEAD estudado:

```text
a4741bc57bc55a50ef2861dbaef09ab36397ff63
```

Blobs causais usados no novo RED:

```text
revisao_turno.py                 222d92624899ed55cc74628869b376075b7e6a1c
modalidade_turno.py              80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241
normalizacao_linguagem.py        92d9a30435a4401c487e991ed793223eb215aeb7
porteiro_acoes.py                19b5eaa9ddafd483eab92d46e92cca30813adbb6
roteador_deterministico.py       a011d0da655c2f00c1d9d75e723ae559107f31e5
orquestrador_deterministico.py   5e1134128c2abdca9e22ec566796bb86159fd007
```

Produção permanece **intacta**.

---

# 4. ESTADO ARQUITETURAL DO V2.4

## 4.1 O problema não é apenas a lista privada do V2.3

O estudo mostrou várias taxonomias diferentes de “verbo/ação operacional” na produção:

- modalidade;
- P0 de ato de fala;
- segmentador cognitivo;
- porteiro;
- preparação/roteador determinístico;
- detectores especialistas.

`abaixa/aumenta/diminui` aparecem em algumas superfícies e faltam em outras.

**Conclusão:** corrigir V2.3 copiando/expandindo `OP_VERB_RE` apenas cria outra fonte sujeita a drift.

## 4.2 Descoberta mais importante: payload tipado localmente volta a ser string

O V2.3 conseguia dizer localmente:

```text
SEARCH(query="nao abaixa o volume")
WRITE(payload="nao abaixa o volume")
MUSIC(title="nao abaixa o volume")
```

Mas os detectores downstream continuam podendo receber a fala inteira como texto normalizado. Assim, a informação “isto era payload” pode morrer antes do consumidor.

Logo:

> **“está dentro de payload” não é prova suficiente de segurança enquanto essa tipagem não for carregada end-to-end.**

## 4.3 Hipótese causal nova: PAYLOAD -> VOLUME

Casos estudados:

```text
toca nao abaixa o volume
pesquisa nao abaixa o volume
escreve nao abaixa o volume no arquivo teste.txt
cria arquivo teste.txt contendo nao aumenta o volume
abre o arquivo nao abaixa volume.txt
```

Caminho suspeito:

```text
fala sem pontuação
    ↓
revisão não resolve
    ↓
modalidade autoriza pelo verbo inicial
    ↓
P0/barreira histórica não reconhece a restrição interna
    ↓
roteador determinístico recebe texto plano
    ↓
detector antecipado de VOLUME vê `volume + abaixa/aumenta/diminui`
    ↓
VOLUME(down/up)
```

Isto é especialmente importante porque no roteador real o detector de mídia/volume tem uma oportunidade **antes** de SEARCH e antes de vários detectores posteriores.

Ainda não chamar isso de E2E físico: é uma hipótese de fronteira cognitiva/determinística que precisa do RED 4.24.

---

# 5. V2.4 RECOMENDADO — PRINCÍPIO CONSERVADOR

O desenho preferido após este estudo é **não perguntar qual verbo vem depois de `não`**.

Fluxo conceitual:

```text
classificação histórica
        ↓
P0 histórica já bloqueou?
  SIM -> preservar histórico / crédito V2.4 zero
  NÃO
        ↓
histórico autoriza execução?
  NÃO -> preservar histórico / crédito zero
  SIM
        ↓
há marcador negativo INTERNO standalone no RAW?
  nao | não | nunca | jamais
        ↓
  SIM
        ↓
não existe prova end-to-end de literalidade
        ↓
FAIL-CLOSED
```

Resultado conceitual:

```text
autoriza_execucao = False
acao_explicita = False
texto_operacional = ""
requer_esclarecimento = True   # intenção desejada; integração ainda precisa ser provada
```

### Por que isso é melhor

Não depende de conhecer:

- `abaixa`;
- `aumenta`;
- `diminui`;
- qualquer verbo futuro;
- catálogo de apps;
- catálogo musical;
- LLM;
- contexto;
- detector especialista.

Assim um comando novo criado no futuro não abre automaticamente um novo furo de polaridade.

---

# 6. EXCEÇÕES: SER EXTREMAMENTE CONSERVADOR

## 6.1 `nao.txt` continua sendo caso importante

`nao.txt` é um átomo lexical, não necessariamente uma negação gramatical. O V2.4 não deve virar simplesmente:

```python
"nao" in texto
```

A detecção precisa operar no RAW e respeitar fronteiras lexicais.

Controles que devem continuar na investigação:

```text
cria arquivo nao.txt
abre o arquivo nao.txt
renomeia nao.txt para sim.txt
```

## 6.2 Não liberar automaticamente formas mais perigosas

Exemplo:

```text
nao-feche.txt
```

Pode ser filename no RAW, mas normalização downstream pode virar:

```text
nao feche txt
```

Sem tipagem end-to-end, não assumir segurança.

## 6.3 Aspas não bastam sozinhas no runtime atual

No parser, aspas são forte evidência de literalidade. Porém se a pontuação/aspas some antes do detector downstream, essa evidência não protege a execução.

Logo, não liberar payload apenas porque estava entre aspas sem provar transporte estrutural até os consumidores.

---

# 7. RECLASSIFICAÇÃO DE ANTIGOS “PAYLOADS DEVEM PASSAR”

Após este estudo, os seguintes casos **não podem mais ser usados como PASS obrigatório do primeiro V2.4**:

```text
pesquisa nao feche o opera
toca nao existe amor em sp
escreve nao feche o opera no arquivo
```

Enquanto a literalidade não sobreviver end-to-end, a política mais segura é:

```text
ambíguo -> não executar -> esclarecer
```

Isso não é mudar o teste para agradar o candidato. É corrigir uma premissa arquitetural que se mostrou falsa: **classificar payload localmente não garante que downstream preserve o payload.**

---

# 8. MELHORIA FUTURA SEPARADA DO ROOT 229

Uma solução completa para naturalidade de payload deve transportar estrutura tipada, algo conceitualmente como:

```text
TurnoEstrutural
└── etapas
    ├── frame
    ├── raw_span
    ├── payload_spans
    ├── negacoes
    └── literalidade
```

Essa estrutura precisa sobreviver:

```text
gramática -> modalidade -> decisão -> roteador -> detector/especialista
```

Só então um detector de volume poderia saber:

```text
"abaixa o volume" está dentro de conteúdo de arquivo
=> não interpretar como VOLUME
```

### Lar arquitetural preferido

`mente_laylay/cognicao/gramatica_operacional.py`

Motivos:

- camada cognitiva baixa;
- funções puras;
- sem contexto;
- sem executor;
- sem autoridade;
- já pode ser compartilhada por modalidade e segmentação.

`cognicao/evidencia_operacional.py` **não deve ser importado pela modalidade como base genérica hoje**, porque ele já depende de `modalidade_turno`, o que cria risco de dependência circular.

---

# 9. RED CRIADO NESTA CONVERSA

Arquivo:

```text
red_v2_4_payload_volume_precedence_teste4_24.py
```

Objetivo:

Provar/falsificar a cadeia real entre componentes:

```text
resolver_revisao_intra_turno()
    ↓
classificar_modalidade_turno()
    ↓
bloqueia_execucao_operacional_prioritaria()
    ↓
detectar_intencao_deterministica_mente()
```

O harness **não executa volume físico**.

Ele testa especialmente:

```text
MUSICA:
  toca nao abaixa o volume
  toca não aumenta o volume
  toca nao diminui o volume

SEARCH:
  pesquisa nao abaixa o volume
  pesquisa gatos nao aumenta o volume

ARQUIVO/CONTEÚDO:
  escreve nao abaixa o volume no arquivo teste.txt
  cria arquivo teste.txt contendo nao aumenta o volume
  abre o arquivo nao abaixa volume.txt
```

### Semântica de exit

```text
EXIT 2 = RED sustentado em pelo menos um killer
EXIT 0 = hipótese PAYLOAD→VOLUME falsificada com premissas válidas
EXIT 1 = lock/harness/premissa histórica inválida
```

**Nunca interpretar apenas a última linha. Ler a primeira fronteira inválida/RED.**

---

# 10. COMO INTERPRETAR O PRÓXIMO RESULTADO

## Se EXIT 2

Não criar patch imediatamente.

Primeiro separar por domínio:

```text
MUSICA
SEARCH
ARQUIVO_CONTEUDO
ARQUIVO_NOME
```

Ver qual foi a **primeira fronteira RED** e quais casos realmente chegaram a `VOLUME(down/up)`.

Se `toca...`, `pesquisa...` e `escreve/cria...` reproduzirem, o problema é claramente multidomínio e reforça a barreira conservadora do V2.4.

## Se EXIT 1

Não chamar candidato de falsificado.

Investigar a primeira premissa que mudou:

- revisão entrou antes?
- modalidade já bloqueou?
- barreira histórica passou a bloquear?
- controle do detector mudou?
- lock divergiu?

## Se EXIT 0

A hipótese PAYLOAD→VOLUME foi falsificada na cadeia testada.

Não construir V2.4 baseado nessa causalidade. Voltar ao estudo da ordem real antes de candidato.

---

# 11. O QUE NÃO FAZER AGORA

- não alterar produção;
- não criar patch do V2.4 antes do RED 4.24;
- não ampliar `_REVISAO` para `nao` sem pontuação;
- não criar nova lista privada de verbos;
- não usar catálogo/LLM/contexto como autoridade de polaridade;
- não declarar SEARCH/payload opaco por causa do V2.1; ele provou isolamento SEARCH→CLOSE na matriz dele, não isolamento universal;
- não misturar bugs laterais com o root sem causalidade;
- não transformar GREEN intermediário em fechamento de root.

---

# 12. PRÓXIMO PASSO EXATO

Executar, a partir da raiz do projeto:

```powershell
& C:\Python314\python.exe ".\red_v2_4_payload_volume_precedence_teste4_24.py"
```

Depois trazer **a saída completa**.

Antes de qualquer candidato V2.4, revisar o resultado inteiro procurando:

1. primeira fronteira RED;
2. controles inválidos;
3. GREEN mentiroso;
4. diferença entre música, SEARCH e arquivo;
5. se a cadeia testada é integração real de componentes ou apenas função isolada;
6. qualquer evidência de que a premissa arquitetural precisa mudar novamente.

---

# 13. ESTADO FINAL DESTA CONVERSA

```text
produção ................................ INTACTA
patch V2.4 ............................... BLOQUEADO
V2.3 como implementação final ........... REJEITADO
princípio multi-ato ...................... ÚTIL
payload local = segurança end-to-end ..... NÃO SUSTENTADO
lista privada de verbos .................. REJEITADA
V2.4 conservador sem taxonomia ........... DIREÇÃO PREFERIDA
PAYLOAD→VOLUME ........................... HIPÓTESE A SER RED-FALSIFICADA
próxima autoridade ....................... RED 4.24
```

**Não carregar handoffs antigos por padrão. Este arquivo é o novo ponto de continuidade.**


---

# 14. ATUALIZAÇÃO — RED 4.24 EXECUTADO / RESULTADO REAL

O usuário executou:

```text
red_v2_4_payload_volume_precedence_teste4_24.py
```

Resultado:

```text
🔴 EXIT 2 — RED V2.4 SUSTENTADO
```

## 14.1 Locks / autoridade do harness

Todos os locks passaram:

```text
HEAD ......................................... PASS
revisao_turno.py ............................. PASS
modalidade_turno.py .......................... PASS
normalizacao_linguagem.py .................... PASS
porteiro_acoes.py ............................ PASS
roteador_deterministico.py ................... PASS
orquestrador_deterministico.py ............... PASS
worktree causal .............................. PASS
```

HEAD continua:

```text
a4741bc57bc55a50ef2861dbaef09ab36397ff63
```

Portanto o RED foi executado exatamente sobre o estado estudado.

## 14.2 Controles do detector real

Todos passaram:

```text
abaixa o volume
→ VOLUME {'acao': 'down'}

aumenta o volume
→ VOLUME {'acao': 'up'}

pesquisa documentacao oficial do python
→ SEARCH

toca nao existe amor em sp
→ MUSIC_SEARCH {'query': 'nao existe amor em sp'}
```

Isso valida as premissas do detector usadas pelo harness.

## 14.3 Primeira fronteira causal comum aos 8 killers

Em TODOS os casos:

```text
revisão:
detectada=False
resolvida=False

modalidade:
comando
autoriza_execucao=True

analisar_protecao_operacional:
bloqueia_execucao=False

barreira prioritária:
False
```

Ou seja, a restrição interna já chegou autorizada ao roteador.

A primeira fronteira RED continua sendo a camada cognitiva de autoridade/proteção:

```text
modalidade_turno / proteção P0
```

O detector VOLUME é amplificador/consumidor downstream, não a raiz.

## 14.4 Killers materializados — 8/8

### Música

```text
toca nao abaixa o volume
→ VOLUME(down)

toca não aumenta o volume
→ VOLUME(up)

toca nao diminui o volume
→ VOLUME(down)
```

### SEARCH

```text
pesquisa nao abaixa o volume
→ VOLUME(down)

pesquisa gatos nao aumenta o volume
→ VOLUME(up)
```

### Arquivo / conteúdo

```text
escreve nao abaixa o volume no arquivo teste.txt
→ VOLUME(down)

cria arquivo teste.txt contendo nao aumenta o volume
→ VOLUME(up)
```

### Arquivo / nome

```text
abre o arquivo nao abaixa volume.txt
→ VOLUME(down)
```

Resumo:

```text
killers testados ............... 8
REDs materializados ............ 8
não materializados ............. 0
```

Todos os domínios reproduziram:

```text
MUSICA ................. RED
SEARCH .................. RED
ARQUIVO_CONTEUDO ........ RED
ARQUIVO_NOME ............ RED
```

## 14.5 Conclusão arquitetural agora sustentada

A hipótese deixou de ser apenas leitura de código.

Está provado, na integração real dos componentes testados, que:

```text
payload reconhecido cognitivamente/localmente
≠
payload protegido end-to-end
```

A informação de literalidade/payload não acompanha a fala até o roteador.

O consumidor downstream volta a enxergar texto plano e pode reinterpretar
conteúdo, query, título ou filename como outra operação.

Isso invalida como política de segurança do primeiro V2.4 qualquer regra do tipo:

```text
"está dentro de SEARCH/MUSIC/WRITE/FILENAME"
→ logo pode ignorar a negação
```

enquanto não existir tipagem end-to-end.

## 14.6 Caso mais forte conceitualmente: ARQUIVO_NOME

```text
abre o arquivo nao abaixa volume.txt
```

Mesmo sendo semanticamente um nome de arquivo, o caminho real testado produziu:

```text
modalidade auth=True
barreira=False
detector=VOLUME(down)
```

Isto demonstra que a semântica de filename foi perdida antes do detector.

Portanto, exceções de payload baseadas apenas no analisador cognitivo são insuficientes.

## 14.7 O que o RED NÃO provou

Não houve execução física do volume.

A autoridade correta da prova é:

```text
integração real entre componentes cognitivos/determinísticos
até a seleção de intent VOLUME
```

Não chamar de:

```text
E2E físico
volume realmente alterado no Windows
```

sem atravessar executor real/efeito físico.

## 14.8 Impacto sobre V2.4

O desenho conservador ganhou forte sustentação:

```text
historical auth=True
+
negação interna standalone no RAW
+
sem prova estrutural end-to-end
=
FAIL-CLOSED
```

Sem perguntar qual verbo vem depois.

Sem whitelist privada.

Sem depender de:

```text
MUSIC
SEARCH
WRITE
FILE
LLM
contexto
APPS_MAP
detector especialista
```

A política deve retirar autoridade ANTES do roteador:

```text
autoriza_execucao=False
acao_explicita=False
texto_operacional=""
```

`requer_esclarecimento=True` continua uma direção desejável de UX,
mas sua integração precisa ser provada separadamente.

## 14.9 Exceções mínimas ainda não fechadas

Não generalizar para simples substring `"nao"`.

Ainda é necessário distinguir átomos lexicais como:

```text
nao.txt
```

de marcador gramatical standalone.

Não liberar de forma ampla:

```text
nao-feche.txt
aspas
SEARCH payload
MUSIC title
WRITE content
```

até existir prova end-to-end.

## 14.10 Próximo passo legítimo após RED 4.24

Antes de patch de produção:

1. revisar integralmente o RED 4.24 — concluído nesta atualização;
2. congelar o contrato mínimo do candidato V2.4;
3. construir LAB V2.4 conservador, ainda sem alterar produção;
4. falsificar principalmente:
   - `nao.txt`;
   - negação inicial já bloqueada pelo histórico;
   - root STT original;
   - `toca/pesquisa/escreve/... nao abaixa o volume`;
   - acento/sem acento;
   - `nunca` / `jamais`;
   - comandos polidos;
   - cadeias multi-ato;
   - positivos sem negação;
   - root pontuado separado;
5. fazer segunda revisão integral do LAB;
6. só então discutir patch.

---

# 15. STATUS ATUAL APÓS RED 4.24

```text
produção ................................ INTACTA

RED 4.24
PAYLOAD→VOLUME .......................... 🔴 SUSTENTADO 8/8

primeira fronteira RED .................. modalidade/proteção de autoridade
detector VOLUME ......................... amplificador downstream

MUSICA .................................. 🔴 reproduziu
SEARCH .................................. 🔴 reproduziu
ARQUIVO_CONTEUDO ........................ 🔴 reproduziu
ARQUIVO_NOME ............................ 🔴 reproduziu

payload local = segurança end-to-end .... ❌ FALSIFICADO
taxonomia privada de verbos ............. ❌ REJEITADA
V2.4 conservador sem taxonomia .......... ✅ DIREÇÃO FORTEMENTE SUSTENTADA

patch de produção ....................... 🚫 BLOQUEADO
próximo passo ........................... LAB V2.4 CONSERVADOR
```


---

# 16. ATUALIZAÇÃO — LAB V2.4 CONSERVADOR CRIADO

Foi criado o candidato de LAB:

```text
falsificacao_candidato_turno229_negacao_stt_LAB_V2_4_CONSERVADOR.py
```

Produção permanece **ZERO ALTERAÇÕES**.

## 16.1 Princípio do candidato

O V2.4 não possui lista privada de verbos.

Ele só participa quando:

```text
baseline histórico autoriza execução = True
```

Então procura no RAW:

```text
nao
não
nunca
jamais
```

como marcador **interno e standalone**.

Se encontrar marcador interno sem exceção lexical end-to-end comprovada:

```text
autoriza_execucao=False
acao_explicita=False
texto_operacional=""
requer_esclarecimento=True
```

O candidato NÃO consulta:

```text
MUSIC
SEARCH
FILE
VOLUME
CLOSE_APP
APPS_MAP
LLM
contexto
catálogo musical
lista de verbos
```

para decidir polaridade.

## 16.2 Exceção lexical estreita

A única exceção inicial do LAB é:

```text
nao.txt
não.txt
```

e extensões fechadas equivalentes, somente quando aparecem em moldura explícita:

```text
arquivo ...
documento ...
```

Exemplos positivos:

```text
cria arquivo nao.txt
abre o arquivo nao.txt
cria arquivo nao.md
```

Não são liberados:

```text
nao-feche.txt
nao feche.txt
```

## 16.3 Mudança de autoridade dos antigos payloads

Após RED 4.24, estes casos NÃO são mais controles obrigatórios de passagem:

```text
toca nao existe amor em sp
pesquisa nao feche o opera
escreve nao feche o opera no arquivo
pesquisa "nao feche o opera"
```

No primeiro V2.4 eles devem falhar fechado, porque a literalidade local não sobrevive comprovadamente end-to-end.

## 16.4 Matriz do LAB

O LAB cobre:

```text
- root STT original
- inversões CLOSE_APP
- acento / sem acento
- RED 4.24 MUSIC/SEARCH/FILE → VOLUME
- títulos/query/conteúdo agora ambíguos
- nunca/jamais
- molduras polidas
- multi-ato / cadeia tripla
- precedência histórica
- nao.txt
- nao-feche.txt e nao feche.txt
- positivos
- root pontuado separado
```

Ele também exige que:

```text
fail-closed
=> barreira prioritária real=True
```

## 16.5 Validações antes da entrega

```text
py_compile ........ PASS
AST parse .......... PASS
microfalsificação .. PASS
```

A microfalsificação pura confirmou:

```text
cria arquivo nao.txt ................. NÃO bloqueia
abre o arquivo nao.txt ............... NÃO bloqueia
abre o arquivo nao-feche.txt ......... BLOQUEIA
abre o arquivo nao feche.txt ......... BLOQUEIA
fecha opera nao Store ................ BLOQUEIA
fecha opera não Store ................ BLOQUEIA
fecha opera nunca Store .............. BLOQUEIA
fecha opera jamais Store ............. BLOQUEIA
toca nao existe amor em sp ........... BLOQUEIA
pesquisa nao abaixa o volume ......... BLOQUEIA
nao fecha o opera .................... V2.4 NÃO toma crédito
```

## 16.6 Semântica de saída

```text
EXIT 0 = candidato sobreviveu a este LAB; NÃO é patch aprovado
EXIT 1 = harness/premissa/lock inconclusivo
EXIT 2 = candidato V2.4 falsificado
```

Mesmo EXIT 0 exige segunda revisão integral adversarial.

## 16.7 Próximo passo

Executar o LAB no HEAD travado e trazer o output completo.

A primeira revisão após a execução deve procurar principalmente:

```text
- alguma premissa histórica que mudou;
- algum caso "nao.txt" semanticamente corrompido mesmo com auth=True;
- alguma negação inicial da qual V2.4 roubou crédito;
- algum root pontuado reivindicado indevidamente;
- algum positivo bloqueado;
- qualquer GREEN causado apenas por assertion fraca.
```


---

# 17. ATUALIZAÇÃO — LAB V2.4 CONSERVADOR EXECUTADO / EXIT 0

O usuário executou:

```text
falsificacao_candidato_turno229_negacao_stt_LAB_V2_4_CONSERVADOR.py
```

Resultado:

```text
🟢 CANDIDATO V2.4 CONSERVADOR SOBREVIVEU AO LAB — EXIT 0
```

## 17.1 O GREEN é válido apenas para a matriz

Passaram:

```text
root STT
RED 4.24 payload→volume bloqueado pelo candidato
payloads reclassificados como ambíguos
nunca/jamais
molduras polidas
multi-ato
precedência histórica
átomo nao.txt
nao-feche / nao feche bloqueados
positivos
root pontuado separado
```

O diferencial lexical funcionou:

```text
cria arquivo nao.txt
→ preservado

abre arquivo nao.txt
→ preservado

abre arquivo nao-feche.txt
→ bloqueado

abre arquivo nao feche.txt
→ bloqueado
```

## 17.2 Sinais laterais no output

No contexto neutro do detector usado pelo LAB:

```text
abre o opera
→ MUSIC_SEARCH('opera')

abre o opera e fecha a microsoft store
→ MUSIC_SEARCH('opera e fecha a microsoft store')
```

Esses resultados não reprovaram o V2.4 porque a fase de positivos media
preservação da classificação/autoridade do candidato, não correção universal
do roteador neutro.

Não usar esses casos como prova de routing E2E correto.

---

# 18. SEGUNDA REVISÃO INTEGRAL DO GREEN V2.4

O EXIT 0 NÃO foi aceito como patch approval.

Foram encontrados dois possíveis GREENs mentirosos estruturais.

## 18.1 Inconsistência do contrato interno

O candidato local `aplicar_v24()` faz cópia do resultado histórico e atualiza:

```text
modalidade
modalidade_geral
ato_principal
acao_explicita
autoriza_execucao
texto_operacional
requer_esclarecimento
...
```

Mas NÃO reescreve explicitamente:

```text
atos
segmentos
texto_conversacional
```

A P0 real da Laylay, quando veta autoridade, reescreve de forma canônica:

```text
atos=[modalidade]
segmentos=[{
  modalidade=<safe>,
  autoriza_execucao=False,
  acao_explicita=False,
  ...
}]
texto_operacional=""
```

Portanto há forte risco de o resultado V2.4 ficar:

```text
top-level:
  recusa
  auth=False

segmentos históricos:
  comando
  auth=True
```

Isto é contrato contraditório e deve ser tratado como falha de implementação
mesmo que consumidores atuais usem preferencialmente o campo de topo.

## 18.2 Produtores de autoridade pós-modalidade

O orquestrador real não encerra a transformação do turno logo após
`classificar_modalidade_turno()`.

Depois da classificação ele ainda pode aplicar:

```text
retarget
elipse espacial
repetição operacional
pedido visual de jogo
```

A função real:

```text
aplicar_pedido_visual_ao_turno()
```

recria explicitamente:

```text
modalidade="comando"
atos=["comando"]
segmentos=[segmento autorizado]
autoriza_execucao=True
acao_explicita=True
```

Ela não verifica se a modalidade anterior havia feito fail-closed por
polaridade interna.

Logo existe uma possível cadeia:

```text
fala com negacao interna
    ↓
V2.4
auth=False
    ↓
modo jogo ativo
    ↓
detectar_pedido_visao_jogo()
    ↓
aplicar_pedido_visual_ao_turno()
    ↓
auth=True novamente
```

Isto invalida a ideia de considerar a simples alteração no classificador
como barreira soberana até o fim do turno.

---

# 19. TESTE 4.25 CRIADO — PÓS-GREEN / AUTORIDADE

Foi criado:

```text
falsificacao_pos_green_v2_4_contrato_reautorizacao_visual_teste4_25.py
```

Objetivo:

1. carregar por SHA o candidato EXATO que deu GREEN;
2. provar se o top-level fail-closed mantém `segmentos` históricos autorizados;
3. usar GAME_VISION real com contexto de jogo ativo;
4. provar/falsificar se GAME_VISION reautoriza o turno depois do veto V2.4.

Killers focados:

```text
olha minha tela nao fecha o opera
olha minha tela nao abaixa o volume
olha minha tela nunca fecha o opera
```

Controle:

```text
olha minha tela
→ precisa ser pedido GAME_VISION real
```

Semântica:

```text
EXIT 2
= GREEN V2.4 falsificado na segunda revisão

EXIT 0
= esses dois bypasses não reproduziram

EXIT 1
= premissa/lock/harness inválido
```

Este teste ainda NÃO é E2E físico de captura de tela.

---

# 20. STATUS APÓS A SEGUNDA REVISÃO DO EXIT 0

```text
produção ................................ INTACTA

LAB V2.4 conservador .................... 🟢 EXIT 0 NA MATRIZ

patch approval .......................... NÃO

política V2.4:
negação interna standalone -> fail-closed
......................................... ✅ CONTINUA PROMISSORA

implementação atual do candidato:
campos de topo apenas
......................................... ⚠️ SUSPEITA

consistência de segmentos ............... 🔴 SUSPEITA FORTE

reautorização pós-modalidade GAME_VISION
......................................... 🔴 SUSPEITA FORTE

próxima autoridade ...................... TESTE 4.25
```

Não criar patch de produção antes do resultado do teste 4.25.


---

# 21. ATUALIZAÇÃO — TESTE 4.25 EXECUTADO / GREEN V2.4 FALSIFICADO

O usuário executou:

```text
falsificacao_pos_green_v2_4_contrato_reautorizacao_visual_teste4_25.py
```

Resultado:

```text
🔴 EXIT 2 — GREEN V2.4 FALSIFICADO NA SEGUNDA REVISÃO
```

## 21.1 Guards

Todos passaram:

```text
HEAD ................................ PASS
modalidade_turno.py ................. PASS
intencao_visual_jogo.py ............. PASS
orquestrador_turno_runtime.py ....... PASS
porteiro_acoes.py ................... PASS
worktree causal ..................... PASS
candidate SHA ....................... PASS
```

O candidato executado era exatamente o LAB V2.4 conservador GREEN:

```text
8d880799ebce1440f4a4ed1b663589508e07d2dc5325d848b9b949161333ea8f
```

## 21.2 Falha A — contrato interno contraditório

Killers:

```text
olha minha tela nao fecha o opera
olha minha tela nao abaixa o volume
olha minha tela nunca fecha o opera
```

Em 3/3:

```text
top-level após V2.4:
modalidade=recusa
auth=False
texto_operacional=""

MAS

segmentos históricos:
modalidade=comando
autoriza_execucao=True
acao_explicita=True
```

Portanto o candidato não produzia um contrato canônico fail-closed.

A P0 real da Laylay, quando veta um ato de fala, reescreve também:

```text
atos
segmentos
texto_conversacional
```

O V2.4 local não fazia isso.

## 21.3 Relevância dos segmentos stale

A revisão de fonte mostrou que o planejador real usa `segmentos` para construir
os atos do plano e define `requer_execucao=True` se houver segmento comando.

Assim o candidato poderia produzir conceitualmente:

```text
turno.autoriza_execucao=False
plano.requer_execucao=True
atos=[comando, comando]
```

O filtro final ainda exige `turno.autoriza_execucao=True`, portanto os
segmentos stale sozinhos não provaram execução física. Porém são um defeito
real de contrato/planejamento e podem combinar-se com reautorizações posteriores.

## 21.4 Falha B — GAME_VISION reautoriza depois do veto

Em 3/3 killers:

```text
V2.4 antes da visão:
auth=False

aplicar_pedido_visual_ao_turno():
auth=True
modalidade=comando
segmentos=[comando autorizado]
```

Resultado:

```text
3/3 reautorizações
```

Logo a implementação "mudar auth=False dentro da modalidade" não é um veto
persistente.

## 21.5 Terceira descoberta no próprio output

Caso:

```text
olha minha tela nao abaixa o volume
```

Após V2.4 e ANTES do GAME_VISION:

```text
auth=False
barreira_prioritaria=False
```

Isto ocorre porque `bloqueia_execucao_operacional_prioritaria()` não trata
qualquer `auth=False` como veto universal. Quando a natureza do candidato não
pertence aos casos históricos reconhecidos e a taxonomia P0 não encontra o
gatilho, a função pode retornar False.

Portanto:

```text
auth=False momentâneo
!=
veto persistente reconhecido pelos gates
```

Esta descoberta é central para o V2.4.1.

---

# 22. DIREÇÃO V2.4.1 APÓS O 4.25

A política conservadora continua sustentada:

```text
negação interna standalone
+ turno operacional historicamente autorizável
+ ausência de literalidade end-to-end
= fail-closed
```

O que foi rejeitado:

```text
wrapper pós-classificação que altera só campos de topo
```

Direção preferida agora:

```text
integrar a regra à proteção P0 canônica
```

Motivos:

1. `classificar_modalidade_turno()` já sabe aplicar uma proteção P0 e
   reescrever canonicamente o contrato inteiro;
2. `bloqueia_execucao_operacional_prioritaria()` reconsulta a proteção P0
   diretamente sobre o texto RAW antes de confiar na classificação recebida;
3. isso permite que um produtor posterior de autoridade seja vetado novamente
   pelo gate quando o RAW continuar contendo a restrição.

Ainda NÃO é patch aprovado. Há rotas paralelas de governança a investigar.

---

# 23. NOVA ROTA PARALELA ENCONTRADA — COOPERAÇÃO GAME_VISION

Na orquestração cooperativa existe rota real:

```text
OrquestradorCooperativoRuntime.processar(texto)
    ↓
detectar_visao_jogo(texto)
    ↓
GAME_VISION tipo=avaliacao_item
    ↓
_processar_analise_item_jogo()
    ↓
GovernancaPlanoCooperativoRuntime.avaliar_autorizacao(
    ..., {"texto": texto, "confirmado": True}
)
    ↓
autorizar_acao_pratica(
    GAME_VISION,
    texto,
    confirmado=True,
    origem="orquestracao_cooperativa"
)
```

O `autorizar_acao_pratica()` atual possui precedência:

```text
if confirmado:
    permitido=True
```

antes das demais regras.

Depois da autorização, o orquestrador chama:

```text
executar_intencao({"intent": "GAME_VISION", ...}, texto)
```

Assim existe hipótese de bypass independente da barreira de comandos imediatos.

---

# 24. RED 4.26 CRIADO — COOPERAÇÃO / CONFIRMADO BYPASS

Arquivo:

```text
red_v2_4_cooperacao_confirmado_bypass_teste4_26.py
```

Objetivo:

provar/falsificar a rota cooperativa real sem captura física.

O teste atravessa:

```text
detectar_pedido_visao_jogo
→ OrquestradorCooperativoRuntime.processar
→ GovernancaPlanoCooperativoRuntime.avaliar_autorizacao
→ autorizar_acao_pratica real
→ recorder de executar_intencao
```

O recorder não executa visão nem efeito externo. Ele apenas prova que o despacho
foi autorizado e chegou ao ponto em que o executor real seria chamado.

Killers:

```text
olha esse item nao fecha o opera
olha esse item nao abaixa o volume
olha esse item nunca fecha o opera
```

Premissa obrigatória:

```text
cada frase deve ser reconhecida pelo detector visual real como:
GAME_VISION / avaliacao_item
```

Fases:

```text
1. detector visual real
2. porteiro central real com confirmado=True
3. governança cooperativa real
4. orquestrador cooperativo real com recorder
```

Semântica:

```text
EXIT 2 = bypass cooperativo sustentado
EXIT 0 = hipótese falsificada
EXIT 1 = premissa/lock inválido
```

---

# 25. STATUS ATUAL

```text
produção ................................ INTACTA

RED 4.24 payload→volume ................. 🔴 SUSTENTADO 8/8

LAB V2.4 conservador .................... 🟢 EXIT 0 NA MATRIZ

SEGUNDA REVISÃO / TESTE 4.25 ............ 🔴 EXIT 2

falha contrato interno .................. 🔴 3/3
reautorização GAME_VISION ............... 🔴 3/3
auth=False != veto persistente .......... 🔴 PROVADO

política conservadora V2.4 .............. ✅ SOBREVIVE
implementação wrapper pós-classificação . ❌ REJEITADA

direção V2.4.1:
regra dentro da P0 canônica ............. ✅ PREFERIDA, AINDA NÃO APROVADA

rota cooperativa confirmado=True ........ ⚠️ HIPÓTESE FORTE
próxima autoridade ...................... RED 4.26

patch produção .......................... 🚫 BLOQUEADO
```


---

# 26. CORREÇÃO FORMAL — TESTE 4.26 V1 NÃO EXECUTOU A HIPÓTESE

O usuário executou:

```text
red_v2_4_cooperacao_confirmado_bypass_teste4_26.py
```

Resultado:

```text
🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA
```

O HEAD estava correto e a worktree causal estava limpa. O erro era do próprio
harness: três SHA de blob tinham sido gravados incorretamente.

Valores AUTORITATIVOS confirmados pelo `git rev-parse HEAD:<arquivo>` local e
pelo tree do GitHub no commit travado `a4741bc...`:

```text
mente_laylay/autonomia/orquestracao_cooperativa.py
4150f749a9a0e1ec286fb600d95f33d057b356e0

mente_laylay/autonomia/governanca_cooperacao.py
97fb1d1b5cf14d347e031062a4752c0915aa4188

mente_laylay/autonomia/quadro_cooperacao.py
3ba4f6a51c42138c794f8dbe4d594e5abf5b55e8
```

Conclusão soberana:

```text
4.26 V1 = INVALIDADO PELO GUARD
não é RED
não é GREEN
não diz nada causal sobre a Laylay
```

Não corrigir apenas os três hashes: a revisão de fonte posterior mostrou que a
hipótese do V1 também estava causalmente estreita.

---

# 27. SEGUNDA REVISÃO DO 4.26 — `confirmado=True` NÃO É A PRIMEIRA FRONTEIRA

O porteiro central atual possui:

```text
if confirmado:
    permitido=True
```

porém `GAME_VISION` também fica fora das categorias sensíveis específicas e,
ao final, pode receber o default:

```text
permitido=True
motivo="acao fora do escopo sensivel atual"
```

Logo:

```text
confirmado=True
```

não é necessário para explicar a autorização de `GAME_VISION`.

Mais importante: `GAME_VISION` é oficialmente uma intent SOMENTE LEITURA.

Portanto:

```text
autorizar visão
!=
autorizar CLOSE_APP/VOLUME mencionados negativamente na mesma fala
```

O 4.25 continua autoritativo para:

```text
- contrato interno inconsistente;
- reautorização do topo por aplicar_pedido_visual_ao_turno().
```

Mas o 4.25 NÃO prova sozinho:

```text
- reachability da ação negada;
- CLOSE_APP/VOLUME físicos;
- bypass causal até executor mutante.
```

Nova regra metodológica:

```text
defeito de contrato != alcance do efeito proibido
```

---

# 28. ORDEM REAL ESTUDADA — VISÃO, CADEIA E DETERMINÍSTICO

## 28.1 Ciclo principal

`RespostaIARuntime` usa o turno já criado e chama a fase de comandos
prioritários antes da conversa/LLM.

## 28.2 Fase prioritária

A ordem relevante em `ComandosImediatosRuntime` é:

```text
barreira P0
↓
...
processar_comandos_em_cadeia()
↓
...
orquestrador_cooperativo.processar()
↓
...
detector determinístico
↓
...
resolver_comando_natural()
```

Portanto a cooperação visual não pode ser assumida como primeira fronteira sem
verificar a cadeia anterior.

## 28.3 Cadeia não corta `olha ... nao fecha ...`

`segmentar_comandos_em_cadeia()` só cria fronteira quando esquerda e direita
começam como etapas operacionais conhecidas.

A lista operacional inclui `fecha`, `abaixa`, etc., mas não `olha`.

Assim:

```text
olha minha tela nao fecha o opera
olha minha tela nao abaixa o volume
```

não devem virar automaticamente:

```text
[olha minha tela nao] + [fecha/abaixa ...]
```

na cadeia multi-etapas.

Isto falsifica a hipótese de que a cadeia execute B antes da visão.

---

# 29. DIFERENÇA CRÍTICA — AVALIAÇÃO DE ITEM VS OBSERVAÇÃO

`OrquestradorCooperativoRuntime.processar()` intercepta apenas:

```text
GAME_VISION
tipo=avaliacao_item
```

Então:

```text
olha esse item ...
```

pode ser consumido pela cooperação.

Já:

```text
olha minha tela ...
```

é normalmente:

```text
GAME_VISION
tipo=observacao
```

e não é consumido por essa porta cooperativa específica.

Logo o caso do 4.25 precisa continuar até o roteamento determinístico/natural.

---

# 30. PRECEDÊNCIA DETERMINÍSTICA VISUAL

No `detectar_intencao_deterministica_mente()` real:

```text
contexto de jogo
↓
detectar_pedido_visao_jogo(texto, contexto)
↓
se houver pedido:
    return GAME_VISION IMEDIATAMENTE
```

Essa chamada ocorre antes das portas de mídia/volume e antes do detector de
fechamento.

Além disso, na lista geral posterior:

```text
detectar_url_visual()
```

vem antes de:

```text
detectar_fechar_alvo()
```

e `detectar_url_visual()` reconhece frases como:

```text
olha minha tela
olha a tela
ver minha tela
```

como `SCREEN_CAPTURE`.

Isto cria uma forte hipótese de isolamento semelhante ao antigo
SEARCH→CLOSE:

```text
detector inferior consegue enxergar CLOSE
!=
CLOSE é alcançável na rota real
```

---

# 31. NUANCE NOVA — JOGO INATIVO / DEGRADADO

A precedência não é idêntica fora do jogo.

Antes da lista geral existe uma porta antecipada:

```text
detectar_volume_ou_midia()
```

Assim uma frase como:

```text
olha minha tela nao abaixa o volume
```

com jogo inativo/degradado pode potencialmente produzir `VOLUME` antes de
`SCREEN_CAPTURE`.

Isto ainda não é RED por si só.

Para receber crédito causal, `VOLUME` precisa sobreviver:

```text
detector
→ turno
→ árbitro
```

CLOSE/VOLUME lexical isolado não recebe crédito.

---

# 32. TESTE 4.26 REV2 — ISOLAMENTO VISUAL × AÇÃO NEGADA

Novo arquivo:

```text
falsificacao_isolamento_visual_negacao_operacional_teste4_26_REV2.py
```

SHA-256:

```text
830954f5cc74355db7bad7426cf8ecbb9f6b9e1da4f7ea38285442a9a0ea7996
```

Validação estática:

```text
py_compile PASS
AST PASS
```

Objetivo:

```text
provar/falsificar se B negado realmente vence
detector + coordenador + árbitro
```

Matriz principal:

```text
olha minha tela nao fecha o opera
olha minha tela nao abaixa o volume
olha minha tela nunca fecha o opera
olha esse item nao fecha o opera
olha esse item nao abaixa o volume
```

Contextos:

```text
JOGO_ATIVO
JOGO_INATIVO
```

Definição semântica:

```text
A positivo:
GAME_VISION / SCREEN_CAPTURE / VISION_QUERY

B proibido:
CLOSE_APP / VOLUME
```

Fases:

```text
0. catálogo oficial de capabilities;
1. modalidade base + segmentador de cadeia;
2. detectores inferiores isolados — diagnóstico SEM crédito;
3. orquestrador determinístico real instrumentado;
4. resolver_intencao + arbitro_turno reais;
5. controles positivos:
   fecha o opera -> CLOSE_APP
   abaixa o volume -> VOLUME
```

O harness instrumenta apenas os detectores para registrar a ORDEM de chamadas.
Os detectores originais continuam sendo executados e são restaurados no final.

Nenhum executor físico é chamado.

EXIT:

```text
2 = CLOSE_APP/VOLUME negado venceu detector + árbitro em alguma rota
0 = isolamento visual sustentado na matriz
1 = guard/premissa/harness inválido
```

Apenas EXIT 2 autoriza dizer que o B negado ganhou reachability cognitiva na
rota testada.

Mesmo EXIT 2 ainda NÃO é E2E físico.

---

# 33. STATUS APÓS CORREÇÃO DO 4.26

```text
produção ................................ INTACTA

4.25 contrato interno ................... 🔴 PROVADO
4.25 visual reautoriza topo ............. 🔴 PROVADO

4.26 V1 ................................. 🟠 INVÁLIDO / HARNESS BUG
hipótese confirmado=True ................ ❌ NÃO É PRIMEIRA FRONTEIRA

cadeia olha→fecha ....................... 🟢 NÃO SEGMENTA PELO CONTRATO ATUAL
visual-first com jogo ativo ............. ✅ FORTE HIPÓTESE DE ISOLAMENTO
volume-first sem jogo ................... ⚠️ SUPERFÍCIE A FALSIFICAR

reachability real de B .................. ⏳ TESTE 4.26 REV2
política conservadora ................... ✅ AINDA VIVA
wrapper V2.4 pós-classificação .......... ❌ REJEITADO
V2.4.1/P0 ............................... ⏸️ NÃO DESENHAR AINDA

patch produção .......................... 🚫 BLOQUEADO
```

Próxima autoridade:

```text
resultado local do TESTE 4.26 REV2
```


---

# 34. AUDITORIA DE PRODUTORES DE AUTORIDADE PÓS-CLASSIFICAÇÃO

Data da auditoria: 20/08/2026.

Escopo: localizar caminhos que, depois de `classificar_modalidade_turno()`, ainda podem criar ou restaurar capacidade de execução sem depender estritamente de `turno_atual.autoriza_execucao`.

## 34.1 Produtores pós-classificação identificados

### A. `aplicar_repeticao_operacional_ao_turno()`

Pode colocar:

```text
autoriza_execucao=True
acao_explicita=True
modalidade=comando
```

mas só quando `resolver_repeticao_ultima_acao()` devolve um contrato reexecutável. O resolvedor exige forma curta por `fullmatch` como `de novo`, `tenta de novo`, etc.; frases contaminadas do root 229 não entram nessa forma. Para o root atual, não é o primeiro RED.

### B. `aplicar_elipse_espacial_autorizada_ao_turno()`

Também pode conceder autoridade depois da classificação, mas apenas para as formas exatas `esquerda` / `direita`, com alvo ainda dependente de contexto tipado. Não é causal para o root 229.

### C. `aplicar_pedido_visual_ao_turno()`

É produtor real de autoridade pós-classificação:

```text
modalidade=comando
autoriza_execucao=True
acao_explicita=True
texto_operacional=<pergunta visual>
```

Ele é chamado no `orquestrador_turno_runtime.py` depois da classificação base. Portanto, se a classificação futura V2.4 fizer fail-closed por negação interna e o detector visual ainda reconhecer o mesmo texto, a visão pode reautorizar o topo do turno. Isto confirma que um patch apenas em `modalidade_turno.py` não basta sem preservar a decisão fail-closed contra reautorizadores posteriores.

### D. `consolidar_arbitragem()`

Pode marcar `contrato_decisao.permite_acao=True` quando há vencedor, mas o árbitro, para intents mutantes normais, já exige que o turno tenha autorizado. Não é a primeira quebra do root 229. Continua relevante como sink de contrato, não como origem primária da permissão neste caso.

### E. filtros de comandos da LLM

`filtrar_comandos_pelo_turno()` exige simultaneamente:

```text
turno.autoriza_execucao
plano.requer_execucao
contrato.permite_acao
```

Logo não cria autoridade a partir de conversa/recusa. Seguro para o root atual.

## 34.2 RED arquitetural novo: governança cooperativa

A auditoria encontrou uma superfície mais séria que o visual wrapper isolado.

Caminho real:

```text
OrquestradorCooperativoRuntime.processar(texto)
  -> detectar_visao_jogo(texto)
  -> _processar_analise_item_jogo(...)
  -> cria plano com autorizacao="explicita_no_pedido"
  -> governanca.avaliar_autorizacao(..., {"texto": texto, "confirmado": True})
  -> PorteiroAcoesRuntime.autorizar_acao_pratica(..., confirmado=True)
  -> autorizar_acao_pratica():
         if confirmado:
             return permitido=True
```

Ponto crítico:

```python
if confirmado:
    return {"permitido": True, "motivo": "confirmacao explicita", ...}
```

A governança cooperativa está fabricando `confirmado=True` internamente em alguns fluxos, em vez de derivá-lo de `turno_atual.autoriza_execucao` ou de uma confirmação canônica do usuário.

Isso significa:

```text
classificador pode negar autoridade
        ↓
cooperacao detecta fluxo próprio
        ↓
plano declara "explicita_no_pedido"
        ↓
confirmado=True interno
        ↓
porteiro geral libera
```

Este é um produtor de autoridade pós-classificação de verdade.

## 34.3 Superfícies cooperativas afetadas

### `analise_item_jogo`

Usa `confirmado=True` ao avaliar autorização e depois chama `executar_intencao(GAME_VISION, ...)`.

### `organizacao_desktop_inteligente`

O executor cooperativo recebe `contexto_execucao={"texto": texto, "confirmado": True}`. Assim a governança também pode tratar o pedido como confirmado por construção.

### `caixa_para_agenda`

Também executa plano cooperativo com `confirmado=True`. Aqui há mais contexto estruturado de composição, mas a origem da confirmação ainda é interna e precisa ser diferenciada de confirmação real do usuário.

### `clipboard_pesquisa_llm`

Usa `confirmado=True` para um fluxo de investigação read-only. Menor risco de mutação, mas mostra o mesmo padrão arquitetural.

### `clipboard_para_arquivo`

Quando não há sobrescrita, a etapa `CREATE_FILE` pode cair no porteiro geral, que por padrão retorna `permitido=True` para ações fora do escopo musical sensível. Portanto a governança cooperativa não está ancorada no contrato de turno mesmo quando `confirmado=False`.

## 34.4 Consequência para V2.4

O princípio conservador continua válido, mas a implementação precisa de uma propriedade pós-classificação que sobreviva ao turno inteiro.

Não basta:

```text
modalidade_turno -> autoriza_execucao=False
```

É necessário impedir qualquer produtor posterior de transformar esse turno em autorizado.

Contrato sugerido para estudo:

```text
turno.fail_closed_operacional = True
```

ou equivalente tipado, com regra:

```text
se fail_closed_operacional=True:
    nenhum produtor pós-classificação pode elevar autoridade
    nenhuma governança cooperativa pode sintetizar confirmação
    apenas uma NOVA fala futura pode criar nova autoridade
```

Ainda não desenhar patch definitivo sem falsificar os produtores.

## 34.5 Produtores que hoje respeitam a negativa

- `bloqueia_execucao_operacional_prioritaria()` é fail-closed.
- `processar_comando_deterministico_precoce()` recusa quando `turno.autoriza_execucao=False`.
- `executar_comando_local_rapido()` recusa quando `turno.autoriza_execucao=False`.
- `filtrar_comandos_pelo_turno()` recusa comandos da LLM quando o turno não autorizou.
- especialista operacional herda `turno.autoriza_execucao` e não cria permissão sozinho.

## 34.6 Superfícies que exigem falsificação focada antes do patch

1. `aplicar_pedido_visual_ao_turno()` após fail-closed V2.4.
2. `OrquestradorCooperativoRuntime._processar_analise_item_jogo()` com texto que contém negação operacional interna.
3. `organizacao_desktop_inteligente` em turno fail-closed.
4. `caixa_para_agenda` para confirmar se `confirmado=True` é sempre derivado de uma confirmação do usuário ou pode ser sintetizado.
5. qualquer caminho que chame `PorteiroAcoesRuntime.autorizar_acao_pratica(..., confirmado=True)` sem prova canônica de confirmação do turno.

## 34.7 Status soberano após esta auditoria

```text
produção ................................ INTACTA
root STT 229 ............................. PROVADO em modalidade/polaridade
V2.4 conservador ........................ CONCEITO VIVO
patch só em modalidade .................. INSUFICIENTE
visual pós-classificação ................ PRODUTOR REAL DE AUTORIDADE
cooperação confirmado=True .............. RED ARQUITETURAL ENCONTRADO POR CÓDIGO
contrato de autoridade monotônica ........ NECESSÁRIO ESTUDAR/FALSIFICAR
patch produção ........................... BLOQUEADO
```

Próximo passo correto: falsificação focada dos produtores pós-classificação, com prioridade para a governança cooperativa e o `confirmado=True` sintético.


---

# 35. TESTE 4.26 REV2 EXECUTADO — RESULTADO AUTORITATIVO

Arquivo executado:

```text
red_v2_4_cooperacao_reautorizacao_independente_confirmacao_teste4_26_REV2.py
```

SHA-256 do harness:

```text
1cadb9db80750752f7efa6a31b682ce28be238a2bfda3f75763f32c880efaffc
```

Resultado local do usuário:

```text
EXIT 2
```

Todos os locks e wiring passaram.

Achados principais:

```text
porteiro permite sem confirmação ....... 3/3
porteiro permite com confirmação ....... 3/3
governança permite sem confirmação ...... 3/3
governança permite com confirmação ...... 3/3
orquestrador despachou GAME_VISION ...... 3/3
orquestrador passou confirmado=True ..... 3/3
```

Conclusão causal correta:

- `confirmado=True` existe no caminho cooperativo;
- porém NÃO é causa necessária da liberação de `GAME_VISION` neste HEAD;
- `autorizar_acao_pratica()` já permite `GAME_VISION` com `confirmado=False` como `acao fora do escopo sensivel atual`;
- portanto a superfície cooperativa é permissiva independentemente da confirmação.

Classificação de autoridade da prova:

```text
integração real de componentes + wiring real travado
!= E2E físico
```

Nenhum efeito físico foi executado; o sink foi substituído por recorder.

Observação de consistência do handoff:

Qualquer seção anterior que chamava outro arquivo de "4.26 REV2" fica
SUPERADA por esta seção. O resultado autoritativo mais recente de 4.26 é o
arquivo acima com EXIT 2.

---

# 36. FALSIFICAÇÃO 4.27 — MONOTONICIDADE PÓS-CLASSIFICAÇÃO

Novo arquivo:

```text
falsificacao_monotonicidade_autoridade_pos_classificacao_teste4_27.py
```

SHA-256:

```text
bd2ec3e929d50e2a7e1715dc7bca14216d10100ed0f1b40d7b675650b4b0ff95
```

Validação estática:

```text
py_compile PASS
AST PASS
```

Objetivo:

> falsificar a hipótese de que basta fazer o V2.4 fail-close em
> `modalidade_turno.py` sem um veto monotônico que sobreviva às camadas
> posteriores.

O teste separa três superfícies:

## 36.1 Controle neutro visual

```text
olha esse item
```

O classificador genérico pode vir sem autoridade, e a especialização visual
PODE legitimamente elevá-la. Este controle existe para provar que simplesmente
congelar todo `False` seria regressão.

## 36.2 Veto P0 real já existente

```text
olha esse item e nao fecha o opera
olha esse item e nunca fecha o opera
```

A P0 atual deve produzir:

```text
modalidade=recusa
autoriza_execucao=False
natureza_acao=cancelamento
```

Depois o teste aplica o produtor visual real e mede se o topo volta para
`autoriza_execucao=True`.

Importante: a barreira prioritária reanalisa o RAW e pode recompor esse P0
histórico. Portanto reautorização do topo não recebe crédito de reachability
física por si só.

## 36.3 Intervenção V2.4 bare/STT

Texto:

```text
olha esse item nao fecha o opera
```

Como a P0 histórica não cobre o boundary bare sem `e/mas/pontuação`, o harness
injeta SOMENTE a saída que qualquer V2.4 conservador teria de produzir:

```text
autoriza_execucao=False
acao_explicita=False
texto_operacional=""
natureza_acao=cancelamento
```

Isso é uma intervenção causal, não um candidato de produção.

Depois atravessa, na ordem real:

```text
repetição
-> elipse espacial
-> detector visual
-> aplicar_pedido_visual_ao_turno
-> barreira prioritária
-> orquestrador cooperativo
-> recorder GAME_VISION
```

Controles de segurança adicionais:

- `resolver_repeticao_ultima_acao()` deve devolver `None` para o bare killer;
- elipse espacial não deve reautorizar texto não espacial;
- árbitro real deve respeitar o veto direto;
- `filtrar_comandos_pelo_turno()` deve respeitar o veto direto;
- pré-fluxo determinístico deve respeitar o veto direto;
- detector visual no ROOT original `fecha o opera nao a microsoft store` deve
  ser `None`, provando que o teste não mistura a rota CLOSE original com GAME_VISION.

EXIT:

```text
2 = patch só na modalidade falsificado:
    intervenção fail-closed -> visão reautoriza -> barreira bare não recompõe
    -> cooperação alcança GAME_VISION no recorder

0 = cadeia de reautorização não reproduzida
1 = lock/wiring/controle/premissa inválida
```

Produção continua intacta.

Próxima autoridade:

```text
resultado local do teste 4.27
```


---

# 37. TESTE 4.27 EXECUTADO — MONOTONICIDADE PÓS-CLASSIFICAÇÃO

Arquivo executado:

```text
falsificacao_monotonicidade_autoridade_pos_classificacao_teste4_27.py
```

SHA-256 do harness:

```text
bd2ec3e929d50e2a7e1715dc7bca14216d10100ed0f1b40d7b675650b4b0ff95
```

Resultado local do usuário:

```text
EXIT 2
```

Todos os locks, worktree causal e wiring pós-classificação passaram.

## 37.1 Controles iniciais

Controle visual neutro:

```text
olha esse item
```

Classificação base:

```text
modalidade=conversa
autoriza_execucao=False
```

Depois da especialização visual:

```text
modalidade=comando
autoriza_execucao=True
natureza=consulta_visual
```

Isto prova que `False` neutro pode legitimamente subir para `True`; portanto a
solução final não pode simplesmente congelar qualquer `autoriza_execucao=False`.

P0 real:

```text
olha esse item e nao fecha o opera
olha esse item e nunca fecha o opera
```

ambos produziram:

```text
modalidade=recusa
autoriza_execucao=False
natureza=cancelamento
```

Root original sem pontuação:

```text
fecha o opera nao a microsoft store
```

permaneceu:

```text
modalidade=comando
autoriza_execucao=True
texto_operacional='fecha o opera nao a microsoft store'
```

O detector visual retornou `None` para esse root, confirmando que o 4.27 não
misturou a rota CLOSE original com GAME_VISION.

## 37.2 Produtores anteriores à visão

No killer bare:

```text
olha esse item nao fecha o opera
```

após intervenção fail-closed V2.4:

```text
autoriza_execucao=False
acao_explicita=False
texto_operacional=''
```

Resultados:

```text
resolver_repeticao_ultima_acao -> None
aplicar_repeticao_operacional_ao_turno -> auth=False
aplicar_elipse_espacial_autorizada_ao_turno -> auth=False
```

Logo repetição e elipse foram falsificadas como FIRST reauth neste cenário.

## 37.3 FIRST REAUTH pós-veto

O detector visual real reconheceu os três casos:

```text
olha esse item
olha esse item e nao fecha o opera
olha esse item nao fecha o opera
```

como:

```text
GAME_VISION / avaliacao_item
```

`aplicar_pedido_visual_ao_turno()` fez:

```text
P0 real: auth=False -> auth=True
V2.4 bare: auth=False -> auth=True
```

Portanto:

```text
FIRST REAUTH REACHABLE no cenário bare/V2.4
= aplicar_pedido_visual_ao_turno()
```

## 37.4 Barreira prioritária

Depois da reautorização visual:

```text
P0 real   -> bloqueia=True
V2.4 bare -> bloqueia=False
```

Interpretação:

- a barreira histórica consegue recompor o P0 real porque relê o RAW e conhece
  `e nao + verbo`;
- ela NÃO conhece o novo boundary bare/STT;
- se a visão apagou o veto bare, a barreira aceita a autoridade congelada e não
  consegue reconstruir a restrição.

## 37.5 Consumidores que respeitam veto direto

Com o veto V2.4 ainda intacto, os seguintes consumidores bloquearam corretamente:

```text
arbitro_turno ................ decisao=None
filtrar_comandos_pelo_turno .. comandos=[]
pre-fluxo determinístico ..... não chamou detector/executor
```

Isto é evidência forte de que esses componentes não precisam ser tratados como
fontes primárias do bug. Eles falham somente depois que um produtor anterior
apagou o veto.

## 37.6 Reachability cooperativa

No killer bare após a reautorização visual:

```text
barreira bare bloqueia? ........ False
coop processar .................. True
auth_trace confirmado ........... [True]
GAME_VISION alcançou recorder ... True
```

Nenhum efeito físico foi executado.

Conclusão do teste:

```text
🔴 EXIT 2 — HIPÓTESE 'PATCH SÓ NA MODALIDADE' FALSIFICADA
```

## 37.7 Diagnóstico arquitetural consolidado

A cadeia causal validada agora é:

```text
ROOT STT bare
  -> modalidade não representa restrição interna
  -> V2.4 conceitual conseguiria fail-close localmente
  -> repetição NÃO reautoriza
  -> elipse NÃO reautoriza
  -> aplicar_pedido_visual_ao_turno REAUTORIZA
  -> barreira histórica bare não recompõe veto
  -> cooperação alcança GAME_VISION
  -> governança/porteiro permitem a rota
```

Isso não muda o FIRST RED original do turno 229:

```text
ROOT original STT -> modalidade/polaridade
```

Mas fecha a pergunta de arquitetura do candidato:

```text
um fail-closed local em modalidade_turno.py é insuficiente
```

A solução final precisa distinguir:

```text
SEM_AUTORIZACAO / NEUTRO
```

de:

```text
VETO_OPERACIONAL_SOBERANO
```

E o veto precisa ser monotônico pelo restante do mesmo turno:

```text
NEUTRO -> AUTORIZADO     permitido por especialização legítima
AUTORIZADO -> VETADO     permitido por proteção posterior
VETADO -> AUTORIZADO     proibido no mesmo turno
```

## 37.8 Status soberano após 4.27

```text
produção ................................ INTACTA
root STT 229 ............................. PROVADO
P0 real .................................. funciona no boundary conhecido
V2.4 política conservadora ............... VIVA
patch só em modalidade .................. FALSIFICADO
repetição como FIRST reauth .............. FALSIFICADA
elipse como FIRST reauth ................. FALSIFICADA
aplicar_pedido_visual_ao_turno .......... FIRST REAUTH PROVADA
barreira histórica em P0 real ............ SALVA
barreira histórica em bare/STT ........... NÃO SALVA
árbitro com veto intacto ................. SEGURO NO CASO TESTADO
filtro LLM com veto intacto .............. SEGURO NO CASO TESTADO
pré-fluxo determinístico com veto ........ SEGURO NO CASO TESTADO
cooperação após reauth ................... REACHABLE / RED
veto monotônico de turno ................. NECESSIDADE ARQUITETURAL SUSTENTADA
patch produção ........................... AINDA BLOQUEADO ATÉ DESENHO FINAL
```

Próximo passo correto: estudo do menor contrato de veto monotônico que possa
ser propagado pelo turno e respeitado pelos produtores pós-classificação sem
quebrar a elevação legítima `NEUTRO -> AUTORIZADO` do controle visual positivo.


---

# 38. ESTUDO DO MENOR CONTRATO DE VETO MONOTÔNICO — SEM PATCH

Data: 20/08/2026.

Objetivo desta etapa: estudar onde o veto deve nascer, sobreviver e ser
consumido sem quebrar elevações legítimas de autoridade. Nenhum arquivo de
produção foi alterado e nenhum candidato foi criado nesta etapa.

## 38.1 O booleano atual não distingue duas situações semanticamente diferentes

Hoje `autoriza_execucao=False` representa ao menos:

```text
NEUTRO
  nenhuma especialização autorizou ainda

PROTEGIDO/VETADO
  uma regra de segurança já determinou que a fala atual não pode executar
```

Controles existentes provam que `NEUTRO -> AUTORIZADO` é necessário:

- visão: `olha esse item` pode partir de conversa/auth=False e virar
  `GAME_VISION` auth=True;
- repetição: `tenta de novo` pode partir de conversa/auth=False e recuperar
  uma ação reexecutável real.

Logo congelar todo `False` seria regressão.

## 38.2 `contratos_turno.py` é o ponto de contrato mais limpo

O módulo já existe para normalizar fronteiras de turno sem migração ampla,
usa apenas tipos/dados e preserva campos extras. É apropriado para um helper
puro de autoridade, sem importar modalidade, detector ou executor e sem criar
ciclo.

Direção estudada:

```text
veto_execucao_operacional: bool   # opcional no turno
```

com estado derivado, sem persistir enum redundante:

```text
veto=True                    -> VETADO
veto=False + auth=True       -> AUTORIZADO
veto=False + auth=False      -> NEUTRO
```

Possíveis helpers puros:

```text
turno_tem_veto_execucao(turno)
turno_autoriza_execucao(turno) = auth and not veto
estado_autoridade_turno(turno)  # apenas diagnóstico/teste
```

Isto é preferível a armazenar simultaneamente enum + booleano, que poderiam
divergir.

## 38.3 O veto deve ser sticky, mas só nascer de uma proteção real

Não deve nascer de qualquer `auth=False`.

Fontes candidatas legítimas do veto no escopo atual:

1. proteção P0 do ato de fala (`_protecao_p0_ato_fala`) quando ela determina
   explicitamente que o turno não autoriza execução;
2. futura proteção conservadora V2.4 para negação interna bare/STT;
3. revisão intra-turno ambígua ou cancelada, que já é fail-closed antes dos
   produtores positivos.

A inclusão da P0 histórica evita manter a inconsistência provada no 4.27 em
que uma recusa P0 é temporariamente reescrita como comando visual e só depois
salva por redundância da barreira.

## 38.4 Propagação é barata porque os produtores atuais copiam o turno

Os produtores pós-classificação estudados usam `dict(turno)` antes de atualizar:

- retarget;
- elipse espacial;
- repetição;
- visão;
- adaptação semântica conversacional;
- reconciliadores de referência.

Portanto um campo extra de veto sobreviveria automaticamente, desde que nenhum
produtor o remova explicitamente.

## 38.5 O melhor comportamento dos produtores positivos é não apagar o veto

Apenas marcar o bit e esperar uma barreira tardia não é suficiente porque o
planejamento é criado DEPOIS desses produtores. Se visão transformar um turno
vetado em `comando/auth=True`, o plano nasce executável e o contrato fica
semanticamente corrompido mesmo que uma barreira posterior consiga impedir um
executor específico.

Assim, para monotonicidade de contrato, produtores que elevam autoridade devem
preservar um turno vetado sem reclassificá-lo.

Produtores positivos atualmente identificados antes do plano:

```text
aplicar_elipse_espacial_autorizada_ao_turno
aplicar_repeticao_operacional_ao_turno
aplicar_pedido_visual_ao_turno
```

O 4.27 falsificou repetição e elipse como FIRST REAUTH para o killer estudado,
mas ambos pertencem à mesma classe arquitetural e são controles positivos
importantes. O guard do veto precisa preservar:

```text
NEUTRO -> AUTORIZADO       permitido
VETADO -> AUTORIZADO       proibido no mesmo turno
```

## 38.6 Não colocar um veto global no executor canônico

`CicloComandosRuntime.executar_intencao()` é compartilhado por vários serviços,
inclusive agenda, área de transferência, painel, cooperação e outras rotas que
podem existir fora da propriedade do turno conversacional atual.

O próprio cache de execução já possui lógica especial para não fazer serviços
background herdarem a identidade de uma conversa encerrada.

Conclusão:

> um `if turno_atual.veto: bloqueia tudo` no sink global seria amplo demais e
> poderia bloquear trabalho background legítimo por causa de um turno de
> conversa simultâneo.

Uma defesa no executor só seria correta no futuro com receipt/ownership de
turno explícito. Não é a menor correção do 229.

## 38.7 Descoberta nova: existe uma segunda rota pós-veto que o 4.27 não cobriu

Depois de `processar_comandos_prioritarios()` recusar uma operação, o fluxo de
resposta ainda entra em `processar_inicio_fluxo_resposta_ia()`.

A primeira etapa operacional desse pré-fluxo é:

```text
processar_continuacao_visao_jogo
```

Ela faz hoje:

```text
se auth=True OU modalidade=comando:
    não continuar visão
senão:
    _continuar_visao_jogo_pendente(texto)
```

Logo um turno fail-closed típico:

```text
modalidade=recusa
auth=False
```

é exatamente ELEGÍVEL para continuação visual.

## 38.8 A ponte de continuação visual não recebe autoridade

`PonteCooperacaoAplicacaoRuntime.continuar_visao_pendente()` tenta em ordem:

```text
1. aplicar_referencia_item(texto)
2. continuar_analise_recente(texto)
3. continuar_pendencia(texto, pendencia_jogo)
4. processar_atualizacao_perfil(texto)
```

A porta `RegistroVisaoJogoAnalise` também não recebe receipt de autoridade.
Portanto a camada visual não consegue distinguir NEUTRO de VETADO por si só.

## 38.9 O killer bare passa pelas guardas lexicais de `continuar_pendencia`

Em `visao_jogo/analise_visual.py`:

`_PEDIDO_NOVA_CAPTURA` só reconhece formas terminadas em:

```text
de novo | novamente | outra vez | mais uma vez
```

`_COMANDO_FORA_DA_VISAO` exige que a fala COMECE por um verbo operacional como:

```text
liga | desliga | abre | fecha | toca | pausa | aumenta | abaixa | diminui ...
```

O killer:

```text
olha esse item nao fecha o opera
```

- não é pedido de nova captura;
- não começa por `fecha`, portanto não casa com `_COMANDO_FORA_DA_VISAO`;
- `aplicar_referencia_item` não casa porque falta molde `meu/minha/atual/equipado`;
- `continuar_analise_recente` não casa porque exige veredito curto por `fullmatch`;
- com pendência visual ativa e análise recente compatível, cai em
  `continuar_pendencia` como se fosse dado complementar.

`continuar_pendencia` então pode iniciar worker, sintetizar resposta, falar e
registrar nova análise/memória visual. Portanto é uma rota operacional real,
ainda que não seja mutação de sistema como CLOSE/VOLUME.

## 38.10 A precondição de pendência visual é real, não fabricada pelo harness

`CoordenadorVisaoJogoRuntime.registrar_analise()` cria pendência canônica quando
uma análise iniciada pelo usuário pede complemento:

```text
origem='visao_jogo'
tipo='complemento_visual'
dominio='jogo'
intencao='GAME_VISION_CONTINUE'
foi_falada=True
ttl=900s
```

Os testes atuais de visão já provam o positivo:

```text
runtime.continuar_pendencia('ela tem 15 de evasão', pendencia) -> True
```

E provam apenas o comando positivo externo:

```text
runtime.continuar_pendencia('liga a luz', pendencia) -> False
```

Eles NÃO cobrem uma fala negada/internalmente contaminada cujo primeiro verbo é
visual, como `olha esse item nao fecha o opera`. Esta é uma lacuna concreta de
teste e de contrato.

## 38.11 Consequência para o menor contrato final

Agora sabemos que somente proteger os três produtores positivos antes do plano
AINDA não basta. Um turno vetado pode sobreviver corretamente até a prioridade,
ser bloqueado ali, e mesmo assim entrar na continuação visual do pré-fluxo.

Logo o menor desenho coerente precisa de duas classes de consumo do veto:

### A. produtores de autoridade

Antes de elevar `auth`, precisam recusar `VETADO -> AUTORIZADO`.

### B. continuidades operacionais do mesmo turno

Antes de consumir pendência/referência anterior, precisam recusar um turno
VETADO. O melhor ponto atual para a visão é o pré-fluxo, onde a decisão inteira
do turno já está disponível; não é necessário empurrar autoridade para dentro
do runtime visual.

## 38.12 Direção mínima atualmente preferida — ainda NÃO é patch aprovado

Contrato puro de turno:

```text
veto_execucao_operacional=True
```

Nascimento:

```text
P0 protegida / V2.4 bare / revisão fail-closed
```

Aplicação:

```text
1. produtores positivos consultam veto antes de elevar autoridade;
2. barreira prioritária trata veto como soberano, independentemente do bool auth;
3. pré-fluxo não entrega continuidades operacionais quando o turno está vetado;
4. decisão/filtro usam autorização efetiva = auth and not veto como defesa de contrato.
```

Não é necessário, para o root 229, colocar veto no executor global nem remodelar
toda a governança cooperativa. Se a prioridade e os produtores preservarem o
veto, a cooperação do 4.26/4.27 deixa de ficar alcançável pelo turno vetado.

## 38.13 Ainda falta uma última falsificação antes do candidato

A nova rota de continuação visual foi provada por composição de fonte e por
precondições reais, mas ainda não recebeu um RED de integração focado.

Próxima falsificação legítima deve testar:

```text
pendência visual canônica ativa
+ análise recente real
+ turno conceitualmente vetado
+ killer bare/internal-negation
-> processar_inicio_fluxo_resposta_ia
-> processar_continuacao_visao_jogo
-> continuar_visao_pendente
```

O sink deve ser recorder/fake de síntese/fala sem captura física.

Pergunta binária:

```text
o veto atual é respeitado pela continuação visual?
```

Pela leitura da fonte, a previsão é RED, mas NÃO carimbar antes da execução.

## 38.14 Status após o estudo

```text
produção ................................ INTACTA
root STT 229 ............................. PROVADO
patch só modalidade ..................... FALSIFICADO
FIRST REAUTH visual ..................... PROVADA
cooperação após reauth .................. REACHABLE
contrato bool único ..................... INSUFICIENTE
campo sticky de veto .................... DIREÇÃO MAIS LIMPA
executor global como gate ............... REJEITADO POR ESCOPO AMPLO
continuação visual pós-veto ............. NOVA ROTA REAL DE FONTE / A FALSIFICAR
candidato final ......................... BLOQUEADO ATÉ ESSA FALSIFICAÇÃO
```


---

# 39. RED 4.28 CRIADO — CONTINUAÇÃO VISUAL PÓS FAIL-CLOSED/VETO

Data: 20/08/2026.

Artefato criado:

`red_v2_4_continuacao_visual_pos_veto_teste4_28.py`

SHA-256:

`d4bb786db7661bed35e1aaebcf831d5ace2d7d6c80b45da9b488c3fb495aca80`

Tamanho: 24741 bytes.
Linhas: 609.
`py_compile`: PASS.
AST parse: PASS.

## 39.1 Pergunta binária

Depois que um turno já está fail-closed (`auth=False`, `modalidade=recusa`,
`texto_operacional=''`) e recebe um receipt sticky de veto, o pré-fluxo real
continua entregando a mesma fala a uma pendência visual anterior?

## 39.2 Componentes reais usados

O 4.28 usa o HEAD travado e trava blobs de:

- `laylay.py`;
- modalidade;
- revisão;
- detector visual;
- porteiro de ações;
- fluxo de resposta IA;
- pré-fluxo contextual;
- ponte de cooperação;
- registros tipados da visão;
- runtime visual;
- análise visual;
- coordenador visual;
- pendência canônica.

A rota exercida é:

```text
classificação fail-closed real
→ processar_inicio_fluxo_resposta_ia
→ processar_continuacao_visao_jogo
→ callback de produção comprovado em laylay.py
→ PonteCooperacaoAplicacaoRuntime.continuar_visao_pendente
→ RegistroVisaoJogoAnalise
→ VisaoJogoRuntime.continuar_pendencia
→ recorder de síntese/fala
```

## 39.3 Pendência não é fabricada à mão

Cada fixture primeiro executa uma análise visual real de componentes com
captura/modelo/voz substituídos por callbacks neutros.

O `CoordenadorVisaoJogoRuntime` recebe a análise que pede complemento e cria a
pendência pela implementação real de:

```text
criar_pendencia
registrar_pendencia
pendencia_ativa
limpar_pendencia
```

Precondições exigidas pelo harness:

```text
origem=visao_jogo
tipo=complemento_visual
dominio=jogo
intencao=GAME_VISION_CONTINUE
status=ativa
foi_falada=True
analise_visual_recente=True
```

Se qualquer uma divergir, EXIT 1.

## 39.4 Harness também foi falsificado

Controles:

1. positivo verdadeiro: `ela tem 15 de evasao` deve atravessar a continuação
   visual real, sintetizar/falar e NÃO fazer nova captura;
2. negativo externo: `liga a luz` não pode ser consumido como complemento
   visual;
3. negativo de recaptura: `lay olha de novo` não pode ser consumido como dado
   complementar.

Além disso o artefato relê a fonte travada para provar:

- `laylay.py` realmente liga `_continuar_visao_jogo_pendente` à
  `PonteCooperacaoAplicacaoRuntime.continuar_visao_pendente`;
- a continuação visual é a primeira etapa do pré-fluxo atual;
- o gate atual usa apenas `autoriza_execucao/modalidade`, não receipt sticky de
  veto.

Segunda revisão estática do harness:

- nenhuma chamada de captura física;
- nenhum `os.startfile`;
- nenhum `pyautogui`;
- nenhum ajuste de volume;
- nenhum fechamento de programa;
- nenhuma chamada de mutação de arquivo;
- único `subprocess.run` é o wrapper de comandos `git` dos guards.

VEREDITO ESTÁTICO DO HARNESS: PASS.

## 39.5 Casos críticos

O RED principal usa formas que o P0 REAL já coloca em fail-closed e que a
revisão não consome:

```text
olha esse item e nao fecha o opera
olha esse item e não fecha o opera
olha esse item e nunca fecha o opera
olha esse item e jamais fecha o opera
```

Para cada caso o harness exige ANTES da execução:

```text
revisao.detectada=False
modalidade=recusa
autoriza_execucao=False
acao_explicita=False
texto_operacional=''
```

Depois adiciona apenas o receipt projetado:

```text
veto_execucao_operacional=True
```

A classificação que originou o fail-closed continua sendo produção real; o
campo extra existe somente para falsificar a hipótese “basta criar/propagar o
veto upstream”.

## 39.6 Semântica de saída

```text
EXIT 1 = lock/import/controle/precondição inválida
EXIT 2 = RED sustentado: pelo menos um fail-closed/vetado chegou ao sink visual
EXIT 0 = hipótese falsificada sob precondições válidas
```

## 39.7 Restrições de interpretação

Até Pedro executar o artefato:

- NÃO carimbar RED;
- NÃO criar candidato final;
- NÃO dizer que a rota foi reproduzida em runtime;
- somente afirmar que a hipótese possui forte prova de fonte e que o harness
  está pronto/estaticamente revisado.

Se der EXIT 2, fica justificado exigir que o consumidor de continuação visual
respeite o veto monotônico. Se der EXIT 0, o desenho deve ser revisto antes de
qualquer candidato.


---

# 40. 4.28 INICIAL EXECUTADO — EXIT 1 DO HARNESS, NÃO DO PRODUTO

Data: 20/08/2026.

Pedro executou:

```text
red_v2_4_continuacao_visual_pos_veto_teste4_28.py
```

Todos os locks, produção limpa e wiring passaram, mas a fixture morreu antes do
RED:

```text
EXIT 1 — FIXTURE CANÔNICA FALHOU
RuntimeError: serviço de leitura da visão de jogo inválido na composição;
operações ausentes: em_andamento, perfil_atual, diagnostico
```

Diagnóstico após estudo de fonte:

O erro foi do próprio harness. Ele fez:

```text
VisaoJogoRuntime cru
  -> registrar_visao_jogo_leitura/analise
```

mas produção NÃO usa essa ligação direta.

`registro_visao_jogo.py` exige para leitura métodos chamáveis:

```text
em_andamento
tem_analise_recente
observar_texto_usuario
perfil_atual
diagnostico
```

Enquanto `VisaoJogoRuntime` expõe `em_andamento` como `@property` e não é a
porta tipada final.

A fronteira correta de produção está em:

```text
mente_laylay/percepcao/visao_jogo/portas_runtime.py
```

com:

```text
VisaoJogoLeituraRuntime
VisaoJogoAnaliseRuntime
```

Esses adaptadores convertem o runtime visual para exatamente o protocolo que os
registros tipados exigem.

Logo:

```text
EXIT 1 = harness sem autoridade
```

Não há evidência causal nova sobre a hipótese de continuação visual.

---

# 41. RED 4.28 REV2 — HARNESS CORRIGIDO NA FRONTEIRA TIPADA REAL

Novo arquivo:

```text
red_v2_4_continuacao_visual_pos_veto_teste4_28_REV2.py
```

SHA-256:

```text
9b1f898a4967a177025ab736f20747d9f1b2dfccc70f937291bc29fde3801146
```

Tamanho: 26172 bytes.
Linhas: 634.
`py_compile`: PASS.
AST parse: PASS.

Mudança única de arquitetura do harness:

```text
VisaoJogoRuntime
  -> criar_visao_jogo_leitura_runtime(visao=runtime)
  -> criar_visao_jogo_analise_runtime(visao=runtime)
  -> registrar_visao_jogo_leitura(adapter)
  -> registrar_visao_jogo_analise(adapter)
```

Também foi adicionado lock do blob real:

```text
mente_laylay/percepcao/visao_jogo/portas_runtime.py
de79bd308c24a9e8a043ef72da78d9ecfbb0b542
```

A hipótese, críticos, controles e semântica de EXIT permanecem iguais.

Segunda revisão estática do REV2:

- HEAD lock PASS;
- `portas_runtime.py` lock PASS;
- adaptador de leitura real presente;
- adaptador de análise real presente;
- registro direto do runtime cru removido;
- full pré-fluxo real mantido;
- seed de pendência canônica mantida;
- positivo `ela tem 15 de evasao` mantido;
- negativos `liga a luz` e `lay olha de novo` mantidos;
- nenhum `os.startfile`, pyautogui, fechamento de programa, ajuste de volume,
  requests, keyboard, win32api ou win32gui;
- nenhuma mutação de arquivo no harness;
- único subprocess continua sendo `git` para guards.

VEREDITO ESTÁTICO REV2: PASS.

Até Pedro executar o REV2:

```text
hipótese de continuação visual ........ FORTE POR FONTE
RED runtime 4.28 ...................... NÃO FECHADO
candidato final ....................... BLOQUEADO
produção .............................. INTACTA
```


---

# 42. TESTE 4.28 REV2 EXECUTADO — RED 4/4 NA CONTINUAÇÃO VISUAL PÓS-VETO

Data/hora local: 20/08/2026, aproximadamente 22:41 -03:00.

Pedro executou:

```text
red_v2_4_continuacao_visual_pos_veto_teste4_28_REV2.py
```

SHA-256 do harness:

```text
9b1f898a4967a177025ab736f20747d9f1b2dfccc70f937291bc29fde3801146
```

Resultado local:

```text
EXIT 2
REDs observados: 4/4
```

Todos os locks, produção limpa, wiring e controles passaram.

## 42.1 Harness ganhou autoridade

A fixture canônica passou usando a fronteira tipada real:

```text
VisaoJogoRuntime
→ VisaoJogoLeituraRuntime / VisaoJogoAnaliseRuntime
→ registros tipados
```

A pendência criada pelos componentes reais ficou:

```text
origem=visao_jogo
tipo=complemento_visual
status=ativa
foi_falada=True
analise_recente=True
```

## 42.2 Controles do harness

Positivo verdadeiro:

```text
ela tem 15 de evasao
```

Resultado:

```text
pre-fluxo tratou=True
sinteses=1
falas=1
capturas_pos_seed=0
```

Logo a rota de continuação visual estava viva.

Negativos também passaram:

```text
liga a luz       -> continuacao=False
lay olha de novo -> continuacao=False
```

Portanto o RED não veio de uma fixture que consumia qualquer texto.

## 42.3 Precondição fail-closed real

Quatro casos foram classificados pela produção real como fail-closed, sem revisão:

```text
olha esse item e nao fecha o opera
olha esse item e não fecha o opera
olha esse item e nunca fecha o opera
olha esse item e jamais fecha o opera
```

Todos:

```text
revisao.detectada=False
modalidade=recusa
autoriza_execucao=False
acao_explicita=False
texto_operacional=''
```

O harness adicionou somente o receipt projetado:

```text
veto_execucao_operacional=True
```

para perguntar se o consumidor atual o respeitaria.

## 42.4 RED 4/4 no pré-fluxo real

Nos quatro críticos:

```text
pendencia_antes=True
prefluxo_tratou=True
continuar_chamadas=1
sumarizacoes=1
falas=1
captura_pos_seed=0
```

Isto prova que:

```text
turno fail-closed/vetado
→ processar_inicio_fluxo_resposta_ia
→ processar_continuacao_visao_jogo
→ continuar_visao_pendente
→ VisaoJogoRuntime.continuar_pendencia
→ síntese/fala
```

permanece alcançável no HEAD travado.

Nenhum efeito físico foi produzido.

## 42.5 FIRST RED desta nova fronteira

Para esta falsificação específica, o primeiro boundary que ignora o novo contrato é:

```text
processar_continuacao_visao_jogo()
```

porque ele considera elegível qualquer turno que satisfaça:

```text
not autoriza_execucao
and modalidade != 'comando'
```

mas não consulta o receipt sticky de veto.

Depois disso a ponte/runtime visual apenas consome a continuação que recebeu.

Não chamar esta função de root original do turno 229. Ela é uma fronteira
pós-fix/pós-veto descoberta durante a auditoria de monotonicidade.

## 42.6 Diagnóstico consolidado das duas classes pós-classificação

A investigação agora provou duas classes distintas que precisam respeitar um
veto soberano:

### A. Produtores positivos de autoridade

Primeiro reautorizador provado para o killer bare/V2.4:

```text
aplicar_pedido_visual_ao_turno()
```

4.27 demonstrou:

```text
VETADO -> AUTORIZADO
```

se o produtor visual não conhece o veto.

### B. Consumidores de continuidade operacional

4.28 REV2 demonstrou:

```text
VETADO -> continuação visual anterior consumida
```

mesmo quando `autoriza_execucao=False` permanece intacto.

Logo preservar somente o booleano `autoriza_execucao=False` também é
insuficiente.

## 42.7 Contrato mínimo agora suficientemente sustentado para candidato

A direção mínima estudada continua:

```text
veto_execucao_operacional=True
```

com semântica sticky no mesmo turno.

Regras necessárias:

```text
NEUTRO -> AUTORIZADO   permitido por especialização legítima
AUTORIZADO -> VETADO   permitido por proteção soberana
VETADO -> AUTORIZADO   proibido no mesmo turno
VETADO -> CONTINUIDADE_OPERACIONAL_ANTERIOR proibido no mesmo turno
```

Defesas mínimas por classe:

1. nascimento do veto em P0/V2.4/revisão fail-closed;
2. produtores positivos consultam veto antes de elevar autoridade;
3. barreira prioritária trata veto como soberano;
4. pré-fluxo não entrega continuidades operacionais quando veto=True;
5. decisão/filtro derivam autoridade efetiva como `auth and not veto`.

Ainda NÃO inserir gate global no executor canônico, pois ele é compartilhado
com serviços/background e não possui receipt de ownership do turno.

## 42.8 Status soberano após 4.28 REV2

```text
produção ................................ INTACTA
root STT 229 ............................. PROVADO
root punctuado de revisão ............... SEPARADO
V2.4 política conservadora .............. VIVA
patch só em modalidade .................. FALSIFICADO
FIRST REAUTH visual ..................... PROVADA
barreira histórica bare/STT ............. NÃO RECOMPÕE
cooperação após reauth .................. REACHABLE
continuação visual pós-veto ............. RED 4/4 PROVADO
FIRST RED dessa nova fronteira .......... processar_continuacao_visao_jogo
booleano auth sozinho ................... INSUFICIENTE
veto sticky monotônico .................. NECESSIDADE ARQUITETURAL SUSTENTADA
executor global como gate ............... REJEITADO POR ESCOPO
candidato final ......................... PODE SER DESENHADO, MAS AINDA NÃO APROVADO
```

Próximo passo correto:

- desenhar o candidato mínimo de veto monotônico;
- antes de tocar produção, montar falsificações do candidato que cubram:
  - NEUTRO -> AUTORIZADO visual e repetição legítimos;
  - VETADO -> AUTORIZADO bloqueado;
  - VETADO -> continuação visual bloqueada;
  - P0 histórica sem regressão;
  - bare/STT do 229;
  - `nao.txt`/payload estreito sem falso positivo;
  - cadeia com nova ação real após boundary;
  - decisão/filtro coerentes, inclusive segmentos internos.
- após qualquer GREEN, segunda revisão integral obrigatória antes de patch de produção.


---

# 43. CANDIDATO FINAL LAB V2.5 — VETO MONOTÔNICO DESENHADO, AINDA NÃO EXECUTADO

Data: 20/08/2026.

Artefato autoritativo atual:

```text
falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py
```

SHA-256 após a segunda auditoria integral:

```text
3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef
```

Tamanho:

```text
1987 linhas
78048 bytes
py_compile PASS
AST PASS
```

Produção continua INTACTA. O arquivo é LAB/falsificador de candidato, não patch.

## 43.1 Contrato central

Receipt único:

```text
veto_execucao_operacional=True
```

Estado derivado:

```text
veto=True                 -> VETADO
veto=False + auth=True    -> AUTORIZADO
veto=False + auth=False   -> NEUTRO
```

Não persistir enum paralelo. Autoridade efetiva:

```text
autoriza_execucao_efetiva = autoriza_execucao and not veto_execucao_operacional
```

Regras:

```text
NEUTRO -> AUTORIZADO                         permitido
AUTORIZADO -> VETADO                         permitido
VETADO -> AUTORIZADO                         proibido
VETADO -> continuidade operacional anterior  proibido
```

## 43.2 Nascimento do veto — correção importante da segunda auditoria

NÃO transformar todo `auth=False` em sticky.

O receipt nasce em proteções soberanas, incluindo:

```text
P0 cancelamento
P0 capacidade
P0 hipotética
P0 menção operacional/metalinguagem
P0 instrução/explicação sobre ação
P0 decepção/autoria
negação interna bare/STT do V2.5
revisão ambígua/cancelada
recusa operacional histórica com comando explícito
```

Mas P0:

```text
natureza_acao=informativa_sobre_acao
```

permanece `auth=False` NÃO-sticky. Motivo: consultas live legítimas como:

```text
o opera continua aberto?
```

precisam continuar alcançando a habilidade read-only sem ganhar autoridade de
mutação.

Também:

```text
nao
```

continua `auth=False` sem receipt por si só, para uma pendência legítima ainda
poder interpretar uma recusa curta.

## 43.3 Fail-closed canônico e coerência nested

O helper do candidato reescreve o contrato inteiro:

```text
modalidade/modalidade_geral/ato_principal
atos
segmentos
texto_operacional=''
autoriza_execucao=False
acao_explicita=False
requer_esclarecimento
natureza/motivo
veto_execucao_operacional=True
```

Cada segmento fica:

```text
modalidade != comando
autoriza_execucao=False
acao_explicita=False
```

Isto fecha o defeito stale do 4.25.

## 43.4 Bare/STT conservador

Predicado puro reconhece standalone:

```text
nao | não | nunca | jamais
```

internos, sem lista privada de verbos e sem confiar em aspas.

Exceção lexical estreita:

```text
nao.<ext>
não.<ext>
```

somente quando o átomo aparece imediatamente sob moldura explícita de
`arquivo/documento`.

Positivos preservados:

```text
cria arquivo nao.txt
abre o arquivo nao.txt
cria arquivo não.md
```

Boundary obrigatório:

```text
cria arquivo nao.txt e fecha o opera nao a microsoft store
```

continua vetado; proteção do átomo não atravessa um ato posterior.

## 43.5 Root pontuado separado

A segunda revisão encontrou que interceptar apenas `substituicao_alvo` era
insuficiente para:

```text
fecha a microsoft store, não feche o opera
```

O candidato agora usa evidência estrutural mínima:

```text
não, FAÇA C  -> correção discursiva positiva pode ser consolidada
não FAÇA B   -> negação; fail-closed
não O B      -> restrição elíptica; fail-closed
```

A pontuação imediatamente DEPOIS de `não` é o receipt literal de correção
discursiva.

Controles positivos preservados:

```text
Abre Wikipédia... não, melhor Prime Video.
Pausa a música... não, continua tocando.
Liga a lâmpada... não, deixa desligada.
Cria um arquivo ... não, chama correcao.txt.
```

## 43.6 Produtores pós-classificação

Veto é consultado antes de elevar autoridade em:

```text
repetição
elipse espacial
pedido visual
```

Controles positivos exigidos:

```text
olha esse item -> visual autorizado
tenta de novo  -> repetição autorizada
esquerda       -> elipse autorizada
```

A barreira candidata também considera:

```text
receipt sticky
OU
predicado raw bare/STT
```

antes de confiar em `autoriza_execucao`, servindo como defesa contra estado
stale produzido por camada antiga.

## 43.7 Read-only prioritário antes da barreira

Estudo de `comandos_imediatos.py` confirmou duas exceções antes da barreira:

1. `processar_consulta_sistema_local()`;
2. resposta estática de catálogo de capacidade.

O candidato diferencia:

```text
LIVE READ-ONLY + VETO -> bloqueia
CAPACIDADE ESTÁTICA + VETO -> pode responder sem criar intent
```

Positivos adicionais agora exigidos:

```text
prioritário read-only sem receipt continua permitido
quais programas estao abertos -> consulta live positiva
o opera continua aberto?      -> P0 informativa NÃO-sticky e consulta positiva
```

## 43.8 Árbitro e coordenador

`arbitrar_turno()` atual isenta `INTENTS_SOMENTE_LEITURA` do booleano de
autorização. O candidate wrapper torna receipt soberano também sobre read-only.

`resolver_intencao()` possui retornos precoces de agenda antes do árbitro. O
candidate gate consulta receipt antes de agenda, continuidade, detector e
IA-first.

Controles:

```text
GAME_VISION read-only sob veto -> árbitro candidato rejeita
GAME_VISION read-only neutro    -> árbitro continua aceitando
agenda + restrição interna      -> coordenador candidato bloqueia
agenda positiva sem veto        -> continua AGENDAR_LEMBRETE / rota agenda
```

## 43.9 Pré-fluxo — segunda auditoria tornou o gate seletivo por classe

4.28 REV2 provou FIRST RED em:

```text
processar_continuacao_visao_jogo
```

A revisão de fonte posterior mostrou que o mesmo pipeline contém outras etapas
capazes de reutilizar estado anterior para gerar trabalho operacional:

```text
processar_reparacao_conversacional
processar_resposta_pendencia_prioritaria
processar_feedback_pendente
processar_confirmacao_musical_pendente
processar_pergunta_curta_contextual
```

O candidato NÃO mata o pré-fluxo inteiro. Em turno VETADO ele omite somente a
classe acima, mais a continuação visual.

Continuam vivos:

```text
comentário sobre resultado anterior
opinião conversacional de música
proteção/bloqueio de playlist
```

O LAB ganhou probes específicos que mostram a superfície atual e exigem o gate
candidato para:

```text
feedback pendente
confirmação musical pendente
pergunta curta contextual
continuação visual
```

Controle de estreiteza:

```text
nao toca playlist agora
```

continua podendo aplicar a proteção de playlist mesmo com receipt soberano.

O monkeypatch do LAB é somente em memória e todos os símbolos são restaurados
em `finally`.

## 43.10 Plano, decisão e filtro

Sob veto:

```text
plano.autoriza_execucao=False
plano.requer_execucao=False
cada ato.requer_execucao=False
contrato_decisao.permite_acao=False
filtro de comandos -> []
```

O LAB fabrica deliberadamente um objeto incoerente:

```text
veto=True
auth=True
segmento comando/auth=True
```

para provar que receipt vence autoridade stale nas defesas tardias.

## 43.11 Cooperação

Controle visual positivo deve alcançar recorder cooperativo.

Turno vetado não deve entrar na cooperação porque a barreira soberana o encerra
antes.

Nenhum efeito físico é produzido.

## 43.12 Matriz principal

Cobre:

- root pontuado original com `só`;
- pontuado sem `só`;
- `mas nao`;
- pontuado com `não feche`;
- STT com/sem `só` e com/sem acento;
- inversão Store/Opera;
- `não feche` explícito nas duas orientações;
- `nunca`/`jamais`;
- payload de volume/search/write/music;
- `toca nao existe amor em sp` conservador;
- quoted/malformed quote conservadores;
- `nao.txt` positivos;
- boundary de ato após `nao.txt`;
- positivos de CLOSE/VOLUME/SEARCH/MUSIC/cadeia;
- P0/históricos;
- P0 informativa read-only positiva;
- visual/repetição/elipse;
- plano/decisão/filtro;
- read-only prioritário positivo e vetado;
- árbitro positivo e vetado;
- coordenador/agenda positivo e vetado;
- pré-fluxo visual;
- feedback pendente;
- confirmação musical;
- pergunta curta contextual;
- proteção de playlist;
- cooperação.

## 43.13 Revisão estática integral final

Resultado:

```text
py_compile ........ PASS
AST ............... PASS
duplicates ........ NONE
unresolved main ... NONE
forbidden hits .... NONE
file mutations .... NONE
VEREDITO ESTÁTICO . PASS
```

Bloqueios de segurança do próprio harness:

```text
os.startfile                         0
pyautogui                            0
fechar_programa                      0
close_app                            0
ajustar_volume_sistema               0
requests                             0
keyboard                             0
win32api/win32gui                    0
captura física                       0
mutação de arquivo                   0
```

Único `subprocess.run`: wrapper de `git` para guards/locks.

Também foi travado:

```text
mente_laylay/autonomia/pre_fluxo_musical.py
7b3f7111f3c844c1b9676ad4f3101786ce500947
```

porque a segunda auditoria passou a falsificar explicitamente a confirmação
musical pendente.

## 43.14 Semântica de saída

```text
EXIT 0 = candidato LAB V2.5 GREEN
EXIT 1 = lock/wiring/controle/precondição inválida
EXIT 2 = candidato falsificado
```

Até Pedro executar:

```text
produção ................................. INTACTA
candidato V2.5 ........................... CRIADO / NÃO EXECUTADO
revisão estática do LAB .................. PASS
GREEN runtime local ...................... NÃO CARIMBADO
patch de produção ........................ BLOQUEADO
```

Se o LAB vier GREEN: segunda revisão integral do RESULTADO e do desenho antes de
qualquer patch de produção. Se vier EXIT 2: FIRST RED do candidato manda no
próximo diagnóstico. Se vier EXIT 1: corrigir harness/premissa, sem dar crédito
ou culpa ao candidato.


---

# 44. LAB V2.5 EXECUTADO — EXIT 0 REAL, MAS SEGUNDA REVISÃO PÓS-GREEN ENCONTROU UMA INVARIANTE FALTANTE

Data/hora local: 20/08/2026, aproximadamente 23:25 -03:00.

Pedro executou:

```text
falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py
```

SHA-256 do artefato executado:

```text
3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef
```

Resultado:

```text
EXIT 0 — CANDIDATO FINAL LAB V2.5 GREEN
```

Todos os guards e locks passaram, produção estava limpa e todos os controles da
matriz escrita passaram.

Portanto o GREEN é legítimo **para a matriz que o LAB realmente testou**. Não é
um EXIT 0 inválido de harness.

## 44.1 O que o GREEN provou

O run local confirmou, entre outros:

```text
FALSE neutro != veto
root pontuado -> fail-closed
root STT/bare -> fail-closed
nao.txt -> não recebe veto
visual neutro -> autorizado
visual vetado -> não reautoriza
repetição neutra -> autorizada
elipse neutra -> autorizada
contrato nested vetado coerente
receipt vence estado stale
cooperação positiva continua viva
cooperação vetada fica inalcançável
read-only neutro continua vivo
read-only sob veto é barrado no candidato
árbitro neutro continua vivo
árbitro sob veto é barrado no candidato
coordenador/agenda positivo continua vivo
coordenador sob veto é barrado
continuação visual sob veto é barrada
feedback/confirmacao musical/pergunta curta do killer usado no LAB não sequestram o turno
proteção de playlist continua viva
```

Assim, a hipótese central do receipt sticky sobreviveu a uma matriz ampla.

## 44.2 Segunda revisão integral obrigatória pós-GREEN — DEFEITO DE DESENHO ENCONTRADO

A revisão pós-GREEN não rejeitou o resultado do harness; ela encontrou que a
**matriz estava incompleta em uma direção importante**.

O V2.5 agrupa estas funções em `ETAPAS_PRE_FLUXO_VETADAS` e as corta por inteiro
quando `veto_execucao_operacional=True`:

```text
processar_continuacao_visao_jogo
processar_reparacao_conversacional
processar_resposta_pendencia_prioritaria
processar_feedback_pendente
processar_confirmacao_musical_pendente
processar_pergunta_curta_contextual
```

Isso é correto para continuidades que podem elevar/reutilizar autoridade, mas é
amplo demais para funções **mistas** que também possuem ramos revogatórios.

### Prova por fonte: exclusão pendente

`processar_resposta_pendencia_prioritaria()` possui um ramo seguro de recusa:

```text
resposta negativa
-> classificar_confirmacao_local(...) == False
-> intent=CANCEL_DELETE_ITEM
-> limpa/cancela a pendência de exclusão
```

`classificar_confirmacao_local()` reconhece explicitamente como False, entre
outras formas:

```text
nao
cancela
nao apaga ...
nao exclui ...
nao remove ...
```

Ao mesmo tempo, `nao apaga ...` é P0 operacional de natureza `cancelamento`,
logo o candidato V2.5 lhe dá receipt sticky.

O gate genérico do LAB faz então:

```text
VETO=True
-> processar_resposta_pendencia_prioritaria NÃO roda
-> CANCEL_DELETE_ITEM nunca nasce
-> pendência antiga pode permanecer ativa
```

Isto é uma regressão real de contrato e potencialmente de segurança: um veto
mais explícito pode deixar uma ação destrutiva pendente em vez de revogá-la.

### Prova por fonte: feedback proativo

`handle_feedback_pendente()` também possui ramo estritamente redutor:

```text
classificar_confirmacao_local(texto) == False
-> limpa _rotina_sugestao_pendente
-> limpa _playlist_sugestao_pendente
-> limpa _email_sugestao_pendente
-> registra recusa
-> não executa a sugestão
```

Bloquear `processar_feedback_pendente()` por inteiro sob receipt impede essa
revogação e pode deixar sugestões antigas pendentes.

Portanto a abstração correta NÃO é:

```text
VETADO -> nenhuma continuidade operacional
```

A regra mais precisa passa a ser:

```text
VETADO -> transição que AUMENTA/REUTILIZA autoridade      PROIBIDA
VETADO -> transição que CONFIRMA execução anterior       PROIBIDA
VETADO -> transição REVOGATÓRIA/CANCELADORA              PERMITIDA
VETADO -> proteção/conversa sem autoridade                PERMITIDA
```

Esse é um refinamento da monotonicidade, não abandono dela.

## 44.3 FIRST boundary do defeito pós-GREEN

No candidato V2.5, o primeiro boundary que causa esta regressão é o gate
genérico:

```text
etapa_prefluxo_operacional_candidata()
```

quando aplicado indiscriminadamente a:

```text
processar_resposta_pendencia_prioritaria
processar_feedback_pendente
processar_confirmacao_musical_pendente
```

A falha não está no receipt em si; está em tratar funções mistas como se todo
resultado delas aumentasse autoridade.

## 44.4 Consequência para o candidato

Status correto após a segunda revisão:

```text
GREEN do LAB V2.5 ........................ LEGÍTIMO PARA A MATRIZ
receipt sticky ............................ CONTINUA PROMISSOR
candidato V2.5 exatamente como desenhado .. REJEITADO PARA PRODUÇÃO
motivo .................................... gate pré-fluxo amplo demais para ramos revogatórios
produção .................................. INTACTA
patch de produção ......................... CONTINUA BLOQUEADO
```

Não chamar esse GREEN de falso. A matriz passou; a segunda revisão encontrou uma
invariante que a matriz não continha.

## 44.5 Nova regra soberana aprendida

Adicionar às regras de investigação:

> **Veto monotônico não pode impedir revogação.** Uma proteção sticky proíbe
> qualquer transição que crie, restaure, confirme ou reutilize autoridade
> prática no mesmo turno, mas deve permitir transições estritamente redutoras
> de autoridade, como cancelar uma exclusão pendente, rejeitar uma sugestão ou
> limpar uma confirmação antiga.

Também:

> **Função mista não pode ser classificada pelo pior ramo.** Se um helper possui
> tanto caminho de confirmação/execução quanto caminho de cancelamento, o gate
> precisa decidir pelo efeito/postcondição ou pelo tipo de resposta, não apenas
> pelo nome da função.

## 44.6 Lacuna secundária de evidência: `nao.txt`

O run mostrou:

```text
A1 veto=False auth=True op='cria arquivo nao txt'
A2 veto=False auth=True op='abre o arquivo nao txt'
```

Isso não é, por si só, prova end-to-end do basename.

Estudo de fonte reduz a preocupação porque:

```text
nome_natural.py::_restaurar_extensao_falada()
```

recoloca o ponto para extensões textuais conhecidas, e
`roteador_arquivos.py` usa `limpar_nome_arquivo_natural()` ao extrair nomes de
arquivo. Ainda assim, pela regra soberana de payload end-to-end, o próximo LAB
deve incluir um positivo funcional que prove que `nao.txt` chega ao roteador
como `nao.txt`, não apenas que a modalidade ficou autorizada.

## 44.7 Próxima falsificação correta

Antes de desenhar V2.5.1 ou tocar produção, montar um falsificador focado em
**revogação sob veto**.

Casos mínimos:

1. exclusão pendente + `nao` curto -> continua cancelando;
2. exclusão pendente + `nao apaga o arquivo` -> receipt sticky, mas
   `CANCEL_DELETE_ITEM` precisa continuar alcançável;
3. exclusão pendente + killer sem relação (`olha item nao fecha opera`) -> não
   pode ser consumido como resposta da exclusão;
4. sugestão proativa pendente + recusa explícita compatível -> pendência é limpa;
5. sugestão pendente + killer não relacionado -> não é consumido;
6. confirmação positiva sob receipt -> continua proibida;
7. `nao.txt` -> prova funcional end-to-end do basename no roteador de arquivos.

Semântica desejada:

```text
EXIT 2 = desenho V2.5 atual falsificado pela revogação (esperado)
EXIT 0 = hipótese de regressão falsificada
EXIT 1 = harness/premissa inválida
```

Somente depois desse RED legítimo redesenhar o gate por **direção de autoridade**
(autorizar/confirmar versus revogar/cancelar).


---

# 45. FALSIFICAÇÃO 4.29 CRIADA — REVOGAÇÃO SOB VETO

Data/hora local: 20/08/2026, aproximadamente 23:34 -03:00.

Artefato:

```text
falsificacao_revogacao_sob_veto_teste4_29.py
```

SHA-256:

```text
62d7c86d8e5f231281981513679571a98433e0c8a2a383bdb83aefb2c089fbd5
```

Tamanho:

```text
787 linhas
30497 bytes
py_compile PASS
AST PASS
```

## 45.1 Objetivo causal

Falsificar o desenho EXATO do V2.5 que ficou GREEN, sem criar V2.5.1 ainda.

Hipótese pós-GREEN:

```text
veto_execucao_operacional=True
+ gate por função inteira
-> pode impedir CANCELAMENTO/REVOGAÇÃO segura
```

Regra refinada a provar:

```text
VETADO -> criar/restaurar/confirmar autoridade   proibido
VETADO -> cancelar/revogar autoridade            permitido
```

## 45.2 O harness importa o candidato GREEN exato

O teste exige na raiz do repo:

```text
falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py
```

com SHA exato:

```text
3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef
```

Se ausente ou diferente, EXIT 1.

O harness importa o arquivo pelo path e usa de verdade:

```text
cand.prefluxo_candidato
cand.construir_turno_candidato
cand.aplicar_veto_canonico
cand.turno_tem_veto_execucao
cand.autoriza_execucao_efetiva
cand.ETAPAS_PRE_FLUXO_VETADAS
```

Logo não existe uma cópia simplificada do desenho V2.5 dentro do 4.29.

## 45.3 Estudo de fonte que sustenta a falsificação

`processar_resposta_pendencia_prioritaria()` é uma função mista real:

```text
resposta positiva -> CONFIRM_DELETE_ITEM
resposta negativa -> CANCEL_DELETE_ITEM
```

A recusa é reconhecida tanto por formas curtas quanto por
`classificar_confirmacao_local()`.

`classificar_confirmacao_local()` retorna False para formas como:

```text
nao
cancela
nao apaga ...
nao exclui ...
nao remove ...
```

Portanto:

```text
nao apaga o arquivo
```

é simultaneamente:

```text
P0 operacional / recusa / cancelamento
```

e uma resposta legítima capaz de gerar:

```text
CANCEL_DELETE_ITEM
```

A função de feedback proativo também é mista. `handle_feedback_pendente()` pode
limpar pendências de rotina/playlist/email em resposta negativa, sem executar a
sugestão.

## 45.4 Matriz de exclusão

### Controle positivo

Pendência de exclusão mental canônica +:

```text
nao
```

não recebe sticky no V2.5 e deve continuar gerando:

```text
CANCEL_DELETE_ITEM
```

pelo pré-fluxo completo do V2.5.

### Crítico

```text
nao apaga o arquivo
```

O candidato V2.5 deve classificar:

```text
modalidade=recusa
autoriza_execucao=False
veto_execucao_operacional=True
```

O helper REAL, chamado diretamente com executor recorder, deve produzir:

```text
CANCEL_DELETE_ITEM
```

Depois o MESMO caso atravessa `cand.prefluxo_candidato()`.

RED esperado do desenho atual:

```text
função mista inteira omitida
-> CANCEL_DELETE_ITEM não chega ao recorder
```

### Controle oposto

O helper real também prova seu ramo positivo:

```text
sim -> CONFIRM_DELETE_ITEM
```

Depois um receipt adversarial é aplicado a `sim`. Sob veto, o V2.5 DEVE
continuar bloqueando `CONFIRM_DELETE_ITEM`.

Isso separa claramente:

```text
bloquear confirmação = correto
bloquear cancelamento = regressão
```

### Não-sequestro

Com exclusão pendente:

```text
olha esse item nao fecha o opera
```

não pode virar nem CONFIRM nem CANCEL da exclusão.

## 45.5 Matriz de feedback proativo

Sugestão de rotina pendente para Opera +:

```text
nao abre o opera
```

O candidato torna o turno sticky via P0.

`classificar_confirmacao_local()` retorna `None`, então o harness usa
`classificar_confirmacao_contextual()` REAL, substituindo somente o boundary
externo da interpretação LLM por um retorno determinístico `False`.

O handler REAL deve então:

```text
classificar recusa
-> registrar feedback aceito=False
-> limpar _rotina_sugestao_pendente
-> não abrir app
```

O V2.5 exato é então executado pelo full pre-fluxo.

RED esperado:

```text
processar_feedback_pendente omitido por gate sticky
-> pendência continua viva
-> revogação não acontece
```

Controle:

```text
olha esse item nao fecha o opera
```

não pode ser sequestrado como feedback da sugestão.

## 45.6 `nao.txt` — fechamento da lacuna end-to-end

O LAB anterior só provou:

```text
veto=False
auth=True
```

para:

```text
cria arquivo nao.txt
```

O 4.29 atravessa agora:

```text
construir_turno_candidato
-> texto_operacional normalizado
-> detectar_intencao_arquivos REAL
```

E exige em duas entradas:

```text
texto_operacional
raw original
```

resultado:

```text
intent=CREATE_FILE
params.alvo='nao.txt'
```

Nenhum arquivo físico é criado.

## 45.7 Segurança do harness

Segunda revisão estática:

```text
py_compile ........ PASS
AST ............... PASS
duplicates ........ NONE
unresolved main ... NONE
forbidden hits .... NONE
file mutations .... NONE
VEREDITO ESTÁTICO . PASS
```

Não há chamadas de:

```text
os.startfile
pyautogui
fechar app
ajustar volume
requests
keyboard
win32api/win32gui
captura física
mover_para_lixeira
confirmar_exclusao_pendente
```

O único `subprocess.run` é o wrapper de `git` para guards.

A pendência de exclusão é somente um contrato em memória; o executor é recorder.

O monkeypatch temporário do candidato é verificado e precisa restaurar as funções
reais após cada passagem.

## 45.8 Semântica de saída

```text
EXIT 1 = lock/import/controle/precondição/harness inválido
EXIT 2 = V2.5 GREEN falsificado pela nova invariável de revogação
EXIT 0 = hipótese pós-GREEN falsificada; V2.5 preservou revogação
```

Até Pedro executar:

```text
V2.5 GREEN anterior ....................... LEGÍTIMO PARA A MATRIZ ANTIGA
hipótese de regressão revogatória ......... FORTE POR FONTE
4.29 runtime ............................... NÃO EXECUTADO
V2.5.1 .................................... NÃO CRIADO
produção .................................. INTACTA
patch produção ............................ BLOQUEADO
```

Próxima autoridade é exclusivamente o resultado local do 4.29.


---

# 46. PRIMEIRA EXECUÇÃO DO 4.29 — EXIT 1 INVÁLIDO POR ARTEFATO CANDIDATO AUSENTE

Data/hora local: 20/08/2026, aproximadamente 23:49 -03:00.

Pedro executou:

```text
falsificacao_revogacao_sob_veto_teste4_29.py
```

Resultado observado:

```text
HEAD ........................................ PASS
blobs causais ............................... PASS
produção rastreada limpa ................... PASS
wiring pendência mista ..................... PASS
wiring feedback runtime .................... PASS
candidato V2.5 GREEN exato ................. FAIL ausente

EXIT 1 — LOCK/PREMISSA INVÁLIDA
```

Classificação soberana:

```text
NÃO é RED
NÃO é GREEN
NÃO atribui culpa nem crédito ao candidato
```

A falha ocorreu antes da falsificação causal porque o 4.29 exige o artefato
local exato:

```text
falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py
SHA256 3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef
```

O candidato havia sido executado anteriormente com EXIT 0 e esse SHA, portanto
a próxima ação correta é localizar/restaurar o artefato exato, não modificar a
hipótese nem atualizar locks.

Diagnóstico recomendado antes de qualquer REV do harness:

```powershell
Get-ChildItem -Path . -Recurse -File -Filter "falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py" |
  Select-Object FullName,Length

Get-ChildItem -Path . -Recurse -File |
  Where-Object { $_.Name -like "*veto*monotonico*V2_5*.py" } |
  ForEach-Object {
    [PSCustomObject]@{
      FullName = $_.FullName
      SHA256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    }
  }
```

Se o arquivo estiver em subpasta com o SHA correto, decidir se o harness deve
passar a localizar o candidato por SHA dentro do repo. Se não existir mais,
restaurar exatamente o artefato GREEN e rerodar o mesmo 4.29 sem mudar uma
linha do falsificador.

Estado:

```text
4.29 runtime causal ............ AINDA NÃO EXECUTADO
primeira tentativa ............. INVALIDA / EXIT 1
hipótese de revogação .......... NÃO TESTADA EM RUNTIME
produção ....................... INTACTA
```


---

# 47. DIAGNÓSTICO DO EXIT 1 DO 4.29 — CANDIDATO V2.5 REALMENTE AUSENTE DO REPO

Data/hora local: 20/08/2026, aproximadamente 23:53 -03:00.

Pedro executou duas buscas recursivas na raiz do repositório:

```powershell
Get-ChildItem -Path . -Recurse -File -Filter "falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py" |
    Select-Object FullName,Length

Get-ChildItem -Path . -Recurse -File |
    Where-Object { $_.Name -like "*veto*monotonico*V2_5*.py" } |
    ForEach-Object {
        [PSCustomObject]@{
            FullName = $_.FullName
            SHA256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
        }
    }
```

Ambos retornaram **nenhuma entrada**.

Conclusão:

```text
o candidato V2.5 GREEN não está em nenhuma subpasta do repo
```

Portanto o EXIT 1 do 4.29 foi corretamente causado por artefato auxiliar ausente,
não por caminho rígido errado do harness.

Não criar REV2 do 4.29. Próximo passo correto:

1. restaurar exatamente na raiz do repo:

```text
falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py
```

2. exigir SHA-256:

```text
3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef
```

3. rerodar o MESMO:

```text
falsificacao_revogacao_sob_veto_teste4_29.py
```

sem alterar HEAD, blobs, locks ou código do 4.29.

Status:

```text
4.29 tentativa 1 ................ INVALID / EXIT 1
causa ............................ candidato auxiliar ausente
REV2 do 4.29 ..................... NÃO NECESSÁRIA
hipótese de revogação ............ AINDA NÃO TESTADA EM RUNTIME
produção .......................... INTACTA
```


---

# 48. SEGUNDA TENTATIVA DO 4.29 — TESTE NÃO ABRIU POR ARTEFATO 4.29 AUSENTE

Data/hora local: 20/08/2026, aproximadamente 23:56 -03:00.

Pedro restaurou corretamente o candidato V2.5 na raiz do repo e confirmou SHA:

```text
3BFCABAAB1E761BE707199FD6DF73EE961695A9C6AB98937119A4CA5178520EF
```

Em seguida tentou executar:

```powershell
& C:\Python314\python.exe ".\falsificacao_revogacao_sob_veto_teste4_29.py"
```

mas o Python retornou:

```text
[Errno 2] No such file or directory
```

Classificação soberana:

```text
NÃO é EXIT do harness
NÃO é RED
NÃO é GREEN
NÃO testa a hipótese de revogação
```

O próprio arquivo `falsificacao_revogacao_sob_veto_teste4_29.py` não está na
raiz local do repo. Próximo passo correto:

1. restaurar o artefato 4.29 exato;
2. conferir SHA-256:

```text
62d7c86d8e5f231281981513679571a98433e0c8a2a383bdb83aefb2c089fbd5
```

3. rerodar o MESMO comando.

Estado:

```text
candidato V2.5 .................... RESTAURADO / SHA OK
4.29 arquivo ...................... AUSENTE LOCALMENTE
4.29 runtime causal ............... AINDA NÃO EXECUTADO
produção ........................... INTACTA
```


---

# 49. TESTE 4.29 EXECUTADO — EXIT 2 AUTORITATIVO, COM DOIS DEFEITOS INDEPENDENTES

Data/hora local: 20/08/2026, aproximadamente 23:57 -03:00.

Pedro executou:

```text
falsificacao_revogacao_sob_veto_teste4_29.py
```

com candidato V2.5 exato restaurado:

```text
SHA256 3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef
```

Resultado:

```text
EXIT 2
```

Todos os guards, blobs, produção limpa, wiring, SHA do candidato e precondições
passaram. Logo esta execução tem autoridade causal.

## 49.1 Revogação de exclusão — RED sustentado

Função real, com pendência de exclusão em memória:

```text
'nao' -> CANCEL_DELETE_ITEM                           PASS
'nao apaga o arquivo' -> CANCEL_DELETE_ITEM           PASS
'sim' -> CONFIRM_DELETE_ITEM                          PASS
killer não relacionado -> nenhuma resposta da lixeira PASS
```

O caso crítico `nao apaga o arquivo` foi classificado pelo V2.5 como:

```text
modalidade=recusa
autoriza_execucao=False
veto_execucao_operacional=True
```

Chamado diretamente, o helper real produz a transição segura:

```text
CANCEL_DELETE_ITEM
```

Mas atravessando o V2.5 exato:

```text
tratado=False
intents=[]
```

Resultado observado:

```text
RED: receipt bloqueou uma transição estritamente revogatória
```

Ao mesmo tempo, o controle adversarial:

```text
'sim' + receipt sticky
```

continuou bloqueando corretamente `CONFIRM_DELETE_ITEM`.

Conclusão:

```text
receipt sticky em si NÃO é o defeito
```

O defeito é o gate por função inteira no pré-fluxo. A função é mista e possui
ramo que aumenta/confirma autoridade e ramo que reduz/cancela autoridade.

FIRST RED do desenho V2.5 para esta família:

```text
etapa_prefluxo_operacional_candidata()
```

quando ela suprime integralmente
`processar_resposta_pendencia_prioritaria()` antes de o helper poder produzir
`CANCEL_DELETE_ITEM`.

## 49.2 Feedback proativo — segunda reprodução da mesma classe

Caso:

```text
nao abre o opera
```

Precondições:

```text
sticky=True
classificar_confirmacao_local -> None
classificar_confirmacao_contextual -> False
```

Handler real:

```text
rota='feedback_pendente'
_rotina_sugestao_pendente=None
feedback=[{'aceito': False}]
```

V2.5 exato:

```text
tratado=False
pendente_permanece=True
```

Resultado:

```text
RED: gate sticky impediu rejeição/limpeza da sugestão antiga
```

O killer não relacionado continuou sem ser sequestrado como feedback.

Portanto há duas reproduções independentes da mesma falha arquitetural:

```text
função mista + veto por nome da função = revogação perdida
```

## 49.3 Regra monotônica refinada e agora sustentada em runtime

A regra correta não é:

```text
VETADO -> nenhuma continuidade
```

É:

```text
VETADO -> cria autoridade                 PROIBIDO
VETADO -> restaura/reutiliza autoridade   PROIBIDO
VETADO -> confirma ação antiga            PROIBIDO
VETADO -> cancela/revoga ação antiga      PERMITIDO
VETADO -> limpa sugestão/pendência         PERMITIDO
VETADO -> proteção/conversa sem autoridade PERMITIDO
```

Nova regra soberana:

> Veto monotônico é monotônico no eixo de AUTORIDADE, não no eixo de qualquer
> mutação de estado. Transições estritamente redutoras precisam continuar
> alcançáveis.

## 49.4 `nao.txt` — falha end-to-end independente também reproduzida

O 4.29 fechou a lacuna que o V2.5 GREEN anterior não cobria.

Entrada:

```text
cria arquivo nao.txt
```

Candidato:

```text
veto=False
auth=True
texto_operacional='cria arquivo nao txt'
```

Roteador REAL sobre `texto_operacional`:

```text
CREATE_FILE alvo='nao txt'
```

Roteador REAL sobre RAW original:

```text
CREATE_FILE alvo='nao.txt'
```

Logo:

```text
basename preservado até roteador = FAIL
```

### FIRST semantic-loss boundary desta família

`porteiro_acoes.normalizar_texto()` faz:

```text
re.sub(r"[^\w\s?]", " ", ...)
```

portanto:

```text
nao.txt -> nao txt
```

`modalidade_turno._classificar_modalidade_turno_composta_base()` segmenta o
texto já normalizado e monta `texto_operacional` pela concatenação dos textos
dos segmentos. O ponto já foi perdido antes do roteador.

O roteador possui a função canônica
`limpar_nome_arquivo_natural()` / `_restaurar_extensao_falada()`, cuja própria
documentação diz que recupera extensões comuns que perderam o ponto durante a
normalização.

Porém em `extrair_criacao_arquivo()`:

- o ramo COMPOSTO chama `limpar_nome_arquivo_natural(nome)`;
- o ramo SIMPLES faz apenas `str(...).strip(...)` e não chama o helper.

Assim:

```text
RAW nao.txt -> funciona porque o ponto nunca foi perdido
OP  nao txt -> falha porque o ramo simples não restaura a extensão
```

Esta é uma segunda família independente do problema de revogação.

## 49.5 Interpretação correta do EXIT final do harness

O output final mostrou:

```text
EXIT 2 — INVARIANTE CRÍTICA ADICIONAL FALHOU
nao.txt não chegou ao roteador real como nao.txt
```

Isso acontece porque o harness verifica `falhas` antes da lista `reds` no
footer.

Não interpretar isso como se a revogação tivesse deixado de ser RED. Durante a
mesma execução, com todos os controles PASS, foram observados explicitamente:

```text
V2.5 suprime CANCEL_DELETE_ITEM ........ SIM
V2.5 suprime revogação de feedback ..... SIM
```

Portanto o 4.29 sustentou **dois diagnósticos independentes**:

```text
A) gate de continuidade amplo demais -> revogação bloqueada
B) payload de nome de arquivo -> extensão perdida no caminho operacional
```

## 49.6 Status soberano após 4.29

```text
produção ................................ INTACTA
V2.5 GREEN antigo ....................... LEGÍTIMO PARA MATRIZ ANTIGA
4.29 .................................... EXIT 2 AUTORITATIVO
receipt sticky .......................... CONTINUA VÁLIDO
monotonicidade de autoridade ............ SUSTENTADA
revogação sob veto ...................... DEVE SER PERMITIDA
function-level preflow gate ............. FALSIFICADO
CANCEL_DELETE_ITEM sob sticky ........... BLOQUEADO INDEVIDAMENTE / PROVADO
feedback negativo sob sticky ............ BLOQUEADO INDEVIDAMENTE / PROVADO
killer não relacionado .................. NÃO SEQUESTRADO
nao.txt auth/veto ....................... CORRETO
nao.txt semantic payload E2E ............ FALHOU
patch de produção ....................... BLOQUEADO
V2.5.1 .................................. AINDA NÃO CRIADO
```

## 49.7 Próximo passo correto

Não criar V2.5.1 imediatamente.

Estudar duas correções mínimas separadamente:

### Eixo A — direção de autoridade

Para helpers mistos, decidir pelo efeito/transição:

```text
CONFIRM / executar / reutilizar -> bloquear sob sticky
CANCEL / rejeitar / limpar      -> permitir sob sticky
```

Atenção: `processar_resposta_pendencia_prioritaria` chama executor contextual
internamente, enquanto feedback pode limpar estado diretamente. O mecanismo
mínimo pode ser diferente por boundary; não inventar abstração comum antes de
estudar todos os ramos reais.

### Eixo B — basename semântico

Estudar o menor ponto canônico para restaurar extensão perdida. A fonte sugere
fortemente o ramo simples de `extrair_criacao_arquivo()`, pois o módulo
`nome_natural.py` já foi criado exatamente para recuperar extensões faladas que
perderam o ponto e o ramo composto já usa o helper.

Antes de patch, falsificar positivos/negativos de extensão para provar que a
restauração não altera nomes legítimos nem conteúdo.


---

# 50. LAB V2.5.1-A CRIADO — DIREÇÃO DE AUTORIDADE / REVOGAÇÃO

Data local: 21/08/2026, aproximadamente 01:10 -03:00.

Artefato:

```text
falsificacao_candidato_v2_5_1A_direcao_autoridade_revogacao_LAB.py
```

SHA-256:

```text
cad96dced9d779a594dec8d5aef5bc9d64b24c031b76bbd429ebed7cddb5081f
```

Tamanho:

```text
409 linhas
34165 bytes
py_compile PASS
AST PASS
```

## 50.1 Escopo

Somente eixo A: direção de autoridade/revogação sob receipt sticky. Filename / `nao.txt`
fica reservado ao V2.5.1-B.

Baseline obrigatório:

```text
falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py
SHA256 3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef
```

## 50.2 Regra candidata

```text
VETADO -> CONFIRMAR / EXECUTAR / REUTILIZAR    PROIBIDO
VETADO -> CANCELAR / REJEITAR / LIMPAR         PERMITIDO
VETADO -> CONVERSA SEM AUTORIDADE               PERMITIDO
```

Revogar não remove o receipt; o turno continua `veto=True`.

## 50.3 Contraste causal

O LAB exige reproduzir primeiro, com o V2.5 exato, os REDs conhecidos do 4.29:

```text
DELETE sticky -> CANCEL_DELETE_ITEM não nasce
feedback sticky -> sugestão antiga continua pendente
```

Se isso não ocorrer, EXIT 1 por premissa inválida.

## 50.4 DELETE

O helper real continua decidindo confirmação/cancelamento. O gate candidato atua no
ponto de execução:

```text
CANCEL_DELETE_ITEM -> permitido sob sticky
qualquer outra intent -> bloqueada sob sticky
```

Casos: cancelamento sticky, confirmação neutra positiva, confirmação sticky adversarial
e killer não relacionado.

## 50.5 Feedback

Usa `FeedbackPendenteRuntime` real. Sob sticky:

```text
classificação False -> handler real pode rejeitar/limpar
classificação True  -> bloqueia
classificação None  -> não presume resposta à pendência
```

No misto `nao e depois fecha o opera`, o prefixo revoga a sugestão e a continuação
`CLOSE_APP` não alcança executor real.

## 50.6 Música

Usa `MusicaConversacionalRuntime` real. Conversa/cobrança sem execução pode passar;
qualquer tentativa de `MUSIC_SEARCH` é interceptada antes do executor real. Se houve
tentativa de execução bloqueada, o wrapper devolve False ao pré-fluxo e não publica
uma falsa falha de execução.

## 50.7 Reparação

`processar_reparacao_conversacional()` permanece real. Sob sticky, o LAB intercepta
`executar_resultado_contextual()` antes da execução. Isso evita o falso `tratado=True`
que o helper real pode devolver mesmo quando `executar_intencao()` retorna False.

Conversa de reparação continua permitida; reparação operacional não.

## 50.8 Visão / pergunta curta

Sem ramo revogatório conhecido, continuam full-block sob sticky. Controles neutros
precisam continuar funcionando.

## 50.9 Receipt não vaza

```text
turno N: veto=True
turno N+1: fecha o opera
```

O turno N+1 deve nascer `veto=False` e autorizado. Sticky vale só no mesmo turno.

## 50.10 Auditoria estática

```text
py_compile ........ PASS
AST ............... PASS
duplicates ........ NONE
forbidden hits .... NONE
file mutations .... NONE
VEREDITO ESTÁTICO . PASS
```

O único `subprocess.run` é Git para guards. Todos os patches são in-memory e possuem
restauração em `finally`; o footer ainda verifica o wiring real.

## 50.11 Saídas

```text
EXIT 0 = V2.5.1-A GREEN no LAB
EXIT 1 = lock/wiring/baseline/precondição/harness inválido
EXIT 2 = candidato falsificado; FIRST RED manda
```

Estado:

```text
V2.5 antigo ........................ GREEN matriz antiga / rejeitado pelo 4.29
4.29 ............................... EXIT 2 autoritativo
V2.5.1-A estático .................. PASS
V2.5.1-A runtime ................... NÃO EXECUTADO
produção ........................... INTACTA
V2.5.1-B ........................... NÃO CRIADO
patch produção ..................... BLOQUEADO
```


---

# 51. V2.5.1-A — RUNTIME GREEN REPORTADO + SEGUNDA REVISÃO INTEGRAL

Data local: 21/08/2026, aproximadamente 05:09 -03:00.

Pedro informou que:

```text
falsificacao_candidato_v2_5_1A_direcao_autoridade_revogacao_LAB.py
```

**passou**. Como o LAB só possui GREEN com `EXIT 0`, o estado de trabalho passa a ser:

```text
V2.5.1-A runtime LAB ........ GREEN reportado por Pedro
```

O stdout integral não foi colado nesta mensagem, portanto não inventar detalhes de linhas
individuais além do fato reportado de que o teste passou.

## 51.1 Segunda revisão integral obrigatória

A revisão pós-GREEN reabriu exatamente os boundaries do candidato:

- DELETE pendente;
- executor curto contextual;
- roteador principal de intenção;
- executor de integrações;
- executor de arquivos;
- porta tipada de mutações;
- feedback misto;
- música;
- reparação;
- visão;
- pergunta curta.

### Achado principal

O A GREEN original prova com helper real que `CANCEL_DELETE_ITEM` é produzido e que o
wrapper direcional o permite, mas a ponta usada pelo LAB era um recorder de
`_executar_intencao_curta_contextual`.

Isso significa:

```text
A GREEN = prova runtime real até o boundary do executor curto
```

mas ainda não prova, por execução, a cadeia completa downstream do cancelamento.

## 51.2 Fonte downstream estudada

A cadeia real foi confirmada por fonte travada:

```text
processar_resposta_pendencia_prioritaria
 -> RespostaConversacionalRuntime.executar_intencao_curta
 -> roteador_intencao.executar_intencao
 -> executor_integracoes._executar_arquivos
 -> execucao_arquivos.executar_intencao_arquivos
 -> RegistroArquivosMutacao.cancelar_exclusao
 -> serviço de mutação / lixeira
```

`RespostaConversacionalRuntime.executar_intencao_curta()` não consulta
`autoriza_execucao`; encaminha a intent ao executor e retorna o resultado real.

`roteador_intencao.executar_intencao()` despacha `CANCEL_DELETE_ITEM` por
`executor_integracoes`.

`executor_integracoes.INTENCOES_ARQUIVOS` contém explicitamente:

```text
CONFIRM_DELETE_ITEM
CANCEL_DELETE_ITEM
```

O executor real de arquivos distingue os dois caminhos:

```text
CANCEL_DELETE_ITEM
 -> arquivos_mutacao.cancelar_exclusao()
 -> status exclusao_cancelada
 -> executou=False
 -> confirmado=True

CONFIRM_DELETE_ITEM
 -> arquivos_mutacao.confirmar_exclusao()
 -> pode realizar a mutação destrutiva/reversível
```

Não há gate por `autoriza_execucao` dentro do ramo de cancelamento.

`LixeiraLaylay.cancelar_pendente()` apenas conclui a pendência com status `cancelada`;
não move arquivo e não altera conteúdo físico.

Conclusão da revisão de fonte:

```text
CANCEL é estritamente redutor de autoridade
CONFIRM é o ramo que pode aplicar o efeito físico
```

A regra direcional do A continua causalmente coerente.

## 51.3 Lacuna residual e teste 4.30

Como a regra soberana não permite chamar um recorder de “runtime real downstream”, foi
criado um pós-GREEN estreito:

```text
pos_green_v2_5_1A_cancelamento_integracao_teste4_30.py
```

SHA-256:

```text
49b0500e46740b132a1ad94954988b28d66a507cfd3f282908a4257cf787f799
```

Stats:

```text
182 linhas
11314 bytes
py_compile PASS
AST PASS
duplicates NONE
forbidden physical hits NONE
file mutations NONE
```

O teste atravessa componentes reais até a porta tipada de mutação, que é substituída
por um serviço IN-MEMORY sem disco:

```text
helper pendente REAL
 -> executor curto REAL
 -> roteador de intenção REAL
 -> executor de integrações REAL
 -> executor de arquivos REAL
 -> RegistroArquivosMutacao REAL
 -> MutacaoMemoria recorder
```

Matriz:

```text
sticky + "nao apaga o arquivo"
 -> CANCEL_DELETE_ITEM
 -> porta.cancelar_exclusao = 1
 -> porta.confirmar_exclusao = 0

sticky + "sim"
 -> CONFIRM_DELETE_ITEM bloqueado pelo candidato A
 -> zero chamadas à porta

NEUTRO + "sim"
 -> mesma cadeia real
 -> porta.confirmar_exclusao = 1
```

Nenhuma lixeira física, arquivo, rede, app, volume ou LLM é usado.

Saídas:

```text
EXIT 0 = confirmação component-integration GREEN
EXIT 1 = lock/wiring/premissa inválida
EXIT 2 = A falsificado na fronteira downstream
```

## 51.4 Estado após segunda revisão

```text
V2.5.1-A LAB runtime ................. GREEN reportado
segunda revisão de fonte ............. PASS com lacuna downstream identificada
4.30 estático ........................ PASS
4.30 runtime ......................... NÃO EXECUTADO
produção ............................. INTACTA
V2.5.1-B ............................. AINDA NÃO CRIADO
patch produção ....................... BLOQUEADO
```

Próximo passo correto: executar o 4.30. Somente com o 4.30 GREEN fechar formalmente
o eixo A e avançar ao V2.5.1-B.


---

# 52. TESTE 4.30 EXECUTADO — EIXO A FORMALMENTE FECHADO

Data local: 21/08/2026, aproximadamente 05:29 -03:00.

Pedro executou:

```text
pos_green_v2_5_1A_cancelamento_integracao_teste4_30.py
```

com todos os guards, blobs e artefatos exatos PASS.

Resultado:

```text
🟢 EXIT 0 — PÓS-GREEN V2.5.1-A / TESTE 4.30 GREEN
```

## 52.1 Evidência decisiva

### Sticky + cancelamento

```text
rota='cancelamento_exclusao'
tratado=True
cancel=1
confirm=0
outras=[]
```

Logo:

```text
CANCEL_DELETE_ITEM
```

atravessou:

```text
helper pendente real
 -> executor curto real
 -> roteador real
 -> executor de integrações real
 -> executor de arquivos real
 -> RegistroArquivosMutacao real
 -> porta tipada in-memory
```

### Sticky + confirmação

```text
rota='confirmacao_exclusao'
tratado=False
cancel=0
confirm=0
blocks=[CONFIRM_DELETE_ITEM]
```

A confirmação foi bloqueada antes da porta tipada.

### Controle neutro

```text
rota='confirmacao_exclusao'
tratado=True
cancel=0
confirm=1
```

A mesma cadeia real continuou funcionando quando não havia veto.

## 52.2 Conclusão soberana do eixo A

O princípio está agora sustentado por fonte + LAB + pós-GREEN component-integration:

```text
VETADO -> CANCELAR / REVOGAR / LIMPAR       PERMITIDO
VETADO -> CONFIRMAR / EXECUTAR / REUTILIZAR PROIBIDO
```

E o receipt permanece sticky durante a revogação; não há transição VETADO -> NEUTRO.

Status:

```text
V2.5.1-A LAB runtime ................. GREEN
segunda revisão integral ............ PASS
4.30 component-integration .......... GREEN
EIXO A .............................. FORMALMENTE FECHADO
produção ............................ INTACTA
patch produção ...................... AINDA BLOQUEADO
V2.5.1-B ............................ PRÓXIMO EIXO
```

Próximo passo correto: iniciar V2.5.1-B — literalidade de filename / `nao.txt`, sem
misturar as mudanças do eixo A.


---

# 53. V2.5.1-B CRIADO — LITERALIDADE DE FILENAME / `nao.txt`

Data local: 21/08/2026, aproximadamente 05:45 -03:00.

Artefato:

```text
falsificacao_candidato_v2_5_1B_literalidade_filename_LAB.py
```

SHA-256 congelado:

```text
1945541d99345ef36462940d18fb686b989c04920a88c70194855c7688596844
```

Stats:

```text
528 linhas
30830 bytes
py_compile PASS
AST PASS
duplicates NONE
forbidden effects NONE
file mutations NONE
```

## 53.1 Root do eixo B fechado por fonte

O caminho real mantém dois textos distintos:

```text
RAW do usuário
  -> preservado como texto_original para execução/auditoria

texto_operacional
  -> normalizado pela modalidade
  -> `nao.txt` vira `nao txt`
  -> este é o texto entregue ao resolvedor
```

Em `pre_fluxo_contextual.processar_comando_deterministico_precoce`:

```text
deteccao = turno.texto_operacional
processar_comando_deterministico(deteccao, origem, RAW)
```

Em `CoordenadorIntencaoRuntime.processar_deterministico`, o RAW segue como
`texto_original`, mas `executar_fluxo_intencao()` chama:

```text
resolvedor(texto_operacional, origem, ctx)
```

O RAW só volta em:

```text
texto_execucao = texto_original
```

Portanto o resolvedor atual realmente pode receber `nao txt` e perder a
literalidade antes do roteador de arquivos. O RED 4.29 não era artefato de
boundary direto.

## 53.2 Fonte canônica de extensões

`nome_natural.py` define:

```text
.txt .md .markdown .log .csv .json .yaml .yml
.py .js .ts .html .css
```

A função `limpar_nome_arquivo_natural()` já possui restauração de extensão falada.

O V2.5 tinha uma lista privada `FILE_ATOM_RE` sem `.markdown`. O B elimina esse
drift no candidato: sua regex de átomo é derivada da lista CANÔNICA da produção.

## 53.3 Segundo drift de autoridade encontrado

O V2.5 só aceitava o átomo literal se o prefixo terminasse em:

```text
arquivo|documento
```

Mas o parser real aceita também:

```text
arquivo de texto
arquivo de txt
```

Logo:

```text
cria arquivo de texto nao.txt
```

podia ser falsamente vetado antes do roteador.

O B amplia SOMENTE o slot literal comprovado:

```text
arquivo|documento
  + opcional `de texto|de txt`
  + opcional `chamado|chamada|com nome|de nome`
  + opcional aspas de abertura
  + nao.<ext suportada>
```

Não existe isenção genérica de frase.

## 53.4 Política conservadora de STT

O B deliberadamente NÃO converte:

```text
cria arquivo nao txt
cria arquivo chamado nao txt
```

em `nao.txt`.

Sem ponto literal no RAW, o caso continua:

```text
VETADO / fail-closed
```

Mesmo que `limpar_nome_arquivo_natural()` saiba restaurar extensões faladas em
outros contextos. A restauração lexical do roteador não ganha autoridade para
reclassificar uma negação ambígua.

`.exe` também não recebe exceção, pois não pertence ao contrato textual canônico.

## 53.5 Reconciliação OP/RAW

RAW nunca substitui o contrato inteiro.

Um campo só é copiado do resultado RAW para o resultado OP quando TODAS as
condições passam:

```text
1. turno autorizado e sem sticky veto
2. OP e RAW retornam mesmo intent canônico de arquivo
3. texto OP e RAW normalizam para a mesma fala inteira
4. campo pertence à allowlist daquele intent
5. valor RAW possui extensão suportada pela produção
6. basename pontuado aparece literalmente no RAW
7. valor OP e valor RAW normalizam iguais
```

Allowlist:

```text
CREATE_FILE     -> alvo
CREATE_FOLDER   -> arquivo_nome
FILE_SEARCH     -> query, alvo
DELETE_ITEM     -> alvo
FILE_TRANSACTION-> origem
```

Nunca são copiados do RAW:

```text
conteudo
destino
pasta
nome da pasta
modo
tipo_arquivo
intent
qualquer campo fora da allowlist
```

## 53.6 Matriz funcional

Casos positivos cobertos:

```text
cria arquivo nao.txt
cria arquivo de texto nao.txt
cria arquivo chamado não.md
cria arquivo chamado "nao.txt"
cria arquivo nao.markdown
cria arquivo nao.txt contendo teste
cria pasta teste e dentro dela arquivo nao.txt
escreve ola dentro do arquivo nao.txt
abre arquivo nao.txt
apaga arquivo nao.txt
move arquivo nao.txt para pasta teste
procura arquivo nao.txt
```

O alvo final deve preservar a extensão literal correta, sem `.txt.txt`.

## 53.7 Killers / falsificações

O B precisa continuar bloqueando:

```text
cria arquivo nao.exe
cria arquivo nao txt
cria arquivo chamado nao txt
cria arquivo nao.txt contendo nao aumenta o volume
cria arquivo nao.markdown e nao fecha o opera
```

E possui falsificações adversariais de merge:

```text
intent OP != intent RAW                  -> sem merge
fala inteira OP != RAW após normalizar   -> sem merge
alvo não equivalente                     -> sem merge
extensão não suportada                   -> sem merge
sem basename pontuado literal no RAW     -> sem merge
conteúdo RAW diferente                   -> conteúdo NÃO copiado
destino RAW diferente                    -> destino NÃO copiado
nome da pasta RAW diferente              -> nome da pasta NÃO copiado
```

## 53.8 Integração do LAB

O B usa `executar_fluxo_intencao()` REAL com executor final in-memory recorder.

A cadeia testada é:

```text
turno candidato autorizado
 -> texto_operacional
 -> resolvedor B com roteador_arquivos REAL em OP e RAW
 -> reconciliação estreita de campo
 -> executar_fluxo_intencao REAL
 -> executor recorder
```

Para turns vetados, `executar_fluxo_intencao()` nem é chamado.

Isso é component-integration; ainda não deve ser chamado de full coordinator
runtime. Se o B vier GREEN, a segunda revisão integral decidirá se é necessário
um pós-GREEN 4.31 atravessando `CoordenadorIntencaoRuntime` real.

## 53.9 Segunda revisão estática antes do run

```text
py_compile ............ PASS
AST ................... PASS
duplicates ............ NONE
forbidden effects ..... NONE
file mutations ........ NONE
subprocess.run ........ 1 [Git guards only]

HEAD lock ......................... PASS
baseline SHA ...................... PASS
4.29 reproduction ................. PASS
production ext source ............. PASS
markdown case ..................... PASS
unsupported exe ................... PASS
STT remains closed ................ PASS
whole-text equivalence ............ PASS
intent equality ................... PASS
field allowlist ................... PASS
content never merged .............. PASS
destination never merged .......... PASS
veto before resolution ............ PASS
real flow component ............... PASS
RAW original kept ................. PASS
patch restore marker .............. PASS
patch restore regex ............... PASS
```

## 53.10 Estado

```text
EIXO A .............................. FORMALMENTE FECHADO
V2.5.1-B fonte/root ................. FECHADO
V2.5.1-B estático ................... PASS
V2.5.1-B runtime .................... NÃO EXECUTADO
produção ............................ INTACTA
integração A+B ...................... NÃO CRIADA
patch produção ...................... BLOQUEADO
```

Próximo passo: Pedro executar o B exato. EXIT 0 -> segunda revisão integral;
EXIT 1 -> INVALID; EXIT 2 -> FIRST RED controla o diagnóstico.


---

# 54. V2.5.1-B PRIMEIRO RUN — EXIT 2; ROOT SEPARADO EM `move`

Pedro executou o B original e obteve:

```text
🔴 EXIT 2 — CANDIDATO V2.5.1-B FALSIFICADO
FIRST RED: autoridade: literalidade estreita ou fail-closed STT divergiu
```

O único FIRST RED concreto foi:

```text
move arquivo nao.txt para pasta teste
veto=False
auth=False
```

Todos os outros positivos de literalidade passaram; os killers, `.markdown`, aspas,
`arquivo de texto`, merge estreito, proteção de conteúdo/destino, STT fail-closed e
`executar_fluxo_intencao` real também passaram.

## 54.1 Diagnóstico causal

O `veto=False` prova que o átomo `nao.txt` foi aceito pelo candidato B.

O `auth=False` aparece antes de qualquer roteamento/reconciliação. Logo a falha não é
no merge OP/RAW nem no filename.

Estudo de fonte mostrou drift histórico independente:

```text
normalizacao_linguagem._VERBOS_OPERACIONAIS -> contém move/mover
modalidade/analisar_protecao_operacional -> negação conhece move/mova
preparar_entrada_deterministica -> comando direto conhece move/mova/mover
roteador de arquivos -> reconhece FILE_TRANSACTION
```

mas a modalidade positiva baseline não promove a frase `move ...` para
autoridade prática no runtime observado.

Classificação:

```text
side-bug pré-B: autoridade positiva de `move`
```

Ele NÃO deve ser corrigido dentro do V2.5.1-B, porque isso misturaria dois roots e
ampliaria autoridade só para fazer o teste passar.

## 54.2 REV2

Artefato:

```text
falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV2.py
```

SHA-256:

```text
8ee8d58a045a8c5d5dc581c7429cadcc15602edcac58b99f3d4422b4acd47d70
```

Stats:

```text
576 linhas
33731 bytes
py_compile PASS
AST PASS
duplicates NONE
forbidden effects NONE
file mutations NONE
```

### Mudança soberana

REV2 NÃO dá autoridade a `move`.

Remove `move ...` da matriz positiva end-to-end do eixo B e cria uma fase diagnóstica
que exige:

```text
move arquivo teste.txt para pasta teste
 -> baseline veto=False / auth=False

move arquivo nao.txt para pasta teste
 -> B veto=False / auth=False

roteador direto
 -> FILE_TRANSACTION
```

Se essa premissa divergir, EXIT 1; não se dá crédito ao B.

### FILE_TRANSACTION ainda é testado

A literalidade do move é testada somente no boundary component-level do parser real +
merge estreito:

```text
OP  : move arquivo nao txt para pasta teste
RAW : move arquivo nao.txt para pasta teste

router(OP)  -> FILE_TRANSACTION origem='nao txt'
router(RAW) -> FILE_TRANSACTION origem='nao.txt'
merge       -> origem='nao.txt'
```

Exigências:

```text
somente `origem` pode ser copiado
destino permanece exatamente o OP
auth do turno move continua False
nenhum executor físico é chamado
```

Assim o eixo B prova seu contrato de filename para FILE_TRANSACTION sem fabricar
reachability que a produção atual não possui.

## 54.3 Estado

```text
B original runtime ................ EXIT 2 autoritativo
FIRST RED .......................... side-bug `move` anterior ao B
estratégia de literalidade ......... preservada pelos demais testes
REV2 estático ...................... PASS
REV2 runtime ....................... NÃO EXECUTADO
produção ........................... INTACTA
side-bug `move` .................... documentado / separado
patch produção ..................... BLOQUEADO
```

Próximo passo: executar a REV2 exata. EXIT 0 -> segunda revisão integral do B;
EXIT 1 -> INVALID; EXIT 2 -> FIRST RED manda novamente.


---

# 55. V2.5.1-B REV2 EXECUTADO — EXIT 2 POR FALHA DO HARNESS EM FILE_TRANSACTION

Pedro executou a REV2 e obteve:

```text
🔴 EXIT 2 — CANDIDATO V2.5.1-B FALSIFICADO
FIRST RED: FILE_TRANSACTION: parser/merge literal divergiu no side-bug `move`
```

Todos os guards/locks PASS. Portanto foi uma execução válida, mas a segunda análise do
FIRST RED mostrou que a expectativa do harness estava errada.

## 55.1 Evidência runtime decisiva

A REV2 imprimiu:

```text
FILE_TRANSACTION OP   -> origem='nao.txt'
FILE_TRANSACTION RAW  -> origem='nao.txt'
FILE_TRANSACTION merge-> origem='nao.txt' campos=[]
```

A REV2 esperava incorretamente:

```text
OP origem='nao txt'
merge campos=['origem']
```

Logo o roteador real já havia preservado/canonicalizado o filename ANTES do merge.

## 55.2 Fonte real confirma

`roteador_arquivos._limpar_item_movimentacao()` faz para a origem:

```text
remove moldura arquivo/documento/item
 -> limpar_nome_arquivo_natural(texto)
```

E `limpar_nome_arquivo_natural()` chama `_restaurar_extensao_falada()`, cujo contrato é
explicitamente recuperar extensões textuais conhecidas que perderam o ponto durante a
normalização do turno, sem autorizar mutação.

Portanto:

```text
move arquivo nao txt para pasta teste
 -> parser FILE_TRANSACTION já produz origem='nao.txt'
```

Isto é comportamento correto e anterior ao reconciliador B.

## 55.3 Reclassificação correta do EXIT 2

O EXIT 2 da REV2 é válido como execução do harness, porém o FIRST RED falsificou a
**expectativa do harness**, não o candidato de literalidade.

Regra soberana aplicada:

```text
harness também precisa ser falsificado antes de ganhar autoridade
```

Não reclassificar o processo como INVALID; o processo rodou e encontrou uma condição
real. O erro estava na asserção causal da REV2.

## 55.4 REV3

Artefato:

```text
falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV3.py
```

SHA-256:

```text
29bb93a77197156f41898806bfb7c30b0f295e9759524f3b0cc159d622825bab
```

Stats:

```text
580 linhas
34069 bytes
py_compile PASS
AST PASS
duplicates NONE
forbidden effects NONE
file mutations NONE
```

Mudança única na fronteira `move`:

```text
FILE_TRANSACTION OP já canonicaliza origem='nao.txt'
FILE_TRANSACTION RAW também origem='nao.txt'
reconciliador B deve ser NO-OP -> campos=[]
destino permanece OP
turno move continua auth=False / veto=False
```

A capacidade do reconciliador de restaurar `origem` quando OP/RAW realmente divergem
continua testada separadamente na falsificação manual de `FILE_TRANSACTION`, que exige
`fields=['origem']` e garante que destino RAW não seja copiado.

## 55.5 Estado

```text
B original runtime ................. EXIT 2 / side-bug move anterior ao B
B REV2 runtime ..................... EXIT 2 / expectativa de harness falsificada
root FILE_TRANSACTION .............. parser já canonicaliza no OP
estratégia B ....................... permanece sustentada
REV3 estático ...................... PASS
REV3 runtime ....................... NÃO EXECUTADO
produção ........................... INTACTA
patch produção ..................... BLOQUEADO
```

Próximo passo: executar REV3 exata. EXIT 0 -> segunda revisão integral do B;
EXIT 1 -> INVALID; EXIT 2 -> FIRST RED manda novamente.


---

# 56. V2.5.1-B REV3 EXECUTADO GREEN + SEGUNDA REVISÃO INTEGRAL

Pedro executou:

```text
falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV3.py
```

com todos os guards/locks PASS e obteve:

```text
🟢 EXIT 0 — CANDIDATO LAB V2.5.1-B REV3 GREEN
```

Evidências relevantes do run:

```text
RED 4.29 basename reproduzido ................ PASS
side-bug `move` isolado ....................... PASS
literal txt/md/markdown/aspas ................. PASS
STT sem ponto ambíguo ......................... PASS fail-closed
.exe não suportado ............................ PASS fail-closed
boundary conteúdo/segundo ato negativo ........ PASS fail-closed
FILE_TRANSACTION parser canonical ............. PASS / merge NO-OP
falsificações de merge ........................ PASS
executar_fluxo_intencao REAL .................. PASS
baseline restaurado final ..................... PASS
```

## 56.1 Segunda revisão integral do B

A revisão reabriu o caminho real acima e abaixo de `executar_fluxo_intencao()`.

Achado principal: o coordenador possui uma lógica `preservar_argumentos_arquivo`, mas
ela recebe o argumento `texto` do resolvedor. No caminho do pré-fluxo esse argumento é
o `texto_operacional`, não o RAW original.

Fonte real:

```text
processar_comando_deterministico_precoce:
  operacional = turno.texto_operacional
  deteccao = operacional se ato_principal == comando
  processar_comando_deterministico(deteccao, origem, texto_usuario_RAW)
```

Depois:

```text
CicloComandosRuntime.processar_deterministico(
    texto=OP,
    texto_original=RAW,
)
 -> executar_fluxo_intencao(texto=OP, texto_original=RAW,
                            resolver_cb=self._resolver_decisao_canonica)
```

E `executar_fluxo_intencao()` chama:

```text
intent, rota = resolvedor(texto_OP, origem, ctx)
```

O RAW só volta depois como:

```text
texto_execucao = texto_original_RAW
```

Logo a regra `preservar_argumentos_arquivo` dentro de `resolver_intencao()` não pode
recuperar um ponto que já desapareceu se o resolvedor recebeu OP.

## 56.2 Consequência arquitetural

O B está semanticamente coerente, mas sua reconciliação precisa ser provada no
boundary real do coordenador. Não basta o helper isolado receber OP+RAW manualmente.

O integration point mínimo apontado pela fonte é:

```text
CicloComandosRuntime.processar_deterministico
```

que já recebe os dois valores:

```text
texto          = OP
texto_original = RAW
```

Sem alterar a assinatura pública, ele pode fornecer ao resolvedor uma closure estreita
que executa a resolução canônica sobre OP e usa RAW somente para reconciliar campos de
filename já equivalentes.

Ainda NÃO é patch de produção; isso é hipótese de integração a falsificar.

## 56.3 Pós-GREEN 4.31 criado

Artefato:

```text
pos_green_v2_5_1B_coordenador_op_raw_teste4_31.py
```

SHA-256:

```text
a6563ffd5a922d121f5f5354634c79c1964900b4af43ac9b7a942304f4c0ed1c
```

Stats:

```text
291 linhas
14750 bytes
py_compile PASS
AST PASS
duplicates NONE
forbidden effects NONE
file mutations NONE
```

Atravessa:

```text
processar_comando_deterministico_precoce REAL
 -> CicloComandosRuntime.processar_deterministico REAL
 -> executar_fluxo_intencao REAL
 -> _resolver_decisao_canonica REAL
 -> resolver_intencao REAL
 -> arbitro REAL
 -> detectar_intencao_arquivos REAL como habilidade determinística focal
 -> CicloComandosRuntime.executar_intencao REAL
 -> roteador físico substituído por recorder in-memory
```

Não chamar isto de full detector graph: a habilidade determinística focal é o roteador
de arquivos real injetado diretamente. O objetivo é provar o boundary OP/RAW do
coordenador, não retestar todos os especialistas.

## 56.4 Matriz 4.31

Primeiro o baseline precisa reproduzir no caminho real:

```text
RAW: cria arquivo nao.txt
OP : cria arquivo nao txt
resolvedor/detector recebe OP
executor recorder recebe CREATE_FILE alvo='nao txt'
texto de execução continua RAW='cria arquivo nao.txt'
```

Se isso não ocorrer, EXIT 1 por premissa inválida.

Depois, com wrapper candidato somente in-memory sobre `_resolver_decisao_canonica`:

```text
cria arquivo nao.txt               -> alvo nao.txt
cria arquivo de texto nao.txt      -> alvo nao.txt
cria arquivo chamado "nao.txt"     -> alvo nao.txt
cria arquivo nao.markdown          -> alvo nao.markdown
cria arquivo relatorio.md          -> alvo relatorio.md
```

Killers devem parar antes do detector:

```text
cria arquivo nao txt
cria arquivo chamado nao txt
cria arquivo nao.exe
cria arquivo nao.txt contendo nao aumenta o volume
cria arquivo nao.markdown e nao fecha o opera
```

O módulo `coordenador_intencao.executar_intencao` é monkeypatched para recorder e
restaurado em `finally`; zero efeitos físicos.

## 56.5 Estado

```text
EIXO A .............................. FORMALMENTE FECHADO
B original ......................... EXIT 2 / side-bug move
B REV2 ............................. EXIT 2 / harness expectation falsified
B REV3 LAB ......................... GREEN
segunda revisão B .................. PASS com lacuna coordinator-boundary identificada
4.31 estático ...................... PASS
4.31 runtime ....................... NÃO EXECUTADO
produção ........................... INTACTA
integração A+B ..................... BLOQUEADA até 4.31
patch produção ..................... BLOQUEADO
```

Próximo passo: executar 4.31 exato. EXIT 0 fecha formalmente o eixo B até o boundary
coordenador; EXIT 1 é INVALID; EXIT 2 tem FIRST RED soberano.


---

# 57. TESTE 4.31 EXECUTADO GREEN — EIXO B FORMALMENTE FECHADO

Pedro executou:

```text
pos_green_v2_5_1B_coordenador_op_raw_teste4_31.py
```

com todos os guards/locks PASS e obteve:

```text
🟢 EXIT 0 — PÓS-GREEN V2.5.1-B / TESTE 4.31 GREEN
```

Evidência runtime:

```text
baseline full coordinator:
  OP='cria arquivo nao txt'
  detector recebeu OP
  executor recebeu CREATE_FILE alvo='nao txt'
  texto de execução permaneceu RAW='cria arquivo nao.txt'
  RED reproduzido

REV3 no mesmo boundary:
  cria arquivo nao.txt              -> alvo='nao.txt' PASS
  cria arquivo de texto nao.txt     -> alvo='nao.txt' PASS
  cria arquivo chamado "nao.txt"    -> alvo='nao.txt' PASS
  cria arquivo nao.markdown         -> alvo='nao.markdown' PASS
  cria arquivo relatorio.md         -> alvo='relatorio.md' PASS

killers:
  detector=[]
  executor=[]
```

Conclusão:

```text
EIXO B .............................. FORMALMENTE FECHADO
```

A literalidade foi restaurada somente no campo filename autorizado usando o RAW já
presente no boundary do coordenador. RAW não ganhou autoridade e não furou sticky.

---

# 58. ESTUDO DE INTEGRAÇÃO A+B E LAB V2.5.1 INTEGRADO CRIADO

Artefato:

```text
falsificacao_candidato_final_turno229_LAB_V2_5_1_INTEGRADO.py
```

SHA-256:

```text
91ac594e3df53014d98d03bf4c8b8ebcd6dbad163262afcbf7b44f428a51b64b
```

Stats:

```text
533 linhas
32722 bytes
py_compile PASS
AST PASS
duplicates NONE
forbidden effects NONE
file mutations NONE
```

## 58.1 Ordem real estudada

`RespostaIARuntime._processar_serializado()` chama:

```text
processar_comandos_prioritarios(texto)
        ↓
processar_inicio_fluxo(contexto_inicio, texto)
```

Logo prioridades rodam ANTES do pré-fluxo A.

## 58.2 Arquivos prioritários usam RAW

`ComandosImediatosRuntime.processar_prioritarios()` chama:

```text
detectar_intencao_arquivos(texto_RAW, ...)
```

para operações prioritárias de arquivo. Portanto:

```text
FILE_SEARCH
FILE_READ
FILE_OPEN_RESULT
RESTORE_DELETED_ITEM
CREATE_FILE editar_existente=True
```

podem preservar `nao.txt` diretamente sem o merge B.

O B é necessário nas rotas que seguem pelo coordenador, como CREATE_FILE simples.

## 58.3 Nova fronteira cross-axis: read-only prioritário

`_candidato_arquivo_prioritario_autorizado()` retorna True para intents somente leitura
independentemente de `autoriza_execucao`.

Portanto um turno sticky precisa dominar também esta exceção. O integrado modela:

```text
if receipt sticky:
    prioridade arquivo/live = False
else:
    delega ao autorizador real
```

O LAB exige primeiro reproduzir o bypass baseline com FILE_SEARCH read-only sob sticky.

Também cobre o helper prioritário geral (`IOT_STATUS`) pela mesma regra.

## 58.4 Ordem soberana no coordenador

No 4.31 isolado, o wrapper B chamava o resolver real e depois checava sticky/effective
auth. Para a integração isso não é suficiente contra um contrato stale:

```text
veto=True
+ autoriza_execucao=True stale
```

O integrado muda a ordem:

```text
resolver_integrado(OP, RAW)
  ↓
resolver_intencao_candidato do V2.5/A
  ↓  [sticky bloqueia AQUI, antes de detector/árbitro]
resolver real(OP)
  ↓
se auth efetiva=False -> conserva resultado, sem merge B
  ↓
se auth efetiva=True -> B pode reconciliar filename OP↔RAW
```

Assim B nunca ganha oportunidade de restaurar conteúdo ou autoridade num turno vetado.

## 58.5 A direcional permanece soberano

O integrado usa o A exato:

```text
falsificacao_candidato_v2_5_1A_direcao_autoridade_revogacao_LAB.py
SHA cad96dced9d779a594dec8d5aef5bc9d64b24c031b76bbd429ebed7cddb5081f
```

com `prefluxo_dir()`.

Cross-test principal:

```text
pendência delete antiga
+ turno "nao apaga o arquivo nao.txt"
+ sticky receipt
-> CANCEL_DELETE_ITEM deve passar
-> receipt continua true
```

Contraste:

```text
sticky adversarial + "sim"
-> CONFIRM_DELETE_ITEM não passa
```

## 58.6 A não pode engolir B

Outro cross-test:

```text
pendência delete antiga
+ novo turno "cria arquivo nao.txt"
```

Esperado:

```text
pré-fluxo A não consome
nenhum CANCEL/CONFIRM nasce
coordenador B executa CREATE_FILE alvo='nao.txt' no recorder
```

Isso prova que a preservação de revogação não transforma toda pendência em dona do
turno seguinte.

## 58.7 Matriz do integrado

### Nascimento

```text
pontuado 229                       -> sticky
STT 229                            -> sticky
cria arquivo nao.txt              -> auth true / veto false
cria arquivo nao.markdown         -> auth true / veto false
cria arquivo chamado "nao.txt"    -> auth true / veto false
cria arquivo nao txt              -> sticky
cria arquivo nao.exe              -> sticky
filename + payload negativo       -> sticky
filename + segundo ato negativo   -> sticky
fresh turn                        -> não herda receipt
```

### Prioridade

```text
FILE_SEARCH baseline sob sticky -> RED reproduzido
FILE_SEARCH integrado           -> bloqueado
IOT_STATUS baseline sob sticky  -> RED reproduzido
IOT_STATUS integrado            -> bloqueado
query nao.txt positiva          -> preservada
edição nao.txt positiva         -> preservada via RAW
```

### Coordenador

```text
cria arquivo nao.txt
cria arquivo de texto nao.txt
cria arquivo chamado "nao.txt"
cria arquivo nao.markdown
cria arquivo nao.txt contendo teste
cria arquivo relatorio.md
```

Todos devem chegar ao executor recorder com filename exato.

Killers devem parar antes de detector/merge/executor.

Adversarial:

```text
veto=True + auth=True stale + nested command
-> detector=[]
-> RAW merge=[]
-> executor=[]
```

### Pré-fluxo

```text
CANCEL + filename sticky -> permitido
CONFIRM + sticky          -> bloqueado
visual neutro             -> continua vivo
visual sticky             -> bloqueado
```

### Contratos

`filtrar_comandos_candidato()` precisa zerar comando nested stale sob receipt.

### Side-bug move

Continua deliberadamente:

```text
move arquivo nao.txt para pasta teste
veto=False
auth=False
roteador=FILE_TRANSACTION origem='nao.txt'
```

O integrado NÃO corrige esse bug independente.

## 58.8 Artefatos anteriores congelados

O integrado exige por SHA:

```text
V2.5 baseline ........ 3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef
A .................... cad96dced9d779a594dec8d5aef5bc9d64b24c031b76bbd429ebed7cddb5081f
4.30 ................. 49b0500e46740b132a1ad94954988b28d66a507cfd3f282908a4257cf787f799
B REV3 ............... 29bb93a77197156f41898806bfb7c30b0f295e9759524f3b0cc159d622825bab
4.31 ................. a6563ffd5a922d121f5f5354634c79c1964900b4af43ac9b7a942304f4c0ed1c
```

## 58.9 Estado

```text
EIXO A .............................. FORMALMENTE FECHADO
EIXO B .............................. FORMALMENTE FECHADO
LAB V2.5.1 INTEGRADO estático ...... PASS
LAB V2.5.1 INTEGRADO runtime ....... NÃO EXECUTADO
produção ............................ INTACTA
patch produção ...................... BLOQUEADO
```

Próximo passo: executar o integrado exato. EXIT 0 -> segunda revisão integral final;
EXIT 1 -> INVALID; EXIT 2 -> FIRST RED soberano.

# REGRAS SOBERANAS DE INVESTIGAÇÃO — LEIA ANTES DE QUALQUER PATCH

> Continuação soberana do handoff `HANDOFF_LAYLAY_2026-08-17_ATUALIZADO_22H40_C1B2_PATCHER_V2_REANALISADO.md`.
>
> O handoff anterior permanece como **base histórica imutável**. Este arquivo não revoga o histórico anterior; ele acrescenta as regras aprendidas no turno 155, registra o estado real pós-teste 3.7 e abre formalmente C1-C/turno 156.

## 0. Regras que agora são obrigatórias

Estas regras nasceram principalmente do incidente C1-B2 no turno 155 e têm precedência sobre atalhos de investigação.

1. **Estudar antes de criar arquivo ou patch.** A ordem continua sendo: estudar → provar vermelho → localizar primeira fronteira causal → falsificar hipótese → candidato em espelho → auditoria → patch de produção → runtime real/chaos.
2. **“Runtime real” não é um nome de teste.** Só pode receber esse rótulo a prova que atravessa o mesmo caminho usado no caos. Testar funções reais em uma costura artificial é integração intermediária, mesmo que tudo importado seja produção.
3. **Um verde verdadeiro pode provar a camada errada.** Verde de detector/orquestrador não prova `entrada → turno congelado → porta pública → gates reais → ciclo canônico → árbitro → executor → publicação`.
4. **A primeira fronteira RED manda no diagnóstico.** Instrumentar as fronteiras e localizar a primeira quebra antes de alterar a camada mais barulhenta.
5. **Harness e produção são raízes diferentes.** HEAD divergente, callback sintético incorreto, fixture artificial ou runner quebrado não são evidência de defeito de produção.
6. **Nunca atualizar o lock de HEAD “só para rodar”.** Se o runner foi criado para outra baseline e recusa, a recusa é proteção correta. Primeiro reestudar a nova baseline.
7. **HEAD lock sozinho não basta para diagnóstico causal local.** Quando possível, travar também blobs dos arquivos causais e recusar mudanças locais/indexadas nesses arquivos.
8. **Contexto, referência linguística, alvo e autoridade são contratos diferentes.** Contexto pode fornecer um alvo tipado; detector pode materializar candidato; nenhum dos dois pode criar autorização de efeito.
9. **Contexto nunca aumenta autoridade.** `child_authority <= parent_authority`; nenhum detector, memória, LLM ou continuidade promove fala não autorizada a efeito por conta própria.
10. **Elipse operacional não deve contaminar a linguagem global.** Uma forma curta pode ter política operacional estreita sem virar “referência contextual” em todo o sistema.
11. **Falsificações vêm antes do candidato.** Testar sem contexto, contexto errado, alvo falho/não confirmado, negação, pergunta, citação e formas próximas que não devem generalizar.
12. **Dívida lateral descoberta durante auditoria continua separada.** Não transformar um achado verdadeiro, mas não causal, em mega-patch.
13. **Runner diagnóstico deve ser read-only por padrão.** Se o objetivo é localizar uma fronteira, não abrir/mover/fechar janelas, não tocar IoT e não depender de efeitos externos.
14. **Segunda revisão integral antes da entrega é obrigatória.** AST/compile não bastam: revisar locks, working tree, side effects, Git, imports, falhas fechadas, ambiente e semântica do exit code.
15. **Chaos/runtime real é evidência soberana de fechamento.** Espelho verde, regressão verde e detector verde sustentam candidato; não fecham uma raiz end-to-end sozinhos.
16. **Nunca enfraquecer teste para obter verde.** Se o teste contradiz a hipótese, a hipótese é que deve cair.
17. **Nunca `git add`, `commit` ou `push` automaticamente.** O usuário mantém controle da árvore e do histórico.

---

# TURNO 155 — RETROSPECTIVA ESPECIAL C1-B2

## 1. Por que este turno virou regra de engenharia

O turno 155 foi a fala de uma palavra:

```text
maximiza
```

Ele pareceu um defeito pequeno de detector, mas expôs uma sequência de contratos que pareciam equivalentes e não eram:

```text
autoridade da fala
    ≠ referência linguística
    ≠ elipse operacional
    ≠ alvo contextual
    ≠ candidato detectado
    ≠ caminho realmente percorrido pelo runtime
```

O problema mais importante que aprendemos não foi a regex. Foi **a prova**.

## 2. O que aconteceu

### 2.1 Teste 3.6 — vermelho real

Baseline antiga:

```text
HEAD f53c9f4ca4165a0bbdecac332b84a89fe993e765
commit teste 3.6
```

No caos, `maximiza` não publicou `MAXIMIZE_WINDOW`.

A investigação separou:

- **C1-B1 — autoridade exata de `maximiza`**: corrigida e fechada;
- **C1-B2 — detector contextual/materialização do alvo**: o detector exigia referência linguística para uma fala que era uma **elipse operacional**, não um pronome.

A correção estreita adicionada em `roteador_deterministico.py` foi:

```python
referencia_linguistica = (
    bool(depende_contexto(t))
    or any(v in t for v in ["ele", "ela", "isso"])
)
acao_janela_eliptica = t == "maximiza"
if not (referencia_linguistica or acao_janela_eliptica):
    return None
```

Isso preservou a regra correta: `maximiza` pode procurar **alvo app confirmado**, sem ser promovido a referência linguística global.

### 2.2 O candidato ficou verde — e aqui veio a armadilha

O auditor chamado na época de “runtime real” passou:

```text
baseline detector ............. RED esperado
baseline orquestrador ......... RED esperado
candidate detector/runtime .... PASS
regressivos ................... PASS
```

Mas depois descobrimos que esse “runtime real” usava uma costura intermediária e substituía gates por callbacks sintéticos, por exemplo:

```python
"texto_conversa_casual_sem_acao": lambda _: False
"texto_bloqueia_playlist_agora": lambda _: False
"texto_social_curto": lambda _: False
"ignorar_token_solto": lambda _: False
"fluxo_prioritario_da_ia": lambda _: False
"texto_expresso_melhor_no_deterministico": lambda _: False
```

Logo, o verde era válido apenas para:

```text
detector/orquestrador em integração intermediária
```

Ele **não provava**:

```text
entrada
→ frozen turn
→ ComandosImediatosRuntime
→ gates reais
→ detector composto
→ CicloComandosRuntime
→ árbitro
→ executor
→ publicação do resultado
```

### 2.3 Teste 3.7 — o chaos desmentiu a conclusão prematura

HEAD atual:

```text
eb71185c19d3727292d60be13abf0b4417f18581
commit teste 3.7
```

O patch C1-B2 está presente no código, mas o caos repetiu a falha end-to-end do turno 155:

```text
> maximiza
[IA] Gerando resposta para: 'maximiza'
[PLANO] ... comandos=[]
```

Resultado semântico:

```text
execucao_nao_publicada
intent_incorreta: esperado=MAXIMIZE_WINDOW; observado=SEM_INTENT
```

Portanto a conclusão correta passou a ser:

```text
C1-B2 detector-level .......... implementado / validado
C1-B2 end-to-end .............. ABERTO
```

Nunca chamar o root completo de fechado só porque a costura intermediária ficou verde.

## 3. O segundo golpe do 155: o runner stale

Foi criado depois um runner de ciclo completo travado no teste 3.6:

```text
red_c1b2_turno155_full_cycle_processar_prioritarios_teste3_6.py
SHA-256 f30972d4ce86a40bf96f6a343db42c7301d14bc8961948cd946e6bf7fdb7bb44
```

Ao ser executado no HEAD 3.7 ele recusou corretamente:

```text
HEAD travado: f53c9f4...
observado:    eb71185c...
produção alterada: NÃO
```

Isso foi **falha de baseline/harness incompatível**, não novo vermelho de produção.

Regra permanente derivada daí:

> Se um runner stale recusa uma baseline nova, não trocar o hash e rodar no escuro. Reestudar a arquitetura atual e redesenhar a prova.

## 4. Dívidas descobertas no 155 que NÃO devem ser misturadas

Exemplo importante:

```text
maximiza opera → detector explícito pode extrair `pera`
```

É defeito real de parsing do artigo opcional, mas é **root separado**. Ele não explica `maximiza` puro e não deve entrar em C1-B2/C1-C sem causalidade.

## 5. Estado oficial do 155 ao abrir C1-C

- C1-B1: **CLOSED**.
- C1-B2 distinção referência linguística × elipse operacional: **implementada e verde em integração intermediária**.
- C1-B2 end-to-end: **OPEN** até nova prova pelo caminho canônico e posterior chaos.
- O trabalho em C1-C não pode “fechar por tabela” C1-B2.

---

# C1-C — TURNO 156 `esquerda`

## 6. Evidência do caos 3.7

Corredor relevante:

```text
154 Abre o Opera.       → APP_OPEN opera / ja_aberto_focado / confirmado
155 maximiza            → SEM_INTENT
156 esquerda            → SEM_INTENT / conversa
157 agora a calculadora → SEM_INTENT
158 direita             → SEM_INTENT
159 fecha ela           → CLOSE_APP opera / confirmado
```

No turno 156:

```text
> esquerda
[IA] Gerando resposta para: 'esquerda'
[PLANO] ... comandos=[]
```

Nenhum executor foi chamado.

## 7. Estudo estático antes do RED

### C1-C.1 — autoridade/modalidade

`esquerda` não está nos gatilhos verbais operacionais e não possui exceção equivalente à estreita exceção C1-B1 de `maximiza`.

Baseline esperada:

```text
classificar_modalidade_turno("esquerda")
→ conversa
→ acao_explicita=False
→ autoriza_execucao=False
```

### C1-C.2 — admissão determinística

`texto_expresso_melhor_no_deterministico()` reconhece formas espaciais explícitas como:

```text
coloca o opera na esquerda
```

mas não direção pura:

```text
esquerda
```

Baseline esperada:

```text
texto_expresso_melhor_no_deterministico("esquerda")
→ False
```

### C1-C.3 — materialização espacial

`detectar_organizacao_desktop()` aceita app + lado, mas não possui contrato de elipse:

```text
esquerda + referente app oficial
→ ORGANIZAR_DESKTOP(left=referente)
```

Baseline esperada:

```text
detectar_organizacao_desktop("esquerda")
→ None
```

### O que já está verde abaixo dessas fronteiras

- `ORGANIZAR_DESKTOP` está no catálogo executável;
- confirmação oferecida é `estado_observado`;
- o organizador real suporta **um único lado** e relê geometria;
- a continuidade canônica consegue fornecer `app=opera` a partir de resultado confirmado;
- o alvo não precisa vir de `ultimo_alvo` frouxo.

Contrato candidato futuro — **ainda não implementado**:

```text
fala atual fornece direção/efeito: esquerda
continuidade tipada fornece alvo: app=opera
→ ORGANIZAR_DESKTOP(left="opera")
```

Regra de segurança:

```text
contexto fornece alvo; contexto NÃO fornece autoridade
```

## 8. Ambiguidade que o candidato futuro terá de respeitar

`esquerda` também pode ser resposta conversacional a uma escolha. Portanto NÃO generalizar:

```python
if texto == "esquerda":
    autoriza_execucao = True
```

sem contrato estreito e falsificações.

Controles obrigatórios antes de qualquer candidato:

```text
app confirmado recente + esquerda  → candidato espacial esperado
sem app + esquerda                  → nenhuma ação
site-only + esquerda                → nenhuma ação
app falho/não confirmado            → nenhuma ação
não esquerda                        → nenhuma ação
"a palavra esquerda"               → nenhuma ação
"você quer dizer esquerda?"        → nenhuma ação
esquerda?                           → nenhuma ação com efeito
```

Não generalizar C1-C para:

```text
lado
pra lá
ali
canto
meio
centro
```

## 9. `direita` do turno 158

Provavelmente pertence à mesma família espacial C1-C, mas o corredor é diferente:

```text
157 agora a calculadora
158 direita
```

Como o 157 está em C1-D e atualmente falha, o fechamento end-to-end de `direita` depende de o alvo correto existir depois de C1-D. Não misturar C1-D no patch de C1-C.

## 10. Dívida lateral de tipagem — NÃO É ROOT C1-C

A continuidade e o contexto imediato conhecem `ORGANIZAR_DESKTOP` como domínio app, porém `cognicao.retrato_turno.dominio_intent()` no HEAD atual não o classifica.

Hoje isso não explica o turno 156 porque a guarda de incompatibilidade do árbitro exige os dois domínios preenchidos. Registrar como dívida separada.

---

# ARTEFATO RED C1-C

## 11. Arquivo criado

```text
red_c1c_turno156_esquerda_eliptica_teste3_7.py
SHA-256: 6fb237ffefbc15a8caa723373c7df2847dce026cb03ceaa49bad9354202dfb87
Estado: PRONTO PARA EXECUÇÃO LOCAL
Baseline: eb71185c19d3727292d60be13abf0b4417f18581 / teste 3.7
Produção alterada pelo artefato: NÃO
```

### Propósito

Provar, de forma read-only, as fronteiras estruturais conhecidas do turno 156 sem fingir ser prova end-to-end.

Saída esperada:

```text
A baseline HEAD + blobs causais ............. PASS
B autoridade atual de `esquerda` ............ RED esperado
C admissão determinística de `esquerda` ..... RED esperado
C1 frase espacial explícita ................. PASS
D referente canônico app .................... PASS
D1 sem app não há referente ................. PASS
E detector espacial `esquerda` pura ......... RED esperado
E1 detector explícito app+lado ............... PASS
E2 negação/pergunta .......................... PASS
F capability ORGANIZAR_DESKTOP ............... PASS
G dominio_intent .............................. WARN separado
I working tree preservada .................... PASS

✅ PROVA C1-C: VERMELHO ESTRUTURAL REPRODUZIDO
```

A primeira fronteira vermelha esperada é **B — autoridade/modalidade**, mas o RED exige que B, C e E apareçam simultaneamente. Isso impede a futura correção de parar na primeira regex e declarar vitória enquanto as outras fronteiras ainda bloqueiam o turno.

## 12. Locks e segurança do runner

HEAD travado:

```text
eb71185c19d3727292d60be13abf0b4417f18581
```

Blobs causais travados:

```text
mente_laylay/cognicao/modalidade_turno.py
80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241

mente_laylay/autonomia/roteador_deterministico.py
46ab5da3aa94fdcf43d042f24e2f46f45e410ade

mente_laylay/memoria_mental/contexto_compartilhado.py
eb3656d04d932b08c6e3b5067a0c22ef7a62780e

mente_laylay/memoria_mental/continuidade_geral.py
302abadc50e620ec70a790a668d88557cba7d1f3

mente_laylay/memoria_mental/resultado_acao.py
310c605e2bf5fcf3ba17cb1eb6bab8009b60c204

mente_laylay/especialistas/capacidades.py
bfc031833b46d650fb6cc6cf4e07d44150c26710

mente_laylay/cognicao/retrato_turno.py
c2a536c1351b02c9bca399d50d1d7862ed1a6b53
```

O runner recusa:

- HEAD divergente;
- blob causal divergente;
- mudança local/indexada em arquivo causal.

Ele permite mudanças preexistentes **não causais**, mas exige que o snapshot completo do working tree/index seja idêntico antes e depois da execução.

Ele também define:

```python
sys.dont_write_bytecode = True
PYTHONDONTWRITEBYTECODE=1
```

para não criar `__pycache__` no projeto durante o diagnóstico.

## 13. Segunda revisão integral do RED — concluída antes da entrega

A revisão integral encontrou um defeito no **harness**, não na hipótese C1-C: a primeira versão podia levantar exceção antes da mensagem controlada quando `--repo` apontava para uma pasta não-Git. O runner foi corrigido para falhar fechado e a hipótese de produção não foi alterada.

Validações feitas no artefato final:

```text
AST parse ................................ PASS
py_compile ............................... PASS
--help ................................... PASS
scan AST por escrita de arquivo .......... PASS / nenhuma
scan de imports de laylay.py .............. PASS / nenhum
scan de Git mutante ....................... PASS / nenhum
Git usado: status, diff, rev-parse ........ somente leitura
simulação pasta não-Git .................... PASS / falha fechada sem traceback bruto
simulação HEAD divergente ................... PASS / recusou
working tree do repo fake após recusa ....... PASS / preservado
```

Falhas/assunções revisadas:

- precisa ser executado em clone local do `projeto-laylay`;
- precisa de Git no PATH;
- precisa de Python capaz de importar os módulos do projeto;
- não importa `laylay.py`, portanto não inicia segunda instância da Laylay;
- não chama `executar_intencao`, executor de sistema ou organizador de janelas;
- a publicação `MAXIMIZE_WINDOW(opera)` usada no teste D é **sintética e sem efeito**, apenas para testar a continuidade canônica pura;
- o normalizador mínimo usado no teste C não é apresentado como callback runtime; para a palavra já canônica `esquerda`, ele é uma identidade semântica controlada;
- exit code `0` significa **RED esperado reproduzido**, não “bug corrigido”;
- exit code `1` significa baseline incompatível/inconclusiva e obriga reestudo.

---

# COMANDO PARA EXECUTAR

Copiar o runner para a raiz do repositório ou chamar por caminho absoluto:

```powershell
& C:\Python314\python.exe ".\red_c1c_turno156_esquerda_eliptica_teste3_7.py"
```

Ou, se ele estiver fora da raiz:

```powershell
& C:\Python314\python.exe "C:\caminho\red_c1c_turno156_esquerda_eliptica_teste3_7.py" --repo "C:\caminho\projeto-laylay"
```

---

# REGISTRO DE ARTEFATOS DESTA ETAPA

## Criado nesta etapa

### `red_c1c_turno156_esquerda_eliptica_teste3_7.py`
- finalidade: baseline RED estrutural read-only do turno 156;
- estado: pronto para execução local;
- SHA-256: `6fb237ffefbc15a8caa723373c7df2847dce026cb03ceaa49bad9354202dfb87`;
- baseline: `eb71185c19d3727292d60be13abf0b4417f18581`;
- próximo passo: usuário executar e devolver saída integral.

## Base histórica imediata

### `HANDOFF_LAYLAY_2026-08-17_ATUALIZADO_22H40_C1B2_PATCHER_V2_REANALISADO.md`
- papel: handoff soberano anterior;
- SHA-256 conhecido: `5b85313d2c96749439996ce0eb4e38ce63d330dd950643792228b2d7dbf606e8`;
- estado: preservado como base histórica.

---

# PRÓXIMO PASSO SOBERANO

**Não criar patch C1-C ainda.**

1. Executar `red_c1c_turno156_esquerda_eliptica_teste3_7.py` no clone real do HEAD travado.
2. Trazer a saída completa.
3. Classificar qualquer falha do runner separadamente de produção.
4. Se o padrão esperado for reproduzido, desenhar o candidato C1-C respeitando simultaneamente:
   - autoridade estreita da direção;
   - admissão determinística;
   - materialização por referente `app` oficial;
   - no-app/no-effect;
   - negação/pergunta/no-effect;
   - nenhum impacto em C1-D.
5. Testar candidato em espelho limpo antes de qualquer patch de produção.

**C1-C permanece OPEN.**

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 03H44 — C1-C MIRROR V3 VERDE

> Esta seção **supersede o estado operacional C1-C das seções antigas acima quando houver conflito**.
> O histórico anterior permanece preservado para explicar como chegamos aqui.
>
> Estado no momento deste handoff:
>
> ```text
> HEAD: de749453599db0201f9f4cac20e2dc664d4a7b4a
> commit: teste 3.8
> C1-C / turno 156 `esquerda`: OPEN
> patch de produção C1-C: NÃO aplicado
> executor real de janelas no candidato: NÃO chamado
> último estágio concluído: MIRROR REAL V3 / auditoria adversarial
> próximo estágio: auditoria/congelamento do DIFF EXATO V3
> ```

## 14. Mudança de baseline desde o handoff anterior

O handoff anterior abriu C1-C em `teste 3.7` / HEAD:

```text
eb71185c19d3727292d60be13abf0b4417f18581
```

A baseline atual é:

```text
de749453599db0201f9f4cac20e2dc664d4a7b4a
commit teste 3.8
```

O teste 3.8 contém a costura C1-B2.2 para `maximiza` em
`mente_laylay/cognicao/orquestrador_turno_runtime.py`.

Importante: os mirrors C1-C preservaram `maximiza` verde, mas isso **não substitui chaos/runtime real soberano** para fechar C1-B2 end-to-end.

## 15. RED C1-C reproduzido e ampliado na baseline 3.8

O RED estrutural confirmou:

```text
B autoridade/modalidade de `esquerda` ........ RED
C admissão determinística global .............. RED
E detector espacial global .................... RED
D continuidade conhece app=opera .............. PASS
F capability ORGANIZAR_DESKTOP ................ PASS
```

Depois o RED ampliado v2 provou:

```text
B   autoridade atual de `esquerda` ............ RED esperado
B0  P0 não bloqueia o token ................... PASS
C   admissão global ........................... RED esperado
R   retrato não congela app para a fala ....... RED descoberto
R1  corrigir só B não basta ................... PASS
H   costura pré-especialista de `maximiza` .... PASS
H1  `esquerda` ainda não usa H ................ RED descoberto
J   não é referência linguística global ....... PASS
K   pode ser resposta conversacional .......... PASS
K2  detector sem veto sequestraria escolha .... RISCO PROVADO
E   detector espacial puro .................... RED esperado
P   alvo contextual pode parecer explícito .... RISCO PROVADO
```

Artefato:

```text
red_c1c_turno156_fronteiras_ampliadas_teste3_8_v2.py
SHA-256: 84ae1c595a323d465b6e630c3f237e7d4b33e2d61b6838af07ea3a3f65fdec6d
```

Conclusão estrutural:

> C1-C não deve ser solucionado promovendo `esquerda` na gramática global.
> A rota segura é uma **elipse operacional estreita**, tipada no turno canônico.

## 16. Candidato-espelho puro — verde

```text
candidato_espelho_c1c_turno156_esquerda_teste3_8.py
SHA-256: 5396a125ca4c8a7d2126af34da2026347d0bcd6c687aa3c0251bf4c4823f37cb
```

Provou:

```text
fala atual cria autoridade estreita ........... PASS
escolha conversacional pode vetar ............. PASS
referência linguística global fica intacta .... PASS
H resolve app=opera antes dos especialistas ... PASS
especialista real autoriza .................... PASS
mesma referência chega à materialização ....... PASS
alvo contextual != explícito .................. PASS
árbitro real aceita comando_contextual ......... PASS
sem app/site-only/app falho ................... FAIL-CLOSED
direita/C1-D permanece fora ................... PASS
```

## 17. Mirror real v1 — módulos reais modificados, sem produção

```text
mirror_real_c1c_turno156_esquerda_teste3_8.py
SHA-256: b5bc80bc0a3ea329f3e51b4147e7c7220bc439d3aa8c668a483732cfdc1c1dfc
```

Resultado:

```text
C/E rota real → ORGANIZAR_DESKTOP(left=opera) .... PASS
P/P1 proveniência contextual ..................... PASS
Q árbitro real → deterministico-contextual ....... PASS
N1/N2/N3 fail-closed ............................. PASS
M1 regressão turno 155 `maximiza` ................ PASS
M2 frase espacial explícita histórica ............ PASS
```

Produção do usuário: **inalterada**.

## 18. Mirror real v2 — porta pública real até executor-spy

```text
mirror_real_c1c_turno156_esquerda_teste3_8_v2.py
SHA-256: ad38dc55e29ea11ba601539fa271bdf3872d027bfa15645fd6d17060d34f73af
```

Refinamentos:

1. P/P1 restritos à nova proveniência C1-C.
2. K0 restrito a `Você prefere esquerda ou direita?`.
3. Shape real de `pendencia_ativa()` testado.
4. `ComandosImediatosRuntime.processar_prioritarios()` atravessado.
5. `executar_intencao` substituído só no último centímetro por executor-espião sem efeito.

Resultados:

```text
P2 rota contextual antiga não reclassificada ........ PASS
Q coordenador + árbitro reais ........................ PASS
Q1 porta pública → executor-spy exatamente 1 vez ..... PASS
   origem=prioritario_linguagem_natural:deterministico-contextual
K2 escolha pendente → zero dispatch .................. PASS
M1 `maximiza` preservado ............................. PASS
M2 layout explícito preservado ....................... PASS
```

## 19. Auditoria adversarial → mirror real v3

A auditoria do v2 encontrou três superfícies a estreitar antes da produção.

### 19.1 Toda pendência ativa reduz autoridade

Foi encontrado `esclarecimento_operacional`, por exemplo:

```text
Pedro: abre um programa
Laylay: Qual programa você quer abrir?
Pedro: esquerda
```

Essa pergunta produz pendência real:

```text
origem=esclarecimento_operacional
tipo=esclarecimento
dominio=app
status=ativa
foi_falada=True
```

Regra v3:

```text
qualquer pendência retornada por pendencia_ativa()
→ `esquerda` pura NÃO ganha autoridade
```

Falsificações:

```text
K3 esclarecimento operacional real cria pendência .... PASS
K4 pendência operacional ativa veta `esquerda` ....... PASS
K5 pendência expirada não chega ao veto .............. PASS
K6 sem pendência ativa a fala volta a autorizar ...... PASS
```

### 19.2 Referente da elipse C1-C é SOMENTE `app`

O mirror v2 aceitava conceitualmente:

```text
tipo in {app, janela}
```

O v3 reduziu para:

```text
referencia_resolvida.tipo == app
```

Falsificação:

```text
N4 referência genérica `janela` não basta ............ PASS
```

### 19.3 Proveniência P/P1 exige shape exato

A identidade C1-C exige:

```text
intent = ORGANIZAR_DESKTOP
modo = posicionar
left = <app>
right/esquerda/direita = vazios
referencia_contextual = True
referencia_contextual_fonte = turno_atual.referencia_resolvida
direcao_original = esquerda
```

Falsificação:

```text
P3 candidato com dois lados não ganha proveniência C1-C ... PASS
```

Artefato:

```text
mirror_real_c1c_turno156_esquerda_teste3_8_v3.py
SHA-256: 36e86f8cefe921329aa512c866c8ebcf79ab258e318ec0c737577eb647930b7e
```

Saída local do usuário:

```text
A baseline HEAD + 25 locks ........................ PASS
Q1 porta pública + executor-spy ................... PASS
K2 escolha pendente → zero efeito ................. PASS
K3/K4/K5/K6 ....................................... PASS
N4 ................................................ PASS
P3 ................................................ PASS
M1/M2 ............................................. PASS
working tree preservada ........................... PASS

✅ C1-C: MIRROR REAL V3 SOBREVIVEU À AUDITORIA ADVERSARIAL
```

## 20. Invariante de revisão intra-turno confirmado

O candidato separa deliberadamente:

```text
autoridade da elipse
→ usa a fala ORIGINAL `texto`

reconciliação H do alvo
→ usa `texto_cognitivo`
```

H mantém:

```python
if not bool(leitura.get("autoriza_execucao")):
    return leitura, snapshot
```

Logo:

> uma revisão intra-turno pode alterar a visão cognitiva usada para resolver alvo,
> mas **não fabrica retroativamente autoridade**.

Propriedade:

```text
fala original não-exata / revisão produz `esquerda`
→ helper de autoridade não autoriza
→ H encontra autoriza_execucao=False
→ nenhum efeito
```

## 21. Candidato de produção congelado em quatro arquivos

Somente:

```text
mente_laylay/cognicao/orquestrador_turno_runtime.py
mente_laylay/autonomia/orquestrador_deterministico.py
mente_laylay/autonomia/coordenador_intencao.py
mente_laylay/memoria_mental/continuidade_contexto.py
```

Preservados deliberadamente:

```text
mente_laylay/cognicao/modalidade_turno.py
mente_laylay/autonomia/roteador_deterministico.py
mente_laylay/cognicao/referencias_linguagem.py
mente_laylay/memoria_mental/compatibilidade_contexto.py
mente_laylay/especialistas/operacional.py
mente_laylay/autonomia/comandos_imediatos.py
```

A solução NÃO:

- transforma `esquerda` em referência linguística global;
- adiciona `esquerda` ao vocabulário global de comando;
- altera detector espacial explícito histórico;
- muda P0 global;
- generaliza para `direita`;
- resolve C1-D por tabela.

## 22. Estado oficial atual

```text
RED estrutural ............................. PASS / reproduzido
RED ampliado ............................... PASS / reproduzido
candidato puro ............................. PASS
especialista real .......................... PASS
árbitro real ............................... PASS
módulos reais em mirror .................... PASS
porta pública real ......................... PASS
executor-spy ............................... PASS
pendência canônica real .................... PASS
falsificações adversariais v3 .............. PASS
patch de produção .......................... NÃO
runtime canônico com produção patchada ..... NÃO
executor real / publicação ................. NÃO
chaos soberano ............................. NÃO
```

**C1-C permanece OPEN.**

## 23. Próximo artefato — auditoria do diff final exato

```text
auditoria_diff_final_c1c_turno156_teste3_8_v3.py
SHA-256: 24f1a5878315816b294aca39de9ec7a51d76b640367b6e9edb9a1393664c0505
```

Objetivo:

1. travar HEAD e runners v1/v2/v3;
2. criar dois `git archive` independentes;
3. aplicar v3 só ao segundo;
4. comparar TODOS os arquivos por SHA-256;
5. exigir changed-set exatamente dos quatro arquivos da seção 21;
6. provar byte-a-byte que módulos globais preservados não mudaram;
7. provar que imports dos quatro arquivos não mudaram;
8. auditar autoridade original, H, tipagem `app` e proveniência;
9. imprimir unified diff exato;
10. calcular SHA-256 do diff;
11. preservar working tree/index.

Comando:

```powershell
& C:\Python314\python.exe ".\auditoria_diff_final_c1c_turno156_teste3_8_v3.py"
```

Se passar:

```text
diff final v3 congelado
→ leitura semântica do diff
→ patch real de produção
→ regressivos focados
→ runtime canônico com produção patchada
→ chaos soberano
```

## 24. Regra de continuação para o próximo chat

1. Não redesenhar C1-C do zero sem evidência nova.
2. Não promover `esquerda` nas gramáticas globais.
3. Não incluir `direita`/C1-D.
4. Contexto nunca cria autoridade.
5. Toda pendência ativa veta a elipse curta.
6. Referente C1-C deve ser `app`, não `janela`.
7. Layout contextual antigo não deve virar C1-C.
8. Não aplicar patch antes do diff final v3 ficar verde.
9. Depois do patch, regressivos/mirror não fecham o root.
10. Closure soberano exige runtime canônico + executor/publicação + chaos.

**Próximo passo soberano: executar a auditoria do diff final v3 e trazer a saída integral.**

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 03H58 — DIFF V3 VERDE, LEITURA HUMANA ENCONTROU 2 HARDENINGS, V4 PENDENTE

> Esta seção supersede o “próximo passo” da atualização 03H44.
>
> Estado:
>
> ```text
> HEAD: de749453599db0201f9f4cac20e2dc664d4a7b4a
> baseline: teste 3.8
> C1-C: OPEN
> diff v3 estruturalmente congelado: SIM
> diff v3 aceito para produção: NÃO
> motivo: auditoria humana encontrou 2 hardenings estreitos
> candidato atual: mirror v4
> patch de produção: NÃO
> ```

## 25. Auditoria do diff final v3 — PASS estrutural

O usuário executou:

```text
auditoria_diff_final_c1c_turno156_teste3_8_v3.py
```

Resultado:

```text
A HEAD travado ........................................ PASS
B runners v1/v2/v3 por SHA ........................... PASS
C produção será alterada .............................. NÃO
D dois git archives independentes .................... PASS
E v3 aplicado só ao segundo mirror ................... PASS
F changed-set exato ................................... PASS | 4 arquivos
G módulos preservados byte-a-byte .................... PASS
H auditoria semântica ................................ PASS
K working tree/index preservados ...................... PASS
```

Changed-set exato:

```text
mente_laylay/autonomia/coordenador_intencao.py
mente_laylay/autonomia/orquestrador_deterministico.py
mente_laylay/cognicao/orquestrador_turno_runtime.py
mente_laylay/memoria_mental/continuidade_contexto.py
```

Diff congelado:

```text
SHA-256: b0ee90b833d659abd2a81a1ecb67bda1af230d4bb4e931961787303315b5556a
linhas: +184 / -13
```

Módulos globais críticos permaneceram byte-a-byte.

## 26. Leitura humana do diff v3 — dois achados antes da produção

O PASS estrutural **não foi tratado como autorização automática de patch**.

### 26.1 Comentário stale no runtime

O código v3 passou a vetar:

```text
qualquer pendência ativa já falada
```

Mas o comentário inserido ainda dizia:

```text
"Uma escolha conversacional pendente só pode vetar essa autoridade."
```

Código correto, documentação local incorreta.

Isso é pequeno, mas não deve entrar na produção porque o comentário descreve uma política de autoridade e poderia induzir manutenção errada futura.

### 26.2 “Shape exato” P/P1 ainda não era literalmente exato

O helper v3 exigia:

```text
intent=ORGANIZAR_DESKTOP
modo=posicionar
left=<app>
referencia_contextual=True
referencia_contextual_fonte=turno_atual.referencia_resolvida
direcao_original=esquerda
sem right/esquerda/direita
```

Porém ainda aceitaria **chaves extras desconhecidas** nos `params`.

Isso não quebrou nenhum teste real porque o detector C1-C publica exatamente o shape esperado.

Mesmo assim, P/P1 está sendo usado como firewall de proveniência. Portanto:

> “não possui segundo lado” é insuficiente para uma assinatura chamada de shape exato.

Hardening escolhido:

```python
set(params) == {
    "left",
    "modo",
    "referencia_contextual",
    "referencia_contextual_fonte",
    "direcao_original",
}
```

Depois disso, qualquer parâmetro extra faz a proveniência C1-C retornar False.

## 27. Revisão intra-turno — leitura do produtor real

Foi auditado:

```text
mente_laylay/cognicao/revisao_turno.py
blob: 222d92624899ed55cc74628869b376075b7e6a1c
```

O resolvedor não transforma naturalmente:

```text
"abre o opera, não, esquerda"
```

em `esquerda` pura.

Ele mantém a operação anterior na substituição de alvo, produzindo forma equivalente a:

```text
abre esquerda
```

Além disso, o helper C1-C de autoridade recebe a fala original inteira, não o texto cognitivo revisado.

Logo continuam verdadeiros dois gates independentes:

```text
fala original não é exatamente `esquerda`
→ autoridade C1-C não nasce

texto cognitivo não é `esquerda` puro
→ H espacial também não reconhece
```

Foi adicionada falsificação executável R2 no v4 para não depender apenas desta leitura estática.

## 28. Mirror real v4 — candidato atual

Artefato:

```text
mirror_real_c1c_turno156_esquerda_teste3_8_v4.py
SHA-256: 5e25e6698a948694dffec67f525a39c30a437f9d8b7844b0a80312758026c174
```

O v4 reproduz integralmente v1 → v2 → v3 e acrescenta apenas:

1. comentário runtime coerente:
   `qualquer pendência ativa já falada veta a elipse ambígua`;
2. P/P1 exige conjunto literal/exato de chaves;
3. falsificação `P4`:
   candidato com `forcado=True` extra **não** ganha proveniência C1-C;
4. controle `P5`:
   candidato real continua ganhando proveniência;
5. falsificação `R2`:
   revisão intra-turno não fabrica autoridade C1-C.

O v4 já foi auditado estaticamente antes de entrega:

```text
AST .............................. PASS
py_compile ....................... PASS
--help ........................... PASS
fora de repo ..................... FAIL-CLOSED
import laylay.py .................. NENHUM
executor/janelas reais ........... NENHUM
```

## 29. Estado oficial revisado

```text
RED estrutural ........................ PASS
RED ampliado .......................... PASS
candidato puro ........................ PASS
mirror v1 ............................. PASS
mirror v2 / porta pública ............. PASS
mirror v3 / adversarial ............... PASS
diff v3 changed-set ................... PASS
diff v3 SHA congelado ................. PASS
leitura humana diff v3 ................ ACHOU 2 HARDENINGS
mirror v4 ............................. A EXECUTAR
diff v4 ............................... NÃO
patch produção ........................ NÃO
runtime canônico produção ............. NÃO
executor real/publicação .............. NÃO
chaos ................................. NÃO
```

**C1-C continua OPEN.**

Importante: o diff v3 não deve ser usado para gerar o patch final, apesar do auditor estrutural ter passado.

## 30. Próximo passo soberano

Executar:

```powershell
& C:\Python314\python.exe ".\mirror_real_c1c_turno156_esquerda_teste3_8_v4.py"
```

Verdes novos obrigatórios:

```text
P4 parâmetro extra não ganha proveniência C1-C ........ PASS
P5 candidato real mantém shape exato .................. PASS
R2 revisão intra-turno não fabrica autoridade ......... PASS
```

Além disso, **todos os verdes herdados de v3 continuam obrigatórios**, especialmente:

```text
Q1 porta pública → executor-spy ....................... PASS
K2/K4 pendências → zero efeito / veto ................. PASS
N1/N2/N3/N4 fail-closed ............................... PASS
P2/P3 regressões de proveniência ...................... PASS
M1 maximiza 155 ....................................... PASS
M2 layout explícito ................................... PASS
```

Se v4 passar:

```text
mirror v4 verde
→ congelar/auditar diff v4
→ leitura humana final do diff v4
→ preparar patch real
→ aplicar patch de produção
→ regressivos focados
→ runtime canônico
→ chaos soberano
```

Não pular o diff v4: o SHA v3 `b0ee90...` fica histórico e não é o patch final.

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 04H02 — V4 ORIGINAL INCONCLUSIVO POR BUG DE HARNESS; FIX1 PRONTO

> Esta seção supersede o “próximo passo” da atualização 03H58.
>
> Estado:
>
> ```text
> HEAD: de749453599db0201f9f4cac20e2dc664d4a7b4a
> baseline: teste 3.8
> C1-C: OPEN
> diff v3: estruturalmente congelado, mas NÃO é patch final
> v4 original: INCONCLUSIVO por bug do runner
> lógica candidata v4 executada no teste falho: NÃO
> produção alterada: NÃO
> runner atual válido: v4_fix1
> ```

## 31. Falha do v4 original — diagnóstico fechado

O usuário executou:

```text
mirror_real_c1c_turno156_esquerda_teste3_8_v4.py
SHA-256: 5e25e6698a948694dffec67f525a39c30a437f9d8b7844b0a80312758026c174
```

A execução chegou até:

```text
A baseline + cadeia v1/v2/v3 travadas ........ PASS
B revisão intra-turno travada ................. PASS
C produção será alterada ...................... NÃO
D git archive temporário ...................... PASS
E v4 aplicado somente ao mirror ............... PASS
F AST + py_compile ............................. PASS
```

e então encerrou com:

```text
❌ PROVA INCONCLUSIVA — não reproduzi child v3
```

### 31.1 Raiz exata

O v3 usa a âncora correta:

```python
marcador_final = "\nprint()\nif falhas:\n"
```

O v4 original foi gerado com:

```python
marcador = "\nprint()\\nif falhas:\\n"
```

Depois de `print()`, o v4 procurava caracteres literais `\` + `n`,
enquanto `CHILD_V2` possui quebras de linha reais.

Consequência:

```text
CHILD_V2.replace(...) não encontrou a âncora
→ CHILD_EXTRA v3 não foi inserido
→ guarda "v3.CHILD_EXTRA not in child_v3" disparou
→ prova fechou como INCONCLUSIVA
```

Portanto:

> o resultado NÃO falsifica a lógica candidata C1-C v4.
> O child nunca foi executado.

## 32. Correção do harness — v4_fix1

Artefato:

```text
mirror_real_c1c_turno156_esquerda_teste3_8_v4_fix1.py
SHA-256: 3e11f0a128b700b83d76ad79b45dc6d376315c17f207a9504b52bd9fe5f2e21f
```

Única correção funcional do runner:

```python
marcador = "\nprint()\nif falhas:\n"
```

A lógica candidata permanece a mesma do v4 original:

1. comentário runtime coerente com veto de toda pendência ativa;
2. firewall P/P1 exige conjunto literal de chaves;
3. P4 rejeita parâmetro extra;
4. P5 preserva candidato real;
5. R2 falsifica revisão intra-turno.

## 33. Auditoria local do v4_fix1 antes da entrega

Foi provado diretamente sobre os artefatos v2/v3/v4_fix1:

```text
marker correto existe no CHILD_V2 ............. PASS
reconstrução CHILD_V2 → CHILD_V3 .............. PASS
CHILD_EXTRA v3 inserido exatamente ............ PASS
injeção CHILD_EXTRA v4 ........................ PASS
P4 presente uma vez ........................... PASS
R2 presente uma vez ........................... PASS
AST child final ............................... PASS
py_compile child final ........................ PASS
AST runner .................................... PASS
py_compile runner ............................. PASS
--help ........................................ PASS
fora de repo .................................. FAIL-CLOSED
```

O SHA antigo:

```text
5e25e6698a948694dffec67f525a39c30a437f9d8b7844b0a80312758026c174
```

deve ser tratado como **runner inválido/histórico** e não deve ser reutilizado.

## 34. Próximo passo soberano

Executar:

```powershell
& C:\Python314\python.exe ".\mirror_real_c1c_turno156_esquerda_teste3_8_v4_fix1.py"
```

Verdes novos obrigatórios:

```text
P4 parâmetro extra não ganha proveniência C1-C ........ PASS
P5 candidato real mantém o shape exato C1-C ........... PASS
R2 revisão intra-turno não fabrica autoridade C1-C .... PASS
```

E todos os verdes herdados do v3 continuam obrigatórios.

Se passar:

```text
v4_fix1 verde
→ congelar/auditar diff v4 final
→ leitura humana final
→ preparar patch real
```

Ainda NÃO executar chaos antes de patch real + regressivos + runtime canônico.

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 04H08 — V4 FIX1 REJEITOU O TESTE R2; RAIZ = ASSERTIVA ERRADA; FIX2 PRONTO

> Esta seção supersede o próximo passo da atualização 04H02.
>
> Estado:
>
> ```text
> HEAD: de749453599db0201f9f4cac20e2dc664d4a7b4a
> baseline: teste 3.8
> C1-C: OPEN
> produção alterada: NÃO
> v4 original: INCONCLUSIVO por bug de montagem do child
> v4_fix1: child executou; FAIL apenas em R2
> candidato C1-C v4 falsificado pelo FAIL R2: NÃO
> raiz R2: teste confundiu autoridade geral com autoridade C1-C
> runner atual: v4_fix2
> ```

## 35. Resultado do v4_fix1

O usuário executou:

```text
mirror_real_c1c_turno156_esquerda_teste3_8_v4_fix1.py
SHA-256: 3e11f0a128b700b83d76ad79b45dc6d376315c17f207a9504b52bd9fe5f2e21f
```

Todos os testes herdados ficaram verdes, inclusive:

```text
Q1 porta pública real → executor-spy ............... PASS
K2/K4 pendências vetam/despacham zero .............. PASS
N1/N2/N3/N4 fail-closed ............................ PASS
P2/P3/P4/P5 proveniência ........................... PASS
M1 maximiza / turno 155 ............................ PASS
M2 layout explícito histórico ...................... PASS
```

Único FAIL:

```text
R2 revisão intra-turno não fabrica autoridade C1-C ... FAIL
texto_cognitivo='abre esquerda'
```

## 36. Diagnóstico do R2 — o teste estava errado

A asserção do FIX1 exigia:

```python
texto_rev != "esquerda"
and turno_rev.get("autoriza_execucao") is not True
```

A primeira metade estava correta:

```text
texto_cognitivo='abre esquerda'
```

Logo a revisão **não** produziu a forma exata `esquerda`.

A segunda metade estava conceitualmente errada.

A fala original:

```text
abre o opera, não, esquerda
```

contém um comando explícito `abre`.

Portanto o classificador geral do turno pode legitimamente produzir:

```text
autoriza_execucao=True
```

por causa de APP_OPEN / comando explícito geral.

A propriedade que C1-C precisa garantir NÃO é:

```text
"turno inteiro não pode ter autoridade"
```

A propriedade correta é:

```text
"C1-C não pode acrescentar autoridade/elipse espacial à revisão"
```

Em outras palavras, precisamos comparar autoridade **antes e depois** do helper C1-C.

## 37. R2 corrigido no v4_fix2

Novo conjunto:

### R2

```text
texto cognitivo != `esquerda`
AND autoridade_depois == autoridade_base
AND nenhuma elipse_operacional foi adicionada
```

Isso prova que o helper C1-C não criou permissão própria.

### R2.1

Executa H com:

```text
texto_cognitivo='abre esquerda'
```

e exige:

```text
origem != elipse_operacional_espacial_confirmada
AND nenhuma elipse espacial adicionada
```

Isso prova que a costura H também não sequestra a revisão.

### R2.2

Entrega o turno ao detector estreito e exige:

```text
_detetectar_elipse_espacial_confirmada('abre esquerda', mente) is None
```

Isso prova que a camada determinística não materializa a revisão como C1-C.

## 38. Artefato atual — v4_fix2

```text
mirror_real_c1c_turno156_esquerda_teste3_8_v4_fix2.py
SHA-256: 77e320cb020834c2cb89690389235b5c5e20f639265614ec50cbaa70692dc52e
```

Auditoria local antes da entrega:

```text
AST runner ................................. PASS
py_compile runner .......................... PASS
reconstrução CHILD v2→v3→v4 ............... PASS
R2/R2.1/R2.2 inseridos ..................... PASS
AST child final ............................ PASS
py_compile child final ..................... PASS
--help ..................................... PASS
fora de repo ............................... FAIL-CLOSED
```

A lógica candidata v4 não foi alterada em relação ao FIX1.
A mudança é somente no teste R2.

## 39. Próximo passo soberano

Executar:

```powershell
& C:\Python314\python.exe ".\mirror_real_c1c_turno156_esquerda_teste3_8_v4_fix2.py"
```

Novos verdes obrigatórios:

```text
R2 helper C1-C não acrescenta autoridade/elipse à revisão .... PASS
R2.1 H não reinterpreta `abre esquerda` como elipse espacial .. PASS
R2.2 detector estreito não materializa revisão como C1-C ...... PASS
```

Também continuam obrigatórios:

```text
P4 parâmetro extra não ganha proveniência C1-C ............... PASS
P5 candidato real mantém shape exato ......................... PASS
Q1 porta pública .............................................. PASS
K2/K4 ......................................................... PASS
N1-N4 ......................................................... PASS
M1/M2 ........................................................ PASS
```

Se o FIX2 passar:

```text
v4_fix2 verde
→ congelar diff v4 final
→ leitura humana final
→ preparar patch real
```

Ainda não executar chaos.


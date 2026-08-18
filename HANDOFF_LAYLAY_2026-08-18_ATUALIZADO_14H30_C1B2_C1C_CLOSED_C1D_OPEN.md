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

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 04H13 — V4 FIX2 VERDE; DIFF FINAL V4 PENDENTE

> Esta seção supersede o próximo passo da atualização 04H08.
>
> Estado:
>
> ```text
> HEAD: de749453599db0201f9f4cac20e2dc664d4a7b4a
> baseline: teste 3.8
> C1-C: OPEN
> candidato atual: V4 FIX2
> mirror v4_fix2: PASS integral
> produção alterada: NÃO
> executor real: NÃO
> próximo estágio: congelar/auditar diff final v4
> ```

## 40. V4 FIX2 — PASS integral

Artefato executado:

```text
mirror_real_c1c_turno156_esquerda_teste3_8_v4_fix2.py
SHA-256: 77e320cb020834c2cb89690389235b5c5e20f639265614ec50cbaa70692dc52e
```

O usuário obteve verde em toda a cadeia herdada:

```text
J/C0/E0 gramáticas globais preservadas ................. PASS
K0/K0.1/K0.2 escolha espacial estreita ................. PASS
B/K/B1 autoridade e falsificações ...................... PASS
H/H1 reconciliação + especialista real ................. PASS
C/E materialização left=opera .......................... PASS
P/P1/P2 proveniência contextual ........................ PASS
Q árbitro real .......................................... PASS
Q1 porta pública → executor-spy uma vez ................. PASS
K2 escolha pendente → zero efeito ...................... PASS
N1/N2/N3 fail-closed ................................... PASS
D1 direita/C1-D fora ................................... PASS
M1 maximiza/155 preservado ............................. PASS
M2 layout explícito histórico .......................... PASS
K3/K4/K5/K6 pendência operacional/expiração ............ PASS
N4 `janela` genérica rejeitada ......................... PASS
P3 dois lados rejeitados ............................... PASS
P4 parâmetro extra rejeitado ........................... PASS
P5 candidato real aceita shape exato ................... PASS
```

Novas provas de revisão:

```text
R2 helper C1-C não acrescenta autoridade/elipse ........ PASS
    texto_cognitivo='abre esquerda'
    autoridade_base=True
    autoridade_depois=True

R2.1 H não reinterpreta `abre esquerda` ................ PASS
R2.2 detector estreito não materializa revisão ......... PASS
```

Working tree/index:

```text
PASS
```

Conclusão desta camada:

> O v4_fix2 é o primeiro candidato que sobreviveu integralmente ao
> firewall final incluindo revisão intra-turno e proveniência literal.

Isso **não fecha C1-C**, porque ainda não existe patch real de produção.

## 41. O que está congelado conceitualmente no v4

A solução continua alterando somente:

```text
mente_laylay/cognicao/orquestrador_turno_runtime.py
mente_laylay/autonomia/orquestrador_deterministico.py
mente_laylay/autonomia/coordenador_intencao.py
mente_laylay/memoria_mental/continuidade_contexto.py
```

Regras finais:

1. somente fala original exata `esquerda` cria a autoridade espacial estreita;
2. qualquer pendência ativa já falada veta essa elipse ambígua;
3. contexto fornece alvo, nunca autoridade;
4. H exige app confirmado coincidente entre continuidade e retrato congelado;
5. referente deve ser tipado como `app`;
6. determinístico usa a mesma `turno_atual.referencia_resolvida`;
7. P/P1 reconhecem apenas conjunto literal de 5 chaves;
8. candidato contextual vai ao árbitro como `deterministico-contextual`;
9. `direita` continua fora;
10. revisão intra-turno não pode fabricar C1-C.

## 42. Próximo artefato — auditoria do diff final v4

Criado:

```text
auditoria_diff_final_c1c_turno156_teste3_8_v4.py
SHA-256: 9c7b7caac0b178153f3b1e7225fbac1027d54b15e45f8e1d86cfa439406af92a
```

Diferença importante em relação ao auditor v3:

- cria BASE, V3 e V4 em mirrors independentes;
- reproduz e exige o SHA histórico do diff v3:
  `b0ee90b833d659abd2a81a1ecb67bda1af230d4bb4e931961787303315b5556a`;
- exige que V4 vs V3 altere **somente**:
  - comentário runtime;
  - firewall P/P1;
- exige changed-set BASE→V4 exatamente de 4 arquivos;
- preserva byte-a-byte módulos globais e `revisao_turno.py`;
- compara imports;
- audita o conjunto literal `set(params)`;
- audita fala original para autoridade vs `texto_cognitivo` para H;
- imprime diff final + SHA-256.

Comando:

```powershell
& C:\Python314\python.exe ".\auditoria_diff_final_c1c_turno156_teste3_8_v4.py"
```

Se passar:

```text
diff v4 congelado
→ leitura humana final do diff
→ preparar patch de produção
```

NÃO usar o SHA do diff v3 como patch final.

## 43. Estado oficial

```text
RED estrutural ........................ PASS
RED ampliado .......................... PASS
mirror puro ........................... PASS
mirror v1 ............................. PASS
mirror v2 / porta pública ............. PASS
mirror v3 / adversarial ............... PASS
diff v3 estrutural .................... PASS
leitura humana v3 ..................... encontrou 2 hardenings
v4 original ........................... INCONCLUSIVO (harness)
v4_fix1 ............................... TESTE R2 incorreto
v4_fix2 ............................... PASS INTEGRAL
diff v4 ............................... A EXECUTAR
patch produção ........................ NÃO
runtime produção ...................... NÃO
executor real/publicação .............. NÃO
chaos ................................. NÃO
```

**C1-C permanece OPEN.**

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 09H20 — AMBIENTE SENAI / AUDITOR V4 STANDALONE

> Esta seção supersede somente o modo de execução do próximo auditor.
> O candidato C1-C e o estado técnico permanecem iguais à atualização 04H13.
>
> Situação:
>
> ```text
> usuário fora do PC principal
> ambiente atual: SENAI
> disponível: clone/repositório normal
> indisponíveis: artefatos históricos mirror_real_*.py
> auditor v4 original: INCONCLUSIVO por dependência externa
> produção alterada: NÃO
> ```

## 44. Por que o auditor v4 original falhou no SENAI

O auditor:

```text
auditoria_diff_final_c1c_turno156_teste3_8_v4.py
```

foi criado para o ambiente do PC principal e exige fisicamente os runners históricos:

```text
mirror_real_c1c_turno156_esquerda_teste3_8.py
mirror_real_c1c_turno156_esquerda_teste3_8_v2.py
mirror_real_c1c_turno156_esquerda_teste3_8_v3.py
mirror_real_c1c_turno156_esquerda_teste3_8_v4_fix2.py
```

No SENAI o usuário possui apenas o repositório, então o fechamento:

```text
❌ PROVA INCONCLUSIVA — runner ausente:
mirror_real_c1c_turno156_esquerda_teste3_8.py
```

é esperado e **não significa RED do candidato**.

## 45. Auditor v4 STANDALONE

Criado:

```text
auditoria_diff_final_c1c_turno156_teste3_8_v4_STANDALONE.py
SHA-256: a08b48c838129224b59529636357617343a5f69d559bc3f0a6bae874ae794b99
```

Propriedade principal:

> É necessário somente este arquivo + o clone Git do repositório no HEAD travado.

O standalone contém internamente, comprimidas e travadas por SHA-256, as fontes auditadas de:

```text
v1 b5bc80bc0a3ea329f3e51b4147e7c7220bc439d3aa8c668a483732cfdc1c1dfc
v2 ad38dc55e29ea11ba601539fa271bdf3872d027bfa15645fd6d17060d34f73af
v3 36e86f8cefe921329aa512c866c8ebcf79ab258e318ec0c737577eb647930b7e
v4_fix2 77e320cb020834c2cb89690389235b5c5e20f639265614ec50cbaa70692dc52e
```

Ele reconstrói esses runners **em memória**, sem procurar arquivos externos.

Mantém as mesmas provas:

```text
HEAD exato de749453... ........................ obrigatório
BASE/V3/V4 por git archive .................... SIM
changed-set BASE→V4 exatamente 4 arquivos ..... obrigatório
módulos globais byte-a-byte ................... obrigatório
SHA histórico diff-v3 b0ee90... ............... obrigatório
V4-vs-V3 somente 2 hardenings ................. obrigatório
auditoria semântica final ..................... obrigatório
AST + py_compile .............................. obrigatório
working tree/index preservados ................ obrigatório
produção alterada ............................. NÃO
```

Auditoria local antes da entrega:

```text
AST ........................................... PASS
cadeia embutida v1/v2/v3/v4 por SHA .......... PASS
dependência mirror_real_*.py externo .......... NENHUMA
--help ........................................ PASS
fora de repo .................................. FAIL-CLOSED
```

## 46. Execução no SENAI

Colocar somente:

```text
auditoria_diff_final_c1c_turno156_teste3_8_v4_STANDALONE.py
```

na raiz do clone e executar:

```powershell
& C:\Python314\python.exe ".\auditoria_diff_final_c1c_turno156_teste3_8_v4_STANDALONE.py"
```

Se o Python do SENAI for outro, pode usar o executável Python disponível, desde que seja compatível com a sintaxe do projeto.

O resultado esperado começa com:

```text
A HEAD travado ........................................ PASS
B cadeia v1/v2/v3/v4 embutida por SHA ............... PASS
C mirrors históricos externos necessários ............ NÃO
D produção será alterada .............................. NÃO
```

Se o HEAD do clone do SENAI não for exatamente:

```text
de749453599db0201f9f4cac20e2dc664d4a7b4a
```

o auditor deve fechar como INCONCLUSIVO. Não enfraquecer esse gate.

## 47. Estado oficial

```text
mirror v4_fix2 ........................ PASS INTEGRAL
auditor diff v4 original .............. não executável no SENAI sem artefatos
auditor diff v4 standalone ............ A EXECUTAR
patch produção ........................ NÃO
runtime produção ...................... NÃO
chaos ................................. NÃO
C1-C .................................. OPEN
```

**Próximo passo soberano no SENAI: executar o standalone e trazer a saída integral.**

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 12H03 — STANDALONE ORIGINAL FALHOU EM K POR ESCAPE DUPLICADO; FIX1 PENDENTE

> Esta seção supersede o próximo passo da atualização 09H20.
>
> Estado:
>
> ```text
> ambiente: SENAI / somente clone Git + auditor standalone
> HEAD: de749453599db0201f9f4cac20e2dc664d4a7b4a
> C1-C: OPEN
> v4_fix2: PASS integral
> standalone original: FAIL de HARNESS em K
> candidato v4 falsificado: NÃO
> produção alterada: NÃO
> auditor atual: STANDALONE_FIX1
> ```

## 48. Resultado do standalone original no SENAI

O usuário executou o auditor standalone e obteve:

```text
A HEAD travado ........................................ PASS
B cadeia v1/v2/v3/v4 embutida por SHA ............... PASS
C mirrors históricos externos necessários ............ NÃO
D produção será alterada .............................. NÃO
E três git archives independentes .................... PASS
F v3 e v4 reproduzidos do próprio auditor ............ PASS
G changed-set final ................................... PASS | 4 arquivos
H módulos globais/preservados byte-a-byte ............. PASS
I SHA histórico diff-v3 reproduzido ................... PASS
J v4-vs-v3 somente 2 hardenings ....................... PASS
K auditoria semântica final ........................... FAIL
  - conv perdeu contrato: (?:voce|você|tu)\\s+prefere
```

Os gates A–J confirmaram que:

- o HEAD correto foi usado;
- as fontes embutidas v1/v2/v3/v4 estavam íntegras;
- o candidato v4 foi reproduzido;
- o changed-set continuou exatamente de 4 arquivos;
- o diff v3 histórico foi reproduzido;
- o delta v4-v3 continuou exatamente de 2 hardenings.

Logo a falha estava localizada na checagem textual de K.

## 49. Raiz exata da falha K

A continuidade final contém a regex normal:

```python
r"(?:voce|você|tu)\s+prefere"
```

O standalone original procurava, por erro de geração:

```python
r"(?:voce|você|tu)\\s+prefere"
```

No segundo caso existem duas barras reais antes de `s`.

Portanto o auditor exigia um texto que o módulo correto não deveria possuir.

Conclusão:

> K falhou por escape duplicado no harness.
> Isso NÃO é RED do candidato C1-C.

## 50. STANDALONE FIX1

Novo artefato:

```text
auditoria_diff_final_c1c_turno156_teste3_8_v4_STANDALONE_FIX1.py
SHA-256: 932f8399c2e585292211b3d47d517ff08dffe2cb5da3abe7e2d7a118cf8cab38
```

Diferença contra o standalone anterior:

```text
EXATAMENTE UMA alteração textual na auditoria semântica:
\\s  →  \s
```

Nenhuma fonte embutida v1/v2/v3/v4 foi alterada.
Nenhuma lógica candidata foi alterada.
Nenhum gate A–J foi enfraquecido.

Auditoria antes da entrega:

```text
AST ........................................ PASS
py_compile ................................. PASS
token regex real .......................... PASS
token regex duplicado ausente ............. PASS
--help ..................................... PASS
fora de repo ............................... FAIL-CLOSED
diff vs standalone anterior ............... 1 linha lógica
```

## 51. Próximo passo no SENAI

Executar:

```powershell
& C:\Python314\python.exe ".\auditoria_diff_final_c1c_turno156_teste3_8_v4_STANDALONE_FIX1.py"
```

Os gates A–J devem permanecer verdes.

K agora deve passar e a execução deve continuar até:

```text
L AST + py_compile diff final ......................... PASS
M SHA-256 do diff v4 .................................. <hash>
N linhas do diff v4 ................................... +X / -Y
O working tree/index preservados ...................... PASS

✅ C1-C: DIFF FINAL V4 STANDALONE CONGELADO E AUDITADO
```

Se qualquer gate A–J regredir, rejeitar.
Se K ainda falhar por outro contrato, estudar o novo primeiro RED; não enfraquecer automaticamente.

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 12H09 — STANDALONE FIX1 PASSOU A–N; LOG RECEBIDO SEM O/BANNER FINAL

> Esta seção supersede apenas o próximo passo da atualização 12H03.
>
> Estado:
>
> ```text
> ambiente: SENAI
> HEAD: de749453599db0201f9f4cac20e2dc664d4a7b4a
> C1-C: OPEN
> standalone FIX1: A–N comprovados
> diff v4 SHA obtido: SIM
> working tree/index final O: NÃO EVIDENCIADO NO LOG RECEBIDO
> banner final de congelamento: NÃO EVIDENCIADO NO LOG RECEBIDO
> produção alterada: NÃO
> ```

## 52. Resultado recebido do STANDALONE FIX1

O usuário executou:

```text
auditoria_diff_final_c1c_turno156_teste3_8_v4_STANDALONE_FIX1.py
```

O log recebido comprova:

```text
A HEAD travado ........................................ PASS
B cadeia v1/v2/v3/v4 embutida por SHA ............... PASS
C mirrors históricos externos necessários ............ NÃO
D produção será alterada .............................. NÃO
E três git archives independentes .................... PASS
F v3 e v4 reproduzidos do próprio auditor ............ PASS
G changed-set final ................................... PASS | 4 arquivos
H módulos globais/preservados byte-a-byte ............. PASS
I SHA histórico diff-v3 reproduzido ................... PASS
J v4-vs-v3 somente 2 hardenings ....................... PASS
K auditoria semântica final ........................... PASS
L AST + py_compile diff final ........................ PASS
```

O diff final foi impresso integralmente.

Resumo congelado até o ponto N:

```text
M SHA-256 do diff v4:
88e0cd1e3ba52fb750fd90a332b8dad53ad3f6de51d5294b90841bb840e80e05

N linhas do diff v4:
+189 / -13
```

## 53. O que ainda falta na evidência recebida

O arquivo de log termina imediatamente após:

```text
N linhas do diff v4..................................... +189 / -13
```

Mas o auditor possui obrigatoriamente, depois de N:

```text
O working tree/index preservados ....................... PASS/FAIL
```

e, se PASS:

```text
✅ C1-C: DIFF FINAL V4 STANDALONE CONGELADO E AUDITADO
```

Portanto:

> Não declarar ainda que o diff v4 está soberanamente congelado.
> A–N estão verdes, mas O e o banner final não chegaram no material recebido.

Isso pode ser apenas corte/cópia incompleta da saída.
Não é evidência de RED do candidato.

## 54. Próximo passo mínimo

Não precisa redesenhar nem criar outro auditor.

Executar novamente o mesmo standalone e capturar o final, ou verificar a saída completa.

O necessário é somente comprovar:

```text
O working tree/index preservados ....................... PASS

✅ C1-C: DIFF FINAL V4 STANDALONE CONGELADO E AUDITADO
```

Se O for PASS, o SHA soberano do diff final v4 será:

```text
88e0cd1e3ba52fb750fd90a332b8dad53ad3f6de51d5294b90841bb840e80e05
```

e a próxima fase passa a ser:

```text
leitura humana final do diff v4
→ preparar patch real de produção
```

Ainda não executar chaos.

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 12H11 — DIFF FINAL V4 CONGELADO E AUDITADO

> Esta seção supersede a pendência da atualização 12H09.
>
> Estado:
>
> ```text
> ambiente: SENAI
> HEAD: de749453599db0201f9f4cac20e2dc664d4a7b4a
> baseline: teste 3.8
> C1-C: OPEN
> mirror v4_fix2: PASS integral
> diff final v4 standalone: PASS integral
> produção alterada: NÃO
> executor real: NÃO
> chaos: NÃO
> próximo estágio: leitura humana final do diff v4 → patch real
> ```

## 55. Prova final recebida

O usuário completou a saída que havia sido enviada de forma truncada.

Banner final:

```text
✅ C1-C: DIFF FINAL V4 STANDALONE CONGELADO E AUDITADO
   requer mirrors históricos externos: NÃO
   changed-set: EXATAMENTE 4 arquivos
   produção alterada: NÃO
   C1-C fechada: NÃO
```

Isso fecha o único gap de evidência da atualização 12H09.

## 56. Diff soberano C1-C v4

O diff final oficialmente congelado é:

```text
SHA-256:
88e0cd1e3ba52fb750fd90a332b8dad53ad3f6de51d5294b90841bb840e80e05

linhas:
+189 / -13
```

Changed-set soberano:

```text
mente_laylay/autonomia/coordenador_intencao.py
mente_laylay/autonomia/orquestrador_deterministico.py
mente_laylay/cognicao/orquestrador_turno_runtime.py
mente_laylay/memoria_mental/continuidade_contexto.py
```

Nenhum outro arquivo pertence ao patch C1-C final.

## 57. Cadeia de evidência oficialmente concluída até o diff

```text
RED estrutural ................................ PASS
RED ampliado .................................. PASS
candidato espelho ............................. PASS
mirror real v1 ................................ PASS
mirror real v2 / porta pública ................ PASS
mirror real v3 / adversarial .................. PASS
diff v3 ....................................... PASS
auditoria humana v3 ........................... 2 hardenings
v4 original ................................... INCONCLUSIVO por harness
v4_fix1 ....................................... teste R2 incorreto
v4_fix2 ....................................... PASS INTEGRAL
standalone original ........................... harness regex duplicada
standalone FIX1 ............................... PASS INTEGRAL
diff v4 congelado ............................. PASS
```

## 58. O que o congelamento autoriza — e o que NÃO autoriza

Agora está autorizado:

```text
leitura humana final do diff v4
→ preparar patch de produção exatamente desse diff
```

Ainda NÃO está autorizado declarar C1-C corrigida.

Ainda faltam:

```text
patch real de produção
→ regressivos focados
→ runtime canônico com produção patchada
→ executor real + publicação
→ chaos soberano
→ segunda auditoria
```

Regra:

> Qualquer alteração de lógica após este ponto muda o SHA e invalida o congelamento.
> Se a leitura humana final exigir mudança de lógica, voltar à fase de candidato/mirror.
> Correções meramente mecânicas do patcher não podem alterar os quatro conteúdos finais.

## 59. Próximo passo soberano

Fazer a leitura humana final do diff congelado:

```text
88e0cd1e3ba52fb750fd90a332b8dad53ad3f6de51d5294b90841bb840e80e05
```

Critérios:

1. cada hunk precisa corresponder a uma causa já provada;
2. nenhuma gramática global pode ter sido promovida;
3. nenhuma rota de C1-D `direita` pode ter entrado;
4. contexto não pode criar autoridade;
5. pendência ativa deve somente reduzir autoridade;
6. P/P1 deve permanecer literal/exato;
7. revisões intra-turno não podem fabricar C1-C;
8. `maximiza`/155 deve permanecer preservado;
9. nenhum módulo fora dos quatro deve ser necessário;
10. nenhum comentário deve contradizer a política real.

Se a leitura humana final passar:

```text
→ gerar patcher de produção travado por HEAD + blobs + diff SHA
```

Ainda sem Git automático.

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 12H13 — LEITURA HUMANA FINAL PASSOU; PATCHER REAL PREPARADO

> Esta seção supersede o próximo passo da atualização 12H11.
>
> Estado:
>
> ```text
> HEAD baseline: de749453599db0201f9f4cac20e2dc664d4a7b4a
> diff soberano C1-C v4:
> 88e0cd1e3ba52fb750fd90a332b8dad53ad3f6de51d5294b90841bb840e80e05
> leitura humana final: PASS
> patcher de produção: PREPARADO
> produção alterada: AINDA NÃO
> C1-C: OPEN
> ```

## 60. Leitura humana final — resultado

Os quatro hunks foram relidos contra o baseline e contra as rotas adjacentes.

### 60.1 `orquestrador_turno_runtime.py`

PASS.

- `_forma_elipse_espacial_exata` aceita somente `esquerda` exato;
- pontuação não é removida para C1-C;
- pendência ativa falada veta a elipse antes da autorização;
- helper de autoridade recebe a fala original `texto`;
- revisão intra-turno não consegue fabricar autoridade C1-C;
- H recebe `texto_cognitivo`, mas exige `elipse_operacional` + autoridade prévia;
- contexto só resolve alvo;
- `maximiza` continua suportado pela mesma reconciliação;
- comentário final condiz com a política real.

### 60.2 `orquestrador_deterministico.py`

PASS.

- detector C1-C exige `texto == esquerda`;
- exige `turno_atual.texto == esquerda`;
- exige `autoriza_execucao=True`;
- exige `requer_esclarecimento=False`;
- exige elipse tipada como posicionamento de janela / `left` / alvo `app`;
- aceita somente `referencia_resolvida.tipo == app`;
- materializa exatamente `ORGANIZAR_DESKTOP(left=<app>, modo=posicionar)`;
- não implementa `direita`.

### 60.3 `coordenador_intencao.py`

PASS.

- shape C1-C deixa de ser rotulado como alvo explícito;
- dependência operacional é separada da dependência linguística global;
- candidato entra como `deterministico-contextual`;
- P/P1 exigem conjunto literal das 5 chaves publicadas;
- layout explícito legado continua separado;
- árbitro continua exigindo a autoridade congelada do turno.

Observação lateral registrada, NÃO bloqueante:

Um shape interno futuro/malformado que carregasse metadata C1-C extra poderia deixar de ganhar a proveniência exata e cair em classificação legada. Isso não cria autoridade nova — o árbitro ainda exige `turno.autoriza_execucao` — e atualmente não existe produtor real desse shape. Não misturar essa dívida futura no C1-C atual.

### 60.4 `continuidade_contexto.py`

PASS.

- regra nova só cobre pergunta binária esquerda/direita;
- `Você prefere esquerda ou direita?` vira escolha;
- `Você prefere café ou chá?` permanece baseline;
- `direita` aparece apenas como opção conversacional, não como ação C1-D.

## 61. Critérios humanos finais

```text
1. cada hunk corresponde à causa provada ................. PASS
2. gramática global não promovida ........................ PASS
3. C1-D `direita` não entrou ............................. PASS
4. contexto não cria autoridade .......................... PASS
5. pendência ativa apenas reduz autoridade ............... PASS
6. P/P1 literal/exato .................................... PASS
7. revisão intra-turno não fabrica C1-C .................. PASS
8. `maximiza`/155 preservado ............................. PASS
9. somente 4 módulos necessários ......................... PASS
10. comentários coerentes ................................ PASS
```

Conclusão:

> O diff soberano `88e0cd...` está APROVADO para aplicação em produção.

## 62. Patcher real de produção

Artefato:

```text
patch_c1c_turno156_teste3_8_v4_PRODUCAO.py
SHA-256:
cc090fe7abb1aeaa56663cc5767a66a5f06d50cbade7a351a6798777afbd6f84
```

Manifesto interno de transformações:

```text
SHA-256:
562dc02c4e5d7fb03b63a062ebc51699282fa019dcda8a4f50b0e003729acf6d
```

Travamentos:

```text
HEAD:
de749453599db0201f9f4cac20e2dc664d4a7b4a

runtime blob:
1c5497369afde2992d282124b6cc3f28c2659643

determinístico blob:
1ace7364d3ac9ef3530e7cd22607d6573f1c5b86

coordenador blob:
09431feecd3d083afc509770a4918e59d2111add

continuidade blob:
5fd03c85e9b53e2f72192bdde0bda6bd4c447a34

diff final:
88e0cd1e3ba52fb750fd90a332b8dad53ad3f6de51d5294b90841bb840e80e05
```

Características:

- self-contained;
- default = CHECK-ONLY;
- `--apply` obrigatório para escrita;
- changed-set interno = exatamente 4 arquivos;
- exige arquivos alvo byte-a-byte iguais ao HEAD baseline;
- exige nenhuma alteração staged nos quatro alvos;
- AST antes e depois;
- manifesto interno por SHA;
- recomputa o diff antes de escrever;
- só escreve se o diff for exatamente `88e0cd...`;
- usa temporários + rollback próprio em falha de escrita;
- pós-aplicação recomputa o SHA do diff;
- index/staging precisa permanecer idêntico;
- Git usado somente para leitura (`rev-parse`, `diff`);
- nenhum `git add`, `commit`, `push`, `reset`, `restore`;
- não executa a Laylay.

## 63. Segunda auditoria do patcher

```text
AST ........................................ PASS
py_compile isolado ......................... PASS
HEAD travado ............................... PASS
4 blobs baseline travados .................. PASS
diff soberano travado ...................... PASS
manifesto por SHA .......................... PASS
changed-set interno = 4 .................... PASS
subprocess Git só no wrapper _git .......... PASS
subcomandos Git: rev-parse + diff .......... PASS
--help ..................................... PASS
fora de repo ............................... FAIL-CLOSED
```

## 64. Próximo passo soberano

Primeiro executar SOMENTE CHECK-ONLY:

```powershell
& C:\Python314\python.exe ".\patch_c1c_turno156_teste3_8_v4_PRODUCAO.py"
```

Esperado:

```text
A HEAD + 4 blobs travados ........................ PASS
B staged nos 4 alvos ............................. NÃO
C manifesto interno travado por SHA .............. PASS
D âncoras únicas + AST final ..................... PASS
E changed-set candidato .......................... PASS | 4 arquivos
F SHA do diff congelado .......................... PASS

✅ CHECK-ONLY VERDE — produção NÃO alterada
```

Somente depois desse CHECK-ONLY verde no clone real, executar:

```powershell
& C:\Python314\python.exe ".\patch_c1c_turno156_teste3_8_v4_PRODUCAO.py" --apply
```

Depois do apply, ainda faltam:

```text
regressivos focados
→ runtime canônico
→ executor real + publicação
→ chaos soberano
→ segunda auditoria
```

**C1-C continua OPEN.**

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 14H17 — TESTE 3.9 PÓS-CHAOS; SEGUNDA AUDITORIA PREPARADA

> Esta seção supersede o próximo passo da atualização 12H13.
>
> O patch V4 já foi aplicado, commitado e submetido ao chaos real. C1-C ainda
> não recebe CLOSED nesta atualização porque a segunda auditoria pós-chaos foi
> preparada, mas ainda precisa ser executada no clone real do usuário.

## 65. Novo HEAD real

```text
HEAD:
a181b7bec50409dd7d3f976b3172389f76df7b8f
commit: teste 3.9

parent único:
de749453599db0201f9f4cac20e2dc664d4a7b4a
commit: teste 3.8
```

O commit é um salto direto de um parent e contém, dentro de `mente_laylay`,
exatamente os quatro módulos aprovados pelo diff C1-C.

## 66. Diff soberano preservado

```text
SHA-256 diff C1-C:
88e0cd1e3ba52fb750fd90a332b8dad53ad3f6de51d5294b90841bb840e80e05

stats:
+189 / -13
```

Blobs finais no HEAD 3.9:

```text
orquestrador_turno_runtime.py
195b67abda420faf792509b20f1b8dd466e3b90e

orquestrador_deterministico.py
55a5ef1f4dfdf6c3b94ca40c7177ddce3fb6cf2c

coordenador_intencao.py
4e1b7be651bf0f4a5e2c11d284c76bff170abc26

continuidade_contexto.py
079bd53d7905c6a6389f0da58df972c5839eb797
```

Patcher commitado:

```text
patch_c1c_turno156_teste3_8_v4_PRODUCAO.py
SHA-256:
cc090fe7abb1aeaa56663cc5767a66a5f06d50cbade7a351a6798777afbd6f84
```

## 67. Gates causais preservados no 3.9

```text
comandos_imediatos.py
27706613cb505219479664a664db038cac78c037

roteador_deterministico.py
46ab5da3aa94fdcf43d042f24e2f46f45e410ade

arbitro_turno.py
7756a15a8538291a118f8b4f3ab900157fa10927

modalidade_turno.py
80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241

revisao_turno.py
222d92624899ed55cc74628869b376075b7e6a1c

referencias_linguagem.py
6f1b759fc190228a9f2c4e2c9620c716fe064b53

retrato_turno.py
c2a536c1351b02c9bca399d50d1d7862ed1a6b53

esclarecimento_operacional.py
369c51be3a3e5bd429837ff87517dc65d68034b7

especialistas/operacional.py
2ee4bbdeedd139f9b98e3611fc13442114c3835c

compatibilidade_contexto.py
768944f808002d8c24f697c0b2769a31d536eb3e
```

Conclusão desta parte:

> O verde do chaos não veio de alteração escondida em autoridade, revisão,
> referência global, especialista, árbitro ou porta pública.

## 68. Chaos 3.9 travado

Diretório:

```text
resultados_testes/roteiro_teste_laylay_caos-20260818-133137-456909
```

Blobs:

```text
terminal.log
32a41c11fe16f4c78339b3e8edb7d1ab42776e6a

checkpoint.json
4fb8d953ac8a8e3a55a56aa5e786fa061412d74a

resumo.json
80e2bf62ae3e4f6ddabd009d0a7cef557653528b

relatorio_semantico.md
3b6a988e1713005bdc0e843429112be3b1c38c95

conversa.md
a8639aa416532ab627bc7d1c211146b87dc8a251
```

## 69. Corredor real 154–159

Resultado observado:

```text
154 Abre o Opera.
→ APP_OPEN opera
→ ja_aberto_focado
→ confirmado=True

155 maximiza
→ MAXIMIZE_WINDOW opera
→ janela_maximizada
→ executou=True
→ confirmado=True

156 esquerda
→ ORGANIZAR_DESKTOP
→ alvo=opera na esquerda
→ layout_confirmado
→ executou=True
→ confirmado=True
→ params:
   left=opera
   modo=posicionar
   referencia_contextual=True
   referencia_contextual_fonte=turno_atual.referencia_resolvida
   direcao_original=esquerda

157 agora a calculadora
→ zero comando operacional

158 direita
→ zero comando operacional

159 fecha ela
→ CLOSE_APP opera
→ app_fechado
→ executou=True
→ confirmado=True
```

O terminal registra como evidência do 156 a releitura da geometria e a
comparação com o lado solicitado.

## 70. O que o estudo pós-chaos provou

### 70.1 C1-B2

`maximiza` deixou de ser `SEM_INTENT` no caminho real e foi até executor +
confirmação. O avaliador semântico marcou o turno 155 como `passou`.

Estado candidato:

```text
C1-B2 end-to-end = pronto para CLOSED
```

### 70.2 C1-C

A fala exata `esquerda` atravessou o runtime real e publicou o shape C1-C
exato no executor. O resultado foi `layout_confirmado`, `executou=True`,
`confirmado=True`.

### 70.3 C1-D não vazou

`direita` continuou sem comando operacional. `agora a calculadora` também
continuou sem efeito. Portanto C1-D permanece root separado.

### 70.4 Autoridade continua soberana

No HEAD 3.9:

```text
fala original
→ aplicar_elipse_espacial_autorizada_ao_turno(texto)
→ construir retrato com texto_cognitivo
→ reconciliar H(texto_cognitivo)
→ especialistas
→ plano
```

H exige autoridade já existente e não escreve `autoriza_execucao`.

A porta pública continua usando:

```text
resolver_comando_natural(texto, "prioritario-linguagem-natural")
→ coordenador
→ árbitro
→ executar_intencao
→ registrar_resultado_execucao
```

O árbitro continua exigindo `turno.autoriza_execucao` para comando contextual
com efeito.

### 70.5 Rota não é inventada a partir do log

O `terminal.log` 3.9 não imprime literalmente o rótulo
`deterministico-contextual` no corredor. A prova da rota será feita por:

1. produtor estrutural único do shape C1-C em `mente_laylay`;
2. coordenador classificando esse shape como dependência operacional;
3. candidato `comando_contextual` de origem `deterministico-contextual`;
4. árbitro recebendo o `turno_atual`;
5. porta pública publicando o executor real.

Não afirmar linha de log inexistente.

## 71. Falhas globais do chaos continuam separadas

O chaos 3.9 possui outras falhas globais e maior latência no PC do SENAI.
Isso não será usado nem para mascarar nem para reabrir C1-C sem causalidade.

Achados laterais conhecidos:

```text
Maximiza ele. → intent/executor corretos, fala contradiz confirmação
Fecha ela.    → apareceu plano bruto FECHA incompleto em outro corredor
lembrete      → provável falso positivo de matcher de fala
```

Nenhum deles entra no patch/fechamento C1-C sem nova prova causal própria.

## 72. Segunda auditoria pós-chaos

Artefato:

```text
auditoria_final_pos_chaos_c1c_turno156_teste3_9.py
SHA-256:
e460c9485ff647cd45ff801628aa61918ae9345cb16118010b68f792340861e2
```

O auditor é self-contained e read-only.

Ele trava:

- HEAD e parent;
- 4 blobs parent;
- 4 blobs finais;
- 10 blobs causais preservados;
- 5 artefatos exatos do chaos;
- SHA do patcher;
- changed-set de produção exatamente 4;
- diff soberano `88e0cd...` e stats `+189/-13`;
- checkout/index causal limpo;
- ordem autoridade → retrato → H → especialista;
- H sem escrita de autoridade;
- detector `esquerda` estrito e sem `direita`;
- shape exato P/P1;
- porta pública e árbitro preservados;
- produtor único do metadata C1-C em produção;
- corredor chaos único;
- turnos 155/156 executados e confirmados;
- 157/158 sem efeito;
- 159 preservando continuidade;
- 155/156 ausentes da lista de erros.

Git usado pelo auditor:

```text
rev-parse
rev-list
show
diff
ls-tree
```

Nenhum Git mutante.

Auditoria do próprio auditor:

```text
AST ...................................... PASS
py_compile isolado ....................... PASS
locks HEAD/parent/diff/patcher ........... PASS
subcomandos Git somente read-only ........ PASS
parser corredor 154-159 .................. PASS
corredor duplicado falha fechado ......... PASS
--help ................................... PASS
fora de repo ............................. FAIL-CLOSED
```

## 73. Próximo comando

Executar no clone do teste 3.9:

```powershell
& C:\Python314\python.exe ".\auditoria_final_pos_chaos_c1c_turno156_teste3_9.py"
```

Ou, se o arquivo estiver fora da raiz do repo:

```powershell
& C:\Python314\python.exe "CAMINHO\auditoria_final_pos_chaos_c1c_turno156_teste3_9.py" --repo "C:\Users\47796476817\Downloads\pasta organizada\projeto lay\projeto-laylay"
```

Fechamento esperado somente se todos os gates passarem:

```text
✅ C1-C CLOSED — SEGUNDA AUDITORIA PÓS-CHAOS PASSOU
   C1-B2 end-to-end: CLOSED pela regressão real do turno 155
   C1-C turno 156 `esquerda`: CLOSED
   C1-D `agora a calculadora`/`direita`: OPEN, sem fechamento por tabela
   produção alterada pelo auditor: NÃO
```

Se qualquer gate falhar, C1-C permanece OPEN e a primeira fronteira vermelha
manda no diagnóstico. Não enfraquecer lock nem teste.

---

# ATUALIZAÇÃO SOBERANA — 18/08/2026 14H30 — C1-B2 E C1-C FORMALMENTE CLOSED

> Esta seção supersede o estado pendente da atualização 14H17.
>
> Estado oficial:
>
> ```text
> HEAD: a181b7bec50409dd7d3f976b3172389f76df7b8f
> parent: de749453599db0201f9f4cac20e2dc664d4a7b4a
> baseline commit: teste 3.9
> diff soberano C1-C:
> 88e0cd1e3ba52fb750fd90a332b8dad53ad3f6de51d5294b90841bb840e80e05
>
> C1-B2 end-to-end: CLOSED
> C1-C `esquerda`: CLOSED
> C1-D `agora a calculadora` / `direita`: OPEN
> ```

## 65. Segunda auditoria pós-chaos — PASS integral

O usuário executou:

```text
auditoria_final_pos_chaos_c1c_turno156_teste3_9.py
```

Resultado integral:

```text
A HEAD + parent exatos ................................ PASS
B blobs parent/finais C1-C ............................ PASS
C gates causais preservados ........................... PASS
D artefatos chaos travados ............................ PASS
E patcher commitado por SHA-256 ....................... PASS
F changed-set produção = exatamente 4 ................ PASS
G diff soberano reproduzido ........................... PASS | +189/-13
H checkout/index causal limpo ......................... PASS
I contrato autoridade→alvo→proveniência ............... PASS
J porta pública + árbitro preservados ................. PASS
K produtor do shape C1-C único ........................ PASS
L C1-D `direita` ausente do detector C1-C ............. PASS
M chaos 154-159 localizado uma única vez .............. PASS
N turno 155 `maximiza` executor+confirmação ........... PASS
O turno 156 `esquerda` executor+geometria confirmada .. PASS
P turno 157 `agora a calculadora` sem efeito .......... PASS
Q turno 158 `direita` sem efeito ...................... PASS
R turno 159 `fecha ela` continuidade preservada ....... PASS
S relatório não marca 155/156 como erro ............... PASS
```

Banner final:

```text
✅ C1-C CLOSED — SEGUNDA AUDITORIA PÓS-CHAOS PASSOU
   C1-B2 end-to-end: CLOSED pela regressão real do turno 155
   C1-C turno 156 `esquerda`: CLOSED
   C1-D `agora a calculadora`/`direita`: OPEN, sem fechamento por tabela
   produção alterada pelo auditor: NÃO
```

## 66. Por que C1-C agora pode ser fechado sem ressalva

A cadeia obrigatória foi provada integralmente:

```text
fala real
→ turno congelado
→ autoridade da fala atual
→ contexto fornece somente alvo
→ reconciliação H
→ especialista
→ detector determinístico
→ proveniência contextual estreita
→ coordenador
→ árbitro
→ porta pública
→ executor real
→ releitura da geometria
→ publicação
→ confirmação
→ chaos
→ segunda auditoria
```

Não existe mais dependência de:

```text
mirror artificial
executor spy
callback sintético
gate falso
inferência baseada apenas em shape
```

## 67. C1-B2 end-to-end também está CLOSED

Turno 155:

```text
maximiza
→ MAXIMIZE_WINDOW
→ alvo=opera
→ status=janela_maximizada
→ executou=True
→ confirmado=True
```

Portanto o root histórico do 155 finalmente possui evidência soberana de runtime real + chaos.

Estado:

```text
C1-B1 ........................ CLOSED
C1-B2 detector ............... CLOSED
C1-B2 end-to-end ............. CLOSED
```

## 68. C1-C CLOSED

Turno 156:

```text
esquerda
→ ORGANIZAR_DESKTOP
→ left=opera
→ modo=posicionar
→ referencia_contextual=True
→ referencia_contextual_fonte=turno_atual.referencia_resolvida
→ direcao_original=esquerda
→ status=layout_confirmado
→ executou=True
→ confirmado=True
```

A confirmação real relê a geometria da janela e compara com o lado solicitado.

Estado:

```text
C1-C implementação ........... CLOSED
C1-C produção ................ CLOSED
C1-C porta pública ........... CLOSED
C1-C executor/publicação ..... CLOSED
C1-C chaos ................... CLOSED
C1-C segunda auditoria ....... CLOSED
```

## 69. Não houve fechamento por tabela de C1-D

No mesmo chaos:

```text
157 agora a calculadora
→ nenhum comando

158 direita
→ nenhum comando
```

Logo:

```text
C1-D `agora a calculadora` ... OPEN
C1-D `direita` ............... OPEN
```

Isso é desejável.

A ausência de efeito prova que o patch C1-C permaneceu estreito e não generalizou `direita`.

## 70. Roots laterais continuam separados

Não misturar com C1-D ou C1-C:

```text
turno 112 `Maximiza ele.`
→ possível dívida de coerência fala/confirmabilidade

turno 179 `Fecha ela.`
→ comando cru FECHA + CLOSE_APP; root lateral de plano/IA

turno 189 lembrete
→ provável falso positivo do avaliador semântico

latência/confirmabilidade global do chaos no SENAI
→ ambiente/dependências externas; root separado
```

Nenhum desses sintomas reabre C1-B2 ou C1-C.

## 71. Próximo root soberano

Próximo corredor:

```text
157 agora a calculadora
158 direita
```

Nome de trabalho:

```text
C1-D — CONTINUAÇÃO DE LAYOUT / TROCA DE ALVO + DIREÇÃO
```

Antes de qualquer patch:

1. congelar comportamento atual;
2. decidir semanticamente o contrato de `agora a calculadora`;
3. separar mudança de alvo de execução;
4. provar se `direita` herda apenas o alvo tipado correto;
5. repetir falsificações de pergunta, negação, metalinguagem e pendência ativa;
6. não reutilizar C1-C de forma ampla;
7. não tocar em C1-B2/C1-C fechados sem nova evidência causal.

**C1-B2 e C1-C não devem mais ser modificados durante C1-D sem prova explícita de regressão.**


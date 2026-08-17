# HANDOFF INTERNO — PROJETO LAYLAY
Atualizado em: 2026-08-17 13:08 (America/Sao_Paulo)

# ESTADO ATUAL — C1 CANDIDATO VERDE / PATCH DE PRODUÇÃO PRONTO

ESTA SEÇÃO SUPERA estados/próximos passos anteriores em caso de conflito.

## HEAD confirmado

`bb69e24ef7be9b6d96d4f5f26f6f1264c1d78a69` — `teste 3.4`

O HEAD foi rechecado após a auditoria do candidato e continua sem commit novo.

Blobs travados:
- `contexto_compartilhado.py`:
  `d6523c919acbb68ef8d7a6f298746211e3855b9c`
- `contexto_imediato.py`:
  `0a1f20628ca096e50b1e56319ad6ff2ed6ef4f56`
- `resultado_acao.py`:
  `310c605e2bf5fcf3ba17cb1eb6bab8009b60c204`

## C1 — RED causal confirmado

Runner:
`red_c1_turno159_referencia_noop_confirmado_teste3_4_v2.py`

Resultado real:
- guards verdes: PASS;
- RED buffer: esperado;
- RED ponte `fecha ela`: esperado;
- regressivos focados: PASS;
- expected failures: 2;
- unexpected failures: 0;
- working tree preservada.

## C1 — candidato V2 VERDE EM ESPELHO

Auditor:
`auditar_candidato_c1_turno159_buffer_operacional_teste3_4_v2.py`

SHA-256:
`49fe5d641ac922c8fceeef1ddeda4ecd433f4fde4552ea576d42049372b6868e`

Resultado real informado pelo usuário:

```text
baseline guards .................... PASS
baseline RED buffer ................ RED esperado
baseline RED dominio ............... RED esperado
baseline RED ponte fecha-ela ....... RED esperado
candidate C1 completo .............. PASS
regressivos focados ................ PASS

CANDIDATO C1 VERDE EM ESPELHO
produção alterada: NÃO
working tree preservada: SIM
```

Conclusão:
**o candidato C1 foi aprovado em espelho antes de qualquer escrita de produção.**

## Política aprovada

A correção NÃO globaliza `confirmado=True`.

Novo conceito:
`estado já satisfeito referenciável`.

Whitelist inicial e única:

```text
(APP_OPEN, ja_aberto_focado)
```

Condições:
- `confirmado=True`;
- intent/status exatamente tipados;
- `executou=False` é permitido somente porque o executor provou que o estado
  desejado já estava satisfeito;
- referência transporta alvo/domínio;
- referência nunca transporta autoridade.

O caminho histórico de `executou=True` permanece.
Statuses contendo `sem_confirmacao` continuam bloqueados pela política atual.

## Produção que o patch poderá alterar

Somente:
1. `mente_laylay/memoria_mental/contexto_compartilhado.py`
2. `mente_laylay/memoria_mental/contexto_imediato.py`

Fonte causal somente lida e congelada:
3. `mente_laylay/memoria_mental/resultado_acao.py`

Nova regressão:
4. `tests/test_regressao_c1_turno159_buffer_operacional.py`

Nenhum outro fonte deve mudar.

## Arquivo criado — regressão permanente de referência

`test_regressao_c1_turno159_buffer_operacional.py`

SHA-256:
`cb2990087c03bc015dfdafe8b5e9bda67a044adfd837cce4ad43f0e69aa27e01`

Estado:
**fonte permanente pronta / AST PASS / 13 testes**.

A V2 passou a ter 13 testes porque o guard incorreto anterior foi separado em
dois contratos corretos:
- execução real com status neutro continua promovível;
- `executado_sem_confirmacao` continua não-promovível.

Cobertura:
- 10 guards;
- 3 contratos causais antes vermelhos:
  - promoção no buffer;
  - domínio do contrato;
  - ponte `fecha ela`.

## Arquivo criado — patcher de produção C1

`patch_c1_turno159_buffer_operacional_teste3_4.py`

SHA-256:
`ed08cc99ed97d2624564f0a4f9528c7dbb03372db52d9f959ef0f7fddc54c2a0`

Estado:
**patch pronto / AST PASS / py_compile PASS / --help PASS**.

O patcher:
1. trava HEAD e os 3 blobs;
2. exige fontes causais localmente limpas;
3. exige regressão permanente ausente;
4. preserva status de arquivos não relacionados;
5. cria baseline e candidato limpos por `git archive HEAD`;
6. repete baseline guards + 3 REDs causais;
7. aplica candidato somente no espelho;
8. roda a regressão C1 permanente no espelho;
9. roda regressivos focados:
   - adaptador de resultado;
   - P0 autorização/modalidade;
   - R1.1;
   - M1 linguístico;
   - M1 wiring;
   - patch20 R1/R2;
10. revalida HEAD/blobs/status antes da escrita;
11. escreve somente os 2 fontes + regressão;
12. preserva BOM e CRLF/LF dos fontes reais;
13. roda `py_compile`;
14. roda regressão permanente de 13 testes;
15. roda todos os regressivos focados novamente no worktree real;
16. exige `resultado_acao.py` byte-intacto;
17. audita whitelist única `(APP_OPEN, ja_aberto_focado)`;
18. audita os 2 usos do predicado em `contexto_imediato.py`;
19. gera diff/log/manifest fora do repo;
20. em falha após escrita, restaura fontes byte-a-byte e remove somente a
    regressão nova;
21. nunca executa add/commit/push/reset/checkout/restore.

Artefatos esperados após execução:

`laylay_patch_artifacts_c1_turno159/`
- `c1_turno159_buffer_operacional.diff`
- `manifest_c1_turno159_buffer_operacional.json`
- `log_c1_turno159_buffer_operacional.txt`

## Comando

```powershell
& C:\Python314\python.exe ".\patch_c1_turno159_buffer_operacional_teste3_4.py" --repo .
```

## Resultado esperado

```text
baseline guards .................... PASS
baseline RED buffer ................ RED esperado
baseline RED domínio ............... RED esperado
baseline RED ponte fecha-ela ....... RED esperado
candidate regressão C1 ............. PASS
candidate regressivos focados ...... PASS
produção escrita ................... SIM
regressão permanente (13 testes) ... PASS
regressivos focados reais .......... PASS
resultado_acao.py .................. INTACTO
working tree não relacionado ....... PRESERVADO

PATCH C1 APLICADO E VALIDADO
```

Após green:
- NÃO fechar C1 ainda;
- NÃO assumir que 154→159 inteiro foi resolvido;
- analisar diff + manifest;
- rodar novo caos / corredor real 154→159;
- observar quais turnos melhoraram naturalmente;
- separar C1-B/C1-C para qualquer falha restante.

## Regra de artefatos/handoff

Mantida:
**qualquer arquivo criado para Laylay exige atualização do handoff na mesma etapa.**

Arquivos criados nesta etapa:
1. `test_regressao_c1_turno159_buffer_operacional.py`
2. `patch_c1_turno159_buffer_operacional_teste3_4.py`
3. `HANDOFF_LAYLAY_2026-08-17_ATUALIZADO_13H08_C1_PATCH_PRONTO.md`

---

# HISTÓRICO ANTERIOR PRESERVADO

Quando houver conflito, prevalece o estado 13:08 acima.

# HANDOFF INTERNO — PROJETO LAYLAY
Atualizado em: 2026-08-17 13:04 (America/Sao_Paulo)

# ESTADO ATUAL — C1 CANDIDATO V2 APÓS GUARD INCORRETO

ESTA SEÇÃO SUPERA estados/próximos passos anteriores em caso de conflito.

## HEAD

`bb69e24ef7be9b6d96d4f5f26f6f1264c1d78a69` — `teste 3.4`

## RED C1

Continua **causalmente confirmado** pelo runner RED V2 anterior:

- guards verdes: PASS;
- buffer `ja_aberto_focado`: RED esperado;
- ponte `fecha ela`: RED esperado;
- regressivos focados: PASS;
- 2 expected failures;
- 0 unexpected failures;
- working tree preservada.

## Auditor de candidato V1 — RECUSADO CORRETAMENTE

Arquivo:

`auditar_candidato_c1_turno159_buffer_operacional_teste3_4.py`

Estado:
**descartado como auditor válido do candidato**.

Motivo:
um guard congelou uma semântica errada:

```text
executou=True
confirmado=False
status=executado_sem_confirmacao
→ esperado no V1: promovível=True
```

Mas `_resultado_pode_promover_referencia()` rejeita statuses com marcador
`sem_confirmacao` antes de chegar ao fallback `contrato.executou is True`.

Baseline correto:

```text
executou=True
confirmado=False
status=executado_sem_confirmacao
→ ultima_acao_promovivel=False
```

A recusa foi segura:
- ocorreu nos guards do baseline;
- nenhum candidato foi aceito;
- produção não foi escrita.

## Auditor de candidato V2

Novo arquivo:

`auditar_candidato_c1_turno159_buffer_operacional_teste3_4_v2.py`

SHA-256:

`49fe5d641ac922c8fceeef1ddeda4ecd433f4fde4552ea576d42049372b6868e`

Estado:
**pronto para execução / AST PASS / compile PASS**.

Correção dos guards:

1. caminho histórico realmente promovível:

```text
executou=True
confirmado=False
status=executado
→ promovível=True
```

2. bloqueio explícito preservado:

```text
executou=True
confirmado=False
status=executado_sem_confirmacao
→ promovível=False
```

Todo o restante permanece com o mesmo objetivo:
- 3 REDs causais separados: buffer, domínio e ponte `fecha ela`;
- candidato somente em espelho;
- whitelist estreita apenas para `(APP_OPEN, ja_aberto_focado)`;
- P0, R1.1 e M1 focados;
- sem escrita em produção;
- sem Git mutante;
- working tree preservada.

## Próximo passo

Rodar:

```powershell
& C:\Python314\python.exe ".\auditar_candidato_c1_turno159_buffer_operacional_teste3_4_v2.py" --repo .
```

Esperado:

```text
baseline guards .................... PASS
baseline RED buffer ................ RED esperado
baseline RED domínio ............... RED esperado
baseline RED ponte fecha-ela ....... RED esperado
candidate C1 completo .............. PASS
regressivos focados ................ PASS
```

Se houver divergência:
**parar e estudar; não adaptar o teste por reflexo.**

## Regra de artefatos

Mantida: qualquer arquivo criado para Laylay exige handoff atualizado.

Arquivos desta etapa:
- `auditar_candidato_c1_turno159_buffer_operacional_teste3_4_v2.py`;
- `HANDOFF_LAYLAY_2026-08-17_ATUALIZADO_13H04_C1_CANDIDATO_V2.md`.

---

# HISTÓRICO ANTERIOR PRESERVADO

Quando houver conflito, prevalece o estado 13:04 acima.

# HANDOFF INTERNO — PROJETO LAYLAY
Atualizado em: 2026-08-17 12:53 (America/Sao_Paulo)

# ESTADO ATUAL — C1 RED CONFIRMADO / CANDIDATO EM ESPELHO

ESTA SEÇÃO SUPERA estados/próximos passos anteriores quando houver conflito.

## HEAD travado

`bb69e24ef7be9b6d96d4f5f26f6f1264c1d78a69` — `teste 3.4`

Blobs causais:
- `mente_laylay/memoria_mental/contexto_compartilhado.py`
  `d6523c919acbb68ef8d7a6f298746211e3855b9c`
- `mente_laylay/memoria_mental/contexto_imediato.py`
  `0a1f20628ca096e50b1e56319ad6ff2ed6ef4f56`
- `mente_laylay/memoria_mental/resultado_acao.py`
  `310c605e2bf5fcf3ba17cb1eb6bab8009b60c204`

## C1 RED — PROVA CAUSAL CONFIRMADA

Runner válido:
`red_c1_turno159_referencia_noop_confirmado_teste3_4_v2.py`

SHA-256:
`b855bd257d6b151dcb034315c1eb93cc8dff2084d55a51c61918655ba826546a`

Resultado real informado pelo usuário:

```text
guards verdes ...................... PASS
buffer ja_aberto_focado ............ RED esperado
ponte fecha-ela ..................... RED esperado
regressivos focados ................. PASS

expected failures: 2
unexpected failures: 0
unexpected passes: 0

PROVA C1: VERMELHO CAUSAL CONFIRMADO
produção alterada: NÃO
working tree preservada: SIM
```

Conclusão:
**a C1 deixou de ser hipótese e virou causa executavelmente provada.**

## Runner V1 — histórico descartado

`red_c1_turno159_referencia_noop_confirmado_teste3_4.py`

SHA-256:
`6a15d1caf468ad78a2f73ed252cfb3de65966df06e350e1f0a51674b7fa7004f`

Estado:
**descartado como prova**.

Motivo:
o lock de `contexto_compartilhado.py` estava incorreto.
O runner recusou no preflight; produção não foi testada nem alterada.

## Causa arquitetural C1

O contrato causal já considera válido:

```text
APP_OPEN
status=ja_aberto_focado
executou=False
confirmado=True
```

Semântica:
- nenhuma mutação foi necessária;
- o app existe;
- o app está em foco;
- o estado desejado foi confirmado.

A memória operacional ainda tinha gates antigos que dependiam de
`executou=True`:

1. `_resultado_pode_promover_referencia(...)`;
2. `_dominio_contrato_referencia(...)`;
3. ponte curta de `fecha ela`.

Corrigir somente um gate seria meia-correção.

## Política candidata

Novo conceito estreito:
**estado já satisfeito referenciável**.

Primeira e única entrada do candidato:

```text
(APP_OPEN, ja_aberto_focado)
```

Requisitos:
- `confirmado=True`;
- intent e status tipados exatamente;
- contexto/referência pode fornecer alvo;
- contexto/referência NUNCA aumenta autoridade.

Preservar:
- caminho histórico de promoção por `executou=True`;
- falhas e no-ops arbitrários continuam bloqueados;
- status de outro intent não ganha referência;
- TTL continua valendo;
- tentativa posterior falha não apaga app válido;
- P0/R1.1 continuam soberanos.

Não generalizar agora para:
- `site_ja_aberto_focado`;
- IoT já ligado/desligado;
- playlists;
- notas;
- lembretes;
- qualquer `confirmado=True` genérico.

## Novo arquivo — auditor de candidato C1

`auditar_candidato_c1_turno159_buffer_operacional_teste3_4.py`

SHA-256:
`37ab0f4a722b17c422c605103b4923faeeb2a462535e691f5f9cb304abf6b8d3`

Estado:
**gerado / AST PASS / py_compile PASS / --help PASS / aguardando execução no repo**.

Ele NÃO escreve produção.

Fluxo:
1. trava HEAD + blobs;
2. exige fontes causais localmente limpas;
3. cria baseline e candidate com `git archive HEAD`;
4. prova baseline:
   - guards verdes;
   - RED buffer;
   - RED domínio;
   - RED ponte `fecha ela`;
5. aplica candidato apenas no espelho;
6. exige teste C1 completo verde;
7. roda regressões focadas:
   - `test_adaptador_resultado.py`;
   - P0 autorização/modalidade;
   - R1.1;
   - M1 linguístico;
   - M1 wiring;
8. gera diff, manifest e log fora do repo;
9. aceita diff somente em:
   - `contexto_compartilhado.py`;
   - `contexto_imediato.py`;
10. exige fontes reais byte-idênticas no fim;
11. exige working tree final idêntico;
12. não usa git add/commit/push/reset/checkout/restore.

## Próximo passo

Rodar na raiz:

```powershell
& C:\Python314\python.exe ".\auditar_candidato_c1_turno159_buffer_operacional_teste3_4.py" --repo .
```

Esperado:

```text
baseline guards .................... PASS
baseline RED buffer ................ RED esperado
baseline RED domínio ............... RED esperado
baseline RED ponte fecha-ela ....... RED esperado
candidate C1 completo .............. PASS
regressivos focados ................ PASS

CANDIDATO C1 VERDE EM ESPELHO
produção alterada: NÃO
working tree preservada: SIM
```

Se ficar verde:
1. analisar saída completa;
2. auditar `candidate_c1_turno159.diff`;
3. auditar manifest;
4. só então criar patcher de produção + regressão permanente;
5. atualizar handoff na mesma etapa.

Não fazer commit ainda.

## Regra de artefatos

Mantida:
**qualquer arquivo criado para Laylay exige atualização do handoff na mesma etapa.**

Arquivos registrados/criados nesta etapa:
- runner V1 — histórico descartado;
- runner V2 — RED causal confirmado;
- `auditar_candidato_c1_turno159_buffer_operacional_teste3_4.py` — candidato em espelho;
- `HANDOFF_LAYLAY_2026-08-17_ATUALIZADO_12H53_C1_RED_CONFIRMADO_CANDIDATO.md` — este handoff.

Frase-guia:
**“Estudar primeiro, provar o vermelho, corrigir a causa raiz, reanalisar o patch pronto, só então entregar.”**

---

# HISTÓRICO ANTERIOR PRESERVADO

Quando houver conflito, prevalece o estado 12:53 acima.

# HANDOFF INTERNO — PROJETO LAYLAY
Atualizado em: 2026-08-17 11:41 (America/Sao_Paulo)
Objetivo: continuidade segura em novos chats.

# ESTADO ATUAL 11:41 — C1-A RED CRIADO

ESTA SEÇÃO SUPERA estados/próximos passos anteriores quando houver conflito.

## HEAD atual

`bb69e24ef7be9b6d96d4f5f26f6f1264c1d78a69`

Mensagem:

`teste 3.4`

M1 / turno 149:
**FECHADA end-to-end.**

Próxima raiz:
**C1 — buffer de referência/memória operacional de apps.**

---

## Descoberta C1 no caos 3.4

Sequência real relevante:

154. `Abre o Opera.`
155. `maximiza`
156. `esquerda`
157. `agora a calculadora`
158. `direita`
159. `fecha ela`

No turno 154:

```text
APP_OPEN opera
aberto=True
foco=True
status=ja_aberto_focado
executou=False
confirmado=True
```

No 155:

```text
maximiza
→ nenhuma intent operacional
→ cai na IA
```

No 156:

```text
esquerda
→ nenhuma intent operacional
```

No 157:

```text
agora a calculadora
→ cai em conversa
```

No 158:

```text
direita
→ nenhuma intent operacional
```

No 159:

```text
fecha ela
→ LLM publica intent não canônica `fechar_janela`
→ alvo `calculadora`
→ executor não reconhece
```

Conclusão nova:

C1 não é apenas “corrigir `fecha ela`”.
Existe um problema mais fundamental de **buffer de memória operacional**:
o runtime observa um app/alvo e confirma seu estado, mas pode perder a
referência porque nenhuma mutação precisou acontecer.

---

## Causa candidata C1-A — fortemente sustentada, agora materializada em RED

Arquivo:

`mente_laylay/memoria_mental/contexto_imediato.py`

Blob no HEAD 3.4:

`0a1f20628ca096e50b1e56319ad6ff2ed6ef4f56`

Dois pontos atuais exigem simultaneamente:

```text
executou=True
confirmado=True
```

1. `_dominio_contrato_referencia(...)`
2. bridge de `fecha_referencia_curta` para:
   - `OPEN_URL`
   - `SWITCH_PREVIOUS_TAB`
   - `APP_OPEN`
   - `MAXIMIZE_WINDOW`

Isso mistura dois conceitos:

```text
executou=True
= houve mutação/ação efetiva

confirmado=True
= o estado/alvo foi observado e comprovado
```

Para memória/referência operacional, um estado satisfeito conhecido pode ser
referenciável sem ter exigido mutação.

Caso real canônico:

```text
APP_OPEN
status=ja_aberto_focado
executou=False
confirmado=True
```

Semântica desejada:
- não repetir abertura;
- mas manter o app como referente operacional forte.

---

## Arquivo criado — RED C1-A

`test_red_c1_buffer_referencia_operacional_teste3_4.py`

SHA-256:

`566f106833e7fa8b7a5897aade24088d63b7a33760a1a43bca11b4a6fcc4fc75`

Estado:
**RED criado / sintaxe validada / aguardando execução no repo do usuário.**

Baseline alvo:
- HEAD `bb69e24...`;
- blob `contexto_imediato.py` `0a1f206...`.

O teste NÃO modifica produção.

Matriz esperada no baseline:

- 6 GUARDS devem passar;
- 2 REDS devem falhar.

### RED 1

`APP_OPEN + executou=False + confirmado=True + status=ja_aberto_focado`

com:

`fecha ela`

deve recuperar:

```text
tipo=app
alvo=opera
intencao=APP_OPEN
origem_continuidade=contrato_confirmado
```

Hoje a hipótese é que falha devido ao gate `executou is True`.

### RED 2

O mesmo contrato deve fazer:

```python
_dominio_contrato_referencia(...) == "app"
```

Hoje a hipótese é que retorna `""` pelo mesmo gate.

### Guards

1. `APP_OPEN executou=True confirmado=True` continua referenciável;
2. no-op não confirmado não vira referência;
3. no-op confirmado com status arbitrário não vira referência;
4. `ja_aberto_focado` em intent de outro domínio não vira permissão global;
5. executado sem confirmação não define domínio;
6. no-op confirmado com status arbitrário não define domínio.

Direção de segurança:

**NÃO substituir globalmente `executou=True` por `confirmado=True`.**

A correção futura, se o RED confirmar a hipótese, deve reconhecer pares
estreitos de resultado/intent que provem **estado desejado já satisfeito**.

Primeiro candidato conceitual:

```text
(APP_OPEN, ja_aberto_focado)
```

Nada além disso sem nova evidência.

---

## Importante: C1-A não promete corrigir 155–159 inteira

O RED atual prova somente a fundação:

**estado confirmado → referência operacional persistente**

Os turnos:

- `maximiza`
- `esquerda`
- `agora a calculadora`
- `direita`

podem revelar subraízes próprias de linguagem/continuidade depois que C1-A
for corrigida.

Não colocar tudo em um mega-patch.

Fluxo:

```text
C1-A RED
→ provar baseline
→ estudar menor contrato de estado satisfeito
→ candidato C1-A
→ regressões
→ runtime real
→ reavaliar 155–159
→ somente então C1-B/C1-C se necessário
```

---

## Próximo passo obrigatório

Rodar na raiz do projeto:

```powershell
& C:\Python314\python.exe -m pytest -q ".\test_red_c1_buffer_referencia_operacional_teste3_4.py"
```

Se `C:\Python314` não tiver pytest, usar o Python/venv que já roda pytest no
projeto.

Esperado:
- 6 pass;
- 2 fail;
- as duas falhas devem ser exatamente os testes com prefixo `test_c1_red_`.

Se a fotografia for diferente:
**parar e estudar o resultado; não adaptar teste por reflexo.**

---

## Regra de artefatos/handoff

Mantida:

**Sempre que qualquer arquivo for criado para a Laylay, atualizar o handoff na
mesma etapa.**

Nesta etapa foram criados:
1. `test_red_c1_buffer_referencia_operacional_teste3_4.py`
2. `HANDOFF_LAYLAY_2026-08-17_ATUALIZADO_11H41_C1_RED.md` — este próprio handoff atualizado.

Frase-guia:

**“Estudar primeiro, provar o vermelho, corrigir a causa raiz, reanalisar o patch pronto, só então entregar.”**

---

# HISTÓRICO ANTERIOR PRESERVADO

Quando houver conflito, prevalece o estado 11:41 acima.

# HANDOFF INTERNO — PROJETO LAYLAY
Atualizado em: 2026-08-17 11:34 (America/Sao_Paulo)
Objetivo: continuidade segura em novos chats.

# ESTADO ATUAL 17/08 11:34 — TESTE 3.4 — M1 FECHADA

ESTA SEÇÃO SUPERA qualquer estado/próximo passo anterior quando houver conflito.

## HEAD atual confirmado

`bb69e24ef7be9b6d96d4f5f26f6f1264c1d78a69`

Mensagem:

`teste 3.4`

Anterior:

`55f10bf9b0fe58dbe52c0412d694a3611af2ccf9` — `teste 3.3`

## M1 / turno 149 — FECHADA POR PROVA END-TO-END

Frase:

`Vai para a próxima faixa e adiciona essa também na caos sonora.`

No teste 3.4 o runtime real executou:

1. `MEDIA_CONTROL(next)`
   - `executou=True`
   - `confirmado=None`
   - status `midia_next_playlist`
   - o `None` é esperado para este executor quando há confirmação de envio,
     mas não prova externa do estado final do player.

2. `PLAYLIST_ADD("caos sonora")`
   - origem: `prioritario-cooperativo-2`
   - `referencia_contextual=True`
   - `executou=True`
   - `confirmado=True`
   - status `playlist_musica_adicionada`
   - música adicionada no teste: `Bad Girl`
   - evidência: persistência local da playlist.

Logo depois, a listagem real de `caos sonora` mostrou:

- `Tipo Rick E Morty`
- `Bad Girl`

Portanto a segunda etapa não apenas nasceu: ela executou, confirmou e ficou
persistida/observável no fluxo real.

O relatório semântico 3.4 marcou o turno 149 como ALERTA, não falha:

`Intents: MEDIA_CONTROL, PLAYLIST_ADD`

O alerta restante é:

`etapas_sem_confirmacao_externa:1`

Ele se refere ao `MEDIA_CONTROL` com `confirmado=None`, não à M1 de playlist.

Conclusão:

**M1 está oficialmente FECHADA.**

Não reabrir:
- gramática estreita de `vai para a próxima faixa`;
- segmentação da cadeia;
- modalidade/autorização M1;
- detector de playlist contextual nomeado;
- wiring `_musica_estado_get -> musica_estado_get`;

sem nova evidência concreta.

## Patch M1 wiring incorporado no teste 3.4

Produção:
`mente_laylay/autonomia/coordenador_intencao.py`

Linha funcional:
```python
"musica_estado_get": contexto_execucao.get("_musica_estado_get"),
```

Regressão permanente:
`tests/test_regressao_m1_turno149_wiring_playlist_contexto.py`

Manifest auditado antes do caos:
- HEAD baseline: `55f10bf9b0fe58dbe52c0412d694a3611af2ccf9`
- blob coordenador baseline:
  `b2b1450e7b3e61152ba31af1736304c2c3229a60`
- RED baseline: causal
- candidato espelho: verde
- produção local: verde
- dependências do ciclo: intocadas
- sem auto add/commit/push
- SHA diff:
  `251293080fe84693bafddfd8c7f33f608514056a441677d3f4598c443164d5d1`
- SHA regressão:
  `8048c6c5ff3f7e8ed39ba15bd03ee230bc488101ce5118c7e681643be19f2a34`

## Caos 3.4

Diretório:

`resultados_testes/roteiro_teste_laylay_caos-20260817-111950-021531/`

Resumo:
- 267/267 respondidos;
- 54 avaliados semanticamente;
- 29 passaram;
- 23 falharam;
- 2 alertas;
- taxa semântica: 53,7%;
- p50: 2,148 s;
- p95: 7,341 s;
- máxima: 37,346 s;
- média: 2,842 s;
- 10 etapas com `confirmado=None`.

Domínios:
- browser: 8 pass / 0 fail;
- segurança: 9 pass / 0 fail;
- iot: 3 pass / 0 fail;
- arquivos: 3 pass / 3 fail;
- apps: 4 pass / 2 fail;
- música: 0 pass / 2 fail / 2 alertas;
- conversa: 0 pass / 16 fail.

Importante:
o placar global não melhorou em quantidade total de pass porque o turno 149
continua classificado como alerta devido à confirmação externa da etapa de
mídia. Porém a falha funcional M1 foi corrigida end-to-end.

## Higiene do commit 3.4

O commit contém corretamente:
- patch M1 de produção;
- regressão permanente M1;
- resultados completos do caos 3.4.

Também contém um arquivo não relacionado à M1:
`melhorias e planos/NOTA_CLAUDE_IDEIAS_FUTURAS.md`

Isso não invalida o patch/teste, mas o commit não é totalmente isolado em
escopo. Em futuros commits continuar conferindo `git status --short` e
selecionando arquivos intencionalmente.

## PRÓXIMA RAIZ: C1 / turno 159

Agora a prioridade passa para C1.

Sequência relevante:
154 `Abre o Opera.`
155 `maximiza`
156 `esquerda`
157 `agora a calculadora`
158 `direita`
159 `fecha ela`

Hipótese/causa estudada antes:
- `APP_OPEN` pode retornar `executou=False`, `confirmado=True`,
  status `ja_aberto_focado`;
- isso é estado confirmado/no-op desejado, não falha;
- o bridge de referência curta historicamente exigia
  `executou=True AND confirmado=True`;
- assim um app já aberto/focado podia deixar de ser promovido como referência;
- t159 então caía no caminho errado/LLM e publicava contrato incompleto.

Princípio C1:
**confirmação de estado pode promover referência mesmo sem mutação, mas somente
para statuses tipados e seguros que provem o estado desejado.**

Reds recomendados antes de patch:
1. `APP_OPEN executou=True confirmado=True` continua promovendo;
2. `APP_OPEN executou=False confirmado=True status=ja_aberto_focado`
   deve promover;
3. `executou=False confirmado=False` continua bloqueado;
4. no-op confirmado de outro domínio não sequestra referência.

NÃO fazer patch C1 antes de reler o HEAD `bb69e24...`, blobs atuais e o fluxo
real do turno 154–159 no caos 3.4.

## REGRA NOVA DE HANDOFF

A pedido do usuário:

**Sempre que o ChatGPT criar QUALQUER arquivo relacionado à Laylay, deve também
atualizar o handoff na mesma etapa.**

Vale para:
- patchers;
- testes;
- auditores;
- manifests;
- diffs;
- scripts;
- relatórios;
- markdowns;
- qualquer outro artefato persistente/relevante.

O handoff deve registrar, quando aplicável:
- nome do arquivo;
- finalidade;
- estado (rascunho/candidato/aplicado/auditado/descartado);
- SHA-256;
- baseline/HEAD;
- próximo passo.

Frase-guia permanece:

**“Estudar primeiro, provar o vermelho, corrigir a causa raiz, reanalisar o patch pronto, só então entregar.”**

---

# HISTÓRICO ANTERIOR PRESERVADO

O conteúdo abaixo permanece para auditoria histórica.
Quando houver conflito, prevalece o estado 11:34 / teste 3.4 acima.

# HANDOFF INTERNO — PROJETO LAYLAY
Data-base original: 2026-08-16
Atualizado em: 2026-08-17 10:54 (America/Sao_Paulo)
Objetivo: continuidade segura em novos chats sem perder o histórico técnico.

# ESTADO ATUAL 17/08 — LEIA PRIMEIRO — ESTA SEÇÃO SUPERA AS ANTERIORES

Esta seção é a fonte de verdade mais nova deste handoff.
Quando houver conflito com qualquer “próximo passo”, HEAD, baseline, status ou
prioridade escrito nas seções históricas abaixo, ESTA SEÇÃO TEM PRECEDÊNCIA.

## A. HEAD / baseline atual

HEAD remoto confirmado no GitHub:

`55f10bf9b0fe58dbe52c0412d694a3611af2ccf9`

Mensagem:

`teste 3.3`

Commit imediatamente anterior relevante:

`06bc15d847ee5fd77ae520187953423fe76a2bda`

Mensagem:

`teste 3.2`

Baseline anterior:

`9538523a22e452481aec6d0f664de08f5a49dd5c`

Mensagem:

`teste 3.2`

IMPORTANTE:
- não assumir que o working tree local é idêntico ao HEAD remoto;
- antes de qualquer novo patch, rodar/consultar `git status --short`;
- nunca reaplicar patch já presente;
- nunca usar somente a mensagem do commit para inferir quais mudanças estão no
  working tree;
- o patch M1 de wiring descrito mais abaixo AINDA NÃO deve ser considerado
  aplicado até existir saída real da execução do usuário.

---

## B. Método obrigatório de trabalho — versão consolidada

Fluxo canônico:

**Estudar primeiro → provar o vermelho → corrigir a causa raiz → reanalisar o
patch pronto → só então entregar.**

Para qualquer nova raiz:

1. confirmar HEAD/branch/blobs atuais;
2. estudar o fluxo real antes de sugerir correção;
3. procurar consumidores upstream/downstream;
4. tentar falsificar a hipótese;
5. materializar RED específico;
6. guardrails existentes precisam ficar verdes;
7. o RED precisa falhar pelo motivo causal previsto;
8. só então desenhar a menor mudança de produção;
9. testar em espelho limpo quando possível;
10. reanalisar patch + testes + anchors antes de entregar;
11. patcher deve ter locks, backup, diff, manifest e rollback;
12. não fazer `git add`, commit ou push automaticamente;
13. após o usuário executar, auditar saída + diff + manifest REAIS;
14. só fechar a raiz depois de regressão/caos real quando a raiz depende do
    runtime integrado.

Não aceitar como causa raiz:
- primeira regex que parece faltar;
- primeiro exemplo reproduzido;
- primeira correção que faz uma frase passar;
- “ficou verde” sem provar que o laboratório/teste estava correto.

RUNNER É PARTE DA PROVA:
- verificar que o Python escolhido possui pytest;
- `.venv314\Scripts\python.exe` já foi runner válido em etapas anteriores;
- não interpretar falha do harness como falha de produção.

---

# C. R1.1 — AUTORIDADE / ABA ANTERIOR — FECHADA

R1.1 foi fechada antes do M1 e NÃO deve ser reaberta sem nova evidência real.

Objetivo que foi corrigido:
- preservar autoridade explícita do turno;
- separar gramática explícita de “aba anterior” de elipse contextual;
- impedir que detectores/candidatos elevem autoridade;
- preservar cadeias reais sem fabricar autorização.

Arquivos de produção envolvidos na R1.1:
- `mente_laylay/cognicao/referencias_linguagem.py`
- `mente_laylay/cognicao/modalidade_turno.py`
- `mente_laylay/memoria_mental/contexto_imediato.py`
- `mente_laylay/autonomia/roteador_deterministico.py`
- `mente_laylay/cognicao/arbitro_turno.py`
- `mente_laylay/autonomia/comandos_imediatos.py`

Regressão permanente:
- `tests/test_regressao_r1_1_autoridade_navegador_cadeia.py`

Contratos importantes:
- `retorna ... aba anterior` explícito é suportado;
- `volta/volte ... anterior` contextual estreito é preservado;
- `retorna/vai ... anterior` genérico não deve ser congelado como comportamento
  desejado;
- detector/candidato nunca aumenta autoridade;
- o turno congelado controla efeitos;
- contexto pode resolver referência/alvo, mas nunca criar autorização.

Helper crítico:
`_candidato_prioritario_autorizado`

Regras dele:
- candidato malformado -> false;
- read-only -> pode passar;
- candidato com efeito -> exige `turno.autoriza_execucao`.

NÃO enfraquecer/remover esse helper para consertar M1 ou qualquer outra raiz.

Validações R1.1 registradas:
- snapshot V1: 23 passed;
- snapshot V2: 30 passed;
- regressão permanente final: 44 passed;
- regressões focadas existentes: 92 passed.

Caos real:
- turno 145 passou corretamente:
  `SWITCH_PREVIOUS_TAB → LIST_TABS(somente_ativa=True)`;
- ambas as etapas ficaram confirmadas;
- a aba ativa retornada foi Wikipédia.

Artefatos históricos R1.1:
- `patch_r1_1_v2_turno145_autoridade_navegador_3_2.py`
  SHA-256:
  `fbf30c3226ed20d370d0f3516c8bbf9742c0861568f3d30e198fc8e6dc5c080d`
- microfix test-only:
  `microfix_test_only_r1_1_remove_gap_freeze_v2.py`
  SHA-256:
  `f02b666e638e1caaa45b450a63eea574cb230c176f40e98c1f9f66785964f961`
- regressão R1.1 final:
  SHA-256:
  `dc739d331036aa06560a23b887d50c16da29c1c241cc3845a5a9bf7b93ccd704`

---

# D. ÚLTIMO CAOS REAL ANALISADO ANTES DO M1 3.3

Diretório analisado:

`resultados_testes/roteiro_teste_laylay_caos-20260817-082424-415052/`

Resumo:
- total: 267;
- respondidos: 267;
- semanticamente avaliados: 54;
- passaram: 29;
- falharam: 24;
- alertas: 1;
- taxa semântica: 53,7%;
- comandos observados: 110;
- confirmações indeterminadas: 9;
- p50: 2,029 s;
- p95: 8,275 s;
- máxima: 47,475 s;
- média: 2,901 s.

Por domínio relevante:
- navegador: 8 pass / 0 fail;
- música: 3 fail / 1 alert;
- conversa: 16 fail;
- apps: 2 fail;
- arquivos: 3 fail;
- segurança: 9 pass.

Erros:
`[22,44,68,69,70,78,79,85,89,91,92,96,113,116,123,126,133,149,155,159,171,174,227,257]`

Mudança mais importante:
- R1.1 resolveu o 145;
- turno 149 passou de alerta para falha;
- turno 159 também apareceu como falha relevante.

Não usar esse caos para afirmar que o M1 3.3 já foi validado end-to-end:
ele é a evidência que originou o trabalho, não um pós-fix definitivo.

---

# E. M1 — TURNO 149 — ESTADO ATUAL

Frase real:

`Vai para a próxima faixa e adiciona essa também na caos sonora.`

Objetivo:

1. avançar a faixa atual;
2. adicionar a nova faixa à playlist recente `caos sonora`;
3. preservar autoridade do turno;
4. não criar autoridade por contexto;
5. não transformar `vai` em verbo operacional global;
6. não inferir playlist arbitrária pelo nome.

## E1. Causa raiz linguística original — PROVADA

A investigação separou três contratos independentes.

### E1-A — segmentação da cadeia

Arquivo:
`mente_laylay/autonomia/analise_comandos.py`

Problema:
`_INICIO_ETAPA_OPERACIONAL` reconhecia `adiciona`, mas não a forma estreita
`vai para a próxima faixa`.

Consequência:
a fala real não era dividida com segurança em:

1. `Vai para a próxima faixa`
2. `adiciona essa também na caos sonora`

NÃO adicionar `vai` genérico à lista global.
Exemplo que deve continuar não operacional:
`Vai chover amanhã`.

### E1-B — modalidade/autoridade

Arquivo:
`mente_laylay/cognicao/modalidade_turno.py`

Forma canônica:
`Próxima faixa.`

já era autorizada.

Forma natural:
`Vai para a próxima faixa.`

não era.

Correção correta:
reconhecer somente a gramática estreita de avanço de mídia, inclusive a cadeia
M1, sem transformar `vai` em imperativo global.

### E1-C — playlist contextual nomeada

Arquivo:
`mente_laylay/autonomia/detectores_playlist.py`

Já funcionavam:
- `adiciona essa música na playlist caos sonora`;
- `essa também` quando existe `ultima_playlist`.

Não funcionava:
`adiciona essa também na caos sonora`

Contrato seguro:
- só inferir a palavra omitida `playlist` se o nome mencionado for EXATAMENTE o
  nome da playlist recente;
- recent=`caos sonora` + mencionado=`caos sonora` -> contextual válido;
- recent=`caos sonora` + mencionado=`rock` -> não reutilizar contexto;
- contexto resolve alvo; contexto não aumenta autoridade.

### Guard importante eliminado como falso suspeito

`detectar_volume_ou_midia()` em
`mente_laylay/autonomia/roteador_deterministico.py`

já reconhecia a fala inteira como:

`MEDIA_CONTROL(next)`

Não mexer nesse detector para M1.

---

# F. M1 — DESENHO REVISADO / TESTES — VALIDADO

O primeiro desenho tentou colocar semântica de mídia em
`normalizacao_linguagem.py`.

Esse desenho foi DESCARTADO porque o próprio módulo declara que normalização
não interpreta nem autoriza ações.

Regra:
**não colocar gramática semântica operacional em `normalizacao_linguagem.py`.**

Foi criado/desenhado um módulo dedicado:

`mente_laylay/cognicao/gramatica_operacional.py`

Responsabilidade:
- reconhecer linguagem operacional estreita;
- não resolver contexto;
- não escolher executor;
- não conceder autoridade por conta própria.

Helper M1:

`texto_pede_avanco_midia_via_vai(texto, permitir_cadeia=False)`

Deve reconhecer:
- `vai para a próxima faixa`;
- `Vai pra próxima música.`;
- a cadeia exata da família M1.

Deve rejeitar:
- `vai chover amanhã`;
- `meu irmão vai para a próxima faixa`;
- `vai para a próxima faixa da estrada`;
- `vai para a próxima reunião amanhã`.

Arquivos do candidato linguístico:
1. novo `mente_laylay/cognicao/gramatica_operacional.py`
2. `mente_laylay/autonomia/analise_comandos.py`
3. `mente_laylay/cognicao/modalidade_turno.py`
4. `mente_laylay/autonomia/detectores_playlist.py`

Não tocar para essa parte:
- `normalizacao_linguagem.py`;
- `roteador_deterministico.py`;
- helper de autoridade R1.1.

Matriz revisada:
- 10 guards;
- 5 reds.

Execução real do auditor revisado:
- preflight estrutural: 5/5 anchors exatos;
- baseline: 10/10 guards verdes;
- baseline: 5/5 reds esperados;
- candidato: 15/15 verdes;
- regressões focadas: 4/4 verdes;
- produção do auditor: intocada.

Artefatos:
- `test_candidato_m1_revisado_turno149_3_3.py`
  SHA-256:
  `4594ee7ae748af4bf17c2cd5584740db1413fd9391f290d07d5b46c482e2ec0f`
- `auditoria_candidato_m1_revisada_turno149_3_3.py`
  SHA-256:
  `89e109251f282246a8745d3c0d9f60a7444c8810275efa63bbe8586000592a17`

O commit atual `teste 3.3` (`55f10bf9...`) contém o candidato linguístico M1:
- novo `gramatica_operacional.py`;
- segmentação estreita por `vai` de mídia;
- autorização estreita da forma;
- continuação de playlist nomeada com matching contextual.

PORTANTO:
a parte linguística do M1 está incorporada no HEAD 3.3.

---

# G. M1 — DESCOBERTA NOVA NO TESTE 3.3: WIRING DO ESTADO MUSICAL

IMPORTANTE:
**M1 NÃO ESTÁ FECHADO AINDA.**

Depois de a gramática/cadeia ficar correta, a análise do fluxo integrado mostrou
uma segunda raiz de execução/contexto.

## G1. Causa raiz — PROVADA

`ContextoIntencaoRuntime.montar()` já publica a dependência tipada:

`_musica_estado_get`

A composição do runtime já injeta essa dependência no contexto de intenção.

Porém:

`CicloComandosRuntime._montar_contexto_resolucao()`

monta um contexto reduzido e NÃO repassa a dependência musical.

Ao mesmo tempo, o resolvedor de playlist contextual procura:

`musica_estado_get`

Resultado:
a etapa 2 pode ter gramática correta e mesmo assim perder `ultima_playlist`
quando atravessa o contexto reduzido.

Causa raiz:

> A dependência musical já possui dono e já existe no contexto tipado, mas a
> ponte `ContextoIntencaoRuntime -> contexto de resolução` esquece de repassá-la.

Não corrigir adicionando `_musica_estado_get` a
`DEPENDENCIAS_CICLO_COMANDOS`.

Isso duplicaria uma dependência que já pertence ao `ContextoIntencaoRuntime`.

## G2. Arquivo exato

Produção:
`mente_laylay/autonomia/coordenador_intencao.py`

Blob confirmado no HEAD 3.3:
`b2b1450e7b3e61152ba31af1736304c2c3229a60`

Mudança funcional mínima pretendida dentro de `_montar_contexto_resolucao()`:

```python
"musica_estado_get": contexto_execucao.get("_musica_estado_get"),
```

Nada além disso deve ser necessário na produção para essa ponte.

## G3. RED da ponte

Contrato:
se `ContextoIntencaoRuntime.montar()` devolve um callable em
`_musica_estado_get`, `_montar_contexto_resolucao()` deve expor o MESMO callable
como:

`musica_estado_get`

Baseline esperado:
RED.

Candidato:
GREEN.

Guard estrutural:
`"_musica_estado_get"` NÃO deve ser adicionado a
`DEPENDENCIAS_CICLO_COMANDOS`.

---

# H. PATCHER M1 WIRING — ENTREGUE, AINDA AGUARDANDO EXECUÇÃO REAL

Arquivo entregue:

`patch_m1_turno149_wiring_playlist_contexto_teste3_3.py`

SHA-256 final:

`47c39325c9753a647f75a71a8629d7ec0c737122ba81b749a85f6159ff670e23`

Locks:
- HEAD:
  `55f10bf9b0fe58dbe52c0412d694a3611af2ccf9`
- coordenador:
  `b2b1450e7b3e61152ba31af1736304c2c3229a60`

O patcher:
1. trava HEAD/blob/anchor;
2. recusa coordenador sujo;
3. cria baseline e candidate via `git archive HEAD`;
4. confirma que a regressão linguística M1 atual já está verde;
5. escreve RED temporário somente no espelho baseline;
6. exige que o RED falhe por AssertionError causal;
7. aplica somente a ponte no espelho candidato;
8. adiciona regressão permanente;
9. roda RED green;
10. roda regressão permanente;
11. roda regressões focadas:
    - M1 cadeia/mídia/playlist;
    - P0 autorização/modalidade;
    - R1.1;
    - Patch20 R1/R2;
    - consciência/capacidades;
12. audita que `DEPENDENCIAS_CICLO_COMANDOS` não mudou;
13. revalida working tree antes de escrever;
14. aplica localmente somente se tudo anterior ficar verde;
15. repete regressões na produção local;
16. gera diff + manifest + log fora do repo;
17. faz rollback byte a byte se falhar depois da escrita;
18. preserva CRLF/autocrlf;
19. não executa add/commit/push/reset/checkout/restore/clean.

Comando entregue ao usuário:

```powershell
& C:\Python314\python.exe ".\patch_m1_turno149_wiring_playlist_contexto_teste3_3.py" --repo .
```

Observação:
o patcher procura um Python COM pytest para os testes internos; ele não depende
de `C:\Python314` possuir pytest.

## H1. Próximo passo obrigatório para M1

Se o usuário retornar com a saída do patcher:

1. NÃO gerar outro patch imediatamente;
2. analisar a saída completa;
3. exigir/auditar:
   - `m1_turno149_wiring_playlist_contexto.diff`
   - `manifest_m1_turno149_wiring_playlist_contexto.json`
   - log se necessário;
4. confirmar que o diff tem somente:
   - uma linha funcional em `coordenador_intencao.py`;
   - um arquivo novo de regressão;
5. confirmar:
   - HEAD correto;
   - blob correto;
   - RED baseline causal;
   - candidato espelho green;
   - produção green;
   - dependências do ciclo intocadas;
   - sem auto commit/push;
6. só depois considerar o patch local tecnicamente aprovado;
7. ainda rodar caos/regressão real relevante antes de marcar o TURNO 149 fechado.

NÃO avançar para C1 antes dessa auditoria, salvo se o usuário explicitamente
repriorizar.

---

# I. C1 — TURNO 159 — PRÓXIMA RAIZ APÓS M1

Não misturar C1 com M1.

Sequência real:

154. `Abre o Opera.`
155. `maximiza`
156. `esquerda`
157. `agora a calculadora`
158. `direita`
159. `fecha ela`

Comportamento antigo:
- t154 `APP_OPEN opera`;
- `executou=True`;
- `confirmado=True`;
- Opera promovia referência;
- t159 conseguia resolver o referente.

Comportamento mais novo:
- t154 encontra Opera já em foco;
- `APP_OPEN`;
- `executou=False`;
- `confirmado=True`;
- status `ja_aberto_focado`;
- o bridge de referência curta exige `executou=True AND confirmado=True`;
- assim o no-op confirmado não promove referente forte;
- t159 cai no LLM;
- plano publica `intent='fechar_janela' alvo='calculadora'`;
- executor canônico espera `CLOSE_APP`;
- a ação falha.

Princípio arquitetural:

> Para promoção de referência, confirmação/evidência de estado pode importar
> independentemente de mutação.

`executou=False, confirmado=True, status=ja_aberto_focado`

não é equivalente a falha.

Direção de C1:
- permitir promoção SOMENTE para estados/no-ops tipados que confirmam que o
  estado desejado já é verdadeiro;
- exemplo: `ja_aberto_focado`;
- não promover:
  - `executou=False, confirmado=False`;
  - falha;
  - no-op arbitrário;
  - domínio errado.

Reds futuros recomendados:
1. `APP_OPEN executou=True confirmado=True` continua promovendo;
2. `APP_OPEN executou=False confirmado=True status=ja_aberto_focado`
   deve promover;
3. `executou=False confirmado=False` continua bloqueado;
4. no-op confirmado de domínio incorreto não sequestra referência.

C1 ainda NÃO tem patch de produção aprovado neste handoff.

---

# J. OUTRAS FALHAS CONHECIDAS — CONTINUAM SEPARADAS

Não misturar com M1/C1 sem repriorização explícita.

Arquivos:
- t68 leitura nominal;
- t69 append elíptico;
- t70 `Leia de novo`;
- t79 leitura nominal;
- Fase C caixa de entrada × filesystem (`troca ideia.txt`, etc.).

Apps/continuidade:
- t155 `maximiza` curto;
- sequência 154–159 deve ser estudada como C1/continuidade.

Música:
- t171 `continua`;
- t174 `essa também`.

Outros:
- confirmação causal de `CLOSE_APP`;
- consulta read-only de app/janela em foco;
- condicionais;
- conversação genérica.

Fase C filesystem:
evidência filesystem explícita deve fazer a caixa de entrada ceder sem quebrar
casos conversacionais reais como:
`Apaga essa nota.`

---

# K. INVARIANTES QUE NÃO PODEM SER SACRIFICADAS

Pipeline conceitual:

`ENTRADA → ATO DE FALA → ESTRUTURA → AÇÃO CANDIDATA → AUTORIZAÇÃO → ALVO → PRÉ-ESTADO → EXECUTOR → PÓS-ESTADO → RESULTADO CAUSAL`

Revisão intra-turno:

`FALA ORIGINAL → REVISÃO → TEXTO OPERACIONAL EFETIVO → AUTORIZAÇÃO → RETRATO → ESPECIALISTAS → PLANO → ROTEAMENTO → EXECUÇÃO`

Separar:

TEXTO ORIGINAL:
- identidade;
- histórico;
- memória;
- auditoria;
- runner correlation.

TEXTO OPERACIONAL EFETIVO:
- cognição;
- classificação;
- autorização;
- detectores;
- roteamento;
- execução.

Autoridade:
- contexto nunca aumenta autoridade;
- detector nunca aumenta autoridade;
- cadeia nunca aumenta autoridade acima do pai;
- read-only pode ter corredor próprio;
- efeito exige autoridade congelada do turno.

M1:
- não adicionar `vai` global;
- não adicionar `adiciona` global só para fazer a cadeia passar;
- não mover semântica operacional para `normalizacao_linguagem.py`;
- não enfraquecer `_candidato_prioritario_autorizado`;
- não adicionar `_musica_estado_get` como nova dependência global do ciclo.

Segurança:
- nunca fechar programas sem comando explícito do usuário;
- não inferir alvo de efeito por conversa vaga;
- confirmação de estado não significa autorização para uma nova ação.

Git:
- sem auto commit/push;
- não usar `git add .`;
- selecionar produção/testes intencionalmente;
- evitar versionar patchers, `.laylay_patch_artifacts`, backups e reds
  temporários sem decisão explícita.

---

# L. CHECKLIST PARA O PRÓXIMO CHAT

Ao abrir um chat novo:

1. ler ESTA seção de 17/08 antes das seções antigas;
2. consultar o GitHub atual — não assumir que HEAD continua `55f10bf9...`;
3. consultar working tree/status se houver acesso/artefato do usuário;
4. se o usuário enviar saída do patcher M1 wiring:
   - analisar primeiro;
   - auditar diff + manifest;
   - não gerar patch novo por reflexo;
5. se M1 já estiver validado localmente:
   - rodar/avaliar caos real do turno 149;
   - só então marcar M1 fechado;
6. somente depois iniciar C1 turno 159;
7. não misturar files/caixa de entrada/música curta/CLOSE_APP causal com M1/C1;
8. se um teste falhar:
   - verificar se é teste/harness/runner antes de culpar produção;
9. se patcher fizer rollback:
   - confirmar status/HEAD antes de assumir repo restaurado;
10. manter patches pequenos, rastreáveis e causais.

Frase-guia atual:

**“Estudar primeiro, provar o vermelho, corrigir a causa raiz, reanalisar o patch pronto, só então entregar.”**

---

# HISTÓRICO HERDADO DO HANDOFF DE 16/08

O conteúdo abaixo é preservado integralmente para auditoria e contexto histórico.
Quando houver conflito de estado/próximo passo, prevalece a seção de 17/08 acima.

# HANDOFF INTERNO — PROJETO LAYLAY
Data: 2026-08-16
Atualizado em: 2026-08-16 23:02 (America/Sao_Paulo)
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

Trilha pós-caos 3.0 / 3.1 — ESTADO MAIS NOVO:
- Fase A — capability truth read-only × barreira P0: FECHADA no `teste 3.1`.
- Fase B foi aprofundada e o desenho antigo “B1 = regex/gramática simples” foi SUPERADO.
- As raízes arquiteturais atuais são:
  - R1 — quebra da autoridade do turno na fase prioritária;
  - R2 — consumo de contexto de arquivo stale fora do accessor canônico.
- Fotografia V2 R1/R2: FECHADA e auditada.
- Patch 2.0 R1/R2: APLICADO no working tree, ainda SEM commit.
- Patch 2.0 passou 112 testes focados após correção do runner pytest.
- Auditoria pós-patch encontrou uma borda nova em `FILE_OPEN_RESULT`: narrativa com ordinal podia ganhar autoridade por prefixo artificial `abre`.
- Red específico dessa borda: confirmado exatamente em `3 failed, 2 passed`.
- Microfix 2.0.1 ordinal narrativo: APLICADO COM SUCESSO conforme relato do usuário; auditoria documental do manifest/microdiff ainda é a próxima checagem antes de considerar pronto para commit.
- V2.1 continua PENDENTE e NÃO foi misturada no Patch 2.0:
  - aliases `ultimo_caminho_arquivo` / `ultima_pasta` sem proveniência temporal própria;
  - continuidade arquivo+pasta simultânea;
  - timestamp futuro aceito pelo accessor/retrato como dívida separada.
- Ergonomia B posterior continua separada: escrita elíptica, leitura nominal, existência contextual e repetição segura de `FILE_READ`.
- Fase C — arbitragem caixa de entrada × filesystem continua SEPARADA; não misturar.

IMPORTANTE SOBRE O ESTADO DO GIT:
- `HEAD` continua `a619a71...` porque Patch 2.0 + microfix ainda não foram commitados.
- Portanto `HEAD == teste 3.1` NÃO significa que o working tree esteja na produção antiga.
- O working tree atual contém mudanças de produção do Patch 2.0 + microfix 2.0.1.
- Antes de qualquer novo patch, consultar `git status --short` e o diff atual; não reaplicar Patch 2.0 sobre ele.

Teste de caos 3.1 que originou a investigação:
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

Conclusão operacional imediata ATUAL:
- NÃO reaplicar a fotografia V2 nem o Patch 2.0.
- Primeiro auditar os artefatos reais do microfix 2.0.1 bem-sucedido (saída, `manifest.json`, `microfix_candidate.diff`).
- Depois confirmar `git status --short`, diff final e conjunto de testes realmente verdes.
- Só então decidir commit/caos.
- R1/R2 ainda não devem ser marcados como encerrados por completo antes da auditoria final + regressão/caos real.
- Depois dessa fundação, seguir para V2.1 pequena do sibling temporal; não misturar ergonomia B ou Fase C nela.

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

# 19. PRÓXIMA AÇÃO RECOMENDADA — ATUALIZADA 23:02

1. NÃO reaplicar Patch 2.0: ele já está no working tree.
2. NÃO executar teste pytest com `C:\Python314\python.exe` diretamente; o Python global não possui pytest.
3. Usar `.venv314\Scripts\python.exe -m pytest` para testes manuais, ou deixar o patcher resolver o runner.
4. Microfix 2.0.1 foi reportado como aplicado com sucesso pelo usuário.
5. Próxima prova documental:
   - saída completa do microfix;
   - `manifest.json` da execução;
   - `microfix_candidate.diff`;
   - se útil, `patch20_after_microfix.diff` e log pytest.
6. Auditar:
   - HEAD esperado;
   - estado exato do Patch 2.0 antes do microfix;
   - mudança somente em `comandos_imediatos.py` + regressão oficial;
   - ordinal legítimo continua permitido;
   - narrativas com ordinal continuam bloqueadas;
   - fotografia V2 continua verde;
   - guards P0/capability/contexto continuam verdes;
   - sem commit/push automático.
7. Antes de commit:
   - `git status --short`;
   - selecionar somente produção + testes oficiais;
   - NÃO incluir patchers, artefatos `.laylay_patch_artifacts`, reds temporários ou backups sem decisão explícita.
8. Depois da auditoria documental, rodar regressão/caos relevante antes de fechar R1/R2.
9. Em seguida, materializar V2.1 pequena para o sibling temporal (`ultimo_caminho_arquivo` / `ultima_pasta` + continuidade arquivo/pasta).
10. Ergonomia de arquivo (elipse, leitura por nome, existência, repetição) e Fase C continuam separadas.

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

---

# ATUALIZAÇÃO FINAL — 2026-08-16 23:02 — V2 FECHADA, PATCH 2.0 APLICADO, MICROFIX 2.0.1

Esta seção SUPERA qualquer “próximo passo” anterior deste handoff quando houver conflito.
As seções antigas continuam preservadas como histórico de investigação.

## 20.1 Baseline e estado real do working tree

HEAD/base remota estudada:
`a619a71ff5d1976fb8a25561ab2512ec291e31e8`

Mensagem:
`teste 3.1`

IMPORTANTE:
- nenhum commit/push automático foi feito;
- por isso o HEAD continua `a619a71...`;
- o working tree atual NÃO é mais a baseline pura;
- nele estão aplicados Patch 2.0 R1/R2 + microfix 2.0.1 ordinal narrativo, conforme execução do usuário.

Antes de qualquer patch futuro:
1. `git status --short`;
2. verificar diff atual;
3. não reaplicar Patch 2.0;
4. não assumir produção antiga apenas olhando HEAD.

## 20.2 Fotografia V2 R1/R2 — FECHADA E AUDITADA

Teste oficial:
`tests/test_red_r1_r2_autoridade_frescor_v2_3_1.py`

SHA-256:
`d89971098276dba74179bfe003332f38eaad85a1524a05269873b0b147fac099`

Patcher V2:
`patch_fotografia_vermelha_r1_r2_v2_3_1.py`

SHA-256:
`173f658cf06144af37c0ea5644f66aec4168a722c51e6d311b16b5da581a5f7e`

Execução real confirmada:
- 10 guards verdes;
- 13 reds;
- cada red executado individualmente;
- cada red falhou por AssertionError no ponto previsto;
- produção não modificada;
- teste ficou untracked;
- sem commit/push.

A auditoria posterior confirmou:
- manifest correto da V2;
- diff reconstruía exatamente o payload esperado;
- SHA do teste idêntico;
- baseline/blobs exatos;
- nenhum red morreu por erro de import/setup/sintaxe.

Reds V2 cobrem:
- efeito descoberto pós-P0 sem autoridade;
- append não autorizado;
- restore não autorizado;
- `FILE_OPEN_RESULT` injetado;
- cadeia elevando autoridade;
- arquivo stale;
- timestamp ausente;
- pesquisa semântica stale;
- retrato stale;
- rejuvenescimento 899 s -> 901 s;
- cache derivado sobrevivendo sem fonte válida;
- combinação R1 × R2 chegando a mutação.

## 20.3 Desenho final do Patch 2.0

Princípios aprovados:
1. Descobrir uma intent NÃO concede autoridade.
2. `FILE_SEARCH` / `FILE_READ` permanecem read-only pelo catálogo canônico.
3. Efeito prioritário exige autoridade congelada do turno, salvo prova contextual estreita e verificável.
4. Cadeia nunca pode elevar `autoriza_execucao` acima do pai.
5. Router/retrato devem consumir `estrutura_arquivo_recente()` em vez de estado cru.
6. Entidade derivada conserva o timestamp da fonte; não recebe `agora`.
7. Cache com `origem=estrutura_arquivo_confirmada` morre se a fonte canônica não for mais válida.
8. Não colocar gate global no executor.
9. Não afrouxar árbitro.
10. Aliases `ultimo_caminho_arquivo` / `ultima_pasta` ficam para V2.1.

## 20.4 Patch 2.0 — primeira tentativa e falso rollback

Patcher inicial:
`patch_producao_r1_r2_v2_0_3_1.py`

Primeira execução terminou em rollback com `pytest focado falhou`.
Causa REAL pelo manifest/log:
`C:\Python314\python.exe: No module named pytest`

Nenhum teste de comportamento havia rodado.
O ImportError visto depois no teste pós-fix era consequência do rollback: a função nova já havia sido removida porque a produção foi restaurada.

Conclusão:
- não era falha da candidata de produção;
- era falha do harness ao usar `sys.executable` sem validar pytest;
- rollback funcionou corretamente.

Regra nova:
VALIDAR O LABORATÓRIO ANTES DO EXPERIMENTO.

## 20.5 Patch 2.0 runnerfix — SUCESSO REAL

Patcher corrigido:
`patch_producao_r1_r2_v2_0_3_1_runnerfix.py`

SHA-256:
`e2368dd97ace4aede5b4daa73968536844699d4fedfe2b9a86c2b48817b6956f`

Runner encontrado:
`.venv314\Scripts\python.exe -m pytest`

Manifest reportou:
- `status = ok`;
- HEAD esperado = observado = `a619a71...`;
- blobs esperados = observados;
- pytest probe: `pytest 9.1.1`;
- pytest focado: `112 passed in 0.98s`;
- stderr vazio;
- commit/push automático: false.

Produção alterada:
- `mente_laylay/autonomia/comandos_imediatos.py`;
- `mente_laylay/autonomia/coordenador_intencao.py`;
- `mente_laylay/arquivos/roteador_arquivos.py`;
- `mente_laylay/cognicao/retrato_turno.py`;
- `mente_laylay/cognicao/modalidade_turno.py`.

Teste legado migrado:
- `tests/test_contexto_execucao_arquivos.py`;
- 10 fixtures ganharam timestamp coerente;
- asserts não foram removidos/afrouxados.

Teste pós-fix criado:
`tests/test_regressao_patch20_r1_r2.py`

SHA antes do microfix:
`a23fc6a2c53557b7b46543d87da69f081b1efd2753f6b8bdcf17df8b0e3ba84d`

## 20.6 Reanálise pós-Patch 2.0 — pontos aprovados

Router:
- leituras principais de estrutura passaram para `estrutura_arquivo_recente()`.

Cadeia:
- `autoriza_execucao=True` fabricado foi substituído por autoridade do pai.
- invariante: `autoridade_filho <= autoridade_pai`.

Restore/modalidade:
- formas de restaurar/recuperar foram alinhadas nas famílias relevantes do classificador/P0.
- direto autoriza; negativo/instrucional/capacidade não autorizam.

Retrato:
- usa fonte fresca;
- cache derivado depende da fonte;
- preserva `ultima_estrutura_arquivo_ts`;
- caso 899 s -> 901 s morre corretamente.

## 20.7 Auditoria “não satisfeita” encontrou borda ordinal nova

Mesmo com 112 verdes, o patch não foi aceito imediatamente.
A exceção de `FILE_OPEN_RESULT` fazia fallback com `f"abre {texto}"` quando o parser ordinal retornava `None`.

Isso permitia que narrativa ganhasse evidência artificial de seleção.
Exemplos:
- `foi meu primeiro jogo`;
- `não foi o primeiro`;
- `eu fiquei em 1 lugar`.

O parser central sozinho rejeita essas narrativas.
A barreira de autoridade não pode depender da suposição de que o detector nunca produzirá candidato errado.

## 20.8 Red ordinal narrativo — CONFIRMADO

Teste temporário:
`test_red_patch20_ordinal_narrativo_auditoria.py`

SHA-256:
`cf1eade28ec0134b2bac148e9f4075a456b839475ca6a27bf74a0720f6efd2a2`

Execução correta com `.venv314`:
`3 failed, 2 passed in 0.14s`

Guards verdes:
- parser central rejeita narrativa ordinal;
- ordinal contextual legítimo continua autorizável.

Reds exatos:
- `foi meu primeiro jogo`;
- `não foi o primeiro`;
- `eu fiquei em 1 lugar`.

Todos falharam no assert previsto porque `_candidato_arquivo_prioritario_autorizado(...)` retornava True.

## 20.9 Microfix 2.0.1 — desenho

Não criar regex paralela.
Reutilizar `valor_e_referencia_contextual(texto)`.

Regra:
- tentar parser ordinal normalmente;
- só se retornar `None` E o texto inteiro já for referência contextual válida, usar fallback `abre <texto>`;
- narrativa longa não recebe prefixo artificial.

Preservar:
- `o primeiro`;
- `abre o primeiro resultado`;
- ordinal contextual curto.

Bloquear:
- as três narrativas acima.

## 20.10 Primeiro microfix recusado por lock incorreto

Primeiro patcher:
`patch_microfix_2_0_1_ordinal_narrativo.py`

Recusou `tests/test_contexto_execucao_arquivos.py` por SHA de diff divergente.

Esperado errado:
`d67d66d33d9bb8b91ec26b40731c3b81c051e7684d87e891c386a520ffacab9d`

Observado real:
`81d1a9d507ae4aa6d21eac885bb6d63bfa874ab802baaf80749a1169719c5362`

Causa provada:
- SHA esperado veio de recorte do diff combinado com uma newline separadora extra;
- remover somente essa newline produz exatamente o SHA observado;
- repo não tinha mudado;
- microfix não tocou produção nessa tentativa.

## 20.11 Microfix 2.0.1 lockfix — SUCESSO REPORTADO PELO USUÁRIO

Patcher final:
`patch_microfix_2_0_1_ordinal_narrativo_lockfix.py`

SHA-256:
`ed3eb52ad30fb930d7ed408b4a72e918e29a5532183447f168c19973d18c0de2`

Produção pretendida:
SOMENTE `mente_laylay/autonomia/comandos_imediatos.py`.

Teste oficial atualizado:
`tests/test_regressao_patch20_r1_r2.py`

Payload atualizado SHA:
`c144255e724094278ac149f9515b7883160e6081adda833bc0fd9b2edece17ed`

O patcher final:
- trava HEAD `a619a71...`;
- trava estado exato dos diffs já aplicados do Patch 2.0;
- trava V2 pelo SHA `d899...`;
- resolve pytest antes de tocar produção;
- inclui o red ordinal temporário se existir com SHA exato;
- roda V2 + pós-fix + P0 + capability + contexto de arquivos + red ordinal;
- rollback volta para “Patch 2.0 aplicado, sem microfix”;
- não faz commit/push.

STATUS:
- usuário informou: `deu certo`;
- microfix deve ser tratado como aplicado no working tree;
- manifest/microdiff da execução final ainda NÃO foram auditados nesta conversa;
- portanto não marcar auditoria documental final como concluída ainda.

## 20.12 Próxima ação antes de commit/fechamento

1. Receber/auditar artefatos finais do microfix:
   - `manifest.json`;
   - `microfix_candidate.diff`;
   - se útil `patch20_after_microfix.diff`;
   - log pytest.
2. Confirmar:
   - `status=ok`;
   - HEAD correto;
   - runner pytest válido;
   - mudança somente no helper ordinal + teste oficial;
   - V2 continua green;
   - narrativas agora bloqueadas;
   - ordinal legítimo preservado;
   - guards P0/capability/contexto verdes;
   - sem commit/push automático.
3. Rodar `git status --short`.
4. Não versionar sem intenção patchers, artefatos, backups, reds temporários e handoffs duplicados.
5. Antes de fechar R1/R2, fazer regressão/caos relevante no runtime real.

## 20.13 V2.1 — sibling conhecido e ainda não patchado

Não colocar retroativamente no Patch 2.0.

Sibling:
- `registrar_mente_curta()` publica `ultimo_caminho_arquivo` e `ultima_pasta` sem timestamp próprio;
- movimentação contextual consulta aliases;
- os aliases também sustentam utilidade real de lembrar arquivo + pasta simultaneamente (`move ele para ela`);
- apagar aliases pode quebrar continuidade válida.

Direção preferida:
- manter fonte operacional temporal canônica;
- preservar referência tipada de arquivo E pasta simultaneamente com TTL/proveniência;
- aliases conversacionais não devem ser prova operacional imortal;
- V2.1 test-only primeiro, com guards de movimento fresco e reds de movimento stale;
- timestamp futuro fica como hardening separado/irmão.

## 20.14 Ergonomia de arquivos permanece depois da fundação

Patch 2.0 não resolve sozinho todos os turnos 67–75.
Ainda faltam separadamente:
- escrita/append elíptico com arquivo fresco tipado;
- leitura por nome equivalente;
- existência contextual;
- repetição segura/qualificada de `FILE_READ` (`Leia de novo`).

Princípio:
primeiro autoridade + frescor confiáveis; depois ergonomia.

## 20.15 Fase C continua separada

Caixa de entrada × filesystem é outra raiz.
Não misturar com V2.1 nem ergonomia de arquivo.

## 20.16 Regras metodológicas novas consolidadas

RUNNER É PARTE DA PROVA:
- provar pytest antes de alterar produção;
- não usar `sys.executable` cegamente;
- falha do laboratório não é falha da candidata.

LOCK TAMBÉM PRECISA SER AUDITÁVEL:
- diff combinado pode conter separadores extras;
- se o lock é de diff isolado, preferir SHA da saída exata de `git diff -- <arquivo>`;
- estudar recusa por lock antes de assumir que o usuário mudou o repo.

Frase-guia:
“Estudar primeiro, provar a causa raiz, materializar o vermelho, corrigir o mínimo, reanalisar o patch pronto, só então entregar.”


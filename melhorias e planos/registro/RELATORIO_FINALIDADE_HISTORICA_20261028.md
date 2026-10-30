# Contexto disponível não cria obrigação histórica — 28/10/2026

Correção aplicada e validada no recorte da **admissão histórica**. A qualidade
integral da conversa permanece aberta: a coleta também encontrou problemas em
autoria, repetição e revisão didática, descritos abaixo e não corrigidos aqui.

Continuação posterior da fronteira didática: ver
`RELATORIO_FINALIDADE_FICCIONAL_20261028.md`. Este relatório conserva o estado
e os limites observados na investigação histórica, sem reclassificar sua coleta.

## Base e cadeia causal

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. Estado Git e hashes de 531 fontes estão em
`resultados_testes/ficcao_historico_20261028/baseline.json`. Não se assume que
esse HEAD isolado representa o código que produziu a ponte histórica.

Os três textos originais da ponte — carta imaginada, mascote fictício e nome
numa aventura — foram reproduzidos com a composição instalada e Qwen real.
Na base, os seis turnos tiveram HTTP 200. O Qwen chegou a escrever conteúdo
imaginativo; o host o substituiu por limite histórico. Não era necessário
atribuir esse sintoma a falha de transporte ou incapacidade de criar histórias.

```text
fala narrativa observada no registro canônico
→ disponibilidade da fonte admite tentativa de vínculo histórico
→ composto com reação/conversa/pergunta não satisfaz o vínculo por ato
→ vínculo retorna None
→ contrato interpreta qualquer None como obrigação histórica inválida
→ revisão histórica publica aviso de evidência
```

A primeira transição incorreta é **tentativa de vínculo → obrigação** em
`contrato_fala.py`. Na rota atômica, uma evidência ou citação também podia
escolher o passado sem que a consulta atual pedisse explicação histórica.
É continuação da distinção compartilhada entre referente e finalidade, não
um mecanismo especial para histórias, nomes, música ou determinada frase.

Falsificações e controles:

- A fala anterior existe e é observada pelo registro real; não é mera falta
  de contexto nem memória fabricada pela fixture.
- O defeito aparece com e sem receipt anterior confirmado. Ausência de
  execução não explica por que uma criação fictícia exige prova histórica.
- Prosa imaginativa já estava na resposta bruta HTTP da base. O primeiro
  bloqueio demonstrado é do contrato, não do transporte/modelo.
- Consultas a ações reais, inclusive em composto com criação fictícia,
  continuam exigindo fonte; causa proposta pela IA não se torna prova.

## Contrato e responsáveis

| Responsabilidade | Owner | Regra |
| --- | --- | --- |
| Admitir obrigação histórica | `cognicao/contrato_fala.py` | Fonte disponível permite lookup; não impõe finalidade. Vínculo inválido conserva o limite quando há consulta histórica ou ocorrência fornecida. |
| Ler a finalidade atual | `cognicao/referencias_linguagem.py` | Construção causal/atribuição qualifica consulta; texto citado sozinho não. Preserva as formas elípticas e de motivo da própria fala antes admitidas pela presença de citação. |
| Conferir fontes e realizar limites | `cognicao/explicacao_fala_historica.py` e revisão existente | Identidade, fonte por ato, receipts, autoridade e cobertura continuam obrigatórios. Sem alteração nesta correção. |
| Produzir efeito e confirmar resultado | Executors existentes | Nenhum efeito ou autoridade é concedido pela nova leitura. Sem alteração. |

Produção alterada nesta etapa: somente `contrato_fala.py` e
`referencias_linguagem.py`. Os diffs exclusivos contra as cópias congeladas
ficam junto da auditoria; o diff contra HEAD contém trabalho anterior e não
representa o escopo exclusivo desta etapa. Nenhum commit criado.

## Validação e limites

O diagnóstico original preserva três REDs/um controle. O RED ampliado tem
16 falhas desta raiz, oito controles aprovados e uma falha vizinha anterior
ao candidato. Essa última não foi contada como a mesma causa.

Novo módulo `scripts/tests/test_finalidade_contexto_historico.py`: **34
aprovados e um xfail estrito**. Inclui os textos originais, variantes atômicas,
conteúdo citado, conversa comum, receipt anterior presente/ausente, duas ações
em domínios distintos, fonte estrangeira e segmentação adulterada.
O primeiro teste adulterava só o texto de apresentação e não invalidava a
fonte canônica; esse preflight foi preservado e a mutação corrigida antes do
patch. Não é RED do contrato de fonte.

Foco com explicações por ato, própria fala, esclarecimento e finalidade:
182 aprovados, um ignorado e um xfail; os dez controles adicionais do leitor
foram executados depois no módulo novo e na regressão ampla.

Regressão relevante em **129 módulos**: 3.324 aprovados, nove falhas e 44 erros
com os mesmos IDs da base anterior; 14 ignorados, um desmarcado, um xfail e
30 subtestes aprovados. As nove falhas anteriores pertencem ao intent da
Calculadora e expectativas de esquema/orçamento; os 44 erros são da fixture
de composição que serializa `PerspectivaEnunciador`. Não foram corrigidos nem
reclassificados nesta raiz. A suíte ampla não é inteiramente verde.

Composição instalada em perfil isolado, composição raiz carregada, Qwen
`qwen3:4b-instruct` real, persistência isolada, sem voz, executores simulados:

- `baseline_dialogo`: seis entradas/publicações/HTTP 200; os três originais
  recebiam `explicacoes_historicas_por_ato=None` e limite histórico.
- `candidato_dialogo`: oito entradas/publicações/HTTP 200. Os três originais
  e os controles criativos não recebem contrato histórico; a pergunta sobre
  abertura do navegador conserva exatamente o limite verificável anterior.
- `seguranca_final`: três publicações, uma execução simulada, receipt negativo
  com `executou=False`, `confirmado=False`, `ok=False`; nenhuma falsa abertura.
- `receipt_historico`: três publicações. Depois da recusa simulada, perguntar
  por que abriu a Calculadora mantém o limite histórico; imaginar um personagem
  volta à conversa criativa sem converter o receipt em obrigação histórica.

**Não são GREEN de qualidade integral:**

- No primeiro turno da coleta candidata, um resumo atribuído do pedido foi
  publicado em vez da história solicitada.
- A pergunta pelo nome da autora na aventura recebeu repetição da escolha
  anterior para o mascote. A ausência de captura histórica não prova pertinência.
- “Gostei da ideia. Vamos pensar em outra. Como isso funcionaria?” não recebeu
  contrato histórico, mas a revisão de `explicacao_didatica` exigiu suporte e
  publicou aviso. É outra fronteira comprovadamente distinta, não falha do
  vínculo histórico ainda ativo.
- Na retomada vaga do receipt, o reparo foi rejeitado e terminou no limite
  técnico de tentativas. Não houve confirmação falsa, mas a resposta não foi útil.
- `Quando disse "Registrei o resultado do pedido.", por que aconteceu?` é
  dividido em atribuição e pergunta; a composição não conserva a relação causal
  entre os segmentos. O RED já existia na base, está preservado como xfail
  estrito e requer investigação própria. Os controles históricos existentes
  com fonte e consulta vinculadas continuam protegidos.

Esses resultados não demonstram compreensão universal de ficção nem resolução
de F1/C5/C7/AUT. Orçamento e saída estruturada inválida da ponte continuam
separados. Próxima fronteira sugerida: finalidade imaginativa na autoria/revisão
didática, antes de dispensar fontes ou esconder avisos por substituição textual.

Artefatos e auditoria reproduzível:
`resultados_testes/ficcao_historico_20261028/auditar.py` e `auditoria.json`.
A auditoria passou: 531 fontes conferidas, só os dois owners declarados
alterados, snapshots das coletas estáveis, mesmas falhas/erros por ID e HEAD
preservado. O primeiro preflight de auditoria comparava caminhos Windows com
separadores diferentes; foi preservado e corrigido por normalização de caminho,
sem dispensar comparação de identidade ou hash. `git diff --check` passou nos
owners modificados. Os arquivos originais da ponte não foram alterados.

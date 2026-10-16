# Compreensão da própria fala e das ações — plano integrado da Laylay

15/10/2026. Plano aprovado conceitualmente por Pedro e registrado a seu pedido.

## 1. Objetivo, autorização e limites

Fazer a Laylay acompanhar o significado daquilo que comunica e das ações que
realiza: identificar referentes, distinguir afirmação de hipótese, recuperar a
evidência, confrontar expectativa e resultado, reconhecer contradições e fazer
correções repercutirem na continuidade e no aprendizado compartilhados.

Pedro autorizou estudo adicional e implementação quando a investigação oferecer
base suficiente. A regra é estudar primeiro sempre que necessário, localizar a
primeira fronteira incorreta, reproduzir um RED válido e só então aplicar um
candidato mínimo. Esta autorização não determina implementar tudo de uma vez.

Não ampliar concessões de autonomia, ativar motores, criar uma nova iniciativa,
retomar objetivos após reinício, mudar modelo/voz, treinar rede ou substituir
os owners existentes como consequência deste plano. Testes de efeitos externos
devem respeitar o escopo e as autorizações específicas do runtime.

Entendimento funcional será medido pelo comportamento. Este plano não demonstra
experiência subjetiva nem torna uma explicação da LLM prova de causa ou efeito.

## 2. Base congelada e nível de evidência

- Branch consultada: `main`.
- HEAD consultado: `d850b8c90cc5ce40bd4832e759ed991ba88cd5cc`.
- Worktree: amplamente modificada antes deste trabalho, incluindo produção,
  firmware, testes, mapa causal, registro central e arquivos não rastreados.
- A base é a worktree lida, não somente o HEAD. Nenhuma alteração anterior deve
  ser atribuída a este plano ou apagada para facilitar testes.
- A inspeção demonstra componentes e algumas relações por código. Não comprova
  a disponibilidade de todos os caminhos no processo atualmente usado por Pedro.
- Nenhum resultado antigo de teste ou memória deve ser apresentado como medição
  atual. Antes de cada candidato, capturar diff, fontes e composição do recorte.

## 3. Relação com o mapa causal e os trabalhos existentes

Consultar e preservar:

- `melhorias e planos/raiz/MAPA_RAIZES_CONVERSA.md`.
- `melhorias e planos/registro/REGISTRO_PROBLEMAS_E_CORRECOES.md`.
- `melhorias e planos/planos/PLANO_LAYLAY_ASSISTENTE_AUTONOMA.md`.
- `melhorias e planos/planos/ESTUDO_E_PLANO_INTERPRETACAO_NATURAL_20261014.md`.
- `melhorias e planos/ideias/CORPO_COMO_PARTE_DA_LAYLAY.md`.

F1 reúne perdas de significado com causas locais distintas, inclusive limites
da validação de explicações livres. Não declarar uma raiz universal de
"falta de entendimento". Estrutura válida, palavras presentes e aprovação pelo
próprio modelo não provam equivalência semântica.

RPV19 e RPV20-06 já tratam confirmação de entrega, publicação textual e contexto
comunicativo. Reutilizar seus owners; não implementar outro detector de entrega.
Pedido composto já tem uma autoria sobre receipts independentes. Preservá-la.

AUT-01 e a correlação por ocorrência já possuem mecanismos na worktree atual,
incluindo captura anterior ao callback e tratamento de resultados tardios.
Reproduzir o estado atual antes de usar um RED histórico como diagnóstico.
Continuidade corporal curta não comprova retomada geral de objetivos após reinício.

Os identificadores abaixo são contratos deste plano, não novos IDs de raízes.
Só vincular uma evidência a uma raiz após demonstrar o mecanismo responsável.

## 4. Responsáveis canônicos e pontos de integração

| Fronteira | Responsável existente | Responsabilidade preservada |
| --- | --- | --- |
| Ato, referente e limite do turno | `cognicao/contratos_turno.py`, `orquestrador_turno_runtime.py`, interpretadores canônicos | Interpretar e manter fonte/ocorrência; proposta não concede autoridade. |
| Sentido pretendido da fala | `cognicao/contrato_fala.py` | Atos, referente, conteúdo obrigatório, inferências proibidas e roteiro. |
| Aderência da redação | `cognicao/validacao_contrato_fala.py`, qualidade comunicativa e `guardiao_alegacoes.py` | Conferir conteúdo e sustentação no limite coberto; cobertura desconhecida não é aprovação. |
| Identidade, escopo e admissão | `cognicao/escopo_autorizacao.py`, `composicao_turno.py`, `autonomia/resposta_ia_runtime.py` | Autoridade e vigência antes das etapas; nenhuma autoridade derivada da fala da própria Laylay. |
| Efeito e resultado | Executores de domínio, `memoria_mental/resultado_acao.py`, `integracao/adaptadores_aplicacao_runtime.py` | Produzir efeito, normalizar e publicar receipt da ocorrência correta. |
| Observação de invocação | `autonomia/composicao_ciclo_comandos.py`, `memoria_mental/observacao_execucao.py` | Preservar pedido e publicações; observação/identidade não comprovam sucesso por si. |
| Autoria final e apresentação | `personalidade/orquestrador_fala_runtime.py` | Fala final, composição por pedido, publicação textual e vínculos de entrega. |
| Reprodução de áudio | `personalidade/voz_runtime.py` | Confirmar reprodução por software; fila aceita não é áudio concluído. |
| Alegações, referentes e revisões | `memoria_mental/registro_semantico.py`, `contexto_compartilhado.py` | Registro semântico curto, fontes, contestação e correção. Estender sem criar cópia da verdade operacional. |
| Continuidade e seleção de evidências | `memoria_mental/continuidade_geral.py`, `contexto_integrado.py`, `cognicao/seletor_contexto.py` | Recuperação relevante e pendências com ciclo de vida; não reexecutar por lembrar. |
| Isolamento e persistência de conversa | `memoria_mental/conversas_runtime.py`, `sessao_conversa.py`, serviços de memória existentes | Separar chat, sessão, histórico e memória durável; reinício não restaura autoridade. |
| Decisão corporal | `cognicao/decisao_corporal.py`, `autonomia/companhia_corporal.py` | Escolher inclusive repouso, preservar decisão e concessão, revalidar antes de efeito. |
| Experiência corporal | `memoria_mental/experiencia_corporal_runtime.py`, executor corporal e sensores | Ocorrência, resultado e feedback com limite físico explícito; PWM não é deslocamento. |
| Cooperação | `autonomia/quadro_cooperacao.py`, `governanca_cooperacao.py`, `executor_cooperacao.py` | Etapas/dependências, autorização por capacidade e falha parcial. |
| Aprendizado | `memoria_mental/motor_aprendizado.py`, `maturidade_aprendizado.py` | Evidências qualificadas, revisão e suficiência; persistência precisa ser confirmada. |
| Consciência de capacidade e diagnóstico | `especialistas/capacidades.py`, `mapa_habilidades.py`, observabilidade/DEV existentes | Disponibilidade, evidência, limites e perguntas naturais; descrição não comprova habilidade instalada. |
| Composição | `laylay.py`, factories e registros em `integracao/` | Conectar responsáveis; manter comportamento de domínio fora do composition root. |

Os caminhos da tabela são relativos a `mente_laylay/`, exceto `laylay.py`.
Os arquivos são pontos a estudar, não uma lista obrigatória de arquivos a editar.

## 5. Contratos e critérios locais

### C1 — Significado explícito e fiel à fala final

Representar ato comunicativo, proposições, referente, negação, condição, tempo,
modalidade e propósito quando relevantes. Distinguir "posso", "vou", "tentei",
"confirmei" e "não sei". Vincular o sentido pretendido à redação final aceita,
incluindo mudanças por guarda, reparo, diretor ou composição.

Owner: contrato de fala e validação; persistência semântica no registro existente.

Validação: paráfrases, mudança de entidade/pessoa, negação, hipótese, citações e
frases compostas. Texto correto com promessa contraditória acrescida deve falhar
na fronteira correspondente. Ausência de cobertura deve aparecer como tal.

### C2 — Evidência por proposição, sem empréstimo de confirmação

Cada afirmação relevante aponta para sua fonte e validade. Autoria, rota, confiança
declarada pelo modelo e presença no histórico não são fontes suficientes.
Uma afirmação sobre efeito usa o receipt adequado. Outra sobre estado atual pode
exigir nova observação. Receipts de etapas diferentes continuam independentes.

Owner: responsáveis por fonte/resultado; registro semântico guarda referências.

Validação: fonte de uma frase não confirma outra sem vínculo; sucesso parcial
não vira total; receipt estrangeiro, malformado ou antigo não sustenta afirmação
atual. Sem evidência, explicitar desconhecimento sem negar capacidade disponível.

### C3 — Fala gerada, publicada e reproduzida possuem estados distintos

Vincular o conteúdo final aos eventos canônicos de entrega por canal. Registrar
tentativa sem promovê-la a comunicação entregue. Texto publicado não comprova
áudio; reprodução por software não comprova que Pedro ouviu ou compreendeu.
Sem evidência por trecho, não inventar até qual palavra um áudio foi ouvido.

Owner: orquestrador da fala e voz; consumidores semânticos observam seus registros.

Validação: texto aceito/recusado, TTS falho, cancelamento, fala substituída antes
de reprodução, callback tardio e texto entregue com áudio incompleto. Preservar
regras existentes de autoria única e deduplicação.

### C4 — Decisão e expectativa anteriores à ação

Uma ação solicitada ou autônoma pode ser ligada ao evento, objetivo, critério
observável registrado na decisão, resultado esperado e autorização aplicável.
O motivo deve ser capturado antes do efeito. Explicação posterior não pode se
apresentar como motivo histórico comprovado se esse registro não existe.

Owner: responsável real pela decisão; executor continua responsável pelo efeito.

Validação: comparar decisão registrada, resultado e explicação posterior; mudar
o estado após a execução não deve reescrever o motivo anterior. Repouso também
é decisão legítima; ausência de gesto não é falha por definição.

### C5 — Revisão dirigida e separação entre história e estado atual

"Eu disse X" e "X é verdade agora" são alegações distintas. Contestações precisam
localizar o objeto contestado, mesmo quando não for a última fala. Preservar o
original, registrar revisão e invalidar a sustentação de conclusões dependentes.
Uma contestação exige exame; não confirma automaticamente a alternativa.

Owner: registro semântico, referências e continuidade canônicas.

Validação: correção da fala anterior e de uma fala mais antiga; ambiguidade deve
pedir esclarecimento adequado; mudança factual com o tempo não é automaticamente
contradição. Nenhuma revisão autoriza desfazer ou repetir efeito externo.

### C6 — Continuidade sem nova autoridade

Perguntas como "por que você disse isso?", "qual ação?" e "por que fez sozinha?"
recuperam ocorrência e evidências relevantes. Explicação ou lembrança não executa.
Promessas usam pendência canônica com origem, alvo, TTL, escopo e encerramento.
Reinício e troca de chat respeitam isolamento, recuperação e revogação.

Owner: continuidade, contexto integrado, sessão e interpretação canônica.

Validação: turnos intermediários, referentes concorrentes, chat diferente,
evidência vencida e reinício. Explicar uma ação antiga não retoma seu objetivo.

### C7 — Aprendizado qualificado e proporcional à evidência

Distinguir correção factual, erro de interpretação, avaliação da explicação,
preferência de estilo, recusa da iniciativa e falha técnica. Enviar aceitação,
recusa, correção, repetição e silêncio qualificado ao motor existente, apenas
quando o contrato da fonte/entrega se aplicar. Não criar outra janela de silêncio.

Owner: interpretadores de feedback, motor e maturidade de aprendizado existentes.

Validação: "explicou mal" não vira falha do dispositivo; "não gostei do gesto"
não apaga receipt elétrico; replay não aumenta evidência; persistência falha não
ganha anúncio de aprendizado. Uma revisão deve mudar a recuperação futura.

### C8 — Cooperação, disponibilidade e observabilidade verificáveis

Usar quadro/coordenador cooperativos quando várias capacidades participarem.
Cada etapa mantém sua autorização e receipt. Publicar relações e lacunas de
forma limitada no diagnóstico e catálogo vivo, com origem e nível de prova.

Owner: cooperação, catálogo e observabilidade existentes.

Validação: caminho combinado com falha parcial e dependência bloqueada; perguntas
naturais sobre o que consegue explicar; recurso indisponível não é anunciado
como instalado. Sem efeitos disparados pela simples consulta diagnóstica.

## 6. Representação mínima proposta — ainda não é API implementada

Estender contratos/registro existentes somente após confirmar o campo e seu owner:

- Identidades de conversa/sessão/turno, ocorrência da fala e pedido operacional.
- Fala final e trechos/proposições correspondentes, com estado de cobertura.
- Ato, referente, propósito, modalidade, negação e condição pertinentes.
- Referências às fontes, instantes e validade; resultado ou observação exigidos.
- Referência à decisão anterior ao efeito e à expectativa observável, se existirem.
- Referência à autorização, sem copiar ou reconstruir sua validade pelo texto.
- Resultados e entrega por canal referenciados em seus responsáveis canônicos.
- Revisões: ocorrência original, evidência nova, status e conclusões dependentes.

Não exigir uma segunda chamada da LLM em todo turno nem armazenar raciocínio
interno livre como prova. A LLM pode propor relações semânticas; o host valida
identidades, origem, disponibilidade e limites. Formato tipado não comprova sentido.
Ausência de mapeamento seguro permanece explícita, sem regex por frase histórica.

Histórico curto deve ter retenção limitada; memória durável usa os serviços
existentes e exige fonte apropriada. Segredos e conteúdos privados não devem
ser copiados para logs, planos ou artefatos de diagnóstico desnecessariamente.

## 7. Execução por raiz e ordem das provas

1. Inventário da composição atual e matriz de campos/owners. Registrar quais
   relações já existem, quais faltam e quais são somente hipóteses.
2. Escolher uma ocorrência demonstrável e localizar a primeira perda causal.
   Falsificar ao menos duas explicações concorrentes plausíveis antes do patch.
3. Formular RED do contrato, com a primeira asserção na primeira fronteira
   divergente. Componente compartilhado sob investigação deve permanecer real.
4. Quando necessário, construir observação temporária limitada dos eventos
   existentes. Primeiro avaliar relações sem influenciar resposta/decisão/aprendizado.
5. Aplicar candidato mínimo no owner demonstrado; registrar diff e escopo.
6. GREEN focado, vizinhos, composição instalada, modelo real quando pertinente,
   publicação/voz/efeito real nos níveis correspondentes e regressão relevante.
7. Revisar o agrupamento causal se a mesma alteração não resolver os REDs
   atribuídos ao contrato. Não acrescentar exceções históricas para compensar.
8. Atualizar mapa/registro com evidências e limites; roadmap somente depois dos
   pilares aplicáveis comprovados. Nenhum commit automático.

Primeiro recorte preferido: uma fala sobre ação, recuperação de seu referente e
resposta a contestação com evidência da mesma ocorrência. A escolha definitiva
depende do estudo focal; não corrigir um sintoma posterior só por ser fácil.

## 8. Matriz de validação ponta a ponta

| Caso | Prova exigida |
| --- | --- |
| "Por que você disse isso?" | Afirmação identificada + evidência correta; falta de base reconhecida. |
| Pergunta reformulada e entidade trocada | Mesmo contrato sem decorar frases; referente novo não herda fato antigo. |
| Hipótese, opinião ou citação | Não promover a fato externo nem a autorização. |
| Sucesso de uma ação | Fala vinculada ao receipt da ocorrência certa. |
| Falha e resultado incerto | Conclusão observável sem confirmação inventada. |
| Composto com falha parcial | Uma autoria; fontes/receipts independentes; objetivo não concluído por inteiro. |
| CREATE falha antes de ADD | Nenhum efeito dependente; explicação mantém a sequência verdadeira. |
| Texto entregue, áudio falho | Estados por canal preservados; não afirmar escuta humana. |
| Áudio interrompido/substituído | Não atribuir entrega completa ao candidato errado. |
| Correção mais antiga que a última fala | Alvo correto revisado; outras alegações e receipts preservados. |
| Estado muda depois da fala | Histórico preservado; validade atual reavaliada. |
| Turno/chat/sessão muda | Resultado/entrega associados à origem; sem contaminação do contexto novo. |
| Reinício | Recuperação conforme política; nenhum objetivo/autoridade reativado pela memória. |
| "Por que fez isso sozinha?" | Evento, critério prévio, autorização e resultado com limites. |
| "Você faria de novo?" | Avaliação contextual; zero execução implícita. |
| Gesto interrompido/protegido | Separar decisão, PWM, parada, sensor e deslocamento desconhecido. |
| Feedback ambíguo ou silêncio | Não inventar aprovação nem preferência; usar qualificação canônica. |
| Replay e falha de persistência | Sem duplicar evidências; sem confirmar aprendizado ausente. |
| Catálogo indisponível ou cobertura ausente | Explicação honesta do limite; ausência de prova não vira capacidade inventada. |

Cobrir pelo menos dois domínios na prova do contrato compartilhado, preferindo
música/arquivos e corpo ou IoT conforme segurança e isolamento. Cooperação real
dos componentes é necessária no caso combinado. Simular somente folhas externas
para provar composição; não chamar isso de efeito real.

## 9. Testes existentes a reutilizar e complementar

Em `scripts/tests/`: `test_contrato_semantico_fala.py`,
`test_orquestrador_fala_registro.py`, `test_guardiao_fala_tts.py`,
`test_registro_conversa_llm.py`, `test_resposta_operacional_composta.py`,
`test_resposta_operacional_composta_composicao.py`,
`test_receipt_ocorrencia_execucao.py`, `test_observacao_execucao.py`,
`test_continuidade_geral.py`, `test_experiencia_corporal_continua.py`,
`test_continuidade_intencao_corporal.py`, `test_motor_aprendizado.py`,
`test_maturidade_aprendizado.py` e os testes de catálogo/cooperação pertinentes.

Usar `.venv314/Scripts/python.exe -m pytest` no recorte estudado. Revalidar
dependências e isolamento antes de importar a composição. Banco e memória de
teste devem ficar isolados; não iniciar main, voz, rede ou hardware por acaso.

Adicionar testes unitários do contrato, regressão pelo caminho de composição
real, negativo de segurança, consciência de capacidade e cooperação quando
aplicável. Modelo, transporte de áudio e hardware exigem provas próprias.

## 10. Encerramento e pontos ainda em estudo

Encerrar cada raiz somente com cadeia causal, RED válido, candidato mínimo,
GREEN focado/vizinhos, composição, runtime pertinente e regressão relevante.
Relatórios devem distinguir hipótese, prova por código, reprodução local,
integração e efeito real. Suíte verde não demonstra compreensão universal.

Antes de implementar a primeira integração, esclarecer:

- Onde cada rota registra a fala final e quais ocorrências chegam ao registro.
- Quais afirmações operacionais recebem representação semântica atualmente.
- Como mapear proposições a evidências distintas sem outro parser de comando.
- Quais eventos de entrega identificam conteúdo/candidato de forma suficiente.
- Como preservar o motivo original de uma iniciativa entre decisões seguintes.
- Como corrigir uma alegação específica sem contaminar outros chats/sessões.
- Qual retenção é necessária e como manter latência e contexto limitados.

## 11. Acompanhamento desta execução

- Plano salvo com autorização de estudo e implementação incremental.
- Produção na primeira etapa: não alterada. O candidato posterior está na seção 13.
- Primeiro estudo focal concluído no nível descrito na seção 12. A recuperação
  posterior na conversa e a explicação pelo modelo real permanecem abertas.
- Nenhum candidato de produção aplicado; diagnóstico reproduzível adicionado.

## 12. Estudo focal executado em 15/10/2026

### 12.1 Artefato e reprodução

Instrumento: `scripts/analises/sonda_vinculos_fala_acao.py`.
Evidência: `resultados_testes/compreensao_fala_acao_20261015/sonda_vinculos_v1.json`.

```powershell
.\.venv314\Scripts\python.exe -m scripts.analises.sonda_vinculos_fala_acao
```

Para guardar nova coleta, usar `--saida caminho_novo.json`. O instrumento recusa
sobrescrever evidência anterior. Ele reutiliza os owners de memória, experiência,
decisão, corpo e formatação, com a composição de teste corporal já existente.
Só o serial e a espera física são simulados. Não consulta modelo, conta, rede,
voz ou hardware e não inicia `laylay.py`. Saída de diagnóstico não é GREEN do plano.

### 12.2 Fala: indexação e existência da memória são coisas diferentes

Reprodução com o registro semântico atual:

- `Tim Maia foi um cantor brasileiro.` gera alegação `incerto` sem fonte.
- `Pausei a música.` e `Liguei a lâmpada do quarto.` não geram alegações.
- Ao passar um `ResultadoAcao` identificado pelo owner de resultados e depois
  `Pausei a música.` pelo registro real de memória curta, o texto permanece em
  `ultima_resposta` e o receipt identificado/confirmado em `ultima_acao_contrato`.
  A lista de alegações permanece vazia.

O receipt dessa sonda é dado sintético, não confirmação de pausa de um player
real. A prova é sobre os consumidores reais de memória, não sobre execução.

Falsificadas neste recorte:

1. A ausência de alegação significa que o texto da própria fala desapareceu.
2. A ausência de alegação significa que o receipt da ação desapareceu.

Aberto: a pergunta posterior consegue recuperar e relacionar o texto à ocorrência
correta, inclusive depois de outra ação? Ampliar a lista de verbos do registro
semântico não prova essa ligação e não é candidato justificado por esta sonda.

Cadeia conferida por leitura: finalização seleciona `fala_final`; a porta de
histórico conclui o turno; o callback real de memória curta segue por
`RespostaIARuntime` → `AdaptadoresAplicacaoRuntime` → `EstadoContextoRuntime` →
`contexto_compartilhado.registrar_mente_curta` → `registrar_interacao_semantica`.
Este último recebe texto, assunto, fonte e tempo, sem envelope de receipt/entrega.
Há outras rotas de fala; não extrapolar essa ordem a todas elas sem auditar.

### 12.3 Corpo: motivo da decisão não é motivo do resultado

A sonda capturou a intenção antes de `ExperienciaCorporalRuntime.iniciar`,
encaminhando a chamada ao owner original sem modificar a ocorrência produzida.
O gesto percorreu o coordenador e o executor reais com serial simulado.

Resultados observados:

| Fronteira | Resultado da coleta |
| --- | --- |
| Decisão anterior | `expressar`, motivo `mudanca_emocional_causal`. |
| Intenção → ocorrência | `intencao_id` preservado; motivo/registro da decisão não acompanha a ocorrência. |
| Resultado do gesto | Experiência confirmada no transporte simulado; `motivo=plano_confirmado`, referente ao executor/coordenador. |
| Decisão seguinte | `atenta`, motivo `atividade_pc_em_andamento`; mesmo objetivo no recorte. |
| Integridade do passado | Experiência anterior preservada integralmente, sem sobrescrita pela nova decisão. |
| Modelo corporal | Experiência ainda contém o `intencao_id` original. |
| Projeção semântica para autoria | O filtro de `ultima_experiencia` retira esse `intencao_id`; o motivo anterior não aparece no bloco projetado. |
| Segurança | `autoriza_execucao=false`, `prova_deslocamento=false`; consulta não gera novos frames de motor. |

Falsificadas neste recorte:

1. O gesto não gera experiência ou perde a identidade da intenção antes do modelo.
2. Uma decisão seguinte necessariamente sobrescreve a experiência anterior.

Provada por código e reproduzida na integração: o payload da ocorrência não
captura o motivo decisional; a projeção posterior perde a referência da intenção.
Isso limita a evidência disponível para uma explicação histórica. Não foi provado
que a LLM inventou motivo, que há corrida de callback, ou que todo motivo antigo
desaparece de qualquer outro registro existente.

A primeira fronteira a estudar para C4 é a captura/recuperabilidade da decisão
anterior à criação da ocorrência. Corrigir somente o filtro do prompt continuaria
sem garantir o motivo histórico. Verificar também o histórico cooperativo e as
referências de objetivo antes de propor uma cópia ou owner novo.

O nome `motivo` tem semânticas distintas nos responsáveis: decisão e retorno
operacional. Não renomear ou reinterpretar o motivo do executor como explicação
da iniciativa. Não substituir esse fato por uma justificativa gerada depois.

### 12.4 Controles executados

| Comando com `.venv314/Scripts/python.exe -m pytest` | Resultado |
| --- | --- |
| `scripts/tests/test_registro_semantico.py scripts/tests/test_objetivo_corporal_entre_turnos.py scripts/tests/test_experiencia_corporal_continua.py -q --tb=short` | 58 passed, 20,35 s. |
| `scripts/tests/test_registro_conversa_llm.py scripts/tests/test_orquestrador_fala_registro.py scripts/tests/test_resposta_operacional_composta_composicao.py -q --tb=short` | 57 passed, 4,19 s. |

Total: **115 testes existentes aprovados**. São controles dos componentes e da
composição com folhas externas isoladas; não comprovam os contratos futuros,
compreensão geral, inferência real do modelo, reprodução audível ou movimento físico.

A primeira tentativa do instrumento falhou ao usar `deepcopy` em uma coleção
viva com RLock. Essa falha era do instrumento, não um RED do contrato. A coleta
válida usa `estado.obter_copia`, sem alteração do estado compartilhado de produção.

Oito fontes críticas tiveram SHA-256 comparado antes/depois: registro semântico,
contexto compartilhado, modelo corporal, companhia corporal, experiência corporal,
orquestrador de fala, estado/contexto runtime e `laylay.py`. Todas permaneceram
iguais durante o estudo. Isso atesta esse recorte, não toda a worktree paralela.

### 12.5 Decisão sobre produção e próximo recorte

**Produção não alterada.** Há evidência suficiente de perda de vínculo em uma
projeção, mas ainda não para escolher um novo contrato de captura/recuperação
geral sem arriscar duplicar os owners existentes ou tratar somente o corpo.

Próximo recorte causal:

1. Percorrer uma consulta posterior à própria fala na composição instalada,
   preservando os owners de histórico, resultado, registro semântico e continuidade.
   Isolar somente modelo e efeitos externos; observar a recuperação antes de
   avaliar a redação. Cobrir uma ação simples e um composto parcialmente falho.
2. Auditar a recuperação da decisão original em experiência/objetivo/quadro
   cooperativo. Se não houver registro canônico suficiente, formular um RED de
   captura anterior ao efeito que sirva também a outro domínio, sem mudar concessão.
3. Só então decidir entre preservar uma referência já existente, estender o
   registro semântico ou adicionar um contrato compartilhado mínimo. Nenhuma
   dessas alternativas está implementada ou escolhida por conveniência.

Mudanças desta execução: este plano, o instrumento diagnóstico e sua evidência
JSON. Nenhum teste existente enfraquecido, nenhum modelo/configuração alterado,
nenhuma autonomia real ativada e nenhum commit criado.

## 13. Continuação autorizada — correlação da fala entregue e recuperação

15/10/2026. Pedro pediu estudar a composição real e aplicar/validar a correção
quando a raiz fosse comprovada. O estudo percorreu os owners instalados e
reproduziu a perda entre publicação e retenção do vínculo com seus receipts.

Oito REDs canônicos e um controle GREEN antecederam o candidato. A correção
estende o registro semântico e usa uma única projeção nas rotas normal e rápida,
preservando a última ação cronológica, fontes distintas e falha parcial. Dez
testes de composição, incluindo o turno completo com modelo controlado, passaram.

Foram alterados cinco arquivos de produção nos owners de registro, fala e
projeção. Não houve alteração de executor, autoridade, decisões corporais,
firmware, modelo ou voz. Não há commit. Fontes anteriores da worktree, hashes,
diff incremental, REDs e resultados estão preservados em:
`resultados_testes/compreensao_fala_acao_20261015/recuperacao_real/RELATORIO.md`.

Regressão relevante: 390 GREEN / 2 RED. Os dois REDs reproduzem com as cinco
fontes anteriores ao candidato e permanecem registrados; não foram ocultados.
Controles posteriores de vínculo/sessão/projeção: 31 GREEN, com sobreposição
de testes. Não somar os grupos como se fossem casos diferentes.

Qwen local real recebeu o contexto recuperado. No simples, preservou o limite
histórico; no composto, preservou sucesso parcial mas inventou causa para a
falha. Logo, C1–C2 de redação fiel e F1 continuam abertos. Essa coleta não teve
publicação, áudio ou efeitos reais. Entrega da evidência não equivale a compreensão.

Escopo desta correção: vínculos efêmeros da mesma sessão, por citação literal
ou referência selecionada pelo owner contextual. Não implementa recuperação
persistida ao reabrir chat, atribuição por cláusula, captura de motivo autônomo
ou revisão causal geral. O próximo trabalho deve partir dessas fronteiras,
sem repetir o diagnóstico de ausência total de memória nem criar outro parser.

## 14. Continuação autorizada — explicação fiel e causa desconhecida

15/10/2026. A causa inventada pelo Qwen foi rastreada pela composição instalada.
O replay esclareceu um limite da coleta anterior: a saída bruta original não
era publicada; a guarda a trocava por uma negação que perdia o sucesso parcial.
Outra causa inventada, formulada sem os marcadores operacionais reconhecidos,
chegava ao consumidor. A fonte estava no prompt e ausente do contrato do juiz.

Correção no contrato compartilhado: mesma seleção histórica no prompt e no
julgamento; execução/confirmação independentes por etapa; causa e processamento
não informados permanecem desconhecidos. Realizações limitadas ao receipt,
sem autoaprovar prosa livre nem copiar histórico para comandos atuais.
Owner canônico em `cognicao/explicacao_fala_historica.py`, integrado a registro,
contrato, qualidade, validação, preparação e guarda final. Sem regra por frase
ou domínio. Estados já satisfeitos sem nova execução e perguntas retrospectivas
naturais têm REDs/controles próprios e mantêm o mesmo contrato.

Validação focal final: 66 GREEN / 1 RED preexistente de duplicação textual.
Qwen real pela composição instalada preservou todos os resultados nos três
casos, com zero comandos admitidos; os executores e a voz eram folhas
controladas. O texto bruto do modelo ainda extrapola; a realização verificada
protege a publicação. Isso não comprova compreensão geral nem autoria livre.

Outras baterias: 347 GREEN / 41 RED, e 278 GREEN / 2 RED. Os 41 reproduzem
exatamente IDs/mensagens nas fontes anteriores; os dois condicionais/catálogo
já estavam reproduzidos no baseline anterior. Não somar lotes sobrepostos.
O RED de duplicação também foi reproduzido nas fontes anteriores: pré-fluxo
publica texto, recebe False da voz e cai na publicação seguinte. Foi preservado
em teste independente, sem ampliar este patch factual para o contrato de entrega.

Fontes, responsáveis, critérios, REDs, controles, diff e HTTP bruto:
`resultados_testes/compreensao_fala_acao_20261015/causalidade_composta/RELATORIO.md`.
Seis arquivos existentes e um owner novo em produção. Nenhum executor,
concessão, motivo corporal, configuração de modelo/voz ou commit alterado.
C1–C2 ganham proteção limitada; F1 global, entrega textual/voz, persistência
entre chats e captura de motivo autônomo continuam com seus próprios limites.

Regressão final das fontes entregues: 632 GREEN / 44 RED em 22 módulos.
Os 44 são os 41 comparados por ID/mensagem, os dois de catálogo reproduzidos
novamente com as fontes anteriores e a duplicação textual também reproduzida.
Essa bateria não é um GREEN global; as pendências continuam visíveis.

## 15. Continuação autorizada — duplicação textual no pré-fluxo

15/10/2026. Raiz de entrega investigada separadamente de causa inventada e do
contrato factual da seção 14. O texto era publicado/registrado por seu canal,
mas `OrquestradorFalaRuntime.falar` retornava apenas o bool da voz. O emitidor
curto devolvia False e o pré-fluxo caía na geração/finalização seguinte.

RED histórico reproduzido pela composição instalada. Controle com a fila real
de `VozRuntime` repetiu a perda quando a deduplicação recusou uma solicitação
idêntica; não depende de Qwen ou indisponibilidade total da voz. Texto sem voz,
voz sem texto e ambos recusados foram comparados com fontes anteriores.

Contrato corrigido em dois arquivos: orquestrador agrega aceitação comunicativa
por texto publicado OU porta de voz aceita; finalização expõe `entrega_aceita`
e deixa `audio_entregue=None`. Fila aceita continua distinta de reprodução;
callbacks e observadores exclusivos de voz não usam o agregado. Continuidade
passa a acompanhar também o texto entregue e a deduplicação operacional não
libera nova publicação depois de aceite textual. Dez fontes de controle,
incluindo voz, pré-fluxo, emitidor, composição e contrato factual, inalteradas.

90 testes focados GREEN. Composição instalada: uma publicação no composto
histórico, zero geração posterior; texto e deduplicação real de voz concluem,
nenhum canal aceito permite seguir sem registrar falsa entrega. Prova em música
e arquivos/e-mail, sem exceção por domínio, frase ou número de turno. Não houve
main/interface diária, áudio audível ou novos efeitos externos. Nenhum commit.
Regressão ampla e comparação das pendências estão no relatório dedicado:
`resultados_testes/compreensao_fala_acao_20261015/entrega_pre_fluxo/RELATORIO.md`.

Controle focal final: 104 GREEN, incluindo feedback/worker de áudio. Fixture
P20 corrigida para usar o owner real de continuidade, que devolve o estado;
o antigo stub None apagava o receipt ao exercitar o novo caminho textual.
As asserções de identidade/canal/aprendizado foram preservadas. Duas falhas
de volume e um timeout da fixture multimodal repetiram nas fontes anteriores;
não foram misturados com esta raiz de aceitação comunicativa.
Regressão final: 417 GREEN / 2 RED preexistentes em 17 módulos. Os 44 casos da
fixture multimodal com timeout permanecem sem validação e não contam como GREEN.

## 16. C4 — motivo capturado antes do efeito, 15/10/2026

Continuação autorizada durante a janela de 30 minutos anterior ao desligamento.
A composição instalada confirmou a perda sugerida na seção 12.3: motivo existe
na decisão, mas não entra na ocorrência. Histórico cooperativo e aprendizado
também não tinham uma cópia recuperável. Três REDs causais e um controle antes
do candidato; não confundir motivo da decisão com `plano_confirmado` do retorno.

Contrato puro compartilhado `DecisaoObservada`, sem novo estado ou parser:
owner registra identidade, regra/motivo, objetivo, referências e critérios antes
de chamar o executor. Companhia corporal é a primeira adoção; experiência
existente conserva a fonte no histórico/aprendizado, e o modelo corporal projeta
o registro correto. Fonte estrangeira/posterior ou dict reintroduzido como tipo
são recusados. Ausência histórica continua desconhecida. Resultado tardio não
reescreve a decisão e memória restaurada não concede execução.

Responsáveis: `companhia_corporal.py` captura; `decisao_observada.py` fixa o
contrato; `experiencia_corporal_runtime.py` conserva a fonte; `modelo_corporal.py`
projeta. Três arquivos existentes e um novo. Decisor, executor, composição,
governança, voz e configuração inalterados; nenhum commit ou autonomia real nova.
Captura não conhece rationale interna de proposta LLM: `intencao_da_mente` só
identifica sua origem. Repouso/observação sem efeito e expectativas ausentes
continuam no escopo futuro de C4, sem inventar registros retroativos.

28 focados GREEN antes da opção real. Regressão corporal:420 GREEN/17 RED;
baseline:393 GREEN/mesmos17 RED, mesmas primeiras asserções. Regressão dos
contratos compartilhados de fala:137 GREEN/1 SKIP opcional. Projeção com a fonte
cabe no transporte sem perder o protocolo. Provas de composição, falha elétrica,
aprendizado e memória usam serial e persistência isolados, sem efeito físico.

Qwen real pela composição:7 GREEN de transporte/fonte, quatro HTTP200 nas duas
rotas, zero comandos enviados ao executor; finalização isolada. **Fidelidade da
explicação ainda RED:** percepção visual inventada no bruto, rationale sem fonte
no reparo e confusão entre indisponibilidade atual e tentativa histórica.
Isso não encerra C1/F1 nem C4 como um todo. A próxima fronteira é ligar a mesma
fonte ao julgamento da explicação, após capturar contrato/referente reais e criar
replay canônico. Não há patch por frase para esse novo sintoma.

Fechamento da janela: replay offline do preparador real já preservado no mesmo
diretório. Duas causas sem fonte são admitidas, enquanto o controle com a regra
observada também passa. `replay_reparo_semantico.py --exigir-fidelidade` reproduz
o RED sem LLM ou efeitos. A captura do contrato e referente do julgamento segue
necessária antes de escolher o candidato dessa próxima fronteira.

Relatório, fontes congeladas, diff incremental, HTTP e próximos critérios:
`resultados_testes/compreensao_fala_acao_20261015/decisao_antes_efeito/RELATORIO.md`.

## 17. Revisão sem fonte no julgamento — continuação de C1/C4/F1

15/10/2026. Continuação autorizada após o handoff da seção 16. A composição
atual reproduziu a primeira perda: motivo no prompt/reparo, sem ocorrência
vinculada ao contrato de explicação. A restrição sobre experiências físicas
inventadas não verificava sustentação causal; uma causa inventada mais discreta
passava. Dois REDs antes do candidato; replay expandido nas fontes anteriores
também confirmou a perda. Não tratar isso como uma nova raiz por nome de gesto.

O juiz compartilhado de explicação histórica recebe agora `ExplicacaoOcorrencia`
com episódios tipados selecionados pelo owner. A experiência corporal fornece
sua própria fonte, e o orquestrador do turno a vincula à consulta; geração,
preparação, qualidade e guarda final consomem o mesmo contrato. Motivo anterior,
tentativa, escopo de confirmação e estado atual ficam distintos. Fonte ausente
não nega o passado; duas ocorrências exigem referência. Fonte inválida/projeção
JSON não desliga a proteção nem se promove a fato pela forma.

Responsáveis: `experiencia_corporal_runtime.py` seleciona sua fonte;
`decisao_observada.py` define os tipos; `referencias_linguagem.py` resolve a
retrospectiva/citação; composição injeta o serviço; `contrato_fala.py` vincula;
`explicacao_fala_historica.py` e `validacao_contrato_fala.py` julgam. Nove arquivos
existentes, sem outro banco, histórico ou juiz exclusivo de corpo. O tipo/juiz
é testado com corpo, arquivos e IoT, mas outros owners ainda precisam fornecer
seus motivos reais. Não inventar rationale de proposta LLM ou de receipt.

Final:39 GREEN com inferência real e composição instalada. Replay do ciclo
publica uma vez nas rotas normal/rápida, sem nova ação; Qwen HTTP200 nas duas
rotas preserva a fonte nas conclusões. Bruto ainda pode divergir: realização
limitada protege a conclusão, sem certificar prosa livre. Corpo/contas/voz são
isolados; não houve efeito físico, UI diária ou áudio audível.

Regressões:245 GREEN em fala no lote inicial; lote expandido256 GREEN/1 RED/1
SKIP; corpo301 GREEN/7 RED; composição/diagnóstico92 GREEN/7 RED. Os15 REDs
vizinhos repetem IDs/primeiras asserções com fontes anteriores, inclusive nos
subprocessos: orçamento corporal, receipts/admissão e expectativas antigas.
Não somar lotes sobrepostos nem declarar GREEN global. Nenhum commit,
configuração, firmware, executor, concessão ou política de decisão alterados.

Critérios locais alcançados: causas sem fonte não passam pelo contrato
instalado; controle com regra registrada é preservado; falha/ambiguidade/fonte
ausente são distintas; referência inexistente não empresta outro episódio;
consulta não produz efeito. F1/C4 gerais, repouso sem ocorrência, redação livre
e recuperação fora da janela permanecem abertos. Relatório, fontes e diff:
`resultados_testes/compreensao_fala_acao_20261015/revisao_causa_sem_fonte/RELATORIO.md`.

## 18. Obrigação explicativa antes da resolução da referência — C1/F1

16/10/2026. Continuação autorizada. O controle com episódio selecionado passou,
mas perguntas mais abertas perdiam a obrigação de fonte e admitiam motivo
inventado na preparação e na guarda. Histórico íntegro, geração controlada sem
Qwen e modalidade sem autoridade falsificaram explicações concorrentes antes
do patch. Mesmo mecanismo em perguntas de corpo, arquivos e IoT; nenhum novo
ID por frase/habilidade nem mudança na captura C4.

Contrato: reconhecer a obrigação retrospectiva não depende de encontrar uma
ocorrência. Sem fonte compatível, conservar consulta/turno tipados, informar o
limite e pedir qual fala/ação; ausência não nega o passado nem escolhe o único
owner disponível. O ciclo sequencial encontrou uma fala contextual substituindo
ação não resolvida; RED antes da correção no binding, mantendo citação literal
e pergunta sobre a própria fala. Não modificar o seletor global de contexto.

Responsáveis: `referencias_linguagem.py` qualifica construção/referente;
`contrato_fala.py` mantém obrigação e elegibilidade da fonte;
`explicacao_fala_historica.py` realiza ausência sem completar causa. Três arquivos
de produção; owners mantêm seleção e evidência, sem parser privado por domínio,
novo histórico ou juiz LLM. Leitura gramatical e prosa continuam limitadas.

Critérios locais: fonte ausente não desliga julgamento; referência corporal não
é emprestada; motivo atual e receipt sem vínculo não justificam; fala/citação
legítimas sobrevivem; controles de hipótese/futuro/outro ator/assunto geral não
viram retrospectiva; seis ciclos normal/rápido publicam uma vez sem execução.
37 GREEN finais com Qwen local real nas duas rotas. Bruto ainda pode inventar;
o contrato protege a conclusão sem certificar compreensão geral do modelo.

Regressões:303 GREEN/4 RED/1 SKIP em fala,249 GREEN/7 RED/5 SKIP em integração,
81 GREEN/1 SKIP em fonte/autoridade. Sem somar lotes sobrepostos. Os11 REDs
vizinhos foram comparados por ID/primeira asserção com somente os três contratos
anteriores, incluindo filhos. Mudança USB paralela em laylay.py preservada e
separada do candidato; base original não atualizada. Sem commit, efeitos físicos,
UI diária ou áudio. F1/C4 gerais, múltiplos owners e explicação livre seguem
abertos; relatório com fontes congeladas, diff e próxima fronteira:
`resultados_testes/compreensao_fala_acao_20261016/obrigacao_explicativa/RELATORIO.md`.

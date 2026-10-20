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

## 19. Cobertura histórica por ato — continuação C1/F1, 17/10

Estudo autorizado da próxima fronteira. Duas perguntas já eram preservadas
pelo interpretador, mas seleção de episódio no texto inteiro passava a ser
cobertura do conjunto: a resposta explicava somente o gesto e perdia a pergunta
sobre arquivo/tomada. RED instalado nas duas ordens, com fonte corporal íntegra
e sem inferência; segmentação, perda da fonte e estilo do Qwen falsificados
como causas. Mecanismo de cobertura parcial distinto da ausência total de
obrigação corrigida na seção18; captura C4 e entrega não reabertas.

Contrato: conservar todos os atos canônicos e suas fontes textuais. Consultar
o mesmo owner por literal de cada parte; vincular fonte/motivo/resultado de
forma independente e realizar uma conclusão conjunta. Fonte de uma parte não
cobre outra. Falha, ausência, ambiguidade, fonte vencida ou sem motivo recebem
limite próprio, sem apagar a fonte válida restante ou declarar sucesso total.
Citação de fala não vira ocorrência; JSON e fonte estrangeira não viram prova.

Responsáveis: interpretador existente delimita; orquestrador fornece porta do
owner; contrato_fala vincula; decisao_observada conserva os tipos imutáveis;
explicacao_fala_historica seleciona/realiza/julga; validacao_contrato_fala usa o
mesmo juiz. Cinco arquivos de produção, uma fixture e um teste novo. Sem banco,
parser de habilidade, executor, concessão ou LLM juiz novos; nenhum commit.

Critérios: duas partes permanecem observáveis; motivos/confirmacões não se
misturam; falha parcial conserva a fonte válida; fonte incompatível não ganha
cobertura; pergunta repetida não cria episódio; fluxo operacional não recebe
esse contrato; seis ciclos (três consultas × normal/rápido) publicam uma vez
sem executor/MOTOR adicional simulado.29 GREEN finais, incluindo dois HTTP200
do Qwen local real com ambas as partes na conclusão. Timeouts anteriores em
candidato e base preservados, sem aumentar prazos para fabricar GREEN.

Controle final também exige aceitação estável da realização oferecida pelo
próprio contrato quando a fonte contém espaços repetidos. RED registrado,
mesma projeção de espaços nos dois lados, literal original preservado. Sem
aprovar paráfrases ou causas adicionais; inferência real repetida depois.

Elegibilidade também conserva fontes que o owner já resolvia fora da gramática
geral de atuação própria (“o que motivou esse movimento?”). RED ampliado antes
de delegar cada parte à porta existente; nenhuma frase adicionada ao parser.
Seleção do texto inteiro só exige binding das partes, nunca comprova cobertura.

Regressão final:306 GREEN/2 SKIP em fala/contratos;199 GREEN/11 RED/1 SKIP em integração. Mesmos
11 IDs/mensagens/primeiras asserções com os cinco contratos anteriores também
nos filhos. Não somar lotes sobrepostos. Trabalho paralelo de notificação
corporal no root/experiência preservado e separado do diff desta tarefa.

Elipse sem interpretação e pergunta fora do escopo histórico ficam visíveis
como ainda não respondidas, sem inventar ator/owner. Isso protege cobertura,
não conclui respostas de conteúdo para todas as partes nem certifica prosa
livre. F1/C4 gerais seguem abertas. Sem main diário, UI, áudio ou corpo físico.
Fontes, responsáveis, critérios, timeouts, diff e limites completos:
`resultados_testes/compreensao_fala_acao_20261017/cobertura_por_ato/RELATORIO.md`.

## 20. Agente da pergunta antes da atribuição de motivo — C1/F1, 17/10

Continuação autorizada. RED instalado: perguntas sobre eu/ele/ela/nós
selecionavam episódio e motivo da Laylay porque o seletor conservava tipo da
ação e referência, mas ignorava o agente. Controle sobre você recupera a fonte
íntegra no mesmo processo; geração controlada afasta Qwen como causa. Mencionar
eu em “quando eu cheguei” não troca o agente principal. Primeira perda na
seleção/atribuição, não na segmentação, captura C4 ou entrega.

Contrato: fonte de decisão própria não prova motivo de outro agente ou grupo.
Leitor compartilhado qualifica pessoa da oração causal e tempo separadamente;
tipo/owner do episódio não substitui essa relação. Consulta retrospectiva de
agente não vinculado conserva obrigação com limite de evidência; uma fala
própria citada como contexto não responde por ele. Pacote composto mantém
limite da parte alheia e motivo válido da Laylay na outra parte.

Responsáveis: referencias_linguagem centraliza pessoa/forma verbal e qualifica
seleção; contrato_fala vincula consulta e fonte elegível; explicacao_fala_historica
aplica o mesmo limite a geração, realização, revisão e guarda. Três arquivos de
produção. O owner corporal reaproveita o leitor existente sem patch privado;
fontes tipadas de corpo/arquivos/IoT cobrem o contrato comum. Sem novo histórico,
juiz LLM, executor, concessão ou reconstrução de motivos humanos.

Critérios: seleção não transfere episódio próprio entre agentes reconhecidos;
fonte própria fornecida diretamente também é limitada; citação e oração
subordinada não trocam sujeito principal; presente não vira passado por
terminação; seis ciclos normal/rápido publicam uma vez sem novo executor/MOTOR
simulado.47 GREEN finais, incluindo Qwen local HTTP200 nas duas rotas. Regressão
de fala306 GREEN/2 SKIP; integração199 GREEN/11 RED/1 SKIP. Mesmos11 IDs,
mensagens e primeiras asserções com os três contratos anteriores nos filhos.
Não somar lotes sobrepostos; expectativas de três controles antigos foram
atualizadas para exigir limite explícito, preservando seus casos e IDs.

Sem commit, main diário, corpo físico, UI ou áudio. Leitura gramatical limitada:
nomes arbitrários, referências indiretas, elipses e resolução de identidade de
terceira pessoa continuam abertas. Não certificar prosa livre ou inferir o
owner por recência. F1/C4 gerais não encerradas. Relatório com fontes,
responsáveis, provas e mudanças de expectativa:
`resultados_testes/compreensao_fala_acao_20261017/agente_da_explicacao/RELATORIO.md`.

## 21. Execução do plano — revisão dirigida C5, 17/10

Pedro autorizou avançar no plano. O recorte passou da explicação retrospectiva
para identificar qual alegação deve ser revista, inclusive depois de outros
assuntos. A composição instalada mostrou fonte antiga íntegra, mas revisão da
recente; repetição do pipeline ainda atingia outra alegação. Perda de memória
e geração Qwen foram afastadas com fontes presentes e modelo vazio.

Contrato compartilhado no registro semântico: referência literal/ID precede
revisão; ausência/ambiguidade não permitem escolher por recência. Original,
fonte e estado anterior ficam auditáveis; correção não confirma alternativa.
Contexto projeta a mesma seleção, sem outro parser de última resposta. Receipts,
efeitos e autorização não são reescritos pela contestação textual.

Depois desse GREEN, duas falhas distintas permaneceram na projeção rápida:
o estado instalado transportava falas observadas, mas não revisões. Registradas
em etapa separada, com baseline próprio. Uma visão limitada do mesmo owner
agora chega às duas rotas; não se expõe o histórico inteiro nem se cria outro
juiz ou banco. O relatório separa as causas, candidatos e replays.

Responsáveis: `registro_semantico.py`, `contexto_compartilhado.py`,
`contexto_integrado.py`, `autonomia/contexto_resposta_ia.py` e
`integracao/composicao_contextos_ia.py`. Cinco arquivos de produção; um teste
novo. Primeiro RED:13 falhas/2 controles. Etapa de projeção:2 falhas na rápida,
reproduzidas com seleção corrigida e fontes anteriores nos subprocessos.
Regressão final:395 aprovados/8 subtestes, incluindo25 casos novos; sem somar
grupos sobrepostos. Composição instalada em duas ordens de assuntos, memória e
publicação reais, com modelo/voz/efeitos externos isolados. Nenhum commit.

C5 não encerrado globalmente: prompt com revisão não prova que toda redação
livre a respeita. Paráfrase, conclusões dependentes, revalidação por fonte nova,
persistência real entre chats e feedback qualificado C7 continuam em estudo.
C4 mantém expectativas/repouso nos próprios owners. Próximo recorte é seguir
a revisão identificada até recuperação e julgamento posterior, sem outro ciclo
de exceções por frase. Fontes, critérios e limites:
`resultados_testes/compreensao_fala_acao_20261017/revisao_dirigida/RELATORIO.md`.

## 22. C5 — revisão vinculada ao julgamento posterior, 17/10

Continuação autorizada após a seção21. Fonte e projeção estavam presentes,
mas o contrato do juiz não recebia a revisão. Consulta pelo ID reafirmava o
conteúdo contestado; por citação, a guarda anterior respondia sobre entrega e
receipts, sem reconhecer contestação. Composição com modelo vazio afastou
geração; registro íntegro afastou perda de memória. Seis REDs antes do candidato.

O registro fornece `RevisaoAlegacaoConsulta` imutável, vinculada ao alvo,
consulta e turno. Contrato de fala conserva essa fonte; preparação, qualidade,
aderência e guarda usam o juiz compartilhado existente. Realização limitada
reconhece estado contestado/corrigido, sem provar falsidade ou alternativa e
sem alterar receipts/autorização. JSON não vira fonte tipada; fonte inválida
mantém limite explícito e estável. Sem detector de frase ou parser de domínio.

Responsáveis: registro_semantico, contrato_fala, explicacao_fala_historica e
validacao_contrato_fala. Quatro arquivos de produção; fixture ampliada e um
teste novo. Quatro ciclos completos arquivo/tomada × normal/rápido publicam
uma vez sem executor externo. Qwen local real: dois HTTP200 e publicação
limitada nas duas rotas;30 focados aprovados. Regressivos:423 aprovados/2 skips
e8 subtestes;169 aprovados/3 skips no recorte histórico. Não somar focal e
regressivos sobrepostos. Replay das fontes anteriores reproduz os seis REDs,
também nos subprocessos. Sem commit ou alteração de modelo/configuração/voz.

Escopo validado: pergunta não operacional de alvo explícito único já revisado.
Paráfrase/pronome, ambiguidade, vários segmentos, conclusões dependentes,
fonte nova verificada e aprendizado C7 permanecem abertos. Não certificar
prosa livre, UI diária, áudio ou efeito físico. Próxima fronteira é o suporte
das conclusões que dependiam da alegação revisada. Provas, erros de instrumento,
fontes, critérios e limites:
`resultados_testes/compreensao_fala_acao_20261017/julgamento_revisao/RELATORIO.md`.

## 23. C5 — suporte interno das conclusões, 17/10

Continuação autorizada. O inventário refinou a hipótese: não há grafo geral de
inferências, mas o campo `fonte` pode conservar o ID de outra alegação. Na
composição, essa referência era promovida a fonte externa; B/C permaneciam
admitidas após contestar A, embora B.fonte=A.id e C.fonte=B.id estivessem
íntegras. Modelo vazio, revisão presente e vizinha independente preservada
falsificam geração, perda de memória e invalidação geral. Sete REDs antes do patch.

Contrato: fonte interna declarada não confirma inferência ou fato externo.
Registro lê a validade da cadeia sem reescrever histórico; origem revisada
produz suporte em revisão, não conclusão falsa. Proveniência, resumo,
projeções e consulta tipada compartilham a mesma restrição. Ausência, ciclo
e ID duplicado falham fechados. Não se deduz vínculo por assunto/conectivo.

Responsáveis: proveniencia_informacao, registro_semantico e
explicacao_fala_historica. Três arquivos de produção; teste novo. Binding,
composição, execução, concessões, modelo e voz preservados. Oito ciclos
arquivo/IoT × um/dois níveis × normal/rápido publicam uma vez sem efeitos.
Qwen real nas duas rotas:dois HTTP200,25 focados aprovados. Regressão:656
aprovados/7 skips/8 subtestes em19 módulos, incluindo o focal; sem somar lotes.
Replay dos três contratos anteriores repete os sete REDs também nos filhos.
Sem commit, main diário, UI, áudio ou confirmação física.

Escopo: fonte interna já declarada por ID, uma fonte por alegação, consulta
explícita única. Referência não prova implicação. Descobrir dependências na
prosa comum, múltiplas premissas/alternativas, fonte nova e aprendizado C7
continuam abertos. Próxima fronteira é a declaração de suporte por proposição
na autoria, com cobertura e revisão semântica; não ativar o grafo offline ou
tomar proposta/âncora como prova. Fontes e limites:
`resultados_testes/compreensao_fala_acao_20261017/suporte_conclusoes/RELATORIO.md`.

## 24. C5 — declaração de suporte na autoria, 17/10

Continuação autorizada. O bruto original conservava `suporte_proposicoes`, mas
o planejamento não transportava a declaração. Memória curta recebia só fala e
fonte agregada; duas proposições eram confirmadas pela mesma fonte contextual,
inclusive aquela cujo suporte proposto estava ausente. Quatro REDs causais em
arquivo/IoT × normal/rápido antes do candidato. Bruto presente, modelo controlado
e observação textual afastam perda no transporte, geração e silêncio de entrega.

Contrato receptor opcional: unidades literais e referências propostas ficam
imutáveis, vinculadas à emissão original, turno e consulta. Forma, cobertura
textual e presença de IDs não provam verdade, implicação ou atomicidade semântica.
Registro conserva pendência, sem promover referência proposta a fonte canônica
nem distribuir fonte global como confirmação dessa autoria declarada. Vinte e
quatro declarações por sessão; renovação limpa propostas pendentes. Se a fala
for substituída, o suporte original não ganha vínculo com o novo texto.

| Contrato | Responsável | Critério de validação |
| --- | --- | --- |
| Captura da proposta vinculada | `orquestrador_turno_runtime` e novo `cognicao/suporte_autoria` | Bruto do host, consulta/turno, forma estrita, âncoras únicas/ordenadas, limites e cobertura textual. |
| Transporte/registro compartilhado | `contexto_compartilhado` e `registro_semantico` | Declaração pendente sem fonte emprestada; tipo/turno/consulta/fala divergentes recusados; deduplicação e renovação. |
| Revisão semântica | Ainda aberta | Confrontar proposição com conteúdo das fontes; ID existente ou proposta LLM não aprova apoio. |

Três arquivos existentes e um módulo novo de produção, um teste novo. Quatro
ciclos instalados preservam declaração e publicação única, sem comandos/efeitos.
Regressão relevante:740 aprovados/9 skips/8 subtestes em21 módulos. Focal final:
21 aprovados, incluindo duas coletas Qwen real com dois HTTP200. Nestas, a
revisão substituiu a fala e o vínculo foi recusado corretamente: prova real da
recusa, não publicação positiva das proposições. Ensaios também mostraram
omissão/invalidade do campo; não há garantia de emissão no prompt diário.
Expectativa inicial de vincular fala substituta foi corrigida pela evidência,
sem relaxar produção. Replay das três fontes anteriores reproduz quatro REDs
nos filhos. Grupos sobrepostos; nenhum commit ou mudança de modelo/voz.

Campo ausente mantém legado, inclusive atribuição agregada anterior. Não
encerrar C5/C1/C2/F1 gerais nem aprendizagem C7. Próxima fronteira é negociar
declaração na autoria e provar revisão semântica antes de criar relação utilizável;
grafo offline permanece offline. Sem main diário, UI, áudio ou efeito físico.
Fontes, falhas intermediárias, responsáveis e limites:
`resultados_testes/compreensao_fala_acao_20261017/declaracao_suporte_autoria/RELATORIO.md`.

## 25. C5 — obrigação de suporte no contrato autoral, 17/10

Continuação autorizada. Emissão principal não negociava suporte obrigatório;
receptor opcional aceitava ausência. Quatorze REDs antes da produção. Codec e
transporte existentes já ofereciam a capacidade: reutilizados, sem outro parser.
Normal/rápido, conversa/operacional e três projeções fechadas passam pelo mesmo
contrato. A recuperação não pode remover a obrigação e aceitar uma redação vazia
de suporte: serviço compartilhado aplica o owner aos tipos autorais do host.

Qwen real demonstrou que exigir duas cópias do texto não garantia cobertura.
Contrato final recebe unidades como representação única; host junta seus textos
para formar a fala. Campo `fala` paralelo é recusado também no schema. Conteúdo
permanece de autoria da IA; a projeção não valida implicação nem fontes.
Presença, ID existente e cobertura textual continuam propostas, sem autoridade.

Controle adicional: principal recusada + reparo válido + fonte contextual.
Quatro REDs mostraram promoção do reparo pela fonte global. Captura obrigatória
agora conserva ausência principal tipada; reparo continua incerto e não herda
prova nem suporte anterior. Replay só do orquestrador repete os quatro casos;
replay dos quatro contratos anteriores reproduz falta de negociação em18 casos.

| Contrato | Responsável | Critério |
| --- | --- | --- |
| Envio obrigatório por ocorrência | `contexto_resposta_ia` | Todas as projeções do envio principal atual; fonte/turno alheios preservam isolamento. |
| Unidades e projeção literal | `suporte_autoria` | Fonte ausente explícita, forma/cobertura/limites e fala derivada; sem segunda cópia ou autoaprovação. |
| Recuperação não contorna formato | `cliente_llm_runtime` | Tipos autorais compartilhados falham fechados; interpretação interna mantém protocolo. |
| Ausência não libera confirmação | `orquestrador_turno_runtime`/`suporte_autoria` | Ausência capturada pelo host chega ao registro; fonte global não certifica o reparo. |

Quatro arquivos de produção. Dezesseis ciclos instalados com transporte controlado,
dois domínios/duas rotas, sucesso e falhas/recuperação. Qwen real nas duas rotas:
dois HTTP200, unidades e fala registradas sem pedido de metadados na utterance;
58 focados aprovados/2 skips. Uma publicação por ciclo, sem efeitos externos.
Nenhum commit, troca de modelo/voz ou ativação corporal. Regressão31 módulos:
1.045 aprovados/11 skips/8 subtestes e um RED prévio do catálogo, sem erros.

Garantia cobre o envio autoral principal atual e tipos autorais de recuperação,
operação e presença explicitamente identificados pelo host. Portas legadas que
chamam `principal` fora do envio canônico requerem migração própria; não afirmar
garantia de toda saída da aplicação. Revisão semântica, atomicidade das unidades,
fontes alternativas/novas, conservação individual de mesclas/reparos e C7 seguem
abertos. Sem UI diária, áudio ou efeito físico. Provas, falhas intermediárias,
owners, regressão e critérios:
`resultados_testes/compreensao_fala_acao_20261017/emissao_suporte_autoria/RELATORIO.md`.

## 26. C5 — consumo das fontes na revisão de cada proposição, 17/10

Raiz reproduzida em 16 ciclos: declaração e conteúdo individual chegavam ao
plano, mas juiz não os consumia; publicava a mesma conclusão com fonte integral,
irrelevante, parcial ou ausente. Estado preservado e geração controlada afastam
perda de transporte e defeito específico de domínio/rota. Mesmo contrato
compartilhado de autoria/revisão, sem criar outra correção por frase.

| Contrato | Responsável | Critério |
| --- | --- | --- |
| Revisão vinculada à emissão | `plano_turno` + novo `revisao_suporte_autoria` | Tipo/turno/consulta/fala, fonte individual e conteúdo conferidos; guardas anteriores preservadas. |
| Alcance da publicação | Mesmo juiz compartilhado | Trecho integral só como citação atribuída; apoio não conferido fica limitado. Semântica/prova/autoridade sempre falsas. |
| Presença de URL | `orquestrador_turno_runtime` | URL preservada não marcada ausente; presença não aprova apoio. Refinamento reproduzido separadamente. |

Correspondência parcial/paráfrase não ganha implicação; fonte oposta não recebe
diagnóstico automático de contradição. Fonte interna/agregada, duplicada ou
vencida não certifica fato. Snapshot conserva conteúdo lido; proposta da IA e
confiança global não são prova. Sem fontes/referências ou obrigação factual,
conversa comum é preservada sem confirmação externa. Reparo/mescla não herda
suporte de outro texto. Grafo e verificadores offline continuam offline.

Três arquivos de produção, dois testes existentes ajustados e um novo. Replays
isolados repetem 16 REDs de falta de revisão e 16 de presença, sem trocar arquivos
da worktree. Focal final:37 aprovados; Qwen real normal/rápido, dois HTTP200,
ambos omitiram referências e a publicação foi limitada. Fontes sintéticas e
porta corporal isolada na fixture: não é prova de consulta web, efeito físico
ou implicação semântica. Contexto diário completo excedeu 4.096 tokens em
ensaio preservado; raiz de tamanho de contexto não corrigida aqui.

Regressão:1.080 aprovados/13 skips/8 subtestes, 32 módulos, um RED prévio de
enum do catálogo reproduzido também na base; zero erros. Grupos sobrepostos.
Outros17 controles de produção estáveis. Nenhum commit, troca de modelo/voz,
main diário, UI ou áudio. C5/C7 gerais permanecem abertos. Próxima fronteira:
justificativa auditável das relações não literais, suporte individual de
reparos/mesclas e fontes alternativas/novas, sem autoaprovação por modelo.
Provas, contratos, limites e falhas intermediárias:
`resultados_testes/compreensao_fala_acao_20261017/revisao_suporte_fontes/RELATORIO.md`.

## 27. C5 — apoio de paráfrase por derivação estrutural, 17/10

Limite demonstrado: fontes e autoria íntegras, mas toda redação não idêntica
recebia pendência. A restrição literal era proteção útil; faltava um contrato
adicional de transformação conferível, independente da proposta.12 REDs antes
do candidato,41 controles aprovados. Não é prova da raiz de toda prosa livre.

Mesmo owner de revisão confere duas realizações integrais de atribuição:
`O valor do atributo «A» de «E» é «V».` e
`«V» é o valor do atributo «A» de «E».` Termos são opacos e devem coincidir
literalmente em seus papéis. Nenhum nome/domínio ou lista de sinônimos serve
de prova; fonte com condição, negação ou texto adicional permanece pendente.

| Contrato | Responsável | Critério |
| --- | --- | --- |
| Derivação independente | `revisao_suporte_autoria` | Leitura integral das duas formas, três papéis, intervalos e hashes recalculados da fonte atual; certificado proposto não vale. |
| Publicação atribuída | Mesmo revisor/juiz de `plano_turno` | Identificar paráfrase, preservar ordem com citações e excluir conclusão adicional; sem confirmação externa/autoridade. |
| Proveniência e registro | Owners anteriores preservados | Fonte individual admitida/atual; proposta pendente não ganha fonte canônica ou vínculo com texto substituto. |

Uma fonte literal e outra estrutural podem sustentar a mesma unidade somente
quando ambas são conferidas. Semântica livre/prova geral/autoridade permanecem
falsas. Snapshot registra apenas apoio estrutural delimitado. Revalidação não
aceita prova antiga para conteúdo alterado. Grafo e contratos offline preservados.

Um arquivo de produção alterado e um teste novo;19 outros controles de produção
e teste anterior idênticos.16 ciclos instalados:quatro positivos e12 negativos,
dois domínios/duas rotas; testes puros incluem terceiro domínio e duas direções.
Replay do revisor anterior repete14 REDs após controles acrescentados. Qwen real:
dois HTTP200, mas omitiu referências e foi limitado. Não há prova positiva de
paráfrase gerada pelo Qwen e admitida. Fontes sintéticas, contexto corporal
isolado só na fixture; sem consulta web/efeito físico ou main diário.

92 focados aprovados/2 skips em dois módulos, incluindo57 do novo módulo com
as inferências reais. Regressão33 módulos:1.135 aprovados/15 skips/8 subtestes,
um RED prévio de enum do catálogo e zero erros. Grupos sobrepostos. Sem commit,
troca de modelo/voz ou remendo no prompt. C5/C7 gerais abertos; prosa livre,
sinonímia, escopo, fontes novas e suporte de reparos/mesclas requerem provas.
Evidências, owners, contrato exato e limites:
`resultados_testes/compreensao_fala_acao_20261017/parafrases_estruturais/RELATORIO.md`.

## 28. C5 — inventário e decisão explícita de referência, 18/10

Raiz demonstrada na negociação:URLs no prompt, mas schema/validator aceitam
`fontes:[]` silenciosamente e não enumeram IDs citáveis. Bruto HTTP já omitia
referências, afastando perda no parser/transporte.24 REDs antes de produção;
replay focado repete20. Mesmo pedido/modelo/temperatura na base:dois HTTP200
sem referências; três repetições do candidato:ambas as rotas referenciam.
Temperatura0,7/sem seed:ensaio observado, sem diagnosticar motivos internos ou
prometer que toda geração citará corretamente.

| Contrato | Responsável | Critério |
| --- | --- | --- |
| Inventário exposto da ocorrência | `contexto_resposta_ia` | Mesmo seletor do bloco, sem catalogar fontes ocultas/turno alheio/projeção fechada. |
| Referência ou ausência explícita | `suporte_autoria` | `autoria_referenciada_v3`:IDs enumerados ou `sem_fonte` declarada; nunca preencher por proximidade ou transformar indicação em prova. |
| Recuperação conserva obrigação | `processamento_resposta_ia` + negociador compartilhado | Material/catálogo do plano atual também nas reescritas; IDs alheios recusados e fonte global não reabilita principal ausente. |
| Fala transformada conserva limite | `revisao_suporte_autoria` | Sem vínculo, limitar conversa que exige fonte; não usar suporte antigo como prova nem substituir owner operacional. |

Refinamentos separados:reparo voltava ao formato anterior (replay só do
processamento:8 REDs/8 positivos); fala alterada perdia vínculo e obrigação
(replay só do revisor:1 RED/2 controles). Não são causas da omissão inicial.
Causa da transformação e apoio individual de reparos/mesclas continuam abertos.

180 focados aprovados/8 skips, cinco módulos, incluindo34 testes novos e duas
inferências reais. Fechamento:normal publica citação atribuída, rápida limita
fala sem vínculo; nenhuma referência aprova implicação/verdade/autoridade.
Fontes sintéticas, contexto corporal isolado na fixture; sem consulta web,
main diário, UI, áudio ou efeito físico. Quatro arquivos de produção, dois
testes vizinhos ajustados para recusa antecipada,16 controles de produção e
dois testes congelados preservados. Nenhum commit ou troca de modelo/voz.

Regressão:1.167 aprovados/17 skips/8 subtestes,34 módulos, um RED prévio do enum
corporal também reproduzido na base e zero erros. Hashes no selo; grupos
sobrepostos. C5/C7 gerais abertos. Portas sem inventário, URLs fora do limite, prosa
livre, semântica individual de reescritas/fontes novas exigem provas próprias.
Contratos, responsáveis, falhas intermediárias e critérios:
`resultados_testes/compreensao_fala_acao_20261017/referencias_autoria/RELATORIO.md`.

## 29. C5 — preservação da fala na higiene compartilhada, 18/10

Raiz da transformação demonstrada: a higiene interpretava qualquer letra final
em fala longa como fragmento interrompido. O HTTP e a projeção autoral traziam
`5 V.` completo; o callback compartilhado apagava `V.` antes da revisão. A
declaração permanecia íntegra e o revisor recusava corretamente o vínculo.
Mesma causa nas duas rotas e em IoT, arquivo e nota. Não é a omissão de fontes
da seção anterior nem autoriza remover sua proteção de revisão.

| Contrato | Responsável | Critério |
| --- | --- | --- |
| Preservar conteúdo ambíguo | `personalidade/higiene_fala` | Não presumir truncamento por uma letra/contagem de palavras; unidades, classes e iniciais preservadas sem listas. |
| Reutilizar a regra comum | Limpeza conversacional, operacional e decoder | Mesma preservação em todos os chamadores; sem remendo em rota/domínio. |
| Manter identidade e limite | Autoria e revisão, preservadas | Declaração não é reancorada; retirada de metadado continua perdendo vínculo e recebendo limite. Fonte proposta não aprova fato ou execução. |

41 REDs antes do patch; replay carregando só a higiene congelada repete os
mesmos41. Candidato altera um arquivo de produção;22 outros arquivos de
produção e seis testes congelados idênticos. Teste legado corrigido porque
presumia interrupção sem evidência. Caudas operacionais explícitas continuam
sendo retiradas.12 ciclos instalados: seis positivos/seis negativos, três
domínios/duas rotas.62 focados aprovados/2 skips; novo módulo com Qwen real:
43 aprovados, dois HTTP200/stop, incluindo os mesmos41 casos. Grupos sobrepostos.

Rápida preserva `5 V.` e publica atribuição à fonte. Normal preserva autoria e
publica trecho de `disco C.`; afirmação adicional sem fonte é excluída. Modelo
local existente `qwen3:4b-instruct`, sem alteração. Flags de semântica geral,
verdade externa, implicação e autoridade falsas. Regressão em37 módulos:1.229
aprovados/19 skips/8 subtestes e um RED prévio do catálogo reproduzido na base;
zero erros. Nenhum commit. Fontes/memória sintéticas/isoladas, áudio/efeitos
bloqueados; porta corporal isolada só nas inferências, sem main diário/UI ou
efeito físico. Não encerra C5/C7 gerais nem apoio livre/reparos/mesclas/fontes
novas. Relatório, responsáveis, critérios, diff e selo:
`resultados_testes/compreensao_fala_acao_20261018/integridade_fala/RELATORIO.md`.

Fechamento adicional:64 focados aprovados, duas inferências reais incluídas.
Três ensaios/seis HTTP200/stop preservam toda autoria. As publicações positivas
acima são do primeiro ensaio; no último, ausência declarada na rápida e apoio
pendente/ausente na normal mantêm limite. Não há garantia de citação pelo modelo.
Um teste intermediário exigia cópia literal em toda geração e falhou; premissa
corrigida sem alterar produção/revisor. RED e saídas conservados no relatório.

## 30. C5 — declaração própria das reescritas e partes aceitas, 18/10

Raiz demonstrada: o reparo já recebia contrato de autoria, mas a preparação,
após aceitá-lo, guardava apenas fala/comandos e descartava sua declaração.
A mescla perdia a relação entre as duas emissões. Oito REDs na composição
instalada, repetidos pelo replay dos contratos congelados. Não remover a
proteção que recusa suporte da principal para um texto diferente.

| Contrato | Responsável | Critério |
| --- | --- | --- |
| Captura e montagem literais | `suporte_autoria` | Partes da mesma ocorrência/pergunta, cobertura e ordem integrais; captura não prova fonte ou sucesso. |
| Seleção após aceitação | `processamento_resposta_ia` | Levar apenas declarações das emissões aceitas, sem selecionar por semelhança ou reancorar a principal. |
| Transporte e publicação | `ContratoRespostaTurno`, runtime da resposta e composição/orquestrador | Objeto tipado e fala íntegra; writer atômico confere turno, pergunta, fala e hash da emissão principal. Cinco negativos instalados preservam o estado; positivo alcança o mesmo writer. |
| Revisão independente | `revisao_suporte_autoria` | Ler fontes individuais atuais para a declaração própria; fonte interna/alheia/vencida, parcial ou prosa livre não ganham prova. |

Sete arquivos de produção na cadeia, um teste novo;19 outros controles de
produção e oito testes congelados idênticos. Teste vizinho corrigido: quatro
reparos de formato válido citavam `alegacao:inexistente` e eram publicados;
agora sua declaração chega ao revisor e exige recusa. Principal/autoridade
originais conservadas, flags de prova/fato externo/execução falsas, sem commit.

121 focados aprovados/2 skips/4 xfails; módulo novo com dois reparos Qwen reais:
27 aprovados/4 xfails. Regressão em40 módulos:1.298 aprovados/19 skips/4 xfails,
8 subtestes, um RED prévio do catálogo reproduzido na base e zero erros.
Grupos sobrepostos. No fechamento real, IoT publica citação conferida e arquivo
mantém paráfrase pendente. Ensaio anterior conservado com timeout de arquivo.
Fontes sintéticas, portas externas/memória/áudio/efeitos isolados; corpo fora
do prompt só nas inferências. Sem main diário, UI ou efeito físico.

Os quatro xfails estritos mantêm outro RED, também na base: a revisão retira
a reação social sem fonte, e a guarda de completude limita a entrega da mescla,
embora agora confira o suporte do trecho factual. Não é GREEN de entrega
completa. Próxima fronteira: evidência do ato discursivo fornecida por seu owner,
distinta de prova factual externa. Não aprovar reação por `sem_fonte` ou tom,
nem enfraquecer completude. C5/C7 gerais e semântica livre continuam abertos.
Owners, artefatos intermediários, contratos e limites:
`resultados_testes/compreensao_fala_acao_20261018/autoria_reescritas/RELATORIO.md`.

Guarda adicional no mesmo contrato: novo planejamento sem reescrita descarta
a montagem da emissão anterior. RED instalado de renovação antes da guarda;
GREEN focado e regressão acima já incluem essa validação do ciclo de vida.

## 31. C5 — evidência independente do ato social na mescla, 18/10

Raiz demonstrada: autoria própria das partes chega íntegra, fonte factual
literal é conferida, mas revisão elimina reconhecimento social por falta de
fonte externa. Completude então limita a entrega. Os quatro xfails históricos
da seção 30 agora passam sem xfail; os registros anteriores ficam preservados.

| Contrato | Responsável | Critério |
| --- | --- | --- |
| Conferir o ato integral no relato atual | `validacao_contrato_fala` | Plano canônico, turno/âncora/papéis atuais; gramática fechada de acolhimento/retomada, sem fato ou causa adicional. |
| Separar ato de apoio factual | `revisao_suporte_autoria` | Ato conferido e fonte factual própria mantêm ordem e atribuição; declaração da IA não é prova; fato sem apoio continua excluído. |
| Preservar segurança e identidade | Autoria, composição e completude existentes | Sem empréstimo de suporte, aprovação de estado real, autoridade, execução ou remoção de guarda. |

Dois arquivos de produção alterados;24 outros e nove testes congelados
idênticos.14 REDs causais antes do candidato e os mesmos14 no replay da base.
87 focados aprovados/2 skips; regressão em41 módulos:1.340 aprovados/21 skips,
8 subtestes, um RED prévio do catálogo também na base, zero erros. Grupos
sobrepostos. Erros intermediários de fixture preservados e corrigidos.

Positivo na composição instalada com geração controlada em dois domínios e
duas rotas. Qwen real ainda não produziu ato elegível: ensaio `bem` teve
36 aprovados/quatro falhas positivas; ensaio `feliz`,34/seis. Quatro HTTP200/stop
totais, sem alteração de modelo. Primeiro excede reparo parcial; segundo
seleciona reescrita total por dois bloqueadores, uma fronteira anterior.
Não ampliar a gramática nem aceitar avaliação do modelo como prova.

Próxima investigação: autoria do ato solicitado e seleção da rota de reparo.
Conferência atual é limitada ao primeiro relato pessoal direto seguido de
perguntas, sem execução. Não fecha C5/C7 gerais, semântica livre ou geração
positiva do Qwen. Fontes/memória/portas isoladas, sem main diário/UI/áudio/efeito
físico, commit ou troca de configuração. Evidências, owners, critérios e selo:
`resultados_testes/compreensao_fala_acao_20261018/ato_social/RELATORIO.md`.

## 32. C5 — seleção do reparo e escopo autoral preservado, 18/10

Dois mecanismos separados foram demonstrados. A qualidade duplicava o
diagnóstico do contrato de fala para o mesmo ato ausente, escolhendo reparo
total em alguns estados. No parcial, wrappers reinjetavam tema/corpo e o
schema negociava prosa livre; a composição aceitava tom como reconhecimento,
embora a revisão integral posterior recusasse a unidade. Não é nova perda
de fonte nem falha da conferência independente da seção 31.

| Contrato | Responsável | Critério |
| --- | --- | --- |
| Um owner por ato ausente | `qualidade_comunicacao` | Cinco estados seguem a decisão canônica; legado sem contrato e bloqueadores distintos preservados. |
| Opções derivadas da gramática existente | `validacao_contrato_fala` | Plano/relato atual conferível, sem ampliar por frase do Qwen ou certificar estado real. |
| Pacote fechado e codec do owner | Qualidade e `processamento_resposta_ia` | Parcial sem reinjeção de tema/corpo; total mantém fontes; composição confere unidade inteira. |
| Restrição literal atravessa autoria | `suporte_autoria` | Uma unidade escolhida do contrato base; recusa texto extra, comando, fonte alheia e certificado da IA. |

Sete REDs iniciais; fechar somente contexto deixou seis falhas reais e
demonstrou a necessidade de alinhar geração/conferência. Seis REDs adicionais
antes do contrato limitado. Replay da base repete nove falhas causais na
seleção/envio/composição. Artefatos e falha intermediária de formato da folha
controlada preservados. Não foi ampliada a gramática social anterior.

Quatro arquivos de produção,22 outros e dez testes congelados iguais.
121 focados aprovados/2 skips. Qwen real:57 aprovados no ensaio `feliz`,74
no histórico `bem`; oito HTTP200/stop positivos, arquivo/normal e IoT/rápida
em duas instâncias cada. Reação conferida e citação factual entregues sem
efeito. Regressão em42 módulos:1.374 aprovados/21 skips/8 subtestes, um RED
prévio do catálogo também na base, zero erros. Grupos sobrepostos.

Positivo real pendente na seção 31 agora demonstrado nesse recorte limitado;
registros antigos não são apagados. Modelo/voz/configuração preservados,
sem commit/main diário/UI/áudio/efeito físico. C5/C7 gerais e compreensão
social livre continuam abertos. Owners, critérios, limites, diff e selo:
`resultados_testes/compreensao_fala_acao_20261018/escopo_reparo/RELATORIO.md`.

## 33. C5 — conferência de saudação e recepção de agradecimento, 19/10

Raiz demonstrada: atos já reconhecidos no contrato chegam com autoria
preservada, mas o conferidor só conhece acolhimento de estado pessoal e os
retira por ausência de fonte externa. O vínculo também comparava a caixa
normalizada do segmento diretamente com o texto original do usuário.

| Contrato | Responsável | Critério |
| --- | --- | --- |
| Fonte literal dos atos já decididos | `fontes_textuais_dos_segmentos`, reutilizado | Intervalos verificáveis; somente caixa/espaços demonstráveis, sem nova segmentação ou autoridade. |
| Conferência integral e papéis do ato | `validacao_contrato_fala` | Saudação recíproca, recepção de agradecimento e acolhimento com fonte atual; nenhum fato, causa, execução ou estado oculto certificado. |
| Apoio factual continua individual | Revisão/autoria existentes | Um ato não sustenta fato adjacente; referência inválida não é removida para aproveitar a reação. |

Um arquivo de produção alterado;26 outros e 12 testes congelados iguais.
19 REDs causais antes do candidato;25 no replay com os positivos adicionais.
176 focados aprovados/4 skips;12 positivos na composição instalada controlada,
arquivo/IoT e normal/rápida. Regressão em43 módulos:1.429 aprovados/23 skips,
8 subtestes, um RED do catálogo (`estado_owner`) também no replay da base,
zero erros. Grupos sobrepostos; não representam estabilidade global da árvore.

Ensaio livre do Qwen continua RED:47 aprovados/quatro falhas, dois HTTP200/stop.
Arquivo omite ato/referência e acrescenta prosa; IoT mescla saudação e fato
sem referência numa unidade. Recusa preservada, sem cortar texto ou usar
proposta como prova. Não há positivo real de entrega livre desses novos atos.

Não amplia para todo ato/ordem: reconhecimento após saudação ou pergunta
seguida de relato possui fronteiras anteriores registradas separadamente.
Próxima investigação: vínculo entre unidade autoral e ato realizado, sem
aceitar classificação da IA como certificado. Mantidos C5/C7 gerais abertos;
sem main diário/UI/áudio/efeito físico, commit ou troca de modelo/configuração.
Interrupção/retomada, regressão intermediária corrigida, owners, critérios:
`resultados_testes/compreensao_fala_acao_20261018/atos_discursivos/RELATORIO.md`.

## 34. C5 — alvo discursivo na negociação de cada unidade, 19/10

Raiz demonstrada: plano exigia saudação/pergunta, mas projeção e codec só
negociavam texto/fontes. Omissão do ato e mistura com fato eram aceitas
deterministicamente antes da revisão. Quatro REDs do contrato e oito no
payload instalado; não é prova sobre raciocínio interno do Qwen.

| Contrato | Responsável | Critério |
| --- | --- | --- |
| Inventário da ocorrência atual | `validacao_contrato_fala` | IDs de turno/entrada/intervalo, só atos e realizações já conferíveis; nenhum ID da IA vira autoridade. |
| Plano chega ao envio | Composição/contexto da IA | Mesma entrada/ocorrência, pacote fechado preservado; primeiro recorte com saudação e perguntas não operacionais e fontes expostas. |
| Unidade declara alvo e suporte | `suporte_autoria` | Cobertura ordenada e unidade social separada; referência ou ausência mantida sem inventar apoio. |
| Reescrita mantém contrato próprio | `processamento_resposta_ia` | Mesmos alvos, nova declaração e inventário de fontes preservado. |
| Alvo, ato e apoio são julgados separadamente | `revisao_suporte_autoria` | Reconstruir inventário atual; trocar/omitir alvo é recusado. Localizar a pergunta não comprova pertinência nem apoio factual. |

Seis arquivos de produção;21 outros e12 testes congelados iguais. Um teste
novo com36 casos, fixture anterior adaptada aos IDs do schema. Replay repete
12 REDs iniciais; só o revisor congelado repete quatro e só o preparador antigo
repete a regressão de contrato no reparo total instalado.253 focados/6 skips.
44 módulos:1.473 aprovados/23 skips/8 subtestes e um RED prévio do catálogo,
zero erros. Prova instalada adicional de reparo passou após esse amplo e está
no fechamento focado. Grupos sobrepostos, sem commit/configuração/modelo/voz.

Quatro inferências reais HTTP200/stop vinculam unidades aos atos atuais e
conservam saudação conferida; não concluem a entrega factual. Arquivo declara
ausência de referência e IoT propõe paráfrase sem apoio conferido. Testes
positivos antigos de fonte/entrega continuam RED no ensaio, preservados sem
xfail. O teste específico de vínculo passa, sem tomar IDs ou fontes por prova.

Não fecha pertinência semântica geral, todos os atos/rotas, C5/C7, main diário,
voz ou efeito físico. Próxima fronteira factual conhecida: apoio à redação e
pertinência à pergunta, distinguindo omissão de fonte de paráfrase não conferida.
Owners, critérios, limites, resultados intermediários e selo:
`resultados_testes/compreensao_fala_acao_20261019/unidades_por_ato/RELATORIO.md`.

## 35. C5 — trecho individual integral na projeção, 19/10

Raiz distinta das omissões e paráfrases com fontes curtas: fundamentação
preserva até 850 caracteres, mas a projeção cortava cada fonte em 300,
eliminando ressalvas. A revisão corretamente exige o snapshot inteiro.
Primeira divergência na projeção, sem necessidade de afrouxar a revisão.

Owner `contexto_resposta_ia`: expor integralmente fontes individuais dentro
do limite canônico, sem transformar conteúdo excessivo/malformado em prefixo
aparentemente completo. Até três fontes; resumo não vira fonte individual.
Critérios: 299/300/301/480/500/501/850, principal/reparo, validade, pacote
fechado, exposição e limite autoral de 500 preservados. Só esse arquivo de
produção pertence ao candidato; `candidato_projecao.diff` separado.

Replay só desse owner, mantendo o candidato da seção 36:15 REDs causais.
Composição controlada valida oito fontes longas em arquivo/IoT e normal/
rápido. Duas inferências reais rápidas recebem os trechos de 386/389
caracteres inteiros, incluindo ressalvas; a saída ainda reformula ou usa
prefixo e permanece pendente. Receber conteúdo não comprova sua redação.

## 36. C5 — instrução autoral permanece no mesmo par atual, 19/10

Outra raiz: o wrapper de alvos da seção 34 criava um novo system e deslocava
contrato/fontes/regras de autoria para a mensagem descartável. A preparação
preserva corretamente só o system adjacente ao usuário e exclui históricos.
Fonte inteira no contexto de origem não provava sua chegada ao transporte.

Owner `suporte_autoria`: estender a mesma instrução atual, sem ampliar a
compactação para sistemas históricos. Inventário exposto só precisa de ID,
tipo e texto; ocorrência, âncoras e flags continuam no host, e opções no
schema. Critérios: principal/reparo, normal/rápido, fonte/contrato/alvos juntos,
consulta/schema conservados e instrução histórica ausente.
Só esse arquivo de produção pertence ao candidato; `candidato_atomico.diff`.

Quatro REDs antes do candidato. Replay só desse owner, projeção atual:
oito REDs e quatro positivos rápidos. Correção de A isoladamente deixou
quatro falhas normais, preservadas e diagnosticadas antes de corrigir B.
Primeiro Qwen com pacote íntegro excedeu contexto (4157/4096); projeção dos
metadados redundantes reduzida sem cortar evidência ou mudar configuração.
Ensaio seguinte HTTP200,4016 tokens de entrada normal. Orçamento geral de
contextos maiores continua fora da garantia deste recorte.

Fechamento compartilhado das provas, sem unificar as raízes:321 focados/
10 skips;47 módulos:1517 aprovados/23 skips/8 subtestes, um RED conhecido
do catálogo e zero erros. Dois testes opcionais novos de entrada real vieram
depois do amplo e passaram no ensaio Qwen e no foco final. Grupos sobrepostos.
Quatro principais HTTP200/stop finais:uma entrega completa IoT, arquivo
livre ainda paráfrase pendente, dois trechos longos recebidos mas saídas sem
apoio. Expectativa factual anterior continua RED; sem xfail/remendo por frase.
Dois arquivos de produção, um teste existente e dois novos;15 controles
congelados iguais. Sem commit/modelo/configuração/voz/main diário/efeito físico.

Permanece aberta a derivação de apoio e pertinência da redação livre; fontes,
alvos ou avaliações da IA não são provas. Owners, critérios, replays, diffs,
falhas intermediárias e selo:
`resultados_testes/compreensao_fala_acao_20261019/integridade_trechos/RELATORIO.md`.

## 37. C5 — obrigação de apoio direcional e pertinência, estudo de 19/10

A recusa das paráfrases livres permanece uma limitação conhecida. O estudo
não demonstrou nova raiz defeituosa de produção que justificasse liberá-las.
Falsificou dois substitutos de derivação: limiar de similaridade e aprovação
por Qwen. Produção/configuração preservadas;25 arquivos congelados idênticos.

Painel sintético curado de24 casos antes da inferência, gold oculto do modelo:
10 apoiados textualmente, dois impertinentes. Encoder ONNX já instalado, sem
treino:papéis trocados atingem0,99347, acima da paráfrase histórica0,94872.
Dois pares com apoio assimétrico têm cosseno exatamente igual na ida/volta;
nenhum limiar desse escalar distingue as direções. Parecer Qwen pelo serviço
instalado, contexto fechado, quatro HTTP200/stop:19/24 julgamentos de apoio
iguais à curadoria, duas aprovações indevidas, três recusas indevidas e três
erros de pertinência. Capacidade virou execução e disjunção virou fato.
Não corrigir booleanos a partir da justificativa para melhorar o resultado.

Revisor atual:duas literais, uma derivação estrutural e21 pendentes. Nenhum
dos14 casos sem apoio curado aprovado, mesmo com autoaprovação inventada no
contexto. Sete apoiados seguem sem derivação; citação literal de outro assunto
mantém a fronteira de pertinência aberta.154 testes aprovados/4 skips em
quatro módulos;28 novos de protocolo/controles. Sem alteração de produção,
treino/modelo/download/voz/execução; não repetida a regressão ampla.

Contrato a implementar só com premissas conferíveis:fonte→proposição,
papéis/polaridade/modalidade/tempo/condições/ressalvas/atribuição preservados;
apoio e pertinência independentes. Snapshot da fonte, hash da unidade,
alvo atual e direção/escopo precisam acompanhar uma derivação cujos passos
sejam conferidos pelo owner. Parecer/estrutura da IA permanecem propostas.

| Responsável | Obrigação | Critério |
| --- | --- | --- |
| Fundamentação/proveniência | Premissas individuais atuais e imutáveis | Fonte ambígua/vencida/alterada invalida derivação. |
| Autoria | Propor unidade, fonte e alvo | Sem autoconferir significado ou criar observação. |
| Revisão de suporte | Relação direcional e cobertura do escopo | Regra e premissas conferidas por passo; desconhecido continua não demonstrado. |
| Contrato de fala/revisão | Pertinência à pergunta | Alvo correto ou literalidade não bastam. |
| Writer/composição | Preservar emissão e julgamento próprios | Nova redação/fonte/pergunta exige nova conferência. |

Próxima fronteira:obter premissas de significado independentemente da proposta
do modelo, reutilizando dados estruturados dos owners e as derivações já
conferíveis. Uma árvore sintática/lógica sugerida pela IA também exige prova
de fidelidade ao texto de origem. Não adicionar regex para a frase do disco
nem instalar juiz probabilístico como confirmação. Futuros candidatos precisam
deste painel congelado, reserva independente e composição real, incluindo
Qwen normal/rápido/principal/reparo. Não há positivo novo de entrega livre,
main diário, áudio ou efeito físico;C5/C7 gerais abertos.
Pesquisa primária, protocolo, fontes, responsáveis, resultados e selo:
`resultados_testes/compreensao_fala_acao_20261019/apoio_direcional/RELATORIO.md`.

## 38. C5 — premissa de escopo preservada no histórico, 19/10

Na busca de premissas independentes da IA foi demonstrada uma perda concreta:
`ResultadoAcao` já possui `confirmacao_oferecida`, mas o snapshot da própria
fala descartava esse campo. Escopos diferentes com o mesmo booleano passavam
a representar a mesma confirmação; a realização histórica não os distinguia.
Primeira divergência na captura do receipt, não na interpretação do Qwen.
Essa raiz é independente do RED de enumeração do catálogo.

Contrato geral: confirmação histórica exige conservar o alcance declarado
na ocorrência, junto de execução/confirmação/identidade. Fonte legada sem
alcance permanece desconhecida; fonte com `indisponivel` não fundamenta
afirmação de efeito pelo booleano. Não inferir alcance por status, descrição
textual, catálogo atual ou proposta da IA; não reescrever receipts anteriores.

| Responsável | Obrigação | Critério |
| --- | --- | --- |
| Executor/`ResultadoAcao`, preservados | Publicar confirmação e alcance do receipt | Premissa existe antes da captura em quatro domínios. |
| Registro semântico | Conservar escopo na ocorrência imutável | Escopos não colapsam; alteração sob mesmo ID recusada. |
| Recuperação/contrato, preservados | Transportar a premissa da fala selecionada | Turno intermediário não empresta último receipt; normal/rápido conservam a fonte. |
| Explicação histórica | Qualificar confirmação pelo escopo capturado | Legado sem backfill, indisponível sem promoção, forma inválida recusada; três valores e idempotência preservados. |
| Composição/writer, preservados | Entregar somente a realização admitida | Uma publicação, nenhuma nova ação, prosa sem cobertura ajustada pelo owner. |

Dois arquivos de produção: `registro_semantico.py` e
`explicacao_fala_historica.py`. Um teste existente ampliado e um novo com32
casos;dez provas instaladas de escopo em música, IoT/playlist parcial,
arquivo/e-mail parcial e receipts sintéticos de firmware/owner. USB/TCP
proibidos.30 controles congelados iguais;configuração/modelo/voz/execução
preservados, nenhum commit. Replays em memória isolam captura e realização
anteriores e reproduzem as perdas sem trocar arquivos da worktree.

Qwen real: música e firmware com HTTP200/stop recebem o alcance no transporte
e terminam com realização qualificada do owner. Redação livre não foi
aprovada como prova. Outros cenários mostram HTTP400 de contexto e saída
truncada, com conclusão segura do owner;sem alegar sucesso da inferência ou
atribuir esses erros à perda do campo. Uma expectativa de teste da variante
controlada foi corrigida para exigir realização integral permitida na fonte
atual, preservando a asserção exata no modo controlado. Artefato real e XML
inicial preservados;onze asserções reaplicadas sem nova geração.

Não resolve apoio/pertinência de prosa livre, fidelidade de representações
semânticas, orçamento/negociação de contexto histórico, C5/C7 gerais,
main diário, reinício/áudio ou efeito físico. A premissa é o alcance
registrado pelo executor; não uma observação adicional de mundo externo.
Contagens focadas/amplas finais, REDs, replays, owners, critérios e selo:
`resultados_testes/compreensao_fala_acao_20261019/premissas_confirmacao/RELATORIO.md`.

Fechamento deste recorte:236 focados/2 skips;49 módulos:1587 aprovados,
25 skips/8 subtestes, uma falha conhecida do catálogo e zero erros. Último
controle de escopo indisponível teve RED próprio antes do ajuste e integra
ambos os fechamentos finais. Sem encerrar as fronteiras gerais acima.

## 39. C5 — negociar na geração o limite histórico que o owner já confere

19/10/2026. Mesma base ca592a9609dd1865b63b22c714f8d3e802fa2a5c,
worktree preservada. Raiz distinta da captura de escopo: fonte e realização
do owner já eram válidas, mas o preparador negociava texto livre, referências
e comandos na consulta histórica. A revisão corrigia depois. O codec anterior
aceita causa/fonte/comando inventados mesmo em contexto mínimo; não depende
da perda de receipt ou de excesso de contexto. Não se afirma acesso ao
raciocínio interno do Qwen.

Contrato: quando a realização histórica já é conferível e cabe numa unidade
autoral existente, o envio negocia exatamente essa realização e comandos
vazios. Mesma ocorrência, utterance original, contrato e plano atuais;
projeção efêmera, sem transformar fonte ou escolha da IA em prova nova.

| Responsável | Obrigação | Critério de validação |
| --- | --- | --- |
| Explicação histórica | Reutilizar o próprio avaliador para obter realização válida | Codec aceita somente a realização; decisão e revisão usam mesmo mecanismo. |
| Preparador compartilhado | Transportar limite no envio normal/rápido da consulta atual | Dez provas na composição registrada; identidade, utterance e autoridade adulteradas recusam projeção. |
| Autoria/codec existentes, preservados | Manter declaração de suporte e restrição literal | Texto/fonte/comando/campo inventados recusados mesmo se provedor ignorar schema. |
| Revisão/publicação existentes, preservadas | Revalidar fonte depois da geração e concluir uma vez | Fonte vencida não recebe validade do codec; sucesso parcial conserva falha e não executa de novo. |

Somente `contexto_resposta_ia.py` e `explicacao_fala_historica.py` em produção.
28 controles novos e ampliação do fixture instalado. RED antes do candidato;
replay em memória do preparador congelado volta a18 falhas/dez controles.
Nenhuma restauração de arquivo ou commit. Sete controles de produção e hash
da configuração persistida preservados.

Qwen real: quatro HTTP200/stop, música, composto IoT/playlist e receipts
sintéticos de firmware/owner. Bruto exatamente igual ao enum do owner,
comandos vazios e declaração de suporte, antes da revisão final. Onze
asserções da composição e quatro específicas do transporte reaplicadas ao
artefato (15 aprovadas, zero novas inferências). Arquivo/e-mail conclui no
pré-fluxo. Não se certifica main diário, áudio, movimento ou semântica livre.

Realizações maiores que500 caracteres continuam na revisão anterior, sem
corte nem ampliação de limites. Próxima fronteira: autoria integral de
realizações longas/por ato com premissas preservadas. Paráfrases/pertinência
gerais e C5/C7 completos continuam abertos. Chamada interna de resumo diário
com rótulo principal e bloqueio de orçamento permanece root separada.

Regressão de51 módulos:1658 aprovados,25 skips,8 subtestes e uma falha
conhecida do catálogo, zero erros. Evidências, XMLs intermediários preservados,
critérios e fechamento focado final:
`resultados_testes/compreensao_fala_acao_20261019/negociacao_historica/RELATORIO.md`.

Foco final:218 aprovados/nove skips/zero erros em oito módulos. Quatro skips
são provas HTTP opcionais conferidas no artefato real preservado;nenhuma
inferência extra. O selo registra hashes e resultados intermediários.

## 40. C5 — realização histórica integral em várias unidades de suporte

19/10/2026. Base ca592a9609dd1865b63b22c714f8d3e802fa2a5c, worktree
preservada. Continuação autorizada do limite da seção39: o owner produz
realização válida acima de500 e a captura já aceita várias unidades com
cobertura integral. A primeira restrição é a negociação de `fala.enum`
como unidade única (`maxItems=1`). A guarda de500 era defensiva;foi
substituída por verificação de representabilidade integral, depois de
corrigido o contrato compartilhado. Sem aumentar limites.

Contrato: repartir somente transporte literal em até8 unidades de500
caracteres, fala até4000. Junção deve ser igual ao texto do owner. Schema
oferece partes e o validator exige a sequência completa de uma realização;
não admite omissão, reordenação, repetição, mistura entre opções ou adição.
Divisão não prova fronteiras semânticas, apoio, autorização ou efeito.

| Responsável | Obrigação | Critério |
| --- | --- | --- |
| Autoria compartilhada | Preservar a realização finita em partes literais | Reconstituição integral;limites, âncoras inequívocas e cobertura da captura existente. |
| Owner histórico | Fechar envio somente se fonte válida e realização integralmente representável | Cinco domínios, dois owners por ato, fonte vencida e texto acima de4000. |
| Preparador/codec/serviço, preservados | Transportar schema e conferir proposta antes de sucesso | Normal/rápido/compactação;prosa livre continua limitada;controle negativo de causa/fonte/comando. |
| Revisão/publicação, preservadas | Revalidar fonte e concluir sem novos efeitos | Uma publicação com oito receipts e parcialidade;declaração não ganha prova semântica ou autoridade. |

Produção somente `suporte_autoria.py` e `explicacao_fala_historica.py`.
Oito controles de produção e configuração idênticos;sem commit, troca de
modelo/voz ou alteração de roteamento/executor.39 casos novos;controle
anterior de excesso atualizado para limite integral de4000, preservando
recusa de corte e de ampliação. Textos sem fronteiras seguras ou âncoras
inequívocas continuam sob revisão anterior;representação conservadora.

RED24/2 antes do candidato. Replays separados da autoria e guarda históricas
congeladas voltam a20 e21 falhas respectivamente, só em memória. Quatro
provas instaladas em duas projeções:composto de oito domínios conclui no
pré-fluxo;composto IoT/playlist passa pela geração. Não contar pré-fluxo como
inferência. Interceptação de `resultado` dentro de citação pelo comentário
operacional registrada separadamente, sem patch. Status canônico de IoT
usado na sonda como no controle anterior;nenhuma regra por frase em produção.

Qwen real, uma inferência local HTTP200/stop:994 caracteres em unidades de
498 e495, oito receipts/quatro sucessos/quatro falhas, bruto integral antes
da revisão, declaração de suporte e comandos vazios. Cinco asserções
aprovadas e reaplicadas ao artefato sem nova geração. Fontes sintéticas;
sem main diário, áudio, dispositivo real ou compreensão livre comprovados.

Foco235 aprovados/dez skips/zero erros;52 módulos:1701 aprovados/30 skips/
oito subtestes e uma falha conhecida do catálogo (`estado_owner` neste
processo), zero erros. Não encerra C5/C7 gerais, derivação/pertinência de
paráfrases, fidelidade de análises da IA ou limites conservadores de
representação. Relatório, responsáveis, REDs, provas e selo:
`resultados_testes/compreensao_fala_acao_20261019/autoria_historica_integral/RELATORIO.md`.

## 41. C5 — fidelidade das premissas propostas, estudo sem ampliar produção

19/10/2026. Base ca592a9609dd1865b63b22c714f8d3e802fa2a5c,17 arquivos
de produção/configuração congelados e preservados. A próxima fronteira foi
testar se texto integral, hash e âncoras bastam para validar uma análise de
papéis/escopo sugerida pela IA. Não bastam:27 propostas com papéis trocados
conservam todas as âncoras e não recebem derivação. Nas nove atribuições do
fragmento conhecido, seis permutações de papéis passam pelas âncoras e só uma
recebe prova do owner;negação/condição externas continuam não conferíveis.

O revisor instalado preservou as recusas. Não foi demonstrada raiz de
produção que justificasse liberar paráfrases livres. Uma sonda e46 testes
foram acrescentados;nenhuma produção, modelo, voz, autonomia ou executor
alterados. Não instalar extrator para linguagem que o owner já lê de forma
determinística nem tratar a análise da IA como premissa independente.

| Responsável | Contrato antes de integrar análise nova | Critério |
| --- | --- | --- |
| Observação/owner | Fonte atual e escopo independentes da proposta | Snapshot/hash/identidade;alteração/expiração não herda prova. |
| Autoria/interpretação | Propor papéis/âncoras sem autoverificação | Papel/negação/condição não inferidos só de IDs ou substring. |
| Codec/preparador | Negociar as relações entre campos e validar resposta completa | Estado/valores compatíveis,cobertura e ordem;HTTP200 não é análise admitida. |
| Revisão de fidelidade | Conferir a representação contra a fonte integral | Regra/premissas independentes do modelo,com todos os qualificadores. |
| Apoio/pertinência | Julgar inferência e resposta à pergunta separadamente | Fidelidade não implica apoio;apoio não implica pertinência. |
| Execução/receipts | Continuar donos de autorização/efeito | Nenhum certificado,valor ou palavra do texto concede ação. |

Qwen real em27 fontes sintéticas,com nove casos de reserva de entidades.
Primeiro protocolo:nove HTTP200/stop,zero lotes admitidos por contradição
entre estado/papéis. RED demonstra que o schema da sonda permitia combinações
que o validator recusava. Somente esse schema diagnóstico foi alinhado,
mantendo o corpo do validator (comparação AST),painel,prompt e parâmetros.
Sem remover a guarda ou aceitar parcialmente documento recusado.

Rodada alinhada:nove HTTP200/stop,cinco lotes admitidos/quatro recusados por
ordem de IDs. Das15 análises admitidas,quatro têm derivação no fragmento e11
não:uma troca de papéis,dez perdas de negação/condição. Fonte e âncoras
corretas não resolveram fidelidade. Sem nova rodada para conseguir verde,
sem publicação/execução. Painel de mesma família/ordem repetida;não é
benchmark cego ou taxa geral de competência. A reserva é de entidades.

203 testes aprovados/quatro skips/zero erros em cinco módulos. Composições
instaladas existentes passaram com folhas controladas;modelo foi usado em
pedidos de interpretação pelo serviço real,não no main diário ou pipeline
conversacional completo. Produção idêntica:não se repetiu a regressão ampla.
Paráfrases livres,C5/C7 gerais e prova física continuam abertos. Próxima
condição:premissas independentes e regra de fidelidade fora do fragmento.
Relatório,contratos,hipóteses,XMLs,payloads e selo:
`resultados_testes/compreensao_fala_acao_20261019/fidelidade_premissas/RELATORIO.md`.

Desligamento do PC autorizado por Pedro para cinco minutos após esta etapa;
agendar somente depois de salvar resultados e registrar retorno do comando.

## 42. C5 — preservar o alcance da confirmação na ocorrência explicável

19/10/2026. Continuação da busca de premissas independentes da seção41.
Base ca592a9609dd1865b63b22c714f8d3e802fa2a5c, main/worktree preservada.
Parada elétrica confirma SACK sem aplicação de PWM; a recuperação histórica
preenchia sempre `PWM e parada elétrica`. Fonte errada antes do modelo:
executor correto e invenção exclusiva do Qwen falsificados. Não é nova raiz
por frase: aplica o princípio C5 de conservação do alcance ao canal de
ocorrência/decisão, separado do snapshot da fala da seção38.

O owner agora registra o escopo pela mesma escolha que define os receipts
exigidos, independentemente de sucesso/falha. Recuperação transporta a
premissa reconhecida; legado/valor inválido ficam com escopo não registrado.
Nome/status/texto do retorno/diagnóstico atual não reconstroem essa informação.
O contrato compartilhado de explicação já admite escopo por owner e foi
reutilizado sem parser novo, mudança de executor ou aprovação de prosa livre.

| Responsável | Contrato | Critério |
| --- | --- | --- |
| Owner da experiência | Vincular obrigação e confirmação à mesma ocorrência | Parada/PWM, sucesso/falha, persistência no aprendizado compartilhado. |
| Recuperação | Preservar premissa histórica, inclusive sua ausência | Legado, tipos inválidos, estado vivo divergente, expiração/três valores. |
| Autoria/revisão/entrega | Responder somente com a realização sustentada | Duas rotas, oito ciclos, uma publicação por ciclo, sem novo efeito. |
| Executor/transporte | Continuar donos de efeito e receipt | Protocolos reais com porta simulada, sem certificação física. |

Produção: somente `experiencia_corporal_runtime.py`, dois pontos do mesmo
contrato.24 controles novos, fixture instalada ampliada, nenhum commit.
RED18/2 e quatro falhas instaladas antes do candidato;replays separados em
memória causam10 e13 falhas. Foco final168 aprovados/cinco skips/zero erros
em sete módulos, incluindo28 controles de experiência contínua. Regressão
ampla de58 módulos:1919 aprovados/30 skips/oito subtestes/cinco falhas/zero
erros. As cinco repetem no baseline anterior e no candidato,com os mesmos
tipos/mensagens em processos novos. Uma é o catálogo conhecido;quatro
receipts/encadeamento corporal estão registrados separadamente,sem raiz
presumida ou patch neste candidato. A suíte ampla não está GREEN.

Giro relativo medido permanece distinto de deslocamento translacional e
parada física. Esta intervenção conserva a premissa elétrica; não amplia
a realização para explicar IMU, não troca modelo/voz nem ativa autonomia.
Sem inferência Qwen nova: divergência demonstrada antes do modelo, com
proposta deliberadamente inválida nos ciclos de revisão. Main diário,
áudio, efeito físico e C5/C7 gerais não certificados. Paráfrases livres
continuam pendentes de fidelidade/apoio/pertinência independentes.

Próxima fronteira: qualificadores/medidas transportáveis pelos owners, com
vínculo de ocorrência e regra de projeção, sem inferir alcance por booleano.
Relatório,baseline,REDs,compostos,contratos e selo:
`resultados_testes/compreensao_fala_acao_20261019/escopo_ocorrencia/RELATORIO.md`.

## 43. Preparo canônico dos ensaios de receipts — diagnóstico dos quatro REDs

19/10/2026. Base ca592a9609dd1865b63b22c714f8d3e802fa2a5c,main/worktree
preservada. Os quatro REDs corporais separados na seção42 foram reproduzidos
antes de alterar os testes. Primeira fronteira comum:preparo parcial do
ensaio atribui apenas classificação a `turno_atual`,sem plano/retrato.
O receipt positivo chega ao publicador instalado,que o recusa por frame
incompleto. Estado/aprendizado ausentes e cadeia interrompida são efeitos
posteriores. Não se demonstrou raiz de produção nesses quatro casos.

Treze cenários com owners instalados comparam preparo parcial,canônico,
entrada completa,mudança de turno com mesma frase e prontidão do ACK.
Entrada real instala turno/plano/retrato antes da execução;receipts aceitos
alimentam SQLite compartilhado e preservam falha parcial. A guarda recusa
o turno antigo mesmo com texto igual. Não flexibilizar o contrato para
aceitar o preparo incompleto dos testes.

| Responsável | Obrigação | Critério |
| --- | --- | --- |
| Ensaios de composição | Preparar pelo owner canônico usado pelo runtime | Comparação parcial/canônica/entrada completa;asserções anteriores preservadas por AST. |
| Publicador vinculado | Conferir ocorrência capturada antes do efeito | Recusa de frame incompleto e turno trocado;sem aprendizado indevido. |
| Executor/aprendizado/cadeia | Preservar receipt,aceitação e parcialidade | Dois IDs,STOP falho,evento SQLite e uma fala parcial. |
| Transporte do ensaio | Manter prontidão sem ampliar TTL | ACK vencido recusa;novo ACK real pelo protocolo permite. |

Produção idêntica nos12 arquivos congelados. Só dois módulos de testes
existentes ajustados e um novo com13 cenários. Nenhuma asserção anterior
removida ou enfraquecida. Fixture de companhia exige ACK após preparar o
turno,pois não inicia heartbeat;uma recusa intermediária foi preservada sem
declarar sua causa exata,que não estava capturada. Controles de expiração e
renovação são independentes da raiz inicial de publicação.

Foco381 aprovados/zero skips/zero erros em sete módulos. Regressão de60
módulos:1964 aprovados/30 skips/oito subtestes/uma falha conhecida do catálogo
(`estado_owner` neste processo)/zero erros. Quatro REDs corporais passaram;
suíte ampla não GREEN pela falha separada. Fechamento no relatório e selo. Sem commit,inferência
Qwen nova,modelo/voz/autonomia diária/produção alterados. Porta serial e
modelo controlados;sem main diário,áudio ou efeito físico. Recusa provada é
de publicação;os controles parciais chegam ao executor simulado.

Catálogo de confirmação continua separado. Não contar quatro sintomas como
quatro raízes,nem reabrir a correção C5 da seção42. Próxima fronteira do plano
continua sendo qualificadores/premissas verificáveis dos owners;semântica
livre e C5/C7 gerais permanecem abertos. Relatório,REDs,contratos e matriz:
`resultados_testes/compreensao_fala_acao_20261019/vinculo_receipts_corpo/RELATORIO.md`.

## 44. C5 — medidas e limites na fonte da explicação

19/10/2026. Base ca592a9609dd1865b63b22c714f8d3e802fa2a5c,worktree
preservada. Extensão da fronteira de premissas verificáveis: o owner já
registra ângulo,prova e método de giro,mas a adaptação para `EpisodioExplicavel`
os descartava. Dois históricos alternativos com valores diferentes viravam
a mesma fonte/fala. Na composição instalada,90/-180 estão no receipt e no
histórico,mas não na fonte anterior à geração. Ausência no produtor e perda
exclusiva pelo Qwen falsificadas. A realização elétrica anterior era
conservadora;não confundir esta extensão com a raiz de escopo da seção42.

Contrato compartilhado `MedicaoObservada`:ocorrência/owner,grandeza,valor
finito,unidade,método e limite explícito,sem autoridade. Episódio exige
medidas tipadas do mesmo ID/owner e sem duplicação. Owner corporal só projeta
a medida com as premissas históricas confirmadas;realizador genérico preserva
valor assinado/unidade/ressalva. Leitura parcial,JSON ou parecer da IA não
criam essa fonte;tipagem não certifica aferição nem causa externa.

| Responsável | Obrigação | Critério |
| --- | --- | --- |
| Owner histórico | Relê medida e premissas daquela ocorrência | Confirmação/prova/método/número;estado vivo não preenche ausência. |
| Contrato compartilhado | Conserva grandeza,valor,unidade,método,limite e vínculo | Três owners sintéticos;imutabilidade,tipo,ID/owner e duplicação. |
| Realização/revisão/autoria | Mantém a informação e recusa extrapolações | Número/sinal/ressalva;sem causa inventada ou novo efeito,duas rotas. |
| Executor/transporte,preservados | Continuam donos de receipt/correlação | PWM/parada não viram ângulo;outra sequência e falha não oferecem medida confirmada. |

Produção só `decisao_observada.py`,`experiencia_corporal_runtime.py` e
`explicacao_fala_historica.py`. Não há novo banco,parser,modelo,executor,
rota ou ativação autônoma. Um teste novo e fixture instalada ampliada;
programa do ensaio passou por stdin ao exceder o limite Windows,e passou
a reler o plano atual entre ciclos. Erros intermediários preservados,
sem alterar guardas para fazê-los desaparecer.

RED6/4 antes do candidato;10 controles iniciais verdes.41 controles novos,
seis casos instalados e12 ciclos normal/rápido,codec e publicação integrais,
zero novos despachos e histórico intacto. Replays da recuperação e realização
anteriores em memória voltam a quatro falhas cada. Foco final168 aprovados/
um skip opcional/zero erros em seis módulos.61 módulos:2005 aprovados/31
skips/oito subtestes/uma falha conhecida do catálogo (`estado_firmware` neste
processo)/zero erros. Suíte ampla não GREEN;sem nova falha no recorte.

Modelo local persistido `qwen3:4b-instruct`,sem mudança de seleção:duas chamadas
HTTP200/stop conservam integralmente452/453 caracteres,90/-180 e ressalva,
antes da revisão. Teste HTTP opcional aprovado separadamente. Cópia controlada
da realização do owner,não parecer usado como prova ou benchmark semântico.
Serial simulado;sem main diário,áudio,medida física real ou paráfrases livres
certificados. C5/C7 gerais continuam abertos.

Próxima fronteira:qualificar leituras parciais separadamente do resultado do
objetivo,sem transformar observação parcial em ação concluída nem falha do
objetivo em ausência de observação. Estudar antes de ampliar a admissão.
Relatório,baseline,contratos,responsáveis,REDs,HTTP e selo:
`resultados_testes/compreensao_fala_acao_20261019/medidas_ocorrencia/RELATORIO.md`.

## 45. C5 — observação parcial e conclusão da obrigação

19/10/2026. Base ca592a9609dd1865b63b22c714f8d3e802fa2a5c, main,
worktree preservada. Duas fronteiras investigadas e registradas separadamente:

- Qualificação independente da leitura: extensão da medida da seção 44. O
  transporte já entrega número em TURNEND, inclusive em encerramentos com
  IMU inválida; `prova_rotacao` apenas qualifica conclusão do alvo. Estudo do
  firmware identifica quais encerramentos atravessam as guardas necessárias.
  Novo qualificador não muda sucesso, PWM, parada, autoridade ou prova de giro.
  Histórico conserva essa premissa; recuperação usa MedicaoObservada existente.
- Escopo global do giro: extensão da família de escopo da seção 42, descoberta
  após GREEN da leitura. Captura omitia obrigação angular apesar de conclusão
  global falsa e PWM/parada verdadeiros. Dois REDs próprios; escopo agora vem
  do alvo canônico solicitado no retorno do executor, não do número observado.

| Responsável | Obrigação | Validação |
| --- | --- | --- |
| Transporte | Qualificar leitura correlacionada sem concluir a operação | Tempo/zero/divergência/ultrapassagem válidos; IMU/saturação/proteção/interrupção ambígua recusadas; outra sessão/sequência sem empréstimo. |
| Experiência/recuperação | Conservar observação e obrigação separadamente | Histórico/SQLite/fonte do mesmo ID; ausência, método estranho e parecer/diagnóstico vivo não completam fonte. |
| Realização/revisão/autoria existentes | Conservar número, sinal, unidade e limite | Dez casos, 20 consultas em duas rotas, codec/publicação integrais, sem novo efeito ou mutação histórica. |
| Aprendizado compartilhado | Não promover objetivo falho a sucesso | Sinal negativo nos dez cenários, inclusive medida válida com parada não confirmada. |

Produção apenas rosto_oled_runtime e experiencia_corporal_runtime. Firmware,
executor, MedicaoObservada, realizador e guardas de autoria preservados; 13 dos
17 arquivos congelados idênticos. Nenhum commit/modelo/voz/autonomia diária.
Princípio geral: observação qualificada não confirma conclusão da obrigação;
falha da obrigação não apaga observação válida. Outros owners reutilizam o
contrato de medida, mas precisam qualificar seus próprios sensores/fontes.

RED transporte 9/2/1 skip; captura três REDs; GREEN inicial 24/1 skip. Escopo:
dois REDs independentes. Novo módulo 39 aprovados/dois skips. Replays em
memória voltam a cinco falhas no transporte, três na captura, três na
recuperação e duas no escopo, sem reverter arquivos. Qwen local persistido:
duas HTTP200/stop, 23.75/0.0, bruto integral com ressalva antes da revisão;
coleta opcional aprovada. Sem tratar indicação do modelo como prova.

Foco de sete módulos:179 aprovados/quatro skips/uma falha de orçamento/zero
erros. Regressão62 módulos:2044 aprovados/33 skips/oito subtestes/uma falha
conhecida do catálogo/zero erros. Complemento do módulo da fixture:cinco
aprovados/um skip/uma falha de orçamento. União63 módulos:2049 aprovados,
34 skips,oito subtestes,duas falhas,zero erros; suíte ampla não GREEN.
Orçamento reproduz 4015 > 3800 tanto com métodos congelados quanto atuais;
não foi causado pelo candidato, não teve limite relaxado e sua raiz específica
continua aberta. Catálogo conhecido permanece separado.

Serial simulado e persistência isolada; não é main diário, aferição física,
áudio ou compreensão livre geral. Compilador C++ ausente: novo teste host
preparado, mas pulado, sem flash/instalação. INTERROMPIDO/PROTECAO continuam
sem leitura oferecida por ambiguidade de validade; ausência de medida oferecida
não prova ausência física de movimento. Próxima fronteira candidata: conferir
a conclusão imediata frente às facetas do receipt, sem misturá-la com validade
histórica, orçamento ou catálogo. C5/C7 gerais seguem abertos.
Relatório completo, contratos, fontes, responsáveis, XMLs, HTTP, comparações e selo:
`resultados_testes/compreensao_fala_acao_20261019/leituras_parciais/RELATORIO.md`.

## 46. C5 — conclusão imediata respeita os aspectos da própria execução

19/10/2026. Por pedido de Pedro, a prova física fica adiada, sem bloquear a
continuidade e sem ser marcada como validada. Base ca592a9609dd1865b63b22c714f8d3e802fa2a5c,
main e worktree preservados. Extensão do alcance da confirmação na fala,
distinta da qualificação da leitura e do escopo angular da seção 45.

Raiz demonstrada: receipt/publicação brutos conservam as partes, mas a escolha
da fala usa o resultado global e ignora confirmações parciais. Falha do giro
vira mensagem genérica que põe em dúvida comando/parada já confirmados.
ACK ausente, perda na entrega e erro exclusivo do Qwen falsificados. A primeira
decisão divergente é de verbalização; não houve perda dos booleans no produtor.

Contrato compartilhado `AspectoResultado`: ID, escopo, confirmação True/False/
None e referência de evidência do owner. ResultadoAcao conserva tupla tipada,
limitada, da mesma execução/origem, sem alterar conclusão global. JSON e nova
proposta não recriam aspectos certificados. Tipagem não é prova da verdade.

| Responsável | Obrigação | Critério |
| --- | --- | --- |
| Executor do domínio | Adaptar seus campos observados | PWM/parada da mesma invocação; sem parser de frase ou inferência de efeito. |
| Adaptador/resultado compartilhados | Conservar só a publicação aceita | ID, origem, tipo e snapshot; recusa/troca/nova tentativa sem empréstimo. |
| Planejador compartilhado | Separar resultado global e alcances | Todas as combinações de três valores em corpo/aplicação/arquivo/IoT; controles fora do corpo são contratuais. |
| Orquestrador/autoria | Entregar a mesma realização factual | Porta direta e lote; trecho de aspectos fechado, sem causa extra ou sucesso total fabricado. |

Produção somente resultado_acao, adaptador_resultado, executor_corpo,
roteador_intencao, planejador_resposta, confirmacao_llm e orquestrador_fala_runtime.
Nove controles congelados idênticos, incluindo transporte, experiência,
medida histórica, guardião e laylay.py. Nenhum commit/modelo/voz/ativação diária.

Dez REDs iniciais; dez verdes após projeção inicial; dois REDs da propagação
nas portas final/composta, seguidos de52 verdes. Fechamento:64 testes aprovados,
dez ações instaladas/20 consultas históricas e três composições aplicação/corpo.
Aplicação já aberta/focada por leitura controlada; corpo usa serial simulado.
Uma publicação por composto, receipts independentes, um TURN por pedido,
falha parcial preservada; autoria fiel aceita e duas propostas inválidas recusadas.
Replays anteriores em memória:27 REDs do planejador,um da entrega,um da autoria.

Regressão70 módulos:2288 aprovados/34 skips/oito subtestes/quatro falhas/zero
erros. Catálogo e orçamento conhecidos; dois testes de transporte composto
também falham com fontes anteriores carregadas em memória. Causas dessas
ocorrências não foram misturadas nem corrigidas neste recorte; suíte ampla
não GREEN. Não houve nova inferência real ao Qwen; autoria controlada pelo
serviço instalado, sem usar proposta como prova.

Primeiro ensaio com “e depois” não chegou ao giro: um único segmento não
fornece átomo corporal ao executor, que recusa sem forçar autorização global.
Foi preservado como fronteira separada. Prova cooperativa usa ponto e vírgula,
já separado pelo segmentador canônico, sem relaxar guardas de produção.
Próxima candidata: estudar atomização/autoridade desse composto antes de
corrigir o contrato compartilhado; não remendar a frase. Medidas detalhadas
na resposta imediata e C5/C7 gerais continuam limites distintos.
Sem main diário/áudio/efeito físico ou compreensão livre geral certificados.
Evidências,contratos,responsáveis,diffs,baselines,XMLs e selo:
`resultados_testes/compreensao_fala_acao_20261019/resposta_imediata/RELATORIO.md`.

## 47. F1 — mesma fronteira lexical para atos, condições e cadeia

19/10/2026. Continuação da fronteira separada na seção 46. Hardware continua
adiado por Pedro. HEAD ca592a9609dd1865b63b22c714f8d3e802fa2a5c, main, worktree
preservada e 17 fontes congeladas antes do candidato. Nenhum commit criado.

Raiz demonstrada: consumidores reconheciam a mesma coordenação com vocabulários
divergentes. A cadeia separava “e depois”, mas modalidade mantinha o bloco;
executor corporal recusava corretamente por falta de ato autorizado específico.
Detector condicional também ignorava “se” após alguns desses conectores,
permitindo que a vírgula soltasse a consequência. “e então/e em seguida”
deixavam “e” no núcleo anterior da cadeia. Não é falha de giro/ACK/Qwen nem
ausência geral de proteção condicional: controles com “e”/“;” funcionam.

Contrato lexical canônico em normalizacao_linguagem, consumido por modalidade
(coordenação e posição da condição) e analise_comandos. Reconhecer fronteira
não autoriza: cada owner conserva semântica, fonte e guardas. Não remover
modificadores temporais iniciais nem dar autoridade à proposta da IA.

| Responsável | Obrigação | Validação |
| --- | --- | --- |
| Normalização compartilhada | Publicar operador inteiro, maior antes do menor | Sete conectores; sem sobra no núcleo e sem apagar tempo inicial. |
| Modalidade | Deliberar atos e vincular condição/consequência | Três pares de domínios; condições, negação, relatos e capacidade sem autorização inventada. |
| Cadeia | Consumir a mesma fronteira lexical | Fonte/case/intervalo, nomes, aspas, enumerações e limites preservados. |
| Escopo/executor existentes | Exigir autorização específica | Proposta de giro condicionado não gera TURN, mesmo com primeiro ato autorizado. |
| Receipts/fala existentes | Concluir sem transformar parcial em total | Duas rotas instaladas, receipts independentes, uma publicação por composto e autoria adversarial recusada. |

Somente três produções alteradas; uma fixture estendida e um novo módulo de
testes. Dos 17 arquivos congelados, 13 controles idênticos. Executor, router,
escopo, dispatcher, transporte, experiência, fala e composition root preservados.
30 REDs/quatro controles antes; mesmos 34 GREEN depois. Novo módulo final:
100 aprovações, incluindo seis compostos e dois negativos na composição real
instalada. Replays antigos em memória retomam seis perdas de fronteira, quatro
condições liberadas e duas sobras de conector, cada consumidor isoladamente.

Foco de 11 módulos:508 aprovados/duas falhas/zero erros. As duas falhas musicais
com negação, já registradas em 14/10, reproduzem com as três fontes anteriores
completas; não foram corrigidas nem misturadas nesta entrega. Regressão80
módulos:2739 aprovados/34 skips/oito subtestes/seis falhas/zero erros,397,89s.
Os 100 novos casos passam também na regressão. Quatro pendências da seção46
e duas musicais preexistentes; suíte ampla não GREEN, sem relaxar testes.
As mesmas seis falhas reproduzem na contraprova final com três fontes
anteriores completas carregadas em memória; preexistência no recorte comprovada.

Leitura de janela e serial controlados, persistência isolada, autoria pelo
serviço instalado com retornos controlados; sem main diário, áudio, inferência
real nova ou prova física. GREEN de composição deste contrato não encerra F1
inteira, C5/C7 ou compreensão livre geral. Princípio global: compartilhar a
fronteira lexical conservando owners semânticos e de autoridade.
Próxima candidata: medidas qualificadas na resposta imediata, distintas dos
aspectos de confirmação e da recuperação histórica já validados.
Contratos, responsáveis, baselines, diffs, XMLs, brutos e limites:
`resultados_testes/compreensao_fala_acao_20261019/atomizacao_compostos/RELATORIO.md`.

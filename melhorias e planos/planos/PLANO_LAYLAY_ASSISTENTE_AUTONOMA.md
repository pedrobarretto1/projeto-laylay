# Plano de evolução da Laylay para assistente autônoma

Data: 30/09/2026. Solicitado por Pedro após a avaliação dos nove pontos de evolução.

## 1. Objetivo e escopo

Evoluir a Laylay para receber um objetivo, conduzi-lo por várias etapas e comprovar o resultado com pouca supervisão. A experiência desejada é inspirada no Jarvis: continuidade, iniciativa útil, coordenação de habilidades, conversa natural e confiança operacional.

Autonomia significa executar e acompanhar objetivos dentro de uma delegação explícita. A LLM propõe interpretações e planos; componentes externos a ela validam autoridade, estado, execução e evidência. Personalidade e emoção não concedem permissão operacional.

Este documento registra a avaliação e o plano de execução. Sua criação não aplica candidatos, não ativa modos autônomos nem autoriza efeitos externos do futuro piloto. Não há implementação concluída por este plano.

## 2. Base e limites da avaliação

- Branch consultada: `main`.
- HEAD de referência: `90a2fb8698541119f523c0a22fa4de0187cbaf92`.
- A worktree contém alterações paralelas de cognição, autonomia, personalidade, composição e experimentos. Preservar todas; HEAD não representa sozinho o código em uso.
- Avaliação por leitura direcionada de código e registros, sem executar testes nesta rodada documental.
- O motor de iniciativa oferece modos desligado, sombra, sugestão e autorizado, governança, limites de frequência e circuitos de falha. O modo sombra é padrão no componente; isso não comprova a configuração da sessão aberta.
- O executor autônomo possui um conjunto delimitado de ações. O quadro cooperativo mantém planos efêmeros, etapas, dependências, cancelamento e resultados. Já existem fluxos cooperativos específicos.
- Há motores compartilhados de memória, aprendizado, continuidade, catálogo de capacidades e políticas de reexecução. Inventariar a cobertura efetiva antes de propor qualquer novo serviço.
- Os registros recentes demonstram avanços na correlação entre turno, plano, retrato e resposta, mas mantêm limites sobre callbacks atrasados, corrida após validação e mescla de receipts por intent. Cada mecanismo exige diagnóstico próprio.
- P02/P06 receberam correções recentes com validação registrada. Não reabrir os 14 casos históricos como se ainda estivessem intocados. Qualidade técnica mais ampla e explicações de capacidades continuam com limites próprios.

Referências canônicas:

- [Instruções do projeto](../../AGENTS.md).
- [Registro de problemas e correções](../registro/REGISTRO_PROBLEMAS_E_CORRECOES.md).
- [Mapa causal da conversa](../raiz/MAPA_RAIZES_CONVERSA.md).
- [Relatório P02/P06 de 30/09](../relatorio/RELATORIO_P02_P06_20260930.md).
- [Plano de memória e segundo cérebro](PLANO_LAYLAY_SEGUNDO_CEREBRO_MEMORIA.md).
- [Plano de conversa natural e personalidade](PLANO_LAYLAY_CONVERSA_NATURAL_PERSONALIDADE_CODEX.md).
- [Roadmap de personalidade viva](../ideias/ROADMAP_PERSONALIDADE_VIVA.md).

Os planos existentes são referências de intenção, não provas de implementação. Distinguir a etapa P16 do roadmap de personalidade do problema histórico P16 do registro: nomes iguais não demonstram uma única causa.

## 3. Os nove pontos preservados

| Ponto | Benefício esperado | Base a reaproveitar / lacuna a investigar |
| --- | --- | --- |
| 1. Objetivos além de um turno | Acompanhar etapas, prazo, progresso e bloqueios; retomar após reinício | Quadro e coordenação cooperativa existem; investigar persistência e recuperação de compromissos longos |
| 2. Planejar e ajustar o plano | Decompor objetivos, respeitar dependências e escolher alternativas permitidas | Cooperação existe em fluxos específicos; ampliar cobertura com critérios verificáveis |
| 3. Correlação completa | Garantir que cada resultado pertence à ação, ao alvo e à ocorrência corretos | Reusar contratos de turno, plano, resultado e publicação; tratar limites registrados separadamente |
| 4. Delegações delimitadas | Agir sem pedir a mesma confirmação a cada passo, dentro de limites escolhidos por Pedro | Governança de iniciativa já existe; investigar delegação por objetivo, alvo, tempo e revogação |
| 5. Percepção e atualização do estado | Revalidar ambiente e distinguir observação recente de hipótese ou memória antiga | Percepção, contexto compartilhado e disponibilidade operacional existentes |
| 6. Aprendizado com evidência | Aplicar correções futuras no contexto certo e reconhecer mudanças de preferência | Motores compartilhados de aprendizado, maturidade e memória confiável |
| 7. Consciência de capacidades | Explicar acesso atual, condições, limites e bloqueios de modo consistente | Catálogo vivo e conversas sobre capacidades; qualidade geral ainda tem pendências |
| 8. Voz e continuidade | Ceder a entrada, aceitar interrupções e retomar o objetivo certo | Pendências P05/P07 e componentes de entrada, presença, fala e histórico |
| 9. Recuperação e progresso real | Retomar, cancelar, evitar duplicação, desfazer quando cabível e comunicar sucesso parcial | Executor cooperativo, resultados e efeitos reversíveis; ampliar provas no caminho real |

## 4. Contratos globais obrigatórios

1. Autoridade explícita antes de efeito; contexto, memória e percepção não autorizam operações.
2. Receipt antes do próximo efeito dependente e antes da confirmação de sucesso.
3. Identidade de objetivo, revisão do plano, etapa, tentativa, ocorrência e alvo deve acompanhar o resultado onde aplicável.
4. Uma decisão possui um owner canônico; domínios não recriam parsers, políticas ou estado privados.
5. Falha fecha operações dependentes; falha parcial não é sucesso integral.
6. Entrada consumida como `tratado=True` precisa de conclusão observável.
7. Objetivo e pendência possuem ciclo de vida explícito; comandos independentes não os consomem por acidente.
8. Memória durável exige fonte e escopo; aprendizado não promove hipótese a fato ou preferência a permissão.
9. Retomada e replanejamento revalidam estado e autoridade. Persistir uma delegação não a torna irrevogável.
10. Cancelamento bloqueia novas etapas; efeitos já iniciados precisam ser reconciliados e relatados.

Aplicar contratos compartilhados progressivamente a habilidades distintas. Provar o benefício em pelo menos dois domínios quando o mecanismo for comum, sem ampliar um patch para roots diferentes.

## 5. Organização do trabalho

A unidade de acompanhamento e encerramento é a raiz causal ou o contrato novo de evolução. Os códigos `AUT-*` abaixo identificam entregas planejadas; não são nove bugs demonstrados nem substituem os IDs históricos do registro.

Antes de cada candidato: consultar registro e mapa, congelar branch/HEAD/worktree, localizar a primeira fronteira RED, mapear owner e composição real, falsificar alternativas plausíveis e criar um RED canônico. Se o resultado surpreender, refazer o diagnóstico antes do patch.

Para evolução sem bug histórico, formular primeiro o comportamento esperado e a evidência que demonstrará o benefício. Confirmar quais capacidades já atendem ao contrato e qual extensão mínima falta.

Ordem proposta:

1. Inventário e mapeamento das roots existentes.
2. AUT-01: confiabilidade da cadeia de autoridade e resultados.
3. AUT-02 e AUT-03: objetivos persistentes e delegação delimitada.
4. AUT-04: percepção revalidada.
5. AUT-05: planejamento e recuperação sobre os contratos anteriores.
6. AUT-06, AUT-07 e AUT-08: aprendizado, explicações e voz; cada raiz pode avançar independentemente, com pré-requisitos respeitados.
7. AUT-09: piloto integrado e ampliação gradual da iniciativa.

Recuperação, cancelamento e observabilidade são requisitos desde a primeira entrega executável, não itens adiados até o piloto final. A numeração organiza entregas, não autoriza implementação paralela irrestrita.

## 6. Entregas por contrato

### AUT-01 — Autoridade e resultados correlacionados

**Estado:** há lacunas registradas; extensão exata e estado atual devem ser reproduzidos antes de editar.

**Owners a conferir:** contratos/decisão de turno, orquestrador do turno, publicação/consumo da resposta e contrato de resultado. `laylay.py` mantém apenas wiring.

**Execução:** mapear cada callback e writer; acompanhar ocorrência esperada e revisão ao publicar; conservar receipts legítimos; impedir que uma resposta tardia ou receipt de outra solicitação certifique o objetivo atual. Investigar mescla por intent como mecanismo separado da troca de frame.

**Provas:** troca de turno durante processamento, frase igual com novo ID, duas operações da mesma intent com alvos distintos, retorno atrasado, receipt ausente/malformado e controles coerentes em arquivos, IoT e música conforme aplicabilidade.

**Conclusão:** cada root efetivamente tratada possui RED, candidato mínimo, regressivos, composição instalada e prova no runtime; nenhuma confirmação de efeito sem vínculo e evidência. Mock ou receipt sintético não certifica efeito externo.

### AUT-02 — Objetivos persistentes e retomáveis

**Estado:** evolução proposta; quadro cooperativo consultado é efêmero. Inventariar persistência e agenda existentes antes de declarar ausência global.

**Owners a conferir:** memória/persistência para compromissos duráveis; quadro/orquestrador cooperativo para execução. Não criar duas cópias autoritativas do mesmo progresso.

**Contrato proposto:** objetivo guarda ID, origem, descrição, critério de conclusão, prazo opcional, estado, revisão, etapas, dependências, vínculo da delegação, checkpoints, resultados e motivo de bloqueio. Estados mínimos: proposto, aguardando autorização, ativo, pausado, bloqueado, concluído, cancelado e expirado; normalizar com estados existentes.

**Execução:** começar por um objetivo explícito; persistir transições; carregar após reinício; conferir receipts, efeitos e disponibilidade antes de retomar. Distinguir objetivo de pendência de confirmação e memória pessoal. Recuperação incompleta deve bloquear com explicação.

**Provas:** reinício entre etapas, checkpoint incompleto, alteração de alvo, objetivo cancelado, prazo vencido e duas metas concorrentes. Em queda após efeito e antes de persistir resultado, reconciliar antes de repetir; se não houver prova suficiente, manter efeito incerto.

**Conclusão:** um objetivo atravessa turnos e reinício sem perder progresso ou repetir efeitos confirmados; nenhuma garantia artificial de execução exatamente uma vez.

### AUT-03 — Delegação com escopo e revogação

**Estado:** ampliar governança existente somente onde o inventário demonstrar necessidade.

**Owners a conferir:** governança/motor de iniciativa, governança cooperativa e porteiros canônicos.

**Contrato proposto:** delegação identifica autorizador, ações, alvos, contexto, validade, limites, risco permitido e revogação. O pedido de um objetivo pode autorizar seus passos quando o escopo for claro; extrapolação exige nova autorização. Reusar linguagem canônica de confirmação.

**Execução:** modelar primeiro delegação reversível de estudo, como luz e volume com limites definidos por Pedro; manter ações que exigem confirmação humana no fluxo previsto pelas políticas atuais. Auditar sem credenciais ou conteúdo privado desnecessário.

**Provas:** validade expirada, alvo diferente, revogação durante execução, limite excedido, mera preferência, frase hipotética e pedido legítimo já autorizado.

**Conclusão:** ações cobertas avançam sem confirmação redundante; ações fora do escopo param com motivo observável. Aprendizado não amplia a delegação.

### AUT-04 — Estado observado e revalidado

**Estado:** evolução da cobertura dos serviços existentes, não prova de que a Laylay desconheça seu ambiente.

**Owners a conferir:** percepção, contexto compartilhado, disponibilidade operacional e adaptadores reais dos domínios.

**Contrato:** observação conserva fonte, alvo, timestamp, validade e qualidade. Ausência de observação não prova ausência do recurso. A etapa consulta pré-condições atuais e confirma pós-condições reais.

**Execução:** selecionar pré-condições para o piloto; revalidar quando houver mudança relevante ou expiração. Consultas não podem causar efeitos escondidos.

**Provas:** dispositivo offline, aplicativo fechado entre etapas, dado expirado, alvo ambiguamente substituído e diferença entre memória e leitura atual.

**Conclusão:** mudança no ambiente bloqueia ou ajusta a etapa pelo owner correto sem trocar alvo nem anunciar sucesso presumido.

### AUT-05 — Planejamento adaptativo e recuperação

**Dependências:** AUT-01, persistência mínima de AUT-02, governança de AUT-03 e pré-condições de AUT-04.

**Owners a conferir:** orquestrador/quadro cooperativo, executor cooperativo, política de reexecução e efeitos reversíveis.

**Contrato:** LLM pode propor etapas; coordenador valida capacidade disponível, parâmetros, dependências, ciclos, autoridade, orçamento e critérios de resultado. Revisão do plano invalida resultados incompatíveis. Cada etapa conserva identidade e recibos.

**Execução:** partir de fluxos existentes; ampliar para objetivo de estudo. Definir tentativas e tempo finitos, limites de custo quando aplicável e política para etapas independentes. Replanejar dentro da delegação. Retry exige segurança da ocorrência, não apenas intent elegível. Desfazer só com efeito reversível confirmado e sem sobrescrever mudanças posteriores de outro fluxo.

**Provas:** sucesso, falha intermediária, idempotência, timeout com efeito incerto, cancelamento, etapa independente, plano inviável, proposta fora do catálogo e orçamento esgotado.

**Conclusão:** uma falha produz recuperação limitada ou bloqueio explicado; não produz loop infinito, repetição cega ou sucesso integral falso. Cancelamento em curso reconcilia efeitos que já começaram.

### AUT-06 — Aprendizado que melhora decisões futuras

**Owners a conferir:** motor de aprendizado, maturidade, correções do usuário e memória confiável; articular com o plano de segundo cérebro.

**Contrato:** separar correção, preferência explícita, hipótese de hábito, fato observado e permissão. Preservar fonte, contexto, validade e contradições.

**Execução:** escolher um comportamento repetido do piloto; registrar feedback e resultado; avaliar aplicação em exemplos novos. Inicialmente observar em sombra. Só ampliar influência operacional após critérios documentados; manter o baseline local quando disponível e apropriado.

**Provas:** correção reaplicada, preferência alterada, contexto diferente, silêncio não conclusivo, resposta da própria IA usada como fonte e tentativa de promover hábito a autoridade. Separar desenvolvimento e avaliação independente.

**Conclusão:** ganho aparece em entradas novas sem degradar controles de segurança ou contaminar avaliação. Quantidade de registros sozinha não certifica aprendizado.

### AUT-07 — Capacidades, explicações e progresso verdadeiro

**Owners a conferir:** catálogo vivo, conversa sobre capacidades, contrato de fala, fundamentação factual e observabilidade; vincular às roots reais de P01 e vizinhas.

**Contrato:** disponibilidade e limites atuais acompanham a tarefa por recuperação contextual. Explicação preserva o objetivo do usuário. Progresso deriva do estado e dos receipts; tentativa, efeito incerto e confirmação ficam distintos.

**Execução:** responder naturalmente “o que você pode fazer sozinha?”, “por que parou?” e “o que falta?”. Publicar mudanças relevantes de progresso sem interromper por eventos internos irrelevantes. Não inserir um catálogo inteiro no prompt permanente.

**Provas:** capacidade indisponível, acesso parcial, dependência offline, falha técnica, sucesso parcial, objetivo concluído e pergunta sobre procedimento sem execução.

**Conclusão:** explicação coincide com capacidades e estado reais; falha não vira pedido de reformulação indevido ou confirmação inventada. Não contar correções recentes de P02/P06 como trabalho novo.

### AUT-08 — Voz, interrupção e continuidade

**Estado:** consultar e reproduzir P05/P07; são pendências distintas, não uma única root presumida.

**Owners a conferir:** composição de entrada, prioridade do usuário, presença, filas de fala, sessão/histórico e continuidade canônica.

**Contrato:** entrada aceita recebe prioridade; interromper fala não significa cancelar objetivo; pedido de cancelamento não é mera interrupção. Falas enfileiradas revalidam relevância e estado antes de emitir. Histórico mantém origem textual/áudio corretamente.

**Execução:** diagnosticar cada fronteira; aceitar correção e retomada natural; impedir confirmação velha depois de cancelamento. Usar os componentes reais da composição.

**Provas:** usuário fala durante presença, interrompe anúncio de progresso, muda de assunto, cancela, retoma e usa exclusivamente áudio. Separar teste de fila de voz de escuta/TTS físico.

**Conclusão:** runtime real cede, mantém continuidade correta e não publica fala obsoleta. Áudio físico deve ser validado para certificar a experiência por voz.

### AUT-09 — Piloto integrado e expansão gradual

**Objetivo de referência:** “Prepare meu ambiente de estudo e acompanhe esta tarefa por uma hora.” Esta frase é cenário de teste, não uma ordem para executar efeitos agora.

**Preparação:** definir com Pedro tarefa, limites de luz/volume, prazo, critério de sucesso e frequência de acompanhamento. Limites numéricos são parâmetros do piloto, não defaults inventados. Acompanhar não autoriza ler conteúdo de tela ou arquivos fora do escopo definido.

**Execução:** observar ambiente → propor plano → validar delegação → executar etapas permitidas → confirmar efeitos → acompanhar progresso → aceitar interrupção/cancelamento → revalidar após falha/reinício → apresentar conclusão comprovada.

**Provas reais obrigatórias:** caminho feliz, indisponibilidade de uma habilidade, falha parcial, mudança do estado, revogação, interrupção de voz, reinício e prevenção de duplicação. Usar controles seguros para falhas; não iniciar caos destrutivo sem autorização específica.

**Progressão:** modo sombra → sugestão → piloto autorizado com ações reversíveis → repetição em cenários variados → expansão de cobertura por contrato. Ter o componente em modo autorizado não comprova prontidão global.

**Conclusão:** todos os critérios aplicáveis possuem evidência; componentes externos e áudio físico têm validação própria. Limites remanescentes ficam publicados e bloqueiam a expansão afetada.

## 7. Validação e métricas

Para cada raiz/capacidade, registrar separadamente:

1. RED canônico que alcança a fronteira correta, incluindo a frase de Pedro quando houver bug histórico e variantes naturais próximas.
2. GREEN unitário e controles negativos, ambíguos, expirados, idempotentes e de falha quando aplicáveis.
3. Integração com componentes compartilhados reais.
4. Composição instalada pelo caminho real, sem wiring manual substituto.
5. Runtime real, incluindo receipt externo e estado observado para alegações de efeito.
6. Regressão ampla relevante; caos apenas depois do diagnóstico focado.

Aplicar os nove pilares do AGENTS.md: contexto, memória, aprendizado, linguagem natural, continuidade, segurança, diagnóstico, consciência de capacidades e cooperação. Atualizar o roadmap de novas habilidades somente após provas aplicáveis.

Métricas do piloto:

| Métrica | Critério |
| --- | --- |
| Efeitos sem autorização / sucesso falsamente anunciado | Zero nos cenários avaliados; qualquer ocorrência interrompe expansão |
| Receipts estrangeiros / duplicação após retomada | Zero nos controles avaliados |
| Cancelamento | Nenhuma nova etapa iniciada após aceite; efeitos em curso reconciliados e comunicados |
| Objetivos concluídos | Conclusão somente com critérios e evidências satisfeitos |
| Recuperação | Tentativas e recursos dentro dos limites; efeito incerto não é repetido cegamente |
| Clareza e utilidade | Avaliar respostas finais e feedback de Pedro, não apenas formato de JSON |
| Aprendizado | Ganho em entradas novas, sem regressão de segurança |
| Voz | Continuidade e prioridade observadas no caminho real com áudio |

Registrar tamanho/amostragem, baseline, versões, condições e limites. Zero falhas numa amostra não demonstra ausência universal de defeitos. Metas numéricas de qualidade e latência devem ser fixadas após medir o baseline, antes da comparação do candidato.

## 8. Controle de execução e handoff

Checklist inicial:

- [x] Revalidar HEAD, branch, diff e arquivos não rastreados causalmente relevantes.
- [x] Ler os adendos mais recentes do registro e mapa; vincular AUT-01 à pendência já registrada de callback tardio.
- [x] Inventariar serviços e testes da primeira raiz: estado transacional, identidade da proposta, writer, composição e runtime de resposta.
- [x] Selecionar a primeira fronteira RED atual: publicação de uma proposta antiga em nova ocorrência coerente.
- [x] Formular contrato e controles antes do candidato; inventário das demais entregas permanece por fazer.

Estado atual: AUT-01 **iniciada e parcial**, com os checkpoints 9 e 10 e correções posteriores de outras frentes reconhecidas no registro central; AUT-02 a AUT-09 continuam planejadas. A criação original deste documento foi somente documental. Cobertura existente deve ser reconhecida no inventário, sem reaplicar ou reivindicar trabalho anterior.

Para cada root, manter no registro canônico: evidência e baseline; comportamento esperado/observado; primeira divergência; owner; hipóteses falsificadas; arquivos alterados; RED/GREEN por nível; prova externa; riscos e limites; próxima fronteira. Não abrir um arquivo por frase nem duplicar a contagem de problemas.

Preservar worktree e histórico; usar patches mínimos; não criar commits automaticamente. Se houver aplicador, ele valida HEAD/bloco, faz backup apropriado, aborta em divergência e confirma a alteração. Nenhum reset, clean, restore, pull ou rebase automático.

Critério global: uma assistente autônoma confiável recebe um objetivo, mantém seu contexto, age dentro da autoridade delegada, verifica resultados, recupera-se com limites e comunica o que realmente ocorreu. O encerramento é por contratos comprovados, não por quantidade de habilidades ou testes verdes.

## 9. Checkpoint AUT-01 — ocorrência esperada nas publicações, 30/09/2026

### Raiz e evidência

Continuação da pendência de callback tardio já registrada no mapa causal e no registro; não cria outra causa por habilidade. Base `main`, HEAD `90a2fb8` preservado, worktree com alterações paralelas.

Cadeia reproduzida: fonte principal capturada → validador aceita o frame original → entra nova ocorrência internamente coerente, inclusive com a mesma frase → writer atualiza fase/comandos/trilha do frame novo. A leitura semântica também publicava antes do writer sem conferir a ocorrência de origem.

Falsificados: incoerência interna como causa necessária (o frame novo é coerente); falha geral do filtro (a proposta é válida antes da troca); necessidade de apagar receipts por omissão (quatro controles preservam o receipt legítimo, incluindo falha do modelo). Os REDs não acionam executor externo.

A primeira versão de testes também tinha expectativas incorretas sobre a normalização do receipt e retorno público de `processar`, que é `None`. Foram corrigidas para observar o receipt realmente armazenado e a sequência causal de callbacks; esses erros de teste não contam como REDs arquiteturais. Após essa correção, a rodada anterior ao candidato teve **25 REDs e quatro controles verdes**; três REDs cobravam o novo encaminhamento do protocolo, os demais alcançavam publicações indevidas ou continuação após recusa.

### Contrato e candidato

Reusar `ContratoPropostaPrincipal` e `motivo_divergencia_ocorrencia_principal`. A validação da ocorrência não exige sucesso do modelo, não concede autoridade e não transforma proposta em receipt.

- Writer moderno confere a ocorrência na transação que publica plano/trilha; fonte inválida ou ausência de transação recusa a publicação.
- Leitura semântica deriva fora do lock e publica com conferência da origem e compare-and-set do snapshot; conserva eventos diretos vigentes e a autoridade anterior.
- Composição expõe callbacks explícitos para as publicações vinculadas; assinatura legada permanece compatível sem promessa de vínculo/atomicidade.
- Runtime interrompe a proposta recusada antes do próximo dispatcher/finalizador; a atualização posterior ao dispatch também leva a fonte capturada.
- A revisão identificou a fase técnica suprimida como outro consumidor do mesmo contrato. Um RED adicional demonstrou a alteração indevida da fase do novo turno após uma primeira publicação aceita; a conclusão técnica agora também usa o writer vinculado.

Produção desta entrega: `mente_laylay/cognicao/orquestrador_turno_runtime.py`, `mente_laylay/cognicao/composicao_turno.py`, `mente_laylay/autonomia/resposta_ia_runtime.py` e somente instalação dos callbacks em `laylay.py`. Nenhum executor de domínio ou algoritmo de mescla por intent foi alterado por este candidato. Nenhum commit.

### Validação e limites

Testes canônicos: `scripts/tests/test_publicacao_ocorrencia_turno.py`. Composição instalada: `scripts/tests/test_publicacao_ocorrencia_composicao.py`, em subprocesso com mutex real de identidade própria para preservar a sessão aberta.

Resultados intermediários: 140 contratos/composição existentes; 430 na seleção com vizinhos; 13 novos controles de composição. São seleções com sobreposição, não somar como contagem de casos independentes. A seleção inicial também encontrou oito REDs de proposta original da frente paralela; a seleção posterior ficou verde. Sua resolução não é atribuída à AUT-01.

Validação final do candidato:

| Nível | Resultado e alcance |
| --- | --- |
| Contratos locais | 35 testes do novo arquivo, incluindo a fase técnica; estado e validadores reais |
| Composição principal | 13 testes novos; callbacks instalados e o próprio `root._resposta_ia_runtime`, com portas externas isoladas |
| Seleção com vizinhos | 446 aprovados em 13,64 s após o refinamento técnico |
| Regressão ampla final | 8.975 aprovados, um ignorado e 56 subtestes aprovados; zero falhas, em 202,48 s |
| Integridade | `git diff --check` limpo; HEAD preservado; hashes dos quatro arquivos de produção conferidos estáveis durante a suíte final |

Uma suíte ampla anterior ao refinamento técnico passou em 8.972 casos; ela não foi usada para certificar o candidato final. A repetição acima inclui o refinamento e os testes disponíveis na worktree ao coletar. Mudanças paralelas de proposta original foram preservadas, sem atribuir seus ganhos a esta raiz. Os totais não representam exclusivamente testes novos da AUT-01.

Os testes usam estado, validador e callbacks compartilhados reais, com transporte, execução externa e fala isolados. A sonda usa o objeto de resposta realmente instalado; não substitui o owner compartilhado que verifica origem. Receipts sintéticos não certificam efeito físico, e essa prova de composição não valida o loop da sessão aberta. A suíte foi executada com mutex real de identidade própria para não disputar a sessão de Pedro.

Snapshot final de produção para retomada (SHA-256):

| Arquivo | SHA-256 |
| --- | --- |
| `orquestrador_turno_runtime.py` | `CB23BDECDFDE5EDA565E0A441726B3F5686AB484DF9B8DFE316400098D7A1944` |
| `composicao_turno.py` | `24EAACD3AF6DB6AD0A045CDCA2648FE1D0A8C704BD3DDD7D6D5C905F2E80FCDB` |
| `resposta_ia_runtime.py` | `BBE72013004E2084B3C1647AA8C323D79765D330E30C468174F94638BBC64AE1` |
| `laylay.py` | `D4753570519B53126D8E9466A88591E13825DD4AA437B9814095E946691C1601` |

AUT-01 continua parcial: mescla por intent, publicação de resultado pelo adaptador de execução, rotas locais/legadas sem ocorrência, janela entre a publicação aceita e o início do executor/fala e revalidação no limite do efeito ainda precisam de investigação própria. Não estender o candidato cegamente, nem fundir essas pendências com autoria emocional. Próxima fronteira a selecionar pela primeira divergência real após este checkpoint.

## 10. Checkpoint AUT-01 — admissão após publicação aceita, 06/10/2026

### Reconciliação antes do candidato

Retomada em `main`, HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, worktree paralela preservada. O checkpoint 9 é histórico: a correlação por solicitação, a procedência da leitura semântica e a conclusão local receberam candidatos em outras frentes depois dele. Não reaplicar nem atribuir esses candidatos a esta entrega. O registro central contém suas provas e limites.

Revalidação atual: 26 testes de `test_mescla_receipts_solicitacao.py`; 75 de identidade/correlação/composição/diagnóstico; 33 de procedência semântica. Todos passaram, com seleções sobrepostas. A nota antiga de que o writer ainda mesclava por intent está superada pelo código atual.

### Primeira divergência e contrato

Publicação vinculada aceita → montagem do contexto ou execução do primeiro comando → nova ocorrência coerente → dispatcher inicia comando antigo ou finalizador recebe a resposta antiga. O writer posterior recusa a publicação, mas essa recusa ocorre depois da admissão indevida.

Falsificadas: falha necessária do writer (a primeira publicação é legítima e a posterior recusa); necessidade de frase diferente (a intercalação usa a mesma frase e outro ID); falha geral do executor (três controles da ocorrência vigente iniciam normalmente as etapas). Não há evidência de que esta intercalação controlada seja a autora da perda de plano histórica `55ee6435...`.

Contrato: publicação aceita não congela a ocorrência. O owner do turno confere um snapshot único com `motivo_divergencia_ocorrencia_principal`; o orquestrador consulta essa conferência depois de montar os contextos; o dispatcher consulta a mesma conferência antes de cada comando. Só `True` explícito admite a etapa; falha, callback malformado e retorno incerto interrompem. Identidade não concede autoridade nem confirma efeito.

### Escopo aplicado

- `mente_laylay/cognicao/composicao_turno.py`: `proposta_vigente`, somente leitura do snapshot real e reuso do contrato canônico.
- `laylay.py`: instalação de `proposta_principal_vigente` no contexto da resposta.
- `mente_laylay/autonomia/resposta_ia_runtime.py`: admissão após montagem do dispatcher/finalizador e passagem de closure ligada à fonte capturada.
- `mente_laylay/autonomia/dispatcher_comandos_json.py`: interrupção dos comandos restantes quando a conferência recusa; alcança portas canônicas e legadas da lista.

Nenhum executor de domínio, parser, receipt, autorização ou política de aprendizado foi modificado por este candidato. Contextos legados sem a nova chave continuam compatíveis, sem promessa de conferência. Nenhum commit criado.

### Evidência e limites

`scripts/tests/test_admissao_proposta_vigente.py`: antes do candidato, 16 REDs e três controles GREEN. Nove falhas atingiam a admissão depois da troca, seis atingiam a guarda ignorada e uma cobrava a nova API de composição. Depois do candidato: 31 GREEN, sendo 19 locais e 12 da composição instalada em aplicativos, IoT e navegador.

A composição importa `laylay.py`, usa o runtime, validador, writer, estado e dispatcher realmente instalados, com SQLite temporário e mutex real próprio. Somente transporte, executor externo e finalizador/fala são portas controladas. Dois erros da primeira versão da sonda foram corrigidos: asserções deslocadas para outro teste e formato IoT flat recusado antes da fronteira desejada. A sonda IoT passou a usar a intenção canônica, sem alterar o validador. Essas falhas de sonda não contam como REDs de produção.

Gate com vizinhos: **600 aprovados e 10 subtestes**, 41,67 s. Regressão ampla da revisão final: **10.161 aprovados, um ignorado e 56 subtestes**, nenhuma falha, 499,80 s. XML em `.pytest_cache/aut01_admissao_ampla.xml`. Manifesto em `.pytest_cache/aut01_admissao_hashes.json`: 222 arquivos Python acompanhados, hashes iguais antes/depois da suíte e novamente conferidos depois. HEAD/branch preservados e `git diff --check` sem erros. Totais abrangem a worktree inteira, incluindo alterações paralelas; não são ganhos exclusivos deste candidato.

AUT-01 permanece parcial. Esta conferência não mantém lock durante efeitos externos, não cancela uma ação já iniciada, não impede uma troca entre a leitura e o efeito dentro de um executor e não certifica som, GUI ou dispositivos físicos. Revalidação da autoridade no próprio limite do efeito, resultado tardio de ação em curso e finalização que chama modelo/fala depois da admissão mantêm investigação própria. Nenhuma raiz histórica foi encerrada por esses controles.

## 11. AUT-08 — piloto autorizado de fala e execução concorrentes, 22/10/2026

Pedro autorizou iniciar um objetivo pequeno com duas habilidades e validar no
runtime real. Entrega: texto copiado para arquivo novo, reaproveitando quadro,
governança, ciclo/executor canônicos, execução silenciosa e receipts observados.
Progresso e conclusão são emissões distintas; esperar pelo início do áudio não
conserva autorização. Revalidar antes do efeito; falha de voz não bloqueia a ação.

No ensaio instalado final, com memória isolada e clipboard/disco/Edge TTS reais,
o arquivo foi observado com hash correto enquanto tocava o anúncio; a conclusão
também teve reprodução confirmada. Controles reais de cancelamento, troca de
turno, indisponibilidade do destino e modo silencioso preservaram os contratos.
21 testes locais novos e uma regressão instalada; seleção de 325 GREEN. Ampliada:
552 GREEN, dois REDs independentes de estrutura composta e um controle de
serialização desmarcado, todos registrados com contraprovas delimitadas.

Detalhes, hashes, limites e reprodução:
`artifacts/fala_execucao/RELATORIO_20261022.md` e
`scripts/validar_fala_execucao_real.py`. TTS teve HTTP 429 intermitente, sem mudança
de voz. Não se declara autonomia geral, objetivos persistentes ou encerramento
das demais raízes. Nenhum reinício da sessão desktop existente, nenhum commit.

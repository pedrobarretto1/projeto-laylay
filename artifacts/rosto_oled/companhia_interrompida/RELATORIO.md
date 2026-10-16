# CORPO-CANCELAMENTO-01 — cancelamento da ocorrência revogava a sessão

Base: main, HEAD d850b8c90cc5ce40bd4832e759ed991ba88cd5cc. Worktree já modificada; arquivos causais anteriores ao candidato em baseline/. Nenhum commit.

## Evidência e primeira divergência

Sessão real 8c561642: DEV mostrava companhia inativa, vigia falsa e intenção interagir/interrompida. SQLite registra proteção rearmada às 21:42:43 e gesto atencao_conversa_v1 não confirmado às 21:42:46, com zero movimentos confirmados. Leituras e alertas continuavam chegando depois. Logs resumidos omitiam a razão do owner; mostravam apenas conversa_em_andamento da intenção antiga.

Isso prova a revogação, mas o receipt bruto daquela falha histórica não foi preservado. Não é possível afirmar qual guarda exata a causou naquela sessão.

Reprodução controlada no root real + COM4: estímulo de diagnóstico marca fala em andamento e encerra essa fala imediatamente antes da expressão motora. Rosto confirmou antecipação; transporte recusou EXPR por expressao_sem_sessao_ou_causa, sem transmitir MOTOR. Owner interpretou como falha elétrica, revogou a companhia inteira e deixou de renovar SENTRY. Prova anterior em runtime_causa_antes.json, companhia=False em 4,280s.

Fronteira: retorno da guarda de EXPR → classificação do resultado pelo owner da companhia. Mudar a causa de uma ocorrência não equivale a revogar a autorização da sessão. O caminho de pausa antes do motor já distinguia os casos; a guarda de EXPR não devolvia essa distinção ao mesmo owner.

Controles concorrentes: ensaio anterior runtime_antes.json confirmou três MACK/SACK na mesma placa, descartando indisponibilidade geral de motor no período. Mesma identificação de boot nos ensaios; não houve necessidade de regravar firmware. Companhia realmente inativa falsifica a explicação de mero descanso ou prioridade transitória como causa suficiente do silêncio persistente. Falhas intermitentes de comunicação permanecem separadas em CORPO-I2C-01.

## Candidato e contrato

Produção alterada neste candidato:

- mente_laylay/autonomia/companhia_corporal.py: quando EXPR recusa a guarda, revalida a concessão e a causa. Somente uma concessão ainda vigente com causa encerrada classifica cancelamento. Mantém retorno sem sucesso, STOP e experiência interrompida; não repete gesto. Preserva também o motivo do receipt da etapa no resultado, antes de STOP limpar o diagnóstico corrente.
- mente_laylay/integracao/dev_console_runtime.py: expõe motivo do owner e motivo final da intenção, preserva detalhe do receipt e registra mudança da companhia sem logs por medição.
- cliente/terminal_2/desenvolvedor.py: mostra estado da companhia no painel Corpo. O diagnóstico existente passa a mostrar a causa concreta.

Firmware, PWM, autorização manual, preferência persistente e gates de segurança não foram alterados por este candidato. Falta de MACK/EACK real, STOP/manual/desativação e perda de sessão continuam caminhos distintos; cancelamento não é sucesso.

Princípio reutilizável: autoridade da sessão, validade da ocorrência e confirmação do executor são estados diferentes. Aplica-se aos gestos de qualquer habilidade, fala ou emoção que usa o mesmo owner; não há exceção por frase ou emoção específica.

## Validação

- RED: três testes nas fases antecipação, expressão e acomodação falhavam exatamente por companhia=False após mudança de causa. GREEN após candidato.
- RED DEV: consulta não expunha motivo_companhia. GREEN após candidato e sanitização pelo bridge.
- 45 testes focados de presença, interrupção, proteção e reconexão passaram.
- 46 testes de DEV, nova interrupção, episódios e continuidade passaram.
- Regressão final: 247 passed, 2 deselected em 73,70s. Excluídos: receipt instalado de ativação já conhecido e teste de preferência contaminado pelo ambiente carregado por imports da raiz. Preferência passou isolada, 1 passed. Três outros REDs de receipts instalados na regressão ampliada original também falharam com módulos anteriores ao incremento sensorial; evidência em ../experiencia_sensores/baseline_receipts.txt. Não foram corrigidos nem chamados GREEN.
- USB posterior runtime_causa_depois.json: mesmo estímulo, zero MOTOR do PC, companhia e vigia permaneceram ativas após cancelamento; vários novos incidentes dos sensores na mesma sessão. STOP final confirmado e serviços encerrados.
- Pedro confirmou: “Sim, voltaram a reagir”. Rodas suspensas; não prova navegação ou antiqueda em deslocamento.
- Renderização Qt do painel inspecionada em dev_diagnostico.png (dados de teste, não sessão real); campos de motivo e falha legíveis. Apenas uma linha redundante de detalhe foi retirada depois; o diagnóstico existente mantém a informação.

Laylay encerrada durante diagnóstico e não reaberta. Preferências de companhia/passeio preservadas para a próxima abertura pelo usuário. Validação prolongada de uso diário ainda não realizada; não concluir que qualquer outra causa de silêncio/reset foi eliminada.

## Relato posterior do mesmo dia

Pedro testou novamente e informou que o problema persistia. SQLite da sessão f52f01ed trouxe uma razão concreta diferente: sem_confirmacao_pwm às 23:06:20 após rearmamento da parede. A correção de cancelamento de fala acima permanece limitada ao seu RED; não resolveu esse segundo mecanismo. A investigação continuou em CORPO-ADMISSAO-PROTECAO-01, com reprodução do silêncio e de MOTOR_OCUPADO durante reflexo real, novo firmware e validação do main completo. Ver ../admissao_motor_reflexo/RELATORIO.md. Não apagar nem reinterpretar o primeiro resultado como prova global.

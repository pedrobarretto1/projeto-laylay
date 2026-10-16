# Experiência corporal contínua, aprendizado e condição no raciocínio

Pedido: aplicar as ideias guardadas; Pedro escolheu incluir condição corporal no raciocínio, além de experiência e aprendizado. Sensores futuros permanecem fora deste incremento.

Base: main, HEAD d850b8c90cc5ce40bd4832e759ed991ba88cd5cc, worktree modificada preservada. Baseline em baseline/. Nenhum commit criado; nenhum firmware, PWM, duração máxima, perfil ou concessão salvo foi alterado.

## Fronteira demonstrada

Pedidos manuais e gestos causais recebiam confirmações, mas não publicavam experiência corporal. Somente propostas corporais da LLM devolviam experiência. RED canônico: dois casos atingiram PWM/parada confirmados e falharam na experiência ausente (red.txt). Isto falsifica ausência geral de execução ou falha geral do estado compartilhado.

O candidato acrescenta um owner de experiência na memória mental, instalado no owner do corpo, reutilizando estado compartilhado, motor de aprendizado, SQLite e coordenação existentes. Pedido manual, gesto espontâneo e proposta da IA percorrem o mesmo registro final. A proposta ainda conclui somente seu próprio plano por identidade/vigência. Histórico transitório de 12 ocorrências mantém origem, turno, sessão, gesto, variante, PWM/tempos pedidos, confirmações e interrupções. O retrato do modelo usa somente três resumos recentes.

Cada ocorrência nasce antes do executor; nenhum receipt antigo é promovido a autorização. Experiência confirma PWM/parada elétrica, nunca deslocamento. Exceção, falha parcial e cancelamento são distintos; falha de memória não altera receipt do motor. Registros técnicos persistidos no aprendizado são deduplicados por ocorrência. Recuperação restaura observações, sem restaurar concessões.

## Aprendizado e ligação com a conversa

Qualificação literal de avaliações corporais foi acrescentada ao interpretador compartilhado, sem parser privado de sim/não. Exemplos: "gostei desse movimento", "não gostei desse gesto", "esse movimento ficou muito forte". Repetição é observação; não aciona motor pelo canal de aprendizado. Elogio geral, música, pergunta, relato e metalinguagem não são preferência corporal. Nenhum silêncio é interpretado como avaliação; este incremento não solicita feedback que pudesse qualificar silêncio.

O adaptador de conversa vincula o feedback à experiência capturada no retrato do próprio plano, não ao último gesto que possa ter ocorrido enquanto a resposta era gerada. Exige texto e turno atuais, sessão e experiência recente (60s). Uma avaliação contextual não vira preferência durável imediatamente. Variantes são selecionadas somente quando a maturidade compartilhada permite aplicar a preferência, respeitando o perfil e todas as concessões/oportunidades existentes. Recusa é evidência da direção evitar; uma hipótese distinta evita tratá-la como falha de uma preferência positiva. Se todas as variantes de uma família forem evitadas com maturidade, não há gesto espontâneo dessa família. Pedidos manuais atuais continuam pelo executor autorizado.

O teste da composição instalada encontrou uma fronteira adicional: o registro filtrado dos adaptadores não injetava o owner corporal. Foi adicionada somente essa dependência à composição. Uma fixture anterior também não possuía confirmação real de sessão/OLED; foi substituída pelo transporte completo sobre dispositivo serial externo simulado, mantendo a guarda de produção.

## Condição e raciocínio

O retrato compartilhado informa condição atual (pronta, desconectada, controle indisponível ou acionamento em andamento), histórico e aprendizado, mantendo percepções físicas como não medidas. Está presente na autoria principal e na realização factual existentes; catálogo vivo descreve experiência e avaliações naturais. Não há outro cérebro no ESP.

Na primeira consulta ao modelo configurado, a frase "não houve deslocamento" foi mais forte que os receipts. Refinado o contrato: ausência de prova significa não medido, não inexistente. Também foi corrigida a projeção de pertence_ao_turno_atual a cada leitura, preservando a ocorrência histórica. A consulta seguinte respeitou a incerteza, mas copiou dados do retrato até truncar o JSON. Refinada a separação entre contexto de entrada e schema de saída, sem retirar fatos ou aumentar orçamento. A consulta final retornou JSON válido, descrevendo "Não medi o deslocamento" e confirmação elétrica. Intenção vazia não é materializada nem executada.

## Provas e limites

- 88 testes focados de experiência, proposta, composição e continuidade verdes: pytest_focado.txt.
- Corpo, companhia e presença: 143 verdes (pytest_corpo.txt).
- Aprendizado e maturidade: 37 verdes (pytest_aprendizado.txt).
- Som/atividade/rosto: 100 verdes; decisão isolada: 14 verdes, em pytest_som.txt e pytest_decisao_isolada.txt. A execução conjunta anterior trouxe uma interferência conhecida de perfil rodas_suspensas contra configuração padrão bancada; não se alteraram configurações nem a asserção para ocultar isso. Não declarar suíte global verde.
- USB real: pedido natural de frente pela composição instalada, gesto causal alegre e feedback explicitamente simulado em SQLite temporário passaram. Quatro confirmações MACK, paradas, olhos e registros foram coletados. Histórico manual e espontâneo chegou ao mesmo owner; condição foi pronta e depois desconectada. Firmware atual permaneceu intacto.
- Emoção e feedback da sonda foram estímulos diagnósticos; não representam sentimentos ou preferências reais de Pedro e não foram persistidos na memória de aprendizado do usuário. Consulta ao modelo real não executou sua proposta.
- receipt_primeiro_ensaio.json preserva a primeira saída com alegação indevida; receipt_fisico.json preserva o ensaio revisado com resposta truncada. consulta_modelo_revisada.json registra a consulta final válida com observações anteriores da sonda e condição viva. Nenhum motor foi enviado nessa última consulta.
- ACKs não provam deslocamento físico, tato ou percepção ambiental. Uso prolongado e avaliação subjetiva de carisma permanecem observação futura.

Produção: novo experiencia_corporal_runtime.py; corpo_motor_runtime.py; companhia_corporal.py; modelo_corporal.py; interpretador_continuidade.py; adaptadores_aplicacao_runtime.py; composicao_estado_aplicacao.py; disponibilidade_operacional.py; mapa_habilidades.py; duas linhas de composição em laylay.py. Mudanças paralelas de música, semântica, som, firmware e UI foram preservadas.

Contrato reutilizável: executor origina ocorrência → efeito/receipt → experiência com proveniência → aprendizado qualificado → projeção para decisão. Experiência e preferência fornecem evidência; autoridade continua no turno/concessão e no executor.

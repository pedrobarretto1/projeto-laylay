# Resultado operacional observado → bip

Base: main, HEAD 2566b621d2c8ee88ff7086c6c36019da85c8a4cd. Worktree já modificada; estado e arquivo anterior preservados em baseline/. Nenhum commit criado.

Ao encerrar a verificação, o HEAD havia avançado externamente para d850b8c90cc5ce40bd4832e759ed991ba88cd5cc. A base histórica acima foi preservada; o diff direto contra o arquivo salvo continua identificando apenas o candidato sonoro descrito aqui.

## Raiz demonstrada

O owner compartilhado publica sucesso/falha atuais, mas o consumidor sonoro consumia a ocorrência antes de verificar o intervalo de dois segundos. Uma ocorrência recebida nesse intervalo era perdida. Além disso, em companhia com rodas suspensas, o sucesso aguardava uma coreografia; a prioridade de tarefa no PC podia impedir essa coreografia até o resultado expirar.

REDs canônicos antes da alteração: sucesso e falha recentes consumidos sem SOUND durante o intervalo; sucesso com companhia/rodas suspensas não emitido pela sincronização comum. Os testes usam owner de atividade e composição reais, substituindo somente a porta serial externa. Comunicação e capacidade SOM1 foram confirmadas na placa real; a primeira sonda usou uma intenção diagnóstica fora do catálogo e foi corretamente recusada como sucesso. Ela foi corrigida para FILE_READ, correspondente à leitura local realizada, sem alterar catálogo ou guardas de produção.

## Contrato e candidato

Único arquivo de produção alterado: mente_laylay/especialistas/rosto_oled_runtime.py. Ocorrências recentes e certificadas podem aguardar até 2,5 segundos para o intervalo sonoro liberar. Há no máximo um sucesso e uma falha pendentes; falha prevalece no conjunto acumulado. O prazo não é renovado pela amostragem. Resultados não dependem da oportunidade de mover os motores; a sincronização emocional por coreografia continua disponível.

Consumo acontece antes da tentativa efetiva, evitando repetição de um som cujo ACK se perdeu. Expiração, origem inválida e troca/fechamento da sessão descartam pendências. Diagnóstico publica tipos pendentes. O bip nunca confirma a ação original e não concede autoridade de movimento.

## Evidências

- 18 testes de som passaram, incluindo espera por intervalo, prioridade no PC, confirmação perdida, reconexão, origem inválida, expiração e falha parcial.
- 167 testes de companhia/corpo passaram: pytest_corpo.txt.
- 130 testes de som, rosto, falha visual, atividade e presença passaram em processo separado: pytest_som_visual.txt. São 297 casos verdes quando as duas famílias não compartilham o estado contaminado pelo teste histórico de volume.
- A execução conjunta inicial teve 296 passes e uma falha por interferência de estado entre testes: pytest.txt. O par mínimo falha tanto com o consumidor sonoro anterior quanto com o atual: interferencia_baseline.txt e interferencia_atual.txt. O teste de companhia sozinho passa, e o conjunto de som com esse mesmo teste também passa (19). Não foi alterada a produção de repetição de comandos nem enfraquecida sua asserção.
- Sonda de composição instalada: leitura real de arquivo existente → sucesso, leitura de caminho inexistente → FileNotFoundError/falha. Owner e getters reais, USB COM4 real. SOUNDACK recebido para acordar (0), sucesso (1) e falha (2), com cerca de dois segundos entre os envios; nenhum MOTOR/MOTOR2, nenhum replay. receipt_fisico.json registra a trilha. A sonda não percorre a classificação de linguagem natural; o teste do executor instalado cobre publicação pelo ciclo real.
- Confirmação serial prova aceitação pelo firmware. Pedro depois relatou um teste próprio funcionando: "eu testei aqui e deu certo chat". Não acompanhou a sonda acima; a confirmação do teste próprio não é atribuída retroativamente à gravação dessa sonda.

Testes alterados: scripts/tests/test_som_corporal.py. Sonda: scripts/validar_som_resultados_fisico.py. Firmware não precisou ser regravado. Interface da Laylay não foi aberta.

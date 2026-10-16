# Sinal sonoro de envio sem observação do efeito

Base preservada: main, HEAD d850b8c90cc5ce40bd4832e759ed991ba88cd5cc; worktree previamente modificada. Arquivos anteriores e status em baseline/. Nenhum commit criado.

## Primeira fronteira e evidência real

Pedro relatou falta de bip em "despausa a musica". O Dev Console da aplicação aberta mostrou às 16:57:04.239 a entrada, às 16:57:04.362 a tecla nativa play/pause e às 16:57:05.711 o receipt MEDIA_CONTROL/midia_play, executou=True, confirmado=None, origem=executor, id=df563abe60e141998e83c49f735f7543. A resposta foi "Pedi pra música continuar". Nenhum controle de música foi enviado pelo diagnóstico de leitura da interface.

O owner de atividade distinguia sucesso confirmado e falha, mas não publicava envio sem confirmação. Ausência de sucesso nesse caso era uma guarda correta; a lacuna era um sinal neutro separado. Este mecanismo difere da perda por cooldown documentada no relatório pai, cuja correção foi preservada.

Controles falsificaram classificação ausente e receipt não publicado: reprodução pela composição instalada alcançou ambos. Após ajustar a fixture para substituir o serviço externo através dos registros reais (serviços estáticos eram sobrescritos pela composição), os seis casos de sucesso/falha passaram e os três casos de envio falharam exatamente na publicação do evento: red.txt. A primeira tentativa de fixture não conta como RED canônico.

## Contrato

Receipt tipado do executor, identificável, ok=True/executou=True/confirmado=None e evidência disponível → evento transitório de envio no mesmo owner. Não altera o receipt, não concede autorização, não confirma efeito e não promove ACK dos próprios motores. Eventos por ocorrência são deduplicados; um lote com falha não sinaliza envio nem sucesso total. Um lote com efeito confirmado e etapa apenas enviada sinaliza envio, preservando os receipts independentes.

Rosto consome envio através do intervalo e descarte existentes. SOUND tipo8 exige ENVIO1 negociado por SENCAPS; firmware antigo continua com os sons anteriores. Nota neutra de 1550Hz/80ms, GPIO6/canal4/duty128, resistor existente; potência não aumentada. Melodias de sucesso/falha preservadas. O catálogo vivo explica a distinção.

## Escopo

Produção alterada neste incremento: atividade_operacional_runtime.py, rosto_oled_runtime.py, mapa_habilidades.py, firmware rosto_laylay.ino e som_expressivo.h. Documentação SOM_OLHOS.md atualizada. Não houve patch de executor musical, modelo, classificação, autoridade ou perfil de motores. Ideias futuras foram apenas guardadas em melhorias e planos/ideias/CORPO_COMO_PARTE_DA_LAYLAY.md e em nota de memória expressamente solicitada.

## Validação e limites

- 57 testes focados verdes: owner real, composição instalada, palavras do usuário e variantes, envio/sucesso/falha, lote parcial/misto, deduplicação, capacidade viva, firmware antigo e cooldown.
- 187/189 casos verdes na regressão conjunta. Os dois REDs são interferências já observadas: volume42 deixado por teste anterior e perfil rodas_suspensas carregado pela composição antes da configuração isolada. Contraprova em memória com ambos os arquivos anteriores ao candidato reproduziu exatamente os mesmos dois REDs (187/189), sem alterar arquivos de produção: pytest_baseline_controle.txt. Companhia isolada78 e decisão isolada14 verdes. Não declarar suíte global verde.
- Host som/olhos e expressõesV3 verdes. A primeira adição ao host reutilizou uma sessão/seq já consumida, sendo corretamente recusada; o teste passou a abrir outra sessão. A guarda de replay não foi enfraquecida.
- Firmware USB/Wi-FiOFF/motoresON/limite5000 compilou (395364bytes, globals17444), gravado COM4 com hash verificado. Pinagem e parâmetros motores preservados.
- Sonda física reutiliza composição/owner instalados e leituras de arquivo reais para sucesso/falha; envio8 foi diagnóstico direto do transdutor, sem fabricar receipt de ação no PC. ENVIO1 e SOUNDACK0/1/2/8 confirmados; nenhum MOTOR enviado; STOP/GOODNIGHT finais registrados em receipt_fisico.json. ACK prova aceitação/início, não audição humana.
- Laylay reaberta com os arquivos atuais. Pedro confirmou o teste cotidiano de "despausa a música": "Sim, ouvi o bip". Esta confirmação fecha a validação auditiva desse caminho; não confirma o estado final do player nem é atribuída retroativamente à sonda de diagnóstico direto. O bip permanece neutro de envio.

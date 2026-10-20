# CORPO-DECISAO-V1 — latência da reação observada, 17/10/2026

Baseline: main, ca592a9609dd1865b63b22c714f8d3e802fa2a5c. Worktree já
continha os candidatos anteriores de transporte, companhia e comentários.
Alterações paralelas nos testes de explicação/motivo histórico preservadas.

Primeira divergência: a observação já publicada na experiência compartilhada
aguardava a próxima execução do Diretor, cujo ciclo padrão é de 15 s. Nos
registros reais da sessão ba710e67, cognição -> fila levou 7,317 s e 5,895 s;
fila -> publicação textual levou cerca de 1,132 s na primeira ocorrência.
Portanto reduzir o cooldown de frequência não elimina a latência de reação.
O modelo e a reprodução são fronteiras distintas do timer de observação.

Contrato aplicado: publicar fato novo sinaliza um threading.Event sem payload
ou autoridade. A mesma thread do Diretor acorda, relê o owner e atravessa as
mesmas portas de vigência, cognição, orçamento, autoria e voz. Não há modelo,
callback de fala ou rede executados na thread de sensores. Sinais acumulados
convergem no fato mais recente; um sinal durante autoria não é perdido. Sem
candidato válido, o sinal não gera fala nem ativa uma rotina cotidiana.

Rotina e feedback de silêncio conservam a cadência de 15 s. O intervalo mínimo
de 60 s dos comentários e as recusas/atividade humana permanecem intactos.
Encerramento interrompe a espera em até o tick de 250 ms, sem deixar thread
presa no antigo intervalo. O sinal só é emitido depois da publicação no estado.

Produção deste incremento:
- experiencia_corporal_runtime.py: sinal depois de um marco novo ou fase IMU
  expressiva publicada; amostra idêntica não gera nova notificação.
- diretor_presenca.py: notificação opcional para qualquer produtor observado;
  separação entre ciclo observado e ciclo cotidiano, mantendo uma thread.
- laylay.py: uma ligação de composição ao sinal do owner corporal existente.

Sem mudanças de modelo, voz, prompt, token budget, firmware, motores ou novas
permissões. Nenhum commit criado. A sessão já aberta por Pedro foi preservada;
precisa do próximo início para carregar os novos objetos Python.

Provas:
- RED: fato novo ficou preso no ciclo, não reagindo dentro de 600 ms.
- GREEN focado/regressivos: 86 passaram, incluindo início rápido, coalescência
  durante autoria, sinais sem candidato, prioridade humana, encerramento,
  callback vinculado ao owner e composição realmente instalada.
- validar_latencia_observada.py importou a composição instalada, manteve o
  modelo real e isolou somente observação física controlada e saída de áudio.
  Publicação -> cognição: 0,0025 s. Modelo iniciou em 0,1031 s e terminou em
  4,1356 s. Proposta agendada em 4,1398 s, fila com um item. Prompt preservado
  com 17.251 caracteres. Sem hardware, motores, GUI ou áudio reproduzido.

Limites: essa medida é um ensaio controlado, não o tempo do manuseio físico
até a audição de Pedro. Leitura do hardware, contenção/carga do modelo, timer
da fila e síntese/reprodução ainda acrescentam tempo. Não se promete resposta
instantânea, fala a cada evento, nem a mesma latência sob carga. O tempo de
geração restante pode ser estudado sem remover evidência ou personalidade do
prompt; esse incremento remove a primeira espera artificial comprovada.

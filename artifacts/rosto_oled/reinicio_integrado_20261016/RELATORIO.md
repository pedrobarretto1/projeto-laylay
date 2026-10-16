# CORPO-I2C-01 — motores, companhia e frontal — 16/10/2026

Base: main, HEAD d850b8c90cc5ce40bd4832e759ed991ba88cd5cc, worktree
modificada preservada. Perfil integrado USB gravado na etapa anterior, sem
nova gravação ou patch de produção nesta investigação. Mesmos motores,
proteções130/100mm, IMU e ToFs. Nenhum commit criado.

## Evidência causal

1. Consulta inicial somente leitura: boot124efe66, uptime24580447ms, motivo1
   (ligação de energia); MPU PRONTA, distâncias frontal e inferior inválidas.
   Isso não mostra reinício recente no começo do ensaio.
2. Após ajuste de cartão, inferior válido, frontal inválido, risco NENHUM.
   Repouso:22/22 sincronizações. Leitura frontal inválida recente é ausência de
   distância confirmada, não evidência de parede livre ou de parede próxima.
3. Pelo mesmo RostoOledRuntime real: esquerdo160/0 por650ms, direito0/160 por650ms,
   frente160/160 por1000ms e giro160/-160 por700ms. Todos tiveram receipt de PWM
   e parada. Boot124efe66 permaneceu igual nas quatro etapas. Pedro confirmou
   visualmente movimento e parada. Parada final confirmada e serial fechada.
4. Ensaio de parede não iniciou vigia nem movimento: frontal ainda INVALIDA,
   inferior26mm. A primeira fronteira RED era a medição, não a coreografia.
5. Pedro abriu a aplicação normal e pediu acompanhamento no modo companhia.
   Leitura pela interface DEV→CORPO, sem segunda conexão serial. Registros
   mostram descanso, exploração, reações de borda e retomada após interrupção.
   Às05:18:18, erro de sincronização serial tipo ValueError; reconectada às
   05:18:23 e reações retomadas. Resumo disponível registra seis perdas de sessão,
   última I2C, zero reinícios observados pela aplicação. Não há receipt bruto do
   pacote que causou ValueError; não atribuir a exceção a um parser específico.
6. Instrumentação visual tem limite: árvores de acessibilidade retornaram
   resumos repetidos mesmo com alterações visuais. dev_companhia.json e
   dev_frontal.json são snapshots públicos, não uma série temporal garantida
   de amostras novas. Não usá-los para provar estabilidade a cada intervalo.
   Nenhuma autenticação da ponte foi contornada; nenhum cliente substituiu a UI.
7. Pedro confirmou que o frontal voltou a detectar a parede e houve reação.
   Em seguida confirmou que havia desligado/reconectado a alimentação. Não
   houve troca de fios ou firmware feita pelo agente para recuperar o frontal.
   Recuperação após religar não prova causa elétrica específica.
8. Consulta final, após encerrar aplicação: STOPPED1; boot33728a23, uptime147319ms,
   motivo1. Esse novo boot foi explicado pela reconexão manual confirmada por
   Pedro. Não é evidência de reinício espontâneo durante a companhia. Inferior
   válido26mm, frontal inválido nessa consulta final (sem confirmação de alvo
   ainda mantido), MPU PRONTA. Serial fechada; nenhum Python da Laylay restante.

## Estado e limites

Motores e reação à parede confirmados por Pedro. Perda por I2C observada no
runtime normal; causa física ou de firmware ainda não isolada. O reinício
espontâneo relatado anteriormente não foi reproduzido com prova neste ensaio.
O novo boot final foi manual. Não declarar CORPO-I2C-01 encerrada, nem mudar
clock, limiares, autoridade ou política de recuperação para esconder o sintoma.
Possível inconsistência em receipt sob falha requer captura bruta antes de
qualquer candidato. Nenhuma alteração de produção feita.

Interface fechada pelo botão Fechar; o núcleo continuou ativo em segundo plano.
Processo exato da sessão12592, com caminho verificado, foi encerrado; consulta
serial posterior confirmou STOPPED1. Pedro relatou funcionamento aparentemente
normal ao final. Não foi necessário pedir troca dos módulos.

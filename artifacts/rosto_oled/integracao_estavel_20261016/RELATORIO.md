# Corpo integrado — estabilidade, objetivos e relato — 16/10/2026

Pedido de Pedro: começar pela estabilidade, seguir para objetivos curtos ligados
à mente preservando quietude, e comentários de acontecimentos corporais reais.
Durante a execução ele ficou indisponível para acompanhar: nenhum MOTOR/TURN
foi enviado. A interface normal não foi aberta; processos de diagnóstico
encerraram transporte com STOP/SACK e GOODNIGHT/NACK. Nenhum commit criado.

## Base preservada

HEAD/main: d850b8c90cc5ce40bd4832e759ed991ba88cd5cc. Worktree já continha muitas
alterações paralelas e arquivos de firmware não rastreados. Não houve reset,
restore ou limpeza. playlists.json permanece adicionado ao índice a pedido de
Pedro; .gitignore e configuração pessoal de pareamento foram preservados.
`usb_antes.json` conserva hashes do firmware/owner antes deste incremento.

## CORPO-I2C-01: fronteiras reproduzidas, causa física ainda aberta

Não atribuímos o reset/travamento histórico a CPU, tamanho do programa, bateria
ou a um parser específico. O ensaio anterior tinha falha de sessão I2C sem novo
boot e uma ValueError sem pacote bruto. A hipótese inicial de que erro IMU
publicaria manuseio válido foi falsificada: `recente()` já exige `!erro`.

Dois REDs específicos foram demonstrados no firmware real compilado com
fronteira de hardware simulada:

1. `processarConsultaImu` consultava millis em diferentes argumentos. Ao cruzar
   os 75ms, emitiu campos incoerentes: a asserção de estado/manuseio/fase falhou.
   O parser Python corretamente recusa essa combinação. Agora o receipt usa
   um instante único; o parser não foi enfraquecido. Isso prova o mecanismo,
   não que tenha causado a ValueError histórica sem pacote capturado.
2. IMU ausente ao iniciar nunca era reavaliada: a asserção de recuperação
   após nove segundos falhou. Agora falha persistente por 500ms inicia
   revalidação espaçada em pelo menos cinco segundos. Sessão/vigia são
   canceladas e ponte cortada ANTES das inicializações. IMU perde calibração
   antiga, VL53L0X são enumerados com XSHUT para evitar colisão, OLED pode
   reinicializar sem reboot. Só um novo handshake e novas amostras podem
   permitir iniciativa. Nenhum gesto antigo é reenviado.

Status óptico INVALIDA recente não aciona reinicialização elétrica. ToF sem
retorno não é promovido a distância válida, e borda inválida continua perigo.
Não foi adicionado reset cego do ESP ou mascaramento dos erros do barramento.

Host: oito executáveis e três casos adicionais passaram; ver
`firmware_host.txt`. Inclui snapshot, ausência/retorno da IMU, recalibração,
falha persistente e recuperação ToF, OLED ausente no boot, falta de retorno
óptico, cortes, sessão, STOP, proteção, som e transições de sono.
Hardware simulado não prova recuperação elétrica física.

Firmware integrado USB gravado na COM4, hash de upload confirmado:
SHA256 CF196486A5DA0A78C86C52FE582A01A34B45A6A4410FB263C1869A3FA7D0B9DC.
443516 bytes de programa; 19548 de globais. Mesmo perfil integrado anterior:
USB, motores de bancada habilitados, limite5000ms, som GPIO6, ToFs/proteção/IMU
ativos, Wi-Fi e teste isolado IMU desligados. Logs `arduino_compile.txt`/`upload.txt`.

Um minuto antes: 72 sincronizações, zero falhas, mesmo boot33728a23.
Um minuto depois: 72 sincronizações, zero falhas, mesmo bootc66d4280;
zero reinícios observados e zero perdas de sessão no novo boot. A mudança de
boot entre ensaios foi a gravação autorizada. IMU PRONTA, inferior26mm válida,
frontal INVALIDA/status4 (desconhecido). Nenhum movimento enviado; `usb_depois.json`
conserva trilha serial e STOP/SACK/GOODNIGHT/NACK finais.
Como o controle anterior também estava saudável, não concluir superioridade
estatística nem encerrar a causa física intermitente. Falta ensaio prolongado
acompanhado e recuperação durante uma ocorrência física real.

## CORPO-DECISAO-V1: propósito finito no mesmo owner

O decider existente continua escolhendo intenção com atividade do PC, emoção
causal, experiência e concessão. Não foi criado outro cérebro/parsing de IA.
Objetivo curto acrescenta propósito, causa, critério, prazo e estado, projetado
à mente e ao catálogo. Gesto: até30s para sua partitura finita e parada; observar
ou descansar:10–90s antes de reavaliar. Reconsultar o mesmo objetivo não renova
o prazo; nova avaliação vencida cria nova oportunidade sem fila de motores.
Concessão não prorroga prazo e resultado atrasado não conclui outro objetivo.
Confirmação por receipts exige ok e parada; não prova caminho/deslocamento.

RED: o retrato só tinha rótulo, e metadado vencido não era barrado. Também havia
uma divergência entre perfis: bancada podia executar fallback mesmo quando
o decider escolhia atenção/descanso. Agora toda decisão sem movimento encerra
a seleção naquele ciclo, em ambos os perfis. As proteções locais continuam
independentes; quietude não desarma borda.

Testes de fixture corrigidos com justificativa causal:
- Reset durante gesto herdava GUARD BORDA constante de um teste expressivo,
  embora DIST inferior=100. A fixture do ensaio agora declara NENHUM para
  alcançar MOTOR; não ignoramos risco em produção para fazer teste passar.
- is_speaking sem audio_playing é preparação, conforme contrato visual.
  O teste de gesto de fala usa reprodução efetiva; novo negativo prova
  quietude durante síntese. O comportamento antigo passava por fallback
  apesar da decisão atenta, exatamente a divergência corrigida.
- Teste de preferência em pasta temporária isola LAYLAY_CORPO_PERFIL pessoal.

## Comentários: oportunidade observada, cognição e entrega separadas

Além de manuseio já existente, a experiência pode propor um comentário por
incidente recente de obstáculo, borda ou perda de retorno inferior. Fonte é
o episódio DIST/GUARD registrado no owner compartilhado; não há comentário a
partir de memória recuperada, outra sessão ou amostra expirada. A idade usa
o início da detecção, sem rejuvenescê-la pelas fases posteriores. Oportunidade
não fala nem movimenta: passa por DiretorPresenca, cognição, autoria, guardião,
fila e porteiro existentes, com revalidação após modelo e na entrega.
Silêncio, orçamento, preferência e prioridade de interação permanecem válidos.

RED em corpo E rotina: o MotorIniciativa penalizava permanentemente chat aberto,
enquanto o porteiro já distinguia conversa ociosa. Regra de atividade fica no
módulo de prioridade compartilhado: fala/claims vigentes e entrada recente,
não apenas canal aberto. Motor, porteiro e callback do cliente local reutilizam
essa qualificação; turno vigente continua bloqueando chamada secundária.
Não demos prioridade interativa artificial ao corpo.

REDs negativos mostraram que instrução ao modelo não bastava para impedir
"recuei", "encontrei uma saída" e acusação sem medida. Guardião compartilhado
agora recusa essas alegações nesse contrato corporal. Um sucesso de detecção
não vira sucesso de fuga. Nenhuma frase local mascara falha de autoria.

## Validação e limites de entrega

- `regressivos_final.txt`:255 testes passaram (corpo, proteção, recuperação USB,
  decisão, continuidade de objetivo, experiência, IMU, presença, governança,
  identidade). Depois foram acrescentados negativos/catálogo; ver logs abaixo.
- `contratos_compartilhados.txt`:154 passaram (cliente real do modelo,
  prioridade/claims, preempção/flush de voz, corpo, governança e objetivos).
- `vizinhos_finais.txt`:176 passaram,1 excluído explicitamente. Inclui guardião
  TTS, companhia, fala, objetivos e manuseio. O excluído é receipt de concessão
  do root já vermelho com a lógica anterior em memória: `reds_anteriores.txt`;
  não foi mascarado nem atribuído a este incremento.
- `catalogo_relato_final.txt`:67 passaram nas novas fronteiras, sensores,
  manuseio, perguntas naturais e catálogo. Os conjuntos se sobrepõem: não somar.
- `composicao_real.json`:importou root instalado, usou MESMO owner/COM4, projetou
  objetivo ficar_quietinha na mente. Callback real do cliente liberou chat ocioso
  e bloqueou claim vigente. Modelo configurado respondeu à leitura atual:
  "O corpo estava em equilíbrio estável e tranquilo." Sucesso de geração,
  não entrega física de voz. Nenhum motor nem thread de companhia iniciado.
- Presença sensorial completa até fila/validador foi testada com fronteira
  serial simulada e owners reais. Não houve episódio novo provocado na placa
  nem audição de comentário espontâneo durante este trabalho; Pedro estava fora.

Não declara integração global terminada, estabilidade física resolvida ou
garantia antiqueda. MPU ainda não confirmado fixo ao corpo; não validamos
rotação/caminho físico. Nenhuma alteração no mapa de pinos ou preferências.

## Escopo deste incremento

Firmware: imu_corporal.h, sensores_distancia.h, rosto_laylay.ino e novo
recuperacao_perifericos.h. Python: decisao_corporal.py, companhia_corporal.py,
corpo_motor_runtime.py, modelo_corporal.py, experiencia_corporal_runtime.py,
prioridade_interacao_usuario.py, motor_iniciativa.py, porteiro_proatividade.py,
ponte_iniciativa_aplicacao.py, composição callback em laylay.py,
resposta_evento_runtime.py, guardiao_alegacoes.py, capacidades.py e mapa_habilidades.py.
Testes/artefatos e registros associados. Alterações paralelas restantes foram
preservadas. Nenhuma modificação de credenciais, playlist, voz configurada,
nome/pareamento USB, motores calibrados ou endpoints Wi-Fi.

Próxima prova física: uso acompanhado em companhia, observando reconexão após
uma falha real e comentários medidos sem interromper conversa. Não é necessário
começar por alterar a alimentação ou mover o corpo automaticamente.

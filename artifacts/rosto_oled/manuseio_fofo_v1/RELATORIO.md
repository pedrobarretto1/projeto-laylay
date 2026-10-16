# Manuseio expressivo e comentários corporais V1 — 15/10/2026

Base: main, HEAD d850b8c90cc5ce40bd4832e759ed991ba88cd5cc, worktree suja
preservada. Estado inicial em status_inicial.txt; cópias locais das fronteiras
principais em baseline/. Nenhum commit criado.

## Contrato e primeira fronteira

Continuação de CORPO-DECISAO-V1, não outra inteligência no ESP. Antes havia
classificação IMU e reação instantânea; não havia continuidade expressiva nem
produtor ligado ao diretor de presença. RED em host mostrou que inclinação
mantida não gerava desconfiança; RED do parser rejeitou a fase medida.

O ESP mantém a classificação e a sensibilidade aprovadas. Uma continuidade
finita sobre esses fatos escolhe curiosidade, desconfiança, susto/resmungo,
desorientação e recomposição suave. Memória de repetição expira em20s e limita3.
Olhos e bips existentes, sem aumentar potência ou conceder movimentos.

O mesmo owner USB transporta sequência/fase/idade/repetição. A experiência
compartilhada registra observações e oferece uma oportunidade por transição.
O diretor existente decide silêncio, orçamento e prioridade; coordenação usa
assunto da observação para distinguir fases, sem desativar deduplicação. A mente
produz contrato e direção social; a mesma autora escreve, com porteiro e receipt
de entrega. Não mede dor, colo, bateria, deslocamento ou intenção de Pedro.

Comentários são sobre episódio recente, no passado: mudar de postura não apaga
o fato que acabou de ocorrer. Sessão diferente, dado vivo ausente, observação
recuperada da memória ou idade maior que25s bloqueiam. Vigência é revalidada
depois da geração e na fila/publicação, sem confirmação fictícia de audição.

## Fronteira de transporte encontrada no runtime

O ensaio capturou respostas genéricas antes da fila. A compactação local tratava
o system final do evento como auxiliar, cortando para500 caracteres e colocando
o diálogo antigo depois dele. REDs em corpo e cotidiano preservados em
red_compactacao.txt. O contrato tipado presenca_evento agora protege esse ato
no envio/retry; metadado interno não é enviado ao provedor. Conversa comum
continua descartando system antigo. Uma tentativa de proteger todo system final
falhou no regressivo de continuidade; foi substituída pela identificação tipada.

Autoria corporal projeta só os campos necessários do contrato, sem duplicar a
mesma evidência várias vezes. Replay no modelo real confirmou tipo, fato e estilo
no payload compacto:6259 caracteres totais,3561 do evento; não há sensor vivo ou
voz nesse replay. Uma tentativa anterior teve timeout12s e está preservada.
Autoria efetiva de humor ainda precisa de refinamento; não é confundida com
confirmação de fala ou qualidade global.

## Provas e limites

- Firmware isolado gravado na COM4 com hash verificado:414152 bytes de programa,
  globais17772; firmware integrado apenas compilado:442942/globais19532.
- Host: continuidade/recomposição/isolamento, calibração, limiar aprovado,
  giro medido, falha fechada e motores desarmados passaram. Não são giro físico.
- Python:398 testes passaram em pytest_final.txt; pytest_transporte.txt contém
  controles focados adicionais. Cobertura inclui parser, fonte,
  sessão/idade, cognição/presença, coordenação, catálogo vivo, DEV, fila e
  alegações indevidas. Controles de contextos distintos protegem o transporte.
- USB real, primeiro ensaio:120 leituras, zero erros; mesmo owner e produtor
  instalado. Repetição solicitada de180s:122 leituras e37 timeouts; estados de
  curiosidade, desconfiança, desorientação, recomposição e tranquila registrados.
  Nenhum MOTOR/TURN/SENTRY enviado. Aplicação normal não era esse ensaio.
- Pedro confirmou que o olhar desconfiado e a recuperação gradual ficaram bons.
- Os comentários dos ensaios sem main ficaram em sombra, sem voz. A aplicação
  normal carrega memória e executa a inicialização canônica da autonomia;
  importar laylay.py não equivale a iniciar esses serviços. Validação do main
  foi feita separadamente com encerramento automático; evidências em main_real.
- Primeiro main:296 amostras sem IMU disponível, sem autoria corporal. Após
  retirar/recolocar SDA/SCL, consulta real voltou a PRONTA/ESTAVEL em0x68/WHO0x98.
  Segundo main:270 observações, incluindo TRANQUILA/CURIOSA/DESCONFIADA/
  DESORIENTADA; parte sem dado. Governança reteve comentários por conversa ativa;
  zero autoria/voz corporal. Não é GREEN da fala corporal ao vivo.
- Pedro relatou travamento persistente. Consulta durante o travamento respondeu
  STOP/HEALTH/IMU pela USB; HELLO retornou OLED_AUSENTE. Boot33f7f872 permaneceu
  igual entre a recuperação e a falha; HEALTH registrou2 perdas I2C. IMU respondeu
  novamente em outro momento, sem boot novo. Isso demonstra periférico/barramento
  sem resposta, não parada integral do MCU ou reinício. Ainda não distingue
  fiação, solda, alimentação e tratamento do barramento. Solicitação de isolar
  apenas OLED no SDA8/SCL9 foi o controle físico seguinte. Nenhuma mudança
  permanente de clock, recuperação automática ou autoridade foi aplicada.
- As perdas de comunicação continuam na fronteira CORPO-I2C-01, sem causa
  elétrica declarada. Aprovação visual não encerra estabilidade.

Perfil permanece só IMU/olhos/som: motores OFF, VL53L0X em XSHUT. Não ligar esse
perfil a locomoção. O sensor continua separado na protoboard; giros físicos e
integração com sensores de distância continuam pendentes. ROADMAP não recebeu
declaração de ligação corporal completa.

## Isolamento e troca dos jumpers — continuação de CORPO-I2C-01

- Somente OLED no barramento:102/102 sincronizações em45s, sem erros;
  Pedro confirmou animação normal. OLED+MPU, sem os dois VL53L0X no SDA/SCL:
  181 amostras,116 sincronizações e65 falhas; MPU sem leitura recente.
- Experimento controlado em100kHz não recuperou a comunicação com o MPU.
  Firmware400kHz anterior foi restaurado com hash verificado; a alteração
  temporária de clock foi retirada das fontes. Isso não prova a causa elétrica.
- Após Pedro substituir os jumpers SDA/SCL do MPU, ele voltou a responder
  em0x68/WHO0x98, calibrado e com gravidade plausível. Ensaio seguinte de60s:
  131 consultas,130 sincronizações e130 leituras PRONTA/recentes; uma perda de
  confirmação aos36,242s, com reconexão automática aos38,745s. Foram observadas
  curiosidade, desconfiança, desorientação e recomposição. Sem comandos motores.
- Pedro confirmou que o OLED continuou animando durante esse ensaio.
  HEALTH após o teste manteve boot77c61101, o mesmo da consulta anterior,
  descartando reinício nesse intervalo. Última perda registrada como TRANSPORTE
  não identifica a origem da falha intermediária: encerramento do ensaio também
  fecha a sessão. Não atribuir essa perda a I2C sem evidência adicional.
- Sonda final confirmou MPU PRONTA/ESTAVEL. O STOP sem sessão da sonda bruta
  foi rejeitado como STOP_INVALIDO; o perfil compilado mantém motores OFF e o
  runtime anterior havia encerrado a sessão. Nenhum efeito de parada é inferido
  desse comando rejeitado. Serial fechada ao final; aplicação normal fechada.

Conclusão limitada: recuperação e melhora observadas após a troca dos jumpers,
sem travamento visual ou reinício no minuto acompanhado. Falha intermitente de
confirmação ainda existe; CORPO-I2C-01 permanece aberta. Não restabelecer
locomoção ou os sensores de distância a partir deste ensaio isolado.

## Reativação solicitada por Pedro — 15/10/2026

Pedro autorizou motores/sensores e confirmou SDA/SCL dos dois VL53L0X
reconectados. Perfil integrado USB recompilado e gravado na COM4, com verificação
de hash:442942 bytes de programa,19532 globais. Opções e hashes atuais em
reativar_build_verificado.json; metadados anteriores continuam históricos.
Motores=1, janela5000ms, distância=1, proteção=1, IMU=1, teste isolado=0,
Wi-Fi=0 e som ponte=0. Nenhuma alteração de produção Python ou firmware necessária.

Consulta sem iniciar motores ou conceder vigia:30/30 sincronizações em25s,
mesma sessão, MPU PRONTA/calibrada/ESTAVEL ao final, ambos VL53L0X respondendo.
Ambos estavam com leituras INVALIDA no final; inferior sem retorno é perigo
BORDA_SEM_RETORNO, não autorização de avanço. Limites130/100mm preservados.
Sem ensaio de movimento: habilitação elétrica/protocolar não prova rotação.
Runtime encerrou e liberou serial. Laylay normal não foi aberta. Estabilidade
prolongada, giro físico e CORPO-I2C-01 permanecem pendentes.

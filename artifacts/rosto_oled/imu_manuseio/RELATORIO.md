# CORPO-DECISAO-V1 — percepção inercial/manuseio e giro relativo

15/10/2026, main/HEAD d850b8c90cc5ce40bd4832e759ed991ba88cd5cc. Worktree suja
preservada, fontes iniciais em baseline/ e status_inicial.txt. Nenhum commit.
Evolução do contrato corporal existente, não substituição da proteção anterior.

## Contrato e evidência causal

IMU só publica fatos medidos e hipóteses qualificadas. Firmware é dono da leitura,
calibração, corte local e controle do giro; owner USB mantém sessão/correlação;
mesma mente/experiência/catálogo/DEV recebem a observação. Percepção não concede
movimento. Giro requer pedido atual com alvo/ângulo preservados. PWM não prova
ângulo. Integração beneficia qualquer ação que use o owner motor, inclusive
gestos de conversa, comemorações e cooperação, sem regra por habilidade.

Antes: firmware respondia PACOTE_INVALIDO a IMU. Após primeira gravação, nenhuma
leitura válida; IPROBE não conseguia ler0x68/0x69. OLED/ToF funcionavam: isso
falsifica ausência geral da serial/I2C, mas não determina qual fio/solda falhava.
Após Pedro recolocar os fios, IPROBE leu0x98 em0x68. Não era identidade MPU6050
0x68: documentado no fabricante como ICM20689. Suporte explícito com releitura
das escalas produziu PRONTA, aproximadamente1,02g parada, calibração e ângulos
variáveis. Os registros brutos anteriores foram preservados; não se declarou
falha definitiva do sensor nem aceitou um ID desconhecido indiscriminadamente.

## Candidato

Firmware: imu_corporal.h e giro_medido.h, hooks limitados no sketch. Driver I2C
sem biblioteca/owner paralelo; protótipos sem IMU conservam stubs. Giro usa
admissão existente, STOP/TTL, proteção e sequência de motor. Reação observada
interrompe tração com HAZARD MANUSEIO, sem iniciar fuga. Olhar ampliado conforme
feedback físico; balanço requer energia mais alta por60ms para não reagir a um
toque. Calibração/dado expirado não são medidas válidas.

Python: percepcao_inercial.py, owner rosto_oled_runtime, corpo_motor_runtime,
gramatica_corpo/executor_corpo, companhia_corporal, modelo_corporal,
experiencia_corporal_runtime. Reutiliza estado, experiência e aprendizado
compartilhados. Disponibilidade operacional/capacidades/mapa publicam a
capacidade condicionada a hardware vivo; leitura disponível não promove motor
desarmado a disponível. DEV→Corpo expõe estado/ângulos sem flood no console.
Sem mudança no composition root ou substituição dos serviços compartilhados.

## Validação e limites

- Host C++: identidade0x98, configuração/escalas, calibração, leitura, toque
  isolado versus balanço sustentado, giro medido, falta/sentido de rotação,
  replay, bloqueio de manuseio, ausência/idade e perfil só IMU sem motores.
  Regressivos de admissão do reflexo, proteção, reconexão, sensores, saúde,
  sono e nove cenários de linguagem de parede/borda/pausa/STOP/som passaram.
  Hardware nesses testes é dublê; não substitui movimento observado.
- Python: 236 passaram e4 foram selecionados fora após reprodução das MESMAS
  quatro falhas no baseline dos owners, registrada em regressivos_baseline.txt:
  receipt instalado sem intent, aprendizado de receipt instalado, cadeia com
  parada e companhia instalada. Não foram enfraquecidas/corrigidas nesta tarefa.
  Depois,20 testes da IMU passaram (inclui interrupção cooperativa/partial,
  alvo divergente e resultado de sessão/sequência estrangeiras). Catálogo e
  experiência:110 passaram,1 xfailed preexistente. Ver logs em pytest_*.txt.
- Firmware integrado compilou com sensores/proteção/motores e IMU. Perfil
  isolado foi gravado na COM4 com hash verificado, Wi-Fi/motores/ToF OFF. Build
  e hashes atuais em build_verificado.json; comandos/limites em IMU.md.
- Pedro acompanhou a reação física; primeira versão discreta, segunda mais
  expressiva mas sensível. Após reduzir sensibilidade confirmou: “Sim, agora
  ficou equilibrado”. Não foram enviados MOTOR ou TURN nos ensaios físicos.
- Composição real importada de laylay.py, sem executar main/UI: mesmo transporte
  do corpo, MPU real PRONTA, modelo/prompt com inercial, DEV real com campos e
  pergunta natural do catálogo confirmando leitura e motores indisponíveis.
  Serial fechada normalmente. Evidência em composicao_real_usb.json. Isso não
  é GREEN de uma sessão completa de conversa/execução no main.
- DEV renderizado/inspecionado em dev_imu.png, componentes reais e dados de teste.
- Na demonstração final de45s houve uma perda de resposta FACE após69 amostras.
  HEALTH confirmou uma perda de sessão por I2C; consulta seguinte e uma nova
  sessão da composição real recuperaram leitura. Falha não foi escondida no
  artefato manuseio_usb.json. Pertence à fronteira CORPO-I2C-01 ainda aberta;
  não foi provada a causa elétrica. Aprovação da expressão não prova estabilidade.

Estado final: perfil só IMU/olhos/som, ToF em XSHUT e motores desarmados; aplicação
normal permanece fechada. Não regravar perfil integrado automaticamente.
Pendente: MPU fixo ao corpo, reativar proteção de distância e validar ângulo,
sentido, inércia e parada física. Nada prova posição, retorno exato ou antiqueda.
ROADMAP de capacidade concluída não atualizado: essas fronteiras seguem abertas.

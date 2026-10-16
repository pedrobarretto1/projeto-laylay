# IMU corporal — primeira versão, 15/10/2026

Ligação: VCC→3V3, GND/AD0→GND, SDA→GPIO8, SCL→GPIO9. XDA/XCL/INT livres.
Montagem definitiva: firme no corpo, componentes para cima, sem balanço nos fios.
O módulo marcado MPU-6050 de Pedro respondeu WHO_AM_I=0x98. Esse ID corresponde
ao ICM-20689; o driver aceita explicitamente 0x68 ou 0x98, confirma o ID duas
vezes e relê a configuração das escalas. Não ignora identidades desconhecidas.
Referência: https://product.tdk.com/en/search/sensor/mortion-inertial/imu/info?part_no=ICM-20689

Escalas ±4g/±500°/s, filtro digital, amostragem solicitada a cada10ms. O loop
continua finito, sem esperar conversões. Calibração inicial exige100 amostras
quietas e pelo menos1,8s; tempo efetivo depende da cadência. Uma lacuna>75ms
invalida a calibração. Não se integra uma lacuna como giro. Roll/pitch vêm da
gravidade quando plausível; yaw integra velocidade angular corrigida por bias.
Yaw é relativo, deriva e não mede posição/distância ou permite retorno exato.

Inclinação≥14° suspende motores;≥40° classifica tombamento. Balanço exige energia
forte (desvio da norma>.65g, variação>.55g ou rotação>170°/s) sustentada60ms.
Um toque isolado não vira susto. A leitura não prova toque/colo. Possível
levantamento combina movimento recente com distância inferior sem superfície,
quando esse sensor está habilitado. Olhos e bips só reagem em sessão acordada.
Sossego visual, sono e concessão de companhia existentes são preservados.
Manuseio interrompe motor/reflexo local; não inicia recuos no colo. Só depois
de estabilidade e nova validação dos sensores volta a admitir motor. Não faz
replay do gesto interrompido. HAZARD MANUSEIO correlaciona uma interrupção.

Protocolo somente leitura: `ICAPS 1 <sessao>` → IMU1/IMU0; `IMU 1 <seq>` retorna
estado, idade, calibração, roll/pitch/yaw e velocidade em centésimos de grau,
norma em milésimos de g, classificação e WHO_AM_I decimal. `IPROBE 1 <seq>`
lê identidades nos endereços0x68/0x69, sem renovar FACE nem iniciar calibração.

`TURN 1 <sessao> <seqMotor> <anguloAssinado> <pwm> <prazoMs>` reutiliza a admissão
e sequência do MOTOR. Esquerda positiva; direita negativa. Ângulos15..360°, PWM
90..200, prazo absoluto até5s no perfil longo. TURNACK confirma admissão;
TURNPWM confirma primeiro PWM; TURNEND confirma desfecho e ângulo relativo;
SACK confirma ponte cortada. Só ALVO coerente e correlacionado + PWM + SACK
permitem sucesso. Sem rotação, sentido oposto, saturação, ultrapassagem,
manuseio, timeout, proteção ou sessão perdida encerram sem sucesso. Controle
reduz PWM perto do alvo; precisão/inércia ainda exigem validação física.

## Perfil anterior: teste isolado

`LAYLAY_TESTE_SOMENTE_IMU=1`, IMU=1, WIFI=0, MOTORES=0, DISTANCIA=0, PROTECAO=0,
SOM_PONTE=0. XSHUT0/10 fica LOW: VL53L0X em repouso. OLED/som permanecem ativos.
Uma guarda de compilação proíbe habilitar motores nesse teste. Essa escolha foi
pedida por Pedro durante o ensaio. Não usar como perfil de locomoção.

Nesse ensaio, o perfil integrado foi apenas compilado. Giro físico permanece
pendente: MPU ainda separado na protoboard. Para giros medidos, prender o sensor
ao corpo. A proteção frontal/inferior deve acompanhar a locomoção.
Com aplicação/monitor serial fechados:

```
.\.venv314\Scripts\python.exe scripts\diagnosticar_imu_usb.py --segundos 45
```

Ensaio somente leitura, olhos e sons; encerra e solta a serial. Medidas e estados
chegam ao mesmo modelo corporal da mente, memória de episódios e aprendizado
compartilhado. No DEV só aparecem na opção Corpo; variação angular não gera
uma linha de log por amostra. Evidências/limites em
`artifacts/rosto_oled/imu_manuseio/RELATORIO.md`.

## Manuseio expressivo V1 — 15/10/2026

A sensibilidade validada continua igual. O mesmo classificador alimenta uma
continuidade expressiva: CURIOSA → DESCONFIADA após1,2s inclinada; SUSTO →
RESMUNGO em balanço persistente ou repetido; DESORIENTADA para inclinação forte
ou possível levantamento. RECOMPONDO dura3s antes de TRANQUILA. Repetições têm
memória curta de20s, limitada a3, sem acumular irritação indefinidamente.

IMU1 acrescenta quatro campos após WHO_AM_I: fase, sequência da transição,
idade da fase e repetições. O parser mantém leitura dos formatos anteriores.
Sem dado calibrado/recente não há expressão inercial. Olhos suaves e bips finitos
reutilizam as melodias existentes; não aumentam potência nem concedem movimento.

Na aplicação, a experiência corporal oferece episódios medidos recentes ao
diretor de presença. Cognição interpreta, modelo escreve e fila de voz conserva
porteiro, prioridade, orçamento e receipt. O comentário é no passado: a postura
pode já ter mudado. Só fontes observadas da mesma sessão e até25s são aceitas;
reconexão ou idade vencida cancelam. Histórico recuperado não reativa comentários.
Não confirma colo, dor, dano, bateria, posição ou deslocamento.

Ensaio finito com composição instalada e USB, sem abrir UI ou iniciar motores:
`python scripts/validar_manuseio_fofo_usb.py --segundos 180`.
O orçamento normal de presença permanece ativo; não se promete falar a cada
manuseio. Provas e limites em `artifacts/rosto_oled/manuseio_fofo_v1/RELATORIO.md`.

## Perfil atualmente gravado: integrado USB — 15/10/2026

A pedido de Pedro, após reconectar SDA/SCL dos dois VL53L0X: WIFI=0,
MOTORES_BANCADA=1, LIMITE_MOTOR_TESTE_MS=5000, SOM_PONTE=0,
SENSORES_DISTANCIA=1, PROTECAO_CORPORAL=1, IMU=1, TESTE_SOMENTE_IMU=0.
Mantém motores GPIO1/2 e3/4, SLEEP7, som6, I2C SDA8/SCL9,
XSHUT frontal0 e inferior10; limites borda130mm e frontal100mm.

Gravação verificada por hash;30/30 sincronizações na consulta USB sem movimento,
motor negociado, MPU calibrado e ambos VL53L0X respondendo. Na consulta final,
as duas medidas eram inválidas; inferior sem retorno gerou BORDA_SEM_RETORNO,
mantendo bloqueio de avanço. Isso não prova giro físico ou estabilidade longa.
Laylay permaneceu fechada e serial liberada. Evidências reativar_* no diretório
manuseio_fofo_v1. CORPO-I2C-01 permanece aberta.

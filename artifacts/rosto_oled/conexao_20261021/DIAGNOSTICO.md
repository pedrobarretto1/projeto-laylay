# Conexão corporal — 21/10/2026

Base: `b128f4e48b774352846a40672de493d19c30f109`, branch `main`.
Worktree já modificada; estado e hashes das fontes registrados em `sessao.json`.
Nenhum arquivo de produção alterado nesta investigação.

## Evidência USB

- Cabo anterior, outra porta, placa isolada e tentativa de BOOT: só COM1.
- Outro cabo de dados, ainda isolada e em BOOT: ESP32-C3 `303A:1001` em COM4.
- RESET sem BOOT: COM4 retorna e permanece presente na observação.
- Um dispositivo desconhecido com erro 43 permaneceu mesmo sem o corpo;
  não foi atribuído ao ESP.
- Cabo anterior é a hipótese mais sustentada para a ausência inicial da USB;
  não há prova suficiente para atribuir toda a instabilidade ao cabo.

## Primeira cadeia causal reproduzida depois da remontagem

Ensaio finito de 45 s usando `RostoOledRuntime` de produção e porta real,
com guarda impedindo MOTOR/TURN/DEMO/SENTRY ativo. Não é o main completo.
11 sincronizações, 8 falhas, nenhum movimento enviado.

1. HELLO/READY e FACE/ACK confirmam comunicação e frame.
2. IMU publica AUSENTE; DIST publica FRENTE e BORDA AUSENTE.
3. HEALTH mantém boot `0d82b043`, uptime crescente, sem reinício observado.
4. A recuperação de periféricos invalida a sessão por `I2C`.
5. SENTRY encontra sessão inválida; GUARD passa a publicar `SEMSESS`.
6. O parser rejeita corretamente o receipt não correlacionado; o transporte fecha.
7. Nova sessão acorda os olhos e a recuperação repete o ciclo.

Exemplo: GUARD válido em 2,0371 s, GUARD SEMSESS em 3,2714 s;
HEALTH seguinte registra outra perda por I2C no mesmo boot.
Não enfraquecer o parser para admitir `SEMSESS` como sessão atual.

## Fronteira ainda aberta

Confirmar a remontagem/alimentação/barramento dos três sensores, todos ausentes
na consulta física. OLED funcional não confirma o ramo elétrico dos sensores.
`recuperacao_perifericos.h` invalida a sessão inteira antes de reinicializar
periféricos indisponíveis a cada 5 s; esse comportamento explica o ciclo observado,
mas não prova por que os sensores estão ausentes.

Revalidar sensores e estabilidade no main depois de corrigir a primeira fronteira.
Firmware não regravado; motores não ensaiados; Laylay encerrada pelo usuário.

## Após conferência dos fios

`apos_conferir_fios.json`: 35 s solicitados, 12 ciclos, 5 falhas, nenhum movimento.
COM4 voltou com o cabo novo. Novo boot por religação, depois uptime crescente
no mesmo boot durante o ensaio. IMU, frontal e borda continuam AUSENTE em todas
as respostas capturadas. HEALTH acumula perdas I2C; GUARD volta a SEMSESS.
Próxima falsificação física: deixar somente OLED + MPU no SDA/SCL e verificar
alimentação/comunicação desse único sensor antes de recolocar os VL53L0X.

## OLED + MPU, SDA/SCL dos VL53L0X desconectados

`sonda_mpu_isolado.json`: três consultas IPROBE ao endereço 0x68 respondem
com WHO_AM_I 0x98; 0x69 não responde, coerente com AD0 ao GND. Três consultas
IMU retornam PRONTA, calibrada e leituras recentes. HEALTH mantém o mesmo boot.
As consultas são somente leitura e não concedem sessão nem tração.
Isso falsifica MPU permanentemente inoperante e falha permanente de comunicação
do par OLED/MPU. Ainda não distingue um VL53L0X/fio defeituoso de carga elétrica
do barramento completo. Próximo controle: reconectar apenas o frontal.

## OLED + MPU + frontal

`sonda_mpu_frontal.json`: IPROBE responde nas três consultas; IMU passa de
CALIBRANDO a PRONTA. Frontal é reconhecido: primeiro retorno INVALIDA/status4,
depois duas medidas VALIDAS de 26 e 30 mm. Inferior permanece AUSENTE,
coerente com SDA/SCL desconectados. Nenhuma tração ou sessão concedida.
Próximo controle: religar também SDA/SCL do inferior e comparar os três módulos.

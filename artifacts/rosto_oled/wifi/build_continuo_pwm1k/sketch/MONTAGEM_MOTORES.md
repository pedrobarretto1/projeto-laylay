#line 1 "C:\\Users\\pbarr\\Downloads\\pasta organizada\\programacao\\PY\\projeto lay\\laylay\\firmware\\rosto_laylay\\MONTAGEM_MOTORES.md"
# Montagem do corpo com dois N20 de 3 V

ESP32-C3 Super Mini, OLED SSD1306 e ponte dupla DRV8833.
Pedro confirmou motores **3 V / 30 RPM**, alimentação atual pelo USB do PC
de **5 V**, inscrições `EEP` e `ULT`, e ausência de conversor de tensão.

**Atualização de bancada, 11/10/2026:** Pedro esclareceu que os motores
atualmente conectados são outros motores de teste, **não os N20**. Confirmou
que giram com 5 V, que os sinais seguem este pinout e que estão na protoboard,
sem rodas. Autorizou habilitar o perfil de bancada. As instruções de 3 V
abaixo continuam destinadas aos N20 planejados para o corpo futuro.

## Alimentação necessária antes do primeiro teste

O ESP continua ligado pelo USB. Os motores precisam de uma **fonte de 3 V**:
fonte externa regulada, ou alimentação de 5 V passando por um conversor
DC-DC step-down ajustado e medido em 3 V antes de conectar à ponte.

**Por enquanto, monte os sinais com tudo desligado e deixe VM/VIN/+ da
ponte desconectado.** Não ligue o USB de 5 V diretamente aos N20 de 3 V.
A ponte comuta a tensão de VM; ela não converte 5 V em 3 V. A saída 3V3
do ESP também não deve alimentar os motores.

Um resistor em série também não regula a alimentação em 3 V: sua queda
é `R × I`, e a corrente muda na partida e com a carga mecânica. Ele pode
dificultar a partida e deixar a tensão subir quando o motor fica leve.
O resistor de 10 kΩ no SLEEP, citado abaixo, tem outra função: manter a
ponte desabilitada durante o reset. Ele não fica na alimentação dos N20.

A fonte e o conversor precisam suportar a corrente de partida dos dois
motores. A indicação “30 RPM” não informa essa corrente; sem o modelo ou
uma medição, a capacidade da porta USB para alimentar ambos continua aberta.
A DRV8833 opera com VM entre 2,7 e 10,8 V; isso é o limite do driver,
não uma autorização para ultrapassar a tensão nominal dos motores.
[Especificação TI](https://www.ti.com/lit/ds/symlink/drv8833.pdf)

## Fios de controle

Use os números **GPIO** da Super Mini, e os nomes impressos nos conectores
da ponte. Os números não são posições físicas do conector.

| ESP32-C3 | Entrada da ponte | Uso |
|---|---|---|
| GPIO **1** | AIN1 / IN1 | Motor esquerdo, entrada 1 |
| GPIO **2** | AIN2 / IN2 | Motor esquerdo, entrada 2 |
| GPIO **3** | BIN1 / IN3 | Motor direito, entrada 1 |
| GPIO **4** | BIN2 / IN4 | Motor direito, entrada 2 |
| GPIO **7** | nSLEEP / SLEEP / SLP | Habilitação da ponte |
| **GND** | GND / − | Terra comum |

`EEP` provavelmente é o final de **SLEEP**, e `ULT` o final de **FAULT**.
São inferências pelas inscrições relatadas, não identificação do circuito
da placa preta. Confirme que EEP é o conector SLEEP antes de ligá-lo ao GPIO7.
O conector FAULT fica **sem conexão** nesta bancada; o firmware não mede esse
sinal. Não una SLEEP à alimentação: precisamos que o GPIO possa desligá-lo.
Se o módulo tiver uma ligação/jumper que prende SLEEP em VIN, isso precisa
ser verificado antes de conectar a saída do ESP.

Um resistor de **10 kΩ entre SLEEP e GND** mantém a habilitação baixa enquanto
o ESP reinicia, desde que o SLEEP não esteja preso à alimentação no módulo.
O GPIO7 é configurado em LOW no início do firmware, antes do OLED e da USB.
O nível de 3,3 V do ESP é suficiente para os controles da DRV8833.
[Entradas, nSLEEP e nFAULT da TI](https://www.ti.com/lit/ds/symlink/drv8833.pdf)

O mapa atual GPIO1/2/3/4 foi escolhido por Pedro após o primeiro teste sem giro;
preserva o OLED em 8/9. GPIO2 participa da configuração no reset: a Espressif
recomenda nível alto na partida para evitar glitches, embora esse pino não
determine o modo SPI/Download. Depois do boot funciona como GPIO normal.
[Configuração de boot do ESP32-C3](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/schematic-checklist.html)

GPIO7 também tem função JTAG,
por isso o pulldown e a inicialização da habilitação são relevantes.
[Pinagem ESP32-C3](https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf)

### Perfil temporário para teste contínuo

Atualização de PWM (11/10/2026): o acionamento dos quatro GPIOs usa agora
**1 kHz / 8 bits**, igual ao padrão de `analogWrite` do core ESP32 3.3.12
usado no projeto de referência. O valor PWM100 representa duty 100/255;
copiar esse valor com outra frequência não reproduz a configuração original.
A versão anterior usava 20 kHz. O pinout atual e os cortes de segurança
permanecem os da tabela acima. Esta equivalência de configuração não mede
torque, corrente nem prova rotação; a confirmação física é registrada à parte.

O build normal limita `MOTOR` a 500 ms. O perfil explicitamente solicitado
para bancada aceita `-DLAYLAY_LIMITE_MOTOR_TESTE_MS=5000` junto com
`-DLAYLAY_HABILITAR_MOTORES_BANCADA=1`. O prazo absoluto de cada ordem permanece
no ESP; FACE não o prolonga. STOP, perda da sessão, desconexão e falha do OLED
continuam cortando a ponte. Valores acima de 5000 ms falham na compilação.

`python -m scripts.testar_motor_continuo_5s` envia uma única ordem para frente,
PWM100/5000ms, mantendo o heartbeat. Não reenvia MOTOR numa falha. Executar
somente após autorização e confirmação de rodas suspensas/área delimitada,
com a Laylay fechada para existir um único controlador. O receipt registra
MACK/SACK; giro e direção física ainda dependem da observação. Após o teste,
regravar o firmware normal de 500 ms. A API dos comandos naturais continua
limitada a 500 ms mesmo durante esse perfil de diagnóstico.

## Saídas, motores e terra

| Ponte | Conexão |
|---|---|
| AOUT1/AOUT2 ou OUT1/OUT2 | Os dois fios do motor esquerdo |
| BOUT1/BOUT2 ou OUT3/OUT4 | Os dois fios do motor direito |
| VM/VIN/+ | Positivo da fonte **3 V** dos motores |
| GND/− | Negativo da fonte 3 V **e GND do ESP** |
| FAULT / ULT | Sem conexão neste primeiro teste |

Se os conectores forem numerados, confirme que as entradas e saídas estão
agrupadas nesses dois canais. Não ligue os fios do motor ao GND: ambos
vão às duas saídas do respectivo canal. O sentido físico será conferido
com cada motor separado; rodas montadas em lados opostos podem exigir
inverter os fios de um deles para ambos empurrarem o corpo para a frente.

```text
USB do PC ───────────────────────────────► ESP32-C3

Fonte regulada de 3 V (+) ───────────────► VM/VIN da DRV8833
Fonte regulada de 3 V (−) ──┬───────────► GND da DRV8833
                            └───────────► GND do ESP

ESP GPIO1/2 ──► AIN1/2 ──► AOUT1/2 ──► N20 esquerdo
ESP GPIO3/4 ──► BIN1/2 ──► BOUT1/2 ──► N20 direito
ESP GPIO7 ────► SLEEP
                 │
                10 kΩ
                 │
                GND
```

Se a fonte escolhida for o USB, a linha “fonte regulada de 3 V” significa
**USB 5 V → conversor ajustado a 3 V → VM**. Não conecte a saída do conversor
ao 3V3 ou ao 5V do ESP. O terra é compartilhado.

## OLED preservado

SDA → GPIO8, SCL/SCK → GPIO9, VCC → 3V3, GND → GND.
Nenhum fio de motor usa esses GPIOs.

## Etapa preparada e limites

Esta é uma melhoria de acionamento físico, separada da causa emocional
RPV18-06. Emoção e encenação não autorizam locomover o corpo. A única porta
COM do ESP continua pertencendo ao transporte serial já existente.

O candidato de bancada em `rosto_laylay.ino` acrescenta pulsos curtos de
motor ao protocolo. A versão atualmente gravada na COM4 continua sendo a
versão de rosto. Nenhum teste físico ou gravação de motores foi feito nesta
etapa: a alimentação de 3 V e a montagem ainda precisam ficar prontas.

O protocolo de bancada reutiliza a sessão do rosto e mantém uma sequência
independente para os motores:

```text
HELLO 1 a1b2c3d4
FACE 1 a1b2c3d4 1 0 1 0 3500
MOTOR 1 a1b2c3d4 1 160 0 250
```

`MOTOR` recebe sessão, sequência do motor, PWM esquerdo, PWM direito e
duração em milissegundos. PWM varia de −255 a +255; 0 deixa aquele motor
sem tração. Duração permitida: 50–500 ms. A sequência acima pede somente
o motor esquerdo durante uma janela nominal de 250 ms. O direito seria
`MOTOR 1 a1b2c3d4 2 0 160 250`, enviado depois do primeiro pulso terminar.
São comandos de diagnóstico, não instruções já disponíveis na conversa.
O exemplo deve ser enviado como um lote de três linhas: se você levar mais
de 3,5 segundos depois da FACE, a sessão expira. Para outro pulso, envie
uma FACE com sequência crescente junto do MOTOR de sequência crescente.
Envie `STOP` separadamente quando quiser interromper; ele cancela também
um pulso que ainda aguarda o despertar da ponte.

Um novo pulso não pode prolongar outro em andamento: é rejeitado como
`MOTOR_OCUPADO`. FACE não renova o prazo do motor. `STOP` cancela inclusive
o despertar pendente; boot, HELLO, DEMO, expiração e perda do OLED desligam
as entradas e SLEEP. O firmware aguarda o despertar do driver sem bloquear
o loop. O prazo é verificado por software no loop, inclusive antes do
render; a latência real de corte sob falha I2C ainda precisa ser medida.
Desligar a tração deixa o motor girar livremente até perder a inércia,
portanto não promete parada mecânica instantânea.

`MACK` é um receipt correlacionado da configuração de GPIO/PWM no firmware.
Ele não mede tensão, corrente, rotação ou deslocamento. Não retransmita
comandos de movimento para compensar ausência de ACK; corte e investigue.
O Monitor Serial precisa ter exclusividade da COM, com a Laylay fechada.
A futura integração terá um único owner serial compartilhado entre rosto
e movimento.

O primeiro teste será com as rodas levantadas: motor esquerdo, motor
direito, sentidos, parada e corte ao perder comunicação. Depois vêm a base,
rodas, apoio e teste curto no chão. Dois motores sem essa montagem mecânica
não permitem avaliar se o corpo anda bem.

Comandos naturais de locomoção e iniciativa ainda **não estão disponíveis**
na Laylay. A integração deve usar o interpretador, autorização, receipts,
continuidade, diagnóstico e catálogo compartilhados; não abrir outra COM
nem transformar o estado emocional em ordem aos motores. Iniciativa terá
modo próprio com autorização e limites, e `pare` deve interrompê-la.
Sem sensores de obstáculos ou encoders, não há prova de caminho livre,
distância percorrida ou posição restaurada ao parar.

## Validação da fonte — 11/10/2026

- Compilação ESP32-C3, core 3.3.12, USB CDC ativado: **380.078 bytes** de
  programa e **15.748 bytes** de RAM estática. Sem upload.
- SHA256 do `.ino` compilado:
  `5269cd53bc66c500dc3a5b96ba5b002df7083384fe7f42e1121c19ba35db92d1`.
- Host compila e executa o `.ino` real com GPIO/PWM/I2C simulados. GREEN
  para boot, wake de pelo menos 1.000 µs, PWM nos dois sentidos, limites,
  ocupação, replay, STOP, zero, HELLO/DEMO, perda do OLED, falha de PWM,
  expiração independente de FACE e wrap de millis/micros.
- REDs precederam os candidatos: ausência de GPIO na versão de rosto;
  autorização/próprio pulso expirando durante I2C; sessão longa sendo
  dividida em sessão e sequência pelo parser. Todos ficaram GREEN sem
  enfraquecer as expectativas de tempo/correlação/desenergização.
- **109 regressivos Python** aprovados para rosto, expressão solicitada
  e reação social. Nenhuma mudança na produção Python de locomoção.
- As 100 trocas de pose do renderer passaram; calma → alegre mudou
  192 pixels no primeiro frame, máximo de 287 nas 100 combinações,
  abaixo dos limites existentes. São pixels simulados, sem nova prova óptica.

O teste host prova decisões/configuração de GPIO; a compilação prova que
a fonte é aceita pelo toolchain da C3. **Giro, alimentação, corte físico,
movimento no chão e integração natural/autônoma continuam pendentes.**

Base: branch `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`.
Worktree anterior preservada. Nenhum commit criado.

## Separação do perfil de rosto — 11/10/2026

A atualização da animação de hack compila por padrão com
`LAYLAY_HABILITAR_MOTORES_BANCADA=0`: nSLEEP e entradas ficam LOW,
LEDC de tração não é habilitado e MOTOR é rejeitado. Os testes positivos de
bancada usam a macro explicitamente em 1; isso não ativa a placa física.
Qualquer habilitação de tração exige outro build e validação próprios.

Pedro informou que conectou dois motores e observou giro com 5 V. É evidência
humana de giro nessa montagem; não é medição de corrente, aquecimento, tensão
nominal ou prova de adequação para uso contínuo. A informação anterior sobre
N20 nominais de 3 V permanece registrada. A atualização visual não executa
testes de motor nem confirma locomoção ou parada física.

## Bancada autorizada e validada — atualização de 11/10/2026

Os motores conectados agora são outros motores de teste, distintos dos N20;
Pedro confirmou uso da própria DRV8833 em 5 V e protoboard sem rodas.
O primeiro perfil habilitado, no mapa antigo 0/1/3/10, confirmou quatro
MACK/STOPPED, porém Pedro observou **"Não giraram"**. Esse RED físico foi
preservado; receipts não foram promovidos a movimento.

Pedro escolheu e confirmou a nova montagem GPIO1/2/3/4. O firmware foi alterado
somente no mapa, com RED de expectativa do novo array antes do candidato e
GREEN nos dois hosts, preservando limites, wake, parada, replay e expiração.
Build C3/core 3.3.12, perfil `LAYLAY_HABILITAR_MOTORES_BANCADA=1`,
383.732 bytes programa / 15.772 RAM; gravado na COM4 com hash verificado.
SHA256 do .ino nesta etapa histórica:
`0c8916f8c2d53826be82a06dab9371f9890d0ed54bc6ec4378f22a0eaee21990`.

Com o novo mapa, PWM180/250 ms produziu giro percebido fraco. A pedido de Pedro,
PWM255/250 ms foi aplicado em quatro pulsos: esquerdo/direito, sentidos A/B,
com pausa e STOP adicional entre eles. Quatro MACK correlacionados e parada
final confirmada. Pedro confirmou **"Sim, os dois ficaram mais fortes e pararam"**.
É prova humana pontual de giro dos dois sentidos e parada, sem medição de
corrente, torque, velocidade ou tempo elétrico exato do corte. Não atribuímos
o RED anterior a uma causa elétrica única sem medida.

Receipts preservados em `artifacts/rosto_oled/motores/`; cada nova sequência
recebe arquivo próprio. Para repetir esse teste com a Laylay/Monitor Serial
fechados e os motores de teste sem carga:

```powershell
.\.venv314\Scripts\python.exe -m scripts.testar_motores_bancada --pwm 255
```

A ferramenta usa o owner serial instalado e escopo visual compartilhado,
sem segunda porta. É uma sequência fixa de bancada autorizada pelo operador;
não registra locomoção como habilidade da conversa. Pedidos como `ande`/`vire`
precisavam integrar modalidade, intents, autorização, executor, receipts,
continuidade, aprendizado e catálogo. Essa integração manual está instalada na
atualização abaixo; iniciativa terá modo e limites próprios.

## Comandos corporais instalados — continuação de 11/10/2026

O mesmo owner serial do rosto agora recebe pedidos pelo ciclo canônico:
`ande para frente`, `ande para trás`, `vire para a esquerda`, `vire para a direita`
e `pare os motores`. `De novo` reusa os parâmetros de um receipt anterior,
exigindo novo pedido autorizador. A ponte recebe um pulso de até 250 ms/PWM255
por padrão, máximo de 500 ms. MACK confirma aplicação de PWM; SACK correlaciona
a parada. Esses sinais não medem giro, orientação das rodas ou deslocamento.

O transporte negocia MCAPS/MOTOR1 sem gerar tração. Perfil0 permanece indisponível
para iniciar movimento. STOP é prioritário, cancela a espera por MACK e corta
a ponte; uma reconexão não reenvia MOTOR nem mistura receipts de sessões.
O catálogo consulta a disponibilidade viva; consulta de capacidade não executa.
Iniciativa corporal está desativada: o executor autônomo de IoT/áudio pressupõe
efeitos reversíveis, e um pulso contrário não é prova de desfazer deslocamento.

Atualização visual preserva GPIO1/2/3/4 e SLEEP7. Fonte atual:
`7fccfad8e05c8f3ce397961d56e11f8507c351ca9fb202658f7176f83b4d2425`.
Build C3/core3.3.12, motor=1, 387.950/15.836 bytes, COM4 com hash verificado.
Caminho instalado com classificação natural/arbiter/executor/receipts reais:
quatro MACK e SACK mais parada explícita. Na primeira passagem Pedro não
acompanhou os pulsos; na repetição confirmou **"Sim, giraram e pararam"**.
É prova pontual de bancada, sem rodas, deslocamento ou medida elétrica do corte.
Receipts únicos em `artifacts/rosto_oled/glitch_boca/`.

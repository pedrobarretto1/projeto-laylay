# Teste local de som ao iniciar

Perfil simples (`LAYLAY_SOM_PONTE=0`, padrão):
GPIO6 -> resistor de1kΩ -> positivo do capacitor6,8µF/200V ->
negativo do capacitor -> positivo do falante8Ω/0,2W -> negativo do falante -> GND.
Capacitor sem polaridade pode ser montado em qualquer sentido.

Perfil temporário em ponte (`LAYLAY_SOM_PONTE=1`):
GPIO6 -> resistor de **220 Ω** -> um terminal do falante -> outro terminal -> GPIO5.
O falante não se conecta ao GND neste perfil. Retirar o capacitor polarizado;
GPIO5 deve estar livre de outras conexões. Trocar fios com USB/bateria desligadas.
O resistor permanece obrigatório. Para uma estimativa ideal de 3,3 V e carga
resistiva de 8 Ω, a corrente fica em cerca de 14,5 mA e a potência no falante
em 1,7 mW. Isso não mede impedância, volume real ou corrente desta montagem.

O firmware emite um bip de1200Hz por2000ms em cada inicialização física do ESP.
Não depende de abrir a Laylay, não repete no loop e não tem comando de áudio.
É um teste de baixo volume, sem amplificação. Não reduzir o resistor para
buscar volume. Canal PWM4 e frequência própria preservam os motores de1kHz.
Em ponte, canais4/5 compartilham o timer de1200Hz com saída5 invertida.
O corte retira a inversão, desliga/destaca os dois canais e deixa ambos GPIOs
em LOW; falha de qualquer etapa encerra o teste, sem nova tentativa no loop.
O loop continua cuidando de OLED, USB e parada dos motores durante o bip.

Logs BEEP_TEST distinguem START, STOP e FALHA_PWM. Não são prova auditiva.
O host validar_bip_inicio.cpp cobre corte em2000ms, ausência de repetição,
falha fechada e configurações dos motores; teste físico requer ouvir o falante.

Build ESP32-C3: esp32:esp32:esp32c3:CDCOnBoot=cdc, core3.3.12,
compiler.cpp.extra_flags=-DLAYLAY_WIFI=0 -DLAYLAY_HABILITAR_MOTORES_BANCADA=1.
Acrescentar `-DLAYLAY_SOM_PONTE=1` apenas para a montagem em ponte descrita acima.

Após ouvir o teste em ponte, Pedro solicitou voltar ao GPIO6 exclusivo.
Perfil ativo solicitado: `LAYLAY_SOM_PONTE=0`, GPIO5 desconectado, montagem
de teste GPIO6 -> 220 Ω -> falante -> GND, sem capacitor. O bip continua
único e limitado a2s; esta ligação de diagnóstico não é amplificador de áudio.

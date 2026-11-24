# Perfil temporário: somente sensor frontal

Autorizado por Pedro em 23/11/2026. O sensor de borda foi retirado.
Frontal VL53L0X: VCC 3V3, GND comum, SDA GPIO8, SCL GPIO9 e XSHUT GPIO0.
O GPIO10 fica livre. OLED, motores e som mantêm a pinagem anterior.

Build: `LAYLAY_SENSORES_DISTANCIA=1`, `LAYLAY_SENSOR_BORDA=0`,
`LAYLAY_PROTECAO_CORPORAL=1`, `LAYLAY_WIFI=1`,
`LAYLAY_HABILITAR_MOTORES_BANCADA=1`, `LAYLAY_LIMITE_MOTOR_TESTE_MS=5000`,
`LAYLAY_IMU=0`, `LAYLAY_SOM_PONTE=0`,
`LAYLAY_PWM_MINIMO_MOTOR=150`, `LAYLAY_PWM_MAXIMO_MOTOR=255`.

O frontal mantém o limite de 100 mm. A busca usa amostras novas do frontal
para verificar a saída; não depende de um sensor inferior inexistente.
Leitura frontal inválida recente continua significando ausência de retorno,
como no perfil anterior. Sensor frontal ausente, erro I2C e amostra vencida
continuam bloqueando a tração. A telemetria inferior informa `DESATIVADA`,
sem distância fictícia. Reconexão aceita essa ausência explícita, mas ainda
exige telemetria recente e condição válida do frontal.

Não há detecção de bordas nem proteção de queda neste perfil. Usar no chão
ou em plataforma que impeça queda. Reconectar o inferior requer regravar
com `LAYLAY_SENSOR_BORDA=1` (padrão), restaurando as guardas do perfil duplo.

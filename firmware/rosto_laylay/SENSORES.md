# Dois VL53L0X — leitura diagnóstica, 14/10/2026

Atualização posterior: a placa já recebeu a proteção V1 e integração USB/mente/DEV.
Este arquivo preserva a primeira etapa de leitura; estado atual em PROTECAO.md.

| Função | VCC | GND | SDA | SCL | XSHUT | Endereço7bits |
|---|---|---|---|---|---|---|
| Obstáculos à frente |3V3|comum|GPIO8|GPIO9|GPIO0|0x30|
| Superfície/borda dianteira |3V3|comum|GPIO8|GPIO9|GPIO10|0x31|

GPIO1 dos módulos sem ligação. OLED continua no mesmo Wire (0x3C/0x3D).
XSHUT é liberado por INPUT para usar o pull-up do módulo. Inicialização sequencial
por endereço padrão0x29; cada endereço é reassociado em cada boot. Se um módulo
falha ao iniciar, seu XSHUT volta a LOW, evitando colisão com o seguinte.

## Estado atual

Firmware compilado e gravado na COM4 com sensores habilitados. Consulta ASCII:

```text
DIST 1 27
DIST 1 27 FRENTE 48 VALIDA 120 41 0 BORDA 49 VALIDA 105 86 0
```

Cada sensor informa endereço decimal, estado, distância em mm (ou-1), idade em
ms e RangeStatus da API. VALIDA exige status0, distância1..8189 e idade<=300ms.
Estados: AUSENTE, AGUARDANDO, VALIDA, INVALIDA, ERRO_I2C, EXPIRADA.
Ausência/erro não significam caminho livre nem superfície segura.

Conversões continuam em hardware; o loop consulta um sensor por vez sem esperar
uma conversão terminar. I²C conserva timeout30ms. Inicialização só no boot com
tração cortada. Distância não concede controle nem altera PWM, OLED ou sono.

**Esta versão mede apenas. Ainda não corta movimento por obstáculo/borda e não
publica percepção dos sensores para o raciocínio da Laylay.** Referência inicial
da superfície inferior94–104mm; altura definitiva confirmada pelo usuário.
Isso não é uma calibração antiqueda validada.

Painel independente, somente leitura, com Laylay/Monitor Serial fechados:

```powershell
.\.venv314\Scripts\python.exe scripts\diagnosticar_sensores_usb.py
```

O painel envia STOP ao abrir, depois somente DIST. Ao fechar salva as últimas400
leituras em artifacts/rosto_oled/sensores/painel.json e libera a serial.

## Compilação reproduzível

Adafruit_VL53L0X1.2.5 foi extraída do pacote oficial do índice Arduino em
artifacts/rosto_oled/sensores/libraries. A instalação no sketchbook OneDrive
falhou ao criar diretório temporário; foi usada dependência local explícita,
sem mudar configuração global. Demais bibliotecas Adafruit existentes reusadas.

```powershell
& 'C:/Users/pbarr/AppData/Local/Programs/Arduino IDE/resources/app/lib/backend/resources/arduino-cli.exe' compile --fqbn 'esp32:esp32:esp32c3:CDCOnBoot=cdc' --libraries 'artifacts/rosto_oled/sensores/libraries' --build-path 'artifacts/rosto_oled/sensores/build' --build-property 'compiler.cpp.extra_flags=-DLAYLAY_WIFI=0 -DLAYLAY_HABILITAR_MOTORES_BANCADA=1 -DLAYLAY_SOM_PONTE=0 -DLAYLAY_LIMITE_MOTOR_TESTE_MS=5000 -DLAYLAY_SENSORES_DISTANCIA=1' 'firmware/rosto_laylay'
```

Perfil de som simples GPIO6, motores1/2 e3/4, nSLEEP7 e USB mantidos. Build
sem LAYLAY_SENSORES_DISTANCIA=1 mantém a compatibilidade histórica sem sensores.

Próxima fronteira: política de borda com referência/qualidade/idade, interrupção
local da tração e leitura no owner USB/mente/DEV; validar sem deslocar o corpo
antes de qualquer teste de movimento apoiado.

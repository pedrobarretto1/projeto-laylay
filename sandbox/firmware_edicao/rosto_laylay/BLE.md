# Conectar o corpo por Bluetooth LE

O ESP32-C3 anuncia o serviço GATT `Laylay-Corpo` com o firmware compilado
com `LAYLAY_BLE=1` e `LAYLAY_WIFI=1`. O firmware reutiliza o token já
provisionado no ESP e em `memoria/corpo_wifi.json`. Quando faltar o
pareamento, use a configuração por USB descrita em [WIFI.md](WIFI.md).
A consulta `BLE_STATUS 1` pela USB informa se o ESP está anunciando o serviço.
O PC precisa de um adaptador Bluetooth LE e da dependência
`bleak` dos requisitos do projeto.

Com a Laylay fechada, inicie na pasta do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\rosto_laylay\iniciar_laylay_com_rosto.ps1 -Porta BLE
```

Também é possível salvar `LAYLAY_ROSTO_PORTA=BLE` em `configuracao.env`.
`AUTO` mantém a seleção USB/Wi-Fi. BLE usa o token existente para autenticar
o PC e a placa por desafio aleatório, sem transmitir o token. A conexão
BLE dispensa rede Wi-Fi ativa. Se houver mais de um corpo anunciando o
serviço, deixe ligado só o alvo durante a conexão.

O canal usa o protocolo do corpo com a mesma sessão, confirmação de
movimento e parada. A queda do link encerra a sessão BLE e corta a tração
no firmware. Reconectar exige uma nova sessão; nenhuma ordem é repetida.
No painel DEV, o transporte aparece como `ble` quando selecionado.

Para compilar o perfil frontal atual, use o Arduino ESP32 3.3.12 para
`esp32:esp32:esp32c3:CDCOnBoot=cdc,PartitionScheme=min_spiffs`, com os
[flags do perfil frontal](PAREDE_SEM_BORDA.md) e `-DLAYLAY_BLE=1`.
O perfil usa a tabela Minimal SPIFFS para acomodar o binário maior.
A partição NVS do pareamento mantém o endereço e o tamanho.

O caminho pelo rádio precisa de validação física com um adaptador. Testes
simulados verificam o cliente GATT, autenticação e integração com o owner.

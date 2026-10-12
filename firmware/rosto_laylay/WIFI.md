# Corpo da Laylay pela rede local

O ESP32-C3 entra no Wi-Fi de 2,4 GHz do roteador e oferece um servidor TCP
local na porta 8765. O PC continua na sua rede. Não é necessário servidor na
internet nem mudar a montagem: OLED SDA8/SCL9; ponte GPIO1/2/3/4 e SLEEP7.

## Configurar

1. Feche a Laylay e qualquer Monitor Serial que esteja usando a COM4.
2. Mantenha o ESP32 alimentado pela USB. Abra
   `scripts/CONFIGURAR_CORPO_WIFI.ps1`, ou execute no ambiente do projeto:
   `python -m scripts.configurar_corpo_wifi`.
3. Digite o nome da rede de 2,4 GHz e a senha na janela local. Clique em
   **Conectar e testar**. A senha não é argumento de comando, log ou arquivo
   no PC; ela é enviada pela USB e armazenada na NVS do ESP32.
4. A janela só ativa `memoria/corpo_wifi.json` depois de autenticar o servidor,
   receber ACK do rosto e SACK da parada. Esse arquivo pessoal, ignorado pelo
   Git, contém IP e token de pareamento; nunca publique seu conteúdo.
5. Abra a Laylay normalmente. No modo AUTO ela prefere a conexão Wi-Fi
   configurada. Emoções, fala, hack, glitch e comandos corporais reutilizam o
   mesmo runtime, autorização e receipts do controle USB.

O JSON guarda o IP obtido do roteador. Se o DHCP mudar esse endereço, execute
novamente a configuração local. `laylay-corpo.local` é anunciado pela placa,
mas nesta versão o cliente usa IPv4 para limitar o tempo de conexão.

### Endereço fixo por rede

O firmware aceita configuração local pela USB, separada das credenciais NVS:

```text
WIFI_IP 1 192.168.137.109 192.168.137.1 255.255.255.0
WIFI_IP_STATUS 1
```

O primeiro comando salva IP/gateway/máscara associados ao SSID atualmente
provisionado, corta a sessão e inicia nova associação. A confirmação
`WIFI_IP_CONFIGURED 1` confirma a configuração salva; somente `WIFI_STATUS`
com CONNECTED e os receipts AUTH/ACK/SACK confirmam a conexão utilizável.
O endereço deve estar livre e pertencer à sub-rede do PC/roteador; esta
configuração não cria uma reserva no servidor DHCP. A rede privada do corpo
deve ser usada pelo ESP, sem outros clientes que disputem o mesmo endereço.

`WIFI_IP 1 DHCP` remove a configuração fixa. Outra rede usa DHCP; retornar
ao SSID configurado reaplica seu endereço fixo. Reiniciar ou regravar sem
apagar a NVS conserva a configuração. TCP não pode alterar IP ou credenciais.
Falha ao aplicar a configuração fixa impede a associação; não há troca
silenciosa para DHCP. Atualize o JSON pessoal somente após validar o servidor
no endereço escolhido, preservando o token. A rede hospedada do PC ainda
precisa ser iniciada a cada sessão com o launcher `-HotspotLocal` abaixo.

## Comandos e limites

Pedidos como “ande para frente”, “ande para trás”, “vire para a esquerda” e
“pare os motores” seguem o fluxo canônico existente. Padrão PWM255/250ms,
limite absoluto500ms. MACK confirma aplicação do PWM, SACK confirma corte;
não medem deslocamento. Movimento espontâneo continua desativado.

AUTH autentica a conexão; HELLO toma a sessão após cortar o motor. Somente
um endpoint USB/TCP controla a sessão. Reconexão não reenvia MOTOR. EOF,
Wi-Fi perdido, congestionamento do envio e vencimento do FACE invalidam a
sessão, cortam os motores e devolvem a placa ao sono. Sem aviso imediato da
rede, o FACE expira em 3,5s; o pulso motriz mantém seu limite próprio500ms.

Falha na rede não provoca troca automática para USB. Para testar por USB,
inicie a Laylay com `LAYLAY_ROSTO_PORTA=COM4`. OFF desativa ambas; configuração
Wi-Fi inválida falha fechada. Nenhuma conexão é aberta ao importar o projeto.

## Evidências de 11/10/2026

462 testes Python +22 subtestes passaram. Servidor TCP de loopback real cobre
autenticação negativa, fragmentação, EOF, receipts, cancelamento, reconexão,
catálogo e composição instalada; o hardware desses testes é simulado.
Hosts do `.ino` verificaram owner único, configuração máxima pela USB,
backpressure, peers abandonados, cortes, replay e as animações existentes.
Build C3/core3.3.12, perfil motor1: 1.089.095 bytes de programa e41.360 RAM.
Gravado na COM4/MAC conhecida, hash da flash verificado. Esses resultados não
substituem a conexão e a observação físicas, registradas separadamente em
`artifacts/rosto_oled/wifi/`.

Continuação do diagnóstico físico: a rede configurada não completou associação
(WIFI_DIAG: STATUS6/REASON2, AUTH_EXPIRE). Perfil experimental
`-DLAYLAY_WIFI_POTENCIA_BAIXA=1` reduz TX para8,5dBm; novo build1.090.491/41.368
bytes gravado e verificado, sem mudar NVS. A mesma falha persistiu após reduzir
potência e após reposicionar a antena, conforme confirmação humana.
Esses controles não provaram senha incorreta ou defeito físico. Teste em outra
rede permanece necessário para separar roteador/configuração de placa.
WIFI_DIAG1 é consulta USB sem credenciais; callback Wi-Fi publica somente o
código em variável atômica e não altera motores, sessão ou I2C.

Controle em hotspot2,4GHz: associação confirmada pelo usuário e pelo
WIFI_STATUS CONNECTED/IP10.68.192.221; WIFI_DIAG STATUS3. Esse sucesso
falsifica incapacidade geral de associação da placa. Não confirma autenticação
no roteador de casa, comandos TCP ou causa única da falha anterior. PC ficou
na rede original e não alcançou TCP8765 no hotspot. Teste não ativou JSON da
Laylay, não enviou MOTOR e não confirmou rosto/parada por TCP. A placa conserva
temporariamente a rede do hotspot; configuração da rede de casa permanece
pendente de diagnóstico do roteador.

## Rede local criada pelo PC (validada em 11/10/2026)

O hotspot móvel falhou neste Broadcom. O driver não oferece Wi-Fi Direct GO,
mas o Hosted Network antigo iniciou via API sem administrador. O PC manteve
SSID/BSSID original e canal9; ESP autenticou na rede `Laylay-Corpo-PC`.
Primeiro havia associação sem IP, sem UDP67 no PC. Consulta elevada confirmou
nenhum ICS completo ativo; parar somente SharedAccess com a rede do teste
encerrada e reiniciar a rede hospedada ativou DHCP. ESP recebeu192.168.137.52,
ping respondeu e AUTH/READY/ACK/SACK foram confirmados por TCP8765.

O provisionador agora tenta o handshake até três vezes, separadas por1s,
antes de falhar: conexão recém-configurada apresentou dois timeouts de800ms
e confirmou na terceira tentativa. Nenhum MOTOR é enviado nesse fluxo;
JSON só é ativado após rosto e parada. Teste RED canônico→GREEN usando o owner
Python e TCP real também preserva falha permanente e SACK ausente.

Pode abrir a Laylay normalmente enquanto a rede local estiver ativa. Para
iniciar rede local e Laylay juntas nas próximas sessões, execute da raiz:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\firmware\rosto_laylay\iniciar_laylay_com_rosto.ps1 -HotspotLocal
```

O launcher solicita explicitamente esse modo, reutiliza um gerente existente
ou inicia o script oculto. Só encerra o gerente que criou. O gerente monitora
a conexão original, não altera ICS completo, mantém chave temporária e
restaura o SSID anterior ao encerrar. Não há alteração de inicialização do
Windows nem de rede ao importar Python. A senha gerada fica somente no JSON
pessoal ignorado `memoria/corpo_hotspot_windows.json`; token separado em
`memoria/corpo_wifi.json`. Nunca publique esses arquivos.

Composição instalada + heartbeat real confirmou frente/ré/giros, MACK/SACK e
GACK da exceção controlada. O primeiro probe importava a composição sem iniciar
o serviço periódico e encontrou sessão expirada; mantido como evidência, não
removida a proteção do firmware. Probes posteriores executaram o mesmo método
registrado no supervisor e encerraram o heartbeat e a tração. Pedro confirmou
fisicamente os dois motores girando/parando e o glitch na repetição por Wi-Fi.
Não houve prova de deslocamento, entrega de voz ou autonomia espontânea.
Regressão focada final:178 testes passaram. Os contratos USB agora isolam o
pareamento pessoal do PC; testes de TCP usam seus próprios endpoints. Scripts
PowerShell tiveram análise de sintaxe sem erros. O launcher novo teve validação
de sintaxe; a sessão física validou o gerente e o serviço Python separadamente.

#line 1 "C:\\Users\\pbarr\\Downloads\\pasta organizada\\programacao\\PY\\projeto lay\\laylay\\firmware\\rosto_laylay\\LEIA-ME.md"
# Rosto físico da Laylay — primeiro teste

Controle por rede local: veja [configuração do Wi-Fi](WIFI.md).

ESP32-C3 Super Mini, OLED I2C SSD1306 0,96″ **128×64**.
SDA → GPIO **8**, SCK/SCL → GPIO **9**, GND → GND, VCC → 3V3.
O firmware procura o OLED em 0x3C e 0x3D. O perfil padrão controla o rosto
e mantém os motores desativados. A fonte também contém um perfil de bancada;
consulte [montagem e alimentação dos N20 de 3 V](MONTAGEM_MOTORES.md) antes de
gravar ou alimentar a ponte. Os comandos corporais naturais estão instalados
para pulsos curtos, com confirmação da ponte e sem medir deslocamento.

**Estado atual da COM4:** após validar o hack, Pedro autorizou liberar outros
motores de teste (não os N20) na protoboard. A placa recebeu o perfil de bancada
com motores=1, mapa AIN1/2→GPIO1/2, BIN1/2→GPIO3/4 e SLEEP→GPIO7. Os dois giraram
nos dois sentidos e pararam com pulsos de 250 ms / PWM255, conforme confirmação
humana. A integração atual aceita pedidos pela conversa; iniciativa corporal
espontânea ainda depende de um modo próprio, sem herdar permissões de IoT/áudio.
Uma compilação padrão no Arduino IDE continua com motores=0; os perfis são explícitos.

## Boca, falhas e comandos corporais — atualização de 11/10/2026

A boca abre em ciclos de amplitudes variadas, fecha entre eles e muda a largura
suavemente. Ao abrir, reduz a curva emocional para evitar o contorno torcido.
O sinal continua sendo `falando`, sem análise de fonemas ou do áudio. Pedro
confirmou no OLED: **"Sim, ficou melhor"**.

Falhas aceitas do executor e exceções observadas publicam uma ocorrência
transitória pelo mesmo owner de atividade. O OLED recebe um glitch de 900 ms:
faixas deslocadas, ruído localizado e recuperação do rosto. Recusa, cancelamento,
pendência, texto emocional, plano e booleano isolado não disparam o efeito.
A ocorrência vale 2 s e é consumida antes do envio, sem replay na reconexão.
Falha da animação não altera o resultado da ação. O glitch prevalece visualmente
sobre o hack durante seu breve intervalo, sem mudar a emoção.

```text
GCAPS 1 a1b2c3d4
GCAPS 1 a1b2c3d4 GLITCH1
GLITCH 1 a1b2c3d4 1 900
GACK 1 a1b2c3d4 1 900
MCAPS 1 a1b2c3d4
MCAPS 1 a1b2c3d4 MOTOR1
STOP 1 a1b2c3d4 1
SACK 1 a1b2c3d4 1
```

GLITCH exige FACE vigente, sequência própria e TTL de 500–1.600 ms. GACK ocorre
após frame, probe I2C e relógio fresco; não confirma efeito da habilidade.
MCAPS distingue perfil preparado `MOTOR1` de `MOTOR0`; não prova cabeamento/giro.
STOP correlacionado corta primeiro, valida depois; STOP legado continua aceito.
Receipts de sessões diferentes não completam um movimento. Parada interrompe
a espera por MACK e o pulso; cancelamento não vira sucesso nem falha visual.

Com a Laylay aberta e o ESP detectado, exemplos: **"ande para frente"**,
**"ande para trás"**, **"vire para a esquerda"**, **"vire para a direita"**,
**"pare os motores"** e **"de novo"** após uma ação confirmada. O padrão é
PWM255 por até 250 ms; limite de firmware/porta: 500 ms. Cada pedido precisa
de autorização do turno e de MACK+SACK próprios. Perguntar sobre a capacidade
não aciona motores; rosto/hack/glitch também não autorizam tração.

Firmware atual na COM4: core 3.3.12, perfil motor=1, 387.950 bytes programa /
15.836 RAM, hash da flash verificado. SHA256 `.ino`:
`7fccfad8e05c8f3ce397961d56e11f8507c351ca9fb202658f7176f83b4d2425`.
425 regressivos relevantes + 22 subtests passaram; hosts dos perfis 0/1
protegem motor, receipts, overlays, tempo e boca. A integração instalada/USB
real recebeu quatro MACK e SACK, parada explícita e GACK de uma exceção
controlada de demonstração. Isso não foi falha de uma habilidade externa real.
Receipts e prévias ficam em `artifacts/rosto_oled/glitch_boca/`.

Validação assistida com a Laylay/Monitor Serial fechados e a bancada sem rodas:

```powershell
.\.venv314\Scripts\python.exe -m scripts.validar_corpo_glitch_fisico --demo
```

`DEMO_FALA` e `DEMO_GLITCH` também são demonstrações locais no Monitor Serial;
cortam os motores antes de iniciar. HELLO cancela a demonstração. Giro/parada
visíveis e inspeção do glitch continuam evidências humanas separadas dos ACKs.
Na repetição da sequência natural pela composição instalada, Pedro confirmou
**"Sim, giraram e pararam"**; no DEMO_GLITCH, **"Sim, ficou legal"**. As
demonstrações foram encerradas com STOPPED+READY e a placa voltou ao sono,
aguardando a conexão automática. Não houve teste de deslocamento no chão ou
entrega da conversa com voz/interface completa nesta sonda.

## Animação de hack durante ações — 11/10/2026

Um mini terminal entra sobre o rosto em cerca de 300 ms: texto fictício digitado,
linhas rolando, cursor piscando e indicador indeterminado. Quando o tratamento
termina, o painel sai e revela a emoção atual; a animação facial continua por
baixo. Ações rápidas recebem um pulso visual mínimo de 0,8 s a partir do início.
Falha, exceção e cancelamento também encerram o escopo. Conversar ou ter um plano
recente não é sinal de execução.

O owner compartilhado é `AtividadeOperacionalRuntime`, instalado no ciclo após
deduplicação, nos executores de autonomia, no resumo assíncrono e na seleção
de saída de áudio. Publica apenas contagem de escopos e relógio transitório em
`mental.atividade_operacional`. Não armazena texto pessoal, não altera emoções,
não autoriza ações e não confirma seus efeitos. É observação de tratamento:
inclui validação e possíveis recusas dentro do despacho, sem prometer sucesso.

A extensão serial é negociada sem mudar HELLO/FACE:

```text
HELLO 1 a1b2c3d4
READY 1 a1b2c3d4 SSD1306 128 64
CAPS 1 a1b2c3d4
CAPS 1 a1b2c3d4 HACK1
FACE 1 a1b2c3d4 1 0 1 0 3500
ACK 1 a1b2c3d4 1 0 1 0
ACTIVITY 1 a1b2c3d4 1 1 1200
AACK 1 a1b2c3d4 1 1
ACTIVITY 1 a1b2c3d4 2 0 1200
AACK 1 a1b2c3d4 2 0
```

ACTIVITY tem sequência própria, booleano 0/1 e TTL de 500–2.000 ms. Só é aceita
na sessão de FACE vigente; não renova FACE nem motores. AACK correlaciona aplicação
após o frame e presença I2C, sem prova óptica ou receipt da ação. Ausência de AACK
degrada somente o efeito; a face recém-confirmada continua disponível. Firmware
anterior continua recebendo FACE e não recebe ACTIVITY sem negociar HACK1.

Sem atualização, o hack expira; perda da sessão devolve o sono. Para inspecionar
apenas o desenho no Monitor Serial, `DEMO_HACK` alterna rosto e terminal e corta
os motores. Um HELLO cancela o demo. O perfil padrão usa
`LAYLAY_HABILITAR_MOTORES_BANCADA=0`, sem habilitar PWM de tração; movimento
permanece uma integração separada. Prévia gerada do renderer real e receipts
da atualização ficam em `artifacts/rosto_oled/hack/`.

Validação: 241 regressivos relevantes aprovados; host do .ino protege o overlay
e os dois perfis motores. C3/core 3.3.12: 376.548 bytes programa / 15.748 RAM
com motores=0. Gravação COM4 com hash verificado; caminho instalado e serial
real produziram 14 ACK FACE e 14 AACK em repouso/escopo controlado/retorno,
sem MOTOR. Pedro confirmou no OLED: **"Sim, ficou legal e fluido"**.
A prova controlada não substitui observar uma ação natural na conversa.
O HELLO da Laylay encerra DEMO_HACK e retoma a sincronização habitual.

## Gravar

Abra `rosto_laylay.ino` no Arduino IDE. Selecione **ESP32C3 Dev Module**,
**USB CDC On Boot: Enabled** e a porta que aparece ao conectar a placa.
Bibliotecas: **Adafruit SSD1306**, **Adafruit GFX Library**, **Adafruit BusIO**.
Compile e envie. GPIO9 também participa do boot da C3; se a placa não iniciar,
verifique a conexão/pull-up do módulo e não mantenha BOOT pressionado ao reiniciar.

No boot o rosto dorme, com olhos fechados, respiração lenta e Zs subindo. No Monitor Serial,
115200 baud, final de linha Nova linha, envie `DEMO` para percorrer as nove
expressões, 3,5 segundos cada; o `D` no canto identifica demonstração.
A demonstração é local, não altera emoções da Laylay. Reinicie para sair,
ou conecte a Laylay (o handshake também cancela a demonstração).

## Validação desta entrega

- Compilação ESP32-C3 no core 3.3.12: 365.524 bytes de programa, 15.508 de RAM estática.
- Gravação na COM4: chip ESP32-C3 confirmado e hash da flash verificado pelo esptool.
- Composição real importada: três frames calmos confirmados pelo ESP, sem dublê serial.
- Todas as nove emoções e os estados de fala aceitos com ACK correlacionado na placa.
- Pedro confirmou no OLED: “Sim, aparecem e animam”. DEMO ficou ativo para inspeção.
- 116 testes relevantes aprovados, incluindo composição real, catálogo e segurança.
- Uma falha de `test_coerencia_capacidade_documentada.py` sobre indisponibilidade
  musical também foi reproduzida carregando o mapa de HEAD anterior ao patch:
  `1 failed, 56 passed`. Está fora da raiz do rosto e não foi corrigida nesta entrega.
- Receipt de hardware e SHA256 da fonte: `artifacts/rosto_oled/receipt_fisico.json`.

A fala fonética e uma conversa completa com emoção espontânea ainda não foram
observadas no OLED. A conexão usa a fonte emocional canônica, sem inventar
emoção para o teste. Para uso normal, abra a Laylay normalmente:
a conexão automática encerra DEMO e liga a tela ao estado real da Laylay.

## Conectar à Laylay

Feche o Monitor Serial para liberar a porta. **Não é mais necessário informar
COM nem usar um launcher especial.** Abra a Laylay pelo seu meio habitual,
ou, no PowerShell, na raiz do projeto:

```powershell
.\.venv314\Scripts\python.exe laylay.py
```

Sem `LAYLAY_ROSTO_PORTA` (ou com `AUTO`), o supervisor procura uma única USB
nativa da Espressif, VID 303A/PID 1001, e verifica o firmware pelo handshake.
Nenhum frame é enviado antes de `READY` correto e correlacionado à sessão.
Se você conectar o ESP depois de abrir, ele será encontrado na próxima busca,
em aproximadamente três segundos. Desconexão invalida o receipt, fecha a porta
e volta a procurar: mudança de COM também é aceita.

Se houver duas placas candidatas, a Laylay aguarda em estado indisponível.
Porta ocupada pelo Monitor Serial ou outra instância também é aguardada,
sem declarar sucesso. Para escolher uma porta manualmente, use o launcher
com `-Porta COM5` ou `LAYLAY_ROSTO_PORTA=COM5`. Para desativar, use
`LAYLAY_ROSTO_PORTA=off`. O launcher aceita execução sem argumentos e usa AUTO.

Atualização da detecção automática: RED reproduzido na ausência de configuração
manual e no caso em que a placa chega depois da inicialização; testes cobrem
essas fronteiras, ambiguidade, porta ocupada, firmware alheio e reconexão em
outra COM. O firmware gravado continua o mesmo. A verificação física atual
encontrou a COM4, mas não abriu porque a Laylay em execução já possui a porta;
o resultado foi registrado em `artifacts/rosto_oled/receipt_automatico.json`.
Reinicie a instância aberta para carregar este código. A prova de ACK do
transporte físico anterior permanece válida; auto-reconexão física ainda não
foi observada retirando e recolocando o cabo nesta atualização.

`pyserial==3.5` foi acrescentado às dependências e já está instalado no ambiente
usado nesta validação. Em outra instalação, instale-o no mesmo Python da Laylay.

## Contrato e limites

O owner emocional é `retrato_emocional_expressavel`: causa ausente, expirada
ou contida resulta em calma. O ESP recebe apenas índice, intensidade 1–3 e
estado booleano de fala. Não recebe conversas, causas pessoais ou credenciais.
A boca acompanha atividade de fala; não é sincronização fonética ou por áudio.
Animação local a ~30 FPS, interpolação de olhos, pálpebras e boca, piscada com
fechamento rápido e abertura suave, e atualização da mente a ~3 Hz.
Expressões: calma, alegre, triste, brava, irritada, surpresa, envergonhada,
debochada e acalmando-se. A última tem pose suave, próxima de calma.

O protocolo v1 usa sessão aleatória e sequência crescente:

```text
HELLO 1 a1b2c3d4
READY 1 a1b2c3d4 SSD1306 128 64
FACE 1 a1b2c3d4 1 1 2 0 3500
ACK 1 a1b2c3d4 1 1 2 0
```

ACK é emitido depois de enviar o frame ao display e verificar presença I2C.
Confirma o caminho de firmware; **não é medição óptica de pixels**. Sem ACK,
o catálogo declara rosto indisponível. Sem atualização por 3,5 segundos,
o firmware dorme e encerra a animação de fala. O HELLO sozinho não o acorda:
é necessário receber um FACE válido. A sessão expirada é invalidada; o host
renova o handshake quando o último ACK tem mais de 2,5 segundos.
Reconexão usa a amostra atual e nova sessão, sem fila de emoções antigas.
Ponto no canto inferior direito: fixo conectado. DEMO é uma exceção local
explícita ao sono; o D identifica a demonstração até o próximo handshake.

Esta capacidade é um consumidor de expressão, não um executor de linguagem.
Reutiliza contexto, causa emocional, observabilidade, catálogo e supervisor
compartilhados. Não cria memória durável, decisões de aprendizagem, pendências
ou planos de cooperação: não há novos pedidos de ação nem duas habilidades
operacionais compondo efeitos. Isso evita inventar parsers ou autoridade.

## Pedir expressões e voltar ao normal

Na conversa habitual: `fique brava`, `fica um pouco triste`, `fique envergonhada`,
`faça uma carinha feliz`, `mostre uma expressão surpresa`, `fique irritada` ou
`fique debochada`. `Lay, fica bem triste` aumenta a intensidade; `um pouco`
reduz. `volte ao normal` e `fique calma` cancelam a pose anterior.

A leitura canônica do turno publica um episódio de expressão solicitada,
depois o owner compartilhado aplica a pose. Ela substitui uma pose anterior
mesmo mais intensa, sem alterar o humor acumulado. Dura até 60 segundos,
sujeita ao decaimento por interações, ou até outra reação/pedido válido.
Não é memória durável, prova de sentimentos humanos nem autorização para
ações externas. Citação, hipótese, negação, outro alvo e pedidos compostos
não são interpretados como ordem certa de pose. A fala acompanha a encenação
com uma resposta curta; OLED e avatar consomem o mesmo estado.

## Atualização de animações e expressão solicitada — 10/10/2026

Olhos maiores e arredondados, pálpebras e sorriso interpolados, rubor de
intensidade variável, olhos alegres em arco e sono animado. Firmware compilado
para C3: 366.620 bytes de programa e 15.532 de RAM estática; gravado na COM4
com hash verificado. Pedro confirmou fisicamente o sono: “Sim, aparece e anima”.
As nove poses/controles da composição instalada receberam ACK na placa;
`receipt_expressoes_usb.json` conserva essa coleta. Prévia de pixels do .ino:
`artifacts/rosto_oled/expressoes.gif`. Não é gravação óptica do OLED.

422 testes relevantes aprovados, incluindo comandos naturais, mesma causa
em plano/fala/estado/rosto, troca por pose menos intensa, calma, segurança,
catálogo, regressão social e renovação de sessão. O renderer host verifica
frames diferentes em todas as poses, sono, despertar, TTL, relógio com wrap,
sessão antiga, falha I2C e ACK após frame. Coletas do modelo preservam o bruto
e a identificação de replay: a primeira coleta mostrou interrogatório/aula
indevidos; o contrato de autoria passou a exigir reação breve sem perguntas.
`receipt_expressoes_final_v3.json` conserva nove falas aceitas após reparo ou
contingência, 13 ACKs antes da autoria e nove ACKs depois. Os brutos principais
são replay identificado de coleta real; os reparos usaram o modelo configurado.
ACKs vieram da COM4 detectada automaticamente. Nesta sonda não há supervisor
contínuo: uma pausa do modelo deixa o firmware dormir; o handshake renovado
acorda com a amostra atual e evita rejeição da sessão antiga.
A conversa completa com voz, avatar e OLED na interface ainda exige inspeção
humana após abrir a versão atual. Nenhum commit criado.

### Fluidez das poses — continuação em 10/10/2026

O renderer agora usa uma única geometria interpolada para olhos e boca:
olho arredondado, arco alegre, pálpebra inclinada, sorriso, tristeza, deboche,
surpresa, abertura de fala e sono se transformam progressivamente. Rubor,
sobrancelhas e lágrima também entram/saem aos poucos. A velocidade depende do
tempo entre frames, com constantes de cerca de 240–350 ms, e o balanço conserva
sua fase ao trocar emoção. A transição costuma chegar perto da pose final em
aproximadamente 0,7 s. A boca de fala usa resposta mais rápida, de 85 ms.

RED no renderer real: calma → alegre alterava 1.164 pixels no primeiro frame.
Com a geometria única, foram 190. As 100 combinações entre nove emoções e sono
passaram: maior primeiro passo de 291 pixels, limite de 350. Piscadas/olhares
foram controlados nesse teste para isolar a troca de pose. Esse indicador
protege contra substituição brusca, mas não é uma nota estética ou prova óptica.
Prévia contínua com piscadas, fala e dormir/acordar: `fluidez/transicoes.gif`
em `artifacts/rosto_oled`. O renderer host também conserva os testes de
protocolo, ACK, falha I2C, TTL e relógio. 109 regressivos relevantes aprovados.

Firmware compilado: 368.652 bytes de programa, 15.588 de RAM estática;
gravado na COM4, hash da flash verificado. O ACK confirma adoção do alvo e
envio do primeiro frame da animação; não afirma que a transformação já
convergiu ou que os pixels foram observados opticamente. Não houve alteração
nos owners de linguagem, emoção, voz ou catálogo nesta continuação.
Na composição instalada, as 13 amostras receberam ACK no firmware novo;
receipt em `artifacts/rosto_oled/fluidez/receipt_expressoes_usb.json`.
Após a sequência local na COM4, Pedro confirmou a fluidez física:
“Sim, ficou mais fluida”. DEMO foi encerrado com handshake e a tela ficou
pronta para dormir/aguardar a conexão automática da Laylay.

Base da implementação: `main`, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`.
As alterações preexistentes de streaming/UI e sondas foram preservadas.
Nenhum commit foi criado. A gravação na COM4 foi autorizada por Pedro nesta
conversa. Compilação e ACK não provam a imagem física: conferir piscadas,
todas as poses em DEMO e fala real na placa continua sendo validação visual.

O teste inicial na placa encontrou e reproduziu uma corrida no próprio
firmware: capturar `agora` antes do handler serial e registrar `ultimoPacote`
depois podia causar underflow e expirar o pacote recém-chegado. O RED host
agora avança `millis()` durante o handler. O relógio usado para verificar TTL
é lido depois da recepção, e o mesmo teste passou.

Documentação dos fabricantes: [I2C ESP32](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/i2c.html)
e [Adafruit SSD1306](https://github.com/adafruit/Adafruit_SSD1306).

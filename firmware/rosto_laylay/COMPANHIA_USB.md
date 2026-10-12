# Companhia corporal — USB e gestos expressivos

Execute `iniciar_companhia_usb.ps1` para abrir a Laylay na COM4. A seleção USB
vale para essa sessão e prevalece sobre o pareamento de rede salvo.

O firmware desta versão foi compilado com `LAYLAY_WIFI=0` e
`LAYLAY_HABILITAR_MOTORES_BANCADA=1`. Não liga o rádio Wi-Fi. Para recompilar,
use essas duas propriedades em `compiler.cpp.extra_flags`, placa
`esp32:esp32:esp32c3:CDCOnBoot=cdc`. O limite normal continua sendo 500 ms;
o perfil temporário de movimento contínuo de cinco segundos não está ativo.

Pinagem preservada: OLED SDA8/SCL9; DRV8833 AIN1/2 GPIO1/2, BIN1/2 GPIO3/4,
nSLEEP/EEP GPIO7. PWM dos quatro GPIOs: 1 kHz, oito bits.

## Pedidos na conversa

- `ative modo companhia na bancada`
- `ative modo companhia na área delimitada`
- `ative modo companhia com rodas suspensas`
- `desative modo companhia`
- `ative modo passeio na mesa com barreiras`
- `ative passeio na área delimitada`
- `desative passeio`
- `pare os motores`
- `ande para frente`, `ande para trás`, `vire para a esquerda/direita`

Com a preferência explícita `LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR=1`
salva em `configuracao.env`, a companhia na bancada ativa automaticamente
assim que a sessão USB e MOTOR1 estiverem confirmados. A conexão AUTO prefere
USB nesse perfil, mesmo com pareamento de rede salvo. Uma seleção explícita
de porta ou OFF continua prevalecendo. O passeio espontâneo exige seu próprio
pedido ou a preferência explícita adicional
`LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR=1`, para a área com barreiras.
Essa preferência adicional foi autorizada e salva por Pedro. Com ambas
ativadas, a primeira sequência começa após oito segundos de sessão pronta,
em silêncio e sem ação em andamento; depois as pausas variam de8–14s.

Sem essa preferência o modo companhia começa desligado. A concessão pertence à sessão USB atual,
sem expirar por tempo de conversa ou contagem de gestos. Reconexão, falha, parada e movimento
manual revogam a iniciativa. Na mesma execução, ativar novamente exige um novo pedido explícito;
o aprendizado e o silêncio não renovam a autorização.
Ao abrir novamente a aplicação, a preferência salva volta a valer.

## Gestos

A mente usa o mesmo retrato emocional causal que envia ao OLED. O perfil
`ritmo_emocional_v2` combina expressão, antecipação, reação, pausas e acomodação:

| Emoção | Gesto pretendido |
| --- | --- |
| Alegria | Avanço e recuo em um balanço animado |
| Tristeza | Pausa mais longa e recolhimento |
| Braveza | Quatro giros alternados, como uma negativa enfática |
| Irritação | Desvio lateral, pausa e retorno parcial |
| Surpresa | Recuo imediato |
| Vergonha | Pequeno giro, hesitação e giro contrário |
| Deboche | Giro lateral mais demorado e resposta curta |
| Fala | Ênfase com pequeno giro alternado |

A intensidade muda o tempo e o lado dos giros varia entre gestos. Calma
permanece no rosto e repouso; não cria movimento periódico dos motores.
No modo passeio, o repouso pode dar lugar a pequenas sequências espontâneas,
alternando avanço, recuo, curva e olhar lateral a cada 8–14 segundos. Elas
aguardam o silêncio e o fim de ações em andamento. Esse modo exige a área
declarada na ativação e mantém a mesma concessão USB e parada do modo companhia.
Usa PWM100, até quatro movimentos de 50–500 ms por gesto, até 1500 ms totais
de motor e até 2400 ms de tempo planejado com pausas, com pelo menos dois
segundos entre inícios. O tempo de espera por receipts é separado desse tempo
planejado e o plano completo expira em cinco segundos. Mudanças
durante esse intervalo são descartadas; não formam uma fila de movimentos.

O coordenador cooperativo primeiro verifica o ACK do mesmo rosto e depois
aciona a ponte. O transporte revalida a concessão imediatamente antes de
cada MOTOR, exige MACK e SACK de cada movimento e não reenvia após falha.
As pausas não bloqueiam STOP. Uma expressão substituída interrompe o gesto
antigo sem produzir glitch de falha; uma falha real do executor continua
revogando a concessão e alimentando o observador operacional. Uma execução
automática confirmada não é registrada como preferência aprovada pelo usuário.
Falhas operacionais usam o observador já existente para o efeito de glitch.

## Comemorações

O observador operacional compartilhado publica uma ocorrência transitória de
sucesso apenas para `ResultadoAcao` aceito, com identidade, origem executor,
execução e confirmação positivas. Receipts dos próprios motores e de concessão
não provocam outra comemoração. O sinal não concede autoridade: somente o modo
companhia ativo permite o movimento. Sucessos anteriores à ativação não são
reproduzidos. O pedido composto publica o sinal somente ao concluir todas as
etapas; falha parcial e cancelamento descartam a comemoração do lote.

As três variações são balanço, dancinha e giro de vitória por tempo. As duas
primeiras reutilizam os tempos práticos de `comemorar` e `wiggle` do projeto
`control_display`, com a pinagem atual preservada. O giro não é anunciado como
360 graus: sem encoder, seu tempo precisa ser calibrado na montagem real.
Parada e perda da sessão interrompem todas as variações, sem replay.

Referências de composição expressiva: [apresentação da equipe Anki na GDC](https://www.gdcvault.com/play/1024488/Cozmo-Animation-Pipeline-for-a)
e [estudo e código do SHARE Lab](https://github.com/shareresearchteam/expressive_cozmo_behaviors).
Os perfis da Laylay são próprios, adaptados aos dois motores e ao OLED; não
copiam animações, código, ângulos nem velocidades do Cozmo. Giro contrário não
prova retorno à mesma posição: não há odometria nesta montagem.

Não há navegação, leitura física do ambiente nem detecção de bordas/obstáculos
nesta versão. Um ACK confirma aplicação de PWM e desenergização da ponte;
não mede giro, posição, alimentação ou temperatura. Alimentar pelo USB não
garante ausência de queda de tensão. A adequação da alimentação e o sentido
das rodas ainda precisam ser conferidos na montagem final.

## Validação

Testes Python verificam concessão, autoridade, composição instalada,
aprendizado, catálogo, falha parcial, parada, concorrência e ausência de replay.
Testes host verificam o firmware real com GPIO/I2C simulados. A gravação e os
receipts FACE/MOTOR1/SACK foram verificados na COM4. A observação dos novos
gestos na montagem física permanece pendente; testes simulados não a substituem.

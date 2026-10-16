# Proteção corporal — 14/10/2026

## Comportamento atual: presença e linguagem corporal

Esta seção substitui a sequência V1 descrita no histórico abaixo. A sessão
FACE permite expressão mesmo parada; não concede movimento. `PCAPS` negocia
`VIGIA1`. O mesmo owner USB renova `SENTRY` de1200ms somente com concessão
de companhia vigente para aquela sessão e sem prioridade de interação/tarefa.
Concessão, leitura e expressão continuam sendo contratos diferentes.

- Borda: susto, recuo250ms/PWM120; persistindo, até três recuos de120ms/PWM110,
  separados por320ms parada. Pavor permanece nos olhos; não há tremor de motor.
  Sem confirmação de superfície não gira nem avança. Termina bloqueada após
  esgotar os passinhos; não repete recuo infinito no mesmo episódio.
- Parede: irritação, recuo250ms/PWM160, pausa100ms, até quatro giros por rodada
  (160/240/400/320ms/PWM170), alternando o lado após as duas primeiras tentativas.
  Para entre giros e exige três leituras novas de ambos os sensores, superfície
  inferior<=120mm e frente>120mm ou inválida recente, antes de avançar400ms.
  Sem saída, `ESPERA_BUSCA`: repousa4s e só recomeça com risco de parede ainda
  presente e concessão renovada. O relógio não apaga STOP/falhas/borda.
- Se a borda deixou de existir mas uma parede permanece, três novas medições
  inferiores<=120mm admitem um novo episódio de parede, com concessão vigente.
  A trava do episódio anterior não exige frente livre para começar a procurar;
  isto não libera avanço nem remove os vetos de sessão/STOP/falha.
- Cada rodada tem teto absoluto3s; TTL, STOP, leitura velha, I2C/PWM/tela com
  falha cortam. Sem perigo, a proteção não cria movimento espontâneo.
- Sons locais distintos para susto, medo hesitante, resmungo e procura; pequenas
  variações de afinação, mesmo duty128/255 e corte450ms. Intervalo mínimo1,5s;
  alertas persistentes sem motor têm pausa8s. Sons0..8 e sono não mudaram.

`GUARD` conserva os dez campos legados e acrescenta reação/tentativa/vigia.
Fases novas: BUSCANDO, CONFERINDO, ESPERA_BUSCA, ESPERA_MEDROSA, RECUO_MEDROSO.
A mente e o DEV recebem a fase real. DEV→Corpo também mostra se a placa
confirmou a autorização renovada; companhia ativa sozinha não prova isso.

**Não existe sensor traseiro: esses recuos são limitados, não uma afirmação de
que há chão atrás. Validado logicamente para a bancada com rodas suspensas;
não é garantia antiqueda em uma mesa.** A condição inferior inválida ou>130mm
continua tendo prioridade sobre parede. Não alterar limiar para forçar teste.

## Histórico V1 e evidência de latência

Um owner decide cada coisa: VL53L0X mede, o ESP veta/interrompe e executa o
reflexo finito, o owner USB preserva os receipts e a mente interpreta os fatos.
A emoção/LLM não concede autoridade nem pode ignorar a proteção local.

Limites aprovados mantendo a altura inferior perto de 10cm:

| Entrada | Política |
|---|---|
| Inferior válido <=130mm | Superfície dentro do limite |
| Inferior válido >130mm | Borda: interromper e reagir |
| Inferior INVALIDA recente | Sem retorno: tratar como borda |
| Frontal válido <=100mm | Obstáculo: interromper e reagir |
| Frontal INVALIDA recente | Distância desconhecida; não inventar parede |
| Sensor ausente, aguardando, falha I2C | Cortar/bloquear; não iniciar manobra cega |
| Inferior >75ms ou frontal >150ms | Dado velho para tração: cortar/bloquear |

DIST conserva o contrato diagnóstico de até300ms. A proteção aplica prazos
mais curtos próprios: não confundir validade diagnóstica com validade para mover.
Para rearmar após um episódio, requer3 amostras inferiores novas <=120mm e
frontal >120mm ou INVALIDA recente (histerese). Não repete recuos enquanto
a mesma condição permanece bloqueada.

Reflexo após uma ordem de movimento vigente: corte antes de bip/expressão,
recuo250ms PWM120, pausa100ms, giro900ms PWM140, verificação parada até500ms,
avanço400ms PWM120 somente após3 novas amostras seguras. Limite absoluto3s,
TTL da sessão, STOP, falha da tela/PWM/I2C cancelam. Não inicia passeio em repouso.
O pedido original fica interrompido, mesmo se o reflexo termina normalmente.

**Giro por tempo não mede180°. Um sensor inferior dianteiro não cobre a
traseira/laterais; o recuo curto não tem confirmação de mesa atrás.** Os testes
atuais são com rodas suspensas/sensores na protoboard; não houve validação
antiqueda em deslocamento real nem medição de distância de frenagem.

## Latência

Primeira fronteira medida: atualização OLED completa bloqueava a observação do
sensor. Firmware instrumentado na placa mediu intervalo inferior até85ms e
render até35ms. Novo perfil usa orçamento20ms, I2C400kHz, timeout5ms, leitura
inferior prioritária antes da frontal, e imagem em blocos32bytes durante tração
ou reação; entre blocos lê sensores/corta motores. Sono/repouso conservam o
envio normal. Watchdog75ms corta tração com leitura inferior velha.

Após gravar a versão rápida, PERF mediu intervalo inferior até38ms na janela
de reação, com25–29ms nas janelas seguintes. Render pode demorar mais no total,
pois é intercalado com segurança. **Esses números medem cadência das amostras,
não o tempo físico entre uma borda real e a roda parar.**

## Protocolo e integração

DCAPS 1 sessão → DCAPS 1 sessão SENSORES2. Depois de FACE confirmado, o mesmo
owner consulta DIST e GUARD. GUARD fornece sessão/consulta/incidente/ordem/risco/
fase/limiares; HAZARD correlaciona interrupção ao MOTOR original. Nenhuma mensagem
de leitura arma motores ou restaura concessão. Firmware sem SENSORES2 continua
compatível sem alegação de sensores. PERFs são diagnósticos manuais, sem MOTOR.

Leituras e proteção chegam a modelo_corporal/percepcao_fisica, disponibilidade
operacional, catálogo e DEV. No DEV aparecem somente na opção Corpo; variação
de mm atualiza o painel sem gerar um log por leitura. Publicação na mente é
transitória; o histórico recebe a experiência/receipt do owner existente.
Interrupção por proteção preserva a companhia, cancela a coreografia corrente,
aguarda superfície segura e não repete a emoção interrompida.

Perfil da placa: USB, motores1/2 e3/4, SLEEP7, OLED/sensores SDA8/SCL9,
XSHUT frente0/inferior10, som6. Compilar com as flags anteriores mais
`-DLAYLAY_PROTECAO_CORPORAL=1`. Dependência local Adafruit_VL53L0X1.2.5.

Provas e pendências: artifacts/rosto_oled/protecao_sensores.

## Busca interrompida por prioridade temporária

SENTRY0 ou expiração da lease cortam imediatamente a iniciativa local. Uma
busca de parede originada pela vigia passa a ESPERA_BUSCA, preservando o
descanso de4s; SENTRY0 repetido não reinicia esse relógio. Ao voltar a concessão
na mesma sessão, só admite outro incidente após três amostras inferiores novas
<=120mm, com leituras recentes e obstáculo ainda confirmado. Não retoma o giro
interrompido. STOP/GOODNIGHT, perda de sessão/tela, limite absoluto da manobra e
falhas continuam cancelando/bloqueando. Borda persistente não ganha recuos
ilimitados. A concessão continua pertencendo à companhia no PC; a distância
não autoriza movimento. Evidências: pausa_busca dentro do diretório acima.

Se uma borda interromper uma busca já iniciada, o executor conserva essa causa
de bloqueio separada da causa inicial do incidente (parede). Ao desaparecer a
borda, a mesma admissão de três amostras inferiores seguras pode abrir outro
episódio de busca. Uma falha de barramento/PWM não vira borda resolvida. STOP
também cancela um episódio já bloqueado: heartbeats seguintes não o rearmam.

## MOTOR recusado durante um reflexo

Uma reação local já em andamento pode disputar o corpo com um comando do PC
chegado após a última consulta GUARD. Tanto nas pausas quanto com PWM local
ativo, a admissão responde HAZARD com sessão e sequência do comando recusado.
Não emite MACK, não reinicia o incidente e não troca os PWM da reação local.
Uma repetição da mesma sequência é rejeitada. Ocupação por outro MOTOR normal
continua MOTOR_OCUPADO; STOP continua prioritário. Isso permite ao owner do PC
distinguir interrupção por proteção de ausência de confirmação elétrica, sem
revogar a companhia por uma disputa normal. Provas RED/USB/main real em
artifacts/rosto_oled/admissao_motor_reflexo/RELATORIO.md.

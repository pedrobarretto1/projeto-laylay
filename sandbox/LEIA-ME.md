# Bancada virtual da Laylay

Feche a Laylay normal e execute `Iniciar.cmd` para abrir a bancada no
navegador e iniciar a Laylay conectada somente ao corpo virtual.
A tela aguarda a indicação **Laylay conectada**. A primeira compilação usa
as ferramentas C++ do Visual Studio no Windows ou G++ disponível no PATH.

- **Pegar** arrasta a caixa. **Girar** muda a orientação. **Inclinar** muda
  roll e pitch e permite tombar o corpo. **Nivelar** volta à posição neutra.
- O rosto distingue inclinação leve, corpo de lado, em pé e de ponta-cabeça.
  Manuseio persistente ou repetido pode gerar um resmungo. A tração fica
  bloqueada durante o desequilíbrio. Após nivelar, o modo companhia pode
  fazer um giro breve se a IMU e o sensor frontal confirmarem condição segura.
- Arraste o círculo pelo feixe frontal. O painel mostra a distância lida, a
  proteção, a IMU, o PWM e os pixels do OLED enviados pelo sketch.
  As quatro paredes da arena também devolvem uma distância ao sensor frontal.
- Na janela da Laylay, diga **ande para frente**, **vire para a direita**
  ou **pare os motores**. Use **Nivelar** após testar tombamento e aguarde
  a IMU indicar `PRONTA/ESTAVEL` antes de pedir movimento.
- O modo companhia inicia com a bancada. Quando está ociosa e pode andar,
  alterna avanços em etapas, curvas e giros de observação. Entre etapas,
  a Laylay revalida a concessão e o firmware pode cortar os motores. Quando
  há espaço frontal medido, a pausa é mais curta entre os primeiros passeios
  e mais longa depois. Conversa e comandos têm prioridade.
  **Pare os motores** ou **desative o modo companhia** encerra a concessão da sessão.
  Você pode pedir **ative modo companhia na bancada** para retomar.
- Um obstáculo que aparece perto ou rápido provoca surpresa. Uma chegada
  gradual provoca curiosidade. Se persistir, ela fecha mais os olhos. Quando
  o caminho volta a ficar livre, mostra alívio por um instante.
  A busca alterna o lado inicial entre encontros. Só vale insistir no
  primeiro giro se as leituras novas mostrarem mais espaço. Sem saída, a
  Laylay para e reavalia depois de quatro segundos, inclusive quando mede
  entre 100 e 120 mm. Durante a pausa, ela mantém a expressão de impaciência
  e desvia o olhar antes de tentar de novo. O avanço exige a confirmação de
  espaço prevista pelo firmware. A vigia e as leituras recentes continuam
  necessárias.
- Em **Firmware**, selecione um `.ino` ou `.h` e use **Salvar e aplicar**.
  Uma compilação bem-sucedida reinicia o firmware virtual e a Laylay renova a
  sessão. Se a compilação falhar, o firmware virtual anterior continua
  rodando e o diagnóstico do compilador aparece no editor.

Os arquivos editados ficam na primeira cópia em
`sandbox/firmware_edicao/rosto_laylay`. A primeira cópia recebe os ajustes
de postura, busca e expressão com o Git. Para levar um ajuste à placa, revise a
diferença e aplique-a ao firmware físico pelo fluxo habitual. O sandbox
executa o código do sketch no computador com adaptadores virtuais de GPIO,
OLED e sensores. A pose e os motores são aproximados. O perfil de host usa
IMU alinhada ao chassi e seleciona o sensor de borda conforme a variante
do código. Ensaios elétricos, temporização e tração real exigem o ESP32.

Esse modo separa o **corpo** da Laylay do hardware e registra as experiências
corporais da bancada somente durante a sessão. Outras funções da instalação
seguem sua configuração normal. Encerre primeiro a Laylay e
pressione Ctrl+C no terminal da bancada. Para usar só a bancada, execute
`python -m sandbox` na pasta da Laylay.

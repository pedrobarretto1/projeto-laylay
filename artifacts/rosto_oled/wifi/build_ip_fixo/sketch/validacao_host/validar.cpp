#line 1 "C:\\Users\\pbarr\\Downloads\\pasta organizada\\programacao\\PY\\projeto lay\\laylay\\firmware\\rosto_laylay\\validacao_host\\validar.cpp"
#include <cassert>
#include <filesystem>
#include <set>
// Apenas este dublê de bancada habilita o caminho MOTOR para regressão.
// O firmware gravado usa o perfil padrão 0, definido no .ino.
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"

void comando(const char *s) { Serial.entrada += s; Serial.entrada += '\n'; loop(); }

void exigirMotoresParados() {
  assert(niveisGpio[7]==LOW && !motorPendente && !motorAtivo);
  for (int pino : {1, 2, 3, 4}) assert(dutiesPwm[pino]==0);
}

void validarAtividade() {
  tempoSimulado=1000; comando("HELLO 1 01234567");
  Serial.saida.clear(); comando("CAPS 1 01234567");
  assert(Serial.saida.find("CAPS 1 01234567 HACK1")!=std::string::npos);
  assert(!conectado && !atividade); // CAPS não acorda nem autoriza ACTIVITY.
  comando("ACTIVITY 1 01234567 1 1 1000"); assert(!atividade && sequenciaAtividade==0);
  comando("FACE 1 01234567 1 6 2 1 3500");
  uint32_t faceOriginal=ultimoPacote, motorOriginal=inicioMotor;
  Serial.saida.clear(); comando("ACTIVITY 1 01234567 1 1 1000");
  assert(atividade && ackAtividadePendente && Serial.saida.find("AACK")==std::string::npos);
  assert(emocao==6 && nivel==2 && falando); // Efeito não fabrica outra emoção.
  assert(ultimoPacote==faceOriginal && inicioMotor==motorOriginal);
  tempoSimulado=1040; loop();
  assert(Serial.saida.find("AACK 1 01234567 1 1")!=std::string::npos && !ackAtividadePendente);
  uint32_t faseOriginal=inicioHack;
  tempoSimulado=1240; comando("ACTIVITY 1 01234567 2 1 2000");
  assert(atividade && inicioHack==faseOriginal); // Refresh conserva a fase.
  const char *invalidos[] = {
    "ACTIVITY 1 01234567 0 1 1000", "ACTIVITY 1 01234567 -1 1 1000",
    "ACTIVITY 1 01234567 +3 1 1000", "ACTIVITY 1 01234567 4294967296 1 1000",
    "ACTIVITY 1 01234567 3 2 1000", "ACTIVITY 1 01234567 3 -1 1000",
    "ACTIVITY 1 01234567 3 1 499", "ACTIVITY 1 01234567 3 1 2001",
    "ACTIVITY 1 01234567 3 1 4294967296", "ACTIVITY 1 01234567 3 1 1000 extra",
    "ACTIVITY 1 01234567 3 1", "ACTIVITY1 01234567 3 1 1000",
    "ACTIVITY 2 01234567 3 1 1000", "ACTIVITY 1 012345673 1 1000",
    "ACTIVITY 1 012345678 3 1 1000", "ACTIVITY 1 0123456g 3 1 1000",
    "ACTIVITY 1 01234567 3 1.0 1000", "ACTIVITY 1 01234567 3 1 +1000",
  };
  for (const char *entrada : invalidos) {
    Serial.saida.clear(); comando(entrada);
    assert(atividade && sequenciaAtividade==2 && ultimoPacoteAtividade==1240);
    assert(Serial.saida.find("AACK")==std::string::npos); exigirMotoresParados();
  }
  comando("ACTIVITY 1 ffffffff 99 0 1000");
  comando("ACTIVITY 1 01234567 1 0 1000"); assert(atividade && sequenciaAtividade==2);
  const char *capsInvalidas[] = {"CAPS 1 ffffffff", "CAPS 1 012345678", "CAPS 2 01234567",
                               "CAPS1 01234567", "CAPS 1 01234567 extra", "CAPS 1"};
  for (const char *entrada : capsInvalidas) {
    Serial.saida.clear(); comando(entrada);
    assert(Serial.saida.find("HACK1")==std::string::npos); exigirMotoresParados();
  }
  int pixelsTexto=0;
  for (int frame=0;frame<15;++frame) {
    tempoSimulado=1300+frame*33; loop(); exigirMotoresParados();
  }
  assert(painelHack==1);
  for(int y=14;y<=51;++y) for(int x=0;x<128;++x) pixelsTexto+=tela.pixels[y][x];
  assert(pixelsTexto>150); // Raster real de comandos, não print do stub no-op.
  // Glifo L: coluna esquerda e base completa da fonte compartilhada.
  assert(tela.pixels[2][2]==1 && tela.pixels[2][3]==0 && tela.pixels[8][6]==1);
  Serial.saida.clear(); tempoSimulado=1828; comando("ACTIVITY 1 01234567 3 0 1000");
  assert(!atividade);
  tempoSimulado=1861; loop(); assert(Serial.saida.find("AACK 1 01234567 3 0")!=std::string::npos);
  for(int frame=0;frame<12;++frame) { tempoSimulado+=33; loop(); exigirMotoresParados(); }
  assert(painelHack==0 && conectado && emocao==6 && falando);
  tempoSimulado=2300; comando("ACTIVITY 1 01234567 4 1 500");
  tempoSimulado=2800; loop(); assert(!atividade && conectado); // TTL próprio não dorme FACE.
  tempoSimulado=2840; comando("ACTIVITY 1 01234567 4 1 500"); assert(!atividade); // Replay expirado.

  // Primeira fronteira temporal: consulta I2C consome o TTL FACE.
  tempoSimulado=10000; comando("HELLO 1 12345678");
  comando("FACE 1 12345678 1 0 1 0 500");
  tempoSimulado=10490; Wire.demoraTransmissao=20; Serial.saida.clear();
  processarLinha("ACTIVITY 1 12345678 1 1 500");
  assert(!atividade && sequenciaAtividade==0 && Serial.saida.find("AACK")==std::string::npos);
  Wire.demoraTransmissao=0;
  // Receipt também revalida a vigência depois do frame e da segunda consulta I2C.
  tempoSimulado=11000; comando("HELLO 1 23456789");
  comando("FACE 1 23456789 1 0 1 0 3500");
  processarLinha("ACTIVITY 1 23456789 1 1 500");
  tempoSimulado=11470; Wire.demoraTransmissao=20; Serial.saida.clear(); loop();
  assert(!atividade && Serial.saida.find("AACK")==std::string::npos);
  Wire.demoraTransmissao=0;
  tempoSimulado=12000; comando("HELLO 1 3456789a");
  comando("FACE 1 3456789a 1 0 1 0 500");
  comando("ACTIVITY 1 3456789a 1 1 2000");
  tempoSimulado=12500; loop();
  assert(!conectado && !atividade && !ackAtividadePendente && painelHack==0 && estavaDormindo);
  comando("ACTIVITY 1 3456789a 2 1 500"); assert(!atividade);
  tempoSimulado=13000; comando("HELLO 1 456789ab");
  comando("FACE 1 456789ab 1 0 1 0 3500");
  comando("ACTIVITY 1 456789ab 1 1 1000");
  Wire.presente=false; tempoSimulado=13040; Serial.saida.clear(); loop();
  assert(!atividade && !ackAtividadePendente && !conectado && painelHack==0);
  assert(Serial.saida.find("AACK")==std::string::npos); Wire.presente=true;
  comando("HELLO 1 56789abc"); assert(!atividade && sequenciaAtividade==0 && painelHack==0);
  comando("FACE 1 56789abc 1 0 1 0 3500"); assert(!atividade); // Host antigo conserva rosto normal.
  comando("ACTIVITY 1 56789abc 1 1 1000"); comando("DEMO");
  assert(!atividade && !demoHack && painelHack==0 && !ackAtividadePendente);
  tempoSimulado=14000; comando("DEMO_HACK");
  assert(demonstracao && demoHack && !conectado && !sessao[0]);
  std::set<std::string> imagens;
  for(int frame=0;frame<180;++frame) {
    tempoSimulado=14000+frame*33; loop(); exigirMotoresParados();
    imagens.insert(std::string(reinterpret_cast<char*>(tela.pixels),sizeof(tela.pixels)));
  }
  assert(imagens.size()>60); // Digitação, rolagem, indicador e transição visíveis.
  comando("HELLO 1 6789abcd");
  assert(!demoHack && !demonstracao && !atividade && painelHack==0);
  tempoSimulado=0xfffffff0; comando("HELLO 1 789abcde");
  comando("FACE 1 789abcde 1 0 1 0 3500");
  comando("ACTIVITY 1 789abcde 1 1 500");
  tempoSimulado=100; loop(); assert(atividade && conectado);
  tempoSimulado=484; loop(); assert(!atividade && conectado); // TTL com wrap de millis.
  comando("HELLO 1 89abcdef"); assert(!atividade && painelHack==0);
  exigirMotoresParados();
  printf("HACK_HOST_OK: CAPS, sessao, campos, replay, AACK apos frame, I2C, TTL, wrap e demo; %d pixels de texto\n",pixelsTexto);
}

void validarMotores() {
  // O mesmo parser/loop do firmware precisa aplicar GPIO; texto ACK não basta.
  tempoSimulado=1000; comando("HELLO 1 11223344");
  comando("FACE 1 11223344 1 0 1 0 3500");
  Serial.saida.clear();
  comando("MOTOR 1 11223344 1 120 -140 300");
  assert(niveisGpio[7]==HIGH && dutiesPwm[1]==0 && dutiesPwm[4]==0);
  assert(Serial.saida.find("MACK")==std::string::npos); // Wake não bloqueia/antecipa receipt.
  tempoSimulado=1001; loop();
  assert(dutiesPwm[1]==120 && dutiesPwm[2]==0 && dutiesPwm[3]==0 && dutiesPwm[4]==140);
  assert(Serial.saida.find("MACK 1 11223344 1 120 -140 300")!=std::string::npos);
  uint32_t inicioOriginalComHack=inicioMotor;
  comando("ACTIVITY 1 11223344 1 1 2000");
  assert(atividade && inicioMotor==inicioOriginalComHack && duracaoMotor==300);
  tempoSimulado=1300; loop();
  assert(niveisGpio[7]==LOW && dutiesPwm[1]==0 && dutiesPwm[4]==0);
  comando("STOP");
  // Primeira fronteira temporal: autorização vence durante a consulta I2C.
  tempoSimulado=2000; comando("HELLO 1 22334455");
  comando("FACE 1 22334455 1 0 1 0 500");
  tempoSimulado=2490; Wire.demoraTransmissao=20; Serial.saida.clear();
  processarLinha("MOTOR 1 22334455 1 80 80 50");
  assert(niveisGpio[7]==LOW && Serial.saida.find("MACK")==std::string::npos);
  Wire.demoraTransmissao=0;
  tempoSimulado=3000; comando("HELLO 1 33445566");
  comando("FACE 1 33445566 1 0 1 0 3500");
  comando("MOTOR 1 33445566 1 80 80 50");
  tempoSimulado=3049; Wire.demoraTransmissao=20; Serial.saida.clear();
  atualizarMotor(tempoSimulado);
  assert(niveisGpio[7]==LOW && dutiesPwm[1]==0 && dutiesPwm[3]==0);
  assert(Serial.saida.find("MACK")==std::string::npos); // Probe consumiu janela: não aplicar/confirmar tarde.
  Wire.demoraTransmissao=0;
  tempoSimulado=4000; comando("HELLO 1 44556677");
  comando("FACE 1 44556677 1 0 1 0 3500");
  // Um token de sessão maior não pode virar sessão + sequência por truncamento.
  Serial.saida.clear();
  comando("MOTOR 1 445566771 120 0 50");
  assert(niveisGpio[7]==LOW && !motorPendente && !motorAtivo);
  assert(sequenciaMotor==0 && Serial.saida.find("MOTOR_INVALIDO")!=std::string::npos);
  // Inteiros, faixa, campos e versão inválidos não mudam a sequência/saídas.
  const char *invalidos[] = {
    "MOTOR 1 44556677 0 80 80 50", "MOTOR 1 44556677 -1 80 80 50",
    "MOTOR 1 44556677 4294967296 80 80 50", "MOTOR 1 44556677 1 256 80 50",
    "MOTOR 1 44556677 1 -256 80 50", "MOTOR 1 44556677 1 80 99999999999999 50",
    "MOTOR 1 44556677 1 +80 80 50", "MOTOR 1 44556677 1 8.0 80 50",
    "MOTOR 1 44556677 1 80 80 49", "MOTOR 1 44556677 1 80 80 501",
    "MOTOR 1 44556677 1 80 80 -1", "MOTOR 1 44556677 1 80 80 4294967296",
    "MOTOR 1 44556677 1 80 80 50 extra", "MOTOR 1 44556677 1 80 80",
    "MOTOR1 44556677 1 80 80 50", "MOTOR 2 44556677 1 80 80 50",
    "MOTOR 1 445566771 1 80 80 50", "MOTOR 1 4455667g 1 80 80 50",
    "MOTOR 1 44556677 1 80 - 50", "MOTOR 1 44556677 +1 80 80 50",
  };
  for (const char *entrada : invalidos) {
    Serial.saida.clear(); comando(entrada); exigirMotoresParados();
    assert(sequenciaMotor==0 && Serial.saida.find("MACK")==std::string::npos);
  }
  tempoSimulado=5000; subMilissegundos=900;
  comando("HELLO 1 55667788");
  comando("MOTOR 1 55667788 1 80 80 200"); exigirMotoresParados(); // HELLO não arma.
  comando("FACE 1 55667788 1 0 1 0 3500");
  Serial.saida.clear(); comando("MOTOR 1 55667788 1 255 -255 200");
  assert(niveisGpio[7]==HIGH && motorPendente && !motorAtivo);
  tempoSimulado=5001; subMilissegundos=0; loop();
  assert(motorPendente && dutiesPwm[1]==0); // Tick de millis não equivale a 1 ms real.
  subMilissegundos=899; loop(); assert(motorPendente && dutiesPwm[1]==0);
  subMilissegundos=900; loop();
  assert(motorAtivo && dutiesPwm[1]==255 && dutiesPwm[2]==0 && dutiesPwm[3]==0 && dutiesPwm[4]==255);
  assert(Serial.saida.find("MACK 1 55667788 1 255 -255 200")!=std::string::npos);
  uint32_t inicioOriginal=inicioMotor;
  comando("MOTOR 1 55667788 2 -50 50 500");
  assert(Serial.saida.find("MOTOR_OCUPADO")!=std::string::npos);
  assert(inicioMotor==inicioOriginal && duracaoMotor==200 && sequenciaMotor==1 && dutiesPwm[1]==255);
  comando("MOTOR 1 55667788 1 100 100 500");
  assert(inicioMotor==inicioOriginal && sequenciaMotor==1 && dutiesPwm[1]==255);
  tempoSimulado=5199; subMilissegundos=0;
  comando("FACE 1 55667788 2 1 2 1 3500"); assert(motorAtivo);
  tempoSimulado=5200; loop(); exigirMotoresParados(); // FACE não prolonga o motor.
  comando("MOTOR 1 55667788 1 100 100 500"); exigirMotoresParados(); // Replay após expiração.
  comando("MOTOR 1 55667788 2 -90 110 500"); assert(motorPendente);
  comando("HELLO 1 55667788"); exigirMotoresParados(); assert(sequenciaMotor==2);
  comando("FACE 1 55667788 1 0 1 0 3500");
  comando("MOTOR 1 55667788 2 90 90 200"); exigirMotoresParados(); // HELLO repetido não libera replay.
  comando("MOTOR 1 55667788 3 90 90 200"); assert(motorPendente);
  comando("STOP"); exigirMotoresParados(); assert(Serial.saida.find("STOPPED 1")!=std::string::npos);
  comando("MOTOR 1 55667788 4 90 90 200");
  tempoSimulado=5201; loop(); assert(motorAtivo);
  comando("STOP"); exigirMotoresParados(); // STOP também interrompe PWM aplicado.
  comando("MOTOR 1 55667788 5 90 90 200");
  Serial.saida.clear(); comando("MOTOR 1 ffffffff 9 0 0 50"); exigirMotoresParados();
  assert(sequenciaMotor==5 && Serial.saida.find("MACK")==std::string::npos); // Zero desenergiza sem receipt falso.
  comando("MOTOR 1 55667788 6 0 0 50"); exigirMotoresParados();
  assert(Serial.saida.find("MACK 1 55667788 6 0 0 50")!=std::string::npos);
  comando("MOTOR 1 55667788 7 90 90 200"); comando("DEMO"); exigirMotoresParados();
  comando("MOTOR 1 55667788 8 90 90 200"); exigirMotoresParados(); // Demo só OLED.

  tempoSimulado=6000; comando("HELLO 1 66778899");
  comando("FACE 1 66778899 1 0 1 0 500");
  tempoSimulado=6490; comando("MOTOR 1 66778899 1 100 100 500");
  tempoSimulado=6491; loop(); assert(motorAtivo);
  tempoSimulado=6500; loop(); exigirMotoresParados(); assert(!conectado); // TTL de FACE menor que pulso.
  tempoSimulado=7000; comando("HELLO 1 778899aa");
  comando("FACE 1 778899aa 1 0 1 0 3500");
  comando("MOTOR 1 778899aa 1 100 100 500"); Wire.presente=false;
  tempoSimulado=7001; Serial.saida.clear(); loop(); exigirMotoresParados();
  assert(Serial.saida.find("MACK")==std::string::npos); // Perda OLED durante wake não confirma.
  Wire.presente=true; comando("HELLO 1 8899aabb");
  comando("FACE 1 8899aabb 1 0 1 0 3500"); comando("MOTOR 1 8899aabb 1 100 100 500");
  tempoSimulado=7002; loop(); assert(motorAtivo);
  Wire.presente=false; loop(); exigirMotoresParados(); Wire.presente=true;

  tempoSimulado=0xfffffffe; comando("HELLO 1 99aabbcc");
  comando("FACE 1 99aabbcc 1 0 1 0 3500"); comando("MOTOR 1 99aabbcc 1 100 100 500");
  tempoSimulado=1; loop(); assert(motorAtivo); // Prazo de motor atravessa wrap de millis.
  tempoSimulado=498; loop(); exigirMotoresParados();
  tempoSimulado=4294967; subMilissegundos=800; comando("HELLO 1 aabbccdd");
  comando("FACE 1 aabbccdd 1 0 1 0 3500"); comando("MOTOR 1 aabbccdd 1 80 80 50");
  tempoSimulado=4294968; subMilissegundos=799; loop(); assert(motorPendente);
  subMilissegundos=800; loop(); assert(motorAtivo); // Wake atravessa wrap de micros.
  comando("STOP"); exigirMotoresParados(); subMilissegundos=0;

  tempoSimulado=8000; comando("HELLO 1 bbccddee");
  comando("FACE 1 bbccddee 1 0 1 0 3500"); comando("MOTOR 1 bbccddee 1 80 80 50");
  falhaPwm=true; tempoSimulado=8001; Serial.saida.clear(); loop(); exigirMotoresParados();
  assert(!motoresProntos && Serial.saida.find("MACK")==std::string::npos);
  falhaPwm=false; comando("MOTOR 1 bbccddee 2 80 80 50"); exigirMotoresParados();
  assert(!motoresProntos); // Falha de PWM não rearma em silêncio.
  falhaPwm=true; setup(); exigirMotoresParados(); assert(!motoresProntos);
  falhaPwm=false;
  puts("MOTOR_HOST_OK: limites, GPIO, wake, ocupacao, replay, parada, OLED, PWM, TTL e wrap");
}

void exportarHack(const std::string &pasta) {
  tempoSimulado=3000000; comando("HELLO 1 abcdef12");
  comando("FACE 1 abcdef12 1 0 1 0 3500");
  proximaPiscada=3100000; inicioPiscada=0; proximoOlhar=3100000; olharAlvo=0;
  uint32_t seqFace=1, seqAtividade=0;
  uint8_t antes[64][128]; int primeiroPasso=0;
  std::set<std::string> quadros;
  for(int frame=0;frame<300;++frame) {
    tempoSimulado=3000000+frame*33;
    if(frame%15==0) {
      char pacote[100]; snprintf(pacote,sizeof(pacote),"FACE 1 abcdef12 %u 0 1 0 3500",++seqFace);
      comando(pacote);
    }
    if(frame==44) memcpy(antes,tela.pixels,sizeof(antes));
    if((frame>=45 && frame<225 && (frame-45)%8==0) || frame==225) {
      char pacote[100]; snprintf(pacote,sizeof(pacote),"ACTIVITY 1 abcdef12 %u %d 1000",
                                 ++seqAtividade,frame<225?1:0);
      comando(pacote);
    }
    loop(); exigirMotoresParados();
    if(frame==45) {
      for(int y=0;y<64;++y) for(int x=0;x<128;++x) primeiroPasso+=antes[y][x]!=tela.pixels[y][x];
      assert(primeiroPasso<250); // Primeiro frame não substitui rosto inteiro por terminal.
    }
    if(frame==150) assert(atividade && painelHack==1);
    if(frame==299) assert(!atividade && painelHack==0 && conectado && emocao==0);
    quadros.insert(std::string(reinterpret_cast<char*>(tela.pixels),sizeof(tela.pixels)));
    char nome[80]; snprintf(nome,sizeof(nome),"/hack_%03d.pgm",frame);
    tela.salvar(pasta+nome);
  }
  printf("HACK_PIXELS_OK: %zu quadros distintos, primeiro passo %d pixels, motores parados\n",
         quadros.size(),primeiroPasso);
  assert(quadros.size()>200);
}

int main(int argc,char **argv) {
  assert(PINOS_MOTOR[0]==1 && PINOS_MOTOR[1]==2 && PINOS_MOTOR[2]==3 && PINOS_MOTOR[3]==4);
  setup(); assert(telaInicializada && endereco==0x3C);
  exigirMotoresParados(); // Boot antes de qualquer pacote de movimento.
  int pixelsAcordados=0;
  for(int y=10;y<28;++y) for(int x=20;x<108;++x) pixelsAcordados+=tela.pixels[y][x];
  assert(pixelsAcordados<200); // Sem sessão: pálpebras fechadas, nunca os olhos acordados.
  validarAtividade();
  tempoSimulado=0; setup();
  Serial.saida.clear();
  comando("FACE 1 a1b2c3d4 1 3 2 0 3500");
  assert(!conectado && emocao==0); // Nenhum efeito antes do handshake.
  comando("HELLO 1 a1b2c3d4");
  assert(Serial.saida.find("READY 1 a1b2c3d4 SSD1306 128 64")!=std::string::npos);
  Serial.saida.clear();
  tempoSimulado=1; comando("FACE 1 a1b2c3d4 1 3 2 0 3500");
  assert(ackPendente && Serial.saida.empty()); // ACK espera o próximo frame.
  tempoSimulado=40; loop();
  assert(Serial.saida.find("ACK 1 a1b2c3d4 1 3 2 0")!=std::string::npos);
  comando("FACE 1 a1b2c3d4 1 2 1 0 3500"); assert(emocao==3); // Sequência velha.
  comando("FACE 1 ffffffff 2 2 1 0 3500"); assert(emocao==3); // Sessão alheia.
  comando("FACE 1 a1b2c3d4 2 99 1 0 3500"); assert(emocao==3);
  comando("FACE 1 a1b2c3d4 2 1 8 0 3500"); assert(emocao==3);
  Serial.saida.clear(); Wire.presente=false;
  tempoSimulado=80; comando("FACE 1 a1b2c3d4 2 1 2 1 3500");
  assert(Serial.saida.find("ACK")==std::string::npos && !conectado);
  Wire.presente=true; comando("HELLO 1 bbbbbbbb");
  tempoSimulado=120; comando("FACE 1 bbbbbbbb 1 1 2 1 500");
  assert(conectado && falando);
  // millis pode avançar entre o início do loop e a recepção do novo pacote.
  tempoSimulado=140; relogioAvanca=true;
  comando("FACE 1 bbbbbbbb 2 1 2 1 500");
  assert(conectado && falando); // RED: agora antigo - ultimoPacote novo estoura uint32.
  relogioAvanca=false;
  tempoSimulado=700; loop(); assert(!conectado && !falando && emocao==0 && estavaDormindo);
  assert(sessao[0]==0);
  comando("FACE 1 bbbbbbbb 3 3 3 1 500"); assert(!conectado && estavaDormindo);
  comando("HELLO 1 cccccccc"); assert(!conectado && estavaDormindo);
  tempoSimulado=740; comando("FACE 1 cccccccc 1 6 2 0 500"); assert(conectado && !estavaDormindo);
  tempoSimulado=1300; loop(); assert(!conectado && estavaDormindo);
  // TTL também atravessa o wrap de millis sem dormir cedo nem prender a sessão.
  tempoSimulado=0xfffffff0; comando("HELLO 1 dddddddd");
  comando("FACE 1 dddddddd 1 4 1 0 500");
  tempoSimulado=100; loop(); assert(conectado);
  tempoSimulado=600; loop(); assert(!conectado && estavaDormindo);
  std::string excesso(180,'X'); Serial.entrada+=excesso+"\n";
  loop(); assert(!conectado);
  comando("DEMO"); assert(demonstracao);
  comando("HELLO 1 cccccccc"); assert(!demonstracao);
  validarMotores();
  conectado=true; falando=false; emocao=0; nivel=2;
  inicioPiscada=0; proximaPiscada=1000000; proximoOlhar=1000000; olhar=0; olharAlvo=0;
  for(int frame=0;frame<90;++frame) renderizar(2000+frame*33);
  uint8_t antes[64][128]; memcpy(antes,tela.pixels,sizeof(antes));
  emocao=1; renderizar(2000+90*33);
  int alterados=0;
  for(int y=0;y<64;++y) for(int x=0;x<128;++x) alterados+=antes[y][x]!=tela.pixels[y][x];
  printf("TROCA_CALMA_ALEGRE_PRIMEIRO_FRAME: %d pixels\n",alterados); fflush(stdout);
  assert(alterados<250); // Morph da pose: não substituir o olho inteiro num frame.
  int maiorMudanca=0;
  uint32_t instante=10000;
  for(int origem=0;origem<10;++origem) for(int destino=0;destino<10;++destino) {
    conectado=origem!=9; emocao=origem==9?0:origem; falando=false; nivel=2;
    inicioPiscada=0; proximaPiscada=100000000; proximoOlhar=100000000; olharAlvo=0;
    for(int frame=0;frame<90;++frame) { instante+=33; renderizar(instante); }
    memcpy(antes,tela.pixels,sizeof(antes));
    conectado=destino!=9; emocao=destino==9?0:destino;
    instante+=33; renderizar(instante);
    int mudanca=0;
    for(int y=0;y<64;++y) for(int x=0;x<128;++x) mudanca+=antes[y][x]!=tela.pixels[y][x];
    maiorMudanca=max(maiorMudanca,mudanca);
    if(mudanca>=350) printf("TROCA_BRUSCA: %d -> %d, %d pixels\n",origem,destino,mudanca);
    assert(mudanca<350); // As 100 trocas, incluindo sono, usam a mesma interpolação.
  }
  printf("100_TROCAS_OK: maior primeiro passo %d pixels\n",maiorMudanca);
  if(argc>1) {
    std::filesystem::create_directories(argv[1]);
    exportarHack(argv[1]);
    if(argc>2 && std::string(argv[2])=="HACK") {
      puts("FIRMWARE_HACK_HOST_OK: preview raster real e regressivos aprovados"); return 0;
    }
    for(int emo=0;emo<10;++emo) {
      emocao=emo;nivel=2;falando=false;demonstracao=false;conectado=true;
      if(emo==9) conectado=false;
      estavaDormindo=true;
      inicioPiscada=0;proximaPiscada=2600;proximoOlhar=0;olhar=0;
      std::set<std::string> imagens;
      for(int frame=0;frame<96;++frame) {
        tempoSimulado=frame*33; renderizar(tempoSimulado);
        imagens.insert(std::string(reinterpret_cast<char*>(tela.pixels),sizeof(tela.pixels)));
        char nome[80];snprintf(nome,sizeof(nome),"/emo_%d_%03d.pgm",emo,frame);
        tela.salvar(std::string(argv[1])+nome);
      }
      assert(imagens.size()>8); // Movimento observável em cada pose, inclusive sono.
    }
    // Sequência contínua, sem resetar fase/estado ao mudar pose ou começar fala.
    int roteiro[]={0,1,6,5,3,4,2,7,8,9,0};
    instante=2000000; conectado=true; emocao=0;
    inicioPiscada=0; proximaPiscada=instante+4500; proximoOlhar=instante+1000;
    for(int trecho=0;trecho<11;++trecho) for(int frame=0;frame<64;++frame) {
      emocao=roteiro[trecho]==9?0:roteiro[trecho]; conectado=roteiro[trecho]!=9;
      falando=(trecho==4 || trecho==5) && frame>=24 && frame<52;
      instante+=33; renderizar(instante);
      char nome[80];snprintf(nome,sizeof(nome),"/troca_%03d.pgm",trecho*64+frame);
      tela.salvar(std::string(argv[1])+nome);
    }
  }
  puts("FIRMWARE_HOST_OK: handshake, sequencia, sessao, validacao, ACK apos frame, falha OLED, TTL, overflow e demo");
}

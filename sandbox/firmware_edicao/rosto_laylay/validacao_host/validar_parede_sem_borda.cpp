#include <cassert>
#include <cstdio>
#define LAYLAY_SENSOR_BORDA 0
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"
void tickParede(uint32_t t,int mm=80,int status=0) {
  tempoSimulado=t;
  auto &f=distancias[0];f.presente=f.amostra=true;f.erroI2c=false;
  f.medidaEm=t;f.mm=mm;f.status=status;
  atualizarMotor(t);
}
int main() {
  Wire.extras[0x29]=true;setup();
  assert(modosGpio[10]==0); // Pino do sensor retirado fica livre neste perfil.
  tickParede(50,200);
  assert(!distancias[1].presente && !distancias[1].amostra);
  assert(!strcmp(riscoProtecao(50),"NENHUM"));
  processarLinha("DIST 1 1");
  assert(Serial.saida.find("BORDA 49 DESATIVADA -1")!=std::string::npos);
  processarLinha("HELLO 1 01234567");processarLinha("FACE 1 01234567 1 0 1 0 3500");
  processarLinha("SENTRY 1 01234567 1 1 1500");
  tickParede(60);assert(!strcmp(faseProtecao,"RECUANDO"));
  tickParede(62);tickParede(64);assert(motorAtivo);
  tickParede(310);tickParede(410);tickParede(412);tickParede(414);
  assert(!strcmp(faseProtecao,"BUSCANDO") && motorAtivo);
  tickParede(580,250);tickParede(600,250);tickParede(620,250);tickParede(640,250);
  assert(!strcmp(faseProtecao,"SEGUINDO"));
  tickParede(642,250);tickParede(644,250);assert(motorAtivo);
  processarLinha("STOP");assert(!motorEmUso() && niveisGpio[PINO_NSLEEP]==LOW);
  tickParede(700,8190,4);assert(!strcmp(riscoProtecao(700),"NENHUM"));
  distancias[0].erroI2c=true;assert(!strcmp(riscoProtecao(700),"FALHA_FRENTE"));
  distancias[0].erroI2c=false;assert(!strcmp(riscoProtecao(1000),"FALHA_FRENTE"));
  tickParede(1200,250);atualizarRecuperacaoPerifericos(1200);
  tickParede(1800,250);atualizarRecuperacaoPerifericos(1800);
  assert(conectado && !recuperacaoPerifericosTentada);
  puts("PAREDE_SEM_BORDA_GREEN: ausencia explicita, recuo, busca, saida, STOP e falha frontal");
}

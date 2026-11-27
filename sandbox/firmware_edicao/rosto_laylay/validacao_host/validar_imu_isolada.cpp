#include <cassert>
#include <cstdio>
#define LAYLAY_IMU 1
#define LAYLAY_TESTE_SOMENTE_IMU 1
#include "../rosto_laylay.ino"
int main() {
  Wire.extras[0x68]=true;Wire.registrosImu[0x75]=0x98;
  Wire.registrosImu[0x3F]=0x20;
  setup();
  assert(niveisGpio[0]==LOW && modosGpio[0]==OUTPUT);
  assert(niveisGpio[10]==LOW && modosGpio[10]==OUTPUT);
  assert(!motoresProntos && imu.presente);
  for(unsigned t=10;t<2300;t+=10) {tempoSimulado=t;atualizarImuCorporal(t);}
  assert(imu.calibrada && fabsf(imu.norma-1)<.001f);
  processarLinha("HELLO 1 01234567");processarLinha("FACE 1 01234567 1 0 1 0 3500");
  processarLinha("MOTOR 1 01234567 1 100 100 500");
  processarLinha("TURN 1 01234567 2 90 160 500");
  assert(!motorEmUso() && niveisGpio[PINO_NSLEEP]==LOW);
  Serial.saida.clear();processarLinha("IMU 1 1");
  assert(Serial.saida.find("PRONTA")!=std::string::npos);
  assert(Serial.saida.find("ESTAVEL 152")!=std::string::npos);
  EstadoImuCorporal toque;
  for(unsigned t=10;t<2300;t+=10) toque.incorporar(t,0,0,1,0,0,0,false);
  toque.incorporar(2300,0,0,1.8f,0,0,0,false);
  toque.incorporar(2310,0,0,1,0,0,0,false);
  assert(strcmp(toque.manuseio,"MOVIMENTO_BRUSCO"));
  for(unsigned t=2320;t<2450;t+=10) toque.incorporar(t,0,0,1,200,0,0,false);
  assert(!strcmp(toque.manuseio,"MOVIMENTO_BRUSCO"));
  puts("IMU_ISOLADA_GREEN: identidade, escala, calibracao, XSHUT baixo, motores desarmados");
}

#include <cassert>
#include <cstdio>
#define LAYLAY_IMU 1
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#define LAYLAY_LIMITE_MOTOR_TESTE_MS 5000
#include "../rosto_laylay.ino"

void amostraImu(uint32_t t, float ax=0, float ay=0, float az=1, float gz=0) {
  tempoSimulado=t;
  imu.incorporar(t,ax,ay,az,0,0,gz,motorEmUso());
  for (int i=0;i<2;++i) {
    auto &s=distancias[i];s.presente=s.amostra=true;s.erroI2c=false;
    s.status=0;s.mm=i?100:250;s.medidaEm=t;
  }
}
int main() {
  Wire.extras[0x29]=Wire.extras[0x68]=true;
  Wire.registrosImu[0x75]=0x98;Wire.registrosImu[0x3F]=0x20;
  setup();
  assert(imu.presente && identidadeImu==0x98);
  assert(!imu.calibrada);
  for(unsigned t=10;t<2500;t+=10) amostraImu(t);
  assert(imu.calibrada && !imu.bloqueia(2490));
  processarLinha("HELLO 1 01234567");
  processarLinha("FACE 1 01234567 1 0 1 0 3500");
  processarLinha("IMU 1 1");
  assert(Serial.saida.find("IMU 1 1 104 PRONTA")!=std::string::npos);
  processarLinha("TURN 1 01234567 1 90 160 5000");
  assert(giroMedidoAtivo);
  // Integrar giro real, sem emprestar o tempo de PWM como sucesso.
  for(unsigned t=2500;t<3560;t+=10) {amostraImu(t,0,0,1,90);atualizarMotor(t);}
  assert(!motorEmUso() && !giroMedidoAtivo);
  assert(Serial.saida.find("TURNEND 1 01234567 1 ALVO")!=std::string::npos);
  assert(niveisGpio[PINO_NSLEEP]==LOW);
  Serial.saida.clear();
  processarLinha("TURN 1 01234567 1 90 160 5000");
  assert(!giroMedidoAtivo); // replay
  amostraImu(3570,0,.8f,.6f);atualizarMotor(3570);
  assert(imu.bloqueia(3570));
  processarLinha("MOTOR 1 01234567 2 100 100 250");
  assert(!motorEmUso());
  assert(Serial.saida.find("MANUSEIO")!=std::string::npos);
  // Telemetria e inclinação não criam concessão nem acionam motor de fuga.
  processarLinha("SENTRY 1 01234567 1 1 1200");
  for(unsigned t=3580;t<3900;t+=10) {amostraImu(t,0,.8f,.6f);atualizarMotor(t);}
  assert(!motorEmUso());
  for(unsigned t=3900;t<5500;t+=10) {amostraImu(t);atualizarMotor(t);}
  assert(!imu.bloqueia(5490));
  processarLinha("STOP");
  assert(!motorEmUso());
  // Falta de rotação e rotação no sentido oposto não recebem ALVO.
  processarLinha("FACE 1 01234567 2 0 1 0 3500");
  Serial.saida.clear();
  processarLinha("TURN 1 01234567 3 -90 160 5000");
  for(unsigned t=5500;t<6500;t+=10) {amostraImu(t);atualizarMotor(t);}
  assert(!motorEmUso() && Serial.saida.find("SEM_ROTACAO")!=std::string::npos);
  processarLinha("TURN 1 01234567 4 -90 160 5000");
  for(unsigned t=6500;t<6700;t+=10) {amostraImu(t,0,0,1,90);atualizarMotor(t);}
  assert(!motorEmUso() && Serial.saida.find("SENTIDO_DIVERGENTE")!=std::string::npos);
  // Não há giro sem calibração, amostra recente ou mantendo sensor imóvel.
  imu.calibrada=false;
  Serial.saida.clear();processarLinha("TURN 1 01234567 5 90 160 5000");
  assert(!giroMedidoAtivo && !motorEmUso());
  imu.calibrada=true;imu.amostra=true;imu.medidaEm=0;
  assert(imu.bloqueia(millis()));
  puts("IMU_GREEN: calibracao, giro medido, replay, manuseio, sem fuga no colo, falha fechada");
}

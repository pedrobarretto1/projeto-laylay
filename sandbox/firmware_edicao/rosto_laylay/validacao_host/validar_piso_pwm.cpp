#include <cassert>
#include <cstdio>
#define LAYLAY_PWM_MINIMO_MOTOR 150
#define LAYLAY_PWM_MAXIMO_MOTOR 255
#define LAYLAY_IMU 1
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#define LAYLAY_LIMITE_MOTOR_TESTE_MS 5000
#include "../rosto_laylay.ino"

void amostraPiso(uint32_t t, float gz=0) {
  tempoSimulado=t;
  imu.incorporar(t,0,0,1,0,0,gz,motorEmUso());
  for (int i=0;i<2;++i) {
    auto &s=distancias[i]; s.presente=s.amostra=true; s.erroI2c=false;
    s.status=0; s.mm=i?100:250; s.medidaEm=t;
  }
}
void conferirPiso() {
  for (int p:PINOS_MOTOR) assert(dutiesPwm[p]==0 || (dutiesPwm[p]>=150 && dutiesPwm[p]<=255));
}
void conferirParada() {
  assert(niveisGpio[PINO_NSLEEP]==LOW && !motorEmUso());
  for (int p:PINOS_MOTOR) assert(dutiesPwm[p]==0);
}
int main(int argc,char **argv) {
  const char *caso=argc>1?argv[1]:"rampa";
  Wire.extras[0x29]=Wire.extras[0x68]=true;
  Wire.registrosImu[0x75]=0x98; Wire.registrosImu[0x3F]=0x20;
  setup(); conferirParada();
  for (unsigned t=10;t<2500;t+=10) amostraPiso(t);
  assert(imu.calibrada && !imu.bloqueia(2490));
  processarLinha("HELLO 1 01234567");
  processarLinha("FACE 1 01234567 1 0 1 0 3500");
  if (!strcmp(caso,"rampa")) {
    processarLinha("MOTOR 2 01234567 1 150 150 1000");
    for (unsigned t=2492;t<3490;t+=2) {
      amostraPiso(t); atualizarMotor(t); assert(motorEmUso()); conferirPiso();
    }
    amostraPiso(3490); atualizarMotor(3490); conferirParada();
    assert(Serial.saida.find("MACK 2 01234567 1 150 150 1000")!=std::string::npos);
  } else if (!strcmp(caso,"reflexo")) {
    for (auto pwm:{-110,-120,120,140,160,170}) {
      pararMotor(); assert(aplicarReflexoProtecao(pwm,-pwm,millis()));
      tempoSimulado+=2; assert(aplicarReflexoProtecao(pwm,-pwm,millis()));
      assert(motorAtivo); conferirPiso();
      assert(abs(pwmEsquerdo)>=150 && abs(pwmDireito)>=150);
    }
  } else if (!strcmp(caso,"giro")) {
    processarLinha("TURN 1 01234567 1 90 160 5000");
    assert(giroMedidoAtivo);
    bool desacelerou=false;
    for (unsigned t=2500;t<3560;t+=10) {
      amostraPiso(t,90); atualizarMotor(t); conferirPiso();
      if (motorAtivo && abs(pwmEsquerdo)<160) desacelerou=true;
    }
    assert(desacelerou && !giroMedidoAtivo);
    conferirParada();
    assert(Serial.saida.find("TURNEND 1 01234567 1 ALVO")!=std::string::npos);
  } else if (!strcmp(caso,"admissao")) {
    processarLinha("MOTOR 1 01234567 1 100 100 250");
    assert(!motorEmUso());
    assert(Serial.saida.find("ERROR 1 MOTOR_PWM_FORA_PERFIL")!=std::string::npos);
    processarLinha("MOTOR 1 01234567 1 0 -150 250");
    amostraPiso(2492); atualizarMotor(2492);
    assert(motorAtivo && dutiesPwm[1]==0 && dutiesPwm[2]==0 && dutiesPwm[4]==150);
  } else assert(false);
  processarLinha("STOP"); conferirParada();
  printf("PISO_PWM_GREEN %s: GPIO simulado, zero preservado, ativo >=150, STOP intacto\n",caso);
}

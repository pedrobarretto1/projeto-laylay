#include <cassert>
#include <cstdio>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"

void amostra(uint32_t t, int frente=80) {
  tempoSimulado=t;
  for (int i=0;i<2;++i) {
    auto &s=distancias[i]; s.presente=s.amostra=true; s.erroI2c=false;
    s.medidaEm=t; s.mm=i ? 100 : frente; s.status=0;
  }
}

int main() {
  Wire.extras[0x29]=true; setup(); amostra(40);
  processarLinha("HELLO 1 01234567");
  processarLinha("FACE 1 01234567 1 0 1 0 3500");
  processarLinha("SENTRY 1 01234567 1 1 1200");
  atualizarMotor(40);
  assert(reflexoProtecaoAtivo());
  auto incidente=incidenteProtecao;
  // A busca já é dona dos PWM; recusar o PC precisa de receipt correlacionado.
  Serial.saida.clear();
  processarLinha("MOTOR 1 01234567 1 100 100 250");
  assert(Serial.saida.find("HAZARD 1 01234567 1 ")!=std::string::npos);
  assert(Serial.saida.find("MACK ")==std::string::npos);
  assert(incidenteProtecao==incidente && reflexoProtecaoAtivo());
  assert(!motorAtivo && !motorPendente);
  amostra(42); atualizarMotor(42);
  amostra(44); atualizarMotor(44);
  assert(motorAtivo && motorEmUso());
  auto pwmLocal=pwmEsquerdo;
  Serial.saida.clear();
  processarLinha("MOTOR 1 01234567 2 100 100 250");
  assert(Serial.saida.find("HAZARD 1 01234567 2 ")!=std::string::npos);
  assert(Serial.saida.find("MACK ")==std::string::npos);
  assert(incidenteProtecao==incidente && pwmEsquerdo==pwmLocal);
  // O perigo pode desaparecer antes de o reflexo terminar: ainda não é MACK.
  amostra(50,200);
  Serial.saida.clear();
  processarLinha("MOTOR 2 01234567 3 120 -120 250");
  assert(Serial.saida.find("HAZARD 1 01234567 3 ")!=std::string::npos);
  assert(Serial.saida.find("AGUARDANDO_ESTABILIDADE")!=std::string::npos);
  assert(Serial.saida.find("MACK ")==std::string::npos);
  assert(incidenteProtecao==incidente);
  // Mesma sequência não pode ser executada mais tarde como replay.
  Serial.saida.clear();
  processarLinha("MOTOR 2 01234567 3 120 -120 250");
  assert(Serial.saida.find("MOTOR_NAO_AUTORIZADO")!=std::string::npos);
  processarLinha("STOP");
  assert(!reflexoProtecaoAtivo() && !motorEmUso());
  for (unsigned t : {80u,100u,120u}) { amostra(t,200); atualizarMotor(t); }
  assert(!travaProtecao);
  processarLinha("MOTOR 1 01234567 4 100 100 250");
  amostra(122,200); atualizarMotor(122);
  amostra(124,200); atualizarMotor(124);
  assert(motorAtivo && ackMotorEmitido);
  Serial.saida.clear();
  processarLinha("MOTOR 1 01234567 5 100 100 250");
  assert(Serial.saida.find("MOTOR_OCUPADO")!=std::string::npos);
  assert(Serial.saida.find("HAZARD ")==std::string::npos && sequenciaMotor==4);
  processarLinha("STOP");
  puts("ADMISSAO_REFLEXO_GREEN: recusa correlacionada, sem PWM emprestado, sem replay, STOP preservado");
}

#line 1 "C:\\Users\\pbarr\\Downloads\\pasta organizada\\programacao\\PY\\projeto lay\\laylay\\firmware\\rosto_laylay\\validacao_host\\validar_perfil_rosto.cpp"
#include <cassert>
#include "../rosto_laylay.ino"

// Perfil entregue para OLED: mesmo comandos válidos não habilitam a ponte.
int main() {
  assert(PINOS_MOTOR[0]==1 && PINOS_MOTOR[1]==2 && PINOS_MOTOR[2]==3 && PINOS_MOTOR[3]==4);
  setup();
  assert(!motoresProntos);
  assert(pinosMotorProntos[0] == false && pinosMotorProntos[1] == false);
  assert(pinosMotorProntos[2] == false && pinosMotorProntos[3] == false);
  processarLinha("HELLO 1 a1b2c3d4");
  processarLinha("FACE 1 a1b2c3d4 1 1 2 0 3500");
  processarLinha("ACTIVITY 1 a1b2c3d4 1 1 1200");
  assert(atividade);
  processarLinha("MOTOR 1 a1b2c3d4 1 255 255 500");
  tempoSimulado += 2;
  atualizarMotor(millis());
  assert(!motorPendente && !motorAtivo);
  assert(pwmEsquerdo == 0 && pwmDireito == 0);
  assert(niveisGpio[PINO_NSLEEP] == LOW);
  for (int pino : PINOS_MOTOR) {
    assert(!pinosPwm[pino] && dutiesPwm[pino] == 0 && niveisGpio[pino] == LOW);
  }
  processarLinha("DEMO_HACK");
  assert(demoHack && !motorAtivo && !motorPendente);
  assert(Serial.saida.find("MACK") == std::string::npos);
  return 0;
}

#line 1 "C:\\Users\\pbarr\\Downloads\\pasta organizada\\programacao\\PY\\projeto lay\\laylay\\firmware\\rosto_laylay\\validacao_host\\validar_motor_continuo.cpp"
#include <cassert>
#include <cstdio>
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"

int main() {
  setup();
  processarLinha("HELLO 1 01234567");
  processarLinha("FACE 1 01234567 1 0 1 0 3500");
  tempoSimulado += 40; loop();
  processarLinha("MOTOR 1 01234567 1 100 100 5001");
  assert(!motorAtivo && !motorPendente);
  processarLinha("MOTOR 1 01234567 1 100 100 5000");
#if defined(LAYLAY_LIMITE_MOTOR_TESTE_MS) && LAYLAY_LIMITE_MOTOR_TESTE_MS == 5000
  assert(motorPendente);
  unsigned inicio = inicioMotor;
  tempoSimulado += 2; atualizarMotor(millis());
  assert(motorAtivo);
  for (unsigned n = 1; n <= 4; ++n) {
    tempoSimulado = inicio + n * 1000;
    char face[80]; snprintf(face, sizeof(face), "FACE 1 01234567 %u 0 1 0 3500", n + 1);
    processarLinha(face); loop();
    assert(motorAtivo && inicioMotor == inicio && duracaoMotor == 5000);
  }
  tempoSimulado = inicio + 5000; atualizarMotor(millis());
  assert(!motorAtivo && !motorPendente && niveisGpio[PINO_NSLEEP] == LOW);
  for (int pino : PINOS_MOTOR) assert(dutiesPwm[pino] == 0);
  processarLinha("MOTOR 1 01234567 1 100 100 5000");
  assert(!motorPendente && !motorAtivo); // A ordem concluída não pode ser repetida.
  processarLinha("MOTOR 1 01234567 2 100 100 5000");
  tempoSimulado += 2; atualizarMotor(millis()); assert(motorAtivo);
  processarLinha("STOP 1 01234567 1");
  assert(!motorAtivo && !motorPendente);
  puts("Perfil temporario: continuo 5s, prazo absoluto, limite, replay e STOP GREEN (GPIO simulado).");
#else
  assert(!motorAtivo && !motorPendente);
  puts("Perfil normal: ordem de 5s rejeitada GREEN (GPIO simulado).");
#endif
}

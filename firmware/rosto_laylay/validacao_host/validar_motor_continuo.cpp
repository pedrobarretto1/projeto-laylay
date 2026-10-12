#include <cassert>
#include <cstdio>
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"

int main() {
  setup();
  // Compatibilidade com analogWrite do core ESP32 3.3.12 usado na referência.
  for (int pino : PINOS_MOTOR) {
    assert(pinosPwm[pino] && frequenciasPwm[pino] == 1000 && resolucoesPwm[pino] == 8);
    assert(dutiesPwm[pino] == 0);
  }
  assert(niveisGpio[PINO_NSLEEP] == LOW);
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
  processarLinha("MOTOR 1 01234567 3 100 100 250");
  tempoSimulado += 2; atualizarMotor(millis());
  assert(motorAtivo && dutiesPwm[1] == 100 && dutiesPwm[2] == 0
         && dutiesPwm[3] == 100 && dutiesPwm[4] == 0);
  processarLinha("STOP 1 01234567 2");
  assert(!motorAtivo && niveisGpio[PINO_NSLEEP] == LOW);
  processarLinha("MOTOR 1 01234567 4 -100 -100 250");
  tempoSimulado += 2; atualizarMotor(millis());
  assert(motorAtivo && dutiesPwm[1] == 0 && dutiesPwm[2] == 100
         && dutiesPwm[3] == 0 && dutiesPwm[4] == 100);
  processarLinha("STOP 1 01234567 3");
  for (int pino : PINOS_MOTOR) assert(dutiesPwm[pino] == 0);
  puts("PWM de referencia: quatro GPIOs em 1kHz/8bits, ambos canais em +/-100 e STOP GREEN (GPIO simulado).");
}

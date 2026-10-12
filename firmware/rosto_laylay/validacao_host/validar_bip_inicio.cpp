#include <cassert>
#include <cstdio>
#define LAYLAY_BIP_TESTE_INICIO 1
#include "../rosto_laylay.ino"

int main() {
  setup();
  assert(bipInicioAtivo && bipInicioTentado);
  assert(PINO_SOM == 6 && frequenciasPwm[6] == 1200 && dutiesPwm[6] == 128);
#if LAYLAY_SOM_PONTE
  assert(pinosPwm[5] && dutiesPwm[5] == 128 && frequenciasPwm[5] == 1200);
  assert(invertidosPwm[5] && !invertidosPwm[6] && ultimoCanalExplicito == 5);
#else
  assert(ultimoCanalExplicito == 4 && !pinosPwm[5]);
#endif
  for (int pino : PINOS_MOTOR) {
    assert(dutiesPwm[pino] == 0);
    if (LAYLAY_HABILITAR_MOTORES_BANCADA) assert(frequenciasPwm[pino] == 1000);
  }
  tempoSimulado = inicioBip + 1999;
  atualizarBipInicio(tempoSimulado);
  assert(bipInicioAtivo && dutiesPwm[6] == 128);
  tempoSimulado = inicioBip + 2000;
  atualizarBipInicio(tempoSimulado);
  assert(!bipInicioAtivo && !pinosPwm[6] && niveisGpio[6] == LOW);
#if LAYLAY_SOM_PONTE
  assert(!pinosPwm[5] && niveisGpio[5] == LOW && !invertidosPwm[5]);
#endif
  iniciarBipTeste();
  assert(!bipInicioAtivo && dutiesPwm[6] == 0);
  for (uint32_t t = 3000; t < 8000; t += 33) {
    tempoSimulado = t; loop();
    assert(!bipInicioAtivo && dutiesPwm[6] == 0 && niveisGpio[PINO_NSLEEP] == LOW);
  }
  // Falha de PWM não deixa saída DC nem provoca tentativas repetidas.
  bipInicioTentado = false; falhaPwm = true;
  iniciarBipTeste();
  assert(!bipInicioAtivo && bipInicioTentado && niveisGpio[6] == LOW);
  falhaPwm = false; iniciarBipTeste();
  assert(!bipInicioAtivo);
#if LAYLAY_SOM_PONTE
  // Falha da segunda saída precisa desligar também a primeira.
  bipInicioTentado = false; falhaPwmPino = 5;
  iniciarBipTeste();
  assert(!bipInicioAtivo && bipInicioTentado && !pinosPwm[6] && !pinosPwm[5]);
  assert(niveisGpio[6] == LOW && niveisGpio[5] == LOW);
  falhaPwmPino = -1; iniciarBipTeste(); assert(!bipInicioAtivo);
  bipInicioTentado = false; falhaInversaoPwm = true;
  iniciarBipTeste();
  assert(!bipInicioAtivo && !pinosPwm[6] && !pinosPwm[5]);
  assert(niveisGpio[6] == LOW && niveisGpio[5] == LOW && !invertidosPwm[5]);
  falhaInversaoPwm = false;
#endif
  puts("Bip unico 1200Hz/2000ms, corte, sem replay e motores preservados: GREEN");
}

#include <cassert>
#include <cstdio>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../../../firmware/rosto_laylay/rosto_laylay.ino"
int main() {
  Wire.extras[0x29] = true; setup();
  distancias[0].dispositivo.distancia = 200;
  distancias[1].dispositivo.distancia = 100;
  tempoSimulado = 20; atualizarSensoresDistancia(20);
  tempoSimulado = 40; atualizarSensoresDistancia(40);
  processarLinha("HELLO 1 01234567");
  processarLinha("FACE 1 01234567 1 0 1 0 3500");
  processarLinha("MOTOR 1 01234567 1 100 100 500");
  tempoSimulado += 2; atualizarMotor(millis());
  assert(dutiesPwm[1] == 100 && dutiesPwm[3] == 100);
  distancias[1].mm = 131; distancias[1].medidaEm = millis();
  atualizarMotor(millis());
  assert(dutiesPwm[1] == 0 && dutiesPwm[3] == 0 && "primeira fronteira: borda nao cortou avanco");
  puts("CORTE_BORDA_GREEN");
}

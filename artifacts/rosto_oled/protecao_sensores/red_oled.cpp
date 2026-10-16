#include <cassert>
#include <cstdio>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../../../firmware/rosto_laylay/rosto_laylay.ino"
int main() {
  Wire.extras[0x29]=true; setup(); tempoSimulado=40;
  for(auto &s:distancias) { s.presente=s.amostra=true; s.status=0; s.mm=100; s.medidaEm=40; }
  distancias[0].mm=200; distancias[0].dispositivo.distancia=200;
  distancias[1].dispositivo.distancia=100;
  processarLinha("HELLO 1 01234567"); processarLinha("FACE 1 01234567 1 0 1 0 3500");
  processarLinha("MOTOR 1 01234567 1 100 100 500");
  tempoSimulado=42; atualizarMotor(42); assert(dutiesPwm[1]==100);
  distancias[1].dispositivo.statusMedida=4;
  tela.demoraDisplay=35;
  renderizar(42);
  assert(dutiesPwm[1]==0 && dutiesPwm[3]==0 && "OLED bloqueou observacao e corte durante frame");
  puts("OLED_COOPERATIVO_GREEN");
}

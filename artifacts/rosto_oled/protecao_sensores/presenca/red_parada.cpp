#include <cassert>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../../../../firmware/rosto_laylay/rosto_laylay.ino"
int main() {
  Wire.extras[0x29]=true; setup(); tempoSimulado=40;
  for(auto &s:distancias) { s.presente=s.amostra=true; s.status=0; s.mm=100; s.medidaEm=40; }
  distancias[0].mm=200; distancias[1].mm=150;
  processarLinha("HELLO 1 01234567"); processarLinha("FACE 1 01234567 1 0 1 0 3500");
  atualizarMotor(40);
  assert(!motorEmUso());
  assert(medoProtecaoCorporal(40) && "borda percebida parada sem expressao de medo");
}

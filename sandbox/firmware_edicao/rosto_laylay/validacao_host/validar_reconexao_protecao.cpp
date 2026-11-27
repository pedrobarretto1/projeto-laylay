#include <cassert>
#include <cstdio>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"
void tick(uint32_t t) {
  tempoSimulado=t;
  for(int i=0;i<2;++i) {
    auto &s=distancias[i];s.presente=s.amostra=true;s.erroI2c=false;
    s.medidaEm=t;s.mm=i ? 100 : 80;s.status=0;
  }
  atualizarMotor(t);
}
int main() {
  Wire.extras[0x29]=true;setup();tick(40);
  processarLinha("HELLO 1 01234567");processarLinha("FACE 1 01234567 1 0 1 0 3500");
  processarLinha("SENTRY 1 01234567 1 1 1200");tick(60);tick(70);tick(80);
  assert(reflexoProtecaoAtivo() && motorEmUso());
  invalidarSessaoPor("OLED");assert(!motorEmUso());
  tick(100);processarLinha("HELLO 1 abcdef01");processarLinha("FACE 1 abcdef01 1 0 1 0 3500");
  processarLinha("SENTRY 1 abcdef01 1 0 1200");tick(120);
  assert(!motorEmUso()); // Novo FACE sozinho não herda tração.
  processarLinha("SENTRY 1 abcdef01 2 1 1200");tick(140);tick(150);tick(160);
  assert(reflexoProtecaoAtivo() && motorEmUso()); // Novo owner vigente pode reagir de novo.
  assert(incidenteProtecao==2);
  processarLinha("STOP");tick(180);assert(!motorEmUso());
  puts("RECONEXAO_GUARD_GREEN: perda OLED corta, nova sessao/lease reage, rosto sozinho nao move");
}

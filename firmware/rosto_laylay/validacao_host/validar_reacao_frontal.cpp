#include <cassert>
#include <cstdio>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#include "../rosto_laylay.ino"

int main() {
  Wire.extras[0x29]=true;
  setup();
  processarLinha("HELLO 1 01234567");
  processarLinha("FACE 1 01234567 1 0 1 0 3500");
  auto tick = [](uint32_t t,int mm) {
    tempoSimulado=t;
    for (auto &s : distancias) {
      s.presente=s.amostra=true; s.medidaEm=t; s.status=0; s.erroI2c=false;
      s.mm=(&s==&distancias[0]) ? mm : 85;
    }
    atualizarAlertaProtecao(t);
    renderizar(t);
  };
  tick(100,140); tick(130,96);
  assert(expressaoFrontal()==ReacaoFrontal::Surpresa);
  const float susto=alturaOlho;
  assert(!strcmp(riscoProtecao(130),"OBSTACULO"));
  for (int t=160;t<=400;t+=30) tick(t,95);
  assert(alturaOlho>susto);
  const float olhosAbertos=alturaOlho;
  for (int t=430;t<=1900;t+=30) tick(t,95);
  assert(expressaoFrontal()==ReacaoFrontal::Impaciente);
  assert(alturaOlho<olhosAbertos-4); // Travessia que ficou parada.
  assert(!strcmp(riscoProtecao(1900),"OBSTACULO"));
  assert(!motorEmUso());
  tick(1950,160);
  assert(!strcmp(riscoProtecao(1950),"NENHUM"));
  assert(expressaoFrontal()==ReacaoFrontal::Aliviada);
  tick(2640,120);
  assert(expressaoFrontal()==ReacaoFrontal::Neutra);
  tick(2740,98);
  assert(expressaoFrontal()==ReacaoFrontal::Curiosa);
  atualizarAlertaProtecao(4000);
  assert(expressaoFrontal()==ReacaoFrontal::Neutra);
  puts("REACAO_FRONTAL_GREEN: entrada rápida e persistência produzem olhos distintos sem alterar risco");
}

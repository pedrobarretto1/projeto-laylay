#include <cassert>
#include <cstdio>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"

int main() {
  Wire.extras[0x29]=true;
  setup();
  processarLinha("HELLO 1 01234567");
  uint32_t t=0, seq=0;
  auto tick = [&](int frente, bool vigia=true) {
    tempoSimulado=t+=10;
    for (auto &s : distancias) {
      s.presente=s.amostra=true; s.medidaEm=t; s.status=0; s.erroI2c=false;
      s.mm=(&s==&distancias[0]) ? frente : 85;
    }
    if (t%200==10) {
      char pacote[96];
      snprintf(pacote,sizeof(pacote),"FACE 1 01234567 %lu 0 1 0 3500",(unsigned long) ++seq);
      processarLinha(pacote);
      snprintf(pacote,sizeof(pacote),"SENTRY 1 01234567 %lu %u 1200",(unsigned long) seq,unsigned(vigia));
      processarLinha(pacote);
    }
    atualizarMotor(t);
  };
  int ladoInicial=0;
  while (!ladoInicial && t<1200) {
    tick(45);
    if (pwmEsquerdo*pwmDireito<0) ladoInicial=pwmEsquerdo>0 ? 1 : -1;
  }
  assert(ladoInicial);
  while (strcmp(faseProtecao,"SEGUINDO") && t<2300) tick(175);
  assert(!strcmp(faseProtecao,"SEGUINDO"));
  tick(50);
  assert(!motorEmUso());
  const uint32_t incidenteInterrompido=incidenteProtecao;
  const auto ate=t+5500;
  int ladoRetomada=0;
  while (!ladoRetomada && t<ate) {
    tick(50);
    assert(pwmEsquerdo<=0 || pwmDireito<=0); // Nenhum avanço na frente obstruída.
    if (pwmEsquerdo*pwmDireito<0) ladoRetomada=pwmEsquerdo>0 ? 1 : -1;
  }
  assert(incidenteProtecao>incidenteInterrompido); // Não fica travada olhando o obstáculo.
  assert(ladoRetomada==-ladoInicial);
  processarLinha("STOP");
  for (int i=0;i<500;++i) tick(50,false);
  assert(!motorEmUso() && !reflexoProtecaoAtivo());
  puts("BUSCA_FRONTAL_GREEN: nova obstrucao corta, aguarda e reavalia pelo outro lado; STOP prevalece");
}

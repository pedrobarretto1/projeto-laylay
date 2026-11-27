#include <cassert>
#include <cstdio>
#include "../rosto_laylay.ino"

int main(int argc, char **argv) {
  setup(); tempoSimulado = 1000;
  processarLinha("HELLO 1 abcd0123");
  uint32_t seqFace = 0, seqExpr = 0;
  auto frame = [&]() {
    tempoSimulado += 33;
    if (tempoSimulado % 20 == 0 || uint32_t(tempoSimulado - ultimoPacote) > 700) {
      char p[96]; snprintf(p, sizeof(p), "FACE 1 abcd0123 %u 0 1 0 3500", ++seqFace);
      processarLinha(p);
    }
    renderizar(tempoSimulado);
  };
  processarLinha("FACE 1 abcd0123 1 0 1 0 3500"); seqFace = 1;
  for (int i = 0; i < 120; ++i) frame();
  const int estilos[] = {6, 5, 1, 2, 3, 4, 7, 9, 10, 0};
  for (int estilo : estilos) {
    for (int i = 0; i < 70; ++i) frame();
    proximaPiscada = tempoSimulado + 10000;
    char p[96]; snprintf(p, sizeof(p), "EXPR 1 abcd0123 %u %d 1 1 1600", ++seqExpr, estilo);
    uint32_t heartbeat = ultimoPacote;
    processarLinha(p);
    assert(ackExpressaoPendente && !motorAtivo && ultimoPacote == heartbeat);
    for (int i = 0; i < 48; ++i) {
      float h = alturaOlho, w = larguraOlho;
      frame();
      assert(fabsf(alturaOlho - h) < 2.5f && fabsf(larguraOlho - w) < 2.5f);
      if (argc > 1 && i % 4 == 0)
        tela.salvar(std::string(argv[1]) + "/estilo_" + std::to_string(estilo) + "_" + std::to_string(i) + ".pgm");
      if (i == 23) {
        if (estilo == 6) assert(rubor > .6f && alturaOlho < 24);
        if (estilo == 5) assert(alturaOlho > 29 && larguraOlho < 31);
        if (estilo == 1) assert(olhosAlegres > .6f);
        if (estilo == 2) assert(sobrancelhasTristes > .5f);
        if (estilo == 3) assert(inclinacaoPalpebra > 6);
        if (estilo == 7 || estilo == 10) assert(fabsf(assimetriaOlhos) > 2);
      }
    }
    assert(!motorAtivo && !motorPendente);
  }
  for (int i = 0; i < 90; ++i) frame();
  assert(!expressaoAtiva && misturaExpressao < .01f && rubor < .01f);
  // Variar uma melodia não aumenta o duty nem muda os timers da tração.
  uint32_t hz = 0;
  for (unsigned seq = 1; seq <= 3; ++seq) {
    tempoSimulado += 2000;
    char p[96]; snprintf(p, sizeof(p), "FACE 1 abcd0123 %u 0 1 0 3500", ++seqFace); processarLinha(p);
    snprintf(p, sizeof(p), "SOUND 1 abcd0123 %u 3", seq); processarLinha(p);
    assert(somExpressivoAtivo && dutiesPwm[PINO_SOM] == 128 && ultimoCanalExplicito == 4);
    if (seq > 1) assert(frequenciasPwm[PINO_SOM] != hz);
    hz = frequenciasPwm[PINO_SOM];
    tempoSimulado += 450; atualizarSomExpressivo(tempoSimulado);
    assert(!somExpressivoAtivo && dutiesPwm[PINO_SOM] == 0);
  }
  puts("EXPRESSOES_V3_OK: estilos distintos, morph finito, sem motor, bips variados e duty preservado");
}

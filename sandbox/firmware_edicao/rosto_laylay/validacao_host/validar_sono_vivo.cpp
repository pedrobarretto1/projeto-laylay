#include <cassert>
#include <cstdio>
#include <set>
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#define LAYLAY_LIMITE_MOTOR_TESTE_MS 5000
#include "../rosto_laylay.ino"

int main(int argc, char **argv) {
  setup();
  std::set<int> estilos;
  uint32_t somAnterior = 0, inicioNota = 0;
  bool tocava = false;
  int bips = 0, frame = 0, maiorPasso = 0;
  uint8_t anterior[64][128] = {};
  for (tempoSimulado = 20; tempoSimulado < 240000; tempoSimulado += 20) {
    loop();
    // Toda a composição real do firmware roda sem sessão/autorização de movimento.
    assert(!conectado && !motorEmUso() && niveisGpio[PINO_NSLEEP] == LOW);
    for (int pino : PINOS_MOTOR) assert(dutiesPwm[pino] == 0);
    assert(sequenciaSom == 0 && !somJaTocou && ultimoInicioSom == 0);
    if (sonhoAtivo && pesoSonho > .8f) estilos.insert(estiloSonho);
    if (somSonoAtivo) {
      assert(pinosPwm[PINO_SOM] && dutiesPwm[PINO_SOM] == 10);
      if (!tocava) {
        assert(tempoSimulado >= 55000);
        if (somAnterior) assert(tempoSimulado - somAnterior >= 65000);
        somAnterior = inicioNota = tempoSimulado; ++bips;
      }
    } else if (tocava) {
      assert(tempoSimulado - inicioNota <= 85);
      assert(!pinosPwm[PINO_SOM] && niveisGpio[PINO_SOM] == LOW);
    }
    tocava = somSonoAtivo;
    int alterados = 0;
    for (int y = 0; y < 64; ++y) for (int x = 0; x < 128; ++x)
      alterados += anterior[y][x] != tela.pixels[y][x];
    if (tempoSimulado > 5000) maiorPasso = max(maiorPasso, alterados);
    memcpy(anterior, tela.pixels, sizeof anterior);
    if (argc > 1 && tempoSimulado < 66000 && tempoSimulado % 100 == 0)
      tela.salvar(std::string(argv[1]) + "/sono_" + std::to_string(frame++) + ".pgm");
  }
  assert(estilos.size() == 3 && bips >= 2 && bips <= 3);
  // Reconexão interrompe murmúrio sem ocupar SOUND ou consumir receipt.
  assert(iniciarSomSono(tempoSimulado, 1450));
  processarLinha("HELLO 1 abcd0123");
  assert(!somSonoAtivo && !somExpressivoAtivo);
  processarLinha("FACE 1 abcd0123 1 0 1 0 3500");
  processarLinha("SOUND 1 abcd0123 1 1");
  assert(Serial.saida.find("SOUNDACK 1 abcd0123 1 1") != std::string::npos);
  assert(somExpressivoAtivo && dutiesPwm[PINO_SOM] == 128);
  assert(!iniciarSomSono(tempoSimulado, 1450));
  for (int i = 0; i < 12; ++i) { tempoSimulado += 33; loop(); }
  assert(!somExpressivoAtivo && !motorEmUso());
  // Demonstrações também não recebem sons locais de sono.
  processarLinha("DEMO");
  assert(!iniciarSomSono(tempoSimulado, 1450));
  // Passagem pelo wrap do relógio preserva sons finitos e agendamentos.
  invalidarSessao(); sonoVivoIniciado = false;
  tempoSimulado = 0xffff0000u;
  for (int i = 0; i < 4500; ++i) { tempoSimulado += 33; loop(); }
  assert(!motorEmUso() && niveisGpio[PINO_NSLEEP] == LOW);
  printf("GREEN sono variado, %d bips discretos/4min, motores parados, reconexao e wrap; maior passo %d pixels\n", bips, maiorPasso);
}

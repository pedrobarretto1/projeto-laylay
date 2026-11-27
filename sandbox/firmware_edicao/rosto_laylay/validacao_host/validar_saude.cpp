#include <cassert>
#include <cstdio>
#include "../rosto_laylay.ino"
int main() {
  setup(); tempoSimulado=1000;
  processarLinha("HEALTH 1 7");
  assert(Serial.saida.find("HEALTH 1 7 112233445566 12345678 0 1000")!=std::string::npos);
  assert(!conectado && !motorEmUso());
  processarLinha("HELLO 1 01234567"); processarLinha("FACE 1 01234567 1 0 1 0 3500");
  auto antes=ultimoPacote; invalidarSessaoPor("OLED");
  assert(perdasSessaoCorpo==1 && !strcmp(motivoPerdaSessaoCorpo,"OLED"));
  invalidarSessao(); assert(perdasSessaoCorpo==1); // Não gera perdas repetidas sem sessão.
  processarLinha("HELLO 1 12345678"); processarLinha("HEALTH 1 8");
  assert(perdasSessaoCorpo==1 && ultimoPacote==antes && !conectado && !motorEmUso());
  puts("SAUDE_GREEN: boot distinto de perda de sessao, consulta nao concede movimento");
}

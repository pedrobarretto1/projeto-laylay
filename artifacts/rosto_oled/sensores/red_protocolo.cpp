#include <cassert>
#include "baseline/rosto_laylay.ino"
int main() {
  setup();
  Serial.saida.clear();
  processarLinha("DIST 1 17");
  assert(Serial.saida.find("DIST 1 17 FRENTE") != std::string::npos);
}

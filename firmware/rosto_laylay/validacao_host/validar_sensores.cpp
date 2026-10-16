#include <cassert>
#include <cstdio>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"

int main() {
  Wire.extras[0x29] = true;
  distancias[0].dispositivo.falharInicio = true;
  setup();
  assert(!distancias[0].presente && distancias[1].presente);
  assert(modosGpio[0] == OUTPUT && niveisGpio[0] == LOW);
  assert(modosGpio[10] == INPUT);
  assert(!strcmp(estadoDistancia(distancias[0], 10), "AUSENTE"));
  assert(!strcmp(estadoDistancia(distancias[1], 10), "AGUARDANDO"));
  distancias[0].dispositivo.falharInicio = false;
  iniciarSensoresDistancia();
  assert(distancias[0].presente && distancias[1].presente);
  tempoSimulado = 20; atualizarSensoresDistancia(20);
  tempoSimulado = 40; atualizarSensoresDistancia(40);
  assert(!strcmp(estadoDistancia(distancias[0], 40), "VALIDA"));
  assert(!strcmp(estadoDistancia(distancias[1], 40), "VALIDA"));
  auto ultima = distancias[0].medidaEm;
  distancias[0].dispositivo.pronto = false;
  tempoSimulado = 360; atualizarSensoresDistancia(360);
  assert(distancias[0].medidaEm == ultima);
  assert(!strcmp(estadoDistancia(distancias[0], 360), "EXPIRADA"));
  distancias[1].dispositivo.statusMedida = 4;
  tempoSimulado = 380; atualizarSensoresDistancia(380);
  assert(!strcmp(estadoDistancia(distancias[1], 380), "INVALIDA"));
  distancias[0].dispositivo.erroConsulta = 1;
  tempoSimulado = 400; atualizarSensoresDistancia(400);
  assert(!strcmp(estadoDistancia(distancias[0], 400), "ERRO_I2C"));
  Serial.saida.clear();
  processarLinha("DIST 1 17");
  assert(Serial.saida.find("DIST 1 17 FRENTE 48 ERRO_I2C -1") != std::string::npos);
  assert(Serial.saida.find("BORDA 49 INVALIDA -1") != std::string::npos);
  Serial.saida.clear(); processarLinha("DIST 1 17 extra");
  assert(Serial.saida.find("DIST_INVALIDA") != std::string::npos);
  for (int p : PINOS_MOTOR) assert(dutiesPwm[p] == 0);
  assert(!motorEmUso() && !conectado && niveisGpio[PINO_NSLEEP] == LOW);
  puts("SENSORES_DIAGNOSTICO_OK: endereco, falha isolada, idade, validade, consulta sem MOTOR");
}

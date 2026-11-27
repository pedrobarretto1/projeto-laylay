#include <cassert>
#include <cstdio>
#define LAYLAY_IMU 1
#include "../rosto_laylay.ino"

int main() {
  Wire.extras[0x69] = true;
  Wire.registrosImuAlternativo[0x75] = 0x98;
  Wire.registrosImuAlternativo[0x3F] = 0x20;
  setup();
  assert(imu.presente && enderecoImu == 0x69 && identidadeImu == 0x98);
  assert(Wire.registrosImuAlternativo[0x1B] == 8 && Wire.registrosImu[0x1B] == 0);

  processarLinha("IPROBE 1 1");
  assert(Serial.saida.find("IPROBE 1 1 105 1 152") != std::string::npos);
  assert(enderecoImu == 0x69);
  const auto inicio = millis();
  for (unsigned t = 10; t <= 2500; t += 10) {
    tempoSimulado = inicio + t;
    atualizarImuCorporal(millis());
  }
  processarLinha("IMU 1 2");
  assert(Serial.saida.find("IMU 1 2 104 PRONTA") != std::string::npos);

  Wire.extras[0x69] = false;
  iniciarImuCorporal();
  assert(!imu.presente && !imu.calibrada && imu.bloqueia(millis()));

  Wire.extras[0x68] = true;
  Wire.registrosImu[0x75] = 0x68;
  iniciarImuCorporal();
  assert(imu.presente && enderecoImu == 0x68 && identidadeImu == 0x68);

  Wire.extras[0x69] = true;
  Wire.registrosImu[0x1B] = Wire.registrosImuAlternativo[0x1B] = 0;
  iniciarImuCorporal();
  assert(!imu.presente && !imu.calibrada && imu.bloqueia(millis()));
  assert(Wire.registrosImu[0x1B] == 0 && Wire.registrosImuAlternativo[0x1B] == 0);

  Wire.registrosImu[0x75] = 0x42;
  Wire.registrosImuAlternativo[0x75] = 0x43;
  iniciarImuCorporal();
  assert(!imu.presente && !imu.calibrada && imu.bloqueia(millis()));
  puts("IMU_GREEN: ambos enderecos, amostragem, sonda, ausencia, ambiguidade e identidades invalidas");
}

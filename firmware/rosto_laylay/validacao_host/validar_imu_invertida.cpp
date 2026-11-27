#include <cassert>
#include <cstdio>
#define LAYLAY_IMU_INVERTIDA_X 1
#define LAYLAY_IMU_REPOUSO_ROLL_CG -1129
#define LAYLAY_IMU_REPOUSO_PITCH_CG 280
#include "../rosto_laylay.ino"

int main() {
  EstadoImuCorporal sensor;
  for (unsigned t = 10; t <= 2000; t += 10)
    sensor.incorporar(t, -.05f, .195f, -.98f, 0, 0, .2f, false);
  assert(sensor.calibrada && !sensor.bloqueia(2000));
  assert(fabsf(sensor.roll) < .2f && fabsf(sensor.pitch) < .2f);
  sensor.incorporar(2010, -.05f, .195f, -.98f, 0, 0, -30, false);
  assert(sensor.gz > 29 && sensor.yaw > 0);
  sensor.incorporar(2020, 0, 0, 1, 0, 0, 0, false);
  assert(!strcmp(sensor.manuseio, "TOMBADA") && sensor.bloqueia(2020));
  // Inclinações reais devem cruzar o limiar a partir da base já corrigida.
  auto inclinar = [&](unsigned t, float lateral, float longitudinal = 0) {
    float roll = (lateral - 11.29f) / 57.29578f;
    float pitch = (2.8f + longitudinal) / 57.29578f;
    sensor.incorporar(t, -sinf(pitch), -sinf(roll)*cosf(pitch),
        -cosf(roll)*cosf(pitch), 0, 0, 0, false);
  };
  inclinar(2030, 12);
  assert(!strcmp(sensor.manuseio, "ESTAVEL") && sensor.bloqueia(2030));
  inclinar(2040, 16);
  assert(!strcmp(sensor.manuseio, "INCLINADA") && sensor.bloqueia(2040));
  inclinar(2050, -16);
  assert(!strcmp(sensor.manuseio, "INCLINADA") && sensor.bloqueia(2050));
  inclinar(2060, 0, 16);
  assert(!strcmp(sensor.manuseio, "INCLINADA") && sensor.bloqueia(2060));
  inclinar(2070, 0, -16);
  assert(!strcmp(sensor.manuseio, "INCLINADA") && sensor.bloqueia(2070));
  for (unsigned t = 2080; t <= 2800; t += 10) inclinar(t, 0);
  assert(!sensor.bloqueia(2800));
  puts("IMU_GREEN: zero mecanico, inclinacoes, giro e bloqueio de tombo");
}

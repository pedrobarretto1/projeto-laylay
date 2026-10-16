#pragma once
// Fonte diagnóstica apenas: distância não concede nem renova tração.
#ifndef LAYLAY_SENSORES_DISTANCIA
#define LAYLAY_SENSORES_DISTANCIA 0
#endif
uint32_t maxLoopProtecaoUs = 0, maxRenderProtecaoUs = 0, maxSensorProtecaoUs = 0;
uint32_t ultimoLoopProtecaoUs = 0, maxIntervaloBordaMs = 0;
#if LAYLAY_SENSORES_DISTANCIA
#include <Adafruit_VL53L0X.h>
struct LeitorDistancia {
  Adafruit_VL53L0X dispositivo;
  uint8_t pino, endereco;
  bool presente = false, amostra = false, erroI2c = false;
  uint16_t mm = 65535;
  uint8_t status = 255;
  uint32_t medidaEm = 0;
  LeitorDistancia(uint8_t p, uint8_t e): pino(p), endereco(e) {}
};
LeitorDistancia distancias[2] = {{0, 0x30}, {10, 0x31}};
uint32_t ultimaConsultaDistancia = 0;
uint8_t proximoSensorDistancia = 0;
bool sensorResponde(uint8_t enderecoSensor) {
  Wire.beginTransmission(enderecoSensor);
  return Wire.endTransmission() == 0;
}
void iniciarSensoresDistancia() {
  for (auto &s : distancias) {
    s.presente=s.amostra=s.erroI2c=false;
    s.mm=65535;s.status=255;s.medidaEm=0;
    digitalWrite(s.pino, LOW); pinMode(s.pino, OUTPUT);
  }
  delay(10); // Só no boot, com nSLEEP já cortado.
  for (auto &s : distancias) {
    pinMode(s.pino, INPUT); // Libera o pull-up do módulo; não injeta tensão em XSHUT.
    delay(10);
    s.presente = sensorResponde(0x29) && s.dispositivo.begin(s.endereco, false, &Wire)
      && sensorResponde(s.endereco)
      && s.dispositivo.setMeasurementTimingBudgetMicroSeconds(20000)
      && s.dispositivo.startRangeContinuous(20);
    if (!s.presente) {
      // Uma inicialização parcial não deixa o endereço padrão colidir com o seguinte.
      digitalWrite(s.pino, LOW); pinMode(s.pino, OUTPUT);
    }
  }
}
void lerSensorDistancia(LeitorDistancia &s) {
  if (!s.presente || !s.dispositivo.isRangeComplete()) return;
  uint32_t inicioLeituraUs = micros();
  VL53L0X_RangingMeasurementData_t medida{};
  bool ok = s.dispositivo.Status == VL53L0X_ERROR_NONE;
  if (ok) ok = s.dispositivo.getRangingMeasurement(&medida, false) == VL53L0X_ERROR_NONE;
  if (ok) ok = s.dispositivo.clearInterruptMask(false) == VL53L0X_ERROR_NONE;
  if (&s == &distancias[1] && s.amostra) maxIntervaloBordaMs = max(maxIntervaloBordaMs, uint32_t(millis() - s.medidaEm));
  s.amostra = true; s.medidaEm = millis(); s.erroI2c = !ok;
  s.status = ok ? medida.RangeStatus : 255;
  s.mm = ok ? medida.RangeMilliMeter : 65535;
  maxSensorProtecaoUs = max(maxSensorProtecaoUs, uint32_t(micros() - inicioLeituraUs));
}
void atualizarSensoresDistancia(uint32_t agora) {
  if (agora - ultimaConsultaDistancia < 2) return;
  ultimaConsultaDistancia = agora;
  // Borda primeiro. Aplicar o corte antes de qualquer leitura frontal ou OLED.
  lerSensorDistancia(distancias[1]);
  atualizarMotor(millis());
  lerSensorDistancia(distancias[0]);
}
const char *estadoDistancia(const LeitorDistancia &s, uint32_t agora) {
  if (!s.presente) return "AUSENTE";
  if (!s.amostra) return "AGUARDANDO";
  if (agora - s.medidaEm > 300) return "EXPIRADA";
  if (s.erroI2c) return "ERRO_I2C";
  return s.status == 0 && s.mm > 0 && s.mm < 8190 ? "VALIDA" : "INVALIDA";
}
#else
void iniciarSensoresDistancia() {}
void atualizarSensoresDistancia(uint32_t) {}
#endif
void processarConsultaDistancia(const char *entrada) {
  unsigned long seq; char extra;
  if (sscanf(entrada, "DIST 1 %lu %c", &seq, &extra) != 1 || seq == 0 || seq > 2147483647UL) {
    responderLinha("ERROR 1 DIST_INVALIDA"); return;
  }
#if LAYLAY_SENSORES_DISTANCIA
  auto &f = distancias[0]; auto &b = distancias[1];
  uint32_t agora = millis();
  const char *ef = estadoDistancia(f, agora), *eb = estadoDistancia(b, agora);
  responder("DIST 1 %lu FRENTE 48 %s %d %lu %u BORDA 49 %s %d %lu %u\n", seq,
    ef, !strcmp(ef, "VALIDA") ? int(f.mm) : -1,
    f.amostra ? (unsigned long)(agora - f.medidaEm) : 4294967295UL, unsigned(f.status),
    eb, !strcmp(eb, "VALIDA") ? int(b.mm) : -1,
    b.amostra ? (unsigned long)(agora - b.medidaEm) : 4294967295UL, unsigned(b.status));
#else
  responderLinha("ERROR 1 DIST_DESABILITADA");
#endif
}

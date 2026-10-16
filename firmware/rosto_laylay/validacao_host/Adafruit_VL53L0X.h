#pragma once
// Dublê da fronteira I2C; não representa prova de leitura física.
#include <Wire.h>
#include <cassert>
constexpr int VL53L0X_ERROR_NONE = 0;
struct VL53L0X_RangingMeasurementData_t {
  uint8_t RangeStatus = 0;
  uint16_t RangeMilliMeter = 180;
};
struct Adafruit_VL53L0X {
  int Status = 0, erroConsulta = 0;
  bool pronto = true, falharInicio = false;
  uint8_t statusMedida = 0;
  uint16_t distancia = 180;
  bool begin(uint8_t endereco, bool, WireSimulada *) {
    assert(niveisGpio[7] == LOW);
    assert(modosGpio[endereco == 0x30 ? 0 : 10] == INPUT);
    if (endereco == 0x30) assert(modosGpio[10] == OUTPUT && niveisGpio[10] == LOW);
    if (falharInicio) return false;
    Wire.extras[endereco] = true;
    return true;
  }
  bool startRangeContinuous(int) { return true; }
  bool setMeasurementTimingBudgetMicroSeconds(uint32_t us) { assert(us==20000); return true; }
  bool isRangeComplete() { Status = erroConsulta; return pronto || Status; }
  int getRangingMeasurement(VL53L0X_RangingMeasurementData_t *m, bool) {
    m->RangeStatus = statusMedida; m->RangeMilliMeter = distancia;
    return erroConsulta;
  }
  int clearInterruptMask(bool) { return erroConsulta; }
};

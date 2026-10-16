#pragma once
#include <Arduino.h>
#include <cstdint>
struct WireSimulada {
  bool presente = true;
  uint8_t alvo = 0;
  bool extras[128] = {};
  uint32_t demoraTransmissao = 0;
  uint32_t clockHz = 100000;
  void begin(int, int) {}
  void setClock(uint32_t hz) { clockHz=hz; }
  size_t write(uint8_t) { return 1; }
  size_t write(const uint8_t *,size_t n) { return n; }
  void setTimeOut(int) {}
  void beginTransmission(uint8_t v) { alvo = v; }
  int endTransmission() {
    tempoSimulado += demoraTransmissao;
    return presente && (alvo == 0x3C || extras[alvo]) ? 0 : 4;
  }
};
inline WireSimulada Wire;

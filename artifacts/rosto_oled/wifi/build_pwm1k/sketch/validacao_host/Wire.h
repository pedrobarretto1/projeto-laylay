#line 1 "C:\\Users\\pbarr\\Downloads\\pasta organizada\\programacao\\PY\\projeto lay\\laylay\\firmware\\rosto_laylay\\validacao_host\\Wire.h"
#pragma once
#include <Arduino.h>
#include <cstdint>
struct WireSimulada {
  bool presente = true;
  uint8_t alvo = 0;
  uint32_t demoraTransmissao = 0;
  void begin(int, int) {}
  void setTimeOut(int) {}
  void beginTransmission(uint8_t v) { alvo = v; }
  int endTransmission() {
    tempoSimulado += demoraTransmissao;
    return presente && alvo == 0x3C ? 0 : 4;
  }
};
inline WireSimulada Wire;

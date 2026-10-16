#pragma once
#include <Arduino.h>
#include <cstdint>
struct WireSimulada {
  bool presente = true;
  uint8_t alvo = 0;
  bool extras[128] = {};
  uint32_t demoraTransmissao = 0;
  uint32_t clockHz = 100000;
  uint8_t registrosImu[128]={}, registroImu=0, escritosImu=0;
  void begin(int, int) {}
  void setClock(uint32_t hz) { clockHz=hz; }
  size_t write(uint8_t valor) {
    if(alvo==0x68) {
      if(!escritosImu++) registroImu=valor;
      else registrosImu[registroImu++ & 127]=valor;
    }
    return 1;
  }
  size_t write(const uint8_t *,size_t n) { return n; }
  void setTimeOut(int) {}
  void beginTransmission(uint8_t v) { alvo = v; escritosImu=0; }
  int endTransmission(bool = true) {
    tempoSimulado += demoraTransmissao;
    return presente && (alvo == 0x3C || extras[alvo]) ? 0 : 4;
  }
  uint8_t requestFrom(uint8_t e, uint8_t n) {return presente && e==0x68 && extras[e]?n:0;}
  int read() {return registrosImu[registroImu++ & 127];}
};
inline WireSimulada Wire;

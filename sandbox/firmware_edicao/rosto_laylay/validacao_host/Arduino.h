// Dublê de hardware para compilar o firmware real e inspecionar seus frames.
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cctype>
#include <cstdarg>
#include <cstdlib>
#include <string>
using std::min;
using std::max;
inline uint32_t tempoSimulado = 0;
inline uint32_t subMilissegundos = 0;
inline bool relogioAvanca = false;
constexpr int LOW = 0, HIGH = 1, INPUT = 1, OUTPUT = 3;
inline int niveisGpio[32] = {}, modosGpio[32] = {};
inline uint32_t dutiesPwm[32] = {};
inline uint32_t frequenciasPwm[32] = {};
inline uint8_t resolucoesPwm[32] = {};
inline bool pinosPwm[32] = {}, falhaPwm = false;
inline bool invertidosPwm[32] = {}, falhaInversaoPwm = false;
inline int falhaPwmPino = -1;
inline void pinMode(int pino, int modo) { modosGpio[pino] = modo; }
inline void digitalWrite(int pino, int nivel) { niveisGpio[pino] = nivel; }
inline bool ledcAttach(uint8_t pino, uint32_t frequencia, uint8_t resolucao) {
  if (falhaPwm || pino == falhaPwmPino) return false;
  frequenciasPwm[pino] = frequencia; resolucoesPwm[pino] = resolucao;
  pinosPwm[pino] = true; return true;
}
inline int ultimoCanalExplicito = -1;
inline bool ledcAttachChannel(uint8_t pino, uint32_t frequencia, uint8_t resolucao, uint8_t canal) {
  ultimoCanalExplicito = canal;
  return ledcAttach(pino, frequencia, resolucao);
}
inline uint32_t ledcReadFreq(uint8_t pino) { return pinosPwm[pino] ? frequenciasPwm[pino] : 0; }
inline bool ledcOutputInvert(uint8_t pino, bool inverter) {
  if (!pinosPwm[pino] || (inverter && falhaInversaoPwm)) return false;
  invertidosPwm[pino] = inverter; return true;
}
inline bool ledcWrite(uint8_t pino, uint32_t duty) {
  if (falhaPwm || pino == falhaPwmPino || !pinosPwm[pino]) return false;
  dutiesPwm[pino] = duty; return true;
}
inline bool ledcDetach(uint8_t pino) {
  pinosPwm[pino] = false; dutiesPwm[pino] = 0; return true;
}
inline uint32_t millis() { return relogioAvanca ? tempoSimulado++ : tempoSimulado; }
inline uint32_t micros() { return tempoSimulado * 1000u + subMilissegundos; }
inline void delay(int) {}
inline long random(long a, long b) { return a + rand() % (b - a); }
struct SerialSimulada {
  std::string entrada, saida;
  void begin(int) {}
  int available() { return entrada.size(); }
  int read() { char c = entrada[0]; entrada.erase(0, 1); return c; }
  void println(const char *s) { saida += s; saida += '\n'; }
  void printf(const char *formato, ...) {
    char buffer[256]; va_list args; va_start(args, formato);
    vsnprintf(buffer, sizeof(buffer), formato, args); va_end(args); saida += buffer;
  }
};
inline SerialSimulada Serial;

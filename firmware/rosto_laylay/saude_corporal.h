#pragma once
// Consulta factual: não renova FACE nem concede tração.
#ifdef ARDUINO_ARCH_ESP32
#include <esp_system.h>
#include <esp_random.h>
#endif
char identidadeCorpo[13]="112233445566", bootCorpo[9]="12345678";
uint32_t motivoBootCorpo=0, perdasSessaoCorpo=0, perdaSessaoEm=0;
const char *motivoPerdaSessaoCorpo="NENHUMA";
void iniciarSaudeCorporal() {
#ifdef ARDUINO_ARCH_ESP32
  snprintf(identidadeCorpo,sizeof(identidadeCorpo),"%012llx",(unsigned long long)ESP.getEfuseMac());
  snprintf(bootCorpo,sizeof(bootCorpo),"%08lx",(unsigned long)esp_random());
  motivoBootCorpo=uint32_t(esp_reset_reason());
#endif
}
void registrarPerdaSessao(const char *motivo) {
  if (conectado || sessao[0]) {
    ++perdasSessaoCorpo; perdaSessaoEm=millis(); motivoPerdaSessaoCorpo=motivo;
  }
}
void processarSaudeCorporal(const char *entrada) {
  char pacote[80],*campos[3]; uint32_t seq;
  if (!separarCampos(entrada,pacote,sizeof(pacote),campos,3)
      || strcmp(campos[1],"1") || !decimalSemSinal(campos[2],seq) || !seq) {
    responderLinha("ERROR 1 HEALTH_INVALIDA"); return;
  }
  uint32_t livre=0,minimo=0;
#ifdef ARDUINO_ARCH_ESP32
  livre=esp_get_free_heap_size(); minimo=esp_get_minimum_free_heap_size();
#endif
  responder("HEALTH 1 %lu %s %s %lu %lu %lu %lu %lu %s %lu\n",
    (unsigned long)seq,identidadeCorpo,bootCorpo,(unsigned long)motivoBootCorpo,
    (unsigned long)millis(),(unsigned long)livre,(unsigned long)minimo,
    (unsigned long)perdasSessaoCorpo,motivoPerdaSessaoCorpo,(unsigned long)perdaSessaoEm);
}

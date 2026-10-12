#include <cassert>
#include <cstdio>
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#define LAYLAY_LIMITE_MOTOR_TESTE_MS 5000
#include "../rosto_laylay.ino"
int main() {
  setup(); tempoSimulado=1000;
  processarLinha("HELLO 1 abcd0123");
  processarLinha("LCAPS 1 abcd0123");
  assert(Serial.saida.find("LCAPS 1 abcd0123 LONGO1")!=std::string::npos);
  processarLinha("FACE 1 abcd0123 1 0 1 0 3500");
  processarLinha("MOTOR 1 abcd0123 1 180 180 5001"); assert(!motorPendente && !motorAtivo);
  processarLinha("MOTOR 1 abcd0123 1 180 180 5000"); assert(motorPendente);
  uint32_t seq=1;
  for(uint32_t t=1002;t<6000;t+=20) {
    tempoSimulado=t;
    if((t-1002)%200==0) {
      char p[128]; snprintf(p,sizeof(p),"FACE 1 abcd0123 %u 0 1 0 3500",++seq); processarLinha(p);
    }
    atualizarMotor(t);
    assert(motorAtivo && pwmEsquerdo==180 && pwmDireito==180);
  }
  tempoSimulado=6000; atualizarMotor(6000);
  assert(!motorAtivo && !motorPendente && niveisGpio[PINO_NSLEEP]==LOW);
  // FACE não estende o prazo do motor; ausência de heartbeat corta antes dele.
  processarLinha("MOTOR 1 abcd0123 2 200 -200 5000");
  tempoSimulado=6002; atualizarMotor(6002); assert(motorAtivo);
  tempoSimulado=ultimoPacote+ttl; atualizarMotor(tempoSimulado);
  assert(!motorAtivo && niveisGpio[PINO_NSLEEP]==LOW);
  puts("MOTOR_LONGO_OK: LONGO1/5s continuo/corte absoluto/TTL/limite5001 rejeitado");
}

#include <cassert>
#include <cstdio>
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#define LAYLAY_LIMITE_MOTOR_TESTE_MS 5000
#include "../rosto_laylay.ino"
int main(int argc, char **argv) {
  setup(); tempoSimulado=1000;
  processarLinha("HELLO 1 abcd0123");
  processarLinha("ECAPS 1 abcd0123");
  assert(Serial.saida.find("OLHOS2")!=std::string::npos);
  processarLinha("FACE 1 abcd0123 1 0 1 0 3500");
  renderizar(tempoSimulado);
  float antes=repouso;
  for(int i=1;i<=40;++i) {
    tempoSimulado=1000+i*33; renderizar(tempoSimulado);
    assert(repouso<=antes && antes-repouso<.07f); antes=repouso;
    if(argc>1 && i%10==0) tela.salvar(std::string(argv[1])+"/acordar_"+std::to_string(i)+".pgm");
  }
  assert(repouso>.4f && repouso<.9f); // Acordar leva ~3 s, não abre logo no início.
  for(int i=41;i<=105;++i) {
    tempoSimulado=1000+i*33; renderizar(tempoSimulado);
  }
  assert(repouso<.01f);
  processarLinha("FACE 1 abcd0123 2 0 1 0 3500");
  uint32_t heartbeat=ultimoPacote;
  processarLinha("EXPR 1 abcd0123 1 9 3 0 1200");
  assert(ackExpressaoPendente && !motorAtivo && ultimoPacote==heartbeat);
  assert(Serial.saida.find("EACK 1 abcd0123 1")==std::string::npos);
  renderizar(tempoSimulado);
  assert(Serial.saida.find("EACK 1 abcd0123 1 9 3 0 1200")!=std::string::npos);
  processarLinha("EXPR 1 abcd0123 1 9 3 0 1200"); assert(!ackExpressaoPendente);
  processarLinha("EXPR 1 abcd0123 2 9 3 0 6001"); assert(!ackExpressaoPendente);
  processarLinha("EXPR 1 ffff0123 2 9 3 0 900"); assert(!ackExpressaoPendente);
  processarLinha("EXPR 1 abcd0123 2 1 1 1 900 extra"); assert(!ackExpressaoPendente);
  // Noite corta energia imediatamente, enquanto o rosto fecha gradualmente.
  processarLinha("MOTOR 2 abcd0123 1 200 200 1000");
  assert(motorPendente);
  uint32_t inicioSuave=tempoSimulado;
  tempoSimulado=inicioSuave+2; atualizarMotor(tempoSimulado);
  assert(motorAtivo && dutiesPwm[1]>0 && dutiesPwm[1]<200);
  assert(Serial.saida.find("MACK 2 abcd0123 1")==std::string::npos);
  tempoSimulado=inicioSuave+170; atualizarMotor(tempoSimulado);
  assert(dutiesPwm[1]==200 && Serial.saida.find("MACK 2 abcd0123 1 200 200 1000")!=std::string::npos);
  tempoSimulado=inicioSuave+950; atualizarMotor(tempoSimulado);
  assert(dutiesPwm[1]>0 && dutiesPwm[1]<200);
  tempoSimulado=inicioSuave+1000; atualizarMotor(tempoSimulado);
  assert(!motorAtivo && niveisGpio[PINO_NSLEEP]==LOW);
  processarLinha("FACE 1 abcd0123 3 1 2 0 3500");
  for(int i=0;i<35;++i) { tempoSimulado+=33; renderizar(tempoSimulado); }
  float alegriaAntesDoSono=olhosAlegres;
  assert(alegriaAntesDoSono>.95f);
  processarLinha("MOTOR 1 abcd0123 2 180 180 5000");
  tempoSimulado+=2; atualizarMotor(tempoSimulado); assert(motorAtivo);
  processarLinha("GOODNIGHT 1 abcd0123 2");
  assert(!motorAtivo && !conectado && niveisGpio[PINO_NSLEEP]==LOW);
  antes=repouso;
  uint32_t inicio=tempoSimulado;
  for(int i=1;i<=100;++i) {
    tempoSimulado=inicio+i*33; renderizar(tempoSimulado);
    assert(repouso>=antes && repouso-antes<.07f); antes=repouso;
    assert(emocao==0 && olhosAlegres==alegriaAntesDoSono); // Estado invalidado, geometria conservada.
    if(i==40) assert(repouso<.7f); // Fechamento não salta para o sono em ~1 s.
    if(argc>1 && i%10==0) tela.salvar(std::string(argv[1])+"/dormir_"+std::to_string(i)+".pgm");
  }
  assert(repouso>.95f && !somExpressivoAtivo);
  puts("PRESENCA_V2_OK: render/sem autoridade/TTL/replay/acordar e adormecer graduais/corte imediato");
}

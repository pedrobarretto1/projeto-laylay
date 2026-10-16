#include <cstdio>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../../../../firmware/rosto_laylay/rosto_laylay.ino"
void mundo(uint32_t t,int f,int b) {
  tempoSimulado=t;
  for(int i=0;i<2;++i) {
    auto &s=distancias[i]; s.presente=s.amostra=true; s.erroI2c=false;
    s.mm=i?b:f; s.status=0; s.medidaEm=t; s.dispositivo.distancia=s.mm;
    s.dispositivo.statusMedida=0;
  }
  atualizarMotor(t); atualizarSomExpressivo(t); renderizar(t);
}
int main() {
  Wire.extras[0x29]=true; setup(); tempoSimulado=40;
  processarLinha("HELLO 1 01234567"); processarLinha("FACE 1 01234567 1 0 1 0 3500");
  for(uint32_t t=60;t<=3250;t+=33) mundo(t,200,100);
  mundo(3270,200,150); mundo(3390,200,150);
  tela.salvar("artifacts/rosto_oled/protecao_sensores/presenca/medo.pgm");
  for(uint32_t t=3420;t<4400;t+=33) {
    ultimoPacote=t; mundo(t,200,150);
  }
  tela.salvar("artifacts/rosto_oled/protecao_sensores/presenca/pavor.pgm");
  for(uint32_t t=4420;t<5200;t+=33) { ultimoPacote=t; mundo(t,80,100); }
  tela.salvar("artifacts/rosto_oled/protecao_sensores/presenca/irritada.pgm");
  for(int p:PINOS_MOTOR) assert(dutiesPwm[p]==0);
  puts("FRAMES_GERADOS_SEM_MOTOR");
}

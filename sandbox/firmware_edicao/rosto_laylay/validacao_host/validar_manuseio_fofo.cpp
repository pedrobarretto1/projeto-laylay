#include <cassert>
#include <cstdio>
#define LAYLAY_IMU 1
#define LAYLAY_TESTE_SOMENTE_IMU 1
#include "../rosto_laylay.ino"
void medir(unsigned t,float ay=0,float az=1,float gx=0) {
  tempoSimulado=t;imu.incorporar(t,0,ay,az,gx,0,0,false);
  atualizarReacaoManuseio(t);
}
int main() {
  Wire.extras[0x68]=true;Wire.registrosImu[0x75]=0x98;
  setup();
  for(unsigned t=10;t<2500;t+=10) medir(t);
  processarLinha("HELLO 1 01234567");
  processarLinha("FACE 1 01234567 1 0 1 0 5000");
  for(unsigned t=2500;t<4100;t+=10) medir(t,.34f,.94f);
  assert(expressaoManuseio()==3 && "inclinacao mantida deve ter olhar desconfiado");
  for(unsigned t=4100;t<4300;t+=10) medir(t,0,1,200);
  assert(expressaoManuseio()!=0);
  assert(!motorEmUso());
  for(unsigned t=4300;t<6000;t+=10) medir(t);
  assert(expressaoManuseio()==4 && "recuperacao conserva resmungo e relaxa depois");
  for(unsigned t=6000;t<9500;t+=10) medir(t);
  assert(expressaoManuseio()==0);
  assert(!motorEmUso() && niveisGpio[0]==LOW && niveisGpio[10]==LOW);
  puts("MANUSEIO_FOFO_GREEN: continuidade, recuperacao e isolamento");
}

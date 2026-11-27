#include <cassert>
#include <cstdio>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"
void amostra(uint32_t t,int f=200,int b=100,int bs=0) {
  tempoSimulado=t;
  for(int i=0;i<2;++i) {
    auto &s=distancias[i]; s.presente=s.amostra=true; s.erroI2c=false; s.medidaEm=t;
    s.mm=i ? b : f; s.status=i ? bs : 0;
    s.dispositivo.distancia=s.mm; s.dispositivo.statusMedida=s.status;
  }
}
void tick(uint32_t t,int f=200,int b=100,int bs=0) { amostra(t,f,b,bs); atualizarMotor(t); atualizarSomExpressivo(t); }
void ligar(const char *s="01234567") {
  char cmd[100]; sprintf(cmd,"HELLO 1 %s",s); processarLinha(cmd);
  sprintf(cmd,"FACE 1 %s 1 0 1 0 3500",s); processarLinha(cmd);
}
void vigia(uint32_t seq,uint32_t ativo=1) {
  char cmd[100]; sprintf(cmd,"SENTRY 1 01234567 %u %u 1200",seq,ativo); processarLinha(cmd);
}
int main() {
  Wire.extras[0x29]=true; setup(); amostra(40); ligar();
  tick(50,200,150); assert(medoProtecaoCorporal(50) && expressaoProtecaoCorporal(50)==1);
  assert(!motorEmUso() && sequenciaMotor==0);
  tick(951,200,150); assert(expressaoProtecaoCorporal(951)==2 && !motorEmUso());
  tick(970,80); assert(expressaoProtecaoCorporal(970)==3 && !motorEmUso());
  tick(1000); assert(expressaoProtecaoCorporal(1000)==0);
  tick(1030,80); vigia(1); tick(1040,80); assert(reflexoProtecaoAtivo());
  assert(origemVigiaProtecao && motorOrigemProtecao==0);
  tick(1042,80); tick(1044,80); assert(dutiesPwm[2]==160 && dutiesPwm[4]==160);
  tick(1290,80); tick(1390,80); assert(!strcmp(faseProtecao,"BUSCANDO"));
  tick(1392,80); tick(1394,80); assert(dutiesPwm[1]==170 && dutiesPwm[4]==170);
  tick(1550,80); assert(!strcmp(faseProtecao,"CONFERINDO") && !motorEmUso());
  tick(1570); tick(1590); tick(1610); assert(!strcmp(faseProtecao,"SEGUINDO"));
  tick(1612); tick(1614); assert(dutiesPwm[1]==120 && dutiesPwm[3]==120);
  tick(1630,200,150); assert(!motorEmUso() && !reflexoProtecaoAtivo()); // Borda supera parede.
  tick(1690); tick(1750); tick(1810); assert(!travaProtecao);
  tick(1840,80); vigia(2); tick(1850,80); assert(reflexoProtecaoAtivo());
  processarLinha("STOP"); tick(1880,80); assert(!reflexoProtecaoAtivo() && !motorEmUso());
  tick(1940); tick(2000); tick(2060);
  tick(2070,80); vigia(3); tick(2080,80);
  // Parede sem saída: no máximo4 tentativas, leitura entre elas, sem loop.
  unsigned faceSeq=1;
  for(uint32_t t=2100;t<5100;t+=20) {
    if(t%500==100) {
      char face[100]; sprintf(face,"FACE 1 01234567 %u 0 1 0 3500",++faceSeq); processarLinha(face);
    }
    if(t==2700) vigia(4);
    if(t==3500) vigia(5);
    if(t==4300) vigia(6);
    tick(t,80);
  }
  assert(tentativasBuscaProtecao==4 && !reflexoProtecaoAtivo() && !motorEmUso());
  assert(expressaoProtecaoCorporal(millis())==3);
  auto incidentes=incidenteProtecao;
  for(uint32_t t=5120;t<6000;t+=20) tick(t,80);
  assert(incidenteProtecao==incidentes && !motorEmUso());
  // Nova sessão não herda VIGIA nem sequência; rosto sozinho não move motores.
  amostra(6000,80); ligar("abcdef01"); tick(6020,80);
  assert(!vigiaProtecao && !motorEmUso());
  processarLinha("SENTRY 1 01234567 99 1 1200"); assert(!vigiaProtecao);
  processarLinha("SENTRY 1 abcdef01 1 1 1200"); assert(vigiaProtecao);
  tick(6060,200,100); tick(6080); tick(6100);
  tick(6120,80); assert(reflexoProtecaoAtivo());
  tick(7250,80); assert(!vigiaProtecao && !motorEmUso()); // Lease expirada corta busca.
  amostra(7300,200,150); processarLinha("GOODNIGHT 1 abcdef01 1");
  atualizarMotor(7300); assert(!medoProtecaoCorporal(7300) && !motorEmUso());
  puts("PRESENCA_GREEN: alerta parado, pavor sem tracao, parede4 buscas, borda prioritaria, lease, STOP, sono");
}

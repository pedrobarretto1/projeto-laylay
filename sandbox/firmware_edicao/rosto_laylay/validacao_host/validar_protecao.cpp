#include <cassert>
#include <cstdio>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#define LAYLAY_LIMITE_MOTOR_TESTE_MS 5000
#include "../rosto_laylay.ino"
void amostra(unsigned t, int frente=200, int borda=100, int fs=0, int bs=0) {
  tempoSimulado = t;
  for (int i=0;i<2;++i) {
    distancias[i].presente = distancias[i].amostra = true;
    distancias[i].erroI2c = false; distancias[i].medidaEm = t;
  }
  distancias[0].mm=frente; distancias[1].mm=borda;
  distancias[0].status=fs; distancias[1].status=bs;
}
void tick(unsigned t,int f=200,int b=100,int fs=0,int bs=0) { amostra(t,f,b,fs,bs); atualizarMotor(t); }
void inicio(unsigned seq) {
  char cmd[90]; snprintf(cmd,sizeof(cmd),"MOTOR 1 01234567 %u 200 200 3000",seq);
  processarLinha(cmd);
}
int main() {
  Wire.extras[0x29]=true; setup(); amostra(40);
  processarLinha("HELLO 1 01234567"); processarLinha("FACE 1 01234567 1 0 1 0 3500");
  assert(!strcmp(riscoProtecao(40),"NENHUM"));
  amostra(40,101,130); assert(!strcmp(riscoProtecao(40),"NENHUM"));
  amostra(40,100,130); assert(!strcmp(riscoProtecao(40),"OBSTACULO"));
  amostra(40,200,131); assert(!strcmp(riscoProtecao(40),"BORDA"));
  amostra(40,8190,100,4); assert(!strcmp(riscoProtecao(40),"NENHUM"));
  amostra(40,200,8190,0,4); assert(!strcmp(riscoProtecao(40),"BORDA_SEM_RETORNO"));
  assert(!strcmp(riscoProtecao(341),"FALHA_BORDA"));
  amostra(50); inicio(1); tick(52); assert(dutiesPwm[1]==200 && dutiesPwm[3]==200);
  tick(70,200,150); assert(dutiesPwm[1]==0 && dutiesPwm[3]==0);
  assert(!strcmp(faseProtecao,"RECUANDO")); assert(medoProtecaoCorporal(70));
  tick(72,200,150); tick(74,200,150); assert(dutiesPwm[2]==120 && dutiesPwm[4]==120);
  // Borda ainda presente após recuo agora bloqueia/pavor. Para virar, uma
  // nova leitura precisa restabelecer superfície (contrato novo solicitado).
  tick(320); assert(!motorEmUso()); tick(420);
  tick(422); tick(424); assert(dutiesPwm[1]==140 && dutiesPwm[4]==140);
  tick(1320); assert(!strcmp(faseProtecao,"VERIFICANDO") && !motorEmUso());
  tick(1380); tick(1440); assert(!strcmp(faseProtecao,"VERIFICANDO"));
  tick(1500); assert(!strcmp(faseProtecao,"SEGUINDO"));
  tick(1502); tick(1504); assert(dutiesPwm[1]==120 && dutiesPwm[3]==120);
  tick(1530,200,150); assert(!strcmp(faseProtecao,"BLOQUEADA") && !motorEmUso());
  inicio(2); assert(!reflexoProtecaoAtivo()); // Não repete recuos infinitamente.
  tick(1590); tick(1650); tick(1710); assert(!travaProtecao);
  inicio(3); tick(1712); tick(1730,80); assert(reflexoProtecaoAtivo());
  processarLinha("STOP"); assert(!reflexoProtecaoAtivo() && !motorEmUso());
  tick(1790); tick(1850); tick(1910); inicio(4); tick(1912);
  tick(1930,200,8190,0,4); tick(2180,200,8190,0,4); tick(2280,200,8190,0,4);
  tick(3180,200,8190,0,4); tick(3680,200,8190,0,4);
  assert(!reflexoProtecaoAtivo() && !motorEmUso());
  // Só 3 medições realmente novas após o giro podem liberar avanço.
  tick(3740); tick(3800); tick(3860); inicio(5); tick(3862); tick(3880,200,150);
  tempoSimulado=4200; atualizarMotor(4200); assert(!motorEmUso() && !reflexoProtecaoAtivo());
  // At rest, distância nunca concede tração; sessão expirada também não.
  tick(4300,80,150); assert(!motorEmUso());
  Serial.saida.clear(); processarLinha("GUARD 1 77");
  assert(Serial.saida.find("GUARD 1 77 01234567")!=std::string::npos);
  puts("PROTECAO_GREEN: limiares, corte, medo, recuo, giro, 3 amostras, falha, STOP, sem loop");
}

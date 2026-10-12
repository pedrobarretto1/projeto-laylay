#include <cassert>
#include <cstdio>
#include "../rosto_laylay.ino"
int main(int argc, char **argv) {
  setup(); assert(!bipInicioAtivo && !somExpressivoAtivo && niveisGpio[6] == LOW);
  tempoSimulado=1000;
  processarLinha("HELLO 1 abcd0123");
  processarLinha("FACE 1 abcd0123 1 0 1 0 3500");
  renderizar(tempoSimulado);
  processarLinha("SCAPS 1 abcd0123");
  assert(Serial.saida.find("SOM1")!=std::string::npos);
  processarLinha("SOUND 1 abcd0123 1 0");
  assert(somExpressivoAtivo && frequenciasPwm[6]==1400 && dutiesPwm[6]==128);
  for(int p:PINOS_MOTOR) assert(dutiesPwm[p]==0 && frequenciasPwm[p]==1000);
  tempoSimulado+=70; atualizarSomExpressivo(tempoSimulado);
  assert(!pinosPwm[6] && somExpressivoAtivo);
  tempoSimulado+=35; atualizarSomExpressivo(tempoSimulado);
  assert(frequenciasPwm[6]==1850 && dutiesPwm[6]==128);
  tempoSimulado+=90; atualizarSomExpressivo(tempoSimulado);
  assert(!somExpressivoAtivo && niveisGpio[6]==LOW && !pinosPwm[6]);
  processarLinha("SOUND 1 abcd0123 1 0"); assert(!somExpressivoAtivo);
  processarLinha("SOUND 1 ffff0123 2 0"); assert(!somExpressivoAtivo);
  processarLinha("SOUND 1 abcd0123 2 9"); assert(!somExpressivoAtivo);
  processarLinha("SOUND 1 abcd0123 2 1 extra"); assert(!somExpressivoAtivo);
  tempoSimulado=2600;
  processarLinha("SOUND 1 abcd0123 3 1"); assert(somExpressivoAtivo);
  tempoSimulado+=450; atualizarSomExpressivo(tempoSimulado);
  assert(!somExpressivoAtivo && !pinosPwm[6]);
  tempoSimulado=4200; processarLinha("SOUND 1 abcd0123 4 2"); assert(somExpressivoAtivo);
  invalidarSessao(); assert(!somExpressivoAtivo && niveisGpio[6]==LOW);
  // Centro inferior do rosto deve ficar sem boca em todas as emoções.
  conectado=true; demonstracao=false; painelHack=0; atividade=false; glitch=false;
  proximaPiscada=proximoOlhar=10000000;
  for(int e=0;e<9;++e) {
    emocao=e; nivel=2;
    for(int f=0;f<90;++f) renderizar(5000+e*4000+f*33);
    for(int y=45;y<62;++y) for(int x=48;x<80;++x) assert(!tela.getPixel(x,y));
    uint8_t antes[64][128]; memcpy(antes,tela.pixels,sizeof(antes));
    falando=!falando; renderizar(5000+e*4000+89*33);
    assert(memcmp(antes,tela.pixels,sizeof(antes))==0);
    if(argc>1) tela.salvar(std::string(argv[1])+"/olhos_"+std::to_string(e)+".pgm");
  }
  puts("SOM_OLHOS_OK: notas/pausa/corte/replay/sessao/sem boca/motores preservados");
}

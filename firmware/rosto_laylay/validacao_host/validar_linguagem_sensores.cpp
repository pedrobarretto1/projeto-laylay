#include <cassert>
#include <cstdio>
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"
void tick(uint32_t t,int frente,int borda=100) {
  tempoSimulado=t;
  for(int i=0;i<2;++i) {
    auto &s=distancias[i]; s.presente=s.amostra=true; s.erroI2c=false;
    s.medidaEm=t; s.mm=i ? borda : frente; s.status=0;
  }
  atualizarMotor(t); atualizarSomExpressivo(t);
}
int main(int argc,char **argv) {
  assert(argc==2); Wire.extras[0x29]=true; setup(); tick(40,200);
  processarLinha("HELLO 1 01234567");
  processarLinha("FACE 1 01234567 1 0 1 0 3500");
  if(!strncmp(argv[1],"parede_borda_",13)) {
    bool stop=!strcmp(argv[1],"parede_borda_stop");
    unsigned face=1,seq=0; bool voltou=false;
    for(uint32_t t=60;t<9000;t+=10) {
      tempoSimulado=t;
      if((t-60)%100==0) {
        char cmd[100]; sprintf(cmd,"FACE 1 01234567 %u 0 1 0 3500",++face); processarLinha(cmd);
        sprintf(cmd,"SENTRY 1 01234567 %u 1 1200",++seq); processarLinha(cmd);
      }
      tick(t,80,t>=800 && t<900 ? 150 : 100);
      if(stop && t==850) processarLinha("STOP");
      if(t==810) assert(!motorEmUso() && !strcmp(faseProtecao,"BLOQUEADA"));
      if(t==910) assert(incidenteProtecao==1 && !motorEmUso()); // Só duas leituras seguras.
      if(t>1000) voltou|=motorAtivo && pwmEsquerdo*pwmDireito<0;
      assert(!(motorAtivo && pwmEsquerdo>0 && pwmDireito>0));
    }
    if(stop) assert(incidenteProtecao==1 && !voltou);
    else assert(incidenteProtecao>=2 && voltou);
    processarLinha("STOP"); assert(!motorEmUso());
    puts("PAREDE_BORDA_GREEN: borda corta busca; tres leituras seguras admitem outro episodio de parede"); return 0;
  }
  if (!strncmp(argv[1],"pausa_",6)) {
    bool descanso=!strcmp(argv[1],"pausa_descanso");
    bool expirar=!strcmp(argv[1],"pausa_lease");
    bool stop=!strcmp(argv[1],"pausa_stop");
    bool borda=!strcmp(argv[1],"pausa_borda");
    bool histerese=!strcmp(argv[1],"pausa_histerese");
    bool falha=!strcmp(argv[1],"pausa_falha");
    unsigned seq=0,face=1; uint32_t pausa=descanso ? 3000 : 800;
    bool cortou=false,girouDepois=false;
    for(uint32_t t=60;t<12000;t+=10) {
      tempoSimulado=t;
      if((t-60)%100==0) {
        char cmd[100]; sprintf(cmd,"FACE 1 01234567 %u 0 1 0 3500",++face); processarLinha(cmd);
        bool suspensa=t>=pausa && t<pausa+2000;
        if(!expirar || !suspensa) {
          sprintf(cmd,"SENTRY 1 01234567 %u %u 1200",++seq,unsigned(!suspensa)); processarLinha(cmd);
        }
      }
      if(stop && t==pausa) processarLinha("STOP");
      if(falha && t==pausa) { tempoSimulado=t; distancias[1].erroI2c=true; atualizarMotor(t); }
      tick(t,80,borda ? 150 : histerese && t>=pausa ? 125 : 100);
      if(t==pausa+1500) { assert(!motorEmUso()); cortou=true; }
      if(t>pausa+2000) girouDepois|=motorAtivo && pwmEsquerdo*pwmDireito<0;
      assert(!(motorAtivo && pwmEsquerdo>0 && pwmDireito>0));
    }
    assert(cortou);
    if(stop || borda || histerese || falha) assert(incidenteProtecao==1 && !girouDepois && !motorEmUso());
    else assert(incidenteProtecao>=2 && girouDepois); // Prioridade temporária não é revogação definitiva.
    processarLinha("STOP"); assert(!motorEmUso());
    puts("PAUSA_GREEN: corta sem concessao, reavalia parede, preserva STOP e limite da borda"); return 0;
  }
  if(!strcmp(argv[1],"vetos")) {
    // Distância/rosto sem concessão não acionam tração, mesmo com perigo.
    tick(50,200,150); tick(60,80,150); assert(!motorEmUso());
    processarLinha("SENTRY 1 01234567 1 1 1200");
    tick(70,200,150); tick(80,200,150); tick(90,200,150); assert(motorEmUso());
    processarLinha("STOP"); tick(100,200,150); assert(!motorEmUso());
    tick(200,200,150); assert(!reflexoProtecaoAtivo());
    // Reabilitação é explícita e não apaga uma trava sem leituras seguras.
    tick(220,200); tick(240,200); tick(260,200);
    processarLinha("SENTRY 1 01234567 2 1 1200");
    tick(280,200,150); tick(540,200,150); tick(870,200,150);
    tick(880,200,150); tick(890,200,150); assert(motorEmUso());
    tempoSimulado=970; atualizarMotor(970); assert(!motorEmUso()); // Inferior velho.
    puts("VETOS_GREEN: sem concessao, STOP e leitura velha cortam recuos"); return 0;
  }
  if(!strcmp(argv[1],"som")) {
    for(int tipo=9;tipo<=12;++tipo) {
      tempoSimulado=2000*(tipo-8); sinalAlertaProtecao(millis(),tipo);
      assert(somExpressivoAtivo && dutiesPwm[6]==128);
      for(int p:PINOS_MOTOR) assert(dutiesPwm[p]==0 && frequenciasPwm[p]==1000);
      for(int j=1;j<=45;++j) { tempoSimulado+=10; atualizarSomExpressivo(millis()); }
      assert(!somExpressivoAtivo && !pinosPwm[6]);
    }
    puts("SONS_GREEN: quatro contornos, mesmo duty, finitos, timer dos motores preservado"); return 0;
  }
  bool parede=!strcmp(argv[1],"parede");
  bool transicao=!strcmp(argv[1],"transicao");
  unsigned seq=0,face=1,recuos=0; bool antes=false,giro=false,intervalo=false,somBusca=false;
  for(uint32_t t=60;t<12000;t+=10) {
    if((t-60)%400==0) {
      char cmd[100]; sprintf(cmd,"FACE 1 01234567 %u 0 1 0 3500",++face); processarLinha(cmd);
      sprintf(cmd,"SENTRY 1 01234567 %u 1 1200",++seq); processarLinha(cmd);
    }
    bool agoraParede=parede || (transicao && t>=3000);
    tick(t,agoraParede ? 80 : 200,agoraParede ? 100 : 150);
    if(transicao && t==3010) assert(incidenteProtecao==1 && !motorEmUso()); // Duas amostras não bastam.
    bool recuando=motorAtivo && pwmEsquerdo<0 && pwmDireito<0;
    if(recuando && !antes) ++recuos;
    antes=recuando;
    giro|=motorAtivo && pwmEsquerdo*pwmDireito<0;
    somBusca|=somExpressivoAtivo && tipoSomExpressivo==12;
    if(parede && incidenteProtecao==1 && !motorEmUso() && t>3000) intervalo=true;
    if(!agoraParede && t>1100) assert(expressaoProtecaoCorporal(t)==2);
    // Nada avança enquanto não há comprovação de uma saída.
    assert(!(motorAtivo && pwmEsquerdo>0 && pwmDireito>0));
  }
  if(parede) {
    assert(giro && intervalo);
    // Uma busca esgotada descansa e reavalia, não vira bloqueio eterno.
    assert(incidenteProtecao>=2 && incidenteProtecao<=3);
    assert(somBusca); // O intervalo sonoro não pode tornar o contorno inalcançável.
  } else if(transicao) {
    // A borda deixou de existir; parede não deve manter a trava da borda.
    assert(giro && incidenteProtecao>=2);
  } else {
    // Sessão e concessão válidas: recuos hesitantes finitos além do susto.
    assert(recuos==4 && !motorEmUso());
    assert(!giro); // Sem superfície confirmada, não gira nem avança.
  }
  processarLinha("STOP"); tick(12020,80,150);
  assert(!motorEmUso() && !reflexoProtecaoAtivo());
  puts(parede ? "PAREDE_GREEN: busca, descanso e nova tentativa autorizada" : transicao ? "TRANSICAO_GREEN: borda resolvida admite busca de parede com tres amostras novas" : "MEDO_GREEN: quatro recuos finitos com pausas, pavor e parada");
}

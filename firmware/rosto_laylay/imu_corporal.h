#pragma once
// MPU6050: uma única fonte de amostras. Não concede sessão nem movimento.
#ifndef LAYLAY_IMU
#define LAYLAY_IMU 0
#endif
struct EstadoImuCorporal {
  bool presente=false, amostra=false, calibrada=false, erro=false;
  uint32_t medidaEm=0, inicioCal=0, estabilidadeEm=0, movimentoEm=0,inicioBrusco=0;
  unsigned amostrasCal=0;
  float bias[3]={}, soma[3]={}, anterior[3]={};
  float roll=0,pitch=0,yaw=0,gz=0,norma=0,energia=0;
  const char *manuseio="ESTAVEL";
  void calibrar() {
    calibrada=false;amostrasCal=0;inicioCal=0;yaw=0;
    for(int i=0;i<3;++i) soma[i]=bias[i]=0;
  }
  void incorporar(uint32_t t,float ax,float ay,float az,float gx,float gy,float z,bool motor) {
    uint32_t intervalo=amostra?uint32_t(t-medidaEm):0;
    float dt=intervalo<=75?intervalo*.001f:0;
    float n=sqrtf(ax*ax+ay*ay+az*az);
    float delta=amostra?sqrtf(powf(ax-anterior[0],2)+powf(ay-anterior[1],2)+powf(az-anterior[2],2)):0;
    anterior[0]=ax;anterior[1]=ay;anterior[2]=az;
    float r=atan2f(ay,az)*57.29578f,p=atan2f(-ax,sqrtf(ay*ay+az*az))*57.29578f;
    bool primeira=!amostra;
    // Lacuna de amostras não se transforma em rotação integrada fictícia.
    if (amostra && intervalo>75) calibrar();
    amostra=presente=true;erro=false;medidaEm=t;norma=n;energia=delta;
    if(!calibrada) {
      bool quieta=!motor && n>.85f && n<1.15f && delta<.035f
          && fabsf(gx)<5 && fabsf(gy)<5 && fabsf(z)<5;
      if(!quieta) {amostrasCal=0;inicioCal=t;for(float &v:soma)v=0;}
      else {
        if(!amostrasCal) inicioCal=t;
        soma[0]+=gx;soma[1]+=gy;soma[2]+=z;++amostrasCal;
        if(amostrasCal>=100 && uint32_t(t-inicioCal)>=1800) {
          for(int i=0;i<3;++i) bias[i]=soma[i]/amostrasCal;
          calibrada=true;yaw=0;
        }
      }
    }
    float peso=primeira?1:1-expf(-max(.001f,dt)/.12f);
    // Acelerômetro corrige inclinação só quando a gravidade domina.
    if(primeira || (n>.75f && n<1.25f)) {
      roll=primeira?r:remainderf(roll+remainderf(r-roll,360)*peso,360);
      pitch=primeira?p:pitch+remainderf(p-pitch,360)*peso;
    }
    gz=z-bias[2];if(calibrada) yaw+=gz*dt;
    float inclinacao=max(fabsf(r),fabsf(p));
    // Um toque isolado não é sacudir. Exigir energia sustentada por60ms.
    bool candidato=!motor && (fabsf(n-1)>.65f || delta>.55f
        || max(fabsf(gx-bias[0]),max(fabsf(gy-bias[1]),fabsf(gz)))>170);
    if(!candidato) inicioBrusco=0;
    else if(!inicioBrusco) inicioBrusco=t;
    bool brusco=candidato && uint32_t(t-inicioBrusco)>=60;
    if(brusco) movimentoEm=t;
    const char *novo=inclinacao>=40?"TOMBADA":inclinacao>=14?"INCLINADA":
        brusco || (movimentoEm && uint32_t(t-movimentoEm)<600)?"MOVIMENTO_BRUSCO":"ESTAVEL";
    if(strcmp(novo,"ESTAVEL")) estabilidadeEm=t;
    manuseio=novo;
  }
  bool recente(uint32_t t) const {return presente && amostra && !erro && uint32_t(t-medidaEm)<=75;}
  bool bloqueia(uint32_t t) const {
    return !recente(t) || !calibrada || strcmp(manuseio,"ESTAVEL") || uint32_t(t-estabilidadeEm)<700;
  }
};
#if LAYLAY_IMU
EstadoImuCorporal imu;
// Continuidade expressiva sobre a classificação já medida, sem outra decisão motora.
struct EpisodioManuseio {
  const char *fase="TRANQUILA",*anterior="ESTAVEL";
  uint32_t inicio=0,mudouEm=0,ultimoEpisodio=0,sequencia=0;
  unsigned repeticoes=0;
  void atualizar(uint32_t t,const char *m,bool valido) {
    const char *nova="TRANQUILA";
    if(!valido) { anterior="ESTAVEL";inicio=0;repeticoes=0;ultimoEpisodio=0; }
    else {
      bool alterado=strcmp(m,"ESTAVEL")!=0;
      if(alterado && !strcmp(anterior,"ESTAVEL")) {
        repeticoes=ultimoEpisodio && uint32_t(t-ultimoEpisodio)<20000?min(3u,repeticoes+1):1;
        ultimoEpisodio=inicio=t;
      }
      if(!strcmp(m,"TOMBADA") || !strcmp(m,"POSSIVEL_LEVANTAMENTO")) nova="DESORIENTADA";
      else if(!strcmp(m,"MOVIMENTO_BRUSCO")) nova=uint32_t(t-inicio)>700 || repeticoes>1?"RESMUNGO":"SUSTO";
      else if(!strcmp(m,"INCLINADA")) nova=uint32_t(t-inicio)>1200?"DESCONFIADA":"CURIOSA";
      else if(strcmp(anterior,"ESTAVEL")) { inicio=t;nova="RECOMPONDO"; }
      else if(!strcmp(fase,"RECOMPONDO") && uint32_t(t-inicio)<3000) nova="RECOMPONDO";
      if(!alterado && ultimoEpisodio && uint32_t(t-ultimoEpisodio)>=20000) repeticoes=0;
      anterior=m;
    }
    if(strcmp(nova,fase)) {fase=nova;mudouEm=t;++sequencia;}
  }
} episodioManuseio;
uint8_t enderecoImu=0x68;
uint8_t identidadeImu=0;
uint32_t ultimaConsultaImu=0,ultimoSomManuseio=0;
uint32_t sustoManuseioAte=0;
const char *estadoManuseioAnterior="ESTAVEL";
bool bloqueioManuseioAnterior=false;
bool lerRegistrosImu(uint8_t reg,uint8_t *dados,uint8_t tamanho) {
  Wire.beginTransmission(enderecoImu);Wire.write(reg);
  if(Wire.endTransmission(false))return false;
  if(Wire.requestFrom(enderecoImu,tamanho)!=tamanho)return false;
  for(uint8_t i=0;i<tamanho;++i) dados[i]=Wire.read();
  return true;
}
bool gravarRegistroImu(uint8_t reg,uint8_t valor) {
  Wire.beginTransmission(enderecoImu);Wire.write(reg);Wire.write(valor);
  return Wire.endTransmission()==0;
}
void iniciarImuCorporal() {
  // Revalidação não herda calibração/amostra anterior a uma falha elétrica.
  imu=EstadoImuCorporal{};
  episodioManuseio=EpisodioManuseio{};
  sustoManuseioAte=0;
  uint8_t id=0,confirmacao=0;
  imu.presente=lerRegistrosImu(0x75,&id,1) && lerRegistrosImu(0x75,&confirmacao,1)
      && id==confirmacao && (id==0x68 || id==0x98);
  identidadeImu=id;
  if(imu.presente) imu.presente=gravarRegistroImu(0x6B,1)
      && gravarRegistroImu(0x1A,3) && gravarRegistroImu(0x19,9)
      && gravarRegistroImu(0x1B,8) && gravarRegistroImu(0x1C,8)
      && (id!=0x98 || (gravarRegistroImu(0x1D,3) && gravarRegistroImu(0x6C,0)));
  uint8_t escalas[2]={};
  if(imu.presente) imu.presente=lerRegistrosImu(0x1B,escalas,2) && escalas[0]==8 && escalas[1]==8;
}
void atualizarImuCorporal(uint32_t agora) {
  if(!imu.presente || uint32_t(agora-ultimaConsultaImu)<10)return;
  ultimaConsultaImu=agora;
  uint8_t bytes[14];
  if(!lerRegistrosImu(0x3B,bytes,14)) {imu.erro=true;return;}
  auto valor=[&](int n){return int16_t(uint16_t(bytes[n])<<8|bytes[n+1]);};
  imu.incorporar(millis(),valor(0)/8192.f,valor(2)/8192.f,valor(4)/8192.f,
      valor(8)/65.5f,valor(10)/65.5f,valor(12)/65.5f,motorEmUso());
}
const char *estadoImu(uint32_t agora=millis()) {
  if(!imu.presente)return "AUSENTE";
  if(imu.erro)return "ERRO_I2C";
  if(!imu.amostra)return "AGUARDANDO";
  if(!imu.recente(agora))return "EXPIRADA";
  return imu.calibrada?"PRONTA":"CALIBRANDO";
}
const char *manuseioImu(uint32_t agora=millis()) {
  if(!imu.recente(agora) || !imu.calibrada)return "DESCONHECIDO";
#if LAYLAY_SENSORES_DISTANCIA
  // Uma leitura inferior sem retorno sozinha pode ser borda; não prova colo.
  if(imu.movimentoEm && uint32_t(agora-imu.movimentoEm)<2000
      && (!strcmp(estadoDistancia(distancias[1],agora),"INVALIDA")
          || (!strcmp(estadoDistancia(distancias[1],agora),"VALIDA") && distancias[1].mm>130)))
    return "POSSIVEL_LEVANTAMENTO";
#endif
  return imu.manuseio;
}
bool manuseioBloqueiaMotor(uint32_t agora) {
  return imu.bloqueia(agora) || !strcmp(manuseioImu(),"POSSIVEL_LEVANTAMENTO");
}
bool admitirMotorManuseio(uint32_t seq) {
  if(!manuseioBloqueiaMotor(millis()))return true;
  sequenciaMotor=seq;
  responder("HAZARD 1 %s %lu 0 MANUSEIO\n",sessao,(unsigned long)seq);
  return false;
}
void interromperMotorPorManuseio() {
  if(motorEmUso() && conectado && sessao[0])
    responder("HAZARD 1 %s %lu 0 MANUSEIO\n",sessao,(unsigned long)sequenciaMotor);
  pararMotor();
}
float olharManuseio() {
  if(!imu.recente(millis()) || !imu.calibrada)return 0;
  // Um pequeno percurso nos cantos faz parte do susto, com saída amortecida.
  uint32_t agora=millis();
  if(int32_t(sustoManuseioAte-agora)>0) {
    float peso=min(1.f,(sustoManuseioAte-agora)/350.f);
    return 13.f*sinf(agora*.018f)*peso;
  }
  return max(-14.f,min(14.f,imu.roll*.6f));
}
float olharVerticalManuseio() {
  if(!imu.recente(millis()) || !imu.calibrada)return 0;
  uint32_t agora=millis();
  if(int32_t(sustoManuseioAte-agora)>0) return 7.f*sinf(agora*.013f)*min(1.f,(sustoManuseioAte-agora)/350.f);
  return max(-8.f,min(8.f,-imu.pitch*.4f));
}
float pesoOlharManuseio() {
  if(!imu.recente(millis()) || !imu.calibrada)return 0;
  if(int32_t(sustoManuseioAte-millis())>0)return 1;
  return min(1.f,max(fabsf(imu.roll),fabsf(imu.pitch))/12);
}
int expressaoManuseio() {
  if(!imu.recente(millis()) || !imu.calibrada)return 0;
  const char *f=episodioManuseio.fase;
  return !strcmp(f,"DESORIENTADA")?2:!strcmp(f,"RESMUNGO") || !strcmp(f,"DESCONFIADA")?3:
      !strcmp(f,"RECOMPONDO")?4:!strcmp(f,"SUSTO")?1:0;
}
void atualizarReacaoManuseio(uint32_t agora) {
  bool bloqueio=manuseioBloqueiaMotor(agora);
  if(bloqueio && !bloqueioManuseioAnterior) {
    // Cancela o episódio, preservando a concessão: sem recuos no colo.
    pararMotor();
#if LAYLAY_PROTECAO_CORPORAL
    if(reflexoProtecaoAtivo()) terminarProtecao("BLOQUEADA",agora);
#endif
  }
  bloqueioManuseioAnterior=bloqueio;
  const char *m=manuseioImu();
  uint32_t anteriorFase=episodioManuseio.sequencia;
  episodioManuseio.atualizar(agora,m,imu.recente(agora) && imu.calibrada && conectado
      && uint32_t(agora-ultimoPacote)<ttl);
  if(!strcmp(imu.manuseio,"MOVIMENTO_BRUSCO")) sustoManuseioAte=agora+1100;
  if(conectado && uint32_t(agora-ultimoPacote)<ttl && episodioManuseio.sequencia!=anteriorFase
      && expressaoManuseio() && uint32_t(agora-ultimoSomManuseio)>3500
      && !somExpressivoAtivo) {
    tipoSomExpressivo=expressaoManuseio()==3?11:expressaoManuseio()==4?6:9;indiceNotaSom=0;
    ultimoInicioSom=inicioNotaSom=ultimoSomManuseio=agora;
    somExpressivoAtivo=somJaTocou=true;aplicarNotaSom();
  }
  estadoManuseioAnterior=m;
}
#else
void iniciarImuCorporal() {}
void atualizarImuCorporal(uint32_t) {}
void atualizarReacaoManuseio(uint32_t) {}
bool manuseioBloqueiaMotor(uint32_t) {return false;}
bool admitirMotorManuseio(uint32_t) {return true;}
void interromperMotorPorManuseio() {pararMotor();}
float olharManuseio() {return 0;}
float olharVerticalManuseio() {return 0;}
float pesoOlharManuseio() {return 0;}
int expressaoManuseio() {return 0;}
#endif
void processarConsultaImu(const char *entrada) {
  char pacote[64],*campos[3];uint32_t seq;
  if(!separarCampos(entrada,pacote,sizeof(pacote),campos,3) || strcmp(campos[1],"1")
      || !decimalSemSinal(campos[2],seq) || !seq) {responderLinha("ERROR 1 IMU_INVALIDA");return;}
#if LAYLAY_IMU
  // Um receipt é um retrato único. Cruzar 75ms entre argumentos não pode
  // publicar estado EXPIRADA com manuseio ainda ESTAVEL (ou o inverso).
  const uint32_t agora=millis();
  const char *estado=estadoImu(agora);
  responder("IMU 1 %lu 104 %s %lu %u %ld %ld %ld %ld %ld %s %u %s %lu %lu %u\n",(unsigned long)seq,
      estado,imu.amostra?(unsigned long)(agora-imu.medidaEm):4294967295UL,
      imu.calibrada?1:0,lroundf(imu.roll*100),lroundf(imu.pitch*100),lroundf(imu.yaw*100),
      lroundf(imu.gz*100),lroundf(imu.norma*1000),manuseioImu(agora),unsigned(identidadeImu),
      !strcmp(estado,"PRONTA")?episodioManuseio.fase:"DESCONHECIDA",
      (unsigned long)episodioManuseio.sequencia,(unsigned long)(agora-episodioManuseio.mudouEm),
      episodioManuseio.repeticoes);
#else
  responderLinha("ERROR 1 IMU_DESABILITADA");
#endif
}
void processarSondaImu(const char *entrada) {
  char pacote[64],*campos[3];uint32_t seq;
  if(!separarCampos(entrada,pacote,sizeof(pacote),campos,3) || strcmp(campos[1],"1")
      || !decimalSemSinal(campos[2],seq) || !seq) {responderLinha("ERROR 1 IPROBE_INVALIDA");return;}
#if LAYLAY_IMU
  // Somente leitura dos endereços conhecidos; não altera calibração ou lease.
  uint8_t salvo=enderecoImu;
  for(uint8_t e : {uint8_t(0x68),uint8_t(0x69)}) {
    enderecoImu=e;uint8_t id=255;
    bool ok=lerRegistrosImu(0x75,&id,1);
    responder("IPROBE 1 %lu %u %u %u\n",(unsigned long)seq,unsigned(e),ok?1u:0u,unsigned(id));
  }
  enderecoImu=salvo;
#else
  responderLinha("ERROR 1 IMU_DESABILITADA");
#endif
}

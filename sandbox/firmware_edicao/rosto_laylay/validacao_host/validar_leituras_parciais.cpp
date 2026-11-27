#include <cassert>
#include <cstdio>
#define LAYLAY_IMU 1
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#define LAYLAY_LIMITE_MOTOR_TESTE_MS 5000
#include "../rosto_laylay.ino"

void amostrar(uint32_t t, float gz=0) {
  tempoSimulado=t;
  imu.incorporar(t,0,0,1,0,0,gz,motorEmUso());
  for(int i=0;i<2;++i) {
    auto &s=distancias[i];s.presente=s.amostra=true;s.erroI2c=false;
    s.status=0;s.mm=i?100:250;s.medidaEm=t;
  }
}
void iniciar(unsigned seq,unsigned duracao=5000) {
  char linha[128];
  snprintf(linha,sizeof(linha),"FACE 1 01234567 %u 0 1 0 3500",seq);
  processarLinha(linha);
  snprintf(linha,sizeof(linha),"TURN 1 01234567 %u 90 160 %u",seq,duracao);
  Serial.saida.clear();processarLinha(linha);assert(giroMedidoAtivo);
}
void mostrar(const char *caso) {
  printf("CASO %s\n%s",caso,Serial.saida.c_str());
}
int main() {
  Wire.extras[0x29]=Wire.extras[0x68]=true;
  Wire.registrosImu[0x75]=0x98;Wire.registrosImu[0x3F]=0x20;
  setup();for(unsigned t=10;t<2500;t+=10)amostrar(t);
  assert(imu.calibrada && !imu.bloqueia(2490));
  processarLinha("HELLO 1 01234567");
  iniciar(1,500);
  for(unsigned t=2500;t<=3010;t+=10){amostrar(t,30);atualizarMotor(t);}
  assert(Serial.saida.find("TEMPO_LIMITE")!=std::string::npos);mostrar("tempo_limite");
  iniciar(2);
  for(unsigned t=3020;t<=3960;t+=10){amostrar(t);atualizarMotor(t);}
  assert(Serial.saida.find("SEM_ROTACAO")!=std::string::npos);mostrar("zero_medido");
  iniciar(3);amostrar(3970,500);atualizarMotor(3970);
  assert(Serial.saida.find("SATURACAO")!=std::string::npos);mostrar("saturacao");
  amostrar(3980);iniciar(4);
  for(unsigned t=3990;t<=4200;t+=10){amostrar(t,40);atualizarMotor(t);}
  processarLinha("STOP");
  assert(Serial.saida.find("INTERROMPIDO")!=std::string::npos);mostrar("stop_com_imu_valida");
  iniciar(5);amostrar(4300,40);atualizarMotor(4300);
  assert(!imu.calibrada && Serial.saida.find("INTERROMPIDO")!=std::string::npos);
  mostrar("lacuna_de_amostras");
  puts("LEITURAS_HOST_GREEN");
}

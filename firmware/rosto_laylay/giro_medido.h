#pragma once
bool giroMedidoAtivo=false;
float inicioYawGiro=0,alvoGiro=0;
int pwmGiro=0;
uint32_t inicioGiro=0;
void terminarGiroMedido(const char *motivo) {
  if(!giroMedidoAtivo)return;
  giroMedidoAtivo=false;
#if LAYLAY_IMU
  float medido=imu.yaw-inicioYawGiro;
  pararMotor();
  responder("TURNEND 1 %s %lu %s %ld\n",sessao,(unsigned long)sequenciaMotor,
      motivo,lroundf(medido*100));
#endif
}
void cancelarGiroMedido() {terminarGiroMedido("INTERROMPIDO");}
void confirmarPwmGiro() {
  if(giroMedidoAtivo) responder("TURNPWM 1 %s %lu\n",sessao,(unsigned long)sequenciaMotor);
}
bool atualizarGiroMedido(uint32_t agora) {
#if LAYLAY_IMU
  if(!giroMedidoAtivo)return false;
  if(!conectado || uint32_t(agora-ultimoPacote)>=ttl || manuseioBloqueiaMotor(agora)) {
    terminarGiroMedido("IMU_OU_SESSAO");return true;
  }
#if LAYLAY_PROTECAO_CORPORAL
  if(strcmp(riscoProtecao(agora),"NENHUM")) {
    terminarGiroMedido("PROTECAO");return true;
  }
#endif
  float progresso=(imu.yaw-inicioYawGiro)*(alvoGiro>0?1:-1);
  float falta=fabsf(alvoGiro)-progresso;
  if(fabsf(imu.gz)>480) {terminarGiroMedido("SATURACAO");return true;}
  if(falta < -12) {terminarGiroMedido("ULTRAPASSOU");return true;}
  if(progresso < -12) {terminarGiroMedido("SENTIDO_DIVERGENTE");return true;}
  if(falta<=3) {terminarGiroMedido("ALVO");return true;}
  if(uint32_t(agora-inicioGiro)>=duracaoMotor) {terminarGiroMedido("TEMPO_LIMITE");return true;}
  if(uint32_t(agora-inicioGiro)>900 && progresso<2) {terminarGiroMedido("SEM_ROTACAO");return true;}
  int pwm=falta<35?max(90,int(pwmGiro*(.4f+.6f*falta/35))):pwmGiro;
  pwmEsquerdo=alvoGiro>0?-pwm:pwm;pwmDireito=-pwmEsquerdo;
#endif
  return false;
}
void processarGiroMedido(const char *entrada) {
#if LAYLAY_IMU
  char pacote[128],*c[7];uint32_t seq,pwm,tempo,magnitude;int angulo;
  if(!separarCampos(entrada,pacote,sizeof(pacote),c,7) || strcmp(c[1],"1")
      || !sessaoValida(c[2]) || !decimalSemSinal(c[3],seq) || !seq
      || !decimalSemSinal(c[4]+(c[4][0]=='-'?1:0),magnitude) || magnitude<15 || magnitude>360
      || !decimalSemSinal(c[5],pwm) || pwm<90 || pwm>200
      || !decimalSemSinal(c[6],tempo) || tempo<500 || tempo>LAYLAY_LIMITE_MOTOR_TESTE_MS
      ) {responderLinha("ERROR 1 TURN_INVALIDO");return;}
  angulo=c[4][0]=='-'?-int(magnitude):int(magnitude);
  // Mesmo owner/admissão/sequência/lease do MOTOR, sem atalho para proteção.
  if(!imu.recente(millis()) || !imu.calibrada || manuseioBloqueiaMotor(millis())) {
    responderLinha("ERROR 1 TURN_IMU_INDISPONIVEL");return;
  }
  char motor[128];int e=angulo>0?-int(pwm):int(pwm);
  uint32_t seqAntes=sequenciaMotor;bool ocupado=motorEmUso();
  snprintf(motor,sizeof(motor),"MOTOR 1 %s %lu %d %d %lu",c[2],(unsigned long)seq,e,-e,(unsigned long)tempo);
  processarMotor(motor);
  if(seqAntes>=seq || ocupado || sequenciaMotor!=seq || !motorPendente || giroMedidoAtivo)return;
  giroMedidoAtivo=true;inicioYawGiro=imu.yaw;alvoGiro=angulo;pwmGiro=pwm;inicioGiro=millis();
  responder("TURNACK 1 %s %lu %d\n",sessao,(unsigned long)seq,angulo);
#else
  responderLinha("ERROR 1 TURN_DESABILITADO");
#endif
}

#line 1 "C:\\Users\\pbarr\\Downloads\\pasta organizada\\programacao\\PY\\projeto lay\\laylay\\firmware\\rosto_laylay\\validacao_host\\validar_glitch_boca.cpp"
#include <cassert>
#include <cstdio>
#include <filesystem>
#include <set>
#include "../rosto_laylay.ino"

// Perfil recebido pela linha de compilação: o mesmo contrato visual nos dois builds.
void enviar(const char *entrada) {
  Serial.entrada += entrada; Serial.entrada += '\n'; loop();
}

void parados() {
  assert(niveisGpio[PINO_NSLEEP]==LOW && !motorAtivo && !motorPendente);
  for (int pino : PINOS_MOTOR) assert(dutiesPwm[pino]==0);
}

void sessaoNova(uint32_t instante, const char *nonce, uint32_t validade=3500) {
  tempoSimulado=instante; Wire.presente=true; Wire.demoraTransmissao=0; tela.demoraDisplay=0;
  tela.desaparecerAposDisplay=false;
  char pacote[128]; snprintf(pacote,sizeof(pacote),"HELLO 1 %s",nonce); processarLinha(pacote);
  snprintf(pacote,sizeof(pacote),"FACE 1 %s 1 6 2 1 %u",nonce,validade); processarLinha(pacote);
}

void validarGlitch() {
  setup(); tempoSimulado=1000;
  enviar("HELLO 1 01234567");
  Serial.saida.clear(); enviar("GCAPS 1 01234567");
  assert(Serial.saida.find("GCAPS 1 01234567 GLITCH1")!=std::string::npos);
  Serial.saida.clear(); enviar("MCAPS 1 01234567");
  assert(Serial.saida.find(LAYLAY_HABILITAR_MOTORES_BANCADA==1 ? "MOTOR1" : "MOTOR0")!=std::string::npos);
  assert(!conectado); parados();
  processarLinha("GLITCH 1 01234567 1 900"); assert(!glitch && sequenciaGlitch==0);
  sessaoNova(1100,"01234567"); tempoSimulado=1140; loop();
  const uint32_t faceOriginal=ultimoPacote, motorOriginal=inicioMotor;
  Serial.saida.clear(); processarLinha("GLITCH 1 01234567 1 900");
  assert(glitch && ackGlitchPendente && Serial.saida.find("GACK")==std::string::npos);
  assert(ultimoPacote==faceOriginal && inicioMotor==motorOriginal && emocao==6 && nivel==2 && falando);
  tempoSimulado=1180; loop();
  assert(Serial.saida.find("GACK 1 01234567 1 900")!=std::string::npos && !ackGlitchPendente);
  parados();
  uint8_t imagemGlitch[64][128]; memcpy(imagemGlitch,tela.pixels,sizeof(imagemGlitch));
  glitch=false; renderizar(tempoSimulado); glitch=true;
  int alterados=0;
  for (int y=0;y<64;++y) for (int x=0;x<128;++x) alterados+=imagemGlitch[y][x]!=tela.pixels[y][x];
  assert(alterados>10); // Faixas/noise do .ino alteram o raster, não só um log.
  const char *invalidos[] = {
    "GLITCH 1 01234567 0 900", "GLITCH 1 01234567 -1 900", "GLITCH 1 01234567 +2 900",
    "GLITCH 1 01234567 4294967296 900", "GLITCH 1 01234567 2 499", "GLITCH 1 01234567 2 1601",
    "GLITCH 1 01234567 2 -900", "GLITCH 1 01234567 2 +900", "GLITCH 1 01234567 2 9.0",
    "GLITCH 1 01234567 2 4294967296", "GLITCH 1 01234567 2 900 extra", "GLITCH 1 01234567 2",
    "GLITCH 2 01234567 2 900", "GLITCH1 01234567 2 900", "GLITCH 1 012345678 2 900",
    "GLITCH 1 0123456g 2 900", "GLITCH 1 ffffffff 2 900", "GLITCH 1 01234567 1 900",
  };
  for (const char *entrada : invalidos) {
    Serial.saida.clear(); processarLinha(entrada);
    assert(glitch && sequenciaGlitch==1 && inicioGlitch==1140 && ttlGlitch==900);
    assert(Serial.saida.find("GACK")==std::string::npos); parados();
  }
  const char *capsInvalidas[] = {
    "GCAPS 1 ffffffff", "GCAPS 1 012345678", "GCAPS 2 01234567", "GCAPS1 01234567",
    "GCAPS 1 01234567 extra", "GCAPS 1", "MCAPS 1 ffffffff", "MCAPS 1 01234567 extra",
  };
  for (const char *entrada : capsInvalidas) {
    Serial.saida.clear(); processarLinha(entrada);
    assert(Serial.saida.find("GLITCH1")==std::string::npos && Serial.saida.find("MOTOR1")==std::string::npos);
    parados();
  }
  tempoSimulado=2040; loop(); assert(!glitch && conectado && ultimoPacote==faceOriginal);
  processarLinha("GLITCH 1 01234567 1 900"); assert(!glitch); // Replay após TTL.
  processarLinha("HELLO 1 01234567"); assert(!glitch && sequenciaGlitch==1);
  processarLinha("FACE 1 01234567 1 0 1 0 3500");
  processarLinha("GLITCH 1 01234567 1 900"); assert(!glitch); // HELLO repetido conserva sequência.

  sessaoNova(3000,"abc01234"); processarLinha("GLITCH 1 abc01234 1 900");
  assert(glitch); Wire.presente=false; Serial.saida.clear();
  processarLinha("GLITCH 1 abc01234 2 900");
  assert(!glitch && !conectado && !sessao[0] && !ackGlitchPendente);
  assert(Serial.saida.find("GACK")==std::string::npos); parados(); Wire.presente=true;

  sessaoNova(10000,"12345678",500);
  tempoSimulado=10490; Wire.demoraTransmissao=20; Serial.saida.clear();
  processarLinha("GLITCH 1 12345678 1 500");
  assert(!glitch && sequenciaGlitch==0 && Serial.saida.find("GACK")==std::string::npos);
  Wire.demoraTransmissao=0;
  sessaoNova(11000,"23456789"); tempoSimulado=11040; loop();
  processarLinha("GLITCH 1 23456789 1 500");
  tempoSimulado=11490; Wire.demoraTransmissao=30; Serial.saida.clear(); loop();
  assert(!glitch && Serial.saida.find("GACK")==std::string::npos); // Probe consumiu TTL do efeito.
  Wire.demoraTransmissao=0;
  sessaoNova(12000,"3456789a"); tempoSimulado=12040; loop();
  processarLinha("GLITCH 1 3456789a 1 500");
  tempoSimulado=12080; tela.demoraDisplay=510; Serial.saida.clear(); loop();
  assert(!glitch && Serial.saida.find("GACK")==std::string::npos); // Frame consumiu TTL do efeito.
  tela.demoraDisplay=0;
  sessaoNova(13000,"456789ab",500);
  processarLinha("GLITCH 1 456789ab 1 1600");
  tempoSimulado=13040; tela.demoraDisplay=510; Serial.saida.clear(); loop();
  assert(!conectado && !glitch && !sessao[0] && !ackGlitchPendente);
  assert(Serial.saida.find("ACK 1")==std::string::npos); // FACE também não confirma frame vencido.
  tela.demoraDisplay=0;
  sessaoNova(14000,"56789abc"); processarLinha("GLITCH 1 56789abc 1 900");
  tempoSimulado=14040; Wire.presente=false; Serial.saida.clear(); loop();
  assert(!conectado && !glitch && !ackGlitchPendente && !sessao[0]);
  assert(Serial.saida.find("GACK")==std::string::npos); parados(); Wire.presente=true;
  sessaoNova(14500,"89abcd12"); processarLinha("GLITCH 1 89abcd12 1 900");
  tempoSimulado=14540; tela.desaparecerAposDisplay=true; Serial.saida.clear(); loop();
  assert(!glitch && !conectado && !sessao[0] && Serial.saida.find("GACK")==std::string::npos);
  parados(); tela.desaparecerAposDisplay=false; Wire.presente=true; // Perda no envio do frame, não antes dele.
  sessaoNova(15000,"6789abcd",500); processarLinha("GLITCH 1 6789abcd 1 1600");
  tempoSimulado=15500; loop(); assert(!glitch && !conectado && estavaDormindo);
  sessaoNova(0xfffffff0,"789abcde"); processarLinha("GLITCH 1 789abcde 1 500");
  tempoSimulado=100; loop(); assert(glitch && conectado);
  tempoSimulado=484; loop(); assert(!glitch && conectado); // TTL atravessa wrap de millis.
  processarLinha("GLITCH 1 789abcde 2 900"); processarLinha("DEMO_GLITCH");
  assert(!glitch && !ackGlitchPendente && demoGlitch && demonstracao && !sessao[0]); parados();
  processarLinha("DEMO_FALA"); assert(demoFala && !demoGlitch); parados();
  processarLinha("HELLO 1 89abcdef"); assert(!demoFala && !demoGlitch && !demonstracao && !glitch);
  printf("GLITCH_HOST_OK: MCAPS/GCAPS, parser, replay, GACK pos-frame, TTL, I2C/display, wrap e demo; %d pixels\n",alterados);
}

void validarParada() {
  if (LAYLAY_HABILITAR_MOTORES_BANCADA==1) {
    sessaoNova(19000,"bcdef034"); processarLinha("MOTOR 1 bcdef034 1 180 -180 200");
    tempoSimulado=19002; atualizarMotor(millis()); assert(motorAtivo);
    const uint32_t inicioOriginal=inicioMotor;
    processarLinha("GLITCH 1 bcdef034 1 900");
    tempoSimulado=19150; processarLinha("FACE 1 bcdef034 2 3 2 0 3500");
    assert(glitch && motorAtivo && inicioMotor==inicioOriginal && duracaoMotor==200);
    tempoSimulado=19200; loop(); parados(); assert(glitch && conectado);
  }
  sessaoNova(20000,"abcdef01"); Serial.saida.clear();
  processarLinha("STOP 1 abcdef01 1"); parados();
  assert(Serial.saida.find("SACK 1 abcdef01 1")!=std::string::npos && sequenciaParada==1);
  const char *invalidos[] = {
    "STOP 1 abcdef01 1", "STOP 1 abcdef01 0", "STOP 1 ffffffff 2", "STOP 1 abcdef01 -2",
    "STOP 1 abcdef01 +2", "STOP 1 abcdef01 4294967296", "STOP 1 abcdef01 2 extra",
    "STOP 2 abcdef01 2", "STOP1 abcdef01 2", "STOP 1 abcdef012 2", "STOP 1 abcdef01",
  };
  uint32_t seqMotor=0;
  for (const char *entrada : invalidos) {
    if (LAYLAY_HABILITAR_MOTORES_BANCADA==1) {
      char pacote[128]; snprintf(pacote,sizeof(pacote),"MOTOR 1 abcdef01 %u 255 255 500",++seqMotor);
      processarLinha(pacote); tempoSimulado+=2; atualizarMotor(millis()); assert(motorAtivo);
    }
    Serial.saida.clear(); processarLinha(entrada); parados();
    assert(sequenciaParada==1 && Serial.saida.find("SACK")==std::string::npos);
  }
  processarLinha("HELLO 1 abcdef01"); assert(sequenciaParada==1);
  Serial.saida.clear(); processarLinha("STOP 1 abcdef01 1"); parados();
  assert(Serial.saida.find("SACK")==std::string::npos);
  processarLinha("STOP 1 abcdef01 2"); parados();
  assert(Serial.saida.find("SACK 1 abcdef01 2")!=std::string::npos);
  processarLinha("STOP"); parados(); assert(Serial.saida.find("STOPPED 1")!=std::string::npos);
  sessaoNova(21000,"bcdef012",500); tempoSimulado=21500; loop();
  Serial.saida.clear(); processarLinha("STOP 1 bcdef012 1"); parados();
  assert(Serial.saida.find("SACK")==std::string::npos); // Corta com sessão expirada, sem receipt correlacionado falso.
  puts("STOP_HOST_OK: SACK correlacionado pos-corte, parser, replay, sessao, legado e corte fail-safe");
}

void validarBoca() {
  demonstracao=false; conectado=true; falando=false; emocao=1; nivel=2; atividade=false; glitch=false;
  repouso=0; sorrisoBoca=1; larguraBoca=13; aberturaBoca=0; larguraFala=1;
  tela.clearDisplay(); desenharBoca(50);
  assert(tela.getPixel(64,55) && !tela.getPixel(64,50)); // Curva emocional fechada.
  aberturaBoca=4.5f; tela.clearDisplay(); desenharBoca(50);
  assert(tela.getPixel(64,46) && tela.getPixel(64,55) && !tela.getPixel(64,50)); // Oval aberto com interior livre.
  proximaPiscada=proximoOlhar=100000000; inicioPiscada=0; olharAlvo=0;
  float menorAbertura=100, maiorAbertura=0, menorLargura=100, maiorLargura=0;
  float aberturaAnterior=aberturaBoca, larguraAnterior=larguraFala, maiorPasso=0;
  uint32_t instante=30000;
  for(int frame=0;frame<180;++frame) {
    falando=true; instante+=33; renderizar(instante);
    if(frame>40) {
      menorAbertura=min(menorAbertura,aberturaBoca); maiorAbertura=max(maiorAbertura,aberturaBoca);
      menorLargura=min(menorLargura,larguraFala); maiorLargura=max(maiorLargura,larguraFala);
      maiorPasso=max(maiorPasso,fabsf(aberturaBoca-aberturaAnterior));
      assert(fabsf(larguraFala-larguraAnterior)<0.08f);
    }
    aberturaAnterior=aberturaBoca; larguraAnterior=larguraFala;
  }
  assert(menorAbertura<0.4f && maiorAbertura>3 && maiorAbertura<4.5f);
  assert(maiorLargura-menorLargura>0.1f && maiorPasso<1.9f);
  uint8_t antes[64][128]; memcpy(antes,tela.pixels,sizeof(antes));
  falando=false; instante+=33; renderizar(instante);
  int salto=0; for(int y=43;y<64;++y) for(int x=44;x<84;++x) salto+=antes[y][x]!=tela.pixels[y][x];
  assert(salto<100); // Parar fala também interpola, sem teleporte de boca.
  for(int frame=0;frame<30;++frame) { instante+=33; renderizar(instante); }
  assert(aberturaBoca<0.03f && larguraFala>0.99f);
  printf("BOCA_HOST_OK: pausa/variacao, abertura %.2f..%.2f, largura %.2f..%.2f, maior passo %.2f, parada %d pixels\n",
         menorAbertura,maiorAbertura,menorLargura,maiorLargura,maiorPasso,salto);
}

void exportar(const std::string &pasta) {
  std::filesystem::create_directories(pasta);
  for(int emo=0;emo<9;++emo) {
    demonstracao=false; conectado=true; atividade=false; glitch=false; emocao=emo; nivel=2; falando=false;
    proximaPiscada=proximoOlhar=100000000; inicioPiscada=0; olharAlvo=0; painelHack=0;
    uint32_t instante=1000000+emo*10000;
    for(int frame=0;frame<90;++frame) { instante+=33; renderizar(instante); }
    for(int frame=0;frame<120;++frame) {
      falando=frame>=15 && frame<95; instante+=33; renderizar(instante); parados();
      char nome[80]; snprintf(nome,sizeof(nome),"/fala_%d_%03d.pgm",emo,frame); tela.salvar(pasta+nome);
    }
  }
  sessaoNova(2000000,"cdef0123"); falando=false; emocao=0; painelHack=0;
  uint32_t seqFace=1; std::set<std::string> distintos;
  for(int frame=0;frame<120;++frame) {
    tempoSimulado=2000000+frame*33;
    if(frame%20==0) {
      char pacote[128]; snprintf(pacote,sizeof(pacote),"FACE 1 cdef0123 %u 0 1 0 3500",++seqFace); processarLinha(pacote);
    }
    if(frame==30) processarLinha("GLITCH 1 cdef0123 1 900");
    loop(); parados(); distintos.insert(std::string(reinterpret_cast<char*>(tela.pixels),sizeof(tela.pixels)));
    char nome[80]; snprintf(nome,sizeof(nome),"/glitch_%03d.pgm",frame); tela.salvar(pasta+nome);
  }
  assert(distintos.size()>35 && !glitch && conectado);
  printf("PREVIEW_RASTER_OK: 9 bocas, %zu quadros glitch distintos, motores parados\n",distintos.size());
}

int main(int argc,char **argv) {
  validarGlitch(); validarParada(); validarBoca();
  if(argc>1) exportar(argv[1]);
  puts("FIRMWARE_GLITCH_BOCA_HOST_OK");
}

#pragma once
// Revalidar um periférico não concede sessão, vigia ou replay de movimento.
uint32_t inicioFalhaPerifericos=0, ultimaRecuperacaoPerifericos=0;
bool falhaPerifericosEmCurso=false, recuperacaoPerifericosTentada=false;
void atualizarRecuperacaoPerifericos(uint32_t agora) {
  bool falhaImu=false, falhaDistancia=false;
#if LAYLAY_IMU
  falhaImu=!imu.presente || imu.erro || !imu.amostra || uint32_t(agora-imu.medidaEm)>500;
#endif
#if LAYLAY_SENSORES_DISTANCIA
  for (auto &s:distancias)
    falhaDistancia|=!s.presente || s.erroI2c || !s.amostra || uint32_t(agora-s.medidaEm)>500;
#endif
  bool falhaTela=!telaInicializada || falhaFrameI2c;
  if (!falhaImu && !falhaDistancia && !falhaTela) {falhaPerifericosEmCurso=false;return;}
  if (!falhaPerifericosEmCurso) {falhaPerifericosEmCurso=true;inicioFalhaPerifericos=agora;}
  if (uint32_t(agora-inicioFalhaPerifericos)<500
      || (recuperacaoPerifericosTentada && uint32_t(agora-ultimaRecuperacaoPerifericos)<5000)) return;
  ultimaRecuperacaoPerifericos=agora;recuperacaoPerifericosTentada=true;
  // Corta antes das inicializações I2C, que podem conter esperas. O PC deve
  // negociar nova sessão e conferir amostras novas; o gesto antigo terminou.
  invalidarSessaoPor("I2C");
#if LAYLAY_SENSORES_DISTANCIA
  if (falhaDistancia) iniciarSensoresDistancia();
#endif
#if LAYLAY_IMU
  if (falhaImu) iniciarImuCorporal();
#endif
  if (falhaTela) {
    endereco=0;telaInicializada=false;
    for(uint8_t e:{uint8_t(0x3C),uint8_t(0x3D)}) {
      Wire.beginTransmission(e);
      if (!Wire.endTransmission()) {endereco=e;break;}
    }
    if(endereco) telaInicializada=tela.begin(SSD1306_SWITCHCAPVCC,endereco,true,false);
    if(telaInicializada) tela.setTextColor(SSD1306_WHITE);
    falhaFrameI2c=!telaInicializada;
  }
  falhaPerifericosEmCurso=false;
}

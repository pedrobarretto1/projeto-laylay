// Saída finita pelo GPIO6. Recepção não comprova audição nem efeito da ação.
#pragma once
struct NotaCorpo { uint16_t hz, ms; };
constexpr NotaCorpo SONS_CORPO[9][5] = {
  {{1400,70},{0,35},{1850,90},{0,0},{0,0}}, // acordar: pi-piu
  {{1450,60},{0,35},{1800,60},{0,30},{2200,90}}, // sucesso
  {{950,90},{0,45},{700,110},{0,0},{0,0}}, // falha: bu-bum
  {{1800,65},{0,35},{2300,85},{0,0},{0,0}}, // alegre
  {{1150,85},{0,35},{850,110},{0,0},{0,0}}, // triste
  {{850,55},{0,35},{850,55},{0,30},{1100,75}}, // brava/irritada
  {{1700,45},{0,70},{2000,60},{0,0},{0,0}}, // vergonha
  {{2200,60},{0,25},{2600,75},{0,0},{0,0}}, // surpresa
  {{1550,80},{0,0},{0,0},{0,0},{0,0}}, // envio: pi neutro, sem comemoração
};
bool somExpressivoAtivo = false, somPwmPronto = false, somJaTocou = false;
uint8_t tipoSomExpressivo = 0, indiceNotaSom = 0;
uint32_t inicioNotaSom = 0, ultimoInicioSom = 0, sequenciaSom = 0;
char sessaoSequenciaSom[9] = "";

NotaCorpo notaSomAtual() {
  NotaCorpo nota = SONS_CORPO[tipoSomExpressivo][indiceNotaSom];
  // Mesma assinatura e volume; pequenas inflexões em ocorrências diferentes.
  // Boot/sucesso/falha mantêm a melodia reconhecível que o usuário validou.
  if (tipoSomExpressivo >= 3 && tipoSomExpressivo <= 7 && nota.hz) {
    const uint16_t afinacao[] = {100, 106, 95};
    nota.hz = uint16_t(uint32_t(nota.hz) * afinacao[(sequenciaSom - 1) % 3] / 100);
  }
  return nota;
}

void pararSomExpressivo() {
  if (somPwmPronto) { ledcWrite(PINO_SOM, 0); ledcDetach(PINO_SOM); }
  somPwmPronto = somExpressivoAtivo = false;
  digitalWrite(PINO_SOM, LOW); pinMode(PINO_SOM, OUTPUT);
}

bool aplicarNotaSom() {
  if (somPwmPronto) { ledcWrite(PINO_SOM, 0); ledcDetach(PINO_SOM); }
  somPwmPronto = false;
  digitalWrite(PINO_SOM, LOW); pinMode(PINO_SOM, OUTPUT);
  auto nota = notaSomAtual();
  if (!nota.hz) return true;
  // Frequências diferentes dos motores (1kHz). Nunca alterar o timer deles.
  somPwmPronto = ledcAttachChannel(PINO_SOM, nota.hz, 8, 4);
  if (!somPwmPronto || !ledcWrite(PINO_SOM, 128)) {
    pararSomExpressivo(); return false;
  }
  return true;
}

void atualizarSomExpressivo(uint32_t agora) {
  if (!somExpressivoAtivo) return;
  // Duração absoluta finita mesmo se o loop atrasar: não enfileirar notas.
  if (uint32_t(agora - ultimoInicioSom) >= 450) { pararSomExpressivo(); return; }
  if (uint32_t(agora - inicioNotaSom) < SONS_CORPO[tipoSomExpressivo][indiceNotaSom].ms) return;
  ++indiceNotaSom;
  if (indiceNotaSom >= 5 || !SONS_CORPO[tipoSomExpressivo][indiceNotaSom].ms) {
    pararSomExpressivo(); return;
  }
  inicioNotaSom = agora;
  if (!aplicarNotaSom()) responderLinha("ERROR 1 SOM_PWM");
}

void processarSomExpressivo(const char *entrada) {
  char pacote[128], *campos[5]; uint32_t seq = 0, tipo = 0;
  if (!separarCampos(entrada, pacote, sizeof(pacote), campos, 5)
      || strcmp(campos[0], "SOUND") || strcmp(campos[1], "1")
      || !sessao[0] || strcmp(campos[2], sessao)
      || !decimalSemSinal(campos[3], seq) || !seq
      || !decimalSemSinal(campos[4], tipo) || tipo > 8
      || !conectado || uint32_t(millis() - ultimoPacote) >= ttl) {
    responderLinha("ERROR 1 SOM_INVALIDO"); return;
  }
  if (strcmp(sessaoSequenciaSom, sessao)) {
    strcpy(sessaoSequenciaSom, sessao); sequenciaSom = 0;
  }
  if (seq <= sequenciaSom) { responderLinha("ERROR 1 SOM_REPLAY"); return; }
  sequenciaSom = seq; // Mesmo uma rejeição não permite repetir a ocorrência.
  uint32_t agora = millis();
  if (somExpressivoAtivo || (somJaTocou && uint32_t(agora - ultimoInicioSom) < 1500)) {
    responderLinha("ERROR 1 SOM_OCUPADO"); return;
  }
  tipoSomExpressivo = tipo; indiceNotaSom = 0;
  ultimoInicioSom = inicioNotaSom = agora;
  somExpressivoAtivo = somJaTocou = true;
  if (!aplicarNotaSom()) { responderLinha("ERROR 1 SOM_PWM"); return; }
  responder("SOUNDACK 1 %s %lu %lu\n", sessao, (unsigned long)seq, (unsigned long)tipo);
}

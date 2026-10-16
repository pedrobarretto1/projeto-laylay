#pragma once
// Reflexo finito do executor. Medir não concede uma sessão nem inicia passeio.
#ifndef LAYLAY_PROTECAO_CORPORAL
#define LAYLAY_PROTECAO_CORPORAL 0
#endif
#if LAYLAY_PROTECAO_CORPORAL && !LAYLAY_SENSORES_DISTANCIA
#error "Protecao exige os dois sensores"
#endif
#if LAYLAY_PROTECAO_CORPORAL
constexpr uint16_t LIMITE_BORDA_MM = 130, LIMITE_OBSTACULO_MM = 100;
uint32_t incidenteProtecao = 0, motorOrigemProtecao = 0, inicioProtecao = 0;
uint32_t inicioFaseProtecao = 0, medoAteProtecao = 0, ultimaAmostraProtecao = 0;
uint8_t amostrasSegurasProtecao = 0;
bool travaProtecao = false;
const char *causaProtecao = "NENHUM", *faseProtecao = "PRONTA";
bool reflexoProtecaoAtivo() {
  return !strcmp(faseProtecao, "RECUANDO") || !strcmp(faseProtecao, "PAUSA")
      || !strcmp(faseProtecao, "GIRANDO") || !strcmp(faseProtecao, "VERIFICANDO")
      || !strcmp(faseProtecao, "SEGUINDO");
}
const char *riscoProtecao(uint32_t agora) {
  const char *b = estadoDistancia(distancias[1], agora);
  if (distancias[1].amostra && uint32_t(agora - distancias[1].medidaEm) > 75) return "FALHA_BORDA";
  if (!strcmp(b, "INVALIDA")) return "BORDA_SEM_RETORNO";
  if (strcmp(b, "VALIDA")) return "FALHA_BORDA";
  if (distancias[1].mm > LIMITE_BORDA_MM) return "BORDA";
  const char *f = estadoDistancia(distancias[0], agora);
  if (distancias[0].amostra && uint32_t(agora - distancias[0].medidaEm) > 150) return "FALHA_FRENTE";
  // RangeStatus inválido recente é desconhecido, não uma parede fictícia.
  // Sensor ausente, barramento com erro e dados expirados são falhas distintas.
  if (strcmp(f, "VALIDA") && strcmp(f, "INVALIDA")) return "FALHA_FRENTE";
  if (!strcmp(f, "VALIDA") && distancias[0].mm <= LIMITE_OBSTACULO_MM) return "OBSTACULO";
  return "NENHUM";
}
void faseNovaProtecao(const char *fase, uint32_t agora) {
  pararMotor(); faseProtecao = fase; inicioFaseProtecao = agora;
}
void terminarProtecao(const char *fase, uint32_t agora) {
  faseNovaProtecao(fase, agora); medoAteProtecao = agora + 2200;
}
void cancelarProtecaoCorporal() {
  if (reflexoProtecaoAtivo()) terminarProtecao("CANCELADA", millis());
}
bool medoProtecaoCorporal(uint32_t agora) {
  return reflexoProtecaoAtivo() || (medoAteProtecao && int32_t(medoAteProtecao - agora) > 0);
}
bool aplicarReflexoProtecao(int e, int d, uint32_t agora) {
  if (!motorPendente && !motorAtivo) {
    // Cada troca de sentido passa por ponte cortada e wake de pelo menos 1ms.
    pararMotor(); digitalWrite(PINO_NSLEEP, HIGH);
    inicioWakeMicros = micros(); motorPendente = true;
  }
  if (uint32_t(micros() - inicioWakeMicros) < 1000) return true;
  int duties[4] = {max(0,e), max(0,-e), max(0,d), max(0,-d)};
  for (int i = 0; i < 4; ++i) if (!ledcWrite(PINOS_MOTOR[i], duties[i])) {
    motoresProntos = false; terminarProtecao("FALHA_PWM", agora); return false;
  }
  pwmEsquerdo = e; pwmDireito = d; motorPendente = false; motorAtivo = true;
  return true;
}
void iniciarProtecao(const char *causa, uint32_t seq, uint32_t agora) {
  pararMotor(); sequenciaMotor = seq; motorOrigemProtecao = seq;
  ++incidenteProtecao; causaProtecao = causa; inicioProtecao = agora;
  travaProtecao = true; amostrasSegurasProtecao = 0;
  medoAteProtecao = agora + 3500;
  // Uma falha elétrica não é autorização para uma manobra cega.
  faseNovaProtecao(!strncmp(causa, "FALHA", 5) ? "BLOQUEADA" : "RECUANDO", agora);
  responder("HAZARD 1 %s %lu %lu %s\n", sessao, (unsigned long)seq,
      (unsigned long)incidenteProtecao, causa);
  // Alarme curto próprio; não promove a ação interrompida a sucesso.
  pararSomExpressivo(); tipoSomExpressivo = 7; indiceNotaSom = 0;
  ultimoInicioSom = inicioNotaSom = agora; somExpressivoAtivo = somJaTocou = true;
  aplicarNotaSom();
}
bool contarSeguraProtecao(uint32_t agora, bool histerese) {
  const char *risco = riscoProtecao(agora);
  bool segura = !strcmp(risco, "NENHUM")
      && (!histerese || distancias[1].mm <= 120)
      && (strcmp(estadoDistancia(distancias[0], agora), "VALIDA") || distancias[0].mm > (histerese ? 120 : 100));
  if (!segura) { amostrasSegurasProtecao = 0; return false; }
  if (ultimaAmostraProtecao != distancias[1].medidaEm) {
    ultimaAmostraProtecao = distancias[1].medidaEm;
    if (amostrasSegurasProtecao < 3) ++amostrasSegurasProtecao;
  }
  return amostrasSegurasProtecao >= 3;
}
bool admitirMovimentoProtegido(uint32_t seq) {
  const char *risco = riscoProtecao(millis());
  if (reflexoProtecaoAtivo()) return false;
  if (!strcmp(risco, "NENHUM") && !travaProtecao) return true;
  if (!travaProtecao) iniciarProtecao(risco, seq, millis());
  else {
    sequenciaMotor = seq;
    responder("HAZARD 1 %s %lu %lu %s\n", sessao, (unsigned long)seq,
      (unsigned long)incidenteProtecao, strcmp(risco, "NENHUM") ? risco : "AGUARDANDO_ESTABILIDADE");
  }
  return false;
}
bool atualizarProtecaoCorporal(uint32_t agora) {
  if (!reflexoProtecaoAtivo()) {
    if (travaProtecao && contarSeguraProtecao(agora, true)) {
      travaProtecao = false; faseProtecao = "PRONTA";
    }
    if (motorEmUso() && conectado && uint32_t(agora - ultimoPacote) < ttl
        && uint32_t(agora - inicioMotor) < duracaoMotor) {
      const char *risco = riscoProtecao(agora);
      if (strcmp(risco, "NENHUM")) { iniciarProtecao(risco, sequenciaMotor, agora); return true; }
    }
    return false;
  }
  if (!conectado || !sessao[0] || uint32_t(agora - ultimoPacote) >= ttl
      || uint32_t(agora - inicioProtecao) >= 3000 || !motoresProntos || !telaInicializada || !telaPresente()) {
    terminarProtecao("CANCELADA", millis()); return true;
  }
  agora = millis();
  if (uint32_t(agora - ultimoPacote) >= ttl || uint32_t(agora - inicioProtecao) >= 3000) {
    terminarProtecao("CANCELADA", agora); return true;
  }
  // Falha do barramento durante uma manobra também corta a ponte.
  const char *f = estadoDistancia(distancias[0], agora), *b = estadoDistancia(distancias[1], agora);
  if ((strcmp(f,"VALIDA") && strcmp(f,"INVALIDA")) || (strcmp(b,"VALIDA") && strcmp(b,"INVALIDA"))
      || uint32_t(agora - distancias[1].medidaEm) > 75 || uint32_t(agora - distancias[0].medidaEm) > 150) {
    terminarProtecao("BLOQUEADA", agora); return true;
  }
  uint32_t idade = agora - inicioFaseProtecao;
  if (!strcmp(faseProtecao,"RECUANDO")) {
    if (idade >= 250) faseNovaProtecao("PAUSA", agora);
    else aplicarReflexoProtecao(-120,-120,agora);
  } else if (!strcmp(faseProtecao,"PAUSA")) {
    if (idade >= 100) faseNovaProtecao("GIRANDO", agora);
  } else if (!strcmp(faseProtecao,"GIRANDO")) {
    // Estimativa por tempo; não afirma 180 graus nem posição conhecida.
    if (idade >= 900) {
      faseNovaProtecao("VERIFICANDO", agora); amostrasSegurasProtecao = 0;
      ultimaAmostraProtecao = distancias[1].medidaEm;
    } else aplicarReflexoProtecao(140,-140,agora);
  } else if (!strcmp(faseProtecao,"VERIFICANDO")) {
    if (contarSeguraProtecao(agora, false)) faseNovaProtecao("SEGUINDO", agora);
    else if (idade >= 500) terminarProtecao("BLOQUEADA", agora);
  } else if (!strcmp(faseProtecao,"SEGUINDO")) {
    if (strcmp(riscoProtecao(agora),"NENHUM")) terminarProtecao("BLOQUEADA",agora);
    else if (idade >= 400) terminarProtecao("CONCLUIDA",agora);
    else aplicarReflexoProtecao(120,120,agora);
  }
  return true;
}
#else
bool atualizarProtecaoCorporal(uint32_t) { return false; }
bool admitirMovimentoProtegido(uint32_t) { return true; }
void cancelarProtecaoCorporal() {}
bool medoProtecaoCorporal(uint32_t) { return false; }
#endif
void processarConsultaProtecao(const char *entrada) {
  uint32_t seq; char pacote[80], *campos[3];
  if (!separarCampos(entrada,pacote,sizeof(pacote),campos,3)
      || strcmp(campos[1],"1") || !decimalSemSinal(campos[2],seq) || !seq) {
    responderLinha("ERROR 1 GUARD_INVALIDA"); return;
  }
#if LAYLAY_PROTECAO_CORPORAL
  responder("GUARD 1 %lu %s %lu %lu %s %s 130 100\n", (unsigned long)seq,
    sessao[0] ? sessao : "SEMSESS", (unsigned long)incidenteProtecao, (unsigned long)motorOrigemProtecao,
    riscoProtecao(millis()), faseProtecao);
#else
  responderLinha("ERROR 1 GUARD_DESABILITADA");
#endif
}

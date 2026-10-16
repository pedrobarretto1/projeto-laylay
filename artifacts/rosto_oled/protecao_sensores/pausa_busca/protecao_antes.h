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
bool vigiaProtecao = false, origemVigiaProtecao = false;
bool novaConcessaoVigiaPendente = true;
uint32_t sequenciaVigiaProtecao = 0, ultimoVigiaProtecao = 0, ttlVigiaProtecao = 1200;
char sessaoVigiaProtecao[9] = "";
uint32_t inicioAlertaProtecao = 0, ultimoSomAlertaProtecao = 0, ultimaFrenteProtecao = 0;
int classeAlertaProtecao = 0, reacaoAlertaProtecao = 0;
uint8_t tentativasBuscaProtecao = 0;
uint8_t recuosMedrososProtecao = 0;
uint8_t amostrasTrocaRiscoProtecao = 0;
uint32_t ultimaTrocaRiscoProtecao = 0;
const char *causaProtecao = "NENHUM", *faseProtecao = "PRONTA";
bool reflexoProtecaoAtivo() {
  return !strcmp(faseProtecao, "RECUANDO") || !strcmp(faseProtecao, "PAUSA")
      || !strcmp(faseProtecao, "GIRANDO") || !strcmp(faseProtecao, "VERIFICANDO")
      || !strcmp(faseProtecao, "BUSCANDO") || !strcmp(faseProtecao, "CONFERINDO")
      || !strcmp(faseProtecao, "RECUO_MEDROSO") || !strcmp(faseProtecao, "ESPERA_MEDROSA")
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
  vigiaProtecao = false;
  if (reflexoProtecaoAtivo() || !strcmp(faseProtecao,"ESPERA_BUSCA")) terminarProtecao("CANCELADA", millis());
}
int expressaoProtecaoCorporal(uint32_t agora) {
  if (!conectado || uint32_t(agora - ultimoPacote) >= ttl) return 0;
  return reacaoAlertaProtecao;
}
bool medoProtecaoCorporal(uint32_t agora) {
  int e = expressaoProtecaoCorporal(agora);
  return e == 1 || e == 2;
}
void sinalAlertaProtecao(uint32_t agora, int tipo) {
  if (somExpressivoAtivo || (somJaTocou && uint32_t(agora-ultimoInicioSom)<1500)) return;
  tipoSomExpressivo = tipo; indiceNotaSom = 0;
  ++ocorrenciaSomAlerta;
  ultimoInicioSom = inicioNotaSom = ultimoSomAlertaProtecao = agora;
  somExpressivoAtivo = somJaTocou = true; aplicarNotaSom();
}
void atualizarAlertaProtecao(uint32_t agora) {
  if (!conectado || uint32_t(agora - ultimoPacote) >= ttl) {
    classeAlertaProtecao = reacaoAlertaProtecao = 0; return;
  }
  const char *risco = riscoProtecao(agora);
  int classe = !strncmp(risco,"BORDA",5) ? 1 : !strcmp(risco,"OBSTACULO") ? 3
      : !strncmp(risco,"FALHA",5) ? 4 : 0;
  bool nova = classe != classeAlertaProtecao;
  if (nova) { classeAlertaProtecao = classe; inicioAlertaProtecao = agora; }
  reacaoAlertaProtecao = classe == 1 && (uint32_t(agora-inicioAlertaProtecao)>=900
      || !strcmp(faseProtecao,"BLOQUEADA")) ? 2 : classe;
  if (!classe && reflexoProtecaoAtivo()) reacaoAlertaProtecao = !strcmp(causaProtecao,"OBSTACULO") ? 3 : 1;
  // Expressão não concede tração. Um bip inicial e depois respiros de8s.
  if (!motorEmUso() && !reflexoProtecaoAtivo() && classe
      && (nova || uint32_t(agora-ultimoSomAlertaProtecao)>=8000))
    sinalAlertaProtecao(agora,classe==3 ? 11 : reacaoAlertaProtecao==2 ? 10 : 9);
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
  tentativasBuscaProtecao = 0;
  recuosMedrososProtecao = 0;
  amostrasTrocaRiscoProtecao = 0;
  origemVigiaProtecao = seq == 0;
  travaProtecao = true; amostrasSegurasProtecao = 0;
  medoAteProtecao = agora + 3500;
  // Uma falha elétrica não é autorização para uma manobra cega.
  faseNovaProtecao(!strncmp(causa, "FALHA", 5) ? "BLOQUEADA" : "RECUANDO", agora);
  responder("HAZARD 1 %s %lu %lu %s\n", sessao, (unsigned long)seq,
      (unsigned long)incidenteProtecao, causa);
  // Alarme após o corte; borda assusta, parede irrita.
  atualizarAlertaProtecao(agora);
  sinalAlertaProtecao(agora,!strcmp(causa,"OBSTACULO") ? 11 : 9);
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
  atualizarAlertaProtecao(agora);
  if (vigiaProtecao && uint32_t(agora-ultimoVigiaProtecao)>=ttlVigiaProtecao) vigiaProtecao=false;
  if (!reflexoProtecaoAtivo()) {
    // A trava pertence ao episódio: não exigir frente livre para reconhecer
    // uma parede nova após a borda desaparecer. Isto não libera avanço.
    bool trocarParaParede=travaProtecao && !strcmp(faseProtecao,"BLOQUEADA")
        && strcmp(causaProtecao,"OBSTACULO") && vigiaProtecao && conectado
        && uint32_t(agora-ultimoPacote)<ttl && motoresProntos && telaInicializada
        && !strcmp(riscoProtecao(agora),"OBSTACULO") && distancias[1].mm<=120;
    if (!trocarParaParede) amostrasTrocaRiscoProtecao=0;
    else if (ultimaTrocaRiscoProtecao!=distancias[1].medidaEm) {
      ultimaTrocaRiscoProtecao=distancias[1].medidaEm;
      if (++amostrasTrocaRiscoProtecao>=3) { iniciarProtecao("OBSTACULO",0,agora); return true; }
    }
    if (travaProtecao && contarSeguraProtecao(agora, true)) {
      travaProtecao = false; faseProtecao = "PRONTA";
    }
    // A busca esgotada descansa. Só a concessão renovada permite outra busca;
    // STOP/falha/borda não entram neste recomeço nem são apagados pelo relógio.
    if (!strcmp(faseProtecao,"ESPERA_BUSCA") && vigiaProtecao && conectado
        && uint32_t(agora-ultimoPacote)<ttl && motoresProntos && telaInicializada
        && uint32_t(agora-inicioFaseProtecao)>=4000
        && !strcmp(riscoProtecao(agora),"OBSTACULO")) {
      iniciarProtecao("OBSTACULO",0,agora); return true;
    }
    if (motorEmUso() && conectado && uint32_t(agora - ultimoPacote) < ttl
        && uint32_t(agora - inicioMotor) < duracaoMotor) {
      const char *risco = riscoProtecao(agora);
      if (strcmp(risco, "NENHUM")) { iniciarProtecao(risco, sequenciaMotor, agora); return true; }
    }
    if (!motorEmUso() && !travaProtecao && vigiaProtecao && conectado
        && uint32_t(agora-ultimoPacote)<ttl && motoresProntos && telaInicializada
        && (!strcmp(riscoProtecao(agora),"OBSTACULO") || !strncmp(riscoProtecao(agora),"BORDA",5))) {
      iniciarProtecao(riscoProtecao(agora),0,agora); return true;
    }
    return false;
  }
  if (!conectado || !sessao[0] || uint32_t(agora - ultimoPacote) >= ttl
      || (origemVigiaProtecao && !vigiaProtecao)
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
  bool parede = !strcmp(causaProtecao,"OBSTACULO");
  if (parede && (!strcmp(riscoProtecao(agora),"BORDA")
      || !strcmp(riscoProtecao(agora),"BORDA_SEM_RETORNO"))) {
    terminarProtecao("BLOQUEADA",agora); atualizarAlertaProtecao(agora); return true;
  }
  if (!strcmp(faseProtecao,"RECUANDO")) {
    if (idade >= 250) {
      if (!parede && strcmp(riscoProtecao(agora),"NENHUM")) faseNovaProtecao("ESPERA_MEDROSA",agora);
      else faseNovaProtecao("PAUSA", agora);
    }
    else aplicarReflexoProtecao(parede ? -160 : -120,parede ? -160 : -120,agora);
  } else if (!strcmp(faseProtecao,"ESPERA_MEDROSA")) {
    // Sem sensor traseiro: no máximo três passinhos adicionais de120ms,
    // separados por320ms parada. O pavor visual continua durante as pausas.
    if (!strcmp(riscoProtecao(agora),"NENHUM")) faseNovaProtecao("PAUSA",agora);
    else if (idade>=320) {
      if (recuosMedrososProtecao>=3) terminarProtecao("BLOQUEADA",agora);
      else { ++recuosMedrososProtecao; faseNovaProtecao("RECUO_MEDROSO",agora); sinalAlertaProtecao(agora,10); }
    }
  } else if (!strcmp(faseProtecao,"RECUO_MEDROSO")) {
    if (idade>=120) faseNovaProtecao("ESPERA_MEDROSA",agora);
    else aplicarReflexoProtecao(-110,-110,agora);
  } else if (!strcmp(faseProtecao,"PAUSA")) {
    if (idade >= 100) {
      faseNovaProtecao(parede ? "BUSCANDO" : "GIRANDO", agora);
      tentativasBuscaProtecao = parede ? 1 : 0;
      if (parede) sinalAlertaProtecao(agora,12);
      amostrasSegurasProtecao=0; ultimaFrenteProtecao=distancias[0].medidaEm;
      ultimaAmostraProtecao=distancias[1].medidaEm;
    }
  } else if (!strcmp(faseProtecao,"BUSCANDO")) {
    const uint16_t tempos[] = {160,240,400,320};
    if (idade >= tempos[tentativasBuscaProtecao-1]) {
      faseNovaProtecao("CONFERINDO",agora); amostrasSegurasProtecao=0;
      ultimaFrenteProtecao=distancias[0].medidaEm; ultimaAmostraProtecao=distancias[1].medidaEm;
    } else {
      int lado=tentativasBuscaProtecao<=2 ? 1 : -1;
      aplicarReflexoProtecao(170*lado,-170*lado,agora);
    }
  } else if (!strcmp(faseProtecao,"CONFERINDO")) {
    // Não reutilizar leituras da orientação anterior nem avançar pelo relógio.
    bool novaFrente=distancias[0].medidaEm!=ultimaFrenteProtecao;
    if (novaFrente && distancias[1].medidaEm!=ultimaAmostraProtecao) {
      ultimaFrenteProtecao=distancias[0].medidaEm;
      contarSeguraProtecao(agora,true);
    }
    if (amostrasSegurasProtecao>=3) faseNovaProtecao("SEGUINDO",agora);
    else if (idade>=160) {
      if (tentativasBuscaProtecao>=4) terminarProtecao("ESPERA_BUSCA",agora);
      else {
        ++tentativasBuscaProtecao; faseNovaProtecao("BUSCANDO",agora);
        sinalAlertaProtecao(agora,12);
        amostrasSegurasProtecao=0;
      }
    }
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
int expressaoProtecaoCorporal(uint32_t) { return 0; }
#endif
void processarVigiaProtecao(const char *entrada) {
  uint32_t seq,ativo,tempo; char pacote[128],*campos[6];
  if (!separarCampos(entrada,pacote,sizeof(pacote),campos,6)
      || strcmp(campos[1],"1") || strcmp(campos[2],sessao) || !sessao[0]
      || !decimalSemSinal(campos[3],seq) || !seq
      || !decimalSemSinal(campos[4],ativo) || ativo>1
      || !decimalSemSinal(campos[5],tempo) || tempo<500 || tempo>1500
      || !conectado || uint32_t(millis()-ultimoPacote)>=ttl) {
    responderLinha("ERROR 1 VIGIA_INVALIDA"); return;
  }
#if LAYLAY_PROTECAO_CORPORAL
  if (strcmp(sessaoVigiaProtecao,sessao)) {
    strcpy(sessaoVigiaProtecao,sessao); sequenciaVigiaProtecao=0;
    novaConcessaoVigiaPendente=true;
  }
  if (seq<=sequenciaVigiaProtecao) { responderLinha("ERROR 1 VIGIA_REPLAY"); return; }
  sequenciaVigiaProtecao=seq; ultimoVigiaProtecao=millis(); ttlVigiaProtecao=tempo;
  vigiaProtecao=ativo==1;
  if (vigiaProtecao && novaConcessaoVigiaPendente) {
    // A manobra da sessão antiga terminou; somente esta concessão NOVA pode
    // admitir outro episódio. Heartbeats da mesma sessão não repetem recuos.
    pararMotor(); faseProtecao="PRONTA"; travaProtecao=false;
    amostrasSegurasProtecao=amostrasTrocaRiscoProtecao=0;
    tentativasBuscaProtecao=recuosMedrososProtecao=0;
    novaConcessaoVigiaPendente=false;
  }
  if (!vigiaProtecao && origemVigiaProtecao && (reflexoProtecaoAtivo() || !strcmp(faseProtecao,"ESPERA_BUSCA"))) terminarProtecao("CANCELADA",millis());
  responder("SENTRYACK 1 %s %lu %lu\n",sessao,(unsigned long)seq,(unsigned long)ativo);
#else
  responderLinha("ERROR 1 VIGIA_DESABILITADA");
#endif
}
void processarConsultaProtecao(const char *entrada) {
  uint32_t seq; char pacote[80], *campos[3];
  if (!separarCampos(entrada,pacote,sizeof(pacote),campos,3)
      || strcmp(campos[1],"1") || !decimalSemSinal(campos[2],seq) || !seq) {
    responderLinha("ERROR 1 GUARD_INVALIDA"); return;
  }
#if LAYLAY_PROTECAO_CORPORAL
  const char *expressoes[] = {"NENHUMA","MEDO","PAVOR","IRRITADA","ALERTA"};
  responder("GUARD 1 %lu %s %lu %lu %s %s 130 100 %s %u %u\n", (unsigned long)seq,
    sessao[0] ? sessao : "SEMSESS", (unsigned long)incidenteProtecao, (unsigned long)motorOrigemProtecao,
    riscoProtecao(millis()), faseProtecao, expressoes[expressaoProtecaoCorporal(millis())],
    unsigned(tentativasBuscaProtecao),vigiaProtecao ? 1u : 0u);
#else
  responderLinha("ERROR 1 GUARD_DESABILITADA");
#endif
}

// Detalhes da partitura recebida. Não inferem emoção nem autorizam motores.
#pragma once
bool expressaoAtiva = false, ackExpressaoPendente = false;
uint32_t sequenciaExpressao = 0, inicioExpressao = 0, ttlExpressao = 1200;
char sessaoExpressao[9] = "";
int estiloExpressao = 0, faseExpressao = 0, ladoExpressao = 0;
float misturaExpressao = 0;

void limparExpressao() {
  expressaoAtiva = ackExpressaoPendente = false;
}

void atualizarExpressao(uint32_t agora) {
  if (!conectado || uint32_t(agora - inicioExpressao) >= ttlExpressao) limparExpressao();
}

void processarExpressao(const char *entrada) {
  char pacote[128], *campos[8]; uint32_t seq, estilo, fase, tempo; int lado;
  if (!separarCampos(entrada, pacote, sizeof(pacote), campos, 8)
      || strcmp(campos[0], "EXPR") || strcmp(campos[1], "1")
      || !sessaoValida(campos[2]) || !decimalSemSinal(campos[3], seq) || !seq
      || !decimalSemSinal(campos[4], estilo) || estilo > 10
      || !decimalSemSinal(campos[5], fase) || fase > 3
      || !decimalPwm(campos[6], lado) || lado < -1 || lado > 1
      || !decimalSemSinal(campos[7], tempo) || tempo < 50 || tempo > 6000) {
    responderLinha("ERROR 1 EXPR_INVALIDA"); return;
  }
  if (!conectado || !sessao[0] || strcmp(campos[2], sessao)
      || uint32_t(millis() - ultimoPacote) >= ttl || !telaInicializada) {
    responderLinha("ERROR 1 EXPR_SEM_SESSAO"); return;
  }
  if (strcmp(sessaoExpressao, sessao)) {
    strcpy(sessaoExpressao, sessao); sequenciaExpressao = 0;
  }
  if (seq <= sequenciaExpressao) { responderLinha("ERROR 1 EXPR_REPLAY"); return; }
  if (!telaPresente() || uint32_t(millis() - ultimoPacote) >= ttl) {
    invalidarSessao(); responderLinha("ERROR 1 EXPR_SEM_OLED"); return;
  }
  sequenciaExpressao = seq; estiloExpressao = estilo; faseExpressao = fase;
  ladoExpressao = lado; ttlExpressao = tempo; inicioExpressao = millis();
  expressaoAtiva = ackExpressaoPendente = true;
}

void publicarAckExpressao() {
  if (!ackExpressaoPendente) return;
  if (!conectado || uint32_t(millis() - ultimoPacote) >= ttl || !telaPresente()) {
    invalidarSessao(); return;
  }
  ackExpressaoPendente = false;
  responder("EACK 1 %s %lu %d %d %d %lu\n", sessao,
    (unsigned long)sequenciaExpressao, estiloExpressao, faseExpressao,
    ladoExpressao, (unsigned long)ttlExpressao);
}

void processarBoaNoite(const char *entrada) {
  char pacote[128], *campos[4]; uint32_t seq;
  if (!separarCampos(entrada, pacote, sizeof(pacote), campos, 4)
      || strcmp(campos[0], "GOODNIGHT") || strcmp(campos[1], "1")
      || !sessao[0] || strcmp(campos[2], sessao)
      || !decimalSemSinal(campos[3], seq) || !seq
      || (strcmp(sessaoExpressao, sessao) == 0 && seq <= sequenciaExpressao)) {
    responderLinha("ERROR 1 BOANOITE_INVALIDA"); return;
  }
  char token[9]; strcpy(token, sessao);
  invalidarSessao(); // Corta motores agora; interpolação visual termina depois.
  responder("NACK 1 %s %lu\n", token, (unsigned long)seq);
}

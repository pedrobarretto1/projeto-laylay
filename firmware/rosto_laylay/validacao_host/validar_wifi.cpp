#include <cassert>
#include <cstdio>
#define LAYLAY_WIFI 0
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"

const std::string tokenTeste(64, 'a');
void parados() {
  assert(niveisGpio[PINO_NSLEEP] == LOW && !motorAtivo && !motorPendente);
  for (int pino : PINOS_MOTOR) assert(dutiesPwm[pino] == 0);
}
void abrirTcp() { tcpClientePresente = true; inicioClienteTcp = millis(); }
void autenticar() {
  abrirTcp(); processarLinhaTcp(("AUTH 1 " + tokenTeste).c_str());
  assert(tcpAutenticado);
  assert(std::string(saidaTcp, tamanhoSaidaTcp) == "AUTH_OK 1\n"); tamanhoSaidaTcp = 0;
}
void face(const char *nonce, OrigemControle origem) {
  if (origem == OrigemControle::TCP) { tamanhoSaidaTcp = 0; Serial.saida.clear(); }
  std::string texto = std::string("HELLO 1 ") + nonce;
  processarLinha(texto.c_str(), origem);
  texto = std::string("FACE 1 ") + nonce + " 1 6 2 1 3500";
  processarLinha(texto.c_str(), origem);
  tempoSimulado += 40; loop();
  assert(conectado && donoControle == origem);
  if (origem == OrigemControle::TCP) {
    assert(Serial.saida.empty());
    assert(std::string(saidaTcp, tamanhoSaidaTcp).find(std::string("ACK 1 ") + nonce + " 1 6 2 1") != std::string::npos);
  }
  tamanhoSaidaTcp = 0; Serial.saida.clear();
}
void motor(const char *nonce, unsigned seq, OrigemControle origem) {
  char pacote[128]; snprintf(pacote, sizeof(pacote), "MOTOR 1 %s %u 255 -255 500", nonce, seq);
  processarLinha(pacote, origem); assert(motorPendente);
  tempoSimulado += 2; atualizarMotor(millis()); assert(motorAtivo);
}
void enviarUsbLongo(const std::string &pacote) {
  Serial.entrada = pacote + "\n";
  while (Serial.available()) loop();
}
int main() {
  setup(); Serial.saida.clear();
  processarLinha("WIFI_STATUS 1");
  assert(Serial.saida == "WIFI_STATUS 1 UNCONFIGURED\n");
  Serial.saida.clear(); processarLinha("WIFI_DIAG 1");
  assert(Serial.saida == "WIFI_DIAG 1 STATUS 0 REASON 0\n");
  Serial.saida.clear();
  // O buffer do USB, e não uma chamada direta ao parser, aceita SSID/senha máximos.
  const std::string config = "WIFI_CONFIG 1 " + std::string(64, '4') + " " + std::string(126, '5') + " " + tokenTeste;
  Serial.saida.clear(); enviarUsbLongo(config);
  assert(Serial.saida == "WIFI_CONFIGURED 1\n");
  assert(strlen(configWifi.ssid) == 32 && strlen(configWifi.senha) == 63);
  assert(wifiConfigurado && !conectado); parados();
  ConfigWifi anterior = configWifi;
  const char *invalidos[] = {
    "WIFI_CONFIG 1 00 - aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "WIFI_CONFIG 1 4142 00 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "WIFI_CONFIG 1 4 - aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "WIFI_CONFIG 2 4142 - aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "WIFI_CONFIG 1 4142 - abc", "WIFI_CONFIG 1 4142 - aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa extra",
  };
  for (const char *entrada : invalidos) {
    processarLinha(entrada); assert(!memcmp(&anterior, &configWifi, sizeof(anterior)));
  }
  tempoSimulado = 1000; face("01234567", OrigemControle::USB); motor("01234567", 1, OrigemControle::USB);
  abrirTcp(); processarLinhaTcp("STOP");
  assert(!tcpClientePresente && motorAtivo && donoControle == OrigemControle::USB);
  abrirTcp(); processarLinhaTcp("AUTH 1 bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb");
  assert(!tcpAutenticado && motorAtivo);
  autenticar(); assert(motorAtivo && donoControle == OrigemControle::USB); // AUTH não toma a sessão.
  uint32_t ultimoFace = ultimoPacote;
  processarLinhaTcp("FACE 1 01234567 2 2 1 0 3500");
  assert(ultimoPacote == ultimoFace && emocao == 6 && motorAtivo);
  processarLinhaTcp("STOP 1 01234567 1"); parados();
  assert(std::string(saidaTcp, tamanhoSaidaTcp).find("SACK") == std::string::npos);
  assert(sequenciaParada == 0 && donoControle == OrigemControle::USB);
  tamanhoSaidaTcp = 0;
  motor("01234567", 2, OrigemControle::USB);
  processarLinhaTcp("HELLO 1 malformed"); assert(motorAtivo && donoControle == OrigemControle::USB);
  tamanhoSaidaTcp = 0;
  face("abcdef01", OrigemControle::TCP); parados();
  // ACKs de render/pulso saem apenas no endpoint dono; USB é controle negativo.
  assert(Serial.saida.empty()); motor("abcdef01", 1, OrigemControle::TCP);
  assert(std::string(saidaTcp, tamanhoSaidaTcp).find("MACK 1 abcdef01 1 255 -255 500") != std::string::npos);
  assert(Serial.saida.empty()); tamanhoSaidaTcp = 0;
  processarLinha("WIFI_STATUS 1");
  assert(Serial.saida == "WIFI_STATUS 1 DISCONNECTED\n" && motorAtivo && donoControle == OrigemControle::TCP);
  Serial.saida.clear(); processarLinha("MOTOR 1 abcdef01 2 255 255 500");
  assert(sequenciaMotor == 1 && motorAtivo && Serial.saida.find("OUTRO_CONTROLADOR") != std::string::npos);
  fecharClienteWifi(); parados(); assert(!conectado && !sessao[0]);
  autenticar(); face("abcdef01", OrigemControle::TCP);
  processarLinhaTcp("MOTOR 1 abcdef01 1 255 -255 500"); parados(); // Não reutiliza comando após reconexão.
  assert(sequenciaMotor == 1); tamanhoSaidaTcp = 0;
  motor("abcdef01", 2, OrigemControle::TCP);
  assert(!enfileirarRespostaWifi(std::string(1025, 'x').c_str())); parados();
  autenticar(); face("abcdef02", OrigemControle::TCP); motor("abcdef02", 1, OrigemControle::TCP);
  tempoSimulado = inicioSaidaTcp + 100; atualizarPrazoWifi(); parados(); assert(!tcpClientePresente);
  autenticar(); face("abcdef03", OrigemControle::TCP); motor("abcdef03", 1, OrigemControle::TCP);
  for (int i = 0; i < 128; ++i) receberByteWifi('x'); parados(); assert(!tcpClientePresente);
  autenticar(); face("abcdef04", OrigemControle::TCP); motor("abcdef04", 1, OrigemControle::TCP);
  assert(!receberByteWifi(0)); parados();
  autenticar(); face("abcdef05", OrigemControle::TCP); motor("abcdef05", 1, OrigemControle::TCP);
  processarLinhaTcp("DEMO"); parados(); assert(!demonstracao && !tcpClientePresente);
  // Peer fantasma sem FIN não bloqueia novas conexões: somente FACE vigente mantém a sessão.
  autenticar(); tempoSimulado += 5000; atualizarPrazoWifi(); assert(!tcpClientePresente);
  autenticar(); processarLinhaTcp("HELLO 1 abcdef07"); tamanhoSaidaTcp = 0;
  tempoSimulado += 5000; atualizarPrazoWifi(); assert(!tcpClientePresente && !sessao[0]);
  autenticar(); face("abcdef08", OrigemControle::TCP);
  tempoSimulado = ultimoPacote + ttl; atualizarPrazoWifi(); assert(!tcpClientePresente && !conectado); parados();
  autenticar(); face("abcdef09", OrigemControle::TCP);
  processarLinha("HELLO 1 fedcba01"); atualizarPrazoWifi();
  assert(!tcpClientePresente && donoControle == OrigemControle::USB); parados();
  autenticar(); face("abcdef06", OrigemControle::TCP); motor("abcdef06", 1, OrigemControle::TCP);
  Serial.saida.clear(); enviarUsbLongo("WIFI_CONFIG 1 4c61796c6179 - " + tokenTeste);
  assert(Serial.saida == "WIFI_CONFIGURED 1\n" && !tcpClientePresente); parados();
  puts("WiFi: config USB máximo/sem eco, autenticação, owner único, ACKs isolados, STOP, cortes/replay/backpressure GREEN (hardware externo simulado).");
}

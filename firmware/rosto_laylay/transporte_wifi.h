#pragma once
#include <cstdarg>

#ifndef LAYLAY_WIFI
#ifdef ARDUINO_ARCH_ESP32
#define LAYLAY_WIFI 1
#else
#define LAYLAY_WIFI 0
#endif
#endif
#if LAYLAY_WIFI
#include <atomic>
#include <WiFi.h>
#include <Preferences.h>
#include <ESPmDNS.h>
#include <lwip/sockets.h>
#include <fcntl.h>
#include <errno.h>
#endif

// Um endpoint controla a sessão; conexão/autenticação não autorizam movimento.
enum class OrigemControle { NENHUMA, USB, TCP };
OrigemControle donoControle = OrigemControle::NENHUMA;
OrigemControle origemEmProcessamento = OrigemControle::NENHUMA;
constexpr uint16_t PORTA_WIFI = 8765;
struct ConfigWifi {
  uint32_t versao;
  char ssid[33], senha[64], token[65];
};
ConfigWifi configWifi = {};
// Configuração independente: preservar o formato NVS existente de credenciais.
struct ConfigIpWifi {
  uint32_t versao, ip, gateway, mascara;
  char ssid[33];
};
ConfigIpWifi configIpWifi = {};
bool ipFixoDaRede() {
  return configIpWifi.versao == 1 && !strcmp(configIpWifi.ssid, configWifi.ssid);
}
bool lerIpv4Wifi(const char *texto, uint32_t &valor) {
  valor = 0;
  for (int parte = 0; parte < 4; ++parte) {
    unsigned numero = 0, digitos = 0;
    while (*texto >= '0' && *texto <= '9') {
      numero = numero * 10 + unsigned(*texto++ - '0');
      if (++digitos > 3 || numero > 255) return false;
    }
    if (!digitos || (parte < 3 ? *texto++ != '.' : *texto != 0)) return false;
    valor = (valor << 8) | numero;
  }
  return true;
}
bool configIpWifiValida(const ConfigIpWifi &config) {
  if (config.versao == 0) return true; // DHCP explícito.
  uint32_t hosts = ~config.mascara;
  auto hostValido = [hosts](uint32_t ip) {
    unsigned primeiro = ip >> 24;
    return primeiro > 0 && primeiro < 224 && primeiro != 127
        && (ip & hosts) != 0 && (ip & hosts) != hosts;
  };
  return config.versao == 1 && memchr(config.ssid, 0, sizeof(config.ssid)) && config.ssid[0]
      && config.mascara && hosts >= 3 && !(hosts & (hosts + 1))
      && hostValido(config.ip) && hostValido(config.gateway) && config.ip != config.gateway
      && (config.ip & config.mascara) == (config.gateway & config.mascara);
}
bool salvarConfigIpWifi(const ConfigIpWifi &config) {
#if LAYLAY_WIFI
  Preferences preferencias;
  if (!preferencias.begin("laylay-wifi", false)) return false;
  bool salvo = preferencias.putBytes("endereco", &config, sizeof(config)) == sizeof(config);
  preferencias.end(); return salvo;
#else
  (void)config; return true;
#endif
}
bool wifiConfigurado = false, wifiConectado = false, wifiConectando = false;
bool tcpAutenticado = false, tcpClientePresente = false, tcpTinhaSessao = false;
char linhaTcp[128], saidaTcp[1024];
size_t tamanhoLinhaTcp = 0, tamanhoSaidaTcp = 0;
uint32_t inicioClienteTcp = 0, inicioSaidaTcp = 0, ultimaTentativaWifi = 0;
bool tentativaWifiIniciada = false;
#if LAYLAY_WIFI
int servidorFd = -1, clienteFd = -1;
bool mdnsIniciado = false;
std::atomic<unsigned int> motivoDesconexaoWifi{0};
#endif

void invalidarSessao();
void atualizarMotor(uint32_t agora);
bool motorEmUso();
bool sessaoTcpExpirada();
void processarLinha(const char *entrada, OrigemControle origem = OrigemControle::USB);

void fecharClienteWifi() {
  if (donoControle == OrigemControle::TCP) invalidarSessao();
#if LAYLAY_WIFI
  if (clienteFd >= 0) { close(clienteFd); clienteFd = -1; }
#endif
  tcpAutenticado = tcpClientePresente = tcpTinhaSessao = false;
  tamanhoLinhaTcp = tamanhoSaidaTcp = 0;
}

bool enfileirarRespostaWifi(const char *texto) {
  size_t tamanho = strlen(texto);
  if (!tcpClientePresente || tamanho > sizeof(saidaTcp) - tamanhoSaidaTcp) {
    fecharClienteWifi(); return false;
  }
  if (!tamanhoSaidaTcp) inicioSaidaTcp = millis();
  memcpy(saidaTcp + tamanhoSaidaTcp, texto, tamanho); tamanhoSaidaTcp += tamanho;
  return true;
}

void responder(const char *formato, ...) {
  char texto[256]; va_list args; va_start(args, formato);
  int tamanho = vsnprintf(texto, sizeof(texto), formato, args); va_end(args);
  OrigemControle destino = origemEmProcessamento != OrigemControle::NENHUMA
                         ? origemEmProcessamento : donoControle;
  if (tamanho < 0 || size_t(tamanho) >= sizeof(texto)) {
    if (destino == OrigemControle::TCP) fecharClienteWifi();
    return;
  }
  if (destino == OrigemControle::TCP) enfileirarRespostaWifi(texto);
  else Serial.printf("%s", texto);
}
void responderLinha(const char *texto) { responder("%s\n", texto); }
struct EscopoOrigem {
  OrigemControle anterior;
  explicit EscopoOrigem(OrigemControle origem) : anterior(origemEmProcessamento) { origemEmProcessamento = origem; }
  ~EscopoOrigem() { origemEmProcessamento = anterior; }
};

int valorHex(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  return -1;
}
bool tokenWifiValido(const char *token) {
  if (strlen(token) != 64) return false;
  for (size_t i = 0; i < 64; ++i) if (valorHex(token[i]) < 0) return false;
  return true;
}
bool decodificarHexWifi(const char *hex, char *destino, size_t capacidade, bool vazio) {
  if (vazio && !strcmp(hex, "-")) { destino[0] = 0; return true; }
  size_t tamanho = strlen(hex);
  if (!tamanho || tamanho % 2 || tamanho / 2 >= capacidade) return false;
  for (size_t i = 0; i < tamanho / 2; ++i) {
    int a = valorHex(hex[i * 2]), b = valorHex(hex[i * 2 + 1]);
    if (a < 0 || b < 0 || !(a * 16 + b)) return false;
    destino[i] = char(a * 16 + b);
  }
  destino[tamanho / 2] = 0; return true;
}
bool configWifiValida(const ConfigWifi &config) {
  return config.versao == 1 && memchr(config.ssid, 0, sizeof(config.ssid))
      && config.ssid[0] && memchr(config.senha, 0, sizeof(config.senha))
      && memchr(config.token, 0, sizeof(config.token)) && tokenWifiValido(config.token);
}
bool salvarConfigWifi(const ConfigWifi &config) {
#if LAYLAY_WIFI
  Preferences preferencias;
  if (!preferencias.begin("laylay-wifi", false)) return false;
  bool salvo = preferencias.putBytes("rede", &config, sizeof(config)) == sizeof(config);
  preferencias.end(); return salvo;
#else
  (void)config; return true; // Porta de persistência ausente somente no host.
#endif
}
void carregarConfigWifi() {
#if LAYLAY_WIFI
  Preferences preferencias;
  if (!preferencias.begin("laylay-wifi", true)) return;
  ConfigWifi candidata = {};
  if (preferencias.getBytesLength("rede") == sizeof(candidata)
      && preferencias.getBytes("rede", &candidata, sizeof(candidata)) == sizeof(candidata)
      && configWifiValida(candidata)) { configWifi = candidata; wifiConfigurado = true; }
  ConfigIpWifi endereco = {};
  if (preferencias.getBytesLength("endereco") == sizeof(endereco)
      && preferencias.getBytes("endereco", &endereco, sizeof(endereco)) == sizeof(endereco)
      && configIpWifiValida(endereco)) configIpWifi = endereco;
  preferencias.end();
#endif
}
void reiniciarWifi() {
  invalidarSessao(); fecharClienteWifi();
#if LAYLAY_WIFI
  if (servidorFd >= 0) { close(servidorFd); servidorFd = -1; }
  if (mdnsIniciado) { MDNS.end(); mdnsIniciado = false; }
  WiFi.disconnect(false, false);
#endif
  wifiConectado = wifiConectando = tentativaWifiIniciada = false;
}
bool separarCamposWifi(const char *entrada, char *pacote, size_t capacidade, char **campos, int total) {
  if (strlen(entrada) >= capacidade) return false;
  strcpy(pacote, entrada); char *cursor = pacote;
  for (int i = 0; i < total; ++i) {
    while (*cursor && isspace(static_cast<unsigned char>(*cursor))) ++cursor;
    if (!*cursor) return false;
    campos[i] = cursor;
    while (*cursor && !isspace(static_cast<unsigned char>(*cursor))) ++cursor;
    if (*cursor) *cursor++ = 0;
  }
  while (*cursor && isspace(static_cast<unsigned char>(*cursor))) ++cursor;
  return !*cursor;
}
bool processarConfiguracaoWifi(const char *entrada, OrigemControle origem) {
  if (!strcmp(entrada, "WIFI_IP_STATUS 1") && origem == OrigemControle::USB) {
    if (!ipFixoDaRede()) responderLinha("WIFI_IP_STATUS 1 DHCP");
    else {
      auto &c = configIpWifi;
      responder("WIFI_IP_STATUS 1 STATIC %u.%u.%u.%u %u.%u.%u.%u %u.%u.%u.%u\n",
        unsigned(c.ip >> 24), unsigned((c.ip >> 16) & 255), unsigned((c.ip >> 8) & 255), unsigned(c.ip & 255),
        unsigned(c.gateway >> 24), unsigned((c.gateway >> 16) & 255), unsigned((c.gateway >> 8) & 255), unsigned(c.gateway & 255),
        unsigned(c.mascara >> 24), unsigned((c.mascara >> 16) & 255), unsigned((c.mascara >> 8) & 255), unsigned(c.mascara & 255));
    }
    return true;
  }
  if (!strncmp(entrada, "WIFI_IP", 7)) {
    ConfigIpWifi candidata = {};
    char pacote[128]; char *campos[5];
    bool dhcp = !strcmp(entrada, "WIFI_IP 1 DHCP");
    bool valido = origem == OrigemControle::USB && wifiConfigurado;
    if (valido && !dhcp) {
      candidata.versao = 1; strcpy(candidata.ssid, configWifi.ssid);
      valido = separarCamposWifi(entrada, pacote, sizeof(pacote), campos, 5)
          && !strcmp(campos[0], "WIFI_IP") && !strcmp(campos[1], "1")
          && lerIpv4Wifi(campos[2], candidata.ip) && lerIpv4Wifi(campos[3], candidata.gateway)
          && lerIpv4Wifi(campos[4], candidata.mascara) && configIpWifiValida(candidata);
    }
    if (!valido) { responderLinha("ERROR 1 WIFI_IP_INVALIDO"); return true; }
    reiniciarWifi(); // Cortar sessão/tração antes da escrita e da nova associação.
    if (!salvarConfigIpWifi(candidata)) { responderLinha("ERROR 1 WIFI_PERSISTENCIA"); return true; }
    configIpWifi = candidata; responderLinha("WIFI_IP_CONFIGURED 1"); return true;
  }
  if (!strcmp(entrada, "WIFI_DIAG 1") && origem == OrigemControle::USB) {
#if LAYLAY_WIFI
    responder("WIFI_DIAG 1 STATUS %u REASON %u\n", unsigned(WiFi.status()), motivoDesconexaoWifi.load());
#else
    responderLinha("WIFI_DIAG 1 STATUS 0 REASON 0");
#endif
    return true;
  }
  if (!strncmp(entrada, "WIFI_STATUS", 11)) {
    if (origem != OrigemControle::USB || strcmp(entrada, "WIFI_STATUS 1")) {
      responderLinha("ERROR 1 WIFI_COMANDO_INVALIDO"); return true;
    }
    if (!wifiConfigurado) responderLinha("WIFI_STATUS 1 UNCONFIGURED");
    else if (wifiConectado) {
#if LAYLAY_WIFI
      auto ip = WiFi.localIP();
      responder("WIFI_STATUS 1 CONNECTED %u.%u.%u.%u %u\n", ip[0], ip[1], ip[2], ip[3], PORTA_WIFI);
#else
      responder("WIFI_STATUS 1 CONNECTED 127.0.0.1 %u\n", PORTA_WIFI);
#endif
    } else responderLinha(wifiConectando ? "WIFI_STATUS 1 CONNECTING" : "WIFI_STATUS 1 DISCONNECTED");
    return true;
  }
  if (strncmp(entrada, "WIFI_CONFIG", 11)) return false;
  char pacote[384]; char *campos[5]; ConfigWifi candidata = {};
  if (origem != OrigemControle::USB || !separarCamposWifi(entrada, pacote, sizeof(pacote), campos, 5)
      || strcmp(campos[0], "WIFI_CONFIG") || strcmp(campos[1], "1")
      || !decodificarHexWifi(campos[2], candidata.ssid, sizeof(candidata.ssid), false)
      || !decodificarHexWifi(campos[3], candidata.senha, sizeof(candidata.senha), true)
      || !tokenWifiValido(campos[4])) {
    responderLinha("ERROR 1 WIFI_CONFIG_INVALIDA"); return true;
  }
  candidata.versao = 1;
  for (size_t i = 0; i < 64; ++i) candidata.token[i] = "0123456789abcdef"[valorHex(campos[4][i])];
  // Provisionamento é operação local USB; nunca ocorre com ponte energizada.
  reiniciarWifi();
  if (!salvarConfigWifi(candidata)) { responderLinha("ERROR 1 WIFI_PERSISTENCIA"); return true; }
  configWifi = candidata; wifiConfigurado = true;
  responderLinha("WIFI_CONFIGURED 1"); return true;
}

void processarLinhaTcp(const char *entrada) {
  if (!tcpClientePresente) return;
  if (!tcpAutenticado) {
    char pacote[128]; char *campos[3];
    bool valido = wifiConfigurado && separarCamposWifi(entrada, pacote, sizeof(pacote), campos, 3)
               && !strcmp(campos[0], "AUTH") && !strcmp(campos[1], "1") && tokenWifiValido(campos[2]);
    unsigned int diferenca = 0;
    if (valido) for (size_t i = 0; i < 64; ++i) diferenca |= valorHex(campos[2][i]) ^ valorHex(configWifi.token[i]);
    if (!valido || diferenca) { fecharClienteWifi(); return; }
    tcpAutenticado = true; inicioClienteTcp = millis(); enfileirarRespostaWifi("AUTH_OK 1\n"); return;
  }
  if (!strncmp(entrada, "AUTH", 4) || !strncmp(entrada, "WIFI_", 5)
      || !strncmp(entrada, "DEMO", 4)) { fecharClienteWifi(); return; }
  processarLinha(entrada, OrigemControle::TCP);
}

bool receberByteWifi(char c) {
  if (c == '\r') return true;
  if (c == '\n') {
    linhaTcp[tamanhoLinhaTcp] = 0;
    atualizarMotor(millis()); processarLinhaTcp(linhaTcp); tamanhoLinhaTcp = 0;
    return tcpClientePresente;
  }
  if (!c || tamanhoLinhaTcp >= sizeof(linhaTcp) - 1) { fecharClienteWifi(); return false; }
  linhaTcp[tamanhoLinhaTcp++] = c; return true;
}
void atualizarPrazoWifi() {
  uint32_t agora = millis();
  if (tcpClientePresente && (((!tcpAutenticado || !tcpTinhaSessao) && agora - inicioClienteTcp >= 5000)
      || (tcpTinhaSessao && sessaoTcpExpirada())
      || (tamanhoSaidaTcp && agora - inicioSaidaTcp >= 100))) fecharClienteWifi();
}

void atualizarWifi() {
  atualizarPrazoWifi();
#if LAYLAY_WIFI
  if (!wifiConfigurado) return;
  bool conectadoAgora = WiFi.status() == WL_CONNECTED;
  if (!conectadoAgora) {
    if (wifiConectado) {
      fecharClienteWifi();
      if (servidorFd >= 0) { close(servidorFd); servidorFd = -1; }
      if (mdnsIniciado) { MDNS.end(); mdnsIniciado = false; }
    }
    wifiConectado = false;
    uint32_t agora = millis();
    if (!tentativaWifiIniciada || agora - ultimaTentativaWifi >= 15000) {
      // Inicialização da pilha nunca compete com um pulso. USB permanece utilizável.
      if (motorEmUso()) return;
      ultimaTentativaWifi = agora; tentativaWifiIniciada = wifiConectando = true;
      WiFi.mode(WIFI_STA); WiFi.setHostname("laylay-corpo"); WiFi.setAutoReconnect(false);
      auto ipv4 = [](uint32_t valor) {
        return IPAddress(valor >> 24, (valor >> 16) & 255, (valor >> 8) & 255, valor & 255);
      };
      // Sem fallback silencioso para DHCP se o IP fixo não puder ser aplicado.
      bool enderecoAplicado = ipFixoDaRede()
        ? WiFi.config(ipv4(configIpWifi.ip), ipv4(configIpWifi.gateway), ipv4(configIpWifi.mascara))
        : WiFi.config(IPAddress(0, 0, 0, 0), IPAddress(0, 0, 0, 0), IPAddress(0, 0, 0, 0));
      if (!enderecoAplicado) { wifiConectando = false; return; }
      WiFi.begin(configWifi.ssid, configWifi.senha);
#if defined(LAYLAY_WIFI_POTENCIA_BAIXA) && LAYLAY_WIFI_POTENCIA_BAIXA == 1
      // Perfil experimental da Super Mini: comparar associação com potência menor.
      WiFi.setTxPower(WIFI_POWER_8_5dBm);
#endif
    }
    return;
  }
  wifiConectado = true; wifiConectando = false;
  if (servidorFd < 0) {
    if (motorEmUso()) return;
    servidorFd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (servidorFd < 0) return;
    int reuse = 1; setsockopt(servidorFd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    sockaddr_in enderecoWifi = {}; enderecoWifi.sin_family = AF_INET;
    enderecoWifi.sin_port = htons(PORTA_WIFI); enderecoWifi.sin_addr.s_addr = htonl(INADDR_ANY);
    if (fcntl(servidorFd, F_SETFL, O_NONBLOCK) < 0 || bind(servidorFd, reinterpret_cast<sockaddr *>(&enderecoWifi), sizeof(enderecoWifi)) < 0
        || listen(servidorFd, 1) < 0) { close(servidorFd); servidorFd = -1; return; }
    // mDNS não participa de execução/receipt e é opcional para descoberta.
    if (!mdnsIniciado && MDNS.begin("laylay-corpo")) { mdnsIniciado = true; MDNS.addService("laylay-corpo", "tcp", PORTA_WIFI); }
  }
  if (clienteFd < 0) {
    clienteFd = accept(servidorFd, nullptr, nullptr);
    if (clienteFd < 0) return;
    if (fcntl(clienteFd, F_SETFL, O_NONBLOCK) < 0) { fecharClienteWifi(); return; }
    tcpClientePresente = true; inicioClienteTcp = millis();
  }
  char bytes[256]; int recebidos = recv(clienteFd, bytes, sizeof(bytes), MSG_DONTWAIT);
  if (!recebidos || (recebidos < 0 && errno != EWOULDBLOCK && errno != EAGAIN)) { fecharClienteWifi(); return; }
  for (int i = 0; i < recebidos; ++i) if (!receberByteWifi(bytes[i])) return;
  atualizarMotor(millis()); atualizarPrazoWifi();
  if (clienteFd < 0 || !tamanhoSaidaTcp) return;
  int enviados = send(clienteFd, saidaTcp, min(size_t(256), tamanhoSaidaTcp), MSG_DONTWAIT);
  if (!enviados || (enviados < 0 && errno != EWOULDBLOCK && errno != EAGAIN)) { fecharClienteWifi(); return; }
  if (enviados > 0) {
    tamanhoSaidaTcp -= enviados; memmove(saidaTcp, saidaTcp + enviados, tamanhoSaidaTcp);
  }
#endif
}

void iniciarWifi() {
#if LAYLAY_WIFI
  WiFi.onEvent([](WiFiEvent_t evento, WiFiEventInfo_t info) {
    if (evento == ARDUINO_EVENT_WIFI_STA_DISCONNECTED)
      motivoDesconexaoWifi.store(info.wifi_sta_disconnected.reason);
  });
#endif
  carregarConfigWifi();
}

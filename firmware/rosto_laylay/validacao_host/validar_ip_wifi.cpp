#include <cassert>
#include <cstdio>
#define LAYLAY_WIFI 0
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"

int main() {
  setup(); Serial.saida.clear();
  std::string token(64, 'a');
  processarLinha(("WIFI_CONFIG 1 4c61796c61792d436f72706f2d5043 - " + token).c_str());
  Serial.saida.clear();
  processarLinha("WIFI_IP 1 192.168.137.109 192.168.137.1 255.255.255.0");
  assert(Serial.saida == "WIFI_IP_CONFIGURED 1\n");
  Serial.saida.clear();
  processarLinha("WIFI_IP_STATUS 1");
  assert(Serial.saida == "WIFI_IP_STATUS 1 STATIC 192.168.137.109 192.168.137.1 255.255.255.0\n");
  const char *invalidos[] = {
    "WIFI_IP 1 192.168.137.1 192.168.137.1 255.255.255.0",
    "WIFI_IP 1 192.168.137.0 192.168.137.1 255.255.255.0",
    "WIFI_IP 1 192.168.137.255 192.168.137.1 255.255.255.0",
    "WIFI_IP 1 192.168.137.109 192.168.100.1 255.255.255.0",
    "WIFI_IP 1 192.168.137.109 192.168.137.1 255.0.255.0",
    "WIFI_IP 1 192.168.137.109 192.168.137.1 255.255.255.255",
    "WIFI_IP 1 999.168.137.109 192.168.137.1 255.255.255.0",
    "WIFI_IP 1 127.0.0.2 127.0.0.1 255.255.255.0",
    "WIFI_IP 2 DHCP", "WIFI_IP 1 DHCP extra",
  };
  for (const char *entrada : invalidos) {
    Serial.saida.clear(); processarLinha(entrada);
    assert(Serial.saida == "ERROR 1 WIFI_IP_INVALIDO\n");
    Serial.saida.clear(); processarLinha("WIFI_IP_STATUS 1");
    assert(Serial.saida.find("STATIC 192.168.137.109") != std::string::npos);
  }
  // A configuração é da rede provisionada; outra rede conserva DHCP.
  processarLinha(("WIFI_CONFIG 1 4f7574726152656465 - " + token).c_str());
  Serial.saida.clear(); processarLinha("WIFI_IP_STATUS 1");
  assert(Serial.saida == "WIFI_IP_STATUS 1 DHCP\n");
  processarLinha(("WIFI_CONFIG 1 4c61796c61792d436f72706f2d5043 - " + token).c_str());
  Serial.saida.clear(); processarLinha("WIFI_IP_STATUS 1");
  assert(Serial.saida.find("STATIC 192.168.137.109") != std::string::npos);
  // TCP autenticado não recebe autoridade para alterar rede/IP.
  tcpClientePresente = true;
  processarLinhaTcp(("AUTH 1 " + token).c_str());
  processarLinhaTcp("WIFI_IP 1 DHCP");
  assert(!tcpClientePresente);
  Serial.saida.clear(); processarLinha("WIFI_IP_STATUS 1");
  assert(Serial.saida.find("STATIC 192.168.137.109") != std::string::npos);
  processarLinha("HELLO 1 01234567");
  processarLinha("FACE 1 01234567 1 0 1 0 3500");
  tempoSimulado += 40; loop();
  processarLinha("MOTOR 1 01234567 1 255 -255 500");
  tempoSimulado += 2; atualizarMotor(millis());
  assert(motorAtivo);
  Serial.saida.clear(); processarLinha("WIFI_IP 1 DHCP");
  assert(Serial.saida == "WIFI_IP_CONFIGURED 1\n");
  assert(niveisGpio[PINO_NSLEEP] == LOW);
  for (int pino : PINOS_MOTOR) assert(dutiesPwm[pino] == 0);
  Serial.saida.clear(); processarLinha("WIFI_IP_STATUS 1");
  assert(Serial.saida == "WIFI_IP_STATUS 1 DHCP\n");
  assert(!motorAtivo && !motorPendente && !conectado);
  puts("IP WiFi: USB, validacao, escopo da rede, DHCP e TCP sem autoridade GREEN; NVS/associacao exigem hardware.");
}

#pragma once

#if defined(LAYLAY_BLE) && LAYLAY_BLE
#if !LAYLAY_WIFI
#error "BLE requer o armazenamento do pareamento Wi-Fi existente"
#endif
#include <BLEDevice.h>
#include <mbedtls/md.h>
#include <esp_random.h>

constexpr char SERVICO_BLE[] = "e0086801-e5a7-44bb-ac7d-a21706aa9301";
constexpr char ENTRADA_BLE[] = "e0086801-e5a7-44bb-ac7d-a21706aa9302";
constexpr char SAIDA_BLE[] = "e0086801-e5a7-44bb-ac7d-a21706aa9303";
struct EventoBle {
  enum Tipo { ABRIU, FECHOU, DADOS } tipo;
  uint16_t id;
  uint8_t tamanho;
  char bytes[20];
};
QueueHandle_t filaBle = nullptr;
std::atomic<bool> falhaFilaBle{false}, contatoBle{false};
std::atomic<uint16_t> idContatoBle{0};
BLEServer *servidorBle = nullptr;
BLECharacteristic *saidaBle = nullptr;
bool presenteBle = false, autenticadoBle = false;
uint16_t idBle = 0;
uint32_t inicioBle = 0, ultimoEnvioBle = 0;
char clienteNonceBle[33]{}, servidorNonceBle[33]{}, linhaBle[128]{}, respostaBle[768]{};
char credencialSessaoBle[65]{};
size_t tamanhoLinhaBle = 0, tamanhoRespostaBle = 0;

void postarBle(const EventoBle &evento) {
  if (xQueueSend(filaBle, &evento, 0) != pdTRUE) falhaFilaBle.store(true);
}
class ConexaoBleCorporal : public BLEServerCallbacks {
  void onConnect(BLEServer *, ble_gap_conn_desc *p) override {
    idContatoBle.store(p->conn_handle);
    contatoBle.store(true);
    postarBle({EventoBle::ABRIU, p->conn_handle, 0, {}});
  }
  void onDisconnect(BLEServer *, ble_gap_conn_desc *p) override {
    contatoBle.store(false);
    postarBle({EventoBle::FECHOU, p->conn_handle, 0, {}});
  }
};
class EscritaBleCorporal : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *c, ble_gap_conn_desc *p) override {
    String valor = c->getValue();
    if (!valor.length() || valor.length() > 20) { falhaFilaBle.store(true); return; }
    EventoBle evento{EventoBle::DADOS, p->conn_handle, uint8_t(valor.length()), {}};
    memcpy(evento.bytes, valor.c_str(), evento.tamanho);
    postarBle(evento);
  }
};

void fecharBleCorporal(bool desconectar) {
  bool ativo = presenteBle;
  presenteBle = autenticadoBle = false;
  tamanhoLinhaBle = tamanhoRespostaBle = 0;
  clienteNonceBle[0] = servidorNonceBle[0] = 0;
  memset(credencialSessaoBle, 0, sizeof(credencialSessaoBle));
  if (donoControle == OrigemControle::BLE) invalidarSessaoPor("TRANSPORTE");
  if (desconectar && ativo) servidorBle->disconnect(idBle);
}
bool enfileirarRespostaBle(const char *texto) {
  size_t tamanho = strlen(texto);
  if (!presenteBle || !contatoBle.load()) return false;
  if (tamanho > sizeof(respostaBle) - tamanhoRespostaBle) {
    falhaFilaBle.store(true); return false;
  }
  memcpy(respostaBle + tamanhoRespostaBle, texto, tamanho);
  tamanhoRespostaBle += tamanho;
  return true;
}
void hexBle(const uint8_t *bytes, size_t tamanho, char *saida) {
  constexpr char digitos[] = "0123456789abcdef";
  for (size_t i = 0; i < tamanho; ++i) {
    saida[2*i] = digitos[bytes[i] >> 4];
    saida[2*i+1] = digitos[bytes[i] & 15];
  }
  saida[2*tamanho] = 0;
}
bool provaBle(char papel, char *saida) {
  char mensagem[80];
  snprintf(mensagem, sizeof(mensagem), "%c:%s:%s", papel, clienteNonceBle, servidorNonceBle);
  uint8_t hash[32];
  if (mbedtls_md_hmac(mbedtls_md_info_from_type(MBEDTLS_MD_SHA256),
      reinterpret_cast<const uint8_t *>(configWifi.token), 64,
      reinterpret_cast<const uint8_t *>(mensagem), strlen(mensagem), hash)) return false;
  hexBle(hash, sizeof(hash), saida);
  return true;
}
void processarLinhaBleCorporal(const char *linha) {
  if (!contatoBle.load()) return;
  if (!autenticadoBle) {
    if (!wifiConfigurado) { fecharBleCorporal(true); return; }
    const char *nonce = linha + 12;
    if (!clienteNonceBle[0] && !strncmp(linha,"BLE_HELLO 1 ",12) && strlen(nonce)==32
        && strspn(nonce,"0123456789abcdef")==32) {
      strcpy(clienteNonceBle, nonce);
      uint8_t bytes[16]; esp_fill_random(bytes, sizeof(bytes)); hexBle(bytes,sizeof(bytes),servidorNonceBle);
      char prova[65], resposta[128];
      if (!provaBle('S', prova)) { fecharBleCorporal(true); return; }
      snprintf(resposta,sizeof(resposta),"BLE_CHALLENGE 1 %s %s\n",servidorNonceBle,prova);
      enfileirarRespostaBle(resposta);
      return;
    }
    char esperada[65];
    if (!clienteNonceBle[0] || strncmp(linha,"BLE_AUTH 1 ",11) || strlen(linha+11)!=64
        || !provaBle('C',esperada)) { fecharBleCorporal(true); return; }
    unsigned diferenca=0;
    for (size_t i=0;i<64;++i) diferenca |= unsigned(linha[11+i]^esperada[i]);
    if (diferenca) { fecharBleCorporal(true); return; }
    memcpy(credencialSessaoBle, configWifi.token, sizeof(credencialSessaoBle));
    autenticadoBle=true; enfileirarRespostaBle("BLE_READY 1\n"); return;
  }
  if (!strncmp(linha,"WIFI",4) || !strncmp(linha,"DEMO",4) || !strncmp(linha,"BEEP_TEST",9)) {
    fecharBleCorporal(true); return;
  }
  // Um cliente BLE não toma a posse de uma sessão USB ou Wi-Fi ativa.
  if (donoControle != OrigemControle::NENHUMA && donoControle != OrigemControle::BLE) {
    enfileirarRespostaBle("ERROR 1 OUTRO_CONTROLADOR\n"); return;
  }
  processarLinha(linha, OrigemControle::BLE);
  if (!strncmp(linha, "HELLO ", 6) && donoControle==OrigemControle::BLE) inicioBle=millis();
}
void iniciarBleCorporal() {
  if (!wifiConfigurado || filaBle) return;
  filaBle=xQueueCreate(24,sizeof(EventoBle));
  if (!filaBle) return;
  BLEDevice::init("Laylay-Corpo");
  servidorBle=BLEDevice::createServer();
  static ConexaoBleCorporal conexao;
  servidorBle->setCallbacks(&conexao);
  auto *servico=servidorBle->createService(SERVICO_BLE);
  auto *entrada=servico->createCharacteristic(ENTRADA_BLE,BLECharacteristic::PROPERTY_WRITE);
  static EscritaBleCorporal escrita;
  entrada->setCallbacks(&escrita);
  saidaBle=servico->createCharacteristic(SAIDA_BLE,BLECharacteristic::PROPERTY_NOTIFY);
  servico->start();
  BLEDevice::getAdvertising()->addServiceUUID(SERVICO_BLE);
  BLEDevice::startAdvertising();
}
void atualizarBleCorporal() {
  if (!filaBle) { iniciarBleCorporal(); return; }
  if (autenticadoBle && memcmp(credencialSessaoBle, configWifi.token, sizeof(credencialSessaoBle))) {
    fecharBleCorporal(true); return;
  }
  if (falhaFilaBle.exchange(false)) {
    bool ativo=contatoBle.load();
    fecharBleCorporal(false);
    xQueueReset(filaBle);
    if (ativo) servidorBle->disconnect(idContatoBle.load());
    else BLEDevice::startAdvertising();
    return;
  }
  EventoBle evento;
  for (int n=0;n<8 && xQueueReceive(filaBle,&evento,0)==pdTRUE;++n) {
    if (evento.tipo==EventoBle::ABRIU) {
      fecharBleCorporal(false);
      presenteBle=true; idBle=evento.id; inicioBle=millis();
    } else if (evento.tipo==EventoBle::FECHOU) {
      if (evento.id==idBle) fecharBleCorporal(false);
      BLEDevice::startAdvertising();
    } else if (presenteBle && contatoBle.load() && evento.id==idBle) {
      for (uint8_t i=0;i<evento.tamanho && presenteBle;++i) {
        char c=evento.bytes[i];
        if (c=='\n') {
          linhaBle[tamanhoLinhaBle]=0; tamanhoLinhaBle=0;
          processarLinhaBleCorporal(linhaBle);
        } else if (c<32 || c>126 || tamanhoLinhaBle>=sizeof(linhaBle)-1) {
          fecharBleCorporal(true);
        } else linhaBle[tamanhoLinhaBle++]=c;
      }
    }
  }
  uint32_t agora=millis();
  if (presenteBle && (!contatoBle.load()
      || ((!autenticadoBle || (donoControle==OrigemControle::BLE && !conectado)) && agora-inicioBle>=6000))) {
    fecharBleCorporal(contatoBle.load()); return;
  }
  if (presenteBle && tamanhoRespostaBle && agora-ultimoEnvioBle>=8) {
    size_t quantidade=min(size_t(20),tamanhoRespostaBle);
    saidaBle->setValue(reinterpret_cast<const uint8_t *>(respostaBle),quantidade);
    saidaBle->notify();
    tamanhoRespostaBle-=quantidade;
    memmove(respostaBle,respostaBle+quantidade,tamanhoRespostaBle);
    ultimoEnvioBle=agora;
  }
}
void responderStatusBleCorporal() {
  responderLinha(!filaBle ? "BLE_STATUS 1 UNCONFIGURED"
      : autenticadoBle ? "BLE_STATUS 1 AUTHENTICATED"
      : contatoBle.load() ? "BLE_STATUS 1 CONNECTED"
      : BLEDevice::getAdvertising()->isAdvertising() ? "BLE_STATUS 1 ADVERTISING" : "BLE_STATUS 1 IDLE");
}
#else
void iniciarBleCorporal() {}
void atualizarBleCorporal() {}
void responderStatusBleCorporal() { responderLinha("BLE_STATUS 1 DISABLED"); }
#endif

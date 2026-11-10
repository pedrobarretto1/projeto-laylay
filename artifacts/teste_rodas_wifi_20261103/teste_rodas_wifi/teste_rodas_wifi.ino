/* ESP32-C3 Super Mini + DRV8833: teste WiFi independente das duas rodas.
 * USB 115200, com Nova linha: F = frente 5 s; S = parar. TCP: TESTE 1 seq ACAO.
 * Ao ligar, as rodas ficam paradas. Nenhum comando depende dos sensores.
 * OLED SSD1306 128x64: VCC=3V3, GND=GND, SDA=8, SCL=9.
 * Arduino-ESP32 3.x; habilitar USB CDC On Boot no Arduino IDE.
 */
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "transporte_wifi.h"

constexpr uint8_t AIN1 = 1, AIN2 = 2;
constexpr uint8_t BIN1 = 3, BIN2 = 4;
constexpr uint8_t SLEEP_PONTE = 7;
constexpr uint8_t PINOS[] = {AIN1, AIN2, BIN1, BIN2};
constexpr uint32_t FREQUENCIA_PWM = 1000;
constexpr uint8_t PWM_TESTE = 150;  // Escala 0..255.
constexpr uint32_t DURACAO_MS = 5000;
constexpr bool INVERTER_ESQUERDO = false;
constexpr bool INVERTER_DIREITO = false;

Adafruit_SSD1306 tela(128, 64, &Wire, -1, 400000, 400000);
bool telaPronta = false, telaSuja = true;
uint8_t enderecoTela = 0;
uint32_t ultimoSegundoTela = UINT32_MAX;
const char *estadoTela = "PRONTO";

bool pwmPronto[4] = {};
bool pronto = false, andando = false;
uint32_t inicioMovimento = 0;
uint32_t ultimoPacoteTeste = 0, ultimaSequenciaTCP = 0;
char entradaUSB[384];
size_t tamanhoUSB = 0;
bool descartandoUSB = false;
uint8_t redeAnterior = 255;

void parar() {
  digitalWrite(SLEEP_PONTE, LOW);  // Corta a ponte antes de qualquer outra operação.
  for (uint8_t i = 0; i < 4; ++i) {
    if (pwmPronto[i] && !ledcWrite(PINOS[i], 0)) {
      ledcDetach(PINOS[i]);
      pwmPronto[i] = false;
      pronto = false;
    }
    if (!pwmPronto[i]) {
      digitalWrite(PINOS[i], LOW);
      pinMode(PINOS[i], OUTPUT);
    }
  }
  andando = false;
  estadoTela = pronto ? "PARADO" : "ERRO PWM";
  telaSuja = true;
}

void conferirPrazo() {
  if (andando && uint32_t(millis() - inicioMovimento) >= DURACAO_MS) {
    parar();
    Serial.println("Tempo encerrado; ponte desligada.");
  }
}

void iniciarTela() {
  Wire.begin(8, 9);
  Wire.setTimeOut(10);
  for (uint8_t endereco : {uint8_t(0x3C), uint8_t(0x3D)}) {
    Wire.beginTransmission(endereco);
    if (Wire.endTransmission() == 0) {
      enderecoTela = endereco;
      break;
    }
  }
  telaPronta = enderecoTela && tela.begin(SSD1306_SWITCHCAPVCC, enderecoTela, true, false);
  if (!telaPronta) Serial.println("OLED nao encontrado; comandos F/S continuam pela serial.");
}

void atualizarTela() {
  if (!telaPronta) return;
  conferirPrazo();
  const uint32_t decorrido = andando ? uint32_t(millis() - inicioMovimento) : 0;
  const uint32_t restante = andando ? DURACAO_MS - min(decorrido, DURACAO_MS) : 0;
  const uint32_t segundos = (restante + 999) / 1000;
  if (!telaSuja && segundos == ultimoSegundoTela) return;
  Wire.beginTransmission(enderecoTela);
  if (Wire.endTransmission() != 0) {
    telaPronta = false;
    Serial.println("OLED perdeu comunicacao; comandos F/S continuam pela serial.");
    return;
  }
  tela.clearDisplay();
  tela.setTextColor(SSD1306_WHITE);
  tela.setTextSize(1);
  tela.setCursor(0, 0);
  tela.print("LAYLAY - RODAS WIFI");
  tela.drawFastHLine(0, 11, 128, SSD1306_WHITE);
  tela.setTextSize(2);
  tela.setCursor(0, 18);
  tela.print(estadoTela);
  tela.setTextSize(1);
  tela.setCursor(0, 40);
  if (andando) {
    tela.print("Frente: ");
    tela.print(segundos);
    tela.print(" s | PWM ");
    tela.print(PWM_TESTE);
    tela.drawRect(0, 52, 128, 10, SSD1306_WHITE);
    tela.fillRect(2, 54, (124UL * (DURACAO_MS - restante)) / DURACAO_MS, 6, SSD1306_WHITE);
  } else {
    if (wifiConectado) tela.print(WiFi.localIP().toString().c_str());
    else tela.print(wifiConfigurado ? "WiFi conectando..." : "WiFi sem config.");
    tela.setCursor(0, 54);
    tela.print("S: parar | PWM ");
    tela.print(PWM_TESTE);
  }
  telaSuja = false;
  ultimoSegundoTela = segundos;
  tela.display();
  conferirPrazo();
}

void frente() {
  if (!pronto) {
    Serial.println("ERRO: PWM indisponivel. Ponte permanece desligada.");
    return;
  }
  if (andando) {
    Serial.println("Teste em andamento; F nao prolonga os 5 segundos.");
    return;
  }
  const uint8_t valores[] = {
    INVERTER_ESQUERDO ? 0 : PWM_TESTE, INVERTER_ESQUERDO ? PWM_TESTE : 0,
    INVERTER_DIREITO ? 0 : PWM_TESTE, INVERTER_DIREITO ? PWM_TESTE : 0,
  };
  for (uint8_t i = 0; i < 4; ++i) {
    if (!ledcWrite(PINOS[i], valores[i])) {
      pronto = false;
      parar();
      Serial.println("ERRO ao aplicar PWM; ponte desligada.");
      return;
    }
  }
  digitalWrite(SLEEP_PONTE, HIGH);
  inicioMovimento = millis();
  andando = true;
  estadoTela = "ANDANDO";
  telaSuja = true;
  Serial.println("PWM aplicado aos dois motores por 5 segundos. S = parar.");
}


// Transporte autenticado compartilhado com o corpo; autenticar nao move rodas.
void invalidarSessao() {
  parar();
  donoControle = OrigemControle::NENHUMA;
  ultimaSequenciaTCP = 0;
}
void atualizarMotor(uint32_t) { conferirPrazo(); }
bool motorEmUso() { return andando; }
bool sessaoTcpExpirada() {
  return donoControle != OrigemControle::TCP || uint32_t(millis() - ultimoPacoteTeste) >= 2000;
}
void publicarStatusTeste(uint32_t seq) {
  conferirPrazo();
  uint32_t restante = andando ? DURACAO_MS - min(uint32_t(millis() - inicioMovimento), DURACAO_MS) : 0;
  const char *estado = !pronto ? "ERRO_PWM" : andando ? "ANDANDO" : "PARADO";
  responder("TESTSTATUS 1 %lu %s %lu %u\n", (unsigned long)seq, estado,
            (unsigned long)restante, unsigned(PWM_TESTE));
}
void processarLinha(const char *entrada, OrigemControle origem) {
  EscopoOrigem escopo(origem);
  if (processarConfiguracaoWifi(entrada, origem)) return;
  if (origem == OrigemControle::USB) {
    if (!strcmp(entrada, "S") || !strcmp(entrada, "s")) {
      parar(); responderLinha("Ponte desligada por comando."); return;
    }
    if (!strcmp(entrada, "F") || !strcmp(entrada, "f")) {
      if (tcpClientePresente) { responderLinha("ERROR 1 CONTROLE_WIFI_ATIVO"); return; }
      donoControle = OrigemControle::USB; frente(); return;
    }
    if (!strcmp(entrada, "STATUS")) { publicarStatusTeste(1); return; }
    responderLinha("ERROR 1 COMANDO_DE_TESTE_INVALIDO"); return;
  }
  if (!tcpAutenticado) return;
  char pacote[96], *campos[4];
  if (!separarCamposWifi(entrada, pacote, sizeof(pacote), campos, 4)
      || strcmp(campos[0], "TESTE") || strcmp(campos[1], "1")
      || !campos[2][0] || strspn(campos[2], "0123456789") != strlen(campos[2])) {
    responderLinha("ERROR 1 COMANDO_DE_TESTE_INVALIDO"); return;
  }
  unsigned long numero = strtoul(campos[2], nullptr, 10);
  if (!numero || numero > UINT32_MAX) { responderLinha("ERROR 1 SEQUENCIA_INVALIDA"); return; }
  uint32_t seq = uint32_t(numero);
  bool consulta = !strcmp(campos[3], "STATUS"), movimento = !strcmp(campos[3], "FRENTE");
  bool parada = !strcmp(campos[3], "PARAR");
  if (!consulta && !movimento && !parada) {
    responder("TESTERROR 1 %lu ACAO_INVALIDA\n", numero); return;
  }
  if (andando && donoControle != OrigemControle::TCP && !parada) {
    responder("TESTERROR 1 %lu OUTRO_CONTROLADOR\n", numero); return;
  }
  if (seq <= ultimaSequenciaTCP) {
    responder("TESTERROR 1 %lu SEQUENCIA_REPETIDA\n", numero); return;
  }
  ultimaSequenciaTCP = seq;
  donoControle = OrigemControle::TCP;
  tcpTinhaSessao = true;
  ultimoPacoteTeste = millis();
  if (consulta) { publicarStatusTeste(seq); return; }
  if (parada) {
    parar(); responder("TESTACK 1 %lu PARADO 0 %u\n", numero, unsigned(PWM_TESTE)); return;
  }
  if (!pronto || andando) {
    responder("TESTERROR 1 %lu %s\n", numero, !pronto ? "PWM_INDISPONIVEL" : "TESTE_EM_ANDAMENTO"); return;
  }
  frente();
  if (!andando) { responder("TESTERROR 1 %lu PWM_NAO_APLICADO\n", numero); return; }
  responder("TESTACK 1 %lu FRENTE %lu %u\n", numero, (unsigned long)DURACAO_MS, unsigned(PWM_TESTE));
}

void setup() {
  digitalWrite(SLEEP_PONTE, LOW);
  pinMode(SLEEP_PONTE, OUTPUT);
  for (uint8_t pino : PINOS) {
    digitalWrite(pino, LOW);
    pinMode(pino, OUTPUT);
  }
  Serial.begin(115200);
  pronto = true;
  for (uint8_t i = 0; i < 4; ++i) {
    pwmPronto[i] = ledcAttach(PINOS[i], FREQUENCIA_PWM, 8);
    if (!pwmPronto[i]) pronto = false;
  }
  parar();
  estadoTela = pronto ? "PRONTO" : "ERRO PWM";
  iniciarTela();
  iniciarWifi();
  atualizarTela();
  Serial.println("Teste de rodas: F = frente por 5 s; S = parar.");
}

void loop() {
  conferirPrazo();
  for (unsigned i = 0; i < 64 && Serial.available(); ++i) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      if (!descartandoUSB && tamanhoUSB) {
        entradaUSB[tamanhoUSB] = 0;
        processarLinha(entradaUSB, OrigemControle::USB);
      }
      tamanhoUSB = 0; descartandoUSB = false;
    } else if (!c || tamanhoUSB >= sizeof(entradaUSB) - 1) {
      tamanhoUSB = 0; descartandoUSB = true;
    } else if (!descartandoUSB) entradaUSB[tamanhoUSB++] = c;
  }
  atualizarWifi();
  conferirPrazo();
  uint8_t rede = wifiConectado ? 2 : wifiConfigurado ? 1 : 0;
  if (rede != redeAnterior) { redeAnterior = rede; telaSuja = true; }
  atualizarTela();
  delay(1);
}

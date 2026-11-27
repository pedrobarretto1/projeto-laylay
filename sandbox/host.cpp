// Executa o sketch no host. Somente os periféricos são simulados.
#include <iostream>
#include <sstream>

#define LAYLAY_WIFI 0
#define LAYLAY_BLE 0
#define LAYLAY_IMU 1
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#define LAYLAY_LIMITE_MOTOR_TESTE_MS 5000
#define LAYLAY_PWM_MINIMO_MOTOR 170
#include LAYLAY_SKETCH_HOST

void amostraImu(uint8_t registro, float valor, float escala) {
  int16_t inteiro = int16_t(std::clamp(std::lround(valor * escala), -32768L, 32767L));
  Wire.registrosImu[registro] = uint16_t(inteiro) >> 8;
  Wire.registrosImu[registro + 1] = uint8_t(inteiro);
}

void emitirSerial() {
  std::istringstream mensagens(Serial.saida);
  std::string texto;
  while (std::getline(mensagens, texto)) std::cout << "R " << texto << '\n';
  Serial.saida.clear();
}

void estadoHost() {
  const bool ponte = niveisGpio[PINO_NSLEEP] == HIGH;
  const int esquerda = ponte ? int(dutiesPwm[PINOS_MOTOR[0]]) - int(dutiesPwm[PINOS_MOTOR[1]]) : 0;
  const int direita = ponte ? int(dutiesPwm[PINOS_MOTOR[2]]) - int(dutiesPwm[PINOS_MOTOR[3]]) : 0;
  const auto &frente = distancias[0];
  const char *estadoFrente = estadoDistancia(frente, millis());
  const int distancia = !strcmp(estadoFrente, "VALIDA") ? frente.mm : -1;
  std::cout << "E " << esquerda << ' ' << direita << ' ' << distancia << ' '
            << estadoFrente << ' ' << estadoImu(millis()) << '/' << manuseioImu(millis()) << ' '
            << riscoProtecao(millis()) << '\n';
  std::cout << "I " << episodioManuseio.fase << '\n';
}

int main() {
  Wire.extras[0x29] = Wire.extras[0x68] = true;
  Wire.registrosImu[0x75] = 0x98;
  amostraImu(0x3f, 1, 8192);
  setup();
  emitirSerial();
  std::cout << "F\n" << std::flush;
  for (std::string linha; std::getline(std::cin, linha);) {
    if (linha.rfind("P ", 0) == 0) {
      Serial.entrada += linha.substr(2) + '\n';
      loop();
    } else if (linha.rfind("S ", 0) == 0) {
      unsigned ms = 0;
      int frente = -1, noColo = 0;
      float ax, ay, az, gx, gy, gz;
      std::istringstream dados(linha.substr(2));
      if (dados >> ms >> frente >> noColo >> ax >> ay >> az >> gx >> gy >> gz) {
        amostraImu(0x3b, ax, 8192); amostraImu(0x3d, ay, 8192); amostraImu(0x3f, az, 8192);
        amostraImu(0x43, gx, 65.5f); amostraImu(0x45, gy, 65.5f); amostraImu(0x47, gz, 65.5f);
        distancias[0].dispositivo.statusMedida = frente < 0 ? 4 : 0;
        distancias[0].dispositivo.distancia = frente < 0 ? 8190 : frente;
        distancias[1].dispositivo.statusMedida = noColo ? 4 : 0;
        distancias[1].dispositivo.distancia = noColo ? 8190 : 85;
        tempoSimulado += std::clamp(ms, 1U, 50U);
        subMilissegundos = 0;
        loop();
        estadoHost();
      }
    } else if (linha == "O") {
      static constexpr char hex[] = "0123456789abcdef";
      std::string oled;
      oled.reserve(2048);
      for (const auto &linhaPixels : tela.pixels) {
        for (int x = 0; x < 128; x += 8) {
          uint8_t byte = 0;
          for (int i = 0; i < 8; ++i) byte = (byte << 1) | uint8_t(linhaPixels[x+i] != 0);
          oled += hex[byte >> 4]; oled += hex[byte & 15];
        }
      }
      std::cout << "O " << oled << '\n';
    }
    emitirSerial();
    std::cout << "F\n" << std::flush;
  }
}

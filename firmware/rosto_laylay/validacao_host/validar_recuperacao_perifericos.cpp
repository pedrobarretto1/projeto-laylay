#include <cassert>
#include <sstream>
#include <vector>
#define LAYLAY_IMU 1
#define LAYLAY_SENSORES_DISTANCIA 1
#define LAYLAY_PROTECAO_CORPORAL 1
#define LAYLAY_HABILITAR_MOTORES_BANCADA 1
#include "../rosto_laylay.ino"

int main(int argc, char **argv) {
  Wire.extras[0x29]=true;
  Wire.registrosImu[0x75]=0x98;Wire.registrosImu[0x3F]=0x20;
  if(argc>1 && !strcmp(argv[1],"distancia")) {
    Wire.extras[0x68]=true;
    distancias[0].dispositivo.falharInicio=true;
    setup();assert(!distancias[0].presente && distancias[1].presente);
    for(unsigned t=100;t<12000;t+=10) {tempoSimulado=t;loop();}
    // Tentativas espaçadas; a falha persistente continua visível e bloqueada.
    auto ultima=ultimaRecuperacaoPerifericos;
    assert(ultima>=10000 && ultima<12000 && !motorEmUso());
    distancias[0].dispositivo.falharInicio=false;
    for(unsigned t=12000;t<18000;t+=10) {tempoSimulado=t;loop();}
    assert(distancias[0].presente && distancias[1].presente && !motorEmUso());
    assert(!conectado && !vigiaProtecao);
    puts("DISTANCIA_GREEN: nova enumeracao sem colisao, espera limitada e tracao cortada");return 0;
  }
  if(argc>1 && !strcmp(argv[1],"oled")) {
    Wire.presente=false;setup();assert(!telaInicializada);
    Wire.presente=true;Wire.extras[0x68]=true;
    for(unsigned t=100;t<9000;t+=10) {tempoSimulado=t;loop();}
    assert(telaInicializada && !falhaFrameI2c && imu.calibrada);
    assert(!motorEmUso() && !conectado);
    puts("OLED_GREEN: falha no boot nao exige reboot");return 0;
  }
  if (argc>1 && !strcmp(argv[1],"snapshot")) {
    Wire.extras[0x68]=true;setup();
    imu.amostra=imu.calibrada=true;imu.medidaEm=1000;
    for (unsigned idade=65;idade<82;++idade) {
      tempoSimulado=1000+idade;relogioAvanca=true;Serial.saida.clear();
      processarConsultaImu("IMU 1 1");
      relogioAvanca=false;
      std::istringstream fluxo(Serial.saida);std::vector<std::string> p;
      for(std::string c;fluxo>>c;)p.push_back(c);
      assert(p.size()==18);
      if(p[4]=="PRONTA") assert(std::stoul(p[5])<=75);
      else assert(p[12]=="DESCONHECIDO" && p[14]=="DESCONHECIDA");
    }
    puts("SNAPSHOT_GREEN: classificacao e idade no mesmo instante");return 0;
  }
  setup();assert(!imu.presente);
  // Ausência no boot não pode exigir reiniciar o ESP ou a aplicação.
  Wire.extras[0x68]=true;
  for(unsigned t=100;t<9000;t+=10) {tempoSimulado=t;loop();}
  assert(imu.presente && imu.calibrada && !imu.erro);
  assert(!motorEmUso() && !conectado && !vigiaProtecao);
  // Lacuna real: nova calibração, sessão anterior cancelada e nenhum replay.
  processarLinha("HELLO 1 01234567");
  processarLinha("FACE 1 01234567 1 0 1 0 5000");
  Wire.extras[0x68]=false;
  for(unsigned t=9000;t<9800;t+=10) {tempoSimulado=t;loop();}
  assert(!conectado && !motorEmUso() && !vigiaProtecao);
  auto perdas=perdasSessaoCorpo;
  Wire.extras[0x68]=true;
  for(unsigned t=9800;t<18000;t+=10) {tempoSimulado=t;loop();}
  assert(imu.presente && imu.calibrada && !imu.erro);
  assert(!conectado && !motorEmUso() && perdasSessaoCorpo==perdas);
  // Sem retorno óptico é leitura válida do protocolo, não falha elétrica.
  distancias[0].dispositivo.statusMedida=4;
  auto perdasAntes=perdasSessaoCorpo;
  processarLinha("HELLO 1 89abcdef");
  processarLinha("FACE 1 89abcdef 1 0 1 0 5000");
  for(unsigned t=18000;t<20000;t+=10) {tempoSimulado=t;loop();}
  assert(conectado && perdasSessaoCorpo==perdasAntes && !motorEmUso());
  puts("RECUPERACAO_GREEN: ausencia, erro, recalibracao e nenhum replay");
}

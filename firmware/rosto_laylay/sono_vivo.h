// Sonhos são variações visuais locais, sem mudar a emoção da mente ou mover o corpo.
#pragma once
bool iniciarSomSono(uint32_t agora, uint16_t hz);
bool sonoVivoIniciado = false, sonhoAtivo = false;
uint8_t estiloSonho = 0, quantidadeZ = 1;
uint32_t proximoSonho = 0, inicioSonho = 0, duracaoSonho = 1;
uint32_t proximoSomSono = 0, inicioZ = 0, duracaoZ = 1, proximoZ = 0;
float pesoSonho = 0, faseSonho = 0, velocidadeSono = 1.05f, amplitudeSono = 1.5f;
float derivaSonho = 0;

float limiarSono(int x, int y) {
  // Dither espacial estável: suaviza bordas no OLED de uma cor, sem piscar pixels.
  const uint8_t ordem[4][4] = {{0,8,2,10},{12,4,14,6},{3,11,1,9},{15,7,13,5}};
  return (ordem[y & 3][x & 3] + .5f) / 16;
}

void desenharPalpebraSono(int x, float topo, float fundo, float peso) {
  for (int y = int(floorf(topo - .5f)); y <= int(ceilf(fundo + .5f)); ++y) {
    float cobertura = max(0.f, min(fundo + .5f, y + .5f) - max(topo - .5f, y - .5f));
    float limiar = misturar(.5f, limiarSono(x, y), peso);
    if (cobertura > limiar) tela.drawPixel(x, y, SSD1306_WHITE);
  }
}

float distanciaSegmentoSono(float x, float y, float ax, float ay, float bx, float by) {
  float dx = bx - ax, dy = by - ay;
  float t = max(0.f, min(1.f, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)));
  dx = x - ax - t * dx; dy = y - ay - t * dy;
  return sqrtf(dx * dx + dy * dy);
}

void desenharZSuave(float x, float y, float tamanho, float intensidade) {
  for (int py = int(floorf(y - 1)); py <= int(ceilf(y + tamanho + 1)); ++py)
    for (int px = int(floorf(x - 1)); px <= int(ceilf(x + tamanho + 1)); ++px) {
      float distancia = min(distanciaSegmentoSono(px, py, x, y, x + tamanho, y),
          min(distanciaSegmentoSono(px, py, x + tamanho, y, x, y + tamanho),
              distanciaSegmentoSono(px, py, x, y + tamanho, x + tamanho, y + tamanho)));
      float cobertura = max(0.f, min(1.f, 1.15f - distancia)) * intensidade;
      if (cobertura > limiarSono(px, py)) tela.drawPixel(px, py, SSD1306_WHITE);
    }
}

void atualizarSonoVivo(bool dormindo, uint32_t agora, float dt) {
  if (!dormindo) {
    sonoVivoIniciado = sonhoAtivo = false;
    pesoSonho = aproximar(pesoSonho, 0, dt, .55f);
    return;
  }
  if (!sonoVivoIniciado) {
    sonoVivoIniciado = true;
    proximoSonho = agora + random(8500, 13000);
    proximoSomSono = agora + random(55000, 90000);
    inicioZ = agora; duracaoZ = random(4200, 6200);
    proximoZ = agora + duracaoZ + random(2000, 5000);
  }
  if (!sonhoAtivo && int32_t(agora - proximoSonho) >= 0) {
    sonhoAtivo = true; inicioSonho = agora;
    duracaoSonho = random(6500, 11000);
    estiloSonho = (estiloSonho + random(1, 3)) % 3;
    derivaSonho = random(0, 2) ? 1 : -1;
    velocidadeSono = random(80, 121) / 100.f;
    amplitudeSono = random(12, 20) / 10.f;
  }
  faseSonho = min(1.f, uint32_t(agora - inicioSonho) / float(duracaoSonho));
  float envelope = sonhoAtivo ? powf(sinf(faseSonho * 3.141593f), 2) : 0;
  pesoSonho = aproximar(pesoSonho, envelope, dt, .3f);
  if (sonhoAtivo && faseSonho >= 1) {
    sonhoAtivo = false;
    proximoSonho = agora + random(4500, 14000);
  }
  if (int32_t(agora - proximoZ) >= 0) {
    inicioZ = agora; duracaoZ = random(4000, 7500);
    quantidadeZ = random(1, 3);
    proximoZ = agora + duracaoZ + random(2000, 6000);
  }
  // Só no sono estabilizado e sem sessão: HELLO/FACE têm prioridade.
  // Não toca em sequência de receipt, cooldown diurno ou controle dos motores.
  if (int32_t(agora - proximoSomSono) >= 0) {
    proximoSomSono = agora + random(65000, 120000);
    if (repouso > .999f && !sessao[0] && telaInicializada && !motorEmUso())
      iniciarSomSono(agora, random(1350, 1651));
  }
}

void desenharSonoVivo(uint32_t agora, float balanco) {
  float forca = max(0.f, (repouso - .65f) / .35f);
  float viagem = uint32_t(agora - inicioZ) / float(duracaoZ);
  for (int i = 0; i < quantidadeZ; ++i) {
    float fase = viagem - i * .22f;
    if (fase <= 0 || fase >= 1) continue;
    float intensidade = min(1.f, min(fase / .18f, (1 - fase) / .24f));
    intensidade = intensidade * intensidade * (3 - 2 * intensidade);
    desenharZSuave(103 + i * 11 + fase * 3, 24 - fase * 23, i ? 5 : 4, intensidade * forca);
  }
  // Um brilho discreto no sonho sorridente; sem símbolos na área da boca.
  if (estiloSonho == 0)
    desenharBrilhoOlhos(11, lroundf(18 - balanco), pesoSonho * repouso * .8f);
}

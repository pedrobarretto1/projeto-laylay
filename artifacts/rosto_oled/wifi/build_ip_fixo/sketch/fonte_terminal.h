#line 1 "C:\\Users\\pbarr\\Downloads\\pasta organizada\\programacao\\PY\\projeto lay\\laylay\\firmware\\rosto_laylay\\fonte_terminal.h"
#pragma once
#include <stdint.h>
#include <string.h>

// Raster 5x7 do próprio efeito: o mesmo código desenha no OLED e na prévia host.
// Somente caracteres dos rótulos fictícios fixos; nenhum texto da conversa.
inline const uint8_t *glifoTerminal(char letra) {
  static const char letras[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789>/:.-_";
  static const uint8_t glifos[][7] = {
    {14,17,17,31,17,17,17}, {30,17,17,30,17,17,30}, {14,17,16,16,16,17,14},
    {30,17,17,17,17,17,30}, {31,16,16,30,16,16,31}, {31,16,16,30,16,16,16},
    {14,17,16,23,17,17,15}, {17,17,17,31,17,17,17}, {14,4,4,4,4,4,14},
    {7,2,2,2,18,18,12}, {17,18,20,24,20,18,17}, {16,16,16,16,16,16,31},
    {17,27,21,21,17,17,17}, {17,25,25,21,19,19,17}, {14,17,17,17,17,17,14},
    {30,17,17,30,16,16,16}, {14,17,17,17,21,18,13}, {30,17,17,30,20,18,17},
    {15,16,16,14,1,1,30}, {31,4,4,4,4,4,4}, {17,17,17,17,17,17,14},
    {17,17,17,17,17,10,4}, {17,17,17,21,21,21,10}, {17,17,10,4,10,17,17},
    {17,17,10,4,4,4,4}, {31,1,2,4,8,16,31},
    {14,17,19,21,25,17,14}, {4,12,4,4,4,4,14}, {14,17,1,2,4,8,31},
    {30,1,1,14,1,1,30}, {2,6,10,18,31,2,2}, {31,16,16,30,1,1,30},
    {14,16,16,30,17,17,14}, {31,1,2,4,8,8,8}, {14,17,17,14,17,17,14},
    {14,17,17,15,1,1,14},
    {16,8,4,2,4,8,16}, {1,2,2,4,8,8,16}, {0,4,4,0,4,4,0},
    {0,0,0,0,0,4,4}, {0,0,0,31,0,0,0}, {0,0,0,0,0,0,31},
  };
  static const uint8_t vazio[7] = {};
  const char *encontrada = strchr(letras, letra);
  return encontrada && letra ? glifos[encontrada - letras] : vazio;
}

template<class Tela>
inline void desenharTextoTerminal(Tela &display, int x, int y, const char *texto,
                                  int limite = 21, int topo = 0, int fundo = 63) {
  for (int letra = 0; texto[letra] && letra < limite; ++letra) {
    const uint8_t *glifo = glifoTerminal(texto[letra]);
    for (int linha = 0; linha < 7; ++linha) {
      int py = y + linha;
      if (py < topo || py > fundo) continue;
      for (int coluna = 0; coluna < 5; ++coluna)
        if (glifo[linha] & (1 << (4 - coluna)))
          display.drawPixel(x + letra * 6 + coluna, py, 1);
    }
  }
}

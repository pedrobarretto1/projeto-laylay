#pragma once
#include "Arduino.h"
#include "Wire.h"
#include <fstream>
#include <cmath>
#define SSD1306_WHITE 1
#define SSD1306_BLACK 0
#define SSD1306_SWITCHCAPVCC 2
class Adafruit_SSD1306 {
 public:
  uint8_t pixels[64][128] = {};
  int frames = 0;
  uint32_t demoraDisplay = 0;
  bool desaparecerAposDisplay = false;
  uint8_t bufferI2c[1024] = {};
  uint8_t *getBuffer() { return bufferI2c; }
  Adafruit_SSD1306(int, int, WireSimulada *, int, uint32_t=400000, uint32_t=400000) {}
  bool begin(int, int, bool, bool) { return Wire.presente; }
  void clearDisplay() { memset(pixels, 0, sizeof(pixels)); }
  void drawPixel(int x, int y, int c) { if (x >= 0 && x < 128 && y >= 0 && y < 64) pixels[y][x] = c; }
  bool getPixel(int x, int y) { return x >= 0 && x < 128 && y >= 0 && y < 64 && pixels[y][x]; }
  void drawFastVLine(int x, int y, int h, int c) { for (int i=0;i<h;++i) drawPixel(x,y+i,c); }
  void drawLine(int x0,int y0,int x1,int y1,int c) {
    int dx=abs(x1-x0),sx=x0<x1?1:-1,dy=-abs(y1-y0),sy=y0<y1?1:-1,err=dx+dy;
    while (true) { drawPixel(x0,y0,c); if(x0==x1&&y0==y1) break;
      int e=2*err; if(e>=dy){err+=dy;x0+=sx;} if(e<=dx){err+=dx;y0+=sy;} }
  }
  void fillRoundRect(int x,int y,int w,int h,int r,int c) {
    for(int yy=0;yy<h;++yy) for(int xx=0;xx<w;++xx) {
      int cx=xx<r?r:xx>=w-r?w-r-1:xx, cy=yy<r?r:yy>=h-r?h-r-1:yy;
      if((xx-cx)*(xx-cx)+(yy-cy)*(yy-cy)<=r*r) drawPixel(x+xx,y+yy,c);
    }
  }
  void fillTriangle(int x0,int y0,int x1,int y1,int x2,int y2,int c) {
    auto cross=[](int ax,int ay,int bx,int by,int px,int py){return (px-ax)*(by-ay)-(py-ay)*(bx-ax);};
    for(int y=min(y0,min(y1,y2)); y<=max(y0,max(y1,y2));++y)
      for(int x=min(x0,min(x1,x2));x<=max(x0,max(x1,x2));++x) {
        int a=cross(x0,y0,x1,y1,x,y),b=cross(x1,y1,x2,y2,x,y),d=cross(x2,y2,x0,y0,x,y);
        if((a>=0&&b>=0&&d>=0)||(a<=0&&b<=0&&d<=0)) drawPixel(x,y,c);
      }
  }
  void fillCircle(int cx,int cy,int r,int c) {
    for(int y=-r;y<=r;++y) for(int x=-r;x<=r;++x) if(x*x+y*y<=r*r)drawPixel(cx+x,cy+y,c);
  }
  void drawCircle(int cx,int cy,int r,int c) {
    int x=0,y=r,p=1-r;
    while(x<=y) { for(int s:{-1,1}) for(int t:{-1,1}) {drawPixel(cx+s*x,cy+t*y,c);drawPixel(cx+s*y,cy+t*x,c);}
      ++x; if(p<0)p+=2*x+1;else {--y;p+=2*(x-y)+1;} }
  }
  void setTextSize(int) {} void setTextColor(int) {} void setCursor(int,int) {} void print(const char*) {}
  void display() {
    ++frames; tempoSimulado += demoraDisplay;
    if (desaparecerAposDisplay) Wire.presente = false;
  }
  void salvar(const std::string &caminho) {
    std::ofstream f(caminho, std::ios::binary); f << "P5\n128 64\n255\n";
    for(auto &linha:pixels) for(auto p:linha) f.put(static_cast<char>(p?255:0));
  }
};

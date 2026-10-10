#pragma once
#include "settings_effect_preview.h"
#include "best_effect_ui.h"

namespace SettingsEffectPreview {
// Translate only the existing renderer's 135x71 readout region into the free
// settings band. No scaled fonts, second framebuffer or per-frame allocation.
class Surface {
  lgfx::LGFXBase &g_;int top_;
public:
  Surface(lgfx::LGFXBase &g,int top):g_(g),top_(top){}
  int width()const{return g_.width();}int height()const{return 240;}
  auto readPixel(int x,int y){return g_.readPixel(x,y+top_);}
  void drawPixel(int x,int y,uint16_t c){g_.drawPixel(x,y+top_,c);}
  void fillRect(int x,int y,int w,int h,uint16_t c){g_.fillRect(x,y+top_,w,h,c);}
};
inline void draw(lgfx::LGFXBase &g,const State &state,Controls::Page page,
                 BestEffectUI::Renderer &renderer,uint32_t now,uint16_t accent,bool buffered,bool failed){
  if(!state.visible())return;
  const bool editing=page==Controls::Page::Edit;const int top=editing?108:130,cx=g.width()/2;
  g.setTextDatum(top_center);g.setTextColor(TFT_DARKGREY,TFT_BLACK);
  g.drawString(state.busy() && buffered?"Sample / paused":"Sample preview",cx,editing?94:116,1);
  g.fillRect(0,top,g.width(),71,TFT_BLACK);
  // Same native bitmap fonts, number placement and readout fallback as recap.
  // This constant is illustrative, never read from or submitted to practice.
  g.setTextColor(accent,TFT_BLACK);g.drawString("NEW BEST",cx,top+2,1);
  g.drawString("8120 RPM",cx,top+17,g.textWidth("8120 RPM",&fonts::Font4)<=g.width()-6?4:2);
  if(buffered && !state.busy()){
    Surface band(g,top);renderer.draw(band,state.mode(),state.elapsed(now),accent);
  }
  if(!failed && (!buffered || state.mode()==Appearance::Effect::Off)){
    g.setTextColor(TFT_DARKGREY,TFT_BLACK);
    g.drawString(!buffered?"Motion unavailable":"Off: static badge",cx,editing?198:206,1);
  }
}
}

#include "appearance_store.h"
#include "best_effect_ui.h"
#include <cassert>
#include <iostream>
#include <limits>

struct Pixels {
  std::array<uint16_t,135*240> p{};
  int width(){return 135;}int height(){return 240;}
  uint16_t readPixel(int x,int y){return p[y*135+x];}
  void drawPixel(int x,int y,uint16_t c){assert(x>=0 && x<135 && y>=0 && y<240);p[y*135+x]=c;}
  void fillRect(int x,int y,int w,int h,uint16_t c){for(int j=0;j<h;++j)for(int i=0;i<w;++i)drawPixel(x+i,y+j,c);}
};
int main(){
  using namespace Appearance;
  Preferences::data.clear();Preferences::zeroLengthKeys.clear();
  Config config;AppearanceStore<Config> settings;assert(settings.begin(config,"a","cfg0","cfg1"));
  assert(config.theme==Theme::Classic && config.effect==Effect::Orbit);
  for(unsigned theme=0;theme<THEMES;++theme)for(unsigned effect=0;effect<EFFECTS;++effect){
    assert(config.select(Theme(theme),Effect(effect)) && settings.save(config));
    Config restored;AppearanceStore<Config> reader;assert(reader.begin(restored,"a","cfg0","cfg1"));
    assert(restored.theme==config.theme && restored.effect==config.effect);
  }
  auto draft=config;draft.select(Theme::Mint,Effect::Orbit);Preferences::failWrite=true;
  assert(!settings.save(draft) && config.theme==Theme::Violet);
  Preferences::failWrite=false;assert(settings.save(draft));
  assert(!draft.select(Theme(255),Effect::Off));
  Bests b;AppearanceStore<Bests> store;assert(store.begin(b,"b","best0","best1"));
  assert(!b.observe(0,0,false,9000) && !b.observe(0,0,true,0) && !b.observe(0,0,true,std::numeric_limits<float>::quiet_NaN()));
  for(unsigned sensor=0;sensor<2;++sensor)for(unsigned method=0;method<2;++method){
    assert(!b.observe(sensor,method,true,6000));assert(!b.observe(sensor,method,true,6000));
    assert(!b.observe(sensor,method,true,5999));assert(b.observe(sensor,method,true,6000.5f));
  }
  assert(b.revision==8 && store.pending(b));assert(store.save(b));
  Bests reboot;AppearanceStore<Bests> afterBoot;assert(afterBoot.begin(reboot,"b","best0","best1"));
  assert(!reboot.observe(0,0,true,6000.5f) && reboot.observe(0,0,true,6100));
  Preferences::shortRead=true;assert(!afterBoot.save(reboot) && afterBoot.pending(reboot));Preferences::shortRead=false;
  assert(afterBoot.save(reboot));
  // Corrupt newest slot recovers verified older generation; all-corrupt/typed
  // keys are retained and disable saves/celebration rather than reseed a PB.
  Preferences::data["bbest0"][0]^=1;
  Bests recovered;AppearanceStore<Bests> older;assert(older.begin(recovered,"b","best0","best1") && recovered.rpm[0]==6000.5f);
  Preferences::zeroLengthKeys={"bbest0","bbest1"};const auto retained=Preferences::data;
  Bests unknown;AppearanceStore<Bests> invalid;assert(!invalid.begin(unknown,"b","best0","best1") && !invalid.ready());
  assert(!invalid.save(unknown) && Preferences::data==retained);Preferences::zeroLengthKeys.clear();
  Celebration c;assert(!c.badge());c.queue(true,7);c.captured(6);assert(!c.badge());
  c.captured(7);assert(c.badge() && !c.moving(10,Effect::Orbit));c.presented(0xfffffff0u);
  assert(c.moving(40,Effect::Orbit) && c.elapsed(40)==56);c.presented(40);assert(c.elapsed(40)==56);
  assert(!c.moving(40,Effect::Off));assert(!c.moving(1100,Effect::Crown) && c.badge());
  c.clear();c.captured(7);c.presented(20);assert(!c.badge());c.queue(false,8);c.captured(8);assert(!c.badge());
  BestEffectUI::Renderer renderer;unsigned frames=0,moving=0;
  for(unsigned theme=0;theme<THEMES;++theme)for(unsigned mode=0;mode<EFFECTS;++mode)for(unsigned ms=0;ms<=1100;ms+=10){
    Pixels base;
    // Glyph pixels including their holes, upper replay edges, and lower UI.
    for(int y=2;y<10;++y)for(int x=44;x<91;++x)if((x+y)%3)base.drawPixel(x,y,0xffff);
    for(int y=17;y<44;++y)for(int x=3;x<132;++x)if((x+y)%5)base.drawPixel(x,y,0x7ff);
    base.fillRect(65,49,4,10,0x18c3);base.fillRect(9,54,2,16,0x39e7);base.fillRect(20,100,90,130,0x39e7);
    Pixels out=base;renderer.draw(out,Effect(mode),ms,accent(Theme(theme)));
    bool changed=false;
    for(int y=0;y<240;++y)for(int x=0;x<135;++x)if(out.p[y*135+x]!=base.p[y*135+x]){
      changed=true;assert(x>=3 && x<132 && y>=3 && y<68 && !(y>=13 && y<=45));
      for(int dy=-3;dy<=3;++dy)for(int dx=-3;dx<=3;++dx)if(x+dx>=0 && x+dx<135 && y+dy>=0 && y+dy<240)assert(!base.p[(y+dy)*135+x+dx]);
    }
    if(ms>=duration(Effect(mode)))assert(!changed);moving+=changed;++frames;
  }
  assert(moving>0);
  std::cout<<"PASS: appearance defaults/cycles, verified alternating stores/retry/reboot/corruption, per-profile/method strict PB, presentation token/wrap, "<<frames<<" clipped effect frames\n";
}

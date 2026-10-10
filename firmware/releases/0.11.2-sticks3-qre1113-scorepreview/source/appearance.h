#pragma once
#include <array>
#include <cstdint>
#include <cstring>
#include <cmath>

// Appearance is UI-only. No detector, IMU or metric policy lives here.
namespace Appearance {
enum class Theme:uint8_t {Classic,Mint,Amber,Violet};
enum class Effect:uint8_t {Orbit,Flames,Sparkles,Shockwave,Crown,Off};
constexpr unsigned THEMES=4,EFFECTS=6;
inline const char *label(Theme t){static const char *s[]={"Classic","Mint","Amber","Violet"};return unsigned(t)<THEMES?s[unsigned(t)]:s[0];}
inline const char *label(Effect e){static const char *s[]={"Orbit","Flames","Sparkles","Shockwave","Crown","Off"};return unsigned(e)<EFFECTS?s[unsigned(e)]:s[0];}
inline uint16_t accent(Theme t){static constexpr uint16_t c[]={0x07ff,0x8ff9,0xff10,0xc5bf};return unsigned(t)<THEMES?c[unsigned(t)]:c[0];}
inline uint32_t duration(Effect e){static constexpr uint16_t ms[]={960,900,800,720,1050,0};return unsigned(e)<EFFECTS?ms[unsigned(e)]:0;}
inline uint32_t hash(const uint8_t *p,size_t n){uint32_t h=2166136261u;while(n--){h^=*p++;h*=16777619u;}return h;}
inline uint32_t get32(const uint8_t *p){return uint32_t(p[0])|uint32_t(p[1])<<8|uint32_t(p[2])<<16|uint32_t(p[3])<<24;}
inline void put32(uint8_t *p,uint32_t v){for(unsigned i=0;i<4;++i)p[i]=uint8_t(v>>(8*i));}
struct Config {
  using Image=std::array<uint8_t,16>;
  Theme theme=Theme::Classic;Effect effect=Effect::Orbit;
  uint32_t revision=0;
  uint32_t generation()const{return revision;}
  bool select(Theme t,Effect e){
    if(unsigned(t)>=THEMES || unsigned(e)>=EFFECTS)return false;
    if(t!=theme || e!=effect){theme=t;effect=e;++revision;}return true;
  }
  void encode(Image &b)const{b={};put32(b.data(),0x01414c4c);put32(b.data()+4,revision);b[8]=uint8_t(theme);b[9]=uint8_t(effect);put32(b.data()+12,hash(b.data(),12));}
  bool decode(const uint8_t *b,size_t n){
    if(n!=16 || get32(b)!=0x01414c4c || get32(b+12)!=hash(b,12) || b[8]>=THEMES || b[9]>=EFFECTS || b[10] || b[11])return false;
    revision=get32(b+4);theme=Theme(b[8]);effect=Effect(b[9]);return true;
  }
};
// First post-upgrade valid pull seeds a profile/method baseline silently.
// Older bounded history has no provenance and is intentionally not migrated.
struct Bests {
  using Image=std::array<uint8_t,32>;
  float rpm[4]={};uint32_t revision=0;
  uint32_t generation()const{return revision;}
  bool observe(unsigned sensor,unsigned method,bool valid,float value){
    if(sensor>=2 || method>=2 || !valid || !std::isfinite(value) || value<1000 || value>1500000)return false;
    float &best=rpm[sensor*2+method];if(value<=best)return false;
    const bool beat=best>0;best=value;++revision;return beat;
  }
  void encode(Image &b)const{
    b={};put32(b.data(),0x01424c4c);put32(b.data()+4,revision);
    for(unsigned i=0;i<4;++i){uint32_t v;std::memcpy(&v,&rpm[i],4);put32(b.data()+8+i*4,v);}
    put32(b.data()+28,hash(b.data(),28));
  }
  bool decode(const uint8_t *b,size_t n){
    if(n!=32 || get32(b)!=0x01424c4c || get32(b+28)!=hash(b,28) || get32(b+24))return false;
    float values[4];for(unsigned i=0;i<4;++i){const auto v=get32(b+8+i*4);std::memcpy(&values[i],&v,4);if(!std::isfinite(values[i]) || (values[i]!=0 && (values[i]<1000 || values[i]>1500000)))return false;}
    revision=get32(b+4);std::memcpy(rpm,values,sizeof(rpm));return true;
  }
};
// A result owns one presentation token. Replay/navigation cannot re-arm it.
class Celebration {
public:
  void clear(){*this=Celebration{};}
  void queue(bool beat,uint32_t number){clear();pending_=beat;number_=number;}
  void captured(uint32_t number){if(pending_ && number==number_){pending_=false;badge_=true;}}
  void presented(uint32_t now){if(badge_ && !started_){started_=true;at_=now;}}
  bool badge()const{return badge_;}
  uint32_t elapsed(uint32_t now)const{return started_?uint32_t(now-at_):0;}
  bool moving(uint32_t now,Effect e)const{return badge_ && started_ && elapsed(now)<duration(e);}
private:
  uint32_t number_=0,at_=0;bool pending_=false,badge_=false,started_=false;
};
}

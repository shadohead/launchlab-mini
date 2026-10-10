#pragma once
#include "controls.h"
#include "appearance.h"

// A settings-only animation clock. It never observes a real launch or owns a
// celebration token, record, preference, sensor or measurement command.
namespace SettingsEffectPreview {
class State {
public:
  static constexpr uint32_t HOLD_MS=600,FRAME_MS=50;
  bool sync(const Controls::State &controls,Appearance::Effect saved,Appearance::Theme theme,bool busy){
    const bool visible=(controls.page==Controls::Page::Settings || controls.page==Controls::Page::Edit) &&
      controls.setting==unsigned(Controls::Setting::BestEffect);
    const auto selected=controls.page==Controls::Page::Edit?Appearance::Effect(controls.draft):saved;
    if(!visible){const bool changed=visible_;*this=State{};return changed;}
    const bool changed=!visible_ || mode_!=selected || theme_!=theme || busy_!=busy;
    if(changed){started_=paintedMoving_=false;at_=lastCycle_=0;}
    visible_=true;mode_=selected;theme_=theme;busy_=busy;return changed;
  }
  bool visible()const{return visible_;}
  bool busy()const{return busy_;}
  Appearance::Effect mode()const{return mode_;}
  uint32_t elapsed(uint32_t now)const{return started_?uint32_t(now-at_)%period():0;}
  bool moving(uint32_t now)const{return visible_ && !busy_ && started_ && elapsed(now)<Appearance::duration(mode_);}
  bool frameDue(uint32_t now,uint32_t lastDraw)const{
    return visible_ && !busy_ && started_ && Appearance::duration(mode_) && uint32_t(now-lastDraw)>=FRAME_MS &&
      (moving(now) || paintedMoving_ || uint32_t(now-at_)/period()!=lastCycle_);
  }
  void presented(uint32_t now,uint32_t renderedAt){
    if(!visible_ || busy_)return;
    const bool first=!started_;
    if(first){at_=now;started_=true;}
    // Remember the frame that was painted, even if transfer crossed its end.
    paintedMoving_=Appearance::duration(mode_) && (first || moving(renderedAt));
    lastCycle_=first?0:uint32_t(renderedAt-at_)/period();
  }
  void presented(uint32_t now){presented(now,now);}
private:
  uint32_t period()const{return Appearance::duration(mode_)+HOLD_MS;}
  uint32_t at_=0,lastCycle_=0;
  Appearance::Effect mode_=Appearance::Effect::Orbit;
  Appearance::Theme theme_=Appearance::Theme::Classic;
  bool visible_=false,busy_=false,started_=false,paintedMoving_=false;
};
}

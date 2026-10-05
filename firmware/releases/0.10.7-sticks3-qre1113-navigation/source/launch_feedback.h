#pragma once
#include <cstdint>

class LaunchFeedback {
public:
  static constexpr uint32_t DISPLAY_MS=5000;
  void show(uint32_t now){started_=now;shown_=true;}
  void clear(){shown_=false;}
  void toggle(uint32_t now,bool available){if(shown_)clear();else if(available)show(now);}
  bool tick(uint32_t now){if(shown_ && now-started_>=DISPLAY_MS){clear();return true;}return false;}
  bool shown()const{return shown_;}
  uint32_t elapsed(uint32_t now)const{return shown_?now-started_:0;}
private:
  uint32_t started_=0;bool shown_=false;
};

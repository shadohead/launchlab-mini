#pragma once
#include <cstdint>

// Navigation never starts/stops measurement. Effects are handled by the sketch
// after the visible state changes; setting writes only happen on Apply.
namespace Controls {
enum class Page:uint8_t {Main,Menu,HistoryMenu,History,Battery,Settings,Edit,NewSession,Tournament};
enum class Effect:uint8_t {None,Recap,BeginEdit,Preview,Apply,CancelEdit,Older,NewSession,Tournament};
enum class Setting:uint8_t {Sleep,Rpm,Brightness,Flip,Sensor};
static constexpr unsigned SETTING_COUNT=5;
struct State {
  Page page=Page::Main;
  uint8_t menu=0,history=0,setting=0,draft=0;
  bool startSession=false;
  bool autoRecap()const{return page==Page::Main;}
  Effect tapA() {
    switch(page) {
      case Page::Main:return Effect::Recap;
      case Page::Menu:
        switch(menu) {
          case 0:page=Page::HistoryMenu;break;
          case 1:page=Page::NewSession;startSession=false;break;
          case 2:page=Page::Battery;break;
          case 3:page=Page::Settings;break;
          case 4:page=Page::Tournament;return Effect::Tournament;
          default:page=Page::Main;break;
        }break;
      case Page::HistoryMenu:page=history<3?Page::History:Page::Menu;break;
      case Page::History:page=Page::HistoryMenu;break;
      case Page::Battery:page=Page::Menu;break;
      case Page::Settings:
        if(setting<SETTING_COUNT){page=Page::Edit;return Effect::BeginEdit;}
        page=Page::Menu;break;
      case Page::Edit:return Effect::Apply;
      case Page::NewSession:page=Page::Menu;return startSession?Effect::NewSession:Effect::None;
      case Page::Tournament:break;
    }
    return Effect::None;
  }
  Effect tapB() {
    switch(page) {
      case Page::Main:page=Page::Menu;menu=0;break;
      case Page::Menu:menu=(menu+1)%6;break;
      case Page::HistoryMenu:history=(history+1)%4;break;
      case Page::History:return Effect::Older;
      case Page::Settings:setting=(setting+1)%(SETTING_COUNT+1);break;
      case Page::Edit:
        switch(Setting(setting)) {
          case Setting::Sleep:draft=draft>=10?1:draft+1;break;
          case Setting::Rpm:case Setting::Flip:case Setting::Sensor:draft=!draft;break;
          case Setting::Brightness:draft=draft>=100?10:draft+10;break;
        }return Effect::Preview;
      case Page::NewSession:startSession=!startSession;break;
      case Page::Tournament:return Effect::Tournament;
      case Page::Battery:break;
    }
    return Effect::None;
  }
  Effect holdB(bool recap=false) {
    switch(page) {
      case Page::Edit:page=Page::Settings;return Effect::CancelEdit;
      case Page::History:page=Page::HistoryMenu;break;
      case Page::HistoryMenu:case Page::Battery:case Page::Settings:case Page::NewSession:page=Page::Menu;break;
      case Page::Menu:page=Page::Main;break;
      case Page::Main:return recap?Effect::Recap:Effect::None;
      case Page::Tournament:break;
    }
    return Effect::None;
  }
  Effect holdA(bool recap=false) {
    if(page==Page::Tournament){page=Page::Main;return Effect::Tournament;}
    if(page==Page::Main && !recap){page=Page::Tournament;return Effect::Tournament;}
    return Effect::None;
  }
};
// Gate physical clicks separately from library event details. A consumed hold
// cannot trigger an unrelated click on release; a new press clears the latch.
struct Gesture {
  bool consumed=false;
  bool click(bool pressed,bool holding,bool clicked) {
    if(pressed)consumed=false;
    if(holding)consumed=true;
    return clicked && !consumed;
  }
};
static constexpr uint32_t WAKE_MAGIC=0x4e560000;
inline uint32_t encodeWake(State state,uint8_t tournamentView) {
  if(state.page==Page::Edit)state.page=Page::Settings;
  return WAKE_MAGIC|uint32_t(state.page)|(uint32_t(state.menu)<<4)|
    (uint32_t(state.history)<<7)|(uint32_t(state.setting)<<9)|(uint32_t(tournamentView)<<12);
}
inline bool decodeWake(uint32_t value,State &out,uint8_t &tournamentView) {
  if((value&0xffffe000)!=WAKE_MAGIC)return false;
  State state;state.page=Page(value&15);state.menu=(value>>4)&7;
  state.history=(value>>7)&3;state.setting=(value>>9)&7;
  if(uint8_t(state.page)>uint8_t(Page::Tournament) || state.page==Page::Edit || state.menu>=6 || state.setting>SETTING_COUNT)return false;
  out=state;tournamentView=(value>>12)&1;return true;
}
}

#include "settings_effect_preview.h"
#include <cassert>
#include <iostream>
int main(){
  using namespace Appearance;using Controls::Page;
  SettingsEffectPreview::State state;Controls::State controls;
  assert(!state.sync(controls,Effect::Orbit,Theme::Classic,false));
  controls.page=Page::Settings;controls.setting=unsigned(Controls::Setting::BestEffect);
  assert(state.sync(controls,Effect::Flames,Theme::Mint,false) && state.visible() && state.mode()==Effect::Flames);
  assert(!state.frameDue(1000,0));state.presented(1000);assert(state.moving(1000));
  assert(!state.frameDue(1049,1000) && state.frameDue(1050,1000));
  // Clear the last moving frame once, then rest until the next cycle.
  state.presented(1850);assert(state.frameDue(1900,1850));state.presented(1900);
  assert(!state.moving(1900) && !state.frameDue(2300,1900));assert(state.frameDue(2500,1900));
  state.presented(2500);assert(state.moving(2500));
  controls.page=Page::Edit;controls.draft=unsigned(Effect::Sparkles);
  assert(state.sync(controls,Effect::Flames,Theme::Mint,false) && state.mode()==Effect::Sparkles && state.elapsed(4000)==0);
  state.presented(4000);state.presented(4820,4790);
  assert(state.frameDue(4870,4820)); // transfer crossed the endpoint; clean-up is still owed
  state.presented(4870);assert(!state.frameDue(4900,4870));
  assert(state.sync(controls,Effect::Flames,Theme::Mint,true));
  state.presented(5000);assert(state.busy() && !state.frameDue(9000,5000));
  assert(state.sync(controls,Effect::Flames,Theme::Mint,false));state.presented(9000);assert(state.elapsed(9000)==0);
  assert(state.sync(controls,Effect::Flames,Theme::Amber,false));assert(state.elapsed(10000)==0);
  controls.page=Page::Settings;assert(state.sync(controls,Effect::Flames,Theme::Amber,false) && state.mode()==Effect::Flames);
  controls.setting=unsigned(Controls::Setting::Theme);assert(state.sync(controls,Effect::Flames,Theme::Amber,false) && !state.visible());
  controls.setting=unsigned(Controls::Setting::BestEffect);
  state.sync(controls,Effect::Off,Theme::Classic,false);state.presented(10000);
  assert(!state.moving(10000) && !state.frameDue(100000,10000));
  // All modes survive the millis rollover and skipped cycles without backlogs.
  for(unsigned e=0;e<EFFECTS;++e){
    state={};state.sync(controls,Effect(e),Theme::Classic,false);
    const uint32_t start=UINT32_MAX-99;state.presented(start);
    assert(state.elapsed(50)==150);assert(state.moving(50)==(150<duration(Effect(e))));
    state.presented(50);assert(!state.frameDue(60,50));
    const auto next=start+(duration(Effect(e))+600)*5+50;
    assert(state.frameDue(next,50)==(e!=unsigned(Effect::Off)));
  }
  controls.page=Page::Main;assert(state.sync(controls,Effect::Orbit,Theme::Classic,false) && !state.visible());
  std::cout<<"PASS: settings-only clock; draft/saved selection, cancellation, pause, restart, Off, wrap, quiet gap and endpoint cleanup\n";
}
